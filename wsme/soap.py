import pkg_resources

from xml.etree import ElementTree as et
from genshi.template import MarkupTemplate
from wsme.controller import register_protocol, pexpose

class SoapProtocol(object):
    name = 'SOAP'
    content_types = ['application/soap+xml']

    ns = {
        "soap": "http://www.w3.org/2001/12/soap-envelope"
    }

    def __init__(self):
        pass

    def accept(self, root, req):
        if req.path.endswith('.wsdl'):
            return True
        if req.headers['Content-Type'] in self.content_types:
            return True
        return False

    def extract_path(self, request):
        if request.path.endswith('.wsdl'):
            print "Here !!"
            return ['_protocol', self.name, 'api_wsdl']

    def read_arguments(self, request, arguments):
        if arguments is None:
            return {}
        return {}

    def encode_result(self, result, return_type):
        return ""

    def make_header(self):
        header = et.Element('{%(soap)s}Header' % self.ns)
        return header

    def make_body(self):
        body = et.Element('{%(soap)s}Body' % self.ns)
        return body

    def make_envelope(self):
        env = et.Element('{%(soap)s}Envelope' % self.ns)
        env.append(self.make_header())
        env.append(self.make_body())
        return env

    def encode_error(self, infos):
        env = self.make_envelope()
        fault = et.Element('{%(soap)s}Fault' % self.ns)
        env.find('{%(soap)s}Body' % self.ns).append(fault)
        return et.tostring(env)

    @pexpose(contenttype="text/xml")
    def api_wsdl(self):
        tmpl = MarkupTemplate(
            pkg_resources.resource_string(__name__, 'templates/wsdl.html'))
        stream = tmpl.generate(
            tns = 'test',
            typenamespace = 'tset',
            soapenc = 'enc',
            service_name = 'sn',
            complex_types = [],
            funclist = [],
            arrays = [],
            baseURL = '',
            )
        return stream.render('xml')


register_protocol(SoapProtocol)
