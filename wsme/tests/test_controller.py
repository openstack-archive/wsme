import unittest
import webob
from webob.dec import wsgify
import webtest

from wsme import *
from wsme.controller import scan_api
import wsme.wsgi


class DummyProtocol(object):
    name = 'dummy'
    content_types = ['', None]

    def __init__(self):
        self.hits = 0

    def accept(self, req):
        return True

    def extract_path(self, request):
        return ['touch']

    def read_arguments(self, funcdef, request):
        self.lastreq = request
        self.hits += 1
        return {}

    def encode_result(self, funcdef, result):
        return str(result)

    def encode_error(self, infos):
        return str(infos)


class TestController(unittest.TestCase):
    def test_expose(self):
        class MyWS(WSRoot):
            @expose(int)
            def getint(self):
                return 1

        assert MyWS.getint._wsme_definition.return_type == int

    def test_validate(self):
        class MyWS(object):
            @expose(int)
            @validate(int, int, int)
            def add(self, a, b, c=0):
                return a + b + c

        args = MyWS.add._wsme_definition.arguments

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
        import wsme.controller
        wsme.controller.register_protocol(DummyProtocol)
        assert wsme.controller.registered_protocols['dummy'] == DummyProtocol

        r = WSRoot()
        assert len(r.protocols) == 0

        r.addprotocol('dummy')
        assert len(r.protocols) == 1
        assert r.protocols[0].__class__ == DummyProtocol

        r = WSRoot(['dummy'])
        assert len(r.protocols) == 1
        assert r.protocols[0].__class__ == DummyProtocol

    def test_scan_api(self):
        class NS(object):
            @expose(int)
            @validate(int, int)
            def multiply(self, a, b):
                return a * b

        class MyRoot(WSRoot):
            ns = NS()

        r = MyRoot()

        api = list(scan_api(r))
        assert len(api) == 1
        fd = api[0]
        assert fd.path == ['ns']
        assert fd.name == 'multiply'

    def test_scan_api_too_deep(self):
        class Loop(object):
            loop = None
        Loop.me = Loop()

        class MyRoot(WSRoot):
            loop = Loop()

        r = MyRoot()

        try:
            list(scan_api(r))
            assert False, "ValueError not raised"
        except ValueError, e:
            assert str(e).startswith("Path is too long")

    def test_handle_request(self):
        class MyRoot(WSRoot):
            @expose()
            def touch(self):
                pass

        p = DummyProtocol()
        r = MyRoot(protocols=[p])

        app = webtest.TestApp(wsme.wsgi.adapt(r))

        res = app.get('/')

        assert p.lastreq.path == '/'
        assert p.hits == 1

        res = app.get('/touch?wsmeproto=dummy')

        assert p.lastreq.path == '/touch'
        assert p.hits == 2

    def test_no_available_protocol(self):
        r = WSRoot()

        app = webtest.TestApp(wsme.wsgi.adapt(r))

        res = app.get('/', expect_errors=True)
        assert res.status_int == 500
        print res.body
        assert res.body.find(
            "None of the following protocols can handle this request") != -1

    def test_return_content_type_guess(self):
        class DummierProto(DummyProtocol):
            content_types = ['text/xml', 'text/plain']

        r = WSRoot([DummierProto()])

        app = webtest.TestApp(wsme.wsgi.adapt(r))

        res = app.get('/', expect_errors=True, headers={
            'Accept': 'text/xml,q=0.8'})
        assert res.status_int == 400
        assert res.content_type == 'text/xml', res.content_type

        res = app.get('/', expect_errors=True, headers={
            'Accept': 'text/plain'})
        assert res.status_int == 400
        assert res.content_type == 'text/plain', res.content_type
