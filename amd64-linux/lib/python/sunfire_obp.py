from cli import *
from components import get_component, mac_as_list

#note: the nvramrc starts at offset 0x1ca2, the env variable is the length
#      format in memory: lines\0<len> (all lines ending with 0xa).
# ends at 1cd8

env_list = { "diag-switch?"         : [ 0x001, 0x001, "bool",  "true"     ],
             "diag-level"           : [ 0x002, 0x001, "enum",  "max",
                                        {"min" : 0x20, "max" : 0x40} ],
             "#power-cycles"        : [ 0x008, 0x004, "int",   0          ],
             "last-hardware-update" : [ 0x020, 0x009, "str",   ""         ],
             "hardware-revision"    : [ 0x029, 0x011, "str",   ""         ],
             "security-#badlogins"  : [ 0x040, 0x004, "int",   0          ],
             "security-password"    : [ 0x047, 0x009, "str",   ""         ],
             "security-mode"        : [ 0x050, 0x001, "enum",  "none",
                                        {"none" : 0x00,
                                         "command" : 0x01,
                                         "full" : 0x02} ],
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
             "boot-device"          : [ 0x2ca, 0x102, "str",
                                        "disk diskbrd diskisp disksoc net"],
             "diag-device"          : [ 0x44e, 0x102, "str",
                                        "disk diskbrd diskisp disksoc net"],
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
             "mfg-mode"             : [ 0x663, 0x001, "enum",  "off",
                                        {"off" : 0x00, "chamber" : 0x01} ],
             "sbus-probe-default"   : [ 0x664, 0x00a, "str",   "d3120"    ],
             "sbus-specific-probe"  : [ 0x66e, 0x092, "str",   ""         ],
             "ttya-mode"            : [ 0x700, 0x012, "str",  "9600,8,n,1,-" ],
             "ttyb-mode"            : [ 0x712, 0x012, "str",  "9600,8,n,1,-" ],
             "ttya-ignore-cd"       : [ 0x724, 0x001, "bool",  "true"     ],
             "ttya-rts-dtr-off"     : [ 0x725, 0x001, "bool",  "false"    ],
             "ttyb-ignore-cd"       : [ 0x726, 0x001, "bool",  "true"     ],
             "ttyb-rts-dtr-off"     : [ 0x727, 0x001, "bool",  "false"    ],
             "keymap"               : [ 0x728, 0x186, "bytes", "@n/a@"    ],
             "keyboard-click?"      : [ 0x8ae, 0x001, "bool",  "false"    ],
             "scsi-initiator-id"    : [ 0x8af, 0x001, "int",   7          ],
             "configuration-policy" : [ 0x8b0, 0x001, "enum",  "component",
                                        {"system" : 0x80,
                                         "board" : 0x40,
                                         "component" : 0x20,
                                         "all" : 0x10} ],
             "memory-interleave"    : [ 0x8b1, 0x001, "enum",  "max",
                                        {"max" : 0x20, "min" : 0x10} ],
             "disabled-board-list"  : [ 0x8b2, 0x012, "str",   ""         ],
             "disabled-memory-list" : [ 0x8c4, 0x012, "str",   ""         ] }

def copy_nvram_to_ioboards(cpu):
    cb_addr = 0x1fff8908000
    io_addr = 0x1c0f8300000
    for board in range(16):
        for i in range(0x20, 0x1cd8):
            try:
                SIM_write_phys_memory(cpu, io_addr + i,
                                      SIM_read_phys_memory(cpu,
                                                           cb_addr + i, 1), 1)
            except:
                break
        io_addr += 0x400000000

