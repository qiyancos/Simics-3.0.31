
##  empty_python_device.py - sample code for a Simics device

##  Copyright 1998-2007 Virtutech AB
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

# Use this file as a skeleton for your own device implementation in Python.

# MODULE: empty-python-device
# CLASS: empty-python-device

from sim_core import *

class_name = "empty-python-device"

class empty_python_device_instance:
    # Instance constructor
    def __init__(self, obj):
        # Update the mapping from configuration objects to this instance,
        # and the other way.
        obj.object_data = self
        self.obj = obj

        # Initialize instance variables
        self.value = 0

def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    empty_python_device_instance(obj)
    return obj

def finalize_instance(obj):
    pass

# operation() is called whenever a memory access (read/write)
# is performed to an address mapped by the empty-python-device object.

def operation(obj, mop, info):
    # offset in the memory mapping
    offset = mop.physical_address + info.start - info.base

    # find instance data
    inst = obj.object_data

    if SIM_mem_op_is_read(mop):
        SIM_set_mem_op_value_le(mop, inst.value)
    else:
        inst.value = SIM_get_mem_op_value_le(mop)
    return Sim_PE_No_Exception

# Attribute get/set functions

def get_value(arg, obj, idx):
    return obj.object_data.value

def set_value(arg, obj, val, idx):
    obj.object_data.value = val
    return Sim_Set_Ok

# Initialization code run when module is loaded

class_data = class_data_t()
class_data.new_instance = new_instance
class_data.finalize_instance = finalize_instance
class_data.description = """
    This device does nothing useful, but can be used as a starting
    point when writing Simics devices in Python.
    The source can be found in
    <tt>[simics]/src/devices/empty-device-python/</tt>.""";
SIM_register_class(class_name, class_data)

SIM_register_typed_attribute(class_name, "value",
                             get_value, None,
                             set_value, None,
                             Sim_Attr_Optional,
                             "i", None,
                             "The <i>value</i> register.")

io_iface = io_memory_interface_t()
io_iface.operation = operation
SIM_register_interface(class_name, "io_memory", io_iface)


# Since this is a Python file, the module commands can be defined here,
# instead of using a separate commands.py file.

import sim_commands

# info command prints static information
def get_info(obj):
    return []

# status command prints dynamic information
def get_status(obj):
    return [("Registers",
             [("Value", obj.value)])]

sim_commands.new_info_command(class_name, get_info)
sim_commands.new_status_command(class_name, get_status)
