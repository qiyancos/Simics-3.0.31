# simple OpenPIC implementation in python

# MODULE: open-pic
# CLASS: open-pic

from sim_core import *

spacename = {
    Sim_Addr_Space_Memory : "Sim_Addr_Space_Memory",
    Sim_Addr_Space_IO     : "Sim_Addr_Space_IO",
    Sim_Addr_Space_Conf   : "Sim_Addr_Space_Conf",
}

def show_map_info(info):
    print "  info.base: 0x%x" % info.base
    print "  info.start: 0x%x" % info.start
    print "  info.length: 0x%x" % info.length
    print "  info.function:", info.function
    print "  info.reverse_endian:", info.reverse_endian

mop_types = {
    Sim_Trans_Load        : "Sim_Trans_Load",
    Sim_Trans_Store       : "Sim_Trans_Store",
    Sim_Trans_Instr_Fetch : "Sim_Trans_Instr_Fetch",
    Sim_Trans_Prefetch    : "Sim_Trans_Prefetch",
    Sim_Trans_Cache       : "Sim_Trans_Cache",
}

def show_mem_op(mop):
    print "  mop.type: %d (%s)" % (mop.type, mop_types[mop.type])
    print "  mop.physical_address: 0x%x" % mop.physical_address
    print "  mop.logical_address: 0x%x" % mop.logical_address
    print "  mop.size: 0x%x" % mop.size

class isu:
    def __init__(self):
        self.regs = [0x80000000L, 0]
    def vec_pri(self):
        return self.regs[0]
    def dest(self):
        return self.regs[1]

class pic_timer:
    def __init__(self):
        self.regs = [0, 0x80000000L, 0x80000000L, 0]
    def cur_count(self):
        return self.regs[0]
    def base_count(self):
        return self.regs[1]
    def vec_pri(self):
        return self.regs[2]
    def dest(self):
        return self.regs[3]

class per_cpu:
    def __init__(self, cpu_id):
        self.regs = [0, 0, 0, 0,
                     0, 0, 0, 0,
                     0xf,               # current task priority
                     cpu_id,            # who am I
                     0, 0]

# implementation parameters
max_isu = 31
max_cpu = 0

# container for per-instance state

openpic_instances = {}                  # indexed by conf object

class openpic_instance:
    def __init__(self, obj):
        global openpic_instances
        openpic_instances[obj] = self
        self.obj = obj

        # registers
        self.isus = [isu() for i in range(max_isu + 1)]
        self.timers = [pic_timer() for i in range(4)]
        self.ipi_vec_pri = [0x80000000L] * 4
        self.per_cpu_regs = [per_cpu(i) for i in range(max_cpu + 1)]
        self.spurious_vec = 0xff
        self.global_conf_reg = 0xf
        self.irq_devs = None

        self.active_isus = {}           # set of active ISUs
        # current interrupt source in progress for each cpu, or -1 if none
        self.in_progress = [0] * (max_cpu + 1)
        # (pri, src) of highest-pri pending sources for each cpu
        self.pending = [(0, 0)] * (max_cpu + 1)

        self.debug = 0

    def debug_pr(self, level, str):
        if self.debug >= level:
            print "[%d]openpic: %s" % (SIM_step_count(conf.cpu0), str)

    # signal start of interrupt processing for a cpu (acknowledge cycle)
    def start_processing(self, cpu):
        debug_str = "Interrupt acknowledge:"
        if self.pending[cpu][0]:
            src = self.pending[cpu][1]
            self.in_progress[cpu] = src
            vec = self.isus[src].vec_pri() & 0xff
            debug_str += "  use src %d" % src
        else:
            # no interrupt pending, use spurious vector
            vec = self.spurious_vec
            debug_str += "  none pending, use spurious"
        self.per_cpu_regs[cpu].regs[10] = vec
        debug_str += "  -- vector %d" % vec
        self.debug_pr(2, debug_str)

    # source N has raised an interrupt
    def activate_isu(self, src):
        isu = self.isus[src]
        self.active_isus[src] = 1
        vpr = isu.vec_pri()
        if vpr & 0x80000000:
            return                      # source masked
        pri = (vpr >> 16) & 0xf
        vec = vpr & 0xff
        # check sense/polarity here?
        dsts = isu.dest()
        for dst in range(max_cpu + 1):
            if  ((1 << dst) & dsts
                 and self.per_cpu_regs[dst].regs[0] < pri
                 and self.pending[dst][0] < pri):
                self.pending[dst] = (pri, src)
                self.activate_idu(dst)

    # issue an interrupt
    def activate_idu(self, dst):
        cpu = self.irq_devs[dst]
        # Assume that the destination does not auto-ack (we pass 0 here)
        self.debug_pr(2, "issuing interrupt to cpu")
        cpu.iface.simple_interrupt.interrupt(cpu, 0)

    def finish_interrupt(self, cpu):
        # finish interrupt, and see if any pending interrupts now will cause
        # another signal to the cpu
        old_src = self.in_progress[cpu]
        # Pretend that the ISU is no longer active (as if level triggered)
        del self.active_isus[old_src]
        self.pending[cpu] = (0, 0)
        mask = 1 << cpu
        for src in self.active_isus.keys():
            isu = self.isus[src]
            vpr = isu.vec_pri()
            pri = (vpr >> 16) & 0xf
            if  (isu.dest() & mask
                 and self.per_cpu_regs[cpu].regs[0] < pri
                 and self.pending[cpu][0] < pri):
                self.pending[cpu] = (pri, src)
        self.debug_pr(2, "finish interrupt")
        if self.pending[cpu][0]:
            self.debug_pr(2,
                          "  new pending is pri %d src %d"
                          % (self.pending[cpu][0], self.pending[cpu][1]))
            self.activate_idu(cpu)
        else:
            self.debug_pr(2, "  no pending interrupt, lowering output pin")
            cpuobj = self.irq_devs[cpu]
            cpuobj.iface.simple_interrupt.interrupt_clear(cpuobj, 0)

