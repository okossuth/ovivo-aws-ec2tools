ovivo-aws-ec2tools
==================

oaws-boot-tools.py : Script the uses boto to execute several operations on Amazon Instances like start and stop 
                     single instances, stop the whole infrastructure, start the whole infrastructure.
                     Used mainly for updates that require reboots.It also gives information about running instances, 
                     elastic IPs used by instances, allows to associate or disassociate elastic IPs and let's
                     you changed the type of stopped instance.

oawshealth.py : Script to check general health of all instances or a single instance. It uses fabric to fetch uptime,
                cpu type, load average stats, disk usage and memory Usage.

oawsupdate.py : Script to update system software on all instances or a single instance. It uses fabric to execute yum,
                if it founds the there are new updates available, it will ask to confirm the update and proceed with it.

oaws-software.py: Script that checks updates for software not managed by YUM, like software shown by pip freeze.
                  If it finds new versions available it will send an email alerting about it. Runs via cron

oaws-ec2snapshot.py: Script that uses boto to execute several snapshot operations on Amazon instances.

