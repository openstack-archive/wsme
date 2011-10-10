import logging

from wsme.exc import UnknownFunction, MissingArgument, UnknownArgument

log = logging.getLogger(__name__)


class RestProtocol(object):
    name = None
    dataformat = None
    content_types = []

    def accept(self, request):
        if request.path.endswith('.' + self.dataformat):
            return True
        return request.headers.get('Content-Type') in self.content_types

    def read_arguments(self, funcdef, request):
        if len(request.params) and request.body:
            raise ClientSideError(
                "Cannot read parameters from both a body and GET/POST params")

        body = None
        if 'body' in request.params:
            body = request.params['body']

        if body is None and len(request.params):
            parsed_args = {}
            for key, value in request.params.items():
                parsed_args[key] = self.parse_arg(key, value)
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
                if arg.mandatory:
                    raise MissingArgument(arg.name)
                continue

            value = parsed_args.pop(arg.name)
            kw[arg.name] = self.decode_arg(value, arg)

        if parsed_args:
            raise UnknownArgument(parsed_args.keys()[0])
        return kw

    def extract_path(self, request):
        path = request.path
        assert path.startswith(self.root._webpath)
        path = path[len(self.root._webpath):]
        path = path.strip('/').split('/')

        if path[-1].endswith('.' + self.dataformat):
            path[-1] = path[-1][:-len(self.dataformat) - 1]

        return path
