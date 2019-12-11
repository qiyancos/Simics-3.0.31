from components import *

# Use the DS12887-dml class instead of the DS12887 class if True.
# Unsupported feature.
use_DS12887_dml = False

def get_highest_2exp(i):
    for b in range(63, -1, -1):
        if (1 << b) <= i:
            return 1 << b
    return 0

def find_device(space, offset):
    devs = [x for x in space.map if x[0] <= offset and (x[0] + x[4]) > offset]
    if len(devs):
        if devs[0][1].classname in ('port-space', 'memory-space'):
            return find_device(devs[0][1], offset)
        return devs[0][1]
    if space.default_target:
        return find_device(space.default_target[0], offset)


### Standard PC Devices, base class for South Bridges and Legacy PC Devices


class standard_pc_devices_component(component_object):
    connectors = {
        'ide0-master': {'type' : 'ide-slot', 'direction' : 'down',
                        'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'ide0-slave' : {'type' : 'ide-slot', 'direction' : 'down',
                        'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'ide1-master': {'type' : 'ide-slot', 'direction' : 'down',
                        'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'ide1-slave' : {'type' : 'ide-slot', 'direction' : 'down',
                        'empty_ok' : True, 'hotplug' : False, 'multi' : False}}

    # self.o.dma.memory must be set by sub-class

    def add_objects(self):
        self.o.pic = pre_obj('pic$', 'i8259x2')
        self.o.isa = pre_obj('isa$', 'ISA')
        self.o.isa.pic = self.o.pic
        # The following table is only used when isa is connected to an IO-APIC
        self.o.isa.irq_to_pin = [2,   1,  0,  3,  4,  5,  6,  7,  8,  9,
                                 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                                 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
                                 30, 31]
        self.o.isa_bus = pre_obj('isa_bus$', 'port-space')
        self.o.pit = pre_obj('pit$', 'i8254')
        self.o.pit.irq_level = 0
        self.o.pit.gate = [1, 1, 0, 0]
        self.o.pit.out = [1, 1, 1, 0]
        self.o.pit.irq_dev = self.o.isa
        self.o.dma = pre_obj('dma$', 'i8237x2')
        if use_DS12887_dml:
                self.o.rtc= pre_obj('rtc$', 'DS12887-dml')
                self.o.rtc.registers_a = 0x20
                self.o.rtc.registers_b = 0x02
        else:
                self.o.rtc= pre_obj('rtc$', 'DS12887')
        self.o.rtc.irq_level = 8
        self.o.rtc.irq_dev = self.o.isa
        self.o.ide0 = pre_obj('ide$', 'ide')
        self.o.ide0.irq_dev = self.o.isa
        self.o.ide0.primary = 1
        self.o.ide0.irq_level = 14
        self.o.ide0.interrupt_delay = 1.0e-5
        self.o.ide1 = pre_obj('ide$', 'ide')
        self.o.ide1.irq_dev = self.o.isa
        self.o.ide1.primary = 0
        self.o.ide1.irq_level = 15
        self.o.ide1.interrupt_delay = 1.0e-5
        self.o.isa_bus.map = [
            [0x000, self.o.dma,  0, 0, 1],
            [0x001, self.o.dma,  0, 1, 1],
            [0x002, self.o.dma,  0, 2, 1],
            [0x003, self.o.dma,  0, 3, 1],
            [0x004, self.o.dma,  0, 4, 1],
            [0x005, self.o.dma,  0, 5, 1],
            [0x006, self.o.dma,  0, 6, 1],
            [0x007, self.o.dma,  0, 7, 1],
            [0x008, self.o.dma,  0, 8, 1],
            [0x00a, self.o.dma,  0, 0xa, 1],
            [0x00b, self.o.dma,  0, 0xb, 1],
            [0x00c, self.o.dma,  0, 0xc, 1],
            [0x00d, self.o.dma,  0, 0xd, 1],
            [0x00e, self.o.dma,  0, 0xe, 1],
            [0x020, self.o.pic,  0,  0x20, 1],
            [0x021, self.o.pic,  0,  0x21, 1],
            [0x040, self.o.pit,  0, 0, 1],
            [0x041, self.o.pit,  0, 1, 1],
            [0x042, self.o.pit,  0, 2, 1],
            [0x043, self.o.pit,  0, 3, 1],
            [0x061, self.o.pit,  1, 0, 1],
            [0x070, self.o.rtc,  0, 0, 1],
            [0x071, self.o.rtc,  0, 1, 1],   
            [0x081, self.o.dma,  0, 0x81, 1],
            [0x082, self.o.dma,  0, 0x82, 1],
            [0x083, self.o.dma,  0, 0x83, 1],
            [0x084, self.o.dma,  0, 0x84, 1],
            [0x085, self.o.dma,  0, 0x85, 1],
            [0x086, self.o.dma,  0, 0x86, 1],
            [0x087, self.o.dma,  0, 0x87, 1],
            [0x088, self.o.dma,  0, 0x88, 1],
            [0x089, self.o.dma,  0, 0x89, 1],
            [0x08a, self.o.dma,  0, 0x8a, 1],
            [0x08b, self.o.dma,  0, 0x8b, 1],
            [0x08c, self.o.dma,  0, 0x8c, 1],
            [0x08d, self.o.dma,  0, 0x8d, 1],
            [0x08e, self.o.dma,  0, 0x8e, 1],
            [0x08f, self.o.dma,  0, 0x8f, 1],
            [0x0a0, self.o.pic,  0, 0xa0, 1],
            [0x0a1, self.o.pic,  0, 0xa1, 1],
            [0x0c0, self.o.dma,  0, 0xc0, 1],
            [0x0c2, self.o.dma,  0, 0xc2, 1],
            [0x0c4, self.o.dma,  0, 0xc4, 1],
            [0x0c6, self.o.dma,  0, 0xc6, 1],
            [0x0c8, self.o.dma,  0, 0xc8, 1],
            [0x0ca, self.o.dma,  0, 0xca, 1],
            [0x0cc, self.o.dma,  0, 0xcc, 1],
            [0x0ce, self.o.dma,  0, 0xce, 1],
            [0x0d0, self.o.dma,  0, 0xd0, 1],
            [0x0d4, self.o.dma,  0, 0xd4, 1],
            [0x0d6, self.o.dma,  0, 0xd6, 1],
            [0x0d8, self.o.dma,  0, 0xd8, 1],
            [0x0da, self.o.dma,  0, 0xda, 1],
            [0x0dc, self.o.dma,  0, 0xdc, 1],
            [0x170, self.o.ide1, 0,   0x0, 4],
            [0x171, self.o.ide1, 0,   0x1, 1],
            [0x172, self.o.ide1, 0,   0x2, 1],
            [0x173, self.o.ide1, 0,   0x3, 1],
            [0x174, self.o.ide1, 0,   0x4, 1],
            [0x175, self.o.ide1, 0,   0x5, 1],
            [0x176, self.o.ide1, 0,   0x6, 1],
            [0x177, self.o.ide1, 0,   0x7, 1],
            [0x1f0, self.o.ide0, 0,   0x0, 4],
            [0x1f1, self.o.ide0, 0,   0x1, 1],
            [0x1f2, self.o.ide0, 0,   0x2, 1],
            [0x1f3, self.o.ide0, 0,   0x3, 1],
            [0x1f4, self.o.ide0, 0,   0x4, 1],
            [0x1f5, self.o.ide0, 0,   0x5, 1],
            [0x1f6, self.o.ide0, 0,   0x6, 1],
            [0x1f7, self.o.ide0, 0,   0x7, 1],
            [0x376, self.o.ide1, 0,   0x8, 1],
            [0x3f6, self.o.ide0, 0,   0x8, 1],
            [0x4d0, self.o.pic,  0, 0x4d0, 1],
            [0x4d1, self.o.pic,  0, 0x4d1, 1]]
        self.used_ports = [x[0] for x in self.o.isa_bus.map]

    def add_connector_info(self):
        self.connector_info['ide0-master'] = []
        self.connector_info['ide0-slave'] = []
        self.connector_info['ide1-master'] = []
        self.connector_info['ide1-slave'] = []

    def connect_ide_slot(self, connector, dev):
        if '0' in connector:
            ide = self.o.ide0
        else:
            ide = self.o.ide1
        if 'master' in connector:
            ide.master = dev
        else:
            ide.slave = dev


