#!/bin/sh
#
# Neater then one long cron line
#

BASEDIR="/home/autotesting"

cd ${BASEDIR}/debian-live/autotesting

exec >${DIR}/log/daily/autotesting.log 2>&1
echo "New Day $(date)"

# Test "daily" images
./run-batch-autotesting.sh daily.lst ${BASEDIR}/iso/daily/ ${BASEDIR}/video/daily/ /var/www/debian-live/i386/

# Test webcoverger
./run-batch-autotesting.sh webconverger.lst ${BASEDIR}/iso/daily/ ${BASEDIR}/video/daily/ /var/www/webconverger/i386/ webc-3.2.mini.iso.MD5SUM

# Build our own images
exec >${DIR}/log/daily/autobuild.log 2>&1
for DIST in etch lenny sid
do
    ./local_build_debian-live.sh ${BASEDIR}/iso/local/debian-live ${DIST} xfce
done

# Test our own images
exec >>${DIR}/log/daily/autotesting.log 2>&1
./run-batch-autotesting.sh local.lst ${BASEDIR}/iso/local/ ${BASEDIR}/video/local/ /var/www/local-build/debian-live/i386/
