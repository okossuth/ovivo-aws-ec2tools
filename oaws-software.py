#!/usr/bin/python

"""
This script checks for updates to some software and libraries used by the ella app
that are not updates via Amazon's YUM repositories. Examples of these are:
	- Celery
	- django-celery
	- uWGSI
	- uWSGItop
	- Supervisor
	- Nginx
	- Other software listed by `pip freeze`
"""

import os
import smtplib
from email.mime.text import MIMEText
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
    #sshkey = "/home/ella/.ssh/ellaswcheck_rsa"
    sshkey = _getkeypem()
    privkey = paramiko.RSAKey.from_private_key_file (sshkey)
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(hostip,username=user,pkey=privkey)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    if 'nginx' in cmd:
        val = ssh_stderr.read()
    else:
	val = ssh_stdout.read()
    print "Installed version: %s" % val
    return val
   
def checksw():
    message = ''
    br = Browser()
    print "Checking librabbitmq..."
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
        message = "New version of librabbitmq available: %s !!\n" % version
    else:
	print "librabbitmq version %s up to date \n" % version
    
    print "Checking celery..."
    libversion = host(CELERY, 'source /home/ella/Ella/venv/bin/activate; pip freeze | grep ^celery', 'ella')
    br.open("https://pypi.python.org/pypi/celery")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/celery/' in i:
	    version = i[-10:-4]
    libversion = libversion[8:]
    if not version in libversion:
        print (color.RED + "New version of celery available: %s !!\n" + color.END)  % version
        message += "New version of celery available: %s !!\n" % version
    else:
	print "celery version %s up to date \n" % version
    
    print "Checking django-celery..."
    libversion = host(CELERY, 'source /home/ella/Ella/venv/bin/activate; pip freeze | grep django-celery', 'ella')
    br.open("https://pypi.python.org/pypi/django-celery")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/django-celery/' in i:
	    version = i[-10:-4]
    libversion = libversion[15:]
    if not version in libversion:
        print (color.RED + "New version of django-celery available: %s !!\n" + color.END)  % version
        message += "New version of django-celery available: %s !!\n" % version
    else:
	print "django-celery version %s up to date \n" % version
    
    print "Checking uWSGI..."
    libversion = host(BACKEND, '/usr/bin/uwsgi --version', 'oskar')
    br.open("https://pypi.python.org/pypi/uWSGI")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/uWSGI/' in i:
	    if len(i) > 57:
	        version = i[-12:-4]
	    else:
		version = i[-10:-4]
    if not version in libversion:
        print (color.RED + "New version of uWSGI available: %s !!\n" + color.END)  % version
        message += "New version of uWSGI available: %s !!\n" % version
    else:
	print "uWSGI version %s up to date \n" % version
   
    print "Checking supervisor..."
    libversion = host(BACKEND, 'pip freeze | grep supervisor','oskar')
    br.open("https://pypi.python.org/pypi/supervisor")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/supervisor/' in i:
	    version = i[-7:-4]
    libversion = libversion[12:]
    if not version in libversion:
        print (color.RED + "New version of supervisor available: %s !!\n" + color.END)  % version
        message += "New version of supervisor available: %s !!\n" % version
    else:
	print "supervisor version %s up to date \n" % version
    
    print "Checking uWSGItop..."
    libversion = host(BACKEND, 'pip freeze | grep uwsgitop','oskar')
    br.open("https://pypi.python.org/pypi/uwsgitop")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/uwsgitop/' in i:
	    version = i[-9:-4]
    libversion = libversion[10:]
    if not version in libversion:
        print (color.RED + "New version of uWSGItop available: %s !!\n" + color.END)  % version
        message += "New version of uWSGItop available: %s !!\n" % version
    else:
	print "uWSGItop version %s up to date \n" % version
    
    print "Checking Nginx..."
    libversion = host(BACKEND, '/usr/local/nginx/sbin/nginx -v','oskar')
    print "libversion is %s" % libversion
    br.open("http://nginx.org/en/download.html")
    page = br.response().read()
    data = page.split('\n')

    array = data[14].split(' ')
    for i in array:
        if 'h4>Stable' in i:
	    pos = array.index(i)    
    version = array[pos+6]
    version = version[42:-6]
    libversion = libversion[21:]
    if not version in libversion:
        print (color.RED + "New version of Nginx available: %s !!\n" + color.END)  % version
        message += "New version of Nginx available: %s !!\n" % version
    else:
	print "Nginx version %s up to date \n" % version
    
    if len(message) >= 1:
        print message
	me = "sysadminops@ovivo.dk"
	to = "okossuth@gmail.com"
	msg = MIMEText(message)
        msg['Subject'] = "Software Updates available for Ovivo's Ella App"
	msg['From'] = me
	msg['To'] = to
	s = smtplib.SMTP('localhost')
	s.sendmail(me, to, msg.as_string())
	s.quit()
    else:
	print "Everything up to date"

if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([checksw])
    p.dispatch()


