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
		#self.__debug( 'Connected ' + str(clientsock.getpeername()) )
		message, clientAddress = socket.recvfrom(2048)
		output = message.decode()
		#host, port = clientsock.getpeername()
		#peerAddress = clientAddress
		port = output[3:8]
		#peerconn = BTPeerConnection( None, host, port, clientsock, debug=False )	
		try:
			#msgtype, msgdata = peerconn.recvdata()
			msgtype = output[0:3]
		    #if msgtype: msgtype = msgtype.upper()
		 #    if msgtype not in self.handlers:
			# self.__debug( 'Not handled: %s: %s' % (msgtype, msgdata) )
		 #    else:
			#self.__debug( 'Handling peer msg: %s: %s' % (msgtype, msgdata) )
			
			#self.handlers[ msgtype ](message)
			if msgtype == "000":
				self.receivePeerDiscovery(clientAddress, output)
			if msgtype == "001":
				nodeName = output[8:24]
				#print(nodeName)
				#print("HEY")
				self.initialRTTack(socket, nodeName.strip())
				#print("HEY2")
			if msgtype == "002" and initialRTTnode != None and startTime != None:
				#print("HI")
				endTime = time.time()
				rtttime = endTime - startTime
				self.rtttimes[initialRTTnode] = rtttime
			if msgtype == "003":
				#print("xd")
				self.receiveRTTsum(clientAddress, output)
			#elif msgtype == "010":
				#self.rtt(clientAddress, output)


		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()
		
	# 	#self.__debug( 'Disconnecting ' + str(clientsock.getpeername()) )
	# 	#peerconn.close()

	#     # end handlepeer method

	def mainloop( self ):
		s = self.makeServerSocket( self.serverport )
		s.settimeout(10)
		# self.__debug( 'Server started: %s (%s:%d)'
		# 	      % ( self.myid, self.serverhost, self.serverport ) )
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
					#print(self.rtttimes)
		#print(self.rtttimes)

		for node in self.rtttimes:
			self.rttsum += self.rtttimes[node]
		#print(self.rttsum)

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
		#print(self.rttsums)
		minrttsum = self.rttsum
		hubnode = name
		for node in self.rttsums:
			if float(self.rttsums[node]) < float(minrttsum):
				minrttsum = self.rttsums[node]
				hubnode = node

		
		# while not self.shutdown:
		# 	try:
		# 		#self.__debug( 'Listening for connections...' )
		# 		#clientsock, clientaddr = s.accept()
		# 		message, clientAddress = serverSocket.recvfrom(2048)
		# 		#clientsock.settimeout(None)

		# 		t2 = threading.Thread( target = self.__handlepeer, args = [ message, clientAddress ] )
		# 		t2.start()
		# 	except KeyboardInterrupt:
		# 		self.shutdown = True
		# 		continue
		# 	except:
		# 		if self.debug:
		# 			traceback.print_exc()
		# 			continue
		# end while loop

		#self.__debug( 'Main loop exiting' )
		#s.close()
	    # end mainloop method

	def initialPoc(self, serverSocket):
		pdpacket = "000" + "{:<5}".format(localPort) + "{:<16}".format(name) + json.dumps(self.peers)
		serverSocket.sendto(pdpacket.encode(), (pocAddress, int(pocPort)))

	def sendPeerDiscovery(self, serverSocket):
		pdpacket = "000" + "{:<5}".format(localPort) + "{:<16}".format(name) + json.dumps(self.peers)
		#print(pdpacket)
		for node in self.peers:
			if node != name:
				serverSocket.sendto(pdpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))
		#print(self.peers)

	def receivePeerDiscovery(self, clientAddress, message):
		incKnownNodes = json.loads(message[23:])
		for node in incKnownNodes:
			if node not in self.peers:
				self.peers[node] = incKnownNodes[node]
		#print(self.peers)

	def initialSendRTT(self, serverSocket, node):
		initialrttpacket = "001" + "{:<5}".format(localPort) + "{:<16}".format(name)
		serverSocket.sendto(initialrttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def initialRTTack(self, serverSocket, node):
		#print(node)
		initialrttpacket = "002" + "{:<5}".format(localPort) + "{:<16}".format(name)
		#print(self.peers[node])
		serverSocket.sendto(initialrttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def sendRTTsum(self, serverSocket):
		rttpacket = "003" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(self.rttsum)
		#print("hi")
		for node in self.peers:
			if node != name:
				serverSocket.sendto(rttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def receiveRTTsum(self, clientAddress, message):
		#print(message[23:])
		incRTTsum = message[23:]
		nodeName = message[8:24].strip()
		#print(nodeName)
		self.rttsums[nodeName] = incRTTsum
		#print(len(self.rttsums))

starnode = Peer(maxNodes, localPort, name)
starnode.peers[name] = [socket.gethostbyname(socket.gethostname()), localPort]
starnode.mainloop()




