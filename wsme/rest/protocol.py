import collections
import os.path
import logging
import six

from wsme.exc import ClientSideError, UnknownArgument, MissingArgument
from wsme.protocol import CallContext, Protocol

import wsme.rest
import wsme.rest.args

log = logging.getLogger(__name__)


class RestProtocol(Protocol):
    name = 'rest'
    displayname = 'REST'
    dataformats = ['json', 'xml']
    content_types = ['application/json', 'text/xml']

    def __init__(self, dataformats=None):
        if dataformats is None:
            dataformats = RestProtocol.dataformats

        self.dataformats = collections.OrderedDict()
        self.content_types = []

        for dataformat in dataformats:
            __import__('wsme.rest.' + dataformat)
            dfmod = getattr(wsme.rest, dataformat)
            self.dataformats[dataformat] = dfmod
            self.content_types.extend(dfmod.accept_content_types)

    def accept(self, request):
        for dataformat in self.dataformats:
            if request.path.endswith('.' + dataformat):
                return True
        return request.headers.get('Content-Type') in self.content_types

    def iter_calls(self, request):
        context = CallContext(request)
        context.outformat = None
        ext = os.path.splitext(request.path.split('/')[-1])[1]
        inmime = request.content_type
        outmime = request.accept.best_match(self.content_types)

        outformat = None
        for dfname, df in self.dataformats.items():
            if ext == '.' + dfname:
                outformat = df

        if outformat is None and request.accept:
            for dfname, df in self.dataformats.items():
                if outmime in df.accept_content_types:
                    outformat = df

        if outformat is None:
            for dfname, df in self.dataformats.items():
                if inmime == df.content_type:
                    outformat = df

        context.outformat = outformat
        yield context

    def extract_path(self, context):
        path = context.request.path
        assert path.startswith(self.root._webpath)
        path = path[len(self.root._webpath):]
        path = path.strip('/').split('/')

        for dataformat in self.dataformats:
            if path[-1].endswith('.' + dataformat):
                path[-1] = path[-1][:-len(dataformat) - 1]

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

        param_args = (), {}

        body = None

        if 'body' in request.params:
            body = request.params['body']
            body_mimetype = context.outformat.content_type
        if body is None:
            body = request.body
            body_mimetype = request.content_type
            param_args = wsme.rest.args.args_from_params(
                funcdef, request.params
            )
        if isinstance(body, six.binary_type):
            body = body.decode('utf8')

        if body and body_mimetype in self.content_types:
            body_args = wsme.rest.args.args_from_body(
                funcdef, body, body_mimetype
            )
        else:
            body_args = ((), {})

        args, kw = wsme.rest.args.combine_args(
            funcdef,
            param_args,
            body_args
        )

        for a in funcdef.arguments:
            if a.mandatory and a.name not in kw:
                raise MissingArgument(a.name)

        argnames = set((a.name for a in funcdef.arguments))

        for k in kw:
            if k not in argnames:
                raise UnknownArgument(k)

        return kw

    def encode_result(self, context, result):
        out = context.outformat.tostring(
            result, context.funcdef.return_type
        )
        return out

    def encode_error(self, context, errordetail):
        out = context.outformat.encode_error(
            context, errordetail
        )
        return out
