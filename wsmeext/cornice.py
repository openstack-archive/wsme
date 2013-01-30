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
from __future__ import absolute_import
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


def signature(*args, **kwargs):
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
            else:
                request.override_renderer = 'wsmejson'
            return {
                'datatype': funcdef.return_type,
                'result': f(*args, **kwargs)
            }

        callfunction.wsme_func = f
        return callfunction
    return decorate


def scan_api(root=None):
    from cornice.service import get_services
    for service in get_services():
        for method, func, options in service.definitions:
            wsme_func = getattr(func, 'wsme_func')
            basepath = service.path.split('/')
            if basepath and not basepath[0]:
                del basepath[0]
            if wsme_func:
                yield (
                    basepath + [method.lower()],
                    wsme_func._wsme_definition
                )


def includeme(config):
    import pyramid.wsgi
    wsroot = wsme.WSRoot(scan_api=scan_api, webpath='/ws')
    wsroot.addprotocol('extdirect')
    config.add_renderer('wsmejson', WSMEJsonRenderer)
    config.add_renderer('wsmexml', WSMEXmlRenderer)
    config.add_route('wsme', '/ws/*path')
    config.add_view(pyramid.wsgi.wsgiapp(wsroot.wsgiapp()), route_name='wsme')
