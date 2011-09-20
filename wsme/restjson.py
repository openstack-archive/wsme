import base64

from wsme.rest import RestProtocol
from wsme.controller import register_protocol
import wsme.types

try:
    import simplejson as json
except ImportError:
    import json


def prepare_encode(value, datatype):
    if datatype in wsme.types.pod_types:
        return value
    if wsme.types.isstructured(datatype):
        d = dict()
        for name, attr in wsme.types.list_attributes(datatype):
            d[name] = prepare_encode(getattr(value, name), attr.datatype)
        return d
    if datatype in wsme.types.dt_types:
        return value.isoformat()
    if datatype is wsme.types.binary:
        return base64.encode()


class RestJsonProtocol(RestProtocol):
    name = 'REST+Json'
    dataformat = 'json'
    content_types = ['application/json', 'text/json', None]

    def decode_args(self, req, arguments):
        kw = json.loads(req.body)
        return kw

    def encode_result(self, result, return_type):
        return json.dumps({'result': prepare_encode(result, return_type)})

    def encode_error(self, errordetail):
        return json.dumps(errordetail)

register_protocol(RestJsonProtocol)
