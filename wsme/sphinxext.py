from sphinx.ext import autodoc
from sphinx.domains.python import PyClasslike, PyClassmember
from sphinx.domains import Domain, ObjType
from sphinx.util.docfields import Field, GroupedField, TypedField

from sphinx.locale import l_, _

from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives

import wsme


class SampleType(object):
    """A Sample Type"""

    #: A Int
    aint = int

    def __init__(self, aint=None):
        if aint:
            self.aint = aint

    @classmethod
    def sample(cls):
        return SampleType(10)


class SampleService(wsme.WSRoot):
    @wsme.expose(SampleType)
    @wsme.validate(SampleType, int)
    def change_aint(data, aint):
        """
        Returns the data object with its aint fields changed
        """
        data.aint = aint
        return data


class TypeDirective(PyClasslike):
    pass


class AttributeDirective(PyClassmember):
    doc_field_types = [
        Field('datatype', label=l_('Type'), has_arg=False,
            names=('type', 'datatype'))
    ]


class TypeDocumenter(autodoc.ClassDocumenter):
    objtype = 'type'
    directivetype = 'type'
    domain = 'wsme'

    required_arguments = 1

    option_spec = dict(autodoc.ClassDocumenter.option_spec, **{
        'protocols': lambda l: [v.strip() for v in l.split(',')]
    })

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        # we don't want to be automaticaly used
        # TODO check if the member is registered a an exposed type
        return False

    def format_name(self):
        return self.object.__name__

    def format_signature(self):
        return u''

    def add_directive_header(self, sig):
        super(TypeDocumenter, self).add_directive_header(sig)
        # remove the :module: option that was added by ClassDocumenter
        if ':module:' in self.directive.result[-1]:
            self.directive.result.pop()

    def import_object(self):
        if super(TypeDocumenter, self).import_object():
            wsme.types.register_type(self.object)
            return True
        else:
            return False

    def add_content(self, more_content, no_docstring=False):
        protocols = self.options.protocols or self.env.app.config.wsme_protocols
        protocols = [wsme.protocols.getprotocol(p) for p in protocols]
        content = []
        if protocols:
            sample_obj = getattr(self.object, 'sample', self.object)()
            content.extend([
                l_(u'Data samples:'),
                u'',
                u'.. cssclass:: toggle',
                u''
            ])
            for protocol in protocols:
                language, sample = protocol.encode_sample_value(
                    self.object, sample_obj, format=True)
                content.extend([
                    protocol.displayname or protocol.name,
                    u'    .. code-block:: ' + language,
                    u'',
                ])
                content.extend((
                    u' ' * 8 + line for line in sample.split('\n')))
        for line in content:
            self.add_line(line, u'<wsme.sphinxext')

        self.add_line(u'', '<wsme.sphinxext>')
        super(TypeDocumenter, self).add_content(
            more_content, no_docstring)


class AttributeDocumenter(autodoc.AttributeDocumenter):
    datatype = None
    domain = 'wsme'

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(parent, TypeDocumenter)

    def import_object(self):
        success = super(AttributeDocumenter, self).import_object()
        if success:
            self.datatype = self.object.datatype
        return success

    def add_content(self, more_content, no_docstring=False):
        self.add_line(u':type: %s' % self.datatype.__name__, '<wsme.sphinxext>')
        self.add_line(u'', '<wsme.sphinxext>')
        super(AttributeDocumenter, self).add_content(
            more_content, no_docstring)

    def add_directive_header(self, sig):
        super(AttributeDocumenter, self).add_directive_header(sig)


class RootDirective(Directive):
    """
    This directive is to tell what class is the Webservice root
    """
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'webpath': directives.unchanged
    }

    def run(self):
        env = self.state.document.settings.env
        rootpath = self.arguments[0].strip()
        env.temp_data['wsme:root'] = rootpath
        return []


class ServiceDirective(PyClasslike):
    name = 'service'


class ServiceDocumenter(autodoc.ClassDocumenter):
    domain = 'wsme'
    objtype = 'service'
    directivetype = 'service'

    def add_directive_header(self, sig):
        super(ServiceDocumenter, self).add_directive_header(sig)
        # remove the :module: option that was added by ClassDocumenter
        if ':module:' in self.directive.result[-1]:
            self.directive.result.pop()

    def format_signature(self):
        return u''


class FunctionDirective(PyClassmember):
    name = 'function'
    objtype = 'function'

    def get_signature_prefix(self, sig):
        return 'function '


class FunctionDocumenter(autodoc.MethodDocumenter):
    domain = 'wsme'
    directivetype = 'function'
    objtype = 'function'

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(parent, ServiceDocumenter) \
            and wsme.api.isfuncproxy(member)


class WSMEDomain(Domain):
    name = 'wsme'

    directives = {
        'type': TypeDirective,
        'attribute':  AttributeDirective,
        'service': ServiceDirective,
        'root': RootDirective,
        'function': FunctionDirective,
    }

    object_types = {
        'type': ObjType(l_('type'), 'type', 'obj'),
        'service': ObjType(l_('service'), 'service', 'obj')
    }


def setup(app):
    app.add_domain(WSMEDomain)
    app.add_autodocumenter(TypeDocumenter)
    app.add_autodocumenter(AttributeDocumenter)
    app.add_autodocumenter(ServiceDocumenter)
    app.add_autodocumenter(FunctionDocumenter)

    app.add_config_value('wsme_protocols', ['restjson', 'restxml'], 'env')
    app.add_javascript('toggle.js')
    app.add_stylesheet('toggle.css')
