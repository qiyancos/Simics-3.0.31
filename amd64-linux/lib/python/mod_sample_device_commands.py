
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
import sim_commands

#
# ------------------------ info -----------------------
#

def get_sample_info(obj):
    return []

sim_commands.new_info_command('sample-device', get_sample_info)

#
# ------------------------ status -----------------------
#

def get_sample_status(obj):
    return [(None,
             [("Attribute 'value'", obj.value)])]

sim_commands.new_status_command('sample-device', get_sample_status)

#
# ------------------------ add-log -----------------------
#

def add_log_cmd(obj, str):
    try:
        obj.add_log = str
    except Exception, msg:
        print "Error adding log string: %s" % msg


new_command("add-log", add_log_cmd,
            [arg(str_t, "log-string", "?", "default text")],
            alias = "",
            type  = "sample-device commands",
            short = "add a text line to the device log",
	    namespace = "sample-device",
            doc = """
Add a line of text to the device log. Use the 'io' command to view the log.<br/>
""", filename="/mp/simics-3.0/src/devices/sample-device/commands.py", linenumber="54")

#
# ---------------------- range-sum -----------------------
#

def sum_cmd(obj, start, end):
    try:
        sum = SIM_get_attribute_idx(obj, "range-sum", [start, end])
        print "The range sum [%d - %d] equals: %d" % (start, end, sum)
    except Exception, msg:
        print "Error calculating sum: %s" % msg


new_command("range-sum", sum_cmd,
            [arg(int_t, "start"), arg(int_t, "end")],
            alias = "",
            type  = "sample-device commands",
            short = "calculate range sum",
	    namespace = "sample-device",
            doc = """
Calculate the sum of all integers from 'start' to 'end'.
""", filename="/mp/simics-3.0/src/devices/sample-device/commands.py", linenumber="76")
