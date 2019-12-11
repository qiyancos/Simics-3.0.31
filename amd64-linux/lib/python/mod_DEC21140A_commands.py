from cli import *
from string import *
import nic_common
import sim_commands

device_name = get_last_loaded_module()

#
# ---------------------- info ----------------------
#
    
def get_info(obj):
    return ([] +
            sim_commands.get_pci_info(obj) +
            nic_common.get_nic_info(obj))



#
# --------------------- status ---------------------
#
    
def get_status(obj):
	csrs = obj.csrs
        return ([(None,
                 [("Bus mode (CSR0)", "0x%0.8x" % csrs[0]),
                  ("Transmit poll demand (CSR1)", "0x%0.8x" % csrs[1]),
                  ("Receive poll demand (CSR2)", "0x%0.8x" % csrs[2]),
                  ("Receive list base address (CSR3)", "0x%0.8x" % csrs[3]),
                  ("Transmit list base address (CSR4)", "0x%0.8x" % csrs[4]),
                  ("Status (CSR5)", "0x%0.8x" % csrs[5]),
                  ("Operation mode (CSR6)", "0x%0.8x" % csrs[6]),
                  ("Interrupt enable (CSR7)", "0x%0.8x" % csrs[7]),
                  ("Missed frames and overflow counter (CSR8)", "0x%0.8x" % csrs[8]),
                  ("Boot ROM serial, ROM MII, (CSR9)", "0x%0.8x" % csrs[9])])
                 ] +
                sim_commands.get_pci_status(obj) +
                nic_common.get_nic_status(obj))

nic_common.new_nic_commands(device_name)

sim_commands.new_info_command(device_name, get_info)
sim_commands.new_status_command(device_name, get_status)
sim_commands.new_pci_header_command(device_name, None)
