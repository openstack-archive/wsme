import webob
import sys

from wsme.exc import UnknownFunction

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

    def handle(self, root, request):
        path = request.path.strip('/').split('/')

        if path[-1].endswith('.' + self.dataformat):
            path[-1] = path[-1][:-len(self.dataformat) - 1]

        res = webob.Response()

        try:
            func, funcdef = root._lookup_function(path)
            kw = self.decode_args(request, funcdef.arguments)
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
