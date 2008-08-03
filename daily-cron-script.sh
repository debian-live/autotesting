#!/bin/bash
#
# Neater then one long cron line
#
echo "New Day " >/home/autotesting/log/daily/autotesting.log
/home/autotesting/debian-live/autotesting/run-batch-autotesting.sh /home/autotesting/debian-live/autotesting/daily.lst /home/autotesting/iso/daily/ /home/autotesting/video/daily/ /var/www/debian-live/i386/ >>/home/autotesting/log/daily/autotesting.log 2>&1

/home/autotesting/debian-live/autotesting/run-batch-autotesting.sh /home/autotesting/debian-live/autotesting/webconverger.lst /home/autotesting/iso/daily/ /home/autotesting/video/daily/ /var/www/webconverger/i386/ webc-3.2.mini.iso.MD5SUM   >>/home/autotesting/log/daily/autotesting.log 2>&1

/home/autotesting/debian-live/autotesting/local_build_debian-live.sh /home/autotesting/iso/local/debian-live etch xfce  >/home/autotesting/log/local/autobuild.log  2>&1
/home/autotesting/debian-live/autotesting/local_build_debian-live.sh /home/autotesting/iso/local/debian-live lenny xfce >/home/autotesting/log/local/autobuild.log  2>&1
/home/autotesting/debian-live/autotesting/local_build_debian-live.sh /home/autotesting/iso/local/debian-live sid xfce   >/home/autotesting/log/local/autobuild.log  2>&1

/home/autotesting/debian-live/autotesting/run-batch-autotesting.sh /home/autotesting/debian-live/autotesting/local.lst /home/autotesting/iso/local/ /home/autotesting/video/local/ /var/www/local-build/debian-live/i386/ >/home/autotesting/log/local/autotesting.log 2>&1

