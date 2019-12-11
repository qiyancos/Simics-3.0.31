
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

# MODULE: ppc440gp-components
# CLASS: ebony-board

import time
from sim_core import *
from components import *

# TODO: change...
SIM_source_python_in_module('%s/home/scripts/flash_memory.py'
                            % conf.sim.simics_base, __name__)


### PPC440GP SOC, base class only for now


class ppc440gp_soc_component(component_object):
    connectors = {
        'uart0' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'uart1' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'emac0' : {'type' : 'ethernet-link', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'emac1' : {'type' : 'ethernet-link', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    for i in range(2):
        connectors['ddr-slot%d' % i] = {
            'type' : 'mem-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    for i in range(0, 4):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    memory_megs = 0

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def get_mac(self, idx):
        return eval('self.mac%d' % idx)

    def set_mac(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if len(mac_as_list(val)) != 6:
            return Sim_Set_Illegal_Value
        exec "self.mac%d = val" % idx
        return Sim_Set_Ok

    def get_mac_address0(self, idx):
        return self.get_mac(0)

    def set_mac_address0(self, val, idx):
        return self.set_mac(val, 0)

    def get_mac_address1(self, idx):
        return self.get_mac(1)

    def set_mac_address1(self, val, idx):
        return self.set_mac(val, 1)

    def add_objects(self):
        self.o.plb = pre_obj('plb', 'memory-space')
        self.o.dcr_space = pre_obj('dcr_space', 'memory-space')        
        self.o.cpu = pre_obj('cpu$', 'ppc440gp')
        self.o.cpu.processor_number = get_next_cpu_number()
        self.o.cpu.freq_mhz = self.freq_mhz
        self.o.cpu.timebase_freq_mhz = self.freq_mhz
        self.o.cpu.physical_memory = self.o.plb
        self.o.cpu.dcr_space = self.o.dcr_space
        self.o.uic0 = pre_obj('uic$', 'ppc440gp-uic')
        self.o.uic0.target = self.o.cpu
        self.o.uic0.target_level = 0
        self.o.uic0.critical_target = self.o.cpu
        self.o.uic0.critical_target_level = 0
        self.o.uic1 = pre_obj('uic$', 'ppc440gp-uic')
        self.o.uic1.target = self.o.uic1
        self.o.uic1.target_level = 30
        self.o.uic1.critical_target = self.o.uic0
        self.o.uic1.critical_target_level = 31
        self.o.dma = pre_obj('dma$', 'ppc440gp-dma')
        self.o.dma.interrupt_device = self.o.uic0
        self.o.dma.memory = self.o.plb
        self.o.dma.cpu = self.o.cpu        
        self.o.cpc = pre_obj('cpc$', 'ppc440gp-cpc')
        self.o.ebc = pre_obj('ebc$', 'ppc440gp-ebc')
        self.o.ebc.cpu = self.o.cpu
        self.o.plb_arbiter = pre_obj('plb_arbiter$', 'ppc440gp-plb')

        self.o.broadcast_bus = pre_obj('broadcast_bus', 'ppc-broadcast-bus')
        self.o.cpu.cpu_group = self.o.broadcast_bus

        # the ppc440gp includes 8Kb onchip sram
        self.o.sram_image = pre_obj('sram$_image', 'image')
        self.o.sram_image.size =  0x2000
        self.o.sram_memory = pre_obj('sram$_memory', 'ram')
        self.o.sram_memory.image = self.o.sram_image 
        
        # the sram controller handles the mapping of sram on the plb bus
        self.o.sram = pre_obj('sram$', 'ppc440gp-sram')
        self.o.sram.sram = self.o.sram_memory
        self.o.sram.plb = self.o.plb
        
        self.o.gpio = pre_obj('gpio$', 'ppc440gp-gpio')
        self.o.i2c0 = pre_obj('i2c$', 'i2c-bus')
        self.o.i2c1 = pre_obj('i2c$', 'i2c-bus')
        self.o.iic0 = pre_obj('iic$', 'ppc440gp-iic')
        self.o.iic0.i2c_bus = self.o.i2c0
        self.o.iic0.interrupt_device = self.o.uic0
        self.o.iic0.interrupt_level = 2
        self.o.iic1 = pre_obj('iic$', 'ppc440gp-iic')
        self.o.iic1.i2c_bus = self.o.i2c1
        self.o.iic1.interrupt_device = self.o.uic0
        self.o.iic1.interrupt_level = 3
        self.o.mc = pre_obj('mc$', 'ppc440gp-mc')
        self.o.mc.memory = self.o.plb
        # MCSTS: Fake: set MRSC & CIS (MRS complete & IDLE)
        self.o.mc.SDRAM0_MCSTS = 0xa0000000 
        self.o.mc.SDRAM0_DLYCAL = 0x40
        self.o.mc.SDRAM0_B0CR   = 0x00000001
        self.o.mal = pre_obj('mal$', 'ppc440gp-mal')
        self.o.mal.memory = self.o.plb
        self.o.mal.cpu = self.o.cpu        
        self.o.mal.interrupts = [self.o.uic0, self.o.uic0]
        self.o.emac0 = pre_obj('emac$', 'ppc440gp-emac')
        self.o.emac0.mac_address = self.mac0
        self.o.emac0.mal = self.o.mal
        self.o.emac1 = pre_obj('emac$', 'ppc440gp-emac')
        self.o.emac1.mac_address = self.mac1
        self.o.emac1.mal = self.o.mal
        self.o.zmii = pre_obj('zmii$', 'ppc440gp-zmii')
        self.o.uart0 = pre_obj('uart$', 'NS16550')
        self.o.uart0.irq_dev = self.o.uic0
        self.o.uart0.irq_level = 0
        self.o.uart1 = pre_obj('uart$', 'NS16550')
        self.o.uart1.irq_dev = self.o.uic0
        self.o.uart1.irq_level = 1
        self.o.pci = pre_obj('pci$', 'ppc440gp-pci')
        self.o.pci.plb = self.o.plb
        self.o.pci.irq_routing = [[1, self.o.uic0, 23],
                                  [2, self.o.uic0, 24],
                                  [3, self.o.uic0, 25],
                                  [4, self.o.uic0, 26]]
        self.o.pciconf = pre_obj('pciconf$', 'memory-space')
        self.o.pciio = pre_obj('pciio$', 'memory-space')
        self.o.pciio.map = []
        self.o.pcimem = pre_obj('pcimem$', 'memory-space')
        self.o.pcimem.map = []
        self.o.pcibus = pre_obj('pcibus$', 'pci-bus')
        self.o.pcibus.bridge = self.o.pci
        self.o.pcibus.interrupt = self.o.pci
        self.o.pcibus.conf_space = self.o.pciconf
        self.o.pcibus.io_space = self.o.pciio
        self.o.pcibus.memory_space = self.o.pcimem
        self.o.pcibus.pci_devices = [[0, 0, self.o.pci]]
        self.o.pci.pci_bus = self.o.pcibus
        self.o.hfs = pre_obj('hfs$', 'hostfs')

        self.o.dcr_space.map = dcr_memory_map([
            # Object      Fn  Idx    DCR (or range in case of list)
            [self.o.mc,   0, [(0x0,  [0x10, 0x11])]],
            [self.o.ebc,  0, [(0x0,  [0x12, 0x13])]],
            [self.o.plb_arbiter, 0, [(0x0,  [0x82, 0x84]),
                              (0x4,   0x86),
                              (0x5,   0x87)]],
            [self.o.sram, 0, [(0x0,  [0x20, 0x2a])]],
            [self.o.cpc,  0, [(0x0,  [0xb0, 0xb3]),
                              (0x30, [0xe0, 0xef])]],
            [self.o.uic0, 0, [(0x0,  0xc0),
                              (0x2,  [0xc2, 0xc8])]],        
            [self.o.uic1, 0, [(0x0,  0xd0),
                              (0x2,  [0xd2, 0xd8])]],
            [self.o.dma,  0, [(0x0,  [0x100, 0x120]),
                              (0x23, 0x123),
                              (0x25, 0x125),
                              (0x26, 0x126)]],
            [self.o.mal,  0, [(0x0,  [0x180, 0x182]),
                              (0x4,  [0x184,0x195]),
                              (0x20, [0x1a0,0x1a3]),
                              (0x40, [0x1c0, 0x1c1]),
                              (0x60, [0x1e0, 0x1e1])]]
            ])
        
        # physical memory map
        self.o.plb.map = [
            [0x0ff660000, self.o.hfs,   0,     0,  0x10],
            [0x140000200, self.o.uart0, 0,     0,   0x8, None, 0, 1],
            [0x140000300, self.o.uart1, 0,     0,   0x8, None, 0, 1],

            [0x140000400, self.o.iic0,  0,  0x00,   2],
            [0x140000402, self.o.iic0,  0,  0x02,   2],
            [0x140000404, self.o.iic0,  0,  0x04,   1],
            [0x140000405, self.o.iic0,  0,  0x05,   1],
            [0x140000406, self.o.iic0,  0,  0x06,   1],
            [0x140000407, self.o.iic0,  0,  0x07,   1],
            [0x140000408, self.o.iic0,  0,  0x08,   1],
            [0x140000409, self.o.iic0,  0,  0x09,   1],
            [0x14000040a, self.o.iic0,  0,  0x0a,   1],
            [0x14000040b, self.o.iic0,  0,  0x0b,   1],
            [0x14000040c, self.o.iic0,  0,  0x0c,   1],
            [0x14000040d, self.o.iic0,  0,  0x0d,   1],
            [0x14000040e, self.o.iic0,  0,  0x0e,   1],
            [0x14000040f, self.o.iic0,  0,  0x0f,   1],
            [0x140000410, self.o.iic0,  0,  0x10,   1],
           
            [0x140000500, self.o.iic1,  0,  0x00,   2],
            [0x140000502, self.o.iic1,  0,  0x02,   2],
            [0x140000504, self.o.iic1,  0,  0x04,   1],
            [0x140000505, self.o.iic1,  0,  0x05,   1],
            [0x140000506, self.o.iic1,  0,  0x06,   1],
            [0x140000507, self.o.iic1,  0,  0x07,   1],
            [0x140000508, self.o.iic1,  0,  0x08,   1],
            [0x140000509, self.o.iic1,  0,  0x09,   1],
            [0x14000050a, self.o.iic1,  0,  0x0a,   1],
            [0x14000050b, self.o.iic1,  0,  0x0b,   1],
            [0x14000050c, self.o.iic1,  0,  0x0c,   1],
            [0x14000050d, self.o.iic1,  0,  0x0d,   1],
            [0x14000050e, self.o.iic1,  0,  0x0e,   1],
            [0x14000050f, self.o.iic1,  0,  0x0f,   1],
            [0x140000510, self.o.iic1,  0,  0x10,   1],
           
            [0x140000700, self.o.gpio,  0,     0,  0x80],
            [0x140000780, self.o.zmii,  0,     0,     4],
            [0x140000784, self.o.zmii,  0,     1,     4],
            [0x140000788, self.o.zmii,  0,     2,     4],
            [0x140000800, self.o.emac0, 0,     0, 0x100],
            [0x140000900, self.o.emac1, 1,     0, 0x100],

            [0x208000000, self.o.pci,   4,      0, 0x000010000, self.o.pciio],
            [0x20ec00000, self.o.pci,   1,      0, 0x000000008],
            [0x20ec80000, self.o.pci,   2, 0x20ec80000, 0x000000100],
            [0x20ee00000, self.o.pci,   3,      0, 0xdf1200000, self.o.pcimem]]


    def add_connector_info(self):
        self.connector_info['uart0'] = [None, self.o.uart0, self.o.uart0.name]
        self.connector_info['uart1'] = [None, self.o.uart1, self.o.uart1.name]
        self.connector_info['emac0'] = []
        self.connector_info['emac1'] = []

        for i in range(2):
            self.connector_info['ddr-slot%d' % i] = [self.o.i2c0, 0x53 - i]

        for i in range(0, 4):
            self.connector_info['pci-slot%d' % i] = [i, self.o.pcibus]

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

    def connect_mem_bus(self, connector, memory_megs, memory_ranks):
        self.memory_megs += memory_megs
        self.update_memory_dep_attrs()

    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        device = slot + 1 # see bug 2760
        pci_devices = bus.pci_devices
        for d in device_list:
            pci_devices += [[device, d[0], d[1]]]
        bus.pci_devices = pci_devices

    def connect_ethernet_link(self, connector, link):
        if connector == 'emac0':
            self.o.emac0.link = link
        else:
            self.o.emac1.link = link

    def disconnect_ethernet_link(self, connector):
        if connector == 'emac0':
            self.o.emac0.link = None
        else:
            self.o.emac1.link = None

    def instantiation_done(self):
        component_object.instantiation_done(self)
        conf.sim.handle_outside_memory = 1

    def get_clock(self):
        return self.o.cpu

    def get_processors(self):
        return [self.o.cpu]

ppc440gp_soc_attributes = [
    ['cpu_frequency', Sim_Attr_Required, 'i',
     'Processor frequency in MHz.'],
    ['mac_address0', Sim_Attr_Required, 's',
     'The MAC address of the first Ethernet adapter.'],
    ['mac_address1', Sim_Attr_Required, 's',
     'The MAC address of the second Ethernet adapter.']]


### Ebony Evaluation Board (PPC440GP SOC based)


class ebony_board_component(ppc440gp_soc_component):
    classname = 'ebony-board'
    basename = 'system'
    description = ('The "ebony-board" component represents the ebony board '
                   'including the CPU.')

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)

    def get_rtc_time(self, idx):
        return self.tod

    def set_rtc_time(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        try:
            time.strptime(val, '%Y-%m-%d %H:%M:%S %Z')
        except Exception, msg:
            SIM_attribute_error(str(msg))
            return Sim_Set_Illegal_Value
        self.tod = val
        return Sim_Set_Ok

    def setup_strp(self, fwd, cpu_to_plb, fbk):
	# sanity checks
	if fwd > 8 or fwd < 1:
            print "invalid forward divisor"
        if cpu_to_plb > 4 or cpu_to_plb < 1:
            print "invalid cpu-to-plb divisor"
	if fbk > 16 or fbk < 1:
            print "invalid feedback divisor"
        # reference frequency equal to pci bus
        ref = pci = 33.333333
	# calculate frequencies
	cpu = round(ref * fbk * cpu_to_plb)
	plb = round(cpu / cpu_to_plb)
	# calculate strp0 field values
	fwdv = int(8 - fwd)
	fbdv = int(fbk & 0x0000FFFF)
	cbdv = int(cpu_to_plb - 1)
	opdv = int(2)
	ppdv = int(round(plb / pci))
	epdv = int(2)
	# more sanity checks
	if fwdv < 0 or fwdv > 7:
            print "invalid fwdv value"
        if fbdv < 0 or fbdv > 15:
            print "invalid fwdv value"
        if cbdv < 0 or cbdv > 3:
            print "invalid cbdv value"
	if opdv < 0 or opdv > 3:
            print "invalid opdv value"
	if ppdv < 0 or ppdv > 3:
            print "invalid ppdv value"
	if epdv < 0 or epdv > 3:
            print "invalid epdv value"
        strp0 = fbdv << 17
        strp0 |= fwdv << 15
	strp0 |= fwdv << 12
	strp0 |= opdv << 10
	strp0 |= ppdv << 13
	strp0 |= epdv << 11
        self.o.cpc.CPC0_STRP0 = strp0

    def update_memory_dep_attrs(self):
        self.o.ram_image.size =  self.memory_megs * 0x100000
        plb_map = self.o.plb.map
        for i in range(len(plb_map)):
            if plb_map[i][1] == self.o.ram:
                plb_map[i] = [0x000000000, self.o.ram, 0, 0, self.memory_megs * 0x100000]
                break
        self.o.plb.map = plb_map

    def add_objects(self):
        ppc440gp_soc_component.add_objects(self)
        self.o.ram_image = pre_obj('sdram_image', 'image')
        self.o.ram_image.size = 0x100000
        self.o.ram = pre_obj('sdram', 'ram')
        self.o.ram.image = self.o.ram_image
        self.o.dummy_CDCV850 = pre_obj('dummy_CDCV850', 'sample-i2c-device')
        self.o.dummy_CDCV850.address = (0xd2 >> 1)
        self.o.dummy_CDCV850.i2c_bus = self.o.i2c0
        self.o.fpga = pre_obj('fpga$', 'ebony-fpga')
        self.o.rtc = pre_obj('rtc$', 'DS1743P')
        mac = mac_as_list(self.mac0)
        self.o.rtc.nvram = (
            (1280 * (0,) + (mac[3], mac[4], mac[5])
             + 2805 * (0,)
             + (0x8b, 0x86, 0x00, 0x7e, 0x62, 0x6f, 0x6f, 0x74, 0x61, 0x72,
                0x67, 0x73, 0x3d, 0x72, 0x6f, 0x6f, 0x74, 0x3d, 0x2f, 0x64,
                0x65, 0x76, 0x2f, 0x68, 0x64, 0x61, 0x31, 0x20, 0x00, 0x62,
                0x61, 0x75, 0x64, 0x72, 0x61, 0x74, 0x65, 0x3d, 0x39, 0x36,
                0x30, 0x30, 0x00, 0x6c, 0x6f, 0x61, 0x64, 0x73, 0x5f, 0x65,
                0x63, 0x68, 0x6f, 0x3d, 0x31, 0x00, 0x73, 0x74, 0x64, 0x69,
                0x6e, 0x3d, 0x73, 0x65, 0x72, 0x69, 0x61, 0x6c, 0x00, 0x73,
                0x74, 0x64, 0x6f, 0x75, 0x74, 0x3d, 0x73, 0x65, 0x72, 0x69,
                0x61, 0x6c, 0x00, 0x73, 0x74, 0x64, 0x65, 0x72, 0x72, 0x3d,
                0x73, 0x65, 0x72, 0x69, 0x61, 0x6c, 0x00, 0x62, 0x6f, 0x6f,
                0x74, 0x63, 0x6d, 0x64, 0x3d, 0x62, 0x6f, 0x6f, 0x74, 0x6d,
                0x20, 0x66, 0x66, 0x63, 0x30, 0x30, 0x30, 0x30, 0x30, 0x20,
                0x66, 0x66, 0x64, 0x30, 0x30, 0x30, 0x30, 0x30)
             + 3968 * (0,)
             + (0x20, 0x00, 0x17, 0x11, 0x03, 0x03, 0x09, 0x03)))
        flash, x = flash_create_memory('sflash1', 'Am29F040B', 1, 8, [])
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.sflash1 = flash_pre['sflash1']
        self.o.sflash1_image = flash_pre['sflash1_image']
        self.o.sflash1_ram = flash_pre['sflash1_ram']
        flash, x = flash_create_memory('sflash2', 'Am29F040B', 1, 8, [])
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.sflash2 = flash_pre['sflash2']
        self.o.sflash2_image = flash_pre['sflash2_image']
        self.o.sflash2_ram = flash_pre['sflash2_ram']
        flash, x = flash_create_memory('lflash1', 'Am29F016D', 1, 8, [])
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.lflash1 = flash_pre['lflash1']
        self.o.lflash1_image = flash_pre['lflash1_image']
        self.o.lflash1_ram = flash_pre['lflash1_ram']
        flash, x = flash_create_memory('lflash2', 'Am29F016D', 1, 8, [])
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.lflash2 = flash_pre['lflash2']
        self.o.lflash2_image = flash_pre['lflash2_image']
        self.o.lflash2_ram = flash_pre['lflash2_ram']
        self.o.plb.map += [
            [0x000000000, self.o.ram,     0,      0, 0x100000],
            [0x148000000, self.o.rtc,     0,      0,   0x1ff8],
            [0x148001ff8, self.o.rtc,     0, 0x1ff8,   0x0001],
            [0x148001ff9, self.o.rtc,     0, 0x1ff9,   0x0001],
            [0x148001ffa, self.o.rtc,     0, 0x1ffa,   0x0001],
            [0x148001ffb, self.o.rtc,     0, 0x1ffb,   0x0001],
            [0x148001ffc, self.o.rtc,     0, 0x1ffc,   0x0001],
            [0x148001ffd, self.o.rtc,     0, 0x1ffd,   0x0001],
            [0x148001ffe, self.o.rtc,     0, 0x1ffe,   0x0001],
            [0x148001fff, self.o.rtc,     0, 0x1fff,   0x0001],
            [0x148300000, self.o.fpga,    0,      0,        3],
            [0x1ff800000, self.o.sflash2, 0,      0,  0x80000,
             self.o.sflash2_ram, 0, 1],
            [0x1ff880000, self.o.sflash1, 0,      0,  0x80000,
             self.o.sflash1_ram, 0, 1],
            [0x1ffc00000, self.o.lflash1, 0,      0, 0x200000,
             self.o.lflash1_ram, 0, 1],
            [0x1ffe00000, self.o.lflash2, 0,      0, 0x200000,
             self.o.lflash2_ram, 0, 1]]
        self.setup_strp(4,3,2)

    def instantiation_done(self):
        ppc440gp_soc_component.instantiation_done(self)
        base = 0x1fffffe00
        self.o.plb.memory[[base + 0x0c, base + 0x11]] = mac_as_list(self.mac0)
        self.o.plb.memory[[base + 0x18, base + 0x1d]] = mac_as_list(self.mac1)
        m = re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', self.tod)
        eval_cli_line(('%s.set-date-time '
                       + 'year=%s month=%s mday=%s hour=%s minute=%s second=%s'
                       ) % ((self.o.rtc.name,) + m.groups()))

# Returns list of port space mappings for dcr
def dcr_memory_map(devices):
    mapping = []
    for d in devices:
        if len(d) < 3:
            print "invalid dcr mapping:",
            print d
            return    
        obj = d[0]
        fn  = d[1]
        dcr_map = d[2]
        # Go through all dcr addresses
        for m in dcr_map:
            (ofs, dcr) = m
            ofs = ofs * 4
            if isinstance(dcr,int):
                mapping += [[dcr*4, obj, fn, ofs, 4]]
            elif len(dcr) == 2:
                mapping += [[(dcr[0] + i)*4, obj, fn, ofs+i*4, 4] for i in range(dcr[1] + 1 - dcr[0])]
            else:
                print "invalid dcr type mapping:",
                print d
    return mapping

register_component_class(
    ebony_board_component,
    [['rtc_time', Sim_Attr_Required, 's',
      'The data and time of the Real-Time clock.']]
    + ppc440gp_soc_attributes,
    top_level = True)
