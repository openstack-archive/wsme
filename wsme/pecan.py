import inspect
import sys

import json

import xml.etree.ElementTree as et

import wsme
import wsme.protocols.commons
import wsme.protocols.restjson
import wsme.protocols.restxml

pecan = sys.modules['pecan']


class JSonRenderer(object):
    def __init__(self, path, extra_vars):
        pass

    def render(self, template_path, namespace):
        data = wsme.protocols.restjson.tojson(
            namespace['datatype'],
            namespace['result']
        )
        return json.dumps(data)


class XMLRenderer(object):
    def __init__(self, path, extra_vars):
        pass

    def render(self, template_path, namespace):
        data = wsme.protocols.restxml.toxml(
            namespace['datatype'],
            'result',
            namespace['result']
        )
        return et.tostring(data)

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
    sig = wsme.sig(*args, **kwargs)

    def decorate(f):
        sig(f)
        funcdef = wsme.api.FunctionDefinition.get(f)

        def callfunction(self, *args, **kwargs):
            args, kwargs = wsme.protocols.commons.get_args(
                funcdef, args, kwargs,
                pecan.request.body, pecan.request.content_type
            )
            result = f(self, *args, **kwargs)
            return dict(
                datatype=funcdef.return_type,
                result=result
            )

        pecan_json_decorate(callfunction)
        pecan_xml_decorate(callfunction)
        pecan.util._cfg(callfunction)['argspec'] = inspect.getargspec(f)
        return callfunction

    return decorate
