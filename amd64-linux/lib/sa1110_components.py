# MODULE: arm-sa1110-components
# CLASS: arm-sa1110-system

from sim_core import *
from components import *


### ARM SA1110 System


class arm_sa1110_system_component(component_object):
    classname = 'arm-sa1110-system'
    basename = 'system'
    description = ('The "arm-sa1110-system" component represents a simple '
                   'ARM SA1110 system with a single processor and a serial '
                   'device.')
    connectors = {
        'console' : {'type' : 'serial', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : False, 'multi' : False}}

    def __init__(self, *args):
        component_object.__init__(self, *args)
        self.memory_megs = 32

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def get_memory_megs(self, idx):
        return self.memory_megs

    def set_memory_megs(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if (val < 1) or (val > 128):
            SIM_frontend_exception(SimExc_General, 'Unsupported memory size')
            return Sim_Set_Illegal_Value
        self.memory_megs = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.cpu = pre_obj('cpu', 'armv5te')
        self.o.cpu.freq_mhz = self.freq_mhz
        self.o.cpu.processor_number = get_next_cpu_number()
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.sa1110 = pre_obj('sa1110', 'SA1110-device')
        self.o.sa1110.irq_dev = self.o.cpu
        self.o.hfs = pre_obj('hfs', 'hostfs')
        self.o.ram_image = pre_obj('ram_image', 'image')
        self.o.ram = pre_obj('ram', 'ram')
        self.o.rom_image = pre_obj('rom_image', 'image')
        self.o.rom = pre_obj('rom', 'rom')
        self.o.bsr_bcr_image = pre_obj('bsr_bcr_image', 'image')
        self.o.bsr_bcr = pre_obj('bsr_bcr', 'rom')
        self.o.cpu.physical_memory = self.o.phys_mem
        self.o.ram.image = self.o.ram_image
        ram_size = self.memory_megs * 0x100000
        self.o.ram_image.size = ram_size
        self.o.rom.image = self.o.rom_image
        self.o.rom_image.size = 0x10000000
        self.o.bsr_bcr.image = self.o.bsr_bcr_image
        self.o.bsr_bcr_image.size = 0x2000
        self.o.phys_mem.map = [
            [0x12000000, self.o.bsr_bcr, 0, 0x0, 0x00000004],
            [0x50000000, self.o.hfs,     0, 0x0, 0x00000010],
            [0x80000000, self.o.sa1110,  0, 0x0, 0x20000000],
            [0xc0000000, self.o.ram,     0, 0x0, ram_size],
            [0xe0000000, self.o.rom,     0, 0x0, 0x10000000]]

    def add_connector_info(self):
        self.connector_info['console'] = [None, self.o.sa1110,
                                          'Serial Console']

    def instantiation_done(self):
        component_object.instantiation_done(self)

    def connect_serial(self, connector, link, console):
        if link:
            self.o.sa1110.link = link
        else:
            self.o.sa1110.console = console

    def disconnect_serial(self, connector):
        # TODO: self.o.sa1110.link = None
        self.o.sa1110.console = None

    def get_clock(self):
        return self.o.cpu

    def get_processors(self):
        return [self.o.cpu]

register_component_class(
    arm_sa1110_system_component,
    [['cpu_frequency', Sim_Attr_Required, 'i',
      'Processor frequency in MHz.'],
     ['memory_megs', Sim_Attr_Optional, 'i',
      'Size of RAM (mapped from 0xc0000000) in MB.']
     ],
    top_level = True)
