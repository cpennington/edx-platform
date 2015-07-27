"""
Module implementing `xblock.runtime.Runtime` functionality for the LMS
"""

import logging
import re
from functools import partial

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.core.cache import cache

import dogstats_wrapper as dog_stats_api
import request_cache
import static_replace
import xblock.reference.plugins
from capa.xqueue_interface import XQueueInterface
from courseware.access import has_access, get_user_role
from courseware.entrance_exams import (
    get_entrance_exam_score,
)
from courseware.field_overrides import OverrideFieldData
from courseware.masquerade import (
    MasqueradingKeyValueStore,
    filter_displayed_blocks,
    is_masquerading_as_specific_student,
)
from courseware.model_data import DjangoKeyValueStore, FieldDataCache, set_score
from courseware.models import SCORE_CHANGED
from edxmako.shortcuts import render_to_string
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig
from lms_xblock.mixin import LmsBlockMixin
from opaque_keys.edx.keys import UsageKey
from openedx.core.djangoapps.user_api.course_tag import api as user_course_tag_api
from openedx.core.lib.xblock_utils import (
    replace_course_urls,
    replace_jump_to_id_urls,
    replace_static_urls,
    add_staff_markup,
    wrap_xblock,
    request_token as xblock_request_token,
)
from psychometrics.psychoanalyze import make_psychometrics_data_update_handler
from requests.auth import HTTPBasicAuth
from student.models import anonymous_id_for_user, user_by_anonymous_id
from student.roles import CourseBetaTesterRole
from util import milestones_helpers
from util.sandboxing import can_execute_unsafe_code, get_python_lib_zip
from verify_student.services import ReverificationService
from xblock.core import XBlock
from xblock.reference.plugins import FSService
from xblock.runtime import KvsFieldData, Runtime
from xblock_django.user_service import DjangoXBlockUserService
from xmodule.contentstore.django import contentstore
from xmodule.error_module import ErrorDescriptor, NonStaffErrorDescriptor
from xmodule.library_tools import LibraryToolsService
from xmodule.lti_module import LTIModule
from xmodule.mixin import wrap_with_license
from xmodule.modulestore import prefer_xmodules
from xmodule.modulestore.django import modulestore, ModuleI18nService
from xmodule.modulestore.edit_info import EditInfoMixin
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.xml import CourseLocationManager
from xmodule.partitions.partitions_service import PartitionService
from xmodule.services import SettingsService
from xmodule.x_module import OpaqueKeyReader, XModuleServiceProvider, XModuleMixin
from xmodule.x_module import XModuleDescriptor, ModuleSystem


log = logging.getLogger(__name__)


if settings.XQUEUE_INTERFACE.get('basic_auth') is not None:
    REQUESTS_AUTH = HTTPBasicAuth(*settings.XQUEUE_INTERFACE['basic_auth'])
else:
    REQUESTS_AUTH = None

XQUEUE_INTERFACE = XQueueInterface(
    settings.XQUEUE_INTERFACE['url'],
    settings.XQUEUE_INTERFACE['django_auth'],
    REQUESTS_AUTH,
)


class LmsModuleRenderError(Exception):
    """
    An exception class for exceptions thrown by module_render that don't fit well elsewhere
    """
    pass


def _quote_slashes(match):
    """
    Helper function for `quote_slashes`
    """
    matched = match.group(0)
    # We have to escape ';', because that is our
    # escape sequence identifier (otherwise, the escaping)
    # couldn't distinguish between us adding ';_' to the string
    # and ';_' appearing naturally in the string
    if matched == ';':
        return ';;'
    elif matched == '/':
        return ';_'
    else:
        return matched


def quote_slashes(text):
    """
    Quote '/' characters so that they aren't visible to
    django's url quoting, unquoting, or url regex matching.

    Escapes '/'' to the sequence ';_', and ';' to the sequence
    ';;'. By making the escape sequence fixed length, and escaping
    identifier character ';', we are able to reverse the escaping.
    """
    return re.sub(ur'[;/]', _quote_slashes, text)


def _unquote_slashes(match):
    """
    Helper function for `unquote_slashes`
    """
    matched = match.group(0)
    if matched == ';;':
        return ';'
    elif matched == ';_':
        return '/'
    else:
        return matched


def unquote_slashes(text):
    """
    Unquote slashes quoted by `quote_slashes`
    """
    return re.sub(r'(;;|;_)', _unquote_slashes, text)


