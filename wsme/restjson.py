from wsme.rest import RestProtocol
from wsme.controller import register_protocol

try:
    import simplejson as json
except ImportError:
    import json

class RestJsonProtocol(RestProtocol):
    name = 'REST+Json'
    dataformat = 'json'
    content_types = [None, 'application/json', 'text/json']

    def get_args(self, req):
        kw = json.loads(req.body)
        return kw

    def encode_result(self, result, return_type):
        return json.dumps({'result': result})

    def encode_error(self, errordetail):
        return json.dumps(errordetail)

register_protocol(RestJsonProtocol)
