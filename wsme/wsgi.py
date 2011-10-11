from webob.dec import wsgify


def adapt(root):
    return wsgify(root._handle_request)
