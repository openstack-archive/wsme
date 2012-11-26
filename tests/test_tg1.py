import wsme.tg1
from wsme import WSRoot
from wsme.tg1 import wsexpose, wsvalidate

from turbogears.controllers import RootController

import unittest

import simplejson


from wsmeext.soap.tests import test_soap


class WSController(WSRoot):
    pass


class Root(RootController):
    ws = WSController(webpath='/ws')
    ws.addprotocol(
        'soap',
        tns=test_soap.tns,
        typenamespace=test_soap.typenamespace
    )
    ws = wsme.tg1.adapt(ws)

    @wsexpose(int)
    @wsvalidate(int, int)
    def multiply(self, a, b):
        return a * b


import cherrypy

from turbogears import testutil, config, startup


class TestController(unittest.TestCase):
    root = Root

    def setUp(self):
        "Tests the output of the index method"
        self.app = testutil.make_app(self.root)
        print cherrypy.root
        testutil.start_server()

    def tearDown(self):
        # implementation copied from turbogears.testutil.stop_server.
        # The only change is that cherrypy.root is set to None
        # AFTER stopTurbogears has been called so that wsme.tg1
        # can correctly uninstall its filter.
        if config.get("cp_started"):
            cherrypy.server.stop()
            config.update({"cp_started": False})

        if config.get("server_started"):
            startup.stopTurboGears()
            config.update({"server_started": False})

    def test_restcall(self):
        response = self.app.post("/multiply",
            simplejson.dumps({'a': 5, 'b': 10}),
            {'Content-Type': 'application/json'}
        )
        print response
        assert simplejson.loads(response.body) == 50

        response = self.app.post("/multiply",
            simplejson.dumps({'a': 5, 'b': 10}),
            {'Content-Type': 'application/json', 'Accept': 'application/json'}
        )
        print response
        assert simplejson.loads(response.body) == 50

        response = self.app.post("/multiply",
            simplejson.dumps({'a': 5, 'b': 10}),
            {'Content-Type': 'application/json', 'Accept': 'text/javascript'}
        )
        print response
        assert simplejson.loads(response.body) == 50

        response = self.app.post("/multiply",
            simplejson.dumps({'a': 5, 'b': 10}),
            {'Content-Type': 'application/json',
             'Accept': 'text/xml'}
        )
        print response
        assert response.body == "<result>50</result>"

    def test_soap_wsdl(self):
        wsdl = self.app.get('/ws/api.wsdl').body
        print wsdl
        assert 'multiply' in wsdl

    def test_soap_call(self):
        ts = test_soap.TestSOAP('test_wsdl')
        ts.app = self.app
        ts.ws_path = '/ws'

        print ts.ws_path
        assert ts.call('multiply', a=5, b=10, _rt=int) == 50
