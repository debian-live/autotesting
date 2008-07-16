#!/bin/bash
#
# video-qemu-booting-iso.sh                               #
#                                                         #
# Copyleft (c) 2007 Brendan M. Sleight                    #
#              <bmsleight@barwap._REMOVE_SPAM_TRAP.com>   #
#                                                         #
# This script is licensed under the GNU GPL v2 or later.  #
#                                                         #
# On Debian systems, this license can be obtained via     #
# /usr/share/common-licenses/GPL                          #
#                                                         #
# Required packages/applications :-                       #
#  bash, expect, ffmpeg2thoera, imagemagick,              #
#  qemu, vncserver, vncrec-twibright                      #
#                                                         #
# Requires /etc/vnc.conf to be ammended.                  #
#                                                         #
#                                                         #


lock_file_check ()
{
if [ -f /tmp/video-qemu-booting-iso.lock ]
then
  echo "Lock file /tmp/video-qemu-booting-iso.lock present indicating $0 is already running"
  exit
fi
VNCCONF=$(cat /etc/vnc.conf | grep "^\$vncStartup")
if [ "$VNCCONF" != "\$vncStartup = \"~/.vnc/xstartup\";" ]
 then
  echo "Requires vnc.conf to have the line:-  "
  echo "\$vncStartup = \"~/.vnc/xstartup\";"
  echo "Else two lots of windowm mangers will launched in the extra vnc sessions."
  exit
fi
echo "Lock file /tmp/video-qemu-booting-iso.lock present indicating $0 is running" >/tmp/video-qemu-booting-iso.lock
}

get_global_variables ()
{
PASSWD="$RANDOM.$RANDOM.$RANDOM.$RANDOM.$RANDOM"
HOSTNAME=$(hostname)
OLD_DISPLAY="$DISPLAY"
TODAY=$(date +"%F")
TMP_DIR=/tmp/vqbi.$$.tmp
IPADDRESS="127.0.0.1"
}

get_options_and_defaults ()
{
if [ "$SENDKEYS" = "" ]; then
 SENDKEYS="spc,l,i,v,e,spc,kp_enter"
fi
if [ "$QEMU_MONITOR_PORT" = "" ]; then
 QEMU_MONITOR_PORT=4444
fi
if [ "$GEOMETRY" = "" ]; then
 GEOMETRY="1280x960"
fi
if [ "$CONVERT_DIM" = "" ]; then
 CONVERT_DIM="800x600"
fi
FFMPEG_DIM_SCALE=$(echo "$CONVERT_DIM" | sed s/x/\ -y\ /g)
FFMPEG_DIM_SCALE="-x $FFMPEG_DIM_SCALE"
if [ "$TIME_Q" = "" ]; then
 TIME_Q="600"
fi
if [ "$VQUALITY" = "" ]; then
 VQUALITY="5"
fi
if [ "$QEMU_BIN" = "" ]; then
 QEMU_BIN="qemu"
 #qemu_0.8.4-etch1
fi
}


set_up_workspace ()
{
mkdir $TMP_DIR 2>/dev/null
rm ~/.vnc/passwd

cat<<EOF > ~/.vnc/xstartup
#!/bin/sh
xsetroot -solid grey
EOF
chmod 755 ~/.vnc/xstartup

cat<<EOF > $TMP_DIR/vnc.exp
spawn vncpasswd
expect "Password:" { send "$PASSWD\r" }
expect "Verify:" { send "$PASSWD\r" }
interact
puts "\nVNC Password changed\n"
EOF

expect $TMP_DIR/vnc.exp >/dev/null 2>/dev/null
echo "VNC Password changed"
}

start_vnc_sessions ()
{
vncserver -depth 24   -Protocol3.3 -geometry $GEOMETRY -localhost >$TMP_DIR/vncserver.txt 2>&1
VNSERVER_QEMU=$(cat $TMP_DIR/vncserver.txt | grep 'New' | awk '{ print $6}' )
VNCSERVER_QMEU_NUMBER=$(cat $TMP_DIR/vncserver.txt | grep 'New' | cut -d: -f3)
echo "Launched vncserver $VNSERVER_QEMU"
vncserver -depth 24  -Protocol3.3 -geometry 1600x1200 -localhost >$TMP_DIR/vncserver.txt 2>&1
VNSERVER_VNCREC=$(cat $TMP_DIR/vncserver.txt | grep 'New' | awk '{ print $6}' )
VNCSERVER_VNCREC_NUMBER=$(cat $TMP_DIR/vncserver.txt | grep 'New' | cut -d: -f3)
echo "Launched vncserver $VNSERVER_VNCREC"
}

