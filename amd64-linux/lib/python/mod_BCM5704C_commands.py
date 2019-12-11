
##  Copyright 2003-2007 Virtutech AB
##  
##  This file is part of the Virtutech Simics, which is distributed
##  under the Virtutech Simics Software License Agreement.

from cli import *
import nic_common
import sim_commands

device_name = get_last_loaded_module()

def get_info(obj):
    # FIXME: add device specific info
    return (nic_common.get_nic_info(obj) +
            sim_commands.get_pci_info(obj))

def get_status(obj):
    # FIXME: add device specific status
    return (nic_common.get_nic_status(obj) +
            sim_commands.get_pci_status(obj))

nic_common.new_nic_commands(device_name)

sim_commands.new_info_command(device_name, get_info)
sim_commands.new_status_command(device_name, get_status)
sim_commands.new_pci_header_command(device_name, None)
