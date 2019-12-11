
##  linux_process_tracker.py - a process tracker for linux

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

# This process tracker distinguishes between different userspace
# processes (they get tids that are equal to their pids) and the
# kernel (which has tid -1).

# MODULE: linux-process-tracker
# CLASS: linux-process-tracker
class_name = "linux-process-tracker"

from conf import *
from sim_core import *
import tracker

# Haps triggered by this module.
Core_Trackee_Active = SIM_hap_get_number("Core_Trackee_Active")
Core_Trackee_Exec = SIM_hap_get_number("Core_Trackee_Exec")

# Haps listened to by this module.
Core_Breakpoint_Memop = "Core_Breakpoint_Memop"
Core_Exception = "Core_Exception"
Core_Mode_Change = "Core_Mode_Change"

kernel_tid = -1

######################################################################
# Utility functions.
######################################################################

def fold(fun, first, iter):
    for e in iter:
        first = fun(first, e)
    return first

# Process tracking error.
class PTrackError(Exception):
    pass

# Error during parameter autodetection.
class PTrackAutodetectFail(PTrackError):
    pass

# Missing required parameter(s).
class PTrackMissingParam(PTrackError):
    def __init__(self, missing):
        self.missing = missing
    def __str__(self):
        return ("Process tracker parameters missing: %s"
                % ", ".join(self.missing))

# Raise exception if expr is false.
def ensure(expr):
    if not expr:
        raise PTrackError()

# Return an arbitrary key from the dictionary, or None if it's empty.
def anykey(dict):
    for k in dict.iterkeys():
        return k

######################################################################
# Processor-specific operations.
######################################################################

Physical, Kernel, User = Address_Types = range(3)

class Address(object):
    def __init__(self, addr, type):
        ensure(type in Address_Types)
        self.addr = long(addr)
        self.type = type
    def ensure_type(self, type):
        ensure(self.type == type)
    def __hash__(self):
        return (self.addr, self.type).__hash__()
    def __cmp__(self, other):
        return cmp((self.addr, self.type), (other.addr, other.type))
    def __add__(self, other):
        return Address(self.addr + other, self.type)
    def __sub__(self, other):
        return Address(self.addr - other, self.type)
    def __str__(self):
        return "%s:0x%x" % ({Physical: "p", Kernel: "v", User: "v"}[self.type],
                            self.addr)

class syscall_catcher(object):
    def __init__(self, exec_syscall_nums, get_syscall_num, get_syscall_param):
        self.exec_syscall_nums = exec_syscall_nums
        self.get_syscall_num = get_syscall_num
        self.get_syscall_param = get_syscall_param
    def syscall(self, obj, cpu):
        try:
            tracker = obj.object_data
            ops = tracker.cpu_ops
            syscall = self.get_syscall_num(cpu)
            if syscall in self.exec_syscall_nums:
                state = exec_state(
                    obj, cpu, ops.get_current_pid(cpu, tracker.param),
                    Address(self.get_syscall_param(cpu), User))
                if not state.try_to_trigger():
                    state.update(active = True)
                    tracker.processors[cpu] = state
        except PTrackMissingParam, e:
            SIM_log_message(obj, 1, 0, Sim_Log_Error, str(e))
            SIM_log_message(obj, 1, 0, Sim_Log_Info,
                            "Disabling tracker until parameters are updated.")
            tracker.param_ok = False
            update(obj)
        except PTrackError, e:
            SIM_log_message(obj, 1, 0, Sim_Log_Error,
                            "Process tracking failed on %s. (%s)" %
                            (cpu.name, e))

class exception_syscall_catcher(syscall_catcher):
    def __init__(self, exception, exec_syscall_nums,
                 get_syscall_num, get_syscall_param):
        syscall_catcher.__init__(self, exec_syscall_nums,
                                 get_syscall_num, get_syscall_param)
        self.exception = exception
    def callback(self, obj, cpu, exception_number):
        self.syscall(obj, cpu)
    def install(self, tracker_obj, cpu):
        def get_remove(callback_id):
            def remove():
                SIM_hap_delete_callback_id(Core_Exception, callback_id)
            return remove
        exc_num = cpu.iface.exception.get_number(cpu, self.exception)
        callback_id = SIM_hap_add_callback_obj_index(Core_Exception, cpu, 0,
                                                     self.callback,
                                                     tracker_obj, exc_num)
        return get_remove(callback_id)

class address_syscall_catcher(syscall_catcher):
    def __init__(self, get_address, exec_syscall_nums,
                 get_syscall_num, get_syscall_param):
        syscall_catcher.__init__(self, exec_syscall_nums,
                                 get_syscall_num, get_syscall_param)
        self.get_address = get_address
    def callback(self, obj, mem_sp, breakpoint_id, memop):
        self.syscall(obj, memop.ini_ptr)
    def install(self, tracker_obj, cpu):
        def get_remove(callback_id, breakpoint_id):
            def remove():
                SIM_hap_delete_callback_id(Core_Breakpoint_Memop, callback_id)
                SIM_delete_breakpoint(breakpoint_id)
            return remove
        # We set a physical breakpoint to avoid having to set breakpoints in
        # all contexts that are created that could possibly be used with the
        # cpu.
        paddr = self.get_address(cpu)
        mem_sp = cpu.physical_memory
        breakpoint_id = SIM_breakpoint(
            mem_sp, Sim_Break_Physical, Sim_Access_Execute,
            paddr.addr, 1, Sim_Breakpoint_Private)
        callback_id = SIM_hap_add_callback_obj_index(
            Core_Breakpoint_Memop, mem_sp, 0,
            self.callback, tracker_obj, breakpoint_id)
        return get_remove(callback_id, breakpoint_id)

