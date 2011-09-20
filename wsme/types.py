import datetime
import decimal
import weakref
import inspect

binary = object()

pod_types = [str, unicode, int, float, bool]
dt_types = [datetime.date, datetime.time, datetime.datetime]
extra_types = [binary, decimal.Decimal]
native_types = pod_types + dt_types + extra_types

structured_types = []


class wsproperty(property):
    def __init__(self, datatype, fget, fset=None,
                 mandatory=False, doc=None):
        property.__init__(self, fget, fset, doc)
        self.mandatory = mandatory


class wsattr(object):
    def __init__(self, datatype, mandatory=False):
        self.datatype = datatype
        self.mandatory = mandatory


def inspect_class(class_):
    attributes = []
    for name in dir(class_):
        if name.startswith('_'):
            continue
            
        attr = getattr(class_, name)
        if inspect.isfunction(attr):
            continue
        if inspect.ismethod(attr):
            continue
        if not isinstance(attr, wsattr):
            attrdef = wsattr(attr)
        else:
            attrdef = attr

        attributes.append((name, wsattr))
    return attributes

def register_type(class_):
    if hasattr(class_, '_wsme_attributes'):
        return

    class_._wsme_attributes = inspect_class(class_)
    structured_types.append(weakref.ref(class_))

def list_attributes(class_):
    return class_._wsme_attributes

