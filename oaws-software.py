#!/usr/bin/python

"""
This script checks for updates to some software and libraries used by the ella app
that are not updates via Amazon's YUM repositories. Examples of these are:
	- RabbitMQ
	- Celery
	- django-celery
	- uWGSI
	- Supervisor
	- Other software listed by `pip freeze`
"""

from mechanize import Browser

def ensure_library_check(name):
    print 'The library %s is not installed \n' % name
    print 'Please install it by executing pip install %s' % name
    raise SystemExit(1)

try:
    from argh import *
except ImportError:
    ensure_library_check('argh')

def checksw():
    br = Browser()
    br.set_handle_robots(False)
    br.open("http://www.rabbitmq.com/download.html")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'latest release of RabbitMQ' in i:
	    version = i[-14:-9]
	    print "The version of RabbitMQ available is: %s" % version
	else:
	    pass

    br.open("https://pypi.python.org/pypi/librabbitmq")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/librabbitmq/' in i:
	    version = i[-9:-4]
	    print "The version of librabbitmq available is: %s" % version

    br.open("https://pypi.python.org/pypi/celery")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/celery/' in i:
	    version = i[-10:-4]
	    print "The version of celery available is: %s" % version
    
    br.open("https://pypi.python.org/pypi/django-celery")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/django-celery/' in i:
	    version = i[-10:-4]
	    print "The version of django-celery available is: %s" % version
    
    br.open("https://pypi.python.org/pypi/uWSGI")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/uWSGI/' in i:
	    version = i[-10:-4]
	    print "The version of uWSGI available is: %s" % version
    
    br.open("https://pypi.python.org/pypi/supervisor")
    page = br.response().read()
    data = page.split('\n')
    for i in data:
        if 'href="/pypi/supervisor/' in i:
	    version = i[-7:-4]
	    print "The version of supervisor available is: %s" % version
    
    
if __name__ == '__main__':
    p = ArghParser()
    p.add_commands([checksw])
    p.dispatch()


