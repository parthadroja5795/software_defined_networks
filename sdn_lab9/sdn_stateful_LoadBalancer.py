#Stateful LoadBalancer application for Ryu controller

#!/usr/bin/env python

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ether
from ryu.lib.packet import packet, ethernet, ether_types, arp, tcp, ipv4
import random
import time

#application class
class Parth_Stateful_LoadBalancer(app_manager.RyuApp):
    #Specifying OpenFlow version
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Parth_Stateful_LoadBalancer, self).__init__(*args, **kwargs)
        
        #MAC to port mapping for the switch
        self.mac_to_port = {}

        #virtual MAC and IP for the LoadBalancer Application        
        self.virtual_ip = "10.0.0.100"
        self.virtual_mac = "11:22:33:44:55:66"
        
        #IP and MAC addresses for three servers
        self.h1_ip = "10.0.0.1"
        self.h2_ip = "10.0.0.2"
        self.h3_ip = "10.0.0.3"
        self.h1_mac = "00:00:00:00:00:01"
        self.h2_mac = "00:00:00:00:00:02"
        self.h3_mac = "00:00:00:00:00:03"
        
        #count to keep track of which server is currently serving
        self.tcp_count = 1
        self.icmp_count = 1

    #Getting switch features and adding default flow as send to CONTROLLER
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]

        #adding default flow as send to CONTROLLER
        self.add_flow(datapath, 0, match, actions)

    #Function to add flow
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,priority=priority, match=match,instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,match=match, instructions=inst)
        datapath.send_msg(mod)

    #Function to handle Packet_IN messages
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dpid = datapath.id
        dst = eth.dst
        src = eth.src
        in_port = msg.match['in_port']
        
        #Displaying Packet_IN information
        if eth.ethertype == 0x0806:
            self.logger.info("Packet_IN -> dpid: {}, src_mac: {}, dst_mac: {}, in_port: {}".format(dpid, src, dst, in_port))

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        #Ignoring LLDP packet
        if eth.ethertype == 0x88cc:
            return

        #Handling ARP Packet_IN
        if eth.ethertype == 0x0806:
            arp_header = pkt.get_protocols(arp.arp)[0]

            #Handling ARP Request Packet_IN for the virtual IP of the application
            if arp_header.dst_ip == self.virtual_ip and arp_header.opcode == 1:

                temp_dst_mac = arp_header.src_mac
                temp_dst_ip = arp_header.src_ip

                packet_reply = packet.Packet()
                ether_reply = ethernet.ethernet(temp_dst_mac, self.virtual_mac, 0x0806)  #(dst_mac, src_mac, type)
                arp_reply = arp.arp(1,0x0800,6,4,2,self.virtual_mac,self.virtual_ip,temp_dst_mac,temp_dst_ip)   #(hw_type, mac_length, ip_length, arp_reply, src_mac, src_ip, dst_mac, dst_ip)
                
                #Creating ARP Reply packet
                packet_reply.add_protocol(ether_reply)
                packet_reply.add_protocol(arp_reply)
                packet_reply.serialize()

                #Specifying action for the ARP Reply packet
                actions_virtual_server = [parser.OFPActionOutput(in_port)]
                
                #Generating Packet_OUT message for the ARP Reply
                arp_virtual_server = parser.OFPPacketOut(datapath=datapath, in_port=ofproto.OFPP_ANY, data=packet_reply.data,actions=actions_virtual_server, buffer_id=0xffffffff)
                
                #Displaying Packet_OUT information
                self.logger.info("Packet_OUT -> dpid: {}, src_mac: {}, dst_mac: {}, in_port: {}".format(dpid, self.virtual_mac, src, in_port))

                #Sending Packet_OUT message
                datapath.send_msg(arp_virtual_server)
                return
 
            else:
                #recording the MAC address and port number
                self.mac_to_port.setdefault(dpid, {})
                self.mac_to_port[dpid][src] = in_port

                if dst in self.mac_to_port[dpid]:
                    out_port = self.mac_to_port[dpid][dst]
                else:
                    out_port = ofproto.OFPP_FLOOD

                actions = [parser.OFPActionOutput(out_port)]

                if out_port != ofproto.OFPP_FLOOD:
                    match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                    if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                        self.add_flow(datapath, 1, match,actions, msg.buffer_id)
                        return
                    else:
                        self.add_flow(datapath, 1, match, actions)
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data

                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
                return

        #Handling IP Packet_IN
        if eth.ethertype == 0x0800:
            raw_ip = pkt.get_protocols(ipv4.ipv4)[0]
            
            #handling ICMP Packet_IN towards the LoadBalancer
            if raw_ip.proto == 0x01 and raw_ip.dst == "10.0.0.100":
                self.logger.info("ICMP Packet_IN detected")
                if self.icmp_count == 1:
                    current_server_mac = self.h1_mac
                    current_server_ip = self.h1_ip
                elif self.icmp_count == 2:
                    current_server_mac = self.h2_mac
                    current_server_ip = self.h2_ip                    
                elif self.icmp_count == 3:
                    current_server_mac = self.h3_mac
                    current_server_ip = self.h3_ip
                    
                self.logger.info("Current Server is {}".format(self.icmp_count))
                
                #Getting the required match parameters
                match_1 = parser.OFPMatch(in_port=in_port, eth_type=eth.ethertype, eth_src=eth.src, eth_dst=eth.dst,ip_proto=raw_ip.proto, ipv4_src=raw_ip.src, ipv4_dst=raw_ip.dst)
                
                #Specifying modify actions on the packet to forward it to current serving server
                actions_1 = [parser.OFPActionSetField(eth_dst=current_server_mac),parser.OFPActionSetField(ipv4_dst=current_server_ip),parser.OFPActionOutput(self.icmp_count)]
                
                #Applying the specified modify actions
                instructions_1 = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions_1)]
                cookie = random.randint(0, 0xffffffffffffffff)
                
                #Creating a FlowMod packet to be sent to the switch
                add_flow_1 = parser.OFPFlowMod(datapath=datapath, match=match_1, idle_timeout=0, instructions=instructions_1, buffer_id=msg.buffer_id, cookie=cookie)
                
                #Displaying the IP flow of the packet (HTTP request)
                self.logger.info("Client to Application -> src_ip: {} dst_ip: {} src_mac: {} dst_mac: {}".format(raw_ip.src,raw_ip.dst,eth.src,eth.dst))
                self.logger.info("Application to Server -> src_ip: {} dst_ip: {} src_mac: {} dst_mac: {}".format(self.virtual_ip,current_server_ip,self.virtual_mac,current_server_mac))
                
                #Adding the flow in the switch
                datapath.send_msg(add_flow_1)
                
                #Getting the required match parameters                
                match_2 = parser.OFPMatch(in_port=self.icmp_count, eth_type=eth.ethertype, eth_src=current_server_mac,eth_dst=eth.src, ip_proto=raw_ip.proto, ipv4_src=current_server_ip,ipv4_dst=raw_ip.src)
                
                #Specifying modify actions on the packet to forward it to requesting host
                actions_2 = [parser.OFPActionSetField(eth_src=current_server_mac),parser.OFPActionSetField(ipv4_src=current_server_ip),parser.OFPActionOutput(in_port)]
                
                #Applying the specified modify actions
                instructions_2 = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions_2)]
                cookie = random.randint(0, 0xffffffffffffffff)
                
                #Creating a FlowMod packet to be sent to the switch
                add_flow_2 = parser.OFPFlowMod(datapath=datapath, match=match_2, idle_timeout=0, instructions=instructions_2, cookie=cookie)
                
                #Displaying the IP flow of the packet (HTTP Reply)
                self.logger.info("Server to Application -> src_ip: {} dst_ip: {} src_mac: {} dst_mac: {}".format(current_server_ip,self.virtual_ip,current_server_mac,self.virtual_mac))
                self.logger.info("Application to Client -> src_ip: {} dst_ip: {} src_mac: {} dst_mac: {}".format(self.virtual_ip,raw_ip.src,self.virtual_mac,eth.src))
                
                #Adding the flow in the switch
                datapath.send_msg(add_flow_2)
                
                #Increasing the icmp_count to change the current server to next server
                self.icmp_count = self.icmp_count + 1
                if self.icmp_count > 3:
                    self.icmp_count = 1
            
            #If the packet is TCP
            if raw_ip.proto == 0x06:
                raw_tcp = pkt.get_protocols(tcp.tcp)[0]

                #If the packet is HTTP
                if raw_tcp.dst_port == 80:
                    
                    self.logger.info("TCP Packet_IN detected")
                    #Selecting the current serving server based on the count
                    if self.tcp_count == 1:
                        current_server_mac = self.h1_mac
                        current_server_ip = self.h1_ip
                    elif self.tcp_count == 2:
                        current_server_mac = self.h2_mac
                        current_server_ip = self.h2_ip                    
                    elif self.tcp_count == 3:
                        current_server_mac = self.h3_mac
                        current_server_ip = self.h3_ip
                        
                    self.logger.info("Current Server is {}".format(self.tcp_count))

                    #Getting the required match parameters
                    match_1 = parser.OFPMatch(in_port=in_port, eth_type=eth.ethertype, eth_src=eth.src, eth_dst=eth.dst,ip_proto=raw_ip.proto, ipv4_src=raw_ip.src, ipv4_dst=raw_ip.dst)
        
                    #Specifying modify actions on the packet to forward it to current serving server
                    actions_1 = [parser.OFPActionSetField(eth_dst=current_server_mac),parser.OFPActionSetField(ipv4_dst=current_server_ip),parser.OFPActionOutput(self.tcp_count)]

                    #Applying the specified modify actions
                    instructions_1 = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions_1)]
                    cookie = random.randint(0, 0xffffffffffffffff)
                    
                    #Creating a FlowMod packet to be sent to the switch
                    add_flow_1 = parser.OFPFlowMod(datapath=datapath, match=match_1, idle_timeout=0, instructions=instructions_1, buffer_id=msg.buffer_id, cookie=cookie)
                    
                    #Displaying the IP flow of the packet (HTTP request)
                    self.logger.info("Client to Application -> src_ip: {} dst_ip: {} src_mac: {} dst_mac: {}".format(raw_ip.src,raw_ip.dst,eth.src,eth.dst))
                    self.logger.info("Application to Server -> src_ip: {} dst_ip: {} src_mac: {} dst_mac: {}".format(self.virtual_ip,current_server_ip,self.virtual_mac,current_server_mac))

                    #Adding the flow in the switch
                    datapath.send_msg(add_flow_1)
        
                    #Getting the required match parameters                
                    match_2 = parser.OFPMatch(in_port=self.tcp_count, eth_type=eth.ethertype, eth_src=current_server_mac,eth_dst=eth.src, ip_proto=raw_ip.proto, ipv4_src=current_server_ip,ipv4_dst=raw_ip.src)
                    
                    #Specifying modify actions on the packet to forward it to requesting host
                    actions_2 = [parser.OFPActionSetField(eth_src=self.virtual_mac),parser.OFPActionSetField(ipv4_src=self.virtual_ip),parser.OFPActionOutput(in_port)]
                    
                    #Applying the specified modify actions
                    instructions_2 = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions_2)]
                    cookie = random.randint(0, 0xffffffffffffffff)

                    #Creating a FlowMod packet to be sent to the switch
                    add_flow_2 = parser.OFPFlowMod(datapath=datapath, match=match_2, idle_timeout=0, instructions=instructions_2, cookie=cookie)
                    
                    #Displaying the IP flow of the packet (HTTP Reply)
                    self.logger.info("Server to Application -> src_ip: {} dst_ip: {} src_mac: {} dst_mac: {}".format(current_server_ip,self.virtual_ip,current_server_mac,self.virtual_mac))
                    self.logger.info("Application to Client -> src_ip: {} dst_ip: {} src_mac: {} dst_mac: {}".format(self.virtual_ip,raw_ip.src,self.virtual_mac,eth.src))
  
                    #Adding the flow in the switch
                    datapath.send_msg(add_flow_2)
                    
                    #Increasing the tcp_count to change the current server to next server
                    self.tcp_count = self.tcp_count + 1
                    if self.tcp_count > 3:
                        self.tcp_count = 1