Changes
=======

0.1.1 (next)
------------

*   Changed the internal API by introducing a CallContext object.
    It makes it easier to implement some protocols that have
    a transaction or call id that has to be returned. It will also
    make it possible to implement batch-calls in a later version.

*   More test coverage.

*   Fix a problem with array attribute types not being registered.

*   Fix the mandatory / default detection on function arguments.

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
