
##  Copyright 2004-2007 Virtutech AB
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

def gdb_remote(port, cpu):
    if not cpu:
        try:
            cpu = current_processor()
        except Exception, msg:
            print msg
            SIM_command_has_problem()
            return
    try:
        SIM_create_object("gdb-remote", "gdb-remote-%d" % port,
                          [["processor", cpu], ["listen", port]])
    except LookupError, msg:
        print "Failed creating a gdb-remote object: %s" % msg
        print "Make sure the gdb-remote module is available."
    except Exception, msg:
        print "Could not create a gdb-remote object: %s" % msg

new_command("gdb-remote", gdb_remote,
            args = [arg(uint32_t,                        "port", "?", 9123),
                    arg(obj_t("processor", "processor"), "cpu",  "?", "")],
            type = ["Symbolic Debugging", "Debugging"],
            short = "start gdb-remote",
            doc = """
Starts listening to incoming connection requests from GDB sessions (provided
that a configuration has been loaded). Simics will listen to TCP/IP requests on
port <arg>port</arg>, or 9123 by default. The GDB session will operate on the
specified <arg>cpu</arg>, or the currently selected cpu by default. Use the gdb
command <b>target remote <i>host</i></b><b>:<i>port</i></b> to connect to
Simics.
""", filename="/mp/simics-3.0/src/extensions/gdb-remote/gcommands.py", linenumber="40")

def new_gdb_remote(name, port, cpu, architecture):
    if not cpu:
        try:
            cpu = current_processor()
        except Exception, msg:
            print msg
            SIM_command_has_problem()
            return
    if not architecture:
        architecture = cpu.architecture
    if not name:
        for i in range(100):
            name = "gdb%d" % i
            try:
                SIM_get_object(name)
            except:
                break
    try:
        SIM_create_object("gdb-remote", name,
                          [["processor", cpu], ["architecture", architecture],
                           ["listen", port]])
    except LookupError, msg:
        print "Failed creating a gdb-remote object: %s" % msg
        print "Make sure the gdb-remote module is available."
    except Exception, msg:
        print "Could not create a gdb-remote object: %s" % msg

new_command("new-gdb-remote", new_gdb_remote,
            args = [arg(str_t,                           "name", "?", None),
                    arg(uint32_t,                        "port", "?", 9123),
                    arg(obj_t("processor", "processor"), "cpu",  "?", ""),
                    arg(str_t,                  "architecture",  "?", None)],
            type = ["Symbolic Debugging", "Debugging"],
            short = "create a gdb session",
            doc = """
Starts listening to incoming connection requests from GDB sessions
(provided that a configuration has been loaded). Simics will listen to
TCP/IP requests on port specified by <arg>port</arg>, or 9123 by default.
If <arg>port</arg> is given as zero, a random port will be selected. The
GDB session will operate on the specified <arg>cpu</arg>, or the currently
selected cpu by default.

The <arg>architecture</arg> argument can be used to specify a particular
architecture for the GDB session. It should be the architecture name used
by Simics and not the GDB architecture name. For example, if you are
debugging a 32-bit program on a 64-bit x86 processor, you may want to
specify <tt>x86</tt> as <arg>architecture</arg> and run <tt>set architecture i386</tt>
in GDB before connecting. If not given, the architecture of the CPU will
be used.

Use the GDB command <b>target remote <i>host</i></b><b>:<i>port</i></b> to
connect to Simics.  """, filename="/mp/simics-3.0/src/extensions/gdb-remote/gcommands.py", linenumber="81")

