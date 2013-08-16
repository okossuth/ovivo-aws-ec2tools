#!/usr/bin/python

""" Python script that uses the boto EC2 libraries for sysadmin operations 
    in Ovivo's Amazon EC2 Infrastructure.

    Oskar Kossuth (c) 2013
    """

REGION="eu-west-1"
AWSAKEY="AVKA"
AWSSKEY="C7F"


BACKEND_EIP="54.247.108.93"
CELERY_EIP="46.137.79.20"
MQREDIS_EIP="54.246.99.180"
DBMASTER_EIP="54.247.108.126"
OUPDATES_EIP="46.137.85.58"


import boto.ec2
import socket

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

def check_socket(address,port):
    s = socket.socket()
    try:
        s.connect((address,port))
	return True
    except socket.error, e:
        print "Connection to address %s failed.. retrying \n" % address
	return False

# Lists all the Instances in the Amazon account
def list():
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    reservations = conn.get_all_instances()
    for i in reservations:
        instance = i.instances[0]
	print "Instance %s , Type: %s , Name: %s , State: %s \n" % (instance.id,instance.instance_type,instance.tags['Name'], instance.state) 

# Stops a particular Amazon Instance
@arg('--instanceid',help='Instance ID of the instance to stop',)

def stop(args):
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    print "Stopping instance..."
    conn.stop_instances(instance_ids=[args.instanceid])
    reservations = conn.get_all_instances(args.instanceid)
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(args.instanceid)
	state = reservations[0].instances[0].state
	
    if state=="stopped":
	print "Instance stopped, checks: %s" % reservations[0].instances[0].monitoring_state
    else:
        print "running"

# Starts a particular Amazon Instance
@arg('--instanceid',help='Instance ID of the instance to start',)

def start(args):

    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    print "Starting instance..."
    conn.start_instances(instance_ids=[args.instanceid])
    reservations = conn.get_all_instances(args.instanceid)
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(args.instanceid)
	state = reservations[0].instances[0].state
    if state == "running":
	print "Instance running, checks: %s" % reservations[0].instances[0].monitoring_state
    else:
	print "Error"

# List all Elastic IPs added to the AWS Account
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

# Associate an elastic IP address to a particular Instance
@arg('--instanceid',help='Instance ID of the instance to add EIP',)
@arg('--eip',help='EIP to add',)

def addeip(args):

    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    icod = conn.get_all_instances(args.instanceid)
    iname = icod[0].instances[0].tags['Name']
    conn.associate_address(args.instanceid, args.eip)
    print "EIP %s added succesfully to Instance %s \n" % (args.eip, iname)


# Disassociate an elastic IP address from a particular Instance
@arg('--instanceid',help='Instance ID of the instance to disassociate EIP',)
@arg('--eip',help='EIP to disassociate',)

def diseip(args):

    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    icod = conn.get_all_instances(args.instanceid)
    iname = icod[0].instances[0].tags['Name']
    conn.disassociate_address(args.eip,args.instanceid)
    print "EIP %s disassociated succesfully from Instance %s \n" % (args.eip, iname)

