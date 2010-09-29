#!/usr/bin/env python

# This script attempts to create a file in CRL format listing all versioned
# components located recursively within the starting directory

import os
import sys
import re
import urlparse
from pprint import pprint

REPOS = dict()
BASE_DIR = os.getcwd()
ROOT = os.path.basename(BASE_DIR)
LAST_URL = 'None'
LAST_PATH = 'None'

def main():
    
    for root, dirs, files in os.walk(BASE_DIR):
        if 'CVS' in dirs:
            process_cvs(root)
        elif '.svn' in dirs:
            process_svn(root)
        elif '.git' in dirs:
            process_git(root)
        elif '.hg' in dirs:
            process_hg(dirs)
        elif '.darcs' in dirs:
            process_darcs(root)
    
    #pprint(REPOS)
    print_CRL()
    
    sys.exit(0)


def process_cvs(root):
    pass


def process_svn(root):
    global LAST_URL
    global LAST_PATH
    os.chdir(root)
    root = re.sub(os.path.dirname(BASE_DIR)+os.sep, '', root)
    pipe = os.popen("svn info")
    for line in pipe:
        if re.match('URL:', line):
            url = re.sub('URL: ', '', line.strip())
            # first check for recursive occurences of .svn, etc
            if not re.search(LAST_URL, url):
                # now check for similar URL structure
                #path = urlparse.urlsplit(url).path
                #if os.path.commonprefix([LAST_PATH, path]) != '':
                #    print os.path.commonprefix([LAST_PATH, path])
                REPOS[url] = dict()
                path = root.split(os.sep)
                checkout = ''
                # find common area of path and url > checkout
                while path != []:
                    if re.search(os.sep.join(path), url):
                        checkout = os.sep.join(path)
                        #print checkout
                        break
                    else:
                        del path[0]
                target = re.sub(checkout, '', root)
                REPOS[url]['target'] = target
                REPOS[url]['type'] = 'svn'
                REPOS[url]['url'] = url
                REPOS[url]['checkout'] = checkout
                LAST_URL = url
                LAST_PATH = path
    pipe.close()


def process_git(root):
    pass


def process_hg(root):
    pass


def process_darcs(root):
    pass


def print_CRL():
    """Takes the discovered repositories and outputs formatted CRL."""
    print "!CRL_VERSION = 1.0"
    print ""
    print "!DEFINE ROOT = %s" % ROOT
    for repo in REPOS:
        print "!TARGET  = %s" % REPOS[repo]['target']
        print "!TYPE    = %s" % REPOS[repo]['type']
        print "!URL     = %s" % REPOS[repo]['url']
        print "!CHECKOUT= %s" % REPOS[repo]['checkout']
        print ""
        


#####################################################################
if __name__ == '__main__':
    main()