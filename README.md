ovivo-aws-ec2tools
==================

oaws-boot-tools.py : Script to start and stop single instances, stop whole infrastructure, start whole infrastructure.
                     Used mainly for updates that require reboots.

oawshealth.py : Script to check general health of all instances or for a single instance. It uses fabric to fetch uptime
                Load usage, Disk usage and Memory Usage.

oawsupdate.py : Script to update system software on all instances or a single instance. It uses fabric to execute yum update.
