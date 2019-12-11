
##  x86_linux_process_tracker.py - a process tracker for linux on x86

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
# kernel (which has tid -1).

# MODULE: x86-linux-process-tracker
# CLASS: x86-linux-process-tracker
class_name = "x86-linux-process-tracker"

from conf import *
from sim_core import *
import tracker

# Haps triggered by this module.
Core_Trackee_Active = SIM_hap_get_number("Core_Trackee_Active")
Core_Trackee_Exec = SIM_hap_get_number("Core_Trackee_Exec")

# Haps listened to by this module.
Core_Mode_Change = "Core_Mode_Change"
Core_Exception = "Core_Exception"

# Supported processors.
def supports_processor(classname):
    return (classname in ["x86-p2", "x86-p4"])

kernel_tid = -1

class tracker_instance:
    # Instance constructor
    def __init__(self, obj):
        obj.object_data = self
        self.obj = obj
        self.kernel_stack_size = 0
        self.pid_offset = 0
        self.processors = []
        self.hap_handles = []
        self.current_tid = {}
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

Process tracker for Linux on x86. <note>This process tracker has been
superseded by the generic
<class>linux-process-tracker</class>.</note>"""

SIM_register_class(class_name, class_data)

# Process tracking error.
class PTrackError(Exception):
    pass # excatly like Exception, but a new class

# Read a little-endian value from a physical address.
def read_phys_value(cpu, paddr, len):
    val = 0L
    for i in range(len - 1, -1, -1):
        try:
            val = (val << 8) | SIM_read_phys_memory(cpu, paddr + i, 1)
        except:
            raise PTrackError("%s could not read byte at p:0x%x"
                              % (cpu.name, paddr + i))
    return val

# Read a little-endian value from a virtual address.
def read_virt_value(cpu, vaddr, len):
    try:
        paddr = SIM_logical_to_physical(cpu, Sim_DI_Data, vaddr)
    except:
        raise PTrackError("%s could not translate v:0x%x to physical"
                          % (cpu.name, vaddr))
    return read_phys_value(cpu, paddr, len)

# Read a null-terminated string from memory.
def read_string(cpu, vaddr):
    str = ""
    while 1:
        c = read_virt_value(cpu, vaddr, 1)
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

def cpu_mode(cpu):
    if SIM_processor_privilege_level(cpu) == 3:
        return Sim_CPU_Mode_User
    else:
        return Sim_CPU_Mode_Supervisor

# Return the pid of the currently executing process.
def get_current_pid(tracker, cpu):

    # The kernel stack pointer is stored at offset 4 from the base of
    # the tr segment.
    (tr_selector, tr_d, tr_dpl, tr_g, tr_p, tr_s, tr_type,
     tr_base, tr_limit, tr_valid) = cpu.tr
    esp = read_virt_value(cpu, tr_base + 4, 4)

    # Some stuff is pushed onto the stack during the user->supervisor
    # switch, but since we always mask away the low bits of the stack
    # pointer, and those low bits are all zero before those pushes, 1
    # byte is a sufficiently good approximation of the size of that
    # stuff.
    esp = esp - 1

    # Pointer to current task_struct is at the bottom of the stack
    # area.
    v_current = esp & ~(tracker.kernel_stack_size - 1)

    # pid of current process is a 4-byte field in the task_struct.
    v_pid = v_current + tracker.pid_offset
    return read_virt_value(cpu, v_pid, 4)

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

# Hap handler for syscalls.
def syscall_callback(obj, cpu, exception_number):
    try:
        syscall = read_register(cpu, "eax")
        if syscall == 11: # execve
            binary = read_string(cpu, read_register(cpu, "ebx"))
            tid = get_current_pid(obj.object_data, cpu)
            try:
                SIM_hap_occurred_always(Core_Trackee_Exec, obj,
                                        tid, [tid, cpu, binary])
            except:
                pass
    except PTrackError, e:
        SIM_log_message(obj, 1, 0, Sim_Log_Error,
                        "Process tracking failed on %s. (%s)" % (cpu.name, e))

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
    tracker.hap_handles = []
    tracker.current_tid = {}
    for cpu in tracker.processors:
        # Record current tid.
        try:
            tracker.current_tid[cpu] = get_current_tid(tracker, cpu,
                                                       cpu_mode(cpu))
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
            try:
                exc_num = cpu.iface.exception.get_number(
                    cpu, "Software_Interrupt_128")
                tracker.hap_handles.append(
                    (Core_Exception,
                     SIM_hap_add_callback_obj_index(
                    Core_Exception, cpu, 0, syscall_callback, obj, exc_num)))
            except:
                SIM_log_message(obj, 1, 0, Sim_Log_Error,
                                "Process tracking failed on %s." % cpu.name)

def attr_pid_offset():
    def get(arg, obj, idx):
        return obj.object_data.pid_offset
    def set(arg, obj, val, idx):
        obj.object_data.pid_offset = val
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "pid_offset", get, None, set, None,
        Sim_Attr_Session, "i", None,
        ("""Offset (in bytes) of the pid in the task_struct struct.
        This can be found by disassembling the kernel's
        <tt>getpid</tt> syscall."""))
attr_pid_offset()

def attr_kernel_stack_size():
    def p2(n):
        return n > 0 and n & (n - 1) == 0
    def get(arg, obj, idx):
        return obj.object_data.kernel_stack_size
    def set(arg, obj, val, idx):
        if not p2(val):
            print "Error: kernel_stack_size must be a power of two."
            return Sim_Set_Illegal_Value
        obj.object_data.kernel_stack_size = val
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "kernel_stack_size", get, None, set, None,
        Sim_Attr_Session, "i", None,
        ("""Size (in bytes) of a kernel stack. Must be a power of two.
        4096 bytes in some 2.6 kernels; otherwise 8192 bytes."""))
attr_kernel_stack_size()

def attr_processors():
    def get(arg, obj, idx):
        return obj.object_data.processors
    def set(arg, obj, val, idx):
        obj.object_data.processors = val
        for cpu in val:
            warn_if_unsupported_cpu(obj, cpu)
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "processors", get, None, set, None,
        Sim_Attr_Session, "[o*]", None,
        "Processors whose modes are being tracked.")
attr_processors()

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
        "linux-2.2.21": ("Linux 2.2.21", 100, 8192),
        "linux-2.4.18": ("Linux 2.4.18", 132, 8192),
        }
    kernel_list = list(kernels.keys())
    def settings_id_list():
        return kernel_list
    def describe_settings(settings_id):
        try:
            name, pid_offs, stack_size = kernels[settings_id]
            return name
        except KeyError:
            return ""
    def use_settings(tracker, settings_id):
        try:
            name, pid_offs, stack_size = kernels[settings_id]
            tracker.pid_offset = pid_offs
            tracker.kernel_stack_size = stack_size
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
                    ("Kernel stack size", obj.object_data.kernel_stack_size),
                    ("PID offset", obj.object_data.pid_offset)])]

sim_commands.new_status_command(class_name, get_status)
