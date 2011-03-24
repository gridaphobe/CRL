#!/usr/bin/env python

"""
This program automates the procedure of checking out components
from multiple sources and mechanisms. For more info see the
built-in help with ./GetComponents -h
"""
#                             LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


__version__ = '$Revision$'

__author__ = 'Eric Seidel <eric@eseidel.org>'

from optparse import OptionParser
import sys
import re
import os
import shutil
import urllib2
from pprint import pprint
from Queue import Queue

QUIET = 0
VERBOSE = 1
MEGA_VERBOSE = 2

BASE_DIR = os.getcwd()


def main():
    Options.Build()
    c = ComponentList()
    for arg in args:
        c.parse(arg)

    c.checkout()
    if Options.update:
        c.update()

    sys.exit(0)


class Options(object):
    """
    Provides options globally as static variables.
    """
    verbose = 0
    anonymous = False
    update = False
    args = list()

    def Build():
        """
        Static method to build options from command line.
        """
        usage = "usage: %prog [options] component_list"
        parser = OptionParser(usage=usage)
        parser.add_option("-v", "--verbose", action="count", dest="verbose",
                default=0, help="print everything!")
        parser.add_option("-a", "--anonymous", action="store_true",
                dest="anonymous", default=False,
                help="use anonymous checkout/update methods")
        parser.add_option("-u", "--update", action="store_true",
                dest="update", default=False,
                help="update all existing components")
        options, args = parser.parse_args()
        Options.verbose = options.verbose
        Options.anonymous = options.anonymous
        Options.update = options.update
        Options.args = args
    Build = staticmethod(Build)

class ComponentList(object):
    """
    Class for the Component List itself.
    """

    def __init__(self):
        self.DEFS = {'ROOT' : '.'}
        self.Components = []
        self.ComponentsToCheckout = {}
        self.ComponentsToUpdate = {}

    def parse(self, file):

        CRL_VERSION_re = '!CRL_VERSION'
        definition_re = '!DEFINE\s*([^\s]+)\s*=\s*(.+)'
        section_re = '!TARGET\s*=\s*'
        pair_re = '\s*!([^\s=]+)\s*=\s*'
        ComponentList = ''
        CRLFile = ''

        # slurp the file or download from URL
        if re.match('https?://', file):
            CRLFile = urllib2.urlopen(file).read()
        else:
            f = open(file, 'r')
            CRLFile = f.readlines()
            f.close()

        # check for CRL_VERSION
        for i in range(len(CRLFile)):

            # kill whitespace
            CRLFile[i] = re.sub('\s|#.*$', '', CRLFile[i])

            # ignore blank lines
            if len(CRLFile[i]) == 0:
                continue

            # this must be CRL_VERSION
            p = re.compile(CRL_VERSION_re)
            m = p.match(CRLFile[i])

            if m is None:
                print "%s is not a CRL file." % FileName
                sys.exit(1)

            else:
                # remove !CRL_VERSION for later parsing
                CRLFile[i] = ''
                break

        # grab definitions and kill comments and blank lines
        # then copy lines into new ComponentList
        for i in range(len(CRLFile)):

            # kill whitespace and comments
            CRLFile[i] = re.sub('\s*$|#.*$', '', CRLFile[i])

            # ignore blank lines
            if len(CRLFile[i]) == 0:
                continue

            # replace definitions
            for k in self.DEFS.keys():
                CRLFile[i] = re.sub('\$'+k, self.DEFS[k], CRLFile[i])

            p = re.compile(definition_re)
            m = p.match(CRLFile[i])

            if m > 0:
                self.DEFS[m.group(1)] = m.group(2)
                continue

            ComponentList += CRLFile[i] + '\n'

        # replace long-form directives with short-form directives
        re.sub('!ANONYMOUS_USER', '!ANON_USER', ComponentList)
        re.sub('!ANONYMOUS_PASS', '!ANON_PASS', ComponentList)
        re.sub('!ANONYMOUS_PASSWORD', '!ANON_PASS', ComponentList)
        re.sub('!LOCAL_PATH', '!LOC_PATH', ComponentList)
        re.sub('!REPOSITORY_PATH', '!REPO_PATH', ComponentList)
        re.sub('!REPOSITORY_BRANCH', '!REPO_BRANCH', ComponentList)
        re.sub('!AUTHORIZATION_URL', '!AUTH_URL', ComponentList)

        # split into sections and pairs
        sections = re.split(section_re, ComponentList)
        # first section is blank...
        del sections[0]

        for i in range(len(sections)):

            # have to add !TARGET back
            sections[i] = '!TARGET=' + sections[i]
            pairs = re.split(pair_re, sections[i])
            # first entry is blank
            del pairs[0]
            pairs = [p.strip() for p in pairs]

            directives = list_to_dict(pairs)

            # split CHECKOUT
            directives['CHECKOUT'] = re.split('\s', directives['CHECKOUT'].strip())

            # now add each individual component to ComponentsToCheckout
            for comp in directives['CHECKOUT']:

                c = None
                # create a component object
                if directives['TYPE'] == 'cvs':
                    c = cvsComponent(directives)
                elif directives['TYPE'] == 'svn':
                    c = svnComponent(directives)
                elif directives['TYPE'] == 'git':
                    c = gitComponent(directives)
                elif directives['TYPE'] == 'hg':
                    c = hgComponent(directives)
                elif directives['TYPE'] == 'darcs':
                    c = darcsComponent(directives)
                elif directives['TYPE'] in ['http', 'https', 'ftp']:
                    c = webComponent(directives)
                else:
                    raise InvalidTypeError(directives['TYPE'])

