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

from sim_core import *
from components import *

import time

# Generic Simple System for PPC64 Processors
class ppc64_simple_base_component(component_object):
    basename = 'system'
    connectors = {
        'uart0' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'uart1' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.cpu = []
        self.map_offset = 0xf0000000
        self.time_of_day = "2006-06-06 06:06:06 UTC"

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

    def get_map_offset(self, idx):
        return self.map_offset

    def set_map_offset(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.map_offset = val
        return Sim_Set_Ok

    def get_time_of_day(self, idx):
        return self.time_of_day

    def set_time_of_day(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        try:
            time.strptime(val, "%Y-%m-%d %H:%M:%S %Z")
        except Exception, msg:
            SIM_attribute_error(str(msg))
            return Sim_Set_Illegal_Value
        self.time_of_day = val
        return Sim_Set_Ok

    def add_objects(self, cpu):
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.ram_image = pre_obj('memory_image', 'image')
        self.o.ram_image.size = self.memory_megs * 0x100000
        self.o.ram = pre_obj('memory', 'ram')
        self.o.ram.image = self.o.ram_image
        self.o.pic = pre_obj('pic$', 'open-pic')
        self.o.pic.irq_devs = [cpu]
        self.o.irq = pre_obj('irq$', 'i8259x2')
        self.o.irq.irq_dev = self.o.pic
        self.o.uart0 = pre_obj('uart0', 'NS16550')
        self.o.uart0.irq_dev = self.o.irq
        self.o.uart0.irq_level = 4
        self.o.uart0.xmit_time = 1000
        self.o.uart1 = pre_obj('uart1', 'NS16550')
        self.o.uart1.irq_dev = self.o.irq
        self.o.uart1.irq_level = 3
        self.o.uart1.xmit_time = 1000
        self.o.of = pre_obj('of', 'ppc-of')
        self.o.of.cpu = self.o.cpu[0]
        self.o.of.memory_megs = self.memory_megs
        self.o.of.entry_point = 0x7000000
        self.o.of.map_offset = self.map_offset
        self.o.of.time_of_day = self.time_of_day
        self.o.broadcast_bus = pre_obj('broadcast_bus', 'ppc-broadcast-bus')
        self.o.empty = pre_obj('empty', 'empty-device')
        self.o.pci_io = pre_obj('pci_io', 'memory-space')
        self.o.hfs = pre_obj('hfs$', 'hostfs')

        self.o.phys_mem.map = [
            [0x00000000, self.o.ram,    0, 0x0,  self.memory_megs * 0x100000],
            [self.map_offset + 0x08000000, self.o.pci_io, 0, 0x0,  0x100000],
            [self.map_offset + 0x0f660000, self.o.hfs,    0, 0,    0x10],
            [self.map_offset + 0x0fc00000, self.o.pic,    0, 0x0,  0x100000]]

        self.o.pci_io.map = [
            [0x020, self.o.irq,         0, 0x20, 0x1],
            [0x021, self.o.irq,         0, 0x21, 0x1],
            [0x0a0, self.o.irq,         0, 0xa0, 0x1],
            [0x0a1, self.o.irq,         0, 0xa1, 0x1],

            # Linux probes for UARTs at 0x2e8 and 0x3e8 too, so provide
            # empty mappings there
            [0x2e8, self.o.empty,       0, 0x0,  0x8],

            # two NS16550, at the traditional addresses
            [0x2f8, self.o.uart1,       0,  0x0, 0x8, None, 0, 1],

            [0x3e8, self.o.empty,       0,  0x0, 0x8],

            [0x3f8, self.o.uart0,       0,  0x0, 0x8, None, 0, 1],

            # no UARTs here either
            [0x890, self.o.empty,       0,  0x0, 0x8],
            [0x898, self.o.empty,       0,  0x0, 0x8]]

    def add_connector_info(self):
        self.connector_info['uart0'] = [None, self.o.uart0, self.o.uart0.name]
        self.connector_info['uart1'] = [None, self.o.uart1, self.o.uart1.name]

    def connect_serial(self, connector, link, console):
        if connector == 'uart0':
            if link:
                self.o.uart0.link = link
            else:
                self.o.uart0.console = console
        elif connector == 'uart1':
            if link:
                self.o.uart1.link = link
            else:
                self.o.uart1.console = console

    def disconnect_serial(self, connector):
        if connector == 'uart0':
            self.o.uart0.link = None
            self.o.uart0.console = None
        elif connector == 'uart1':
            self.o.uart1.link = None
            self.o.uart1.console = None

    def get_clock(self):
        return self.o.cpu[0]

    def get_processors(self):
        return self.o.cpu

ppc64_simple_attributes =  [
    ['cpu_frequency', Sim_Attr_Required, 'f',
     'Processor frequency in MHz.'],
    ['memory_megs', Sim_Attr_Required, 'i',
     'The amount of RAM in megabytes.'],
    ['map_offset', Sim_Attr_Optional, 'i',
     'Base address for device mappings. ' \
     'Offsets at 4 GB and above will not work'],
    ['time_of_day', Sim_Attr_Optional, 's',
     'Date and time to initialize the OpenFirmware RTC to']]
