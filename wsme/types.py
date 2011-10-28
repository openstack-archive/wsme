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


class UnsetType(object):
    pass

Unset = UnsetType()


def iscomplex(datatype):
    return hasattr(datatype, '_wsme_attributes')


def validate_value(datatype, value):
    print datatype
    if hasattr(datatype, 'validate'):
        return datatype.validate(value)
    else:
        if value is not None and not isinstance(value, datatype):
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
                 mandatory=False, doc=None):
        property.__init__(self, fget, fset)
        self.key = None
        self.datatype = datatype
        self.mandatory = mandatory


class wsattr(object):
    """
    Complex type attribute definition.

    Example::

        class MyComplexType(object):
            optionalvalue = int
            mandatoryvalue = wsattr(int, mandatory=True)

    After inspection, the non-wsattr attributes will be replace, and
    the above class will be equivalent to::

        class MyComplexType(object):
            optionalvalue = wsattr(int)
            mandatoryvalue = wsattr(int, mandatory=True)

    """
    def __init__(self, datatype, mandatory=False):
        self.key = None  # will be set by class inspection
        self.datatype = datatype
        self.mandatory = mandatory

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, '_' + self.key, Unset)

    def __set__(self, instance, value):
        validate_value(self.datatype, value)
        setattr(instance, '_' + self.key, value)

    def __delete__(self, instance):
        delattr(instance, '_' + self.key)


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
                    inspect.isclass(attr) or isinstance(attr, list)):
                register_type(attr)
            attrdef = wsattr(attr)

        attrdef.key = name
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
        array_types.append(class_[0])
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
