from socket import *
import sys
import json

def peerdiscovery(name, pocAddress, pocPort, knownNodes):
	pdpacket = "000" + "{:<16}".format(name) + json.dumps(knownNodes)
	print(pdpacket)
	serverSocket.sendto(pdpacket.encode(), (pocAddress, int(pocPort)))
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

knownNodes = {name:True}

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', int(localPort)))

peerdiscovery(name, pocAddress, pocPort, knownNodes)