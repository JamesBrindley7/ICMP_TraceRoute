#!/ur/bin/python
# -*- coding: UTF-8 -*-

from socket import * 
import sys 


def handleRequest(tcpSocket):
	
	request_message = tcpSocket.recv(1024) # 1. Receive request message from the client on connection socket
	
	request_get = request_message.splitlines()[0] #Splits the recieved message and only keeps the first line
	request_get = request_get.rstrip("\r\n")	#returns a new line with extra lines removed if any
	
	(get_request, filename_,http_version) = request_get.split()	#Split the line into the 3 different sections
	
	_,filename = filename_.split("/")
	
	try:
		file = open(filename, "r")	# 3. Read the corresponding file from disk
	except IOError: 
           response_header = "HTTP/1.1 404 Not Found \r\n\n"	# 5. Send the correct HTTP response error
           tcpSocket.send(response_header)
	else:
		filebuffer = file.read() 	# 4. Store in temporary buffer
		filesize = len(filebuffer)
		response_header = "HTTP/1.1 200 OK \r\n\n"
		tcpSocket.send(response_header+filebuffer) # 6. Send the content of the file to the socket
		
	tcpSocket.close() # 7. Close the connection socket 
    

def startServer(serverAddress, serverPort=8000):
	while True:
		tcpSocket = socket(AF_INET, SOCK_STREAM)	# 1. Create server socket
		tcpSocket.bind((serverAddress, int(serverPort))) # 2. Bind the server socket to server address and server port
		tcpSocket.listen(5) # 3. Continuously listen for connections to server sockets
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