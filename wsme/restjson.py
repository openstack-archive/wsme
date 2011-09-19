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

    def encode_response(self, response):
        return json.dumps(response)

register_protocol(RestJsonProtocol)
