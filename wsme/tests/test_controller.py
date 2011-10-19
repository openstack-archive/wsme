# encoding=utf8

import unittest
import webob
from webob.dec import wsgify
import webtest

from wsme import *
from wsme.controller import getprotocol, scan_api, pexpose
from wsme.controller import FunctionArgument, FunctionDefinition, CallContext
import wsme.wsgi


class DummyProtocol(object):
    name = 'dummy'
    content_types = ['', None]

    def __init__(self):
        self.hits = 0

    def accept(self, req):
        return True

    def iter_calls(self, req):
        yield CallContext(req)

    def extract_path(self, context):
        return ['touch']

    def read_arguments(self, context):
        self.lastreq = context.request
        self.hits += 1
        return {}

    def encode_result(self, context, result):
        return str(result)

    def encode_error(self, context, infos):
        return str(infos)


def test_getprotocol():
    try:
        getprotocol('invalid')
        assert False, "ValueError was not raised"
    except ValueError, e:
        pass


def test_pexpose():
    class Proto(DummyProtocol):
        def extract_path(self, context):
            if context.request.path.endswith('ufunc'):
                return ['_protocol', 'dummy', 'ufunc']
            else:
                return ['_protocol', 'dummy', 'func']

        @pexpose(None, "text/xml")
        def func(self):
            return "<p></p>"

        @pexpose(None, "text/xml")
        def ufunc(self):
            return u"<p>é</p>"

    assert FunctionDefinition.get(Proto.func).return_type is None
    assert FunctionDefinition.get(Proto.func).protocol_specific
    assert FunctionDefinition.get(Proto.func).contenttype == "text/xml"

    p = Proto()
    r = WSRoot()
    r.addprotocol(p)

    app = webtest.TestApp(wsme.wsgi.adapt(r))
    res = app.get('/func')
    assert res.status_int == 200
    assert res.body == "<p></p>", res.body
    res = app.get('/ufunc')
    assert res.unicode_body == u"<p>é</p>", res.body


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
        path, fd = api[0]
        assert path == ['ns', 'multiply']
        assert fd.name == 'multiply'

    def test_scan_subclass(self):
        class MyRoot(WSRoot):
            class SubClass(object):
                pass

        r = MyRoot()
        api = list(scan_api(r))

        assert len(api) == 0

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

        class NoPathProto(DummyProtocol):
            def extract_path(self, request):
                return None

        p = NoPathProto()
        r = MyRoot(protocols=[p])
        
        app = webtest.TestApp(wsme.wsgi.adapt(r))

        res = app.get('/', expect_errors=True)
        print res.status, res.body
        assert res.status_int == 400

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

    def test_getapi(self):
        class MyRoot(WSRoot):
            pass

        r = MyRoot()
        api = r.getapi()
        assert r.getapi() is api


class TestFunctionDefinition(unittest.TestCase):

    def test_get_arg(self):
        def myfunc(self):
            pass

        fd = FunctionDefinition(FunctionDefinition)
        fd.arguments.append(FunctionArgument('a', int, True, None))

        assert fd.get_arg('a').datatype is int
        assert fd.get_arg('b') is None
