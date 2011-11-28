API
===

Public API
----------

:mod:`wsme` -- Essentials
~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: wsme

.. autoclass:: WSRoot
    :members:

.. autoclass:: expose
.. autoclass:: validate

.. autoclass:: wsproperty
.. autoclass:: wsattr

.. data:: Unset

    Default value of the complex type attributes.

Internals
---------

:mod:`wsme.types` -- Types
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: wsme.types
    :members: register_type

:mod:`wsme.api` -- API related api
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: wsme.api
    :members: scan_api, FunctionArgument, FunctionDefinition

:mod:`wsme.protocols.rest` -- REST protocol commons
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: wsme.protocols.rest
    :members:

