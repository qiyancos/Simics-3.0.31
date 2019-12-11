# MODULE: pci-components
# CLASS: pci-sym53c810
# CLASS: pci-sym53c875
# CLASS: pci-sym53c876
# CLASS: pci-isp1040
# CLASS: pci-isp2200
# CLASS: pci-bcm5703c
# CLASS: pci-bcm5704c
# CLASS: pci-dec21041
# CLASS: pci-dec21140a
# CLASS: pci-dec21143
# CLASS: pci-dec21140a-dml
# CLASS: pci-i82543gc
# CLASS: pci-i82546bg
# CLASS: pci-am79c973
# CLASS: pci-vga
# CLASS: pci-voodoo3
# CLASS: agp-voodoo3
# CLASS: pci-ragexl
# CLASS: pci-rage-pm-mobility-pci
# CLASS: pci-i21152
# CLASS: pci-pd6729
# CLASS: pci-pmc1553-bc
# CLASS: south-bridge-piix4
# CLASS: south-bridge-6300esb
# CLASS: south-bridge-md1535d
# CLASS: south-bridge-amd8111
# CLASS: pci-backplane
# CLASS: pcie-pex8524
# CLASS: pci-sil680a

# TODO: rage

import os
from sim_core import *
from components import *
from base_components import *

SIM_source_python_in_module('%s/home/scripts/flash_memory.py'
                            % conf.sim.simics_base, __name__)


### SYM53C810/SYM53C875 SCSI Controllers


class pci_sym53c8xx_component(component_object):
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'scsi-bus' : {'type' : 'scsi-bus', 'direction' : 'down',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

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
        self.biossize = os.stat(SIM_lookup_file(val)).st_size
        self.bios = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.sym = pre_obj('sym$', self.confclass)
        if self.bios:
            map_size = get_highest_2exp(self.biossize - 1) << 1
            self.o.sym_prom_image = pre_obj('symprom$_image', 'image')
            self.o.sym_prom_image.size = map_size
            self.o.sym_prom_image.files = [[self.bios, 'ro', 0, self.biossize]]
            self.o.sym_prom = pre_obj('symprom$', 'rom')
            self.o.sym_prom.image = self.o.sym_prom_image
            self.o.sym.expansion_rom = [self.o.sym_prom, map_size, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.sym]]]
        self.connector_info['scsi-bus'] = [self.o.sym, 7]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.sym.pci_bus = pci_bus

    def connect_scsi_bus(self, connector, bus):
        self.o.sym.scsi_bus = bus

class pci_sym53c810_component(pci_sym53c8xx_component):
    classname = 'pci-sym53c810'
    basename = 'scsi'
    description = ('The "pci-sym53C810" component represents a SYM53C810'
                   'PCI based SCSI controller.')
    confclass = 'SYM53C810'

class pci_sym53c875_component(pci_sym53c8xx_component):
    classname = 'pci-sym53c875'
    basename = 'scsi'
    description = ('The "pci-sym53C875" component represents a SYM53C875'
                   'PCI based SCSI controller.')
    confclass = 'SYM53C875'

for model in ('sym53c810', 'sym53c875'):
    register_component_class(eval('pci_%s_component' % model),
                             [['bios', Sim_Attr_Optional, 's',
                               'The x86 SCSI BIOS file to use.']])


### SYM53C876 Dual SCSI Controller


class pci_sym53c876_component(component_object):
    classname = 'pci-sym53c876'
    basename = 'scsi'
    description = ('The "pci-sym53C876" component represents a SYM53C876'
                   'PCI based dual-port SCSI controller.')
    connectors = {
        'pci-bus'   : {'type' : 'pci-bus', 'direction' : 'up',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'scsi-bus0' : {'type' : 'scsi-bus', 'direction' : 'down',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'scsi-bus1' : {'type' : 'scsi-bus', 'direction' : 'down',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def add_objects(self):
        self.o.sym0 = pre_obj('sym$', 'SYM53C876')
        self.o.sym1 = pre_obj('sym$', 'SYM53C876')

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.sym0], [1, self.o.sym1]]]
        self.connector_info['scsi-bus0'] = [self.o.sym0, 7]
        self.connector_info['scsi-bus1'] = [self.o.sym1, 7]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.sym0.pci_bus = pci_bus
        self.o.sym1.pci_bus = pci_bus

    def connect_scsi_bus(self, connector, bus):
        if connector == 'scsi-bus0':
            self.o.sym0.scsi_bus = bus
        else:
            self.o.sym1.scsi_bus = bus

register_component_class(pci_sym53c876_component, [])


### ISP 1040 SCSI Controller


class pci_isp1040_component(component_object):
    classname = 'pci-isp1040'
    basename = 'scsi'
    description = ('The "pci-isp1040" component represents an ISP1040 '
                   'PCI based SCSI controller.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'scsi-bus' : {'type' : 'scsi-bus', 'direction' : 'down',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.bios = None
        self.scsi_id = 7

    def get_bios(self, idx):
        return self.bios

    def set_bios(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if not SIM_lookup_file(val):
            SIM_attribute_error('Could not locate bios file %s' % val)
            return Sim_Set_Illegal_Value
        self.biossize = os.stat(SIM_lookup_file(val)).st_size
        self.bios = val
        return Sim_Set_Ok

    def get_scsi_id(self, idx):
        return self.scsi_id

    def set_scsi_id(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.scsi_id = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.isp = pre_obj('isp$', 'ISP1040')
        self.o.isp.scsi_id = self.scsi_id
        if self.bios:
            map_size = get_highest_2exp(self.biossize - 1) << 1
            self.o.isp_prom_image = pre_obj('ispprom$_image', 'image')
            self.o.isp_prom_image.size = map_size
            self.o.isp_prom_image.files = [[self.bios, 'ro', 0, self.biossize]]
            self.o.isp_prom = pre_obj('ispprom$', 'rom')
            self.o.isp_prom.image = self.o.isp_prom_image
            self.o.isp.expansion_rom = [self.o.isp_prom, map_size, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.isp]]]
        self.connector_info['scsi-bus'] = [self.o.isp, self.scsi_id]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.isp.pci_bus = pci_bus

    def connect_scsi_bus(self, connector, bus):
        self.o.isp.scsi_bus = bus

register_component_class(
    pci_isp1040_component,
    [['scsi_id', Sim_Attr_Optional, 'i',
      'The ID on the SCSI bus.'],
     ['bios', Sim_Attr_Optional, 's',
      'The x86 SCSI BIOS file to use.']])


### ISP 2200 SCSI Fibre-Channel Controller


class pci_isp2200_component(component_object):
    classname = 'pci-isp2200'
    basename = 'scsi'
    description = ('The "pci-isp2200" component represents an ISP2200 '
                   'PCI based Fibre-Channel SCSI controller.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'fc-loop' : {'type' : 'simple-fc-loop', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : False, 'multi' : True}}

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
        self.biossize = os.stat(SIM_lookup_file(val)).st_size
        self.bios = val
        return Sim_Set_Ok

    def get_loop_id(self, idx):
        return self.loop_id

    def set_loop_id(self, val, idx):
        self.loop_id = val
        return Sim_Set_Ok

    def add_objects(self):
        self.used_loops = [self.loop_id]
        self.o.qlc = pre_obj('qlc$', 'ISP2200')
        self.o.qlc.loop_id = self.loop_id
        if self.bios:
            map_size = get_highest_2exp(self.biossize - 1) << 1
            self.o.qlc_prom_image = pre_obj('qlcprom$_image', 'image')
            self.o.qlc_prom_image.size = map_size
            self.o.qlc_prom_image.files = [[self.bios, 'ro', 0, self.biossize]]
            self.o.qlc_prom = pre_obj('qlcprom$', 'rom')
            self.o.qlc_prom.image = self.o.qlc_prom_image
            self.o.qlc.expansion_rom = [self.o.qlc_prom, map_size, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.qlc]]]
        self.connector_info['fc-loop'] = [self.o.qlc]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.qlc.pci_bus = pci_bus

    def check_simple_fc_loop(self, connector, info):
        if info >= 127:
            raise Exception, "Illegal loop ID 0x%x." % info
        if info in self.used_loops:
            raise Exception, "Loop ID 0x%x already in use." % info
        self.used_loops += [info]

    def connect_simple_fc_loop(self, connector, device, loop_id):
        pass

register_component_class(
    pci_isp2200_component,
    [['loop_id', Sim_Attr_Required, 'i',
      'The FC loop ID of the ISP2200 Fibre-Channel controller.'],
     ['bios', Sim_Attr_Optional, 's',
      'The x86 SCSI BIOS file to use.']])


### Broadcom 5703C Ethernet Adapter


class pci_bcm5703c_component(component_object):
    classname = 'pci-bcm5703c'
    basename = 'eth_adapter'
    description = ('The "pci-bcm5703c" component represents a Broadcom '
                   '5703C PCI based gigabit Ethernet adapter.')
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
        self.o.bge = pre_obj('bge$', 'BCM5703C')
        self.o.bge.mac_address = mac_as_list(self.mac)
        if self.bios:
            biossize = os.path.getsize(SIM_lookup_file(self.bios))
            map_size = get_highest_2exp(biossize - 1) << 1
            self.o.prom_image = pre_obj('prom$_image', 'image')
            self.o.prom_image.size = map_size
            self.o.prom_image.files = [[self.bios, 'ro', 0, biossize]]
            self.o.prom = pre_obj('prom$', 'rom')
            self.o.prom.image = self.o.prom_image
            self.o.bge.expansion_rom = [self.o.prom, map_size, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.bge]]]
        self.connector_info['ethernet'] = []

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.bge.pci_bus = pci_bus

    def connect_ethernet_link(self, connector, link):
        self.o.bge.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.bge.link = None

register_component_class(
    pci_bcm5703c_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.'],
     ['bios', Sim_Attr_Optional, 's',
      'The x86 BIOS file to use.']])


### Broadcom 5704C Dual Ethernet Adapter


class pci_bcm5704c_component(component_object):
    classname = 'pci-bcm5704c'
    basename = 'eth_adapter'
    description = ('The "pci-bcm5704c" component represents a Broadcom '
                   '5704C PCI based dual-port gigabit Ethernet adapter.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet0' : {'type' : 'ethernet-link', 'direction' : 'down',
                       'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'ethernet1' : {'type' : 'ethernet-link', 'direction' : 'down',
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
        self.o.bge0 = pre_obj('bge$', 'BCM5704C')
        self.o.bge0.mac_address = mac_as_list(self.mac0)
        self.o.bge0.is_mac1 = 0
        self.o.bge1 = pre_obj('bge$_1', 'BCM5704C')
        self.o.bge1.mac_address = mac_as_list(self.mac1)
        self.o.bge1.is_mac1 = 1
        self.o.bge0.other_bcm = self.o.bge1
        self.o.bge1.other_bcm = self.o.bge0
        if self.bios:
            biossize = os.path.getsize(SIM_lookup_file(self.bios))
            map_size = get_highest_2exp(biossize - 1) << 1
            self.o.prom_image = pre_obj('prom$_image', 'image')
            self.o.prom_image.size = map_size
            self.o.prom_image.files = [[self.bios, 'ro', 0, biossize]]
            self.o.prom = pre_obj('prom$', 'rom')
            self.o.prom.image = self.o.prom_image
            self.o.bge0.expansion_rom = [self.o.prom, map_size, 0]
        
    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.bge0], [1, self.o.bge1]]]
        self.connector_info['ethernet0'] = []
        self.connector_info['ethernet1'] = []

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.bge0.pci_bus = pci_bus
        self.o.bge1.pci_bus = pci_bus

    def connect_ethernet_link(self, connector, link):
        if connector == 'ethernet0':
            self.o.bge0.link = link
        else:
            self.o.bge1.link = link

    def disconnect_ethernet_link(self, connector):
        if connector == 'ethernet0':
            self.o.bge0.link = None
        else:
            self.o.bge1.link = None

register_component_class(
    pci_bcm5704c_component,
    [['mac_address0', Sim_Attr_Required, 's',
      'The MAC address of the first Ethernet adapter.'],
     ['mac_address1', Sim_Attr_Required, 's',
      'The MAC address of the second Ethernet adapter.'],
     ['bios', Sim_Attr_Optional, 's',
      'The x86 BIOS file to use.']])


### Intel 82543 Ethernet Adapter


class pci_i82543gc_component(component_object):
    classname = 'pci-i82543gc'
    basename = 'eth_adapter'
    description = ('The "pci-i82543gc" component represents an Intel 82543 '
                   '(Intel PRO) PCI based gigabit Ethernet adapter.')
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
        return self.mac_address

    def set_mac_address(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if len(mac_as_list(val)) != 6:
            return Sim_Set_Illegal_Value
        self.mac_address = val
        return Sim_Set_Ok

    def calculate_csum(self, data):
        # After adding the 16-bit words 0x00 to 0x3F, the sum should be
        # 0xBABA after masking off the carry bits.
        sum = 0
        for i, x in enumerate(data):
            if i&1: sum += x
            else:   sum += x << 8
        sum = 0xbaba - sum
        return ((sum & 0xff00) >> 8, sum & 0xff)

    def add_objects(self):
        self.o.mac = pre_obj('mac$', 'i82543')
        self.o.mac.STATUS = 0
        if self.bios:
            biossize = os.path.getsize(SIM_lookup_file(self.bios))
            map_size = get_highest_2exp(biossize - 1) << 1
            self.o.prom_image = pre_obj('prom$_image', 'image')
            self.o.prom_image.size = map_size
            self.o.prom_image.files = [[self.bios, 'ro', 0, biossize]]
            self.o.prom = pre_obj('prom$', 'rom')
            self.o.prom.image = self.o.prom_image
            self.o.mac.expansion_rom = [self.o.prom, map_size, 0]

        # EEPROM
        self.o.eeprom = pre_obj('eth_eeprom$', "microwire-eeprom")
        self.o.eeprom.width = 16
        self.o.eeprom.size  = 1024
        ma = mac_as_list(self.mac_address)
        eeprom_data = (ma[1], ma[0], ma[3], ma[2], ma[5], ma[4], 0, 0,
                       0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0,    0,    0,    0, 0x44, 0x08, 0x80, 0x86,
                       0x80, 0x86, 0x10, 0x79, 0x80, 0x86,    0,    0,
                       0x00, 0x00, 0x10, 0x08,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,

                       0x00, 0x00, 0x78, 0x63, 0x28, 0x0c, 0x00, 0xc8,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0)
        eeprom_data = eeprom_data + self.calculate_csum(eeprom_data)
        assert self.calculate_csum(eeprom_data) == (0, 0)
        self.o.eeprom.data = eeprom_data
        self.o.mac.eeprom = self.o.eeprom

        # PHYs
        self.o.phy = pre_obj('phy$', 'eth-transceiver')
        # define M88E1011_I_PHY_ID  0x01410C20
        self.o.phy.phyidr1 = 0x0141
        self.o.phy.phyidr2 = 0x0c20
        # link up
        self.o.phy.registers = [0]*32
        self.o.phy.registers[1] = 0x794d
        self.o.mac.phy_device = self.o.phy

        # speed selection
        self.o.phy.speed = 1000
        self.o.mac.tx_bandwidth = 1000000000

    def connect_ethernet_link(self, connector, link):
        self.o.mac.link = link
        self.o.phy.link_up = 1
        self.o.phy.full_duplex = 1

    def disconnect_ethernet_link(self, connector):
        self.o.mac.link = None
        self.o.phy.link_up = 0
        self.o.phy.full_duplex = 0

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.mac.pci_bus = pci_bus

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [
            [[0, self.o.mac]]]
        self.connector_info['ethernet'] = []

register_component_class(
    pci_i82543gc_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.'],
     ['bios', Sim_Attr_Optional, 's',
      'The x86 BIOS file to use.']])


### Intel 82546 Dual Ethernet Adapter


class pci_i82546bg_component(component_object):
    classname = 'pci-i82546bg'
    basename = 'eth_adapter'
    description = ('The "pci-i82546bg" component represents an Intel 82546 '
                   '(Intel PRO) PCI based dual-port gigabit Ethernet adapter.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet0' : {'type' : 'ethernet-link', 'direction' : 'down',
                       'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'ethernet1' : {'type' : 'ethernet-link', 'direction' : 'down',
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
        return self.mac_address

    def set_mac_address(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if len(mac_as_list(val)) != 6:
            return Sim_Set_Illegal_Value
        self.mac_address = val
        return Sim_Set_Ok

    def calculate_csum(self, data):
        # After adding the 16-bit words 0x00 to 0x3F, the sum should be
        # 0xBABA after masking off the carry bits.
        sum = 0
        for i, x in enumerate(data):
            if i&1: sum += x
            else:   sum += x << 8
        sum = 0xbaba - sum
        return ((sum & 0xff00) >> 8, sum & 0xff)

    def add_objects(self):
        self.o.mac_a = pre_obj('mac$_a', 'i82546')
        self.o.mac_a.STATUS = 0
        self.o.mac_b = pre_obj('mac$_b', 'i82546')
        self.o.mac_b.STATUS = 0x04 # this is the second MAC
        if self.bios:
            biossize = os.path.getsize(SIM_lookup_file(self.bios))
            map_size = get_highest_2exp(biossize - 1) << 1
            self.o.prom_image = pre_obj('prom$_image', 'image')
            self.o.prom_image.size = map_size
            self.o.prom_image.files = [[self.bios, 'ro', 0, biossize]]
            self.o.prom = pre_obj('prom$', 'rom')
            self.o.prom.image = self.o.prom_image
            self.o.mac_a.expansion_rom = [self.o.prom, map_size, 0]

        # EEPROM
        self.o.eeprom = pre_obj('eth_eeprom$', "microwire-eeprom")
        self.o.eeprom.width = 16
        self.o.eeprom.size  = 1024
        ma = mac_as_list(self.mac_address)
        eeprom_data = (ma[1], ma[0], ma[3], ma[2], ma[5], ma[4], 0, 0,
                       0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0,    0,    0,    0, 0x44, 0x08, 0x80, 0x86,
                       0x80, 0x86, 0x10, 0x79, 0x80, 0x86,    0,    0,
                       0x00, 0x00, 0x10, 0x08,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,

                       0x00, 0x00, 0x78, 0x63, 0x28, 0x0c, 0x00, 0xc8,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0,    0,    0,
                          0,    0,    0,    0,    0,    0)
        eeprom_data = eeprom_data + self.calculate_csum(eeprom_data)
        assert self.calculate_csum(eeprom_data) == (0, 0)
        self.o.eeprom.data = eeprom_data
        self.o.mac_a.eeprom = self.o.eeprom
        self.o.mac_b.eeprom = self.o.eeprom

        # PHYs
        self.o.phy_a = pre_obj('phy$_a', 'eth-transceiver')
        self.o.phy_b = pre_obj('phy$_b', 'eth-transceiver')
        for phy in (self.o.phy_a, self.o.phy_b):
            # define M88E1011_I_PHY_ID  0x01410C20
            phy.phyidr1 = 0x0141
            phy.phyidr2 = 0x0c20
            # link up
            phy.registers = [0]*32
            phy.registers[1] = 0x794d
        self.o.mac_a.phy_device = self.o.phy_a
        self.o.mac_b.phy_device = self.o.phy_b

        # speed selection
        self.o.phy_a.speed = 1000
        self.o.phy_b.speed = 1000
        self.o.mac_a.tx_bandwidth = 1000000000
        self.o.mac_b.tx_bandwidth = 1000000000

    def connect_ethernet_link(self, connector, link):
        if connector == 'ethernet0':
            self.o.mac_a.link = link
            self.o.phy_a.link_up = 1
            self.o.phy_a.full_duplex = 1
        else:
            self.o.mac_b.link = link
            self.o.phy_b.link_up = 1
            self.o.phy_b.full_duplex = 1

    def disconnect_ethernet_link(self, connector):
        if connector == 'ethernet0':
            self.o.mac_a.link = None
            self.o.phy_a.link_up = 0
            self.o.phy_a.full_duplex = 0
        else:
            self.o.mac_b.link = None
            self.o.phy_b.link_up = 0
            self.o.phy_b.full_duplex = 0

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.mac_a.pci_bus = pci_bus
        self.o.mac_b.pci_bus = pci_bus

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [
            [[0, self.o.mac_a], [1, self.o.mac_b]]]
        self.connector_info['ethernet0'] = []
        self.connector_info['ethernet1'] = []

register_component_class(
    pci_i82546bg_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the first Ethernet adapter. The last bit is '
      'toggled to get the address for the second interface.'],
     ['bios', Sim_Attr_Optional, 's',
      'The x86 BIOS file to use.']])


### DEC 21041/21140A/21143 Ethernet Adapters


for cl in (pci_dec21041_component, pci_dec21140a_component,
           pci_dec21143_component):
    register_dec21xxx_component_class(cl)


class pci_dec21140a_dml_component(component_object):
    classname = 'pci-dec21140a-dml'
    basename = 'eth_adapter'
    description = ('The "pci-dec21140a-dml" component represents a DEC21140A '
                   'PCI based fast Ethernet adapter (modeled in DML).')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet' : {'type' : 'ethernet-link', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.bios = None

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
        self.o.dec = pre_obj('dec$', "DEC21140A-dml")

        self.o.eeprom = pre_obj('dec$-eeprom', "microwire-eeprom")
        mac_a = mac_as_list(self.mac)
        eeprom_data = (0x0e, 0x11, 0xb0, 0xbb, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x18, 0x3f, 0x01, 0x04,
                       mac_a[1], mac_a[0], mac_a[3],
                       mac_a[2], mac_a[5], mac_a[4],
                       0x1e, 0x00, 0x00, 0x00, 0x00, 0x00,

                       0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                              
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
        # The last two bytes should be the CRC, but we ignore it here

        self.o.eeprom.data = eeprom_data
        self.o.eeprom.width = 16
        self.o.eeprom.size = 1024
        
        self.o.phy = pre_obj('dec$-phy', "mii-transceiver")
        self.o.phy.mac = self.o.dec

        self.o.mii = pre_obj('dec$-mii', "mii-management-bus")
        
        self.o.dec.phy = self.o.phy
        self.o.dec.serial_eeprom = self.o.eeprom
        self.o.dec.mii_bus = self.o.mii
        self.o.mii.devices = [[self.o.phy, 0]]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.dec]]]
        self.connector_info['ethernet'] = []

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.dec.pci_bus = pci_bus

    def connect_ethernet_link(self, connector, link):
        self.o.phy.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.phy.link = None

register_component_class(pci_dec21140a_dml_component,
                         [['mac_address', Sim_Attr_Required, 's',
                           'The MAC address of the Ethernet adapter.']])


### AMD 79C973 Ethernet Adapter


class pci_am79c973_component(component_object):
    classname = 'pci-am79c973'
    basename = 'eth_adapter'
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
        self.o.lance = pre_obj('lance$', 'AM79C973')
        self.o.phy = pre_obj('phy$', 'mii-transceiver')
        self.o.phy.mac = self.o.lance
        self.o.lance.phy = self.o.phy
        # build Address PROM
        aprom = [0]*16
        aprom[0:6] = mac_as_list(self.mac)
        aprom[14:16] = [ 0x57, 0x57 ]
        self.o.lance.ioreg_aprom = aprom
        if self.bios:
            biossize = os.path.getsize(SIM_lookup_file(self.bios))
            map_size = get_highest_2exp(biossize - 1) << 1
            self.o.prom_image = pre_obj('prom$_image', 'image')
            self.o.prom_image.size = map_size
            self.o.prom_image.files = [[self.bios, 'ro', 0, biossize]]
            self.o.prom = pre_obj('prom$', 'rom')
            self.o.prom.image = self.o.prom_image
            self.o.lance.expansion_rom = [self.o.prom, map_size, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.lance]]]
        self.connector_info['ethernet'] = []

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.lance.pci_bus = pci_bus

    def connect_ethernet_link(self, connector, link):
        self.o.lance.phy.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.lance.phy.link = None

    description = ('The "pci-am79c973" component represents a AM79C973 '
                   'PCI based Ethernet adapter.')

register_component_class(
    pci_am79c973_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.'],
     ['bios', Sim_Attr_Optional, 's',
      'The x86 BIOS file to use.']])



### VGA PCI Graphics Adapter

class pci_vga_component(component_object):
    classname = 'pci-vga'
    basename = 'gfx_adapter'
    description = ('The "pci-vga" component represents a '
                   'PCI based VGA compatible graphics adapter.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'console' : {'type' : 'graphics-console', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.bios = 'VGABIOS-elpin-2.20'
        self.biossize = 0x8000

    def get_bios(self, idx):
        return iff(self.bios, self.bios, "")

    def set_bios(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if not val:
            self.bios = None
            return Sim_Set_Ok
        if not SIM_lookup_file(val):
            SIM_attribute_error('Could not locate bios file %s' % val)
            return Sim_Set_Illegal_Value
        self.biossize = os.stat(SIM_lookup_file(val)).st_size
        self.bios = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.vga = pre_obj('vga$', 'vga_pci')
        self.o.vga_vram_image = pre_obj('vga$_vram_image', 'image')
        self.o.vga_vram_image.size = 256*1024
        self.o.vga.image = self.o.vga_vram_image
        if self.bios:
            self.o.vga_prom_image = pre_obj('vga$_prom_image', 'image')
            self.o.vga_prom_image.size = 0x8000
            self.o.vga_prom_image.files = [[self.bios,
                                            'ro', 0, self.biossize]]
            self.o.vga_prom = pre_obj('vga$_prom', 'rom')
            self.o.vga_prom.image = self.o.vga_prom_image
            self.o.vga.expansion_rom = [self.o.vga_prom, self.biossize, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.vga]]]
        self.connector_info['console'] = [self.o.vga]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.vga.pci_bus = pci_bus
        self.o.vga.memory_space = pci_bus.memory_space
        # TODO: only add the following two if isa-compat enabled?
        pci_bus.memory_space.map += [
            [0x0000a0000, self.o.vga, 1, 0, 0x20000]]
        pci_bus.io_space.map += [
            [0x3c0, self.o.vga, 0, 0x3c0, 1],
            [0x3c1, self.o.vga, 0, 0x3c1, 1],
            [0x3c2, self.o.vga, 0, 0x3c2, 1],
            [0x3c4, self.o.vga, 0, 0x3c4, 1],
            [0x3c5, self.o.vga, 0, 0x3c5, 1],
            [0x3c6, self.o.vga, 0, 0x3c6, 1],
            [0x3c7, self.o.vga, 0, 0x3c7, 1],
            [0x3c8, self.o.vga, 0, 0x3c8, 1],
            [0x3c9, self.o.vga, 0, 0x3c9, 1],
            [0x3cc, self.o.vga, 0, 0x3cc, 1],
            [0x3ce, self.o.vga, 0, 0x3ce, 1],
            [0x3cf, self.o.vga, 0, 0x3cf, 1],
            [0x3da, self.o.vga, 0, 0x3da, 1],
            [0x3ba, self.o.vga, 0, 0x3ba, 1],
            [0x3b4, self.o.vga, 0, 0x3b4, 1],
            [0x3b5, self.o.vga, 0, 0x3b5, 1],
            [0x3d4, self.o.vga, 0, 0x3d4, 1],
            [0x3d5, self.o.vga, 0, 0x3d5, 1]]

    def connect_graphics_console(self, connector, console):
        self.o.vga.console = console

    def disconnect_graphics_console(self, connector):
        # TODO
        print "graphics console disconnect not implemented"

register_component_class(pci_vga_component,
                         [['bios', Sim_Attr_Optional, 's',
                           'The VGA BIOS file to use.']])


### Voodoo3 PCI Graphics Adapter


class pci_voodoo3_component(component_object):
    classname = 'pci-voodoo3'
    basename = 'gfx_adapter'
    description = ('The "pci-voodoo3" component represents a 3dfx Voodoo3 '
                   'PCI based VGA compatible graphics adapter.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'console' : {'type' : 'graphics-console', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.vga_prom_image = pre_obj('vga$_prom_image', 'image')
        self.o.vga_prom_image.size = 0x8000
        self.o.vga_prom_image.files = [['voodoo3-pci-bios.bin',
                                        'ro', 0, 0x8000]]
        self.o.vga_prom = pre_obj('vga$_prom', 'rom')
        self.o.vga_prom.image = self.o.vga_prom_image
        self.o.vga_vram_image = pre_obj('vga$_vram_image', 'image')
        self.o.vga_vram_image.size = 0x1000000
        self.o.vga = pre_obj('vga$', 'voodoo3')
        self.o.vga.expansion_rom = [self.o.vga_prom, 0x8000, 0]
        self.o.vga.image = self.o.vga_vram_image

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.vga]]]
        self.connector_info['console'] = [self.o.vga]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.vga.pci_bus = pci_bus
        self.o.vga.memory_space = pci_bus.memory_space
        # TODO: only add the following two if isa-compat enabled?
        pci_bus.memory_space.map += [
            [0x0000a0000, self.o.vga, 1, 0, 0x20000]]
        pci_bus.io_space.map += [
            [0x3c0, self.o.vga, 0, 0x3c0, 1],
            [0x3c1, self.o.vga, 0, 0x3c1, 1],
            [0x3c2, self.o.vga, 0, 0x3c2, 1],
            [0x3c4, self.o.vga, 0, 0x3c4, 1],
            [0x3c5, self.o.vga, 0, 0x3c5, 1],
            [0x3c6, self.o.vga, 0, 0x3c6, 1],
            [0x3c7, self.o.vga, 0, 0x3c7, 1],
            [0x3c8, self.o.vga, 0, 0x3c8, 1],
            [0x3c9, self.o.vga, 0, 0x3c9, 1],
            [0x3cc, self.o.vga, 0, 0x3cc, 1],
            [0x3ce, self.o.vga, 0, 0x3ce, 1],
            [0x3cf, self.o.vga, 0, 0x3cf, 1],
            [0x3da, self.o.vga, 0, 0x3da, 1],
            [0x3ba, self.o.vga, 0, 0x3ba, 1],
            [0x3b4, self.o.vga, 0, 0x3b4, 1],
            [0x3b5, self.o.vga, 0, 0x3b5, 1],
            [0x3d4, self.o.vga, 0, 0x3d4, 1],
            [0x3d5, self.o.vga, 0, 0x3d5, 1]]

    def connect_graphics_console(self, connector, console):
        self.o.vga.console = console

    def disconnect_graphics_console(self, connector):
        # TODO
        print "graphics console disconnect not implemented"

    def connect_agp_bus(self, connector, slot, pci_bus):
        self.connect_pci_bus(connector, slot, pci_bus)
        
register_component_class(pci_voodoo3_component, [])


### Voodoo3 AGP Graphics Adapter


class agp_voodoo3_component(pci_voodoo3_component):
    classname = 'agp-voodoo3'
    basename = 'gfx_adapter'
    description = ('The "pci-voodoo3" component represents a 3dfx Voodoo3 '
                   'AGP based VGA compatible graphics adapter.')
    connectors = pci_voodoo3_component.connectors.copy()
    del connectors['pci-bus']
    connectors['agp-bus'] = {
        'type' : 'agp-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}

    def add_objects(self):
        pci_voodoo3_component.add_objects(self)
        self.o.vga.__class_name__ = 'voodoo3-agp'
        self.o.vga_prom_image.size = 0x10000
        self.o.vga_prom_image.files = [['voodoo3-agp-bios.bin',
                                        'ro', 0, 0x10000]]
        self.o.vga.expansion_rom = [self.o.vga_prom, 0x10000, 0]

    def add_connector_info(self):
        pci_voodoo3_component.add_connector_info(self)
        del self.connector_info['pci-bus']
        self.connector_info['agp-bus'] = [[[0, self.o.vga]]]
        self.connector_info['console'] = [self.o.vga]

register_component_class(agp_voodoo3_component, [])


### Ragexl PCI Graphics Adapter


class pci_ragexl_component(component_object):
    classname = 'pci-ragexl'
    basename = 'gfx_adapter'
    description = ('The "pci-ragexl" component represents a Rage XL '
                   'PCI based VGA compatible graphics adapter.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'console' : {'type' : 'graphics-console', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.vga_prom_image = pre_obj('vga$_prom_image', 'image')
        self.o.vga_prom_image.size = 0x8000
        self.o.vga_prom_image.files = [['ragexl-bios.bin',
                                        'ro', 0, 0x8000]]
        self.o.vga_prom = pre_obj('vga$_prom', 'rom')
        self.o.vga_prom.image = self.o.vga_prom_image
        self.o.vga_vram_image = pre_obj('vga$_vram_image', 'image')
        self.o.vga_vram_image.size = 0x800000
        self.o.vga = pre_obj('vga$', 'ragexl')
        self.o.vga.expansion_rom = [self.o.vga_prom, 0x8000, 0]
        self.o.vga.image = self.o.vga_vram_image

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.vga]]]
        self.connector_info['console'] = [self.o.vga]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.vga.pci_bus = pci_bus
        self.o.vga.memory_space = pci_bus.memory_space
        # TODO: only add the following two if isa-compat enabled?
        pci_bus.memory_space.map += [
            [0x0000a0000, self.o.vga, 1, 0, 0x20000]]
        pci_bus.io_space.map += [
            [0x3c0, self.o.vga, 0, 0x3c0, 1],
            [0x3c1, self.o.vga, 0, 0x3c1, 1],
            [0x3c2, self.o.vga, 0, 0x3c2, 1],
            [0x3c4, self.o.vga, 0, 0x3c4, 1],
            [0x3c5, self.o.vga, 0, 0x3c5, 1],
            [0x3c6, self.o.vga, 0, 0x3c6, 1],
            [0x3c7, self.o.vga, 0, 0x3c7, 1],
            [0x3c8, self.o.vga, 0, 0x3c8, 1],
            [0x3c9, self.o.vga, 0, 0x3c9, 1],
            [0x3cc, self.o.vga, 0, 0x3cc, 1],
            [0x3ce, self.o.vga, 0, 0x3ce, 1],
            [0x3cf, self.o.vga, 0, 0x3cf, 1],
            [0x3da, self.o.vga, 0, 0x3da, 1],
            [0x3ba, self.o.vga, 0, 0x3ba, 1],
            [0x3b4, self.o.vga, 0, 0x3b4, 1],
            [0x3b5, self.o.vga, 0, 0x3b5, 1],
            [0x3d4, self.o.vga, 0, 0x3d4, 1],
            [0x3d5, self.o.vga, 0, 0x3d5, 1]]

    def connect_graphics_console(self, connector, console):
        self.o.vga.console = console

    def disconnect_graphics_console(self, connector):
        # TODO
        print "graphics console disconnect not implemented"

    def connect_agp_bus(self, connector, slot, pci_bus):
        self.connect_pci_bus(connector, slot, pci_bus)
        
register_component_class(pci_ragexl_component, [])


### Rage P/M Mobility PCI Graphics Adapter


class pci_rage_pm_mobility_pci_component(component_object):
    classname = 'pci-rage-pm-mobility-pci'
    basename = 'gfx_adapter'
    description = ('The "pci-rage-pm-mobility-pci" component represents '
                   'a Rage P/M Mobility '
                   'PCI based VGA compatible graphics adapter.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'console' : {'type' : 'graphics-console', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.vga_prom_image = pre_obj('vga$_prom_image', 'image')
        self.o.vga_prom_image.size = 0x20000
        self.o.vga_prom_image.files = [['video-bios', 'ro', 0, 0x10000]]
        self.o.vga_prom = pre_obj('vga$_prom', 'rom')
        self.o.vga_prom.image = self.o.vga_prom_image
        self.o.vga_vram_image = pre_obj('vga$_vram_image', 'image')
        self.o.vga_vram_image.size = 0x800000
        self.o.vga = pre_obj('vga$', 'rage-pm-mobility-pci')
        self.o.vga.expansion_rom = [self.o.vga_prom, 0x20000, 0]
        self.o.vga.image = self.o.vga_vram_image

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.vga]]]
        self.connector_info['console'] = [self.o.vga]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.vga.pci_bus = pci_bus
        self.o.vga.memory_space = pci_bus.memory_space
        # TODO: only add the following two if isa-compat enabled?
        pci_bus.memory_space.map += [
            [0x0000a0000, self.o.vga, 1, 0, 0x20000]]
        pci_bus.io_space.map += [
            [0x3c0, self.o.vga, 0, 0x3c0, 1],
            [0x3c1, self.o.vga, 0, 0x3c1, 1],
            [0x3c2, self.o.vga, 0, 0x3c2, 1],
            [0x3c4, self.o.vga, 0, 0x3c4, 1],
            [0x3c5, self.o.vga, 0, 0x3c5, 1],
            [0x3c6, self.o.vga, 0, 0x3c6, 1],
            [0x3c7, self.o.vga, 0, 0x3c7, 1],
            [0x3c8, self.o.vga, 0, 0x3c8, 1],
            [0x3c9, self.o.vga, 0, 0x3c9, 1],
            [0x3cc, self.o.vga, 0, 0x3cc, 1],
            [0x3ce, self.o.vga, 0, 0x3ce, 1],
            [0x3cf, self.o.vga, 0, 0x3cf, 1],
            [0x3da, self.o.vga, 0, 0x3da, 1],
            [0x3ba, self.o.vga, 0, 0x3ba, 1],
            [0x3b4, self.o.vga, 0, 0x3b4, 1],
            [0x3b5, self.o.vga, 0, 0x3b5, 1],
            [0x3d4, self.o.vga, 0, 0x3d4, 1],
            [0x3d5, self.o.vga, 0, 0x3d5, 1]]

    def connect_graphics_console(self, connector, console):
        self.o.vga.console = console

    def disconnect_graphics_console(self, connector):
        # TODO
        print "graphics console disconnect not implemented"

    def connect_agp_bus(self, connector, slot, pci_bus):
        self.connect_pci_bus(connector, slot, pci_bus)
        
register_component_class(pci_rage_pm_mobility_pci_component, [])




### Intel i21152 Transparent PCI Bridge


# TODO: It would be better to have a separate pci-bus component than
#       including it with the bridge. But since we only support one
#       upstream bridge per bus currently, this won't work. If it is
#       changed, then connectors of the bus should be 'any'.