class processor_ops(object):
    def __init__(self):
        self.comm_size = 16
        self.exec_bin_size = 1000 # arbitrary
        self.max_tasks = 100000 # arbitrary
    def user_v2p(self, cpu, vaddr):
        vaddr.ensure_type(User)
        try:
            paddr = SIM_logical_to_physical(cpu, Sim_DI_Data, vaddr.addr)
            return Address(paddr, Physical)
        except:
            raise PTrackError("%s could not translate %s to physical"
                              % (cpu.name, vaddr))
    def v2p(self, cpu, vaddr):
        if vaddr.type == Kernel:
            return self.kernel_v2p(cpu, vaddr)
        else:
            return self.user_v2p(cpu, vaddr)
    def read_register(self, cpu, reg):
        try:
            return SIM_read_register(
                cpu, SIM_get_register_number(cpu, reg))
        except:
            raise PTrackError("Could not read register %s of %s"
                              % (reg, cpu.name))
    def read_virt_value(self, cpu, vaddr, len):
        return self.read_phys_value(cpu, self.v2p(cpu, vaddr), len)
    def read_ptr(self, cpu, vaddr, type):
        """Read a pointer and make sure it contains a valid address."""
        ptr = self.read_virt_value(cpu, vaddr, self.pointer_size)
        if type == Kernel:
            ensure(self.is_kernel_virtual(ptr))
        return Address(ptr, type)
    def read_string(self, cpu, vaddr, maxlen):
        """Read a null-terminated string of at most len bytes
        (including the terminator)."""
        s = ""
        for i in range(maxlen):
            c = self.read_virt_value(cpu, vaddr + i, 1)
            if c == 0:
                return s
            s += "%c" % c
        raise PTrackError("String too long.")
    def read_partial_string(self, cpu, vaddr, maxlen):
        """Read a null-terminated string from memory. The second part
        of the tuple is true if the entire string was read, false
        otherwise."""
        s = ""
        for i in range(maxlen):
            try:
                c = self.read_virt_value(cpu, vaddr + i, 1)
            except PTrackError:
                return (s, False)
            if c == 0:
                return (s, True)
            s += "%c" % c
        raise PTrackError("String too long.")
    def ensure_required_param(self, param, required):
        missing = (required | self.required_param) - set(param.iterkeys())
        if len(missing) > 0:
            raise PTrackMissingParam(missing)
    def get_current_pid(self, cpu, param):
        self.ensure_required_param(param, set(["ts_pid"]))
        task_struct = self.get_current_task(cpu, param)
        return self.read_virt_value(
            cpu, task_struct + param["ts_pid"], self.pid_size)
    def get_current_tid(self, cpu, param, mode = None):
        if mode == None:
            mode = self.cpu_mode(cpu)
        if mode == Sim_CPU_Mode_User:
            return self.get_current_pid(cpu, param)
        else:
            return kernel_tid

class big_endian_ops(processor_ops):
    def __init__(self):
        processor_ops.__init__(self)
    def read_phys_value(self, cpu, paddr, len):
        paddr.ensure_type(Physical)
        val = 0L
        for i in range(len):
            try:
                val = (val << 8) | SIM_read_phys_memory(
                    cpu, paddr.addr + i, 1)
            except:
                raise PTrackError("%s could not read byte at %s"
                                  % (cpu.name, paddr + i))
        return val

class little_endian_ops(processor_ops):
    def __init__(self):
        processor_ops.__init__(self)
    def read_phys_value(self, cpu, paddr, len):
        paddr.ensure_type(Physical)
        val = 0L
        for i in reversed(range(len)):
            try:
                val = (val << 8) | SIM_read_phys_memory(
                    cpu, paddr.addr + i, 1)
            except:
                raise PTrackError("%s could not read byte at %s"
                                  % (cpu.name, paddr + i))
        return val

class cpu32bit_ops:
    def __init__(self):
        self.pointer_size = 4
        self.pid_size = 4
        self.long_size = 4
    def kernel_v2p(self, cpu, vaddr):
        vaddr.ensure_type(Kernel)
        return Address(vaddr.addr & 0x0fffffffL, Physical)
    def is_kernel_virtual(self, addr):
        return (addr & 0xf0000000L) == 0xc0000000L

class ppc_ops(big_endian_ops):
    def __init__(self):
        big_endian_ops.__init__(self)
        self.syscall_catchers = [
            exception_syscall_catcher("System_call", [11],
                                      self.get_syscall_num,
                                      self.get_syscall_param)]
    def cpu_mode(self, cpu):
        if SIM_processor_privilege_level(cpu) == 0:
            return Sim_CPU_Mode_User
        else:
            return Sim_CPU_Mode_Supervisor
    def get_syscall_num(self, cpu):
        return self.read_register(cpu, "r0")
    def get_syscall_param(self, cpu):
        return self.read_register(cpu, "r3")

class ppc32_ops(ppc_ops, cpu32bit_ops):
    def __init__(self):
        ppc_ops.__init__(self)
        cpu32bit_ops.__init__(self)
        self.required_param = set(["ts_thread_struct"])
    def get_current_task(self, cpu, param):
        self.ensure_required_param(param, set(["ts_thread_struct"]))
        thread = Address(self.read_register(cpu, "sprg3") | 0xc0000000L,
                         Kernel)
        return thread - param["ts_thread_struct"]
    def bootstrap_autodetect(self, cpu):
        params = []
        for tsoffs in range(0x0, 0x280, self.pointer_size):
            params.append({"ts_thread_struct": tsoffs})
        return params

