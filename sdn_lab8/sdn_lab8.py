#script for the Push of a button routing application in an SDN network

#!/usr/bin/env python

from flask import Flask,request,render_template
import requests
from netmiko import ConnectHandler
import time
import re

global path
path={"upper":"1 6 7 5",
      "middle":"1 2 3 4 5",
      "bottom":"1 8 5"
      }

#flask application
app=Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
def index():
    #index page
    return render_template('sdn_lab8_index.html')

@app.route('/default_topo', methods = ['GET', 'POST'])
def default_topo():
    
    mininet={
    'device_type':'linux',
    'username':'mininet',
    'password':'mininet',
    'ip':"192.168.10.21",
    }

    net_connect1=ConnectHandler(**mininet)
    
    net_connect1.send_command("echo mininet | sudo -S mn -c")

    #spinning the custom topology
    net_connect1.write_channel("sudo mn --custom sdn_lab8_normal.py --topo=mytopo --controller=remote,ip=192.168.10.22,port=6653 --mac\n")
    time.sleep(1)
    output2 = net_connect1.read_channel()
    if "word" in output2:
        net_connect1.write_channel("mininet\n")
        time.sleep(1)
    
    #configuring IP address on s1 and s5
    url_s1 = 'http://192.168.10.22:8080/router/0000000000000001'
    data_s1 = '{"address":"10.0.0.2/24"}'
    
    url_s5 = 'http://192.168.10.22:8080/router/0000000000000005'
    data_s5 = '{"address":"1.1.1.2/24"}'
    
    r_s1 = requests.post(url = url_s1, data = data_s1)
    r_s5 = requests.post(url = url_s5, data = data_s5)
    
    var_file = {6:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                7:{"1.1.1.0/24":1, "10.0.0.0/24":2},
                1:{"1.1.1.0/24":3},
                5:{"10.0.0.0/24":4}
                }
    
    url_flow_add = "http://192.168.10.22:8080/stats/flowentry/add"

    #adding required flows on other switches
    cookie = 10
    for i in var_file:
        for j in var_file[i]:
            data_flow = '{"dpid":'+str(i)+', "cookie":'+str(cookie)+', "table_id":0, "priority":1000, "match": { "dl_type":0x800, "nw_dst":"'+str(j)+'", }, "actions":[{"type":"OUTPUT", "port":'+str(var_file[i][j])+', }]}'
            r_flow = requests.post(url = url_flow_add, data= data_flow)
            cookie+=1
    
    #performing the traceroute for ICMP traffic
    f1 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value1= int(f1.split(',')[3].split('=')[1])
    
    p1 = net_connect1.send_command("Host ping Server -c 4")    

    f2 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value2= int(f2.split(',')[3].split('=')[1])
    
    if value2>value1:
        icmp_path="ICMP traffic is going via {}".format(path["upper"])
    else:
        icmp_path="ICMP traffic is going via either {} or {} path.".format(path["middle"],path["bottom"])
        
    f3 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value3= int(f3.split(',')[3].split('=')[1])
    
    #performing the traceroute for HTTP traffic
    http_run = net_connect1.send_command("Server python -m SimpleHTTPServer 80 &")
    
    http_test = net_connect1.send_command("Host wget -O - Server")
   
    f4= net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value4= int(f4.split(',')[3].split('=')[1])

    if value4>value3:
        http_path="HTTP traffic is going via {}".format(path["upper"])
    else:
        http_path="HTTP traffic is going via either {} or {} path.".format(path["middle"],path["bottom"])
        
    return render_template('sdn_lab8_default.html',icmp_path=icmp_path, http_path=http_path)
    
