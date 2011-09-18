from wsme.rest import RestProtocol
from wsme.controller import register_protocol

class RestJsonProtocol(RestProtocol):
    name = 'REST+Json'
    dataformat = 'json'
    content_types = [None, 'application/json', 'text/json']

    def get_args(self, req):
        kw = json.loads(req.body)


register_protocol(RestJsonProtocol)
