import webob
import sys

from wsme.exc import UnknownFunction


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

        res = webob.Response()
        res.headers['Content-Type'] = 'application/json'

        try:
            func, funcdef = root._lookup_function(path)
            kw = self.get_args(request)
            result = func(**kw)
            # TODO make sure result type == a._wsme_definition.return_type
            res.body = self.encode_result(result, funcdef.return_type)
            res.status = "200 OK"
        except Exception, e:
            res.status = "500 Error"
            res.body = self.encode_error(
                root._format_exception(sys.exc_info()))

        return res
