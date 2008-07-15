#!/bin/bash
#
# run-batch-autotesting.sh                                #
#                                                         #
# Copyleft (c) 2008 Brendan M. Sleight                    #
#              <bmsleight@barwap._REMOVE_SPAM_TRAP.com>   #
#                                                         #
# This script is licensed under the GNU GPL v2 or later.  #
#                                                         #
# On Debian systems, this license can be obtained via     #
# /usr/share/common-licenses/GPL                          #
#
# Download the list of images and run video-qemu-booting against each download.
#
# Usage: run-batch-autotesting.sh filelist.txt isolocation videos
#   e.g: run-batch-autotesting.sh dailylist.txt daily/ video/daily/
# Hence can be run Daily, weekly or month using different lists
# Another script can do the tidy up.
#
#   We make be downloading an iso on the 21st Jan, built on the
# 20th or even the 1st Jan. This needs to be identified in the
# someway - mayeb the filename. 
# iso-file-name_Built_02-Apr-2008_tested_03-Apr-2008.ogg
#
# 0 - Check lockfile
# 1 - For each iso [each file in in Auotest-iso-urls.lst]
# 1a -  Remove the old iso
# 1b -  if file does not exist or datestamp local iso iso is before today:
# 1b -    Download the new-current-iso and related md5sum-file
# 1c -  check md5sum, if md5sum ok:
# 1d -    Video-qemu-booting-iso iso-name date-iso-name.ogg/.jpg
# 1e -    ????
# 2  -  Profit
#
#

VIDEO_QEMU_BOOTING="/home/autotesting/debian-live/autotesting/video-qemu-booting-iso.sh"

if [ -z "$1" -a -z "$2" -a -z "$3" ]
then
    echo "usage: $0 directory/ "
    echo
    echo " e.g: run-batch-autotesting.sh dailylist.txt iso/daily/ video/daily/"
    exit
fi

URLLIST=$1
DIRECTORY=$2
VIDEO_DIRECTORY=$3

if [ -f /tmp/run-batch-autotesting.lock ]
then
   echo "Lock file /tmp/run-batch-autotesting.lock present indicating $0 is already running"
   exit
fi

echo "Lock file present indicating $0 is running" >/tmp/run-batch-autotesting.lock

URLS=$(cat $URLLIST) # stdio is used by video-qemu-booting
for URL in $URLS
do 
    BASE_NAME=$(echo $URL |  rev | cut -d"/" -f 1 | rev)
    PART_URL=$(echo $URL |  rev | cut -d"/" -f 2- | rev)
    MD5SUMS="$PART_URL/MD5SUMS"
    HAS_FILE_UPDATED_TODAY=$(find $DIRECTORY/ -ctime -1 \! -type d | grep "$BASE_NAME")
    if [ -n "$HAS_FILE_UPDATED_TODAY" ]
    then
        echo "$BASE_NAME already downloaded today "
        echo " - skipping download and testing. To retest please remove file or set ctime>1 day"
    else
        echo "Downloading $URL"
        rm $DIRECTORY/$BASE_NAME 2>/dev/null
        rm $DIRECTORY/MD5SUMS 2>/dev/null
        wget --no-verbose --tries=3 --timeout=60 --directory-prefix=$DIRECTORY $URL
        wget --no-verbose --tries=3 --timeout=60 --directory-prefix=$DIRECTORY $MD5SUMS
        MD5SUM_LOCAL=$(md5sum $DIRECTORY/$BASE_NAME | cut --fields=1 --delimiter=\  )
        MD5SUM_REMOTE=$(cat $DIRECTORY/MD5SUMS | grep "$BASE_NAME" | head -n 1 | cut --fields=1 --delimiter=\  )
        if [[ $MD5SUM_LOCAL != $MD5SUM_REMOTE ]]
        then
            echo "$BASE_NAME - md5sums different, remote: $MD5SUM_REMOTE, local: $MD5SUM_LOCAL. "
            echo "    Skip testing."
        else
            DATE_IMAGE_BUILT=$(ls -lh --time-style long-iso $DIRECTORY/$BASE_NAME |tr -s " "|cut -d" " -f6)
            DATE_DOWNLOADED=$(ls -lc --time-style long-iso $DIRECTORY/$BASE_NAME |tr -s " "|cut -d" " -f6)
            VIDEO_NAME="$VIDEO_DIRECTORY/${BASE_NAME}_Built_${DATE_IMAGE_BUILT}_Tested_${DATE_DOWNLOADED}_.ogg"
            LOG_FILE="$VIDEO_DIRECTORY/${BASE_NAME}_Built_${DATE_IMAGE_BUILT}_Tested_${DATE_DOWNLOADED}_.log"
            echo "AutoTesting $BASE_NAME $VIDEO_NAME"
            $VIDEO_QEMU_BOOTING -g 1024x768  -t 300 -v 5  $DIRECTORY/$BASE_NAME $VIDEO_NAME >$LOG_FILE 2>&1
            echo "Finished Autotesting $BASE_NAME"
            echo
            echo "----"
            echo
        fi
    fi
done



rm /tmp/run-batch-autotesting.lock
