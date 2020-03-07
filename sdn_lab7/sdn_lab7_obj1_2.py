#script to detect an attack on the controller and mitigate it by aading iptable rules

#!/usr/bin/env python

import os
import sys
import re
import subprocess
import threading

#function to capture packets between controller and Mininet VM
def capture():
	print("Captring packets")
	command = "tshark -i enp0s8 -d tcp.port==6653,openflow -O openflow_v4 -Y openflow_v4.type==10 >> packets.xml"
	z=os.system(command)

#function to detect the attack and add iptable rules to stop the attack
def detect():
	while 1:
		src = []
		port = []
		src_port = {}
		final = []

		with open('packets.xml') as f:
			lines = f.read()

			#counting the packets coming to the controller
			a = re.findall('Src: (?:\d{1,3}\.){3}\d{1,3}, Dst: 192.168.10.22\nTransmission Control Protocol, Src Port: 9999',lines)
			for i in a:
				temp1=i.split(",")[0]
				temp2=i.split(",")[2]
				src=temp1.split(":")[1]
				port=temp2.split(":")[1]
				src_port=str([src.split(" ")[1]]) +","+ str(port.split(" ")[1])
				final.append(src_port)

			d={}
			for i in final:
				d[i]=final.count(i)

			#if the packet count is above certain threshold then adding iptable rules for that source address
			v = d.values()
			for i in v:
				if i > 50:
					print("Attack on Controller detected from 192.168.10.21 with source port of 9999. Adding iptables rules to prevent it.")
					x1 = subprocess.call(["sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport=6653", "-d","192.168.10.22","-s","192.168.10.21", "--sport=9999", "-j", "DROP"])
					sys.exit(0)

if __name__ =="__main__":
	
	#starting the packet capture thread
    t1=threading.Thread(target=capture)
    t1.start()
    
    #starting the attack detection thread
    t2=threading.Thread(target=detect)
    t2.start()