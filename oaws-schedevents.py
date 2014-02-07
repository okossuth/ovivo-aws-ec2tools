#!/usr/bin/python

import boto.ec2

REGION="eu-west-1"

# AWS Credentials retrieval using encrypted C shared library ##

import os, pwd, grp
f=open('/tmp/.uwsgi.lock', 'w+')
f.close()
uid = pwd.getpwnam('oskar').pw_uid
gid = grp.getgrnam('oskar').gr_gid
os.chown('/tmp/.uwsgi.lock', uid, gid)

import ctypes
from ctypes import CDLL

pylibc = CDLL("/home/ella/Ella/ella/awsenckeys.so")
pylibc.awsakey.restype = ctypes.c_char_p
pylibc.awsskey.restype = ctypes.c_char_p

AWSAKEY = pylibc.awsakey()
AWSSKEY = pylibc.awsskey()

def sendalert(id,event):
    message = "Instance %s has a scheduled event: %s" % (id, event)
    me = "sysadminops@ovivo.dk"
    to = ["okossuth@gmail.com", "jh@ovivo.dk", "af@ovivo.dk"]
    #to = "okossuth@gmail.com"
    msg = MIMEText(message)
    msg['Subject'] = "AWS Scheduled Event!"
    msg['From'] = me
    msg['To'] = ", ".join(to)
    #msg['To'] = to
    cmd = "tail -1 /etc/hosts | awk '{print $1}'"
    ret = subprocess.check_output(cmd , shell=True)
    s = smtplib.SMTP(ret)
    s.sendmail(me, to, msg.as_string())
    s.quit()

def main():
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    stats = conn.get_all_instance_status()
    x = 0
    y = 0
    for i in stats:
         stat= stats[x]
         reservations = conn.get_all_instances(instance_ids=[stat.id])
         instance = reservations[0].instances[0]
         if stat.events is not None:
             print "instance: %s" % stat.id
             print "Instance Name: %s" % instance.tags['Name']
             print "Events pending: %s" % stat.events
             print "State: %s" % stat.state_name
	     sendalert(stat.id, stat.events)
	     y = 1
         else:
             pass
         x=x+1
    if y == 1:
        print "There are instances with scheduled events"
    else:
        print "There are no instances with scheduled events"

main()
