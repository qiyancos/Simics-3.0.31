# MODULE: sun-components
# CLASS: sun-pci-pgx64
# CLASS: sun-pci-ce
# CLASS: sun-pci-hme
# CLASS: sun-pci-hme-isp
# CLASS: sun-pci-qlc
# CLASS: sun-pci-qlc-qlc
# CLASS: sun-type5-keyboard
# CLASS: sun-type5-mouse

from sim_core import *
from components import *

def patch_hme_prom(image, mac):
    # Fill in the VPD field
    image.byte_access[[0xc010, 0xc015]] = (0x90, 0x28, 0x00, 0x4e, 0x41, 0x06)
    # and the MAC address
    image.byte_access[[0xc016, 0xc01b]] = tuple(mac_as_list(mac))

def patch_cassini_prom(image, mac):
    # Fill in MAC address in the VPD field
    image.byte_access[0xc0ea] = 0xff
    image.byte_access[[0xc100, 0xc105]] = tuple(mac_as_list(mac))


### Sun PGX64 PCI Device


class sun_pci_pgx64_component(component_object):
    classname = 'sun-pci-pgx64'
    basename = 'gfx_adapter'
    description = ('The "sun-pci-pgx64" component represents a PCI card with '
                   'a PGX64 (Rage XL) graphics adapter, for use in Sun '
                   'systems.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'console' : {'type' : 'graphics-console', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.prom_image = pre_obj('pgx64_prom$_image', 'image')
        self.o.prom_image.size = 0x20000
        self.o.prom_image.files = [['pgx64.fcode', 'ro', 0, 0x10000]]
        self.o.prom = pre_obj('pgx64_prom$', 'rom')
        self.o.prom.image = self.o.prom_image
        self.o.vram_image = pre_obj('pgx64_vram$_image', 'image')
        self.o.vram_image.size = 0x800000
        self.o.pgx = pre_obj('pgx$', 'ragexl')
        self.o.pgx.expansion_rom = [self.o.prom, 0x20000, 0]
        self.o.pgx.image = self.o.vram_image

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.pgx]]]
        self.connector_info['console'] = [self.o.pgx]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.pgx.pci_bus = pci_bus
        self.o.pgx.memory_space = pci_bus.memory_space

    def connect_graphics_console(self, connector, console):
        self.o.pgx.console = console

    def disconnect_graphics_console(self, connector):
        # TODO
        print "graphics console disconnect not implemented"

register_component_class(sun_pci_pgx64_component, [])


### Sun Cassini PCI Device


class sun_pci_ce_component(component_object):
    classname = 'sun-pci-ce'
    basename = 'eth_adapter'
    description = ('The "sun-pci-ce" component represents a PCI card with a '
                   'Cassini gigabit Ethernet adapter, for use in Sun systems.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet' : {'type' : 'ethernet-link', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

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
        self.o.pcicfg = pre_obj('pcicfg$', 'memory-space')
        self.o.pciio = pre_obj('pciio$', 'memory-space')
        self.o.pcimem = pre_obj('pcimem$', 'memory-space')
        self.o.bridge = pre_obj('bridge$', 'i21152')
        self.o.pcibus = pre_obj('pcibus$', 'pci-bus')
        self.o.bridge.secondary_bus = self.o.pcibus
        self.o.pcibus.bridge = self.o.bridge
        self.o.pcibus.conf_space = self.o.pcicfg
        self.o.pcibus.io_space = self.o.pciio
        self.o.pcibus.memory_space = self.o.pcimem
        self.o.ce0 = pre_obj('ce$', 'cassini')
        self.o.ce0.mac_address = mac_as_list(self.mac)
        self.o.ce0.pci_bus = self.o.pcibus
        for i in [1, 2, 3]:
            exec "self.o.ce%d = pre_obj('ce$_sub%d', 'cassini_sub')" % (i, i)
            exec "self.o.ce%d.pci_bus = self.o.pcibus" % i
            exec "self.o.ce%d.main_object = self.o.ce0" % i
            exec "self.o.ce%d.pci_function = %d" % (i, i)
        self.o.pcibus.pci_devices = [[0, 0, self.o.ce0],
                                     [0, 1, self.o.ce1],
                                     [0, 2, self.o.ce2],
                                     [0, 3, self.o.ce3]]
        self.o.prom_image = pre_obj('ce_prom$_image', 'image')
        self.o.prom_image.size = 0x10000
        self.o.prom_image.files = [['cassini_plus.fcode', 'ro', 0, 0x10000]]
        self.o.prom = pre_obj('ce_prom$', 'rom')
        self.o.prom.image = self.o.prom_image
        self.o.ce0.expansion_rom = [self.o.prom, 0x10000, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.bridge]]]
        self.connector_info['ethernet'] = []

    def instantiation_done(self):
        component_object.instantiation_done(self)
        patch_cassini_prom(self.o.prom_image, self.mac)

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.bridge.pci_bus = pci_bus

    def connect_ethernet_link(self, connector, link):
        self.o.ce0.link = link

    def disconnect_ethernet_link(self, connector):
        # TODO
        print "Ethernet disconnect not implemented"