### DEC 21xxx Ethernet Adapters


class pci_dec21xxx_component(component_object):
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet' : {'type' : 'ethernet-link', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.bios = None

    def get_bios(self, idx):
        return self.bios

    def set_bios(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if not SIM_lookup_file(val):
            SIM_attribute_error('Could not locate bios file %s' % val)
            return Sim_Set_Illegal_Value
        self.bios = val
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

    def add_objects(self):
        self.o.dec = pre_obj('dec$', self.confclass)
        self.o.dec.mac_address = mac_as_list(self.mac)
        if self.bios:
            biossize = os.path.getsize(SIM_lookup_file(self.bios))
            map_size = get_highest_2exp(biossize - 1) << 1
            self.o.prom_image = pre_obj('prom$_image', 'image')
            self.o.prom_image.size = map_size
            self.o.prom_image.files = [[self.bios, 'ro', 0, biossize]]
            self.o.prom = pre_obj('prom$', 'rom')
            self.o.prom.image = self.o.prom_image
            self.o.dec.expansion_rom = [self.o.prom, map_size, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.dec]]]
        self.connector_info['ethernet'] = []

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.dec.pci_bus = pci_bus

    def connect_ethernet_link(self, connector, link):
        self.o.dec.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.dec.link = None

class pci_dec21041_component(pci_dec21xxx_component):
    classname = 'pci-dec21041'
    basename = 'eth_adapter'
    description = ('The "pci-dec21041" component represents a DEC21041 '
                   'PCI based fast Ethernet adapter.')
    confclass = 'DEC21041'

class pci_dec21140a_component(pci_dec21xxx_component):
    classname = 'pci-dec21140a'
    basename = 'eth_adapter'
    description = ('The "pci-dec21140a" component represents a DEC21140A '
                   'PCI based fast Ethernet adapter.')
    confclass = 'DEC21140A'

class pci_dec21143_component(pci_dec21xxx_component):
    classname = 'pci-dec21143'
    basename = 'eth_adapter'
    description = ('The "pci-dec21143" component represents a DEC21143 '
                   'PCI based fast Ethernet adapter.')
    confclass = 'DEC21143'

def register_dec21xxx_component_class(cl):
    register_component_class(
        cl, [['mac_address', Sim_Attr_Required, 's',
              'The MAC address of the Ethernet adapter.'],
             ['bios', Sim_Attr_Optional, 's',
              'The x86 BIOS file to use.']])
