#DNS Blacklist application for Ryu controller

#!/usr/bin/env python

import sys
from ryu.lib.packet import packet as ryu_packet
from scapy.all import packet as scapy_packet
from ryu.lib.packet import *
from scapy.all import *
import chardet
import requests
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp, tcp, ipv4, udp

class Parth_DNS(app_manager.RyuApp):
	#Specifying OpenFlow version
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(Parth_DNS, self).__init__(*args, **kwargs)

		#MAC to port mapping for the switch
		self.mac_to_port = {}

		#Getting switch features and adding default flow as send to CONTROLLER
		@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
		def switch_features_handler(self, ev):
			datapath = ev.msg.datapath
			#print("Connection from switch with DPID: ",datapath.id)
			ofproto = datapath.ofproto
			parser = datapath.ofproto_parser
			match = parser.OFPMatch()
			actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
			#adding default flow as send to CONTROLLER
			#self.add_flow(datapath, 0, match, actions)

	def add_flow(self, datapath, priority, match, actions, buffer_id=None):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
		if buffer_id:
			mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,priority=priority, match=match,instructions=inst)
		else:
			mod = parser.OFPFlowMod(datapath=datapath, priority=priority,match=match, instructions=inst)
		datapath.send_msg(mod)

	#function to create and send DNS response
	def dns_response(self,datapath,pkt_ethernet,port,pkt_ipv4,pkt_udp,data,flag):
		print("DNS response function")

		hw_addr = "00:17:5a:37:60:11"        
		if flag == "good":
			response_url = "35.172.72.141"
		elif flag == "bad":
			response_url = "127.0.0.1"
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		pkt_len = len(data)
		flag = data[42:44]
		b=chardet.detect(data[42:44])
		if b['encoding'] == None:
			c=flag.hex()
		else:
			flag.decode(b['encoding'])
			c=flag.hex()
		d=int(c,16)
		domain = (data[55:pkt_len-5])
		dm = domain
		if dm[0:4] == "http":
			pass
		else:
			dm = "http://"+str(domain)
				
		doen = chardet.detect(domain)
		d_len = len(domain)
		domain1 = domain
		domain = domain.decode("utf-8")

		for g in range(0,len(domain)-1):
			if ord(domain[g])<32 or ord(domain[g])>126:
				domain=domain[:g]+"."+domain[g+1:]

		ip_src = pkt_ipv4[0].dst
		ip_dst = pkt_ipv4[0].src
		sport = 53
		dport = pkt_udp[0].src_port
		dm = domain
		if dm[0:4] == "http":
			pass
		else:
			dm = "http://"+domain

		#creating DNS response packet with scapy
		a = Ether(dst=pkt_ethernet.src, src=hw_addr)/IP(dst=ip_dst,src=ip_src)/UDP(sport=sport,dport=dport)/DNS(opcode=0,id=d,qr=1,rd=1,ra=1,aa=0,tc=0,z=0, rcode=0,qdcount=1,ancount=1,nscount=1,arcount=0,qd=DNSQR(qname=domain),an=DNSRR(rrname=domain,ttl=60,rdata=response_url),ns=DNSRR(rrname=domain,type=2,ttl=60,rdata="ns1."+str(domain)),ar=None)
		data = scapy.all.Packet(a)
		data = bytes(data)
		actions = [parser.OFPActionOutput(port=port)]
		
		#sending the DNS response packet
		out = parser.OFPPacketOut(datapath=datapath,buffer_id=ofproto.OFP_NO_BUFFER,in_port=ofproto.OFPP_CONTROLLER,actions=actions,data=data)
		datapath.send_msg(out)
		print("DNS response sent")

	#function to handle Packet_IN messages
	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		if ev.msg.msg_len < ev.msg.total_len:
			self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		pkt = ryu_packet.Packet(data=msg.data)
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

		#Handling IP Packet_IN
		if(eth.ethertype==0x0800):
			pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)
			pkt_ethernet = pkt.get_protocol(ethernet.ethernet)

			#If the packet is UDP
			if pkt_ipv4[0].proto == in_proto.IPPROTO_UDP:
				pkt_udp = pkt.get_protocols(udp.udp)

				if pkt_udp[0].dst_port == 53:
					data = msg.data

					checker = "http://checksite.herokuapp.com"

					url_good = "http://goodweb.herokuapp.com"
					url_bad = "http://badweb.herokuapp.com"

					print("DNS packet_IN detected")
					dns_data=((pkt[-1].decode('utf-8','ignore')))
					
					#checking if the user is accessing good, bad or other site
					if "good" in str(dns_data):
						print("Host is accessing Good site")
						call_good = checker+"/api/url="+url_good
						response_good = requests.get(call_good)
						raw_json_good = response_good.json()
						flag = raw_json_good['site']['id']
						flag = "good"
						self.dns_response(datapath,pkt_ethernet,in_port,pkt_ipv4,pkt_udp,data,flag)

					elif "bad" in str(dns_data):
						print("Host is accessing Bad site")
						call_bad = checker+"/api/url="+url_bad
						response_bad = requests.get(call_bad)
						raw_json_bad = response_bad.json()
						flag = raw_json_bad['site']['id']
						flag="bad"
						self.dns_response(datapath,pkt_ethernet,in_port,pkt_ipv4,pkt_udp,data,flag)
						
					else:
						print("Host is accessing other site")
						call_bad = checker+"/api/url="+url_bad
						response_bad = requests.get(call_bad)
						raw_json_bad = response_bad.json()
						flag = raw_json_bad['site']['id']
						flag = 'bad'
						self.dns_response(datapath,pkt_ethernet,in_port,pkt_ipv4,pkt_udp,data,flag)