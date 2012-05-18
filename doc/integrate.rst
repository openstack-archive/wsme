Integrating with a Framework
============================

WSGI Application
----------------

:mod:`wsme.wsgi` -- WSGI adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: wsme.wsgi

.. function:: adapt

    Returns a wsgi application that serve a :class:`wsme.controller.WSRoot`.

Example
~~~~~~~

.. code-block:: python

    from wsme import *
    import wsme.wsgi

    class MyRoot(WSRoot):
        @expose(unicode)
        def helloworld(self):
            return u"Hello World !"

    application = wsme.wsgi.adapt(
            MyRoot(protocols=['restjson']))


Pyramid
-------

The WSRoot._handle_request method is a valid pyramid view:

.. code-block:: python

    from paste.httpserver import serve
    from pyramid.config import Configurator

    from wsme import *

    class WSController(WSRoot):
        @expose(int)
        @validate(int, int)
        def multiply(self, a, b):
            return a * b

    myroot = WSRoot()
    myroot.addprotocol('restjson')
    myroot.addprotocol('extdirect')

    if __name__ == '__main__':
        config = Configurator()
        config.add_route('ws', '')
        config.add_view(wsroot._handle_request, route_name='ws')
        app = config.make_wsgi_app()
        serve(app, host='0.0.0.0')

Turbogears 1.x
--------------

:mod:`wsme.tg1` -- TG1 adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: wsme.tg1

.. class:: Controller(wsroot)

    A TG1 Controller that publish a :class:`wsme.WSRoot`.

.. function:: adapt

    Returns a :class:`Controller` that publish a :class:`wsme.WSRoot`.

:mod:`wsme.tg15` -- TG 1.5 adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: wsme.tg15

.. class:: Controller(wsroot)

    A TG1 Controller that publish a :class:`wsme.WSRoot`.

.. function:: adapt

    Returns a :class:`Controller` that publish a :class:`wsme.WSRoot`.

Example
~~~~~~~

In a freshly quickstarted tg1 application (let's say, wsmedemo),
the prefered way is the following :

Create a new file, "wsmedemo/ws.py" :

.. code-block:: python

    import wsme.tg1
    from wsme import expose, validate, WSRoot

    class WSController(WSRoot):
        @expose(int)
        @validate(int, int)
        def multiply(self, a, b):
            return a * b

Insert the ws controller in the controller tree, (file controllers.py):

.. code-block:: python

    # ...

    from wsmedemo.ws import WSController
    
    import wsme.tg1

    class Root(controllers.RootController):
        ws = wsme.tg1.adapt(
            WSController(webpath='/ws', protocols=['restjson']))

        # ...
