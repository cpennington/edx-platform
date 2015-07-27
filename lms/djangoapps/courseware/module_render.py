"""
Module rendering
"""

import hashlib
import json
import logging
import mimetypes

import static_replace

from collections import OrderedDict
from functools import partial
from requests.auth import HTTPBasicAuth
import dogstats_wrapper as dog_stats_api

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.test.client import RequestFactory
from django.views.decorators.csrf import csrf_exempt

import newrelic.agent

from capa.xqueue_interface import XQueueInterface
from courseware.access import has_access, get_user_role
from courseware.models import SCORE_CHANGED
from courseware.model_data import FieldDataCache
from courseware.entrance_exams import (
    get_entrance_exam_score,
    user_must_complete_entrance_exam
)
from edxmako.shortcuts import render_to_string
from eventtracking import tracker
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from lms.djangoapps.lms_xblock.runtime import LmsRuntime, unquote_slashes, quote_slashes
from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey, CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.lib.xblock_utils import (
    replace_course_urls,
    replace_jump_to_id_urls,
    replace_static_urls,
    add_staff_markup,
    wrap_xblock,
    request_token as xblock_request_token,
)
from psychometrics.psychoanalyze import make_psychometrics_data_update_handler
from student.models import anonymous_id_for_user, user_by_anonymous_id
from student.roles import CourseBetaTesterRole
from xblock.core import XBlock
from xblock.django.request import django_to_webob_request, webob_to_django_response
from xblock_django.user_service import DjangoXBlockUserService
from xblock.exceptions import NoSuchHandlerError, NoSuchViewError
from xblock.reference.plugins import FSService
from xblock.runtime import KvsFieldData
from xmodule.contentstore.django import contentstore
from xmodule.error_module import ErrorDescriptor, NonStaffErrorDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore.django import modulestore, ModuleI18nService
from xmodule.lti_module import LTIModule
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.x_module import XModuleDescriptor, ModuleSystem
from xmodule.mixin import wrap_with_license
from util.json_request import JsonResponse
from util.sandboxing import can_execute_unsafe_code, get_python_lib_zip
from util import milestones_helpers
from verify_student.services import ReverificationService
from courseware.masquerade import setup_masquerade
from .field_overrides import OverrideFieldData

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

# TODO: course_id and course_key are used interchangeably in this file, which is wrong.
# Some brave person should make the variable names consistently someday, but the code's
# coupled enough that it's kind of tricky--you've been warned!

def toc_for_course(user, request, course, active_chapter, active_section, field_data_cache):
    '''
    Create a table of contents from the module store

    Return format:
    [ {'display_name': name, 'url_name': url_name,
       'sections': SECTIONS, 'active': bool}, ... ]

    where SECTIONS is a list
    [ {'display_name': name, 'url_name': url_name,
       'format': format, 'due': due, 'active' : bool, 'graded': bool}, ...]

    active is set for the section and chapter corresponding to the passed
    parameters, which are expected to be url_names of the chapter+section.
    Everything else comes from the xml, or defaults to "".

    chapters with name 'hidden' are skipped.

    NOTE: assumes that if we got this far, user has access to course.  Returns
    None if this is not the case.

    field_data_cache must include data from the course module and 2 levels of its descendents
    '''

    with modulestore().bulk_operations(course.id):
        course_module = get_module_for_descriptor(
            user, request, course, field_data_cache, course.id, course=course
        )
        if course_module is None:
            return None

        toc_chapters = list()
        chapters = course_module.get_display_items()

        # See if the course is gated by one or more content milestones
        required_content = milestones_helpers.get_required_content(course, user)

        # The user may not actually have to complete the entrance exam, if one is required
        if not user_must_complete_entrance_exam(request, user, course):
            required_content = [content for content in required_content if not content == course.entrance_exam_id]

        for chapter in chapters:
            # Only show required content, if there is required content
            # chapter.hide_from_toc is read-only (boo)
            local_hide_from_toc = False
            if required_content:
                if unicode(chapter.location) not in required_content:
                    local_hide_from_toc = True

            # Skip the current chapter if a hide flag is tripped
            if chapter.hide_from_toc or local_hide_from_toc:
                continue

            sections = list()
            for section in chapter.get_display_items():

                active = (chapter.url_name == active_chapter and
                          section.url_name == active_section)

                if not section.hide_from_toc:
                    sections.append({'display_name': section.display_name_with_default,
                                     'url_name': section.url_name,
                                     'format': section.format if section.format is not None else '',
                                     'due': section.due,
                                     'active': active,
                                     'graded': section.graded,
                                     })
            toc_chapters.append({
                'display_name': chapter.display_name_with_default,
                'url_name': chapter.url_name,
                'sections': sections,
                'active': chapter.url_name == active_chapter
            })
        return toc_chapters


