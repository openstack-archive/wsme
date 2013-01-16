import wsme.tg15
from wsme import WSRoot

from turbogears.controllers import RootController

from wsmeext.soap.tests import test_soap

import simplejson


class Root(RootController):
    ws = WSRoot(webpath='/ws')
    ws.addprotocol('soap',
        tns=test_soap.tns,
        typenamespace=test_soap.typenamespace,
        baseURL='/ws/'
    )
    ws = wsme.tg15.adapt(ws)

    @wsme.tg15.wsexpose(int)
    @wsme.tg15.wsvalidate(int, int)
    def multiply(self, a, b):
        return a * b


from turbogears import testutil


class TestController(testutil.TGTest):
    root = Root

#    def setUp(self):
#        "Tests the output of the index method"
#        self.app = testutil.make_app(self.root)
#        #print cherrypy.root
#        testutil.start_server()

#    def tearDown(self):
#        # implementation copied from turbogears.testutil.stop_server.
#        # The only change is that cherrypy.root is set to None
#        # AFTER stopTurbogears has been called so that wsme.tg15
#        # can correctly uninstall its filter.
#        if config.get("cp_started"):
#            cherrypy.server.stop()
#            config.update({"cp_started": False})
#
#        if config.get("server_started"):
#            startup.stopTurboGears()
#            config.update({"server_started": False})

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
        ts.ws_path = '/ws/'

        print ts.ws_path
        assert ts.call('multiply', a=5, b=10, _rt=int) == 50
