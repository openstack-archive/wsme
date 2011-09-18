class RestProtocol(object):
    name = None
    dataformat = None
    content_types = []

    def accept(self, root, request):
        if request.path.endswith('.' + self.dataformat):
            return True
        return request.headers.get('Content-Type') in self.content_types
        
    def handle(self, root, request):
        path = request.path.split('/')
        a = root
        for name in path:
            a = getattr(a, name)
        if not hasattr(a, '_ews_description'):
            raise ValueError('Invalid path')
        fonc = a
        kw = self.get_args(req)

