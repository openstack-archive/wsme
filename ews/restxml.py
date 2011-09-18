class RestXmlProtocol(RestProtocol):
    name = 'REST+XML'

import controller
controller.register_protocol(RestXmlProtocol)


