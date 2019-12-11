# MODULE: leon2-components
# CLASS: leon2-simple

from sim_core import *
from components import *

def _make_leon_cfg(dsu, sdram, wpts, mac, nwin, icsz, ilsz, dcsz, dlsz, div,
                   mul, wdog, mst, fpu, pci, wp):
    leoncfg = 0
    leoncfg = leoncfg | dsu << 30    # Debug Support Unit
    leoncfg = leoncfg | sdram << 29  # SDRAM Controller
    leoncfg = leoncfg | wpts << 26   # N Watchpoints
    leoncfg = leoncfg | mac << 25    # MAC Instr Available
    leoncfg = leoncfg | (nwin-1) << 20   # Number of Register Windows
    leoncfg = leoncfg | icsz << 17   # I-Cache Size
    leoncfg = leoncfg | ilsz << 15   # I-Cache Line Size
    leoncfg = leoncfg | dcsz << 12   # D-Cache Size
    leoncfg = leoncfg | dlsz << 10   # D-Cache Line Size
    leoncfg = leoncfg | div << 9     # Integer Divide Instructions Enabled
    leoncfg = leoncfg | mul << 8     # Integer Multiply Instructions Enabled
    leoncfg = leoncfg | wdog << 7    # Watchdog Present
    leoncfg = leoncfg | mst << 6     # Mem Stat and Fail Addr Regs Available
    leoncfg = leoncfg | fpu << 4     # FPU Type (00 = None, 01 = Meiko)
    leoncfg = leoncfg | pci << 2     # PCI Core (00 = None, 01 = InSilicon,
                                     #           10 = ESA,  11 = Other)
    leoncfg = leoncfg | wp << 0      # Write Protection Type (00 = None,
                                     #                        01 = Standard)
    
    return leoncfg

