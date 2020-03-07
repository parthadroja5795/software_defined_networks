#getting IP address assigned to Mininet VM

#!/usr/bin/env python

from netmiko import ConnectHandler
import re

def dhcp_bindings():
    
    ios_r1={
    'device_type':'cisco_ios',
    'username':'sdn',
    'password':'sdn',
    'ip':'192.168.100.1',
    }

    net_connect1=ConnectHandler(**ios_r1)
    output1=net_connect1.send_command("sh ip dhcp binding")
    
    reg=r'192.168.100.\d+'
    match1=re.findall(reg,output1)
    net_connect1.disconnect()
    return match1[0]