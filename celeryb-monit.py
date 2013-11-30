#!/usr/bin/python

import os
import subprocess
import time 
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def sendalert():

    print "Celery Beat is not runnning! Please Check!"
    message = "It seems celery is down or celery beat is not publishing tasks.."
    me = "sysadminops@ovivo.dk"
    to = ["okossuth@gmail.com", "jh@ovivo.dk", "af@ovivo.dk"]
    #to = "okossuth@gmail.com"
    msg = MIMEText(message)
    msg['Subject'] = "Celery Problems!"
    msg['From'] = me
    msg['To'] = ", ".join(to)
    #msg['To'] = to
    cmd = "tail -1 /etc/hosts | awk '{print $1}'"
    ret = subprocess.check_output(cmd , shell=True)
    s = smtplib.SMTP(ret)
    s.sendmail(me, to, msg.as_string())
    s.quit()

def main():
    x = 0    
    LOG = "/var/log/celeryd.log"
    cmd = "tail -10 %s | grep Beat" % LOG

    current_time = time.time()
    print current_time
    modtime = os.path.getmtime(LOG)
    print modtime

    if current_time - modtime > 300:
        print "Celery is not running!"
        sendalert()
        raise SystemExit(1)

    while x < 30:
        try:
            ret = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            print ret
	    print "Celery Beat is running... move along"
            raise SystemExit(0)
        except Exception, e:
            print "Celery beat error!!"
            pass
        x = x+1
        time.sleep(1)

    sendalert()
    raise SystemExit(1)

main()
