from suds.client import Client

url = 'http://127.0.0.1:8080/ws/api.wsdl'

client = Client(url, cache=None)

print client

print client.service.multiply(4, 5)
print client.service.helloworld()
print client.service.getperson()
p = client.service.listpersons()
p = client.service.setpersons(p)
print p
