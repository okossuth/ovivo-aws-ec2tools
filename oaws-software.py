#!/usr/bin/python

"""
This script checks for updates to some software and libraries used by the ella app
that are not updates via Amazon's YUM repositories. Examples of these are:
	- Celery
	- django-celery
	- uWGSI
	- uWSGItop
	- Supervisor
	- Other software listed by `pip freeze`
"""

import os
from mechanize import Browser

AWSCREDS = "./awscreds.txt"
BACKEND = "54.247.108.93"
CELERY = "46.137.79.20"

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

def ensure_library_check(name):
    print 'The library %s is not installed \n' % name
    print 'Please install it by executing pip install %s' % name
    raise SystemExit(1)

try:
    from argh import *
except ImportError:
    ensure_library_check('argh')

try:
    import paramiko
except ImportError:
    ensure_library_check('paramiko')

def _getkeypem():
    f = open(AWSCREDS, "r")
    c = f.readlines()
    f.seek(0)
    aws_keypem = c[2]
    for i in range(len(aws_keypem)):
        if aws_keypem[i] == "=":
            pos = i
    return aws_keypem[pos+2:-2]

def host(server, cmd, user):
    hostip = server
    ssh = paramiko.SSHClient()
    sshkey = _getkeypem()
    privkey = paramiko.RSAKey.from_private_key_file (sshkey)
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(hostip,username=user,pkey=privkey)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    val = ssh_stdout.read()
    print "Installed version: %s" % val
    return val
   
def checksw():
    br = Browser()
    libversion = host(BACKEND, 'source /home/ella/Ella/venv/bin/activate; pip freeze | grep librab', 'ella')
    br.open("https://pypi.python.org/pypi/librabbitmq")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/librabbitmq/' in i:
	    version = i[-9:-4]
    libversion = libversion[13:]
    if not version in libversion:
        print (color.RED + "New version of librabbitmq available: %s !!\n" + color.END)  % version
    else:
	print "librabbitmq version %s up to date \n" % version

    libversion = host(CELERY, 'source /home/ella/Ella/venv/bin/activate; pip freeze | grep ^celery', 'ella')
    br.open("https://pypi.python.org/pypi/celery")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/celery/' in i:
	    version = i[-10:-4]
    libversion = libversion[8:]
    if not version in libversion:
        print (color.RED + "New version of celery available: %s \n!!" + color.END)  % version
    else:
	print "celery version %s up to date \n" % version
    
    libversion = host(CELERY, 'source /home/ella/Ella/venv/bin/activate; pip freeze | grep django-celery', 'ella')
    br.open("https://pypi.python.org/pypi/django-celery")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/django-celery/' in i:
	    version = i[-10:-4]
    libversion = libversion[15:]
    if not version in libversion:
        print (color.RED + "New version of django-celery available: %s \n!!" + color.END)  % version
    else:
	print "django-celery version %s up to date \n" % version
    
    libversion = host(BACKEND, 'pip freeze | grep uwsgi', 'oskar')
    br.open("https://pypi.python.org/pypi/uWSGI")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/uWSGI/' in i:
	    version = i[-10:-4]
    libversion = libversion[7:]
    if not version in libversion:
        print (color.RED + "New version of uWSGI available: %s \n!!" + color.END)  % version
    else:
	print "uWSGI version %s up to date \n" % version
    
    libversion = host(BACKEND, 'pip freeze | grep supervisor','oskar')
    br.open("https://pypi.python.org/pypi/supervisor")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/supervisor/' in i:
	    version = i[-7:-4]
    libversion = libversion[12:]
    if not version in libversion:
        print (color.RED + "New version of supervisor available: %s \n!!" + color.END)  % version
    else:
	print "supervisor version %s up to date \n" % version
    
    libversion = host(BACKEND, 'pip freeze | grep uwsgitop','oskar')
    br.open("https://pypi.python.org/pypi/uwsgitop")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/uwsgitop/' in i:
	    version = i[-9:-4]
	    print version
    libversion = libversion[10:]
    if not version in libversion:
        print (color.RED + "New version of uWSGItop available: %s \n!!" + color.END)  % version
    else:
	print "uWSGItop version %s up to date \n" % version
    
    
if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([checksw])
    p.dispatch()


