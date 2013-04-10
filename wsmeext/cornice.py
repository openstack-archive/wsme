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

import wsme
from wsme.rest import json as restjson
from wsme.rest import xml as restxml
import wsme.runtime
import functools

from wsme.rest.args import (
    args_from_args, args_from_params, args_from_body, combine_args
)


class WSMEJsonRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, data, context):
        response = context['request'].response
        response.content_type = 'application/json'
        return restjson.encode_result(data['result'], data['datatype'])


class WSMEXmlRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, data, context):
        response = context['request'].response
        response.content_type = 'text/xml'
        return restxml.encode_result(data['result'], data['datatype'])


def get_outputformat(request):
    df = None
    if 'Accept' in request.headers:
        if 'application/json' in request.headers['Accept']:
            df = 'json'
        elif 'text/xml' in request.headers['Accept']:
            df = 'xml'
    if df is None and 'Content-Type' in request.headers:
        if 'application/json' in request.headers['Content-Type']:
            df = 'json'
        elif 'text/xml' in request.headers['Content-Type']:
            df = 'xml'
    return df if df else 'json'


def signature(*args, **kwargs):
    sig = wsme.signature(*args, **kwargs)

    def decorate(f):
        sig(f)
        funcdef = wsme.api.FunctionDefinition.get(f)
        funcdef.resolve_types(wsme.types.registry)

        @functools.wraps(f)
        def callfunction(request):
            args, kwargs = combine_args(
                funcdef,
                (args_from_args(funcdef, (), request.matchdict),
                 args_from_params(funcdef, request.params),
                 args_from_body(funcdef, request.body, request.content_type))
            )
            wsme.runtime.check_arguments(funcdef, args, kwargs)
            request.override_renderer = 'wsme' + get_outputformat(request)
            if funcdef.pass_request:
                kwargs[funcdef.pass_request] = request
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
