import inspect

__all__ = ['expose', 'validate']

APIPATH_MAXLEN = 20


def scan_api(controller, path=[]):
    """
    Recursively iterate a controller api entries, while setting
    their :attr:`FunctionDefinition.path`.
    """
    for name in dir(controller):
        if name.startswith('_'):
            continue
        a = getattr(controller, name)
        if inspect.ismethod(a):
            if hasattr(a, '_wsme_definition'):
                yield path + [name], a._wsme_definition
        elif inspect.isclass(a):
            continue
        else:
            if len(path) > APIPATH_MAXLEN:
                raise ValueError("Path is too long: " + str(path))
            for i in scan_api(a, path + [name]):
                yield i


class FunctionArgument(object):
    """
    An argument definition of an api entry
    """
    def __init__(self, name, datatype, mandatory, default):
        #: argument name
        self.name = name

        #: Data type
        self.datatype = datatype

        #: True if the argument is mandatory
        self.mandatory = mandatory

        #: Default value if argument is omitted
        self.default = default

    def resolve_type(self, registry):
        self.datatype = registry.resolve_type(self.datatype)


def funcproxy(func):
    """
    A very simple wrapper for exposed function.

    It will carry the FunctionDefinition in place of the
    decorared function so that a same function can be exposed
    several times (for example a parent function can be exposed
    in different ways in the children classes).

    The returned function also carry a ``_original_func`` attribute
    so that it can be inspected if needed.
    """
    def newfunc(*args, **kw):
        return func(*args, **kw)
    newfunc._is_wsme_funcproxy = True
    newfunc._original_func = func
    newfunc.__doc__ = func.__doc__
    newfunc.__name__ = func.__name__
    return newfunc


def isfuncproxy(func):
    """
    Returns True if ``func`` is already a function proxy.
    """
    return getattr(func, '_is_wsme_funcproxy', False)


class FunctionDefinition(object):
    """
    An api entry definition
    """
    def __init__(self, func):
        #: Function name
        self.name = func.__name__

        #: Function documentation
        self.doc = func.__doc__

        #: Return type
        self.return_type = None

        #: The function arguments (list of :class:`FunctionArgument`)
        self.arguments = []

        #: True if this function is exposed by a protocol and not in
        #: the api tree, which means it is not part of the api.
        self.protocol_specific = False

        #: Override the contenttype of the returned value.
        #: Make sense only with :attr:`protocol_specific` functions.
        self.contenttype = None

        #: Dictionnary of protocol-specific options.
        self.extra_options = None

    @classmethod
    def get(cls, func):
        """
        Returns the :class:`FunctionDefinition` of a method.
        """
        if not isfuncproxy(func):
            fd = FunctionDefinition(func)
            func = funcproxy(func)
            func._wsme_definition = fd

        return func, func._wsme_definition

    def get_arg(self, name):
        """
        Returns a :class:`FunctionArgument` from its name
        """
        for arg in self.arguments:
            if arg.name == name:
                return arg
        return None

    def resolve_types(self, registry):
        self.return_type = registry.resolve_type(self.return_type)
        for arg in self.arguments:
            arg.resolve_type(registry)


class expose(object):
    """
    Decorator that expose a function.

    :param return_type: Return type of the function

    Example::

        class MyController(object):
            @expose(int)
            def getint(self):
                return 1
    """
    def __init__(self, return_type=None, **options):
        self.return_type = return_type
        self.options = options

    def __call__(self, func):
        func, fd = FunctionDefinition.get(func)
        if fd.extra_options is not None:
            raise ValueError("This function is already exposed")
        fd.return_type = self.return_type
        fd.extra_options = self.options
        return func


class pexpose(object):
    def __init__(self, return_type=None, contenttype=None):
        self.return_type = return_type
        self.contenttype = contenttype

    def __call__(self, func):
        func, fd = FunctionDefinition.get(func)
        fd.return_type = self.return_type
        fd.protocol_specific = True
        fd.contenttype = self.contenttype
        return func


class validate(object):
    """
    Decorator that define the arguments types of a function.


    Example::

        class MyController(object):
            @expose(str)
            @validate(datetime.date, datetime.time)
            def format(self, d, t):
                return d.isoformat() + ' ' + t.isoformat()
    """
    def __init__(self, *param_types):
        self.param_types = param_types

    def __call__(self, func):
        func, fd = FunctionDefinition.get(func)
        args, varargs, keywords, defaults = inspect.getargspec(
                func._original_func)
        if args[0] == 'self':
            args = args[1:]
        for i, argname in enumerate(args):
            datatype = self.param_types[i]
            mandatory = defaults is None or i < (len(args) - len(defaults))
            default = None
            if not mandatory:
                default = defaults[i - (len(args) - len(defaults))]
            fd.arguments.append(FunctionArgument(argname, datatype,
                                                 mandatory, default))
        return func
