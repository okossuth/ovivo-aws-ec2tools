#!/usr/bin/python

""" Script to create consistent snapshots of Amazon EC2 instances
    Oskar Kossuth (c)2013

    The file awscreds.txt is stored in the same directory as the script.
        the contents of this file should be:
	AWSAKEY='xxxxxxxxxxxxxxxxxxxxxxx'       -> your Amazon Access Key
	AWSAKEY='xxxxxxxxxxxxxxxxxxxxxxx'       -> your Amazon Secret Key
	AWSKEYPEM='/path/to/awskey.pem'         -> your Amazon Key PEM

    To use the script type:
    oaws-ec2snapshot or oaws-ec2snapshot "Name of Instance" 
"""
import time
import boto.ec2
import sys
import os

REGION="eu-west-1"
#REGION="us-east-1"
VPCID_EUWEST="sg-cb6764bf"
VPCID_USEAST="sg-4a43ca22"
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
    import paramiko
except ImportError:
    check_library('paramiko')

try:
    from argh import *
except ImportError:
    check_library('argh')


#dnsdict = {}

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

def _getawsaccid():
    f = open(AWSCREDS, "r")
    c = f.readlines()
    f.seek(0)
    aws_accid = c[3]
    for i in range(len(aws_accid)):
        if aws_accid[i] == "=":
	    pos = i
    return aws_accid[pos+2:-2]

"""def _gethosts(*name):
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
	if ip_instance is not None and (sec_instance.id==VPCID_EUWEST or sec_instance.id==VPCID_USEAST):
	     array_inst.append(ip_instance)
             dnsdict[ip_instance] = iname
	     
	else:
	    if ip_instance is None and (sec_instance.id==VPCID_EUWEST or sec_instance.id==VPCID_USEAST):
	         array_inst.append(iname)
                 dnsdict[iname] = iname
                 
    return tuple(array_inst)
"""

@arg('--instance', help = 'Instance to list snapshots',)
def list(args):
    AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None:
        print 'Listing all snapshots'
        snaps = conn.get_all_snapshots(owner=AWSACCID)
        for i in snaps:
	    print "Snapshot: %s %s %sGB %s %s" % (i.id, i.description, i.volume_size, i.status, i.start_time)
    else:
	snaps = conn.get_all_snapshots(filters = {"description": args.instance})
	for i in snaps:
	    print "Snapshot: %s %s %sGB %s %s" % (i.id, i.description, i.volume_size, i.status, i.start_time)
	   

def snapall(args):
    print "snap all"

def create_image(args):
    print "create image"

@arg('--instance', help = 'Instance to snapshot',)

def snapshot(args):
    AWSAKEY,AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    #if len(name[0]) < 1:
    #    val = "''" + dnsdict[env.host_string] + "''"
    #else:
    #	 val = str(name[0])
    if args.instance == "" or args.instance is None:
        print 'You have to pass the name of the instance to snapshot using --instance="name"'
	raise SystemExit(1)
    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % args.instance})
    for i in reservations:
        instance = i.instances[0]
	print instance.id
        volumes = conn.get_all_volumes(filters={'attachment.instance-id': instance.id})
	for i in volumes:
	    #vol = i[7:]
	    print str(i)[7:]
	#print "Freezing filesytem..."
	#run('sudo fsfreeze -f / && sleep 30 && fsfreeze -u /')
	if instance.state == "running":
	    host = instance.ip_address
	    ssh = paramiko.SSHClient()
	    sshkey = _getkeypem()
	    privkey = paramiko.RSAKey.from_private_key_file (sshkey)
	    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
	    ssh.connect(host,username='oskar',pkey=privkey)
	    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sync')
	    print "output", ssh_stdout.read() 
        else:
	    print "Ovivo is stopped or IPs not available"
	    pass
        print instance.tags['Name']
	print "Creating snapshot..."
	snapshot = conn.create_snapshot(str(volumes[0])[7:], args.instance)
	#print "Thawing filesystem..."
        #run('sudo fsfreeze -u /')
        print "Snapshot %s created!" % snapshot


if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([list, snapshot, snapall, create_image])
    p.dispatch()


"""    sys.argv = ['fab', '-f', __file__, ] + sys.argv[1:]
    env.hosts = _gethosts(sys.argv[3:])
    env.user = 'oskar'
    env.key_filename = _getkeypem()
    env.warn_only = True
    fabric.state.output['running'] = False
    for i in env.hosts:
	env.host_string = i
	snapshot(sys.argv[3:])
"""
