#!/usr/bin/env python

##  Copyright 2002-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.


# Execute a python script using a Python with a specified minimal version
# number.
# Usage: ./python.py -required <req_major>.<req_minor> <script> <args>

import sys
import os
import string

required_version = 0

# We could use getopt, but I'm not sure if really old Pythons have getopt.
for i in range(1, len(sys.argv)):
    if sys.argv[i] == "-required":
        (required_major, required_minor) = string.split(sys.argv[i+1], ".")
        required_version = int(required_major) << 24L | int(required_minor) << 16L
        # print "%x" % (required_version)
        del sys.argv[i:i+2]
        break

# print sys.argv
# print "%x" % (required_version)

bestpython = ( required_version, "" )

for p in string.split(os.environ['PATH'], ":"):
    try:
        for python in os.listdir(p):
            if string.find(python, "python") != -1:
                fullpython = os.path.join(p, python)
                cmd = "%s -c 'import sys; print sys.hexversion' 2>/dev/null" % (fullpython)
                try:
                    hexversion = int(string.strip(os.popen(cmd).readline()))
                except:
                    # If the python command failed; we probably encountered
                    # something which wasn't a python executable, so we
                    # just ignore it.
                    hexversion = 0
                    
                # print "%x" % (hexversion)
                if hexversion > bestpython[0]:
                    bestpython = ( hexversion, fullpython )
    except OSError, msg:
        pass

if bestpython[1] == "":
    print "Failed to find Python version %s.%s." % (required_major, required_minor)
    sys.exit(1)
    
sys.argv[0] = bestpython[1]
os.execv(bestpython[1], sys.argv)