def get_module(user, request, usage_key, field_data_cache,
               position=None, log_if_not_found=True, wrap_xmodule_display=True,
               grade_bucket_type=None, depth=0,
               static_asset_path='', course=None):
    """
    Get an instance of the xmodule class identified by location,
    setting the state based on an existing StudentModule, or creating one if none
    exists.

    Arguments:
      - user                  : User for whom we're getting the module
      - request               : current django HTTPrequest.  Note: request.user isn't used for anything--all auth
                                and such works based on user.
      - usage_key             : A UsageKey object identifying the module to load
      - field_data_cache      : a FieldDataCache
      - position              : extra information from URL for user-specified
                                position within module
      - log_if_not_found      : If this is True, we log a debug message if we cannot find the requested xmodule.
      - wrap_xmodule_display  : If this is True, wrap the output display in a single div to allow for the
                                XModule javascript to be bound correctly
      - depth                 : number of levels of descendents to cache when loading this module.
                                None means cache all descendents
      - static_asset_path     : static asset path to use (overrides descriptor's value); needed
                                by get_course_info_section, because info section modules
                                do not have a course as the parent module, and thus do not
                                inherit this lms key value.

    Returns: xmodule instance, or None if the user does not have access to the
    module.  If there's an error, will try to return an instance of ErrorModule
    if possible.  If not possible, return None.
    """
    try:
        descriptor = modulestore().get_item(usage_key, depth=depth)
        return get_module_for_descriptor(user, request, descriptor, field_data_cache, usage_key.course_key,
                                         position=position,
                                         wrap_xmodule_display=wrap_xmodule_display,
                                         grade_bucket_type=grade_bucket_type,
                                         static_asset_path=static_asset_path,
                                         course=course)
    except ItemNotFoundError:
        if log_if_not_found:
            log.debug("Error in get_module: ItemNotFoundError")
        return None

    except:
        # Something has gone terribly wrong, but still not letting it turn into a 500.
        log.exception("Error in get_module")
        return None


def load_single_xblock(request, user_id, course_id, usage_key_string, course=None):
    """
    Load a single XBlock identified by usage_key_string.
    """
    usage_key = UsageKey.from_string(usage_key_string)
    course_key = CourseKey.from_string(course_id)
    usage_key = usage_key.map_into_course(course_key)
    user = User.objects.get(id=user_id)
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_key,
        user,
        modulestore().get_item(usage_key),
        depth=0,
    )
    instance = get_module(user, request, usage_key, field_data_cache, grade_bucket_type='xqueue', course=course)
    if instance is None:
        msg = "No module {0} for user {1}--access denied?".format(usage_key_string, user)
        log.debug(msg)
        raise Http404
    return instance


@csrf_exempt
def xqueue_callback(request, course_id, userid, mod_id, dispatch):
    '''
    Entry point for graded results from the queueing system.
    '''
    data = request.POST.copy()

    # Test xqueue package, which we expect to be:
    #   xpackage = {'xqueue_header': json.dumps({'lms_key':'secretkey',...}),
    #               'xqueue_body'  : 'Message from grader'}
    for key in ['xqueue_header', 'xqueue_body']:
        if key not in data:
            raise Http404

    header = json.loads(data['xqueue_header'])
    if not isinstance(header, dict) or 'lms_key' not in header:
        raise Http404

    course_key = CourseKey.from_string(course_id)

    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=0)

        instance = load_single_xblock(request, userid, course_id, mod_id, course=course)

        # Transfer 'queuekey' from xqueue response header to the data.
        # This is required to use the interface defined by 'handle_ajax'
        data.update({'queuekey': header['lms_key']})

        # We go through the "AJAX" path
        # So far, the only dispatch from xqueue will be 'score_update'
        try:
            # Can ignore the return value--not used for xqueue_callback
            instance.handle_ajax(dispatch, data)
            # Save any state that has changed to the underlying KeyValueStore
            instance.save()
        except:
            log.exception("error processing ajax call")
            raise

        return HttpResponse("")


@csrf_exempt
def handle_xblock_callback_noauth(request, course_id, usage_id, handler, suffix=None):
    """
    Entry point for unauthenticated XBlock handlers.
    """
    request.user.known = False

    course_key = CourseKey.from_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=0)
        return _invoke_xblock_handler(request, course_id, usage_id, handler, suffix, course=course)