def update_eeprom_checksum(system):
    base = 0x1fff8908000
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
        SIM_write_phys_memory(cpu, addr + i,
                              (val >> ((length - i - 1 ) * 8)) & 0xff, 1)

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
    system = get_component(obj)
    base = 0x1fff8908000
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
                SIM_write_phys_memory(system.master_cpu,
                                      base + env_list[env][0], 0x00, 1)
            elif val == "true":
                SIM_write_phys_memory(system.master_cpu,
                                      base + env_list[env][0], 0xff, 1)
            else:
                raise Exception, "Illegal bool value '%s'" % val
    elif env_list[env][2] == "int":
        write_int_bytes(system.master_cpu,
                        base + env_list[env][0], val, env_list[env][1])
    elif env_list[env][2] == "enum":
        lst = env_list[env][4]
        try:
            SIM_write_phys_memory(system.master_cpu,
                                  base + env_list[env][0], lst[val], 1)
        except KeyError:
            raise Exception, "Could not set enum to '%s'" % val
    elif env_list[env][2] == "bytes":
        raise Exception, "Setting %s not supported" % env
    elif env_list[env][2] == "str":
        if (len(val) + 1) > env_list[env][1]:
            raise Exception, "String too long, max %d" % (env_list[env][1] - 1)
            return
        write_str_bytes(system.master_cpu, base + env_list[env][0], val)
    elif env_list[env][2] == "rc":
        raise Exception, "Setting %s not supported" % env
    else:
        raise Exception, "%s is UNKNOWN %s" % (env, env_list[env][2])
    if do_chk != 0:
        update_eeprom_checksum(system)

def set_prom_env(obj, env, val_tuple):
    try:
        set_env(obj, env, val_tuple,1)
    except Exception, msg:
        print msg
        SIM_command_has_problem()
    
def get_prom_env(obj, env):
    system = get_component(obj)
    base = 0x1fff8908000
    if env_list[env][2] == "bool":
        val = SIM_read_phys_memory(system.master_cpu, base + env_list[env][0], 1)
        if val == 0xff:
            return "true"
        else:
            return "false"
    elif env_list[env][2] == "int":
        return "0x%x" % read_int_bytes(system.master_cpu,
                                       base + env_list[env][0],
                                       env_list[env][1])
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
    update_eeprom_checksum(get_component(obj))

def write_memory(space, addr, value, size):
    data = [0] * size
    for i in range(size):
        data[i] = (value >> ((size - 1) * 8) - (i * 8)) & 0xff
    space.memory[[addr, addr + size - 1]] = data

def read_memory(space, addr):
    return space.memory[[addr, addr]][0]

def write_idprom_to_nvram(obj, hostid, mac):
    phys_mem = get_component(obj).master_cpu.physical_memory
    addr = 0x1fff8909fd8
    # offset 0 = format (1)
    write_memory(phys_mem, addr +  0, 1, 1)
    if hostid:
        # offset 1, 12-14 = hostid
        write_memory(phys_mem, addr +  1, hostid >> 24, 1)
        write_memory(phys_mem, addr + 12, hostid >> 16, 1)
        write_memory(phys_mem, addr + 13, hostid >>  8, 1)
        write_memory(phys_mem, addr + 14, hostid >>  0, 1)
    if mac:
        # offset 2 - 7 = ethernet
        mac = mac_as_list(mac)
        for i in range(len(mac)):
            write_memory(phys_mem, addr +  2 + i, mac[i], 1)
    # offset 8 - 11 = date (not used)
    # offset 15 = checksum
    chk = 0
    for i in range(15):
        chk ^= read_memory(phys_mem, addr + i)
    write_memory(phys_mem, addr + 15, chk, 1)

def get_hostid(obj):
    phys_mem = get_component(obj).master_cpu.physical_memory
    addr = 0x1fff8909fd8
    hostid = read_memory(phys_mem, addr + 1) << 24
    hostid |= read_memory(phys_mem, addr + 12) << 16
    hostid |= read_memory(phys_mem, addr + 13) << 8
    hostid |= read_memory(phys_mem, addr + 14)
    return hostid

def set_hostid(obj, hostid):
    write_idprom_to_nvram(obj, hostid, None)

