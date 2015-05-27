import base64
import datetime
import decimal
import inspect
import logging
import netaddr
import re
import six
import sys
import uuid
import weakref

from wsme import exc

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
        return isinstance(other, ArrayType) \
            and self.item_type == other.item_type

    def sample(self):
        return [getattr(self.item_type, 'sample', self.item_type)()]

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
            raise ValueError("Dictionaries key can only be a pod type")
        self.key_type = key_type
        if iscomplex(value_type):
            self._value_type = weakref.ref(value_type)
        else:
            self._value_type = value_type

    def __hash__(self):
        return hash((self.key_type, self.value_type))

    def sample(self):
        key = getattr(self.key_type, 'sample', self.key_type)()
        value = getattr(self.value_type, 'sample', self.value_type)()
        return {key: value}

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


class IntegerType(UserType):
    """
    A simple integer type. Can validate a value range.

    :param minimum: Possible minimum value
    :param maximum: Possible maximum value

    Example::

        Price = IntegerType(minimum=1)

    """
    basetype = int
    name = "integer"

    def __init__(self, minimum=None, maximum=None):
        self.minimum = minimum
        self.maximum = maximum

    @staticmethod
    def frombasetype(value):
        return int(value) if value is not None else None

    def validate(self, value):
        if self.minimum is not None and value < self.minimum:
            error = 'Value should be greater or equal to %s' % self.minimum
            raise ValueError(error)

        if self.maximum is not None and value > self.maximum:
            error = 'Value should be lower or equal to %s' % self.maximum
            raise ValueError(error)

        return value


class StringType(UserType):
    """
    A simple string type. Can validate a length and a pattern.

    :param min_length: Possible minimum length
    :param max_length: Possible maximum length
    :param pattern: Possible string pattern

    Example::

        Name = StringType(min_length=1, pattern='^[a-zA-Z ]*$')

    """
    basetype = six.string_types
    name = "string"

    def __init__(self, min_length=None, max_length=None, pattern=None):
        self.min_length = min_length
        self.max_length = max_length
        if isinstance(pattern, six.string_types):
            self.pattern = re.compile(pattern)
        else:
            self.pattern = pattern

    def validate(self, value):
        if not isinstance(value, self.basetype):
            error = 'Value should be string'
            raise ValueError(error)

        if self.min_length is not None and len(value) < self.min_length:
            error = 'Value should have a minimum character requirement of %s' \
                    % self.min_length
            raise ValueError(error)

        if self.max_length is not None and len(value) > self.max_length:
            error = 'Value should have a maximum character requirement of %s' \
                    % self.max_length
            raise ValueError(error)

        if self.pattern is not None and not self.pattern.search(value):
            error = 'Value should match the pattern %s' % self.pattern.pattern
            raise ValueError(error)

        return value


class IPv4AddressType(UserType):
    """
    A simple IPv4 type.
    """
    basetype = six.string_types
    name = "ipv4address"

    @staticmethod
    def validate(value):
        try:
            netaddr.IPAddress(value, version=4, flags=netaddr.INET_PTON)
        except netaddr.AddrFormatError:
            error = 'Value should be IPv4 format'
            raise ValueError(error)
        else:
            return value


class IPv6AddressType(UserType):
    """
    A simple IPv6 type.

    This type represents IPv6 addresses in the short format.
    """
    basetype = six.string_types
    name = "ipv6address"

    @staticmethod
    def validate(value):
        try:
            netaddr.IPAddress(value, version=6, flags=netaddr.INET_PTON)
        except netaddr.AddrFormatError:
            error = 'Value should be IPv6 format'
            raise ValueError(error)
        else:
            return value


