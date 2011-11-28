# coding=utf8
"""
A mini-demo of what wsme can do.

To run it::

    python setup.py develop

Then::

    paster serve demo.cfg
"""

from wsme import WSRoot, expose, validate
from wsme.wsgi import adapt

import logging


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

    @expose(Person)
    @validate(Person)
    def setperson(self, person):
        return person


def app_factory(global_config, **local_conf):
    root = DemoRoot()

    root.addprotocol('soap',
            tns='http://example.com/demo',
            typenamespace='http://example.com/demo/types',
            baseURL='http://127.0.0.1:8989/',
    )

    root.addprotocol('restjson')

    return adapt(root)

logging.basicConfig(level=logging.DEBUG)
