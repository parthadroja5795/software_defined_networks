#script to display the bad DNS webpage

#!/usr/bin/env python

from flask import Flask,render_template

#flask applications
app=Flask(__name__)

@app.route('/')
def index():
    #index page
    return render_template('sdn_lab10_DNS_bad.html')

#starting the flask application
if __name__=='__main__':
    
    app.debug = True
    app.run(host='0.0.0.0',port=80)