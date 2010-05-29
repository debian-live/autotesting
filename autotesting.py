#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   autotesting - automatically test by video qemu booting.
#   Copyright (C) Brendan M. Sleight, et al. <bms@barwap.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


from optparse import OptionParser
import amara, datetime, os, shutil, subprocess, sys, telnetlib, tempfile, time, datetime, urllib, twitter, fcntl

class SingleInstance:
    # Slimed down from excellent example given at:-
    # http://stackoverflow.com/questions/380870/python-single-instance-of-program
    def __init__(self):
        self.lockfile = os.path.normpath(tempfile.gettempdir() + '/' + os.path.basename(__file__) + '.lock')
        self.fp = open(self.lockfile, 'w')
        try:
            fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            log("Another Autotesting is already running, quitting.")
            sys.exit(-1)

def displayNumber():
    """Really a global we can change later to something better.
    like automaticaly get the next free display number. """
    return ":8"
    
def log(message):
    """ Print [date] message """ 
    now = datetime.datetime.now()
    print "[" + str(now) + "] " + str(message) 
    sys.stdout.flush()

def cronCheak(frequency, debug):
    """Check if the frequency (e.g. daily, weekly, mounthly is due to 
    be run at this time
    returns boolean.
    """
    if debug == True:
        log("*** Debug mode - run regardless of frequency ***")
        return True
    now = datetime.datetime.now()
    if frequency == "Daily" or frequency == "daily":
        return True
    elif frequency == "Weekly" or frequency == "weekly":
        if now.weekday() == 0:
            return True
    elif frequency == "Monthly" or frequency == "monthly":
        if now.day == 1:
            return True
    return False

def dateBasedOnFrequency(frequency, keep):
    now = datetime.datetime.now()
    if frequency == "Daily" or frequency == "daily":
        days=1 
    elif frequency == "Weekly" or frequency == "weekly":
        days=7 
    elif frequency == "Monthly" or frequency == "monthly":
        # No date delta of month so near enough ...
        days=30
    old = now - datetime.timedelta(days=days*keep)
    return old

def parseTest(xml):
    """ Get the xml file and load as a object usign amara
    returns amaraObject"""
    tests = amara.parse(xml)
    return tests.autotesting.tests

def parseTwitter(xml):
    """ Get the xml file and load as a object using amara
    returns amaraObject"""
    twit = amara.parse(xml)
    return twit.autotesting.twitter

def wget(url, limit):
    """ Use wget to download a file
    return fileObject"""
    # --limit-rate=4M
    log("Downloading " + url)
    tmpFile = tempfile.NamedTemporaryFile(prefix="autotesting_wget_")
    L = ['wget', '-nv', str(url), '-O', tmpFile.name]
    if limit == True:
        L.append('--limit-rate=1M')
    # Maybe do something with the retcode in the future.
    retcode = subprocess.call(L)
    return tmpFile

def getDownloads(download, backgroundURL, limit):
    """ Create two temp files and download the main download and 
    the background 
    return tempfile, tempfile""" 
    background = wget(str(backgroundURL), limit)
    try:
        # datetime.timedelta(days=55) 
        daysOfset = int(str(download.daysofset)) 
        dateUrlPart = datetime.datetime.now() - datetime.timedelta(days=daysOfset)
        downloadURL=str(download.url) + dateUrlPart.strftime(str(download.dateformat)) + str(download.dateformatend)
    except:
        downloadURL=str(download.url)
    download = wget(str(downloadURL), limit)
    return download, downloadURL, background

