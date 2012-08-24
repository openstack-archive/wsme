import inspect
import re
import sys

from sphinx import addnodes
from sphinx.ext import autodoc
from sphinx.domains.python import PyClasslike, PyClassmember
from sphinx.domains import Domain, ObjType
from sphinx.directives import ObjectDescription
from sphinx.util.docfields import Field
from sphinx.util.nodes import make_refnode

from sphinx.roles import XRefRole
from sphinx.locale import l_, _

from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives

import wsme
import wsme.types

field_re = re.compile(r':(?P<field>\w+)(\s+(?P<name>\w+))?:')


def datatypename(datatype):
    if isinstance(datatype, wsme.types.UserType):
        return datatype.name
    return datatype.__name__


def make_sample_object(datatype):
    if datatype is wsme.types.bytes:
        return 'samplestring'
    if datatype is wsme.types.text:
        return u'sample unicode'
    if datatype is int:
        return 5
    sample_obj = getattr(datatype, 'sample', datatype)()
    return sample_obj


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


def getroot(env, force=False):
    root = env.temp_data.get('wsme:root')
    if not force and root:
        return root
    rootpath = env.temp_data.get('wsme:rootpath', env.app.config.wsme_root)

    if rootpath is None:
        return None

    modname, classname = rootpath.rsplit('.', 1)
    __import__(modname)
    module = sys.modules[modname]
    root = getattr(module, classname)
    env.temp_data['wsme:root'] = root
    return root


def scan_services(service, path=[]):
    has_functions = False
    for name in dir(service):
        if name.startswith('_'):
            continue
        a = getattr(service, name)
        if inspect.ismethod(a):
            if hasattr(a, '_wsme_definition'):
                has_functions = True
        if inspect.isclass(a):
            continue
        if len(path) > wsme.api.APIPATH_MAXLEN:
            raise ValueError("Path is too long: " + str(path))
        for value in scan_services(a, path + [name]):
            yield value
    if has_functions:
        yield service, path


def find_service_path(env, service):
    root = getroot(env)
    if service == root:
        return []
    for s, path in scan_services(root):
        if s == service:
            return path
    return None


class TypeDirective(PyClasslike):
    def get_index_text(self, modname, name_cls):
        return _('%s (webservice type)') % name_cls[0]

    def add_target_and_index(self, name_cls, sig, signode):
        ret = super(TypeDirective, self).add_target_and_index(name_cls, sig, signode)
        name = name_cls[0]
        types = self.env.domaindata['wsme']['types']
        if name in types:
            self.state_machine.reporter.warning(
                'duplicate type description of %s ' % name)
        types[name] = self.env.docname
        return ret


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
        # TODO check if the member is registered an an exposed type
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
            sample_obj = make_sample_object(self.object)
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
        self.add_line(
            u':type: %s' % datatypename(self.datatype),
            '<wsme.sphinxext>'
        )
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
        env.temp_data['wsme:rootpath'] = rootpath
        if 'wsme:root' in env.temp_data:
            del env.temp_data['wsme:root']
        if 'webpath' in self.options:
            env.temp_data['wsme:webpath'] = self.options['webpath']
        return []


