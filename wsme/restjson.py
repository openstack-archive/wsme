import base64
import datetime
import decimal

from simplegeneric import generic

from wsme.rest import RestProtocol
from wsme.controller import register_protocol
import wsme.types

try:
    import simplejson as json
except ImportError:
    import json


@generic
def tojson(datatype, value):
    if wsme.types.isstructured(datatype):
        d = dict()
        for name, attr in wsme.types.list_attributes(datatype):
            d[name] = tojson(attr.datatype, getattr(value, name))
        return d
    return value


@tojson.when_object(decimal.Decimal)
def decimal_tojson(datatype, value):
    return str(value)


@tojson.when_object(datetime.date)
def date_tojson(datatype, value):
    return value.isoformat()


@tojson.when_object(datetime.time)
def time_tojson(datatype, value):
    return value.isoformat()


@tojson.when_object(datetime.datetime)
def datetime_tojson(datatype, value):
    return value.isoformat()


@tojson.when_object(wsme.types.binary)
def datetime_tojson(datatype, value):
    return base64.encodestring(value)


@generic
def fromjson(datatype, value):
    if value is None:
        return None
    if wsme.types.isstructured(datatype):
        obj = datatype()
        for name, attrdef in wsme.types.list_attributes(datatype):
            if name in value:
                setattr(obj, name, fromjson(attrdef.datatype, value[name]))
        return obj
    return value


@fromjson.when_object(decimal.Decimal)
def decimal_fromjson(datatype, value):
    return decimal.Decimal(value)


@fromjson.when_object(datetime.date)
def date_fromjson(datatype, value):
    return datetime.datetime.strptime(value, '%Y-%m-%d').date()


@fromjson.when_object(datetime.time)
def time_fromjson(datatype, value):
    return datetime.datetime.strptime(value, '%H:%M:%S').time()


@fromjson.when_object(datetime.datetime)
def time_fromjson(datatype, value):
    return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')


@fromjson.when_object(wsme.types.binary)
def binary_fromjson(datatype, value):
    return base64.decodestring(value)


class RestJsonProtocol(RestProtocol):
    name = 'REST+Json'
    dataformat = 'json'
    content_types = ['application/json', 'text/json', None]

    def decode_args(self, req, arguments):
        raw_args = json.loads(req.body)
        kw = {}
        for farg in arguments:
            if farg.mandatory and farg.name not in raw_args:
                raise MissingArgument(farg.name)
            value = raw_args[farg.name]
            kw[farg.name] = fromjson(farg.datatype, value)
        return kw

    def encode_result(self, result, return_type):
        return json.dumps({'result': tojson(return_type, result)})

    def encode_error(self, errordetail):
        return json.dumps(errordetail)

register_protocol(RestJsonProtocol)
