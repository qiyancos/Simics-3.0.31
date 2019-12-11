
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

# MODULE: fiesta-system
# CLASS: fiesta-system

from cli import *
from sim_core import *
from text_console_common import wait_for_string
import sim_commands

# The name of the class defined in this file, as a convenient shorthand
class_name = "fiesta-system"

instances = {}

class fiesta_system_instance:
    def __init__(self, conf_obj):
        global instances
        instances[conf_obj] = self
        self.obj = conf_obj

        self.master_cpu = None
        self.nvram_image = None
        self.all_cpus = []
        
def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    fiesta_system_instance(obj)
    return obj

def finalize_instance(obj):
    pass

def get_master_cpu(data, obj, idx):
    return instances[obj].master_cpu

def set_master_cpu(data, obj, val, idx):
    instances[obj].master_cpu = val
    return Sim_Set_Ok

def get_nvram_image(data, obj, idx):
    return instances[obj].nvram_image

def set_nvram_image(data, obj, val, idx):
    instances[obj].nvram_image = val
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
The <class>fiesta-system</class> class is deprecated and only distributed
for compatibility with old configurations.
"""
SIM_register_class(class_name, class_data)

SIM_register_typed_attribute(class_name, "master-cpu",
                             get_master_cpu, None,
                             set_master_cpu, None,
                             Sim_Attr_Required,
                             "o", None,
                             "The master processor in the machine.")

SIM_register_typed_attribute(class_name, "nvram-image",
                             get_nvram_image, None,
                             set_nvram_image, None,
                             Sim_Attr_Required,
                             "o", None,
                             "The nvram image object, holding OBP variables.")

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
             [("Master CPU", system.master_cpu.name)])]
                                                                                                               
sim_commands.new_info_command(class_name, get_info)

############################# NVRAM Start

#
# The first variables in the list below have fixed offsets in the NVRAM
# structure. The size of their data fields depend on the type of that
# variable.
#
# Other variables are written at offset 0x40 with the following format:
#
# <4-byte key> <1-byte chksum> <2-byte len> <data>
#
# There are some special keys that are not followed by any checksum, etc:
# 0x836b93cb start
# 0xffffffff end
# 0x051d148b reboot ?
#
# Also keys with the highest bit == 0 are not followed by any bytes. They
# specify that the default value of that variable is to be used.
#
# The checksum is a folded addition of the <len> and <data> fields.
#
# The NVRAM typically only contains differences from the default values,
# but OBP writes any change to the NVRAM until the buffer (not sure about
# the size) is full. It then removes any duplicated and only saves the
# variable values that are really needed.
#            

variable_offset = 0x40 # variables with lower offsets have fixed offset

start_key =  0x046e8899L   # used to be 0x836b93cbL on older proms
stop_key  =  0xffffffffL
reboot_key = 0x051d148bL

env_list = { "diag-switch?"         : [ 0x001, 0x001, "bool",  "false"     ],
             "diag-level"           : [ 0x002, 0x001, "enum",  "max",        {"off" : 0x00, "min" : 0x20, "max" : 0x40, "menus" : 0x80} ],
             "diag-script"          : [ 0x003, 0x001, "enum",  "none",       {"none"     : 0x00, "all"      : 0x02,
                                                                              "menu-int" : 0x10, "menu-ext" : 0x11,
                                                                              "bft-int"  : 0x20, "bft-ext"  : 0x21,
                                                                              "sys-int"  : 0x40, "sys-ext"  : 0x41 } ],
             "security-#badlogins"  : [ 0x020, 0x004, "int",   0          ],
             "security-password"    : [ 0x024, 0x009, "str",   ""         ],
             "security-mode"        : [ 0x02e, 0x001, "enum",  "none",       {"none" : 0x00, "command" : 0x01, "full" : 0x02} ],
             # variables below start at offset 'variable_offset' (0x40)
             "oem-banner?"          : [ 0x8b66d3cbL, 0x001, "bool",  "false"    ],
             "oem-banner"           : [ 0x8db453caL, 0x046, "str",   ""         ],
             "oem-logo?"            : [ 0x85d713c9L, 0x001, "bool",  "false"    ],
             "oem-logo"             : [ 0x00000000L, 0x204, "bytes", "@n/a@"    ],
             "nvramrc"              : [ 0x85fa9387L, 0x002, "rc",    ""         ],
             "use-nvramrc?"         : [ 0x8b6bb54cL, 0x001, "bool",  "false"    ],
             "silent-mode?"         : [ 0x8c90b4ccL, 0x001, "bool",  "false"    ],
             "screen-#rows"         : [ 0x88a0b4ccL, 0x004, "int",   34         ],
             "screen-#columns"      : [ 0x8b6134cfL, 0x004, "int",   80         ],
             "ansi-terminal?"       : [ 0x8779504eL, 0x001, "bool",  "true"     ],
             "local-mac-address?"   : [ 0x8c9b1312L, 0x001, "bool",  "true"     ],
             "boot-device"          : [ 0x89f1308bL, 0x102, "str",   "disk net"],
             "diag-device"          : [ 0x8767110bL, 0x102, "str",   "net"],
             "boot-file"            : [ 0x81e1d089L, 0x082, "str",   ""         ],
             "diag-file"            : [ 0x8f579109L, 0x082, "str",   ""         ],
             "auto-boot?"           : [ 0x88b5f04aL, 0x001, "bool",  "true"     ],
             "boot-command"         : [ 0x881d708cL, 0x042, "str",   "boot"     ],
             "load-base"            : [ 0x8ee43309L, 0x004, "int",   16384      ],
             "input-device"         : [ 0x8ec8724cL, 0x022, "str",   "keyboard" ],
             "output-device"        : [ 0x8dfc53cdL, 0x022, "str",   "screen"   ],
             "fcode-debug?"         : [ 0x8a1f718cL, 0x001, "bool",  "false"    ],
             "ttya-mode"            : [ 0x86abb509L, 0x012, "str",   "9600,8,n,1,-" ],
             "ttyb-mode"            : [ 0x86f3b509L, 0x012, "str",   "9600,8,n,1,-" ],
             "ttya-ignore-cd"       : [ 0x8605750eL, 0x001, "bool",  "true"     ],
             "ttya-rts-dtr-off"     : [ 0x82351510L, 0x001, "bool",  "false"    ],
             "ttyb-ignore-cd"       : [ 0x864d550eL, 0x001, "bool",  "true"     ],
             "ttyb-rts-dtr-off"     : [ 0x827d1510L, 0x001, "bool",  "false"    ],
             "scsi-initiator-id"    : [ 0x875c94d1L, 0x001, "int",   7          ],
             "test-args"            : [ 0x8cdbb509L, 0x100, "str",   ""         ],
             "diag-passes"          : [ 0x852bf10bL, 0x004, "int",   1          ],
             "error-reset-recovery" : [ 0x898eb154L, 0x001, "boot",  "boot", {"none" : 0x00, "boot" : 0x01, "sync" : 0x02} ] }

# Obsolete?
#             "no-cassini?"          : [ 0x811db38bL, 0x001, "bool",  "true"     ],


def update_eeprom_checksum(nvram):
    start = 0x0020
    end = 0x39
    chk = 0x0c # start magic
    for i in range(start, end):
        chk ^= nvram.byte_access[i]
    chk ^= 0xf0
    nvram.byte_access[0x0] = chk

def write_int_bytes(nvram, addr, val, length):
    for i in range(0, length):
        nvram.byte_access[addr + i] = (val >> ((length - i - 1 ) * 8)) & 0xff

def read_int_bytes(nvram, addr, length):
    val = 0L
    for i in range(0, length):
        val = (val << 8) | nvram.byte_access[addr + i]
    return val

def write_str_bytes(nvram, addr, val):
    nvram.byte_access[addr] = len(val)
    for i in range(0, len(val)):
        nvram.byte_access[addr + 1 + i] = ord(val[i])
    nvram.byte_access[addr + 1 + len(val)] = 0

def write_rc_bytes(nvram, addr, val):
    for i in range(0, len(val)):
        nvram.byte_access[addr + i] = ord(val[i])

def read_str_bytes(nvram, addr):
    strlen = nvram.byte_access[addr]
    str = ""
    for i in range(0, strlen):
        str += chr(nvram.byte_access[addr + 1 + i])
    return str

def read_rc_bytes(nvram, addr, len):
    str = ""
    for i in range(0, len):
        str += chr(nvram.byte_access[addr + i])
    return str

def variable_from_key(key):
    for env in env_list.keys():
        if env_list[env][0] == key:
            return env
    raise Exception, "Unknown key: 0x%x" % key

def read_key(nvram, offset):
    key = read_int_bytes(nvram, offset, 4)
    if key == start_key:
        return [key, 4, offset]
    elif key == stop_key:
        return [key, 4, offset]
    elif key == reboot_key:
        return [key, 4, offset]
    elif key & 0x80000000L == 0: # default value
        return [key, 4, offset]
    else:
        len = read_int_bytes(nvram, offset + 5, 2)
        return [key, 7 + len, offset]

# Get a dictionary of all variables that differ from the default. Since we parse
# the actual NVRAM we must handle anything that the OBP may have written there.
# returned in the dictonary are lists: [key, length, offset] indexed by key.
def get_diff_variables(nvram):
    off = 0
    diff_keys = {}
    
    key = read_key(nvram, variable_offset)
    if key[0] != start_key:
        # no valid variable table
        return

    while key[0] != stop_key:
        if (key[0] != reboot_key) and (key[0] != stop_key) and (key[0] != start_key):
            # check for default values - simply remove any previous entry
            if (key[0] & 0x80000000L) == 0:
                diff_keys.pop(key[0] | 0x80000000L, None)
            else:
                # add to the list, overwrite old ones
                diff_keys[key[0]] = key
        off += key[1]
        key = read_key(nvram, variable_offset + off)
    
    return diff_keys

# calculate folded sum
# offset: address of first byte to include
# len   : length of data and length field
def get_variable_checksum(nvram, offset, len):
    sum = 0
    for i in range(offset, offset + len):
        sum += read_int_bytes(nvram, i, 1)
    while sum > 0xff:
        tmp = 0
        while sum > 0:
            tmp += sum & 0xff
            sum >>= 8
        sum = tmp
    return sum

def read_variable(nvram, env, offset, int_len = 0):
    if env_list[env][2] == "bool":
        val = read_int_bytes(nvram, offset, 1)
        if val == 0xff:
            return "true"
        else:
            return "false"
    elif env_list[env][2] == "int":
        return read_int_bytes(nvram, offset, int_len)
    elif env_list[env][2] == "enum":
        val = read_int_bytes(nvram, offset, 1)
        try:
            lst = env_list[env][4]
            return lst.keys()[lst.values().index(val)]
        except KeyError:
            raise Exception, "Unknown enum value '%d'" % val
    elif env_list[env][2] == "str":
        return read_str_bytes(nvram, offset)
    elif env_list[env][2] == "rc":
        return read_rc_bytes(nvram, offset, read_int_bytes(nvram, offset - 2, 2))
    else:
        raise Exception, "Error in 'read_variable()'"

def get_input_value(key, val):
    env = variable_from_key(key)
    if env_list[env][2] == "bool":
        if val == "false":
            return 0x00
        elif val == "true":
            return 0xff
        else:
            raise Exception, StandardError, "Illegal bool value '%s'" % val
    elif env_list[env][2] == "int":       
        return val
    elif env_list[env][2] == "enum":
        if val in env_list[env][4].keys():
            return env_list[env][4][val]
        else:
            raise Exception, "Could not set enum to '%s'" % val
    elif env_list[env][2] == "str":
        return val
    elif env_list[env][2] == "rc":
        return val
    elif env_list[env][2] == "bytes":
        raise Exception, "Setting %s is not supported" % env
    else:
        raise Exception, "%s is UNKNOWN %s" % (env, env_list[env][2])


# get diff list from NVRAM
# if found in diff list, remove it from there, change = 1
# if != default:
#     add to diff list, change = 1
# if change == 1
#     write the diff file back to the NVRAM
#
def set_env(obj, env, val_tuple):
    system = instances[obj]
    nvram = system.nvram_image
    key = env_list[env][0]
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

    if key < variable_offset:
        value = get_input_value(key, val)
        if env_list[env][2] == "bool" or env_list[env][2] == "int" or env_list[env][2] == "enum":
            write_int_bytes(nvram, key, value, env_list[env][1])
        elif env_list[env][2] == "str":
            write_str_bytes(nvram, key, value)
        update_eeprom_checksum(nvram)
        return

    changed = 0

    # check if already modified - then remove old change
    diff_keys = get_diff_variables(nvram)
    if diff_keys.has_key(key):
        del diff_keys[key]
        changed = 1

    if val == env_list[env][3]:
        # setting default value?
        if diff_keys.has_key(key):
            del diff_keys[key]
            changed = 1
        # if default value and nothing changed, return now
        if changed == 0:
            return
        
    new_list = {}
    for i in diff_keys.keys():
        try:
            var = variable_from_key(i)
        except:
            # OBP has written a key we don't know about
            # print "Unknown key: 0x%x" % i
            continue
        if env_list[var][2] == "int":
            int_len = env_list[var][1]
        else:
            int_len = 0 # not used
        new_list[i] = [i, get_input_value(i, read_variable(nvram, var, diff_keys[i][2] + 7, int_len))]

    # add the new one as well
    new_list[key] = [key, get_input_value(key, val)]

    # we now have a list of all variables - update the NVRAM
    write_int_bytes(nvram, variable_offset, start_key, 4)
    offset = variable_offset + 4
    for i in new_list.values():
        var = variable_from_key(i[0])
        write_int_bytes(nvram, offset, i[0], 4)
        length = 0
        if env_list[var][2] == "bool" or env_list[var][2] == "int" or env_list[var][2] == "enum":
            length = env_list[var][1]
            write_int_bytes(nvram, offset + 5, length, 2)
            write_int_bytes(nvram, offset + 7, i[1], length)
        elif env_list[var][2] == "str":
            length = len(i[1]) + 2 # add for length and 0 in string
            write_int_bytes(nvram, offset + 5, length, 2)
            write_str_bytes(nvram, offset + 7, i[1])
        elif env_list[var][2] == "rc":
            #if i[1][-1] != "\n":
            #    print "Warning: Adding \\n at end of nvramrc"
            #    i[1] += "\n"
            length = len(i[1])
            write_int_bytes(nvram, offset + 5, length, 2)
            write_rc_bytes(nvram, offset + 7, i[1])
        write_int_bytes(nvram, offset + 4, get_variable_checksum(nvram, offset + 5, length + 2), 1)
        offset += 7 + length
    write_int_bytes(nvram, offset, stop_key, 4)

def set_prom_env(obj, env, val_tuple):
    print ("The <fiesta-system>.set-prom-env command is obsolete, use "
           "<taco-system>.set-prom-env instead.")
    try:
        set_env(obj, env, val_tuple)
    except Exception, msg:
        print "Failed setting variable:", msg
        SIM_command_has_problem()

def get_prom_env(obj, env):
    system = instances[obj]
    nvram = system.nvram_image
    key = env_list[env][0]
    diff_keys = get_diff_variables(nvram)
    
    if diff_keys.has_key(key):
        offset = diff_keys[key][2] + 7 # 4 + 1 + 2
        int_len = diff_keys[key][1] - 7
    elif key < variable_offset:
        offset = key
        int_len = env_list[env][1]
    else: # use default value
        return "%s" % env_list[env][3]
    
    if env_list[env][2] == "bool":
        return read_variable(nvram, env, offset)
    elif env_list[env][2] == "int":
        return "%d" % read_variable(nvram, env, offset, int_len)
    elif env_list[env][2] == "enum":
        return read_variable(nvram, env, offset)
    elif env_list[env][2] == "bytes":
        raise Exception, "Getting %s not supported" % env
    elif env_list[env][2] == "str":
        return read_variable(nvram, env, offset)
    elif env_list[env][2] == "rc":
        return read_variable(nvram, env, offset)
    else:
        raise Exception, "Error in 'get-prom-env' command"


def print_prom_env(obj, env):
    print ("The <fiesta-system>.get-prom-env command is obsolete, use "
           "<taco-system>.get-prom-env instead.")
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
    print ("The <fiesta-system>.set-prom-defaults command is obsolete, use "
           "<taco-system>.set-prom-defaults instead.")
    system = instances[obj]
    nvram = system.nvram_image
    if read_int_bytes(nvram, variable_offset, 4) == start_key:
        # already initialized? (e.g. from an image file)
        print "Skipping nvram init."
        return
    write_int_bytes(nvram, variable_offset + 0, start_key, 4)
    write_int_bytes(nvram, variable_offset + 4, reboot_key, 4)
    write_int_bytes(nvram, variable_offset + 8, stop_key, 4)
    for env in env_list.keys():
        if env_list[env][0] >= variable_offset:
            # skip default values for 'non-fixed' variables
            continue
        if env_list[env][3] != "@n/a@":
            set_env(obj, env, env_list[env][3])
    update_eeprom_checksum(nvram)

def var_expand(string):
    return get_completions(string, env_list.keys())

new_command("set-prom-env", set_prom_env,
            [arg(str_t, "variable", expander = var_expand),
             arg((int_t, str_t), ("int", "string"))],
            alias = "",
            type  = class_name + " commands",
            short = "Set an OBP environment variable",
	    namespace = class_name,
            deprecated = "<taco-system>.set-prom-env")

new_command("get-prom-env", print_prom_env,
            [arg(str_t, "variable", "?", "", expander = var_expand)],
            alias = "",
            type  = class_name + " commands",
            short = "Get an OBP environment variable",
	    namespace = class_name,
            deprecated = "<taco-system>.get-prom-env")

new_command("set-prom-defaults", set_default_nvram,
            [],
            alias = "",
            type  = class_name + " commands",
            short = "Restore all OBP variables",
	    namespace = class_name,
            deprecated = "<taco-system>.set-prom-defaults")

############################# NVRAM End