def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    openpic_instance(obj)
    return obj

def isu_operation(inst, addr, mop):
    type = mop.type
    size = mop.size
    if size != 4:
        print "size", size, "!= 4, not supported"
        return Sim_PE_No_Exception
    if (addr & 0xf) != 0:
        print "address", addr, "not register aligned"
        return Sim_PE_No_Exception
    isu = (addr & 0xffff) >> 5
    reg = (addr & 0x10) >> 4
    if isu > max_isu:
        print "Bad openpic register"
        return Sim_PE_No_Exception
    if type == Sim_Trans_Load:
        val = inst.isus[isu].regs[reg]
        SIM_set_mem_op_value_le(mop, val)
        inst.debug_pr(2, "load 0x%x from ISU %d reg %d" % (val, isu, reg))
    else:
        val = SIM_get_mem_op_value_le(mop)
        inst.isus[isu].regs[reg] = val
        inst.debug_pr(2, "store 0x%x to ISU %d reg %d" % (val, isu, reg))
    return Sim_PE_No_Exception

def global_operation(inst, addr, mop):
    type = mop.type
    size = mop.size
    if size != 4:
        print "size", size, "!= 4, not supported"
        return Sim_PE_No_Exception
    if (addr & 0xf) != 0:
        print "address", addr, "not register aligned"
        return Sim_PE_No_Exception
    if type == Sim_Trans_Load:
        if addr == 0x1000:              # Feature Reporting Register 0
            version = 2                 # openpic spec version 1.2
            val = max_isu << 16 | max_cpu << 8 | version
        elif addr == 0x1020:            # Global Configuration Register
            val = inst.global_conf_reg
        elif 0x10a0 <= addr <= 0x10d0:  # IPI vector/priority
            reg = (addr - 0x10a0) >> 4
            val = inst.ipi_vec_pri[reg]
        elif addr == 0x10e0:            # Spurious Vector Register
            val = inst.spurious_vec
        elif addr == 0x10f0:            # Timer Frequency Reporting Register
            # value matters little (not used by Linux)
            val = 100000000
        elif 0x1100 <= addr < 0x1200:   # global timers
            reg = (addr - 0x1100) >> 4
            val = inst.timers[reg >> 2].regs[reg & 3]
        else:
            print "Bad openpic register"
            return Sim_PE_No_Exception
        SIM_set_mem_op_value_le(mop, val)
        inst.debug_pr(2, "load 0x%x from reg 0x%x" % (val, addr))
    else:
        val = SIM_get_mem_op_value_le(mop)
        inst.debug_pr(2, "store 0x%x to reg 0x%x" % (val, addr))
        if addr == 0x1020:              # Global Configuration Register
            if val & 0x80000000:
                print "openpic reset not implemented"
                return Sim_PE_No_Exception
            inst.global_conf_reg = val
        elif 0x10a0 <= addr <= 0x10d0:  # IPI vector/priority
            reg = (addr - 0x10a0) >> 4
            inst.ipi_vec_pri[reg] = val
        elif addr == 0x10e0:            # Spurious Vector Register
            inst.spurious_vec = val
        elif 0x1100 <= addr < 0x1200:   # global timers
            reg = (addr - 0x1100) >> 4
            inst.timers[reg >> 2].regs[reg & 3] = val
            if (reg & 3) == 1 and not (val & 0x80000000):
                print "Turning on timers not supported"
                return Sim_PE_No_Exception
        else:
            print "Bad openpic register"
            return Sim_PE_No_Exception
    return Sim_PE_No_Exception

