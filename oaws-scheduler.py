#!/usr/bin/python

"""
 * Script that starts and stops EC2 instances automatically 
 * using a pre-defined schedule to save in amazon costs
 *
 """

import os
import boto.ec2

STGBACKEND_EIP = "54.247.108.75"
DEV_EIP = "54.247.82.236"
REGION="eu-west-1"

def ensure_library_is_installed(args):
    print "The library %s is not installed!" % args
    raise SystemExit(1)

try:
    from argh import *
except ImportError:
    ensure_library_is_installed('argh')

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

######################################################


# Starts the scheduled Amazon Instance
#@arg('--instance',help='Instance ID of the instance to start',)
#@arg('--eip',help='EIP to associate',)
def start():
    
    sche = ["Staging Backend", "Backbone.js devserver"]
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    for x in sche:
        reservations = conn.get_all_instances(filters={"tag:Name": "%s" % x})
        for i in reservations:
            instance = i.instances[0]
	print "Starting instance %s " % x
	conn.start_instances(instance_ids=[instance.id])
	state = reservations[0].instances[0].state
        while state !="running":
            reservations = conn.get_all_instances(instance.id)
	    state = reservations[0].instances[0].state
        if state == "running":
            print "Instance running, checks: %s" % reservations[0].instances[0].monitoring_state
	    if x == "Staging Backend":
	        conn.associate_address(instance.id, STGBACKEND_EIP)
	    else:
		conn.associate_address(instance.id, DEV_EIP)
        else:
	    print "Error"
    
    fp = open("/var/log/scheduler.txt", 'r+')
    fp.seek(0)
    i = "Instances started.."
    fp.write(i)
    fp.close()

def stop():
    sche = ["Staging Backend", "Backbone.js devserver"]
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    for x in sche:
        reservations = conn.get_all_instances(filters={"tag:Name": "%s" % x})
        for i in reservations:
            instance = i.instances[0]
	conn.stop_instances(instance_ids=[instance.id])
	state = reservations[0].instances[0].state
        while state !="stopped":
            reservations = conn.get_all_instances(instance.id)
	    state = reservations[0].instances[0].state
        if state == "stopped":
            print "Instance stopped, checks: %s" % reservations[0].instances[0].monitoring_state
        else:
	    print "Running"
    
    fp = open("/var/log/scheduler.txt", 'r+')
    fp.seek(0)
    i = "Instances stopped.."
    fp.write(i)
    fp.close()

def status():
    sche = ["Staging Backend", "Backbone.js devserver"]
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    print "Scheduled Ovivo Amazon EC2 Instances" 
    print "-------------------------------------"
    print
    for x in sche:
	reservations = conn.get_all_instances(filters={"tag:Name": "%s" % x})
        for i in reservations:
            instance = i.instances[0]
	    try:
	        instance.tags['Name']
            except KeyError:
		instance.tags['Name'] = 'empty name'
            print "Instance: %s , Name: %s , Type: %s , State: %s " % (instance.id,instance.tags['Name'],instance.instance_type, instance.state)
    print
    print

if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([start,stop,status])
    p.dispatch()

    

