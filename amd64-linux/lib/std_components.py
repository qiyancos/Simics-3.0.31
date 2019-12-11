# MODULE: std-components
# CLASS: std-scsi-bus
# CLASS: std-scsi-disk
# CLASS: std-scsi-cdrom
# CLASS: std-ide-disk
# CLASS: std-ide-cdrom
# CLASS: std-pcmcia-flash-disk
# CLASS: std-text-console
# CLASS: std-server-console
# CLASS: std-host-serial-console
# CLASS: std-text-graphics-console
# CLASS: std-graphics-console
# CLASS: simple-fc-disk
# CLASS: std-ethernet-link
# CLASS: std-serial-link
# CLASS: std-service-node
# CLASS: std-ms1553-link
# CLASS: std-etg
# CLASS: dummy-component

from sim_core import *
from components import *
import sim

# The first CD has id 1 and the first disk id 2 (for backward compatibility
# reasons) then simply assign new numbers

ide_serial_number = 3

# Standard CIS for an PCMCIA Flash/IDE disk

ide_cis = (
    0x01, 0x03, 0xd9, 0x01, 0xff, 0x1c, 0x04, 0x03, 0xd9, 0x01, 0xff, 0x18,
    0x02, 0xdf, 0x01, 0x20, 0x04, 0x01, 0x4e, 0x00, 0x02, 0x15, 0x2b, 0x04,
    0x01, 0x56, 0x69, 0x6b, 0x69, 0x6e, 0x67, 0x20, 0x41, 0x54, 0x41, 0x20,
    0x46, 0x6c, 0x61, 0x73, 0x68, 0x20, 0x43, 0x61, 0x72, 0x64, 0x20, 0x20,
    0x20, 0x20, 0x00, 0x53, 0x54, 0x4f, 0x52, 0x4d, 0x20, 0x20, 0x00, 0x53,
    0x54, 0x42, 0x4d, 0x30, 0x00, 0xff, 0x21, 0x02, 0x04, 0x01, 0x22, 0x02,
    0x01, 0x01, 0x22, 0x03, 0x02, 0x04, 0x5f, 0x1a, 0x05, 0x01, 0x03, 0x00,
    0x02, 0x0f, 0x1b, 0x0b, 0xc0, 0x40, 0xa1, 0x27, 0x55, 0x4d, 0x5d, 0x75,
    0x08, 0x00, 0x21, 0x1b, 0x06, 0x00, 0x01, 0x21, 0xb5, 0x1e, 0x4d, 0x1b,
    0x0d, 0xc1, 0x41, 0x99, 0x27, 0x55, 0x4d, 0x5d, 0x75, 0x64, 0xf0, 0xff,
    0xff, 0x21, 0x1b, 0x06, 0x01, 0x01, 0x21, 0xb5, 0x1e, 0x4d, 0x1b, 0x12,
    0xc2, 0x41, 0x99, 0x27, 0x55, 0x4d, 0x5d, 0x75, 0xea, 0x61, 0xf0, 0x01,
    0x07, 0xf6, 0x03, 0x01, 0xee, 0x21, 0x1b, 0x06, 0x02, 0x01, 0x21, 0xb5,
    0x1e, 0x4d, 0x1b, 0x12, 0xc3, 0x41, 0x99, 0x27, 0x55, 0x4d, 0x5d, 0x75,
    0xea, 0x61, 0x70, 0x01, 0x07, 0x76, 0x03, 0x01, 0xee, 0x21, 0x1b, 0x06,
    0x03, 0x01, 0x21, 0xb5, 0x1e, 0x4d, 0x14)


### SCSI Bus


class scsi_bus_component(component_object):
    classname = 'std-scsi-bus'
    basename = 'scsi_bus'
    description = ('The "std-scsi-bus" component represents a 16 slot SCSI '
                   'bus.')
    connectors = {
        'scsi-bus' : {'type' : 'scsi-bus', 'direction' : 'any',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : True}}

    def add_objects(self):
        self.o.sb = pre_obj('sb$', 'scsi-bus')
        self.o.sb.targets = []

    def add_connector_info(self):
        self.connector_info['scsi-bus'] = [self.o.sb]

    def check_scsi_bus(self, connector, tgt, id):
        if id < 0 or id > 15:
            raise Exception, "Illegal SCSI id %d" % id
        if len ([x for x in self.o.sb.targets if x[0] == id]):
            # TODO: change to warning when we handle IDs correctly"
            raise Exception, "SCSI ID %d is already used." % id

    def connect_scsi_bus(self, connector, tgt, id):
        tgts = self.o.sb.targets
        tgts += [[id, tgt, 0]]
        self.o.sb.targets = tgts

register_component_class(scsi_bus_component, [])


### SCSI Disk


