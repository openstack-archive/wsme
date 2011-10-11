from webob.dec import wsgify
from wsme import controller


class WSRoot(controller.WSRoot, wsgify):
    """
    A WSRoot that is usable as a wsgi application.
    """
    def __init__(self, *args, **kw):
        super(WSRoot, self).__init__(*args, **kw)
        wsgify.__init__(self, self._handle_request)

    def clone(self, func=None, **kw):
        return WSRoot(**kw)