def handle_xblock_callback(request, course_id, usage_id, handler, suffix=None):
    """
    Generic view for extensions. This is where AJAX calls go.

    Arguments:

      - request -- the django request.
      - location -- the module location. Used to look up the XModule instance
      - course_id -- defines the course context for this request.

    Return 403 error if the user is not logged in. Raises Http404 if
    the location and course_id do not identify a valid module, the module is
    not accessible by the user, or the module raises NotFoundError. If the
    module raises any other error, it will escape this function.
    """
    if not request.user.is_authenticated():
        return HttpResponse('Unauthenticated', status=403)

    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        raise Http404("Invalid location")

    with modulestore().bulk_operations(course_key):
        try:
            course = modulestore().get_course(course_key)
        except ItemNotFoundError:
            raise Http404("invalid location")

        return _invoke_xblock_handler(request, course_id, usage_id, handler, suffix, course=course)


def xblock_resource(request, block_type, uri):  # pylint: disable=unused-argument
    """
    Return a package resource for the specified XBlock.
    """
    try:
        xblock_class = XBlock.load_class(block_type, select=settings.XBLOCK_SELECT_FUNCTION)
        content = xblock_class.open_local_resource(uri)
    except IOError:
        log.info('Failed to load xblock resource', exc_info=True)
        raise Http404
    except Exception:  # pylint: disable=broad-except
        log.error('Failed to load xblock resource', exc_info=True)
        raise Http404
    mimetype, _ = mimetypes.guess_type(uri)
    return HttpResponse(content, mimetype=mimetype)


def get_module_by_usage_id(request, course_id, usage_id, disable_staff_debug_info=False, course=None):
    """
    Gets a module instance based on its `usage_id` in a course, for a given request/user

    Returns (instance, tracking_context)
    """
    user = request.user

    try:
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        usage_key = course_id.make_usage_key_from_deprecated_string(unquote_slashes(usage_id))
    except InvalidKeyError:
        raise Http404("Invalid location")

    try:
        descriptor = modulestore().get_item(usage_key)
        descriptor_orig_usage_key, descriptor_orig_version = modulestore().get_block_original_usage(usage_key)
    except ItemNotFoundError:
        log.warn(
            "Invalid location for course id %s: %s",
            usage_key.course_key,
            usage_key
        )
        raise Http404

    tracking_context = {
        'module': {
            'display_name': descriptor.display_name_with_default,
            'usage_key': unicode(descriptor.location),
        }
    }

    # For blocks that are inherited from a content library, we add some additional metadata:
    if descriptor_orig_usage_key is not None:
        tracking_context['module']['original_usage_key'] = unicode(descriptor_orig_usage_key)
        tracking_context['module']['original_usage_version'] = unicode(descriptor_orig_version)

    unused_masquerade, user = setup_masquerade(request, course_id, has_access(user, 'staff', descriptor, course_id))
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_id,
        user,
        descriptor
    )
    instance = get_module_for_descriptor(
        user,
        request,
        descriptor,
        field_data_cache,
        usage_key.course_key,
        disable_staff_debug_info=disable_staff_debug_info,
        course=course
    )
    if instance is None:
        # Either permissions just changed, or someone is trying to be clever
        # and load something they shouldn't have access to.
        log.debug("No module %s for user %s -- access denied?", usage_key, user)
        raise Http404

    return (instance, tracking_context)


def _invoke_xblock_handler(request, course_id, usage_id, handler, suffix, course=None):
    """
    Invoke an XBlock handler, either authenticated or not.

    Arguments:
        request (HttpRequest): the current request
        course_id (str): A string of the form org/course/run
        usage_id (str): A string of the form i4x://org/course/category/name@revision
        handler (str): The name of the handler to invoke
        suffix (str): The suffix to pass to the handler when invoked
    """

    # Check submitted files
    files = request.FILES or {}
    error_msg = _check_files_limits(files)
    if error_msg:
        return JsonResponse(object={'success': error_msg}, status=413)

    # Make a CourseKey from the course_id, raising a 404 upon parse error.
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        raise Http404

    with modulestore().bulk_operations(course_key):
        instance, tracking_context = get_module_by_usage_id(request, course_id, usage_id, course=course)

        # Name the transaction so that we can view XBlock handlers separately in
        # New Relic. The suffix is necessary for XModule handlers because the
        # "handler" in those cases is always just "xmodule_handler".
        nr_tx_name = "{}.{}".format(instance.__class__.__name__, handler)
        nr_tx_name += "/{}".format(suffix) if suffix else ""
        newrelic.agent.set_transaction_name(nr_tx_name, group="Python/XBlock/Handler")

        tracking_context_name = 'module_callback_handler'
        req = django_to_webob_request(request)
        try:
            with tracker.get_tracker().context(tracking_context_name, tracking_context):
                resp = instance.handle(handler, req, suffix)

        except NoSuchHandlerError:
            log.exception("XBlock %s attempted to access missing handler %r", instance, handler)
            raise Http404

        # If we can't find the module, respond with a 404
        except NotFoundError:
            log.exception("Module indicating to user that request doesn't exist")
            raise Http404

        # For XModule-specific errors, we log the error and respond with an error message
        except ProcessingError as err:
            log.warning("Module encountered an error while processing AJAX call",
                        exc_info=True)
            return JsonResponse(object={'success': err.args[0]}, status=200)

        # If any other error occurred, re-raise it to trigger a 500 response
        except Exception:
            log.exception("error executing xblock handler")
            raise

    return webob_to_django_response(resp)


