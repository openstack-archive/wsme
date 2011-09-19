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

def mandatory(datatype):
    if isinstance(datatype, AttrDef):
        datatype.mandatory = True
        return datatype
    return AttrDef(datatype, True)


class AttrDef(object):
    def __init__(self, datatype, mandatory=False, default=None):
        self.datatype = datatype
        self.mandatory = mandatory
        self.default = None

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
        if not isinstance(attr, AttrDef):
            attrdef = AttrDef(attr)
        else:
            attrdef = attr

        attributes.append((name, AttrDef))
    return attributes

def register_type(class_):
    if hasattr(class_, '_wsme_attributes'):
        return

    class_._wsme_attributes = inspect_class(class_)
    structured_types.append(weakref.ref(class_))

def list_attributes(class_):
    return class_._wsme_attributes

