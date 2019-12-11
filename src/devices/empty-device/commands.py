
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

# increment command
def increment_value_cmd(obj):
    try:
        obj.value += 1
        print "The new counter value is:", obj.value
    except Exception, msg:
        print "Error incrementing counter:", msg

new_command("increment", increment_value_cmd, [],
            alias = "",
            type  = "empty-device commands",
            short = "increment value",
	    namespace = "empty-device",
            doc = """
Increments the value by adding 1 to it.
""")

#
# ------------------------ info -----------------------
#

def get_info(obj):
    # USER-TODO: Return something useful here
    return []

sim_commands.new_info_command('empty-device', get_info)

#
# ------------------------ status -----------------------
#

def get_status(obj):
    # USER-TODO: Return something useful here
    return [("Internals",
             [("Attribute 'value'", SIM_get_attribute(obj, "value"))])]

sim_commands.new_status_command('empty-device', get_status)
