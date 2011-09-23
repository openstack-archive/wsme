import pkg_resources

from xml.etree import ElementTree as et
from genshi.template import MarkupTemplate
from wsme.controller import register_protocol, pexpose
import wsme.types

nativetypes = {
    str: 'xsd:string',
    int: 'xsd:int',
}

class SoapProtocol(object):
    name = 'SOAP'
    content_types = ['application/soap+xml']

    ns = {
        "soap": "http://www.w3.org/2001/12/soap-envelope"
    }

    def __init__(self, tns=None,
            typenamespace=None,
            baseURL=None
            ):
        self.tns = tns
        self.typenamespace = typenamespace
        self.servicename = 'MyApp'

    def accept(self, root, req):
        if req.path.endswith('.wsdl'):
            return True
        for ct in self.content_types:
            if req.headers['Content-Type'].startswith(ct):
                return True
        return False

    def extract_path(self, request):
        if request.path.endswith('.wsdl'):
            print "Here !!"
            return ['_protocol', self.name, 'api_wsdl']
        el = et.fromstring(request.body)
        body = el.find('{http://schemas.xmlsoap.org/soap/envelope/}Body')
        fname = list(body)[0].tag
        print fname
        return [fname]

    def read_arguments(self, request, funcdef):
        return {}

    def encode_result(self, result, funcdef):
        envelope = self.render_template('soap')
        print envelope
        return envelope

    def get_template(self, name):
        return pkg_resources.resource_string(
            __name__, 'templates/%s.html' % name)

    def render_template(self, name, **kw):
        tmpl = MarkupTemplate(self.get_template(name))
        stream = tmpl.generate(**kw)
        return stream.render('xml')

    def encode_error(self, infos):
        return self.render_template('fault',
            typenamespace=self.typenamespace,
            **infos)
        
    @pexpose(contenttype="text/xml")
    def api_wsdl(self, root, service=None):
        if service is None:
            servicename = self.servicename
        else:
            servicename = self.servicename + service.capitalize()
        return self.render_template('wsdl',
            tns = self.tns,
            typenamespace = self.typenamespace,
            soapenc = 'http://schemas.xmlsoap.org/soap/encoding/',
            service_name = servicename,
            complex_types = (t() for t in wsme.types.complex_types),
            funclist = root.getapi(),
            arrays = [],
            list_attributes = wsme.types.list_attributes,
            baseURL = service,
            soap_type = self.soap_type,
            soap_fname = self.soap_fname,
        )

    def soap_type(self, datatype):
        if datatype in nativetypes:
            return nativetypes[datatype]
        if wsme.types.iscomplex(datatype):
            return "types:%s" % datatype.__name__

    def soap_fname(self, funcdef):
        return "%s%s" % (
            "".join((i.capitalize() for i in funcdef.path)),
            funcdef.name.capitalize())

register_protocol(SoapProtocol)