@app.route('/shortest_topo', methods = ['GET', 'POST'])
def shortest_topo():
    
    mininet={
    'device_type':'linux',
    'username':'mininet',
    'password':'mininet',
    'ip':"192.168.10.21",
    }

    net_connect1=ConnectHandler(**mininet)

    net_connect1.send_command("echo mininet | sudo -S mn -c")

    #spinning the custom topology
    net_connect1.write_channel("sudo mn --custom sdn_lab8_normal.py --topo=mytopo --controller=remote,ip=192.168.10.22,port=6653 --mac\n")
    time.sleep(1)
    output2 = net_connect1.read_channel()
    if "word" in output2:
        net_connect1.write_channel("mininet\n")
        time.sleep(1)    

    url_s1 = 'http://192.168.10.22:8080/router/0000000000000001'
    data_s1 = '{"address":"10.0.0.2/24"}'
    
    url_s5 = 'http://192.168.10.22:8080/router/0000000000000005'
    data_s5 = '{"address":"1.1.1.2/24"}'
    
    r_s1 = requests.post(url = url_s1, data = data_s1)
    r_s5 = requests.post(url = url_s5, data = data_s5)

    url_flow_add = "http://192.168.10.22:8080/stats/flowentry/add"
    
    var_file1 = {6:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                7:{"1.1.1.0/24":1, "10.0.0.0/24":2},
                1:{"1.1.1.0/24":3},
                5:{"10.0.0.0/24":4}
                }
    
    var_file2 = {8:{"1.1.1.0/24":2, "10.0.0.0/24":1}}

    cookie = 30
    
    #adding required flows on other switches
    for i in var_file1:
        for j in var_file1[i]:
            data_flow = '{"dpid":'+str(i)+', "cookie":'+str(cookie)+', "table_id":0, "priority":1000, "match": { "dl_type":0x800, "nw_dst":"'+str(j)+'", }, "actions":[{"type":"OUTPUT", "port":'+str(var_file1[i][j])+', }]}'
            r_flow = requests.post(url = url_flow_add, data= data_flow)
            cookie+=1
    
    for i in var_file2:
        for j in var_file2[i]:
            data_flow = '{"dpid":'+str(i)+', "cookie":'+str(cookie)+', "table_id":0, "priority":2000, "match": { "dl_type":0x800, "nw_dst":"'+str(j)+'", }, "actions":[{"type":"OUTPUT", "port":'+str(var_file2[i][j])+', }]}'
            r_flow = requests.post(url = url_flow_add, data= data_flow)
            cookie+=1
 
    #adding high priority flows for HTTP traffic
    data_flow_s1_1='{"dpid":1, "cookie":'+str(cookie)+', "table_id":0, "priority":2000, "match": { "dl_type":0x800, "nw_proto":6, "tp_dst":80, }, "actions":[{"type":"OUTPUT", "port":4, }]}'
    cookie+=1
    data_flow_s5_1='{"dpid":5, "cookie":'+str(cookie)+', "table_id":0, "priority":2000, "match": { "dl_type":0x800, "nw_proto":6, "tp_src":80, }, "actions":[{"type":"OUTPUT", "port":3, }]}'
    cookie+=1
    
    r_flow_s1_1 = requests.post(url = url_flow_add, data= data_flow_s1_1)
    r_flow_s5_1 = requests.post(url = url_flow_add, data= data_flow_s5_1)
    
    #performing the traceroute for ICMP traffic
    f1 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value1= int(f1.split(',')[3].split('=')[1])
    
    p1 = net_connect1.send_command("Host ping Server -c 4")    

    f2 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value2= int(f2.split(',')[3].split('=')[1])
    
    if value2>value1:
        icmp_path="ICMP traffic is going via {}".format(path["upper"])
    else:
        icmp_path="It is either {} or {} path.".format(path["middle"],path["bottom"])
    
    f3 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:4")
    value3= int(f3.split(',')[3].split('=')[1])
    
    #performing the traceroute for HTTP traffic
    http_run = net_connect1.send_command("Server python -m SimpleHTTPServer 80 &")
    
    http_test = net_connect1.send_command("Host wget -O - Server")
   
    f4= net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:4")
    value4= int(f4.split(',')[3].split('=')[1])

    if value4>value3:
        http_path="HTTP traffic is going via {}".format(path["bottom"])
    else:
        http_path="HTTP traffic is going via either {} or {} path.".format(path["upper"], path["middle"])

    return render_template('sdn_lab8_shortest.html',icmp_path=icmp_path, http_path=http_path)

