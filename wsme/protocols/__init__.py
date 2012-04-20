import weakref

import pkg_resources

__all__ = [
    'CallContext',

    'register_protocol', 'getprotocol',
]

registered_protocols = {}


class CallContext(object):
    def __init__(self, request):
        self._request = weakref.ref(request)
        self.path = None

        self.func = None
        self.funcdef = None

    @property
    def request(self):
        return self._request()


class Protocol(object):
    name = None
    displayname = None
    dataformat = None
    content_types = []

    def accept(self, request):
        if request.path.endswith('.' + self.dataformat):
            return True
        return request.headers.get('Content-Type') in self.content_types

    def iter_calls(self, request):
        pass

    def extract_path(self, context):
        pass

    def read_arguments(self, context):
        pass

    def encode_result(self, context, result):
        pass

    def encode_sample_value(self, datatype, value, format=False):
        return ('none', 'N/A')

    def encode_sample_params(self, params, format=False):
        return ('none', 'N/A')

    def encode_sample_result(self, datatype, value, format=False):
        return ('none', 'N/A')


def register_protocol(protocol):
    registered_protocols[protocol.name] = protocol


def getprotocol(name, **options):
    protocol_class = registered_protocols.get(name)
    if protocol_class is None:
        for entry_point in pkg_resources.iter_entry_points(
                'wsme.protocols', name):
            if entry_point.name == name:
                protocol_class = entry_point.load()
        if protocol_class is None:
            raise ValueError("Cannot find protocol '%s'" % name)
        registered_protocols[name] = protocol_class
    return protocol_class(**options)
