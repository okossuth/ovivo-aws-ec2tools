#!/usr/bin/python

import os
import subprocess
import time 
import smtplib
from email.mime.text import MIMEText

LOG = "/var/log/celeryd.log"

cmd = "tail -1 %s | grep Beat" % LOG
x = 0

while x < 30:
    try:
        ret = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        print ret
	print "Celery Beat is running... move along"
        raise SystemExit(0)
    except Exception, e:
        print "Celery beat error!!"
        pass
    x = x+1
    time.sleep(1)

print "Celery Beat is not runnning! Please Check!"
message = "It seems celery beat is not publishing tasks.."
me = "sysadminops@ovivo.dk"
to = "okossuth@gmail.com"
msg = MIMEText(message)
msg['Subject'] = "Celery Beat Problems!!!"
msg['From'] = me
msg['To'] = to
cmd = "tail -1 /etc/hosts | awk '{print $1}'"
ret = subprocess.check_output(cmd , shell=True)
s = smtplib.SMTP(ret)
s.sendmail(me, to, msg.as_string())
s.quit()
raise SystemExit(1)