start_vnc_record ()
{
export DISPLAY="$VNSERVER_VNCREC"
export VNCREC_MOVIE_FRAMERATE
echo "Starting vncrec, recording :$VNCSERVER_QMEU_NUMBER. Local display :$VNCSERVER_VNCREC_NUMBER"
vncrec -display :$VNCSERVER_VNCREC_NUMBER -passwd ~/.vnc/passwd -depth 24 -shared -truecolor -viewonly -encoding raw -record $TMP_DIR/qemu.1.vnc :$VNCSERVER_QMEU_NUMBER  &
}

start_qemu ()
{
export DISPLAY=$VNSERVER_QEMU
echo "Starting qemu, within Display $VNSERVER_QEMU"
IMAGE_TYPE=$(echo "$ISO" | sed -e 's/.*[.]//g')
if [ "$IMAGE_TYPE" = "img" ]
then
  QEMU_OPTS="-hda"
else
  QEMU_OPTS="-cdrom"
fi
$QEMU_BIN -full-screen $QEMU_OPTS $ISO -monitor telnet:$IPADDRESS:$QEMU_MONITOR_PORT,server,nowait &
sleep 10 # This is really important. I not sure why, vnc catch-up time maybe, but it just works :), remove at your peril
i=1
REACHED_LAST_KB=""
while [ -z $REACHED_LAST_KB ]
do
 KEY=$(echo $SENDKEYS | cut -d, -f$i)
 if [ "$KEY" != "" ]
 then
  echo "sendkey $KEY" | socat - TCP4:$IPADDRESS:$QEMU_MONITOR_PORT
 else
  REACHED_LAST_KB="Y"
 fi
 let i=i+1
done
sleep 1
}

let_qemu_run ()
{
echo "Sleeping for $TIME_Q seconds whilst qemu runs"
sleep $TIME_Q
}

stop_qemu ()
{
echo "Stopping vncrec and qemu"
killall vncrec
killall $QEMU_BIN
}

stop_vncservers ()
{
echo "Stopping vncservers"
vncserver -kill :$VNCSERVER_QMEU_NUMBER >/dev/null 2>&1
vncserver -kill :$VNCSERVER_VNCREC_NUMBER >/dev/null 2>&1
}

gen_video ()
{
#Need to runs some tests to ensure vncrec -movie does temriante at end of session.
echo "Generating video from recorded vnc stream. "
vncrec  -movie $TMP_DIR/qemu.1.vnc 2>/dev/null | ffmpeg2theora $FFMPEG_DIM_SCALE --videoquality $VQUALITY --inputfps 40 --artist "AutoTesting.livecd.org" --title "Video of Qemu booting $ISO"  --date "$TODAY" -o $VIDEO - 2>/dev/null
}

