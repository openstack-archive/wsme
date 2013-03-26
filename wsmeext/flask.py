from __future__ import absolute_import

import functools
import logging
import sys

import wsme
import wsme.api
import wsme.rest.json
import wsme.rest.xml
import wsme.rest.args

import flask

log = logging.getLogger(__name__)


def signature(*args, **kw):
    sig = wsme.signature(*args, **kw)

    def decorator(f):
        sig(f)
        funcdef = wsme.api.FunctionDefinition.get(f)
        funcdef.resolve_types(wsme.types.registry)

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            args, kwargs = wsme.rest.args.get_args(
                funcdef, args, kwargs,
                flask.request.args, flask.request.form,
                flask.request.data,
                flask.request.mimetype
            )

            dataformat = None
            if 'Accept' in flask.request.headers:
                if 'application/json' in flask.request.headers['Accept']:
                    dataformat = wsme.rest.json
                elif 'text/xml' in flask.request.headers['Accept']:
                    dataformat = wsme.rest.xml
            if dataformat is None:
                log.info('''Could not determine what format is wanted by the
                caller, falling back to json''')
                dataformat = wsme.rest.json
            try:
                status_code = None
                result = f(*args, **kwargs)

                # Status code in result
                if isinstance(result, (list, tuple)) and len(result) == 2:
                    result, status_code = result

                # Status code is attached to request
                if not status_code and hasattr(flask.request, 'status_code'):
                    status_code = flask.request.status_code

                res = flask.make_response(
                    dataformat.encode_result(
                        result,
                        funcdef.return_type
                    )
                )
                res.mimetype = dataformat.content_type
                res.status_code = status_code or 200
            except:
                data = wsme.api.format_exception(sys.exc_info())
                res = flask.make_response(dataformat.encode_error(None, data))
                if data['faultcode'] == 'client':
                    res.status_code = 400
                else:
                    res.status_code = 500
            return res

        wrapper.wsme_func = f
        return wrapper
    return decorator
