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
    from wsme.protocols import restjson

    class MyRoot(WSRoot):
        @expose(unicode)
        def helloworld(self):
            return u"Hello World !"

    application = wsme.wsgi.adapt(
            MyRoot(protocols=['REST+Json']))

Turbogears 1.x
--------------

:mod:`wsme.tg1` -- TG1 adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: wsme.tg1

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
    
    # make sure the wanted protocols are known
    import wsme.protocols.restjson
    import wsme.tg1

    class Root(controllers.RootController):
        ws = wsme.tg1.adapt(
            WSController(webpath='/ws', protocols=['REST+Json']))

        # ...
