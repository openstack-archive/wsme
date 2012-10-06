import base64
import datetime
import decimal
import inspect
import logging
import six
import sys
import weakref

log = logging.getLogger(__name__)

#: The 'str' (python 2) or 'bytes' (python 3) type.
#: Its use should be restricted to
#: pure ascii strings as the protocols will generally not be
#: be able to send non-unicode strings.
#: To transmit binary strings, use the :class:`binary` type
bytes = six.binary_type

#: Unicode string.
text = six.text_type


class ArrayType(object):
    def __init__(self, item_type):
        if iscomplex(item_type):
            self._item_type = weakref.ref(item_type)
        else:
            self._item_type = item_type

    def __hash__(self):
        return hash(self.item_type)

    def __eq__(self, other):
        return self.item_type == other.item_type

    @property
    def item_type(self):
        if isinstance(self._item_type, weakref.ref):
            return self._item_type()
        else:
            return self._item_type

    def validate(self, value):
        if value is None:
            return
        if not isinstance(value, list):
            raise ValueError("Wrong type. Expected '[%s]', got '%s'" % (
                    self.item_type, type(value)
            ))
        return [
            validate_value(self.item_type, item)
            for item in value
        ]


class DictType(object):
    def __init__(self, key_type, value_type):
        if key_type not in pod_types:
            raise ValueError("Dictionnaries key can only be a pod type")
        self.key_type = key_type
        if iscomplex(value_type):
            self._value_type = weakref.ref(value_type)
        else:
            self._value_type = value_type

    def __hash__(self):
        return hash((self.key_type, self.value_type))

    @property
    def value_type(self):
        if isinstance(self._value_type, weakref.ref):
            return self._value_type()
        else:
            return self._value_type

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValueError("Wrong type. Expected '{%s: %s}', got '%s'" % (
                    self.key_type, self.value_type, type(value)
                ))
        return dict((
            (
                validate_value(self.key_type, key),
                validate_value(self.value_type, v)
            ) for key, v in value.items()
        ))


class UserType(object):
    basetype = None
    name = None

    def validate(self, value):
        return value

    def tobasetype(self, value):
        return value

    def frombasetype(self, value):
        return value


def isusertype(class_):
    return isinstance(class_, UserType)


class BinaryType(UserType):
    """
    A user type that use base64 strings to carry binary data.
    """
    basetype = bytes
    name = 'binary'

    def tobasetype(self, value):
        if value is None:
            return None
        return base64.encodestring(value)

    def frombasetype(self, value):
        if value is None:
            return None
        return base64.decodestring(value)

#: The binary almost-native type
binary = BinaryType()


class Enum(UserType):
    """
    A simple enumeration type. Can be based on any non-complex type.

    :param basetype: The actual data type
    :param values: A set of possible values

    If nullable, 'None' should be added the values set.

    Example::

        Gender = Enum(str, 'male', 'female')
        Specie = Enum(str, 'cat', 'dog')

    """
    def __init__(self, basetype, *values, **kw):
        self.basetype = basetype
        self.values = set(values)
        name = kw.pop('name', None)
        if name is None:
            name = "Enum(%s)" % ', '.join((str(v) for v in values))
        self.name = name

    def validate(self, value):
        if value not in self.values:
            raise ValueError("Value '%s' is invalid (should be one of: %s)" % (
                value, ', '.join(self.values)))
        return value

    def tobasetype(self, value):
        return value

    def frombasetype(self, value):
        return value


class UnsetType(object):
    if sys.version < '3':
        def __nonzero__(self):
            return False
    else:
        def __bool__(self):
            return False

Unset = UnsetType()


pod_types = six.integer_types + (
    bytes, text, float, bool)
dt_types = (datetime.date, datetime.time, datetime.datetime)
extra_types = (binary, decimal.Decimal)
native_types = pod_types + dt_types + extra_types


def iscomplex(datatype):
    return inspect.isclass(datatype) \
            and '_wsme_attributes' in datatype.__dict__


def isarray(datatype):
    return isinstance(datatype, ArrayType)


def isdict(datatype):
    return isinstance(datatype, DictType)


def validate_value(datatype, value):
    if hasattr(datatype, 'validate'):
        return datatype.validate(value)
    else:
        if value in (Unset, None):
            return value

        if isinstance(datatype, list):
            datatype = ArrayType(datatype[0])
        if isinstance(datatype, dict):
            datatype = DictType(*list(datatype.items())[0])
        if isarray(datatype):
            datatype.validate(value)
        elif isdict(datatype):
            datatype.validate(value)
        elif datatype in six.integer_types:
            if not isinstance(value, six.integer_types):
                raise ValueError(
                    "Wrong type. Expected an integer, got '%s'" % (
                        type(value)
                    ))
        elif datatype is text and isinstance(value, bytes):
            value = value.decode()
        elif datatype is bytes and isinstance(value, text):
            value = value.encode()
        elif not isinstance(value, datatype):
            raise ValueError(
                "Wrong type. Expected '%s', got '%s'" % (
                    datatype, type(value)
                ))
        return value


