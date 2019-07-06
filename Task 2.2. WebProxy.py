#!/ur/bin/python
# -*- coding: UTF-8 -*-

from socket import * 
import sys 


def handleRequest(tcpSocket):
	
	
	request_message = tcpSocket.recv(1024) # 1. Receive request message from the client on connection socket
	request_get = request_message.splitlines()[0] #Splits the recieved message and only keeps the first line
	request_get = request_get.rstrip("\r\n")	#returns a new line with extra lines removed if any
	
	(get_request, filename,http_version) = request_get.split()	#Split the line into the 3 different sections
	
	http, address = filename.split("://") #Splits the line by the start, cuts of the http;//
	address,_ = address.split("/") #Splits the blackslash after the address
	try:
		Address = gethostbyname(address)	#Convert the address into a IP
	except gaierror:
		tcpSocket.send("HTTP/1.1 502 Bad Gateway \r\n\n")
		return
		
		
	sendsocket = socket(AF_INET, SOCK_STREAM)  #Open a new socket
	sendsocket.connect((Address, 80))	#Connect the socket to the destination address and to port 80
	sendsocket.send(request_message)         # send request to webserver
	
	Chunks = 0
	Checks = 5
	while True:
		destinationresponce = sendsocket.recv(1024)	#Wait for a responce
		if (len(destinationresponce) > 0):	#If theres a responce then send it to the requester
			tcpSocket.send(destinationresponce)
			Chunks = Chunks + 1
			Checks = Checks - 1
		if (len(destinationresponce) == 0 and Chunks > 0): #If all chunks of data are gotten then break
			break
		if (Checks == 5):
			tcpSocket.send("HTTP/1.1 404 Not Found \r\n\n") #If its checked 5 times then break saying its not found
			break
		Checks = Checks + 1
	sendsocket.close()
	tcpSocket.close() # 7. Close the connection socket 
    

def startServer(serverAddress, serverPort=8000):
	while True:
		tcpSocket = socket(AF_INET, SOCK_STREAM)	# 1. Create server socket
		tcpSocket.bind((serverAddress, int(serverPort))) # 2. Bind the server socket to server address and server port
		tcpSocket.listen(5) # 3. Continuously listen for connections to server socket
		newsocket, received_address = tcpSocket.accept()
		handleRequest(newsocket)	# 4. When a connection is accepted, call handleRequest function, passing new connection socket (see https://docs.python.org/2/library/socket.html#socket.socket.accept)
		tcpSocket.close() # 5. Close server socket

portnum = raw_input("Please enter a port number to use: ")
try:
   val = int(portnum)
except ValueError:
	startServer("127.0.0.1")
else:
	startServer("127.0.0.1", portnum)