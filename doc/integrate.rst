Integrating with a Framework
============================

General considerations
----------------------

Using WSME within another framework providing its own REST capabilities is
generally done by using a specific decorator to declare the function signature,
in addition to the framework own way of declaring exposed functions.

This decorator can have two different names depending on the adapter.

``@wsexpose``
    This decorator will declare the function signature *and*
    take care of calling the adequate decorators of the framework.

    Generally this decorator is provided for frameworks that use
    object-dispatch controllers, like Pecan_ or Turbogears_. 

``@signature``
    This decorator only set the function signature and returns a function
    that can be used by the host framework as a REST request target.

    Generally this decorator is provided for frameworks that expects functions
    taking a request object as a single parameter and returning a response
    object. This is the case of cornice_.

Additionnaly, if you want to enable additionnal protocols, you will need to
mount a :class:`WSRoot` instance somewhere in the application, generally
``/ws``. This subpath will then handle the additional protocols.

.. note::

    Not all the adapters are at the same level of maturity.

WSGI Application
----------------

The :func:`wsme.WSRoot.wsgiapp` function of WSRoot returns a wsgi
application.

Example
~~~~~~~

The following example assume the REST protocol will be entirely handled by
WSME, which is the case if you write a WSME standalone application.

.. code-block:: python

    from wsme import WSRoot, expose


    class MyRoot(WSRoot):
        @expose(unicode)
        def helloworld(self):
            return u"Hello World !"

    root = MyRoot(protocols=['restjson'])
    application = root.wsgiapp()


Bottle
------

No adapter is provided yet but it should not be hard to write one, by taking
example on the cornice adapter.

This example only show how to mount a WSRoot inside a bottle application.

.. code-block:: python

    import bottle
    import wsme

    class MyRoot(wsme.WSRoot):
        @wsme.expose(unicode)
        def helloworld(self):
            return u"Hello World !"

    root = MyRoot(webpath='/ws', protocols=['restjson'])

    bottle.mount('/ws', root.wsgiapp())
    bottle.run()

Pyramid
-------

The recommended way of using WSME inside Pyramid is to use cornice.

Cornice
-------

Pecan
-----

.. warning::

    A pecan application is not able to mount another wsgi application on a
    subpath. For that reason, additional protocols are not supported for now.

Api
~~~

.. module:: wsmeext.pecan

.. function:: wsexpose(return_type, \*arg_types, **options)

    See @\ :func:`signature` for parameters documentation.

    Can be used on any function of a pecan
    `RestController <http://pecan.readthedocs.org/en/latest/rest.html>`_
    instead of the expose decorator from Pecan.

Example
~~~~~~~

The `example <http://pecan.readthedocs.org/en/latest/rest.html#nesting-restcontroller>`_ from the Pecan documentation becomes:

.. code-block:: python

    from wsmeext.pecan import wsexpose
        
    class BooksController(RestController):
        @wsexpose(Book, int, int)
        def get(self, author_id, id):
            # ..

        @wsexpose(Book, int, int, body=Book)
        def put(self, author_id, id, book):
            # ..

    class AuthorsController(RestController):
            books = BooksController()

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

.. _Pecan: http://pecanpy.org/
.. _TurboGears: http://www.turbogears.org/
.. _cornice: http://pypi.python.org/pypi/cornice
