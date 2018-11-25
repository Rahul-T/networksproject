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

		self.receivedPackets = set()
		self.receivedAcks = set()

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
		t7 = threading.Thread( target = self.__handlepeer, args = [ s ] )
		t7.daemon = True
		t7.start()
		t8 = threading.Thread( target = self.__handlepeer, args = [ s ] )
		t8.daemon = True
		t8.start()
		t9 = threading.Thread( target = self.__handlepeer, args = [ s ] )
		t9.daemon = True
		t9.start()
		t10 = threading.Thread( target = self.__handlepeer, args = [ s ] )
		t10.daemon = True
		t10.start()
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
				if not t7.isAlive():
					t7 = threading.Thread( target = self.__handlepeer, args = [ s ] )
					t7.daemon = True
					t7.start()
				if not t8.isAlive():
					t8 = threading.Thread( target = self.__handlepeer, args = [ s ] )
					t8.daemon = True
					t8.start()
				if not t9.isAlive():
					t9 = threading.Thread( target = self.__handlepeer, args = [ s ] )
					t9.daemon = True
					t9.start()
				if not t10.isAlive():
					t10 = threading.Thread( target = self.__handlepeer, args = [ s ] )
					t10.daemon = True
					t10.start()
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
			#print(output)
			msgtype = output[0:3]
			if msgtype == "000":
				#print("Received peer discovery from " + output[8:24].strip())
				self.receivePeerDiscovery(clientAddress, output, socket)
			if msgtype == "001":
				nodeName = output[8:24]
				#print("received rtt pack from " + nodeName)
				packetNumber = output[24:]
				self.initialRTTack(socket, nodeName.strip(), packetNumber)
			if msgtype == "002":
				nodeName = output[8:24].strip()
				#print("got ack from " + nodeName)
				endTime = time.time()
				#print(self.packetTimes)
				#print("packettimes index " + str(output[24:].strip()))
				#print(self.packetTimes)
				#print("pack above")
				rtttime = endTime - self.packetTimes[int(output[24:].strip())]
				self.rtttimes[nodeName] = rtttime
				confpacknum = int(output[24:].strip())
				#print("conf")
				#print(confpacknum)
				self.receivedAcks.add(confpacknum)
			if msgtype == "003":
				self.receiveRTTsum(clientAddress, output, socket)
			if msgtype == "004":
				#print("got string")
				self.receiveStringMessage(clientAddress, output, socket)
			if msgtype == "005":
				self.receiveFile(clientAddress, output, socket, message)
			if msgtype == "006":
				#print("Received ack")
				confpacknum = int(message[24:].strip())
				self.receivedAcks.add(confpacknum)
				#print("Received ack from " + output[8:24].strip())
				#print(self.packetNum)
				#print(self.receivedAcks)

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
		temppacketnum = int(self.packetNum)
		self.packetNum += 1
		while int(temppacketnum) not in self.receivedAcks:
			#print("Sending packet " + str(temppacketnum) + " to poc")
			#print(self.receivedAcks)
			pdpacket = "000" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<100}".format(temppacketnum) + json.dumps(self.peers)
			serverSocket.sendto(pdpacket.encode(), (pocAddress, int(pocPort)))
			#print("sleep1")
			time.sleep(1)
		#print("the end")

	def sendPeerDiscovery(self, serverSocket):
		temppacketnum = int(self.packetNum)
		self.packetNum += 1
		for node in self.peers:
			if node != name:
				ts = threading.Thread( target = self.sendPeerHelper, args = [ serverSocket, temppacketnum, node ] )
				ts.daemon = True
				ts.start()
			temppacketnum = int(self.packetNum)
			self.packetNum += 1

	def sendPeerHelper(self, serverSocket, temppacketnum, node):
		while int(temppacketnum) not in self.receivedAcks:
			#print("Sending packet " + str(temppacketnum) + " to node " + str(node))
			pdpacket = "000" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<100}".format(temppacketnum) + json.dumps(self.peers)
			serverSocket.sendto(pdpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))
			#print("sleep2")
			time.sleep(1)

	def receivePeerDiscovery(self, clientAddress, message, serverSocket):
		packnum = int(message[24:123].strip())
		#print("Node name is " + message[8:24].strip())
		if (message[8:24].strip(), packnum) not in self.receivedPackets:
			self.receivedPackets.add((message[8:24].strip(), packnum))
			incKnownNodes = json.loads(message[123:])
			for node in incKnownNodes:
				if node not in self.peers:
					self.log = open(self.logfilename, 'a')
					self.log.write("First discovered node " + str(node) + " at " + str(time.time()) + "\n")
					self.log.close()
					self.peers[node] = incKnownNodes[node]
		ackpacket = "006" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<100}".format(packnum)
		nodeName = message[8:24].strip()
		serverSocket.sendto(ackpacket.encode(), (self.peers[nodeName][0], int(self.peers[nodeName][1])))

	def initialPeerDiscovery(self, s):
		timeoutcounter = 0
		while len(self.peers) < int(maxNodes) and not self.shutdown:
			try:
				if str(pocAddress) != "0" and str(pocPort) != "0" and not [pocAddress, pocPort] in self.peers.values():
					#print("NO ABC")
					#print(str(pocAddress) + " " + str(pocPort) + " ")
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
			#print("sleep3")
			time.sleep(1)
		self.sendPeerDiscovery(s)
		#print("finish")


	#RTT

	def initialSendRTT(self, serverSocket, node):
		temppacketnum = int(self.packetNum)
		self.packetNum += 1
		while int(temppacketnum) not in self.receivedAcks:
			self.startingTime = time.time()
			self.packetTimes[int(temppacketnum)] = self.startingTime
			#print(node)
			#print("stuck")
			initialrttpacket = "001" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<100}".format(temppacketnum)
			self.log = open(self.logfilename, 'a')
			self.log.write("Sent RTT request to " + str(node) + " at " + str(time.time()) + "\n")
			self.log.close()
			serverSocket.sendto(initialrttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))
			#print(temppacketnum)
			#print(self.receivedAcks)


	def initialRTTack(self, serverSocket, node, packetNumber):
		if (node, int(packetNumber.strip())) not in self.receivedPackets:
			self.receivedPackets.add((node, int(packetNumber.strip())))
		#print("sent ack")
		initialrttpacket = "002" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<100}".format(packetNumber)
		self.log = open(self.logfilename, 'a')
		self.log.write("Received RTT request from " + str(node) + " at " + str(time.time()) + "\n")
		self.log.close()
		serverSocket.sendto(initialrttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))

	def sendRTTsum(self, serverSocket):
		temppacketnum = int(self.packetNum)
		self.packetNum += 1
		#print(self.peers)
		for node in self.peers:
			if node != name:
				ts = threading.Thread( target = self.rttsumhelper, args = [ serverSocket, temppacketnum, node ] )
				ts.daemon = True
				ts.start()
			temppacketnum = int(self.packetNum)
			self.packetNum += 1

	def rttsumhelper(self, serverSocket, temppacketnum, node):
		while int(temppacketnum) not in self.receivedAcks:
			rttpacket = "003" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<32}".format(str(self.rttsum)) + "{:<100}".format(temppacketnum)
			serverSocket.sendto(rttpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))
			time.sleep(1)

	def receiveRTTsum(self, clientAddress, message, serverSocket):
		packnum = int(message[55:].strip())
		nodeName = message[8:24].strip()
		#print(message)
		#print(packnum)
		if (message[8:24].strip(), packnum) not in self.receivedPackets:
			self.receivedPackets.add((message[8:24].strip(), packnum))
			incRTTsum = message[23:55]
			#print(incRTTsum)
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
		ackpacket = "006" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<100}".format(packnum)
		serverSocket.sendto(ackpacket.encode(), (self.peers[nodeName][0], int(self.peers[nodeName][1])))

	def getintialrttsandhub(self, s):
		print("Getting rtts to each node...")
		for node in self.peers:
			if (node != name):
				ts = threading.Thread( target = self.rtthelper, args = [ s, node ] )
				ts.daemon = True
				ts.start()
		while(len(self.rtttimes) < int(maxNodes)-1):
			time.sleep(.1)
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

	def rtthelper(self, s, node):
		while (node not in self.rtttimes):
			self.initialSendRTT(s, node)
			time.sleep(1)

	def updaterttsandhub(self, s):
		time.sleep(5)
		#print("recalculating")
		for node in self.rtttimes:
			#self.startingTime = time.time()
			#self.packetTimes[int(self.packetNum)] = self.startingTime
			self.initialSendRTT(s, node)
			#self.packetNum = self.packetNum + 1
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

		if self.hubnode == name:
			temppacketnum = int(self.packetNum)
			self.packetNum += 1
			for node in self.peers:
				if node != name:
					ts = threading.Thread( target = self.sendStringHelper, args = [ serverSocket, stringMessage, temppacketnum, node ] )
					ts.daemon = True
					ts.start()
				temppacketnum = int(self.packetNum)
				self.packetNum += 1
		else:
			temppacketnum = int(self.packetNum)
			self.packetNum += 1
			while int(temppacketnum) not in self.receivedAcks:
				broadcastpacket = "004" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(name) + "{:<100}".format(temppacketnum) + stringMessage
				serverSocket.sendto(broadcastpacket.encode(), (self.peers[self.hubnode][0], int(self.peers[self.hubnode][1])))
				time.sleep(1)
		self.log = open(self.logfilename, 'a')
		self.log.write("Sent message " + stringMessage + " at " + str(time.time()) + "\n")
		self.log.close()

	def sendStringHelper(self, serverSocket, stringMessage, temppacketnum, node):
		while int(temppacketnum) not in self.receivedAcks:
			broadcastpacket = "004" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(name) + "{:<100}".format(temppacketnum) + stringMessage
			serverSocket.sendto(broadcastpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))
			time.sleep(1)

	def receiveStringMessage(self, clientAddress, message, serverSocket):
		#print("Received message: " + message)
		packnum = int(message[40:140].strip())
		if (message[24:40].strip(), packnum) not in self.receivedPackets:
			self.receivedPackets.add((message[24:40].strip(), packnum))
			print("\nReceived message from " + message[8:24].strip())
			print("Message: " + message[140:])
			print("Star-node command: ", end='', flush=True)
			if self.hubnode == name:
				temppacketnum = int(self.packetNum)
				self.packetNum += 1
				for node in self.peers:
					if node != name and node != message[8:24].strip():
						ts = threading.Thread( target = self.receiveStringHelper, args = [ serverSocket, message, temppacketnum, node ] )
						ts.daemon = True
						ts.start()
					temppacketnum = int(self.packetNum)
					self.packetNum += 1

				self.log = open(self.logfilename, 'a')
				self.log.write("Forwarded message " + message[24:] + " from " + message[8:24].strip() + " at " + str(time.time()) + "\n")
				self.log.close()
			self.log = open(self.logfilename, 'a')
			self.log.write("Received message " + message[24:] + " from " + message[8:24].strip() + " at " + str(time.time()) + "\n")
			self.log.close()

		ackpacket = "006" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<100}".format(packnum)
		nodeName = message[24:40].strip()
		serverSocket.sendto(ackpacket.encode(), (self.peers[nodeName][0], int(self.peers[nodeName][1])))
		#print("sent ack to " + nodeName)
		#print(str((self.peers[nodeName][0])) + " " +  str(int(self.peers[nodeName][1])))

	def receiveStringHelper(self, serverSocket, message, temppacketnum, node):
		while int(temppacketnum) not in self.receivedAcks:
			forwardpacket = "004" + "{:<5}".format(localPort) + message[8:24] + "{:<16}".format(name) + "{:<100}".format(temppacketnum) + message[140:]
			serverSocket.sendto(forwardpacket.encode(), (self.peers[node][0], int(self.peers[node][1])))
			time.sleep(1)

	#File broadcasting

	def sendFile(self, fileName, serverSocket):
		f = open(fileName, 'rb')
		data = f.read()
		if self.hubnode == name:
			temppacketnum = int(self.packetNum)
			self.packetNum += 1
			for node in self.peers:
				if node != name:
					ts = threading.Thread( target = self.sendFileHelper, args = [ serverSocket, temppacketnum, data, fileName, node ] )
					ts.daemon = True
					ts.start()
				temppacketnum = int(self.packetNum)
				self.packetNum += 1
		else:
			temppacketnum = int(self.packetNum)
			self.packetNum += 1
			while int(temppacketnum) not in self.receivedAcks:
				filepacketheader = "005" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(name) + "{:<16}".format(fileName) + "{:<100}".format(temppacketnum)
				z = filepacketheader.encode()
				filepacketvalue = data
				totalfilepacket = z + data
				serverSocket.sendto(totalfilepacket, (self.peers[self.hubnode][0], int(self.peers[self.hubnode][1])))
				time.sleep(1)

		f.close()
		self.log = open(self.logfilename, 'a')
		self.log.write("Sent file " + fileName + " at " + str(time.time()) + "\n")
		self.log.close()

	def sendFileHelper(self, serverSocket, temppacketnum, data, fileName, node):
		while int(temppacketnum) not in self.receivedAcks:
			filepacketheader = "005" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<16}".format(name) + "{:<16}".format(fileName) + "{:<100}".format(temppacketnum)
			z = filepacketheader.encode()
			filepacketvalue = data
			totalfilepacket = z + data
			serverSocket.sendto(totalfilepacket, (self.peers[node][0], int(self.peers[node][1])))
			time.sleep(1)

	def receiveFile(self, clientAddress, packetheader, serverSocket, message):
		packnum = int(message[56:156].strip())
		if (message[24:40].strip(), packnum) not in self.receivedPackets:
			self.receivedPackets.add((message[24:40].strip(), packnum))
			print("\nReceived file from " + packetheader[8:24])
			fileName = packetheader[40:56].strip()
			print(fileName)
			tempname = name + fileName
			f = open(tempname, 'wb')
			data = message[156:]
			f.write(data)
			print("Star-node command: ", end='', flush=True)
			if self.hubnode == name:
				temppacketnum = int(self.packetNum)
				self.packetNum += 1
				for node in self.peers:
					if node != name and node != packetheader[8:24].strip():
						ts = threading.Thread( target = self.receiveFileHelper, args = [ serverSocket, packetheader, temppacketnum, data, node, fileName ] )
						ts.daemon = True
						ts.start()
					temppacketnum = int(self.packetNum)
					self.packetNum += 1


				self.log = open(self.logfilename, 'a')
				self.log.write("Forwarded file " + tempname + " from " + packetheader[8:24].strip() + " at " + str(time.time()) + "\n")
				self.log.close()
			f.close()
			self.log = open(self.logfilename, 'a')
			self.log.write("Received file " + tempname + " from " + packetheader[8:24].strip() + " at " + str(time.time()) + "\n")
			self.log.close()

		ackpacket = "006" + "{:<5}".format(localPort) + "{:<16}".format(name) + "{:<100}".format(packnum)
		nodeName = packetheader[24:40].strip()
		#print("Sent ack to " + nodeName)
		serverSocket.sendto(ackpacket.encode(), (self.peers[nodeName][0], int(self.peers[nodeName][1])))

	def receiveFileHelper(self, serverSocket, message, temppacketnum, data, node, fileName):
		while int(temppacketnum) not in self.receivedAcks:
			filepacketheader = "005" + "{:<5}".format(localPort) + message[8:24] + "{:<16}".format(name) + "{:<16}".format(fileName) + "{:<100}".format(temppacketnum)
			z = filepacketheader.encode()
			filepacketvalue = data
			totalfilepacket = z + data
			serverSocket.sendto(totalfilepacket, (self.peers[node][0], int(self.peers[node][1])))
			time.sleep(1)




#Main runner
starnode = Peer(maxNodes, localPort, name)
starnode.peers[name] = [socket.gethostbyname(socket.gethostname()), localPort]
starnode.mainloop()