class ppc64_ops(ppc_ops):
    def __init__(self):
        ppc_ops.__init__(self)
        self.pointer_size = 8
        self.pid_size = 4
        self.long_size = 8
        self.required_param = set(["paca_task_struct"])
    def kernel_v2p(self, cpu, vaddr):
        vaddr.ensure_type(Kernel)
        return self.user_v2p(cpu, Address(vaddr.addr, User))
    def is_kernel_virtual(self, addr):
        return (addr & 0xf000000000000000L) != 0
    def get_current_task(self, cpu, param):
        self.ensure_required_param(param, set(["paca_task_struct"]))
        paca = Address(self.read_register(cpu, "sprg3"), Kernel)
        return self.read_ptr(cpu, paca + param["paca_task_struct"], Kernel)
    def bootstrap_autodetect(self, cpu):
        params = []
        for paca_ts in range(0x0, 0x100, self.pointer_size):
            params.append({"paca_task_struct": paca_ts})
        return params

class sparc64_64_ops(big_endian_ops):
    def __init__(self):
        big_endian_ops.__init__(self)
        self.pointer_size = 8
        self.pid_size = 4
        self.long_size = 8
        # TODO: for 64-bit binaries Linux uses Trap_Instruction_109
        self.syscall_catchers = [
            exception_syscall_catcher("Trap_Instruction_16", [11, 59],
                                      self.get_syscall_num,
                                      self.get_syscall_param)]
        self.required_param = set(["ts_indirect"])
    def user_v2p(self, cpu, vaddr):
        vaddr.ensure_type(User)
        try:
            # when kernel runs as primary, the user context is typically
            # available as secondary
            if cpu.mmu.ctxt_primary == 0:
                asi = 0x81 # ASI_SECONDARY
            else:
                asi = 0x80 # ASI_PRIMARY
            (pa, _) = cpu.mmu.d_translation[[vaddr.addr, asi]]
            return Address(pa, Physical)
        except:
            raise PTrackError("%s could not translate %s to physical"
                              % (cpu.name, vaddr))
    def kernel_v2p(self, cpu, vaddr):
        vaddr.ensure_type(Kernel)
        try:
            # Since SPARC has software table walks use the address-mask hack
            # when possible. For low addresses it is not needed since those
            # mappings are locked in the TLB.
            if vaddr.addr & 0xfffff80000000000:
                pa = vaddr.addr & 0x7ffffffffff
            else: # 4 = ASI_NUCLEUS
                (pa, _) = cpu.mmu.d_translation[[vaddr.addr, 4]]
        except Exception, msg:
            raise PTrackError("%s could not translate %s to physical"
                              % (cpu.name, vaddr))
        return Address(pa, Physical)
    def is_kernel_virtual(self, addr):
        return True
    def get_current_task(self, cpu, param):
        # Linux has a pointer to the current task in %g6 when in kernel mode.
        # We can typically find it in the %g6 alternate register.
        g6 = conf.cpu0.iface.sparc_v9.read_global_register(cpu, 1, 6)
        value = Address(g6, Kernel)
        if param['ts_indirect']:
            value = self.read_ptr(cpu, value, Kernel)
        return value
    def cpu_mode(self, cpu):
        if SIM_processor_privilege_level(cpu) == 0:
            return Sim_CPU_Mode_User
        else:
            return Sim_CPU_Mode_Supervisor
    def bootstrap_autodetect(self, cpu):
        return [{"ts_indirect": 0} , {"ts_indirect": 1}]
    def get_syscall_num(self, cpu):
        return self.read_register(cpu, "g1")
    def get_syscall_param(self, cpu):
        return self.read_register(cpu, "o0")

class x86_ops(little_endian_ops, cpu32bit_ops):
    def __init__(self):
        little_endian_ops.__init__(self)
        cpu32bit_ops.__init__(self)
        self.syscall_catchers = [
            exception_syscall_catcher("Software_Interrupt_128", [11],
                                      self.get_syscall_num,
                                      self.get_syscall_param)]
        self.required_param = set(["kernel_stack_size", "ts_indirect"])
    def cpu_mode(self, cpu):
        if SIM_processor_privilege_level(cpu) == 3:
            return Sim_CPU_Mode_User
        else:
            return Sim_CPU_Mode_Supervisor
    def get_current_task(self, cpu, param):
        self.ensure_required_param(param, set(["kernel_stack_size"]))
        if self.cpu_mode(cpu) == Sim_CPU_Mode_User:
            # The kernel stack pointer is stored at offset 4 from the base
            # of the tr segment.
            (tr_selector, tr_d, tr_dpl, tr_g, tr_p, tr_s, tr_type,
             tr_base, tr_limit, tr_valid) = cpu.tr
            esp = self.read_virt_value(cpu, Address(tr_base, Kernel) + 4,
                                       self.pointer_size)
        else:
            esp = self.read_register(cpu, "esp")

        # Pointer to current task_struct is at the bottom of the stack
        # area.
        ptr = Address((esp - 1) & ~(param["kernel_stack_size"] - 1), Kernel)
        if param["ts_indirect"]:
            ptr = self.read_ptr(cpu, ptr, Kernel)
        return ptr
    def get_syscall_num(self, cpu):
        return self.read_register(cpu, "eax")
    def get_syscall_param(self, cpu):
        return self.read_register(cpu, "ebx")
    def bootstrap_autodetect(self, cpu):
        params = []
        for stack in (4096, 8192):
            for indir in (0, 1):
                param = {"kernel_stack_size": stack, "ts_indirect": indir}
                params.append(param)
        return params

