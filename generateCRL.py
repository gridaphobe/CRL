#!/usr/bin/env python

# This script attempts to create a file in CRL format listing all versioned
# components located recursively within the starting directory

import os
import sys
import re
from pprint import pprint

REPOS = dict()
BASE_DIR = os.getcwd()
LAST_URL = 'None'

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
    
    pprint(REPOS)
    
    sys.exit(0)


def process_cvs(root):
    pass
    
def process_svn(root):
    global LAST_URL
    os.chdir(root)
    pipe = os.popen("svn info")
    for line in pipe:
        if re.match('URL:', line):
            url = re.sub('URL: ', '', line.strip())
            if not re.search(LAST_URL, url):
                REPOS[url] = dict()
                target = re.sub(BASE_DIR, '', root)
                REPOS[url]['target'] = target
                REPOS['type'] = 'svn'
                LAST_URL = url
    pipe.close()
    
def process_git(root):
    pass
    
def process_hg(root):
    pass
    
def process_darcs(root):
    pass

#####################################################################
if __name__ == '__main__':
    main()