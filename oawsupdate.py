#!/usr/bin/python

""" Script to check and update system software on Amazon EC2 instances
    Oskar Kossuth (c)2013
    
    Dont forget to add the path to your key.pem
    env.key_filename = '/path/to/awskey.pem'
    
    Also create a file .fabricrc in your $HOME with this content:
    fabfile = oawsupdate.py
    After these customizations, to use the script type:
    fab oawsupdate   
"""
import fabric
from fabric.api import env, roles, cd, run, sudo, prompt, task, local, put, hide, get
import time
import boto.ec2

REGION="eu-west-1"
VPCID="sg-cb6764bf"


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
    """ The file awscreds.txt is stored in the same directory as the script.
        the contents of this file should be:
	AWSAKEY='xxxxxxxxxxxxxxxxxxxxxxx'       -> your Amazon Access Key
	AWSAKEY='xxxxxxxxxxxxxxxxxxxxxxx'       -> your Amazon Secret Key
	"""
    creds = []
    f = open("./awscreds.txt", "r")
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

def _gethosts():
    array_inst=[]
    AWSAKEY,AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    reservations = conn.get_all_instances()
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


env.user = 'oskar'
env.hosts = _gethosts()
#env.key_filename = '/path/to/awskey.pem' ---> DONT FORGET TO ENABLE THIS
env.warn_only = True
fabric.state.output['running'] = False

def oawsupdate():
    with hide('warnings'):
        print "-----------------------------------------"
	print(color.BOLD + color.YELLOW + dnsdict[env.host_string] + color.END)
	print(color.BOLD + color.BLUE + "Checking for updates to system software..." + color.END)
        status = run('yum check-update -q')
        if len(status) <= 0 :
            print "System software is at the latest level"
	    print ""
        else:
            print(color.RED + "New updates for system software available!!!" + color.END)
            input = raw_input("Do you want to update system software on instance? (y/n)")
	    if input == "y":
                print "Updating now..."
	        sudo('yum update -y')
                print(color.GREEN + "System software is now at the latest level :)" +  color.END)
                print ""
	    elif input == "n":
	        pass
	    else:
		print "Wrong answer, continuing with the next instance..."
	print "----------------------------------------------"
	print ""

def health(*name):
    #with hide('running','output','warnings'):
    with hide('everything'):
        AWSAKEY,AWSSKEY = _getcreds()
        conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
        if not name:
            reservations = conn.get_all_instances()
        else:
	    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % name})
        for i in reservations:
            instance = i.instances[0]
	    if instance.tags['Name'] == dnsdict[env.host_string] :
	        print "----------------------------------------------------------------------------------"
    	        print(color.BOLD + color.YELLOW + dnsdict[env.host_string] + " health status" + color.END)
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
	    else:
                pass



