import datetime
import decimal

binary = object()

pod_types = [str, unicode, int, float, bool]
dt_types = [datetime.date, datetime.time, datetime.datetime]
extra_types = [binary, decimal.Decimal]
native_types = pod_types + dt_types + extra_types

structured_types = []

def register_type(class_):
    structured_types.append(class_)

