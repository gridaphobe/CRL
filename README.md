GetComponents
=============
[GetComponents][] is a tool designed to facilitate the task of retrieving
a large set of software components from multiple versioning systems.
Currently it supports cvs, svn, git, mercurial, darcs, and http/ftp checkouts
and updates. It is based on the GetCactus tool that was designed for the
[Cactus Framework][cctk], however GetComponents is designed as a general-purpose
tool. To use GetComponents, you must have a component list in the Component
Retrieval Language (CRL), which has been designed in conjunction with
[GetComponents.

Usage
-----
    ./GetComponents [options] [file]
    ./GetComponents [options] [url]

Author
------
[Eric Seidel][eseidel]

<eric@eseidel.org>

[eseidel]:http://www.eseidel.org
[GetComponents]:http://www.eseidel.org/projects/GetComponents
[cctk]:http://www.cactuscode.org