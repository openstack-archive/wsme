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
    :members: FunctionArgument, FunctionDefinition

:mod:`wsme.rest.args` -- REST protocol argument handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: wsme.rest.args
    :members:

