Integrating with a Framework
============================

WSGI Application
----------------

:mod:`wsme.wsgi` -- WSGI adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: wsme.wsgi

.. class:: WSRoot

    A :class:`wsme.controller.WSRoot` that act as a WSGI application.

Example
~~~~~~~

.. code-block:: python

    from wsme import expose, validate
    from wsme.wsgi import WSRoot
    from wsme.protocols import restjson

    class MyRoot(WSRoot):
        @expose(unicode)
        def helloworld(self):
            return u"Hello World !"

    application = MyRoot(protocols=['REST+Json'])

Turbogears 1.x
--------------

:mod:`wsme.tg1` -- TG1 adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: wsme.tg1

.. class:: WSRoot

    A :class:`wsme.controller.WSRoot` that can be inserted in a TG1
    controller tree.

Example
~~~~~~~

In a freshly quickstarted tg1 application (let's say, wsmedemo),
the prefered way is the following :

Create a new file, "wsmedemo/ws.py" :

.. code-block:: python

    from wsme.tg1 import WSRoot
    from wsme import expose, validate

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

    class Root(controllers.RootController):
        ws = WSController(webpath='/ws', protocols=['REST+Json'])

        # ...
