import webob

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
        a = root
        for name in path:
            a = getattr(a, name)

        if not hasattr(a, '_wsme_definition'):
            raise ValueError('Invalid path')
        fonc = a

        kw = self.get_args(request)
        
        res = webob.Response()
        res.headers['Content-Type'] = 'application/json'
        res.status = "200 OK"

        res.body = self.encode_response(a(**kw))

        return res
