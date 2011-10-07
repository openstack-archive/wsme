import datetime
import decimal
import weakref
import inspect

binary = object()

pod_types = [str, unicode, int, float, bool]
dt_types = [datetime.date, datetime.time, datetime.datetime]
extra_types = [binary, decimal.Decimal]
native_types = pod_types + dt_types + extra_types

complex_types = []
array_types = []


def iscomplex(datatype):
    return hasattr(datatype, '_wsme_attributes')


class wsproperty(property):
    def __init__(self, datatype, fget, fset=None,
                 mandatory=False, doc=None):
        property.__init__(self, fget, fset)
        self.datatype = datatype
        self.mandatory = mandatory


class wsattr(object):
    def __init__(self, datatype, mandatory=False):
        self.datatype = datatype
        self.mandatory = mandatory


def iswsattr(attr):
    if inspect.isfunction(attr) or inspect.ismethod(attr):
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

    attrs = dict(attributes)

    if hasattr(class_, '_wsme_attr_order'):
        names_order = class_._wsme_attr_order
    else:
        names = attrs.keys()
        names_order = []
        try:
            lines = []
            for line in inspect.getsourcelines(class_)[0]:
                line = line.strip().replace(" ", "")
                if '=' in line:
                    aname = line[:line.index('=')]
                    if aname in names and aname not in names_order:
                        names_order.append(aname)
            assert len(names_order) == len(names)
        except (TypeError, IOError):
            names_order = list(names)
            names_order.sort()

    attributes[:] = [(name, attrs[name]) for name in names_order]


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
            if attr not in native_types and inspect.isclass(attr):
                print name, attr
                register_type(attr)
            attrdef = wsattr(attr)

        attributes.append((name, attrdef))
    sort_attributes(class_, attributes)
    return attributes


def register_type(class_):
    if class_ is None or \
            class_ in native_types or \
            hasattr(class_, '_wsme_attributes'):
        return

    if isinstance(class_, list):
        if len(class_) != 1:
            raise ValueError("Cannot register type %s" % repr(class_))
        register_type(class_[0])
        array_types.append(class_[0])
        return

    class_._wsme_attributes = inspect_class(class_)

    complex_types.append(weakref.ref(class_))


def list_attributes(class_):
    if not hasattr(class_, '_wsme_attributes'):
        register_type(class_)
    return class_._wsme_attributes
