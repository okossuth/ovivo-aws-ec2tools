ovivo-aws-ec2tools
==================

oaws-boot-tools.py : Script to start and stop single instances, stop whole infrastructure, start whole infrastructure.
                     Used mainly for updates that require reboots.It also gives information about running instances, 
                     elastic IPs used by instances, and allows to associate or disassociate elastic IPs.

oawshealth.py : Script to check general health of all instances or a single instance. It uses fabric to fetch uptime,
                load usage, disk usage and memory Usage.

oawsupdate.py : Script to update system software on all instances or a single instance. It uses fabric to execute yum,
                if it founds the there are new updates available, it will ask to confirm the update and proceed with it.