class pci_i21152_component(component_object):
    classname = 'pci-i21152'
    basename = 'pci_bridge'
    description = ('The "pci-i21152" component represents an Intel 21152 '
                   'transparent PCI-to-PCI bridge.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False}}
    for i in range(24):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'any',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    # TODO: we may need an attribute to map slots (24) to device-ids (32)

    def add_objects(self):
        self.o.bridge = pre_obj('bridge$', 'i21152')
        self.o.pcicfg = pre_obj('pcicfg$', 'memory-space')
        self.o.pciio = pre_obj('pciio$', 'memory-space')
        self.o.pcimem = pre_obj('pcimem$', 'memory-space')
        self.o.pcibus = pre_obj('pcibus$', 'pci-bus')
        self.o.pcibus.bridge = self.o.bridge
        self.o.pcibus.pci_devices = []
        self.o.pcibus.conf_space = self.o.pcicfg
        self.o.pcibus.io_space = self.o.pciio
        self.o.pcibus.memory_space = self.o.pcimem
        self.o.bridge.secondary_bus = self.o.pcibus
        self.o.pcimem.map = []

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.bridge]]]
        for i in range(24):
            self.connector_info['pci-slot%d' % i] = [i, self.o.pcibus]

    def connect_pci_bus_up(self, connector, slot, pci_bus):
        self.o.bridge.pci_bus = pci_bus

    def connect_pci_bus_down(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        devs = bus.pci_devices
        for dev in device_list:
            devs += [[slot, dev[0], dev[1]]]
        bus.pci_devices = devs

    def connect_pci_bus(self, connector, *arg):
        if connector == 'pci-bus':
            self.connect_pci_bus_up(connector, *arg)
        else:
            self.connect_pci_bus_down(connector, *arg)

register_component_class(pci_i21152_component, [])


### Cirrus Logic PD6729 PCI-to-PCMCIA Controller (PC-Card)


class pci_pd6729_component(component_object):
    classname = 'pci-pd6729'
    basename = 'pcmcia_bridge'
    description = ('The "pci-pd6729" component represents a Cirrus Logic '
                   'PD6729 PCI-to-PCMCIA (PC-Card) Controller with two '
                   'slots.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'pcmcia0' : {'type' : 'pcmcia-slot', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'pcmcia1' : {'type' : 'pcmcia-slot', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}
        
    def add_objects(self):
        self.o.pcmcia = pre_obj('pcmcia$', 'CL-PD6729')

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.pcmcia]]]
        self.connector_info['pcmcia0'] = [self.o.pcmcia, 0]
        self.connector_info['pcmcia1'] = [self.o.pcmcia, 1]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.pcmcia.pci_bus = pci_bus

    def connect_pcmcia_slot(self, connector, attr_space, cmn_space, io_space):
        if '0' in connector:
            self.o.pcmcia.slot0_spaces = [attr_space, cmn_space, io_space]
        else:
            self.o.pcmcia.slot1_spaces = [attr_space, cmn_space, io_space]

    def disconnect_pcmcia_slot(self, connector):
        if '0' in connector:
            self.o.pcmcia.slot0_spaces = None
        else:
            self.o.pcmcia.slot1_spaces = None


register_component_class(pci_pd6729_component, [])


### PMC-1553-BC PCI based MIL-STD-1553 Controller


class pci_pmc1553_component(component_object):
    classname = 'pci-pmc1553-bc'
    basename = 'pmc'
    description = ('The "pci-pmc1553-bc" component represents a PMC-1553'
                   'PCI based MIL-STD-1553 Bus Controller.')
    connectors = {
        'pci-bus'   : {'type' : 'pci-bus', 'direction' : 'up',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ms1553-link' : {'type' : 'ms1553-link', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.sram_image = pre_obj('pmc$_sram_image', 'image')
        self.o.sram_image.size = 0x20000
        self.o.sram = pre_obj('pmc$_sram', 'ram')
        self.o.sram.image = self.o.sram_image
        self.o.pmc = pre_obj('pmc$', 'PMC1553-BC')
        self.o.pmc.sram = self.o.sram
        self.o.pmc.sram_image = self.o.sram_image

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.pmc]]]
        self.connector_info['ms1553-link'] = []

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.pmc.pci_bus = pci_bus

    def connect_ms1553_link(self, connector, link):
        self.o.pmc.link = link

    def disconnect_ms1553_link(self, connector):
        self.o.pmc.link = None

register_component_class(pci_pmc1553_component, [])


### South Bridge base class


