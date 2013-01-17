# encoding=utf8

from six import b
import sys

import unittest
import webtest

from wsme import WSRoot, expose, validate
from wsme.rest import scan_api
from wsme.api import FunctionArgument, FunctionDefinition
from wsme.types import iscomplex
import wsme.types

from wsme.tests.test_protocols import DummyProtocol


class TestController(unittest.TestCase):
    def test_expose(self):
        class MyWS(WSRoot):
            @expose(int)
            def getint(self):
                return 1

        assert MyWS.getint._wsme_definition.return_type == int

    def test_validate(self):
        class ComplexType(object):
            attr = int

        class MyWS(object):
            @expose(int)
            @validate(int, int, int)
            def add(self, a, b, c=0):
                return a + b + c

            @expose(bool)
            @validate(ComplexType)
            def setcplx(self, obj):
                pass

        MyWS.add._wsme_definition.resolve_types(wsme.types.registry)
        MyWS.setcplx._wsme_definition.resolve_types(wsme.types.registry)
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

        assert iscomplex(ComplexType)

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
        path, fd, args = api[0]
        assert path == ['ns', 'multiply']
        assert fd._wsme_definition.name == 'multiply'
        assert args == []

    def test_scan_subclass(self):
        class MyRoot(WSRoot):
            class SubClass(object):
                pass

        r = MyRoot()
        api = list(scan_api(r))

        assert len(api) == 0

    def test_scan_api_too_deep(self):
        class Loop(object):
            pass

        l = Loop()
        for i in range(0, 21):
            nl = Loop()
            nl.l = l
            l = nl

        class MyRoot(WSRoot):
            loop = l

        r = MyRoot()

        try:
            list(scan_api(r))
            assert False, "ValueError not raised"
        except ValueError:
            e = sys.exc_info()[1]
            assert str(e).startswith("Path is too long")

    def test_handle_request(self):
        class MyRoot(WSRoot):
            @expose()
            def touch(self):
                pass

        p = DummyProtocol()
        r = MyRoot(protocols=[p])

        app = webtest.TestApp(r.wsgiapp())

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

        app = webtest.TestApp(r.wsgiapp())

        res = app.get('/', expect_errors=True)
        print(res.status, res.body)
        assert res.status_int == 400

    def test_no_available_protocol(self):
        r = WSRoot()

        app = webtest.TestApp(r.wsgiapp())

        res = app.get('/', expect_errors=True)
        assert res.status_int == 500
        print(res.body)
        assert res.body.find(
            b("None of the following protocols can handle this request")) != -1

    def test_return_content_type_guess(self):
        class DummierProto(DummyProtocol):
            content_types = ['text/xml', 'text/plain']

        r = WSRoot([DummierProto()])

        app = webtest.TestApp(r.wsgiapp())

        res = app.get('/', expect_errors=True, headers={
            'Accept': 'text/xml,q=0.8'})
        assert res.status_int == 400
        assert res.content_type == 'text/xml', res.content_type

        res = app.get('/', expect_errors=True, headers={
            'Accept': 'text/plain'})
        assert res.status_int == 400
        assert res.content_type == 'text/plain', res.content_type

    def test_double_expose(self):
        try:
            class MyRoot(WSRoot):
                @expose()
                @expose()
                def atest(self):
                    pass
            assert False, "A ValueError should have been raised"
        except ValueError:
            pass

    def test_multiple_expose(self):
        class MyRoot(WSRoot):
            def multiply(self, a, b):
                return a * b

            mul_int = expose(int, int, int, wrap=True)(multiply)

            mul_float = expose(
                float, float, float,
                wrap=True)(multiply)

            mul_string = expose(
                wsme.types.text, wsme.types.text, int,
                wrap=True)(multiply)

        r = MyRoot(['restjson'])

        app = webtest.TestApp(r.wsgiapp())

        res = app.get('/mul_int?a=2&b=5', headers={
            'Accept': 'application/json'
        })

        self.assertEquals(res.body, b('10'))

        res = app.get('/mul_float?a=1.2&b=2.9', headers={
            'Accept': 'application/json'
        })

        self.assertEquals(res.body, b('3.48'))

        res = app.get('/mul_string?a=hello&b=2', headers={
            'Accept': 'application/json'
        })

        self.assertEquals(res.body, b('"hellohello"'))


class TestFunctionDefinition(unittest.TestCase):

    def test_get_arg(self):
        def myfunc(self):
            pass

        fd = FunctionDefinition(FunctionDefinition)
        fd.arguments.append(FunctionArgument('a', int, True, None))

        assert fd.get_arg('a').datatype is int
        assert fd.get_arg('b') is None
