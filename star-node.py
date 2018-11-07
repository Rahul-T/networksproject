import sys
import json
import socket
import time
import threading
import _thread
import os

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
		self.startingTime = time.time()

	    # used to stop the main loop
		self.shutdown = False  

		self.handlers = {}
		self.router = None
	    # end constructor

	def mainloop( self ):
		s = self.makeServerSocket( self.serverport )
		#s.settimeout(10)
		self.initialPeerDiscovery(s)
		self.getintialrttsandhub(s)
		t4 = threading.Thread( target = self.__commands, args = [ s ] )
		t4.start()
		t5 = threading.Thread( target = self.__handlepeer, args = [ s ] )
		t5.daemon = True
		t5.start()
		t6 = threading.Thread(target = self.updaterttsandhub, args = [ s ])
		t6.daemon = True
		t6.start()

		while not self.shutdown:
			try:
				if not t4.isAlive() and not self.shutdown:
					t4 = threading.Thread( target = self.__commands, args = [ s ] )
					t4.start()
				if not t5.isAlive():
					t5 = threading.Thread( target = self.__handlepeer, args = [ s ] )
					t5.daemon = True
					t5.start()
				if not t6.isAlive():
					t6 = threading.Thread(target = self.updaterttsandhub, args = [ s ])
					t6.daemon = True
					t6.start()
			except KeyboardInterrupt:
				self.shutdown = True
				continue
			except:
				if self.debug:
					traceback.print_exc()
					continue		

	








	#Server socket creation

	def makeServerSocket(self, port):
		serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		serverSocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
		serverSocket.bind(('', port))
		return serverSocket




	#Thread handling functions

	def __handlepeer( self, socket, initialRTTnode = None, startTime = None ):
		message, clientAddress = socket.recvfrom(65000)
		output = message.decode()
		port = output[3:8]

		try:

			msgtype = output[0:3]

			if msgtype == "000":
				self.receivePeerDiscovery(clientAddress, output)
			if msgtype == "001":
				nodeName = output[8:24]
				self.initialRTTack(socket, nodeName.strip())
			if msgtype == "002":
				nodeName = output[8:24].strip()
				#print("received")
				endTime = time.time()
				rtttime = endTime - self.startingTime
				self.rtttimes[nodeName] = rtttime
			if msgtype == "003":
				self.receiveRTTsum(clientAddress, output)
			if msgtype == "004":
				self.receiveStringMessage(clientAddress, output, socket)
			if msgtype == "005":
				self.receiveFile(clientAddress, output, socket)

		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()



	def __commands(self, socket):
		command = input("Star-node command: ")
		if command == "show-status":
			self.showstatus()
		elif command == "disconnect":
			self.shutdown = True
		elif command[0:4] == "send":
			if command[5] == "\"" and command.endswith("\""):
				stringMessage = command[6:-1]
				self.sendStringMessage(socket, stringMessage)
			else:
				fileName = command[5:]
				self.sendFile(fileName, socket)



	#Peer Discovery

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

	def initialPeerDiscovery(self, s):
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


	#RTT

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
		if self.hubnode == name:
			if float(incRTTsum) + 0.01 < float(self.rttsum):
				self.hubnode = nodeName
		elif float(incRTTsum) + 0.01 < float(self.rttsums[self.hubnode]):
			self.hubnode = nodeName
		self.rttsums[nodeName] = incRTTsum

	def getintialrttsandhub(self, s):
		for node in self.peers:
			if (node != name):
				t2 = threading.Thread( target = self.__handlepeer, args = [ s ] )
				t2.start()
				while (node not in self.rtttimes):
					self.startingTime = time.time()
					self.initialSendRTT(s, node)
					if not t2.isAlive():
						t2 = threading.Thread( target = self.__handlepeer, args = [ s ] )
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

	def updaterttsandhub(self, s):
		time.sleep(20)
		print("recalculating")
		for node in self.rtttimes:
			self.startingTime = time.time()
			self.initialSendRTT(s, node)
		#print(self.rttsum)
		self.rttsum = 0
		for node in self.rtttimes:
			self.rttsum += self.rtttimes[node]
		#print(self.rttsum)
		if self.hubnode != name and float(self.rttsum) + 0.01 < float(self.rttsums[self.hubnode]):
			self.hubnode = name
		else:
			for node in self.rttsums:
				if float(self.rttsums[node]) + 0.01 < float(self.rttsum):
					self.hubnode = node
		self.sendRTTsum(s)

	#Show status

	def showstatus(self):
		for node in self.rttsums:
			print("Node name: " + node + " RTT sum: " + self.rttsums[node])
		print("Hub: " + self.hubnode)




	#String message broadcasting

	def sendStringMessage(self, serverSocket, stringMessage):
		broadcastpacket = "004" + "{:<5}".format(localPort) + "{:<16}".format(name) + stringMessage
		if self.hubnode == name:
			for node in self.peers:
				if node != name:
					serverSocket.sendto(broadcastpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))
		else:
			serverSocket.sendto(broadcastpacket.encode(), (self.peers[self.hubnode][0], int(self.peers[self.hubnode][1])))

	def receiveStringMessage(self, clientAddress, message, serverSocket):
		print("\nReceived message from " + message[8:24])
		print("Message: " + message[24:])
		print("Star-node command: ", end='', flush=True)
		if self.hubnode == name:
			for node in self.peers:
				if node != name and node != message[8:24].strip():
					serverSocket.sendto(message.encode(), (self.peers[node][0], int(self.peers[node][1])))


	#File broadcasting

	def sendFile(self, fileName, serverSocket):
		f = open(fileName, 'rb')
		data = f.read()
		filepacketheader = "005" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(fileName)
		filepacketvalue = data

		if self.hubnode == name:
			for node in self.peers:
				if node != name:
					serverSocket.sendto(filepacketheader.encode(), (self.peers[node][0], int(self.peers[node][1])))
					serverSocket.sendto(filepacketvalue, (self.peers[node][0], int(self.peers[node][1])))
		else:
			serverSocket.sendto(filepacketheader.encode(), (self.peers[self.hubnode][0], int(self.peers[self.hubnode][1])))
			serverSocket.sendto(filepacketvalue, (self.peers[self.hubnode][0], int(self.peers[self.hubnode][1])))

		f.close()

	def receiveFile(self, clientAddress, packetheader, serverSocket):
		print("\nReceived file from " + packetheader[8:24])
		fileName = packetheader[24:40].strip()
		print(fileName)
		#FIX ME
		#FIX ME
		#FIX ME
		tempname = name + ".txt"
		f = open(tempname, 'wb')
		data, addr = serverSocket.recvfrom(65000)
		f.write(data)
		print("Star-node command: ", end='', flush=True)
		if self.hubnode == name:
			for node in self.peers:
				if node != name and node != packetheader[8:24].strip():
					serverSocket.sendto(packetheader.encode(), (self.peers[node][0], int(self.peers[node][1])))
					serverSocket.sendto(data, (self.peers[node][0], int(self.peers[node][1])))
		f.close()


#Main runner
starnode = Peer(maxNodes, localPort, name)
starnode.peers[name] = [socket.gethostbyname(socket.gethostname()), localPort]
starnode.mainloop()




