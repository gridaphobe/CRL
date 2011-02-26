GetComponents
=============
[GetComponents][] is a tool designed to facilitate the task of retrieving
a large set of software components from multiple versioning systems.
Currently it supports cvs, svn, git, mercurial, darcs, and http/ftp checkouts
and updates. It is based on the GetCactus tool that was designed for the
[Cactus Framework][cctk], however GetComponents is designed as a general-purpose
tool. To use GetComponents, you must have a component list in the Component
Retrieval Language (CRL), which has been designed in conjunction with
GetComponents.

Usage
-----
    ./GetComponents [options] [file|URL]

GetComponents will accept a CRL file specified locally or remotely, in which
case it will download the remote file. It can checkout and update components
(also from a specific date), show the status of all components, and do a diff
on all components.

For a full overview of the options and the CRL syntax look at the [wiki][]
or look at the built-in documentation with

    ./GetComponents --man

Example
-------
If you want to try GetComponents without building your own component list, try
checking out the [Einstein Toolkit][et]. It's an open source toolkit for solving
relativistic equations, and is using GetComponents as its primary means of
distribution.

    ./GetComponents --anonymous http://svn.einsteintoolkit.org/branches/ET_2010_11/einsteintoolkit.th

Notes
-----
There are 3 scripts in this repository. GetComponents is the main script and
is fully functional. It is stable and safe to use, however there is also an
older version in the stable branch, which coincides with the June 2010 release
of the Einstein Toolkit. 

The other scripts in the master branch are incomplete
and unstable. py_components.py is an implementation of CRL in Python, which
eventually will succeed the current Perl implementation when I have time to
finish it. generateCRL.py is basically a reverse GetComponents script. It will
analyze the contents of the working directory and generate a CRL file, 
allowing you to checkout the same items on another computer without having
to write the CRL yourself. It is very new and only supports svn and cvs right 
now (it will not produce the correct checkout path if you used 
`cvs checkout -d`").

Author
------
[Eric Seidel][eseidel]

[eseidel]:http://eseidel.org
[GetComponents]:http://eseidel.org/projects/getcomponents
[cctk]:http://www.cactuscode.org
[wiki]:http://github.com/gridaphobe/CRL/wiki
[et]:http://www.einsteintoolkit.org
