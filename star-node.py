import sys
import json
import socket
import time
import threading
import _thread

name = sys.argv[1]
localPort = sys.argv[2]
pocAddress = sys.argv[3]
pocPort = sys.argv[4]
maxNodes = sys.argv[5]

class Peer:
	RTTack = False
	def __init__( self, maxpeers, serverport, myid):
		self.debug = 0

		self.maxpeers = int(maxpeers)
		self.serverport = int(serverport)
		self.serverhost = socket.gethostbyname(socket.gethostname())
		self.myid = myid

	    # list (dictionary/hash table) of known peers
		self.peers = {} 
		self.rtttimes = {}
		self.rttsum = 0
		self.rttsums = {}
		self.hubnode = name

	    # used to stop the main loop
		self.shutdown = False  

		self.handlers = {}
		self.router = None
	    # end constructor

	def makeServerSocket(self, port):
		serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		serverSocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
		serverSocket.bind(('', port))
		return serverSocket

	def __handlepeer( self, socket, initialRTTnode = None, startTime = None ):
		message, clientAddress = socket.recvfrom(2048)
		output = message.decode()
		port = output[3:8]

		try:

			msgtype = output[0:3]

			if msgtype == "000":
				self.receivePeerDiscovery(clientAddress, output)
			if msgtype == "001":
				nodeName = output[8:24]
				self.initialRTTack(socket, nodeName.strip())
			if msgtype == "002" and initialRTTnode != None and startTime != None:
				endTime = time.time()
				rtttime = endTime - startTime
				self.rtttimes[initialRTTnode] = rtttime
			if msgtype == "003":
				self.receiveRTTsum(clientAddress, output)


		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()
	def __commands(self, socket):
		command = input("Star-node command: ")
		if command == "show-status":
			self.showstatus()

	def mainloop( self ):
		s = self.makeServerSocket( self.serverport )
		#s.settimeout(10)
		t1 = threading.Thread( target = self.__handlepeer, args = [ s ] )
		t1.start()

		while len(self.peers) < int(maxNodes) and not self.shutdown:
			try:
				if not t1.isAlive():
					t1 = threading.Thread( target = self.__handlepeer, args = [ s ] )
					t1.start()
				if pocAddress != 0 and pocPort != 0 and not [pocAddress, pocPort] in self.peers.values():
					self.initialPoc(s)
				self.sendPeerDiscovery(s)
			except KeyboardInterrupt:
				self.shutdown = True
				continue
			except:
				if self.debug:
					traceback.print_exc()
					continue

		self.sendPeerDiscovery(s)

		for node in self.peers:
			if (node != name):
				t2 = threading.Thread( target = self.__handlepeer, args = [ s, node ] )
				t2.start()
				while (node not in self.rtttimes):
					self.initialSendRTT(s, node)
					if not t2.isAlive():
						t2 = threading.Thread( target = self.__handlepeer, args = [ s, node, time.time() ] )
						t2.start()


		for node in self.rtttimes:
			self.rttsum += self.rtttimes[node]

		t3 = threading.Thread( target = self.__handlepeer, args = [ s ] )
		t3.start()
		while len(self.rttsums) < int(maxNodes)-1 and not self.shutdown:
			try:
				if not t3.isAlive():
					t3 = threading.Thread( target = self.__handlepeer, args = [ s ] )
					t3.start()
				self.sendRTTsum(s)
			except KeyboardInterrupt:
				self.shutdown = True
				continue
			except:
				if self.debug:
					traceback.print_exc()
					continue

		minrttsum = self.rttsum
		self.hubnode = name
		for node in self.rttsums:
			if float(self.rttsums[node]) < float(minrttsum):
				minrttsum = self.rttsums[node]
				self.hubnode = node

		t4 = threading.Thread( target = self.__commands, args = [ s ] )
		t4.start()
		t5 = threading.Thread( target = self.__handlepeer, args = [ s ] )
		t5.start()
		while not self.shutdown:
			try:
				if not t4.isAlive():
					t4 = threading.Thread( target = self.__commands, args = [ s ] )
					t4.start()
				if not t5.isAlive():
					t5 = threading.Thread( target = self.__handlepeer, args = [ s ] )
					t5.start()
			except KeyboardInterrupt:
				self.shutdown = True
				continue
			except:
				if self.debug:
					traceback.print_exc()
					continue


	def initialPoc(self, serverSocket):
		pdpacket = "000" + "{:<5}".format(localPort) + "{:<16}".format(name) + json.dumps(self.peers)
		serverSocket.sendto(pdpacket.encode(), (pocAddress, int(pocPort)))

	def sendPeerDiscovery(self, serverSocket):
		pdpacket = "000" + "{:<5}".format(localPort) + "{:<16}".format(name) + json.dumps(self.peers)
		for node in self.peers:
			if node != name:
				serverSocket.sendto(pdpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def receivePeerDiscovery(self, clientAddress, message):
		incKnownNodes = json.loads(message[23:])
		for node in incKnownNodes:
			if node not in self.peers:
				self.peers[node] = incKnownNodes[node]

	def initialSendRTT(self, serverSocket, node):
		initialrttpacket = "001" + "{:<5}".format(localPort) + "{:<16}".format(name)
		serverSocket.sendto(initialrttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def initialRTTack(self, serverSocket, node):
		initialrttpacket = "002" + "{:<5}".format(localPort) + "{:<16}".format(name)
		serverSocket.sendto(initialrttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def sendRTTsum(self, serverSocket):
		rttpacket = "003" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(self.rttsum)
		for node in self.peers:
			if node != name:
				serverSocket.sendto(rttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def receiveRTTsum(self, clientAddress, message):
		incRTTsum = message[23:]
		nodeName = message[8:24].strip()
		self.rttsums[nodeName] = incRTTsum

	def showstatus(self):
		for node in self.rttsums:
			print("Node name: " + node + " RTT sum: " + self.rttsums[node])
		print("Hub: " + self.hubnode)



starnode = Peer(maxNodes, localPort, name)
starnode.peers[name] = [socket.gethostbyname(socket.gethostname()), localPort]
starnode.mainloop()




