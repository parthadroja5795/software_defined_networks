#DHCP and Self-Healing application for Ryu controller

#!/usr/bin/env python

import http.client as httpclient
import requests
import json
import time
import os
from netmiko import ConnectHandler

#function to add flows on the device
def add_flow(flowadd):
    flow = json.dumps(flowadd)
    restpath = "/stats/flowentry/add"
    head = {'Content-type': 'application/json', 'Accept': 'application/json', }
    connect = httpclient.HTTPConnection('10.20.30.55', 8080)
    connect.request("POST", restpath, flow, head)
    resp = connect.getresponse()
    reply = [resp.status, resp.reason, resp.read()]
    connect.close()
    return reply

#function to delete flow on the device
def del_flows(flowdel):
    flow = json.dumps(flowdel)
    restpath = "/stats/flowentry/delete_strict"
    head = {'Content-type': 'application/json', 'Accept': 'application/json', }
    connect = httpclient.HTTPConnection('10.20.30.55', 8080)
    connect.request("POST", restpath, flow, head)
    resp = connect.getresponse()
    reply = [resp.status, resp.reason, resp.read()]
    connect.close()
    return reply

#function to check connectivity to dell abmx and dell ovs
def connections(device1,device2):
    c1 = ConnectHandler(**device1)
    print("Connection to dell abmx successful!")
    c2 = ConnectHandler(**device2)
    print("Connection to dell OvS successful!")
    return c1,c2