#                 for k, v in d.iteritems():
#                     c.add(k, v)

                c.CHECKOUT = comp
                self.Components.append(c)

        for comp in self.Components:
            #print comp
            if comp.exists():
                try:
                    self.ComponentsToUpdate[comp.TARGET].put(comp)
                except KeyError:
                    self.ComponentsToUpdate[comp.TARGET] = Queue()
                    self.ComponentsToUpdate[comp.TARGET].put(comp)
            else:
                try:
                    self.ComponentsToCheckout[comp.TARGET].put(comp)
                except KeyError:
                    self.ComponentsToCheckout[comp.TARGET] = Queue()
                    self.ComponentsToCheckout[comp.TARGET].put(comp)

    def checkout(self):
        keys = self.ComponentsToCheckout.keys()
        keys.sort()
        for target in keys:
            while not self.ComponentsToCheckout[target].empty():
                c = self.ComponentsToCheckout[target].get()
                pprint(vars(c))
                c.checkout()

    def update(self):
        keys = self.ComponentsToUpdate.keys()
        keys.sort()
        for target in keys:
            while not self.ComponentsToUpdate[target].empty():
                c = self.ComponentsToUpdate[target].get()
                c.update()


class Component(object):
    """
    Base class for components. Provides __init__(), __str__(),
    and exists() methods.
    """

    def __init__(self, directives):
        # initialize all possible attributes
        self.TARGET = None
        self.TYPE = None
        self.CHECKOUT = None
        self.URL = None
        self.AUTH_URL = None
        self.NAME = None
        self.REPO_PATH = None
        self.USER = None
        self.ANON_USER = None
        self.ANON_PASS = None
        self.LOC_PATH = None
        self.DIR = None

        # now replace attributes with proper values
        for k, v in directives.iteritems():
            # make sure that directives are properly defined
            if not hasattr(self, k):
                raise InvalidDirectiveError(k)
            setattr(self, k, v)

        # DIR = defined(NAME) ? NAME : CHECKOUT
        if self.NAME is not None:
            self.DIR = self.NAME
        else:
            self.DIR = self.CHECKOUT

    def __str__(self):
        """
        Output all attributes of the Component instance. Eventually this
        will output just the directives in CRL format.
        """

        attr_dict = vars(self)
        strings = []
        for k, v in attr_dict.iteritems():
            if v is not None:
                strings.append("%s = %s\n" % (k, v))
        #strings.sort()
        return ''.join(strings)

