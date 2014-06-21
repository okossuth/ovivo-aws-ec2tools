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
REGIONB="us-east-1"
VPCID_EUWEST="sg-cb6764bf"
VPCID_USEAST="sg-4a43ca22"
AWSCREDS="./awscreds.txt"
DBMASTER_TEST="i-803ea5cc"
DBMASTER_ID = "Production DB Master"
MQREDIS_ID = "Production MQRedis"
BACKEND_ID = "Production Backend"
CELERY_ID = "Production Celery"
CELERYLP_ID = "Production CeleryLowPrio"
CELERYSMS_ID = "Production CeleryMessages"
NUM_SNAPS = 2

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

# Rotate Snapshots
@arg('--region', default=REGION, help = 'Region to use, eu-west-1 or us-east-1',)
def rotatesnap(args, *foo):
    temp = []
    temp_extra = []
    db_sem = 0
    #AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    try:
        if args.region == "" or args.region is None:
	    region = args
	    print region
	else:
	    region = args.region
    except AttributeError:    
	region = args
	print "is %s" % region
    conn = boto.ec2.connect_to_region(region,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    snaps = conn.get_all_snapshots(filters = {"description": args})
    for i in snaps:
        print "Snapshot: %s %s %sGB %s %s" % (i.id, i.description, i.volume_size, i.status, i.start_time)
	if i.volume_size != 8:
	    print "Snapshot is from an extra volume"
	    db_sem = 1
	    temp_extra.append(i.id)
	else:
            print "Snapshot is from normal volume"
            temp.append(i.id)
    if len(temp) < NUM_SNAPS:
            print "There is only one snapshot for this instance. Aborting rotate..."
    else:    	
        temp.pop()
        for i in temp:
	    name = i.encode('ascii')
            try:
                conn.delete_snapshot(name)
	    except EC2ResponseError:
	        print "Error deleting snapshot"
    if len(temp_extra) < NUM_SNAPS and db_sem == 1:
        print "There is only one DB snapshot for this instance. Aborting rotate..."
    elif len(temp_extra) >= NUM_SNAPS and db_sem == 1:    	
        temp_extra.pop()
        for i in temp_extra:
	    name = i.encode('ascii')
            try:
                conn.delete_snapshot(name)
	    except EC2ResponseError:
	        print "Error deleting snapshot"
    
    else:
        pass

# List all snapshots in Amazon account or particular instance
@arg('--instance', help = 'Instance to list snapshots',)
@arg('--region', default=REGION, help = 'Region to use, eu-west-1 or us-east-1',)
def snaplist(args, ):
    #AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(args.region,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None:
        print color.BLUE + 'Listing all Ovivo snapshots ' + color.END
	print '------------------------------ \n'
        snaps = conn.get_all_snapshots(owner=AWSACCID)
        for i in snaps:
	    print "Snapshot: %s %s %sGB %s %s" % (i.id, i.description, i.volume_size, i.status, i.start_time)
    else:
	snaps = conn.get_all_snapshots(filters = {"description": args.instance})
	for i in snaps:
	    print "Snapshot: %s %s %sGB %s %s" % (i.id, i.description, i.volume_size, i.status, i.start_time)
    print	   


# Copy snapshots from one region to another
@arg('--snapshotid', help = 'Snapshot ID of the snapshot to copy',)
def cpsnap(args):
    temp = []
    #AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGIONB,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.snapshotid == "" or args.snapshotid is None:
        print 'You have to pass the snapshot ID of the snapshot to be copied with --snapshotid="snapid"'
	raise SystemExit(1)
    else:
	try:
	    print ""
            sconn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
	    if args.snapshotid != "prodbase" and  args.snapshotid !="prodcelery":
	        snaps = sconn.get_all_snapshots(snapshot_ids=[args.snapshotid])
	        for i in snaps:
	            descr = "[Copied from %s] %s" % (REGION, i.description)
	        conn.copy_snapshot(REGION, args.snapshotid, description=descr)
	        print "Snapshot %s copied successfully to region %s" % (args.snapshotid, REGIONB)
	    else:
		prodlist = []
		if args.snapshotid == "prodbase":
		    prodlist.extend((DBMASTER_ID, MQREDIS_ID, BACKEND_ID))
	        else:
		    prodlist.extend((CELERY_ID, CELERYLP_ID, CELERYSMS_ID))
		for i in prodlist:
		    print i
		    snaps = sconn.get_all_snapshots(filters = {"description": i})
	            for i in snaps:
	                if i.volume_size != 8:
	                    print "Snapshot is from an extra volume"
	                else:
                            print "Snapshot is from normal volume"
                            temp.append(i.id)
                    if len(temp) > 1:
                        snap = temp.pop()   
		    else:
			snap = temp
	            descr = "[Copied from %s] %s" % (REGION, i.description)
		    try:
		        conn.copy_snapshot(REGION, snap, description=descr)
	                print "Snapshot %s copied successfully to region %s" % (snap, REGIONB)
	            except EC2ResponseError:
                        print "Error when trying to copy snapshot %s" % snap
		    temp[:] = []
	except EC2ResponseError:
            print "Error when trying to copy snapshot %s" % args.snapshotid

# Deletes all snapshots from an instance
@arg('--instance', help = 'Instance name to delete snapshots from',)
@arg('--region', default=REGION, help = 'Region to use, eu-west-1 or us-east-1',)
def delsnapall(args):
    #AWSAKEY,AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(args.region,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None:
        print 'You have to pass the instance name of the instance to delete snapshots from with --instance="instance_name"'
	raise SystemExit(1)
    else:
        snaps = conn.get_all_snapshots(filters = {"description": args.instance})
	if len(snaps) == 0:
	    print "No snapshots available or Instance ID is wrong. Exiting..."
	    raise SystemExit(1)
        for i in snaps:
	    try:
	        print ""
	        conn.delete_snapshot(i.id)
	        print "Snapshot deleted successfully"
	    except EC2ResponseError:
                print "Error when trying to delete snapshot %s" % i.id


# Delete a particular snapshot 
@arg('--snapshotid', help = 'Snapshot ID of the snapshot to delete',)
@arg('--region', default=REGION, help = 'Region to use, eu-west-1 or us-east-1',)
def delsnap(args):
    #AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(args.region,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.snapshotid == "" or args.snapshotid is None:
        print 'You have to pass the snapshot ID of the snapshot to be deleted with --snapshotid="snapid"'
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
    #AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.imageid == "" or args.imageid is None:
        print 'You have to pass the image ID of the image to be deleted with --imageid="imgid"'
	raise SystemExit(1)
    else:
	try:
	    ret = conn.deregister_image(args.imageid)
	    print "Image %s deleted successfully" % args.imageid
	except EC2ResponseError:
	    print "Error when trying to delete image %s" % args.imageid

# List all images of Amazon account
def imagelist(args):
    #AWSAKEY,AWSSKEY = _getcreds()
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
    #AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.snapshotid == "" or args.snapshotid is None:
        print 'You have to pass the snapshot ID used to create the image with --snapshotid="snapid"'
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

# Launch Amazon image from image
@arg('--imageid', help = 'Image ID to launch image from',)
@arg('--itype'  , help = 'Type of Amazon instance to launch',)
def launchimg(args):
    #AWSAKEY,AWSSKEY = _getcreds()
    AWSACCID = _getawsaccid()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.itype == "" or args.imageid is None:
        print 'You have to pass the type of instance used to launch the image with --itype="itype"'
	raise SystemExit(1)
    if args.imageid == "" or args.imageid is None:
        print 'You have to pass the image ID used to launch the image with --imageid="imgid"'
	raise SystemExit(1)
    else:
	try:
            ret=conn.run_instances(args.imageid,min_count=1,max_count=1,instance_type=args.itype, \
		    security_groups=['default'],kernel_id='aki-71665e05')
	    instance = ret.instances[0]
	    status = instance.update()
	    while status == 'pending':
	        status = instance.update()
            if status == 'running':
	        instance.add_tag("Name","Empty")
	    print "Image launch successful"
	except EC2ResponseError:
	    print "Image launch error"

# Create snapshot from a particular Amazon instance
@arg('--instance', help = 'Instance to snapshot',)
@arg('--region', default=REGION, help = 'Region to use, eu-west-1 or us-east-1',)
def snapshot(args, *foo):
    #AWSAKEY,AWSSKEY = _getcreds()
    try:
        if args.region == "" or args.region is None:
	    region = args
	    print region
	else:
	    region = args.region
    except AttributeError:    
	region = args
	print "is %s" % region
    
    conn = boto.ec2.connect_to_region(region,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    try:
        if args.instance == "" or args.instance is None:
            print 'You have to pass the name of the instance to snapshot using --instance="name"'
	    raise SystemExit(1)
    except AttributeError:    
	print foo 
    if  len(foo) == 0:
        name = args.instance
    else:
	name = foo[0].encode('ascii')
    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % name})
    if len(reservations) == 0:
        print "Name of Instance incorrect or Instance doesnt exist... Aborting!"
	raise SystemExit(1)
    for i in reservations:
        instance = i.instances[0]
	print instance.id
        volumes = conn.get_all_volumes(filters={'attachment.instance-id': instance.id})
	for i in volumes:
	    print str(i)[7:]
        print instance.tags['Name']
	print "Creating snapshot..."
	if instance.state == "running" and region != "us-east-1":
	    host = instance.ip_address
	    ssh = paramiko.SSHClient()
	    sshkey = _getkeypem()
	    privkey = paramiko.RSAKey.from_private_key_file (sshkey)
	    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
	    ssh.connect(host,username='oskar',pkey=privkey)
	    chan = ssh.get_transport().open_session()
	    chan.get_pty()
	    if name == "Production DB Master":
		print "Freezing database filesystem..."
	        chan.exec_command('sudo fsfreeze -f /var/lib/pgsql9 ; touch /tmp/kkk')
	        for i in volumes:
	            snapshot = conn.create_snapshot(str(i)[7:], name)
                    print "Snapshot %s created!" % snapshot
	        print "Thawing database filesystem..."
	        chan = ssh.get_transport().open_session()
	        chan.get_pty()
	        chan.exec_command('sudo fsfreeze -u /var/lib/pgsql9 ; touch /tmp/roor')
	    else:    
	        chan.exec_command('sudo sync')
	        for i in volumes:
	            snapshot = conn.create_snapshot(str(i)[7:], name)
                    print "Snapshot %s created!" % snapshot
	else:    
	    print "Ovivo instance is stopped, IPs not available or Region is US-EAST-1"
	    for i in volumes:
	        snapshot = conn.create_snapshot(str(i)[7:], name)
                print "Snapshot %s created!" % snapshot
            
        print "Snapshot creation process finished..." 

# Snapshot all instances on Amazon account
@arg('--region', default=REGION, help = 'Region to use, eu-west-1 or us-east-1',)
def snapall(args):
    #AWSAKEY,AWSSKEY = _getcreds()
    if args.region == "" or args.region is None:
        args.region = REGION
    conn = boto.ec2.connect_to_region(args.region,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    reservations = conn.get_all_instances()
    for i in reservations:
       instance = i.instances[0]
       sec_instance = instance.groups[0]
       if sec_instance.id == VPCID_EUWEST or sec_instance == VPCID_USEAST and instance.id != DBMASTER_TEST  :
           param = instance.tags['Name']
           rotatesnap(args.region, param)
           snapshot(args.region, param)
       else:
	   pass


if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([snaplist, snapshot, snapall, create_image, imagelist, delimage, delsnap, cpsnap, launchimg, delsnapall])
    p.dispatch()

