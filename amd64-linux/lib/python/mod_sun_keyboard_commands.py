
##  Copyright 2003-2007 Virtutech AB
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

#
# -------------------- key-down, key-up --------------------
#

def key_down_cmd(obj, key_code):
    SIM_set_attribute_idx(obj, "key-event", key_code, 0)


def key_up_cmd(obj, key_code):
    SIM_set_attribute_idx(obj, "key-event", key_code, 1)

new_command("key-down", key_down_cmd,
            [arg(int_t, "key-code")], # <b>key-down</b> <i>keycode</i>
            alias = "",
            type  = "sun-keyboard commands",
            short = "send key event",
	    namespace = "sun-keyboard",
            doc = """
Send a key press to the keyboard controller.
The argument is the internal Simics keycode.
""", filename="/mp/simics-3.0/src/devices/sun-keyboard/commands.py", linenumber="34")

new_command("key-up", key_up_cmd,
            [arg(int_t, "key-code")], # <b>key-up</b> <i>keycode</i>
            alias = "",
            type  = "sun-keyboard commands",
            short = "send key event",
	    namespace = "sun-keyboard",
            doc_with = "<sun-keyboard>.key-down", filename="/mp/simics-3.0/src/devices/sun-keyboard/commands.py", linenumber="45")