def hash_resource(resource):
    """
    Hash a :class:`xblock.fragment.FragmentResource
    """
    md5 = hashlib.md5()
    for data in resource:
        md5.update(repr(data))
    return md5.hexdigest()


def xblock_view(request, course_id, usage_id, view_name):
    """
    Returns the rendered view of a given XBlock, with related resources

    Returns a json object containing two keys:
        html: The rendered html of the view
        resources: A list of tuples where the first element is the resource hash, and
            the second is the resource description
    """
    if not settings.FEATURES.get('ENABLE_XBLOCK_VIEW_ENDPOINT', False):
        log.warn("Attempt to use deactivated XBlock view endpoint -"
                 " see FEATURES['ENABLE_XBLOCK_VIEW_ENDPOINT']")
        raise Http404

    if not request.user.is_authenticated():
        raise PermissionDenied

    try:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    except InvalidKeyError:
        raise Http404("Invalid location")

    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key)
        instance, _ = get_module_by_usage_id(request, course_id, usage_id, course=course)

        try:
            fragment = instance.render(view_name, context=request.GET)
        except NoSuchViewError:
            log.exception("Attempt to render missing view on %s: %s", instance, view_name)
            raise Http404

        hashed_resources = OrderedDict()
        for resource in fragment.resources:
            hashed_resources[hash_resource(resource)] = resource

        return JsonResponse({
            'html': fragment.content,
            'resources': hashed_resources.items(),
            'csrf_token': unicode(csrf(request)['csrf_token']),
        })



def _check_files_limits(files):
    """
    Check if the files in a request are under the limits defined by
    `settings.MAX_FILEUPLOADS_PER_INPUT` and
    `settings.STUDENT_FILEUPLOAD_MAX_SIZE`.

    Returns None if files are correct or an error messages otherwise.
    """
    for fileinput_id in files.keys():
        inputfiles = files.getlist(fileinput_id)

        # Check number of files submitted
        if len(inputfiles) > settings.MAX_FILEUPLOADS_PER_INPUT:
            msg = 'Submission aborted! Maximum %d files may be submitted at once' % \
                  settings.MAX_FILEUPLOADS_PER_INPUT
            return msg

        # Check file sizes
        for inputfile in inputfiles:
            if inputfile.size > settings.STUDENT_FILEUPLOAD_MAX_SIZE:  # Bytes
                msg = 'Submission aborted! Your file "%s" is too large (max size: %d MB)' % \
                      (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE / (1000 ** 2))
                return msg

    return None


# This is just a shim, and should be removed in favor of calling LmsRuntime directly
def get_module_for_descriptor(user, request, descriptor, field_data_cache, course_key,
                              position=None, wrap_xmodule_display=True, grade_bucket_type=None,
                              static_asset_path='', disable_staff_debug_info=False,
                              course=None):

    runtime = LmsRuntime(
        request=request,
        user=user,
        position=position,
        wrap_xmodule_display=wrap_xmodule_display,
        grade_bucket_type=grade_bucket_type,
        static_asset_path=static_asset_path,
        disable_staff_debug_info=disable_staff_debug_info,
        course_id=course_key,
    )

    # This should be converted to runtime.prefetch(...)
    runtime._field_data_cache = field_data_cache

    return runtime.get_module_for_descriptor(descriptor)

# Temporary shim, just load the runtime normally
def get_xqueue_callback_url_prefix(request):
    return LmsRuntime(request).get_xqueue_callback_url_prefix()


def get_module_for_descriptor_internal(user, descriptor, student_data, course_id,  # pylint: disable=invalid-name
                                       track_function, xqueue_callback_url_prefix, request_token,
                                       position=None, wrap_xmodule_display=True, grade_bucket_type=None,
                                       static_asset_path='', user_location=None, disable_staff_debug_info=False,
                                       course=None):
    runtime = LmsRuntime(
        request=None,
        user=user,
        position=position,
        wrap_xmodule_display=wrap_xmodule_display,
        grade_bucket_type=grade_bucket_type,
        static_asset_path=static_asset_path,
        disable_staff_debug_info=disable_staff_debug_info,
        course_id=course_id,
        course=course,
    )

    return runtime.get_module_for_descriptor_without_request(
        descriptor=descriptor,
        student_data=student_data,
        track_function=track_function,
        xqueue_callback_url_prefix=xqueue_callback_url_prefix,
        request_token=request_token,
    )
