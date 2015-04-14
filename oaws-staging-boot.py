#!/usr/bin/python

""" Python script that uses the boto EC2 libraries to start/stop staging setup 
    in Ovivo's Amazon EC2 Infrastructure.

    Oskar Kossuth (c) 2015

    Operations supported:
    - Stop Ovivo's staging Instances in order    (stop)
    - Start Ovivo's staging Instances in order   (start)
    
    """

import boto.ec2
import socket
import time
from boto.exception import EC2ResponseError

REGION="eu-west-1"
BACKEND_EIP="52.16.255.78"
CELERY_EIP="54.154.108.115"
MQREDIS_EIP="54.77.33.83"
DBMASTER_EIP="54.77.148.34"
CELERYMSG_EIP="54.76.37.0"
CELERYLP_EIP="54.77.146.112"
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


# Stops the Ovivo Staging Infrastructure automatically stopping each instance in order
def stop(args):

    AWSAKEY, AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    ids = conn.get_all_instances()
    for i in ids:
        codinstance = i.instances[0]
	instance = codinstance.id
	if codinstance.tags['Name'] == "Staging Celery":
	    celery_id = instance
        elif codinstance.tags['Name'] == "Staging ProdBackend":
 	    backend_id = instance
        elif codinstance.tags['Name'] == "Staging MQRedis":
	    mqredis_id = instance
	elif codinstance.tags['Name'] == "Staging DBMaster":
            dbmaster_id = instance
	elif codinstance.tags['Name'] == "Staging CeleryMessages": 
            celerymsg_id = instance
	elif codinstance.tags['Name'] == "Staging CeleryLowPrio":
            celerylp_id = instance
	else:
	    pass

    print
    print "Stopping Ovivo AWS Staging Infrastructure..."
    print
    print "Stopping Staging CeleryLowPrio instance..."
    conn.stop_instances(instance_ids=[celerylp_id])
    print "Stopping Staging CeleryMessages instance..."
    conn.stop_instances(instance_ids=[celerymsg_id])
    print "Stopping Staging Celery instance..."
    conn.stop_instances(instance_ids=[celery_id])
    print "Stopping Staging Backend instance..."
    conn.stop_instances(instance_ids=[backend_id])
    print "Stopping Staging MQRedis instance..."
    conn.stop_instances(instance_ids=[mqredis_id])
    print "Stopping Staging DB Master instance..."
    conn.stop_instances(instance_ids=[dbmaster_id])
    print "Checking if the Staging infrastructure is completely halted..."
    
    ids = conn.get_all_instances()
    for i in ids:
        codinstance = i.instances[0]
	if codinstance.tags['Name'] == "Staging Celery" or codinstance.tags['Name'] == "Staging ProdBackend" or \
           codinstance.tags['Name'] == "Staging CeleryLowPrio" or codinstance.tags['Name'] == "Staging CeleryMessages" or codinstance.tags['Name'] == "Staging DBMaster" or codinstance.tags['Name'] == "Staging MQRedis": 
            state = codinstance.state
            if state !="stopped":
	        print "Instance %s state is still %s, waiting to be completely stopped..." % (codinstance.tags['Name'],codinstance.state)
            while state !="stopped":
                res = conn.get_all_instances(codinstance.id);
	        state = res[0].instances[0].state
	        print "Instance %s state is %s" % (codinstance.tags['Name'],codinstance.state)
        else:
	    pass
    print
    print "Ovivo AWS Infrastructure stopped"


