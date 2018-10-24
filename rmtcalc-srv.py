from socket import *
import sys

# Some parts of the connection setup in this code are based off of the
# socket programming lecture slides that were presented in class

# When running the program, 2 command line arguments are required
# for the protocol and server port
protocol = sys.argv[1]
serverPort = int(sys.argv[2])

# Create a UDP or TCP socket depending on the protocol and bind the serverSocket
# to the passed in port
if protocol == "UDP":
    serverSocket = socket(AF_INET, SOCK_DGRAM)
elif protocol == "TCP":
    serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))

# Listen for incoming TCP requests
if protocol == "TCP":
    serverSocket.listen(1)

# Set the connection variable to 0 if there are no current connections
connectionOpen = 0
print("The server is ready to receive")

while True:
    # Receive message from the client
    if protocol == "UDP":
        # Receive message from server socket
        message, clientAddress = serverSocket.recvfrom(2048)
    elif protocol == "TCP":
        if connectionOpen == 0:
            # Server waits for incoming requests then creates a new socket
            connectionSocket, addr = serverSocket.accept()
            connectionOpen = 1;

        try:
            # If the message from the client can not be received or the length
            # of the message is 0, the client has closed the connection so
            # the connection on the serverside must also be closed (TCP only)
            message = connectionSocket.recv(1024)
            divide = 1/len(message)
        except Exception as e:
            # Prevent the message analysis / operations by setting
            # connectionOpen to 0
            connectionOpen = 0
            connectionSocket.close()

    operation = message.decode()

    # Conduct required operations on received message
    if protocol == "UDP" or connectionOpen == 1:
        firstnum = operation[0:16]
        secondnum = operation[16:32]
        operator = operation[32:33]
        finalanswer = 0
        info = ""

        # Calculate operation requested by client
        if operator == "+":
            finalanswer = float(firstnum) + float(secondnum)
        elif operator == "-":
            finalanswer = float(firstnum) - float(secondnum)
        elif operator == "*":
            finalanswer = float(firstnum) * float(secondnum)
        elif operator == "/":
            if float(secondnum) == 0.0:
                # Prevent divide by zero exception
                info = "ERR: Can't divide by zero"
            else:
                finalanswer = float(firstnum) / float(secondnum)
        else:
            # Server only supports +, -, *, and /
            # Any other operations are not supported
            info = "ERR: Invalid operand"

        # If the result of the arithmetic operation is an integer, convert
        # the result back to an integer so that the user doesn't receive an
        # unnecessary floating point value
        if int(finalanswer) == float(finalanswer):
            finalanswer = int(finalanswer)

        finalanswer = str(finalanswer)
        # Pad the final answer with spaces if it is less than 16 bytes
        # Ensure first byte is the sign if the number is not negative
        if finalanswer[0] != "-":
            finalanswer = "+" + finalanswer
        finalanswer = finalanswer[:16]
        finalanswer = "{:<16}".format(finalanswer)
        if not info:
            # Pad the message with spaces if it is less than 16 bytes
            info = "{:<32}".format("Offered to you by Rahul's server!")

        # Pack the answer with the message
        finalmessage = finalanswer + info

        # Send the answer back to the client
        if protocol == "UDP":
            serverSocket.sendto(finalmessage.encode(), clientAddress)
        elif protocol == "TCP":
            connectionSocket.send(finalmessage.encode())
