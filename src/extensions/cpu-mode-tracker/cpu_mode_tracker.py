
## cpu_mode_tracker.py - a "process tracker" that tracks only the
##                       processor user/supervisor modes
                         
##  Copyright 2005-2007 Virtutech AB
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

# This tracker doesn't distinguish between different userspace
# processes. It has separate tids for each of the processor privilege
# levels.

# MODULE: cpu-mode-tracker
# CLASS: cpu-mode-tracker
class_name = "cpu-mode-tracker"

from sim_core import *
import tracker

Core_Trackee_Active = SIM_hap_get_number("Core_Trackee_Active")

class tracker_instance:
    # Instance constructor
    def __init__(self, obj):
        obj.object_data = self
        self.obj = obj
        self.processors = []
        self.hap_handles = []
        self.num_users = 0

def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    tracker_instance(obj)
    return obj

def finalize_instance(obj):
    pass

class_data = class_data_t()
class_data.new_instance = new_instance
class_data.finalize_instance = finalize_instance
class_data.kind = Sim_Class_Kind_Session
class_data.description = """
    This is a process tracker that is only able to track the processor
    mode (user or supervisor), and not individual processes.""";
SIM_register_class(class_name, class_data)

# Hap handler for the Core_Mode_Change hap triggered by processors
# when they change privilege level.
def mode_change_hap(obj, cpu, old_mode, new_mode):
    try:
        SIM_hap_occurred_always(Core_Trackee_Active, obj,
                                old_mode, [old_mode, cpu, 0])
    except:
        pass
    try:
        SIM_hap_occurred_always(Core_Trackee_Active, obj,
                                new_mode, [new_mode, cpu, 1])
    except:
        pass

def update(obj):
    for h in obj.object_data.hap_handles:
        SIM_hap_delete_callback_id("Core_Mode_Change", h)
    obj.object_data.hap_handles = []
    if obj.object_data.num_users > 0:
        obj.object_data.hap_handles = [
            SIM_hap_add_callback_obj("Core_Mode_Change", cpu, 0,
                                     mode_change_hap, obj)
            for cpu in obj.object_data.processors]

def get_processors(arg, obj, idx):
    return obj.object_data.processors

def set_processors(arg, obj, val, idx):
    obj.object_data.processors = val
    update(obj)
    return Sim_Set_Ok

SIM_register_typed_attribute(
    class_name, "processors",
    get_processors, None, set_processors, None,
    Sim_Attr_Session, "[o*]", None,
    "Processors whose modes are being tracked.")

def active_trackee(obj, cpu):
    return SIM_cpu_privilege_level(cpu)

def describe_trackee(obj, tid):
    return "cpu mode %d" % tid

def processor_list(obj):
    return obj.object_data.processors

def add_processor(obj, cpu):
    if not cpu in obj.object_data.processors:
        obj.object_data.processors.append(cpu)
        update(obj)

def remove_processor(obj, cpu):
    if cpu in obj.object_data.processors:
        obj.object_data.processors.remove(cpu)
        update(obj)

def supports_processor(class_name):
    return 1 # supports all processors

def activate(obj):
    obj.object_data.num_users += 1
    update(obj)

def deactivate(obj):
    obj.object_data.num_users -= 1
    update(obj)

tracker_if = tracker_interface_t()
tracker_if.active_trackee = active_trackee
tracker_if.describe_trackee = describe_trackee
tracker_if.processor_list = processor_list
tracker_if.add_processor = add_processor
tracker_if.remove_processor = remove_processor
tracker_if.supports_processor = supports_processor
tracker_if.activate = activate
tracker_if.deactivate = deactivate
SIM_register_interface(class_name, "tracker", tracker_if)

from cli import *
import sim_commands

# status command prints dynamic information
def get_status(obj):
    plist = [cpu.name for cpu in obj.object_data.processors]
    return [(None, [("Processors", ", ".join(plist))])]

sim_commands.new_status_command(class_name, get_status)