class UuidType(UserType):
    """
    A simple UUID type.

    This type allows not only UUID having dashes but also UUID not
    having dashes. For example, '6a0a707c-45ef-4758-b533-e55adddba8ce'
    and '6a0a707c45ef4758b533e55adddba8ce' are distinguished as valid.
    """
    basetype = six.string_types
    name = "uuid"

    @staticmethod
    def validate(value):
        try:
            return six.text_type((uuid.UUID(value)))
        except (TypeError, ValueError, AttributeError):
            error = 'Value should be UUID format'
            raise ValueError(error)


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
            name = "Enum(%s)" % ', '.join((six.text_type(v) for v in values))
        self.name = name

    def validate(self, value):
        if value not in self.values:
            raise ValueError("Value should be one of: %s" %
                             ', '.join(map(six.text_type, self.values)))
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

    def __repr__(self):
        return 'Unset'

Unset = UnsetType()

#: A special type that corresponds to the host framework request object.
#: It can only be used in the function parameters, and if so the request object
#: of the host framework will be passed to the function.
HostRequest = object()


pod_types = six.integer_types + (
    bytes, text, float, bool)
dt_types = (datetime.date, datetime.time, datetime.datetime)
extra_types = (binary, decimal.Decimal)
native_types = pod_types + dt_types + extra_types
# The types for which we allow promotion to certain numbers.
_promotable_types = six.integer_types + (text, bytes)


def iscomplex(datatype):
    return inspect.isclass(datatype) \
        and '_wsme_attributes' in datatype.__dict__


def isarray(datatype):
    return isinstance(datatype, ArrayType)


def isdict(datatype):
    return isinstance(datatype, DictType)


def validate_value(datatype, value):
    if value in (Unset, None):
        return value

    # Try to promote the data type to one of our complex types.
    if isinstance(datatype, list):
        datatype = ArrayType(datatype[0])
    elif isinstance(datatype, dict):
        datatype = DictType(*list(datatype.items())[0])

    # If the datatype has its own validator, use that.
    if hasattr(datatype, 'validate'):
        return datatype.validate(value)

    # Do type promotion/conversion and data validation for builtin
    # types.
    v_type = type(value)
    if datatype in six.integer_types:
        if v_type in _promotable_types:
            try:
                # Try to turn the value into an int
                value = datatype(value)
            except ValueError:
                # An error is raised at the end of the function
                # when the types don't match.
                pass
    elif datatype is float and v_type in _promotable_types:
        try:
            value = float(value)
        except ValueError:
            # An error is raised at the end of the function
            # when the types don't match.
            pass
    elif datatype is text and isinstance(value, bytes):
        value = value.decode()
    elif datatype is bytes and isinstance(value, text):
        value = value.encode()

    if not isinstance(value, datatype):
        raise ValueError(
            "Wrong type. Expected '%s', got '%s'" % (
                datatype, v_type
            ))
    return value


