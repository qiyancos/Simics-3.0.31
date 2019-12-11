
##  Copyright 2001-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.

from cli import *
import string
import nic_common
import sim_commands

device_name = get_last_loaded_module()

rx_sizes = [32, 64, 128, 256]
    
def get_info(obj):
    if string.find(obj.classname, "sbus") < 0:
        pci_info = sim_commands.get_pci_info(obj)
    else:
        pci_info = []
    return ([ (None,
               [ ("Rx base addr", "0x%08x" % obj.rx_desc_base),
                 ("Rx ring size", rx_sizes[obj.rx_ring_size_idx]),
                 ("Tx base addr", "0x%08x" % obj.tx_desc_base),
                ("Tx ring size", obj.tx_ring_size) ])
              ] +
            nic_common.get_nic_info(obj) +
            pci_info)


def get_status(obj):
    if string.find(obj.classname, "sbus") < 0:
        pci_status = sim_commands.get_pci_status(obj)
    else:
        pci_status = []
    return ([ (None,
               [ ("Packets sent", obj.pkt_snt),
                 ("Packets received", obj.pkt_rec) ])] +
            nic_common.get_nic_status(obj) +
            pci_status)

nic_common.new_nic_commands(device_name)

sim_commands.new_info_command(device_name, get_info)
sim_commands.new_status_command(device_name, get_status)

if string.find(device_name, "sbus") < 0:
    sim_commands.new_pci_header_command(device_name, None)
