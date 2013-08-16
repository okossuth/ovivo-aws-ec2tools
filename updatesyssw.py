#!/usr/bin/python

""" Script to check and update system software on Amazon EC2 instances
    Oskar Kossuth (c)2013
"""

from fabric.api import env, roles, cd, run, sudo, prompt, task, local, put, hide, get
import time
import boto.ec2

REGION="eu-west-1"
AWSAKEY="AKA"
AWSSKEY="C7F"

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def check_library(name):
    print 'The library %s is not installed' % name
    print
    print 'Just type pip install %s and you will be fine :) \n' % name
    raise SystemExit(1)

try:
    from fabric import *
except ImportError:
    check_library('fabric')

def _gethosts():
    array_inst=[]
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    reservations = conn.get_all_instances()
    for i in reservations:
        instance = i.instances[0]
	id_instance = instance.id
	ip_instance = instance.ip_address
	sec_instance = instance.groups[0]
	if ip_instance is not None and sec_instance.id=="sg-cb6764bf":
	     array_inst.append(ip_instance)
    return tuple(array_inst)

env.user = 'oskar'
env.hosts = _gethosts()
env.key_filename = '/home/oskar/Documents/Projects/Ovivo/ovivoec2.pem'
env.warn_only = True

def updatesyssw():
    with hide('output','running','warnings'):
	print(color.BOLD + color.BLUE + "Checking for updates to System Software..." + color.END)
        status = run('yum check-update -q')
        if len(status) <= 0 :
            print "System Software is at the latest level"
	    print ""
        else:
            print "System Software is oudated"
	    print "Updating now..."
	    sudo('yum update -y')
            print(color.GREEN + "System Software is now at the latest level :)" +  color.END)
            print ""
	print "----------------------------------------------"
	print ""





