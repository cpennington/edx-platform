# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from .models import CourseDurationLimitConfig


admin.site.register(CourseDurationLimitConfig, ConfigurationModelAdmin)
