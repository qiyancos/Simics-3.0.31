# MODULE: malta-components
# CLASS: malta-system

import time
from sim_core import *
from components import *
from base_components import find_device


### Malta System


class malta_system_component(component_object):
    classname = 'malta-system'
    basename = 'system'
    description = ('The "malta-system" component represents a MIPS Malta '
                   'development board with a MIPS 4Kc or 5Kc processor and a '
                   'Galileo GT64120 system controller.')
    connectors = {
        'pci-slot-sb' : {'type' : 'pci-bus', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : False,
                         'multi' : False},
        'interrupt'    : {'type' : 'sb-interrupt', 'direction' : 'down',
                          'empty_ok' : False, 'hotplug' : False,
                          'multi' : False}}
    for i in range(1, 5):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def get_cpu_class(self, idx):
        return self.cpu_class

    def set_cpu_class(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if val not in ('mips-4kc', 'mips-5kc'):
            SIM_attribute_error("Unsupported CPU class")
            return Sim_Set_Illegal_Value
        self.cpu_class = val
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
        self.tod = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.hfs = pre_obj('hfs', 'hostfs')
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.cpu = pre_obj('cpu0', self.cpu_class)
        self.o.cpu.physical_memory = self.o.phys_mem
        self.o.cpu.freq_mhz = self.freq_mhz
        self.o.cbus_space = pre_obj('cbus_space', 'memory-space')
        self.o.ram_image = pre_obj('ram_image', 'image')
        # TODO: configurable size?
        self.o.ram_image.size = 0x08000000
        self.o.ram = pre_obj('ram', 'ram')
        self.o.ram.image = self.o.ram_image
        self.o.rom_image = pre_obj('rom_image', 'image')
        self.o.rom_image.size = 0x400000
        self.o.rom = pre_obj('rom', 'rom')
        self.o.rom.image = self.o.rom_image
        #
        self.o.gt_pci_0_0 = pre_obj('gt_pci_0_0', 'GT64120-pci')
        self.o.gt_pci_0_0.bridge_num = 0
        self.o.gt_pci_0_0.function_num = 0
        self.o.gt_pci_0_1 = pre_obj('gt_pci_0_1', 'GT64120-pci')
        self.o.gt_pci_0_1.bridge_num = 0
        self.o.gt_pci_0_1.function_num = 1
        # Dummies for non-existent pci-bus 1
        self.o.gt_pci_1_0 = pre_obj('gt_pci_1_0', 'GT64120-pci')
        self.o.gt_pci_1_0.bridge_num = 1
        self.o.gt_pci_1_0.function_num = 0
        self.o.gt_pci_1_1 = pre_obj('gt_pci_1_1', 'GT64120-pci')
        self.o.gt_pci_1_1.bridge_num = 1
        self.o.gt_pci_1_1.function_num = 1
        #
        self.o.pci_bus0_conf = pre_obj('pci_bus0_conf', 'memory-space')
        self.o.pci_bus0_io = pre_obj('pci_bus0_io', 'memory-space')
        self.o.pci_bus0_mem = pre_obj('pci_bus0_mem', 'memory-space')
        #
        self.o.pci_bus1_conf = pre_obj('pci_bus1_conf', 'memory-space')
        self.o.pci_bus1_io = pre_obj('pci_bus1_io', 'memory-space')
        self.o.pci_bus1_mem = pre_obj('pci_bus1_mem', 'memory-space')
        #
        self.o.pci_bus0 = pre_obj('pci_bus0', 'pci-bus')
        self.o.pci_bus0.bridge = self.o.gt_pci_0_0
        self.o.pci_bus0.interrupt = self.o.gt_pci_0_0
        self.o.pci_bus0.conf_space = self.o.pci_bus0_conf
        self.o.pci_bus0.io_space = self.o.pci_bus0_io
        self.o.pci_bus0.io_space.map = []
        self.o.pci_bus0.memory_space = self.o.pci_bus0_mem
        self.o.pci_bus0.pci_devices = [[0, 0, self.o.gt_pci_0_0],
                                       [0, 1, self.o.gt_pci_0_1]]
        #
        self.o.pci_bus1 = pre_obj('pci_bus1', 'pci-bus')
        self.o.pci_bus1.bridge = self.o.gt_pci_1_0
        self.o.pci_bus1.interrupt = self.o.gt_pci_1_0
        self.o.pci_bus1.conf_space = self.o.pci_bus1_conf
        self.o.pci_bus1.io_space = self.o.pci_bus1_io
        self.o.pci_bus1.io_space.map = []
        self.o.pci_bus1.memory_space = self.o.pci_bus1_mem
        self.o.pci_bus1.pci_devices = [[0, 0, self.o.gt_pci_1_0],
                                       [0, 1, self.o.gt_pci_1_1]]
        #
        self.o.gt_pci_0_0.pci_bus = self.o.pci_bus0
        self.o.gt_pci_0_1.pci_bus = self.o.pci_bus0
        #
        self.o.gt_pci_1_0.pci_bus = self.o.pci_bus1
        self.o.gt_pci_1_1.pci_bus = self.o.pci_bus1
        #
        self.o.gt = pre_obj('gt', 'GT64120')
        self.o.gt.cpu_mem = self.o.phys_mem
        self.o.gt.pci_0_0 = self.o.gt_pci_0_0
        self.o.gt.pci_0_1 = self.o.gt_pci_0_1
        self.o.gt.pci_1_0 = self.o.gt_pci_1_0
        self.o.gt.pci_1_1 = self.o.gt_pci_1_1
        self.o.gt.scs0 = self.o.ram
        self.o.gt.cs3 = self.o.cbus_space
        self.o.gt.bootcs = self.o.cbus_space
        self.o.gt.pci_0_conf = self.o.pci_bus0_conf
        self.o.gt.pci_0_io = self.o.pci_bus0_io
        self.o.gt.pci_0_memory = self.o.pci_bus0_mem
        self.o.gt.pci_1_conf = self.o.pci_bus1_conf
        self.o.gt.pci_1_io = self.o.pci_bus1_io
        self.o.gt.pci_1_memory = self.o.pci_bus1_mem
        self.o.gt.irq_dev = self.o.cpu
        self.o.gt.irq_level = 2
        # Little endian
        self.o.gt.cpu_interface_configuration = 0x00041000
        # Map 128MB RAM.
        self.o.gt.scs10_high_decode_address = 0x40
        self.o.gt.scs0_low_decode_address = 0x0
        self.o.gt.scs0_high_decode_address = 0x7f
        # Map the internal registers at 0x1be00000.
        self.o.gt.internal_space_decode = 0xdf
        # Disable host-PCI mappings
        self.o.gt.pci_0_io_high_decode_address =       0
        self.o.gt.pci_0_io_low_decode_address =        1
        self.o.gt.pci_0_io_remap =                     1
        self.o.gt.pci_0_memory_0_high_decode_address = 0
        self.o.gt.pci_0_memory_0_low_decode_address =  1
        self.o.gt.pci_0_memory_0_remap =               1
        self.o.gt.pci_0_memory_1_high_decode_address = 0
        self.o.gt.pci_0_memory_1_low_decode_address =  1
        self.o.gt.pci_0_memory_1_remap =               1
        self.o.gt.pci_1_io_high_decode_address =       0
        self.o.gt.pci_1_io_low_decode_address =        1
        self.o.gt.pci_1_io_remap =                     1
        self.o.gt.pci_1_memory_0_high_decode_address = 0
        self.o.gt.pci_1_memory_0_low_decode_address =  1
        self.o.gt.pci_1_memory_0_remap =               1
        self.o.gt.pci_1_memory_1_high_decode_address = 0
        self.o.gt.pci_1_memory_1_low_decode_address =  1
        self.o.gt.pci_1_memory_1_remap =               1
        # Disable PCI_host mappings
        self.o.gt.pci_0_base_address_registers_enable = 0x1ff
        self.o.gt.pci_1_base_address_registers_enable = 0x1ff
        #
        self.o.gt_pci_0_0.gt64120 = self.o.gt
        self.o.gt_pci_0_1.gt64120 = self.o.gt
        self.o.gt_pci_1_0.gt64120 = self.o.gt
        self.o.gt_pci_1_1.gt64120 = self.o.gt
        #
        self.o.malta = pre_obj('malta', 'malta')
        self.o.display = pre_obj('display', 'text-console')
        self.o.display.title = "MALTA Display"
	self.o.display.bg_color = "black"
	self.o.display.fg_color = "red"
	self.o.display.width = 8
	self.o.display.height = 1
	self.o.display.scrollbar = 0
	self.o.display.x11_font = "-*-*-*-r-*-*-*-240-*-*-m-*-*-*"
	self.o.display.win32_font = "Lucida Console:Bold:48"
	self.o.display.output_timeout = 120
        self.o.display.read_only = 1
        self.o.malta.console = self.o.display
        #
        self.o.phys_mem.map = [
            # the pci-io mapping should be created by the bios
            [0x18000000, self.o.pci_bus0_io, 0, 0, 0x10000],
            [0x1c000000, self.o.hfs,   0,     0, 16]]
        self.o.cbus_space.map = [
            [0x1f000000, self.o.malta, 0,   0, 0xc00000],
            [0x1fc00000, self.o.rom,   0,   0, 0x400000]]

    def add_connector_info(self):
        # PCI device numbers:
        # 10    South-bridge
        # 11    Ethernet controller
        # 12    Audio
        # 17    Core Coard
        # 18-21 PCI slot 1-4
        self.connector_info['interrupt'] = [self.o.gt, None]
        self.connector_info['pci-slot-sb'] = [10, self.o.pci_bus0]
        for i in range(1, 5):
            self.connector_info['pci-slot%d' % i] = [17 + i, self.o.pci_bus0]

    def instantiation_done(self):
        component_object.instantiation_done(self)
        conf.sim.handle_outside_memory = 1
        rtc = find_device(self.o.pci_bus0_io, 0x70)
        if not rtc:
            print "RTC device not found - can not write information."
            return
        m = re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', self.tod)
        eval_cli_line(('%s.set-date-time '
                       + 'year=%s month=%s mday=%s hour=%s minute=%s second=%s'
                       ) % ((rtc.name,) + m.groups()))

    def connect_sb_interrupt(self, connector, pic):
        # It seems like Linux expects the master 8259 to have VBA 0.
        # Maybe that would be set up by YAMON?
        pic.pic.vba = [0, 1]

    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        pci_devices = self.o.pci_bus0.pci_devices
        for d in device_list:
            pci_devices += [[slot, d[0], d[1]]]
        self.o.pci_bus0.pci_devices = pci_devices

    def get_clock(self):
        return self.o.cpu

    def get_processors(self):
        return [self.o.cpu]

register_component_class(
    malta_system_component,
    [['cpu_frequency', Sim_Attr_Required, 'i',
      'Processor frequency in MHz.'],
     ['cpu_class', Sim_Attr_Required, 's',
      'Processor type, one of "mips-4kc" and "mips-5kc"'],
     ['rtc_time', Sim_Attr_Required, 's',
      'The data and time of the Real-Time clock.']],
    top_level = True)
