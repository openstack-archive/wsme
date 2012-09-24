import logging
import sys
import traceback
import weakref

from six import u, b
import six

import webob

from wsme import exc
from wsme.protocols import getprotocol
from wsme.api import scan_api
from wsme import spore
import wsme.types

log = logging.getLogger(__name__)

html_body = u("""
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
""")


def default_prepare_response_body(request, results):
    r = None
    sep = None
    for value in results:
        if sep is None:
            if isinstance(value, six.text_type):
                sep = u('\n')
                r = u('')
            else:
                sep = b('\n')
                r = b('')
        else:
            r += sep
        r += value
    return r


class DummyTransaction:
    def commit(self):
        pass

    def abort(self):
        pass


class WSRoot(object):
    """
    Root controller for webservices.

    :param protocols: A list of protocols to enable (see :meth:`addprotocol`)
    :param webpath: The web path where the webservice is published.

    :type  transaction: A `transaction
                        <http://pypi.python.org/pypi/transaction>`_-like
                        object or ``True``.
    :param transaction: If specified, a transaction will be created and
                        handled on a per-call base.

                        This option *can* be enabled along with `repoze.tm2
                        <http://pypi.python.org/pypi/repoze.tm2>`_
                        (it will only make it void).

                        If ``True``, the default :mod:`transaction`
                        module will be imported and used.

    """
    __registry__ = wsme.types.registry

    def __init__(self, protocols=[], webpath='', transaction=None):
        self._debug = True
        self._webpath = webpath
        self.protocols = []

        self._transaction = transaction
        if self._transaction is True:
            import transaction
            self._transaction = transaction

        for protocol in protocols:
            self.addprotocol(protocol)

        self._api = None

    def wsgiapp(self):
        """Returns a wsgi application"""
        from webob.dec import wsgify
        return wsgify(self._handle_request)

    def begin(self):
        if self._transaction:
            return self._transaction.begin()
        else:
            return DummyTransaction()

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
            for path, fdef in self._api:
                fdef.resolve_types(self.__registry__)
        return self._api

    def _get_protocol(self, name):
        for protocol in self.protocols:
            if protocol.name == name:
                return protocol

    def _select_protocol(self, request):
        log.debug("Selecting a protocol for the following request :\n"
                  "headers: %s\nbody: %s", request.headers.items(),
                  request.content_length and (
                      request.content_length > 512
                      and request.body[:512]
                      or request.body)
                  or '')
        protocol = None
        path = str(request.path)
        assert path.startswith(self._webpath)
        path = path[len(self._webpath) + 1:]
        if 'wsmeproto' in request.params:
            return self._get_protocol(request.params['wsmeproto'])
        elif path.startswith('_protocol'):
            return self._get_protocol(path.split('/')[1])
        else:

            for p in self.protocols:
                if p.accept(request):
                    protocol = p
                    break
        return protocol

    def _do_call(self, protocol, context):
        request = context.request
        request.calls.append(context)
        try:
            if context.path is None:
                context.path = protocol.extract_path(context)

            if context.path is None:
                raise exc.ClientSideError(u(
                    'The %s protocol was unable to extract a function '
                    'path from the request') % protocol.name)

            context.func, context.funcdef = self._lookup_function(context.path)
            kw = protocol.read_arguments(context)

            for arg in context.funcdef.arguments:
                if arg.mandatory and arg.name not in kw:
                    raise exc.MissingArgument(arg.name)

            txn = self.begin()
            try:
                result = context.func(**kw)
                txn.commit()
            except:
                txn.abort()
                raise

            if context.funcdef.protocol_specific \
                    and context.funcdef.return_type is None:
                return result
            else:
                # TODO make sure result type == a._wsme_definition.return_type
                return protocol.encode_result(context, result)

        except Exception:
            e = sys.exc_info()[1]
            infos = self._format_exception(sys.exc_info())
            if isinstance(e, exc.ClientSideError):
                request.client_errorcount += 1
            else:
                request.server_errorcount += 1
            return protocol.encode_error(context, infos)

    def _handle_request(self, request):
        res = webob.Response()
        res_content_type = None

        if request.path == self._webpath + '/api.spore':
            res.body = spore.getdesc(self, request.host_url)
            res.content_type = 'application/json'
            return res

        try:
            msg = None
            protocol = self._select_protocol(request)
        except Exception:
            e = sys.exc_info()[1]
            msg = ("Error while selecting protocol: %s" % str(e))
            log.exception(msg)
            protocol = None

        if protocol is None:
            if msg is None:
                msg = ("None of the following protocols can handle this "
                       "request : %s" % ','.join(
                            (p.name for p in self.protocols)))
            res.status = 500
            res.content_type = 'text/plain'
            res.text = u(msg)
            log.error(msg)
            return res

        request.calls = []
        request.client_errorcount = 0
        request.server_errorcount = 0

        try:

            context = None

            if hasattr(protocol, 'prepare_response_body'):
                prepare_response_body = protocol.prepare_response_body
            else:
                prepare_response_body = default_prepare_response_body

            body = prepare_response_body(request, (
                self._do_call(protocol, context)
                for context in protocol.iter_calls(request)))

            if isinstance(body, six.text_type):
                res.text = body
            else:
                res.body = body

            if len(request.calls) == 1:
                if hasattr(protocol, 'get_response_status'):
                    res.status = protocol.get_response_status(request)
                else:
                    if request.client_errorcount:
                        res.status = 400
                    elif request.server_errorcount:
                        res.status = 500
                    else:
                        res.status = 200
                if request.calls[0].funcdef:
                    res_content_type = request.calls[0].funcdef.contenttype
            else:
                res.status = protocol.get_response_status(request)
                res_content_type = protocol.get_response_contenttype(request)
        except Exception:
            infos = self._format_exception(sys.exc_info())
            request.server_errorcount += 1
            res.text = protocol.encode_error(context, infos)
            res.status = 500

        if res_content_type is None:
            # Attempt to correctly guess what content-type we should return.
            ctypes = [ct for ct in protocol.content_types if ct]
            if ctypes:
                res_content_type = request.accept.best_match(ctypes)

        # If not we will attempt to convert the body to an accepted
        # output format.
        if res_content_type is None:
            if "text/html" in request.accept:
                res.text = self._html_format(res.body, protocol.content_types)
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
        except Exception:
            e = sys.exc_info()[1]
            log.warning(
                "Could not pygment the content because of the following "
                "error :\n%s" % e)
            return html_body % dict(
                css='',
                content=u('<pre>%s</pre>') %
                    content.replace(b('>'), b('&gt;'))
                           .replace(b('<'), b('&lt;')))