class leon2_simple(component_object):
    classname   = 'leon2-simple'
    basename    = 'system'
    description = ('A simple LEON2 based component including a CPU and some memory.')
    
    connectors = {
        'uart1' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'uart2' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        }
    
    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
    
    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def get_prom_size(self, idx):
        return self.prom_size
    
    def set_prom_size(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.prom_size = val
        return Sim_Set_Ok

    def get_sram_size(self, idx):
        return self.sram_size
    
    def set_sram_size(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.sram_size = val
        return Sim_Set_Ok

    def set_has_sram(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.has_sram = val
        return Sim_Set_Ok
    
    def get_has_sram(self, idx):
        return self.has_sram


    def get_sdram_size(self, idx):
        return self.sdram_size
    
    def set_sdram_size(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.sdram_size = val
        return Sim_Set_Ok

    def set_num_windows(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        # must be a power of two and in the range [2, 32]
        if ((val & (val - 1)) != 0) and (val < 2) and (val > 32):
            return Sim_Set_Illegal_Value
        self.num_windows = val
        return Sim_Set_Ok
    
    def set_has_v8e_mac(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.has_v8e_mac = val
        return Sim_Set_Ok
    
    def set_has_v8_mul(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.has_v8_mul = val
        return Sim_Set_Ok
    
    def set_has_v8_div(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.has_v8_div = val
        return Sim_Set_Ok

    def get_num_windows(self, idx):
        return self.num_windows
            
    def get_has_v8e_mac(self, idx):
        return self.has_v8e_mac
            
    def get_has_v8_mul(self, idx):
        return self.has_v8_mul
    
    def get_has_v8_div(self, idx):
        return self.has_v8_div
    
    def add_objects(self):
        self.o.amba = pre_obj('amba$', 'memory-space')
        self.o.cpu = pre_obj('cpu$', 'leon2')
        self.o.cpu.processor_number = get_next_cpu_number()
        self.o.cpu.freq_mhz = self.freq_mhz
        self.o.cpu.physical_memory = self.o.amba
        self.o.cpu.num_windows = self.num_windows
        self.o.cpu.has_v8e_mac = self.has_v8e_mac
        self.o.cpu.has_v8_mul = self.has_v8_mul
        self.o.cpu.has_v8_div = self.has_v8_div
        
        # Interrupt controller
        self.o.irq1 = pre_obj("irq$", "leon2_irq")
        self.o.irq1.cpu = self.o.cpu
        self.o.irq1.queue = self.o.cpu
        self.o.cpu.interrupt_controller = self.o.irq1
        
        # Onchip prom
        self.o.prom_image = pre_obj('prom$_image', 'image')
        self.o.prom_image.size = self.prom_size
        self.o.prom_memory = pre_obj('prom$_memory', 'rom')
        self.o.prom_memory.image = self.o.prom_image
        
        # Onchip sram / sdram
        self.o.sram_image = pre_obj('sram$_image', 'image')
        self.o.sram_image.size = self.sram_size
        self.o.sram_memory = pre_obj('sram$_memory', 'ram')
        self.o.sram_memory.image = self.o.sram_image 

        self.o.sdram_image = pre_obj('sdram$_image', 'image')
        self.o.sdram_image.size = self.sdram_size
        self.o.sdram_memory = pre_obj('sdram$_memory', 'ram')
        self.o.sdram_memory.image = self.o.sdram_image 
        
        # UARTS
        self.o.uart1 = pre_obj('uart$', 'leon2_uart')
        self.o.uart1.irq = self.o.irq1
        self.o.uart1.interrupt = 3
        self.o.uart1.queue = self.o.cpu
        self.o.uart2 = pre_obj('uart$', 'leon2_uart')
        self.o.uart2.irq = self.o.irq1
        self.o.uart2.interrupt = 2
        self.o.uart2.queue = self.o.cpu

        # Timer
        self.o.timer = pre_obj("timer$", "leon2_timer")
        self.o.timer.irq = self.o.irq1
        self.o.timer.queue = self.o.cpu
        
        # Configuration registers (power down reg, memcfg, ccr, etc)
        self.o.cfg = pre_obj("cfg$", "leon2_cfg")
        self.o.cfg.cpu = self.o.cpu
        
        # Set the LEON2 configuration register
        sdram = 1
        if self.sdram_size == 0:
            sdram = 0    
        self.o.cfg.b_leonconfig  = _make_leon_cfg(0, sdram, 0, self.has_v8e_mac,
                                                self.num_windows, 0, 0, 0, 0,
                                                self.has_v8_div, self.has_v8_mul,
                                                0, 0, 1, 0, 0)
        
        # Parallel IO
        self.o.ioport = pre_obj("ioport$", "leon2_ioport")
        
        # Ethernet
        self.o.eth = pre_obj("eth$", "opencores_eth")
        self.o.eth.irq_ctrl = self.o.irq1

        self.o.amba.map = [
            [0x00000000, self.o.prom_memory, 0, 0, self.prom_size],
            [0x80000000, self.o.cfg, 0, 0, 0x28],
            [0x80000040, self.o.timer, 0, 0, 0x28],
            [0x80000070, self.o.uart1, 0, 0, 16],
            [0x80000080, self.o.uart2, 0, 0, 16],
            [0x80000090, self.o.irq1, 0, 0, 16],
            [0x800000a0, self.o.ioport, 0, 0, 12],
            [0xb0000000, self.o.eth, 0, 0, 0x0001ffff]]
        
        # physical memory map                     
        if self.has_sram == 1:
            self.o.amba.map = self.o.amba.map + [
                [0x00000000, self.o.prom_memory, 0, 0, self.prom_size],
                [0x40000000, self.o.sram_memory, 0, 0, self.sram_size],
                [0x60000000, self.o.sdram_memory, 0, 0, self.sdram_size]]
        else:
            self.o.amba.map = self.o.amba.map + [
                [0x00000000, self.o.prom_memory, 0, 0, self.prom_size],
                [0x40000000, self.o.sdram_memory, 0, 0, self.sdram_size]]
                            
    def add_connector_info(self):
        self.connector_info['uart1'] = [None, self.o.uart1, self.o.uart1.name]
        self.connector_info['uart2'] = [None, self.o.uart2, self.o.uart2.name]
    
    
    def connect_serial(self, connector, link, console):
        if connector == 'uart1':
            if link:
                self.o.uart1.link = link
            else:
                self.o.uart1.console = console
        elif connector == 'uart2':
            if link:
                self.o.uart2.link = link
            else:
                self.o.uart2.console = console
    
    def disconnect_serial(self, connector):
        if connector == 'uart1':
            self.o.uart1.console = None
        elif connector == 'uart2':
            self.o.uart2.console = None

    def instantiation_done(self):
        component_object.instantiation_done(self)
        conf.sim.handle_outside_memory = 1

    def get_clock(self):
        return self.o.cpu

    def get_processors(self):
        return [self.o.cpu]


leon2_simple_attributes = [
    ['cpu_frequency', Sim_Attr_Required, 'f',
     'Processor frequency in MHz.'],
    ['prom_size', Sim_Attr_Required, 'i',
     'Size of PROM in bytes'],
    ['has_sram', Sim_Attr_Required, 'i',
     'True if SRAM is available (if so, SDRAM starts at 0x60000000)'],
    ['sram_size', Sim_Attr_Required, 'i',
     'Size of SRAM in bytes'],
    ['sdram_size', Sim_Attr_Required, 'i',
     'Size of SDRAM in bytes'],
    ['num_windows', Sim_Attr_Required, 'i',
     'Number of register windows, (must be a power of 2)'],
    ['has_v8e_mac', Sim_Attr_Required, 'b',
     'TRUE if the V8E UMAC / SMAC instructions are to be allowed'],
    ['has_v8_mul', Sim_Attr_Required, 'b',
     'TRUE if the V8 IMUL instructions are to be allowed'],
    ['has_v8_div', Sim_Attr_Required, 'b',
     'TRUE if the V8 IDIV instructions are to be allowed']]

register_component_class(
    leon2_simple,
    leon2_simple_attributes,
    top_level = True)