@app.route('/longest_topo', methods = ['GET', 'POST'])
def longest_topo():
    mininet={
    'device_type':'linux',
    'username':'mininet',
    'password':'mininet',
    'ip':"192.168.10.21",
    }

    net_connect1=ConnectHandler(**mininet)

    net_connect1.send_command("echo mininet | sudo -S mn -c")
    
    #spinning the custom topology
    net_connect1.write_channel("sudo mn --custom sdn_lab8_normal.py --topo=mytopo --controller=remote,ip=192.168.10.22,port=6653 --mac\n")
    time.sleep(1)
    output2 = net_connect1.read_channel()
    if "word" in output2:
        net_connect1.write_channel("mininet\n")
        time.sleep(1)    

    url_s1 = 'http://192.168.10.22:8080/router/0000000000000001'
    data_s1 = '{"address":"10.0.0.2/24"}'
    
    url_s5 = 'http://192.168.10.22:8080/router/0000000000000005'
    data_s5 = '{"address":"1.1.1.2/24"}'
    
    r_s1 = requests.post(url = url_s1, data = data_s1)
    r_s5 = requests.post(url = url_s5, data = data_s5)
    
    url_flow_add = "http://192.168.10.22:8080/stats/flowentry/add"
    
    var_file1 = {6:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                7:{"1.1.1.0/24":1, "10.0.0.0/24":2},
                1:{"1.1.1.0/24":3},
                5:{"10.0.0.0/24":4}
                }
    
    var_file2 = {2:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                 3:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                 4:{"1.1.1.0/24":2, "10.0.0.0/24":1}
                 }

    cookie = 40
    
    #adding required flows on other switches
    for i in var_file1:
        for j in var_file1[i]:
            data_flow = '{"dpid":'+str(i)+', "cookie":'+str(cookie)+', "table_id":0, "priority":1000, "match": { "dl_type":0x800, "nw_dst":"'+str(j)+'", }, "actions":[{"type":"OUTPUT", "port":'+str(var_file1[i][j])+', }]}'
            r_flow = requests.post(url = url_flow_add, data= data_flow)
            cookie+=1
    
    
    for i in var_file2:
        for j in var_file2[i]:
            data_flow = '{"dpid":'+str(i)+', "cookie":'+str(cookie)+', "table_id":0, "priority":3000, "match": { "dl_type":0x800, "nw_dst":"'+str(j)+'", }, "actions":[{"type":"OUTPUT", "port":'+str(var_file2[i][j])+', }]}'
            r_flow = requests.post(url = url_flow_add, data= data_flow)
            cookie+=1
    
    #adding high priority flows for HTTP traffic
    data_flow_s1_1='{"dpid":1, "cookie":'+str(cookie)+', "table_id":0, "priority":3000, "match": { "dl_type":0x800, "nw_proto":6, "tp_dst":80, }, "actions":[{"type":"OUTPUT", "port":2, }]}'
    cookie+=1
    data_flow_s5_1='{"dpid":5, "cookie":'+str(cookie)+', "table_id":0, "priority":3000, "match": { "dl_type":0x800, "nw_proto":6, "tp_src":80, }, "actions":[{"type":"OUTPUT", "port":1, }]}'
    cookie+=1
    
    r_flow_s1_1 = requests.post(url = url_flow_add, data= data_flow_s1_1)
    r_flow_s5_1 = requests.post(url = url_flow_add, data= data_flow_s5_1)
    
    #performing the traceroute for ICMP traffic
    f1 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value1= int(f1.split(',')[3].split('=')[1])
    
    p1 = net_connect1.send_command("Host ping Server -c 4")    

    f2 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value2= int(f2.split(',')[3].split('=')[1])
    
    if value2>value1:
        icmp_path="ICMP traffic is going via {}".format(path["upper"])
    else:
        icmp_path="ICMP traffic is going via either {} or {} path.".format(path["middle"],path["bottom"])
    
    f3 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:2")
    value3= int(f3.split(',')[3].split('=')[1])

    #performing the traceroute for HTTP traffic
    http_run = net_connect1.send_command("Server python -m SimpleHTTPServer 80 &")
    
    http_test = net_connect1.send_command("Host wget -O - Server")
   
    f4= net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:2")
    value4= int(f4.split(',')[3].split('=')[1])

    if value4>value3:
        http_path="HTTP traffic is going via {}".format(path["middle"])
    else:
        http_path="HTTP traffic is going via either {} or {} path.".format(path["upper"],path["bottom"])

    return render_template('sdn_lab8_longest.html',icmp_path=icmp_path, http_path=http_path)
    
