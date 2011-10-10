import wsme
import cherrypy
import webob
from turbogears import expose

class WSRoot(wsme.WSRoot):
    @expose()
    def default(self, *args, **kw):
        req = webob.Request(cherrypy.request.wsgi_environ)
        res = self._handle_request(req)
        cherrypy.response.header_list = res.headerlist
        cherrypy.status = res.status
        return res.body
