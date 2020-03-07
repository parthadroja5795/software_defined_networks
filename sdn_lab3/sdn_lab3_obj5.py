#script to detect any OvS connection to the controller in real-time and store the switch information in a file

#!/usr/bin/env python

import subprocess
import time
from scapy.all import *
from scapy.contrib.openflow3 import *
import re
import json
    
#function to capture packets between controller and mininet
def capture():
	x=subprocess.Popen(["echo sdn | sudo -S tcpdump -i enp0s8 -c 200 -w sdn_lab3_obj5.pcap"],stdout=subprocess.PIPE,shell=True)

	time.sleep(30)

#function to analyze the captured packets
def analysis():

	a=rdpcap("sdn_lab3_obj5.pcap")
	connections={}

	for i in range(0,len(a)):
		try:
			temp=a[i][TCP].payload
			o1=str(temp.show)

			#analyzing only FEATURE_REPLY message
			if "FEATURES_REPLY" in o1:
				switch={}

				ip=a[i][IP].src
				reg1=r'(?m)(?<=\bdatapath_id=).\w*'
				match1=re.findall(reg1,o1)
				dpid=match1[0]
				print("Connection from switch with DPID {} detected.".format(dpid))
				
				#storing required information about the switch
				switch["ip_address"]=ip
				switch["status"]="Connected"
				connections[dpid]=switch
		except:
			pass

	#storing the switch information in the file
	filename="connected.txt"
	
	f=open(filename,"r")
	connections_old=json.load(f)
	f.close()

	for i in connections_old:
		connections[i]=connections_old[i] 
	
	f=open(filename,"w")
	json.dump(connections,f)

	print("Connections information has been saved in {} file.".format(filename))

if __name__=="__main__":
	
	#running the capture and analysis application
	while 1:
		print("The switch detection application is now running.")
		capture()
		analysis()