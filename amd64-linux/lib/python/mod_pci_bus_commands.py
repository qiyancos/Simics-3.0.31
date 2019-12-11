
##  Copyright 2000-2007 Virtutech AB
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
from sim_commands import *

device_name = get_last_loaded_module()

#
# -------------------- info --------------------
#

def slot_cmp((slot1, fun1, name1, en1), (slot2, fun2, name2, en2)):
    if slot1 == slot2:
        return cmp(fun1, fun2)
    return cmp(slot1, slot2)

def get_info(obj):
    devs = obj.pci_devices[:]
    devs.sort(slot_cmp)
    bridge_info = [("Bridge device", obj.bridge.name)]
    if obj.interrupt:
        bridge_info += [("Interrupt devices", [iobj.name for iobj in obj.interrupt])]

    return [ (None,
              bridge_info +
              [("PCI Bus Number", "0x%x" % obj.bus_number)]),
             (None,
              [ ("Config space", obj.conf_space),
                ("IO space", obj.io_space),
                ("Memory space", obj.memory_space)]),
             ("Connected devices",
              [ ("Slot %d function %d" % (dev[0], dev[1]), "%s%s"%(dev[2].name, iff(dev[3], "", " (disabled)")))
                for dev in devs ] ) ]

new_info_command(device_name, get_info)
