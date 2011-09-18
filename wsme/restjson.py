class RestJsonProtocol(RestProtocol):
    name = 'REST+Json'
    dataformat = 'json'
    content_types = [None, 'application/json', 'text/json']


controller.register_protocol(RestJsonProtocol)
