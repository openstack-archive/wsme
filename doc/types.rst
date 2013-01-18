Types
=====

3 kinds of data types can be used as input or output by WSME.

Native types
------------

The native types are a fixed set of standard python types that
the different protocols will map to theirs own basic types.

The native types are :

    -   .. wsme:type:: bytes
    
            A pure-ascii string (:py:class:`wsme.types.bytes` which is
            :py:class:`str` in Python 2 and :py:class:`bytes` in Python 3).
            

    -   .. wsme:type:: text

            A unicode string (:py:class:`wsme.types.text` which is
            :py:class:`unicode` in Python 2 and :py:class:`str` in Python 3).

    -   .. wsme:type:: int
    
            An integer (:py:class:`int`)

    -   .. wsme:type:: float
    
            A float (:py:class:`float`)

    -   .. wsme:type:: bool
    
            A boolean (:py:class:`bool`)

    -   .. wsme:type:: Decimal
    
            A fixed-width decimal (:py:class:`decimal.Decimal`)

    -   .. wsme:type:: date
            
            A date (:py:class:`datetime.date`)

    -   .. wsme:type:: datetime

            A date and time (:py:class:`datetime.datetime`)

    -   .. wsme:type:: time
    
            A time (:py:class:`datetime.time`)

    -   Arrays -- This is a special case. When stating a list
        datatype, always state its content type as the unique element
        of a list. Example::

            class SomeWebService(object):
                @expose([str])
                def getlist(self):
                    return ['a', 'b', 'c']

    -   Dictionnaries -- Statically typed mapping are allowed. When exposing
        a dictionnary datatype, you can specify the key and value types,
        with a restriction on the key value that must be a 'pod' type.
        Example::

            class SomeType(object):
                amap = {str: SomeOthertype}

There are other types that are supported out of the box, see
the :ref:`pre-defined-user-types`.

User types
----------

User types allow to define new almost-native types.

The idea is that you may have python data that should be transported as native
types by the different protocols, but needs conversion to/from this basetypes,
or needs to validate data integrity.

To define a user type, you just have to inherit from
:class:`wsme.types.UserType` and instanciate your new class. This instance
will be your new type and can be used as @\ :class:`wsme.expose` or
@\ :class:`wsme.validate` parameters.

Note that protocols can choose to specifically handle a user type or
a base class of user types. This is case with the two pre-defined
user types, :class:`wsme.types.Enum` and :data:`wsme.types.binary`.

.. _pre-defined-user-types:

Pre-defined user types
~~~~~~~~~~~~~~~~~~~~~~

WSME provides some pre-defined user types:

-   :class:`binary <wsme.types.binary>` -- for transporting binary data as
    base64 strings.
-   :class:`Enum <wsme.types.Enum>` -- enforce that the values belongs to a
    pre-defined list of values.

These types are good examples of how to define user types. Have
a look at their source code !

Here is a little example that combines :class:`binary <wsme.types.binary>`
and :class:`Enum <wsme.types.Enum>`::
    
    ImageKind = Enum(str, 'jpeg', 'gif')

    class Image(object):
        name = unicode
        kind = ImageKind
        data = binary

.. data:: wsme.types.binary

    The :class:`wsme.types.BinaryType` instance to use when you need to
    transfert base64 encoded data.

.. autoclass:: wsme.types.BinaryType

.. autoclass:: wsme.types.Enum


Complex types
-------------

Complex types are structured types. They are defined as simple python classes
and will be mapped to adequate structured types in the various protocols.

A base class for structured types is proposed, :class:`wsme.types.Base`,
but is not mandatory. The only thing it add is a default constructor.

The attributes that are set at the class level will be used by WSME to discover
the structure. These attributes can be:

    -   A datatype -- Any native, user or complex type.
    -   A :class:`wsattr <wsme.wsattr>` -- Allow to add more information about
        the attribute, for example if it is mandatory.
    -   A :class:`wsproperty <wsme.wsproperty>` -- Special typed property. Works
        like standard properties with additional properties like
        :class:`wsattr <wsme.wsattr>`.

Attributes having a leading '_' in there name will be ignored, as well as the
ones that are none of the above list. It means the type can have functions,
they will not get in the way.

Example
~~~~~~~

::

    Gender = wsme.types.Enum(str, 'male', 'female')
    Title = Ewsme.types.num(str, 'M', 'Mrs')

    class Person(wsme.types.Base):
        lastname = wsme.types.wsattr(unicode, mandatory=True)
        firstname = wsme.types.wsattr(unicode, mandatory=True)

        age = int
        gender = Gender
        title = Title

        hobbies = [unicode]

Rules
~~~~~

A few things you should know about complex types:

    -   The class must have a default constructor --
        Since instances of the type will be created by the protocols when
        used as input types, they must be instanciable without any argument.

    -   Complex types are registered automatically 
        (and thus inspected) as soon a they are used in expose or validate,
        even if they are nested in another complex type.

        If for some reasons you need to control when type is inspected, you
        can use :func:`wsme.types.register_type`.

    -   The datatype attributes will be replaced

        When using the 'short' way of defining attributes, ie setting a 
        simple data type, they will be replaced by a wsattr instance.

        So, when you write::

            class Person(object):
                name = unicode

        After type registration the class will actually be equivalent to::

            class Person(object):
                name = wsattr(unicode)

        You can still access the datatype by accessing the attribute on the
        class, along with the other wsattr properties::

            class Person(object):
                name = unicode

            register_type(Person)

            assert Person.name.datatype is unicode
            assert Person.name.key == "name"
            assert Person.name.mandatory is False

    -   The default value of instances attributes is
        :data:`Unset <wsme.Unset>`.

        ::

            class Person(object):
                name = wsattr(unicode)

            p = Person()
            assert p.name is Unset

        This allow the protocol to make a clear distinction between null values
        that will be transmitted, and unset values that will not be transmitted.

        For input values, it allows the code to know if the values were, or not,
        sent by the caller.

    -   When 2 complex types refers to each other, their names can be
        used as datatypes to avoid adding attributes afterwards:

        ::

            class A(object):
                b = wsattr('B')

            class B(object):
                a = wsattr(A)


Predefined Types
~~~~~~~~~~~~~~~~

.. default-domain:: wsme

-   .. autotype:: wsme.types.File
        :members:

