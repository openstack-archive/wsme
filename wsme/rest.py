import webob
import sys
import logging

from wsme.exc import UnknownFunction, MissingArgument, UnknownArgument

log = logging.getLogger(__name__)

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


class RestProtocol(object):
    name = None
    dataformat = None
    content_types = []

    def accept(self, root, request):
        if request.path.endswith('.' + self.dataformat):
            return True
        return request.headers.get('Content-Type') in self.content_types

    def read_arguments(self, request, arguments):
        if len(request.params) and request.body:
            raise ClientSideError(
                "Cannot read parameters from both a body and GET/POST params")

        body = None
        if 'body' in request.params:
            body = request.params['body']

        if body is None and len(request.params):
            parsed_args = {}
            for key, value in request.params.items():
                parsed_args[key] = self.parse_arg(key, value)
        else:
            if body is None:
                body = request.body
            if body:
                parsed_args = self.parse_args(body)
            else:
                parsed_args = {}

        kw = {}

        for arg in arguments:
            if arg.name not in parsed_args:
                if arg.mandatory:
                    raise MissingArgument(arg.name)
                continue

            value = parsed_args.pop(arg.name)
            kw[arg.name] = self.decode_arg(value, arg)

        if parsed_args:
            raise UnknownArgument(parsed_args.keys()[0])
        return kw

    def handle(self, root, request):
        path = request.path.strip('/').split('/')

        if path[-1].endswith('.' + self.dataformat):
            path[-1] = path[-1][:-len(self.dataformat) - 1]

        res = webob.Response()

        try:
            func, funcdef = root._lookup_function(path)
            kw = self.read_arguments(request, funcdef.arguments)
            result = func(**kw)
            # TODO make sure result type == a._wsme_definition.return_type
            res.body = self.encode_result(result, funcdef.return_type)
            res.status = "200 OK"
        except Exception, e:
            res.status = 500
            res.body = self.encode_error(
                root._format_exception(sys.exc_info()))

        # Attempt to correctly guess what content-type we should return.
        res_content_type = None

        last_q = 0
        if hasattr(request.accept, '_parsed'):
            for mimetype, q in request.accept._parsed:
                if mimetype in self.content_types and last_q < q:
                    res_content_type = mimetype
        else:
            res_content_type = request.accept.best_match([
                ct for ct in self.content_types if ct])

        # If not we will attempt to convert the body to an accepted
        # output format.
        if res_content_type is None:
            if "text/html" in request.accept:
                res.body = self.html_format(res.body)
                res_content_type = "text/html"

        res.headers['Content-Type'] = "%s; charset=UTF-8" % res_content_type

        return res

    def html_format(self, content):
        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_for_mimetype
            from pygments.formatters import HtmlFormatter

            lexer = None
            for ct in self.content_types:
                try:
                    print ct
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
                "Could not pygment the content because of the following error :\n%s" % e)
            return html_body % dict(
                css='',
                content='<pre>%s</pre>' % content.replace('>', '&gt;').replace('<', '&lt;'))
