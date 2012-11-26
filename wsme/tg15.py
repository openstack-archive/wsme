import cherrypy

from wsme.tg1 import wsexpose, wsvalidate
import wsme.tg1


__all__ = ['adapt', 'wsexpose', 'wsvalidate']


def scan_api(root=None):
    for baseurl, instance in cherrypy.tree.apps.items():
        path = [token for token in baseurl.split('/') if token]
        for i in wsme.tg1._scan_api(instance.root, path):
            yield i


def adapt(wsroot):
    wsroot._scan_api = scan_api
    controller = wsme.tg1.Controller(wsroot)
    return controller
