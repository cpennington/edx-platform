from .x_module import XModuleDescriptor, DescriptorService


class MakoDescriptorService(DescriptorService):
    def __init__(self, render_template, **kwargs):
        super(MakoDescriptorService, self).__init__(**kwargs)

        self.render_template = render_template


class MakoModuleDescriptor(XModuleDescriptor):
    """
    Module descriptor intended as a mixin that uses a mako template
    to specify the module html.

    Expects the descriptor to have the `mako_template` attribute set
    with the name of the template to render, and it will pass
    the descriptor as the `module` parameter to that template

    MakoModuleDescriptor.__init__ takes the same arguments as xmodule.x_module:XModuleDescriptor.__init__
    """

    def get_context(self):
        """
        Return the context to render the mako template with
        """
        return {
            'module': self,
            'editable_metadata_fields': self.editable_metadata_fields
        }

    def get_html(self):
        return self.system.render_template(
            self.mako_template, self.get_context())

