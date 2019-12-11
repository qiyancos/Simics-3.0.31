#
#  ppc64_linux_process_tracker.py - a process tracker for linux on ppc64
#
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


# NOTE: This process tracker has been superseded by the generic
# linux-process-tracker.

# This process tracker distinguishes between different userspace
# processes (they get tids that are equal to their pids) and the
# kernel (which has tid -1). It has been tested on linux 2.4 and 2.6
# on ppc64.

# MODULE: ppc64-linux-process-tracker
# CLASS: ppc64-linux-process-tracker
class_name = "ppc64-linux-process-tracker"

from sim_core import *
import tracker

# Haps triggered by this module.
Core_Trackee_Active = SIM_hap_get_number("Core_Trackee_Active")
Core_Trackee_Exec = SIM_hap_get_number("Core_Trackee_Exec")

# Haps listened to by this module.
Core_Mode_Change = "Core_Mode_Change"
Core_Breakpoint_Memop = "Core_Breakpoint_Memop"

# Supported processors.
def supports_processor(classname):
    return (classname in ["ppc970fx", "ppc-power6"])

kernel_tid = -1

class tracker_instance:
    # Instance constructor
    def __init__(self, obj):
        obj.object_data = self
        self.obj = obj
        self.task_struct_offset_in_paca = 0
        self.pid_offset_in_task_struct = 0
        self.processors = []
        self.hap_handles = []
        self.current_tid = {}
        self.breakpoints = []
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

