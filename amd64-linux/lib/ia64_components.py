# MODULE: ia64-components
# CLASS: ia64-460gx-system
# CLASS: itanium-cpu

import time
from sim_core import *
from components import *
from configuration import convert_to_pre_objects
from base_components import standard_pc_devices_component, find_device

MAX_CPUS = 32


### IA64 System Based on the 460GX Chipset


class ia64_460gx_system_component(component_object):
    classname = 'ia64-460gx-system'
    basename = 'system'
    description = ('The "ia64-460gx-system" component represents a system '
                   'based on the Itanium processor with the 460GX chipset')
    connectors = {'isa-bus' : {
        'type' : 'isa-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi' : True}}
    for i in range(MAX_CPUS):
        connectors['cpu%d' % i] = {
            'type' : 'ia64-cpu', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    for i in range(2, 24):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.cpu_list = [None] * MAX_CPUS

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

    def get_processor_list(self, idx):
        return self.cpu_list

    def set_processor_list(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.cpu_list = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.rom_image = pre_obj('rom$_image', 'image')
        self.o.rom = pre_obj('rom$', 'ram')
        self.o.rom_image.size = 0x800000
        self.o.rom.image = self.o.rom_image
        self.o.ram_image = pre_obj('mem$_image', 'image')
        self.o.ram = pre_obj('ram$', 'ram')
        self.o.ram_image.size = self.memory_megs * 1024 * 1024
        self.o.ram.image = self.o.ram_image
        self.o.lpc_space = pre_obj('lpc_space', 'port-space')
        self.o.sac = pre_obj('sac', 'i82461GX')
        self.o.pid = pre_obj('pid', 'uPD66566S1016')
        self.o.sapic_bus = pre_obj('sapic_bus', 'sapic-bus')
        self.o.io_space = pre_obj('io_space$', 'memory-space')
        self.o.pci_conf = pre_obj('pcicfg$', 'memory-space')
        self.o.pci_io = pre_obj('pciio$', 'memory-space')
        self.o.pci_mem = pre_obj('pcimem$', 'memory-space')
        self.o.pci_bus = pre_obj('pci_bus$', 'pci-bus')
        self.o.pci_bus.bridge = self.o.sac
        self.o.pci_bus.interrupt = self.o.pid
        self.o.pci_bus.conf_space = self.o.pci_conf
        self.o.pci_bus.io_space = self.o.pci_io
        self.o.pci_bus.memory_space = self.o.pci_mem
        self.o.pci_io.map = []
        self.o.pci_mem.map = []
        lomem = min(self.memory_megs * 1024 * 1024, 0x80000000)
        himem = max(self.memory_megs * 1024 * 1024 - 0x80000000, 0)
        self.o.phys_mem.map = [
            [0x000000000000, self.o.ram, 0, 0,     lomem, None, 1],
            [0x0000000a0000, self.o.pci_mem, 0, 0xa0000, 0x20000],
            [0x0000fec00000, self.o.pid, 0, 0,    0x1000],
            [0x0000ff800000, self.o.rom, 0, 0,  0x800000],
            [0x0ffffc000000, self.o.sac, 0, 0, 0x4000000, self.o.io_space]]
        if himem > 0:
            self.o.phys_mem.map += [
                [0x000100000000, self.o.ram, 0, 0x80000000, himem, None, 0]]
        # TODO: get comment from ia64_conf.py
        gap_chunksize = 0x4000000
        self.o.phys_mem.map += [
            [0xfe000000 - gap_chunksize, self.o.sac,
             3, 0, gap_chunksize, self.o.pci_mem]]
        #
        self.o.sac.physical_memory = self.o.phys_mem
        self.o.sac.io_space = self.o.io_space
        # TODO: list all pci-buses
        self.o.sac.pci_buses = [[self.o.pci_bus, 0]]
        self.o.pid.pci_bus = self.o.pci_bus
        self.o.pid.sapic_bus = self.o.sapic_bus
        self.o.sapic_bus.iosapic = self.o.pid
        self.o.sapic_bus.sapics = []
        # this is hopefully the same routing table as
        # \_SB_.PCI0._PRT of the DSDT of godzilla
        self.o.pid.pci_rt = [[1, -1, 0, 0x23],
                             [1, -1, 1, 0x22],
                             [1, -1, 2, 0x21],
                             [1, -1, 3, 0x20],
                             [2, -1, 0, 0x27],
                             [2, -1, 1, 0x26],
                             [2, -1, 2, 0x25],
                             [2, -1, 3, 0x24],
                             [4, -1, 0, 0x2b],
                             [4, -1, 1, 0x2a],
                             [4, -1, 2, 0x29],
                             [4, -1, 3, 0x28],
                             [3, -1, 0, 0x2e],
                             [3, -1, 1, 0x2e],
                             [3, -1, 2, 0x2f],
                             [3, -1, 3, 0x2f]]
        self.o.io_space.map = [
            [0x00000000, self.o.lpc_space,  0, 0, 0xcf8],
            [0x00000cf8, self.o.sac,        0, 0, 0x008],
            # TODO: map space directly instead, only bus 0?
            [0x00001000, self.o.pci_bus, 1, 0, 0x1000000]]
        self.add_lpc_objects()
        self.o.pci_bus.pci_devices = [[0, 0, self.o.ifb], [1, 0, self.o.pid]]

    def add_lpc_objects(self):
        self.o.ifb = pre_obj('ifb$', 'i82468GX_0')
        self.o.ifb.iosapic = self.o.pid
        self.o.ifb.pci_bus = self.o.pci_bus
        self.o.pit = pre_obj('pic$', 'i8254')
        self.o.pit.irq_dev = self.o.ifb
        self.o.pit.irq_level = 0
        self.o.pit.gate = [1, 1, 0, 0]
        self.o.pit.out = [1, 1, 1, 0]
        self.o.rtc= pre_obj('rtc$', 'DS12887')
        self.o.rtc.irq_level = 8
        self.o.rtc.irq_dev = self.o.ifb
        self.o.lpc_space.map = [
            [0x40, self.o.pit, 0, 0, 1],
            [0x41, self.o.pit, 0, 1, 1],
            [0x42, self.o.pit, 0, 2, 1],
            [0x43, self.o.pit, 0, 3, 1],
            [0x70, self.o.rtc, 0, 0, 1],
            [0x71, self.o.rtc, 0, 1, 1]]
        self.used_ports = [x[0] for x in self.o.lpc_space.map]

    def add_connector_info(self):
        for i in range(MAX_CPUS):
            self.connector_info['cpu%d' % i] = [i, self.o.phys_mem]
        for i in range(2, 24):
            self.connector_info['pci-slot%d' % i] = [i, self.o.pci_bus]
        self.connector_info['isa-bus'] = [self.o.lpc_space, self.o.pci_mem,
                                          self.o.ifb, None]

    def instantiation_done(self):
        component_object.instantiation_done(self)
        for c in range(len(self.cpu_list)):
            if self.cpu_list[c]:
                self.cpu_list[c] = SIM_get_object(self.cpu_list[c].name)
        m = re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', self.tod)
        eval_cli_line(('%s.set-date-time -binary '
                       + 'year=%s month=%s mday=%s '
                       + 'hour=%s minute=%s second=%s')
                      % ((self.o.rtc.name,) + m.groups()))

    def connect_ia64_cpu(self, connector, cpu):
        id = self.connector_info[connector][0]
        self.cpu_list[id] = cpu
        self.o.phys_mem.map += [
            [0xfee00000 + id * 0x1000, cpu, 1, 0, 0x100],
            [0xff000000 + id *  0x100, cpu, 0, 0, 0x100]]
        self.o.sapic_bus.sapics += [cpu]

    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        devs = bus.pci_devices
        for dev in device_list:
            devs += [[slot, dev[0], dev[1]]]
        bus.pci_devices = devs

    def check_isa_bus(self, connector, ports):
        for p in ports:
            if p in self.used_ports:
                raise Exception, "Port 0x%x already in use." % p
        self.used_ports += ports

    def connect_isa_bus(self, connector):
        pass

    def get_clock(self):
        for i in range(MAX_CPUS):
            if self.cpu_list[i]:
                return self.cpu_list[i]
        return None

    def get_processors(self):
        return [x for x in self.cpu_list if x]

register_component_class(
    ia64_460gx_system_component,
    [['memory_megs', Sim_Attr_Required, 'i',
      'The amount of RAM in mega-bytes in the machine.'],
     ['rtc_time', Sim_Attr_Required, 's',
      'The date and time of the Real-Time clock.']],
    [['processor_list', Sim_Attr_Optional, '[o|n{' + str(MAX_CPUS) + '}]',
      'Processors connected to the system.']],
    top_level = True)


### TODO: cpu


class itanium_cpu_component(component_object):
    classname = 'itanium-cpu'
    basename = 'cpu'
    description = ('The "itanium-cpu" component represents an Itanium processor')
    connectors = {'backplane' : {
        'type' : 'ia64-cpu', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.cpu = pre_obj('cpu$', 'ia64-itanium')
        self.o.cpu.processor_number = get_next_cpu_number()
        self.o.cpu.freq_mhz = self.freq_mhz
        self.o.cpu.proc_ratio = [1, 1]
        self.o.cpu.itc_ratio = [1, 1]
        self.component_queue = self.o.cpu

    def add_connector_info(self):
        self.connector_info['backplane'] = [self.o.cpu]

    def connect_ia64_cpu(self, connector, id, phys_mem):
        self.o.cpu.physical_memory = phys_mem

register_component_class(itanium_cpu_component,
                         [['cpu_frequency', Sim_Attr_Required, 'i',
                           'Processor frequency in MHz.']])