class LmsHandlerUrls(object):
    """
    A runtime mixin that provides a handler_url function that routes
    to the LMS' xblock handler view.

    This must be mixed in to a runtime that already accepts and stores
    a course_id
    """
    # pylint: disable=unused-argument
    # pylint: disable=no-member
    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        """See :method:`xblock.runtime:Runtime.handler_url`"""
        view_name = 'xblock_handler'
        if handler_name:
            # Be sure this is really a handler.
            func = getattr(block, handler_name, None)
            if not func:
                raise ValueError("{!r} is not a function name".format(handler_name))
            if not getattr(func, "_is_xblock_handler", False):
                raise ValueError("{!r} is not a handler name".format(handler_name))

        if thirdparty:
            view_name = 'xblock_handler_noauth'

        url = reverse(view_name, kwargs={
            'course_id': unicode(self.course_id),
            'usage_id': quote_slashes(unicode(block.scope_ids.usage_id).encode('utf-8')),
            'handler': handler_name,
            'suffix': suffix,
        })

        # If suffix is an empty string, remove the trailing '/'
        if not suffix:
            url = url.rstrip('/')

        # If there is a query string, append it
        if query:
            url += '?' + query

        # If third-party, return fully-qualified url
        if thirdparty:
            scheme = "https" if settings.HTTPS == "on" else "http"
            url = '{scheme}://{host}{path}'.format(
                scheme=scheme,
                host=settings.SITE_NAME,
                path=url
            )

        return url

    def local_resource_url(self, block, uri):
        """
        local_resource_url for Studio
        """
        path = reverse('xblock_resource_url', kwargs={
            'block_type': block.scope_ids.block_type,
            'uri': uri,
        })
        return '//{}{}'.format(settings.SITE_NAME, path)


class LmsPartitionService(PartitionService):
    """
    Another runtime mixin that provides access to the student partitions defined on the
    course.

    (If and when XBlock directly provides access from one block (e.g. a split_test_module)
    to another (e.g. a course_module), this won't be necessary, but for now it seems like
    the least messy way to hook things through)

    """
    @property
    def course_partitions(self):
        course = modulestore().get_course(self._course_id)
        return course.user_partitions


class UserTagsService(object):
    """
    A runtime class that provides an interface to the user service.  It handles filling in
    the current course id and current user.
    """

    COURSE_SCOPE = user_course_tag_api.COURSE_SCOPE

    def __init__(self, runtime):
        self.runtime = runtime

    def _get_current_user(self):
        """Returns the real, not anonymized, current user."""
        real_user = self.runtime.get_real_user(self.runtime.anonymous_student_id)
        return real_user

    def get_tag(self, scope, key):
        """
        Get a user tag for the current course and the current user for a given key

            scope: the current scope of the runtime
            key: the key for the value we want
        """
        if scope != user_course_tag_api.COURSE_SCOPE:
            raise ValueError("unexpected scope {0}".format(scope))

        return user_course_tag_api.get_course_tag(
            self._get_current_user(),
            self.runtime.course_id, key
        )

    def set_tag(self, scope, key, value):
        """
        Set the user tag for the current course and the current user for a given key

            scope: the current scope of the runtime
            key: the key that to the value to be set
            value: the value to set
        """
        if scope != user_course_tag_api.COURSE_SCOPE:
            raise ValueError("unexpected scope {0}".format(scope))

        return user_course_tag_api.set_course_tag(
            self._get_current_user(),
            self.runtime.course_id, key, value
        )


def get_score_bucket(grade, max_grade):
    """
    Function to split arbitrary score ranges into 3 buckets.
    Used with statsd tracking.
    """
    score_bucket = "incorrect"
    if grade > 0 and grade < max_grade:
        score_bucket = "partial"
    elif grade == max_grade:
        score_bucket = "correct"

    return score_bucket