def get_mac(obj):
    phys_mem = get_component(obj).master_cpu.physical_memory
    addr = 0x1fff8909fd8
    mac = [0] * 6
    for i in range(6):
        mac[i] = read_memory(phys_mem, addr + 2 + i)
    return '%x:%x:%x:%x:%x:%x' % (mac[0], mac[1], mac[2],
                                  mac[3], mac[4], mac[5])

def set_mac(obj, mac):
    write_idprom_to_nvram(obj, None, mac)

def var_expand(string):
    return get_completions(string, env_list.keys())

def register_obp_commands(class_name):
    new_command("set-prom-env", set_prom_env,
                [arg(str_t, "variable", expander = var_expand),
                 arg((int_t, str_t), ("int", "string"))],
                type  = class_name + " commands",
                short = "set an OBP environment variable",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-prom-env'],
                doc = ("Sets the value OBP variable in the NVRAM. Only "
                       "variables with string, integer, boolean and "
                       "enumeration types are supported."), filename="/mp/simics-3.0/src/extensions/apps-python/sunfire_obp.py", linenumber="284")

    new_command("get-prom-env", print_prom_env,
                [arg(str_t, "variable", "?", "", expander = var_expand)],
                type  = class_name + " commands",
                short = "get an OBP environment variable",
                namespace = class_name,
                see_also = ['<' + class_name + '>.set-prom-env'],
                doc = ("Prints an OBP variable with its value, or all "
                       "variables if no argument is specified. Only variables "
                       "with string, integer, boolean and enumeration types "
                       "are supported."), filename="/mp/simics-3.0/src/extensions/apps-python/sunfire_obp.py", linenumber="295")

    new_command("set-prom-defaults", set_default_nvram,
                [],
                type  = class_name + " commands",
                short = "restore all OBP variables",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-prom-env',
                            '<' + class_name + '>.set-prom-env'],
                doc = "Restores all OBP variables to their default values.", filename="/mp/simics-3.0/src/extensions/apps-python/sunfire_obp.py", linenumber="306")

    new_command("set-nvram-hostid", set_hostid,
                [arg(int_t, "hostid")],
                type  = class_name + " commands",
                short = "set the Sun hostid in NVRAM",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-nvram-hostid',
                            '<' + class_name + '>.get-nvram-mac',
                            '<' + class_name + '>.set-nvram-mac'],
                doc = "Writes the Sun hostid into the NVRAM.", filename="/mp/simics-3.0/src/extensions/apps-python/sunfire_obp.py", linenumber="315")

    new_command("get-nvram-hostid", get_hostid,
                [],
                type  = class_name + " commands",
                short = "get the Sun hostid from NVRAM",
                namespace = class_name,
                see_also = ['<' + class_name + '>.set-nvram-hostid',
                            '<' + class_name + '>.get-nvram-mac',
                            '<' + class_name + '>.set-nvram-mac'],
                doc = "Reads the Sun hostid from the NVRAM.", filename="/mp/simics-3.0/src/extensions/apps-python/sunfire_obp.py", linenumber="325")

    new_command("set-nvram-mac", set_mac,
                [arg(str_t, "mac")],
                type  = class_name + " commands",
                short = "set the default MAC address in NVRAM",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-nvram-hostid',
                            '<' + class_name + '>.set-nvram-hostid',
                            '<' + class_name + '>.get-nvram-mac'],
                doc = "Writes the default MAC address into the NVRAM.", filename="/mp/simics-3.0/src/extensions/apps-python/sunfire_obp.py", linenumber="335")

    new_command("get-nvram-mac", get_mac,
                [],
                type  = class_name + " commands",
                short = "get the default MAC from NVRAM",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-nvram-hostid',
                            '<' + class_name + '>.set-nvram-hostid',
                            '<' + class_name + '>.set-nvram-mac'],
                doc = "Reads the default MAC address from the NVRAM.", filename="/mp/simics-3.0/src/extensions/apps-python/sunfire_obp.py", linenumber="345")
