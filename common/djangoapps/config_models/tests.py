"""
Tests of ConfigurationModel
"""

import ddt
from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase
from freezegun import freeze_time

from mock import patch
from config_models.models import ConfigurationModel


class ExampleConfig(ConfigurationModel):
    """
    Test model for testing ``ConfigurationModels``.
    """
    cache_timeout = 300

    string_field = models.TextField()
    int_field = models.IntegerField(default=10)


@patch('config_models.models.cache')
class ConfigurationModelTests(TestCase):
    """
    Tests of ConfigurationModel
    """
    def setUp(self):
        self.user = User()
        self.user.save()

    def test_cache_deleted_on_save(self, mock_cache):
        ExampleConfig(changed_by=self.user).save()
        mock_cache.delete.assert_called_with(ExampleConfig.cache_key_name())

    def test_cache_key_name(self, _mock_cache):
        self.assertEquals(ExampleConfig.cache_key_name(), 'configuration/ExampleConfig/current')

    def test_no_config_empty_cache(self, mock_cache):
        mock_cache.get.return_value = None

        current = ExampleConfig.current()
        self.assertEquals(current.int_field, 10)
        self.assertEquals(current.string_field, '')
        mock_cache.set.assert_called_with(ExampleConfig.cache_key_name(), current, 300)

    def test_no_config_full_cache(self, mock_cache):
        current = ExampleConfig.current()
        self.assertEquals(current, mock_cache.get.return_value)

    def test_config_ordering(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            first = ExampleConfig(changed_by=self.user)
            first.string_field = 'first'
            first.save()

        second = ExampleConfig(changed_by=self.user)
        second.string_field = 'second'
        second.save()

        self.assertEquals(ExampleConfig.current().string_field, 'second')

    def test_cache_set(self, mock_cache):
        mock_cache.get.return_value = None

        first = ExampleConfig(changed_by=self.user)
        first.string_field = 'first'
        first.save()

        ExampleConfig.current()

        mock_cache.set.assert_called_with(ExampleConfig.cache_key_name(), first, 300)


class ExampleKeyedConfig(ExampleConfig):
    """
    Test model for testing ``ConfigurationModels`` with keyed configuration.
    """

    KEY_FIELDS = ('left', 'right')

    left = models.CharField(max_length=30)
    right = models.CharField(max_length=30)


@ddt.ddt
@patch('config_models.models.cache')
class KeyedConfigurationModelTests(TestCase):

    def setUp(self):
        self.user = User()
        self.user.save()

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_cache_key_name(self, left, right, _mock_cache):
        self.assertEquals(ExampleKeyedConfig.cache_key_name(left, right), 'configuration/ExampleKeyedConfig/current/{!r},{!r}'.format(left, right))

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_no_config_empty_cache(self, left, right, mock_cache):
        mock_cache.get.return_value = None

        current = ExampleKeyedConfig.current(left, right)
        self.assertEquals(current.int_field, 10)
        self.assertEquals(current.string_field, '')
        mock_cache.set.assert_called_with(ExampleKeyedConfig.cache_key_name(left, right), current, 300)

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_no_config_full_cache(self, left, right, mock_cache):
        current = ExampleKeyedConfig.current(left, right)
        self.assertEquals(current, mock_cache.get.return_value)

    def test_config_ordering(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(
                changed_by=self.user,
                left='left_a',
                right='right_a',
                string_field='first_a',
            ).save()

            ExampleKeyedConfig(
                changed_by=self.user,
                left='left_b',
                right='right_b',
                string_field='first_b',
            ).save()

        ExampleKeyedConfig(
            changed_by=self.user,
            left='left_a',
            right='right_a',
            string_field='second_a',
        ).save()
        ExampleKeyedConfig(
            changed_by=self.user,
            left='left_b',
            right='right_b',
            string_field='second_b',
        ).save()

        self.assertEquals(ExampleKeyedConfig.current('left_a', 'right_a').string_field, 'second_a')
        self.assertEquals(ExampleKeyedConfig.current('left_b', 'right_b').string_field, 'second_b')

    def test_cache_set(self, mock_cache):
        mock_cache.get.return_value = None

        first = ExampleKeyedConfig(
            changed_by=self.user,
            left='left',
            right='right',
            string_field='first',
        )
        first.save()

        ExampleKeyedConfig.current('left', 'right')

        mock_cache.set.assert_called_with(ExampleKeyedConfig.cache_key_name('left', 'right'), first, 300)