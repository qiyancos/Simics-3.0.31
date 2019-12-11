
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

# MODULE: sunfire-system
# CLASS: sunfire-system

from cli import *
from sim_core import *
from text_console_common import wait_for_string
import sim_commands

# The name of the class defined in this file, as a convenient shorthand
class_name = "sunfire-system"

instances = {}

class sunfire_system_instance:
    def __init__(self, conf_obj):
        global instances
        instances[conf_obj] = self
        self.obj = conf_obj

        self.mp_speedup_state = 0
        self.max_mem_address = 0
        self.master_cpu = None
        self.all_cpus = []
        self.slaves = 0
        
    def lock_entry_callback(self, arg, obj, access, bp_id, reg_ptr, size):
        SIM_log_message(self.obj, 2, 0, Sim_Log_Info,
                        "Locking entry 1 in D-TLB (temporarily).")
        mmu_trans = self.master_cpu.mmu.dtlb_daccess
        mmu_trans[1] = 0xc000020003c00076
        self.master_cpu.mmu.dtlb_daccess = mmu_trans
        VT_revexec_barrier()
        
    def lock_entry(self):
        # set a breakpoint where we only run once per boot
        bp_id = SIM_breakpoint(self.master_cpu.physical_memory,
                               Sim_Break_Physical, Sim_Access_Execute,
                               0x03c465c8, 4,
                               Sim_Breakpoint_Simulation)
        SIM_hap_add_callback_index("Core_Breakpoint",
                                   self.lock_entry_callback,
                                   None,
                                   bp_id)

    def mp_speedup(self):
        # small hack to make the boot be a bit faster. Once all cpus have
        # been started be the OBP and gone to sleep, we disable them until
        # the OS is about to start them again.
        if len(self.all_cpus) == 1:
            return
        if self.mp_speedup_state < 2:
            self.mp_speedup_state = 1
            map = self.master_cpu.physical_memory.map
            if map[0][1].class_data == "memory-space":
                space = map[0][1]
            else:
                space = self.master_cpu.physical_memory
            bp_id = SIM_breakpoint(space,
                                   Sim_Break_Physical, Sim_Access_Execute,
                                   self.max_mem_address - 0x27090, 4,
                                   Sim_Breakpoint_Simulation)
            while self.slaves < (len(self.all_cpus) - 1):
                wait_for_hap_idx("Core_Breakpoint", bp_id)
                SIM_disable_processor(SIM_current_processor())
                self.slaves += 1
            SIM_delete_breakpoint(bp_id)
            SIM_log_message(self.obj, 1, 0, Sim_Log_Info,
                            "Disabling slave processors.")
            self.mp_speedup_state = 2
        if self.mp_speedup_state == 2:
            # put a temporary breakpoint at the cross-cpu interrupt call
            bp_id = SIM_breakpoint(self.master_cpu.physical_memory,
                                   Sim_Break_Physical, Sim_Access_Execute,
                                   self.max_mem_address - 0x3591c, 4,
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
    sunfire_system_instance(obj)
    return obj

mp_speedup_instance = None

def mp_speedup():
    mp_speedup_instance.mp_speedup()

def finalize_instance(obj):
    global mp_speedup_instance
    instances[obj].lock_entry()
    mp_speedup_instance = instances[obj]
    start_branch(mp_speedup)

def get_mp_speedup_state(data, obj, idx):
    return instances[obj].mp_speedup_state

def set_mp_speedup_state(data, obj, val, idx):
    instances[obj].mp_speedup_state = val
    return Sim_Set_Ok

def get_slaves(data, obj, idx):
    return instances[obj].slaves

def set_slaves(data, obj, val, idx):
    instances[obj].slaves = val
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

# "init_local"

class_data = class_data_t()
class_data.new_instance = new_instance
class_data.finalize_instance = finalize_instance
class_data.description = """
The <class>sunfire-system</class> class is deprecated and only distributed
for compatibility with old configurations.
"""
SIM_register_class(class_name, class_data)

SIM_register_typed_attribute(class_name, "mp-speedup-state",
                             get_mp_speedup_state, None,
                             set_mp_speedup_state, None,
                             Sim_Attr_Optional,
                             "i", None,
                             "State of the speedup hack for multi-processor boot.")

SIM_register_typed_attribute(class_name, "disabled_slaves",
                             get_slaves, None,
                             set_slaves, None,
                             Sim_Attr_Optional,
                             "i", None,
                             "Number of slave processors currently disabled.")

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
              ("Top of RAM", "0x%x" % system.max_mem_address)])]
                                                                                                               