class x86_64_ops(little_endian_ops):
    def __init__(self):
        little_endian_ops.__init__(self)
        self.pointer_size = 8
        self.pid_size = 4
        self.long_size = 8
        self.syscall_catchers = [
            address_syscall_catcher(self.get_syscall_address, [59],
                                    self.get_syscall_num_64,
                                    self.get_syscall_param_64),
            exception_syscall_catcher("Software_Interrupt_128", [11],
                                      self.get_syscall_num_32,
                                      self.get_syscall_param_32)]
        self.required_param = set(["pda_task_struct"])
    def kernel_v2p(self, cpu, vaddr):
        vaddr.ensure_type(Kernel)
        # Addresses larger than 64 bits can by generated during parameter
        # auto-detection. They can't be wrapped for the linear_to_physical()
        # call so we raise an error here instead.
        if vaddr.addr > 0xffffffffffffffff:
            raise PTrackError("Address larger than 64 bits.")
        try:
            paddr = cpu.iface.x86.linear_to_physical(
                conf.cpu0, Sim_DI_Data, vaddr.addr)
            return Address(paddr, Physical)
        except:
            raise PTrackError("%s could not translate %s to physical"
                              % (cpu.name, vaddr))
    def is_kernel_virtual(self, addr):
        return addr >= 0x10000000000
    def cpu_mode(self, cpu):
        if SIM_processor_privilege_level(cpu) == 3:
            return Sim_CPU_Mode_User
        else:
            return Sim_CPU_Mode_Supervisor
    def get_current_task(self, cpu, param):
        # When executing in the kernel the gs segment base points to the PDA, a
        # per-processor data structure. When running user code the gs segment
        # base is zero, and the pointer to the PDA can be found in the "kernel
        # gs base" MSR. A pointer to the task struct can be found near the top
        # of the PDA.
        (gs_selector, gs_d, gs_dpl, gs_g, gs_p, gs_s, gs_type,
         gs_base, gs_limit, gs_valid, gs_l) = cpu.gs
        if gs_base != 0:
            pda = gs_base
        else:
            pda = cpu.kernel_gs_base
        ptr = Address(pda + param["pda_task_struct"], Kernel)
        return self.read_ptr(cpu, ptr, Kernel)
    def get_syscall_address(self, cpu):
        return self.v2p(cpu, Address(cpu.lstar, Kernel))
    def get_syscall_num_32(self, cpu):
        return self.read_register(cpu, "eax")
    def get_syscall_param_32(self, cpu):
        return self.read_register(cpu, "ebx")
    def get_syscall_num_64(self, cpu):
        return self.read_register(cpu, "rax")
    def get_syscall_param_64(self, cpu):
        return self.read_register(cpu, "rdi")
    def bootstrap_autodetect(self, cpu):
        params = []
        for pda_ts in range(0x0, 0x30, self.pointer_size):
            params.append({"pda_task_struct": pda_ts})
        return params


######################################################################
# Supported processor types.
######################################################################

processor_table = {
    "ppc32": (ppc32_ops(), ["ppc750", "ppc440gp"]),
    "ppc64": (ppc64_ops(), ["ppc970fx", "ppc-power6"]),
    "x86":   (x86_ops(),   ["x86-p2", "x86-p4"]),
    "x86-64": (x86_64_ops(), ["x86-hammer"]),
    "sparc-v9" : (sparc64_64_ops(), ["ultrasparc-ii"]),
    }
supported_processors = dict(((p, ps) for (p, (ops, ps))
                             in processor_table.iteritems()))
processor_ops = dict(((p, ops) for (p, (ops, ps))
                      in processor_table.iteritems()))
all_cpus = fold(lambda x, y: x + y, [], supported_processors.itervalues())
cpu_type = dict(((c, t) for (t, cs) in supported_processors.iteritems()
                 for c in cs))

def get_ops(cpu):
    return processor_ops[cpu_type[cpu.classname]]

def supports_processor(classname):
    return (classname in all_cpus)

def supports_cpu(obj, cpu):
    if supports_processor(cpu.classname):
        return True
    SIM_log_message(
        obj, 1, 0, Sim_Log_Error,
        ("%s is of class %s, which is not supported."
         % (cpu.name, cpu.classname)))
    return False

def same_type_cpus(cpus, log):
    cputypes = {}
    for cpu in cpus:
        t = cpu_type[cpu.classname]
        cputypes[t] = cputypes.get(t, []) + [cpu.classname]
    if len(cputypes) <= 1:
        return True
    if log:
        SIM_log_message(
            obj, 1, 0, Sim_Log_Error,
            ("Not all processors have the same type. (%s)"
             % ", ".join(["%s: %s" % (t, ", ".join([c.name for c in cs]))
                          for (t, cs) in cputypes.iteritems()])))
    return False

######################################################################
# Task struct enumeration.
######################################################################

# Return a list of all task structs. Fail if there's something wrong.
def get_task_structs(cpu_ops, cpu, param):
    check_task_struct_offset_order(param)
    cpu_ops.ensure_required_param(
        param, set(["ts_next", "ts_prev", "ts_next_relative"]))
    pid_to_ts = {}
    def get_ts(addr):
        p = cpu_ops.read_ptr(cpu, addr, Kernel)
        if param["ts_next_relative"]:
            return p - param["ts_next"]
        else:
            return p
    def read_pid(task):
        if "ts_pid" in param:
            pid = cpu_ops.read_virt_value(cpu, task + param["ts_pid"],
                                          cpu_ops.pid_size)
            ensure(pid < 32768)
            ensure(not pid in pid_to_ts)
            pid_to_ts[pid] = task
            task_structs[task]["pid"] = pid
    def read_comm(task):
        if "ts_comm" in param:
            comm = cpu_ops.read_string(cpu, task + param["ts_comm"],
                                       cpu_ops.comm_size)
            ensure(len(comm) > 0)
            for c in comm:
                ensure(ord(c) >= 32 and ord(c) <= 126)
            task_structs[task]["comm"] = comm
    def read_state(task):
        if "ts_state" in param:
            state = cpu_ops.read_virt_value(cpu, task + param["ts_state"],
                                            cpu_ops.long_size)
            sign_bit = (1 << (8*cpu_ops.long_size))
            if state == 0:
                task_structs[task]["state"] = "runnable"
            elif state & sign_bit == 0:
                task_structs[task]["state"] = "stopped"
            else:
                task_structs[task]["state"] = "unrunnable"

    # Initialize current_task.
    first_task = cpu_ops.get_current_task(cpu, param)
    current_task = first_task
    current_next = get_ts(current_task + param["ts_next"])
    current_prev = get_ts(current_task + param["ts_prev"])
    task_structs = {current_task: {"next": current_next, "prev": current_prev}}
    read_pid(current_task)
    read_comm(current_task)
    read_state(current_task)

    # Iterate over other tasks.
    while True:
        # Get next task struct.
        next_task = current_next
        next_next = get_ts(next_task + param["ts_next"])
        next_prev = get_ts(next_task + param["ts_prev"])

        # Make sure there is a backlink.
        ensure(next_prev == current_task)

        # If next is first, we're done.
        if next_task == first_task:
            break

        # Make sure we haven't seen this address before.
        ensure(not next_task in task_structs)

        # Insert in map. Fail if map grows too large.
        task_structs[next_task] = {"next": next_next, "prev": next_prev}
        ensure(len(task_structs) < cpu_ops.max_tasks)

        # Read optional stuff.
        read_pid(next_task)
        read_comm(next_task)
        read_state(next_task)

        # Next is new current.
        current_task = next_task
        current_next = next_next
        current_prev = next_prev

    # With less than, say, 5 processes, the result is too uncertain.
    ensure(len(task_structs) >= 5)
    return task_structs