@app.route('/latency_topo', methods = ['GET', 'POST'])
def latency_topo():
    
    mininet={
    'device_type':'linux',
    'username':'mininet',
    'password':'mininet',
    'ip':"192.168.10.21",
    }

    net_connect1=ConnectHandler(**mininet)

    net_connect1.send_command("echo mininet | sudo -S mn -c")
    
    #spinning the custom topology
    net_connect1.write_channel("sudo mn --custom sdn_lab8_delay.py --topo=mytopo --controller=remote,ip=192.168.10.22,port=6653 --mac\n")
    time.sleep(1)
    output2 = net_connect1.read_channel()
    if "word" in output2:
        net_connect1.write_channel("mininet\n")
        time.sleep(1)    
    
    url_flow_add = "http://192.168.10.22:8080/stats/flowentry/add"
    url_flow_del = "http://192.168.10.22:8080/stats/flowentry/delete_strict"

    url_s1 = 'http://192.168.10.22:8080/router/0000000000000001'
    data_s1 = '{"address":"10.0.0.2/24"}'
    
    url_s5 = 'http://192.168.10.22:8080/router/0000000000000005'
    data_s5 = '{"address":"1.1.1.2/24"}'
    
    r_s1 = requests.post(url = url_s1, data = data_s1)
    r_s5 = requests.post(url = url_s5, data = data_s5)
 
    var_file1 = {6:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                7:{"1.1.1.0/24":1, "10.0.0.0/24":2},
                2:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                3:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                4:{"1.1.1.0/24":2, "10.0.0.0/24":1},
                8:{"1.1.1.0/24":2, "10.0.0.0/24":1}
                }

    cookie = 40
    
    #adding required flows on other switches
    for i in var_file1:
        for j in var_file1[i]:
            data_flow = '{"dpid":'+str(i)+', "cookie":'+str(cookie)+', "table_id":0, "priority":1000, "match": { "dl_type":0x800, "nw_dst":"'+str(j)+'", }, "actions":[{"type":"OUTPUT", "port":'+str(var_file1[i][j])+', }]}'
            r_flow = requests.post(url = url_flow_add, data= data_flow)
            cookie+=1
    
    latency={}
    
    #adding flows to measure the latency of top path
    s1_top = '{"dpid":1, "cookie":50, "table_id":0, "priority":1000, "match": { "dl_type":0x800, "nw_dst":"1.1.1.0/24", }, "actions":[{"type":"OUTPUT", "port":3, }]}'
    s5_top = '{"dpid":5, "cookie":50, "table_id":0, "priority":1000, "match": { "dl_type":0x800, "nw_dst":"10.0.0.0/24", }, "actions":[{"type":"OUTPUT", "port":4, }]}'

    r_flow = requests.post(url = url_flow_add, data= s1_top)
    r_flow = requests.post(url = url_flow_add, data= s5_top)

    p1 = net_connect1.send_command("Host ping Server -c 4")    
    reg=r'\/\d+\.?\d+'
    find=re.findall(reg,p1)
    latency['up']=float(find[0][1:])
    
    #deleting flows from top path
    r_flow = requests.post(url = url_flow_del, data= s1_top)
    r_flow = requests.post(url = url_flow_del, data= s5_top)
    
    #adding flows to measure the latency of middle path  
    s1_middle = '{"dpid":1, "cookie":50, "table_id":0, "priority":2000, "match": { "dl_type":0x800, "nw_dst":"1.1.1.0/24", }, "actions":[{"type":"OUTPUT", "port":2, }]}'
    s5_middle = '{"dpid":5, "cookie":50, "table_id":0, "priority":2000, "match": { "dl_type":0x800, "nw_dst":"10.0.0.0/24", }, "actions":[{"type":"OUTPUT", "port":1, }]}'
    
    r_flow = requests.post(url = url_flow_add, data= s1_middle)
    r_flow = requests.post(url = url_flow_add, data= s5_middle)
    
    p2 = net_connect1.send_command("Host ping Server -c 4")    
    reg=r'\/\d+\.?\d+'
    find=re.findall(reg,p2)
    latency['middle']=float(find[0][1:])
    
    #deleting flows from middle path
    r_flow = requests.post(url = url_flow_del, data= s1_middle)
    r_flow = requests.post(url = url_flow_del, data= s5_middle)
    
    #adding flows to measure the latency of bottom path
    s1_bottom = '{"dpid":1, "cookie":50, "table_id":0, "priority":3000, "match": { "dl_type":0x800, "nw_dst":"1.1.1.0/24", }, "actions":[{"type":"OUTPUT", "port":4, }]}'
    s5_bottom = '{"dpid":5, "cookie":50, "table_id":0, "priority":3000, "match": { "dl_type":0x800, "nw_dst":"10.0.0.0/24", }, "actions":[{"type":"OUTPUT", "port":3, }]}'
    
    r_flow = requests.post(url = url_flow_add, data= s1_bottom)
    r_flow = requests.post(url = url_flow_add, data= s5_bottom)
    
    p3 = net_connect1.send_command("Host ping Server -c 4")    
    reg=r'\/\d+\.?\d+'
    find=re.findall(reg,p3)
    latency['bottom']=float(find[0][1:])

    #deleting flows from bottom path
    r_flow = requests.post(url = url_flow_del, data= s1_bottom)
    r_flow = requests.post(url = url_flow_del, data= s5_bottom)

    #finding the lowest latency path
    key_min = min(latency.keys(), key=(lambda k: latency[k]))
    http_path="HTTP traffic is going via {}".format(path[key_min])

    #adding flows for the lowest latency path
    s1_http_middle='{"dpid":1, "cookie":60, "table_id":0, "priority":3000, "match": { "dl_type":0x800, "nw_proto":6, "tp_dst":80, }, "actions":[{"type":"OUTPUT", "port":2, }]}'
    s5_http_middle='{"dpid":5, "cookie":61, "table_id":0, "priority":3000, "match": { "dl_type":0x800, "nw_proto":6, "tp_src":80, }, "actions":[{"type":"OUTPUT", "port":1, }]}'

    r_flow = requests.post(url = url_flow_add, data= s1_http_middle)
    r_flow = requests.post(url = url_flow_add, data= s5_http_middle)
    r_flow = requests.post(url = url_flow_add, data= s1_top)
    r_flow = requests.post(url = url_flow_add, data= s5_top)

    #testing the end-to-end connectivity for ICMP traffic
    print("Look at the flow-dumps & n_packets on switches to test the ICMP traffic")
    time.sleep(30)
    p_test = net_connect1.send_command("Host ping Server -c 4")
    print(p_test)
    
    #testing the end-to-end connectivity for HTTP traffic
    http_run = net_connect1.send_command("Server python -m SimpleHTTPServer 80 &")

    print("Look at the flow-dumps & n_packets on switches to test the HTTP traffic")
    time.sleep(30)
    http_test = net_connect1.send_command("Host wget -O - Server")
    print(http_test)
    
    #performing the traceroute for ICMP traffic
    f1 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value1= int(f1.split(',')[3].split('=')[1])
    
    p1 = net_connect1.send_command("Host ping Server -c 4")    

    f2 = net_connect1.send_command("sh ovs-ofctl dump-flows -O OpenFlow13 OvS1 | grep actions=output:3")
    value2= int(f2.split(',')[3].split('=')[1])
    
    if value2>value1:
        icmp_path="ICMP traffic is going via {}".format(path["upper"])
    else:
        icmp_path="ICMP traffic is going via either {} or {} path.".format(path["middle"],path["bottom"])

    return render_template('sdn_lab8_latency.html',icmp_path=icmp_path, http_path=http_path)

#running the flask application
if __name__=='__main__':
    
    app.debug = True
    app.run(host='0.0.0.0',port=9000)