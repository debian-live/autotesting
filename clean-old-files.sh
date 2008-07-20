#!/bin/bash
#
# Remove old files
find /home/autotesting/*/daily/ -not -type d -ctime +4 -print0     | xargs --null --no-run-if-empty rm -f
find /home/autotesting/*/weekly/ -not -type d -ctime +28 -print0   | xargs --null --no-run-if-empty rm -f
find /home/autotesting/*/monthly/ -not -type d -ctime +124 -print0 | xargs --null --no-run-if-empty rm -f

# Remove old symlinks
for f in $(find /home/autotesting/www-root/ -type l)
do 
    if [ ! -e "$f" ]
    then 
        echo $f
    fi
done

# Remove empty directories
find /home/autotesting/www-root/ -depth -type d -empty -exec rmdir {} \;
