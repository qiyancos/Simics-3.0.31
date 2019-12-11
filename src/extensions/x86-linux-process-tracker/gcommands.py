
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

class_name = "x86-linux-process-tracker"

def x86_ptrack_settings_ifc():
    return SIM_get_class_interface(
        SIM_get_class(class_name), "tracker_settings")

def x86_linux_kernel_expander(string):
    return get_completions(
        string, x86_ptrack_settings_ifc().settings_id_list())

def new_x86_linux_process_tracker_cmd(name, pid_offset,
                                      kernel_stack_size, kernel):

    # Input validation.
    if (kernel_stack_size == None) != (pid_offset == None):
        print ("You must specify none or both of kernel_stack_size"
               + " and pid_offset.")
        return
    if kernel_stack_size == None and kernel == None:
        print ("You must specify either kernel, or kernel_stack_size"
               + " and pid_offset.")
        return
    if kernel_stack_size != None and kernel != None:
        print ("You cannot specify both kernel and"
               + " kernel_stack_size/pid_offset.")
        return

    # Choose a name.
    real_name = new_object_name(name, "tracker")
    if real_name == None:
        print "An object called '%s' already exists." % name
        return
    else:
        name = real_name

    # Using canned parameters?
    if kernel:
        if kernel in x86_ptrack_settings_ifc().settings_id_list():
            print ("Using parameters suitable for %s."
                   % x86_ptrack_settings_ifc().describe_settings(kernel))
        else:
            print "There is no named set of parameters called '%s'." % kernel
            return

    # Finally, create the tracker.
    tracker = SIM_create_object(class_name, name, [])
    if kernel:
        x86_ptrack_settings_ifc().use_settings(tracker, kernel)
    else:
        tracker.thread_offset = thread_offset
        tracker.pid_offset = pid_offset
    print "New process tracker %s created." % name
    print "    kernel_stack_size %d" % tracker.kernel_stack_size
    print "    pid_offset        %d" % tracker.pid_offset

new_command("new-" + class_name,
            new_x86_linux_process_tracker_cmd,
            [arg(str_t, "name", "?", None),
             arg(int_t, "pid_offset", "?", None),
             arg(int_t, "kernel_stack_size", "?", None),
             arg(str_t, "kernel", "?", None,
                 expander = x86_linux_kernel_expander)],
            type = "Debugging",
            see_also = ["new-context-switcher", "<tracker>.add-processor"],
            short = "create new x86-linux process tracker",
            doc = """

Create a new x86-linux process tracker. You must either specify the
<i>kernel_stack_size</i> and <i>pid_offset</i> integer parameters, or
choose a named set of parameters by giving the <i>kernel</i> argument.

The tracker's set of processors will initially be empty. You can add
the processors you want it to watch with its add-processors
command.""")

register_tracker(class_name)
