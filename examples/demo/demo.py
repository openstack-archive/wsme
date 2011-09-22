# coding=utf8
"""
A mini-demo of what wsme can do.

To run it::

    python setup.py develop

Then::

    paster serve demo.cfg
"""

from webob.dec import wsgify
from wsme import *

import wsme.restjson
import wsme.restxml
import wsme.soap


class DemoRoot(WSRoot):
    @expose(int)
    @validate(int, int)
    def multiply(self, a, b):
        return a * b

    @expose(unicode)
    def helloworld(self):
        return u"こんにちは世界 (<- Hello World in Japanese !)"


def app_factory(global_config, **local_conf):
    return wsgify(DemoRoot()._handle_request)