gen_video_preview ()
{
MONTAGE_DIR=/tmp/tp.$$.dir.montage
mkdir $MONTAGE_DIR
ffmpeg -i $VIDEO -vcodec copy $TMP_DIR/duration.ogg 2>$TMP_DIR/ffmpeg.log
DURATION_H=$(cat $TMP_DIR/ffmpeg.log | grep Duration | cut -d ' ' -f 4 | sed s/,// | cut -d ':' -f 1)
DURATION_M=$(cat $TMP_DIR/ffmpeg.log | grep Duration | cut -d ' ' -f 4 | sed s/,// | cut -d ':' -f 2)
DURATION_S=$(cat $TMP_DIR/ffmpeg.log | grep Duration | cut -d ' ' -f 4 | cut -d '.' -f 1 | sed s/,// | cut -d ':' -f 3)
LENGTH=$(($DURATION_H*3600+$DURATION_M*60+$DURATION_S))
echo "Duration of Video $LENGTH $DURATION_H $DURATION_M $DURATION_S"
COUNTER=0
END=5
COUNT=1
# Generate a Frame every 0.5 secs for the start of the video
while [  $COUNTER -lt $END ]; do
	HALFSECS=$(echo $COUNTER/2|bc -l)
	ffmpeg -i $VIDEO -an -ss $HALFSECS -t 01 -r 1 -y -s 320x240 $TMP_DIR/video%d.jpg 2>/dev/null
	mv $TMP_DIR/video1.jpg $MONTAGE_DIR/$COUNT.jpg 
	LIST="$LIST $MONTAGE_DIR/$COUNT.jpg"
	let COUNT=COUNT+1
	let COUNTER=COUNTER+1
done
SPLIT=$(($LENGTH/12))
COUNTER="$SPLIT" 	
while [  $COUNTER -lt $LENGTH ]; do
	ffmpeg -i $VIDEO -an -ss $COUNTER -t 01 -r 1 -y $TMP_DIR/video%d.jpg 2>/dev/null
	mv $TMP_DIR/video1.jpg $MONTAGE_DIR/$COUNT.jpg 
	LIST="$LIST $MONTAGE_DIR/$COUNT.jpg"
	let COUNT=COUNT+1
	let COUNTER=$(($COUNTER+$SPLIT))
done
montage -geometry 180x135+4+4 -frame 5 $LIST $VIDEO.montage.jpg 
LAST_FRAME_OF_MONTAGE=$(echo $LIST | rev | cut -d" " -f1 | rev )
cp $LAST_FRAME_OF_MONTAGE $VIDEO.end.jpg
rm -R $MONTAGE_DIR
rmdir $MONTAGE_DIR
}

clean_up ()
{
DISPLAY="$OLD_DISPLAY"
export DISPLAY="$OLD_DISPLAY"
rm $TMP_DIR -r
rm /tmp/video-qemu-booting-iso.lock
}


while getopts s:p:g:d:t:v:q:n opt
do
    case "$opt" in
      s)  SENDKEYS="$OPTARG";;
      p)  QEMU_MONITOR_PORT="$OPTARG";;
      g)  GEOMETRY="$OPTARG";;
      d)  CONVERT_DIM="$OPTARG";;
      t)  TIME_Q="$OPTARG";;
      v)  VQUALITY="$OPTARG";;
      q)  QEMU_BIN="$OPTARG";;
      n)  NOPREVIEW="true";;


      \?)		# unknown flag
      	  echo >&2 \
		"usage: $0 [-s \"keys,to,send,to,qemu\"] [-p port_number for qemu-monitor] [-g geometry of vncsession] [-d dimensions of video] [-t time to run qemu] [-v (0 to 10) encoding quality for video] [-q alternative qemu binary name] [-n] IsoToTest.iso Video.ogg "
	  exit 1;;
    esac
done
shift `expr $OPTIND - 1`

if [ -z "$1" -a -z "$2" ]; then
    echo "usage: $0 [-s \"keys,to,send,to,qemu\"] [-p port_number for qemu-monitor] [-g geometry of vncsession] [-d dimensions of video] [-t time to run qemu] [-v (0 to 10) encoding quality for video] [-q alternative qemu binary name] [-n Do not gernerate a preview of the video.ogg.jpg] IsoToTest.iso Video.ogg " 
    echo
    echo " This script boots a livecd using qemu and records a video of the process. "
    echo
    echo " It is worth noting that this script takes a long time to run and heavy usage of CPU."
    echo " There is heavy usage of the qemu, imagemagik tools. "
    echo " For every second of running qemu the script it can take up to 3s to compile the video."
    echo " For example using -t 1200 will about one hour."
    echo
    echo " Minimum geometry for qemu -g 1024x768"
    echo
    echo " Launches a couple of vncserver session, kills other vncrec and qemu sessions running."
    exit
fi

ISO=$1
VIDEO=$2

lock_file_check
get_options_and_defaults
get_global_variables
set_up_workspace
start_vnc_sessions
start_vnc_record
start_qemu
let_qemu_run
stop_qemu
gen_video
if [ "$NOPREVIEW" = "true" ]; then
	echo "Skipping jpg preview"
else
	gen_video_preview
fi
stop_vncservers
clean_up