# add() should be deprecated
#     def add(self, k, v):
#         if k == 'TARGET':
#             self.TARGET = v
#
#         elif k == 'TYPE':
#             self.TYPE = v
#
#         elif k == 'CHECKOUT':
#             self.CHECKOUT = v
#
#         elif k == 'NAME':
#             self.NAME = v.strip()
#
#         elif k == 'URL':
#             self.URL = v
#
#         elif k == 'AUTH_URL' or k == 'AUTHORIZATION_URL':
#             self.AUTH_URL = v
#
#         elif k == 'ANON_USER' or k == 'ANONYMOUS_USER':
#             self.ANON_USER = v
#
#         elif k == 'ANON_PASS' or k == 'ANONYMOUS_PASSWORD':
#             self.ANON_PASS = v
#
#         elif k == 'REPO_PATH' or k == 'REPOSITORY_PATH':
#             self.REPO_PATH = v
#
#         elif k == 'LOC_PATH' or k == 'LOCAL_PATH':
#             self.LOC_PATH = v
#
#         else:
#             raise InvalidDirectiveError(k)

    def exists(self):
        if self.NAME is not None:
            self.DIR = self.NAME
        else:
            self.DIR = self.CHECKOUT

        if os.path.exists(os.path.join(BASE_DIR, self.TARGET, self.DIR)):
            return True

#         elif self.TARGET == DEFINITIONS['ROOT'] and os.path.exists(os.path.join(BASE_DIR, self.TARGET)):
#             return True

        else:
            return False

    def checkout(self):
        pass

    def update(self):
        pass

    def verify_url(self):
        pass

    def status(self):
        pass

    def diff(self):
        pass

    def authenticate(self):
        pass


class cvsComponent(Component):
    """
    Extends Component class for use with CVS.
    Provides additional checkout(), update(), and authenticate() methods
    """

    CVS = None

    def __init(self, directives):
        Component.__init__(self, directives)

        if cvsComponent.CVS is None:
            if run_command("cvs --help", QUIET):
                cvsComponent.CVS = "cvs"
            else:
                cvsComponent.CVS = raw_input("Could not find cvs. Please enter the path: ")
                while not run_command("cvs --help", QUIET):
                    cvsComponent.CVS = raw_input("Bad path. Try again: ")

    def exists(self):
        if self.NAME is not None:
            self.DIR = self.NAME
        else:
            self.DIR = self.CHECKOUT

        if os.path.exists(os.path.join(BASE_DIR, self.TARGET, self.DIR, 'CVS')):
            return True

#         elif self.TARGET == DEFINITIONS['ROOT'] and os.path.exists(os.path.join(BASE_DIR, self.TARGET, 'CVS')):
#             return True

        else:
            return False

    def checkout(self):
        tmpdir = ".GetComponents-tmp-%s" % os.getpid()
        shutil.rmtree(tmpdir)
        cmd = [CVS, "-q -d", self.URL, "checkout -d", tmpdir, self.CHECKOUT]
        print_checkout_info(self.CHECKOUT, self.URL, self.TARGET, self.NAME)
        if not run_command(cmd):
            print "Could not checkout %s." % self.DIR
            return False
        os.makedirs(self.DIR)
        cmd = "mv %s/* %s" % (tmpdir, self.NAME)
        shutil.rmtree(tmpdir)
        return True



class svnComponent(Component):
    """
    Extends Component class for use with subversion.
    Provides additional checkout(), update(), and authenticate() methods.
    Overloads exists() method.
    """

    SVN = None

    def __init__(self, directives):
        Component.__init__(self, directives)

        if self.USER is not None:
            self.USER = "--username %s" % self.USER
        else:
            self.USER = ''

        if svnComponent.SVN is None:
            if run_command("svn --help", QUIET):
                svnComponent.SVN = "svn"
            else:
                svnComponent.SVN = raw_input("Could not find svn. Please enter the path: ")
                while not run_command("svn --help", QUIET):
                    svnComponent.SVN = raw_input("Bad path. Try again: ")

    def exists(self):
        if self.NAME is not None:
            self.DIR = self.NAME
        else:
            self.DIR = self.CHECKOUT

        if os.path.exists(os.path.join(BASE_DIR, self.TARGET, self.DIR, '.svn')):
            return True

