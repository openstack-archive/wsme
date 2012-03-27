import cherrypy
from cherrypy.filters.basefilter import BaseFilter
import webob
from turbogears import expose


class WSMECherrypyFilter(BaseFilter):
    def on_start_resource(self):
        cherrypy.request.processRequestBody = False


class Controller(object):
    _cp_filters = [WSMECherrypyFilter()]

    def __init__(self, wsroot):
        self._wsroot = wsroot

    @expose()
    def default(self, *args, **kw):
        req = webob.Request(cherrypy.request.wsgi_environ)
        res = self._wsroot._handle_request(req)
        cherrypy.response.header_list = res.headerlist
        cherrypy.response.status = res.status
        return res.body


def adapt(wsroot):
    return Controller(wsroot)
