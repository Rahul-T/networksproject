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
	def __init__( self, maxpeers, serverport, myid):
		self.debug = 0

		self.maxpeers = int(maxpeers)
		self.serverport = int(serverport)
		self.serverhost = socket.gethostbyname(socket.gethostname())
		self.myid = myid

	    # list (dictionary/hash table) of known peers
		self.peers = {}  

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

	def __handlepeer( self, socket ):
		print("ZZZ")
		#self.__debug( 'Connected ' + str(clientsock.getpeername()) )
		message, clientAddress = socket.recvfrom(2048)
		output = message.decode()
		#host, port = clientsock.getpeername()
		#peerAddress = clientAddress
		print("XXXXXXXXXX")
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
			elif msgtype == "010":
				self.rtt(clientAddress, output)


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
				if not [pocAddress, pocPort] in self.peers.values():
					self.initialPoc(s)
				self.sendPeerDiscovery()
			except KeyboardInterrupt:
				self.shutdown = True
				continue
			except:
				if self.debug:
					traceback.print_exc()
					continue



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

	def sendPeerDiscovery(self):
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
		print(self.peers)


starnode = Peer(maxNodes, localPort, name)
starnode.peers[name] = [socket.gethostbyname(socket.gethostname()), localPort]
starnode.mainloop()

	# def rtt(rttsum):
	# 	rttpacket = "001" + "{:<16}".format(name) + str(rttsum)
	# 	startTime = time.time()
	# 	for node in knownNodes:
	# 		if node != name:
	# 			serverSocket.sendto(rttpacket.encode(), (knownNodes[node][0], int(knownNodes[node][1])))
	# 	incomingPacket, address = serverSocket.recvfrom(2048)
	# 	endTime = time.time()
	# 	output = incomingPacket.decode()
	# 	incNode = output[3:19].strip()
	# 	roundTrip = startTime - endTime
	# 	rttsum = rttsum - rttlist[incNode][0] + roundTrip
	# 	rttlist[incNode][1] = output[19:]
	# 	print(rttlist)


	# def PeerDiscovery(self):
	# 	pdpacket = "000" + "{:<16}".format(name) + json.dumps(knownNodes)
	# 	#print(pdpacket)
	# 	for node in knownNodes:
	# 		if node != name:
	# 			serverSocket.sendto(pdpacket.encode(), (knownNodes[node][0], int(knownNodes[node][1])))
	# 	incomingPacket, address = serverSocket.recvfrom(2048)
	# 	output = incomingPacket.decode()
	# 	incKnownNodes = json.loads(output[19:])
	# 	for node in incKnownNodes:
	# 		if node not in knownNodes:
	# 			knownNodes[node] = incKnownNodes[node]
	# 	print(knownNodes)




