from cli import *
from string import *
import nic_common
import sim_commands


nic_common.new_nic_commands("ppc440gp-emac")


#
# ------------------------ info -----------------------
#

sim_commands.new_info_command("ppc440gp-emac", nic_common.get_nic_info)

#
# ------------------------ status -----------------------
#

def get_emac_status(obj):
    status = []
    for x in obj.attributes:
        name = x[0]
        if name[0:6] == "EMACx_":
            value = SIM_get_attribute(obj, name)
            name = name[0:5] + "_" + name[6:]
            description = x[2]
            status.append((name, "0x%08x" % value))
    return nic_common.get_nic_status(obj) + [("Registers", status)]

sim_commands.new_status_command("ppc440gp-emac", get_emac_status)

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
	    namespace = "ppc440gp-dma",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="45")

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
	    namespace = "ppc440gp-pci",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="67")

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
	    namespace = "ppc440gp-ebc",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="89")

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
	    namespace = "ppc440gp-gpio",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="111")

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
	    namespace = "ppc440gp-cpc",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="133")

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
	    namespace = "ppc440gp-mal",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="155")

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
	    namespace = "ppc440gp-uic",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="177")

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
	    namespace = "ppc440gp-zmii",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="199")

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
	    namespace = "ppc440gp-iic",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="221")

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
	    namespace = "ppc440gp-mc",
            doc = """
Print detailed dynamic information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/440gp-devices/commands.py", linenumber="243")
