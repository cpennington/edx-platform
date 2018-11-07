"""
Content Type Gating Configuration Models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from django.db import models
from django.utils.translation import ugettext as _

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel


class ContentTypeGatingConfig(StackedConfigurationModel):

    STACKABLE_FIELDS = ('enabled', 'enabled_as_of', 'studio_override_enabled')

    enabled_as_of = models.DateField(default=None, null=True, verbose_name=_('Enabled As Of'))
    studio_override_enabled = models.NullBooleanField(default=None, verbose_name=_('Studio Override Enabled'))

    def enabled_for_enrollment(self, enrollment=None, user=None, course_key=None):
        if enrollment is not None and (user is not None or course_key is not None):
            raise ValueError('Specify enrollment or user/course_key, but not both')

        if enrollment is None and (user is None or course_key is None):
            raise ValueError('Both user and course_key must be specified if no enrollment is provided')

        if course_key is None:
            course_key = enrollment.course_id

        if enrollment is None:
            enrollment = CourseEnrollment.get_enrollment()

        current_config = self.current(course=course_key)
        return current_config.enabled and current_config.enabled_as_of <= enrollment.created

    def enabled_now(self, now=None):
        if now is None:
            now = datetime.utcnow()

        return self.enabled and self.enabled_as_of <= now