class ServiceDirective(ObjectDescription):
    name = 'service'

    optional_arguments = 1

    def handle_signature(self, sig, signode):
        path = sig.split('/')

        namespace = '/'.join(path[:-1])
        if namespace and not namespace.endswith('/'):
            namespace += '/'

        servicename = path[-1]

        if not namespace and not servicename:
            servicename = '/'

        signode += addnodes.desc_annotation('service ', 'service ')

        if namespace:
            signode += addnodes.desc_addname(namespace, namespace)

        signode += addnodes.desc_name(servicename, servicename)

        return sig


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

    def format_name(self):
        path = find_service_path(self.env, self.object)
        return '/' + '/'.join(path)


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
        found_params = set()

        protocols = self.options.protocols or self.env.app.config.wsme_protocols
        protocols = [wsme.protocols.getprotocol(p) for p in protocols]

        for si, docstring in enumerate(docstrings):
            for i, line in enumerate(docstring):
                m = field_re.match(line)
                if m and m.group('field') == 'param':
                    found_params.add(m.group('name'))

        next_param_pos = (0, 0)

        for arg in self.wsme_fd.arguments:
            content = [
                u':type  %s: :wsme:type:`%s`' % (
                    arg.name, datatypename(arg.datatype))
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

        codesamples = []

        if protocols:
            params = []
            for arg in self.wsme_fd.arguments:
                params.append((arg.name, arg.datatype,
                    make_sample_object(arg.datatype)))
            codesamples.extend([
                u':%s:' % l_(u'Parameters samples'),
                u'    .. cssclass:: toggle',
                u''
            ])
            for protocol in protocols:
                language, sample = protocol.encode_sample_params(
                    params, format=True)
                codesamples.extend([
                    u' ' * 4 + (protocol.displayname or protocol.name),
                    u'        .. code-block:: ' + language,
                    u'',
                ])
                codesamples.extend((
                    u' ' * 12 + line for line in sample.split('\n')))

            if self.wsme_fd.return_type:
                codesamples.extend([
                    u':%s:' % l_(u'Return samples'),
                    u'    .. cssclass:: toggle',
                    u''
                ])
                sample_obj = make_sample_object(self.wsme_fd.return_type)
                for protocol in protocols:
                    language, sample = protocol.encode_sample_result(
                        self.wsme_fd.return_type, sample_obj, format=True)
                    codesamples.extend([
                        u' ' * 4 + protocol.displayname or protocol.name,
                        u'        .. code-block:: ' + language,
                        u'',
                    ])
                    codesamples.extend((
                        u' ' * 12 + line for line in sample.split('\n')))

        docstrings[0:0] = [codesamples]
        return docstrings

    def add_content(self, more_content, no_docstring=False):
        super(FunctionDocumenter, self).add_content(more_content, no_docstring)

    def format_name(self):
        return self.wsme_fd.name

    def add_directive_header(self, sig):
        super(FunctionDocumenter, self).add_directive_header(sig)
        # remove the :module: option that was added by ClassDocumenter
        if ':module:' in self.directive.result[-1]:
            self.directive.result.pop()


class WSMEDomain(Domain):
    name = 'wsme'
    label = 'WSME'

    object_types = {
        'type': ObjType(l_('type'), 'type', 'obj'),
        'service': ObjType(l_('service'), 'service', 'obj')
    }

    directives = {
        'type': TypeDirective,
        'attribute':  AttributeDirective,
        'service': ServiceDirective,
        'root': RootDirective,
        'function': FunctionDirective,
    }

    roles = {
        'type': XRefRole()
    }

    initial_data = {
        'types': {},  # fullname -> docname
    }

    def clear_doc(self, docname):
        for name, value in self.data['types'].items():
            if value == docname:
                del self.data['types'][name]


    def resolve_xref(self, env, fromdocname, builder,
                     type, target, node, contnode):
        if target not in self.data['types']:
            return None
        todocname = self.data['types'][target]
        return make_refnode(
            builder, fromdocname, todocname, target, contnode, target)


def setup(app):
    app.add_domain(WSMEDomain)
    app.add_autodocumenter(TypeDocumenter)
    app.add_autodocumenter(AttributeDocumenter)
    app.add_autodocumenter(ServiceDocumenter)
    app.add_autodocumenter(FunctionDocumenter)

    app.add_config_value('wsme_root', None, 'env')
    app.add_config_value('wsme_webpath', '/', 'env')
    app.add_config_value('wsme_protocols', ['restjson', 'restxml'], 'env')
    app.add_javascript('toggle.js')
    app.add_stylesheet('toggle.css')