# Stops the Ovivo Production Infrastructure automatically stopping each instance in order
def stopinfr(args):

    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    ids = conn.get_all_instances()
    for i in ids:
        codinstance = i.instances[0]
	instance = codinstance.id
	if codinstance.tags['Name'] == "Production Celery":
	    celery_id = instance
        elif codinstance.tags['Name'] == "Production Backend":
 	    backend_id = instance
        elif codinstance.tags['Name'] == "Production MQRedis":
	    mqredis_id = instance
	elif codinstance.tags['Name'] == "Production DB Master":
            dbmaster_id = instance
	elif codinstance.tags['Name'] == "Ovivo Updates":
            oupdates_id = instance
	else:
	    pass

    print "Starting Ovivo Updates Instance..."
    conn.start_instances(instance_ids=[oupdates_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Ovivo Updates"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Ovivo Updates"});
	state = reservations[0].instances[0].state

    print "Ovivo Updates Instance is running"
    conn.associate_address(oupdates_id, OUPDATES_EIP)
    print "Checking if Ovivo Updates is ready for connections..."
    val = check_socket(OUPDATES_EIP, 80)
    while val!= True:
        val = check_socket(OUPDATES_EIP, 80)
    
    print "Connected to Ovivo Updates address %s on port %s \n" % (OUPDATES_EIP,"80")
    conn.disassociate_address(OUPDATES_EIP,oupdates_id)
    conn.disassociate_address(BACKEND_EIP,backend_id)
    print "EIP %s disassociated succesfully from Instance %s \n" % (BACKEND_EIP, "Production Backend")
    conn.associate_address(oupdates_id, BACKEND_EIP)
    print "EIP %s added succesfully to Instance %s \n" % (BACKEND_EIP, "Ovivo Updates")
    print "Ovivo Updates is now showing maintenance message..."
    
    print
    print "Stopping Ovivo AWS Infrastructure..."
    print
    print "Stopping Production Celery instance..."
    conn.stop_instances(instance_ids=[celery_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Production Celery"});
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(filters={"tag:Name": "Production Celery"});
	state = reservations[0].instances[0].state
    print "Production Celery instance stopped"
    print
    print "Stopping Production Backend instance..."
    conn.stop_instances(instance_ids=[backend_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Production Backend"});
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(filters={"tag:Name": "Production Backend"});
	state = reservations[0].instances[0].state
    print "Production Backend instance stopped"
    print
    print "Stopping Production MQRedis instance..."
    conn.stop_instances(instance_ids=[mqredis_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Production MQRedis"});
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(filters={"tag:Name": "Production MQRedis"});
	state = reservations[0].instances[0].state
    print "Production MQRedis instance stopped"
    print
    print "Stopping Production DB Master instance..."
    conn.stop_instances(instance_ids=[dbmaster_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Production DB Master"});
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(filters={"tag:Name": "Production DB Master"});
	state = reservations[0].instances[0].state
    print "Production DB Master instance stopped"
    print
    print "Ovivo AWS Infrastructure stopped"


# Starts the Ovivo Production Infrastructure automatically launching each instance in order
def startinfr(args):

    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    ids = conn.get_all_instances()
    for i in ids:
        codinstance = i.instances[0]
	instance = codinstance.id
	if codinstance.tags['Name'] == "Production Celery":
	    celery_id = instance
        elif codinstance.tags['Name'] == "Production Backend":
 	    backend_id = instance
        elif codinstance.tags['Name'] == "Production MQRedis":
	    mqredis_id = instance
	elif codinstance.tags['Name'] == "Production DB Master":
            dbmaster_id = instance
	elif codinstance.tags['Name'] == "Ovivo Updates":
            oupdates_id = instance
	else:
	    pass

    print "Starting Ovivo AWS Infrastructure..."
    print
    print "Starting Production DB Master instance..."
    conn.start_instances(instance_ids=[dbmaster_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Production DB Master"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Production DB Master"});
	state = reservations[0].instances[0].state
    conn.associate_address(dbmaster_id, DBMASTER_EIP)
    print "EIP %s added succesfully to Instance %s \n" % (DBMASTER_EIP, "Production DB Master")
    print "Production DB Master instance running"
    print
    
    print "Starting Production MQRedis instance..."
    conn.start_instances(instance_ids=[mqredis_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Production MQRedis"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Production MQRedis"});
	state = reservations[0].instances[0].state
    conn.associate_address(mqredis_id, MQREDIS_EIP)
    print "EIP %s added succesfully to Instance %s \n" % (MQREDIS_EIP, "Production MQRedis")
    print "Production MQRedis instance running"
    print
    
    print "Starting Production Backend instance..."
    conn.start_instances(instance_ids=[backend_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Production Backend"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Production Backend"});
	state = reservations[0].instances[0].state
    conn.disassociate_address(BACKEND_EIP,oupdates_id)
    print "EIP %s disassociated succesfully from Instance %s \n" % (BACKEND_EIP, "Ovivo Updates")
    conn.associate_address(backend_id, BACKEND_EIP)
    print "EIP %s added succesfully to Instance %s \n" % (BACKEND_EIP, "Production Backend")
    print "Production Backend instance running"
    print
    
    print "Starting Production Celery instance..."
    conn.start_instances(instance_ids=[celery_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Production Celery"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Production Celery"});
	state = reservations[0].instances[0].state
    conn.associate_address(celery_id, CELERY_EIP)
    print "EIP %s added succesfully to Instance %s \n" % (CELERY_EIP, "Production Celery")
    print "Production Celery instance running"
    print "Ovivo AWS Infrastructure started"
    
    print "Stopping Ovivo Updates instance..."
    conn.stop_instances(instance_ids=[oupdates_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Ovivo Updates"});
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(filters={"tag:Name": "Ovivo Updates"});
	state = reservations[0].instances[0].state
    print "Ovivo Updates instance stopped"
    print
    print "Ovivo AWS Ella Application should be online soon.."
    val = check_socket(BACKEND_EIP, 80)
    while val!= True:
        val = check_socket(BACKEND_EIP, 80)
    print "Ovivo AWS Ella Application online!"
    print "Operation completed succesfully"
    

if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([start,stop,list,getalleip,addeip,diseip,stopinfr,startinfr])
    p.dispatch()



