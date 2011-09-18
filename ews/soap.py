class SoapProtocol(object):
    name = 'soap'
    accept = ''

    def __init__(self):
        pass


controller.register_protocol(SoapProtocol)