def per_cpu_operation(inst, addr, mop):
    type = mop.type
    size = mop.size
    if size != 4:
        print "size", size, "!= 4, not supported"
        return Sim_PE_No_Exception
    if (addr & 0xf) != 0:
        print "address", addr, "not register aligned"
        return Sim_PE_No_Exception
    if addr & 0x1f000:
        cpu = (addr >> 3) & 0x1f
    else:
        cpu = 0                         # FIXME: should be "this cpu"
    reg = (addr & 0xfff) >> 4
    if reg >= 0xc:
        print "Bad openpic register"
        return Sim_PE_No_Exception
    if type == Sim_Trans_Load:
        if reg == 10:                   # Interrupt Acknowledge Register
            inst.start_processing(cpu)
        val = inst.per_cpu_regs[cpu].regs[reg]
        SIM_set_mem_op_value_le(mop, val)
        inst.debug_pr(2, "load 0x%x from per-CPU reg 0x%x" % (val, addr))
    else:
        val = SIM_get_mem_op_value_le(mop)
        inst.debug_pr(2, "store 0x%x to per-CPU reg 0x%x" % (val, addr))
        inst.per_cpu_regs[cpu].regs[reg] = val
        if 4 <= reg <= 7:
            print "Write to IPI command port, not yet implemented"
            return Sim_PE_No_Exception
        elif reg == 11:                 # EOI Register
            inst.finish_interrupt(cpu)
    return Sim_PE_No_Exception

def openpic_map(obj, memory_or_io, info):
    return 0

def openpic_operation(obj, mop, info):
    addr = mop.physical_address - info.base
    try:
        inst = openpic_instances[obj]
        if addr < 0x1000:
            ret = per_cpu_operation(inst, addr, mop)
        elif 0x1000 <= addr < 0x10000:
            ret = global_operation(inst, addr, mop)
        elif 0x10000 <= addr < 0x20000:
            ret = isu_operation(inst, addr, mop)
        elif 0x20000 <= addr < 0x40000:
            ret = per_cpu_operation(inst, addr, mop)
        else:
            ret = Sim_PE_No_Exception
    except:
        print "oops, python exception (bug)"
        ret = Sim_PE_No_Exception
    if ret != Sim_PE_No_Exception:
        show_mem_op(mop)
        show_map_info(info)
    return ret

def openpic_raise_int(obj, ack_fn, ack_arg):
    inst = openpic_instances[obj]
    inst.debug_pr(2, "raise_interrupt(obj=%s, ack_arg=%s)" % (obj.name,
                                                              ack_arg.name))
    # This interface should only be used for the 8259
    if ack_arg.classname != 'i8259x2':
        print "WARNING: got raise_interrupt() from non-8259 source"
    # Don't ack the interrupt; the OS will do that by talking to the 8259
    # directly. (Alternatively, we could implement the magic CHRP register
    # 8259-interrupt-acknowledge.)
    inst.activate_isu(0)

def openpic_lower_int(obj, ack_fn):
    inst = openpic_instances[obj]
    inst.debug_pr(2,
                  "lower_interrupt(obj=%s fn=%s)" % (obj.name, repr(ack_fn)))
    # to be implemented --- for some reason, the NS16550 does not lower
    # its line
    return Sim_PE_No_Exception

def get_irq_devs(data, obj, idx):
    return openpic_instances[obj].irq_devs

def set_irq_devs(data, obj, val, idx):
    def make_obj(x):
        if type(x) == type(''):
            return SIM_get_object(x)
        else:
            return x
    if type(val) != type([]):
        return Sim_Set_Need_List
    val = map(make_obj, val)
    inst = openpic_instances[obj]
    inst.irq_devs = val
    return Sim_Set_Ok

def get_isus(data, obj, idx):
    inst = openpic_instances[obj]
    return [isu.regs for isu in inst.isus]

def set_isus(data, obj, val, idx):
    if type(val) != type([]):
        return Sim_Set_Need_List
    inst = openpic_instances[obj]
    for i in range(max_isu + 1):
        inst.isus[i].regs = val[i]
    return Sim_Set_Ok

