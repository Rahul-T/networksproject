import sys
import json
import socket
import time
import threading
import _thread
import os
from threading import Lock

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
		self.logfilename = name + "log.txt"

		self.packetNum = 0
		self.packetTimes = {}

		self.receivedPackets = {}
		self.receivedAcks = {}

	    # used to stop the main loop
		self.shutdown = False  

		self.handlers = {}
		self.router = None

	    # end constructor

	def mainloop( self ):
		try:
			os.remove(self.logfilename)
		except:
			pass
		s = self.makeServerSocket( self.serverport )
		#s.settimeout(10)
		print("Running peer discovery...")
		

		te = threading.Thread( target = self.__handlepeer, args = [ s ] )
		te.start()
		tr = threading.Thread( target = self.initialPeerDiscovery, args = [ s ] )
		tr.start()

		while tr.isAlive():
			if not te.isAlive():
				te = threading.Thread( target = self.__handlepeer, args = [ s ] )
				te.start()


		if self.shutdown == True:
			print("Timeout")
			sys.exit()
		

		ta = threading.Thread( target = self.__handlepeer, args = [ s ] )
		ta.start()
		tz = threading.Thread( target = self.getintialrttsandhub, args = [ s ] )
		tz.start()

		while tz.isAlive():
			if not ta.isAlive():
				ta = threading.Thread( target = self.__handlepeer, args = [ s ] )
				ta.start()

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
				packetNumber = output[24:]
				self.initialRTTack(socket, nodeName.strip(), packetNumber)
			if msgtype == "002":
				nodeName = output[8:24].strip()
				endTime = time.time()
				rtttime = endTime - self.packetTimes[int(output[24:].strip())]
				self.rtttimes[nodeName] = rtttime
			if msgtype == "003":
				#print("received rttsum packet from " + output[8:24].strip())
				self.receiveRTTsum(clientAddress, output)
			if msgtype == "004":
				self.receiveStringMessage(clientAddress, output, socket)
			if msgtype == "005":
				self.receiveFile(clientAddress, output, socket, message)

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
		elif command == "show-log":
			self.showlog()



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
				self.log = open(self.logfilename, 'a')
				self.log.write("First discovered node " + str(node) + " at " + str(time.time()) + "\n")
				self.log.close()
				self.peers[node] = incKnownNodes[node]

	def initialPeerDiscovery(self, s):
		timeoutcounter = 0
		while len(self.peers) < int(maxNodes) and not self.shutdown:
			try:
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
			timeoutcounter += 1
			if timeoutcounter == 30:
				self.shutdown = True
			time.sleep(1)
		self.sendPeerDiscovery(s)


	#RTT

	def initialSendRTT(self, serverSocket, node, packetNum):
		initialrttpacket = "001" + "{:<5}".format(localPort) + "{:<16}".format(name) + str(packetNum)
		self.log = open(self.logfilename, 'a')
		self.log.write("Sent RTT request to " + str(node) + " at " + str(time.time()) + "\n")
		self.log.close()
		serverSocket.sendto(initialrttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))


	def initialRTTack(self, serverSocket, node, packetNumber):
		initialrttpacket = "002" + "{:<5}".format(localPort) + "{:<16}".format(name) + packetNumber
		self.log = open(self.logfilename, 'a')
		self.log.write("Received RTT request from " + str(node) + " at " + str(time.time()) + "\n")
		self.log.close()
		serverSocket.sendto(initialrttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def sendRTTsum(self, serverSocket):
		rttpacket = "003" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(self.rttsum)
		#print(self.peers)
		for node in self.peers:
			if node != name:
				#print("Sent my rttsum of " + str(self.rttsum) + " to " + node)
				serverSocket.sendto(rttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def receiveRTTsum(self, clientAddress, message):
		
		incRTTsum = message[23:]
		nodeName = message[8:24].strip()
		#print("Received rttsum of " + incRTTsum + " from " + nodeName)
		self.log = open(self.logfilename, 'a')
		self.log.write("Received new RTT sum from " + str(nodeName) + " at " + str(time.time()) + "\n")
		self.log.close()
		#print("stuck1")
		if nodeName in self.rttsums:
			oldRTTsum = self.rttsums[nodeName]
			self.rttsums[nodeName] = incRTTsum
		#print("stuck2")
		if self.hubnode == name:
			#print("stuck3")
			if float(incRTTsum) + 0.25 < float(self.rttsum):
				self.hubnode = nodeName
				self.log = open(self.logfilename, 'a')
				self.log.write("Updated hub from " + self.hubnode + " to " + nodeName + " at " + str(time.time()) + "\n")
				self.log.close()
				#print("h1")
		elif float(incRTTsum) + 0.25 < float(self.rttsums[self.hubnode]) and self.hubnode != nodeName:
			#print("stuck4")
			self.log = open(self.logfilename, 'a')
			self.log.write("Updated hub from " + self.hubnode + " to " + nodeName + " at " + str(time.time()) + "\n")
			self.log.close()
			self.hubnode = nodeName
			#print("h2")
		elif self.hubnode == nodeName:
			# print("stuck5")
			# if float(incRTTsum) > float(oldRTTsum):
			# 	x = 1
			#print("stuck5a")
			if float(incRTTsum) > float(oldRTTsum):
				# print("stuckA")
				tempmin = float(incRTTsum)
				tempnode = self.hubnode
				# print("stuckB")
				for node in self.rttsums:
					if float(self.rttsums[node]) < float(tempmin):
						# print("stuckC")
						tempmin = float(self.rttsums[node])
						tempnode = node
				# print("stuckD")
				if float(self.rttsum) < float(tempmin):
					# print("stuckE")
					tempmin = float(self.rttsum)
					tempnode = name
				# print("stuckF")
				if float(tempmin) + 0.25 < float(incRTTsum):
					# print("stuckG")
					self.hubnode = tempnode
					self.log = open(self.logfilename, 'a')
					self.log.write("Updated hub from " + self.hubnode + " to " + tempnode + " at " + str(time.time()) + "\n")
					self.log.close()
			# print("stuckI")
		# print("stuck6")
		if nodeName not in self.rttsums:
			self.rttsums[nodeName] = incRTTsum
		# print("stuck7")
		# print("Post-receive status")
		# print(name + ": " + str(self.rttsum))
		# for node in self.rttsums:
		# 	print(node + " " + str(self.rttsums[node]))
		# print("Hubnode: " + self.hubnode)

	def getintialrttsandhub(self, s):
		print("Getting rtts to each node...")
		for node in self.peers:
			if (node != name):
				while (node not in self.rtttimes):
					self.startingTime = time.time()
					self.packetTimes[int(self.packetNum)] = self.startingTime
					self.initialSendRTT(s, node, self.packetNum)
					self.packetNum = self.packetNum + 1
					time.sleep(1)

		#print(self.rtttimes)
		for node in self.rtttimes:
			self.rttsum += self.rtttimes[node]

		self.log = open(self.logfilename, 'a')
		self.log.write("Calculated new RTT sum " + str(self.rttsum) + " at " + str(time.time()) + "\n")
		self.log.close()

		print("Sending/Receiving RTT sums...")
		self.sendRTTsum(s)
		#sentit = False
		while len(self.rttsums) < int(maxNodes)-1 and not self.shutdown:
			try:
				#if not sentit:
				self.sendRTTsum(s)
					#sentit = True
			except KeyboardInterrupt:
				self.shutdown = True
				continue
			except:
				if self.debug:
					traceback.print_exc()
					continue
			time.sleep(1)

			#print(self.rttsums)
		print("Calculating hub...")
		#print("last2")
		#print(self.rttsums)
		minrttsum = self.rttsum
		self.hubnode = name
		for node in self.rttsums:
			if float(self.rttsums[node]) < float(minrttsum):
				minrttsum = self.rttsums[node]
				self.hubnode = node
				#print("h3")
		self.log = open(self.logfilename, 'a')
		self.log.write("Initialized hub to " + self.hubnode + " at " + str(time.time()) + "\n")
		self.log.close()

	def updaterttsandhub(self, s):
		time.sleep(5)
		#print("recalculating")
		for node in self.rtttimes:
			self.startingTime = time.time()
			self.packetTimes[int(self.packetNum)] = self.startingTime
			self.initialSendRTT(s, node, self.packetNum)
			self.packetNum = self.packetNum + 1
		#print(self.rttsum)
		self.rttsum = 0
		for node in self.rtttimes:
			self.rttsum += self.rtttimes[node]

		self.log = open(self.logfilename, 'a')
		self.log.write("Calculated new RTT sum " + str(self.rttsum) + " at " + str(time.time()) + "\n")
		self.log.close()

		#print(self.rttsum)
		if self.hubnode != name and float(self.rttsum) + 0.25 < float(self.rttsums[self.hubnode]):
			#print("h4")
			self.log = open(self.logfilename, 'a')
			self.log.write("Updated hub from " + self.hubnode + " to " + name + " at " + str(time.time()) + "\n")
			self.log.close()

			self.hubnode = name
		elif self.hubnode == name:
			tempmin = float(self.rttsum)
			tempnode = name
			for node in self.rttsums:
				if float(self.rttsums[node]) < tempmin:
					tempmin = float(self.rttsums[node])
					tempnode = node
			if tempmin + 0.25 < self.rttsum:
				self.log = open(self.logfilename, 'a')
				self.log.write("Updated hub from " + self.hubnode + " to " + tempnode + " at " + str(time.time()) + "\n")
				self.log.close()
				
				self.hubnode = tempnode

			#print("Tempmin " + str(tempmin)),
			#print(" My rttsum " + str(self.rttsum))
		self.sendRTTsum(s)

	#Show status

	def showstatus(self):
		print("Node name: " + name + " RTT sum: " + str(self.rttsum))
		for node in self.rttsums:
			print("Node name: " + node + " RTT sum: " + self.rttsums[node])
		print("Hub: " + self.hubnode)


	def showlog(self):
		self.log = open(self.logfilename, 'r')
		print(self.log.read())
		self.log.close()

	#String message broadcasting

	def sendStringMessage(self, serverSocket, stringMessage):
		broadcastpacket = "004" + "{:<5}".format(localPort) + "{:<16}".format(name) + stringMessage
		if self.hubnode == name:
			for node in self.peers:
				if node != name:
					serverSocket.sendto(broadcastpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))
		else:
			serverSocket.sendto(broadcastpacket.encode(), (self.peers[self.hubnode][0], int(self.peers[self.hubnode][1])))
		self.log = open(self.logfilename, 'a')
		self.log.write("Sent message " + stringMessage + " at " + str(time.time()) + "\n")
		self.log.close()

	def receiveStringMessage(self, clientAddress, message, serverSocket):
		print("\nReceived message from " + message[8:24])
		print("Message: " + message[24:])
		print("Star-node command: ", end='', flush=True)
		if self.hubnode == name:
			for node in self.peers:
				if node != name and node != message[8:24].strip():
					serverSocket.sendto(message.encode(), (self.peers[node][0], int(self.peers[node][1])))
			self.log = open(self.logfilename, 'a')
			self.log.write("Forwarded message " + message[24:] + " from " + message[8:24].strip() + " at " + str(time.time()) + "\n")
			self.log.close()
		self.log = open(self.logfilename, 'a')
		self.log.write("Received message " + message[24:] + " from " + message[8:24].strip() + " at " + str(time.time()) + "\n")
		self.log.close()


	#File broadcasting

	def sendFile(self, fileName, serverSocket):
		f = open(fileName, 'rb')
		data = f.read()
		filepacketheader = "005" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(fileName)
		z = filepacketheader.encode()
		filepacketvalue = data
		totalfilepacket = z + data
		print(totalfilepacket)
		if self.hubnode == name:
			for node in self.peers:
				if node != name:
					serverSocket.sendto(totalfilepacket, (self.peers[node][0], int(self.peers[node][1])))
					#serverSocket.sendto(filepacketvalue, (self.peers[node][0], int(self.peers[node][1])))
		else:
			serverSocket.sendto(totalfilepacket, (self.peers[self.hubnode][0], int(self.peers[self.hubnode][1])))
			#serverSocket.sendto(filepacketvalue, (self.peers[self.hubnode][0], int(self.peers[self.hubnode][1])))

		f.close()
		self.log = open(self.logfilename, 'a')
		self.log.write("Sent file " + fileName + " at " + str(time.time()) + "\n")
		self.log.close()


	def receiveFile(self, clientAddress, packetheader, serverSocket, message):
		print("\nReceived file from " + packetheader[8:24])
		fileName = packetheader[24:40].strip()
		print(fileName)
		tempname = name + fileName
		f = open(tempname, 'wb')
		#data, addr = serverSocket.recvfrom(65000)
		data = message[40:]
		print(message)
		f.write(data)
		print("Star-node command: ", end='', flush=True)
		if self.hubnode == name:
			for node in self.peers:
				if node != name and node != packetheader[8:24].strip():
					serverSocket.sendto(message, (self.peers[node][0], int(self.peers[node][1])))
					#serverSocket.sendto(data, (self.peers[node][0], int(self.peers[node][1])))
					self.log = open(self.logfilename, 'a')
					self.log.write("Forwarded file " + tempname + " from " + packetheader[8:24].strip() + " at " + str(time.time()) + "\n")
					self.log.close()
		f.close()

		self.log = open(self.logfilename, 'a')
		self.log.write("Received file " + tempname + " from " + packetheader[8:24].strip() + " at " + str(time.time()) + "\n")
		self.log.close()


#Main runner
starnode = Peer(maxNodes, localPort, name)
starnode.peers[name] = [socket.gethostbyname(socket.gethostname()), localPort]
starnode.mainloop()