Process tracker for Linux on ppc64. <note>This process tracker has
been superseded by the generic
<class>linux-process-tracker</class>.</note>"""

SIM_register_class(class_name, class_data)

# Process tracking error.
class PTrackError(Exception):
    pass # excatly like Exception, but a new class

# Read a big-endian value from a virtual address.
def read_value(cpu, vaddr, len):
    try:
        paddr = SIM_logical_to_physical(cpu, Sim_DI_Data, vaddr)
    except:
        raise PTrackError("%s could not translate v:0x%x to physical"
                          % (cpu.name, vaddr))
    val = 0L
    for i in range(len):
        try:
            val = (val << 8) | SIM_read_phys_memory(cpu, paddr + i, 1)
        except:
            raise PTrackError("%s could not read byte at p:0x%x"
                              % (cpu.name, paddr + i))
    return val

# Read a null-terminated string from memory.
def read_string(cpu, vaddr):
    str = ""
    while 1:
        try:
            c = read_value(cpu, vaddr, 1)
        except PTrackError:
            c = 0
        if c == 0:
            return str
        str += "%c" % c
        vaddr += 1

# Read the value of a register.
def read_register(cpu, reg):
    try:
        return SIM_read_register(
            cpu, SIM_get_register_number(cpu, reg))
    except:
        raise PTrackError("Could not read register %s of %s" % (reg, cpu.name))

# Return the pid of the current process.
def get_current_pid(tracker, cpu):
    vp_paca = read_register(cpu, "sprg3")
    vp_task_struct = read_value(
        cpu, vp_paca + tracker.task_struct_offset_in_paca, 8)
    pid = read_value(cpu, vp_task_struct
                     + tracker.pid_offset_in_task_struct, 4)
    return pid

def get_current_tid(tracker, cpu, mode):
    if mode == Sim_CPU_Mode_User:
        return get_current_pid(tracker, cpu)
    else:
        return kernel_tid

# Hap handler for the Core_Mode_Change hap triggered by processors
# when they change privilege level.
def mode_change_hap(obj, cpu, old_mode, new_mode):
    try:
        tracker = obj.object_data
        old_tid = tracker.current_tid[cpu]
        new_tid = get_current_tid(tracker, cpu, new_mode)
        try:
            SIM_hap_occurred_always(Core_Trackee_Active, obj,
                                    old_tid, [old_tid, cpu, 0])
        except:
            pass
        try:
            SIM_hap_occurred_always(Core_Trackee_Active, obj,
                                    new_tid, [new_tid, cpu, 1])
        except:
            pass
        tracker.current_tid[cpu] = new_tid
    except PTrackError, e:
        SIM_log_message(obj, 1, 0, Sim_Log_Error,
                        "Process tracking failed on %s. (%s)" % (cpu.name, e))

# Breakpoint hap handler for the syscall breakpoint.
def syscall_callback(obj, mem, bp, memop):
    try:
        cpu = SIM_current_processor()
        syscall = read_register(cpu, "r0")

        # We're only interested in syscall 11 (execve).
        if syscall == 11:
            # The binary name is pointed to by register r3, but in order
            # to read it, we have to temporarily switch on
            # virtual->physical translations.
            msr_reg_no = SIM_get_register_number(cpu, "msr")
            original_msr = SIM_read_register(cpu, msr_reg_no)
            SIM_write_register(cpu, msr_reg_no, original_msr | 0x30)
            file = read_string(cpu, SIM_read_register(
                cpu, SIM_get_register_number(cpu, "r3")))
            SIM_write_register(cpu, msr_reg_no, original_msr)

            # The tid argument to this hap should be the user-mode pid
            # that made the system call.
            tid = get_current_pid(obj.object_data, cpu)
            try:
                SIM_hap_occurred_always(Core_Trackee_Exec, obj,
                                        tid, [tid, cpu, file])
            except:
                pass
    except PTrackError, e:
        SIM_log_message(obj, 1, 0, Sim_Log_Error,
                        "Process tracking failed on %s. (%s)" % cpu.name, e)

def warn_if_unsupported_cpu(obj, cpu):
    if supports_processor(cpu.classname):
        return
    SIM_log_message(
        obj, 1, 0, Sim_Log_Info,
        ("%s is of class %s which is not supported by this process tracker."
         + " Tracking processes on this processor might not work.")
        % (cpu.name, cpu.classname))

# Make sure everything is up-to-date when some attribute has changed.
def update(obj):
    tracker = obj.object_data
    for hap, id in tracker.hap_handles:
        SIM_hap_delete_callback_id(hap, id)
    for bp in tracker.breakpoints:
        SIM_delete_breakpoint(bp)
    tracker.hap_handles = []
    tracker.breakpoints = []
    tracker.current_tid = {}
    for cpu in tracker.processors:
        # Record current tid.
        try:
            tracker.current_tid[cpu] = get_current_tid(
                tracker, cpu, SIM_processor_privilege_level(cpu))
        except PTrackError, e:
            SIM_log_message(obj, 1, 0, Sim_Log_Error,
                            "Process tracking failed on %s. (%s)"
                            % (cpu.name, e))
            tracker.current_tid[cpu] = kernel_tid
        if tracker.num_users > 0:
            # Listen for mode change hap.
            tracker.hap_handles.append(
                (Core_Mode_Change,
                 SIM_hap_add_callback_obj(Core_Mode_Change, cpu, 0,
                                          mode_change_hap, obj)))
            # Watch for system calls.
            bp = SIM_breakpoint(cpu.physical_memory, Sim_Break_Physical,
                                Sim_Access_Execute, 0xc00, 4,
                                Sim_Breakpoint_Simulation)
            hap = SIM_hap_add_callback_index(
                Core_Breakpoint_Memop, syscall_callback, obj, bp)
            tracker.breakpoints.append(bp)
            tracker.hap_handles.append((Core_Breakpoint_Memop, hap))

def attr_task_struct_offset_in_paca():
    def get(arg, obj, idx):
        return obj.object_data.task_struct_offset_in_paca
    def set(arg, obj, val, idx):
        obj.object_data.task_struct_offset_in_paca = val
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "task_struct_offset_in_paca", get, None, set, None,
        Sim_Attr_Session, "i", None,
        "Offset (in bytes) of the task_struct pointer in the paca struct.")
attr_task_struct_offset_in_paca()

def attr_pid_offset_in_task_struct():
    def get(arg, obj, idx):
        return obj.object_data.pid_offset_in_task_struct
    def set(arg, obj, val, idx):
        obj.object_data.pid_offset_in_task_struct = val
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "pid_offset_in_task_struct", get, None, set, None,
        Sim_Attr_Session, "i", None,
        "Offset (in bytes) of the pid in the task_struct struct.")
attr_pid_offset_in_task_struct()

def get_processors(arg, obj, idx):
    return obj.object_data.processors

def set_processors(arg, obj, val, idx):
    obj.object_data.processors = val
    for cpu in val:
        warn_if_unsupported_cpu(obj, cpu)
    update(obj)
    return Sim_Set_Ok

SIM_register_typed_attribute(
    class_name, "processors",
    get_processors, None, set_processors, None,
    Sim_Attr_Session, "[o*]", None,
    "Processors whose modes are being tracked.")

def ifc_tracker():
    def active_trackee(obj, cpu):
        return obj.object_data.current_tid[cpu]
    def describe_trackee(obj, tid):
        if tid == kernel_tid:
            return "kernel"
        else:
            return "process %d" % tid
    def processor_list(obj):
        return obj.object_data.processors
    def add_processor(obj, cpu):
        if not cpu in obj.object_data.processors:
            warn_if_unsupported_cpu(obj, cpu)
            obj.object_data.processors.append(cpu)
            update(obj)
    def remove_processor(obj, cpu):
        if cpu in obj.object_data.processors:
            obj.object_data.processors.remove(cpu)
            update(obj)
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
ifc_tracker()

def ifc_tracker_settings():
    kernels = {
        "linux-2.5.70": ("Linux 2.5.70", 16, 236),
        "linux-2.6.6":  ("Linux 2.6.6",  16, 240),
        }
    kernel_list = list(kernels.keys())
    def settings_id_list():
        return kernel_list
    def describe_settings(settings_id):
        try:
            name, ts_offs, pid_offs = kernels[settings_id]
            return name
        except KeyError:
            return ""
    def use_settings(tracker, settings_id):
        try:
            name, ts_offs, pid_offs = kernels[settings_id]
            tracker.task_struct_offset_in_paca = ts_offs
            tracker.pid_offset_in_task_struct = pid_offs
            return 1
        except KeyError:
            return 0
    tracker_settings_if = tracker_settings_interface_t()
    tracker_settings_if.settings_id_list = settings_id_list
    tracker_settings_if.describe_settings = describe_settings
    tracker_settings_if.use_settings = use_settings
    SIM_register_interface(class_name, "tracker_settings", tracker_settings_if)
ifc_tracker_settings()

def ifc_tracker_unix():
    def trackee_type(tracker, tid):
        if tid > 0:
            return Sim_Trackee_Process
        elif tid == kernel_tid:
            return Sim_Trackee_Kernel
        else:
            return Sim_Trackee_Invalid
    def tid_to_pid(tracker, tid):
        if tid > 0:
            return tid
        else:
            raise SimExc_IllegalValue("tid has no corresponding pid")
    def pid_to_tid(tracker, pid):
        if pid > 0:
            return pid
        else:
            raise SimExc_Illegal_Value("illegal pid")
    tracker_unix_if = tracker_unix_interface_t()
    tracker_unix_if.trackee_type = trackee_type
    tracker_unix_if.tid_to_pid = tid_to_pid
    tracker_unix_if.pid_to_tid = pid_to_tid
    SIM_register_interface(class_name, "tracker_unix", tracker_unix_if)
ifc_tracker_unix()

from cli import *
import sim_commands

# status command prints dynamic information
def get_status(obj):
    plist = [cpu.name for cpu in obj.object_data.processors]
    return [(None, [("Processors", ", ".join(plist)),
                    ("Task struct offset in paca",
                     obj.object_data.task_struct_offset_in_paca),
                    ("PID offset in task struct",
                     obj.object_data.pid_offset_in_task_struct)])]

sim_commands.new_status_command(class_name, get_status)
