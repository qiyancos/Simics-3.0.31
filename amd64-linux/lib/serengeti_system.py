
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

# docs...

# MODULE: serengeti-system
# CLASS: serengeti-system

from cli import *
from sim_core import *
from text_console_common import wait_for_string
import sim_commands, string

# The name of the class defined in this file, as a convenient shorthand
class_name = "serengeti-system"

instances = {}

class serengeti_system_instance:
    def __init__(self, conf_obj):
        global instances
        instances[conf_obj] = self
        self.obj = conf_obj

        self.mp_speedup_state = 0
        self.max_mem_address = 0
        self.master_cpu = None
        self.nvci = None
        self.all_cpus = []
        
    def mp_speedup(self):
        # small hack to make the boot be a bit faster. Once all cpus have
        # been started be the OBP and gone to sleep, we disable them until
        # the OS is about to start them again.
        if len(self.all_cpus) == 1:
            return
        if self.mp_speedup_state < 2:
            self.mp_speedup_state = 1
            bp_id = SIM_breakpoint(self.master_cpu.physical_memory,
                                   Sim_Break_Physical, Sim_Access_Execute,
                                   self.max_mem_address - 0x7f2be0, 4,
                                   Sim_Breakpoint_Simulation)
            wait_for_hap_idx("Core_Breakpoint", bp_id)
            SIM_delete_breakpoint(bp_id)
            SIM_log_message(self.obj, 1, 0, Sim_Log_Info,
                            "Disabling slave processors.")
            for o in self.all_cpus:
                if o != self.master_cpu:
                    SIM_disable_processor(o)
            self.mp_speedup_state = 2
        if self.mp_speedup_state == 2:
            # put a temporary breakpoint at the cross-cpu interrupt call
            bp_id = SIM_breakpoint(self.master_cpu.physical_memory,
                                   Sim_Break_Physical, Sim_Access_Execute,
                                   self.max_mem_address - 0x7efdd8, 4,
                                   Sim_Breakpoint_Simulation)
            wait_for_hap_idx("Core_Breakpoint", bp_id)
            SIM_delete_breakpoint(bp_id)
            SIM_log_message(self.obj, 1, 0, Sim_Log_Info,
                            "Enabling slave processors.")
            for o in self.all_cpus:
                if o != self.master_cpu:
                    SIM_enable_processor(o)
            self.mp_speedup_state = 3

def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    serengeti_system_instance(obj)
    return obj

mp_speedup_instance = None

def mp_speedup():
    mp_speedup_instance.mp_speedup()

def finalize_instance(obj):
    global mp_speedup_instance
    mp_speedup_instance = instances[obj]
    start_branch(mp_speedup)

def get_mp_speedup_state(data, obj, idx):
    return instances[obj].mp_speedup_state

def set_mp_speedup_state(data, obj, val, idx):
    instances[obj].mp_speedup_state = val
    return Sim_Set_Ok

def get_max_mem_address(data, obj, idx):
    return instances[obj].max_mem_address

def set_max_mem_address(data, obj, val, idx):
    instances[obj].max_mem_address = val
    return Sim_Set_Ok

def get_master_cpu(data, obj, idx):
    return instances[obj].master_cpu

def set_master_cpu(data, obj, val, idx):
    instances[obj].master_cpu = val
    return Sim_Set_Ok

def get_all_cpus(data, obj, idx):
    return instances[obj].all_cpus

def set_all_cpus(data, obj, val, idx):
    instances[obj].all_cpus = val
    return Sim_Set_Ok

def get_nvci(data, obj, idx):
    return instances[obj].nvci

def set_nvci(data, obj, val, idx):
    instances[obj].nvci = val
    return Sim_Set_Ok

# "init_local"

class_data = class_data_t()
class_data.new_instance = new_instance
class_data.finalize_instance = finalize_instance
class_data.description = """
The <class>serengeti-system</class> class is deprecated and only distributed
for compatibility with old configurations.
"""
SIM_register_class(class_name, class_data)

