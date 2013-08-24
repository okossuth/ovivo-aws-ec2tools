#!/usr/bin/python

""" Script to check Health of Amazon EC2 instances
    Oskar Kossuth (c)2013

    The file awscreds.txt is stored in the same directory as the script.
        the contents of this file should be:
	AWSAKEY='xxxxxxxxxxxxxxxxxxxxxxx'       -> your Amazon Access Key
	AWSAKEY='xxxxxxxxxxxxxxxxxxxxxxx'       -> your Amazon Secret Key
	AWSKEYPEM='/path/to/awskey.pem'         -> your Amazon Key PEM

    To use the script type:
    oawshealth  or oawshealth "Name of Instance" 
"""
import fabric
from fabric.api import env, roles, cd, run, sudo, prompt, task, local, put, hide, get
from fabric.main import main
import time
import boto.ec2
import sys


REGION="eu-west-1"
VPCID="sg-cb6764bf"
AWSCREDS="./awscreds.txt"

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

dnsdict = {}


def _getcreds():
    creds = []
    f = open(AWSCREDS, "r")
    c = f.readlines()
    f.seek(0)
    aws_akey = c[0]
    aws_skey = c[1]
    for i in range(len(aws_akey)):
        if aws_akey[i] == "=":
	    pos = i
    for i in range(len(aws_skey)):
        if aws_skey[i] == "=":
	    pos = i
    creds.append(aws_akey[pos+2:-2])
    creds.append(aws_skey[pos+2:-2])
    return tuple(creds)

def _getkeypem():
    f = open(AWSCREDS, "r")
    c = f.readlines()
    f.seek(0)
    aws_keypem = c[2]
    for i in range(len(aws_keypem)):
        if aws_keypem[i] == "=":
	    pos = i
    return aws_keypem[pos+2:-2]

def _gethosts(*name):
    array_inst=[]
    AWSAKEY,AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if len(name[0]) < 1:
        reservations = conn.get_all_instances()
    else:
        val = str(name[0])
	reservations = conn.get_all_instances(filters={"tag:Name": "%s" % val[2:-2]})
    for i in reservations:
        instance = i.instances[0]
	id_instance = instance.id
	ip_instance = instance.ip_address
	sec_instance = instance.groups[0]
	iname = instance.tags['Name']
	if ip_instance is not None and sec_instance.id==VPCID:
	     array_inst.append(ip_instance)
             dnsdict[ip_instance] = iname
    return tuple(array_inst)



def health(*name):
    #with hide('running','output','warnings'):
    with hide('everything'):
        AWSAKEY,AWSSKEY = _getcreds()
        conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
        if len(name) <= 1:
            reservations = conn.get_all_instances()
        else:
	    val = str(name[0])
	    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % val[2:-2]})
        for i in reservations:
            instance = i.instances[0]
	    if len(name) <= 1:
		val = "''" + dnsdict[env.host_string] + "''"
	    if instance.tags['Name'] == "%s" % val[2:-2] :
	        print "----------------------------------------------------------------------------------"
	        print(color.BOLD + color.YELLOW + val[2:-2] + " health status" + color.END)
		print "Instance state: %s " % instance.state
                print "Instance ID: %s " % instance.id
	        print "Instance Type: %s " % instance.instance_type
                status = run('uptime')
	        print (color.GREEN + "Instance Uptime" +color.END)
		print status
		print
		status = run('df -h')
		print (color.GREEN + "Instance Disk Space" +color.END)
		print status
		print
		status = run('free -m')
		print (color.GREEN + "Instance Memory Usage" +color.END)
		print status
		print
		print "----------------------------------------------------------------------------------"
	        print ""
		break
	    else:
                pass


if __name__ == '__main__':
    sys.argv = ['fab', '-f', __file__, ] + sys.argv[1:]
    env.hosts = _gethosts(sys.argv[3:])
    env.user = 'oskar'
    env.key_filename = _getkeypem()
    env.warn_only = True
    fabric.state.output['running'] = False
    for i in env.hosts:
	env.host_string = i
	health(sys.argv[3:])