def get_status(obj):
    system = instances[obj]
    return [("MP Speedup",
             [("Current state", mp_state(system.mp_speedup_state))])]

sim_commands.new_info_command(class_name, get_info)
sim_commands.new_status_command(class_name, get_status)


#note: the nvramrc starts at offset 0x1ca2, the env variable is the length
#      format in memory: lines\0<len> (all lines ending with 0xa).
# ends at 1cd8

env_list = { "diag-switch?"         : [ 0x001, 0x001, "bool",  "true"     ],
             "diag-level"           : [ 0x002, 0x001, "enum",  "max",        {"min" : 0x20, "max" : 0x40} ],
             "#power-cycles"        : [ 0x008, 0x004, "int",   0          ],
             "last-hardware-update" : [ 0x020, 0x009, "str",   ""         ],
             "hardware-revision"    : [ 0x029, 0x011, "str",   ""         ],
             "security-#badlogins"  : [ 0x040, 0x004, "int",   0          ],
             "security-password"    : [ 0x047, 0x009, "str",   ""         ],
             "security-mode"        : [ 0x050, 0x001, "enum",  "none",       {"none" : 0x00, "command" : 0x01, "full" : 0x02} ],
             "oem-banner?"          : [ 0x070, 0x001, "bool",  "false"    ],
             "oem-banner"           : [ 0x071, 0x046, "str",   ""         ],
             "oem-logo?"            : [ 0x0b7, 0x001, "bool",  "false"    ],
             "oem-logo"             : [ 0x0b8, 0x204, "bytes", "@n/a@"    ],
             "nvramrc"              : [ 0x2bc, 0x002, "rc",    "@n/a@"    ],
             "use-nvramrc?"         : [ 0x2be, 0x001, "bool",  "false"    ],
             "silent-mode?"         : [ 0x2bf, 0x001, "bool",  "false"    ],
             "screen-#rows"         : [ 0x2c0, 0x004, "int",   34         ],
             "screen-#cols"         : [ 0x2c4, 0x004, "int",   80         ],
             "ansi-terminal?"       : [ 0x2c8, 0x001, "bool",  "true"     ],
             "local-mac-address?"   : [ 0x2c9, 0x001, "bool",  "false"    ],
             "boot-device"          : [ 0x2ca, 0x102, "str",   "disk diskbrd diskisp disksoc net"],
             "diag-device"          : [ 0x44e, 0x102, "str",   "disk diskbrd diskisp disksoc net"],
             "boot-file"            : [ 0x3cc, 0x082, "str",   ""         ],
             "diag-file"            : [ 0x550, 0x082, "str",   ""         ],
             "watchdog-reboot?"     : [ 0x5d2, 0x001, "bool",  "false"    ],
             "auto-boot?"           : [ 0x5d3, 0x001, "bool",  "true"     ],
             "boot-command"         : [ 0x5d4, 0x042, "str",   "boot"     ],
             "load-base"            : [ 0x616, 0x004, "int",   16384      ],
             "input-device"         : [ 0x61a, 0x022, "str",   "keyboard" ],
             "output-device"        : [ 0x63c, 0x022, "str",   "screen"   ],
             "fcode-debug?"         : [ 0x65e, 0x001, "bool",  "false"    ],
             "powerfail-time"       : [ 0x65f, 0x004, "int",   0          ],
             "mfg-mode"             : [ 0x663, 0x001, "enum",  "off",        {"off" : 0x00, "chamber" : 0x01} ],
             "sbus-probe-default"   : [ 0x664, 0x00a, "str",   "d3120"    ],
             "sbus-specific-probe"  : [ 0x66e, 0x092, "str",   ""         ],
             "ttya-mode"            : [ 0x700, 0x012, "str",   "9600,8,n,1,-" ],
             "ttyb-mode"            : [ 0x712, 0x012, "str",   "9600,8,n,1,-" ],
             "ttya-ignore-cd"       : [ 0x724, 0x001, "bool",  "true"     ],
             "ttya-rts-dtr-off"     : [ 0x725, 0x001, "bool",  "false"    ],
             "ttyb-ignore-cd"       : [ 0x726, 0x001, "bool",  "true"     ],
             "ttyb-rts-dtr-off"     : [ 0x727, 0x001, "bool",  "false"    ],
             "keymap"               : [ 0x728, 0x186, "bytes", "@n/a@"    ],
             "keyboard-click?"      : [ 0x8ae, 0x001, "bool",  "false"    ],
             "scsi-initiator-id"    : [ 0x8af, 0x001, "int",   7          ],
             "configuration-policy" : [ 0x8b0, 0x001, "enum",  "component",  {"system" : 0x80, "board" : 0x40, "component" : 0x20, "all" : 0x10} ],
             "memory-interleave"    : [ 0x8b1, 0x001, "enum",  "max",        {"max" : 0x20, "min" : 0x10} ],
             "disabled-board-list"  : [ 0x8b2, 0x012, "str",   ""         ],
             "disabled-memory-list" : [ 0x8c4, 0x012, "str",   ""         ] }

