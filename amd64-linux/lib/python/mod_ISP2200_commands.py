
##  Copyright 2003-2007 Virtutech AB

from cli import *
import sim_commands

device_name = get_last_loaded_module()

def get_info(obj):
    return ([ (None,
               [ ("Loop ID", obj.loop_id),
                 ("Node Name", obj.node_name),
                 ("Port Name", obj.port_name),
                 ] ),
              ("Attached disks",
               obj.fc_disks)] +
            sim_commands.get_pci_info(obj))

def get_status(obj):
    return [] + sim_commands.get_pci_status(obj)

sim_commands.new_info_command(device_name, get_info)
sim_commands.new_status_command(device_name, get_status)
sim_commands.new_pci_header_command(device_name, None)
