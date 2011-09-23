import __builtin__

if '_' not in __builtin__.__dict__:
    __builtin__._ = lambda s: s


class ClientSideError(RuntimeError):
    def __unicode__(self):
        return RuntimeError.__str__(self)

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')


class InvalidInput(ClientSideError):
    def __init__(self, fieldname, value, msg=''):
        self.fieldname = fieldname
        self.value = value
        self.msg = msg

    def __unicode__(self):
        return _(u"Invalid input for field/attribute %s. Value: '%s'. %s") % (
                 self.fieldname, self.value, self.msg)


class MissingArgument(ClientSideError):
    def __init__(self, argname, msg=''):
        self.argname = argname
        self.msg = msg

    def __unicode__(self):
        return _(u'Missing argument: "%s"%s') % (
            self.argname, self.msg and ": " + self.msg or "")


class UnknownArgument(ClientSideError):
    def __init__(self, argname, msg=''):
        self.argname = argname
        self.msg = msg

    def __unicode__(self):
        return _(u'Unknown argument: "%s"%s') % (
            self.argname, self.msg and ": " + self.msg or "")


class UnknownFunction(ClientSideError):
    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return _(u"Unknown function name: %s") % (self.name)
