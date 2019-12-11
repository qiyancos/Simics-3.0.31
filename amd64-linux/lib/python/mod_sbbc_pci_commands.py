
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

def get_info(obj):
    return ([(None,
              [("System Console", obj.sc)])]
            + sim_commands.get_pci_info(obj))

sim_commands.new_info_command("sbbc-pci", get_info)

def get_status(obj):
    return ([("Registers",
              [("Interrupt Enable", "0x%x" % obj.interrupt_enable),
               ("Interrupt Status", "0x%x" % obj.interrupt_status),
               ("EPLD Interrupt", "0x%x" % obj.epld_interrupt),
               ("Irq Generation 0", "0x%x" % obj.irq_generation_0),
               ("Irq Generation 1", "0x%x" % obj.irq_generation_1)]),
             (None,
              [("Access info", iff(obj.access_info, "enabled", "disabled"))])]
            + sim_commands.get_pci_status(obj))

sim_commands.new_status_command("sbbc-pci", get_status)

sim_commands.new_pci_header_command("sbbc-pci", None)

#
# ----------------- access-debug -----------------
#

def access_info_cmd(obj):
    try:
        cur = obj.access_info
        obj.access_info = 1 - cur
        print "%sabling access info" % iff(cur == 0, "En", "Dis")
    except Exception, msg:
        print msg
    
new_command("access-info", access_info_cmd,
            [],
            type  = "sbbc-pci commands",
            namespace = "sbbc-pci",
            short = "toggle debug output for IOSRAM accesses",
            doc = """
            When access info debugging is enabled, the sbbc-pci device
            will print where the IOSRAM is accessed.<br/>
""", filename="/mp/simics-3.0/src/devices/sbbc-pci/commands.py", linenumber="58")

#
# -------------------- ignore --------------------
#

def ignore_cmd(obj, str):
    if str == "":
        try:
            ignore = obj.access_ignore[:]
        except Exception, msg:
            print "Empty list"
            return
        print "access-info will ignore the following strings:"
        print "----------------------------------------------"
        for i in range(len(ignore)):
            print "%s" % ignore[i]
        print
    else:
        try:
            obj.access_ignore[-1] = str
        except Exception, msg:
            print msg
    
new_command("access-ignore", ignore_cmd,
            [arg(str_t, "ignore-str", "?", "")],
            type  = "sbbc-pci commands",
            namespace = "sbbc-pci",
            short = "add string to ignore for access info",
            doc = """
            Adds a string to the list of strings that will be ignored
            when access-info debugging is enabled. Adding a string
            a second time will remove it from the list.<br/>
""", filename="/mp/simics-3.0/src/devices/sbbc-pci/commands.py", linenumber="90")
