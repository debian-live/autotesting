#!/bin/bash
#
# Locally build a debian-live image.
#  as crontab from root
#  Kick auotesting to test..

if [ -z "$1" -a -z "$2" ]
then
    echo " Usage $0 build.iso distribution packages-list "
    exit
fi

if [ -z "$3" ]
then
    echo "blank packages-lists"
    PACKAGE_LISTS=""
else
    PACKAGE_LISTS=" --packages-lists \"$2 \""
fi

TODAY=$(date +"%F")
TMP_DIR=/tmp/local_build_$$/
mkdir $TMP_DIR
#chmod a+w $TMP_DIR
cd $TMP_DIR

lh_config --distribution $2  "$PACKAGE_LISTS"
sudo lh_build
cp ./binary.iso "$1"
ls ./ "$1"
#chmod a+w "$1"
sudo rm $TMP_DIR -R