def testCheckSum(download, downloadURL, md5sum):
    """ Check md5sum locally against remote list of md5sum stored. 
    """
    mdFile = wget(str(md5sum), False)
    data = [line.split() for  line in open(mdFile.name,'r')]
    downloadFilename = downloadURL.split('/')[-1]
    required = False
    for line in data:
        if line[1] == downloadFilename:
            log("MDSUM required: " + str(line))
            required = line
    if required:
        p = subprocess.Popen("md5sum " + download.name, shell = True, stdout=subprocess.PIPE) 
        localMD = p.stdout.readline().split()
        p.wait()
        log("MDSUM required: " + str(localMD))
        if localMD[0] == required[0]:
            log("MDSUM matched")
            return True
        else:
            log("MDSUM not matched")
            return False
    else:
        # file maybe one line with non-mathcing filename (morphix.org - thanks Alex!)
        p = subprocess.Popen("md5sum " + download.name, shell = True, stdout=subprocess.PIPE) 
        localMD = p.stdout.readline().split()
        p.wait()
        for line in data:
            if line[0] == localMD[0]:
                log("MDSUM required: " + str(line))
                log("MDSUM matched" + str(localMD))
                return True
        log("MDSUM not found for filename")
        return False
        
def authorityFile():
    """ Return a file containing "localhost"
    """
    authority = tempfile.NamedTemporaryFile(prefix="autotesting_authority_")
    authority.write("localhost\n")
    authority.close()
    return authority

def startXvfb(display, xscreen, background):
    """Start a Xvfb instance. The host display for qemu to run inside.
    then set the background image. Return ths PID of Xvfb
    return interger"""
    log("Starting Xvfb")
    authority = authorityFile()
    xvfbCommand = ["Xvfb", display, "-auth", authority.name, "-screen", "0", xscreen] 
    xvfb = subprocess.Popen(xvfbCommand)
    time.sleep(1)
    log("Setting Xvfb background")
    xloadimage = ["xloadimage", "-display", display, "-onroot", "-fullscreen", background]
    retcode = subprocess.call(xloadimage)
    return xvfb

def waitUntilEncodingFinished(recordMyDesktop):
    log("Waiting for recordmydesktop encoding to finish")
    while recordMyDesktop.poll()!=0:
        print ".. ",
        time.sleep(1)
    print " "

def kill(process, message):
    log(message)
    kill = ["kill", str(process.pid)]
    retcode = subprocess.call(kill)

def startRecordMyDesktop(display):
    log("Starting Record My Desktop")
    video = tempfile.NamedTemporaryFile(prefix="autotesting_video_", suffix=".ogv")
#    recordmydesktopCommand = ["recordmydesktop",  "--no-cursor", "-display", 
#                               display ,"--no-sound", "--overwrite", "-o" ,video.name]
# -v_bitrate
    recordmydesktopCommand = ["recordmydesktop",  "--no-cursor", "-display", 
                               display ,"--no-sound", "--overwrite", "-o" ,video.name,
                               "-v_bitrate", "100000"]
    recordmydesktop = subprocess.Popen(recordmydesktopCommand)
    return recordmydesktop, video 

def xmessage(display, title, message, time, font):
    xloadimage = ["gmessage", "-display", display, "-timeout", time, 
                "-font", font, "-button", "", "-title", title, 
                "-center", "\n" + message]
    retcode = subprocess.call(xloadimage)
    
def openingTitles(display, test, downloadURL):
    log("Showing Opening Titles")
    time.sleep(2)
    xmessage(display, str(test.title), "Autotesting of: " + str(test.title), "3", "monospace 14")
    xmessage(display, str(test.title), "Created at " + str(datetime.datetime.now()), "2", "monospace 10")
    xmessage(display, str(test.title), str(test.description), "3", "monospace 6")
    xmessage(display, str(test.title), "Downloaded using this url: " + str(downloadURL), "2", "monospace 6")
    
def runningQemu(display, test, qemuDownload):
    """ Start qemu running, with a local telnet port at 55555 listening acting as the qemu monitor
    returns subprocess.process"""
    telnet = ("127.0.0.1", "55555")
    qemuBinary = str(test.qemu.binary)
    log("Starting " + qemuBinary)
    if not qemuBinary.startswith("qemu"):
        log("WARNING! : " + qemuBinary + " does not start with qemu, using qemu instead.")
        qemuBinary = "qemu"
    address, port = telnet
    monitor = "telnet:" + address + ":" + port  + ",server,nowait"
    qemuCommandStr = qemuBinary + " -monitor " + monitor + " -full-screen " + str(test.qemu.options) + " " + str(qemuDownload)
    qemuCommand = []
    for o in qemuCommandStr.split(' '):
        qemuCommand.append(o)
    log("Qemu command: " + str(qemuCommand))
    qemu = subprocess.Popen(qemuCommand, env={"DISPLAY": display})
    sendkeysToQemu(test, telnet)
    log("Running qemu for  " + str(test.qemu.time) + " seconds")
    time.sleep(int(str(test.qemu.time)))
    return qemu

