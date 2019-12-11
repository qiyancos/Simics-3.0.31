
##  sample_device_python.py - sample code for a Simics device

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

# First, the following structured comments are required. They must come first
# in the file, preceded only by comments and blank lines:

# MODULE: sample-device-python
# CLASS: sample-device-python

# The MODULE line gives the name of this module, and each CLASS line names
# a configuration class defined by the module (there can be zero or more).
#
# Note that Python source file names must not contain dashes ("-"), so
# this file is called "sample_device_python.py".

from sim_core import *

# The name of the class defined in this file, as a convenient shorthand
class_name = "sample-device-python"

class sample_device_instance:
    # Instance constructor
    def __init__(self, obj):
        # Update the mapping from configuration objects to this instance,
        # and the other way.
        obj.object_data = self
        self.obj = obj

        # Initialize instance variables (we only have one).
        self.temperature = 0

    def read_temperature(self):
        return self.temperature

    def write_temperature(self, value):
        self.temperature = value

# Create a new configuration object and instance object of the class.
# This is called each time a new object of class sample-device-python
# is created. You probably do not need to modify this code.

def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    sample_device_instance(obj)
    return obj

# The following function is called after the object is created and all
# attributes from the configuration are set. All other objects in the
# machine also exist at this point.

def finalize_instance(obj):
    pass

# Functions implementing the io-memory interface for sample-device-python:

# sample_operation() is called whenever a memory access (read/write)
# is performed to an address mapped to a sample-device-python object.
# On errors, the simulation is stopped with an error message. This is
# appropriate when debugging a module.

def sample_operation(obj, mop, info):
    # offset in  our memory mapping
    offset = mop.physical_address + info.start - info.base

    # find corresponding instance data
    inst = obj.object_data

    # Find out what to do:
    if offset == 0x00:
        # our register 0 is read-only and reads the temperature
        if SIM_mem_op_is_read(mop):
            # we are a little endian device
            SIM_set_mem_op_value_le(mop, inst.read_temperature())
        else:
            print "Offset 0x00 is read-only"
            SIM_break_simulation("Illegal " + class_name + " access")
    elif offset == 0x01:
        # our register 1 is write-only, and sets the temperature
        if SIM_mem_op_is_write(mop):
            # we are a little endian device
            inst.write_temperature(SIM_get_mem_op_value_le(mop))
        elif mop.inquiry:
            return Sim_PE_Inquiry_Unhandled
        else:
            print "Offset 0x01 is write-only"
            SIM_set_mem_op_value_le(mop, 0)
            SIM_break_simulation("Illegal " + class_name + " access")
    else:
        # bad offset
        if mop.inquiry:
            return Sim_PE_Inquiry_Unhandled
        if SIM_mem_op_is_read(mop):
            SIM_set_mem_op_value_le(mop, 0)
        print "Offset %x is not part of this device." % offset
        SIM_break_simulation("Illegal " + class_name + " access")
    return Sim_PE_No_Exception


# These functions are called when the attribute "temperature" is read or set.

def get_temperature(arg, obj, idx):
    return obj.object_data.temperature

def set_temperature(arg, obj, val, idx):
    obj.object_data.temperature = val
    return Sim_Set_Ok


# The top-level code in the file is run when the module is loaded.
# It should create the implemented configuration classes and register
# all attributes.

# First, register the class "sample-device-python" with Simics:

class_data = class_data_t()
class_data.new_instance = new_instance           # function defined above
class_data.finalize_instance = finalize_instance # function defined above
class_data.description = """
    This device does nothing useful, but can be used as a starting
    point when writing Simics devices in Python.
    The source can be found at
    <tt>simics/src/devices/sample-device-python</tt>.""";
SIM_register_class(class_name, class_data)

# Next, register the attributes of this class:

SIM_register_typed_attribute(class_name, "temperature",
                             get_temperature, None,
                             set_temperature, None,
                             Sim_Attr_Optional,
                             "i", None,
                             "The <i>temperature</i> register.")

# Finally, register the interfaces used by this class. In our case, we only
# implement the io-memory interface, which is the interface for memory-mapped
# peripherals.

io_if = io_memory_interface_t()
io_if.operation = sample_operation
SIM_register_interface(class_name, "io_memory", io_if)


# Since this is a Python file, the module commands can be defined here,
# instead of using a separate commands.py file.

from cli import *
import sim_commands

# info command prints static information
def get_info(obj):
    return []

# status command prints dynamic information
def get_status(obj):
    return [("Registers",
             [("Temperature", obj.temperature)])]

sim_commands.new_info_command(class_name, get_info)
sim_commands.new_status_command(class_name, get_status)


# If you want to quickly try your new device code, go to the directory
# SIMICS/home/vacuum.  There is a startup script there called
# "vacuum.simics", which loads the sample-device-python device.
# Replace that name with the name of your new device to try it!
# But do not forget to "make" the module before trying it.