# Print a process list.
def print_process_list(cpu_ops, cpu, param, tsaddr):
    cpu_ops.ensure_required_param(
        param, set(["ts_pid", "ts_state", "ts_comm"]))
    if tsaddr:
        fmt = "  %5s  %20s  %10s  %s"
        print fmt % ("pid", "task_struct", "state", "comm")
    else:
        fmt = "  %5s  %10s  %s"
        print fmt % ("pid", "state", "comm")
    print "-"*70
    tasks = [(task["pid"], task["state"], task["comm"], addr)
             for addr, task
             in get_task_structs(cpu_ops, cpu, param).iteritems()]
    for (pid, state, comm, addr) in sorted(tasks):
        if tsaddr:
            print fmt % ("%d" % pid, addr, state, comm)
        else:
            print fmt % ("%d" % pid, state, comm)

######################################################################
# Parameter autodetection.
######################################################################

# Make sure that the fields of the task_struct are in the correct order.
correct_order = ["ts_state", "ts_next", "ts_prev", "ts_pid",
                 "ts_comm", "ts_thread_struct"]
def check_task_struct_offset_order(param):
    cord = [x for x in correct_order if x in param]
    for i in range(len(cord) - 1):
        try:
            first = param[cord[i]]
            second = param[cord[i + 1]]
            ensure(first < second)
        except KeyError:
            pass

# Given a list of working parameters and a list of candidates for new
# parameters, try all combinations and return a new list of working
# parameters.
def find_param_candidates(cpu_ops, cpu, params, candidates):
    good = []
    for param in params:
        for cand in candidates:
            p = param.copy()
            p.update(cand)
            try:
                get_task_structs(cpu_ops, cpu, p)
                good.append(p)
            except PTrackError:
                pass
    return good

# Weed out all parameter sets except those where par has the smallest
# value.
def find_lowest_param_candidate(params, par):
    if len(params) == 0:
        return []
    min_par = min([param[par] for param in params])
    return [param for param in params if param[par] == min_par]

# Weed out all parameter sets except those with the highest score.
def find_best_param_candidate(cpu_ops, cpu, params, fun):
    if len(params) == 0:
        return []
    score = []
    for param in params:
        score.append([fun(cpu_ops, cpu, param), param])
    score.sort()
    best_score, best_param = score[-1]
    return [param for s, param in score if s == best_score]

# Compute score that is the average length of comm strings.
def comm_length_score(cpu_ops, cpu, param):
    total_length = 0
    task_structs = get_task_structs(cpu_ops, cpu, param)
    for addr, ts in task_structs.iteritems():
        total_length += len(ts["comm"])
    return float(total_length)/len(task_structs)

# Find offsets of "next" and "prev" pointers in task_struct.
def find_next_prev_offs(cpu_ops, cpu, params):
    candidates = [{"ts_next": next_offs,
                   "ts_prev": next_offs + cpu_ops.pointer_size,
                   "ts_next_relative": rel}
                  for next_offs in range(0x0, 0x100, cpu_ops.pointer_size)
                  for rel in (0, 1)]
    return find_param_candidates(cpu_ops, cpu, params, candidates)

# Find offset of "pid" field in task_struct.
def find_pid_offs(cpu_ops, cpu, params):
    candidates = [{"ts_pid": pid}
                  for pid in range(0x0, 0x500, cpu_ops.pid_size)]
    return find_param_candidates(cpu_ops, cpu, params, candidates)

# Find offset of "comm" field in task_struct.
def find_comm_offs(cpu_ops, cpu, params):
    candidates = [{"ts_comm": comm} for comm in range(0x0, 0x1000)]
    return find_param_candidates(cpu_ops, cpu, params, candidates)

# Find offset of "state" field in task_struct.
def find_state_offs(params):
    for param in params:
        param["ts_state"] = 0
    return params

