Protocols
=========

REST+Json
---------

:name: ``'restjson'``

REST+XML
--------

:name: ``'restxml'``

SOAP
----

:name: ``'soap'``
:package: WSME-Soap

Options
~~~~~~~

:tns: Type namespace

ExtDirect
---------

:name: ``extdirect``
:package: WSME-ExtDirect

Implements the `Ext Direct`_ protocol.

The provider definition is made available at the ``/extdirect/api.js`` subpath.

The router url is ``/extdirect/router[/subnamespace]``.

Options
~~~~~~~

:namespace: Base namespace of the api. Used for the provider definition.
:params_notation: Default notation for function call parameters. Can be
    overriden for individual functions by adding the
    ``extdirect_params_notation`` extra option to @expose.

    The possible notations are :

    -   ``'named'``  -- The function will take only one object parameter
        in which each property will be one of the parameters.
    -   ``'positional'`` -- The function will take as many parameters as
        the function has, and their position will determine which parameter
        they are.

expose extra options
~~~~~~~~~~~~~~~~~~~~

:extdirect_params_notation: Override the params_notation for a particular
    function.

.. _Ext Direct: http://www.sencha.com/products/extjs/extdirect
