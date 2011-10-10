Integrating with a Framework
============================

Turbogears 1.x
--------------

.. module:: wsme.tg1

wsme.tg1 provides a WSRoot controller that can be part of your
controller tree.

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
        ws = WSController(webpath='ws', protocols=['REST+Json'])

        # ...
