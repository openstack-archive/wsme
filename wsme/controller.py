import inspect
import traceback
import weakref

from wsme import exc

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
    def __init__(self, func):
        self.name = func.__name__
        self.return_type = None
        self.arguments = []

    @classmethod
    def get(cls, func):
        fd = getattr(func, '_wsme_definition', None)
        if fd is None:
            fd = FunctionDefinition(func)
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
                default = defaults[i - (len(args) - len(defaults))]
            print argname, datatype, mandatory, default
            fd.arguments.append(FunctionArgument(argname, datatype,
                                                 mandatory, default))
        return func


class WSRoot(object):
    def __init__(self, protocols=None):
        self.debug = True
        if protocols is None:
            protocols = registered_protocols.keys()
        self.protocols = {}
        for protocol in protocols:
            if isinstance(protocol, str):
                protocol = registered_protocols[protocol]()
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

    def _format_exception(self, excinfo):
        """Extract informations that can be sent to the client."""
        if isinstance(excinfo[1], exc.ClientSideError):
            return dict(faultcode="Client",
                        faultstring=unicode(excinfo[1]))
        else:
            r = dict(faultcode="Server",
                     faultstring=str(excinfo[1]))
            if self.debug:
                r['debuginfo'] = ("Traceback:\n%s\n" %
                                  "\n".join(traceback.format_exception(*excinfo)))
            return r

    def _lookup_function(self, path):
        a = self

        for name in path:
            a = getattr(a, name, None)
            if a is None:
                break

        if not hasattr(a, '_wsme_definition'):
            raise exc.UnknownFunction('/'.join(path))

        return a, a._wsme_definition