# Find all parameter sets.
def find_all_params(obj, cpu_ops, cpu):
    def assert_not_empty(params, pas):
        if len(params) == 0:
            raise PTrackAutodetectFail("failed to find %s" % pas)
    try:
        params = cpu_ops.bootstrap_autodetect(cpu)
        assert_not_empty(params, "first task")

        params = find_next_prev_offs(cpu_ops, cpu, params)
        assert_not_empty(params, "list pointers")
        params = find_pid_offs(cpu_ops, cpu, params)
        assert_not_empty(params, "pid offset")
        params = find_comm_offs(cpu_ops, cpu, params)
        assert_not_empty(params, "comm offset")
        params = find_state_offs(params)
        assert_not_empty(params, "state offset")

        params = find_lowest_param_candidate(params, "ts_pid")
        assert_not_empty(params, "lowest pid offset")
        params = find_best_param_candidate(cpu_ops, cpu, params,
                                           comm_length_score)
        assert_not_empty(params, "best comm offset")

        if len(params) == 1:
            return params[0]
        else:
            raise PTrackAutodetectFail("found %d possible parameter sets"
                                       % len(params))
    except PTrackAutodetectFail, e:
        SIM_log_message(
            obj, 3, 0, Sim_Log_Error, "Autodetection failure: %s" % e)
        raise PTrackAutodetectFail(
            "Failed to autodetect parameters. Make sure that the target"
            " OS is booted.")
    except PTrackError, e:
        raise PTrackAutodetectFail(
            "Error while autodetecting process tracker parameters: %s" % e)

######################################################################
# State for tracking exec() syscalls.
######################################################################

# Sometimes the program string can't be read immediately; in that case
# we set a breakpoint on the string and wait until the OS tries to
# read it. Repeat until success.

class exec_state:
    def __init__(self, obj, cpu, pid, address, partial_string = ""):
        self.obj = obj
        self.cpu = cpu
        self.pid = pid
        self.address = address
        self.partial_string = partial_string
        self.active = False
        self.hap_handle = None
        self.breakpoint = None
    def __nonzero__(self):
        return self.active
    def try_to_trigger(self):
        tracker = self.obj.object_data
        s, all = tracker.cpu_ops.read_partial_string(
            self.cpu, self.address, tracker.cpu_ops.exec_bin_size)
        self.partial_string += s
        self.address += len(s)
        if all:
            self.active = False
            self.update()
            SIM_log_message(self.obj, 3, 0, Sim_Log_Info,
                            ("process %d on %s executed '%s'"
                             % (self.pid, self.cpu.name,
                                self.partial_string)))
            try:
                SIM_hap_occurred_always(Core_Trackee_Exec, self.obj,
                                        self.pid, [self.pid, self.cpu,
                                                   self.partial_string])
            except:
                pass
        return all
    def callback(self, dummy, mem, bp, memop):
        self.try_to_trigger()
    def update(self, active = None):
        tracker = self.obj.object_data
        if active != None:
            self.active = bool(active)

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
                Sim_Access_Read, self.address.addr,
                tracker.cpu_ops.exec_bin_size, Sim_Breakpoint_Simulation)
            self.hap_handle = SIM_hap_add_callback_index(
                Core_Breakpoint_Memop, self.callback, None, self.breakpoint)

######################################################################
# Process tracker object.
######################################################################

class tracker_instance:
    # Instance constructor
    def __init__(self, obj):
        obj.object_data = self
        self.obj = obj
        self.processors = {}
        self.param = {}
        self.param_ok = False
        self.cpu_ops = None
        self.cleanup_funs = []
        self.current_tid = {}
        self.num_users = 0
    def cputype(self):
        for cpu in self.processors.iterkeys():
            return cpu_type[cpu.classname]
        return None

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