def sendkeysToQemu(test, telnet):
    """Using telnet to send commands to qemu monitor
    """
    address, port = telnet
    log("Sending keys after pause of " + str(test.qemu.pause) + " seconds")
    time.sleep(int(str(test.qemu.pause)))
    tn = telnetlib.Telnet(address, port)
    sendkeys = str(test.qemu.sendkeys)
    for key in sendkeys.split(','):
        log("qemu sendkey " + key)
        tn.write("sendkey " + key + "\n")
        time.sleep(1)


def captureScreenshot(display):
    """ Capture screen shot on display
    return fileObject"""
    log("Capture screenshot")
    finalImage = tempfile.NamedTemporaryFile(prefix="autotesting_video_", suffix=".png")
    captureCommand = ["import", "-display", display, "-window", "root", finalImage.name]
    retcode = subprocess.call(captureCommand)
    return finalImage

def createMontage(video, test):
    """ Make 16 frames of the video at 1/16, 2/16, 3/16 .... 16/16 of 
        way through the video. The make a montage of these frames in to
        one image. 
    return fileObject"""
    log("Creating Montage")
    montage = tempfile.NamedTemporaryFile(prefix="autotesting_video_", suffix=".png")
    tempDir = tempfile.mkdtemp(prefix="autotesting_video_", suffix="_dir")
    videoLength = int(str(test.qemu.pause)) + int(str(test.qemu.time)) 
    # Time for opening titles
    videoLength = videoLength + 2 + 3 + 3 + 2
    listFrames = []
    listFramesNames = []
    # Total frames = videoLength * 15fps. Hence for get 16 snapshots.
    # (not forgetting a snapshot at frame=0)
    framestep = "framestep=" + str(int((videoLength * 15)/14))
    mplayer = ["mplayer", "-vf", framestep, "-framedrop", "-nosound",
               "-quiet", video.name, "-speed", "100", "-vo", 
               "jpeg:outdir=" + tempDir]
    retcode = subprocess.call(mplayer)
    listFramesNames = os.listdir(tempDir)
    listFramesNames.sort()
    montageCommand = ["montage", "-geometry", "180x135+4+4", "-frame", "5"]
    for frame in listFramesNames:
        montageCommand.append(tempDir + "/" + frame)
    montageCommand.append(montage.name)
    retcode = subprocess.call(montageCommand)
    shutil.rmtree(tempDir)
    return montage

def storeFile(tmpFile, copyLocation, symLocation):
    shutil.copyfile(tmpFile, copyLocation)
    try:
        os.remove(symLocation)
    except:
        pass
    os.symlink(copyLocation, symLocation)

def tiny_url(url):
    apiurl = "http://tinyurl.com/api-create.php?url="
    tinyurl = urllib.urlopen(apiurl + url).read()
    return tinyurl

