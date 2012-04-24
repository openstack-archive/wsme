import six
from six.moves import builtins

if '_' not in builtins.__dict__:
    builtins._ = lambda s: s


class ClientSideError(RuntimeError):
    @property
    def faultstring(self):
        return str(self)


class InvalidInput(ClientSideError):
    def __init__(self, fieldname, value, msg=''):
        self.fieldname = fieldname
        self.value = value
        self.msg = msg

    @property
    def faultstring(self):
        return _(six.u(
            "Invalid input for field/attribute %s. Value: '%s'. %s")) % (
                 self.fieldname, self.value, self.msg)


class MissingArgument(ClientSideError):
    def __init__(self, argname, msg=''):
        self.argname = argname
        self.msg = msg

    @property
    def faultstring(self):
        return _(six.u('Missing argument: "%s"%s')) % (
            self.argname, self.msg and ": " + self.msg or "")


class UnknownArgument(ClientSideError):
    def __init__(self, argname, msg=''):
        self.argname = argname
        self.msg = msg

    @property
    def faultstring(self):
        return _(six.u('Unknown argument: "%s"%s')) % (
            self.argname, self.msg and ": " + self.msg or "")


class UnknownFunction(ClientSideError):
    def __init__(self, name):
        self.name = name

    @property
    def faultstring(self):
        return _(six.u("Unknown function name: %s")) % (self.name)