if __name__ == "__main__":
    
    #specifying required flows for each device
    dhcp_fwd_abmx = { "dpid": 22095312424577, "cookie": 2, "table_id": 0, "priority": 2000, "match": { "in_port":4, "udp_dst": 67, "ip_proto": 17,"eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 3 }]}
    dhcp_rvs_abmx = { "dpid": 22095312424577, "cookie": 3, "table_id": 0, "priority": 2000, "match": { "in_port":3, "eth_type": 2048, "ip_proto": 17, "udp_dst": 68 }, "actions": [{ "type": "OUTPUT", "port": 4 }]}
    arp_fwd_abmx = { "dpid": 22095312424577, "cookie": 5, "table_id": 0, "priority": 1000, "match": { "in_port":4, "eth_type": 2054 }, "actions": [{ "type": "OUTPUT", "port": 3 }]}
    arp_rvs_abmx = { "dpid": 22095312424577, "cookie": 6, "table_id": 0, "priority": 1000, "match": { "in_port":3, "eth_type": 2054 }, "actions": [{ "type": "OUTPUT", "port": 4 }]}
    ip_fwd_abmx = { "dpid": 22095312424577, "cookie": 9, "table_id": 0, "priority": 1500, "match": { "in_port":4, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 3 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    ip_rvs_abmx = { "dpid": 22095312424577, "cookie": 10, "table_id": 0, "priority": 1500, "match": { "in_port":3, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 4 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    dns_fwd_abmx = { "dpid": 22095312424577, "cookie": 12, "table_id": 0, "priority": 3000, "match": { "in_port":4, "eth_type": 2048, "ip_proto": 17, "udp_dst": 53 }, "actions": [{ "type": "OUTPUT", "port": "CONTROLLER" }]}
    dns_rvs_abmx = { "dpid": 22095312424577, "cookie": 13, "table_id": 0, "priority": 3000, "match": { "in_port":"NORMAL", "eth_type": 2048,"ip_proto": 17, "udp_src" :53 }, "actions": [{ "type": "OUTPUT", "port": 4 }]}
    
    dhcp_fwd_dell = { "dpid": 22095312165766, "cookie": 2, "table_id": 0, "priority": 2000, "match": { "in_port":2, "eth_dst": "ff:ff:ff:ff:ff:ff", "udp_src": 68, "udp_dst": 67, "ip_proto": 17,"eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 1 }]}
    dhcp_rvs_dell = { "dpid": 22095312165766, "cookie": 3, "table_id": 0, "priority": 2000, "match": { "in_port":1, "eth_type": 2048, "ip_proto": 17, "udp_src": 67, "udp_dst": 68 }, "actions": [{ "type": "OUTPUT", "port": 2 }]}
    arp_fwd_dell = { "dpid": 22095312165766, "cookie": 5, "table_id": 0, "priority": 1000, "match": { "in_port":2, "eth_type": 2054 }, "actions": [{ "type": "OUTPUT", "port": 1 }]}
    arp_rvs_dell = { "dpid": 22095312165766, "cookie": 6, "table_id": 0, "priority": 1000, "match": { "in_port":1, "eth_type": 2054}, "actions": [{ "type": "OUTPUT", "port": 2 }]}
    ip_fwd_dell = { "dpid": 22095312165766, "cookie": 9, "table_id": 0, "priority": 1500, "match": { "in_port":2, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 1 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    ip_rvs_dell = { "dpid": 22095312165766, "cookie": 10, "table_id": 0, "priority": 1500, "match": { "in_port":1, "eth_type": 2048}, "actions": [{ "type": "OUTPUT", "port": 2 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    
    arista_fwd = { "dpid": 122194256519, "cookie": 2, "table_id": 0, "priority": 2000, "match": { "in_port":18 }, "actions": [{ "type": "OUTPUT", "port": 19 }]}
    arista_rvs = { "dpid": 122194256519, "cookie": 3, "table_id": 0, "priority": 2000, "match": { "in_port":19 }, "actions": [{ "type": "OUTPUT", "port": 18 }]}
    arista_fwd_trace = { "dpid": 122194256519, "cookie": 4, "table_id": 0, "priority": 3000, "match": { "in_port":18, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 19 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    arista_rvs_trace = { "dpid": 122194256519, "cookie": 5, "table_id": 0, "priority": 3000, "match": { "in_port":19, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 18 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    
    hpsw_fwd = { "dpid": 122196472497, "cookie": 2, "table_id": 0, "priority": 2000, "match": { "in_port":19 }, "actions": [{ "type": "OUTPUT", "port": 20 }]}
    hpsw_rvs = { "dpid": 122196472497, "cookie": 3, "table_id": 0, "priority": 2000, "match": { "in_port":20 }, "actions": [{ "type": "OUTPUT", "port": 19 }]}
    hpsw_fwd_trace = { "dpid": 122196472497, "cookie": 4, "table_id": 0, "priority": 3000, "match": { "in_port":19, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 20 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    hpsw_rvs_trace = { "dpid": 122196472497, "cookie": 5, "table_id": 0, "priority": 3000, "match": { "in_port":20, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 19 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    
    hpovs_fwd = { "dpid": 63464340112, "cookie": 2, "table_id": 0, "priority": 2000, "match": { "in_port": 3 }, "actions": [{ "type": "OUTPUT", "port": 1 }]}
    hpovs_rvs = { "dpid": 63464340112, "cookie": 3, "table_id": 0, "priority": 2000, "match": { "in_port": 1 }, "actions": [{ "type": "OUTPUT", "port": 3 }]}
    hpovs_fwd_trace = { "dpid": 63464340112, "cookie": 4, "table_id": 0, "priority": 3000, "match": { "in_port":3, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 1 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    hpovs_rvs_trace = { "dpid": 63464340112, "cookie": 5, "table_id": 0, "priority": 3000, "match": { "in_port":1, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 3 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    
    dhcp_fwd_abmx_up = { "dpid": 22095312424577, "cookie": 2, "table_id": 0, "priority": 2000, "match": { "in_port":4, "udp_dst": 67, "ip_proto": 17,"eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 2 }]}
    dhcp_rvs_abmx_up = { "dpid": 22095312424577, "cookie": 3, "table_id": 0, "priority": 2000, "match": { "in_port":2, "eth_type": 2048, "ip_proto": 17, "udp_dst": 68 }, "actions": [{ "type": "OUTPUT", "port": 4 }]}
    arp_fwd_abmx_up = { "dpid": 22095312424577, "cookie": 5, "table_id": 0, "priority": 1000, "match": { "in_port":4, "eth_type": 2054 }, "actions": [{ "type": "OUTPUT", "port": 2 }]}
    arp_rvs_abmx_up = { "dpid": 22095312424577, "cookie": 6, "table_id": 0, "priority": 1000, "match": { "in_port":2, "eth_type": 2054 }, "actions": [{ "type": "OUTPUT", "port": 4 }]}
    ip_fwd_abmx_up = { "dpid": 22095312424577, "cookie": 9, "table_id": 0, "priority": 1500, "match": { "in_port":4, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 2 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    ip_rvs_abmx_up = { "dpid": 22095312424577, "cookie": 10, "table_id": 0, "priority": 1500, "match": { "in_port":2, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 4 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    
    dhcp_fwd_dell_up = { "dpid": 22095312165766, "cookie": 2, "table_id": 0, "priority": 2000, "match": { "in_port":3, "eth_dst": "ff:ff:ff:ff:ff:ff", "udp_src": 68, "udp_dst": 67, "ip_proto": 17,"eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 1 }]}
    dhcp_rvs_dell_up = { "dpid": 22095312165766, "cookie": 3, "table_id": 0, "priority": 2000, "match": { "in_port":1, "eth_type": 2048, "ip_proto": 17, "udp_src": 67, "udp_dst": 68 }, "actions": [{ "type": "OUTPUT", "port": 3 }]}
    arp_fwd_dell_up = { "dpid": 22095312165766, "cookie": 5, "table_id": 0, "priority": 1000, "match": { "in_port":3, "eth_type": 2054 }, "actions": [{ "type": "OUTPUT", "port": 1 }]}
    arp_rvs_dell_up = { "dpid": 22095312165766, "cookie": 6, "table_id": 0, "priority": 1000, "match": { "in_port":1, "eth_type": 2054}, "actions": [{ "type": "OUTPUT", "port": 3 }]}
    ip_fwd_dell_up = { "dpid": 22095312165766, "cookie": 9, "table_id": 0, "priority": 1500, "match": { "in_port":3, "eth_type": 2048 }, "actions": [{ "type": "OUTPUT", "port": 1 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    ip_rvs_dell_up = { "dpid": 22095312165766, "cookie": 10, "table_id": 0, "priority": 1500, "match": { "in_port":1, "eth_type": 2048}, "actions": [{ "type": "OUTPUT", "port": 3 },{"type": "OUTPUT", "port":"CONTROLLER" }]}
    
    #list of flows needed for each path
    perm_flows = [arista_fwd,arista_rvs,arista_fwd_trace,arista_rvs_trace,hpovs_fwd,hpovs_rvs,hpovs_fwd_trace,hpovs_rvs_trace,hpsw_fwd,hpsw_rvs,hpsw_fwd_trace,hpsw_rvs_trace]
    flows_up = [dhcp_fwd_abmx_up,dhcp_rvs_abmx_up,arp_fwd_abmx_up,arp_rvs_abmx_up,ip_fwd_abmx_up,ip_rvs_abmx_up,dhcp_fwd_dell_up,dhcp_rvs_dell_up,arp_fwd_dell_up,arp_rvs_dell_up,ip_fwd_dell_up,ip_rvs_dell_up]
    flows_lower = [dhcp_fwd_abmx,dhcp_rvs_abmx,arp_fwd_abmx,arp_rvs_abmx,ip_fwd_abmx,dns_fwd_abmx,ip_rvs_abmx,dns_rvs_abmx,dhcp_fwd_dell,dhcp_rvs_dell,arp_fwd_dell,arp_rvs_dell,ip_fwd_dell,ip_rvs_dell]
    
    #adding the permanent flows
    for flow in perm_flows:
        add_flow(flow)
        
    #checking connectivity to dell abmx and dell OvS
    device1 = {'device_type':'linux', 'ip':'10.20.30.65', 'username':'parth', 'password':'parth'}
    device2 = {'device_type':'linux', 'ip':'10.20.30.56', 'username':'parth', 'password':'parth'}
    connect1,connect2 = connections(device1,device2)

    #monitoring the connectivity between dell abmx and dell OvS
    while True:
        def_topo1 = str(connect1.send_command("ip addr | grep eno4 |  awk '{print $11}'").strip())
        def_topo2 = str(connect2.send_command("ip addr | grep eno2 | awk '{print $11}'").strip())

        #if the connectivity is UP then choose the shortest path and add required flows
        if (def_topo1 == 'UP') and (def_topo2 == 'UP'):
            for flow in flows_up:
                del_flows(flow)
            for flow in flows_lower:
                add_flow(flow)
            print("Shortest path selected")
        
        #if the connectivity is DOWN then choose the longest path and add required flows
        else:
            for flow in flows_lower:
                del_flows(flow)
            for flow in flows_up:
                add_flow(flow)
            print("Longest path selected")
        time.sleep(10)