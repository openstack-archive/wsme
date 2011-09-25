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


class Person(object):
    id = int
    firstname = unicode
    lastname = unicode


class DemoRoot(WSRoot):
    @expose(int)
    @validate(int, int)
    def multiply(self, a, b):
        return a * b

    @expose(unicode)
    def helloworld(self):
        return u"こんにちは世界 (<- Hello World in Japanese !)"


    @expose(Person)
    def getperson(self):
        p = Person()
        p.id = 12
        p.firstname = u'Ross'
        p.lastname = u'Geler'
        return p

def app_factory(global_config, **local_conf):
    soap = wsme.soap.SoapProtocol(
        tns='http://example.com/demo',
        typenamespace='http://example.com/demo/types',
    )
    return wsgify(DemoRoot([soap])._handle_request)
