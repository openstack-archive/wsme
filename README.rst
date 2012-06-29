Web Services Made Easy
======================

Introduction
------------

Web Service Made Easy (WSME) is a very easy way to implement webservices
in your python web application.
It is originally a rewrite of TGWebServices
with focus on extensibility, framework-independance and better type handling.

How Easy ?
~~~~~~~~~~

::
    
    from wsme import WSRoot, expose, validate

    class MyService(WSRoot):
        @expose(unicode)
        @validate(unicode)
        def hello(self, who=u'World'):
            return u"Hello {0} !".format(who)


With this published at the ``/ws`` path of your application, you can access
your hello function in various protocols:

.. list-table::
    :header-rows: 1

    * - URL
      - Returns
    
    * - ``http://<server>/ws/hello.json?who=you``
      - ``"Hello you !"``

    * - ``http://<server>/ws/hello.xml``
      - ``<result>Hello World !</result>``

    * - ``http://<server>/ws/api.wsdl``
      - A WSDL description for any SOAP client.


Main features
~~~~~~~~~~~~~

-   Very simple API.
-   Supports user-defined simple and complex types.
-   Multi-protocol : REST+Json, REST+XML, SOAP, ExtDirect and more to come.
-   Extensible : easy to add more protocols or more base types.
-   Framework independance : adapters are provided to easily integrate
    your API in any web framework, for example a wsgi container,
    turbogears...
-   Very few runtime dependencies: webob, simplegeneric
    (+ Genshi if you use SOAP).
-   Integration in `Sphinx`_ for making clean documentation with
    wsme.sphinxext (work in progress).

Install
~~~~~~~

::

    easy_install WSME

Changes
~~~~~~~

-   Read the `Changelog`_

Getting Help
~~~~~~~~~~~~

-   Read the `WSME Documentation`_.
-   Questions about WSME should go to the `python-wsme mailinglist`_.

Contribute
~~~~~~~~~~

:Report issues: `WSME issue tracker`_
:Source code: hg clone https://bitbucket.org/cdevienne/wsme/
:Jenkins: https://jenkins.shiningpanda.com/wsme/

.. _Changelog: http://packages.python.org/WSME/changes.html
.. _python-wsme mailinglist: http://groups.google.com/group/python-wsme
.. _WSME Documentation: http://packages.python.org/WSME/
.. _WSME issue tracker: https://bitbucket.org/cdevienne/wsme/issues?status=new&status=open
.. _Sphinx: http://sphinx.pocoo.org/
