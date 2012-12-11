Changes
=======

0.5 (next)
----------

*   Introduce a new kind of adapters that rely on the framework routing.
    Adapters are provided for Pecan, TurboGears and cornice.

*   Reorganised the rest protocol implementation to ease the implementation of
    adapters that rely only on the host framework routing system.

*   The default rest ``@expose`` decorator does not wrap the decorated function
    anymore. If needed to expose a same function several times, a parameter
    ``multiple_expose=True`` has been introduced.

*   Remove the wsme.release module

*   Fix == operator on ArrayType

*   Adapted the wsme.sphinxext module to work with the function exposed by the
    ``wsme.pecan`` adapter.
   
*   Allow promotion of ``int`` to ``float`` on float attributes (Doug Hellman)

*   Add a ``samples_slot`` option to the ``.. autotype`` directive to
    choose where the data samples whould be inserted (Doug Hellman).

*   Add ``sample()`` to ArrayType and DictType (Doug Hellman).

0.4 (2012-10-15)
----------------

*   Automatically converts unicode strings to/from ascii bytes.

*   Use d2to1 to simplify setup.py.

*   Implements the SPORE specification.

*   Fixed a few things in the documentation

0.4b1 (2012-09-14)
------------------

*   Now supports Python 3.2

*   String types handling is clearer.

*   New :class:`wsme.types.File` type.

*   Supports cross-referenced types.

*   Various bugfixes.

*   Tests code coverage is now over 95%.

*   RESTful protocol can now use the http method.

*   UserTypes can now be given a name that will be used in the
    documentation.

*   Complex types can inherit :class:`wsme.types.Base`. They will
    have a default constructor and be registered automatically.

*   Removed the wsme.wsgi.adapt function if favor of
    :meth:`wsme.WSRoot.wsgiapp`

Extensions
~~~~~~~~~~

wsme-soap
    *   Function names now starts with a lowercase letter.

    *   Fixed issues with arrays (issue #3).

    *   Fixed empty array handling.


wsme-sqlalchemy
    This new extension makes it easy to create webservices on top
    of a SQLAlchemy set of mapped classes.

wsme-extdirect
    *   Implements server-side DataStore
        (:class:`wsmeext.extdirect.datastore.DataStoreController`).

    *   Add Store and Model javascript definition auto-generation

    *   Add Store server-side based on SQLAlchemy mapped classes
        (:class:`wsmeext.extdirect.sadatastore.SADataStoreController`).

0.3 (2012-04-20)
----------------

*   Initial Sphinx integration.

0.3b2 (2012-03-29)
------------------

*   Fixed issues with the TG1 adapter.

*   Now handle dict and UserType types as GET/POST params.

*   Better handling of application/x-www-form-urlencoded encoded POSTs
    in rest protocols.

*   :class:`wsattr` now takes a 'default' parameter that will be returned
    instead of 'Unset' if no value has been set.

0.3b1 (2012-01-19)
------------------

*   Per-call database transaction handling.

*   :class:`Unset` is now imported in the wsme module

*   Attributes of complex types can now have a different name in
    the public api and in the implementation.

*   Complex arguments can now be sent as GET/POST params in the rest
    protocols.

*   The restjson protocol do not nest the results in an object anymore.

*   Improved the documentation

*   Fix array attributes validation.

*   Fix date|time parsing errors.

*   Fix Unset values validation.

*   Fix registering of complex types inheriting form already
    registered complex types.

*   Fix user types, str and None values encoding/decoding.

0.2.0 (2011-10-29)
------------------

*   Added batch-calls abilities.

*   Introduce a :class:`UnsetType` and a :data:`Unset` constant
    so that non-mandatory attributes can remain unset (which is
    different from null).

*   Fix: If a complex type was only used as an input type, it was
    not registered.

*   Add support for user types.

*   Add an Enum type (which is a user type).

*   The 'binary' type is now a user type.

*   Complex types:

    -   Fix inspection of complex types with inheritance.

    -   Fix inspection of self-referencing complex types.

    -   wsattr is now a python Descriptor, which makes it possible
        to retrieve the attribute definition on a class while
        manipulating values on the instance.
    
    -   Add strong type validation on assignment (made possible by
        the use of Descriptors).

*   ExtDirect:

    -   Implements batch calls

    -   Fix None values conversion

    -   Fix transaction result : 'action' and 'method' were missing.

0.1.1 (2011-10-20)
------------------

*   Changed the internal API by introducing a CallContext object.
    It makes it easier to implement some protocols that have
    a transaction or call id that has to be returned. It will also
    make it possible to implement batch-calls in a later version.

*   More test coverage.

*   Fix a problem with array attribute types not being registered.

*   Fix the mandatory / default detection on function arguments.

*   Fix issues with the SOAP protocol implementation which should now
    work properly with a suds client.

*   Fix issues with the ExtDirect protocol implementation.

0.1.0 (2011-10-14)
------------------

*   Protocol insertion order now influence the protocol selection

*   Move the soap protocol implementation in a separate lib,
    WSME-Soap

*   Introduce a new protocol ExtDirect in the WSME-ExtDirect lib.

0.1.0a4 (2011-10-12)
--------------------

*   Change the way framework adapters works. Now the adapter modules
    have a simple adapt function that adapt a :class:`wsme.WSRoot`
    instance. This way a same root can be integrated in several
    framework.

*   Protocol lookup now use entry points in the group ``[wsme.protocols]``.

0.1.0a3 (2011-10-11)
--------------------

*   Add specialised WSRoot classes for easy integration as a
    WSGI Application (:class:`wsme.wsgi.WSRoot`) or a
    TurboGears 1.x controller (:class:`wsme.tg1.WSRoot`).

*   Improve the documentation.

*   More unit tests and code-coverage.

0.1.0a2 (2011-10-07)
--------------------

*   Added support for arrays in all the protocols

0.1.0a1 (2011-10-04)
--------------------

Initial public release.
