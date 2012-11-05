import wsme.tg1
from wsme import WSRoot
from wsme.tg1 import wsexpose, wsvalidate

from turbogears.controllers import RootController

import unittest

import simplejson


class WSController(WSRoot):
    pass


class Root(RootController):
    ws = wsme.tg1.adapt(
            WSController(webpath='/ws', protocols=['restjson']))

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

    def test_simplecall(self):
        response = self.app.post("/multiply",
            simplejson.dumps({'a': 5, 'b': 10}),
            {'Content-Type': 'application/json'})
        print response
        assert simplejson.loads(response.body) == 50
