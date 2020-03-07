#main script for Lab5

#!/usr/bin/env python

import sdn_lab5_dhcp
import sdn_lab5_underlay
import sdn_lab5_topology
from netmiko import ConnectHandler
import re
from flask import Flask,render_template
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as p
import io
import base64

mininet={
'device_type':'linux',
'username':'mininet',
'password':'mininet',
'ip':'192.168.100.2',
}

#flask application
app=Flask(__name__)
global values,net_connect3
values=[]
x=[0]

net_connect3=ConnectHandler(**mininet)

#function to display the live graph abount the count of Packet_IN messages
@app.route('/')
def index():
    c=len(values)
    a=net_connect3.send_command("echo mininet | sudo -S ovs-ofctl dump-flows s1 --protocols=OpenFlow13 | grep 'priority=0 actions=CONTROLLER:65535'")
    
    #counting the number of packets
    reg1=r'(?m)(?<=\bn_packets=)\d+'
    find1=re.findall(reg1,a)
    if len(values)>0:
        s=sum(values)
        n=int(find1[0])-s
        x.append(c*5)
    else:
        n=int(find1[0])
    values.append(n)
    c+=1
    
    #plotting the graph    
    p.plot(x,values)
    p.xlabel("Time (seconds)")
    p.ylabel("Number of Packet_IN")
    p.title("Monitoring OpenFlow Channel")

    #passing the graph to flask page
    g=[]
    img=io.BytesIO()
    p.savefig(img,format='png')
    img.seek(0)
    url=base64.b64encode(img.getvalue()).decode()
    p.close()
    g.append('data:image/png;base64,{}'.format(url))
    
    return render_template('sdn_lab5_graph.html',z=g[0])

if __name__=="__main__":
    
    #getting IP address assigned to Mininet VM
    print("----------Getting IP address assigned to Mininet + OFM VM----------")
    ip=SDN_Lab5_DHCP.dhcp_bindings()
    print("IP address assigned to Mininet + OFM VM is: {}".format(ip))
    
    #configuring the underlay network for required connectivity
    print("----------Configuring Underlay network----------")
    SDN_Lab5_Underlay.underlay()
    print("----------Underlay network is fully configured----------")
    
    #spinning the mininet topology
    print("----------Starting topology----------")
    flag=SDN_Lab5_Topology.topology(ip)
    
    #monitoring the count for Packet_IN messages
    if flag==1:
        print("The OpenFlow connection between OVS and controller is established.")
        print("Starting the monitoring of Packet_IN messages")
        app.run(host='0.0.0.0',port=80)

    else:
        print("The OpenFlow connection between OVS and controller is not established.")