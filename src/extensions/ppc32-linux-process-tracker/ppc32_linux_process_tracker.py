
##  ppc32_linux_process_tracker.py - a process tracker for linux on ppc32

##  Copyright 1991-2007 Virtutech AB
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

# MODULE: ppc32-linux-process-tracker
# CLASS: ppc32-linux-process-tracker
class_name = "ppc32-linux-process-tracker"

from conf import *
from sim_core import *
import tracker

# Haps triggered by this module.
Core_Trackee_Active = SIM_hap_get_number("Core_Trackee_Active")
Core_Trackee_Exec = SIM_hap_get_number("Core_Trackee_Exec")

# Haps listened to by this module.
Core_Mode_Change = "Core_Mode_Change"
Core_Exception = "Core_Exception"
Core_Breakpoint_Memop = "Core_Breakpoint_Memop"

# Supported processors.
def supports_processor(classname):
    return (classname in ["ppc750", "ppc440gp"])

kernel_tid = -1

class exec_state:
    # State for tracking exec() syscalls. Sometimes the program string
    # can't be read immediately; in that case we set a breakpoint on
    # the string and wait until the OS tries to read it. Repeat until
    # success.
    def __init__(self, obj, cpu, pid, address):
        self.obj = obj
        self.cpu = cpu
        self.pid = pid
        self.address = address
        self.active = False
        self.hap_handle = None
        self.breakpoint = None
    def __nonzero__(self):
        return self.active
    def try_to_trigger(self):
        file, all = read_string(self.cpu, self.address)
        if all:
            self.active = False
            self.update()
            try:
                SIM_hap_occurred_always(Core_Trackee_Exec, self.obj,
                                        self.pid, [self.pid, self.cpu, file])
            except:
                pass
        return all
    def callback(self, dummy, mem, bp, memop):
        self.try_to_trigger()
    def update(self):
        # Remove breakpoint.
        if self.hap_handle != None:
            SIM_hap_delete_callback_id(Core_Breakpoint_Memop, self.hap_handle)
            self.hap_handle = None
        if self.breakpoint != None:
            SIM_delete_breakpoint(self.breakpoint)
            self.breakpoint = None
        # Set breakpoint if we're active.
        if self.active:
            self.breakpoint = SIM_breakpoint(
                self.cpu.current_context, Sim_Break_Virtual,
                Sim_Access_Read, self.address, 100,
                Sim_Breakpoint_Simulation)
            self.hap_handle = SIM_hap_add_callback_index(
                Core_Breakpoint_Memop, self.callback, None, self.breakpoint)

class tracker_instance:
    # Instance constructor
    def __init__(self, obj):
        obj.object_data = self
        self.obj = obj
        self.pid_offset = 0
        self.thread_offset = 0
        self.processors = {}
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

