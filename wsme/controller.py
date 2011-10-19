import inspect
import traceback
import weakref
import logging
import webob
import sys

import pkg_resources

from wsme import exc
from wsme.types import register_type

__all__ = ['expose', 'validate']

log = logging.getLogger(__name__)

registered_protocols = {}

APIPATH_MAXLEN = 20


html_body = """
<html>
<head>
  <style type='text/css'>
    %(css)s
  </style>
</head>
<body>
%(content)s
</body>
</html>
"""


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
        self.extra_options = {}

    @classmethod
    def get(cls, func):
        """
        Returns the :class:`FunctionDefinition` of a method.
        """
        fd = getattr(func, '_wsme_definition', None)
        if fd is None:
            fd = FunctionDefinition(func)
            func._wsme_definition = fd
        return fd

    def get_arg(self, name):
        """
        Returns a :class:`FunctionArgument` from its name
        """
        for arg in self.arguments:
            if arg.name == name:
                return arg
        return None


def register_protocol(protocol):
    registered_protocols[protocol.name] = protocol


def getprotocol(name, **options):
    protocol_class = registered_protocols.get(name)
    if protocol_class is None:
        for entry_point in pkg_resources.iter_entry_points(
                'wsme.protocols', name):
            if entry_point.name == name:
                protocol_class = entry_point.load()
        if protocol_class is None:
            raise ValueError("Cannot find protocol '%s'" % name)
        registered_protocols[name] = protocol_class
    return protocol_class(**options)


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
        register_type(return_type)

    def __call__(self, func):
        fd = FunctionDefinition.get(func)
        fd.return_type = self.return_type
        fd.extra_options = self.options
        return func


class pexpose(object):
    def __init__(self, return_type=None, contenttype=None):
        self.return_type = return_type
        self.contenttype = contenttype
        register_type(return_type)

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
        for i, argname in enumerate(args):
            datatype = self.param_types[i]
            mandatory = defaults is None or i < (len(args) - len(defaults))
            default = None
            if not mandatory:
                default = defaults[i - (len(args) - len(defaults))]
            fd.arguments.append(FunctionArgument(argname, datatype,
                                                 mandatory, default))
        return func


class CallContext(object):
    def __init__(self, request):
        self.request = request
        self.path = None

        self.func = None
        self.funcdef = None


