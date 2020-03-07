#spinning the mininet topology

#!/usr/bin/env python

from netmiko import ConnectHandler
import time
import re

def topology(ip):
    
    mininet={
    'device_type':'linux',
    'username':'mininet',
    'password':'mininet',
    'ip':ip,
    }
    
    net_connect2=ConnectHandler(**mininet)
    
    #updating the default route on the Mininet VM
    net_connect2.write_channel("echo mininet | sudo -S ip route del 0.0.0.0/0\n")
    time.sleep(1)
    net_connect2.write_channel("echo mininet | sudo -S ip route add 0.0.0.0/0 dev eth0\n")
    time.sleep(1)
    
    #spinning the default mininet topology
    net_connect2.write_channel("sudo mn\n")
    time.sleep(1)
    output2 = net_connect2.read_channel()
    print(output2)
    if "word" in output2:
        net_connect2.write_channel("mininet\n")
        time.sleep(1)    
    
    #changing the OpenFlow version
    net_connect2.write_channel("sh ovs-vsctl set bridge s1 protocols=OpenFlow13\n")
    time.sleep(1)
    print("OpenFlow version changed to OpenFlow1.3")
    
    #setting the controller
    net_connect2.write_channel("sh ovs-vsctl set-controller s1 tcp:10.20.30.2:6653\n")
    time.sleep(10)
    print("Controller on OVS changed to Ryu (10.20.30.2:6653)")    
    
    z=net_connect2.send_command("sh ovs-vsctl show")
    
    reg1=r'(?m)(?<=\bis_connected: ).*$'
    find1=re.findall(reg1,z)
    
    #checking the connection to the controller
    if len(find1)>0 and find1[0]=="true":
        net_connect2.write_channel("pingall\n")
        flag=1
        return flag
        
    else:    
        flag=0
        return flag