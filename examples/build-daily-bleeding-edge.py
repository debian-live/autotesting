#!/usr/bin/python
# -*- coding: utf-8 -*-
#

# Depends: python, python-amara, wget, python-twitter, git-core, dpkg-dev, apache2-mpm-prefork
# backports debhelper 

# Build daily standard

# 2 - build iso -> daily-standard + (tweet!)
#   mkdir
#   lh config -d sid --repositories live.debian.net --packages-lists standard
#   lh build
#   mv 
# 3 - Download git and build and install
# 4 - Build iso -> Bleeding edge  + (tweet!)
# 5 - Test
# 6 - Remove live-helper
# 7 - install live-helper from live.debian.net 
# 8 - ???
# 9 - Profit

# <dba> bmsleight: git clone git://live.debian.net/git/live-helper.git
# cd live-helper
# <dba> git checkout -b debian-next origin/debian-next


from optparse import OptionParser
import amara, datetime, os, shutil, subprocess, sys, tempfile, time, datetime, urllib, twitter, fcntl, glob

class SingleInstance:
    # Slimed down from excellent example given at:-
    # http://stackoverflow.com/questions/380870/python-single-instance-of-program
    def __init__(self):
        self.lockfile = os.path.normpath(tempfile.gettempdir() + '/' + os.path.basename(__file__) + '.lock')
        self.fp = open(self.lockfile, 'w')
        try:
            fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            log("Another copy of this script is already is already running, quitting.")
            sys.exit(-1)

def log(message):
    """ Print [date] message """ 
    now = datetime.datetime.now()
    print "[" + str(now) + "] " + str(message) 
    sys.stdout.flush()


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
        L.append('--limit-rate=1.5M')
    # Maybe do something with the retcode in the future.
    retcode = subprocess.call(L)
    return tmpFile

def tiny_url(url):
    apiurl = "http://tinyurl.com/api-create.php?url="
    tinyurl = urllib.urlopen(apiurl + url).read()
    return tinyurl

def storeFile(tmpFile, copyLocation, symLocation):
    if tmpFile:
        shutil.copyfile(tmpFile, copyLocation)
    try:
        os.remove(symLocation)
    except:
        pass
    os.symlink(copyLocation, symLocation)

def mkdir(d):
    try:
        os.makedirs(d)
    except:
        pass

def parseBuilds(xml):
    builds = amara.parse(xml)
    return builds.autotesting.builds

def postTweet(twit, message, long_url=False):
    if long_url:
        tiny=tiny_url(long_url) 
        tweet = message[:120] + "... " + str(tiny)
    else:
        tweet = message[:139]
    try:
        api = twitter.Api(username=str(twit.user), password=str(twit.passw) )
        status = api.PostUpdate(tweet)
        log("Tweet: " + tweet)
    except:
        log("Tweeting failed! " + tweet)


def igore():
    tweet =  "Autotesting of: " + str(test.description)[:90] + "... " + str(tiny)
    api = twitter.Api(username=str(twit.user), password=str(twit.passw) )
    status = api.PostUpdate(tweet)


def log_process(c, cwd="/tmp/", storeLog=False, shell=False):
    p = subprocess.Popen(c,
                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       cwd=cwd)
    (stdout, stderr) = p.communicate()
    log(stdout)
    if storeLog:
        f = open(storeLog,"w")
        f.write(stdout)
        f.close()
    return stdout

def git_live_helper():
    tempDir = tempfile.mkdtemp(prefix="autobuild_git_", suffix="_dir")
    log("Building lh from git")
    log_process(["git", "clone", "git://live.debian.net/git/live-helper.git"], tempDir)
    log_process(["git", "checkout", "-b", "debian-next", "origin/debian-next"], tempDir + "/live-helper")
    log_process(["dpkg-buildpackage", "-us", "-uc", "-rfakeroot"], tempDir + "/live-helper")    
    debs = glob.glob(tempDir + "/*.deb")
    for deb in debs:
        log_process(["dpkg", "-i", deb], tempDir)
    shutil.rmtree(tempDir)

