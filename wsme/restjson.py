import base64
import datetime

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
    return base64.encode(value)


class RestJsonProtocol(RestProtocol):
    name = 'REST+Json'
    dataformat = 'json'
    content_types = ['application/json', 'text/json', None]

    def decode_args(self, req, arguments):
        kw = json.loads(req.body)
        return kw

    def encode_result(self, result, return_type):
        return json.dumps({'result': tojson(return_type, result)})

    def encode_error(self, errordetail):
        return json.dumps(errordetail)

register_protocol(RestJsonProtocol)
