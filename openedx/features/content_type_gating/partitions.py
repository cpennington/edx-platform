"""
Define the ContentTypeGatingPartition and ContentTypeGatingPartitionScheme.

These are used together to allow course content to be blocked for a subset
of audit learners.
"""

import logging

from course_modes.models import CourseMode

from django.utils.translation import ugettext_lazy as _

from django.apps import apps
from lms.djangoapps.courseware.masquerade import (
    get_course_masquerade,
    is_masquerading_as_specific_student,
    get_masquerading_user_group,
)
from xmodule.partitions.partitions import Group, UserPartition, UserPartitionError
from openedx.features.course_duration_limits.config import CONTENT_TYPE_GATING_FLAG
from openedx.features.content_type_gating.models import ContentTypeGatingConfig

LOG = logging.getLogger(__name__)

# Studio generates partition IDs starting at 100. There is already a manually generated
# partition for Enrollment Track that uses ID 50, so we'll use 51.
CONTENT_GATING_PARTITION_ID = 51


CONTENT_TYPE_GATE_GROUP_IDS = {
    'limited_access': 1,
    'full_access': 2,
}


def create_content_gating_partition(course):
    """
    Create and return the Content Gating user partition.
    """

    content_type_gating_config = ContentTypeGatingConfig.current(course=course.id)
    if not (CONTENT_TYPE_GATING_FLAG.is_enabled() or content_type_gating_config.enabled_now()):
        return None

    try:
        content_gate_scheme = UserPartition.get_scheme("content_type_gate")
    except UserPartitionError:
        LOG.warning("No 'content_type_gate' scheme registered, ContentTypeGatingPartitionScheme will not be created.")
        return None

    used_ids = set(p.id for p in course.user_partitions)
    if CONTENT_GATING_PARTITION_ID in used_ids:
        # It's possible for course authors to add arbitrary partitions via XML import. If they do, and create a
        # partition with id 51, it will collide with the Content Gating Partition. We'll catch that here, and
        # then fix the course content as needed (or get the course team to).
        LOG.warning(
            "Can't add 'content_type_gate' partition, as ID {id} is assigned to {partition} in course {course}.".format(
                id=CONTENT_GATING_PARTITION_ID,
                partition=_get_partition_from_id(course.user_partitions, CONTENT_GATING_PARTITION_ID).name,
                course=unicode(course.id)
            )
        )
        return None

    partition = content_gate_scheme.create_user_partition(
        id=CONTENT_GATING_PARTITION_ID,
        name=_(u"Feature-based Enrollments"),
        description=_(u"Partition for segmenting users by access to gated content types"),
        parameters={"course_id": unicode(course.id)}
    )
    return partition


class ContentTypeGatingPartition(UserPartition):
    pass


class ContentTypeGatingPartitionScheme(object):
    """
    This scheme implements the Content Type Gating permission partitioning.

    This partitioning is roughly the same as the verified/audit split, but also allows for individual
    schools or courses to specify particular learner subsets by email that are allowed to access
    the gated content despite not being verified users.
    """

    LIMITED_ACCESS = Group(CONTENT_TYPE_GATE_GROUP_IDS['limited_access'], 'Limited-access Users')
    FULL_ACCESS = Group(CONTENT_TYPE_GATE_GROUP_IDS['full_access'], 'Full-access Users')

    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition, **kwargs):  # pylint: disable=unused-argument
        """
        Returns the Group for the specified user.
        """

        # First, check if we have to deal with masquerading.
        # If the current user is masquerading as a specific student, use the
        # same logic as normal to return that student's group. If the current
        # user is masquerading as a generic student in a specific group, then
        # return that group.
        if get_course_masquerade(user, course_key) and not is_masquerading_as_specific_student(user, course_key):
            return get_masquerading_user_group(course_key, user, user_partition)

        # For now, treat everyone as a Full-access user, until we have the rest of the
        # feature gating logic in place.

        if not CONTENT_TYPE_GATING_FLAG.is_enabled():
            return cls.FULL_ACCESS

        # If CONTENT_TYPE_GATING is enabled use the following logic to determine whether a user should have FULL_ACCESS
        # or LIMITED_ACCESS

        course_mode = apps.get_model('course_modes.CourseMode')
        modes = course_mode.modes_for_course(course_key, include_expired=True, only_selectable=False)
        modes_dict = {mode.slug: mode for mode in modes}

        # If there is no verified mode, all users are granted FULL_ACCESS
        if not course_mode.has_verified_mode(modes_dict):
            return cls.FULL_ACCESS

        course_enrollment = apps.get_model('student.CourseEnrollment')

        mode_slug, is_active = course_enrollment.enrollment_mode_for_user(user, course_key)

        if mode_slug and is_active:
            course_mode = course_mode.mode_for_course(
                course_key,
                mode_slug,
                modes=modes,
            )
            if course_mode is None:
                LOG.error(
                    "User %s is in an unknown CourseMode '%s'"
                    " for course %s. Granting full access to content for this user",
                    user.username,
                    mode_slug,
                    course_key,
                )
                return cls.FULL_ACCESS

            if mode_slug == CourseMode.AUDIT:
                return cls.LIMITED_ACCESS
            else:
                return cls.FULL_ACCESS
        else:
            # Unenrolled users don't get gated content
            return cls.LIMITED_ACCESS

    @classmethod
    def create_user_partition(cls, id, name, description, groups=None, parameters=None, active=True):  # pylint: disable=redefined-builtin, invalid-name, unused-argument
        """
        Create a custom UserPartition to support dynamic groups.

        A Partition has an id, name, scheme, description, parameters, and a list
        of groups. The id is intended to be unique within the context where these
        are used. (e.g., for partitions of users within a course, the ids should
        be unique per-course). The scheme is used to assign users into groups.
        The parameters field is used to save extra parameters e.g., location of
        the course ID for this partition scheme.

        Partitions can be marked as inactive by setting the "active" flag to False.
        Any group access rule referencing inactive partitions will be ignored
        when performing access checks.
        """
        return ContentTypeGatingPartition(
            id,
            unicode(name),
            unicode(description),
            [
                cls.LIMITED_ACCESS,
                cls.FULL_ACCESS,
            ],
            cls,
            parameters,
            # N.B. This forces Content Type Gating partitioning to always be active on every course,
            # no matter how the course xml content is set. We will manage enabling/disabling
            # as a policy in the LMS.
            active=True,
        )


def _get_partition_from_id(partitions, user_partition_id):
    """
    Look for a user partition with a matching id in the provided list of partitions.

    Returns:
        A UserPartition, or None if not found.
    """
    for partition in partitions:
        if partition.id == user_partition_id:
            return partition

    return None