def remove_git_live():
    #dpkg -r live-helper
    log("Remove lh (git) and install lh from live.debian.net")
    log_process(["dpkg", "-r", "live-helper"])
    log_process(["apt-get", "update"])
    log_process(["apt-get", "install", "live-helper"])


def builds(buildsXML, moveDir, prefix, twit):
    for d in buildsXML.distributions.distribution:
        for p in buildsXML.package_lists.package_list:
            build(d, p, moveDir, prefix, twit)

def build(d, packageList, moveDir, prefix, twit):
#   mkdir
#   lh config -d sid --repositories live.debian.net --packages-lists standard
#   lh build
#   mv 
    ISO_NAME = "binary-hybrid.iso"
    tempDir = tempfile.mkdtemp(prefix="autobuild_iso_", suffix="_dir")
    lh = ["lh", "config", "-d", str(d), 
          "--repositories", "live.debian.net", "--packages-lists",
          str(packageList)]
    log_process(lh, tempDir, tempDir + "/config.log")
    log_process(["lh", "build"], tempDir, tempDir + "/build.log")

    today=str(datetime.date.today())
    todayDir = moveDir + "/" + today + "/"
    mkdir(todayDir)
    currentDir = moveDir + "/current/"
    mkdir(currentDir)
    shortPrefix = prefix + str(d) + "-" + str(packageList) + "-"
    todayPrefix = todayDir + shortPrefix
    currentPrefix = currentDir + shortPrefix
    
    # Now this is ugly... why not /bin/sh instead of python ??
    # Now that I've written it looks bad, real bad...
    stores = ["build.log", "config.log", "binary-hybrid.iso", "binary.list", "binary.packages"]
    for store in stores:
        try:
            storeFile(tempDir + "/" + store, todayPrefix + store, currentPrefix + store)
        except:
            log("Error copying " + store)
    try:
        log_process(["md5sum", shortPrefix + "binary-hybrid.iso" ], 
                    todayDir, todayPrefix + "binary-hybrid.iso.md5sum" )
        # Now this is ugly... why not /bin/sh instead of python ??
        storeFile(False, todayPrefix + "binary-hybrid.iso.md5sum",
                  currentPrefix + "binary-hybrid.iso.md5sum")
    except:
        log("Error making MD5SUM")

    if twit:
        long_url=str(twit.hosting.url) + "/" + today + "/"
        message = "Autobuild Debian-Live, (" + prefix + ") " + str(d) + " " + str(packageList) + " "
        postTweet(twit, message, long_url=long_url)
    shutil.rmtree(tempDir)

    # Remove old builds
    keepDate = datetime.datetime.now() - datetime.timedelta(days=4)
    log("Removing old Builds before " + keepDate.strftime("%A %B %d %I:%M:%S %p %Y"))
    for f in os.listdir(moveDir):
        fp = moveDir + f
        if (time.mktime(keepDate.timetuple()) - os.path.getmtime(fp) ) > 0:
            # Remove the old file
            shutil.rmtree(fp)
            log("Removing - " + fp)


def main():
    usage = "usage: %prog [options] \n       %prog --help for all options"
    parser = OptionParser(usage, version="%prog ")
    parser.add_option("-b", "--builds", dest="builds",
                      help="complete the builds in the xml template")
    parser.add_option("-l", "--limit", action="store_true", dest="limit",
                      help="Limit download rates to 4M")
    parser.add_option("-w", "--twitter", dest="twit",
                      help="Tweet after each build is completed, accordig to the setting in xml template")
    (options, args) = parser.parse_args() 
    if not options.builds:
        parser.error("Must pass a list of builds to complete.")
    if options.twit:
        twit = parseTwitter(options.twit)
    else:
        twit = False
    
    # Only one instance of ME should be running.
    me = SingleInstance()
    # Main loop
    buildsXML = parseBuilds(options.builds)
    wwwRoot = "/var/www/autobuild/debian-live/"
    builds(buildsXML, wwwRoot, "live-snapshot-", twit)
    git_live_helper()
    builds(buildsXML, wwwRoot, "git-debian-next-", twit)
    remove_git_live()


if __name__ == "__main__":
    main()
