#!/usr/bin/python
# -*- coding: UTF-8 -*-

from socket import *
import os
import sys
import struct
import time
import select
import binascii  


ICMP_ECHO_REQUEST = 8 #ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0 #ICMP type code for echo reply messages


def checksum(string): 
	csum = 0
	countTo = (len(string) // 2) * 2  
	count = 0

	while count < countTo:
		thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
		csum = csum + thisVal 
		csum = csum & 0xffffffff  
		count = count + 2
		
	if countTo < len(string):
		csum = csum + ord(string[len(string) - 1])
		csum = csum & 0xffffffff 
		
	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff 
	answer = answer >> 8 | (answer << 8 & 0xff00)
	
	if sys.platform == 'darwin':
		answer = htons(answer) & 0xffff        
	else:
		answer = htons(answer)

	return answer 


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout, datasent, TTL):
	timeLeft = timeout
	counter = 0
	while True:
		starttimer = time.time()
		Ready = select.select([icmpSocket], [], [], timeLeft)	# 1. Wait for the socket to receive a reply Says wait until ready for reading
		timer = (time.time() - starttimer)


		if Ready[0] == []: # Timeout 	If not ready for reading then timeout
			return 0, False, "", ""
		
		timeReceived = time.time() # 2. Once received, record time of receipt, otherwise, handle a timeout
		received_Packet, received_DestinationAddress = icmpSocket.recvfrom(1024) # recieve the packet
		header = received_Packet[20:28] #section the header from the other bytes
		received_Type, received_Code, received_Checksum, received_ID, received_Sequence = struct.unpack("bbHHh", header)	# 4. Unpack the packet header for useful information, including the ID
		try:
			addressname = gethostbyaddr(received_DestinationAddress[0]) #try to convert the ip to host name
		except herror:
			addressname = "-------" # if it cant then put it as a -
		if destinationAddress == received_DestinationAddress[0] and received_Type == 0 and received_ID == ID:	# 5. Check that the ID matches between the request and reply
			datalength = len(datasent)
			data = received_Packet[28:datalength]
			return timeReceived, True, addressname[0], received_DestinationAddress[0]	# 6. Return total network delay
		elif received_Type == 11: #if its a ttl reply
			return timeReceived, False, addressname[0], received_DestinationAddress[0]
		elif destinationAddress == received_DestinationAddress[0]:
			return timeReceived, False, addressname[0], received_DestinationAddress[0]
		TTL+= 1
		timeLeft = timeLeft - timer
		if timeLeft <= 0:
			return 0, True , "", ""

def sendOnePing(icmpSocket, destinationAddress, ID, sequence):
	# Header is type (8), code (8), checksum (16), id (16), sequence (16)
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, ID, sequence)   # 1. Build ICMP header
	
	data = 192 * "b" # Sends 192 b's as data
	checksnum = checksum(header + data)  # 2. Checksum ICMP packet using given function
	
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, checksnum, ID, sequence) # 3. Insert checksum into packet
	package = header + data	#Adds the header and the data into one package
	
	icmpSocket.sendto(package, (destinationAddress, 33534)) # 4. Send packet using socket
	timesent = time.time() # 5. Record time of send
	return timesent, data

def doOnePing(destinationAddress, timeout, maxhops): 
	arr = []
	recieved = 0
	lost = 0
	sequence = 0
	passed = False
	TTL = 1
	icmpprotocol = getprotobyname("icmp")   #Gets the protocol code
	udpprotocol = getprotobyname("udp") 
	while passed == False: #Starts a loop to keep increasing ttl until its at its destination
		if maxhops == 0: #If max hops is reached then stop
			return arr, TTL, recieved
		print TTL, "   ",
		completed = 0;
		for x in range(0, 3): #Does a loop of 3 each destination to get different readins
	
			sending_socket = socket(AF_INET, SOCK_RAW, icmpprotocol) #Creates the sending socket
			sending_socket.setsockopt(SOL_IP, IP_TTL, TTL)
	
			ID = os.getpid()   # creates a unique ID based on the process ID
			timesent, datasent = sendOnePing(sending_socket, destinationAddress, ID, sequence) # 2. Call sendOnePing function
			timerecieved, passed, addressname, received_DestinationAddress = receiveOnePing(sending_socket, destinationAddress, ID, timeout, datasent, TTL) # 3. Call receiveOnePing function
		
			timedelay = timerecieved - timesent
			sending_socket.close()# 4. Close ICMP socket
			if (timedelay >0):
				timedelay = timedelay * 1000 # Converts into miliseconds
				timedelay = float(round(timedelay, 0))
				print timedelay, "ms",    # 3. Print out the returned delay
				arr.append(timedelay)
				recieved = recieved + 1
				completed = completed + 1
			else:
				lost = lost + 1
				print "  *   ", 
		if completed > 0:
			print " ", addressname, "(", received_DestinationAddress, ")"
		else:
			print "   Request timed out"
		sequence = sequence + 1
		maxhops = maxhops - 1
		TTL = TTL + 1
	return arr, TTL, recieved, lost  # 5. Return total network delay

def ping(host, timeout=0.2, maxhops = 30):	#Both time out and number of ping times optional arguments
	try:
		IPV4 = gethostbyname(host) # 1. Look up hostname, resolving it to an IP address, if it fails and cant find host print out error	
	except gaierror:
		print "Ping request could not find host (", host, ")"
		return
	print "Tracing", host , "(", IPV4, ")"
	arr, TTL,recieved,lost = doOnePing(IPV4, timeout,maxhops)
	
	aveagedelay = sum(arr) / len(arr)	#Total sum of all numbers in the list and divide by the amount of them
	aveagedelay = float(round(aveagedelay, 0))
	maximumdelay = max(arr)	#Finds the max number in the list
	minumumdelay = min(arr)	#Finds the min number in the lists
	if (recieved == 0):
		percentage = 100
	else:
		percentage = (float(lost)/float(((TTL-1)*3)))*100 #Gets percentage of lost
		percentage = float(round(percentage, 0))
	print "\nTraceroute stats for", host , "(", IPV4, ")" #Prints everything out
	print "    Packets: Sent =", (TTL-1)*3, ",  Received =", recieved, ",  Lost =", abs(lost), "(", percentage, "%)"
	print "Approximate times:"
	print "    Maximum delay: ", maximumdelay, "ms ,", " Minimum delay: ", minumumdelay, "ms ,", " Average delay: ", aveagedelay, "ms"
	
	
hostname = raw_input("Please enter a destination address: ")	#Host name
timeout = raw_input("Please enter the timeout time: ")	#Timeout time
maxhops = raw_input("Please enter the maximum hops: ")	#max num of hops
detect = 0
try:
   val = int(timeout)	#Checks to see if max hops is a number, then chhecks the timeout as well
except ValueError:
   ping(hostname)
   detect = 1
try:
   val = int(maxhops)
except ValueError:
   ping(hostname)
   detect = 1
if detect == 0:
	ping(hostname, int(timeout), int(maxhops))
