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


def iswsmefunction(f):
    return hasattr(f, '_wsme_definition')


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

        #: If the body carry the datas of a single argument, its type
        self.body_type = None

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
        if not hasattr(func, '_wsme_definition'):
            fd = FunctionDefinition(func)
            func._wsme_definition = fd

        return func._wsme_definition

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
    def __init__(self, return_type=None, body=None, **options):
        self.return_type = return_type
        self.body_type = body
        self.options = options

    def __call__(self, func):
        fd = FunctionDefinition.get(func)
        if fd.extra_options is not None:
            raise ValueError("This function is already exposed")
        fd.return_type = self.return_type
        fd.body_type = self.body_type
        fd.extra_options = self.options
        return func


class sig(object):
    def __init__(self, return_type, *param_types, **options):
        self.expose = expose(return_type, **options)
        self.validate = validate(*param_types)

    def __call__(self, func):
        func = self.expose(func)
        func = self.validate(func)
        return func


class pexpose(object):
    def __init__(self, return_type=None, contenttype=None):
        self.return_type = return_type
        self.contenttype = contenttype

    def __call__(self, func):
        fd = FunctionDefinition.get(func)
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
        fd = FunctionDefinition.get(func)
        args, varargs, keywords, defaults = inspect.getargspec(func)
        if args[0] == 'self':
            args = args[1:]
        param_types = list(self.param_types)
        if fd.body_type is not None:
            param_types.append(fd.body_type)
        for i, argname in enumerate(args):
            datatype = param_types[i]
            mandatory = defaults is None or i < (len(args) - len(defaults))
            default = None
            if not mandatory:
                default = defaults[i - (len(args) - len(defaults))]
            fd.arguments.append(FunctionArgument(argname, datatype,
                                                 mandatory, default))
        return func
