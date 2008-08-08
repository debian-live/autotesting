#!/bin/sh
#
# Script to be run video-qemu-boot-iso.sh via cron job
#

while getopts p:v:q:t: opt
do
    case "$opt" in
      p)  VQBI="$OPTARG";;
      q)  QEMU_BIN="$OPTARG";;
      t)  TIME_Q="$OPTARG";;
      v)  VQUALITY="$OPTARG";;


      \?)		# unknown flag
      	  echo >&2 \
		"usage: $0 [-p path to video-qemu-booting-iso.sh ] [-q alternative qemu binary name] [-t time to run qemu] /foo/bar/iso.directory/ /foo/bar/video.directory/ "
	  exit 1;;
    esac
done
shift `expr $OPTIND - 1`

if [ -z "$1" -a -z "$2" -a -z "$3" ]; then
    echo "usage: $0 [-p path to video-qemu-booting-iso.sh ] [-q alternative qemu binary name] [-t time to run qemu] [-v (0 to 10) encoding quality for video] /foo/bar/iso.directory/ /foo/bar/video.directory/ "
    echo
    echo " This script runs the video-qemu-booting-iso.sh for each iso in a directory. "
    echo
    echo " This script will take _along_ time to run. Approx 1 hour per iso."
    echo " Basically for time to run = number of isos x time to run qmeu x 3  seconds"
    echo " For testing the set-up use -t with a small value e.g. -t 10"
    echo
    echo " The use of -q could allow qemu-ppc be used once Debian bug #388735 is resolved."

    exit
fi

ISODIR=$1
VIDEODIR=$2

if [ "$VQBI" = "" ]; then
 VQBI="video-qemu-booting-iso.sh"
fi
if [ "$QEMU_BIN" = "" ]; then
 QEMU_BIN="qemu"
 #qemu_0.8.4-etch1
fi
if [ "$TIME_Q" = "" ]; then
 TIME_Q="1200"
fi
if [ "$VQUALITY" = "" ]; then
 VQUALITY="5"
fi

for ISO in $ISODIR/*.iso
do
 ISOBN=$(basename $ISO)
 VIDEO=$VIDEODIR$ISOBN.ogg
 echo "Running $VQBI -t $TIME_Q -q $QEMU_BIN -v $VQUALITY $ISO $VIDEO"
 $VQBI -t $TIME_Q -q $QEMU_BIN -v $VQUALITY $ISO $VIDEO
done
echo "Finished Autotesting"
