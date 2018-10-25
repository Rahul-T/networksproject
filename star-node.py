import sys
import json
import socket

def initialPoc(name, pocAddress, pocPort, knownNodes):
	pdpacket = "000" + "{:<16}".format(name) + json.dumps(knownNodes)
	#print(pdpacket)
	serverSocket.sendto(pdpacket.encode(), (pocAddress, int(pocPort)))
	incomingPacket, address = serverSocket.recvfrom(2048)
	output = incomingPacket.decode()
	incKnownNodes = json.loads(output[19:])
	for node in incKnownNodes:
		if node not in knownNodes:
			knownNodes[node] = incKnownNodes[node]
	#print(knownNodes)

def peerDiscovery(name, knownNodes):
	pdpacket = "000" + "{:<16}".format(name) + json.dumps(knownNodes)
	#print(pdpacket)
	for node in knownNodes:
		if node != name:
			serverSocket.sendto(pdpacket.encode(), (knownNodes[node][0], int(knownNodes[node][1])))
	incomingPacket, address = serverSocket.recvfrom(2048)
	output = incomingPacket.decode()
	incKnownNodes = json.loads(output[19:])
	for node in incKnownNodes:
		if node not in knownNodes:
			knownNodes[node] = incKnownNodes[node]
	print(knownNodes)

name = sys.argv[1]
localPort = sys.argv[2]
pocAddress = sys.argv[3]
pocPort = sys.argv[4]
maxNodes = sys.argv[5]


knownNodes = {name:[socket.gethostname(), localPort]}

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.bind(('', int(localPort)))

initialPoc(name, pocAddress, pocPort, knownNodes)
peerDiscovery(name, knownNodes)