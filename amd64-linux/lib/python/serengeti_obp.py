import string
from cli import *
from components import get_component, mac_as_list

sys_attr = [ "queue", "attributes", "classname", "name", "object-id", "iface" ]

variable_list = {}

def check_variable_list(system):
    if len(variable_list) > 0:
        return
    attrs = system.o.nvci.attributes
    for a in attrs:
        if sys_attr.count(a[0]) == 0:
            var = string.replace(a[0], "Q", "?")
            var = string.replace(var, "_", "-")
            variable_list[var] = a[0]

def set_prom_env(obj, env, val_tuple):
    system = get_component(obj)
    check_variable_list(system)
    if not variable_list.has_key(env):
        print "Unknown OBP variable '%s'" % env
        SIM_command_has_problem()
        return
    try:
        val = str(val_tuple[1])
        SIM_set_attribute(system.o.nvci, variable_list[env], val)
    except Exception, msg:
        print "Failed setting variable: %s" % msg
        SIM_command_has_problem()

def get_prom_env(obj, env):
    system = get_component(obj)
    check_variable_list(system)
    if env == "":
        lst = variable_list.keys()
    elif not variable_list.has_key(env):
        print "Unknown OBP variable '%s'" % env
        SIM_command_has_problem()
        return
    else:
        lst = [env]
    for i in lst:
        print "%-30s  :  %s" % (i, SIM_get_attribute(system.o.nvci,
                                                     variable_list[i]))

def get_hostid(obj):
    sc = get_component(obj).o.sc
    hostid = 0
    for i in range(4):
        hostid |= sc.idprom[10 + i] << (24 - i * 8)
    return hostid

def set_hostid(obj, hostid):
    sc = get_component(obj).o.sc
    idprom = sc.idprom
    for i in range(4):
        idprom[10 + i] = hostid >> (24 - i * 8)
    sc.idprom = idprom

def get_mac(obj):
    sc = get_component(obj).o.sc
    return '%x:%x:%x:%x:%x:%x' % (sc.idprom[0], sc.idprom[1], sc.idprom[2],
                                  sc.idprom[3], sc.idprom[4], sc.idprom[5])

def set_mac(obj, mac):
    sc = get_component(obj).o.sc
    mac = mac_as_list(mac)
    idprom = sc.idprom
    for i in range(6):
        idprom[i] = mac[i]
    sc.idprom = idprom

def var_expand(string, obj):
    system = get_component(obj)
    check_variable_list(system)
    return get_completions(string, variable_list.keys())

def register_obp_commands(class_name):
    new_command("set-prom-env", set_prom_env,
                [arg(str_t, "variable", expander = var_expand),
                 arg((int_t, str_t), ("int", "string"))],
                type  = class_name + " commands",
                short = "Set an OBP environment variable",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-prom-env'],
                doc = ("Sets the value of an OBP variable. Only variables "
                       "with string, integer, boolean and enumeration types "
                       "are supported."), filename="/mp/simics-3.0/src/extensions/apps-python/serengeti_obp.py", linenumber="81")

    new_command("get-prom-env", get_prom_env,
                [arg(str_t, "variable", "?", "", expander = var_expand)],
                alias = "",
                type  = class_name + " commands",
                short = "Get an OBP environment variable",
                namespace = class_name,
                see_also = ['<' + class_name + '>.set-prom-env'],
                doc = ("Prints an OBP variable with its value, or all "
                       "variables if no argument is specified. Only variables "
                       "with string, integer, boolean and enumeration types "
                       "are supported."), filename="/mp/simics-3.0/src/extensions/apps-python/serengeti_obp.py", linenumber="92")

    new_command("set-nvram-hostid", set_hostid,
                [arg(int_t, "hostid")],
                type  = class_name + " commands",
                short = "set the Sun hostid in NVRAM",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-nvram-hostid',
                            '<' + class_name + '>.get-nvram-mac',
                            '<' + class_name + '>.set-nvram-mac'],
                doc = "Writes the Sun hostid into the NVRAM.", filename="/mp/simics-3.0/src/extensions/apps-python/serengeti_obp.py", linenumber="104")

    new_command("get-nvram-hostid", get_hostid,
                [],
                type  = class_name + " commands",
                short = "get the Sun hostid from NVRAM",
                namespace = class_name,
                see_also = ['<' + class_name + '>.set-nvram-hostid',
                            '<' + class_name + '>.get-nvram-mac',
                            '<' + class_name + '>.set-nvram-mac'],
                doc = "Reads the Sun hostid from the NVRAM.", filename="/mp/simics-3.0/src/extensions/apps-python/serengeti_obp.py", linenumber="114")

    new_command("set-nvram-mac", set_mac,
                [arg(str_t, "mac")],
                type  = class_name + " commands",
                short = "set the default MAC address in NVRAM",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-nvram-hostid',
                            '<' + class_name + '>.set-nvram-hostid',
                            '<' + class_name + '>.get-nvram-mac'],
                doc = "Writes the default MAC address into the NVRAM.", filename="/mp/simics-3.0/src/extensions/apps-python/serengeti_obp.py", linenumber="124")

    new_command("get-nvram-mac", get_mac,
                [],
                type  = class_name + " commands",
                short = "get the default MAC from NVRAM",
                namespace = class_name,
                see_also = ['<' + class_name + '>.get-nvram-hostid',
                            '<' + class_name + '>.set-nvram-hostid',
                            '<' + class_name + '>.set-nvram-mac'],
                doc = "Reads the default MAC address from the NVRAM.", filename="/mp/simics-3.0/src/extensions/apps-python/serengeti_obp.py", linenumber="134")
