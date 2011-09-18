import unittest
import webob
from webob.dec import wsgify
import webtest

from ews import *
from ews.controller import scan_api

class DummyProtocol(object):
    name = 'dummy'

    def __init__(self):
        self.hits = 0

    def accept(self, root, req):
        return True

    def handle(self, root, req):
        self.lastreq = req
        self.lastroot = root
        res = webob.Response()
        self.hits += 1
        return res


def serve_ws(req, root):
    return root._handle_request(req)


class TestController(unittest.TestCase):
    def test_expose(self):
        class MyWS(WSRoot):
            @expose(int)
            def getint(self):
                return 1

        assert MyWS.getint._ews_definition.return_type == int

    def test_validate(self):
        class MyWS(object):
            @expose(int)
            @validate(int, int, int)
            def add(self, a, b, c=0):
                return a + b + c

        args = MyWS.add._ews_definition.arguments

        assert args[0].name == 'a'
        assert args[0].datatype == int
        assert args[0].mandatory
        assert args[0].default is None

        assert args[1].name == 'b'
        assert args[1].datatype == int
        assert args[1].mandatory
        assert args[1].default is None

        assert args[2].name == 'c'
        assert args[2].datatype == int
        assert not args[2].mandatory
        assert args[2].default == 0

    def test_register_protocol(self):
        p = DummyProtocol()
        import ews.controller
        ews.controller.register_protocol(p)
        assert ews.controller.registered_protocols['dummy'] == p

        r = WSRoot()
        assert r.protocols['dummy']

    def test_scan_api(self):
        class NS(object):
            @expose(int)
            @validate(int, int)
            def multiply(self, a, b):
                return a * b

        class MyRoot(WSRoot):
            ns = NS()

        r = MyRoot()

        api = [i for i in scan_api(r)]
        assert len(api) == 1
        assert api[0][0] == ['ns']
        fd = api[0][1]
        assert fd.name == 'multiply'

    def test_handle_request(self):
        class MyRoot(WSRoot):
            pass

        p = DummyProtocol()
        r = MyRoot(protocols=[p])

        app = webtest.TestApp(
            wsgify(r._handle_request))

        res = app.get('/')

        assert p.lastreq.path == '/'
        assert p.lastroot == r
        assert p.hits == 1

        res = app.get('/?ewsproto=dummy')

        assert p.lastreq.path == '/'
        assert p.lastroot == r
        assert p.hits == 2