class wsproperty(property):
    """
    A specialised :class:`property` to define typed-property on complex types.
    Example::

        class MyComplexType(wsme.types.Base):
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

        class MyComplexType(wsme.types.Base):
            optionalvalue = int
            mandatoryvalue = wsattr(int, mandatory=True)
            named_value = wsattr(int, name='named.value')

    After inspection, the non-wsattr attributes will be replaced, and
    the above class will be equivalent to::

        class MyComplexType(wsme.types.Base):
            optionalvalue = wsattr(int)
            mandatoryvalue = wsattr(int, mandatory=True)

    """
    def __init__(self, datatype, mandatory=False, name=None, default=Unset,
                 readonly=False):
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
        #: If True value cannot be set from json/xml input data
        self.readonly = readonly

        self.complextype = None

    def _get_dataholder(self, instance):
        dataholder = getattr(instance, '_wsme_dataholder', None)
        if dataholder is None:
            dataholder = instance._wsme_DataHolderClass()
            instance._wsme_dataholder = dataholder
        return dataholder

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(
            self._get_dataholder(instance),
            self.key,
            self.default
        )

    def __set__(self, instance, value):
        try:
            value = validate_value(self.datatype, value)
        except ValueError as e:
            raise exc.InvalidInput(self.name, value, six.text_type(e))
        dataholder = self._get_dataholder(instance)
        if value is Unset:
            if hasattr(dataholder, self.key):
                delattr(dataholder, self.key)
        else:
            setattr(dataholder, self.key, value)

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
    #: determined when needed (generally just before scanning the api).
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
        to define an arbitrary order of the attributes (useful for
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
        if inspect.isroutine(attr):
            continue

        if isinstance(attr, (wsattr, wsproperty)):
            attrdef = attr
        else:
            if attr not in native_types and (
                    inspect.isclass(attr) or
                    isinstance(attr, (list, dict))):
                register_type(attr)
            attrdef = getattr(class_, '__wsattrclass__', wsattr)(attr)

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


def make_dataholder(class_):
    # the slots are computed outside the class scope to avoid
    # 'attr' to pullute the class namespace, which leads to weird
    # things if one of the slots is named 'attr'.
    slots = [attr.key for attr in class_._wsme_attributes]

    class DataHolder(object):
        __slots__ = slots

    DataHolder.__name__ = class_.__name__ + 'DataHolder'
    return DataHolder


class Registry(object):
    def __init__(self):
        self._complex_types = []
        self.array_types = set()
        self.dict_types = set()

    @property
    def complex_types(self):
        return [t() for t in self._complex_types if t()]

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
        class_._wsme_DataHolderClass = make_dataholder(class_)

        class_.__registry__ = self
        self._complex_types.append(weakref.ref(class_))
        return class_

    def reregister(self, class_):
        """Register a type which may already have been registered.
        """
        self._unregister(class_)
        return self.register(class_)

    def _unregister(self, class_):
        """Remove a previously registered type.
        """
        # Clear the existing attribute reference so it is rebuilt if
        # the class is registered again later.
        if hasattr(class_, '_wsme_attributes'):
            del class_._wsme_attributes
        # FIXME(dhellmann): This method does not recurse through the
        # types like register() does. Should it?
        if isinstance(class_, list):
            at = ArrayType(class_[0])
            try:
                self.array_types.remove(at)
            except KeyError:
                pass
        elif isinstance(class_, dict):
            key_type, value_type = list(class_.items())[0]
            self.dict_types = set(
                dt for dt in self.dict_types
                if (dt.key_type, dt.value_type) != (key_type, value_type)
            )
        # We can't use remove() here because the items in
        # _complex_types are weakref objects pointing to the classes,
        # so we can't compare with them directly.
        self._complex_types = [
            ct for ct in self._complex_types
            if ct() is not class_
        ]

    def lookup(self, typename):
        log.debug('Lookup %s' % typename)
        modname = None
        if '.' in typename:
            modname, typename = typename.rsplit('.', 1)
        for ct in self._complex_types:
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
                self.resolve_type(type_.value_type)
            )
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
        if bases and bases[0] is not object and '__registry__' not in dct:
            dct['__registry__'] = registry
        return type.__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        if bases and bases[0] is not object and cls.__registry__:
            cls.__registry__.register(cls)


class Base(six.with_metaclass(BaseMeta)):
    """Base type for complex types"""
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
                self.contenttype = text(fieldstorage.type)
            else:
                self._content = fieldstorage.value

    @property
    def file(self):
        if self._file is None and self._content:
            self._file = six.BytesIO(self._content)
        return self._file


class DynamicBase(Base):
    """Base type for complex types for which all attributes are not
    defined when the class is constructed.

    This class is meant to be used as a base for types that have
    properties added after the main class is created, such as by
    loading plugins.

    """

    @classmethod
    def add_attributes(cls, **attrs):
        """Add more attributes

        The arguments should be valid Python attribute names
        associated with a type for the new attribute.

        """
        for n, t in attrs.items():
            setattr(cls, n, t)
        cls.__registry__.reregister(cls)
