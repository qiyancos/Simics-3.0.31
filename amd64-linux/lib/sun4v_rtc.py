#
#  sun4v_rtc.py
#
#  Copyright (C) 2005 Virtutech AB, All Rights Reserved
#
#  This program is a component ("Component") of Virtutech Simics and is
#  being distributed under Section 1(a)(iv) of the Virtutech Simics
#  Software License Agreement (the "Agreement").  You should have
#  received a copy of the Agreement with this Component; if not, please
#  write to Virtutech AB, Norrtullsgatan 15, 1tr, SE-113 27 STOCKHOLM,
#  Sweden for a copy of the Agreement prior to using this Component.
#
#  By using this Component, you agree to be bound by all of the terms of
#  the Agreement.  If you do not agree to the terms of the Agreement, you
#  may not use, copy or otherwise access the Component or any derivatives
#  thereof.  You may create and use derivative works of this Component
#  pursuant to the terms the Agreement provided that any such derivative
#  works may only be used in conjunction with and as a part of Virtutech
#  Simics for use by an authorized licensee of Virtutech.
#
#  THIS COMPONENT AND ANY DERIVATIVES THEREOF ARE PROVIDED ON AN "AS IS"
#  BASIS.  VIRTUTECH MAKES NO WARRANTIES WITH RESPECT TO THE COMPONENT OR
#  ANY DERIVATIVES THEREOF AND DISCLAIMS ALL IMPLIED WARRANTIES,
#  INCLUDING, WITHOUT LIMITATION, WARRANTIES OF MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.

# MODULE: sun4v-rtc
# CLASS: sun4v-rtc

from sim_core import *
import time

class_name = 'sun4v-rtc'
device_instances = {}    

class rtc_instance:
    # Instance constructor
    def __init__(self, conf_obj):
        global device_instances
        device_instances[conf_obj] = self
        self.obj = conf_obj
        self.start_time = 1143631685

    def current_time(self):
        return SIM_time(self.obj.queue) + self.start_time

    def set_time(self, val):
        self.start_time = val - SIM_time(self.obj.queue)
            
def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    rtc_instance(obj)
    return obj

def rtc_operation(obj, mop, info):
    offset = mop.physical_address + info.start - info.base

    if mop.inquiry:
        return Sim_PE_Inquiry_Unhandled
    if mop.size != 8:
        print 'Illegal access size: %d bytes' % mop.size
        SIM_break_simulation('Illegal ' + class_name + ' access')
        return Sim_PE_No_Exception

    # find corresponding instance data
    inst = device_instances[obj]

    # Find out what to do:
    if offset == 0x00:
        if SIM_mem_op_is_read(mop):
            SIM_set_mem_op_value_be(mop, inst.current_time())
        else:
            inst.set_time(SIM_get_mem_op_value_be(mop))
    else:
        if SIM_mem_op_is_read(mop):
            SIM_set_mem_op_value_be(mop, 0)
        print 'Offset %x is not part of this device.' % offset
        SIM_break_simulation('Illegal ' + class_name + ' access')
    return Sim_PE_No_Exception

def get_start_time(arg, obj, idx):
    return device_instances[obj].start_time

def set_start_time(arg, obj, val, idx):
    device_instances[obj].start_time = val
    return Sim_Set_Ok

class_data = class_data_t()
class_data.new_instance = new_instance
class_data.description = 'Real time clock for sun4v systems.'

SIM_register_class(class_name, class_data)

SIM_register_typed_attribute(
    class_name, 'start_time',
    get_start_time, None,
    set_start_time, None,
    Sim_Attr_Optional,
    'i', None,
    'The time, as seconds in standard Unix format, when the simulation was '
    'started.')

io_if = io_memory_interface_t()
io_if.operation = rtc_operation
SIM_register_interface(class_name, 'io_memory', io_if)

from cli import *
import sim_commands

# info command prints static information
def get_info(obj):
    return []

# status command prints dynamic information
def get_status(obj):
    inst = device_instances[obj]
    return [('Registers',
             [('Seconds', str(long(inst.current_time())))]),
            ('Other', [('Time', time.ctime(inst.current_time()))])]

sim_commands.new_info_command(class_name, get_info)
sim_commands.new_status_command(class_name, get_status)
