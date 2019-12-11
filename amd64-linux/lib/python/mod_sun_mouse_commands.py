
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
# -------------------- left-button, right-button --------------------
#

def right_button_cmd(obj, dir):
    if dir == "up":
        SIM_set_attribute_idx(obj, "button-event", 1, 1)
    elif dir == "down":
        SIM_set_attribute_idx(obj, "button-event", 1, 0)
    else:
	print "Unknown button direction: %s" % dir


def left_button_cmd(obj, dir):
    if dir == "up":
        SIM_set_attribute_idx(obj, "button-event", 0, 1)
    elif dir == "down":
        SIM_set_attribute_idx(obj, "button-event", 0, 0)
    else:
	print "Unknown button direction: %s" % dir

def middle_button_cmd(obj, dir):
    if dir == "up":
        SIM_set_attribute_idx(obj, "button-event", 2, 1)
    elif dir == "down":
        SIM_set_attribute_idx(obj, "button-event", 2, 0)
    else:
	print "Unknown button direction: %s" % dir

def up_down_expander(string):
	return get_completions(string, ("up", "down"))

new_command("right-button", right_button_cmd,
            [arg(str_t, "direction", expander = up_down_expander)], # <b>right-button</b> up|down
            alias = "",
            type  = "sun-mouse commands",
            short = "set button state",
	    namespace = "sun-mouse",
            doc = """
Set the state of the left or right mouse button.
Valid arguments are "up" and "down".""", filename="/mp/simics-3.0/src/devices/sun-mouse/commands.py", linenumber="55")

new_command("left-button", left_button_cmd,
            [arg(str_t, "direction", expander = up_down_expander)], # <b>left-button</b> up|down
            alias = "",
            type  = "sun-mouse commands",
            short = "set button state",
	    namespace = "sun-mouse",
            doc_with = "<sun-mouse>.right-button", filename="/mp/simics-3.0/src/devices/sun-mouse/commands.py", linenumber="65")

new_command("middle-button", middle_button_cmd,
            [arg(str_t, "direction", expander = up_down_expander)], # <b>middle-button</b> up|down
            alias = "",
            type  = "sun-mouse commands",
            short = "set button state",
	    namespace = "sun-mouse",
            doc_with = "<sun-mouse>.right-button", filename="/mp/simics-3.0/src/devices/sun-mouse/commands.py", linenumber="73")

#
# -------------------- mouse-up, mouse-down, mouse-left, mouse-right --------------------
#

def mouse_up_cmd(obj, delta):
    SIM_set_attribute_idx(obj, "mouse-event", 0, delta)

def mouse_down_cmd(obj, delta):
    SIM_set_attribute_idx(obj, "mouse-event", 1, delta)

def mouse_left_cmd(obj, delta):
    SIM_set_attribute_idx(obj, "mouse-event", 2, delta)

def mouse_right_cmd(obj, delta):
    SIM_set_attribute_idx(obj, "mouse-event", 3, delta)

new_command("mouse-up", mouse_up_cmd,
            [arg(int_t, "millimeters")],
            alias = "",
            type  = "sun-mouse commands",
            short = "move mouse",
	    namespace = "sun-mouse",
            doc = """
Move the mouse up/down/left/right a specified number of millimeters.<br/>
""", filename="/mp/simics-3.0/src/devices/sun-mouse/commands.py", linenumber="97")

new_command("mouse-down", mouse_down_cmd,
            [arg(int_t, "millimeters")],
            alias = "",
            type  = "sun-mouse commands",
            short = "move mouse",
	    namespace = "sun-mouse",
            doc_with = "<sun-mouse>.mouse-up", filename="/mp/simics-3.0/src/devices/sun-mouse/commands.py", linenumber="107")

new_command("mouse-right", mouse_right_cmd,
            [arg(int_t, "millimeters")],
            alias = "",
            type  = "sun-mouse commands",
            short = "move mouse",
	    namespace = "sun-mouse",
            doc_with = "<sun-mouse>.mouse-up", filename="/mp/simics-3.0/src/devices/sun-mouse/commands.py", linenumber="115")

new_command("mouse-left", mouse_left_cmd,
            [arg(int_t, "millimeters")],
            alias = "",
            type  = "sun-mouse commands",
            short = "move mouse",
	    namespace = "sun-mouse",
            doc_with = "<sun-mouse>.mouse-up", filename="/mp/simics-3.0/src/devices/sun-mouse/commands.py", linenumber="123")
