#!/usr/bin/python

import subprocess

dump_dir = '/tmp/'
dump_filename = 'ella-pgbackup.sql'
dump_filename_gl = 'ella-pgglobals.sql'
db_name = 'ella'

try:
    command = '/usr/bin/pg_dump ' + '--clean --file=/%s/%s' % (dump_dir,dump_filename) + ' %s' % db_name
    command_gl = '/usr/bin/pg_dumpall ' + '--clean --globals-only --file=/%s/%s' % (dump_dir,dump_filename_gl)
    print 'Creating postgres backup for database %s \n' % db_name
    subprocess.call(command, shell=True)
    print 'Backup for database %s created!' % db_name
    print 'Creating postgres globals backup \n'
    subprocess.call(command_gl, shell=True)
    print 'Backup for postgres globals created!'
except:
    print 'Couldn\'t create backup for database %s' % db_name



