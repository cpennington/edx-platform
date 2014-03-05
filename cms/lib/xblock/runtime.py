"""
XBlock runtime implementations for edX Studio
"""

from django.core.urlresolvers import reverse
from xblock.runtime import Runtime
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.x_module import XModuleMixin

from cms.lib.xblock.mixin import CmsBlockMixin
from lms.lib.xblock.mixin import LmsBlockMixin
from lms.lib.xblock.runtime import quote_slashes


class StudioRuntime(Runtime):
    def __init__(self, request, **kwargs):
        kwargs['mixins'] = (LmsBlockMixin, CmsBlockMixin, InheritanceMixin, XModuleMixin)
        super(StudioRuntime, self).__init__(**kwargs)
        self.request = request

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