class wsproperty(property):
    """
    A specialised :class:`property` to define typed-property on complex types.
    Example::

        class MyComplexType(object):
            def get_aint(self):
                return self._aint

            def set_aint(self, value):
                assert avalue < 10  # Dummy input validation
                self._aint = value

            aint = wsproperty(int, get_aint, set_aint, mandatory=True)
    """
    def __init__(self, datatype, fget, fset=None,
                 mandatory=False, doc=None, name=None):
        property.__init__(self, fget, fset)
        #: The property name in the parent python class
        self.key = None
        #: The attribute name on the public of the api.
        #: Defaults to :attr:`key`
        self.name = name
        #: property data type
        self.datatype = datatype
        #: True if the property is mandatory
        self.mandatory = mandatory


class wsattr(object):
    """
    Complex type attribute definition.

    Example::

        class MyComplexType(object):
            optionalvalue = int
            mandatoryvalue = wsattr(int, mandatory=True)
            named_value = wsattr(int, name='named.value')

    After inspection, the non-wsattr attributes will be replace, and
    the above class will be equivalent to::

        class MyComplexType(object):
            optionalvalue = wsattr(int)
            mandatoryvalue = wsattr(int, mandatory=True)

    """
    def __init__(self, datatype, mandatory=False, name=None, default=Unset):
        #: The attribute name in the parent python class.
        #: Set by :func:`inspect_class`
        self.key = None  # will be set by class inspection
        #: The attribute name on the public of the api.
        #: Defaults to :attr:`key`
        self.name = name
        self._datatype = (datatype,)
        #: True if the attribute is mandatory
        self.mandatory = mandatory
        #: Default value. The attribute will return this instead
        #: of :data:`Unset` if no value has been set.
        self.default = default

        self.complextype = None

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, '_' + self.key, self.default)

    def __set__(self, instance, value):
        try:
            value = validate_value(self.datatype, value)
        except ValueError:
            e = sys.exc_info()[1]
            raise ValueError("%s: %s" % (self.name, e))
        if value is Unset:
            if hasattr(instance, '_' + self.key):
                delattr(instance, '_' + self.key)
        else:
            setattr(instance, '_' + self.key, value)

    def __delete__(self, instance):
        self.__set__(instance, Unset)

    def _get_datatype(self):
        if isinstance(self._datatype, tuple):
            self._datatype = \
                self.complextype().__registry__.resolve_type(self._datatype[0])
        if isinstance(self._datatype, weakref.ref):
            return self._datatype()
        if isinstance(self._datatype, list):
            return [
                item() if isinstance(item, weakref.ref) else item
                for item in self._datatype
            ]
        return self._datatype

    def _set_datatype(self, datatype):
        self._datatype = datatype

    #: attribute data type. Can be either an actual type,
    #: or a type name, in which case the actual type will be
    #: determined when needed (generaly just before scaning the api).
    datatype = property(_get_datatype, _set_datatype)


def iswsattr(attr):
    if inspect.isfunction(attr) or inspect.ismethod(attr):
        return False
    if isinstance(attr, property) and not isinstance(attr, wsproperty):
        return False
    return True


def sort_attributes(class_, attributes):
    """Sort a class attributes list.

    3 mechanisms are attempted :

    #.  Look for a _wsme_attr_order attribute on the class_. This allow
        to define an arbitrary order of the attributes (usefull for
        generated types).

    #.  Access the object source code to find the declaration order.

    #.  Sort by alphabetically"""

    if not len(attributes):
        return

    attrs = dict((a.key, a) for a in attributes)

    if hasattr(class_, '_wsme_attr_order'):
        names_order = class_._wsme_attr_order
    else:
        names = attrs.keys()
        names_order = []
        try:
            lines = []
            for cls in inspect.getmro(class_):
                if cls is object:
                    continue
                lines[len(lines):] = inspect.getsourcelines(cls)[0]
            for line in lines:
                line = line.strip().replace(" ", "")
                if '=' in line:
                    aname = line[:line.index('=')]
                    if aname in names and aname not in names_order:
                        names_order.append(aname)
            if len(names_order) < len(names):
                names_order.extend((
                    name for name in names if name not in names_order))
            assert len(names_order) == len(names)
        except (TypeError, IOError):
            names_order = list(names)
            names_order.sort()

    attributes[:] = [attrs[name] for name in names_order]