def fileOutputs(test, video, finalImage, montage):
    """ Move files to the correct place (as per XML tags)
    including symlinks to current.
    """
    log("Moving files to the correct place.")
    root=str(test.output.root)
    local=str(test.output.local)
    today=str(datetime.date.today())
    mainDir = root + "/" + local + "/" + today + "/"
    dateDirs = root + "/" + local + "/"
    currentDir = root + "/current/" + local + "/"
    try:
        os.makedirs(mainDir)
    except:
        pass
    try:
        os.makedirs(currentDir)
    except:
        pass
    # Output the xml describing the test
    singleTestFile = tempfile.NamedTemporaryFile(prefix="autotesting_test_", suffix=".xml")
    f = open(singleTestFile.name,"w")
    f.write(test.xml())
    f.close()
    storeFile(singleTestFile.name, mainDir + "test.xml", currentDir + "test.xml")

    storeFile(video.name, mainDir + str(test.output.video), 
                                   currentDir + str(test.output.video))    
    storeFile(finalImage.name, mainDir + str(test.output.screenshots.final), 
                                   currentDir + str(test.output.screenshots.final))
    storeFile(montage.name, mainDir + str(test.output.screenshots.montage), 
                                   currentDir + str(test.output.screenshots.montage))
    keepDate = dateBasedOnFrequency(str(test.frequency), int(str(test.output.keep)))
    log("Removing old Autotesting output before " + keepDate.strftime("%A %B %d %I:%M:%S %p %Y"))
    for f in os.listdir(dateDirs):
        fp = dateDirs + f
        if (time.mktime(keepDate.timetuple()) - os.path.getmtime(fp) ) > 0:
            # Remove the old file
            shutil.rmtree(fp)
            log("Removing - " + fp)

def postTweet(test, twit):
    local=str(test.output.local)
    today=str(datetime.date.today())
    long_url=str(twit.hosting.url) + "/" + local + "/" + today + "/"
    tiny=tiny_url(long_url) 
    tweet =  "Autotesting of: " + str(test.description)[:50] + "... " + str(tiny) + " (See test.xml for url of image tested)"
    api = twitter.Api(username=str(twit.user), password=str(twit.passw) )
    status = api.PostUpdate(tweet)
    log("Tweet: " + tweet)

def main():
    usage = "usage: %prog [options] --tests=TESTS.XML \n       %prog --help for all options"
    parser = OptionParser(usage, version="%prog ")
    parser.add_option("-t", "--tests", dest="tests",
                      help="complete the autotesting definined in the xml template")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="Debug, run all tests regardless of frquency of testing.")
    parser.add_option("-l", "--limit", action="store_true", dest="limit",
                      help="Limit download rates to 4M")
    parser.add_option("-w", "--twitter", dest="twit",
                      help="Tweet after each test is completed, accordig to the setting in xml template")
    (options, args) = parser.parse_args() 
    if not options.tests :
        parser.error("Must pass a list of tests to complete.")
    if options.twit:
        twit = parseTwitter(options.twit)
    else:
        twit = False
    
    # Only one instance of Autotesting should be running.
    me = SingleInstance()
    
    # Main loop
    display = displayNumber()
    tests = parseTest(options.tests)
    for test in tests.test:
        if cronCheak(str(test.frequency), options.debug):
            log("Starting Autotesting of: " + str(test.title))
            (download, downloadURL, background) = getDownloads(test.download, str(test.background), options.limit)
            try:
                md5sum = str(test.download.md5sum)
                checkSum = testCheckSum(download, downloadURL, md5sum)
            except:
                log("No md5sum found - assuming file downloaded ok")
                checkSum = True
            if checkSum == True:
                xvfb = startXvfb(display, str(test.qemu.xscreen), background.name)
                (recordMyDesktop, video) = startRecordMyDesktop(display)
                openingTitles(display, test, downloadURL)
                try:
                    qemu = runningQemu(display, test, download.name)
                    finalImage = captureScreenshot(display)
                    kill(qemu, "Killing qemu")
                except:
                    xmessage(display, str(test.title), "Qemu failed to run correctly!", "5", "monospace 14")
                    finalImage = captureScreenshot(display)
                    log("Qemu failed")
                kill(recordMyDesktop, "Killing recordmysdesktop")
                waitUntilEncodingFinished(recordMyDesktop)
                kill(xvfb, "Killing Xvfb")
                # Put video, montage in right place remvoe old versions etc.
                montage = createMontage(video, test)
                fileOutputs(test, video, finalImage, montage)
                if twit:
                    try:
                        postTweet(test, twit)
                    except:
                        log("Tweeting failed")
            else:
                log("Checksum (md5sum) failed - test skipped")
            log("Finished Autotesting of: " + str(test.title))
            log("**********************************")
        else:
            log("Skipping Autotesting of: " + str(test.title) + " as frequency " + str(test.frequency))
            log("**********************************")

if __name__ == "__main__":
    main()