class south_bridge_component(standard_pc_devices_component):
    connectors = standard_pc_devices_component.connectors.copy()
    connectors['isa-bus'] = {
        'type' : 'isa-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi' : True}
    connectors['interrupt'] = {
        'type' : 'sb-interrupt', 'direction' : 'up',
        'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    connectors['pci-bus'] =  {
        'type' : 'pci-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}

    def add_objects(self):
        standard_pc_devices_component.add_objects(self)

    def add_connector_info(self):
        standard_pc_devices_component.add_connector_info(self)
        if "isa" in dir(self.o):
            self.connector_info['interrupt'] = [self.o.isa]
            self.connector_info['isa-bus'] = [self.o.isa_bus, None,
                                              self.o.isa, self.o.dma]

    def check_isa_bus(self, connector, ports):
        for p in ports:
            if p in self.used_ports:
                raise Exception, "Port 0x%x already in use." % p
        self.used_ports += ports

    def connect_isa_bus(self, connector):
        pass

    def connect_sb_interrupt(self, connector, irq_dst, ioapic):
        self.o.pic.irq_dev = irq_dst
        if ioapic:
            self.o.isa.ioapic = ioapic

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.dma.memory = pci_bus.memory_space
        pci_bus.io_space.map += [[0, self.o.isa_bus, 0, 0, 0x10000, None, 2]]
        if self.connector_info.has_key('isa-bus'):
            self.connector_info['isa-bus'] = [self.o.isa_bus,
                                              pci_bus.memory_space,
                                              self.o.isa, self.o.dma]


### Intel PIIX4 South Bridge


class south_bridge_piix4_component(south_bridge_component):
    connectors = south_bridge_component.connectors.copy()

    for i in range(2):
        connectors['usb%d' % i] = {
            'type' : 'usb-port', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : True, 'multi' : False}

    classname = 'south-bridge-piix4'
    basename = 'south_bridge'
    description = ('The "south-bridge-piix4" component represents an Intel '
                   'PIIX4 PCI south bridge with the common legacy PC '
                   'devices. It includes two IDE controllers, and a real-time '
                   'clock. There is also a USB controller that is not '
                   'supported in Simics.')

    def add_objects(self):
        south_bridge_component.add_objects(self)
        self.o.pci_to_isa = pre_obj('pci_to_isa$', 'piix4_isa')
        self.o.pci_to_isa.pirqrca = 10
        self.o.pci_to_isa.pirqrcb = 11
        self.o.pci_to_isa.pirqrcc = 10
        self.o.pci_to_isa.pirqrcd = 11
        self.o.pci_to_isa.irq_dev = self.o.isa
        self.o.pci_to_ide = pre_obj('pci_to_ide$', 'piix4_ide')
        self.o.pci_to_ide.primary_ide = self.o.ide0
        self.o.pci_to_ide.secondary_ide = self.o.ide1
        self.o.ide0.bus_master_dma = self.o.pci_to_ide
        self.o.ide1.bus_master_dma = self.o.pci_to_ide
        self.o.pci_to_usb = pre_obj('pci_to_usb$', 'piix4_usb')
        self.o.power = pre_obj('power$', 'piix4_power')
        self.o.power.sci_irq_level = 9
        self.o.power.sci_irq_dev = self.o.isa
        self.o.apm = pre_obj('apm$', 'apm')
        self.o.apm.pm = self.o.power
        isa_map = [
            [0xb2, self.o.apm,     0, 0, 2],
            [0x8000, self.o.power, 0,  0x0, 1],
            [0x8001, self.o.power, 0,  0x1, 1],
            [0x8002, self.o.power, 0,  0x2, 1],
            [0x8003, self.o.power, 0,  0x3, 1],
            [0x8004, self.o.power, 0,  0x4, 1],
            [0x8005, self.o.power, 0,  0x5, 1],
            [0x8006, self.o.power, 0,  0x6, 1],
            [0x8007, self.o.power, 0,  0x7, 1],
            [0x8008, self.o.power, 0,  0x8, 1],
            [0x8009, self.o.power, 0,  0x9, 1],
            [0x800a, self.o.power, 0,  0xa, 1],
            [0x800b, self.o.power, 0,  0xb, 1],
            [0x800c, self.o.power, 0,  0xc, 1],
            [0x800d, self.o.power, 0,  0xd, 1],
            [0x800e, self.o.power, 0,  0xe, 1],
            [0x800f, self.o.power, 0,  0xf, 1],
            [0x8010, self.o.power, 0, 0x10, 1],
            [0x8011, self.o.power, 0, 0x11, 1],
            [0x8012, self.o.power, 0, 0x12, 1],
            [0x8013, self.o.power, 0, 0x13, 1],
            [0x8014, self.o.power, 0, 0x14, 1],
            [0x8015, self.o.power, 0, 0x15, 1],
            [0x8016, self.o.power, 0, 0x16, 1],
            [0x8017, self.o.power, 0, 0x17, 1],
            [0x8018, self.o.power, 0, 0x18, 1],
            [0x8019, self.o.power, 0, 0x19, 1],
            [0x801a, self.o.power, 0, 0x1a, 1],
            [0x801b, self.o.power, 0, 0x1b, 1],
            [0x801c, self.o.power, 0, 0x1c, 1],
            [0x801d, self.o.power, 0, 0x1d, 1],
            [0x801e, self.o.power, 0, 0x1e, 1],
            [0x801f, self.o.power, 0, 0x1f, 1],
            [0x8020, self.o.power, 0, 0x20, 1],
            [0x8021, self.o.power, 0, 0x21, 1],
            [0x8022, self.o.power, 0, 0x22, 1],
            [0x8023, self.o.power, 0, 0x23, 1],
            [0x8024, self.o.power, 0, 0x24, 1],
            [0x8025, self.o.power, 0, 0x25, 1],
            [0x8026, self.o.power, 0, 0x26, 1],
            [0x8027, self.o.power, 0, 0x27, 1],
            [0x8028, self.o.power, 0, 0x28, 1],
            [0x8029, self.o.power, 0, 0x29, 1],
            [0x802a, self.o.power, 0, 0x2a, 1],
            [0x802b, self.o.power, 0, 0x2b, 1],
            [0x802c, self.o.power, 0, 0x2c, 1],
            [0x802d, self.o.power, 0, 0x2d, 1],
            [0x802e, self.o.power, 0, 0x2e, 1],
            [0x802f, self.o.power, 0, 0x2f, 1],
            [0x8030, self.o.power, 0, 0x30, 1],
            [0x8031, self.o.power, 0, 0x31, 1],
            [0x8032, self.o.power, 0, 0x32, 1],
            [0x8033, self.o.power, 0, 0x33, 1],
            [0x8034, self.o.power, 0, 0x34, 1],
            [0x8035, self.o.power, 0, 0x35, 1],
            [0x8036, self.o.power, 0, 0x36, 1],
            [0x8037, self.o.power, 0, 0x37, 1]]              
        used_ports = [x[0] for x in isa_map]
        for p in used_ports:
            if p in self.used_ports:
                raise Exception, "Port %d already used." % p
        self.o.isa_bus.map += isa_map
        self.used_ports += used_ports

    def add_connector_info(self):
        south_bridge_component.add_connector_info(self)
        self.connector_info['pci-bus'] = [[[0, self.o.pci_to_isa],
                                           [1, self.o.pci_to_ide],
                                           [2, self.o.pci_to_usb],
                                           [3, self.o.power]]]
        for i in range(2):
            self.connector_info['usb%d' % i] = [self.o.pci_to_usb]

    def connect_pci_bus(self, connector, slot, pci_bus):
        south_bridge_component.connect_pci_bus(self, connector, slot, pci_bus)
        pci_bus.interrupt = self.o.pci_to_isa
        self.o.pci_to_isa.pci_bus = pci_bus
        self.o.pci_to_ide.pci_bus = pci_bus
        self.o.pci_to_usb.pci_bus = pci_bus
        self.o.power.pci_bus = pci_bus
        self.o.pci_to_ide.memory = pci_bus.memory_space

    def connect_usb_port(self, connector, dev):
        pass

    def disconnect_usb_port(self, connector):
        pass

register_component_class(south_bridge_piix4_component, [])


### Intel 6300ESB South Bridge


class south_bridge_6300esb_component(south_bridge_component):
    connectors = south_bridge_component.connectors.copy()

    connectors['northbridge'] = {
        'type' : 'hub-link', 'direction' : 'up',
        'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    connectors['apic-bus'] = {
        'type' : 'apic-bus', 'direction' : 'up',
        'empty_ok' : True, 'hotplug' : False, 'multi' : False}   
    connectors['cpu-pins'] = {
        'type' : 'x86-pins', 'direction' : 'up',
        'empty_ok' : True, 'hotplug' : False, 'multi' : True}   
    connectors['reset'] = {
        'type' : 'x86-reset-bus', 'direction' : 'up',
        'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    connectors['reset-bus'] = {
        'type' : 'x86-reset-bus', 'direction' : 'down',
        'empty_ok' : 1, 'hotplug' : False, 'multi' : False}

    connectors['generic-i2c'] = {
        'type' : 'generic-i2c', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': True}
    connectors['mem-slotA1'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': False}
    connectors['mem-slotA2'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': False}
    connectors['mem-slotB1'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': False}
    connectors['mem-slotB2'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': False}
    connectors['mem-slotA1p'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': False}
    connectors['mem-slotA2p'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': False}
    connectors['mem-slotB1p'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': False}
    connectors['mem-slotB2p'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi': False}
    connectors['pci-slot-rage'] = {
        'type' : 'pci-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    connectors['com1'] = {
        'type' : 'serial', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : True, 'multi' : False}
    connectors['com2'] = {
        'type' : 'serial', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : True, 'multi' : False}
    for i in range(4):
        connectors['usb%d' % i] = {
            'type' : 'usb-port', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : True, 'multi' : False}
    for i in range(64):
        connectors['gpio-input%d' % i] = {
            'type' : 'gpio-input-pin', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : False}
    for i in range(64):
        connectors['gpio-output%d' % i] = {
            'type' : 'gpio-output-pin', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : False}

    del connectors['pci-bus']
    del connectors['interrupt']

    flash_size = 1
    classname = 'south-bridge-6300esb'
    basename = 'south_bridge'
    description = ('The "south-bridge-6300esb" component represents an Intel '
                   '6300ESB I/O Controller Hub.')

    def add_objects(self):
        south_bridge_component.add_objects(self)

        # for connect functions later
        self.save_pci_bus = None
        self.save_apic_bus = None

        # remove default rtc from mappings and delete it
        self.o.isa_bus.map = [x for x in self.o.isa_bus.map
                              if x[1] != self.o.rtc]
        del self.o.rtc

        # APICs
        self.o.ioapic0 = pre_obj('ioapic0', 'io-apic')
        self.o.ioapic1 = pre_obj('ioapic1', 'io-apic')

        # connect isa to APIC too
        self.o.isa.ioapic = self.o.ioapic0

        # Normal PCI bus 
        self.o.sb_hi_pci      = pre_obj('sb$_hi_pci',      'i6300esb_hi')
        self.o.sb_hi_pci_bus  = pre_obj('sb$_hi_pci_bus',  'pci-bus')
        self.o.sb_hi_pci_conf = pre_obj('sb$_hi_pci_conf', 'memory-space')
        self.o.sb_hi_pci_io   = pre_obj('sb$_hi_pci_io',   'memory-space')
        self.o.sb_hi_pci_mem  = pre_obj('sb$_hi_pci_mem',  'memory-space')
        self.o.sb_hi_pci_bus.conf_space   = self.o.sb_hi_pci_conf
        self.o.sb_hi_pci_bus.io_space     = self.o.sb_hi_pci_io
        self.o.sb_hi_pci_bus.memory_space = self.o.sb_hi_pci_mem
        self.o.sb_hi_pci_bus.bridge       = self.o.sb_hi_pci
        self.o.sb_hi_pci.secondary_bus    = self.o.sb_hi_pci_bus
        self.o.sb_hi_pci_io.map      = []
        self.o.sb_hi_pci_mem.map     = []
        self.o.sb_hi_pci_bus.pci_devices = []

        # LPC space
        self.o.lpc_space = pre_obj('lpc_space$', 'memory-space')

        # Flash-memory containing the BIOS
        if self.flash_size != 1 and self.flash_size != 2:
            print "6300ESB: Incorrect flash size, assuming 1Mb"
            self.flash_size = 1
        if self.flash_size == 2:
            flash, fsize = flash_create_memory('bios_flash$',
                                               'Am29F016D',1, 8, [])
        else:
            flash, fsize = flash_create_memory('bios_flash$',
                                               '82802-8',1, 8, [])
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.bios_flash = flash_pre['bios_flash$']
        self.o.bios_image = flash_pre['bios_flash$_image']
        self.o.bios_ram = flash_pre['bios_flash$_ram']

        self.o.lpc_space.map = [
            [0x100000000 - fsize, self.o.bios_flash, 0, 0, fsize,
             self.o.bios_ram, 0, 1, 0]]

        # LPC interface
        self.o.sb_lpc = pre_obj('sb$_lpc', 'i6300esb_lpc')
        self.o.sb_lpc.lpc_space = self.o.lpc_space
        self.o.sb_lpc.pic = self.o.pic
        self.o.sb_lpc.apic = self.o.ioapic0
        self.o.sb_lpc.cpus = []
        self.o.sb_lpc.gpio_output = [None for i in range(64)]

        # USB
        self.o.sb_usb_uhci0 = pre_obj('sb$_usb_uhci0', 'i6300esb_usb_uhci')
        self.o.sb_usb_uhci0.function = 0
        self.o.sb_usb_uhci0.usb_devices = [None] * 2
        self.o.sb_usb_uhci1 = pre_obj('sb$_usb_uhci1', 'i6300esb_usb_uhci')
        self.o.sb_usb_uhci1.function = 1
        self.o.sb_usb_uhci1.usb_devices = [None] * 2
        self.o.sb_usb_ehci = pre_obj('sb$_usb_ehci', 'i6300esb_usb_ehci')
        self.o.sb_usb_ehci.usb_devices = [None] * 4
        self.o.sb_usb_ehci.companion_hc = [self.o.sb_usb_uhci0,
                                           self.o.sb_usb_uhci0,
                                           self.o.sb_usb_uhci1,
                                           self.o.sb_usb_uhci1]

        self.o.sb_smbus = pre_obj('sb$_smbus', 'i6300esb_smbus')
        self.o.smbus = pre_obj('smbus$', 'i2c-bus')
        self.o.sb_smbus.smbus = self.o.smbus

        self.o.sb_wdt = pre_obj('sb$_watchdog', 'i6300esb_wdt')
        self.o.sb_wdt.smi = self.o.sb_lpc
        self.o.sb_wdt.gpio = self.o.sb_lpc
        self.o.sb_apic = pre_obj('sb$_ioapic1', 'i6300esb_apic')
        self.o.sb_apic.ioapic = self.o.ioapic1
        self.o.sb_wdt.apic = self.o.ioapic1

        self.o.sb_ide = pre_obj('sb$_ide', 'i6300esb_ide')
        self.o.sb_ide.ide = [self.o.ide0, self.o.ide1]
        self.o.sb_ide.isa_bus = self.o.isa_bus
        self.o.ide0.bus_master_dma = self.o.sb_ide
        self.o.ide1.bus_master_dma = self.o.sb_ide

        self.o.sb_sata = pre_obj('sb$_sata', 'i6300esb_sata')

        self.o.sb_rtc = pre_obj('sb$_rtc', 'M5823')
        self.o.sb_rtc.irq_level = 8
        self.o.sb_rtc.irq_dev = self.o.isa

        self.o.sb_hi_pcix      = pre_obj('sb$_hi_pcix',      'i6300esb_pci_x')
        self.o.sb_hi_pcix_bus  = pre_obj('sb$_hi_pcix_bus',  'pci-bus')
        self.o.sb_hi_pcix_conf = pre_obj('sb$_hi_pcix_conf', 'memory-space')
        self.o.sb_hi_pcix_io   = pre_obj('sb$_hi_pcix_io',   'memory-space')
        self.o.sb_hi_pcix_mem  = pre_obj('sb$_hi_pcix_mem',  'memory-space')
        self.o.sb_hi_pcix_bus.conf_space   = self.o.sb_hi_pcix_conf
        self.o.sb_hi_pcix_bus.io_space     = self.o.sb_hi_pcix_io
        self.o.sb_hi_pcix_bus.memory_space = self.o.sb_hi_pcix_mem
        self.o.sb_hi_pcix_bus.bridge       = self.o.sb_hi_pcix
        self.o.sb_hi_pcix.secondary_bus    = self.o.sb_hi_pcix_bus
        self.o.sb_hi_pcix_mem.map = []

        self.o.sb_ac97_audio = pre_obj('sb$_ac97_audio', 'i6300esb_ac97_audio')
        self.o.sb_ac97_modem = pre_obj('sb$_ac97_modem', 'i6300esb_ac97_modem')

        # add a sub isa-bus where the SIU and the rest of the 6300 will
        # catch unmapped accesses
        self.o.sb_isa_bus = pre_obj('sb0_isa_bus$', 'port-space')
        self.o.isa_bus.default_target = [self.o.sb_isa_bus, 0, 0, None]
        self.o.sb_isa_bus.map = []

        self.o.sb_siu = pre_obj('sb$_siu', 'i6300esb_siu')
        self.o.sb_com1 = pre_obj('sb$_siu_com1', 'NS16550')
        self.o.sb_com1.interrupt_mask_out2 = 1
        self.o.sb_com1.irq_level = 4
        self.o.sb_com1.irq_dev = self.o.isa
        self.o.sb_com2 = pre_obj('sb$_siu_com2', 'NS16550')
        self.o.sb_com2.interrupt_mask_out2 = 1
        self.o.sb_com2.irq_level = 3
        self.o.sb_com2.irq_dev = self.o.isa
        self.o.sb_siu.com1 = self.o.sb_com1
        self.o.sb_siu.com2 = self.o.sb_com2
        self.o.sb_siu.isa_bus = self.o.sb_isa_bus
        
        self.o.post_log = pre_obj('post$', 'amibios8-post-log')

        # add aliases in isa_bus
        self.o.isa_bus.map += [
            # request register
            [0x009, self.o.dma,  0, 0x9, 1],
            # write all mask
            [0x00f, self.o.dma,  0, 0xf, 1],

            # dma aliases
            [0x010, self.o.dma,  0, 0, 1],
            [0x011, self.o.dma,  0, 1, 1],
            [0x012, self.o.dma,  0, 2, 1],
            [0x013, self.o.dma,  0, 3, 1],
            [0x014, self.o.dma,  0, 4, 1],
            [0x015, self.o.dma,  0, 5, 1],
            [0x016, self.o.dma,  0, 6, 1],
            [0x017, self.o.dma,  0, 7, 1],
            [0x018, self.o.dma,  0, 8, 1],
            [0x01a, self.o.dma,  0, 0xa, 1],
            [0x01b, self.o.dma,  0, 0xb, 1],
            [0x01c, self.o.dma,  0, 0xc, 1],
            [0x01d, self.o.dma,  0, 0xd, 1],
            [0x01e, self.o.dma,  0, 0xe, 1],

            # request register
            [0x019, self.o.dma,  0, 0x9, 1],
            # write all mask alias
            [0x01f, self.o.dma,  0, 0xf, 1],

            [0x024, self.o.pic,  0,  0x20, 1],
            [0x025, self.o.pic,  0,  0x21, 1],
            [0x028, self.o.pic,  0,  0x20, 1],
            [0x029, self.o.pic,  0,  0x21, 1],
            [0x02C, self.o.pic,  0,  0x20, 1],
            [0x02D, self.o.pic,  0,  0x21, 1],
            [0x030, self.o.pic,  0,  0x20, 1],
            [0x031, self.o.pic,  0,  0x21, 1],
            [0x034, self.o.pic,  0,  0x20, 1],
            [0x035, self.o.pic,  0,  0x21, 1],
            [0x038, self.o.pic,  0,  0x20, 1],
            [0x039, self.o.pic,  0,  0x21, 1],
            [0x03C, self.o.pic,  0,  0x20, 1],
            [0x03D, self.o.pic,  0,  0x21, 1],

            [0x04E, self.o.sb_siu,  0,  0, 1],
            [0x04F, self.o.sb_siu,  0,  1, 1],

            [0x050, self.o.pit,  0, 0, 1],
            [0x051, self.o.pit,  0, 1, 1],
            [0x052, self.o.pit,  0, 2, 1],
            [0x053, self.o.pit,  0, 3, 1],

            [0x070, self.o.sb_rtc,  0, 0, 1],
            [0x071, self.o.sb_rtc,  0, 1, 1],
            [0x072, self.o.sb_rtc,  0, 2, 1],
            [0x073, self.o.sb_rtc,  0, 3, 1],
            [0x074, self.o.sb_rtc,  0, 0, 1],
            [0x075, self.o.sb_rtc,  0, 1, 1],
            [0x076, self.o.sb_rtc,  0, 2, 1],
            [0x077, self.o.sb_rtc,  0, 3, 1],


            [0x080, self.o.post_log, 0, 0, 2],
            [0x081, self.o.dma,  0, 0x81, 1],
            
            [0x091, self.o.dma,  0, 0x81, 1],
            [0x092, self.o.sb_lpc, 4,  0x92, 1],
            
            [0x093, self.o.dma,  0, 0x83, 1],
            [0x094, self.o.dma,  0, 0x84, 1],
            [0x095, self.o.dma,  0, 0x85, 1],
            [0x096, self.o.dma,  0, 0x86, 1],
            [0x097, self.o.dma,  0, 0x87, 1],
            [0x098, self.o.dma,  0, 0x88, 1],
            [0x099, self.o.dma,  0, 0x89, 1],
            [0x09a, self.o.dma,  0, 0x8a, 1],
            [0x09b, self.o.dma,  0, 0x8b, 1],
            [0x09c, self.o.dma,  0, 0x8c, 1],
            [0x09d, self.o.dma,  0, 0x8d, 1],
            [0x09e, self.o.dma,  0, 0x8e, 1],
            [0x09f, self.o.dma,  0, 0x8f, 1],
        
            [0x0A4, self.o.pic,  0,  0xA0, 1],
            [0x0A5, self.o.pic,  0,  0xA1, 1],
            [0x0A8, self.o.pic,  0,  0xA0, 1],
            [0x0A9, self.o.pic,  0,  0xA1, 1],
            [0x0AC, self.o.pic,  0,  0xA0, 1],
            [0x0AD, self.o.pic,  0,  0xA1, 1],
            [0x0B0, self.o.pic,  0,  0xA0, 1],
            [0x0B1, self.o.pic,  0,  0xA1, 1],

            [0x0B2, self.o.sb_lpc, 3, 0xB2, 1],
            [0x0B3, self.o.sb_lpc, 3, 0xB3, 1],
            
            [0x0B4, self.o.pic,  0,  0xA0, 1],
            [0x0B5, self.o.pic,  0,  0xA1, 1],
            [0x0B8, self.o.pic,  0,  0xA0, 1],
            [0x0B9, self.o.pic,  0,  0xA1, 1],
            [0x0BC, self.o.pic,  0,  0xA0, 1],
            [0x0BD, self.o.pic,  0,  0xA1, 1],

            [0x0c1, self.o.dma,  0, 0xc0, 1],
            [0x0c3, self.o.dma,  0, 0xc2, 1],
            [0x0c5, self.o.dma,  0, 0xc4, 1],
            [0x0c7, self.o.dma,  0, 0xc6, 1],
            [0x0c9, self.o.dma,  0, 0xc8, 1],
            [0x0cb, self.o.dma,  0, 0xca, 1],
            [0x0cd, self.o.dma,  0, 0xcc, 1],
            [0x0cf, self.o.dma,  0, 0xce, 1],
            [0x0d1, self.o.dma,  0, 0xd0, 1],
            [0x0d5, self.o.dma,  0, 0xd4, 1],
            [0x0d7, self.o.dma,  0, 0xd6, 1],
            [0x0d9, self.o.dma,  0, 0xd8, 1],
            [0x0db, self.o.dma,  0, 0xda, 1],
            [0x0dd, self.o.dma,  0, 0xdc, 1],

            # request register
            [0x0d2, self.o.dma,  0, 0xd2, 1],
            [0x0d3, self.o.dma,  0, 0xd2, 1],
            # write all mask
            [0x0de, self.o.dma,  0, 0xde, 1],
            [0x0df, self.o.dma,  0, 0xde, 1],
            [0x0e0, self.o.post_log, 0, 1, 1],]

    def add_connector_info(self):
        south_bridge_component.add_connector_info(self)
        self.connector_info['northbridge'] = []
        self.connector_info['cpu-pins'] = []
        self.connector_info['reset'] = []
        self.connector_info['reset-bus'] = [self.o.sb_lpc]
        self.connector_info['generic-i2c'] = [self.o.smbus]
        self.connector_info['mem-slotA1'] = [self.o.smbus, 0xA0 >> 1]
        self.connector_info['mem-slotA2'] = [self.o.smbus, 0xA2 >> 1]
        self.connector_info['mem-slotB1'] = [self.o.smbus, 0xA4 >> 1]
        self.connector_info['mem-slotB2'] = [self.o.smbus, 0xA6 >> 1]
        self.connector_info['mem-slotA1p'] = [self.o.smbus, 0xA8 >> 1]
        self.connector_info['mem-slotA2p'] = [self.o.smbus, 0xAA >> 1]
        self.connector_info['mem-slotB1p'] = [self.o.smbus, 0xAC >> 1]
        self.connector_info['mem-slotB2p'] = [self.o.smbus, 0xAE >> 1]
        self.connector_info['pci-slot-rage'] = [4, self.o.sb_hi_pci_bus]
        self.connector_info['apic-bus'] = []
        self.connector_info['com1'] = [None, self.o.sb_com1, 'Console on com1']
        self.connector_info['com2'] = [None, self.o.sb_com2, 'Console on com2']
        self.connector_info['isa-bus'] = [self.o.sb_isa_bus,
                                          None,
                                          self.o.isa, self.o.dma]
        for i in range(4):
            self.connector_info['usb%d' % i] = [self.o.sb_usb_ehci]
        for i in range(64):
            self.connector_info['gpio-input%d' % i] = [self.o.sb_lpc]
        for i in range(64):
            self.connector_info['gpio-output%d' % i] = [i]

    def connect_x86_reset_bus(self, connector, bus = None):
        if bus != None:
            # connecting from 'reset'
            self.o.sb_lpc.reset_bus = bus

    def connect_gpio_input_pin(self, connector):
        pass

    def connect_gpio_output_pin(self, connector, listener):
        index = self.connector_info[connector][0]
        self.o.sb_lpc.gpio_output[index] = listener

    def connect_mem_bus(self, connector, memory_megs, memory_ranks):
        pass

    def connect_generic_i2c(self, connector):
        pass

    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        devs = bus.pci_devices
        for dev in device_list:
            devs += [[slot, dev[0], dev[1]]]
        self.o.sb_hi_pci_bus.pci_devices = devs

    def update_apic_bus(self):
        if self.save_pci_bus and self.save_apic_bus:
            self.save_pci_bus.memory_space.map += [
                [0xfee00000, self.save_apic_bus, 0, 0, 0x100000]]

    def connect_hub_link(self, connector, pci_bus):
        self.connector_info['isa-bus'] = [self.o.sb_isa_bus,
                                          pci_bus.memory_space,
                                          self.o.isa, self.o.dma]
        self.save_pci_bus = pci_bus
        self.update_apic_bus()
        self.o.dma.memory            = pci_bus.memory_space
        self.o.sb_hi_pci.pci_bus     = pci_bus
        self.o.sb_lpc.pci_bus        = pci_bus
        self.o.sb_usb_uhci0.pci_bus  = pci_bus
        self.o.sb_usb_uhci1.pci_bus  = pci_bus
        self.o.sb_usb_ehci.pci_bus   = pci_bus
        self.o.sb_smbus.pci_bus      = pci_bus
        self.o.sb_wdt.pci_bus        = pci_bus
        self.o.sb_apic.pci_bus       = pci_bus
        self.o.sb_ide.pci_bus        = pci_bus
        self.o.sb_hi_pcix.pci_bus    = pci_bus
        self.o.sb_sata.pci_bus       = pci_bus
        self.o.sb_ac97_audio.pci_bus = pci_bus
        self.o.sb_ac97_modem.pci_bus = pci_bus
        pci_bus.memory_space.map += [
             [0xfec00000, self.o.ioapic0, 0, 0, 0x44]]
        pci_bus.pci_devices += [
            [28, 0, self.o.sb_hi_pcix],
            [29, 0, self.o.sb_usb_uhci0],
            [29, 1, self.o.sb_usb_uhci1],
            [29, 4, self.o.sb_wdt],
            [29, 5, self.o.sb_apic],
            [29, 7, self.o.sb_usb_ehci],
            [30, 0, self.o.sb_hi_pci],
            [31, 0, self.o.sb_lpc],
            [31, 1, self.o.sb_ide],
            [31, 2, self.o.sb_sata],
            [31, 3, self.o.sb_smbus],
            [31, 5, self.o.sb_ac97_audio],
            [31, 6, self.o.sb_ac97_modem]]
        pci_bus.io_space.default_target = [self.o.isa_bus, 0, 0, None]

        # redirect interrupt to the LPC device
        pci_bus.send_interrupt_to_bridge = 0
        pci_bus.interrupt = self.o.sb_lpc

    def connect_apic_bus(self, connector, apic_bus, dram):
        self.o.ioapic0.apic_bus = apic_bus
        self.o.ioapic1.apic_bus = apic_bus
        apic_bus.ioapic = [self.o.ioapic0, self.o.ioapic1]
        self.o.pic.irq_dev = apic_bus
        self.save_apic_bus = apic_bus
        self.update_apic_bus()

        self.o.sb_usb_uhci0.dram = dram
        self.o.sb_usb_uhci1.dram = dram
        self.o.sb_usb_ehci.dram = dram
        
    def connect_x86_pins(self, connectors, cpu):
        self.o.sb_lpc.cpus += cpu

    def connect_serial(self, connector, link, console):
        if connector == 'com1':
            if link:
                self.o.sb_com1.link = link
            else:
                self.o.sb_com1.console = console
        else:
            if link:
                self.o.sb_com2.link = link
            else:
                self.o.sb_com2.console = console

    def disconnect_serial(self, connector):
        if connector == 'com1':
            self.o.sb_com1.link = None
            self.o.sb_com1.console = None
        else:
            self.o.sb_com2.link = None
            self.o.sb_com2.console = None

    def connect_usb_port(self, connector, dev):
        pass

    def disconnect_usb_port(self, connector):
        pass

    def get_flash_size(self, idx):
        return self.flash_size

    def set_flash_size(self, val, idx):
        self.flash_size = val
        return Sim_Set_Ok

    def get_bios(self, idx):
        return self.bios

    def set_bios(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if self.instantiated:
            # allow checkpoint to be loaded, bios isn't used once instantiated
            self.bios = val
            return Sim_Set_Ok
        if not SIM_lookup_file(val):
            # TODO: use exception
            print 'Could not locate bios file %s' % val
            return Sim_Set_Illegal_Value
        self.bios_size = os.stat(SIM_lookup_file(val)).st_size
        self.bios = val
        return Sim_Set_Ok

    def load_bios(self):
        # Write the bios into the ROM area, so that checkpoints not
        # depend on the BIOS file being available all time.
        if self.flash_size * 1024 * 1024 < self.bios_size:
            print 'BIOS is too big for flash model'
            return
        f = open(SIM_lookup_file(self.bios), "rb")
        base = 0x100000000 - self.bios_size
        data = map(ord, f.read(self.bios_size))
        self.o.lpc_space.iface.memory_space.write(self.o.lpc_space, None,
                                                  base, tuple(data), 1)
        f.close()

    def instantiation_done(self):
        south_bridge_component.instantiation_done(self)
        self.load_bios()

register_component_class(south_bridge_6300esb_component,
                         [['bios', Sim_Attr_Required, 's',
                           'The BIOS file to use.'],
                          ['flash_size', Sim_Attr_Optional, 'i',
                           'The size of flash to configure (1 or 2Mb)']])


### AMD 8111 South Bridge


class south_bridge_amd8111_component(south_bridge_component):
    connectors = south_bridge_component.connectors.copy()
    classname = 'south-bridge-amd8111'
    basename = 'south_bridge'
    description = (
        'The "south-bridge-amd8111" component represents an AMD-8111 '
        'HyperTransport I/O hub.')
    connectors['mem-slot0'] = {
        'type' : 'mem-bus', 'direction' : 'down',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['pci-bus-bridge'] =  {
        'type' : 'pci-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['pci-bus-sb'] =  {
        'type' : 'pci-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    del connectors['pci-bus']
    for i in range(24):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : False}
    connectors['i2c-bus'] = {
        'type' : 'i2c-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi' : True}

    def add_objects(self):
        south_bridge_component.add_objects(self)
        # replace the RTC from standard-pc-devices
        self.o.isa_bus.map = [x for x in self.o.isa_bus.map
                              if x[1] != self.o.rtc]
        self.o.rtc = pre_obj(self.o.rtc.name, 'amd8111_rtc')
        self.o.pci_bridge = pre_obj('pci_bridge$', 'amd8111_pci_bridge')
        self.o.lpc_bridge = pre_obj('pci_to_isa$', 'amd8111_lpc_bridge')
        self.o.pci_to_ide = pre_obj('pci_to_ide$', 'amd8111_ide')
        self.o.pci_to_smbus = pre_obj('pci_to_smbus$', 'amd8111_smbus')
        self.o.system_management = pre_obj('system_management$',
                                           'amd8111_system_management')
        del(self.o.isa)
        self.o.rtc.irq_dev = self.o.system_management
        self.o.rtc.irq_level = 8
        self.o.system_management.pic = self.o.pic
        self.o.pit.irq_dev = self.o.system_management
        self.o.ide0.irq_dev = self.o.system_management
        self.o.ide1.irq_dev = self.o.system_management
        self.o.audio = pre_obj('audio$', 'amd8111_audio')
        self.o.modem = pre_obj('modem$', 'amd8111_modem')
        self.o.secondary_bus = pre_obj('pci_bus$', 'pci-bus')
        self.o.pci_bridge.secondary_bus = self.o.secondary_bus
        self.o.secondary_bus.bridge = self.o.pci_bridge
        self.o.secondary_conf = pre_obj('pci_conf$', 'memory-space')
        self.o.secondary_bus.conf_space = self.o.secondary_conf
        self.o.secondary_memory = pre_obj('pci_mem$', 'memory-space')
        self.o.secondary_memory.map = []
        self.o.secondary_bus.memory_space = self.o.secondary_memory
        self.o.secondary_io = pre_obj('pci_io$', 'memory-space')
        self.o.secondary_io.map = []
        self.o.secondary_bus.io_space = self.o.secondary_io

        self.o.pci_to_ide.primary_ide = self.o.ide0
        self.o.pci_to_ide.secondary_ide = self.o.ide1
        self.o.ide0.bus_master_dma = self.o.pci_to_ide
        self.o.ide1.bus_master_dma = self.o.pci_to_ide

        self.o.usb0 = pre_obj('pci_to_usb$', 'amd8111_usb')
        self.o.usb1 = pre_obj('pci_to_usb$', 'amd8111_usb')
        self.o.ehc = pre_obj('pci_to_ehc$', 'amd8111_ehc')
        self.o.nic = pre_obj('nic$', 'amd8111_nic')
        self.o.usb0.pci_bus = self.o.secondary_bus
        self.o.usb1.pci_bus = self.o.secondary_bus
        self.o.ehc.pci_bus = self.o.secondary_bus
        self.o.nic.pci_bus = self.o.secondary_bus
        self.o.secondary_bus.pci_devices = [[0, 0, self.o.usb0],
                                            [0, 1, self.o.usb1],
                                            [0, 2, self.o.ehc],
                                            [1, 0, self.o.nic]]

        self.o.i2c_bus = pre_obj('smbus$', 'i2c-bus')
        self.o.system_management.i2c_bus = self.o.i2c_bus

    def add_connector_info(self):
        south_bridge_component.add_connector_info(self)      
        self.connector_info['pci-bus-bridge'] = [[[0, self.o.pci_bridge]]]
        self.connector_info['pci-bus-sb'] = [[[0, self.o.lpc_bridge],
                                              [1, self.o.pci_to_ide],
                                              [2, self.o.pci_to_smbus],
                                              [3, self.o.system_management],
                                              [5, self.o.audio],
                                              [6, self.o.modem]]]
        self.connector_info['mem-slot0'] = [self.o.i2c_bus, 0x50]
        isa_map = [[0x70, self.o.rtc, 0, 0, 1],
                   [0x71, self.o.rtc, 0, 1, 1],
                   [0x72, self.o.rtc, 0, 2, 1],
                   [0x73, self.o.rtc, 0, 3, 1]]
        self.o.isa_bus.map += isa_map
        self.connector_info['i2c-bus'] = [self.o.i2c_bus]

        # The PCI bridge and LPC bridge have remapping duties and need to know
        # of almost all other devices
        self.o.pci_bridge.lpc_bridge = self.o.lpc_bridge
        self.o.pci_bridge.ide_controller = self.o.pci_to_ide
        self.o.pci_bridge.smbus = self.o.pci_to_smbus
        self.o.pci_bridge.system_management = self.o.system_management
        self.o.pci_bridge.audio = self.o.audio
        self.o.pci_bridge.modem = self.o.modem
        self.o.lpc_bridge.ide_controller = self.o.pci_to_ide
        self.o.lpc_bridge.smbus = self.o.pci_to_smbus
        self.o.lpc_bridge.system_management = self.o.system_management
        self.o.lpc_bridge.audio = self.o.audio
        self.o.lpc_bridge.modem = self.o.modem
        self.o.lpc_bridge.usb0 = self.o.usb0
        self.o.lpc_bridge.usb1 = self.o.usb1
        self.o.lpc_bridge.ehc = self.o.ehc
        self.o.lpc_bridge.nic = self.o.nic
        self.o.lpc_bridge.secondary_pci_bus = self.o.secondary_bus

        for i in range(24):
            self.connector_info['pci-slot%d' % i] = [i, self.o.secondary_bus]

        self.connector_info['interrupt'] = [self.o.system_management]
        self.connector_info['isa-bus'] = [self.o.isa_bus, None,
                                          self.o.system_management, self.o.dma]

    def connect_mem_bus(self, connector, memory_megs, memory_ranks):
        pass
    
    def connect_pci_bus(self, connector, *args):
        if len(args) == 1:
            device_list = args[0]
        else:
            slot = args[0]
            pci_bus = args[1]
        if connector == 'pci-bus-bridge':
            self.o.pci_bridge.pci_bus = pci_bus
        elif connector == 'pci-bus-sb':
            self.o.dma.memory = pci_bus.memory_space
            pci_bus.io_space.map += [[0, self.o.isa_bus, 0, 0, 0x10000, None, 2]]
            self.connector_info['isa-bus'] = [self.o.isa_bus,
                                              pci_bus.memory_space,
                                              self.o.system_management, self.o.dma]
            pci_bus.interrupt = self.o.system_management
            self.o.lpc_bridge.pci_bus = pci_bus
            self.o.pci_to_ide.pci_bus = pci_bus
            self.o.pci_to_smbus.pci_bus = pci_bus
            self.o.system_management.pci_bus = pci_bus
            self.o.audio.pci_bus = pci_bus
            self.o.modem.pci_bus = pci_bus
            self.o.pci_to_ide.memory = pci_bus.memory_space
        else:
            slot = self.connector_info[connector][0]
            bus = self.connector_info[connector][1]
            devs = bus.pci_devices
            for dev in device_list:
                devs += [[slot, dev[0], dev[1]]]
            bus.pci_devices = devs

    def connect_sb_interrupt(self, connector, irq_dst, ioapic):
        self.o.pic.irq_dev = irq_dst
        self.o.system_management.ioapic = ioapic
        self.o.system_management.irq_dev = irq_dst

    def connect_i2c_bus(self, connector):
        pass

register_component_class(south_bridge_amd8111_component, [])


### ALi MD1535D South Bridge


class south_bridge_md1535d_component(south_bridge_component):
    classname = 'south-bridge-md1535d'
    basename = 'south_bridge'
    description = ('The "south-bridge-md1535d" component represents an ALi '
                   'MD1535D PCI south bridge with the common legacy PC '
                   'devices. It includes two IDE controllers, a floppy '
                   'controller with two drives, three serial ports, and a '
                   'real-time clock. There is also a USB controller that is '
                   'not supported in Simics.')
    connectors = south_bridge_component.connectors.copy()
    del connectors['pci-bus']
    connectors['pci-bus-pm'] =  {
        'type' : 'pci-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['pci-bus-isa'] =  {
        'type' : 'pci-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['pci-bus-ide'] =  {
        'type' : 'pci-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['com1'] = {
        'type' : 'serial', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : True, 'multi' : False}
    connectors['com2'] = {
        'type' : 'serial', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : True, 'multi' : False}
    connectors['com3'] = {
        'type' : 'serial', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : True, 'multi' : False}

    def add_objects(self):
        south_bridge_component.add_objects(self)
        # replace the RTC from standard-pc-devices
        self.o.isa_bus.map = [x for x in self.o.isa_bus.map
                              if x[1] != self.o.rtc]
        self.o.rtc = pre_obj('rtc', 'M5823')
        self.o.rtc.irq_dev = self.o.isa
        self.o.rtc.irq_level = 8
        self.o.com1 = pre_obj('com1', 'NS16550')
        self.o.com1.irq_dev = self.o.isa
        self.o.com1.irq_level = 4
        self.o.com2 = pre_obj('com2', 'NS16550')
        self.o.com2.irq_dev = self.o.isa
        self.o.com2.irq_level = 3
        self.o.com3 = pre_obj('com3', 'NS16550')
        self.o.com3.irq_dev = self.o.isa
        self.o.com3.irq_level = 4
        self.o.fd0 = pre_obj('fd$', 'floppy-drive')
        self.o.fd1 = pre_obj('fd$', 'floppy-drive')
        self.o.flp = pre_obj('flp$', 'i82077')
        self.o.flp.irq_dev = self.o.isa
        self.o.flp.dma_channel = 2
        self.o.flp.dma_dev = self.o.dma
        self.o.flp.irq_level = 6
        self.o.flp.drives = [self.o.fd0, self.o.fd1]
        self.o.sb_isa = pre_obj('sb_isa', 'MD1535D-isa')
        self.o.sb_isa.irq_dev = self.o.isa
        self.o.sb_isa.pci_to_isa_irq = [9, 10, 11, 12]
        self.o.sb_pm = pre_obj('sb_pm', 'MD1535D-power')
        self.o.sb_ide = pre_obj('sb_ide', 'MD1535D-ide')
        self.o.acpi = pre_obj('acpi', 'MD1535D-acpi')
        self.o.cfg = pre_obj('cfg', 'MD1535D-cfg')
        self.o.unknown = pre_obj('unknown', 'MD1535D-unknown')
        self.o.smb = pre_obj('smb', 'MD1535D-smb')
        # self.o.usb = pre_obj('usb', 'MD1535D-usb')
        self.o.ide0.bus_master_dma = self.o.sb_ide
        self.o.ide1.bus_master_dma = self.o.sb_ide
        self.o.ide0.interrupt_delay = 1.0e-6
        self.o.ide1.interrupt_delay = 1.0e-6
        self.o.sb_ide.primary_ide = self.o.ide0
        self.o.sb_ide.secondary_ide = self.o.ide1
        isa_map = [
            # 0x0f missing
            [0x70, self.o.rtc, 0, 0, 1],
            [0x71, self.o.rtc, 0, 1, 1],
            [0x72, self.o.rtc, 0, 2, 1],
            [0x73, self.o.rtc, 0, 3, 1],
            # 0xd2 missing
            # 0xde missing
            [0x2e8, self.o.com3, 1, 0, 1],
            [0x2e9, self.o.com3, 1, 1, 1],
            [0x2ea, self.o.com3, 1, 2, 1],
            [0x2eb, self.o.com3, 1, 3, 1],
            [0x2ec, self.o.com3, 1, 4, 1],
            [0x2ed, self.o.com3, 1, 5, 1],
            [0x2ee, self.o.com3, 1, 6, 1],
            [0x2ef, self.o.com3, 1, 7, 1],
            # next is the parallel port, not implemented
            [0x378, self.o.unknown,  0, 0, 4],
            [0x3e8, self.o.com2, 1, 0, 1],
            [0x3e9, self.o.com2, 1, 1, 1],
            [0x3ea, self.o.com2, 1, 2, 1],
            [0x3eb, self.o.com2, 1, 3, 1],
            [0x3ec, self.o.com2, 1, 4, 1],
            [0x3ed, self.o.com2, 1, 5, 1],
            [0x3ee, self.o.com2, 1, 6, 1],
            [0x3ef, self.o.com2, 1, 7, 1],
            [0x3f0, self.o.cfg,  0, 0, 2],
            [0x3f2, self.o.flp,  0, 0, 1],
            [0x3f4, self.o.flp,  0, 2, 1],
            [0x3f5, self.o.flp,  0, 3, 1],
            [0x3f7, self.o.flp,  0, 5, 1],
            [0x3f8, self.o.com1, 1, 0, 1],
            [0x3f9, self.o.com1, 1, 1, 1],
            [0x3fa, self.o.com1, 1, 2, 1],
            [0x3fb, self.o.com1, 1, 3, 1],
            [0x3fc, self.o.com1, 1, 4, 1],
            [0x3fd, self.o.com1, 1, 5, 1],
            [0x3fe, self.o.com1, 1, 6, 1],
            [0x3ff, self.o.com1, 1, 7, 1],
            # System Management Bus
            [0x600, self.o.smb,  0, 0, 1],
            [0x601, self.o.smb,  0, 1, 1],
            [0x602, self.o.smb,  0, 2, 1],
            [0x603, self.o.smb,  0, 3, 1],
            [0x604, self.o.smb,  0, 4, 1],
            [0x605, self.o.smb,  0, 5, 1],
            [0x606, self.o.smb,  0, 6, 1],
            [0x607, self.o.smb,  0, 7, 1],
            # ACPI
            [0x800, self.o.acpi,  0, 0, 2],
            [0x802, self.o.acpi,  0, 0, 2],
            [0x804, self.o.acpi,  0, 0, 2],
            [0x828, self.o.acpi,  0, 0, 1]]
        # overwrite 0x70 - 0x73
        used_ports = [x[0] for x in isa_map if x[0] < 0x70 or x[0] > 0x73]
        for p in used_ports:
            if p in self.used_ports:
                raise Exception, "Port 0x%x already used." % p
        self.o.isa_bus.map += isa_map
        self.used_ports += used_ports

    def add_connector_info(self):
        south_bridge_component.add_connector_info(self)      
        self.connector_info['pci-bus-pm']  = [[[0, self.o.sb_pm]]]  # slot  6
        self.connector_info['pci-bus-isa'] = [[[0, self.o.sb_isa]]] # slot  7
        self.connector_info['pci-bus-ide'] = [[[0, self.o.sb_ide]]] # slot 13
        self.connector_info['com1'] = [None, self.o.com1, 'com1']
        self.connector_info['com2'] = [None, self.o.com2, 'com2']
        self.connector_info['com3'] = [None, self.o.com3, 'com3']

    def connect_pci_bus(self, connector, slot, pci_bus):
        if connector == 'pci-bus-isa':
            south_bridge_component.connect_pci_bus(self, connector, slot,
                                                   pci_bus)
            pci_bus.interrupt = self.o.sb_isa
            self.o.sb_isa.pci_bus = pci_bus
        elif connector == 'pci-bus-pm':
            self.o.sb_pm.pci_bus = pci_bus
        elif connector == 'pci-bus-ide':
            self.o.sb_ide.pci_bus = pci_bus
            self.o.sb_ide.memory = pci_bus.memory_space

    def connect_serial(self, connector, link, console):
        if connector == 'com1':
            if link:
                self.o.com1.link = link
            else:
                self.o.com1.console = console
        elif connector == 'com2':
            if link:
                self.o.com2.link = link
            else:
                self.o.com2.console = console
        elif connector == 'com3':
            if link:
                self.o.com3.link = link
            else:
                self.o.com3.console = console

    def disconnect_serial(self, connector):
        if connector == 'com1':
            self.o.com1.link = None
            self.o.com1.console = None
        elif connector == 'com2':
            self.o.com2.link = None
            self.o.com2.console = None
        elif connector == 'com3':
            self.o.com3.link = None
            self.o.com3.console = None

register_component_class(south_bridge_md1535d_component, [])


### PCI Backplane


class pci_backplane_component(component_object):
    classname = "pci-backplane"
    basename = "backplane"
    description = "PCI backplane"
    num_pci_slots = 32
    connectors = dict(
        [("pci-slot%d" % i, {"type": "pci-bus", "direction": "down",
                             "empty_ok": True, "hotplug": False})
         for i in xrange(num_pci_slots)]
        + [("pci-bridge", {"type": "pci-bridge", "direction": "down",
                           "empty_ok": False, "hotplug": False})])

    def add_objects(self):
        self.o.pci_bus = pre_obj('pci_bus', 'pci-bus')
        self.o.pci_space_io = pre_obj('pci_io', 'memory-space')
        self.o.pci_space_conf = pre_obj('pci_conf', 'memory-space')
        self.o.pci_space_mem = pre_obj('pci_mem', 'memory-space')
        self.o.pci_bus.io_space = self.o.pci_space_io
        self.o.pci_bus.conf_space = self.o.pci_space_conf
        self.o.pci_bus.memory_space = self.o.pci_space_mem
        self.o.pci_bus.pci_devices = []
        self.o.pci_space_mem.map = []

    def add_connector_info(self):
        for i in xrange(self.num_pci_slots):
            self.connector_info["pci-slot%d" % i] = [i, self.o.pci_bus]
        self.connector_info["pci-bridge"] = [self.o.pci_bus]

    def connect_pci_bus(self, connector, device_list):
        slot, bus = self.connector_info[connector]
        for function, obj in device_list:
            bus.pci_devices.append([slot, function, obj])

    def connect_pci_bridge(self, connector, obj):
        self.o.pci_bus.bridge = obj

    def get_clock(self):
        return self.get_processors()[0]

    def get_processors(self):
        return find_all_processors(self)

register_component_class(pci_backplane_component, [], top_level = True)


### PEX8524 - PCI Express switch

class pcie_pex8524_component(component_object):
    classname = "pcie-pex8524"
    basename = "pcie-switch"
    description = "PEX8524 PCI Express switch"
    max_ports = 16

    connectors = {
        'pcie-switch0' : {'type' : 'pci-bus', 'direction' : 'up',
                         'empty_ok' : True, 'hotplug' : True,
                         'multi' : False},
        'pcie-switch1' : {'type' : 'pci-bus', 'direction' : 'up',
                          'empty_ok' : True, 'hotplug' : True,
                          'multi' : False}}

    for i in xrange(max_ports):
        connectors['pcie-slot%d' % i] = {'type' : 'pci-bus',
                                         'direction' : 'down',
                                         'empty_ok' : True,
                                         'hotplug' : False,
                                         'multi' : False}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.down_port = [None] * self.max_ports
        self.o.down_bus = [None] * self.max_ports
        self.o.down_conf = [None] * self.max_ports
        self.o.down_io = [None] * self.max_ports
        self.o.down_mem = [None] * self.max_ports

        self.up_port_number = 0
        self.nt_port_number = -1
        self.ports = [0, 1, 8, 9, 10, 11]

    def get_ports(self):
        return ' '.join(map(str, self.ports))

    def set_ports(self, value, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.ports = map(int, value.split())
        return Sim_Set_Ok

    def get_up_port_number(self):
        return self.up_port_number

    def set_up_port_number(self, value, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.up_port_number = value
        return Sim_Set_Ok

    def get_nt_port_number(self):
        return self.nt_port_number

    def set_nt_port_number(self, value, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.nt_port_number = value
        return Sim_Set_Ok

    def add_objects(self):

        all_ports = []

        # The virtual bus that connects the up-port to all the down-ports
        self.o.up_conf = pre_obj('pex$-up-conf', 'memory-space')
        self.o.up_io = pre_obj('pex$-up-io', 'memory-space')
        self.o.up_mem = pre_obj('pex$-up-mem', 'memory-space')

        self.o.up_bus = pre_obj('pex$-up-bus', 'pcie-switch')
        self.o.up_bus.conf_space = self.o.up_conf
        self.o.up_bus.io_space = self.o.up_io
        self.o.up_bus.memory_space = self.o.up_mem
        self.o.up_bus.pci_devices = []
        self.o.up_mem.map = []

        self.o.up_port = pre_obj('pex$-up-port', 'pex8524')
        self.o.up_port.port_number = self.up_port_number
        self.o.up_port.is_upstream_port = True
        self.o.up_port.secondary_bus = self.o.up_bus
        self.o.up_bus.bridge = self.o.up_port

        all_ports += [self.o.up_port]

        # Create all the down-ports
        for port in self.ports:
            if port == self.up_port_number:
                continue

            if port == self.nt_port_number:
                # Create the virtual side of the non-transparent port
                self.o.nt_virt_port = pre_obj('pex$-nt-virt-port',
                                              'pex8524_nt_virtual')
                self.o.nt_virt_port.port_number = port
                self.o.nt_virt_port.pci_bus = self.o.up_bus

                # Create the link side of the non-transparent port
                self.o.nt_link_port = pre_obj('pex$-nt-link-port',
                                              'pex8524_nt_link')
                self.o.nt_link_port.up_port = self.o.up_port
                self.o.nt_link_port.port_number = port
                self.o.nt_link_port.nt_port_companion = self.o.nt_virt_port
                self.o.nt_virt_port.nt_port_companion = self.o.nt_link_port

                all_ports += [self.o.nt_virt_port]
            else:
                self.o.down_conf[port] = pre_obj('pex$-down-conf%d' % port,
                                                 'memory-space')
                self.o.down_io[port] = pre_obj('pex$-down-io%d' % port,
                                               'memory-space')
                self.o.down_mem[port] = pre_obj('pex$-down-mem%d' % port,
                                                'memory-space')

                self.o.down_bus[port] = pre_obj('pex$-down-bus%d' % port,
                                                'pcie-switch')
                self.o.down_bus[port].conf_space = self.o.down_conf[port]
                self.o.down_bus[port].io_space = self.o.down_io[port]
                self.o.down_bus[port].memory_space = self.o.down_mem[port]
                self.o.down_bus[port].pci_devices = []
                self.o.down_mem[port].map = []

                self.o.down_port[port] = pre_obj('pex$-down-port%d' % port,
                                                 'pex8524')
                self.o.down_port[port].port_number = port
                self.o.down_port[port].is_upstream_port = False
                self.o.down_port[port].pci_bus = self.o.up_bus
                self.o.down_port[port].secondary_bus = self.o.down_bus[port]
                self.o.down_bus[port].bridge = self.o.down_port[port]

                all_ports += [self.o.down_port[port]]

        # Add all down-port bridges to the virtual bus
        devs = self.o.up_bus.pci_devices
        for port in (port for port in all_ports if port != self.o.up_port):
            devs += [[port.port_number, 0, port]]

        # Create memory space that maps all ports' PCI conf space
        self.o.pci_conf_space = pre_obj('pex$-pci-conf-space', 'memory-space')
        self.o.pci_conf_space.map = []
        for port in all_ports:
            self.o.pci_conf_space.map += [
                [0x1000 * port.port_number, port, 255, 0, 0x1000]]

        # Create list of all ports, sorted so that element i maps to port i
        port_list = [None] * 16
        for port in all_ports:
            port_list[port.port_number] = port

        # Assign list of other ports to all ports
        for port in all_ports:
            port.other_ports = port_list
            port.up_port = self.o.up_port
            port.pci_config_memory_space = self.o.pci_conf_space

        if self.nt_port_number != -1:
            self.o.pci_conf_space.map += [
                [0x1000 * 0x10, self.o.nt_virt_port, 255, 0, 0x1000],
                [0x1000 * 0x11, self.o.nt_link_port, 255, 0, 0x1000]]
            self.o.nt_link_port.pci_config_memory_space = self.o.pci_conf_space

    def add_connector_info(self):
        self.connector_info['pcie-switch0'] = [[[0, self.o.up_port]]]
        if self.nt_port_number != -1:
            self.connector_info['pcie-switch1'] = [[[0, self.o.nt_link_port]]]
        else:
            self.connector_info['pcie-switch1'] = [[[0, None]]]
        for i in xrange(self.max_ports):
            if i in self.ports:
                self.connector_info['pcie-slot%d' % i] = [0,
                                                          self.o.down_bus[i]]
            else:
                self.connector_info['pcie-slot%d' % i] = [0, None]

    def connect_pci_bus(self, connector, *args):
        if connector in ['pcie-switch0', 'pcie-switch1']:
            slot = args[0]
            pci_bus = args[1]
            if connector == 'pcie-switch0':
                self.o.up_port.pci_bus = pci_bus
            else:
                self.o.nt_link_port.pci_bus = pci_bus
        else:
            device_list = args[0]
            bus = self.connector_info[connector][1]
            slot = self.connector_info[connector][0]

            devs = bus.pci_devices
            for dev in device_list:
                devs += [[slot, dev[0], dev[1]]]
            bus.pci_devices = devs

    def disconnect_pci_bus(self, connector, *args):
        if connector == 'pcie-switch0':
            self.o.up_port.pci_bus = None
        elif connector == 'pcie-switch1':
            self.o.nt_link_port.pci_bus = None
        else:
            device_list = args[0]
            bus = self.connector_info[connector][1]
            slot = self.connector_info[connector][0]

            devs = bus.pci_devices
            new_devs = []
            for dev in devs:
                if not [dev[1], dev[2]] in device_list:
                    new_devs += dev
            bus.pci_devices = new_devs

register_component_class(pcie_pex8524_component,
                         [['ports', Sim_Attr_Optional, 's',
                           'List of port numbers that should be available. ' \
                           'The default is "0 1 8 9 10 11"'],
                          ['up_port_number', Sim_Attr_Optional, 'i',
                           'Port number of up-port. The default is 0.'],
                          ['nt_port_number', Sim_Attr_Optional, 'i',
                           'Port number of NT-port. If not specified, no ' \
                           'NT-port will be created. This is the default.']])


class pci_sil680a_component(component_object):
    classname = "pci-sil680a"
    basename = "ide"
    description = "SIL680a IDE controller"
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ide0-slot0' : {'type' : 'ide-slot', 'direction' : 'down',
                        'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'ide0-slot1' : {'type' : 'ide-slot', 'direction' : 'down',
                        'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'ide1-slot0' : {'type' : 'ide-slot', 'direction' : 'down',
                        'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'ide1-slot1' : {'type' : 'ide-slot', 'direction' : 'down',
                        'empty_ok' : True, 'hotplug' : False, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.ide = [None] * 2

    def add_objects(self):
        self.o.sil = pre_obj('sil680a$', 'SIL680A')
        for i in xrange(2):
            self.o.ide[i] = pre_obj('ide$', 'ide')
            self.o.ide[i].bus_master_dma = self.o.sil
            self.o.ide[i].irq_dev = self.o.sil
            self.o.ide[i].irq_level = i
        self.o.ide[0].primary = 1
        self.o.sil.primary_ide = self.o.ide[0]
        self.o.sil.secondary_ide = self.o.ide[1]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.sil]]]
        self.connector_info['ide0-slot0'] = []
        self.connector_info['ide0-slot1'] = []
        self.connector_info['ide1-slot0'] = []
        self.connector_info['ide1-slot1'] = []

    def connect_ide_slot(self, connector, dev):
        if connector == 'ide0-slot0':
            self.o.ide[0].master = dev
        elif connector == 'ide0-slot1':
            self.o.ide[0].slave = dev
        elif connector == 'ide1-slot0':
            self.o.ide[1].master = dev
        else:
            self.o.ide[1].slave = dev

    def connect_pci_bus(self, connector, slot, bus):
        self.o.sil.pci_bus = bus
        self.o.sil.memory = bus.memory_space

register_component_class(pci_sil680a_component, [])
