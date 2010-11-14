#!/usr/bin/env python

'''
This script attempts to create a file in CRL format listing all versioned
components located recursively within the starting directory.
'''

__author__ = "Eric Seidel <eric@eseidel.org>"

import os
import sys
import re
import urlparse
from pprint import pprint

REPOS = dict()
BASE_DIR = os.getcwd()
ROOT = os.path.basename(BASE_DIR)
LAST_URL = 'rDjLIYICiziFQNRcFKrhpcdYf8QwAzCLYrNu8JAEPpmRAJamCA'
LAST_PATH = 'gDaMUCyJvqVjxJhnFHbTQTJevMxDGWqZY4jmaBEQOGkDMss7Ek'

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
    '''
    Takes a known CVS repository and determines the options to check it out.
    '''
    global LAST_URL
    global LAST_PATH
    os.chdir(root)
    root = re.sub("%s%s" % (os.path.dirname(BASE_DIR), os.sep), '', root)
    
    # get url from CVS/Root
    f = open(os.path.join('CVS', 'Root'))
    url = f.read().strip()
    f.close()
    
    # get checkout from CVS/Repository
    f = open(os.path.join('CVS', 'Repository'))
    checkout = f.read().strip()
    f.close()
 
    if url == LAST_URL and re.search(LAST_PATH, checkout):
        # moving lower into a repository
        return
    
    # now we need to do some clever matching to figure out what
    # checkout, name, and target should be
    #checkout_path = checkout.split(os.sep)
    target_path = root.split(os.sep)
    #for cpath in checkout_path:
    #    if cpath not in target_path:
    #        checkout_path.remove(cpath)       
    #name = os.sep.join(checkout_path)
    
    # now split again to fix target
    checkout_path, checkout_item = os.path.split(checkout)
    while target_path != []:
        if checkout_item in target_path:
            target_path.remove(checkout_item)
            checkout_path, checkout_item = os.path.split(checkout_path)
        else:
            break
    target = os.sep.join(target_path)
          
    # sub in $ROOT if it belongs
    target = re.sub(r'^%s' % ROOT, r'$ROOT', target)
    
    try:
        REPOS[url]['checkout'].append(checkout)
    except KeyError:
        REPOS[url] = {'target' : target, 'type' : 'cvs',
                     'url' : url, 'checkout' : [checkout]
                     #, 'name' : name
                     }
           
    LAST_URL = url
    LAST_PATH = checkout
    os.chdir(BASE_DIR)
      
def process_svn(root):
    '''
    Takes a known Subversion repository and determines the options
    to check it out.
    '''
    global LAST_URL
    os.chdir(root)
    root = re.sub("%s%s" % (os.path.dirname(BASE_DIR), os.sep), '', root)
    pipe = os.popen("svn info")
    for line in pipe:
        if re.match('URL:', line):
            url = re.sub('URL: ', '', line.strip())
            # first check for recursive occurrences of .svn
            if not re.search(LAST_URL, url):
                # a little odd, but we modify url during this function
                LAST_URL = url
                # now check for similar URL structure
                path = root.split(os.sep)
                checkout = ''
                # checkout = common area of path and url
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
                
    pipe.close()
    os.chdir(BASE_DIR)

def process_git(root):
    '''
    Takes a known git repository and determines the options to clone it.
    '''
    os.chdir(root)
    print "found git"
    root = re.sub("%s%s" % (os.path.dirname(BASE_DIR), os.sep), '', root)
    pipe = os.popen("git remote show -n origin")
    for line in pipe:
        if re.search(r'fetch\s+url:', line, flags=re.I):
            url = re.sub(r'fetch\s+url:\s*', '', line.strip(), flags=re.I)
            url.strip()
            target = root
            checkout = '.'
            REPOS[url] = {'target' : target, 'type' : 'git',
                            'url' : url, 'checkout' : [checkout]}
    pipe.close()
    os.chdir(BASE_DIR)

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
        try:
            print "!NAME    = %s" % REPOS[repo]['name']
        except KeyError:
            pass
        print ""
        


#####################################################################
if __name__ == '__main__':
    main()