#traceroute application for Ryu controller

#!/usr/bin/env python

from ryu.base import app_manager
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import packet
from ryu.lib.packet.packet import Packet
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import ipv4

class tracert(app_manager.RyuApp):
    #Specifying OpenFlow version
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    #list of devices and their DPIDs
    dpid_list = {'22095312424577':'DELL_ABMX_OVS', '22095312165766':'Dell_OVS_Server', '122194256519':'Arista Switch', '122196472497':'HP Switch','63464340112':'HP_OVS_Server'}
    
    trace = []
    names = []

    def __init__(self, *args, **kwargs):
        super(tracert, self).__init__(*args, **kwargs)

    #function to detect and analyze the messages coming to the controller
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def pacIN_parser(self, ev):
        msg = ev.msg
        datap = msg.datapath
        ofp = datap.ofproto
        ofp_parser = datap.ofproto_parser

        #recording the in_port of the packet
        incoming_port = msg.match['in_port']
        print("Packet_IN incoming port is /n")
        print(incoming_port)
        pack = packet.Packet(msg.data)
        
        #recording the DPID of the packet
        print('DPID is '+str(datap.id)+' of' + str(self.dpid_list[str(datap.id)]) + ' from port '+str(incoming_port))
        
        #making list of DPIDs via which the packet has traversed
        if str(datap.id) not in self.trace:
            self.trace.append(str(datap.id))
        print("DPID list is " + str(self.trace))

        #making list of devices via which the packet has traversed
        if self.dpid_list[str(datap.id)] not in self.names:
            self.names.append(str(self.dpid_list[str(datap.id)]))
            
        #printing the trace
        print("Devices traversed are " + str(self.names))