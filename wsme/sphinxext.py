import inspect
import re

from sphinx.ext import autodoc
from sphinx.domains.python import PyClasslike, PyClassmember
from sphinx.domains import Domain, ObjType
from sphinx.util.docfields import Field, GroupedField, TypedField

from sphinx.roles import XRefRole
from sphinx.locale import l_, _

from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives

import wsme

field_re = re.compile(r':(?P<field>\w+)(\s+(?P<name>\w+))?:')


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
    @wsme.validate(SampleType, int, str)
    def change_aint(data, aint, dummy='useless'):
        """
        :param aint: The new value

        :return: The data object with its aint field value changed.
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
    priority = 1

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(parent, ServiceDocumenter) \
            and wsme.api.isfuncproxy(member)

    def import_object(self):
        ret = super(FunctionDocumenter, self).import_object()
        self.directivetype = 'function'
        self.object, self.wsme_fd = \
            wsme.api.FunctionDefinition.get(self.object)
        self.retann = self.wsme_fd.return_type.__name__
        return ret

    def format_args(self):
        args = [arg.name for arg in self.wsme_fd.arguments]
        defaults = [arg.default
            for arg in self.wsme_fd.arguments if not arg.mandatory]
        return inspect.formatargspec(args, defaults=defaults)

    def get_doc(self, encoding=None):
        """Inject the type and param fields into the docstrings so that the
        user can add its own param fields to document the parameters"""
        docstrings = super(FunctionDocumenter, self).get_doc(encoding)
        print docstrings
        found_params = set()

        for si, docstring in enumerate(docstrings):
            for i, line in enumerate(docstring):
                m = field_re.match(line)
                if m and m.group('field') == 'param':
                    found_params.add(m.group('name'))

        next_param_pos = (0, 0)

        for arg in self.wsme_fd.arguments:
            content = [
                u':type  %s: :wsme:type:`%s`' % (
                    arg.name, arg.datatype.__name__)
            ]
            if arg.name not in found_params:
                content.insert(0, u':param %s: ' % (arg.name))
                pos = next_param_pos
            else:
                for si, docstring in enumerate(docstrings):
                    for i, line in enumerate(docstring):
                        m = field_re.match(line)
                        if m and m.group('field') == 'param' \
                                and m.group('name') == arg.name:
                            pos = (si, i + 1)
                            break
                            break
            docstring = docstrings[pos[0]]
            docstring[pos[1]:pos[1]] = content
            next_param_pos = (pos[0], pos[1] + len(content))

        if self.wsme_fd.return_type:
            content = [
                u':rtype: %s' % self.wsme_fd.return_type.__name__
            ]
            pos = None
            for si, docstring in enumerate(docstrings):
                for i, line in enumerate(docstring):
                    m = field_re.match(line)
                    if m and m.group('field') == 'return':
                        pos = (si, i + 1)
                        break
                        break
            if pos is None:
                pos = next_param_pos
            docstring = docstrings[pos[0]]
            docstring[pos[1]:pos[1]] = content
        return docstrings

    def add_content(self, more_content, no_docstring=False):
        super(FunctionDocumenter, self).add_content(more_content, no_docstring)


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

    roles = {
        'type': XRefRole()
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
