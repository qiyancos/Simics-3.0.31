# MODULE: isa-components
# CLASS: std-super-io
# CLASS: ps2-keyboard-mouse
# CLASS: pc-dual-serial-ports
# CLASS: pc-quad-serial-ports
# CLASS: pc-floppy-controller
# CLASS: pc-single-parallel-port
# CLASS: isa-vga
# CLASS: isa-lance
# CLASS: sio-w83627hf
# CLASS: sio-lpc47m172

from sim_core import *
from components import *
import os

# Use the AM79C960-dml class instead of the AM79C960 class.
# Unsupported feature.
use_AM79C960_dml = False


### Super-IO Device


class super_io_component(component_object):
    classname = 'std-super-io'
    basename = 'sio'
    description = ('The "std-super-io" component represents a generic '
                   'Super I/O device with legacy PC devices such as two '
                   'serial ports, one PS/2 keyboard and mouse controller, one '
                   'floppy device and a parallel port')
    connectors = {
        'isa-bus' :     {'type' : 'isa-bus', 'direction' : 'up',
                         'empty_ok' : False, 'hotplug' : False,
                         'multi' : False},
        'reset' :       {'type' : 'x86-reset-bus', 'direction' : 'up',
                         'empty_ok' : True, 'hotplug' : False,
                         'multi' : False},
        'kbd-console' : {'type' : 'keyboard', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'mse-console' : {'type' : 'mouse', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'com1' :        {'type' : 'serial', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'com2' :        {'type' : 'serial', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.add_par_port = False

    def get_add_par_port(self, idx):
        return self.add_par_port

    def set_add_par_port(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.add_par_port = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.kbd = pre_obj('kbd$', 'i8042')
        self.o.kbd.kbd_irq_level = 1
        self.o.kbd.mouse_irq_level = 12
        self.o.fd0 = pre_obj('fd$', 'floppy-drive')
        self.o.fd1 = pre_obj('fd$', 'floppy-drive')
        self.o.flp = pre_obj('flp$', 'i82077')
        self.o.flp.dma_channel = 2
        self.o.flp.drives = [self.o.fd0, self.o.fd1]
        self.o.flp.irq_level = 6
        self.o.com1 = pre_obj('com1', 'NS16550')
        self.o.com1.interrupt_mask_out2 = 1
        self.o.com1.irq_level = 4
        self.o.com2 = pre_obj('com2', 'NS16550')
        self.o.com2.interrupt_mask_out2 = 1
        self.o.com2.irq_level = 3
        if self.add_par_port:
            self.o.prt = pre_obj('prt$', 'pc-parallel-port')
            #self.o.prt.irq_level = 7
            #self.o.prt.dma_channel = 4

    def add_connector_info(self):
        self.connector_info['isa-bus'] = ([], [[0x60, 0x64, 0x92,
                                                0x3f2, 0x3f4, 0x3f5, 0x3f7,
                                                0x2f8, 0x2f9, 0x2fa, 0x2fb, 
                                                0x2fc, 0x2fd, 0x2fe, 0x2ff,
                                                0x3f8, 0x3f9, 0x3fa, 0x3fb,
                                                0x3fc, 0x3fd, 0x3fe, 0x3ff,
                                                0x378, 0x379, 0x37a]])
        self.connector_info['com1'] = [None, self.o.com1, 'Console on com1']
        self.connector_info['com2'] = [None, self.o.com2, 'Console on com2']
        self.connector_info['reset'] = []
        self.connector_info['kbd-console'] = [self.o.kbd]
        self.connector_info['mse-console'] = [self.o.kbd]

    def connect_x86_reset_bus(self, connector, bus):
        self.o.kbd.reset_target = bus
    
    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        self.o.kbd.irq_dev = irq
        port_space.map += [[0x60, self.o.kbd, 0, 0, 1],
                           [0x64, self.o.kbd, 0, 4, 1],
                           [0x92, self.o.kbd, 0, 0x92-0x60, 1]] 
        self.o.flp.irq_dev = irq
        self.o.flp.dma_dev = dma
        port_space.map += [[0x3f2, self.o.flp, 0, 0, 1],
                           [0x3f4, self.o.flp, 0, 2, 1],
                           [0x3f5, self.o.flp, 0, 3, 1],
                           [0x3f7, self.o.flp, 0, 5, 1]]
        self.o.com1.irq_dev = irq
        self.o.com2.irq_dev = irq
        port_space.map += [
            [0x2f8, self.o.com2, 2, 0, 1],
            [0x2f9, self.o.com2, 2, 1, 1],
            [0x2fa, self.o.com2, 2, 2, 1],
            [0x2fb, self.o.com2, 2, 3, 1],
            [0x2fc, self.o.com2, 2, 4, 1],
            [0x2fd, self.o.com2, 2, 5, 1],
            [0x2fe, self.o.com2, 2, 6, 1],
            [0x2ff, self.o.com2, 2, 7, 1],
            [0x3f8, self.o.com1, 1, 0, 1],
            [0x3f9, self.o.com1, 1, 1, 1],
            [0x3fa, self.o.com1, 1, 2, 1],
            [0x3fb, self.o.com1, 1, 3, 1],
            [0x3fc, self.o.com1, 1, 4, 1],
            [0x3fd, self.o.com1, 1, 5, 1],
            [0x3fe, self.o.com1, 1, 6, 1],
            [0x3ff, self.o.com1, 1, 7, 1]]
        if self.add_par_port:
            #self.o.prt.irq_dev = irq
            #self.o.prt.dma_dev = irq
            port_space.map += [[0x378, self.o.prt, 0, 0, 1],
                               [0x379, self.o.prt, 0, 1, 1],
                               [0x37a, self.o.prt, 0, 2, 1]]

    def connect_keyboard(self, connector, console):
        pass

    def disconnect_keyboard(self, connector):
        # TODO
        print "keyboard disconnect not implemented"

    def connect_mouse(self, connector, console):
        pass

    def disconnect_mouse(self, connector):
        # TODO
        print "mouse disconnect not implemented"

    def connect_serial(self, connector, link, console):
        if connector == 'com1':
            if link:
                self.o.com1.link = link
            else:
                self.o.com1.console = console
        else:
            if link:
                self.o.com2.link = link
            else:
                self.o.com2.console = console

    def disconnect_serial(self, connector):
        if connector == 'com1':
            self.o.com1.link = None
            self.o.com1.console = None
        else:
            self.o.com2.link = None
            self.o.com2.console = None

register_component_class(
    super_io_component,
    [['add_par_port', Sim_Attr_Optional, 'b',
      'Set to TRUE to add a parallel port to the Super I/O device. Default is '
      'FALSE since the current implementation is a dummy device.']])


### Legacy PC PS/2 Keyboard and Mouse


class ps2_keyboard_mouse_component(component_object):
    classname = 'ps2-keyboard-mouse'
    basename = 'keyboard'
    description = ('The "ps2-keyboard-mouse" component represents the '
                   'PS/2 8042 keyboard controller with a connected 105 key '
                   'keyboard and three button mouse.')
    connectors = {
        'isa-bus'   : {'type' : 'isa-bus', 'direction' : 'up',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'reset'     : {'type' : 'x86-reset-bus', 'direction' : 'up',
                       'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'kbd-console' : {'type' : 'keyboard', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'mse-console' : {'type' : 'mouse', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.kbd = pre_obj('kbd$', 'i8042')
        self.o.kbd.kbd_irq_level = 1
        self.o.kbd.mouse_irq_level = 12

    def add_connector_info(self):
        self.connector_info['isa-bus'] = ([], [[0x60, 0x64, 0x92]])
        self.connector_info['reset'] = []
        self.connector_info['kbd-console'] = [self.o.kbd]
        self.connector_info['mse-console'] = [self.o.kbd]

    def connect_x86_reset_bus(self, connector, bus):
        self.o.kbd.reset_target = bus
    
    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        self.o.kbd.irq_dev = irq
        port_space.map += [[0x60, self.o.kbd, 0, 0, 1],
                           [0x64, self.o.kbd, 0, 4, 1],
                           [0x92, self.o.kbd, 0, 0x92-0x60, 1]] 

    def connect_keyboard(self, connector, console):
        pass

    def disconnect_keyboard(self, connector):
        # TODO
        print "keyboard disconnect not implemented"

    def connect_mouse(self, connector, console):
        pass

    def disconnect_mouse(self, connector):
        # TODO
        print "mouse disconnect not implemented"

register_component_class(ps2_keyboard_mouse_component, [])


### Legacy PC Floppy Controller


class floppy_controller_component(component_object):
    classname = 'pc-floppy-controller'
    basename = 'floppy_controller'
    description = ('The "pc-floppy-controller" component represents a legacy '
                   'pc floppy controller with two attached drives.')
    connectors = {
        'isa-bus' : {'type' : 'isa-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def add_objects(self):
        self.o.fd0 = pre_obj('fd$', 'floppy-drive')
        self.o.fd1 = pre_obj('fd$', 'floppy-drive')
        self.o.flp = pre_obj('flp$', 'i82077')
        self.o.flp.dma_channel = 2
        self.o.flp.drives = [self.o.fd0, self.o.fd1]
        self.o.flp.irq_level = 6

    def add_connector_info(self):
        self.connector_info['isa-bus'] =([], [[0x3f2, 0x3f4, 0x3f5, 0x3f7]])

    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        self.o.flp.irq_dev = irq
        self.o.flp.dma_dev = dma
        port_space.map += [[0x3f2, self.o.flp, 0, 0, 1],
                           [0x3f4, self.o.flp, 0, 2, 1],
                           [0x3f5, self.o.flp, 0, 3, 1],
                           [0x3f7, self.o.flp, 0, 5, 1]]

register_component_class(floppy_controller_component, [])


### Legacy Dual PC Serial Ports


class pc_dual_serial_ports_component(component_object):
    classname = 'pc-dual-serial-ports'
    basename = 'dual_uart'
    description = ('The "pc-dual-serial-ports" component represents two '
                   'PC compatible serial ports.')
    connectors = {
        'isa-bus' : {'type' : 'isa-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'com1'    : {'type' : 'serial', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'com2'    : {'type' : 'serial', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.com1 = pre_obj('com1', 'NS16550')
        self.o.com1.interrupt_mask_out2 = 1
        self.o.com1.irq_level = 4
        self.o.com2 = pre_obj('com2', 'NS16550')
        self.o.com2.interrupt_mask_out2 = 1
        self.o.com2.irq_level = 3

    def add_connector_info(self):
        self.connector_info['isa-bus'] = ([], [[0x2f8, 0x2f9, 0x2fa, 0x2fb, 
                                               0x2fc, 0x2fd, 0x2fe, 0x2ff,
                                               0x3f8, 0x3f9, 0x3fa, 0x3fb,
                                               0x3fc, 0x3fd, 0x3fe, 0x3ff]])
        self.connector_info['com1'] = [None, self.o.com1, 'Console on com1']
        self.connector_info['com2'] = [None, self.o.com2, 'Console on com2']

    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        self.o.com1.irq_dev = irq
        self.o.com2.irq_dev = irq
        port_space.map += [
            [0x2f8, self.o.com2, 2, 0, 1],
            [0x2f9, self.o.com2, 2, 1, 1],
            [0x2fa, self.o.com2, 2, 2, 1],
            [0x2fb, self.o.com2, 2, 3, 1],
            [0x2fc, self.o.com2, 2, 4, 1],
            [0x2fd, self.o.com2, 2, 5, 1],
            [0x2fe, self.o.com2, 2, 6, 1],
            [0x2ff, self.o.com2, 2, 7, 1],
            [0x3f8, self.o.com1, 1, 0, 1],
            [0x3f9, self.o.com1, 1, 1, 1],
            [0x3fa, self.o.com1, 1, 2, 1],
            [0x3fb, self.o.com1, 1, 3, 1],
            [0x3fc, self.o.com1, 1, 4, 1],
            [0x3fd, self.o.com1, 1, 5, 1],
            [0x3fe, self.o.com1, 1, 6, 1],
            [0x3ff, self.o.com1, 1, 7, 1]]
            
    def connect_serial(self, connector, link, console):
        if connector == 'com1':
            if link:
                self.o.com1.link = link
            else:
                self.o.com1.console = console
        else:
            if link:
                self.o.com2.link = link
            else:
                self.o.com2.console = console

    def disconnect_serial(self, connector):
        if connector == 'com1':
            self.o.com1.link = None
            self.o.com1.console = None
        else:
            self.o.com2.link = None
            self.o.com2.console = None

register_component_class(pc_dual_serial_ports_component, [])


### Legacy Quad PC Serial Ports


class pc_quad_serial_ports_component(pc_dual_serial_ports_component):
    classname = 'pc-quad-serial-ports'
    basename = 'quad_uart'
    description = ('The "pc-quad-serial-ports" component represents four '
                   'PC compatible serial ports.')
    connectors = pc_dual_serial_ports_component.connectors.copy()
    connectors['com3'] = {
        'type' : 'serial', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : True, 'multi' : False}
    connectors['com4'] = {
        'type' : 'serial', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : True, 'multi' : False}

    def add_objects(self):
        pc_dual_serial_ports_component.add_objects(self)
        self.o.com3 = pre_obj('com3', 'NS16550')
        self.o.com3.interrupt_mask_out2 = 1
        self.o.com3.irq_level = 4
        self.o.com4 = pre_obj('com4', 'NS16550')
        self.o.com4.interrupt_mask_out2 = 1
        self.o.com4.irq_level = 3

    def add_connector_info(self):
        pc_dual_serial_ports_component.add_connector_info(self)
        self.connector_info['isa-bus'] = ([],
                                          [self.connector_info['isa-bus'][1]
                                           + [0x2e8, 0x2e9, 0x2ea, 0x2eb,
                                              0x2ec, 0x2ed, 0x2ee, 0x2ef,
                                              0x3e8, 0x3e9, 0x3ea, 0x3eb,
                                              0x3ec, 0x3ed, 0x3ee, 0x3ef]])
        self.connector_info['com3'] = [None, self.o.com3, 'Console on com3']
        self.connector_info['com4'] = [None, self.o.com4, 'Console on com4']

    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        pc_dual_serial_ports_component.connect_isa_bus(self, connector,
                                                       port_space, mem_space,
                                                       irq, dma)
        self.o.com3.irq_dev = irq
        self.o.com4.irq_dev = irq
        port_space.map += [
            [0x2e8, self.o.com4, 2, 0, 1],
            [0x2e9, self.o.com4, 2, 1, 1],
            [0x2ea, self.o.com4, 2, 2, 1],
            [0x2eb, self.o.com4, 2, 3, 1],
            [0x2ec, self.o.com4, 2, 4, 1],
            [0x2ed, self.o.com4, 2, 5, 1],
            [0x2ee, self.o.com4, 2, 6, 1],
            [0x2ef, self.o.com4, 2, 7, 1],
            [0x3e8, self.o.com3, 1, 0, 1],
            [0x3e9, self.o.com3, 1, 1, 1],
            [0x3ea, self.o.com3, 1, 2, 1],
            [0x3eb, self.o.com3, 1, 3, 1],
            [0x3ec, self.o.com3, 1, 4, 1],
            [0x3ed, self.o.com3, 1, 5, 1],
            [0x3ee, self.o.com3, 1, 6, 1],
            [0x3ef, self.o.com3, 1, 7, 1]]
            
    def connect_serial(self, connector, link, console):
        if connector == 'com3':
            if link:
                self.o.com3.link = link
            else:
                self.o.com3.console = console
        elif connector == 'com4':
            if link:
                self.o.com4.link = link
            else:
                self.o.com4.console = console
        else:
            pc_dual_serial_ports_component.connect_serial(self, link,
                                                          connector, console)

    def disconnect_serial(self, connector):
        if connector == 'com3':
            self.o.com3.link = None
            self.o.com3.console = None
        elif connector == 'com4':
            self.o.com4.link = None
            self.o.com4.console = None
        else:
            pc_dual_serial_ports_component.disconnect_serial(self, connector)


register_component_class(pc_quad_serial_ports_component, [])


### Legacy PC Parallel Port


class pc_parallel_port_component(component_object):
    classname = 'pc-single-parallel-port'
    basename = 'parallel'
    description = ('The "pc-single-parallel-port" component represents a '
                   'PC compatible parallel port.')
    connectors = {
        'isa-bus' : {'type' : 'isa-bus', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def add_objects(self):
        self.o.prt = pre_obj('prt$', 'pc-parallel-port')
        #self.o.prt.irq_level = 7
        #self.o.prt.dma_channel = 4

    def add_connector_info(self):
        self.connector_info['isa-bus'] = ([], [[0x378, 0x379, 0x37a]])

    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        #self.o.prt.irq_dev = irq
        #self.o.prt.dma_dev = irq
        port_space.map += [[0x378, self.o.prt, 0, 0, 1],
                           [0x379, self.o.prt, 0, 1, 1],
                           [0x37a, self.o.prt, 0, 2, 1]]

register_component_class(pc_parallel_port_component, [])


### Legacy ISA VGA Adapter


class isa_vga_component(component_object):
    classname = 'isa-vga'
    basename = 'isa_vga'
    description = ('The "isa-vga" component represents an ISA bus based VGA '
                   'compatible graphics adapter.')
    connectors = {
        'isa-bus' : {'type' : 'isa-bus', 'direction' : 'up',
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
        if self.bios:
            self.o.vga_prom_image = pre_obj('vga$_prom_image', 'image')
            self.o.vga_prom_image.size = self.biossize
            self.o.vga_prom_image.files = [[self.bios,
                                            'ro', 0, self.biossize]]
            self.o.vga_prom = pre_obj('vga$_prom', 'rom')
            self.o.vga_prom.image = self.o.vga_prom_image
        self.o.vga_vram_image = pre_obj('vga$_vram_image', 'image')
        self.o.vga_vram_image.size = 0x40000
        self.o.vga = pre_obj('vga$', 'vga')
        self.o.vga.image = self.o.vga_vram_image

    def add_connector_info(self):
        self.connector_info['isa-bus'] = ([],
                                          [[0x3c0, 0x3c1, 0x3c2, 0x3c4, 0x3c5,
                                            0x3c6, 0x3c7, 0x3c8, 0x3c9, 0x3cc,
                                            0x3ce, 0x3cf, 0x3da, 0x3ba, 0x3b4,
                                            0x3b5, 0x3d4, 0x3d5]])
        self.connector_info['console'] = [self.o.vga]

    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        self.o.vga.memory_space = mem_space
        mem_space.map += [[0x0000a0000, self.o.vga,      1, 0, 0x20000]]
        if self.bios:
            mem_space.map += [[0x0000c0000, self.o.vga_prom, 0, 0, 0x08000]]
        port_space.map += [
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

register_component_class(isa_vga_component,
                         [['bios', Sim_Attr_Optional, 's',
                           'The VGA BIOS file to use.']])


### ISA Lance Network Adapter


class isa_lance_component(component_object):
    classname = 'isa-lance'
    basename = 'isa_lance'
    description = ('The "isa-lance" component represents an ISA bus based '
                   'Ethernet adapter.')
    connectors = {
        'isa-bus'  : {'type' : 'isa-bus', 'direction' : 'up',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet' : {'type' : 'ethernet-link', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.irq_level = 7
        self.port = 0x300

    def get_mac_address(self, idx):
        return self.mac

    def set_mac_address(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if len(mac_as_list(val)) != 6:
            return Sim_Set_Illegal_Value
        self.mac = val
        return Sim_Set_Ok

    def get_irq_level(self, idx):
        return self.irq_level

    def set_irq_level(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if val < 0 or val > 15:
            return Sim_Set_Illegal_Value
        self.irq_level = val
        return Sim_Set_Ok

    def get_base_port(self, idx):
        return self.port

    def set_base_port(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if val < 0 or val > 0xffff:
            return Sim_Set_Illegal_Value
        self.port = val
        return Sim_Set_Ok

    def add_objects(self):
        if use_AM79C960_dml:
                self.o.lance = pre_obj('lance$', 'AM79C960-dml')
        else:
                self.o.lance = pre_obj('lance$', 'AM79C960')
        self.o.lance.irq_level = self.irq_level
        self.o.lance.mac_address = self.mac

    def add_connector_info(self):
        self.connector_info['isa-bus'] = (
            [],
            [[self.port + 0x00, self.port + 0x01, self.port + 0x02,
              self.port + 0x03, self.port + 0x04, self.port + 0x05,
              self.port + 0x06, self.port + 0x07, self.port + 0x08,
              self.port + 0x09, self.port + 0x0a, self.port + 0x0b,
              self.port + 0x0c, self.port + 0x0d, self.port + 0x0e,
              self.port + 0x0f, self.port + 0x10, self.port + 0x12,
              self.port + 0x14, self.port + 0x16]])
        self.connector_info['ethernet'] = []

    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        self.o.lance.memory = mem_space
        self.o.lance.irq_dev = irq
        port_space.map += [
            [self.port + 0x00, self.o.lance, 0, 0x00, 1],
            [self.port + 0x01, self.o.lance, 0, 0x01, 1],
            [self.port + 0x02, self.o.lance, 0, 0x02, 1],
            [self.port + 0x03, self.o.lance, 0, 0x03, 1],
            [self.port + 0x04, self.o.lance, 0, 0x04, 1],
            [self.port + 0x05, self.o.lance, 0, 0x05, 1],
            [self.port + 0x06, self.o.lance, 0, 0x06, 1],
            [self.port + 0x07, self.o.lance, 0, 0x07, 1],
            [self.port + 0x08, self.o.lance, 0, 0x08, 1],
            [self.port + 0x09, self.o.lance, 0, 0x09, 1],
            [self.port + 0x0a, self.o.lance, 0, 0x0a, 1],
            [self.port + 0x0b, self.o.lance, 0, 0x0b, 1],
            [self.port + 0x0c, self.o.lance, 0, 0x0c, 1],
            [self.port + 0x0d, self.o.lance, 0, 0x0d, 1],
            [self.port + 0x0e, self.o.lance, 0, 0x0e, 1],
            [self.port + 0x0f, self.o.lance, 0, 0x0f, 1],
            [self.port + 0x10, self.o.lance, 0, 0x10, 2],
            [self.port + 0x12, self.o.lance, 0, 0x12, 2],
            [self.port + 0x14, self.o.lance, 0, 0x14, 2],
            [self.port + 0x16, self.o.lance, 0, 0x16, 2]]

    def connect_ethernet_link(self, connector, link):
        self.o.lance.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.lance.link = None

register_component_class(
    isa_lance_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.'],
     ['irq_level', Sim_Attr_Optional, 'i',
      'The interrupt level for the Lance device, default is 7.'],
     ['base_port', Sim_Attr_Optional, 'i',
      'The starting port number in I/O space. The default port is 0x300, and '
      'the mapping is 0x17 bytes large.']])


### Winbond W83627HF I/O


class winbond_w83627hf_component(super_io_component):
    classname = 'sio-w83627hf'
    basename = 'sio'
    description = 'Winbond W83627HF I/O.'

    connectors = super_io_component.connectors.copy()
    connectors['i2c-bus'] = {'type' : 'i2c-bus', 'direction' : 'up',
                             'empty_ok' : False, 'hotplug' : False,
                             'multi' : False}

    def add_objects(self):
        self.add_par_port = True
        super_io_component.add_objects(self)
        self.o.sio = pre_obj('sio$', 'w83627hf')
        self.o.sio.kbc = self.o.kbd
        self.o.sio.fdc = self.o.flp
        self.o.sio.prt = self.o.prt
        self.o.sio.uart_a = self.o.com1
        self.o.sio.uart_b = self.o.com2

    def add_connector_info(self):
        super_io_component.add_connector_info(self)
        self.connector_info['i2c-bus'] = []
        self.connector_info['isa-bus'] = (
            [],
            [self.connector_info['isa-bus'][1][0]
             + [0x2e, 0x395, 0x396]])

    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        super_io_component.connect_isa_bus(self, connector, port_space,
                                           mem_space, irq, dma)
        port_space.map += [[0x2e, self.o.sio, 1, 0, 1],
                           [0x2f, self.o.sio, 1, 1, 1]]
        self.o.sio.lpc_space = port_space

    def connect_i2c_bus(self, connector, bus):
        self.o.sio.i2c_bus = bus

register_component_class(winbond_w83627hf_component, [])


### SMSC LPC47M172 Super I/O

class smsc_lpc47m172_component(super_io_component):
    classname = 'sio-lpc47m172'
    basename = 'sio'
    description = 'SMSC LPC47M172 Super I/O.'

    connectors = super_io_component.connectors.copy()

    def get_ld_num(self, idx):
        return self.ld_num

    def set_ld_num(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.ld_num = val
        return Sim_Set_Ok

    def add_objects(self):
        self.add_par_port = True
        super_io_component.add_objects(self)
        self.o.sio = pre_obj('sio$', 'LPC47M172')
        self.o.sio.global_regs_test7 = self.ld_num
        self.o.sio.flp = self.o.flp
        self.o.sio.kbd = self.o.kbd
        self.o.sio.com1 = self.o.com1
        self.o.sio.com2 = self.o.com2
        self.o.sio.prt = self.o.prt

    def add_connector_info(self):
        super_io_component.add_connector_info(self)
        self.connector_info['isa-bus'] = (
            [],
            [self.connector_info['isa-bus'][1][0]
             + [0x2e, 0x395, 0x396]])

    def connect_isa_bus(self, connector, port_space, mem_space, irq, dma):
        super_io_component.connect_isa_bus(self, connector, port_space,
                                           mem_space, irq, dma)
        self.o.sio.isa_bus = port_space

register_component_class(smsc_lpc47m172_component,
                         [['ld_num', Sim_Attr_Required, 'i',
                           'The setting of the LD_NUM bit.']])