def copy_nvram_to_ioboards(cpu):
    cb_addr = 0x1fff8908000
    io_addr = 0x1c0f8300000
    for board in range(16):
        for i in range(0x20, 0x1cd8):
            try:
                SIM_write_phys_memory(cpu, io_addr + i,
                                      SIM_read_phys_memory(cpu, cb_addr + i, 1),
                                      1)
            except:
                break
        io_addr += 0x400000000

def update_eeprom_checksum(obj):
    base = 0x1fff8908000
    system = instances[obj]
    start = 0x0020
    end = 0x1cd8
    chk = 0x0c # start magic
    for i in range(start, end):
        chk ^= SIM_read_phys_memory(system.master_cpu, base + i, 1)
    chk ^= 0xf0
    SIM_write_phys_memory(system.master_cpu, base, chk, 1)
    # Linux doesn't boot for some reason if we copy the nvram contents
    # to the ioboards. Don't know why yet (bug #2755)
    # copy_nvram_to_ioboards(system.master_cpu)
    
def write_int_bytes(cpu, addr, val, length):
    for i in range(0, length):
        SIM_write_phys_memory(cpu, addr + i, (val >> ((length - i - 1 ) * 8)) & 0xff, 1)

def read_int_bytes(cpu, addr, length):
    val = 0
    for i in range(0, length):
        val = (val << 8) | SIM_read_phys_memory(cpu, addr + i, 1)
    return val

def write_str_bytes(cpu, addr, val):
    SIM_write_phys_memory(cpu, addr, len(val), 1)
    for i in range(0, len(val)):
        SIM_write_phys_memory(cpu, addr + 1 + i, ord(val[i]), 1)

def read_str_bytes(cpu, addr):
    strlen = SIM_read_phys_memory(cpu, addr, 1)
    str = ""
    for i in range(0, strlen):
        str += chr(SIM_read_phys_memory(cpu, addr + 1 + i, 1))
    return str

