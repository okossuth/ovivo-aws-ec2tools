#!/usr/bin/python

""" Python script that uses the boto EC2 libraries for sysadmin operations 
    in Ovivo's Amazon EC2 Infrastructure.

    Oskar Kossuth (c) 2013

    Operations supported:
    - List all running instances  (ec2list)
    - Stop a running instance     (stop)
    - Start a stopped instance    (start)
    - Get all elastic IPs associated to instances   (getalleip)
    - Associate elastic IP to running instance      (asseip)
    - Disassociate elastic IP from running instance (diseip) 
    - Stop Ovivo's Production Instances in order    (stopinfr)
    - Start Ovivo's Production Instances in order   (startinfr)
    
    """

import boto.ec2
import socket
from boto.exception import EC2ResponseError

REGION="eu-west-1"
#REGION="us-east-1"
BACKEND_EIP="54.247.108.93"
CELERY_EIP="46.137.79.20"
MQREDIS_EIP="54.246.99.180"
DBMASTER_EIP="54.247.108.126"
AWSCREDS="./awscreds.txt"


class Color:
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

# Check socket to see if its available and accepting connections
def check_socket(address,port):
    s = socket.socket()
    try:
        s.connect((address,port))
	return True
    except socket.error, e:
        print "Connection to address %s failed.. retrying \n" % address
	return False

# Lists all the Instances in the Amazon account
def ec2list():
    AWSAKEY, AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    reservations = conn.get_all_instances()
    print Color.BOLD + Color.BLUE + "Ovivo Amazon EC2 Instances" + Color.END
    print "--------------------------"
    print
    for i in reservations:
        instance = i.instances[0]
	print "Instance: %s , Name: %s , Type: %s , State: %s " % (instance.id,instance.tags['Name'],instance.instance_type, instance.state)
    print

# Change type of Amazon instance
@arg('--instance',help='Instance to change type',)
@arg('--itype',help='Type to choose',)
def chgtype(args):
    AWSAKEY, AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None or args.itype is None:
        print "Instance name or Instance Type not given. You have to pass the name of the instance using --instance='name'"
	print "or the instance type using --type='name'"
	raise SystemExit(1)
    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % args.instance})
    for i in reservations:
        instance = i.instances[0]
    state = instance.state
    old_type = instance.instance_type
    icod = instance.id
    if state == "stopped":
        print "Changing instance type from %s to %s" % (old_type,args.itype)
	try:
	    conn.modify_instance_attribute(icod,'instanceType',args.itype)
	    print "%s instance type modified to %s" % (args.instance,args.itype)
	except EC2ResponseError:
	    print "An Error occured: Failed to change instance type"
    else:
	print "Instance is running. Please stop it before changing instance type"
	raise SystemExit(1)

     
     

# Stops a particular Amazon Instance
@arg('--instance',help='Instance ID of the instance to stop',)

def stop(args):
    AWSAKEY, AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None:
        print "Instance name not given. You have to pass the name of the instance using --instance='name'"
	raise SystemExit(1)
    print "Stopping instance..."
    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % args.instance})
    for i in reservations:
        instance = i.instances[0]
    if instance.tags['Name'] == "%s" % args.instance :
        conn.stop_instances(instance_ids=[instance.id])
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(instance.id)
	state = reservations[0].instances[0].state
	
    if state=="stopped":
	print "Instance stopped, checks: %s" % reservations[0].instances[0].monitoring_state
    else:
        print "running"

# Starts a particular Amazon Instance
@arg('--instance',help='Instance ID of the instance to start',)
@arg('--eip',help='EIP to add',)

def start(args):

    AWSAKEY, AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None:
        print "Instance name not given. You have to pass the name of the instance using --instance='name'"
	raise SystemExit(1)
    print "Starting instance..."
    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % args.instance})
    for i in reservations:
        instance = i.instances[0]
    if instance.tags['Name'] == "%s" % args.instance :
        conn.start_instances(instance_ids=[instance.id])
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(instance.id)
	state = reservations[0].instances[0].state
    if state == "running":
	print "Instance running, checks: %s" % reservations[0].instances[0].monitoring_state
    else:
	print "Error"
    if args.eip is not None:
        conn.associate_address(instance.id, args.eip)
    

# List all Elastic IPs added to the AWS Account
def getalleip():
    
    AWSAKEY, AWSSKEY = _getcreds()
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
@arg('--instance',help='Instance ID of the instance to add EIP',)
@arg('--eip',help='EIP to add',)

def asseip(args):

    AWSAKEY, AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None:
        print "Instance name not given. You have to pass the name of the instance using --instane='name'"
	raise SystemExit(1)
    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % args.instance})
    for i in reservations:
        instance = i.instances[0]
    if instance.tags['Name'] == "%s" % args.instance :
        icod = conn.get_all_instances(instance.id)
        iname = icod[0].instances[0].tags['Name']
	if args.eip is None:
	    args.eip = conn.allocate_address()
	print args.eip
        conn.associate_address(instance.id, args.eip)
        print "EIP %s added succesfully to Instance %s \n" % (args.eip, iname)


# Disassociate an elastic IP address from a particular Instance
@arg('--instance',help='Instance ID of the instance to disassociate EIP',)
@arg('--eip',help='EIP to disassociate',)

def diseip(args):

    AWSAKEY, AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    if args.instance == "" or args.instance is None:
        print "Instance name not given. You have to pass the name of the instance using --instane='name'"
	raise SystemExit(1)
    reservations = conn.get_all_instances(filters={"tag:Name": "%s" % args.instance})
    for i in reservations:
        instance = i.instances[0]
    if instance.tags['Name'] == "%s" % args.instance :
        icod = conn.get_all_instances(instance.id)
        iname = icod[0].instances[0].tags['Name']
	if args.eip is None:
	    args.eip = instance.ip_address	
        conn.disassociate_address(args.eip,instance.id)
        print "EIP %s disassociated succesfully from Instance %s \n" % (args.eip, iname)

# Stops the Ovivo Production Infrastructure automatically stopping each instance in order
def stopinfr(args):

    AWSAKEY, AWSSKEY = _getcreds()
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
    OUPDATES_EIP = conn.allocate_address()
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

    AWSAKEY, AWSSKEY = _getcreds()
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
    val = check_socket(DBMASTER_EIP, 22)
    while val!= True:
        val = check_socket(DBMASTER_EIP, 22)
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
    val = check_socket(MQREDIS_EIP, 55672)
    while val!= True:
        val = check_socket(MQREDIS_EIP, 55672)
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
    val = check_socket(BACKEND_EIP, 80)
    while val!= True:
        val = check_socket(BACKEND_EIP, 80)
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
    val = check_socket(CELERY_EIP, 80)
    while val!= True:
        val = check_socket(CELERY_EIP, 80)
    
    print "Stopping Ovivo Updates instance..."
    conn.stop_instances(instance_ids=[oupdates_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Ovivo Updates"});
    state = reservations[0].instances[0].state
    while state !="stopped":
        reservations = conn.get_all_instances(filters={"tag:Name": "Ovivo Updates"});
	state = reservations[0].instances[0].state
    for i in reservations:
        instance = i.instances[0]
    conn.release_address(instance.ip_address)
    print "Ovivo Updates instance stopped"
    print
    print "Ovivo AWS Ella Application online!"
    print "Operation completed succesfully"
    

if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([start,stop,ec2list,getalleip,asseip,diseip,chgtype,stopinfr,startinfr])
    p.dispatch()



