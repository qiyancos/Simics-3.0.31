from cli import *
from string import *
import nic_common
import sim_commands

device_name = get_last_loaded_module()

register_names = ["Control",
                  "Status",
                  "PHY Identifier",
                  "PHY Identifier",
                  "Auto-Negotiation Advertisement",
                  "Link Partner Ability",
                  "Auto-Negotiation Expansion",
                  "Next Page Transmit",
                  "Link Partner Next Page",
                  "1000BASE-T Control",
                  "1000BASE-T Status",
                  "Reserved",
                  "Reserved",
                  "Reserved",
                  "Reserved",
                  "Extended Status",
                  "PHY Specific Control",
                  "PHY Specific Status",
                  "Interrupt Enable",
                  "Interrupt Status",
                  "Extended PHY Specific Control",
                  "Receive Error Counter",
                  "Extended Address",
                  "Global Status",
                  "LED Control",
                  "Manual LED Override",
                  "Extended Control 2",
                  "Extended Status",
                  "Cable Tester Status",
                  "Extended Address",
                  "Calibration",
                  "Reserved"]

#
# ---------------------- info ----------------------
#
    
def get_info(obj):
    return []

#
# --------------------- status ---------------------
#
    
def get_status(obj):
    register_values = map(lambda x: "0x%04x" % x, obj.registers)
    return [("MII Management Register Set", zip(register_names, register_values))]

nic_common.new_nic_commands(device_name)
sim_commands.new_info_command(device_name, get_info)
sim_commands.new_status_command(device_name, get_status)
