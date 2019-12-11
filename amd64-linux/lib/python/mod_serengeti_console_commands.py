
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
import time, string

#
# -------------------- set-time-current -----------------
#

def set_time_current_cmd(obj):
    try:
        obj.time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time()))
    except Exception, y:
        print "Error setting time in serengeti-console device: %s" % y

new_command("set-time-current", set_time_current_cmd,
            [],
            alias = "",
            type  = "serengeti-console commands",
            short = "set date and time to the current (real) time",
            namespace = "serengeti-console",
            doc = """
Set the date and time to the actual wall clock time.
""", filename="/mp/simics-3.0/src/extensions/serengeti-console/commands.py", linenumber="35")

#
# -------------------- set-time --------------------
#

def set_time_cmd(obj, time_str):
    try:
        obj.time = time_str
    except Exception, y:
        print "Error setting time in serengeti-console device: %s" % y

new_command("set-time", set_time_cmd,
            [arg(str_t, "time")],
            alias = "",
            type  = "serengeti-console commands",
            short = "set date and time",
            namespace = "serengeti-console",
            doc = """
Set the date and time of the realtime clock (UTC).
Format is: "YYYY-MM-DD HH:MM:SS".
""", filename="/mp/simics-3.0/src/extensions/serengeti-console/commands.py", linenumber="55")

#
# -------------------- get-time --------------------
#

def get_time_cmd(obj):
    print "Time: %s" % obj.time

new_command("get-time", get_time_cmd,
            [],
            alias = "",
            type  = "serengeti-console commands",
            short = "get date and time",
            namespace = "serengeti-console",
            doc = """
Return the date and time of the realtime clock (UTC).<br/>
""", filename="/mp/simics-3.0/src/extensions/serengeti-console/commands.py", linenumber="73")


#
# ---------------------- info ----------------------
#

def get_boards(obj):
    stat = []
    for bd in obj.boards:
        type = '%s board' % bd[1].upper()
        if bd[1].startswith('cpu'):
            type += ' - %d processor%s @ %d MHz' % (bd[2],
                                                    iff(bd[2] > 1, 's', ''),
                                                    bd[3])
        stat += [('Slot %d' % bd[0], type)]
    return stat

def get_mem_banks(obj):
    stat = []
    for i in range(len(obj.mem_banks)):
        mb = obj.mem_banks[i]
        stat += [('Bank %d' % i,
                  'CPU: %d   Bank ID: %d   Size: %d MB' % 
                  (mb[0], mb[1], mb[2]))]
    return stat

def get_sc_info(obj):
    return ([("Configuration",
             [("Text Console", obj.console),
              ("NVCI Object", obj.nvci),
              ("IOSRAM-SBBC", obj.iosram_sbbc),
              ("Interrupt Bus", obj.irq_bus),
              ("Recorder", obj.recorder)]),
            (None,
             [("Chassis Type", obj.chassis_type)])]
            + [("Boards",
                get_boards(obj))]
            + [("Memory Banks",
                get_mem_banks(obj))])

sim_commands.new_info_command("serengeti-console", get_sc_info)

#
# --------------------- status ---------------------
#

# No status to report

#
# --------------- NVCI COMMANDS ----------
#

def get_nvci_info(obj):
    return []

sim_commands.new_info_command("nvci", get_nvci_info)

def list_variables_cmd(obj):
    import serengeti_system
    print "Warning: '<nvci>.list-variables' is deprecated. Use '<serengeti-system>.get-prom-env' instead."
    serengeti_system.get_prom_env(conf.system, "")

new_command("list-variables", list_variables_cmd,
            [],
            alias = "",
            type  = "nvci commands",
            short = "deprecated command",
            deprecated = "<serengeti-6800-chassis>.get-prom-env",
            namespace = "nvci",
            doc = "", filename="/mp/simics-3.0/src/extensions/serengeti-console/commands.py", linenumber="144")

def get_variable_cmd(obj, str):
    import serengeti_system
    print "Warning: '<nvci>.get-variable' is deprecated. Use '<serengeti-system>.get-prom-env' instead."
    serengeti_system.get_prom_env(conf.system, string.replace(str, "Q", "?"))

new_command("get-variable", get_variable_cmd,
            [arg(str_t, "var-name")],
            alias = "",
            type  = "nvci commands",
            short = "deprecated command",
            deprecated = "<serengeti-6800-chassis>.get-prom-env",
            namespace = "nvci",
            doc = "", filename="/mp/simics-3.0/src/extensions/serengeti-console/commands.py", linenumber="158")

def set_variable_cmd(obj, str, val):
    import serengeti_system
    print "Warning: '<nvci>.set-variable' is deprecated. Use '<serengeti-system>.set-prom-env' instead."
    serengeti_system.set_prom_env(conf.system, string.replace(str, "Q", "?"), val)

new_command("set-variable", set_variable_cmd,
            [arg(str_t, "var-name"),
             arg((int_t, str_t), ("int", "string"))],
            alias = "",
            type  = "nvci commands",
            short = "deprecated command",
            namespace = "nvci",
            deprecated = "<serengeti-6800-chassis>.set-prom-env",
            doc = "", filename="/mp/simics-3.0/src/extensions/serengeti-console/commands.py", linenumber="172")
