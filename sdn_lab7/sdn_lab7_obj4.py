#script to add required flows and firewall rules via user friendly webpage

#!/usr/bin/env python

from flask import Flask, render_template, request
import requests

#flask application
app = Flask (__name__)

@app.route("/")
def index():
        #number to name the flows
        global number
        number = number + 1
        #index page
        return render_template('sdn_lab7_index.html')
    
@app.route("/static", methods =['GET','POST'])
def static_flow_entries():
        #static flow addition page
        return render_template('sdn_lab7_static_flow_entries.html')
    
@app.route("/add", methods =['GET','POST'])
def static_flow():
    if request.method=='POST':
        
        #getting the information provided via webpage
        dpid=request.form['DPID']
        priority=request.form['PRIORITY']
        in_port=request.form['IN_PORT']
        eth_type=request.form['ETH_TYPE']
        dest_ip=request.form['DESTINATION_IP']
        action=request.form['ACTION']

        url_flow_add="http://192.168.10.22:8080/wm/staticentrypusher/json"
        
        #adding static flows for ARP
        if dest_ip =='':
            data_flow = "{\"switch\":\""+dpid+"\",\"name\":\"flow-mod-"+str(number)+"\",\"priority\":\""+str(priority)+"\",\"in_port\":\""+str(in_port)+"\",\"active\":\"true\",\"eth_type\":\""+str(eth_type)+"\",\"actions\":\"output="+str(action)+"\"}"
            r_flow = requests.post(url = url_flow_add, data= data_flow)

        #adding static flows for other traffic
        else:
            data_flow = "{\"switch\":\""+dpid+"\",\"name\":\"flow-mod-"+str(number)+"\",\"priority\":\""+str(priority)+"\",\"in_port\":\""+str(in_port)+"\",\"active\":\"true\",\"eth_type\":\""+str(eth_type)+"\",\"ipv4_dst\":\""+str(dest_ip)+"\",\"actions\":\"output="+str(action)+"\"}"
            r_flow = requests.post(url = url_flow_add, data= data_flow)
    
    return render_template('sdn_lab7_added.html')
    
@app.route("/firewall", methods =['GET','POST'])
def firewall():
        
    #enabling firewall
    url_firewall="http://192.168.10.22:8080/wm/firewall/module/enable/json"
    data_flow=""
    requests.put(url=url_firewall,data=data_flow)

    return render_template('sdn_lab7_firewall.html')

@app.route("/add_firewall", methods =['GET','POST'])
def firewall_add():
    if request.method=='POST':
        
        #getting the information provided via webpage
        dpid=request.form['DPID']
        priority=request.form['PRIORITY']
        in_port=request.form['IN_PORT']
        eth_type=request.form['ETH_TYPE']
        src_ip=request.form['SOURCE_IP']
        dest_ip=request.form['DESTINATION_IP']
        l4_protocol=request.form['L4_PROTOCOL']
        action=request.form['ACTION']

        url_flow_add="http://192.168.10.22:8080/wm/staticentrypusher/json"

        #adding static flows for ARP
        if src_ip =='':
            data_flow = "{\"switch\":\""+dpid+"\",\"name\":\"flow-mod-"+str(number)+"\",\"priority\":\""+str(priority)+"\",\"in_port\":\""+str(in_port)+"\",\"active\":\"true\",\"eth_type\":\""+str(eth_type)+"\",\"actions\":\"output="+str(action)+"\"}"
            r_flow = requests.post(url = url_flow_add, data= data_flow)

        #adding static flows for other traffic
        else:
            data_flow = "{\"switch\":\""+dpid+"\",\"name\":\"flow-mod-"+str(number)+"\",\"priority\":\""+str(priority)+"\",\"in_port\":\""+str(in_port)+"\",\"active\":\"true\",\"eth_type\":\""+str(eth_type)+"\",\"ipv4_dst\":\""+str(dest_ip)+"\",\"ipv4_src\":\""+str(src_ip)+"\",\"ip_proto\":\""+str(l4_protocol)+"\",\"actions\":\"output="+str(action)+"\"}"
            r_flow = requests.post(url = url_flow_add, data= data_flow)

        return render_template('sdn_lab7_added.html')

if __name__ =="__main__":
    
    number = 1
    app.debug=True
    #starting web server
    app.run(host='0.0.0.0',port=8000)