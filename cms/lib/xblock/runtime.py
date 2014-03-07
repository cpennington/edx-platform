"""
XBlock runtime implementations for edX Studio
"""

from django.core.urlresolvers import reverse
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.django import modulestore
from xmodule.x_module import XModuleMixin, XModuleRuntime

from cms.lib.xblock.mixin import CmsBlockMixin
from lms.lib.xblock.mixin import LmsBlockMixin
from lms.lib.xblock.runtime import quote_slashes


class StudioRuntime(XModuleRuntime):
    def __init__(self, **kwargs):
        kwargs['mixins'] = (LmsBlockMixin, CmsBlockMixin, InheritanceMixin, XModuleMixin)
        super(StudioRuntime, self).__init__(**kwargs)

    def get_block(self, usage_id):
        return modulestore().get_item(usage_id)

    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        """
        Handler URL function for Studio
        """

        if thirdparty:
            raise NotImplementedError("edX Studio doesn't support third-party xblock handler urls")

        url = reverse('component_handler', kwargs={
            'usage_id': quote_slashes(unicode(block.scope_ids.usage_id).encode('utf-8')),
            'handler': handler_name,
            'suffix': suffix,
        }).rstrip('/')

        if query:
            url += '?' + query

        return url

    def local_resource_url(self, block, uri):
        """
        local_resource_url for Studio
        """
        return reverse('xblock_resource_url', kwargs={
            'block_type': block.scope_ids.block_type,
            'uri': uri,
        })

    def resource_url(self, resource):
        raise NotImplementedError('Deprecated')

    def publish(self, block, event, custom_user=None):
        """A function that allows XModules to publish events. This only supports grade changes right now."""
        raise NotImplementedError("Studio doesn't know how to publish events")
