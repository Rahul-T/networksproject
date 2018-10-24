from socket import *
import re
import sys

# Some parts of the connection setup in this code are based off of the
# socket programming lecture slides that were presented in class

# When running the program, 3 command line arguments are required
# for the protocol, server name, and server port
protocol = sys.argv[1]
serverName = sys.argv[2]
serverPort = int(sys.argv[3])

# Based on the protocol, the connection must be set up differently
# TCP needs a established connection channel between the client and server
# while UDP does not
if protocol == "UDP":
    # Create a UDP socket
    clientSocket = socket(AF_INET, SOCK_DGRAM)
elif protocol == "TCP":
    # Create a TCP socket and connect to the server
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))

# Receive user input here (proper formatting is assumed)
message = input('Enter operation: ')

# This client accepts input until the user types "quit"
while message != "quit":

    # A regular expression is used to find all integers and floats
    # in the input
    operands = re.findall("[+-]?\d*\.?\d+", message)

    # The operand is found by looping through the input string and finding
    # the first symbol which is not a space or period
    # This starts at the second character because the first character may be
    # a "-" sign for the fist number
    for c in message[1:]:
        if not c.isdigit() and c != " " and c != ".":
            operator = c
            break

    # If no sign is preceding either of the two numbers
    # prepend a positive sign
    if operands[0][:1] != '+' and operands[0][:1] != '-':
        operands[0] = "+" + operands[0]

    if operands[1][:1] != '+' and operands[1][:1] != '-':
        operands[1] = "+" + operands[1]

    # Pad the two numbers with spaces if they are less than 16 bytes
    firstoperand = "{:<16}".format(operands[0])
    secondoperand = "{:<16}".format(operands[1])

    # Pack the message together in the correct order
    fullmessage = firstoperand + secondoperand + operator

    # Send packed message to server, then output the modified message
    # from the server (TCP receives from the established connection socket so
    # separate cases must be made for UDP and TCP)
    if protocol == "UDP":
        clientSocket.sendto(fullmessage.encode(), (serverName, serverPort))
        modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
    elif protocol == "TCP":
        clientSocket.send(fullmessage.encode())
        modifiedMessage = clientSocket.recv(1024)

    output = modifiedMessage.decode()
    # If there is an error, only output the error message
    # not the meaningless result
    if output[16:20] == "ERR:":
        print(output[16:])
    # If the leading sign is positive, don't print it because it is unnecessary
    elif output[0] == "-":
        print("Result = " + output[0:16] + "\n" + output[16:])
    else:
        print("Result = " + output[1:16] + "\n" + output[16:])

    # Continuously loop and ask for user input
    message = input('Enter operation:')

# Once the user types "quit", close the connection socket
print("Bye!")
clientSocket.close()
