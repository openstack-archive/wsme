import base64
import datetime
import decimal
import inspect
import weakref


class UserType(object):
    basetype = None

    def validate(self, value):
        return

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
    basetype = str

    def tobasetype(self, value):
        return base64.encodestring(value)

    def frombasetype(self, value):
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
    def __init__(self, basetype, *values):
        self.basetype = basetype
        self.values = set(values)

    def validate(self, value):
        if value not in self.values:
            raise ValueError("Value '%s' is invalid (should be one of: %s)" % (
                value, ', '.join(self.values)))

    def tobasetype(self, value):
        return value

    def frombasetype(self, value):
        return value

pod_types = [str, unicode, int, float, bool]
dt_types = [datetime.date, datetime.time, datetime.datetime]
extra_types = [binary, decimal.Decimal]
native_types = pod_types + dt_types + extra_types

complex_types = []
array_types = []
dict_types = []


class UnsetType(object):
    def __nonzero__(self):
        return False

Unset = UnsetType()


def iscomplex(datatype):
    return inspect.isclass(datatype) \
            and '_wsme_attributes' in datatype.__dict__


def isarray(datatype):
    return isinstance(datatype, list)


def isdict(datatype):
    return isinstance(datatype, dict)


def validate_value(datatype, value):
    if hasattr(datatype, 'validate'):
        return datatype.validate(value)
    else:
        if value is Unset:
            return True
        if value is not None:
            if isarray(datatype):
                if not isinstance(value, list):
                    raise ValueError("Wrong type. Expected '%s', got '%s'" % (
                            datatype, type(value)
                        ))
                for item in value:
                    validate_value(datatype[0], item)
            elif isdict(datatype):
                if not isinstance(value, dict):
                    raise ValueError("Wrong type. Expected '%s', got '%s'" % (
                            datatype, type(value)
                        ))
                key_type = datatype.keys()[0]
                value_type = datatype.values()[0]
                for key, v in value.items():
                    validate_value(key_type, key)
                    validate_value(value_type, v)
            elif datatype in (int, long):
                if not isinstance(value, int) and not isinstance(value, long):
                    raise ValueError(
                        "Wrong type. Expected an integer, got '%s'" % (
                            type(value)
                        ))
            elif not isinstance(value, datatype):
                raise ValueError(
                    "Wrong type. Expected '%s', got '%s'" % (
                        datatype, type(value)
                    ))


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
        #: attribute data type
        self.datatype = datatype
        #: True if the attribute is mandatory
        self.mandatory = mandatory
        #: Default value. The attribute will return this instead
        #: of :data:`Unset` if no value has been set.
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, '_' + self.key, self.default)

    def __set__(self, instance, value):
        try:
            validate_value(self.datatype, value)
        except ValueError, e:
            raise ValueError("%s: %s" % (self.name, e))
        if value is Unset:
            if hasattr(instance, '_' + self.key):
                delattr(instance, '_' + self.key)
        else:
            setattr(instance, '_' + self.key, value)

    def __delete__(self, instance):
        self.__set__(instance, Unset)


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
        attributes.append(attrdef)
        setattr(class_, name, attrdef)

    sort_attributes(class_, attributes)
    return attributes


def register_type(class_):
    """
    Make sure a type is registered.

    It is automatically called by :class:`expose() <wsme.expose>`
    and :class:`validate() <wsme.validate>`.
    Unless you want to control when the class inspection is done there
    is no need to call it.
    """
    if class_ is None or \
            class_ in native_types or \
            isusertype(class_) or iscomplex(class_):
        return

    if isinstance(class_, list):
        if len(class_) != 1:
            raise ValueError("Cannot register type %s" % repr(class_))
        register_type(class_[0])
        if class_[0] not in array_types:
            array_types.append(class_[0])
        return

    if isinstance(class_, dict):
        if len(class_) != 1:
            raise ValueError("Cannot register type %s" % repr(class_))
        key_type, value_type = class_.items()[0]
        if key_type not in pod_types:
            raise ValueError("Dictionnaries key can only be a pod type")
        register_type(value_type)
        if (key_type, value_type) not in dict_types:
            dict_types.append((key_type, value_type))
        return

    class_._wsme_attributes = None
    class_._wsme_attributes = inspect_class(class_)

    complex_types.append(weakref.ref(class_))


def list_attributes(class_):
    """
    Returns a list of a complex type attributes.
    """
    if not hasattr(class_, '_wsme_attributes'):
        register_type(class_)
    return class_._wsme_attributes
