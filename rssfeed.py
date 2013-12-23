#!/usr/bin/python

"""
 Script for parsing Amazon SES RSS status feed.
 """

import feedparser
import smtplib
from email.mime.text import MIMEText

def sendalert(status):
    message = status
    me = "sysadminops@ovivo.dk"
    to = ["okossuth@gmail.com", "jh@ovivo.dk", "af@ovivo.dk"]
    #to = "okossuth@gmail.com"
    msg = MIMEText(message)
    msg['Subject'] = "Amazon SES problems!"
    msg['From'] = me
    msg['To'] = ", ".join(to)
    s = smtplib.SMTP('localhost')
    s.sendmail(me, to, msg.as_string())
    s.quit()


def main():
    data = feedparser.parse('http://status.aws.amazon.com/rss/ses-us-east-1.rss')
    print data.feed.title
    print data.feed.link
    print data.version
    print len(data.entries)
    print data.entries[0].title + ' || ' + data.entries[0].published
    status = data.entries[0].title + ' || ' + data.entries[0].published
    if not "normally" in status:
        print "Amazon SES is having problems..."
	sendalert(status)
    else:
        print "Amazon SES is working fine..."


main()
