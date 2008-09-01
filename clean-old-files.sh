#!/bin/sh
#
# Remove old files
find /home/autotesting/*/daily/ -not -type d -ctime +4 -print0     | xargs --null --no-run-if-empty rm -f
find /var/www/debian-live/i386/*-sid-*  -not -type d -ctime +4 -print0   | xargs --null --no-run-if-empty rm -f
find /var/www/webconverger/i386/*  -not -type d -ctime +4 -print0   | xargs --null --no-run-if-empty rm -f
find /var/www/local-build/debian-live/i386/*  -not -type d -ctime +4 -print0   | xargs --null --no-run-if-empty rm -f
find /var/www/lenny_live_beta1/i386/*  -not -type d -ctime +4 -print0   | xargs --null --no-run-if-empty rm -f

find /home/autotesting/*/weekly/ -not -type d -ctime +28 -print0   | xargs --null --no-run-if-empty rm -f
find /var/www/debian-live/i386/*-lenny-*  -not -type d -ctime +28 -print0   | xargs --null --no-run-if-empty rm -f

find /home/autotesting/*/monthly/ -not -type d -ctime +124 -print0 | xargs --null --no-run-if-empty rm -f
find /var/www/debian-live/i386/*-etch-*  -not -type d -ctime +4 -print0   | xargs --null --no-run-if-empty rm -f

# Remove empty directories
find /var/www/*/ -depth -type d -empty -exec rmdir {} \;
