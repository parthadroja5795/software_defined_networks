#script to automate the configuration of all devices

#!/usr/bin/env python

import os
import json
from netmiko import ConnectHandler

#function to read the NSOT file
def read_nsot(filename):
	with open(filename) as file:
		configuration = json.load(file)

	logins = {}
	commands = {}
	for i in configuration.keys():
		login = {}
		print("Below is the info regarding router :" + str(i)+"\n")
		print(str(configuration[i]))
		commands[i] = configuration[i]['Commands']
		login['device_type']= str(configuration[i]['device_type'])
		login['ip'] = str(configuration[i]['SwitchIP'])
		login['username'] = str(configuration[i]['username'])
		login['password'] = str(configuration[i]['password'])
		logins[str(i)] = login
	return(logins,commands)

#function to push the configuration to the devices
def push_config(logins,commands,cred):
	for devicename in logins.keys():
		device = logins[devicename]
		command_str = commands[devicename]
		connect = ConnectHandler(**device)
		command_list = command_str.split(",")
		print('Connection to device '+str(devicename)+' successful')
		print(command_list)
		for command in command_list:
			send_command = connect.send_command_timing(command)
			if 'password' in send_command:
				send_command += connect.send_command_timing(str(cred[devicename]))
		print("Device "+str(devicename)+" configured successfully")

#function to check the OpenFlow connection between device and controller
def check_connectivity(logins,check,cred):
	print("Verifying the connectivity with the controller")
	for devicename in logins.keys():
		device = logins[devicename]
		connect = ConnectHandler(**device)
		send_command = connect.send_command_timing(str(check[devicename]))
		if 'password' in send_command:
			send_command += connect.send_command_timing(str(cred[devicename]))
		print("Connectivity status for device "+str(devicename))
		print("/n")

if __name__ == "__main__":
	
	filename = "sdn_lab10_nsot.json"

	#checking if NSOT file exists or not
	if os.path.isfile(filename) == 0:
		print("NSOT file not found. Please try again.")
		exit()

	configure_commands = {'HP OVS':'sudo ovs-vsctl show hp_br', 'ABMX-dell OVS':'sudo ovs-vsctl show abmx_br', 'Dell OVS':'sudo ovs-vsctl show dell_br', 'HP Switch':'show openflow', 'Arista switch':'show openflow'}
	credentials = {'HP OVS':'parth', 'ABMX-dell OVS':'parth', 'Dell OVS':'parth', 'HP Switch':'parth', 'Arista switch':'parth'}

	#reading the NSOT file
	logins,commands = read_nsot(filename)
	
	#pushing the configuration
	push_config(logins,commands,credentials)
	
	#checking the OpenFlow connection between device and controller
	check_connectivity(logins,configure_commands,credentials)