class scsi_disk_component(component_object):
    classname = 'std-scsi-disk'
    basename = 'scsi_disk'
    description = ('The "std-scsi-disk" component represents a SCSI-2 disk.')
    connectors = {
        'scsi-bus' : {'type' : 'scsi-bus', 'direction' : 'up',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.file = None

    def get_size(self, idx):
        return self.size

    def set_size(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.size = val
        return Sim_Set_Ok

    def get_file(self, idx):
        return self.file

    def set_file(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.file = val
        return Sim_Set_Ok

    def get_scsi_id(self, idx):
        return self.scsi_id

    def set_scsi_id(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.scsi_id = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.sd_image = pre_obj('sd$_image', 'image')
        self.o.sd_image.size = self.size
        if self.file:
            self.o.sd_image.files = [[self.file, 'ro', 0, self.size, 0]]
        self.o.sd = pre_obj('sd$', 'scsi-disk')
        self.o.sd.image = self.o.sd_image
        self.o.sd.geometry = [self.size / 512, 1, 1]
        self.o.sd.synchronous_support = 1
        self.o.sd.scsi_target = self.scsi_id

    def add_connector_info(self):
        self.connector_info['scsi-bus'] = [self.o.sd, self.scsi_id]

    def connect_scsi_bus(self, connector, bus):
        self.o.sd.scsi_bus = bus

register_component_class(
    scsi_disk_component,
    [['scsi_id', Sim_Attr_Required, 'i',
      'The ID on the SCSI bus.'],
     ['size', Sim_Attr_Required, 'i',
      'The size of the SCSI disk in bytes.'],
     ['file', Sim_Attr_Optional, 's',
      'File with disk contents for the full disk Either a raw file '
      'or a CRAFF file.']])


### SCSI CD-ROM


class scsi_cdrom_component(component_object):
    classname = 'std-scsi-cdrom'
    basename = 'scsi_cdrom'
    description = ('The "std-scsi-cdrom" component represents a SCSI-2 '
                   'CD-ROM.')
    connectors = {
        'scsi-bus' : {'type' : 'scsi-bus', 'direction' : 'up',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def get_scsi_id(self, idx):
        return self.scsi_id

    def set_scsi_id(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.scsi_id = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.cd = pre_obj('cd$', 'scsi-cdrom')
        self.o.cd.scsi_target = self.scsi_id

    def add_connector_info(self):
        self.connector_info['scsi-bus'] = [self.o.cd, self.scsi_id]

    def connect_scsi_bus(self, connector, bus):
        self.o.cd.scsi_bus = bus

register_component_class(
    scsi_cdrom_component,
    [['scsi_id', Sim_Attr_Required, 'i',
      'The ID on the SCSI bus.']])


### Simple FC Disk


class simple_fc_disk_component(component_object):
    classname = 'simple-fc-disk'
    basename = 'fc_disk'
    description = ('The "simple-fc-disk" component represents a SCSI-2 disk '
                   'for use with Fibre-Channel SCSI controllers using the '
                   'simplified FC protocol in Simics.')
    connectors = {'fc-loop' : {'type' : 'simple-fc-loop', 'direction' : 'up',
                               'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.file = None

    def get_size(self, idx):
        return self.size

    def set_size(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.size = val
        return Sim_Set_Ok

    def get_file(self, idx):
        return self.file

    def set_file(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.file = val
        return Sim_Set_Ok

    def get_loop_id(self, idx):
        return self.loop_id

    def set_loop_id(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.loop_id = val
        return Sim_Set_Ok

    def get_node_name(self, idx):
        return self.node_name

    def set_node_name(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.node_name = val
        return Sim_Set_Ok

    def get_port_name(self, idx):
        return self.port_name

    def set_port_name(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.port_name = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.image = pre_obj('fc$_image', 'image')
        self.o.image.size = self.size
        if self.file:
            self.o.image.files = [[self.file, 'ro', 0, self.size, 0]]
        self.o.disk = pre_obj('fc$', 'fc-disk')
        self.o.disk.image = self.o.image
        self.o.disk.geometry = [self.size / 512, 1, 1]
        self.o.disk.loop_id = self.loop_id
        self.o.disk.node_name = self.node_name
        self.o.disk.port_name = self.port_name

    def add_connector_info(self):
        self.connector_info['fc-loop'] = ([self.o.disk, self.loop_id],
                                          [self.loop_id])

    def connect_simple_fc_loop(self, connector, controller):
        self.o.disk.fc_controller = controller

register_component_class(
    simple_fc_disk_component,
    [['size', Sim_Attr_Required, 'i',
      'The size of the FC disk in bytes.'],
     ['file', Sim_Attr_Optional, 's',
      'File with disk contents for the full disk Either a raw file '
      'or a CRAFF file.'],
     ['loop_id', Sim_Attr_Required, 'i',
      'The loop ID for the FC disk.'],
     ['node_name', Sim_Attr_Required, 'i',
      'The node name for the FC disk.'],
     ['port_name', Sim_Attr_Required, 'i',
      'The port name for the FC disk.']])


### IDE Disk


class ide_disk_component(component_object):
    classname = 'std-ide-disk'
    basename = 'ide_disk'
    description = ('The "std-ide-disk" component represents an IDE disk.')
    connectors = {
        'ide-slot' : {'type' : 'ide-slot', 'direction' : 'up',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False}}
    first_ide_disk = 1

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.file = None

    def get_size(self, idx):
        return self.size

    def set_size(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.size = val
        self.geometry = [min(val / (16 * 63 * 512), 16383), 16, 63]
        return Sim_Set_Ok

    def get_file(self, idx):
        return self.file

    def set_file(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.file = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.hd_image = pre_obj('disk$_image', 'image')
        self.o.hd_image.size = self.size
        if self.file:
            self.o.hd_image.files = [[self.file, 'ro', 0, self.size, 0]]
        self.o.hd = pre_obj('disk$', 'ide-disk')
        self.o.hd.image = self.o.hd_image
        self.o.hd.disk_sectors = self.size / 512
        self.o.hd.disk_cylinders = self.geometry[0]
        self.o.hd.disk_heads = self.geometry[1]
        self.o.hd.disk_sectors_per_track = self.geometry[2]
        if ide_disk_component.first_ide_disk:
            ide_disk_component.first_ide_disk = 0
            serial_number = 2
        else:
            global ide_serial_number
            serial_number = ide_serial_number
            ide_serial_number += 1
        self.o.hd.serial_number = " VT%05d" % serial_number

    def add_connector_info(self):
        self.connector_info['ide-slot'] = [self.o.hd]

    def connect_ide_slot(self, connector):
        pass

register_component_class(
    ide_disk_component,
    [['size', Sim_Attr_Required, 'i',
      'The size of the IDE disk in bytes.'],
     ['file', Sim_Attr_Optional, 's',
      'File with disk contents for the full disk Either a raw file '
      'or a CRAFF file.']])


### IDE CD-ROM


class ide_cdrom_component(component_object):
    classname = 'std-ide-cdrom'
    basename = 'ide_cdrom'
    description = ('The "std-ide-cdrom" component represents an IDE ATAPI '
                   'CD-ROM.')
    connectors = {
        'ide-slot' : {'type' : 'ide-slot', 'direction' : 'up',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False}}
    first_ide_cdrom = 1

    def add_objects(self):
        self.o.cd = pre_obj('cd$', 'ide-cdrom')
        if ide_cdrom_component.first_ide_cdrom:
            ide_cdrom_component.first_ide_cdrom = 0
            serial_number = 1
        else:
            global ide_serial_number
            serial_number = ide_serial_number
            ide_serial_number += 1
        self.o.cd.serial_number = " VT%05d" % serial_number

    def add_connector_info(self):
        self.connector_info['ide-slot'] = [self.o.cd]

    def connect_ide_slot(self, connector):
        pass

register_component_class(ide_cdrom_component, [])


### PCMCIA Flash Disk

# list of "small" known disk ageometries
known_geometries = {  94080: ( 735,  4, 32),
                     125440: ( 490,  8, 32),  # SDCFJ-64-388
                     250880: ( 980,  8, 32),  # SDCFJ-128-388
                     501760: ( 980, 16, 32),  # SDCFJ-256-388
                    1000944: ( 993, 16, 63),  # SDCFJ-512-388
                    2064384: (2048, 16, 63),  # SDCFJ-1024-388
                    3931200: (3900, 16, 63)
}

class pcmcia_flash_disk_component(component_object):
    classname = 'std-pcmcia-flash-disk'
    basename = 'flash_disk'
    description = ('The "std-pcmcia-flash-disk" component represents a PCMCIA '
                   'Flash disk.')
    connectors = {
        'pcmcia-slot' : {
        'type' : 'pcmcia-slot', 'direction' : 'up',
        'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.file = None

    def get_size(self, idx):
        return self.size

    def set_size(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.size = val
        sects = self.size / 512
        if sects >= 16 * 63 * 16363:
            self.geometry = (16383, 16, 63)
        else:
            if known_geometries.has_key(sects):
                self.geometry = known_geometries[sects]
            else:
                s = sects / (16 * 63)
                if s * 16 * 63 != sects:
                    print "No exact disk geometry calucated, set manually"
                self.geometry = (s, 16, 63)
        return Sim_Set_Ok

    def get_file(self, idx):
        return self.file

    def set_file(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.file = val
        return Sim_Set_Ok

    def add_objects(self):
        global ide_serial_number
        self.o.hd_image = pre_obj('disk$_image', 'image')
        self.o.hd_image.size = self.size
        if self.file:
            self.o.hd_image.files = [[self.file, 'ro', 0, self.size, 0]]
        self.o.hd = pre_obj('disk$', 'ide-disk')
        self.o.hd.image = self.o.hd_image
        self.o.hd.disk_sectors = self.size / 512
        self.o.hd.disk_cylinders = self.geometry[0]
        self.o.hd.disk_heads = self.geometry[1]
        self.o.hd.disk_sectors_per_track = self.geometry[2]
        self.o.hd.serial_number = " VT%05d" % ide_serial_number
        ide_serial_number += 1
        self.o.ide = pre_obj('pcmcia_ide$', 'ide')
        self.o.ide.lba_mode = 1
        self.o.ide.primary = 1
        self.o.ide.interrupt_delay = 0.000001
        self.o.ide.master = self.o.hd
        self.o.cis_image = pre_obj('cis$_image', 'image')
        self.o.cis_image.size = 0x300
        self.o.cis = pre_obj('cis$', 'rom')
        self.o.cis.image = self.o.cis_image
        self.o.attr_space = pre_obj('pcmcia_attr_space$', 'memory-space')
        # Last register at 0x206 the following bytes must be unmapped.
        self.o.attr_space.map = [[0x0, self.o.cis, 0, 0, 0x208]]
        #
        # "True IDE-mode" mappings are not supported
        #
        self.o.cmn_space = pre_obj('pcmcia_common_space$', 'memory-space')
        self.o.io_space = pre_obj('pcmcia_io_space$', 'memory-space')
        io_ide_map = [[0x000, self.o.ide, 0, 0x0, 8],
                      [0x008, self.o.ide, 0, 0x0, 2],
                      [0x00d, self.o.ide, 0, 0x1, 1],
                      [0x00e, self.o.ide, 0, 0x8, 1]]
        mem_ide_map = [[0x000, self.o.ide, 0, 0x0, 8],
                       [0x008, self.o.ide, 0, 0x0, 2],
                       [0x00d, self.o.ide, 0, 0x1, 1],
                       [0x00e, self.o.ide, 0, 0x8, 1]]
        for i in range(0x400, 0x800, 2):
            mem_ide_map.append([i, self.o.ide, 0, 0x0, 2])
        self.o.cmn_space.map = mem_ide_map
        self.o.io_space.map = io_ide_map

    def add_connector_info(self):
        self.connector_info['pcmcia-slot'] = [self.o.attr_space,
                                              self.o.cmn_space,
                                              self.o.io_space]

    def instantiation_done(self):
        component_object.instantiation_done(self)
        for i in range(len(ide_cis)):
            self.o.attr_space.iface.memory_space.write(self.o.attr_space,
                                                       None,
                                                       i * 2,
                                                       (ide_cis[i], ), 1)
        # Fake some attribute space registers
        self.o.attr_space.iface.memory_space.write(self.o.attr_space,
                                                   None,
                                                   0x204, (0x2e, ), 1)

    def connect_pcmcia_slot(self, connector, bridge, slot_id):
        self.o.ide.irq_dev = bridge
        self.o.ide.irq_level = slot_id

    def disconnect_pcmcia_slot(self, connector):
        self.o.ide.irq_dev = None

register_component_class(
    pcmcia_flash_disk_component,
    [['size', Sim_Attr_Required, 'i',
      'The size of the IDE disk in bytes.'],
     ['file', Sim_Attr_Optional, 's',
      'File with disk contents for the full disk Either a raw file '
      'or a CRAFF file.']])


### Text Console


class text_console_component(component_object):
    classname = 'std-text-console'
    basename = 'text_console'
    description = ('The "std-text-console" component represents a serial text '
                   'console.')
    connectors = {
        'serial' : {'type' : 'serial', 'direction' : 'up',
                    'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        # self.title is not used once an object has been created
        self.title = 'Console - not connected'
        self.user_title = 0
        self.bg_color = "gray"
        self.fg_color = "black"
        self.width = 80
        self.height = 24
        self.vt_height = 24
        self.x11_font = '6x10'
        self.win32_font = 'Lucida Console:Regular:10'

    def get_title(self, idx):
        try:
            return self.o.con.title
        except:
            return self.title

    def set_title(self, val, idx):
        try:
            if self.o.con.configured or isinstance(self.o.con, pre_obj):
                self.o.con.title = val
        finally:
            self.title = val
            self.user_title = 1
            return Sim_Set_Ok

    def get_bg_color(self, idx):
        return self.bg_color

    def set_bg_color(self, val, idx):
        try:
            if self.o.con.configured or isinstance(self.o.con, pre_obj):
                self.o.con.bg_color = val
        finally:
            self.bg_color = val
            return Sim_Set_Ok

    def get_fg_color(self, idx):
        return self.fg_color

    def set_fg_color(self, val, idx):
        try:
            if self.o.con.configured or isinstance(self.o.con, pre_obj):
                self.o.con.fg_color = val
        finally:
            self.fg_color = val
            return Sim_Set_Ok

    def get_x11_font(self, idx):
        return self.x11_font

    def set_x11_font(self, val, idx):
        try:
            if self.o.con.configured or isinstance(self.o.con, pre_obj):
                self.o.con.x11_font = val
        finally:
            self.x11_font = val
            return Sim_Set_Ok

    def get_win32_font(self, idx):
        return self.win32_font

    def set_win32_font(self, val, idx):
        try:
            if self.o.con.configured or isinstance(self.o.con, pre_obj):
                self.o.con.win32_font = val
        finally:
            self.win32_font = val
            return Sim_Set_Ok

    def get_width(self, idx):
        return self.width

    def set_width(self, val, idx):
        try:
            if self.o.con.configured or isinstance(self.o.con, pre_obj):
                self.o.con.width = val
        finally:
            self.width = val
            return Sim_Set_Ok

    def get_height(self, idx):
        return self.height

    def set_height(self, val, idx):
        try:
            if self.o.con.configured or isinstance(self.o.con, pre_obj):
                self.o.con.height = val
        finally:
            self.height = val
            return Sim_Set_Ok

    def add_objects(self):
        self.o.con = pre_obj('con$', 'text-console')
        self.o.con.width = self.width
        self.o.con.height = self.height
        self.o.con.bg_color = self.bg_color
        self.o.con.fg_color = self.fg_color
        self.o.con.title = self.title
        self.o.con.vt_height = self.vt_height
        self.o.con.output_timeout = 20

    def add_connector_info(self):
        self.connector_info['serial'] = [None, self.o.con]

    def connect_serial(self, connector, link, port, name = None):
        if link:
            self.o.con.link = link
            if not self.user_title:
                self.o.con.title = 'Console - %s' % link.name
        else:
            self.o.con.device = port
            if not self.user_title:
                self.o.con.title = 'Serial Console on %s' % name

    def disconnect_serial(self, connector):
        self.o.con.title = 'Console - not connected'
        self.o.con.device = None
        self.o.con.link = None

register_component_class(
    text_console_component,
    [['title', Sim_Attr_Optional, 's',
      'The Window title.'],
     ['bg_color', Sim_Attr_Optional, 's',
      'The background color.'],
     ['fg_color', Sim_Attr_Optional, 's',
      'The foreground color.'],
     ['x11_font', Sim_Attr_Optional, 's',
      'Font to use in the console when using X11 (Linux/Solaris host).'],
     ['win32_font', Sim_Attr_Optional, 's',
      'Font to use in the console on Windows host.'],
     ['width', Sim_Attr_Optional, 'i',
      'The width of the console window.'],
     ['height', Sim_Attr_Optional, 'i',
      'The height of the console window.']])


### Server Console


class server_console_component(component_object):
    classname = 'std-server-console'
    basename = 'server_console'
    description = ('The "std-server-console" component represents a serial '
                   'console accessible from the host using telnet.')
    connectors = {
        'serial' : {'type' : 'serial', 'direction' : 'up',
                    'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def get_telnet_port(self, idx):
        return self.port

    def set_telnet_port(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.port = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.con = pre_obj('con$', 'server-console')
        self.o.con.port = self.port
        self.o.con.buffer_until_connection = 0
        self.o.con.device = None

    def add_connector_info(self):
        self.connector_info['serial'] = [None, self.o.con]

    def connect_serial(self, connector, link, port, name = None):
        if link:
            self.o.con.link = link
        else:
            self.o.con.device = port

    def disconnect_serial(self, connector):
        # TODO: self.o.con.link = None
        self.o.con.device = None

register_component_class(
    server_console_component,
    [['telnet_port', Sim_Attr_Required, 'i',
      'TCP/IP port to connect the telnet service of the '
      'console to.']])


### Host Serial Console


class host_serial_console_component(component_object):
    classname = 'std-host-serial-console'
    basename = 'host_serial_console'
    description = ('The "std-host-serial console" component represents a '
                   'serial console accessible from the host as a virtual '
                   'serial port. On Windows a COM port is used and on Unix '
                   'a pty (pseudo-terminal).')
    connectors = {
        'serial' : {'type' : 'serial', 'direction' : 'up',
                    'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.con = pre_obj('con$', 'host-serial-console')

    def add_connector_info(self):
        self.connector_info['serial'] = [None, self.o.con]

    def connect_serial(self, connector, link, port, name = None):
        self.o.con.device = port

    def disconnect_serial(self, connector):
        self.o.con.device = None

register_component_class(
    host_serial_console_component,
    [])


### Text Graphics Console


class text_graphics_console_component(text_console_component):
    classname = 'std-text-graphics-console'
    basename = 'text_gfx_console'
    description = ('The "std-text-graphics-console" component represents a '
                   'text console for use with VGA instead of a graphics '
                   'console.')
    connectors = {
        'device'   : {'type' : 'graphics-console', 'direction' : 'up',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'keyboard' : {'type' : 'keyboard', 'direction' : 'up',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        text_console_component.__init__(self, parse_obj)
        self.vt_height = 25
        self.height = 25

    def add_objects(self):
        text_console_component.add_objects(self)

    def add_connector_info(self):
        text_console_component.add_connector_info(self)
        del self.connector_info['serial']
        self.connector_info['device'] = [self.o.con]
        self.connector_info['keyboard'] = [self.o.con]
        self.o.con.title = 'Textual Graphics Console'

    def connect_graphics_console(self, connector, video):
        pass

    def disconnect_graphics_console(self, connector):
        # TODO
        print "graphics console disconnect not implemented"

    def connect_keyboard(self, connector, keyboard):
        self.o.con.device = keyboard

    def disconnect_keyboard(self, connector):
        # TODO
        print "keyboard disconnect not implemented"

register_component_class(text_graphics_console_component, [])


### Graphics Console


class graphics_console_component(component_object):
    classname = 'std-graphics-console'
    basename = 'gfx_console'
    description = ('The "std-graphics-console" component represents a '
                   'graphical console for displaying output from a simulated '
                   'graphics adapters and getting input for mouse and '
                   'keyboard devices.')
    connectors = {
        'device'   : {'type' : 'graphics-console', 'direction' : 'up',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'mouse'    : {'type' : 'mouse', 'direction' : 'up',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'keyboard' : {'type' : 'keyboard', 'direction' : 'up',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.window = True

    def add_objects(self):
        self.o.con = pre_obj('con$', 'gfx-console')
        self.o.con.x_size = 640
        self.o.con.y_size = 400
        self.o.con.try_open = self.window

    def get_window(self, idx):
        return self.window

    def set_window(self, val, idx):
        if self.obj.instantiated and self.obj.configured:
            return Sim_Set_Illegal_Value
        self.window = val
        if self.obj.configured:
            self.o.con.try_open = val
        return Sim_Set_Ok

    def add_connector_info(self):
        self.connector_info['device'] = [self.o.con]
        self.connector_info['keyboard'] = [self.o.con]
        self.connector_info['mouse'] = [self.o.con]

    def connect_graphics_console(self, connector, video):
        self.o.con.video = video

    def disconnect_graphics_console(self, connector):
        # TODO
        print "graphics console disconnect not implemented"

    def connect_keyboard(self, connector, keyboard):
        self.o.con.keyboard = keyboard

    def connect_mouse(self, connector, mouse):
        self.o.con.mouse = mouse

    def disconnect_keyboard(self, connector):
        # TODO
        print "keyboard disconnect not implemented"

    def disconnect_mouse(self, connector):
        # TODO
        print "mouse disconnect not implemented"

register_component_class(
    graphics_console_component,
    [['window', Sim_Attr_Optional, 'b',
      'Try to open window if TRUE (default). FALSE disabled the window.']])


### Ethernet Link


class ethernet_link_component(component_object):
    classname = 'std-ethernet-link'
    basename = 'ethernet_link'
    description = ('The "std-ethernet-link" component represents a standard '
                   'Ethernet link.')
    connectors = {
        'device' : {'type' : 'ethernet-link', 'direction' : 'any',
                    'empty_ok' : True, 'hotplug' : True, 'multi' : True}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.link_name = None
        self.frame_echo = 0

    def add_objects(self):
        if self.link_name:
            self.o.link = pre_obj_noprefix(self.link_name, 'ethernet-link')
        else:
            self.o.link = pre_obj('link$', 'ethernet-link')
        self.o.link.frame_echo = self.frame_echo
        self.o.link.frequency = 1000000000000

    def add_connector_info(self):
        self.connector_info['device'] = [self.o.link]

    def connect_ethernet_link(self, connector):
        pass

    def disconnect_ethernet_link(self, connector):
        pass

    def set_link_name(self, attr, idx):
        self.link_name = attr
        return Sim_Set_Ok

    def get_link_name(self, idx):
        return self.link_name

    def set_frame_echo(self, attr, idx):
        if self.obj.configured:
            self.o.link.frame_echo = attr
        else:
            self.frame_echo = attr
        return Sim_Set_Ok

    def get_frame_echo(self, idx):
        return self.o.link.frame_echo

    def instantiation_done(self):
        component_object.instantiation_done(self)
        if self.link_name and self.o.link.name != self.link_name:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                "Could not instantiate ethernet-link with name %s."
                " %s used instead."%(self.link_name, self.o.link.name))
            SIM_command_has_problem()

register_component_class(ethernet_link_component, [
    ['link_name', Sim_Attr_Optional, 's',
     'The name to use for the <b>ethernet-link</b> object.'
     ' An error will be raised at instantiation time if the link cannot'
     ' be given this name.'],
    ['frame_echo', Sim_Attr_Optional, 'i',
     'Set this attribute to echo frames back to the sender. Default is'
     ' not to echo frames.']])


### Serial Link


class serial_link_component(component_object):
    classname = 'std-serial-link'
    basename = 'serial_link'
    description = ('The "std-serial-link" component represents a standard '
                   'Serial link.')
    connectors = {
        'serial0' : {'type' : 'serial', 'direction' : 'any',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'serial1' : {'type' : 'serial', 'direction' : 'any',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def add_objects(self):
        self.o.link = pre_obj('link$', 'serial-link')

    def add_connector_info(self):
        self.connector_info['serial0'] = [self.o.link, None]
        self.connector_info['serial1'] = [self.o.link, None]

    # not all serial devices implement the link interface
    def check_serial(self, connector, link, device, name = None):
        if link:
            return
        try:
            SIM_get_class(device.classname)
        except Exception, msg:
            raise Exception, ("Unknown class for serial-link %s."
                              % device.classname)
        if not 'link' in sim.classes[device.classname].attributes:
            raise Exception, "Serial-link not supported by serial device."

    def connect_serial(self, connector, link, device, name = None):
        pass

    def disconnect_serial(self, connector):
        pass

register_component_class(serial_link_component, [])


### MIL-STD-1553 Link


class ms1553_link_component(component_object):
    classname = 'std-ms1553-link'
    basename = 'ms1553_link'
    description = ('The "std-ms1553-link" component represents a MIL-STD-1553 '
                   'bus/link.')
    connectors = {
        'device' : {'type' : 'ms1553-link', 'direction' : 'any',
                    'empty_ok' : True, 'hotplug' : True, 'multi' : True}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.link_name = None

    def add_objects(self):
        self.o.link = pre_obj('link$', 'ms1553-link')

    def add_connector_info(self):
        self.connector_info['device'] = [self.o.link]

    def connect_ms1553_link(self, connector):
        pass

    def disconnect_ms1553_link(self, connector):
        pass

register_component_class(ms1553_link_component, [])


### Service Node


from mod_service_node_commands import add_route, add_host_cmd

class service_node_component(component_object):
    classname = 'std-service-node'
    basename = 'service_node'
    description = ('The "std-service-node" component represents a network '
                   'service node that can be connected to Ethernet links to '
                   'provide services such as DNS, DHCP/BOOTP, RARP and TFTP. '
                   'A service node component does not have any connectors by '
                   'default. Instead, connectors have to be added using the '
                   '<cmd>&lt;std-service-node>.add-connector</cmd> command.')
    connectors = {}
    simics_name_cnt = 0

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.snd = []
        self.dynamic_connectors = []
        self.next_connector_id = 0
    
    def set_next_connector_id(self, val, idx):
        self.next_connector_id = val
        return Sim_Set_Ok

    def get_next_connector_id(self, idx):
        return self.next_connector_id

    def set_dynamic_connectors(self, val, idx):
        self.dynamic_connectors = val
        for c in self.dynamic_connectors:
            self.add_link_connector(c[0])
        return Sim_Set_Ok

    def get_dynamic_connectors(self, idx):
        return self.dynamic_connectors

    def add_objects(self):
        self.o.sn = pre_obj('sn$', 'service-node')
        for c in self.dynamic_connectors:
            add_obj = True
            for d in self.o.snd:
                if d.ip_address == c[1] and d.netmask == c[2]:
                    add_obj = False
            if add_obj:
                # add object if loading component template
                self.add_connector_object(c[0], c[1], c[2])

    def add_connector_info(self):
        for c in self.connectors:
            self.connector_info[c] = []

    def connect_ethernet_link(self, connector, link):
        id = string.atoi(connector.replace('link', ''))
        self.o.snd[id].link = link

    def disconnect_ethernet_link(self, connector):
        id = string.atoi(connector.replace('link', ''))
        self.o.snd[id].link = None

    def add_snd_route(self, snd):
        add_route(self.o.sn, snd.net_ip, snd.netmask, "0.0.0.0", snd)
        # add to host list, if not already there
        if len([x for x in self.o.sn.hosts
                if x[1] == snd.ip_address]) == 0:
            # the domain name will always be 'network.sim'
            add_host_cmd(self.o.sn, snd.ip_address,
                         'simics%d' % self.simics_name_cnt,
                         None, snd.mac_address)
            self.simics_name_cnt += 1

    def instantiation_done(self):
        component_object.instantiation_done(self)
        for snd in self.o.snd:
            self.add_snd_route(snd)

    def add_link_connector(self, id):
        self.connectors['link%d' % id] = {
            'type' : 'ethernet-link', 'direction' : 'up',
            'empty_ok' : True, 'hotplug' : True, 'multi' : False}
        self.connector_info['link%d' % id] = []

    def add_connector_object(self, id, ip, netmask):
        if self.obj.instantiated:
            name = get_available_object_name('snd')
            snd = SIM_create_object('service-node-device', name,
                                    [['ip_address', ip],
                                     ['service-node', self.o.sn]])
            snd.queue = self.o.sn.queue
        else:
            snd = pre_obj('snd$', 'service-node-device')
            snd.ip_address = ip
            snd.service_node = self.o.sn
        snd.netmask = netmask
        snd.component = self.obj
        self.o.snd.append(snd)
        return (snd, 'link%d' % id)

    def add_connector(self, ip, netmask):
        id = self.next_connector_id
        self.next_connector_id += 1
        self.add_link_connector(id)
        (snd, cnt_name) = self.add_connector_object(id, ip, netmask)
        if self.obj.instantiated:
            self.add_snd_route(snd)
        self.dynamic_connectors += [[id, ip, netmask]]
        return cnt_name

def add_connector_cmd(obj, ip, netmask):
    return get_component(obj).add_connector(ip, netmask)

new_command('add-connector', add_connector_cmd,
            [arg(str_t, 'ip'),
             arg(str_t, 'netmask', '?', '255.255.255.0')],
            short = 'add a service-node connector',
            namespace = 'std-service-node',
            doc = ('Adds a connector to the service-node with specified IP '
                   'address and netmask. A connector must be created for the '
                   'service-node before an Ethernet link can be connected to '
                   'it. The <param>ip</param> argument is the IP address that '
                   'the service node will use on the link. The '
                   '<param>netmask</param> argument is optional, and defaults '
                   'to <tt>255.255.255.0</tt>.<br/>'
                   'The name of the new connector is returned.'))
            
register_component_class(service_node_component,
                         [],
                         [['next_connector_id', Sim_Attr_Optional, 'i',
                           'Next service-node device ID.'],
                          ['dynamic_connectors', Sim_Attr_Optional, '[[iss]*]',
                           'List of user added connectors', True]])


### Ethernet traffic generator component


class etg_component(component_object):
    classname = 'std-etg'
    basename = 'etg'
    description = ('The "std-etg" component represents an ethernet traffic generator.')
    connectors = {
        'ethernet' : {'type' : 'ethernet-link', 'direction' : 'down',
                      'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)

    def get_mac_address(self, idx):
        return self.mac

    def set_mac_address(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if len(mac_as_list(val)) != 6:
            return Sim_Set_Illegal_Value
        self.mac = val
        return Sim_Set_Ok

    def get_ip(self, idx):
        return self.ip

    def set_ip(self, val, idx):
        self.ip = val
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_netmask(self, idx):
        return self.netmask

    def set_netmask(self, val, idx):
        self.netmask = val
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_dst_ip(self, idx):
        return self.dst_ip

    def set_dst_ip(self, val, idx):
        self.dst_ip = val
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_gateway_ip(self, idx):
        return self.gateway_ip

    def set_gateway_ip(self, val, idx):
        self.gateway_ip = val
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_pps(self, idx):
        return self.pps

    def set_pps(self, val, idx):
        self.pps = val
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_packet_size(self, idx):
        return self.packet_size

    def set_packet_size(self, val, idx):
        self.packet_size = val
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def add_objects(self):
        self.o.etg = pre_obj('etg$', 'etg')
        self.o.etg.mac_address = self.mac
        self.o.etg.ip = self.ip
        self.o.etg.netmask = self.netmask
        self.o.etg.dst_ip = self.dst_ip
        self.o.etg.gateway = self.gateway_ip
        self.o.etg.pps = self.pps
        self.o.etg.packet_size = self.packet_size

    def add_connector_info(self):
        self.connector_info['ethernet'] = []

    def connect_ethernet_link(self, connector, link):
        self.o.etg.network = link

    def disconnect_ethernet_link(self, connector):
        self.o.etg.network = None

register_component_class(
    etg_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the traffic generator.'],
     ['ip', Sim_Attr_Required, 's',
      'IP address of the traffic generator.'],
     ['netmask', Sim_Attr_Required, 's',
      'IP netmask of the traffic generator.'],
     ['dst_ip', Sim_Attr_Required, 's',
      'Destination IP address for generated traffic.'],
     ['gateway_ip', Sim_Attr_Required, 's',
      'Gateway for non-local traffic.'],
     ['pps', Sim_Attr_Required, 'i',
      'Traffic rate in packets per second.'],
     ['packet_size', Sim_Attr_Required, 'i',
      'Packet size.']])


### Dummy Components


class dummy_component(component_object):
    classname = 'dummy-component'
    basename = 'no_component'
    description = ('Dummy component used for configurations that are not '
                   'component based.')
    connectors = {}

    def add_objects(self):
        pass

    def add_connector_info(self):
        pass

register_component_class(dummy_component, [])
