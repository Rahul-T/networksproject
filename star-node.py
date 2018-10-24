from socket import *
import sys

name = sys.argv[1]
localport = sys.argv[2]
pocaddress = sys.argv[3]
pocport = sys.argv[3]
maxnodes = sys.argv[4]

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', localPort))

def peerdiscovery():
