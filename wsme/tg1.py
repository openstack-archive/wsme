try:
    import json
except ImportError:
    import simplejson as json  # noqa

import functools

import cherrypy
from cherrypy.filters.basefilter import BaseFilter
import webob
from turbogears import expose, config
from turbogears.startup import call_on_startup, call_on_shutdown

from wsme.rest import validate as wsvalidate
import wsme.api
import wsme.rest.args
import wsme.rest.json

import inspect

APIPATH_MAXLEN = 50

__all__ = ['adapt', 'wsexpose', 'wsvalidate']


def wsexpose(*args, **kwargs):
    tg_json_expose = expose(
        'wsmejson:',
        accept_format='application/json',
        content_type='application/json',
        tg_format='json'
    )
    tg_altjson_expose = expose(
        'wsmejson:',
        accept_format='text/javascript',
        content_type='application/json'
    )
    tg_xml_expose = expose(
        'wsmexml:',
        accept_format='text/xml',
        content_type='text/xml',
        tg_format='xml'
    )
    sig = wsme.signature(*args, **kwargs)

    def decorate(f):
        sig(f)
        funcdef = wsme.api.FunctionDefinition.get(f)

        @functools.wraps(f)
        def callfunction(self, *args, **kwargs):
            args, kwargs = wsme.rest.args.get_args(
                funcdef, args, kwargs,
                cherrypy.request.body,
                cherrypy.request.headers['Content-Type']
            )
            result = f(self, *args, **kwargs)
            return dict(
                datatype=funcdef.return_type,
                result=result
            )

        callfunction = tg_xml_expose(callfunction)
        callfunction = tg_altjson_expose(callfunction)
        callfunction = tg_json_expose(callfunction)
        callfunction._wsme_original_function = f
        return callfunction

    return decorate


class AutoJSONTemplate(object):
    def __init__(self, extra_vars_func=None, options=None):
        pass

    def load_template(self, templatename):
        "There are no actual templates with this engine"
        pass

    def render(self, info, format="json", fragment=False, template=None):
        "Renders the template to a string using the provided info."
        return wsme.rest.json.encode_result(
            info['result'], info['datatype']
        )

    def get_content_type(self, user_agent):
        return "application/json"


class AutoXMLTemplate(object):
    def __init__(self, extra_vars_func=None, options=None):
        pass

    def load_template(self, templatename):
        "There are no actual templates with this engine"
        pass

    def render(self, info, format="json", fragment=False, template=None):
        "Renders the template to a string using the provided info."
        return wsme.rest.xml.encode_result(
            info['result'], info['datatype']
        )

    def get_content_type(self, user_agent):
        return "text/xml"


import turbogears.view

turbogears.view.engines['wsmejson'] = AutoJSONTemplate(turbogears.view.stdvars)
turbogears.view.engines['wsmexml'] = AutoXMLTemplate(turbogears.view.stdvars)


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
    wsroot._scan_api = scan_api
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


import wsme.rest


def _scan_api(controller, path=[], objects=[]):
    """
    Recursively iterate a controller api entries.
    """
    for name in dir(controller):
        if name.startswith('_'):
            continue
        a = getattr(controller, name)
        if a in objects:
            continue
        if inspect.ismethod(a):
            if wsme.api.iswsmefunction(a):
                yield path + [name], a._wsme_original_function, [controller]
        elif inspect.isclass(a):
            continue
        else:
            if len(path) > APIPATH_MAXLEN:
                raise ValueError("Path is too long: " + str(path))
            for i in _scan_api(a, path + [name], objects + [a]):
                yield i


def scan_api(root=None):
    return _scan_api(cherrypy.root)
