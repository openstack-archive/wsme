import webob
import sys

from wsme.exc import UnknownFunction, MissingArgument, UnknownArgument

html_body = """
<html>
<body>
<pre>
%(content)s
</pre>
</body>
</html>
"""


class RestProtocol(object):
    name = None
    dataformat = None
    content_types = []

    def accept(self, root, request):
        if request.path.endswith('.' + self.dataformat):
            return True
        return request.headers.get('Content-Type') in self.content_types

    def read_arguments(self, request, arguments):
        if len(request.params) and request.body:
            raise ClientSideError(
                "Cannot read parameters from both a body and GET/POST params")

        body = None
        if 'body' in request.params:
            body = request.params['body']

        if body is None and len(request.params):
            parsed_args = {}
            for key, value in request.params.items():
                parsed_args[key] = self.parse_arg(value)
        else:
            if body is None:
                body = request.body
            parsed_args = self.parse_args(body)

        kw = {}

        for arg in arguments:
            if arg.name not in parsed_args:
                if arg.mandatory:
                    raise MissingArgument(arg.name)
                continue

            value = parsed_args.pop(arg.name)
            kw[arg.name] = self.decode_arg(value, arg)

        if parsed_args:
            raise UnknownArgument(parsed_args.keys()[0])
        return kw

    def handle(self, root, request):
        path = request.path.strip('/').split('/')

        if path[-1].endswith('.' + self.dataformat):
            path[-1] = path[-1][:-len(self.dataformat) - 1]

        res = webob.Response()

        try:
            func, funcdef = root._lookup_function(path)
            kw = self.read_arguments(request, funcdef.arguments)
            result = func(**kw)
            # TODO make sure result type == a._wsme_definition.return_type
            res.body = self.encode_result(result, funcdef.return_type)
            res.status = "200 OK"
        except Exception, e:
            res.status = 500
            res.body = self.encode_error(
                root._format_exception(sys.exc_info()))

        # Attempt to correctly guess what content-type we should return.
        res_content_type = None

        last_q = 0
        if hasattr(request.accept, '_parsed'):
            for mimetype, q in request.accept._parsed:
                if mimetype in self.content_types and last_q < q:
                    res_content_type = mimetype
        else:
            res_content_type = request.accept.best_match([
                ct for ct in self.content_types if ct])

        # If not we will attempt to convert the body to an accepted
        # output format.
        if res_content_type is None:
            if "text/html" in request.accept:
                res_content_type = "text/html"
                res.body = html_body % dict(content=res.body)

        res.headers['Content-Type'] = "%s; charset=UTF-8" % res_content_type

        return res
