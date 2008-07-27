#!/bin/bash
#
# Locally build a debian-live image.
#  as crontab from root
#  Kick auotesting to test..
# debian-live-lenny-i386-gnome-desktop.iso

if [ -z "$1" -a -z "$2" ]
then
    echo " Usage $0 build.iso distribution packages-list "
    exit
fi

if [ -z "$3" ]
then
    echo "blank packages-lists"
    PACKAGES_LISTS=""
else
    PACKAGES_LISTS="--packages-lists $3"
fi

TODAY=$(date +"%F")
TMP_DIR=/tmp/local_build_$$/
mkdir $TMP_DIR
#chmod a+w $TMP_DIR
cd $TMP_DIR

lh_config --distribution $2  $PACKAGES_LISTS
sudo lh_build
cp ./binary.iso ${1}-${2}-${3}.iso
ls ./ "$1"
#chmod a+w "$1"
sudo rm $TMP_DIR -R