Process tracker for Linux on ppc32. <note>This process tracker has
been superseded by the generic
<class>linux-process-tracker</class>.</note>"""

SIM_register_class(class_name, class_data)

# Process tracking error.
class PTrackError(Exception):
    pass # excatly like Exception, but a new class

# Read a big-endian value from a physical address.
def read_phys_value(cpu, paddr, len):
    val = 0L
    for i in range(len):
        try:
            val = (val << 8) | SIM_read_phys_memory(cpu, paddr + i, 1)
        except:
            raise PTrackError("%s could not read byte at p:0x%x"
                              % (cpu.name, paddr + i))
    return val

# Read a big-endian value from a virtual address.
def read_virt_value(cpu, vaddr, len):
    try:
        paddr = SIM_logical_to_physical(cpu, Sim_DI_Data, vaddr)
    except:
        raise PTrackError("%s could not translate v:0x%x to physical"
                          % (cpu.name, vaddr))
    return read_phys_value(cpu, paddr, len)

# Read a null-terminated string from memory. The second part of the
# tuple is true if the entire string was read, false otherwise.
def read_string(cpu, vaddr):
    str = ""
    while 1:
        try:
            c = read_virt_value(cpu, vaddr, 1)
        except PTrackError:
            return (str, False)
        if c == 0:
            return (str, True)
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
    p_thread = read_register(cpu, "sprg3")
    p_task_struct = p_thread - tracker.thread_offset
    p_pid = p_task_struct + tracker.pid_offset
    if p_pid & 0xc0000000 == 0:
        pid = read_phys_value(cpu, p_pid, 4)
    else:
        pid = read_virt_value(cpu, p_pid, 4)
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

# Hap handler for syscalls.
def syscall_callback(obj, cpu, exception_number):
    try:
        syscall = read_register(cpu, "r0")

        # We're only interested in syscall 11 (execve).
        if syscall == 11:
            state = exec_state(
                obj, cpu, get_current_pid(obj.object_data, cpu),
                read_register(cpu, "r3"))
            if not state.try_to_trigger():
                state.active = True
                state.update()
                obj.object_data.processors[cpu] = state
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
    for cpu, exec_state in tracker.processors.iteritems():
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
            try:
                exc_num = cpu.iface.exception.get_number(cpu, "System_call")
                tracker.hap_handles.append(
                    (Core_Exception,
                     SIM_hap_add_callback_obj_index(
                    Core_Exception, cpu, 0, syscall_callback, obj, exc_num)))
            except:
                SIM_log_message(obj, 1, 0, Sim_Log_Error,
                                "Process tracking failed on %s." % cpu.name)
        # Update exec state.
        if exec_state:
            if not tracker.num_users > 0:
                exec_state.active = False
            exec_state.update()

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

def attr_thread_offset():
    def get(arg, obj, idx):
        return obj.object_data.thread_offset
    def set(arg, obj, val, idx):
        obj.object_data.thread_offset = val
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "thread_offset", get, None, set, None,
        Sim_Attr_Session, "i", None,
        ("""Offset (in bytes) of the thread struct in the task_struct
        struct. This can be found by disassembling the
        <tt>transfer_to_handler</tt> kernel function."""))
attr_thread_offset()

def attr_processors():
    def get(arg, obj, idx):
        return list(obj.object_data.processors.keys())
    def set(arg, obj, val, idx):
        def mkset(iter):
            set = {}
            for x in iter:
                set[x] = True
            return set
        old_processors = dict(obj.object_data.processors)
        new_processors = mkset(val)
        for cpu, exec_state in old_processors.iteritems():
            if not cpu in new_processors:
                if exec_state:
                    exec_state.active = False
                    exec_state.update()
                del obj.object_data.processors[cpu]
        for cpu in new_processors.iterkeys():
            if not cpu in old_processors:
                warn_if_unsupported_cpu(obj, cpu)
                obj.object_data.processors[cpu] = None
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "processors", get, None, set, None,
        Sim_Attr_Session, "[o*]", None,
        "Processors whose modes are being tracked.")
attr_processors()

def attr_per_cpu_state():
    def get(arg, obj, idx):
        def getattr(cpu, exec_state):
            if exec_state:
                attr = [exec_state.pid, exec_state.address]
            else:
                attr = []
            return [cpu, attr]
        return [getattr(cpu, exec_state) for cpu, exec_state
                in obj.object_data.processors.iteritems()]
    def set(arg, obj, val, idx):
        def setattr(dict, cpu, attr):
            if cpu in dict:
                if dict[cpu]:
                    dict[cpu].active = False
                    dict[cpu].update()
                try:
                    pid, addr = attr
                    dict[cpu] = exec_state(obj, cpu, pid, addr)
                    dict[cpu].active = True
                except ValueError:
                    dict[cpu] = None
        for cpu, attr in val:
            setattr(obj.object_data.processors, cpu, attr)
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "per_cpu_state", get, None, set, None,
        Sim_Attr_Optional, "[[o[a*]]*]", None,

        """Per-processor state that has to be maintained by the
        process tracker.""")

attr_per_cpu_state()

def ifc_tracker():
    def active_trackee(obj, cpu):
        return obj.object_data.current_tid[cpu]
    def describe_trackee(obj, tid):
        if tid == kernel_tid:
            return "kernel"
        else:
            return "process %d" % tid
    def processor_list(obj):
        return obj.object_data.processors.keys()
    def add_processor(obj, cpu):
        if not cpu in obj.object_data.processors:
            warn_if_unsupported_cpu(obj, cpu)
            obj.object_data.processors[cpu] = None
            update(obj)
    def remove_processor(obj, cpu):
        if cpu in obj.object_data.processors:
            del obj.object_data.processors[cpu]
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
        "linux-2.4.17": ("Linux 2.4.17", 624, 144),
        "linux-2.4.31": ("Linux 2.4.31", 616, 140),
        }
    kernel_list = list(kernels.keys())
    def settings_id_list():
        return kernel_list
    def describe_settings(settings_id):
        try:
            name, thread_offs, pid_offs = kernels[settings_id]
            return name
        except KeyError:
            return ""
    def use_settings(tracker, settings_id):
        try:
            name, thread_offs, pid_offs = kernels[settings_id]
            tracker.thread_offset = thread_offs
            tracker.pid_offset = pid_offs
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
    plist = [cpu.name for cpu in obj.object_data.processors.iterkeys()]
    return [(None, [("Processors", ", ".join(plist)),
                    ("Thread offset", obj.object_data.thread_offset),
                    ("PID offset", obj.object_data.pid_offset)])]

sim_commands.new_status_command(class_name, get_status)
