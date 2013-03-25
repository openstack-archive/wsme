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

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            args, kwargs = wsme.rest.args.get_args(
                funcdef, args, kwargs, flask.request.args, flask.request.data,
                flask.request.content_type
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
                res = flask.make_response(
                    dataformat.encode_result(
                        f(*args, **kwargs),
                        funcdef.return_type
                    )
                )
                res.mimetype = dataformat.content_type
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
