#!/usr/bin/env python

# This script attempts to create a file in CRL format listing all versioned
# components located recursively within the starting directory

__author__ = "Eric Seidel <eric@eseidel.org>"

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
                # a little odd, but 
                LAST_URL = url
                # now check for similar URL structure
                path = root.split(os.sep)
                checkout = ''
                # find common area of path and url > checkout
                while path != []:
                    if re.search(os.sep.join(path), url):
                        checkout = os.sep.join(path)
                        break
                    else:
                        del path[0]
                target = re.sub(checkout, '', root)
                # kill any trailing '/'
                target = re.sub(os.sep+'$', '', target)
                # sub in $ROOT if it belongs
                target = re.sub(r'^%s' % ROOT, r'$ROOT', target)
                # account for empty checkout (should be '.' then)
                if checkout == '':
                    checkout = '.'
                # insert URL variables
                for i in range(len(path)):
                    url = re.sub(path[i], r'$%d' % (i+1), url, count=1)
                #component = {'target' : target, 'type' : 'svn',
                #             'url' : url, 'checkout' : checkout}
                try:
                    REPOS[url]['checkout'].append(checkout)
                except KeyError:
                    REPOS[url] = {'target' : target, 'type' : 'svn',
                                 'url' : url, 'checkout' : [checkout]}
                #REPOS[url]['target'] = target
                #REPOS[url]['type'] = 'svn'
                #REPOS[url]['url'] = url
                #REPOS[url]['checkout'] = checkout
                
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
    print ""
    for repo in REPOS:
        print "!TARGET  = %s" % REPOS[repo]['target']
        print "!TYPE    = %s" % REPOS[repo]['type']
        print "!URL     = %s" % REPOS[repo]['url']
        print "!CHECKOUT= "
        for c in REPOS[repo]['checkout']:
            print c
        print ""
        


#####################################################################
if __name__ == '__main__':
    main()