register_component_class(
    sun_pci_ce_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.']])


### Sun HME PCI Device


class sun_pci_hme_component(component_object):
    classname = 'sun-pci-hme'
    basename = 'eth_adapter'
    description = ('The "sun-pci-hme" component represents a PCI card with a '
                   'HME Ethernet adapter, for use in Sun systems.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet' : {'type' : 'ethernet-link', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

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
        self.o.e2bus = pre_obj('e2bus$', 'cheerio-e2bus')
        self.o.hme = pre_obj('hme$', 'cheerio-hme')
        self.o.hme.mac_address = mac_as_list(self.mac)
        self.o.prom_image = pre_obj('hmeprom$_image', 'image')
        self.o.prom_image.size = 0x1000000
        self.o.prom_image.files = [['cheerio_hme.fcode', 'ro', 0, 0x4c20]]
        self.o.prom = pre_obj('hmeprom$', 'rom')
        self.o.prom.image = self.o.prom_image
        self.o.hme.expansion_rom = [self.o.prom, 0x1000000, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.e2bus], [1, self.o.hme]]]
        self.connector_info['ethernet'] = []

    def instantiation_done(self):
        component_object.instantiation_done(self)
        patch_hme_prom(self.o.prom_image, self.mac)

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.e2bus.pci_bus = pci_bus
        self.o.hme.pci_bus = pci_bus

    def connect_ethernet_link(self, connector, link):
        self.o.hme.link = link

    def disconnect_ethernet_link(self, connector):
        # TODO
        print "Ethernet disconnect not implemented"

register_component_class(
    sun_pci_hme_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.']])


### Sun HME/ISP PCI Device


class sun_pci_hme_isp_component(component_object):
    classname = 'sun-pci-hme-isp'
    basename = 'scsi_eth'
    description = ('The "sun-pci-hme-isp" component represents a PCI card '
                   'with one HME Ethernet adapter and one ISP SCSI controller '
                   'for use in Sun systems.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'scsi-bus' : {'type' : 'scsi-bus', 'direction' : 'down',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet' : {'type' : 'ethernet-link', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.scsi_id = 7

    def get_mac_address(self, idx):
        return self.mac

    def set_mac_address(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if len(mac_as_list(val)) != 6:
            return Sim_Set_Illegal_Value
        self.mac = val
        return Sim_Set_Ok

    def get_scsi_id(self, idx):
        return self.scsi_id

    def set_scsi_id(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.scsi_id = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.pcicfg = pre_obj('pcicfg$', 'memory-space')
        self.o.pciio = pre_obj('pciio$', 'memory-space')
        self.o.pcimem = pre_obj('pcimem$', 'memory-space')
        self.o.bridge = pre_obj('bridge$', 'i21152')
        self.o.pcibus = pre_obj('pcibus$', 'pci-bus')
        self.o.bridge.secondary_bus = self.o.pcibus
        self.o.pcibus.bridge = self.o.bridge
        self.o.pcibus.conf_space = self.o.pcicfg
        self.o.pcibus.io_space = self.o.pciio
        self.o.pcibus.memory_space = self.o.pcimem
        self.o.isp = pre_obj('isp$', 'ISP1040')
        self.o.isp.pci_bus = self.o.pcibus
        self.o.isp.scsi_id = self.scsi_id
        self.o.e2bus = pre_obj('e2bus$', 'cheerio-e2bus')
        self.o.e2bus.pci_bus = self.o.pcibus
        self.o.hme = pre_obj('hme$', 'cheerio-hme')
        self.o.hme.mac_address = mac_as_list(self.mac)
        self.o.hme.pci_bus = self.o.pcibus
        self.o.pcibus.pci_devices = [[0, 0, self.o.e2bus],
                                     [0, 1, self.o.hme],
                                     [4, 0, self.o.isp]]
        self.o.hme_prom_image = pre_obj('hmeprom$_image', 'image')
        self.o.hme_prom_image.size = 0x1000000
        self.o.hme_prom_image.files = [['cheerio_hme.fcode', 'ro', 0, 0x4c20]]
        self.o.hme_prom = pre_obj('hmeprom$', 'rom')
        self.o.hme_prom.image = self.o.hme_prom_image
        self.o.hme.expansion_rom = [self.o.hme_prom, 0x1000000, 0]
        self.o.isp_prom_image = pre_obj('ispprom$_image', 'image')
        self.o.isp_prom_image.size = 0x10000
        self.o.isp_prom_image.files = [['isp1040.fcode', 'ro', 0, 0xaa14]]
        self.o.isp_prom = pre_obj('ispprom$', 'rom')
        self.o.isp_prom.image = self.o.isp_prom_image
        self.o.isp.expansion_rom = [self.o.isp_prom, 0x10000, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.bridge]]]
        self.connector_info['ethernet'] = []
        self.connector_info['scsi-bus'] = [self.o.isp, self.scsi_id]

    def instantiation_done(self):
        component_object.instantiation_done(self)
        patch_hme_prom(self.o.hme_prom_image, self.mac)
    
    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.bridge.pci_bus = pci_bus

    def connect_scsi_bus(self, connector, bus):
        self.o.isp.scsi_bus = bus

    def connect_ethernet_link(self, connector, link):
        self.o.hme.link = link

    def disconnect_ethernet_link(self, connector):
        # TODO
        print "Ethernet disconnect not implemented"

register_component_class(
    sun_pci_hme_isp_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.'],
     ['scsi_id', Sim_Attr_Optional, 'i',
      'The ID on the SCSI bus.']])


### Sun QLC PCI Device


class sun_pci_qlc_component(component_object):
    classname = 'sun-pci-qlc'
    basename = 'scsi'
    description = ('The "sun-pci-qlc" component represents a PCI card '
                   'with a QLC Fibre-Channel SCSI controller for use in Sun '
                   'systems.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'fc-loop' : {'type' : 'simple-fc-loop', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : False, 'multi' : True}}

    def get_loop_id(self, idx):
        return self.loop_id

    def set_loop_id(self, val, idx):
        self.loop_id = val
        return Sim_Set_Ok

    def add_objects(self):
        self.used_loops = [self.loop_id]
        self.o.qlc = pre_obj('qlc$', 'ISP2200')
        self.o.qlc.loop_id = self.loop_id
        self.o.qlc_prom_image = pre_obj('qlcprom$_image', 'image')
        self.o.qlc_prom_image.size = 0x10000
        self.o.qlc_prom_image.files = [['isp2200.fcode', 'ro', 0, 0x1b2fc]]
        self.o.qlc_prom = pre_obj('qlcprom$', 'rom')
        self.o.qlc_prom.image = self.o.qlc_prom_image
        self.o.qlc.expansion_rom = [self.o.qlc_prom, 0x10000, 0]

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
    sun_pci_qlc_component,
    [['loop_id', Sim_Attr_Required, 'i',
      'The FC loop ID of the QLC controller.']])


### Sun Dual QLC PCI Device


class sun_pci_qlc_qlc_component(component_object):
    classname = 'sun-pci-qlc-qlc'
    basename = 'scsi'
    description = ('The "sun-pci-qlc-qlc" component represents a PCI card '
                   'with two QLC Fibre-Channel SCSI controller for use in Sun '
                   'systems.')
    connectors = {
        'pci-bus' : {'type' : 'pci-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'fc-loop0' : {'type' : 'simple-fc-loop', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : False, 'multi' : True},
        'fc-loop1' : {'type' : 'simple-fc-loop', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : False, 'multi' : True}}

    def get_loop_id0(self, idx):
        return self.loop_id0

    def set_loop_id0(self, val, idx):
        self.loop_id0 = val
        return Sim_Set_Ok

    def get_loop_id1(self, idx):
        return self.loop_id1

    def set_loop_id1(self, val, idx):
        self.loop_id1 = val
        return Sim_Set_Ok

    def add_objects(self):
        self.used_loops0 = [self.loop_id0]
        self.used_loops1 = [self.loop_id1]
        self.o.pcicfg = pre_obj('pcicfg$', 'memory-space')
        self.o.pciio = pre_obj('pciio$', 'memory-space')
        self.o.pcimem = pre_obj('pcimem$', 'memory-space')
        self.o.bridge = pre_obj('bridge$', 'i21152')
        self.o.pcibus = pre_obj('pcibus$', 'pci-bus')
        self.o.bridge.secondary_bus = self.o.pcibus
        self.o.pcibus.bridge = self.o.bridge
        self.o.pcibus.conf_space = self.o.pcicfg
        self.o.pcibus.io_space = self.o.pciio
        self.o.pcibus.memory_space = self.o.pcimem
        self.o.qlc0 = pre_obj('qlc$', 'ISP2200')
        self.o.qlc0.pci_bus = self.o.pcibus
        self.o.qlc0.loop_id = self.loop_id0
        self.o.qlc1 = pre_obj('qlc$', 'ISP2200')
        self.o.qlc1.pci_bus = self.o.pcibus
        self.o.qlc1.loop_id = self.loop_id1
        self.o.pcibus.pci_devices = [[4, 0, self.o.qlc0],
                                     [5, 0, self.o.qlc1]]
        self.o.qlc_prom_image = pre_obj('qlcprom$_image', 'image')
        self.o.qlc_prom_image.size = 0x10000
        self.o.qlc_prom_image.files = [['isp2200.fcode', 'ro', 0, 0x1b2fc]]
        self.o.qlc_prom = pre_obj('qlcprom$', 'rom')
        self.o.qlc_prom.image = self.o.qlc_prom_image
        self.o.qlc0.expansion_rom = [self.o.qlc_prom, 0x10000, 0]
        self.o.qlc1.expansion_rom = [self.o.qlc_prom, 0x10000, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.bridge]]]
        self.connector_info['fc-loop0'] = [self.o.qlc0]
        self.connector_info['fc-loop1'] = [self.o.qlc0]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.bridge.pci_bus = pci_bus

    def check_simple_fc_loop(self, connector, info):
        if connector == 'fc-loop0':
            used = self.used_loops0
        else:
            used = self.used_loops1
        if info >= 127:
            raise Exception, "Illegal loop ID 0x%x." % info
        if info in used:
            raise Exception, "Loop ID 0x%x already in use." % info
        used += [info]

    def connect_simple_fc_loop(self, connector, device, loop_id):
        pass

register_component_class(
    sun_pci_qlc_qlc_component,
    [['loop_id0', Sim_Attr_Required, 'i',
      'The FC loop ID of the first QLC controller.'],
     ['loop_id1', Sim_Attr_Required, 'i',
      'The FC loop ID of the second QLC controller.']])


### Sun Type 5 Keyboard


class sun_keyboard_component(component_object):
    classname = 'sun-type5-keyboard'
    basename = 'keyboard'
    description = ('The "sun-type5-keyboard" component represents a Sun Type '
                   '5 serial keyboard for use in Sun systems.')
    connectors = {
        'device'  : {'type' : 'serial', 'direction' : 'up',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'console' : {'type' : 'keyboard', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.kbd = pre_obj('kbd', 'sun-keyboard')

    def add_connector_info(self):
        self.connector_info['device'] = [None, self.o.kbd]
        self.connector_info['console'] = [self.o.kbd]

    def connect_serial(self, connector, link, port, name):
        if link:
            self.o.kbd.link = port
        else:
            self.o.kbd.device = port

    def disconnect_serial(self, connector):
        # TODO: self.o.kbd.link = None
        self.o.kbd.device = None

    def connect_keyboard(self, connector, console):
        pass

    def disconnect_keyboard(self, connector):
        # TODO
        print "keyboard disconnect not implemented"

register_component_class(sun_keyboard_component, [])


### Sun Type 5 Mouse


class sun_mouse_component(component_object):
    classname = 'sun-type5-mouse'
    basename = 'mouse'
    description = ('The "sun-type5-mouse" component represents a Sun Type '
                   '5 serial mouse for use in Sun systems.')
    connectors = {
        'device'  : {'type' : 'serial', 'direction' : 'up',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'console' : {'type' : 'mouse', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.mouse = pre_obj('mse', 'sun-mouse')

    def add_connector_info(self):
        self.connector_info['device'] = [None, self.o.mouse]
        self.connector_info['console'] = [self.o.mouse]

    def connect_serial(self, connector, link, port, name):
        if link:
            self.o.mouse.link = link
        else:
            self.o.mouse.device = port

    def disconnect_serial(self, connector):
        # TODO: self.o.mouse.link = None
        self.o.mouse.device = None

    def connect_mouse(self, connector, console):
        pass

    def disconnect_mouse(self, connector):
        # TODO
        print "mouse disconnect not implemented"

register_component_class(sun_mouse_component, [])
