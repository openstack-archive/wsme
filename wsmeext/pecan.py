from __future__ import absolute_import

import functools
import inspect
import sys

import wsme
import wsme.rest.args
import wsme.rest.json
import wsme.rest.xml

import pecan


class JSonRenderer(object):
    def __init__(self, path, extra_vars):
        pass

    def render(self, template_path, namespace):
        if 'faultcode' in namespace:
            return wsme.rest.json.encode_error(None, namespace)
        return wsme.rest.json.encode_result(
            namespace['result'],
            namespace['datatype']
        )


class XMLRenderer(object):
    def __init__(self, path, extra_vars):
        pass

    def render(self, template_path, namespace):
        if 'faultcode' in namespace:
            return wsme.rest.xml.encode_error(None, namespace)
        return wsme.rest.xml.encode_result(
            namespace['result'],
            namespace['datatype']
        )

pecan.templating._builtin_renderers['wsmejson'] = JSonRenderer
pecan.templating._builtin_renderers['wsmexml'] = XMLRenderer


def wsexpose(*args, **kwargs):
    pecan_json_decorate = pecan.expose(
        template='wsmejson:',
        content_type='application/json',
        generic=False)
    pecan_xml_decorate = pecan.expose(
        template='wsmexml:',
        content_type='application/xml',
        generic=False
    )
    sig = wsme.signature(*args, **kwargs)

    def decorate(f):
        sig(f)
        funcdef = wsme.api.FunctionDefinition.get(f)
        funcdef.resolve_types(wsme.types.registry)

        @functools.wraps(f)
        def callfunction(self, *args, **kwargs):
            try:
                args, kwargs = wsme.rest.args.get_args(
                    funcdef, args, kwargs, pecan.request.params,
                    pecan.request.body, pecan.request.content_type
                )
                result = f(self, *args, **kwargs)
            except:
                data = wsme.api.format_exception(sys.exc_info())
                if data['faultcode'] == 'Client':
                    pecan.response.status = 400
                else:
                    pecan.response.status = 500
                return data

            return dict(
                datatype=funcdef.return_type,
                result=result
            )

        pecan_xml_decorate(callfunction)
        pecan_json_decorate(callfunction)
        pecan.util._cfg(callfunction)['argspec'] = inspect.getargspec(f)
        callfunction._wsme_definition = funcdef
        return callfunction

    return decorate
