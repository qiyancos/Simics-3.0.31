
##  Copyright 2000-2007 Virtutech AB
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

from cli import *
import time

#
# -------------------- set-time-current -----------------
#

def set_time_current_cmd(obj):
    try:
        obj.time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time()))
    except Exception, y:
        print "Error setting time in the MK48T08 device: %s" % y

new_command("set-time-current", set_time_current_cmd,
            [],
            alias = "",
            type  = "MK48T08 commands",
            short = "set date and time to the current (real) time",
	    namespace = "MK48T08",
            doc = """
Set the date and time to the actual wall clock time.
""", filename="/mp/simics-3.0/src/devices/MK48T08/commands.py", linenumber="34")

#
# -------------------- set-time --------------------
#

def set_time_cmd(obj, time_str):
    try:
        SIM_set_attribute(obj, "time", time_str)
    except Exception, y:
	print "Error setting time in MK48T08 device: %s" % y

new_command("set-time", set_time_cmd,
            [arg(str_t, "time")],
            alias = "",
            type  = "MK48T08 commands",
            short = "set date and time",
	    namespace = "MK48T08",
            doc = """
Set the date and time of the realtime clock (UTC).
Format is: "YYYY-MM-DD HH:MM:SS".
""", filename="/mp/simics-3.0/src/devices/MK48T08/commands.py", linenumber="54")


#
# -------------------- get-time --------------------
#

def get_time_cmd(obj):
    print "Time: %s" % SIM_get_attribute(obj, "time")
    
new_command("get-time", get_time_cmd,
            [],
            alias = "",
            type  = "MK48T08 commands",
            short = "get date and time",
	    namespace = "MK48T08",
            doc = """
Return the date and time of the realtime clock (UTC).<br/>
""", filename="/mp/simics-3.0/src/devices/MK48T08/commands.py", linenumber="73")
