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


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout, datasent):
	timeLeft = timeout
	test=0
	while True:
		starttimer = time.time()
		Ready = select.select([icmpSocket], [], [], timeLeft)	# 1. Wait for the socket to receive a reply Says wait until ready for reading has timout
		timer = (time.time() - starttimer)
		
		if Ready[0] == []: # Timeout 	If not ready for reading then timeout
			print "Destination Network Unreachable"
			return 0
		
		timeReceived = time.time() # 2. Once received, record time of receipt, otherwise, handle a timeout
		received_Packet, received_DestinationAddress = icmpSocket.recvfrom(1024)
		header = received_Packet[20:28]
		received_Type, received_Code, received_Checksum, received_ID, received_Sequence = struct.unpack("bbHHh", header)	# 4. Unpack the packet header for useful information, including the ID
		if received_Type != 8 and received_ID == ID:	# 5. Check that the ID matches between the request and reply
			datalength = len(datasent)
			data = received_Packet[28:datalength]
			return timeReceived	# 6. Return total network delay
		elif received_Type == 3: # Checks for icmp error codes
			if received_Code == 0:
				print "Net Unreachable"
				return 0
			if received_Code == 1:
				print "Host Unreachable"
				return 0
			if received_Code == 2:
				print "Protocol Unreachable"
				return 0
			if received_Code == 3:
				print "Port Unreachable"
				return 0
			if received_Code == 6:
				print "Destination Network Unknown"
				return 0
			if received_Code == 7:
				print "Destination Host Unknown"
				return 0
		elif received_Type == 11:
			print "TTL"
			return 0
		
		timeLeft = timeLeft - timer #Catches timeout
		if timeLeft <= 0:
			return 0

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

def doOnePing(destinationAddress, timeout,sequence): 
	protocol = getprotobyname("icmp")   #Gets the protocol code
	
	icmpSocket = socket(AF_INET, SOCK_RAW, protocol)    # 1. Create ICMP socket
	ID = os.getpid()   # creates a unique ID based on the process ID
	
	
	
	timesent, datasent = sendOnePing(icmpSocket, destinationAddress, ID, sequence) # 2. Call sendOnePing function
	timerecieved = receiveOnePing(icmpSocket, destinationAddress, ID, timeout, datasent) # 3. Call receiveOnePing function
	
	timedelay = float(timerecieved) - float(timesent)
	icmpSocket.close()# 4. Close ICMP socket
	
	return timedelay # 5. Return total network delay

def ping(host, timeout=1, numpingtimes = 3):	#Both time out and number of ping times optional arguments
	arr = []
	recieved = 0
	try:
		IPV4 = gethostbyname(host) # 1. Look up hostname, resolving it to an IP address, if it fails and cant find host print out error	
	except gaierror:
		print "Ping request could not find host (", host, ")" 
		return
	print "Pinging", host , "(", IPV4, ")"
	for x in range(0, numpingtimes):    # 4. Continue this process until stopped   
		timedelay = doOnePing(IPV4, timeout, x) # 2. Call doOnePing function, approximately every second
		timedelay = timedelay * 1000 # Converts into miliseconds
		timedelay = float(round(timedelay, 0)) #Round down to 0 decimal places
		if (timedelay >=0):
			print "Reply from:",IPV4," ICMP Sequence:", x ," Time delay:",timedelay, "ms"    # 3. Print out the returned delay
			arr.append(timedelay)
			recieved = recieved + 1
		else:
			print "Ping request timed out\n"   #Print out rquest timed out if it didnt recieive anything
			arr.append(0)
	aveagedelay = sum(arr) / len(arr)	#Total sum of all numbers in the list and divide by the amount of them
	aveagedelay = float(round(aveagedelay, 0))
	maximumdelay = max(arr)	#Finds the max number in the list
	minumumdelay = min(arr)	#Finds the min number in the lists
	if (recieved == 0):
		percentage = 100
	else:
		percentage = (numpingtimes/recieved)*100
		percentage = percentage - 100 #Finds the percentage of pakets that were lost
	lost = recieved - numpingtimes #Prints out all information 
	print "\nPing stats for", host , "(", IPV4, ")"
	print "    Packets: Sent =", numpingtimes, ",  Received =", recieved, ",  Lost =", abs(lost), "(", percentage, "%)"
	print "Approximate times:"
	print "    Maximum delay: ", maximumdelay, "ms ,", " Minimum delay: ", minumumdelay, "ms ,", " Average delay: ", aveagedelay, "ms"
	
	
hostname = raw_input("Please enter a destination address: ")	#Host name
numpingtimes = raw_input("Please enter the number of times you want to ping: ") #Number of times to ping
timeout = raw_input("Please enter the timeout time: ")	#Timeout time
detect = 0
try:
   val = int(numpingtimes) #Checks to see if num ping times is a number, then chhecks the timeout as well
except ValueError:
   ping(hostname)
   detect = 1
try:
   val = int(timeout)
except ValueError:
   ping(hostname)
   detect = 1
if detect == 0:
	ping(hostname, int(timeout), int(numpingtimes))
