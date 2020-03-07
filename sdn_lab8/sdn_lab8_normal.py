#custom script to spin the mininet topology

#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch, IVSSwitch, UserSwitch
from mininet.link import Link, TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

from mininet.topo import Topo

class MyTopo( Topo ):

    def __init__( self ):
        
	Topo.__init__( self)

	print "*** Creating nodes"
        h1 = self.addHost( 'Host', ip="10.0.0.1/24", defaultRoute="via 10.0.0.2" )
        h2 = self.addHost( 'Server', ip="1.1.1.1/24", defaultRoute="via 1.1.1.2" )

     	print "*** Creating switches"
        s1 = self.addSwitch( 'OvS1', protocols='OpenFlow13' )
	    s2 = self.addSwitch( 'OvS2', protocols='OpenFlow13' )
        s3 = self.addSwitch( 'OvS3', protocols='OpenFlow13' )
        s4 = self.addSwitch( 'OvS4', protocols='OpenFlow13' )
        s5 = self.addSwitch( 'OvS5', protocols='OpenFlow13' )
        s6 = self.addSwitch( 'OvS6', protocols='OpenFlow13' )
        s7 = self.addSwitch( 'OvS7', protocols='OpenFlow13' )
        s8 = self.addSwitch( 'OvS8', protocols='OpenFlow13' )

        print "*** Creating links"
        self.addLink( s1, h1 )
        self.addLink( s1, s2 )
        self.addLink( s1, s6 )
        self.addLink( s1, s8 )
        self.addLink( s2, s3 )
        self.addLink( s3, s4 )
        self.addLink( s4, s5 )
        self.addLink( s5, h2 )
        self.addLink( s5, s8 )
        self.addLink( s5, s7 )
        self.addLink( s6, s7 )

topos = { 'mytopo': ( lambda: MyTopo() ) }