Process tracker for Linux. Works on ppc32, ppc64, UltraSPARC and
x86 targets."""

SIM_register_class(class_name, class_data)

# Hap handler for the Core_Mode_Change hap triggered by processors
# when they change privilege level.
def mode_change_hap(obj, cpu, old_mode, new_mode):
    try:
        tracker = obj.object_data
        old_tid = tracker.current_tid[cpu]
        new_tid = tracker.cpu_ops.get_current_tid(cpu, tracker.param, new_mode)
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
    except PTrackMissingParam, e:
        SIM_log_message(obj, 1, 0, Sim_Log_Error, str(e))
        SIM_log_message(obj, 1, 0, Sim_Log_Info,
                        "Disabling tracker until parameters are updated.")
        tracker.param_ok = False
        update(obj)
    except PTrackError, e:
        SIM_log_message(obj, 1, 0, Sim_Log_Error,
                        "Process tracking failed on %s. (%s)" % (cpu.name, e))

# Make sure everything is up-to-date when some attribute has changed.
def update(obj):
    tracker = obj.object_data
    for fun in tracker.cleanup_funs:
        fun()
    tracker.cleanup_funs = []
    tracker.current_tid = {}
    if len(tracker.processors) == 0:
        tracker.cpu_ops = None
    else:
        tracker.cpu_ops = get_ops(anykey(tracker.processors))
    for cpu, exec_state in tracker.processors.iteritems():
        # Record current tid.
        try:
            if tracker.param_ok:
                tracker.current_tid[cpu] = tracker.cpu_ops.get_current_tid(
                    cpu, tracker.param)
            else:
                tracker.current_tid[cpu] = kernel_tid
        except PTrackMissingParam, e:
            SIM_log_message(obj, 1, 0, Sim_Log_Error, str(e))
            SIM_log_message(obj, 1, 0, Sim_Log_Info,
                            "Disabling tracker until parameters are updated.")
            tracker.param_ok = False
            update(obj)
        except PTrackError, e:
            SIM_log_message(obj, 1, 0, Sim_Log_Error,
                            "Process tracking failed on %s. (%s)"
                            % (cpu.name, e))
            tracker.current_tid[cpu] = kernel_tid
        if tracker.num_users > 0 and tracker.param_ok:
            # Listen for mode change hap.
            def get_remove(callback_id):
                def remove():
                    SIM_hap_delete_callback_id(Core_Mode_Change, callback_id)
                return remove
            callback_id = SIM_hap_add_callback_obj(
                Core_Mode_Change, cpu, 0, mode_change_hap, obj)
            tracker.cleanup_funs.append(get_remove(callback_id))
            # Watch for system calls.
            try:
                for catcher in tracker.cpu_ops.syscall_catchers:
                    tracker.cleanup_funs.append(catcher.install(obj, cpu))
            except:
                SIM_log_message(obj, 1, 0, Sim_Log_Error,
                                "Process tracking failed on %s." % cpu.name)
        # Update exec state.
        if exec_state:
            if not tracker.num_users > 0:
                exec_state.active = False
            exec_state.update()

######################################################################
# Simics object attributes.
######################################################################

def attr_processors():
    def getter(arg, obj, idx):
        return list(obj.object_data.processors.keys())
    def setter(arg, obj, val, idx):
        old_processors = dict(obj.object_data.processors)
        new_processors = set(val)
        for cpu in new_processors:
            if not supports_cpu(obj, cpu):
                return Sim_Set_Illegal_Value
        if not same_type_cpus(new_processors, log = True):
            return Sim_Set_Illegal_Value
        for cpu, exec_state in old_processors.iteritems():
            if not cpu in new_processors:
                if exec_state:
                    exec_state.update(active = False)
                del obj.object_data.processors[cpu]
        for cpu in new_processors:
            if not cpu in old_processors:
                obj.object_data.processors[cpu] = None
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "processors", getter, None, setter, None,
        Sim_Attr_Session, "[o*]", None,
        "Processors whose modes are being tracked.")
attr_processors()

def attr_per_cpu_state():
    def getter(arg, obj, idx):
        def getattr(cpu, exec_state):
            if exec_state:
                attr = [exec_state.pid, exec_state.address.addr(),
                        exec_state.partial_string]
            else:
                attr = []
            return [cpu, attr]
        return [getattr(cpu, exec_state) for cpu, exec_state
                in obj.object_data.processors.iteritems()]
    def setter(arg, obj, val, idx):
        def setattr(dict, cpu, attr):
            if cpu in dict:
                try:
                    pid, addr, pstr = attr
                    dict[cpu] = exec_state(obj, cpu, pid,
                                           Address(addr, User), pstr)
                    dict[cpu].active = True
                except ValueError:
                    dict[cpu] = None
        tracker = obj.object_data
        for cpu, exec_state in tracker.processors.iteritems():
            if exec_state:
                exec_state.update(active = False)
        for cpu, attr in val:
            setattr(tracker.processors, cpu, attr)
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "per_cpu_state", getter, None, setter, None,
        Sim_Attr_Optional, "[[o[a*]]*]", None,

        """Per-processor state that has to be maintained by the
        process tracker.""")

attr_per_cpu_state()

def attr_param():
    def getter(arg, obj, idx):
        tracker = obj.object_data
        if idx == None:
            return [[key, val] for (key, val) in tracker.param.iteritems()]
        else:
            return tracker.param[idx]
    def setter(arg, obj, val, idx):
        tracker = obj.object_data
        if idx == None:
            tracker.param = dict(val)
        else:
            tracker.param[idx] = val
        tracker.param_ok = True
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "param", getter, None, setter, None,
        Sim_Attr_Session | Sim_Attr_String_Indexed, "[[s,i]*]", "i",

        """Linux version dependent parameters, such as
        <tt>task_struct</tt> offsets. The easiest way to set these are
        to give the <arg>kernel</arg> argument to
        <cmd>new-linux-process-tracker</cmd>, or to run the
        <cmd>autodetect-parameters</cmd> command.

        Parameters starting with <tt>ts_</tt> are offsets in the
        <tt>task_struct</tt>. <b><tt>ts_comm</tt></b> is the offset of
        the <tt>comm</tt> field, which contains the name of the
        process. <b><tt>ts_pid</tt></b> and <b><tt>ts_state</tt></b>
        are the offsets of the fields that contain the process's pid
        and state. <b><tt>ts_thread_struct</tt></b> is the offset of
        the <tt>thread_struct</tt> embedded in the
        <tt>task_struct</tt>.

        <b><tt>ts_next</tt></b> and <b><tt>ts_prev</tt></b> are the
        offsets of the pointers that connect all the task structs in a
        circular double-linked list. <b><tt>ts_next_relative</tt></b>
        is non-zero if these pointers point at the <tt>next</tt> field
        of other <tt>task_struct</tt>s, and zero if they point to the
        first byte.

        <b><tt>kernel_stack_size</tt></b> is the size, in bytes, of a
        kernel stack; this is either 4096 or 8192.
        <b><tt>paca_task_struct</tt></b> is the offset in the
        <tt>paca</tt> struct of the pointer to the current
        <tt>task_struct</tt>.

        Not all of these parameters are necessary for any given
        simulated machine.""")

attr_param()

######################################################################
# Simics interfaces.
######################################################################

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
        tracker = obj.object_data
        if (not cpu in tracker.processors
            and supports_cpu(obj, cpu)
            and same_type_cpus(set(tracker.processors.keys() + [cpu]),
                               log = True)):
            tracker.processors[cpu] = None
            update(obj)
    def remove_processor(obj, cpu):
        tracker = obj.object_data
        p = tracker.processors
        if cpu in p:
            if p[cpu]:
                p[cpu].update(active = False)
            del p[cpu]
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
        "ppc32-linux-2.4.17": ("ppc32 Linux 2.4.17",
                               { "ts_comm": 582,
                                 "ts_next": 72,
                                 "ts_next_relative": 0,
                                 "ts_pid": 128,
                                 "ts_prev": 76,
                                 "ts_state": 0,
                                 "ts_thread_struct": 624,
                                 }),
        "ppc32-linux-2.4.31": ("ppc32 Linux 2.4.31",
                               { "ts_comm": 574,
                                 "ts_next": 72,
                                 "ts_next_relative": 0,
                                 "ts_pid": 124,
                                 "ts_prev": 76,
                                 "ts_state": 0,
                                 "ts_thread_struct": 616,
                                 }),
        "ppc64-linux-2.6.6": ("ppc64 Linux 2.6.6",
                              { "paca_task_struct": 16,
                                "ts_comm": 1090,
                                "ts_next": 136,
                                "ts_next_relative": 1,
                                "ts_pid": 236,
                                "ts_prev": 144,
                                "ts_state": 0,
                                }),
        "sparc-v9-linux-2.6.13": ("sparc-v9 Linux 2.6.13",
                                  {"ts_comm": 724,
                                   "ts_indirect": 1,
                                   "ts_next": 152,
                                   "ts_next_relative": 1,
                                   "ts_pid": 260,
                                   "ts_prev": 160,
                                   "ts_state": 0,
                                   }),
        "sparc-v9-linux-2.4.14-SMP": ("sparc-v9 Linux 2.4.14-SMP",
                                      {"ts_comm": 1402,
                                       "ts_indirect": 0,
                                       "ts_next": 112,
                                       "ts_next_relative": 0,
                                       "ts_pid": 204,
                                       "ts_prev": 120,
                                       "ts_state": 0,
                                       }),
        "x86-linux-2.2.21": ("x86 Linux 2.2.21",
                             { "kernel_stack_size": 8192,
                               "ts_comm": 454,
                               "ts_indirect": 0,
                               "ts_next": 56,
                               "ts_next_relative": 0,
                               "ts_pid": 100,
                               "ts_prev": 60,
                               "ts_state": 0,
                               }),
        "x86-linux-2.4.18": ("x86 Linux 2.4.18",
                             { "kernel_stack_size": 8192,
                               "ts_comm": 570,
                               "ts_indirect": 0,
                               "ts_next": 76,
                               "ts_next_relative": 0,
                               "ts_pid": 116,
                               "ts_prev": 80,
                               "ts_state": 0,
                               }),
        "x86-linux-2.4.18-smp": ("x86 Linux 2.4.18 SMP",
                                 { "kernel_stack_size": 8192,
                                   "ts_comm": 818,
                                   "ts_indirect": 0,
                                   "ts_next": 76,
                                   "ts_next_relative": 0,
                                   "ts_pid": 116,
                                   "ts_prev": 80,
                                   "ts_state": 0,
                                   }),
        "x86-linux-2.6.15": ("x86 Linux 2.6.15 (UP/SMP)",
                             { "kernel_stack_size": 4096,
                               "ts_comm": 432,
                               "ts_indirect": 1,
                               "ts_next": 96,
                               "ts_next_relative": 1,
                               "ts_pid": 156,
                               "ts_prev": 100,
                               "ts_state": 0,
                               }),
        "x86-64-linux-2.4.19": ("x86-64 Linux 2.4.19 (SuSE 8.2)",
                                {"pda_task_struct": 0,
                                 "ts_comm": 946,
                                 "ts_next": 152,
                                 "ts_next_relative": 0,
                                 "ts_pid": 252,
                                 "ts_prev": 160,
                                 "ts_state": 0}),
        "x86-64-linux-2.6.15": ("x86-64 Linux 2.6.15 (UP/SMP)",
                                {"pda_task_struct": 0,
                                 "ts_comm": 768,
                                 "ts_next": 176,
                                 "ts_next_relative": 1,
                                 "ts_pid": 284,
                                 "ts_prev": 184,
                                 "ts_state": 0})}
    kernel_list = list(kernels.keys())
    def settings_id_list():
        return kernel_list
    def describe_settings(settings_id):
        try:
            name, param = kernels[settings_id]
            return name
        except KeyError:
            return ""
    def use_settings(obj, settings_id):
        try:
            name, param = kernels[settings_id]
            obj.param = [[key, val] for (key, val) in param.iteritems()]
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

######################################################################
# Command line interface.
######################################################################

from cli import *
import sim_commands

# status command prints dynamic information
def get_status(obj):
    tracker = obj.object_data
    return [(None,
             [("Processors", ", ".join([c.name for c
                                        in tracker.processors.iterkeys()])),
              ("Processor type", tracker.cputype())]),
            ("Process tracking parameters",
             sorted(((key, "%d" % value)
                     for (key, value) in tracker.param.iteritems())))]
sim_commands.new_status_command(class_name, get_status)

def cmd_process_list(obj, tsaddr):
    tracker = obj.object_data
    if len(tracker.processors) == 0:
        raise CliError("Cannot read process list without a processor.")
    cpu = anykey(tracker.processors)
    try:
        print_process_list(tracker.cpu_ops, cpu, tracker.param, tsaddr)
    except PTrackError, e:
        raise CliError(str(e))
new_command("process-list", cmd_process_list,
            [arg(flag_t, "-task-struct-address")],
            namespace = class_name,
            type = ["Debugging"],
            short = "list running processes",
            doc = """

Print a list of all running processes on the simulated system. If the
<tt>-task-struct-address</tt> flag is given, list the
<tt>task_struct</tt> address for each process.""")

def cmd_autodetect_parameters(obj):
    tracker = obj.object_data
    if len(tracker.processors) == 0:
        raise CliError("Cannot autodetect without a processor.")
    try:
        param = find_all_params(obj, tracker.cpu_ops,
                                anykey(tracker.processors))
        obj.param = [[key, val] for (key, val) in param.iteritems()]
    except PTrackAutodetectFail, e:
        raise CliError(str(e))
new_command("autodetect-parameters", cmd_autodetect_parameters, [],
            namespace = class_name,
            short = "autodetect parameters",
            doc = """

Autodetect the parameters to use in the <attr>param</attr> attribute.
For this to work, the process tracker must have at least one
processor, and Linux must be already running on the simulated machine.
(This means that if you want to use process tracking during the boot,
you must enter the parameters manually; but you can still get hold of
them in the first place by running
<cmd>autodetect-parameters</cmd>.)""")