def inspect_class(class_):
    """Extract a list of (name, wsattr|wsproperty) for the given class_"""
    attributes = []
    for name, attr in inspect.getmembers(class_, iswsattr):
        if name.startswith('_'):
            continue

        if isinstance(attr, wsattr):
            attrdef = attr
        elif isinstance(attr, wsproperty):
            attrdef = attr
        else:
            if attr not in native_types and (
                    inspect.isclass(attr)
                    or isinstance(attr, list)
                    or isinstance(attr, dict)):
                register_type(attr)
            attrdef = wsattr(attr)

        attrdef.key = name
        if attrdef.name is None:
            attrdef.name = name
        attrdef.complextype = weakref.ref(class_)
        attributes.append(attrdef)
        setattr(class_, name, attrdef)

    sort_attributes(class_, attributes)
    return attributes


def list_attributes(class_):
    """
    Returns a list of a complex type attributes.
    """
    if not iscomplex(class_):
        raise TypeError("%s is not a registered type")
    return class_._wsme_attributes


class Registry(object):
    def __init__(self):
        self.complex_types = []
        self.array_types = set()
        self.dict_types = set()

    def register(self, class_):
        """
        Make sure a type is registered.

        It is automatically called by :class:`expose() <wsme.expose>`
        and :class:`validate() <wsme.validate>`.
        Unless you want to control when the class inspection is done there
        is no need to call it.
        """
        if class_ is None or \
                class_ in native_types or \
                isusertype(class_) or iscomplex(class_) or \
                isarray(class_) or isdict(class_):
            return class_

        if isinstance(class_, list):
            if len(class_) != 1:
                raise ValueError("Cannot register type %s" % repr(class_))
            dt = ArrayType(class_[0])
            self.register(dt.item_type)
            self.array_types.add(dt)
            return dt

        if isinstance(class_, dict):
            if len(class_) != 1:
                raise ValueError("Cannot register type %s" % repr(class_))
            dt = DictType(*list(class_.items())[0])
            self.register(dt.value_type)
            self.dict_types.add(dt)
            return dt

        class_._wsme_attributes = None
        class_._wsme_attributes = inspect_class(class_)

        class_.__registry__ = self
        self.complex_types.append(weakref.ref(class_))
        return class_

    def lookup(self, typename):
        log.debug('Lookup %s' % typename)
        modname = None
        if '.' in typename:
            modname, typename = typename.rsplit('.', 1)
        for ct in self.complex_types:
            ct = ct()
            if ct is not None and typename == ct.__name__ and (
                    modname is None or modname == ct.__module__):
                return ct

    def resolve_type(self, type_):
        if isinstance(type_, six.string_types):
            return self.lookup(type_)
        if isinstance(type_, list):
            type_ = ArrayType(type_[0])
        if isinstance(type_, dict):
            type_ = DictType(list(type_.keys())[0], list(type_.values())[0])
        if isinstance(type_, ArrayType):
            type_ = ArrayType(self.resolve_type(type_.item_type))
            self.array_types.add(type_)
        elif isinstance(type_, DictType):
            type_ = DictType(
                    type_.key_type,
                    self.resolve_type(type_.value_type))
            self.dict_types.add(type_)
        else:
            type_ = self.register(type_)
        return type_

# Default type registry
registry = Registry()


def register_type(class_):
    return registry.register(class_)


class BaseMeta(type):
    def __new__(cls, name, bases, dct):
        if bases[0] is not object and '__registry__' not in dct:
            dct['__registry__'] = registry
        return type.__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        if bases[0] is not object:
            cls.__registry__.register(cls)


class Base(six.with_metaclass(BaseMeta)):
    def __init__(self, **kw):
        for key, value in kw.items():
            if hasattr(self, key):
                setattr(self, key, value)


class File(Base):
    """A complex type that represents a file.

    In the particular case of protocol accepting form encoded data as
    input, File can be loaded from a form file field.
    """
    #: The file name
    filename = wsattr(text)

    #: Mime type of the content
    contenttype = wsattr(text)

    def _get_content(self):
        if self._content is None and self._file:
            self._content = self._file.read()
        return self._content

    def _set_content(self, value):
        self._content = value
        self._file = None

    #: File content
    content = wsproperty(binary, _get_content, _set_content)

    def __init__(self, filename=None, file=None, content=None,
            contenttype=None, fieldstorage=None):
        self.filename = filename
        self.contenttype = contenttype
        self._file = file
        self._content = content

        if fieldstorage is not None:
            if fieldstorage.file:
                self._file = fieldstorage.file
                self.filename = fieldstorage.filename
                self.contenttype = unicode(fieldstorage.type)
            else:
                self._content = fieldstorage.value

    @property
    def file(self):
        if self._file is None and self._content:
            self._file = six.BytesIO(self._content)
        return self._file
