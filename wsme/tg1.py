import cherrypy
from cherrypy.filters.basefilter import BaseFilter
import webob
from turbogears import expose, config
from turbogears.startup import call_on_startup, call_on_shutdown


class WSMECherrypyFilter(BaseFilter):
    def __init__(self, controller):
        self.controller = controller
        self.webpath = None

    def on_start_resource(self):
        path = cherrypy.request.path
        if path.startswith(self.controller._wsroot._webpath):
            cherrypy.request.processRequestBody = False


class Controller(object):
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
    controller = Controller(wsroot)
    filter_ = WSMECherrypyFilter(controller)

    def install_filter():
        filter_.webpath = config.get('server.webpath') or ''
        controller._wsroot._webpath = \
            filter_.webpath + controller._wsroot._webpath
        cherrypy.root._cp_filters.append(filter_)

    def uninstall_filter():
        cherrypy.root._cp_filters.remove(filter_)
        controller._wsroot._webpath = \
            controller._wsroot._webpath[len(filter_.webpath):]

    call_on_startup.append(install_filter)
    call_on_shutdown.insert(0, uninstall_filter)
    return controller