# Starts the Ovivo Staging Infrastructure automatically launching each instance in order
def start(args):

    AWSAKEY, AWSSKEY = _getcreds()
    conn = boto.ec2.connect_to_region(REGION,aws_access_key_id=AWSAKEY,aws_secret_access_key=AWSSKEY)
    ids = conn.get_all_instances()
    for i in ids:
        codinstance = i.instances[0]
	instance = codinstance.id
	if codinstance.tags['Name'] == "Staging Celery":
	    celery_id = instance
        elif codinstance.tags['Name'] == "Staging ProdBackend":
 	    backend_id = instance
        elif codinstance.tags['Name'] == "Staging MQRedis":
	    mqredis_id = instance
	elif codinstance.tags['Name'] == "Staging DBMaster":
            dbmaster_id = instance
	elif codinstance.tags['Name'] == "Staging CeleryMessages":
            celerymsg_id = instance
	elif codinstance.tags['Name'] == "Staging CeleryLowPrio":
            celerylp_id = instance
	else:
	    pass

    print "Starting Ovivo AWS Infrastructure..."
    print
    print "Starting Staging DBMaster instance..."
    conn.start_instances(instance_ids=[dbmaster_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Staging DBMaster"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Staging DBMaster"});
	state = reservations[0].instances[0].state
    eips = conn.get_all_addresses()
    for i in eips:
        icod = conn.get_all_instances(i.instance_id)
        iname = icod[0].instances[0].tags['Name']
	if iname == "Staging DBMaster":
	    conn.associate_address(i.instance_id, None, i.allocation_id )
	else:													                                 pass
    
    print "EIP %s added succesfully to Instance %s \n" % (DBMASTER_EIP, "Staging DBMaster")
    val = check_socket(DBMASTER_EIP, 22)
    while val!= True:
        val = check_socket(DBMASTER_EIP, 22)
	time.sleep(10)
    print "Staging DBMaster instance running"
    print
    
    print "Starting Staging MQRedis instance..."
    conn.start_instances(instance_ids=[mqredis_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Staging MQRedis"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Staging MQRedis"});
	state = reservations[0].instances[0].state
    for i in eips:
        icod = conn.get_all_instances(i.instance_id)
        iname = icod[0].instances[0].tags['Name']
	if iname == "Staging MQRedis":
	    conn.associate_address(i.instance_id, None, i.allocation_id )
	else:													                                 pass

    print "EIP %s added succesfully to Instance %s \n" % (MQREDIS_EIP, "Staging MQRedis")
    val = check_socket(MQREDIS_EIP, 55672)
    while val!= True:
        val = check_socket(MQREDIS_EIP, 55672)
	time.sleep(10)
    print "Staging MQRedis instance running"
    print
    
    print "Starting Staging ProdBackend instance..."
    conn.start_instances(instance_ids=[backend_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Staging ProdBackend"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Staging ProdBackend"});
	state = reservations[0].instances[0].state
    for i in eips:
        icod = conn.get_all_instances(i.instance_id)
        iname = icod[0].instances[0].tags['Name']
	if iname == "Staging ProdBackend":
	    conn.associate_address(i.instance_id, None, i.allocation_id )
	else:													                                 pass

    print "EIP %s added succesfully to Instance %s \n" % (BACKEND_EIP, "Staging ProdBackend")
    #BACKEND_DNS = reservations[0].instances[0].public_dns_name
    val = check_socket(BACKEND_EIP, 80)
    while val!= True:
        val = check_socket(BACKEND_EIP, 80)
	time.sleep(10)
    print "Staging ProdBackend instance running"
    print
    
    print "Starting Staging Celery instance..."
    conn.start_instances(instance_ids=[celery_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Staging Celery"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Staging Celery"});
	state = reservations[0].instances[0].state
    for i in eips:
        icod = conn.get_all_instances(i.instance_id)
        iname = icod[0].instances[0].tags['Name']
	if iname == "Staging Celery":
	    conn.associate_address(i.instance_id, None, i.allocation_id )
	else:													                                 pass

    print "EIP %s added succesfully to Instance %s \n" % (CELERY_EIP, "Staging Celery")
    print "Staging Celery instance running"
    
    print "Starting Staging CeleryMessages instance..."
    conn.start_instances(instance_ids=[celerymsg_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Staging CeleryMessages"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Staging CeleryMessages"});
	state = reservations[0].instances[0].state
    for i in eips:
        icod = conn.get_all_instances(i.instance_id)
        iname = icod[0].instances[0].tags['Name']
	if iname == "Staging CeleryMessages":
	    conn.associate_address(i.instance_id, None, i.allocation_id )
	else:													                                 pass

    print "EIP %s added succesfully to Instance %s \n" % (CELERYMSG_EIP, "Staging CeleryMessages")
    print "Staging CeleryMessages instance running"
    
    print "Starting Staging CeleryLowPrio instance..."
    conn.start_instances(instance_ids=[celerylp_id])
    reservations = conn.get_all_instances(filters={"tag:Name": "Staging CeleryLowPrio"});
    state = reservations[0].instances[0].state
    while state !="running":
        reservations = conn.get_all_instances(filters={"tag:Name": "Staging CeleryLowPrio"});
	state = reservations[0].instances[0].state
    for i in eips:
        icod = conn.get_all_instances(i.instance_id)
        iname = icod[0].instances[0].tags['Name']
	if iname == "Staging CeleryLowPrio":
	    conn.associate_address(i.instance_id, None, i.allocation_id )
	else:													                                 pass

    print "EIP %s added succesfully to Instance %s \n" % (CELERYLP_EIP, "Staging CeleryLowPrio")
    print "Staging CeleryLowPrio instance running"
    
    val = check_socket(CELERY_EIP, 80)
    while val!= True:
        val = check_socket(CELERY_EIP, 80)
	time.sleep(10)
    
    
    print
    print "Ovivo AWS Staging Ella Application online!"
    print "Operation completed succesfully"
    

if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([start,stop])
    p.dispatch()



