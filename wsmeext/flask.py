from __future__ import absolute_import

import functools
import wsme
import wsme.api
from wsme.rest.args import (
    args_from_params, args_from_body, combine_args
)

import flask


def signature(*args, **kw):
    sig = wsme.signature(*args, **kw)

    def decorator(f):
        sig(f)
        funcdef = wsme.api.FunctionDefinition.get(f)

        @functools.wraps(f)
        def wrapper(*args, **kw):
            args, kwargs = combine_args(
                funcdef,
                args_from_params(funcdef, flask.request.args),
                args_from_body(funcdef, flask.request.data, flask.request.content_type)
            )
            resp = make_response(f(*args, **kw))
            return resp

        wrapper.wsme_func = f
        return wrapper
    return decorator
