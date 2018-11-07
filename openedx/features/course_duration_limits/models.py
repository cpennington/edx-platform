"""
Course Duration Limit Configuration Models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _
from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel


class CourseDurationLimitConfig(StackedConfigurationModel):

    STACKABLE_FIELDS = ('enabled', 'enabled_as_of')

    enabled_as_of = models.DateField(default=None, null=True, verbose_name=_('Enabled As Of'))
