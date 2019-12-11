
##  Copyright 2005-2007 Virtutech AB
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
from cli_impl import new_object_name
from tracker import register_tracker

class_name = "cpu-mode-tracker"

def new_cpu_mode_tracker_cmd(name):
    real_name = new_object_name(name, "tracker")
    if real_name == None:
        print "An object called '%s' already exists." % name
        SIM_command_has_problem()
        return
    else:
        name = real_name
    SIM_create_object(class_name, name, [])
    if SIM_is_interactive():
        print "New cpu mode tracker %s created." % name
    return (name, )

new_command("new-" + class_name, new_cpu_mode_tracker_cmd,
            [arg(str_t, "name", "?", None)],
            type = "Debugging",
            see_also = ["new-context-switcher", "<tracker>.add-processor"],
            short = "create new cpu mode tracker",
            doc = """

Create a new cpu mode tracker. The tracker's set of processors will
initially be empty. You can add the processors you want it to watch
with its add-processors command.""")

register_tracker(class_name)
