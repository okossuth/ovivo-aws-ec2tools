#!/usr/bin/python

import boto
import os
import subprocess
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError
from boto.exception import S3CreateError

# AWS Credentials retrieval using encrypted C shared library ##

import os, pwd, grp
f=open('/tmp/.uwsgi.lock', 'w+')
f.close()
uid = pwd.getpwnam('jonathan').pw_uid
gid = grp.getgrnam('jonathan').gr_gid
os.chown('/tmp/.uwsgi.lock', uid, gid)

import ctypes
from ctypes import CDLL

pylibc = CDLL("/home/ella/Ella/ella/awsenckeys.so")
pylibc.awsakey.restype = ctypes.c_char_p
pylibc.awsskey.restype = ctypes.c_char_p

AWSAKEY = pylibc.awsakey()
AWSSKEY = pylibc.awsskey()

######################################################
DEFAULT_BUCKET = "ella-db"

class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

conn = S3Connection(AWSAKEY, AWSSKEY)

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

def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
	size = '%.2fT' % terabytes
    elif bytes >= 1073741824:
	gigabytes = bytes / 1073741824
        size = '%.2fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
	size = '%.2fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
	size = '%.2fK' % kilobytes
    else:
	size = '%.2f bytes' % bytes
    return size

def progress_for(action):
    def progress_callback(transferred, size, up=True):
        transferred, size = map(convert_bytes, (transferred, size))
	print '{2}-> {3} {0} of {1}      '.format(transferred,size,up and '\033[A' or '', action,)
    return progress_callback


@arg('--bucket', default=DEFAULT_BUCKET,help='The name of the S3 bucket to list dumps from', )
def lsdump(args):
    a = []
    bucket =  conn.get_bucket(args.bucket)
    for key in bucket.list():
        a.append(key)
    a = sorted(a, key=lambda k: k.last_modified)
    print
    print Color.BLUE + "Available Database Backups on S3"
    print "---------------------------------"
    for key in a:
        print Color.GREEN + "%s, %s \n" % (key.name, key.last_modified)
    print Color.END


@arg('--bucket', default=DEFAULT_BUCKET, help='The name of the S3 bucket to download dumps from',)
@arg('--dbdump', help='Database dump to retrieve',)
def get(args):
    fp = "/tmp/"
    bucket =  conn.get_bucket(args.bucket)
    dump = args.dbdump
    k = Key(bucket)
    k.key = dump
    fp = fp + k.name
    print (Color.GREEN + "Retrieving database dump %s" + Color.END) % fp
    progress_callback = progress_for('downloading')
    progress_callback(0, 0, False)
    k.get_contents_to_filename(fp, cb=progress_callback)
    print Color.CYAN + "Download complete!"
    print  Color.YELLOW + " decompressing database dump..."
    cmd = "tar xfvs %s" % fp
    print "tar xfvz %s" % fp
    subprocess.call(cmd, shell=True)
    print "Importing database dump into ella database..."
    sqlfp = k.name[:-17]  + "sql"
    cmd = "psql -U jonathan -d ella -f %s " % sqlfp
    print ("psql -U jonathan -d ella -f %s ") % sqlfp
    subprocess.call(cmd, shell=True)
    print "Import finished"
    print "Removing compressed dump and *.sql files..."
    os.remove(fp)
    dir = os.getcwd()
    os.remove(dir+"/"+sqlfp)
    os.remove(dir+"/ella-pgglobals.sql")
    print "Operation completed succesfully"
    print 

if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([lsdump, get ])
    p.dispatch()





