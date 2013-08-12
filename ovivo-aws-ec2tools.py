#!/usr/bin/python

""" Python script that uses the boto EC2 libraries for sysadmin operations 
    in Ovivo's Amazon EC2 Infrastructure.
    """

REGION="eu-west-1"
AWSAKEY=""
AWSSKEY=""

import boto.ec2


def ensure_the_library_is_installed(name):
	    print 'You have to install the python library "%s" in order to use ' \
		  'this script' % name
	    print 
	    print 'Just type: sudo pip install %s and you should be fine :)' % name
	    raise SystemExit(1)

try:
    from argh import *
except ImportError:
    ensure_the_library_is_installed('argh')


def list():
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    reservations = conn.get_all_instances()
    for i in reservations:
        instance = i.instances[0]
	print "Instance %s , Type: %s , Name: %s , State: %s \n" % (i.instances,instance.instance_type,instance.tags['Name'], instance.state) 

@arg('--instanceid',help='Instance ID of the instance to stop',)

def stop(args):
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    print "Stopping instance..."
    conn.stop_instances(instance_ids=[args.instanceid])
    reservations = conn.get_all_instances(filters={"tag:Name": "Redirect_Updates"});
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(filters={"tag:Name": "Redirect_Updates"});
        state = reservations[0].instances[0].state
	
    if state=="stopped":
	print "Instance stopped, checks: %s" % reservations[0].instances[0].monitoring_state
    else:
        print "running"

@arg('--instanceid',help='Instance ID of the instance to start',)

def start(args):

    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    print "Starting instance..."
    conn.start_instances(instance_ids=[args.instanceid])
    reservations = conn.get_all_instances(filters={"tag:Name": "Redirect_Updates"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Redirect_Updates"});
        state = reservations[0].instances[0].state
    if state == "running":
	print "Instance running, checks: %s" % reservations[0].instances[0].monitoring_state
    else:
	print "Error"

def getalleip():
    
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    eips = conn.get_all_addresses()
    for i in eips:
	if i.instance_id is not None:
	    if len(i.instance_id) > 0:	
	        icod = conn.get_all_instances(i.instance_id)
	        iname = icod[0].instances[0].tags['Name']
                print "IP: %s ---> Instance: %s " % (i,iname)
            else:
                print "IP: %s ---> Not associated to any Instance " % (i)
        else:
            print "IP: %s ---> Not associated to any Instance " % (i)

@arg('--instanceid',help='Instance ID of the instance to add EIP',)
@arg('--eip',help='EIP to add',)

def addeip(args):

    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    icod = conn.get_all_instances(args.instanceid)
    iname = icod[0].instances[0].tags['Name']
    conn.associate_address(args.instanceid, args.eip)
    print "EIP %s added succesfully to Instance %s \n" % (args.eip, iname)


if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([start,stop,list,getalleip,addeip])
    p.dispatch()


















