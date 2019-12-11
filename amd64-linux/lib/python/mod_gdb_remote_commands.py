
##  Copyright 2001-2007 Virtutech AB
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

def signal_cmd(obj, signal):
    SIM_set_attribute(obj, "signal", signal)

new_command("signal", signal_cmd,
            [arg(int_t, "signal")],
            type  = "symbolic debugging commands",
            short = "tell remote gdb we got a signal",
	    namespace = "gdb-remote",
            doc = """
Send a signal to the remote GDB. See the Simics User Guide for a
longer description of gdb-remote.
""", filename="/mp/simics-3.0/src/extensions/gdb-remote/commands.py", linenumber="27")

def disconnect_cmd(obj):
    SIM_set_attribute(obj, "disconnect", 0)

new_command("disconnect", disconnect_cmd,
            [],
            type  = "symbolic debugging commands",
            short = "disconnect from the remote gdb",
	    namespace = "gdb-remote",
            doc = """
Disconnect from the remote GDB. See the Simics User Guide for a longer
description of gdb-remote.
""", filename="/mp/simics-3.0/src/extensions/gdb-remote/commands.py", linenumber="40")

def target_cmd(obj, cpu):
    if cpu:
        obj.queue = cpu
        obj.context_object = cpu.current_context
    print "Target for %s: %s" % (obj.name, obj.queue)

new_command("target", target_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?")],
            type = "symbolic debugging commands",
            short = "set target CPU for gdb connection",
            namespace = "gdb-remote",
            doc = """
Set the target CPU for this remote GDB connection. One GDB connection
can only debug instructions on a single CPU at a time.
""", filename="/mp/simics-3.0/src/extensions/gdb-remote/commands.py", linenumber="56")

def follow_context_cmd(gdb, ctxt):
    if ctxt is None:
        if gdb.follow_context:
            print "Stopped following %s." % gdb.context_object
            gdb.follow_context = 0
        else:
            print "Not following any context."
    else:
        gdb.context_object = ctxt
        gdb.follow_context = 1
        print "Started following %s." % ctxt

new_command("follow-context", follow_context_cmd,
            [arg(obj_t('context', 'context'), "context", "?")],
            type = "symbolic debugging commands",
            short = "follow context",
            namespace = "gdb-remote",
            doc = """
Set the GDB session to follow <arg>context</arg>.  If <arg>context</arg>
is not specified, the GDB session will stop following any context.""", filename="/mp/simics-3.0/src/extensions/gdb-remote/commands.py", linenumber="78")

def get_info(gdb):
    """Return information about gdb object as list of (doc, value)
    tuples."""
    return ([ (None,
               [ ("Architecture",	gdb.architecture),
                 ("Listen port",	gdb.listen),
                 ("Processor",		gdb.processor),
                 ("Context",		gdb.context_object),
                 ("Follow context",	iff(gdb.follow_context, "enabled",
                                            "disabled"))
                 ] )
              ])

sim_commands.new_info_command("gdb-remote", get_info)
