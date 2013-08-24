#!/usr/bin/python

""" Script to check and update system software on Amazon EC2 instances
    Oskar Kossuth (c)2013
    
    The file awscreds.txt is stored in the same directory as this script.
        the contents of the file should be:
	AWSAKEY='xxxxxxxxxxxxxxxxxxxxxxx'       -> your Amazon Access Key
	AWSAKEY='xxxxxxxxxxxxxxxxxxxxxxx'       -> your Amazon Secret Key
	AWSKEYPEM='/path/to/awskey.pem'         -> your Amazon Key PEM
	
    After these customizations, to use the script type:
    ./oawsupdate  or ./oawsupdate "Name of Amazon instance" 
"""
import fabric
from fabric.api import env, roles, cd, run, sudo, prompt, task, local, put, hide, get
from fabric.main import main
import sys
import time
import boto.ec2

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


if __name__ == '__main__':
    sys.argv = ['fab', '-f', __file__, ] + sys.argv[1:]
    env.hosts = _gethosts(sys.argv[3:])
    env.user = 'oskar'
    env.key_filename = _getkeypem() 
    env.warn_only = True
    fabric.state.output['running'] = False
    for i in env.hosts:
        env.host_string = i
	oawsupdate()