class LmsRuntime(LmsHandlerUrls, XModuleServiceProvider, Runtime):  # pylint: disable=abstract-method
    """
    ModuleSystem specialized to the LMS
    """
    def __init__(self,
                 request,
                 user=None,
                 position=None,
                 wrap_xmodule_display=True,
                 grade_bucket_type=None,
                 static_asset_path='',
                 disable_staff_debug_info=False,
                 course_id=None,
                 **kwargs):

        self.request_token = kwargs.pop('request_token', None)
        self.course_id=course_id
        self.user = request.user if user is None else user
        self.request = request
        self._field_data_cache = None

        if course_id is not None:
            self._field_data_cache = FieldDataCache([], course_id, self.user)

        self.position = None
        if position is not None:
            try:
                self.position = int(position)
            except (ValueError, TypeError):
                log.exception('Non-integer %r passed as position.', position)
                self.position = None

        self.wrap_xmodule_display = wrap_xmodule_display
        self.grade_bucket_type = grade_bucket_type
        self.static_asset_path = static_asset_path
        self.disable_staff_debug_info = disable_staff_debug_info
        self.course = None

        request_cache_dict = request_cache.get_cache('partition-cache')
        services = kwargs.setdefault('services', {})
        services['user_tags'] = UserTagsService(self)
        services['partitions'] = LmsPartitionService(
            user=self.user,
            course_id=course_id,
            track_function=kwargs.get('track_function', None),
            cache=request_cache_dict
        )
        services['library_tools'] = LibraryToolsService(modulestore())
        services['fs'] = xblock.reference.plugins.FSService()
        services['settings'] = SettingsService()

        if course_id is not None:
            id_manager = CourseLocationManager(course_id)
            kwargs.setdefault('id_reader', id_manager)
            kwargs.setdefault('id_generator', id_manager)
        else:
            kwargs.setdefault('id_reader', OpaqueKeyReader())

        kwargs.setdefault('mixins', (LmsBlockMixin, InheritanceMixin, XModuleMixin, EditInfoMixin))
        kwargs.setdefault('select', prefer_xmodules)

        super(LmsRuntime, self).__init__(**kwargs)

    def wrap_aside(self, block, aside, view, frag, context):
        """
        Creates a div which identifies the aside, points to the original block,
        and writes out the json_init_args into a script tag.

        The default implementation creates a frag to wraps frag w/ a div identifying the xblock. If you have
        javascript, you'll need to override this impl
        """
        extra_data = {
            'block-id': quote_slashes(unicode(block.scope_ids.usage_id)),
            'url-selector': 'asideBaseUrl',
            'runtime-class': 'LmsRuntime',
        }
        if self.request_token:
            extra_data['request-token'] = self.request_token

        return self._wrap_ele(
            aside,
            view,
            frag,
            extra_data,
        )

    def applicable_aside_types(self, block):
        """
        Return all of the asides which might be decorating this `block`.

        Arguments:
            block (:class:`.XBlock`): The block to render retrieve asides for.
        """

        config = XBlockAsidesConfig.current()

        if not config.enabled:
            return []

        if block.scope_ids.block_type in config.disabled_blocks.split():
            return []

        return super(LmsRuntime, self).applicable_aside_types()

    def _fulfill_content_milestones(self, xblock):
        """
        Internal helper to handle milestone fulfillments for the specified content module
        """
        # Fulfillment Use Case: Entrance Exam
        # If this module is part of an entrance exam, we'll need to see if the student
        # has reached the point at which they can collect the associated milestone
        if settings.FEATURES.get('ENTRANCE_EXAMS', False):
            course = modulestore().get_course(self.course_id)
            content = modulestore().get_item(xblock)
            entrance_exam_enabled = getattr(course, 'entrance_exam_enabled', False)
            in_entrance_exam = getattr(content, 'in_entrance_exam', False)
            if entrance_exam_enabled and in_entrance_exam:
                # We don't have access to the true request object in this context, but we can use a mock
                # TODO: Use the local request
                request = RequestFactory().request()
                request.user = self.user
                exam_pct = get_entrance_exam_score(request, course)
                if exam_pct >= course.entrance_exam_minimum_score_pct:
                    exam_key = UsageKey.from_string(course.entrance_exam_id)
                    relationship_types = milestones_helpers.get_milestone_relationship_types()
                    content_milestones = milestones_helpers.get_course_content_milestones(
                        self.course_id,
                        exam_key,
                        relationship=relationship_types['FULFILLS']
                    )
                    # Add each milestone to the user's set...
                    user = {'id': request.user.id}
                    for milestone in content_milestones:
                        milestones_helpers.add_user_milestone(user, milestone)

    def handle_grade_event(self, block, event_type, event):  # pylint: disable=unused-argument
        """
        Manages the workflow for recording and updating of student module grade state
        """
        user_id = event.get('user_id', self.user.id)

        grade = event.get('value')
        max_grade = event.get('max_value')

        set_score(
            user_id,
            block.location,
            grade,
            max_grade,
        )

        # Bin score into range and increment stats
        score_bucket = get_score_bucket(grade, max_grade)

        tags = [
            u"org:{}".format(self.course_id.org),
            u"course:{}".format(self.course_id),
            u"score_bucket:{0}".format(score_bucket)
        ]

        if self.grade_bucket_type is not None:
            tags.append('type:%s' % self.grade_bucket_type)

        dog_stats_api.increment("lms.courseware.question_answered", tags=tags)

        # Cycle through the milestone fulfillment scenarios to see if any are now applicable
        # thanks to the updated grading information that was just submitted
        self._fulfill_content_milestones(
            block,
        )

        # Send a signal out to any listeners who are waiting for score change
        # events.
        SCORE_CHANGED.send(
            sender=None,
            points_possible=event['max_value'],
            points_earned=event['value'],
            user_id=user_id,
            course_id=unicode(self.course_id),
            usage_id=unicode(block.location)
        )

    def publish(self, block, event_type, event):
        """A function that allows XModules to publish events."""
        if event_type == 'grade' and not is_masquerading_as_specific_student(self.user, self.course_id):
            self.handle_grade_event(block, event_type, event)
        else:
            self._track_function(event_type, event)

    def resource_url(*args, **kwargs):
        raise Exception("Need to figure out resource_url")

    def get_block(self, block_id, for_parent=None):
        return self.get_module_for_descriptor(
            modulestore().get_item(block_id, for_parent=for_parent),
        )

    def _track_function(self, event_type, event):
        '''
        A tracking function that logs what happened.
        For use in ModuleSystem.
        '''
        from track.views import server_track
        return server_track(self.request, event_type, event, page='x_module')


    def get_module_for_descriptor(self, descriptor):
        """
        Implements get_module, extracting out the request-specific functionality.

        disable_staff_debug_info : If this is True, exclude staff debug information in the rendering of the module.

        See get_module() docstring for further details.
        """
        track_function = self._track_function
        xqueue_callback_url_prefix = self.get_xqueue_callback_url_prefix()

        user_location = getattr(self.request, 'session', {}).get('country_code')

        student_kvs = DjangoKeyValueStore(self._field_data_cache)
        if is_masquerading_as_specific_student(self.user, self.course_id):
            student_kvs = MasqueradingKeyValueStore(student_kvs, self.request.session)
        student_data = KvsFieldData(student_kvs)

        return self.get_module_for_descriptor_without_request(
            descriptor=descriptor,
            student_data=student_data,
            track_function=track_function,
            xqueue_callback_url_prefix=xqueue_callback_url_prefix,
            user_location=user_location,
            request_token=xblock_request_token(self.request),
        )


    def get_xqueue_callback_url_prefix(self):
        """
        Calculates default prefix based on request, but allows override via settings

        This is separated from get_module_for_descriptor so that it can be called
        by the LMS before submitting background tasks to run.  The xqueue callbacks
        should go back to the LMS, not to the worker.
        """
        prefix = '{proto}://{host}'.format(
            proto=self.request.META.get(
                'HTTP_X_FORWARDED_PROTO',
                'https' if self.request.is_secure() else 'http'
            ),
            host=self.request.get_host()
        )
        return settings.XQUEUE_INTERFACE.get('callback_url', prefix)


    # TODO: Find all the places that this method is called and figure out how to
    # get a loaded course passed into it
    def get_module_for_descriptor_without_request(
            self, descriptor, student_data,  # pylint: disable=invalid-name
            track_function, xqueue_callback_url_prefix, request_token,
            user_location=None):
        """
        Actually implement get_module, without requiring a request.

        See get_module() docstring for further details.

        Arguments:
            request_token (str): A unique token for this request, used to isolate xblock rendering
        """

        (system, student_data) = self.get_module_system(
            student_data=student_data,  # These have implicit user bindings, the rest of args are considered not to
            descriptor=descriptor,
            track_function=track_function,
            xqueue_callback_url_prefix=xqueue_callback_url_prefix,
            user_location=user_location,
            request_token=request_token,
        )

        descriptor.bind_for_student(
            system,
            self.user.id,
            [
                partial(OverrideFieldData.wrap, self.user, self.course),
                partial(LmsFieldData, student_data=student_data),
            ],
        )

        descriptor.scope_ids = descriptor.scope_ids._replace(user_id=self.user.id)  # pylint: disable=protected-access

        # Do not check access when it's a noauth request.
        # Not that the access check needs to happen after the descriptor is bound
        # for the student, since there may be field override data for the student
        # that affects xblock visibility.
        if getattr(self.user, 'known', True):
            if not has_access(self.user, 'load', descriptor, self.course_id):
                return None

        return descriptor

    def make_xqueue_callback(self, descriptor, xqueue_callback_url_prefix, dispatch='score_update'):
        """
        Returns fully qualified callback URL for external queueing system
        """
        relative_xqueue_callback_url = reverse(
            'xqueue_callback',
            kwargs=dict(
                course_id=self.course_id.to_deprecated_string(),
                userid=str(self.user.id),
                mod_id=descriptor.location.to_deprecated_string(),
                dispatch=dispatch
            ),
        )
        return xqueue_callback_url_prefix + relative_xqueue_callback_url


    def get_module_system(self, student_data,  # TODO  # pylint: disable=too-many-statements
                          descriptor, track_function, xqueue_callback_url_prefix,
                          request_token, user_location=None):
        """
        Helper function that returns a module system and student_data bound to a user and a descriptor.

        The purpose of this function is to factor out everywhere a user is implicitly bound when creating a module,
        to allow an existing module to be re-bound to a user.  Most of the user bindings happen when creating the
        closures that feed the instantiation of ModuleSystem.

        The arguments fall into two categories: those that have explicit or implicit user binding, which are user
        and student_data, and those don't and are just present so that ModuleSystem can be instantiated, which
        are all the other arguments.  Ultimately, this isn't too different than how get_module_for_descriptor_internal
        was before refactoring.

        Arguments:
            see arguments for get_module()
            request_token (str): A token unique to the request use by xblock initialization

        Returns:
            (LmsModuleSystem, KvsFieldData):  (module system, student_data) bound to, primarily, the user and descriptor
        """

        # Default queuename is course-specific and is derived from the course that
        #   contains the current module.
        # TODO: Queuename should be derived from 'course_settings.json' of each course
        xqueue_default_queuename = descriptor.location.org + '-' + descriptor.location.course

        xqueue = {
            'interface': XQUEUE_INTERFACE,
            'construct_callback': partial(self.make_xqueue_callback, descriptor, xqueue_callback_url_prefix),
            'default_queuename': xqueue_default_queuename.replace(' ', '_'),
            'waittime': settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS
        }

        # This is a hacky way to pass settings to the combined open ended xmodule
        # It needs an S3 interface to upload images to S3
        # It needs the open ended grading interface in order to get peer grading to be done
        # this first checks to see if the descriptor is the correct one, and only sends settings if it is

        # Get descriptor metadata fields indicating needs for various settings
        needs_open_ended_interface = getattr(descriptor, "needs_open_ended_interface", False)
        needs_s3_interface = getattr(descriptor, "needs_s3_interface", False)

        # Initialize interfaces to None
        open_ended_grading_interface = None
        s3_interface = None

        # Create interfaces if needed
        if needs_open_ended_interface:
            open_ended_grading_interface = settings.OPEN_ENDED_GRADING_INTERFACE
            open_ended_grading_interface['mock_peer_grading'] = settings.MOCK_PEER_GRADING
            open_ended_grading_interface['mock_staff_grading'] = settings.MOCK_STAFF_GRADING
        if needs_s3_interface:
            s3_interface = {
                'access_key': getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
                'secret_access_key': getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
                'storage_bucket_name': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'openended')
            }

        def inner_get_module(descriptor):
            """
            Delegate to get_module_for_descriptor_internal() with all values except `descriptor` set.

            Because it does an access check, it may return None.
            """
            # TODO: fix this so that make_xqueue_callback uses the descriptor passed into
            # inner_get_module, not the parent's callback.  Add it as an argument....
            return self.get_module_for_descriptor_without_request(
                descriptor=descriptor,
                student_data=student_data,
                track_function=track_function,
                xqueue_callback_url_prefix=xqueue_callback_url_prefix,
                user_location=user_location,
                request_token=request_token,
            )

        def rebind_noauth_module_to_user(module, real_user):
            """
            A function that allows a module to get re-bound to a real user if it was previously bound to an AnonymousUser.

            Will only work within a module bound to an AnonymousUser, e.g. one that's instantiated by the noauth_handler.

            Arguments:
                module (any xblock type):  the module to rebind
                real_user (django.contrib.auth.models.User):  the user to bind to

            Returns:
                nothing (but the side effect is that module is re-bound to real_user)
            """
            if self.user.is_authenticated():
                err_msg = ("rebind_noauth_module_to_user can only be called from a module bound to "
                        "an anonymous user")
                log.error(err_msg)
                raise LmsModuleRenderError(err_msg)

            field_data_cache_real_user = FieldDataCache.cache_for_descriptor_descendents(
                self.course_id,
                real_user,
                module.descriptor,
                asides=XBlockAsidesConfig.possible_asides(),
            )
            student_data_real_user = KvsFieldData(DjangoKeyValueStore(field_data_cache_real_user))

            (inner_system, inner_student_data) = self.get_module_system(
                student_data=student_data_real_user,  # These have implicit user bindings, rest of args considered not to
                descriptor=module.descriptor,
                track_function=track_function,
                xqueue_callback_url_prefix=xqueue_callback_url_prefix,
                user_location=user_location,
                request_token=request_token,
            )

            module.descriptor.bind_for_student(
                inner_system,
                real_user.id,
                [
                    partial(OverrideFieldData.wrap, real_user, self.course),
                    partial(LmsFieldData, student_data=inner_student_data),
                ],
            )

            module.descriptor.scope_ids = (
                module.descriptor.scope_ids._replace(user_id=real_user.id)  # pylint: disable=protected-access
            )
            module.scope_ids = module.descriptor.scope_ids  # this is needed b/c NamedTuples are immutable
            # now bind the module to the new ModuleSystem instance and vice-versa
            module.runtime = inner_system
            inner_system.xmodule_instance = module

        # Build a list of wrapping functions that will be applied in order
        # to the Fragment content coming out of the xblocks that are about to be rendered.
        block_wrappers = []

        if is_masquerading_as_specific_student(self.user, self.course_id):
            block_wrappers.append(filter_displayed_blocks)

        if settings.FEATURES.get("LICENSING", False):
            block_wrappers.append(wrap_with_license)

        # Wrap the output display in a single div to allow for the XModule
        # javascript to be bound correctly
        if self.wrap_xmodule_display is True:
            block_wrappers.append(partial(
                wrap_xblock,
                'LmsRuntime',
                extra_data={'course-id': self.course_id.to_deprecated_string()},
                usage_id_serializer=lambda usage_id: quote_slashes(usage_id.to_deprecated_string()),
                request_token=request_token,
            ))

        # TODO (cpennington): When modules are shared between courses, the static
        # prefix is going to have to be specific to the module, not the directory
        # that the xml was loaded from

        # Rewrite urls beginning in /static to point to course-specific content
        block_wrappers.append(partial(
            replace_static_urls,
            getattr(descriptor, 'data_dir', None),
            course_id=self.course_id,
            static_asset_path=self.static_asset_path or descriptor.static_asset_path
        ))

        # Allow URLs of the form '/course/' refer to the root of multicourse directory
        #   hierarchy of this course
        block_wrappers.append(partial(replace_course_urls, self.course_id))

        # this will rewrite intra-courseware links (/jump_to_id/<id>). This format
        # is an improvement over the /course/... format for studio authored courses,
        # because it is agnostic to course-hierarchy.
        # NOTE: module_id is empty string here. The 'module_id' will get assigned in the replacement
        # function, we just need to specify something to get the reverse() to work.
        block_wrappers.append(partial(
            replace_jump_to_id_urls,
            self.course_id,
            reverse('jump_to_id', kwargs={'course_id': self.course_id.to_deprecated_string(), 'module_id': ''}),
        ))

        if settings.FEATURES.get('DISPLAY_DEBUG_INFO_TO_STAFF'):
            if is_masquerading_as_specific_student(self.user, self.course_id):
                # When masquerading as a specific student, we want to show the debug button
                # unconditionally to enable resetting the state of the student we are masquerading as.
                # We already know the user has staff access when masquerading is active.
                staff_access = True
                # To figure out whether the user has instructor access, we temporarily remove the
                # masquerade_settings from the real_user.  With the masquerading settings in place,
                # the result would always be "False".
                masquerade_settings = self.user.real_user.masquerade_settings
                del self.user.real_user.masquerade_settings
                instructor_access = bool(has_access(self.user.real_user, 'instructor', descriptor, self.course_id))
                self.user.real_user.masquerade_settings = masquerade_settings
            else:
                staff_access = has_access(self.user, 'staff', descriptor, self.course_id)
                instructor_access = bool(has_access(self.user, 'instructor', descriptor, self.course_id))
            if staff_access:
                block_wrappers.append(partial(add_staff_markup, self.user, instructor_access, self.disable_staff_debug_info))

        # These modules store data using the anonymous_student_id as a key.
        # To prevent loss of data, we will continue to provide old modules with
        # the per-student anonymized id (as we have in the past),
        # while giving selected modules a per-course anonymized id.
        # As we have the time to manually test more modules, we can add to the list
        # of modules that get the per-course anonymized id.
        is_pure_xblock = isinstance(descriptor, XBlock) and not isinstance(descriptor, XModuleDescriptor)
        module_class = getattr(descriptor, 'module_class', None)
        is_lti_module = not is_pure_xblock and issubclass(module_class, LTIModule)
        if is_pure_xblock or is_lti_module:
            anonymous_student_id = anonymous_id_for_user(self.user, self.course_id)
        else:
            anonymous_student_id = anonymous_id_for_user(self.user, None)

        field_data = LmsFieldData(descriptor._field_data, student_data)  # pylint: disable=protected-access

        user_is_staff = bool(has_access(self.user, u'staff', descriptor.location, self.course_id))

        system = ModuleSystem(
            track_function=track_function,
            render_template=render_to_string,
            static_url=settings.STATIC_URL,
            xqueue=xqueue,
            # TODO (cpennington): Figure out how to share info between systems
            filestore=self.service(descriptor, 'legacy-xmodule-descriptor-system').resources_fs,
            get_module=inner_get_module,
            user=self.user,
            debug=settings.DEBUG,
            hostname=settings.SITE_NAME,
            # TODO (cpennington): This should be removed when all html from
            # a module is coming through get_html and is therefore covered
            # by the replace_static_urls code below
            replace_urls=partial(
                static_replace.replace_static_urls,
                data_directory=getattr(descriptor, 'data_dir', None),
                course_id=self.course_id,
                static_asset_path=self.static_asset_path or descriptor.static_asset_path,
            ),
            replace_course_urls=partial(
                static_replace.replace_course_urls,
                course_key=self.course_id
            ),
            replace_jump_to_id_urls=partial(
                static_replace.replace_jump_to_id_urls,
                course_id=self.course_id,
                jump_to_id_base_url=reverse('jump_to_id', kwargs={'course_id': self.course_id.to_deprecated_string(), 'module_id': ''})
            ),
            node_path=settings.NODE_PATH,
            publish=self.publish,
            anonymous_student_id=anonymous_student_id,
            course_id=self.course_id,
            open_ended_grading_interface=open_ended_grading_interface,
            s3_interface=s3_interface,
            cache=cache,
            can_execute_unsafe_code=(lambda: can_execute_unsafe_code(self.course_id)),
            get_python_lib_zip=(lambda: get_python_lib_zip(contentstore, self.course_id)),
            wrappers=block_wrappers,
            get_real_user=user_by_anonymous_id,
            get_user_role=lambda: get_user_role(self.user, self.course_id),
            descriptor_system=self.service(descriptor, 'legacy-xmodule-descriptor-system'),  # pylint: disable=protected-access
            rebind_noauth_module_to_user=rebind_noauth_module_to_user,
            user_location=user_location,
        )

        # pass position specified in URL to module through ModuleSystem
        system.set('position', self.position)
        if settings.FEATURES.get('ENABLE_PSYCHOMETRICS') and self.user.is_authenticated():
            system.set(
                'psychometrics_handler',  # set callback for updating PsychometricsData
                make_psychometrics_data_update_handler(self.course_id, self.user, descriptor.location)
            )

        system.set(u'user_is_staff', user_is_staff)
        system.set(u'user_is_admin', bool(has_access(self.user, u'staff', 'global')))
        system.set(u'user_is_beta_tester', CourseBetaTesterRole(self.course_id).has_user(self.user))
        system.set(u'days_early_for_beta', getattr(descriptor, 'days_early_for_beta'))

        # make an ErrorDescriptor -- assuming that the descriptor's system is ok
        if has_access(self.user, u'staff', descriptor.location, self.course_id):
            system.error_descriptor_class = ErrorDescriptor
        else:
            system.error_descriptor_class = NonStaffErrorDescriptor

        return system, field_data
