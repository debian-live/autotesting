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
import amara, datetime, os, shutil, subprocess, sys, telnetlib, tempfile, time, datetime

def displayNumber():
    """Really a global we can change later to something better.
    like automaticaly get the next free display number. """
    return ":8"
    
def log(message):
    """ Print [date] message """ 
    now = datetime.datetime.now()
    print "[" + str(now) + "] " + str(message) 
    sys.stdout.flush()

def cronCheak(frequency):
    """Check if the frequency (e.g. daily, weekly, mounthly is due to 
    be run at this time
    returns boolean.
    """
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

def wget(url):
    """ Use wget to download a file
    return fileObject"""
    log("Downloading " + url)
    tmpFile = tempfile.NamedTemporaryFile(prefix="autotesting_wget_")
    L = ['wget', '-nv', str(url), '-O', tmpFile.name]
    # Maybe do something with the retcode in the future.
    retcode = subprocess.call(L)
    return tmpFile

def getDownloads(download, backgroundURL):
    """ Create two temp files and download the main download and 
    the background 
    return tempfile, tempfile""" 
    background = wget(str(backgroundURL))
    try:
        # datetime.timedelta(days=55) 
        daysOfset = int(str(download.daysofset)) 
        dateUrlPart = datetime.datetime.now() - datetime.timedelta(days=daysOfset)
        downloadURL=str(download.url) + dateUrlPart.strftime(str(download.dateformat)) + str(download.dateformatend)
    except:
        downloadURL=str(download.url)
    download = wget(str(downloadURL))
    return download, downloadURL, background

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
    recordmydesktopCommand = ["recordmydesktop",  "--no-cursor", "-display", 
                               display ,"--no-sound", "--overwrite", "-o" ,video.name]
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
    xmessage(display, str(test.title), str(test.description), "3", "monospace 6")
    xmessage(display, str(test.title), "Created at " + str(datetime.datetime.now()), "2", "monospace 10")
    xmessage(display, str(test.title), "Downloaded using this url: " + str(downloadURL), "2", "monospace 10")
    
def runningQemu(display, test, qemuDownload):
    """ Start qemu running, with a local telnet port at 55555 listening acting as the qemu monitor
    returns subprocess.process"""
    telnet = ("127.0.0.1", "55555")
    address, port = telnet
    monitor = "telnet:" + address + ":" + port  + ",server,nowait"
    qemuBinary = str(test.qemu.binary)
    log("Starting " + qemuBinary)
    if not qemuBinary.startswith("qemu"):
        log("WARNING! : " + qemuBinary + " does not start with qemu, using qemu instead.")
        qemuBinary = "qemu"
    qemuCommand = [qemuBinary, "-monitor", monitor, "-full-screen", str(test.qemu.options), str(qemuDownload)]
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
    videoLength = int(str(test.qemu.pause)) + int(str(test.qemu.time)) 
    # Time for opening titles
    videoLength = videoLength + 2 + 3 + 3 + 2
    listFrames = []
    listFramesNames = []
    for count in range(16):
        ss = 0.0625 * count * videoLength
        frame = tempfile.NamedTemporaryFile(prefix="autotesting_frame_", suffix=".jpg")
        frameName = frame.name + "%d.jpg"
        frameNameOut = frame.name + "1.jpg"
        ffmpeg = ["ffmpeg", "-i", video.name, "-an", "-ss", str(ss), "-t", 
                  "01", "-r", "1", "-y", frameName]
        retcode = subprocess.call(ffmpeg)
        try:
            shutil.move(frameNameOut, frame.name)
            listFramesNames.append(frame.name)
            listFrames.append(frame)
        except:
            pass
    montageCommand = ["montage", "-geometry", "180x135+4+4", "-frame", "5"]
    for frame in listFramesNames:
        montageCommand.append(frame)
    montageCommand.append(montage.name)
    retcode = subprocess.call(montageCommand)
    return montage

def storeFile(tmpFile, copyLocation, symLocation):
    shutil.copyfile(tmpFile, copyLocation)
    try:
        os.remove(symLocation)
    except:
        pass
    os.symlink(copyLocation, symLocation)

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

def main():
    usage = "usage: %prog [options] --tests=TESTS.XML \n       %prog --help for all options"
    parser = OptionParser(usage, version="%prog ")
    parser.add_option("-t", "--tests", dest="tests",
                      help="complete the autotesting definined in the xml template")
    (options, args) = parser.parse_args() 
    if not options.tests :
        parser.error("Must pass a list of tests to complete.")
        
    # Main loop
    display = displayNumber()
    tests = parseTest(options.tests)
    for test in tests.test:
        if cronCheak(str(test.frequency)):
            log("Starting Autotesting of: " + str(test.title))
            (download, downloadURL, background) = getDownloads(test.download, str(test.background))
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
            log("Finished Autotesting of: " + str(test.title))
            log("*****************************")
        else:
            log("Skipping Autotesting of: " + str(test.title) + " as frequency " + str(test.frequency))
            log("*****************************")

if __name__ == "__main__":
    main()
