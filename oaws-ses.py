#!/usr/bin/python

import os
from boto.ses.connection import SESConnection

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

conn = SESConnection(AWSAKEY, AWSSKEY)
data =  conn.get_send_statistics()
data =  data["GetSendStatisticsResponse"]["GetSendStatisticsResult"]
for i in data["SendDataPoints"]:
    print "Complaints: %s" % i["Complaints"]
    print "Timestamp: %s" % i["Timestamp"]
    print "DeliveryAttempts: %s" % i["DeliveryAttempts"]
    print "Bounces: %s" % i["Bounces"]
    print "Rejects: %s" % i["Rejects"]
				            