class WSRoot(object):
    """
    Root controller for webservices.

    :param protocols: A list of protocols to enable (see :meth:`addprotocol`)
    :param webpath: The web path where the webservice is published.
    """
    def __init__(self, protocols=[], webpath=''):
        self._debug = True
        self._webpath = webpath
        self.protocols = []
        for protocol in protocols:
            self.addprotocol(protocol)

        self._api = None

    def addprotocol(self, protocol, **options):
        """
        Enable a new protocol on the controller.

        :param protocol: A registered protocol name or an instance
                         of a protocol.
        """
        if isinstance(protocol, str):
            protocol = getprotocol(protocol, **options)
        self.protocols.append(protocol)
        protocol.root = weakref.proxy(self)

    def getapi(self):
        """
        Returns the api description.

        :rtype: list of (path, :class:`FunctionDefinition`)
        """
        if self._api is None:
            self._api = [i for i in scan_api(self)]
        return self._api

    def _get_protocol(self, name):
        for protocol in self.protocols:
            if protocol.name == name:
                return protocol

    def _select_protocol(self, request):
        log.debug("Selecting a protocol for the following request :\n"
                  "headers: %s\nbody: %s", request.headers,
                  len(request.body) > 512
                  and request.body[:512]
                  or request.body)
        protocol = None
        if 'wsmeproto' in request.params:
            return self._get_protocol(request.params['wsmeproto'])
        else:

            for p in self.protocols:
                if p.accept(request):
                    protocol = p
                    break
        return protocol

    def _handle_request(self, request):
        res = webob.Response()
        res_content_type = None
        try:
            protocol = self._select_protocol(request)
            if protocol is None:
                msg = ("None of the following protocols can handle this "
                       "request : %s" % ','.join(
                            (p.name for p in self.protocols)))
                res.status = 500
                res.content_type = 'text/plain'
                res.body = msg
                log.error(msg)
                return res

            context = None
            calls = list(protocol.iter_calls(request))

            if len(calls) != 1:
                raise NotImplementedError("Batch calls are not yet supported")

            context = calls[0]
            context.path = protocol.extract_path(context)
            if context.path is None:
                raise exc.ClientSideError(
                    u'The %s protocol was unable to extract a function '
                    u'path from the request' % protocol.name)
            context.func, context.funcdef = self._lookup_function(context.path)
            kw = protocol.read_arguments(context)

            for arg in context.funcdef.arguments:
                if arg.mandatory and arg.name not in kw:
                    raise exc.MissingArgument(arg.name)

            result = context.func(**kw)

            res.status = 200

            if context.funcdef.protocol_specific and context.funcdef.return_type is None:
                if isinstance(result, unicode):
                    res.unicode_body = result
                else:
                    res.body = result
            else:
                # TODO make sure result type == a._wsme_definition.return_type
                res.body = protocol.encode_result(context, result)
            res_content_type = context.funcdef.contenttype
        except Exception, e:
            infos = self._format_exception(sys.exc_info())
            if isinstance(e, exc.ClientSideError):
                res.status = 400
            else:
                res.status = 500
            res.body = protocol.encode_error(context, infos)

        if res_content_type is None:
            # Attempt to correctly guess what content-type we should return.
            last_q = 0
            ctypes = [ct for ct in protocol.content_types if ct]
            if ctypes:
                res_content_type = request.accept.best_match(ctypes)

        # If not we will attempt to convert the body to an accepted
        # output format.
        if res_content_type is None:
            if "text/html" in request.accept:
                res.body = self._html_format(res.body, protocol.content_types)
                res_content_type = "text/html"

        # TODO should we consider the encoding asked by
        # the web browser ?
        res.headers['Content-Type'] = "%s; charset=UTF-8" % res_content_type

        return res

    def _lookup_function(self, path):
        a = self

        isprotocol_specific = path[0] == '_protocol'

        if isprotocol_specific:
            a = self._get_protocol(path[1])
            path = path[2:]

        for name in path:
            a = getattr(a, name, None)
            if a is None:
                break

        if not hasattr(a, '_wsme_definition'):
            raise exc.UnknownFunction('/'.join(path))

        definition = a._wsme_definition

        return a, definition

    def _format_exception(self, excinfo):
        """Extract informations that can be sent to the client."""
        error = excinfo[1]
        if isinstance(error, exc.ClientSideError):
            r = dict(faultcode="Client",
                     faultstring=error.faultstring)
            log.warning("Client-side error: %s" % r['faultstring'])
            r['debuginfo'] = None
            return r
        else:
            faultstring = str(error)
            debuginfo = "\n".join(traceback.format_exception(*excinfo))

            log.error('Server-side error: "%s". Detail: \n%s' % (
                faultstring, debuginfo))

            r = dict(faultcode="Server", faultstring=faultstring)
            if self._debug:
                r['debuginfo'] = debuginfo
            else:
                r['debuginfo'] = None
            return r

    def _html_format(self, content, content_types):
        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_for_mimetype
            from pygments.formatters import HtmlFormatter

            lexer = None
            for ct in content_types:
                try:
                    lexer = get_lexer_for_mimetype(ct)
                    break
                except:
                    pass

            if lexer is None:
                raise ValueError("No lexer found")
            formatter = HtmlFormatter()
            return html_body % dict(
                css=formatter.get_style_defs(),
                content=highlight(content, lexer, formatter).encode('utf8'))
        except Exception, e:
            log.warning(
                "Could not pygment the content because of the following "
                "error :\n%s" % e)
            return html_body % dict(
                css='',
                content='<pre>%s</pre>' %
                    content.replace('>', '&gt;').replace('<', '&lt;'))
