from cli import *
from sim_commands import *

def shadow_cmd(obj):
    r = [ [ "Base", "Read", "Write" ] ]
    read_write = ("PCI", "RAM")
    crs = obj.config_register
    for i in range(384/2):
        subrange = crs[i]
        if subrange:
            r.append(["%x" % ((640 + i * 2) * 1024), read_write[subrange & 1],
                      read_write[subrange >> 1]])
    print_columns([Just_Left, Just_Left, Just_Left], r)
    print "All addresses not listed are forwarded to PCI"

new_command("status", shadow_cmd, [], namespace = "pc-shadow",
            type = "inspect commands",
            short = "device status",
            doc = """
Print the shadow RAM status for each 2kb region between 640kb and 1Mb.""", filename="/mp/simics-3.0/src/devices/pc-shadow/commands.py", linenumber="16")

def get_info(obj):
    return []

new_info_command('pc-shadow', get_info)
