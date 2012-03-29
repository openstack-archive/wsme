from sphinx.ext import autodoc
from sphinx.domains.python import PyClasslike, PyClassmember
from sphinx.domains import Domain, ObjType
from sphinx.util.docfields import Field, GroupedField, TypedField

from sphinx.locale import l_, _

from docutils.parsers.rst import Directive

import wsme


class SampleType(object):
    """A Sample Type"""

    #: A Int
    aint = int


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

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        # we don't want to be automaticaly used
        # TODO check if the member is registered a an exposed type
        return False

    def format_name(self):
        return self.object.__name__

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
        self.add_line(u':type: %s' % self.datatype.__name__, '<sphinxext>')
        super(AttributeDocumenter, self).add_content(
            more_content, no_docstring)

    def add_directive_header(self, sig):
        super(AttributeDocumenter, self).add_directive_header(sig)


class WSMEDomain(Domain):
    name = 'wsme'

    directives = {
        'type': TypeDirective,
        'attribute':  AttributeDirective
    }

    object_types = {
        'type': ObjType(l_('type'), 'type', 'obj')
    }


def setup(app):
    app.add_domain(WSMEDomain)
    app.add_autodocumenter(TypeDocumenter)
    app.add_autodocumenter(AttributeDocumenter)
