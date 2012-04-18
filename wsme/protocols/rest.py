import logging

from wsme.exc import ClientSideError, UnknownArgument
from wsme.protocols import CallContext, Protocol
from wsme.protocols.commons import from_params
from wsme.types import Unset

log = logging.getLogger(__name__)


class RestProtocol(Protocol):
    def iter_calls(self, request):
        yield CallContext(request)

    def extract_path(self, context):
        path = context.request.path
        assert path.startswith(self.root._webpath)
        path = path[len(self.root._webpath):]
        path = path.strip('/').split('/')

        if path[-1].endswith('.' + self.dataformat):
            path[-1] = path[-1][:-len(self.dataformat) - 1]

        return path

    def read_arguments(self, context):
        request = context.request
        funcdef = context.funcdef

        if 'Content-Type' in request.headers \
                and "application/x-www-form-urlencoded" in \
                    request.headers['Content-Type']:
            # The params were read from the body, ignoring the body then
            pass
        elif len(request.params) and request.body:
            log.warning("The request has both a body and params.")
            log.debug("Params: %s" % request.params)
            log.debug("Body: %s" % request.body)
            raise ClientSideError(
                "Cannot read parameters from both a body and GET/POST params")

        body = None
        if 'body' in request.params:
            body = request.params['body']

        if body is None and len(request.params):
            kw = {}
            hit_paths = set()
            for argdef in funcdef.arguments:
                value = from_params(
                    argdef.datatype, request.params, argdef.name, hit_paths)
                if value is not Unset:
                    kw[argdef.name] = value
            paths = set(request.params.keys())
            unknown_paths = paths - hit_paths
            if unknown_paths:
                raise UnknownArgument(', '.join(unknown_paths))
            return kw
        else:
            if body is None:
                body = request.body
            if body:
                parsed_args = self.parse_args(body)
            else:
                parsed_args = {}

        kw = {}

        for arg in funcdef.arguments:
            if arg.name not in parsed_args:
                continue

            value = parsed_args.pop(arg.name)
            kw[arg.name] = self.decode_arg(value, arg)

        if parsed_args:
            raise UnknownArgument(parsed_args.keys()[0])
        return kw
