from cli import *
from string import *
import nic_common

nic_common.new_nic_commands("ppc405gp-emac")


#
# ---------------------- info ----------------------
#

def emac_status_cmd(obj):
    print
    if obj.connected:
        print "connected to: " + obj.network
    print    
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:6] == "EMAC0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:5] + "_" + name[6:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", emac_status_cmd,
            [],
            alias = "",
            type  = "ppc405gp-emac commands",
            short = "print dynamic information about device",
	    namespace = "ppc405gp-emac",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/405gp-devices/commands.py", linenumber="27")

