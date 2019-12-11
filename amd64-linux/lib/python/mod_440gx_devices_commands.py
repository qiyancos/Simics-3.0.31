from cli import *
from string import *
import nic_common

module_name = get_last_loaded_module()

if module_name == "440gx-devices":
    soc_name = "ppc440gx"
elif module_name == "440gp-devices":
    soc_name = "ppc440gp"
else:
    print "unknown module name: " + module_name

nic_common.new_nic_commands(soc_name + "-emac")

#
# ------------------------ info -----------------------
#

def emac_info_cmd(obj):
    print 
    print "%s is a %s" % (obj.name, obj.classname)
    print
    print "the ethernet address is " + obj.mac_address
    print "min-latency is %s ns" % obj.min_latency    

new_command("info", emac_info_cmd,
            [],
            alias = "",
            type  = "ppc440gp-emac commands",
            short = "print static information about device",
	    namespace = soc_name + "-emac",
            doc = """
Print detailed static information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="27")

#
# ------------------------ status -----------------------
#

def emac_status_cmd(obj):
    print
    if obj.connected:
        print "connected to: " + obj.network
    print    
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:6] == "EMACx-":
            value = SIM_get_attribute(obj, name)
            name = name[0:5] + "_" + name[6:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", emac_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-emac commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-emac",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="56")

def dma_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:5] == "DMA0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:4] + "_" + name[5:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", dma_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-dma commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-dma",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="78")

def pci_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:6] == "PCIX0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:5] + "_" + name[6:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", pci_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-pci commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-pci",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="100")

def ebc_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:5] == "EBC0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:4] + "_" + name[5:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", ebc_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-ebc commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-ebc",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="122")

def gpio_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:6] == "GPIO0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:5] + "_" + name[6:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", gpio_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-gpio commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-gpio",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="144")

def cpc_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:5] == "CPC0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:4] + "_" + name[5:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", cpc_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-cpc commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-cpc",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="166")

def mal_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:5] == "MAL0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:4] + "_" + name[5:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", mal_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-mal commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-mal",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="188")

def uic_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:5] == "UICx-":
            value = SIM_get_attribute(obj, name)
            name = name[0:4] + "_" + name[5:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", uic_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-uic commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-uic",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="210")

def zmii_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:6] == "ZMII0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:5] + "_" + name[6:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", zmii_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-zmii commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-zmii",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="232")

def iic_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:5] == "IICx-":
            value = SIM_get_attribute(obj, name)
            name = name[0:4] + "_" + name[5:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", iic_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-iic commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-iic",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="254")

def mc_status_cmd(obj):
    print
    registers = [["Register", "Value", "Description"]]
    for x in obj.attributes:
        name = x[0]
        if name[0:7] == "SDRAM0-":
            value = SIM_get_attribute(obj, name)
            name = name[0:6] + "_" + name[7:]
            description = x[2]
            registers += [[name, "0x%08x" % value, description]]
    print_columns([Just_Left, Just_Left, Just_Left], registers)

new_command("status", mc_status_cmd,
            [],
            alias = "",
            type  = "ppc440gp-mc commands",
            short = "print dynamic information about device",
	    namespace = soc_name + "-mc",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/4xx-devices/commands.py", linenumber="276")
