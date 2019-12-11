# MODULE: fiesta-components
# CLASS: taco-system
# CLASS: enchilada-system
# CLASS: south-bridge-sun-md1535d

import time
from sim_core import *
from components import *
from configuration import convert_to_pre_objects
from fiesta_nvram import register_nvram_commands, write_idprom_to_nvram
    
SIM_load_module('pci-components')
from pci_components import south_bridge_md1535d_component
from base_components import find_device

SIM_source_python_in_module('%s/home/scripts/flash_memory.py'
                            % conf.sim.simics_base, __name__)


### Taco/Enchilada System


class fiesta_system_component(component_object):
    connectors = {
        'i2c' : {'type' : 'i2c-bus', 'direction' : 'down',
                 'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    for i in range(4):
        connectors['ddr-slot%d' % i] = {
            'type' : 'mem-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi': False}
    for i in range(6):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    for i in ('pm', 'isa', 'ide'):
        connectors['pci-slot-%s' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : False, 'hotplug' : False, 'multi' : False}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.cpu = [None, None]
        self.o.mmu = [None, None]
        self.o.gpio_i2c_bus = [None, None]
        self.o.tomatillo = [None, None]
        self.o.pcicfgA = [None, None]
        self.o.pcicfgB = [None, None]
        self.o.pciioA = [None, None]
        self.o.pciioB = [None, None]
        self.o.pcimemA = [None, None]
        self.o.pcimemB = [None, None]
        self.o.pcibusA = [None, None]
        self.o.pcibusB = [None, None]
        self.o.i2c_dram_image = [None] * 8
        self.o.i2c_dram = [None] * 8
        self.memory_megs = [0] * 4
        self.memory_ranks = [0] * 4

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def get_num_cpus(self, idx):
        return self.num_cpus

    def set_num_cpus(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if val in [1, 2]:
            self.num_cpus = val
        else:
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_memory_megs(self, idx):
        return sum([x[1].memory_megs for x in self.connections
                    if x[0].startswith('ddr-slot')])

    def get_hostid(self, idx):
        return self.hostid

    def set_hostid(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.hostid = val
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

    def get_mac_address(self, idx):
        return self.mac

    def set_mac_address(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if len(mac_as_list(val)) != 6:
            return Sim_Set_Illegal_Value
        self.mac = val
        return Sim_Set_Ok

    def add_tomatillo(self, id, aid):
        self.o.gpio_i2c_bus[id] = pre_obj('gpio_i2c_bus%d' % aid, 'i2c-bus')
        self.o.pcicfgA[id] = pre_obj('pcicfg%dA' % aid, 'memory-space')
        self.o.pcicfgB[id] = pre_obj('pcicfg%dB' % aid, 'memory-space')
        self.o.pciioA[id] = pre_obj('pciio%dA' % aid, 'memory-space')
        self.o.pciioB[id] = pre_obj('pciio%dB' % aid, 'memory-space')
        self.o.pcimemA[id] = pre_obj('pcimem%dA' % aid, 'memory-space')
        self.o.pcimemB[id] = pre_obj('pcimem%dB' % aid, 'memory-space')
        self.o.pcibusA[id] = pre_obj('pcibus%dA' % aid, 'pci-bus')
        self.o.pcibusB[id] = pre_obj('pcibus%dB' % aid, 'pci-bus')
        self.o.tomatillo[id] = pre_obj('tomatillo%d' % aid, 'fiesta-tomatillo')
        self.o.pcibusA[id].conf_space = self.o.pcicfgA[id]
        self.o.pcibusA[id].io_space = self.o.pciioA[id]
        self.o.pcibusA[id].io_space.map = []
        self.o.pcibusA[id].memory_space = self.o.pcimemA[id]
        self.o.pcibusB[id].conf_space = self.o.pcicfgB[id]
        self.o.pcibusB[id].io_space = self.o.pciioB[id]
        self.o.pcibusB[id].io_space.map = []
        self.o.pcibusB[id].memory_space = self.o.pcimemB[id]
        self.o.tomatillo[id].memory_space = self.o.phys_mem
        self.o.tomatillo[id].io_space = self.o.phys_io
        self.o.tomatillo[id].irq_bus = self.o.irqbus
        self.o.tomatillo[id].jpid = aid
        self.o.tomatillo[id].i2c_bus = self.o.gpio_i2c_bus[id]
        self.o.tomatillo[id].pci_busA = self.o.pcibusA[id]
        self.o.tomatillo[id].pci_busB = self.o.pcibusB[id]
        self.o.pcibusA[id].bridge = self.o.tomatillo[id]
        self.o.pcibusB[id].bridge = self.o.tomatillo[id]
        # map the tomatillo
        self.o.phys_io.map += [
            [0x40000000000 + (aid          << 23), self.o.tomatillo[id],
             0, 0, 0x800000],
            [0x40000000000 + ((aid + 1) << 23), self.o.tomatillo[id],
             0, 0, 0x800000]]

    def add_i2c_bus(self, id):
        self.o.i2c_bus = pre_obj('i2c_bus', 'i2c-bus')
        self.o.seeprom_image = pre_obj('seeprom_image', 'image')
        self.o.seeprom_image.files = self.seeprom_fru_file
        self.o.seeprom_image.size = 0x4000
        self.o.seeprom = pre_obj('seeprom', 'PCF8582C')
        self.o.seeprom.i2c_bus = self.o.i2c_bus
        self.o.seeprom.image = self.o.seeprom_image
        self.o.seeprom.address_bits = 16
        self.o.seeprom.address_mask = 0x7f
        self.o.seeprom.address = self.seeprom_i2c_addr
        self.o.pci_clock = pre_obj('pci_clock', 'ICS951601')
        self.o.pci_clock.i2c_bus = self.o.i2c_bus
        self.o.pci_clock.address = 0x69
        self.o.temp = pre_obj('temp', 'ADM1031')
        self.o.temp.i2c_bus = self.o.i2c_bus
        self.o.temp.address = self.temp_i2c_addr
        #for i in range(4):
        #    self.o.i2c_dram_image[i] = pre_obj('i2c_dram$_image', 'image')
        #    self.o.i2c_dram_image[i].size = 0x2000
        #    self.o.i2c_dram[i] = pre_obj('i2c_dram$', 'PCF8582C')
        #    self.o.i2c_dram[i].i2c_bus = self.o.i2c_bus
        #    self.o.i2c_dram[i].image = self.o.i2c_dram_image[i]
        #    self.o.i2c_dram[i].address = self.dram_i2c_addr + i
        #    self.o.i2c_dram[i].address_mask = 0x7f
        if self.num_cpus == 2:
            for i in range(4, 8):
                self.o.i2c_dram_image[i] = pre_obj('i2c_dram$_image', 'image')
                self.o.i2c_dram_image[i].size = 0x2000
                self.o.i2c_dram[i] = pre_obj('i2c_dram$', 'PCF8582C')
                self.o.i2c_dram[i].i2c_bus = self.o.i2c_bus
                self.o.i2c_dram[i].image = self.o.i2c_dram_image[i]
                self.o.i2c_dram[i].address = 0x63 + i - 4
                self.o.i2c_dram[i].address_mask = 0x7f
    
    def add_objects(self):
        self.o.simicsfs = pre_obj('simicsfs', 'hostfs')
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.phys_mem.map = [[0x7fff07ffff0, self.o.simicsfs, 0, 0x0, 0x10]]
        self.o.phys_io = pre_obj('phys_io', 'memory-space')
        self.o.phys_io.map = []
        self.o.irqbus = pre_obj('irqbus', 'sparc-irq-bus')

        # one cpu, one tomatillo
        presence = 0x21L     # port 5, 0
        if self.num_cpus == 2:
            presence |= 0x02 # port 1 (only a guess)
        if self.dual_tomatillo:
            presence |= 0x40 # port 6 (only a guess)

        for i in range(self.num_cpus):
            self.o.cpu[i] = pre_obj('cpu%d' % i, 'ultrasparc-iii-i')
            self.o.mmu[i] = pre_obj('mmu%d' % i, 'jalapeno-mmu')
            self.o.cpu[i].control_registers = [
                ['mid', i],
                ['safari_config', ((presence << 51)
                                   | (presence << 44)
                                   | (i << 17))],
                ['ver', 0x3e001655000000]]
            self.o.cpu[i].cpu_group = self.o.irqbus
            self.o.cpu[i].freq_mhz = self.freq_mhz
            self.o.cpu[i].processor_number = get_next_cpu_number()
            self.o.cpu[i].system_tick_frequency = 12.0
            self.o.cpu[i].mmu = self.o.mmu[i]
            self.o.cpu[i].physical_io = self.o.phys_io
            self.o.cpu[i].physical_memory = self.o.phys_mem
            self.o.cpu[i].simicsfs = self.o.simicsfs
            self.o.phys_io.map += [
                [0x40000000000 + (i << 23), self.o.mmu[i], 0x0, 0, 0x800000]]

        self.add_tomatillo(0, 30)
        if self.dual_tomatillo:
            self.add_tomatillo(1, 28)

        # TODO: replace with new flash
        self.o.cpuprom_image = pre_obj('cpuprom_image', 'image')
        self.o.cpuprom_image.size = 0x100000
        self.o.cpuprom_image.files = self.cpuprom_files
        self.o.cpuprom_ram = pre_obj('cpuprom_ram', 'ram')
        self.o.cpuprom_ram.image = self.o.cpuprom_image
        self.o.cpuprom = pre_obj('cpuprom', 'flash-memory')
        self.o.cpuprom.cfi_compatible = 0
        self.o.cpuprom.intel_compatible = 0
        self.o.cpuprom.jedec_compatible = 0
        self.o.cpuprom.amd_compatible = 1
        self.o.cpuprom.interleave =  1
        self.o.cpuprom.bus_width =  1
        self.o.cpuprom.vendor_id =  0x1
        self.o.cpuprom.device_id =  0xd5
        self.o.cpuprom.sectors   =  16
        self.o.cpuprom.sector_size = 0x10000
        self.o.cpuprom.storage_ram =  self.o.cpuprom_ram
        self.o.pcimemA[0].map = [
            [0xf0000000, self.o.cpuprom, 0, 0, 0x100000,
             self.o.cpuprom_ram, 1, 0]]
        self.o.nvram_image = pre_obj('nvram_image', 'image')
        self.o.nvram_image.size = 0x8000
        self.o.nvram = pre_obj('nvram', 'PCF8582C')
        self.o.nvram.image = self.o.nvram_image
        self.o.nvram.address_bits = 16
        self.o.nvram.address = 0x57
        self.o.nvram.address_mask = 0x7f
        self.o.nvram.i2c_bus = self.o.gpio_i2c_bus[0]

        self.add_i2c_bus(0)

        self.o.memory_image = pre_obj('memory_image', 'image')
        self.o.memory = pre_obj('memory', 'ram')
        self.o.memory.image = self.o.memory_image

    def add_connector_info(self):
        self.connector_info['i2c'] = [self.o.i2c_bus]
        self.connector_info['pci-slot-pm'] =  [ 6, self.o.pcibusA[0]]
        self.connector_info['pci-slot-isa'] = [ 7, self.o.pcibusA[0]]
        self.connector_info['pci-slot-ide'] = [13, self.o.pcibusA[0]]
        for i in range(4):
            self.connector_info['ddr-slot%d' % i] = [self.o.i2c_bus,
                                                      self.dram_i2c_addr + i]
        if self.num_slots == 6:
            self.connector_info['pci-slot0'] = [2, self.o.pcibusA[0]]
            self.connector_info['pci-slot1'] = [3, self.o.pcibusA[0]]
            self.connector_info['pci-slot2'] = [4, self.o.pcibusA[0]]
            self.connector_info['pci-slot3'] = [5, self.o.pcibusA[0]]
            self.connector_info['pci-slot4'] = [2, self.o.pcibusB[0]] # BCM
            self.connector_info['pci-slot5'] = [3, self.o.pcibusB[0]]
        else:
            self.connector_info['pci-slot0'] = [2, self.o.pcibusA[1]]
            self.connector_info['pci-slot1'] = [3, self.o.pcibusA[1]] # BCM
            self.connector_info['pci-slot2'] = [2, self.o.pcibusB[1]]
            self.connector_info['pci-slot3'] = [4, self.o.pcibusB[1]] # SCSI
            self.connector_info['pci-slot4'] = [2, self.o.pcibusA[0]]
            self.connector_info['pci-slot5'] = [3, self.o.pcibusA[0]]
            self.connector_info['pci-slot6'] = [4, self.o.pcibusA[0]]
            self.connector_info['pci-slot7'] = [2, self.o.pcibusB[0]]

    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        try:
            devs = bus.pci_devices
        except:
            devs = []
        for dev in device_list:
            devs += [[slot, dev[0], dev[1]]]
        bus.pci_devices = devs

    def connect_i2c_bus(self, connector, device):
        pass

    def check_mem_bus(self, connector, type, memory_megs, ranks,
                      width, ecc_width):
        if width != 72:
            raise Exception, "Only 72-bit SDRAMs are supported"
        if ecc_width != 8:
            raise Exception, "Only 8-bit ECC SDRAMs are supported."
        if type != 7:
            raise Exception, "Only DDR SDRAM modules are supported"

    def connect_mem_bus(self, connector, memory_megs, ranks):
        dimm = int(connector[-1])
        self.memory_megs[dimm] = memory_megs
        self.memory_ranks[dimm] = ranks
        self.change_ram_map()

    def change_ram_map(self):
        # remove old mappings
        self.o.phys_mem.map = [m for m in self.o.phys_mem.map
                               if m[1] != self.o.memory]
        self.o.memory_image.size = sum(self.memory_megs) * 0x100000
        if sum(self.memory_ranks[2:4]) > 2:
            # more than two ranks in second pair
            banks = range(4)
        elif sum(self.memory_ranks[2:4]) > 0:
            # untested
            banks = range(3)
        elif sum(self.memory_ranks[0:2]) > 2:
            # more than two ranks in first pair
            # untested
            banks = range(2)
        else:
            banks = range(1)
        bank_space = 0x100000000
        bank_size = self.o.memory_image.size / len(banks)
        for b in banks:
            self.o.phys_mem.map += [
                [b * bank_space, self.o.memory, 0, b * bank_size, bank_size]]

    def get_clock(self):
        return self.o.cpu[0]

    def get_processors(self):
        return [x for x in self.o.cpu if x]
    
    def instantiation_done(self):
        component_object.instantiation_done(self)
        write_idprom_to_nvram(self.obj, self.hostid, self.mac)
        conf.sim.handle_outside_memory = 1
        m = re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', self.tod)
        rtc = find_device(self.o.pciioA[0], 0x70)
        if not rtc:
            print 'RTC device not found - can not write date/time.'
            return
        eval_cli_line(('%s.set-date-time -binary '
                       + 'year=%s month=%s mday=%s '
                       + 'hour=%s minute=%s second=%s')
                      % ((rtc.name,) + m.groups()))

class taco_system_component(fiesta_system_component):
    classname = 'taco-system'
    basename = 'system'
    description = ('The "taco-system" component represents a Sun Blade 1500 '
                   'single processor workstation mother-board with all '
                   'on-board devices except the south-bridge and PCI devices.'
                   '<insert id="taco-system-extras"/>')
    dual_tomatillo = 0
    cpuprom_files = [['openbootprom.ta', 'ro', 0, 0x100000]]
    seeprom_fru_file = [['885-0086-10.bin', 'ro', 0, 0x2000]]
    seeprom_i2c_addr = 0x54
    temp_i2c_addr = 0x2e
    dram_i2c_addr = 0x50
    num_cpus = 1
    num_slots = 6

class enchilada_system_component(fiesta_system_component):
    classname = 'enchilada-system'
    basename = 'system'
    description = ('The "enchilada-system" component represents a Sun Blade '
                   '2500 dual processor workstation mother-board with all '
                   'on-board devices except the south-bridge and PCI devices. '
                   'The "enchilada-system" component is currently NOT '
                   'supported in Simics')
    dual_tomatillo = 1
    cpuprom_files = [['openboot_enchilada.bin', 'ro',0, 463192]]
    seeprom_fru_file = [['885-0143-09.bin', 'ro', 0, 0x2000]]
    seeprom_i2c_addr = 0x51
    temp_i2c_addr = 0x2c
    dram_i2c_addr = 0x5b
    num_slots = 8
    connectors = fiesta_system_component.connectors.copy()
    for i in range(6, 8):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

attrs = [['cpu_frequency', Sim_Attr_Required, 'i',
          'Processor frequency in MHz.'],
         ['hostid', Sim_Attr_Required, 'i',
          'The hostid of the machine.'],
         ['mac_address', Sim_Attr_Required, 's',
          'The main MAC address is the machine.'],
         ['rtc_time', Sim_Attr_Required, 's',
          'The date and time of the Real-Time clock.'],
         ['memory_megs', Sim_Attr_Pseudo, 'i',
          'The amount of RAM in mega-bytes in the machine.']]


register_component_class(taco_system_component, attrs, top_level = True)
register_nvram_commands(taco_system_component.classname)

attrs += [['num_cpus', Sim_Attr_Required, 'i',
           'Number of processors in the sytem.']]

register_component_class(enchilada_system_component, attrs, top_level = True)
register_nvram_commands(enchilada_system_component.classname)


### Sun ALi MD1535D South Bridge


class south_bridge_sun_md1535d_component(south_bridge_md1535d_component):
    classname = 'south-bridge-sun-md1535d'
    basename = 'south_bridge'
    description = ('The "south-bridge-sun-md1535d" component represents the '
                   'ALi MD1535D south-bridge modified for use in a Fiesta '
                   '(Taco/Enchilada) system.')
    
    connectors = south_bridge_md1535d_component.connectors.copy()
    del connectors['interrupt']
    del connectors['isa-bus']
    connectors['i2c'] = {
        'type' : 'i2c-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}

    def add_objects(self):
        south_bridge_md1535d_component.add_objects(self)
        self.o.isa_bus.map = [x for x in self.o.isa_bus.map
                              if x[1] != self.o.pic]
        del self.o.pic
        # floppy not enabled
        del self.o.fd0
        del self.o.fd1
        del self.o.isa
        self.o.flp.drives = None
        self.o.flp.irq_dev = None
        self.o.flp.irq_level = 0
        self.o.sb_isa.pci_to_isa_irq = [0, 0, 0, 0]
        self.o.i2c = pre_obj('i2c', 'PCF8584')
        # use INO for simplicity
        self.o.ide0.irq_level = 0x18
        self.o.ide1.irq_level = 0x18
        self.o.rtc.irq_level  = 0x19
        self.o.com1.irq_level = 0x2c
        self.o.com2.irq_level = 0x2c
        self.o.com3.irq_level = 0x2c
        self.o.i2c.irq_level  = 0x2e
        self.o.sb_pm.show_leds = 1
        isa_map = [
            [0x320, self.o.i2c,  0, 0, 2],
            # PLL Programming
            [0x700, self.o.unknown,  0, 0, 2],  # temporary: PLL programming
            # next is unknown (perhaps not Sun specific)
            [0x77a, self.o.unknown,  0, 0, 1]]
        used_ports = [x[0] for x in isa_map]
        for p in used_ports:
            if p in self.used_ports:
                raise Exception, "Port 0x%x already used." % p
        self.o.isa_bus.map += isa_map
        self.used_ports += used_ports

    def add_connector_info(self):
        south_bridge_md1535d_component.add_connector_info(self)
        self.connector_info['i2c'] = [self.o.i2c]

    def connect_pci_bus(self, connector, slot, pci_bus):
        south_bridge_md1535d_component.connect_pci_bus(self, connector,
                                                       slot, pci_bus)
        if connector == 'pci-bus-isa':
            self.o.i2c.irq_dev = pci_bus.bridge
            self.o.rtc.irq_dev = pci_bus.bridge
            self.o.com1.irq_dev = pci_bus.bridge
            self.o.com2.irq_dev = pci_bus.bridge
            self.o.com3.irq_dev = pci_bus.bridge
            self.o.flp.irq_dev = pci_bus.bridge
            self.o.sb_isa.irq_dev = pci_bus.bridge
            self.o.ide0.irq_dev = pci_bus.bridge
            self.o.ide1.irq_dev = pci_bus.bridge
            self.o.pit.irq_dev = pci_bus.bridge

    def connect_i2c_bus(self, connector, bus):
        self.o.i2c.i2c_bus = bus

register_component_class(south_bridge_sun_md1535d_component, [])
