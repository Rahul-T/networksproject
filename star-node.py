from socket import *
import sys

def peerdiscovery(name, pocAddress, pocPort):
	pdpacket = "000"
	pdpacket = pdpacket + name
	print(pdpacket)
	serverSocket.sendto(pdpacket.encode(), (pocAddress, int(pocPort)))
	incomingPacket, address = serverSocket.recvfrom(2048)
	output = incomingPacket.decode()
	print(output)

name = sys.argv[1]
localPort = sys.argv[2]
pocAddress = sys.argv[3]
pocPort = sys.argv[4]
maxNodes = sys.argv[5]
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', int(localPort)))
peerdiscovery(name, pocAddress, pocPort)