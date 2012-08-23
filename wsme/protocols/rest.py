import logging
import six

from six import u

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

        # Check if the path is actually a function, and if not
        # see if the http method make a difference
        # TODO Re-think the function lookup phases. Here we are
        # doing the job that will be done in a later phase, which
        # is sub-optimal
        for p, fdef in self.root.getapi():
            if p == path:
                return path

        # No function at this path. Now check for function that have
        # this path as a prefix, and declared an http method
        for p, fdef in self.root.getapi():
            if len(p) == len(path) + 1 and p[:len(path)] == path and \
                    fdef.extra_options.get('method') == context.request.method:
                return p

        return path

    def read_arguments(self, context):
        request = context.request
        funcdef = context.funcdef

        if 'Content-Type' in request.headers \
                and ("application/x-www-form-urlencoded"
                        in request.headers['Content-Type']
                    or "multipart/form-data"
                        in request.headers['Content-Type']):
            # The params were read from the body, ignoring the body then
            pass
        elif len(request.params) and request.content_length:
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
            if isinstance(body, six.binary_type):
                body = body.decode('utf8')
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
            raise UnknownArgument(u(', ').join(parsed_args.keys()))
        return kw
