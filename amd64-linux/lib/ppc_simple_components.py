# MODULE: ppc-simple-components
# CLASS: ppc-simple

from sim_core import *
from components import *


# Simple System with a PPC Processor


class ppc_simple_component(component_object):
    classname = 'ppc-simple'
    basename = 'system'
    description = ('A simple system containing a single PPC processor, some '
                   'memory and a serial device.')
    connectors = {
        'uart0' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def get_cpu_class(self, idx):
        return self.cpu_class

    def set_cpu_class(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        try:
            SIM_get_class(val)
        except:
            SIM_attribute_error("Unsupported CPU class: %s" % val)
            return Sim_Set_Illegal_Value
        self.cpu_class = val
        return Sim_Set_Ok

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
        self.memory_megs = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.broadcast_bus = pre_obj('broadcast_bus', 'ppc-broadcast-bus')
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        #
        self.o.cpu = pre_obj('cpu$', self.cpu_class)
        self.o.cpu.processor_number = get_next_cpu_number()
        self.o.cpu.freq_mhz = self.freq_mhz
        self.o.cpu.timebase_freq_mhz = self.freq_mhz / 8
        self.o.cpu.physical_memory = self.o.phys_mem
        self.o.cpu.cpu_group = self.o.broadcast_bus
        #
        self.o.ram_image = pre_obj('memory_image', 'image')
        self.o.ram_image.size = self.memory_megs * 0x100000
        self.o.ram = pre_obj('memory', 'ram')
        self.o.ram.image = self.o.ram_image
        #
        self.o.uart0 = pre_obj('uart0', 'NS16550')
        self.o.uart0.xmit_time = 1000
        #
        self.o.phys_mem.map = [
            #
            # RAM starting at address 0x0
            #
            [0x00000000, self.o.ram,    0,  0x0, self.memory_megs * 0x100000],
            #
            # One serial device (UART)
            #
            [0xff600300, self.o.uart0,  0,  0x0,  0x8, None, 0, 1]]

    def add_connector_info(self):
        self.connector_info['uart0'] = [None, self.o.uart0, self.o.uart0.name]

    def connect_serial(self, connector, link, console):
        if link:
            self.o.uart0.link = link
        else:
            self.o.uart0.console = console

    def disconnect_serial(self, connector):
        self.o.uart0.link = None
        self.o.uart0.console = None

    def get_clock(self):
        return self.o.cpu

    def get_processors(self):
        return [self.o.cpu]

register_component_class(
    ppc_simple_component,
    [['cpu_class', Sim_Attr_Required, 's',
      'Processor type, PowerPC processor to use.'],
     ['cpu_frequency', Sim_Attr_Required, 'f',
      'Processor frequency in MHz.'],
     ['memory_megs', Sim_Attr_Required, 'i',
      'The amount of RAM in megabytes.']],
    top_level = True)
