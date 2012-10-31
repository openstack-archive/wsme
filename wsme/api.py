import functools
import inspect


def iswsmefunction(f):
    return hasattr(f, '_wsme_definition')


def wrapfunc(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    wrapper._wsme_original_func = f
    return wrapper


def getargspec(f):
    f = getattr(f, '_wsme_original_func', f)
    return inspect.getargspec(f)


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

    def set_options(self, body=None, **extra_options):
        self.body_type = body
        self.extra_options = extra_options

    def set_arg_types(self, argspec, arg_types):
        args, varargs, keywords, defaults = argspec
        if args[0] == 'self':
            args = args[1:]
        arg_types = list(arg_types)
        if self.body_type is not None:
            arg_types.append(self.body_type)
        for i, argname in enumerate(args):
            datatype = arg_types[i]
            mandatory = defaults is None or i < (len(args) - len(defaults))
            default = None
            if not mandatory:
                default = defaults[i - (len(args) - len(defaults))]
            self.arguments.append(FunctionArgument(argname, datatype,
                                                 mandatory, default))


class signature(object):
    def __init__(self, *types, **options):
        self.return_type = types[0] if types else None
        self.arg_types = types[1:] if len(types) > 1 else None
        self.wrap = options.pop('wrap', False)
        self.options = options

    def __call__(self, func):
        argspec = getargspec(func)
        if self.wrap:
            func = wrapfunc(func)
        fd = FunctionDefinition.get(func)
        if fd.extra_options is not None:
            raise ValueError("This function is already exposed")
        fd.return_type = self.return_type
        fd.set_options(**self.options)
        if self.arg_types:
                fd.set_arg_types(argspec, self.arg_types)
        return func

sig = signature