def get_timers(data, obj, idx):
    inst = openpic_instances[obj]
    return [t.regs for t in inst.timers]

def set_timers(data, obj, val, idx):
    if type(val) != type([]):
        return Sim_Set_Need_List
    inst = openpic_instances[obj]
    for i in range(4):
        inst.timers[i].regs = val[i]
    return Sim_Set_Ok

def get_ipi(data, obj, idx):
    return openpic_instances[obj].ipi_vec_pri

def set_ipi(data, obj, val, idx):
    if type(val) != type([]):
        return Sim_Set_Need_List
    openpic_instances[obj].ipi_vec_pri = val
    return Sim_Set_Ok

def get_spurious(data, obj, idx):
    return openpic_instances[obj].spurious_vec

def set_spurious(data, obj, val, idx):
    if type(val) != type(0):
        return Sim_Set_Need_Integer
    openpic_instances[obj].spurious_vec = val
    return Sim_Set_Ok

def get_global_conf(data, obj, idx):
    return openpic_instances[obj].global_conf_reg

def set_global_conf(data, obj, val, idx):
    if type(val) != type(0):
        return Sim_Set_Need_Integer
    openpic_instances[obj].global_conf_reg = val
    return Sim_Set_Ok

def get_active_isus(data, obj, idx):
    return openpic_instances[obj].active_isus.keys()

def set_active_isus(data, obj, val, idx):
    if type(val) != type([]):
        return Sim_Set_Need_List
    openpic_instances[obj].active_isus = {}
    for isu in val:
        openpic_instances[obj].active_isus[isu] = 1
    return Sim_Set_Ok

def get_in_progress(data, obj, idx):
    return openpic_instances[obj].in_progress

def set_in_progress(data, obj, val, idx):
    if type(val) != type([]):
        return Sim_Set_Need_List
    openpic_instances[obj].in_progress = val
    return Sim_Set_Ok

def get_pending(data, obj, idx):
    return [ [pri, src] for (pri, src) in openpic_instances[obj].pending ]

def set_pending(data, obj, val, idx):
    if type(val) != type([]):
        return Sim_Set_Need_List
    openpic_instances[obj].pending = val
    return Sim_Set_Ok

op_class = class_data_t()
op_class.new_instance = new_instance
op_class.description = """
Simple model of an OpenPIC-compliant interrupt controller."""
SIM_register_class("open-pic", op_class)

io_if = io_memory_interface_t()
io_if.map = openpic_map
io_if.operation = openpic_operation
SIM_register_interface("open-pic", "io-memory", io_if)

ia_if = interrupt_ack_interface_t()
ia_if.raise_interrupt = openpic_raise_int
ia_if.lower_interrupt = openpic_lower_int
SIM_register_interface("open-pic", "interrupt-ack", ia_if)

SIM_register_attribute("open-pic", "irq-devs",
                       get_irq_devs, 0, set_irq_devs, 0,
                       Sim_Attr_Required,
                       "List of devices to which interrupts are sent")
SIM_register_attribute("open-pic", "isus",
                       get_isus, 0, set_isus, 0,
                       Sim_Attr_Optional,
                       "Registers for each interrupt source")
SIM_register_attribute("open-pic", "timers",
                       get_timers, 0, set_timers, 0,
                       Sim_Attr_Optional,
                       "Registers for each timer")
SIM_register_attribute("open-pic", "ipi",
                       get_ipi, 0, set_ipi, 0,
                       Sim_Attr_Optional,
                       "IPI Vector/Priority registers")
SIM_register_attribute("open-pic", "spurious",
                       get_spurious, 0, set_spurious, 0,
                       Sim_Attr_Optional,
                       "Spurious vector register")
SIM_register_attribute("open-pic", "global-conf",
                       get_global_conf, 0, set_global_conf, 0,
                       Sim_Attr_Optional,
                       "Global configuration register")
SIM_register_attribute("open-pic", "active-isus",
                       get_active_isus, 0, set_active_isus, 0,
                       Sim_Attr_Optional,
                       "List of active sources")
SIM_register_attribute("open-pic", "in-progress",
                       get_in_progress, 0, set_in_progress, 0,
                       Sim_Attr_Optional,
                       "Current source in progress for each cpu")
SIM_register_attribute("open-pic", "pending",
                       get_pending, 0, set_pending, 0,
                       Sim_Attr_Optional,
                       "(<i>pri</i>, <i>src</i>) of pending sources"
                       + " for each cpu")

