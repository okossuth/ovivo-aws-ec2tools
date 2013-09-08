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
from boto.ec2.blockdevicemapping import EBSBlockDeviceType, BlockDeviceMapping
from boto.exception import EC2ResponseError

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

# List all snapshots in Amazon account or particular instance
@arg('--instance', help = 'Instance to list snapshots',)
def snaplist(args):
    AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None:
        print 'Listing all Ovivo snapshots'
        snaps = conn.get_all_snapshots(owner=AWSACCID)
        for i in snaps:
	    print "Snapshot: %s %s %sGB %s %s" % (i.id, i.description, i.volume_size, i.status, i.start_time)
    else:
	snaps = conn.get_all_snapshots(filters = {"description": args.instance})
	for i in snaps:
	    print "Snapshot: %s %s %sGB %s %s" % (i.id, i.description, i.volume_size, i.status, i.start_time)
    print	   

# Snapshot all instances on Amazon account
def snapall(args):
    AWSAKEY,AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    print "snap all"

# Delete a particular snapshot 
@arg('--snapshotid', help = 'Snapshot ID of the snapshot to delete',)
def delsnap(args):
    AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.snapshotid == "" or args.snapshotid is None:
        print "You have to pass the snapshot ID of the snapshot to be deleted"
	raise SystemExit(1)
    else:
	try:
	    print ""
	    conn.delete_snapshot(args.snapshotid)
	    print "Snapshot deleted successfully"
	except EC2ResponseError:
            print "Error when trying to delete snapshot %s" % args.snapshotid

# Delete a particular Amazon image
@arg('--imageid', help = 'Image ID of the image to delete',)
def delimage(args):
    AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.imageid == "" or args.imageid is None:
        print "You have to pass the image ID of the image to be deleted"
	raise SystemExit(1)
    else:
	try:
	    ret = conn.deregister_image(args.imageid)
	    print "Image %s deleted successfuly" % args.imageid
	except EC2ResponseError:
	    print "Error when trying to delete image %s" % args.imageid

# List all images of Amazon account
def imagelist(args):
    AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    images = conn.get_all_images(owners=AWSACCID)
    print "Images available from Ovivo"
    print "------------------------------------"
    print
    for i in images:
        print "%s --- %s | %s | %s | %s" % (i.id,i.description,i.name,i.architecture,i.kernel_id)	    
    print

# Create Amazon image from snapshot
@arg('--snapshotid', help = 'Snapshot ID to create image from',)
def create_image(args):
    AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.snapshotid == "" or args.snapshotid is None:
        print "You have to pass the snapshot ID used to create the image with --snapshotid"
	raise SystemExit(1)
    else:
	namei = raw_input("Enter name of image: ")
	descr = raw_input("Enter a description for image: ")
        print "Creating image from snapshot %s ..." % args.snapshotid
	ebs = EBSBlockDeviceType()
	ebs.snapshot_id = args.snapshotid
	block_map = BlockDeviceMapping()
	block_map['/dev/sda1'] = ebs
	try:
            ret = conn.register_image(name=namei,description=descr,architecture='x86_64',kernel_id='aki-71665e05',\
			root_device_name='/dev/sda1', block_device_map=block_map)
	    print "Image creation successful"
	except EC2ResponseError:
	    print "Image creation error"

# Create snapshot from a particular Amazon instance
@arg('--instance', help = 'Instance to snapshot',)
def snapshot(args):
    AWSAKEY,AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
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
    p.add_commands([snaplist, snapshot, snapall, create_image, imagelist, delimage, delsnap])
    p.dispatch()

