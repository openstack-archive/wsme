TODO
====

WSME is a work in progress. Here is a list of things that should
be done :

-   Improve the protocol factory -> we should not have to import the
    module manually except if we need special parameters.
    For example, calling WSRoot.addprotocol('restjson') should just
    work, wether or not the wsme.protocols.restjson has been imported yet.

-   Fix the SOAP protocol : the namespace for parameters is not correctly
    handle -> some tests with suds should help.

-   Implement new protocols :

    -   json-rpc

    -   xml-rpc

    -   ExtDirect
 
-   Implement adapters for other framework :

    -   TurboGears 2

    -   Pyramid

    -   Pylons

    -   CherryPy

    -   others ?

-   Add unittests for adapters