SIM_register_typed_attribute(class_name, "mp-speedup-state",
                             get_mp_speedup_state, None,
                             set_mp_speedup_state, None,
                             Sim_Attr_Optional,
                             "i", None,
                             "State of the speedup hack for multi-processor boot.")

SIM_register_typed_attribute(class_name, "max-mem-address",
                             get_max_mem_address, None,
                             set_max_mem_address, None,
                             Sim_Attr_Required,
                             "i", None,
                             "The highest memory (RAM) address in the machine.")

SIM_register_typed_attribute(class_name, "master-cpu",
                             get_master_cpu, None,
                             set_master_cpu, None,
                             Sim_Attr_Required,
                             "o", None,
                             "The master processor in the machine.")

SIM_register_typed_attribute(class_name, "all-cpus",
                             get_all_cpus, None,
                             set_all_cpus, None,
                             Sim_Attr_Required,
                             "[o*]", None,
                             "List of all processors in the machine.")

SIM_register_typed_attribute(class_name, "nvci",
                             get_nvci, None,
                             set_nvci, None,
                             Sim_Attr_Required,
                             "o", None,
                             "The 'nvci' object used for OBP variables.")

# commands

def mp_state(state):
    if state == 0:
        return "Inactive"
    elif state == 1:
        return "Active (Slave CPUs not yet disabled)"
    elif state == 2:
        return "Active (Slave CPUs disabled)"
    elif state == 3:
        return "Done (Slave CPUs running)"
    else:
        return "Uknown"
    
def get_info(obj):
    system = instances[obj]
    return [("Setup",
             [("Master CPU", system.master_cpu.name),
              ("NVCI object", system.nvci.name),
              ("Top of RAM", "0x%x" % system.max_mem_address)])]
                                                                                                               
def get_status(obj):
    system = instances[obj]
    return [("MP Speedup",
             [("Current state", mp_state(system.mp_speedup_state))])]

sim_commands.new_info_command(class_name, get_info)
sim_commands.new_status_command(class_name, get_status)

sys_attr = [ "queue", "attributes", "classname", "name", "object-id", "iface" ]

variable_list = {}

def check_variable_list(obj):
    if len(variable_list) > 0:
        return
    system = instances[obj]
    attrs = system.nvci.attributes
    for a in attrs:
        if sys_attr.count(a[0]) == 0:
            var = string.replace(a[0], "Q", "?")
            var = string.replace(var, "_", "-")
            variable_list[var] = a[0]

def set_prom_env(obj, env, val_tuple):
    check_variable_list(obj)
    if not variable_list.has_key(env):
        print "Unknown OBP variable '%s'" % env
        SIM_command_has_problem()
        return
    try:
        val = str(val_tuple[1])
        SIM_set_attribute(obj.nvci, variable_list[env], val)
    except Exception, msg:
        print "Failed setting variable: %s" % msg
        SIM_command_has_problem()

def get_prom_env(obj, env):
    check_variable_list(obj)
    if env == "":
        lst = variable_list.keys()
    elif not variable_list.has_key(env):
        print "Unknown OBP variable '%s'" % env
        SIM_command_has_problem()
        return
    else:
        lst = [env]
    for i in lst:
        print "%-30s  :  %s" % (i, SIM_get_attribute(obj.nvci, variable_list[i]))

def var_expand(string, obj):
    check_variable_list(obj)
    return get_completions(string, variable_list.keys())

new_command("set-prom-env", set_prom_env,
            [arg(str_t, "variable", expander = var_expand),
             arg((int_t, str_t), ("int", "string"))],
            short = "Set an OBP environment variable",
	    namespace = class_name,
            type = "deprecated commands",
            deprecated = "<serengeti-6800-chassis>.set-prom-env")

new_command("get-prom-env", get_prom_env,
            [arg(str_t, "variable", "?", "", expander = var_expand)],
            short = "Get an OBP environment variable",
	    namespace = class_name,
            type = "deprecated commands",
            deprecated = "<serengeti-6800-chassis>.get-prom-env")
