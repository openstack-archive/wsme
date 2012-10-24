"""
WSME for cornice


Activate it::

    config.include('wsme.cornice')


And use it::

    @hello.get()
    @wsexpose(Message, wsme.types.text)
    def get_hello(who=u'World'):
        return Message(text='Hello %s' % who)
"""
import json

import xml.etree.ElementTree as et

import wsme
import wsme.protocols
from wsme.protocols import restjson
from wsme.protocols import restxml
import functools

from wsme.protocols.commons import (
    args_from_params, args_from_body, combine_args
)


class WSMEJsonRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, data, context):
        response = context['request'].response
        response.content_type = 'application/json'
        data = restjson.tojson(
            data['datatype'],
            data['result']
        )
        return json.dumps(data)


class WSMEXmlRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, data, context):
        response = context['request'].response
        response.content_type = 'text/xml'
        data = restxml.toxml(
            data['datatype'],
            'result',
            data['result']
        )
        return et.tostring(data)


def wsexpose(*args, **kwargs):
    sig = wsme.sig(*args, **kwargs)

    def decorate(f):
        sig(f)
        funcdef = wsme.api.FunctionDefinition.get(f)

        @functools.wraps(f)
        def callfunction(request):
            args, kwargs = combine_args(
                funcdef,
                args_from_params(funcdef, request.params),
                args_from_body(funcdef, request.body, request.content_type)
            )
            if 'application/json' in request.headers['Accept']:
                request.override_renderer = 'wsmejson'
            elif 'text/xml' in request.headers['Accept']:
                request.override_renderer = 'wsmexml'
            return {
                'datatype': funcdef.return_type,
                'result': f(*args, **kwargs)
            }

        return callfunction
    return decorate


def includeme(config):
    config.add_renderer('wsmejson', WSMEJsonRenderer)
    config.add_renderer('wsmexml', WSMEXmlRenderer)
