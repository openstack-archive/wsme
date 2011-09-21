from webob.dec import wsgify
from wsme import *

import wsme.restjson
import wsme.restxml


class DemoRoot(WSRoot):
    @expose(int)
    @validate(int, int)
    def multiply(self, a, b):
        return a * b


def app_factory(global_config, **local_conf):
    return wsgify(DemoRoot()._handle_request)
