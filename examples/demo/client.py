from suds.client import Client

url = 'http://127.0.0.1:8989/api.wsdl'

client = Client(url, cache=None)

print client

print client.service.Multiply(4, 5)
print client.service.Helloworld()
print client.service.Getperson()