def set_env(obj, env, val_tuple, do_chk = 1):
    base = 0x1fff8908000
    system = instances[obj]
    try:
        env_list[env]
    except:
        raise Exception, "Unknown OBP variable '%s'" % env
    if type(val_tuple) == type((0,)):
        if env_list[env][2] == "int" and val_tuple[2] != "int":
            raise Exception, "Variable needs integer argument"
        elif env_list[env][2] != "int" and val_tuple[2] == "int":
            raise Exception, "Variable needs string argument"
        val = val_tuple[1]
    else:
        val = val_tuple
    if env_list[env][2] == "bool":
            if val == "false":
                SIM_write_phys_memory(system.master_cpu, base + env_list[env][0], 0x00, 1)
            elif val == "true":
                SIM_write_phys_memory(system.master_cpu, base + env_list[env][0], 0xff, 1)
            else:
                raise Exception, "Illegal bool value '%s'" % val
    elif env_list[env][2] == "int":
        write_int_bytes(system.master_cpu, base + env_list[env][0], val, env_list[env][1])
    elif env_list[env][2] == "enum":
        lst = env_list[env][4]
        try:
            SIM_write_phys_memory(system.master_cpu, base + env_list[env][0], lst[val], 1)
        except KeyError:
            raise Exception, "Could not set enum to '%s'" % val
    elif env_list[env][2] == "bytes":
        raise Exception, "Setting %s not supported" % env
    elif env_list[env][2] == "str":
        if (len(val) + 1) > env_list[env][1]:
            raise Exception, "String too long, max = %d" % (env_list[env][1] - 1)
            return
        write_str_bytes(system.master_cpu, base + env_list[env][0], val)
    elif env_list[env][2] == "rc":
        raise Exception, "Setting %s not supported" % env
    else:
        raise Exception, "%s is UNKNOWN %s" % (env, env_list[env][2])
    if do_chk != 0:
        update_eeprom_checksum(obj)

def set_prom_env(obj, env, val_tuple):
    try:
        set_env(obj, env, val_tuple,1)
    except Exception, msg:
        print msg
        SIM_command_has_problem()
    
def get_prom_env(obj, env):
    base = 0x1fff8908000
    system = instances[obj]
    if env_list[env][2] == "bool":
        val = SIM_read_phys_memory(system.master_cpu, base + env_list[env][0], 1)
        if val == 0xff:
            return "true"
        else:
            return "false"
    elif env_list[env][2] == "int":
        return "0x%x" % read_int_bytes(system.master_cpu, base + env_list[env][0], env_list[env][1])
    elif env_list[env][2] == "enum":
        val = SIM_read_phys_memory(system.master_cpu, base + env_list[env][0], 1)
        try:
            lst = env_list[env][4]
            return lst.keys()[lst.values().index(val)]
        except KeyError:
            raise Exception, "Unkown enum value '%d'" % val
    elif env_list[env][2] == "bytes":
        raise Exception, "Getting %s not supported" % env
    elif env_list[env][2] == "str":
        return read_str_bytes(system.master_cpu, base + env_list[env][0])
    elif env_list[env][2] == "rc":
        raise Exception, "Getting %s not supported" % env
    else:
        raise Exception, "Error in 'get-prom-env' command"

def print_prom_env(obj, env):
    if env == "":
        lst = env_list.keys()
    else:
        try:
            env_list[env]
        except:
            print "Unknown OBP variable '%s'" % env
            SIM_command_has_problem()
            return
        lst = [env]
    for i in lst:
        try:
            print "%-20s : %s" % (i, get_prom_env(obj, i))
        except:
            print "%-20s :" % i

def set_default_nvram(obj):
    for env in env_list.keys():
        if env_list[env][3] != "@n/a@":
            set_env(obj, env, env_list[env][3], 0)
    update_eeprom_checksum(obj)

def var_expand(string):
    return get_completions(string, env_list.keys())

new_command("set-prom-env", set_prom_env,
            [arg(str_t, "variable", expander = var_expand),
             arg((int_t, str_t), ("int", "string"))],
            short = "Set an OBP environment variable",
	    namespace = class_name,
            type = "deprecated commands",
            deprecated = "<sunfire-6500-backplane>.set-prom-env")

new_command("get-prom-env", print_prom_env,
            [arg(str_t, "variable", "?", "", expander = var_expand)],
            short = "Get an OBP environment variable",
	    namespace = class_name,
            type = "deprecated commands",
            deprecated = "<sunfire-6500-backplane>.get-prom-env")

new_command("set-prom-defaults", set_default_nvram,
            [],
            short = "Restore all OBP variables",
	    namespace = class_name,
            type = "deprecated commands",
            deprecated = "<sunfire-6500-backplane>.set-prom-defaults")