#         elif self.TARGET == DEFINITIONS['ROOT'] and os.path.exists(os.path.join(BASE_DIR, self.TARGET, '.svn')):
#             return True

        else:
            return False

    def checkout(self):
        cmd = "%s checkout %s %s %s %s" % (SVN, self.USER, self.DATE, self.URL,
                os.path.join(BASE_DIR, self.TARGET, self.DIR))
        print_checkout_info(self.CHECKOUT, self.URL, self.TARGET, self.NAME)
        if run_command(cmd):
            return True
        else:
            return False

    def update(self):
        cmd = "%s update %s" % (SVN, os.path.join(
            BASE_DIR, self.TARGET, self.DIR))
        print_update_info(self.CHECKOUT, self.URL, self.TARGET, self.NAME)
        if run_command(cmd):
            return True
        else:
            return False


class gitComponent(Component):
    """
    Extends Component class for use with git.
    Provides additional checkout(), update(), and authenticate() methods
    """

    GIT = None

    def __init__(self, directives):
        Component.__init__(self, directives)


class hgComponent(Component):
    """
    Extends Component class for use with mercurial.
    Provides additional checkout(), update(), and authenticate() methods
    """
    pass


class darcsComponent(Component):
    """
    Extends Component class for use with darcs.
    Provides additional checkout(), update(), and authenticate() methods
    """
    pass


class webComponent(Component):
    """
    Extends Component class for use with http/ftp.
    Provides additional checkout() and update() methods
    """

    def __init__(self, directives):
        Component.__init__(self, directives)

    def checkout(self):

        dirname = os.path.dirname(self.CHECKOUT)
        filename = os.path.basename(self.CHECKOUT)
        targetdir = os.path.join(BASE_DIR, self.TARGET)

        try:
            os.chdir(targetdir)
        except OSError:
            os.makedirs(targetdir)
            os.chdir(targetdir)

        if dirname != '':
            os.makedirs(os.path.dirname(dirname))

        f = urllib2.urlopen(self.URL)

        try :
            fptr = open(filename, 'w')
        except IOError:
            print "Could not open %s" % self.CHECKOUT
            return False

        fptr.write(f.read())
        fptr.close()

    def update(self):

        dirname = os.path.dirname(self.CHECKOUT)
        filename = os.path.basename(self.CHECKOUT)
        targetdir = os.path.join(BASE_DIR, self.TARGET)

        os.chdir(os.path.join(targetdir, dirname))

        f = urllib2.urlopen(self.URL)

        try :
            fptr = open(filename, 'w')
        except IOError:
            print "Could not open %s" % self.CHECKOUT
            return False

        fptr.write(f.read())
        fptr.close()


class InvalidDirectiveError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value + ' is not a valid directive')


class InvalidTypeError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value + ' is not a valid type')


def list_to_dict(list):
    """Convert a list with an even number of items into a dict"""
    d = {}
    for i in range(len(list)/2):
        d[list[2*i]] = list[2*i+1]
    return d


def print_checkout_info(checkout, url, target, name):
    msg = '''-------------------------------------------------------
    Checking out module: %s
        from repository: %s
                   into: %s''' % (checkout, url, target)
    if name is not None:
        msg = msg + '                 as: %s' % name
    print msg


def print_update_info(checkout, url, target, name):
    msg = '''-------------------------------------------------------
    Updating module: %s
    from repository: %s
         located in: %s''' % (checkout, url, target)
    if name is not None:
        msg = msg + '          under: %s' % name
    print msg


def run_command(cmd, verbose=Options.verbose):
    if cmd == '':
        return

    if verbose >= 2:
        print os.getcwd()
        print cmd

        out = os.popen(cmd+" 2>&1")
        err = ''
        for line in out.readlines():
            if re.match('^cvs|^svn|^error|^fatal|^abort', line):
                err = err + line
            print line
        ret = out.close()
        if ret is None:
            return True
        else:
            return False

    elif verbose == 1 and not re.match('^ln|^mkdir|^mv|^rm|^rmdir|^which', cmd):
        out = os.popen(cmd+" 2>&1 1>/dev/null")
        err = ''
        for line in out.readlines():
            if re.match('^cvs|^svn|^error|^fatal|^abort', line):
                err = err + line
            print line
        ret = out.close()
        if ret is None:
            return True
        else:
            return False

    else:
        out = os.popen(cmd+" 2>&1")
        err = ''
        for line in out.readlines():
            if re.match('^cvs|^svn|^error|^fatal|^abort', line):
                err = err + line
                print line
        ret = out.close()
        if ret is None:
            return True
        else:
            return False


#############################################################
if __name__ == '__main__':
    main()
