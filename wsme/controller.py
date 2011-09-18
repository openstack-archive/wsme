import inspect

__all__ = ['expose', 'validate', 'WSRoot']

registered_protocols = {}

def scan_api(controller, path=[]):
    for name in dir(controller):
        if name.startswith('_'):
            continue
        a = getattr(controller, name)
        if hasattr(a, '_wsme_definition'):
            yield path, a._wsme_definition
        else:
            for i in scan_api(a, path + [name]):
                yield i


class FunctionArgument(object):
    def __init__(self, name, datatype, mandatory, default):
        self.name = name
        self.datatype = datatype
        self.mandatory = mandatory
        self.default = default


class FunctionDefinition(object):
    def __init__(self, name):
        self.name = name
        self.return_type = None
        self.arguments = []
    
    @classmethod
    def get(cls, func):
        fd = getattr(func, '_wsme_definition', None)
        if fd is None:
            fd = FunctionDefinition(func.__name__)
            func._wsme_definition = fd
        return fd


def register_protocol(protocol):
    global registered_protocols
    registered_protocols[protocol.name] = protocol


class expose(object):
    def __init__(self, return_type=None):
        self.return_type = return_type

    def __call__(self, func):
        fd = FunctionDefinition.get(func)
        fd.return_type = self.return_type
        return func


class validate(object):
    def __init__(self, *args, **kw):
        self.param_types = args

    def __call__(self, func):
        fd = FunctionDefinition.get(func)
        args, varargs, keywords, defaults = inspect.getargspec(func)
        print args, defaults
        if args[0] == 'self':
            args = args[1:]
        for i, argname in enumerate(args):
            datatype = self.param_types[i]
            mandatory = defaults is None or i <= len(defaults)
            default = None
            if not mandatory:
                default = defaults[i-(len(args)-len(defaults))]
            print argname, datatype, mandatory, default
            fd.arguments.append(FunctionArgument(argname, datatype,
                                                 mandatory, default))
        return func


class WSRoot(object):
    def __init__(self, protocols=None):
        if protocols is None:
            protocols = registered_protocols.values()
        self.protocols = {}
        for protocol in protocols:
            if isinstance(protocol, str):
                protocol = registered_protocols[protocol]
            self.protocols[protocol.name] = protocol

    def _handle_request(self, request):
        protocol = None
        if 'wsmeproto' in request.params:
            protocol = self.protocols[request.params['wsmeproto']]
        else:
            for p in self.protocols.values():
                if p.accept(self, request):
                    protocol = p
                    break

        return protocol.handle(self, request)
