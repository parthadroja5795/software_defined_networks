#configuring the underlay network for required connectivity

#!/usr/bin/env python

from netmiko import ConnectHandler
import time

def underlay():
    ios_r1={
    'device_type':'cisco_ios',
    'username':'sdn',
    'password':'sdn',
    'ip':'192.168.100.1',
    }
    
    ios_r2={
    'device_type':'cisco_ios',
    'username':'sdn',
    'password':'sdn',
    'ip':'192.168.200.2',
    }
    
    ios_r3={
    'device_type':'cisco_ios',
    'username':'sdn',
    'password':'sdn',
    'ip':'172.16.100.1',
    }
    
    net_connect1=ConnectHandler(**ios_r1)

    print("----------Adding routes to R1----------")

    net_connect1.send_config_set(["ip route 172.16.100.0 255.255.255.0 192.168.200.2"])
    print("ip route 172.16.100.0 255.255.255.0 192.168.200.2")
    
    net_connect1.send_config_set(["ip route 10.20.30.0 255.255.255.0 192.168.200.2"])
    print("ip route 10.20.30.0 255.255.255.0 192.168.200.2")

    print("----------Routes added to R1----------")

    print("----------Adding routes to R2----------")
    
    net_connect1.write_channel("ssh -l sdn 192.168.200.2\n")
    time.sleep(1)
    output2 = net_connect1.read_channel()
    if "word" in output2:
        net_connect1.write_channel(net_connect1.password + '\n')
    time.sleep(1)
    output2 += net_connect1.read_channel()
    
    net_connect1.write_channel("conf t\n")
    time.sleep(1)
    
    net_connect1.write_channel("ip route 192.168.100.0 255.255.255.0 192.168.200.1\n")
    print("ip route 192.168.100.0 255.255.255.0 192.168.200.1")
    
    net_connect1.write_channel("ip route 10.20.30.0 255.255.255.0 172.16.100.1\n")
    print("ip route 10.20.30.0 255.255.255.0 172.16.100.1")
    
    time.sleep(1)    
    net_connect1.write_channel("exit\n")

    print("----------Routes added to R2----------")

    print("----------Adding routes to R4----------")
    
    net_connect1.write_channel("ssh -l sdn 172.16.100.1\n")
    time.sleep(1)
    output2 = net_connect1.read_channel()
    if "word" in output2:
        net_connect1.write_channel(net_connect1.password + '\n')
    time.sleep(1)
    
    net_connect1.write_channel("conf t\n")
    time.sleep(1)
    
    net_connect1.write_channel("ip route 192.168.100.0 255.255.255.0 172.16.100.2\n")
    print("ip route 192.168.100.0 255.255.255.0 172.16.100.2")
    
    net_connect1.write_channel("ip route 192.168.200.0 255.255.255.0 172.16.100.2\n")
    print("ip route 192.168.200.0 255.255.255.0 172.16.100.2")
    
    time.sleep(1)
    
    print("----------Routes added to R4----------")

    net_connect1.disconnect()