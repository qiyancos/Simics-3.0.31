# MODULE: alpha-components
# CLASS: alpha-lx164-system
# CLASS: south-bridge-saturn

import time
from sim_core import *
from components import *
from configuration import convert_to_pre_objects
from base_components import standard_pc_devices_component, find_device

BOOT_ADDR = 0x2000000
default_bios = 'lx164.milo'


### Alpha LX164 System


class alpha_lx164_system_component(component_object):
    classname = 'alpha-lx164-system'
    basename = 'system'
    description = ('The "alpha-lx164-system" component represents a '
                   'single-processor Alpha LX164 system with a Pyxis PCI '
                   'north bridge.')
    connectors = {
        'interrupt' : {'type' : 'alpha-interrupt', 'direction' : 'down',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False}}
    for i in range(5, 10):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        try:
            self.set_bios_file(default_bios)
        except:
            self.bios = None

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
        if val < 1:
            SIM_attribute_error('Unsupported memory size')
            return Sim_Set_Illegal_Value
        self.memory_megs = val
        return Sim_Set_Ok

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

    def get_bios(self, idx):
        return self.bios

    def set_bios_file(self, name):
        if not SIM_lookup_file(name):
            raise Exception, 'Could not locate bios file %s' % name
        self.bios = name
        
    def set_bios(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        try:
            self.set_bios_file(val)
        except Exception, error:
            SIM_attribute_error(error)
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def add_objects(self):
        self.o.cpu = pre_obj('cpu$', 'alpha-ev5')
        self.o.cpu.processor_number = get_next_cpu_number()
        self.o.phys_mem = pre_obj('phys_mem$', 'memory-space')
        self.o.cia = pre_obj('cia$', 'pyxis')
        self.o.ram = pre_obj('ram$', 'ram')
        self.o.ram_image = pre_obj('ram$_image', 'image')
        self.o.nvram_image = pre_obj('nvram$_image', 'image')
        self.o.nvram = pre_obj('nvram$', 'LX164-NVRAM')
        self.o.hfs = pre_obj('hfs$', 'hostfs')
        self.o.pld = pre_obj('pld$', 'LX164-IRQ-PLD')
        self.o.pci_conf = pre_obj('pci_conf$', 'memory-space')
        self.o.pci_io = pre_obj('pci_io$', 'memory-space')
        self.o.pci_mem = pre_obj('pci_mem$', 'memory-space')
        self.o.pci_bus = pre_obj('pci_bus$', 'pci-bus')
        self.o.cpu.freq_mhz = self.freq_mhz
        self.o.cpu.physical_memory = self.o.phys_mem
        self.o.ram.image = self.o.ram_image
        self.o.ram_image.size = self.memory_megs * 1024 * 1024
        self.o.nvram.image = self.o.nvram_image
        self.o.nvram_image.size = 0x100000
        self.o.pci_bus.conf_space = self.o.pci_conf
        self.o.pci_bus.io_space = self.o.pci_io
        self.o.pci_bus.memory_space = self.o.pci_mem
        self.o.pci_bus.bridge = self.o.cia
        self.o.pci_bus.interrupt = self.o.pld
        self.o.pci_bus.pci_devices = []
        self.o.pci_io.map = [
            [0x800, self.o.nvram, 1,     0, 1],
            [0x804, self.o.pld,   0,     0, 1],
            [0x805, self.o.pld,   0,     1, 1],
            [0x806, self.o.pld,   0,     2, 1]]
        self.o.pci_mem.map = [[0xfff80000, self.o.nvram,  0, 0, 0x000080000]]
        self.o.pld.cpu = self.o.cpu
        self.o.cia.pci_bus = self.o.pci_bus
        self.o.cia.pci_configuration_space = self.o.pci_conf
        self.o.cia.pci_io_space = self.o.pci_io
        self.o.cia.pci_memory_space = self.o.pci_mem
        self.o.cia.memory = self.o.phys_mem
        self.o.phys_mem.map = [
            [0x0000000000, self.o.ram,   0, 0, self.o.ram_image.size],
            [0x00ffe81000, self.o.hfs,   0, 0, 0x10],
            [0x8000000000, self.o.cia, 101, 0x8000000000, 0x400000000],
            [0x8400000000, self.o.cia, 102, 0x8400000000, 0x100000000],
            [0x8500000000, self.o.cia, 103, 0x8500000000, 0x080000000],
            [0x8580000000, self.o.cia, 104, 0x8580000000, 0x040000000],
            [0x85c0000000, self.o.cia, 105, 0x85c0000000, 0x040000000],
            [0x8600000000, self.o.cia,   6, 0x8600000000, 0x100000000,
             self.o.pci_mem],
            [0x8700000000, self.o.cia, 107, 0x8700000000, 0x020000000],
            [0x8720000000, self.o.cia,   8, 0x0000000000, 0x020000000],
            [0x8740000000, self.o.cia,   9, 0x0000000000, 0x030000000],
            [0x87a0000000, self.o.cia,  10, 0x0000000000, 0x010000000],
            [0x8800000000, self.o.cia,  11, 0x8800000000, 0x100000000,
             self.o.pci_mem],
            [0x8900000000, self.o.cia,  12, 0x8900000000, 0x100000000,
             self.o.pci_io],
            [0x8a00000000, self.o.cia, 113, 0x8A00000000, 0x100000000],
            [0x8b00000000, self.o.cia, 114, 0x8B00000000, 0x100000000]]

    def add_connector_info(self):
        self.connector_info['interrupt'] = [self.o.cpu]
        for i in range(5, 10):
            self.connector_info['pci-slot%d' % i] = [i, self.o.pci_bus]

    def instantiation_done(self):
        component_object.instantiation_done(self)
        if self.bios:
            SIM_load_file(self.o.phys_mem, self.bios, BOOT_ADDR, 0)
        else:
            print "Warning: No BIOS loaded."
        SIM_set_program_counter(self.o.cpu, BOOT_ADDR + 1)
        conf.sim.handle_outside_memory = 1
        m = re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', self.tod)
        rtc = find_device(self.o.pci_io, 0x70)
        if not rtc:
            print 'RTC device not found - can not write date/time.'
            return
        eval_cli_line(('%s.set-date-time -binary '
                       + 'year=%s month=%s mday=%s '
                       + 'hour=%s minute=%s second=%s')
                      % ((rtc.name,) + m.groups()))

    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        devs = bus.pci_devices
        for dev in device_list:
            devs += [[slot, dev[0], dev[1]]]
        bus.pci_devices = devs

    def connect_alpha_interrupt(self, connector):
        pass

    def get_clock(self):
        return self.o.cpu

    def get_processors(self):
        return [self.o.cpu]

register_component_class(
    alpha_lx164_system_component,
    [['cpu_frequency', Sim_Attr_Required, 'i',
      'Processor frequency in MHz.'],
     ['memory_megs', Sim_Attr_Required, 'i',
      'The amount of RAM in mega-bytes in the machine.'],
     ['rtc_time', Sim_Attr_Required, 's',
      'The date and time of the Real-Time clock.'],
     ['bios', Sim_Attr_Optional, 's',
      'The boot BIOS file to use.']],
    top_level = True)


### Saturn I/O South Bridge


class south_bridge_saturn_component(standard_pc_devices_component):
    classname = 'south-bridge-saturn'
    basename = 'south_bridge'
    description = ('The "south-bridge-saturn" component represents a Saturn '
                   'PCI based south bridge for use in Alpha LX164 systems. '
                   'It includes the common legacy PC devices, two IDE '
                   'controllers, a real-time clock and a floppy controller '
                   'with two drives attached.')

    connectors = standard_pc_devices_component.connectors.copy()
    connectors['interrupt'] = {
        'type' : 'alpha-interrupt', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['pci-bus'] =  {
        'type' : 'pci-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['isa-bus'] = {
        'type' : 'isa-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi' : True}

    def add_objects(self):
        standard_pc_devices_component.add_objects(self)
        self.o.pci_to_isa = pre_obj('pci_to_isa$', 'SIO82378ZB')
        self.o.pic.irq_dev = self.o.pci_to_isa
        self.o.pci_to_isa.irq_dev = self.o.pic
        self.o.fd0 = pre_obj('fd$', 'floppy-drive')
        self.o.fd1 = pre_obj('fd$', 'floppy-drive')
        self.o.flp = pre_obj('flp$', 'i82077')
        self.o.flp.dma_channel = 2
        self.o.flp.dma_dev = self.o.dma
        self.o.flp.irq_level = 6
        self.o.flp.irq_dev = self.o.isa
        self.o.flp.drives = [self.o.fd0, self.o.fd1]
        isa_map = [
            [0x3f0, self.o.flp,  0,     5, 1],
            [0x3f1, self.o.flp,  0,     5, 1],
            [0x3f2, self.o.flp,  0,     0, 1],
            [0x3f4, self.o.flp,  0,     2, 1],
            [0x3f5, self.o.flp,  0,     3, 1],
            [0x3f7, self.o.flp,  0,     5, 1]]
        used_ports = [x[0] for x in isa_map]
        for p in used_ports:
            if p in self.used_ports:
                raise Exception, "Port 0x%x already used." % p
        self.o.isa_bus.map += isa_map
        self.used_ports += used_ports
        self.connector_info['interrupt'] = []

    def add_connector_info(self):
        standard_pc_devices_component.add_connector_info(self)
        self.connector_info['pci-bus'] = [[[0, self.o.pci_to_isa]]]
        self.connector_info['isa-bus'] = [self.o.isa_bus, None, self.o.isa,
                                          self.o.dma]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.dma.memory = pci_bus.memory_space
        pci_bus.io_space.map += [[0, self.o.isa_bus, 0, 0, 0x10000, None, 2]]
        self.o.pci_to_isa.pci_bus = pci_bus
        self.connector_info['isa-bus'] = [self.o.isa_bus, pci_bus.memory_space,
                                          self.o.isa, self.o.dma]

    def check_isa_bus(self, connector, ports):
        for p in ports:
            if p in self.used_ports:
                raise Exception, "Port 0x%x already in use." % p
        self.used_ports += ports

    def connect_isa_bus(self, connector):
        pass

    def connect_alpha_interrupt(self, connector, cpu):
        self.o.rtc.irq_dev = cpu
        self.o.rtc.irq_level = 2

register_component_class(south_bridge_saturn_component, [])
