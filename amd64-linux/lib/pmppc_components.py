# MODULE: pmppc-components
# CLASS: pmppc-board

import time
from sim_core import *
from components import *
from configuration import DATA # TODO: replace

SIM_source_python_in_module('%s/home/scripts/flash_memory.py'
                            % conf.sim.simics_base, __name__)

# TODO: separate processor component, or board-attribute?


### PM-PPM Board Component


class pmppc_board_component(component_object):
    classname = 'pmppc-board'
    basename = 'system'
    description = 'TODO:'
    connectors = {
        'uart0' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'uart1' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'eth0'  : {'type' : 'ethernet-link', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    # TODO: add other PCI slots
    for i in (2, 6):
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
        try:
            SIM_get_class(val)
        except:
            return Sim_Set_Illegal_Value

        self.cpu_class = val
        return Sim_Set_Ok

    def get_timebase_frequency(self, idx):
        return self.tb_freq_mhz

    def set_timebase_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.tb_freq_mhz = val
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

    def add_objects(self):
        self.memory_bytes = 256 * 0x100000
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.cpu = pre_obj('cpu$', self.cpu_class)
        self.o.cpu.processor_number = get_next_cpu_number()
        self.o.cpu.freq_mhz = self.freq_mhz
        self.o.cpu.timebase_freq_mhz = self.tb_freq_mhz
        self.o.cpu.physical_memory = self.o.phys_mem
        self.o.ram_image = pre_obj('memory_image', 'image')
        self.o.ram_image.size = self.memory_bytes
        self.o.ram = pre_obj('memory', 'ram')
        self.o.ram.image = self.o.ram_image
        self.o.bootrom0_image = pre_obj('bootrom0_image', 'image')
        self.o.bootrom0_image.size = 0x200000
        self.o.bootrom0 = pre_obj('bootrom0', 'rom')
        self.o.bootrom0.image = self.o.bootrom0_image
        self.o.bootrom1_image = pre_obj('bootrom1_image', 'image')
        self.o.bootrom1_image.size = 0x80000
        self.o.bootrom1 = pre_obj('bootrom1', 'rom')
        self.o.bootrom1.image = self.o.bootrom1_image
        self.o.i2cbus0 = pre_obj('i2c_bus0', 'i2c-bus')
        self.o.i2cbus1 = pre_obj('i2c_bus1', 'i2c-bus')
        self.o.mc = pre_obj('mc', 'cpc700-mc')
        self.o.pi = pre_obj('pi', 'cpc700-pi')
        self.o.uic = pre_obj('uic', 'cpc700-uic')
        self.o.uic.irq_dev = self.o.cpu
        self.o.uart0 = pre_obj('uart0', 'NS16550')
        self.o.uart0.irq_dev = self.o.uic
        self.o.uart0.irq_level = 28
        self.o.uart1 = pre_obj('uart1', 'NS16550')
        self.o.uart1.irq_dev = self.o.uic
        self.o.uart1.irq_level = 27
        self.o.gpt = pre_obj('gpt', 'cpc700-gpt')
        self.o.gpt.irq_dev = self.o.uic
        self.o.gpt.irq_base_level = 24
        self.o.iic0 = pre_obj('iic0', 'cpc700-iic')
        self.o.iic0.i2c_bus = self.o.i2cbus0
        self.o.iic1 = pre_obj('iic1', 'cpc700-iic')
        self.o.iic1.i2c_bus = self.o.i2cbus1
        self.o.pmppc = pre_obj('pmppc', 'artesyn-pm-ppc')
        self.o.pmppc.board_config_reg0= 0xa1
        self.o.pmppc.board_config_reg1= 0x66
        self.o.pmppc.led_board_id_reg = 0x10
        self.o.pmppc.irq_dev = self.o.uic
        self.o.pmppc.irq_base_level = 11
        self.o.rtc = pre_obj('rtc', 'DS17485')
        self.o.rtc.irq_dev = self.o.uic
        self.o.rtc.irq_level = 6
        self.o.eeprom = pre_obj('eeprom', 'AT24C164')
        self.o.eeprom.i2c_bus = self.o.i2cbus0
        self.o.eeprom.a210 = 3
        self.o.eeprom.memory = DATA(0x800, 'eeprom.raw', 0x200)
        self.o.eth0 = pre_obj('eth0', 'CS8900A')
        self.o.eth0.mac_address = self.mac
        self.o.eth0.irq_dev = self.o.uic
        self.o.eth0.irq_level = 7
        self.o.bridge = pre_obj('pci_bridge', 'cpc700-pci')
        self.o.bridge.memory = self.o.phys_mem
        # This are needed since normally the PROM initilize the pci-bridge
        self.o.bridge.config_registers = (
            [0xf91014, 0x2000006, 0x6000001, 0x700, 0, 0,
             0x8000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.o.bridge.pmm0la = 0x80000000
        self.o.bridge.pmm0ma = 0xc0000001
        self.o.bridge.pmm0pcila = 0x80000000
        self.o.bridge.pmm0pciha = 0
        self.o.bridge.pmm1la = 0
        self.o.bridge.pmm1ma = 0xfffff000
        self.o.bridge.pmm1pcila = 0
        self.o.bridge.pmm1pciha = 0
        self.o.bridge.pmm2la = 0
        self.o.bridge.pmm2ma = 0xfffff000
        self.o.bridge.pmm2pcila = 0
        self.o.bridge.pmm2pciha = 0
        self.o.bridge.ptm1ms = 0xf8000001
        self.o.bridge.ptm1la = 0
        self.o.bridge.ptm2ms = 0xfffff001
        self.o.bridge.ptm2la = 0x7ff40000
        self.o.bridge.pcicfgadr = 0x80000048
        self.o.pci_cfg = pre_obj('pci_cfg', 'memory-space')
        self.o.pci_io = pre_obj('pci_io', 'memory-space')
        self.o.pci_mem = pre_obj('pci_mem', 'memory-space')
        self.o.pci_bus = pre_obj('pci_bus', 'pci-bus')
        self.o.pci_bus.bridge = self.o.bridge
        self.o.pci_bus.conf_space = self.o.pci_cfg
        self.o.pci_bus.io_space = self.o.pci_io
        self.o.pci_bus.memory_space = self.o.pci_mem
        self.o.pci_bus.interrupt = self.o.pmppc
        self.o.pci_bus.pci_devices = [[0, 0, self.o.bridge]]
        self.o.bridge.pci_bus = self.o.pci_bus
        flash, map_size = flash_create_memory('flash', '28F128J3A', 1, 16,
                                              big_endian = 1)
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.flash = flash_pre['flash']
        self.o.flash_image = flash_pre['flash_image']
        self.o.flash_ram = flash_pre['flash_ram']
        self.o.hfs = pre_obj('hfs', 'hostfs')
        self.o.phys_mem.map = [
            [0x00000000, self.o.ram,        0,          0, self.memory_bytes],
            [0x70000000, self.o.flash,      0,          0,   map_size,
             self.o.flash_ram, 0, 2],
            [0x7fe00000, self.o.eth0,       0,          0,   0x100000],
            [0x7ff00000, self.o.rtc,        0,          0,     0x2000],
            [0x7ff40000, self.o.pmppc,      0, 0x7ff40000,    0x40000],
            [0x7ff80000, self.o.bootrom1,   0,          0,    0x80000],
            [0x80000000, self.o.pci_mem,    0, 0x80000000, 0x78000000],
            [0xf8000000, self.o.bridge,    11,          0,    0x10000],
            [0xf8800000, self.o.bridge,    11,   0x800000,  0x3800000],
            [0xfec00000, self.o.bridge,    10, 0xfec00000,          8],
            [0xff400000, self.o.bridge,    10, 0xff400000,   0x100000],
            [0xff500000, self.o.pi,         0, 0xff500000,          8],
            [0xff500008, self.o.mc,         0, 0xff500008,          8],
            [0xff500880, self.o.uic,        0,          0,       0x24],
            [0xff600300, self.o.uart0,      0,        0x0,        0x8, None, 0, 1],
            [0xff600400, self.o.uart1,      0,        0x0,        0x8, None, 0, 1],
            [0xff620000, self.o.iic0,       0,        0x0,        0x2],
            [0xff620002, self.o.iic0,       0,        0x2,        0x2],
            [0xff620004, self.o.iic0,       0,        0x4,        0x1],
            [0xff620005, self.o.iic0,       0,        0x5,        0x1],
            [0xff620006, self.o.iic0,       0,        0x6,        0x1],
            [0xff620007, self.o.iic0,       0,        0x7,        0x1],
            [0xff620008, self.o.iic0,       0,        0x8,        0x1],
            [0xff620009, self.o.iic0,       0,        0x9,        0x1],
            [0xff62000a, self.o.iic0,       0,        0xa,        0x1],
            [0xff62000b, self.o.iic0,       0,        0xb,        0x1],
            [0xff62000c, self.o.iic0,       0,        0xc,        0x1],
            [0xff62000d, self.o.iic0,       0,        0xd,        0x1],
            [0xff62000e, self.o.iic0,       0,        0xe,        0x1],
            [0xff62000f, self.o.iic0,       0,        0xf,        0x1],
            [0xff620010, self.o.iic0,       0,       0x10,        0x1],
            [0xff630000, self.o.iic1,       0,        0x0,        0x2],
            [0xff630002, self.o.iic1,       0,        0x2,        0x2],
            [0xff630004, self.o.iic1,       0,        0x4,        0x1],
            [0xff630005, self.o.iic1,       0,        0x5,        0x1],
            [0xff630006, self.o.iic1,       0,        0x6,        0x1],
            [0xff630007, self.o.iic1,       0,        0x7,        0x1],
            [0xff630008, self.o.iic1,       0,        0x8,        0x1],
            [0xff630009, self.o.iic1,       0,        0x9,        0x1],
            [0xff63000a, self.o.iic1,       0,        0xa,        0x1],
            [0xff63000b, self.o.iic1,       0,        0xb,        0x1],
            [0xff63000c, self.o.iic1,       0,        0xc,        0x1],
            [0xff63000d, self.o.iic1,       0,        0xd,        0x1],
            [0xff63000e, self.o.iic1,       0,        0xe,        0x1],
            [0xff63000f, self.o.iic1,       0,        0xf,        0x1],
            [0xff630010, self.o.iic1,       0,       0x10,        0x1],
            [0xff650000, self.o.gpt,        0,          0,      0x100],
            [0xff660000, self.o.hfs,        0,          0,       0x10],
            [0xffe00000, self.o.bootrom0,   0,          0,   0x200000]]

    def add_connector_info(self):
        self.connector_info['uart0'] = [None, self.o.uart0, self.o.uart0.name]
        self.connector_info['uart1'] = [None, self.o.uart1, self.o.uart1.name]
        self.connector_info['eth0'] = []
        self.connector_info['pci-slot2'] = [2, self.o.pci_bus]
        self.connector_info['pci-slot6'] = [6, self.o.pci_bus]

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

    def connect_pci_bus(self, connector, device_list):
        device = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        pci_devices = bus.pci_devices
        for d in device_list:
            pci_devices += [[device, d[0], d[1]]]
        bus.pci_devices = pci_devices

    def connect_ethernet_link(self, connector, link):
        self.o.eth0.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.eth0.link = None

    def instantiation_done(self):
        component_object.instantiation_done(self)
        conf.sim.handle_outside_memory = 1
        m = re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', self.tod)
        eval_cli_line(('%s.set-date-time '
                       + 'year=%s month=%s mday=%s hour=%s minute=%s second=%s'
                       ) % ((self.o.rtc.name,) + m.groups()))

    def get_clock(self):
        return self.o.cpu

    def get_processors(self):
        return [self.o.cpu]

register_component_class(
    pmppc_board_component,
    [['cpu_class', Sim_Attr_Required, 's',
      'Processor type, PowerPC processor to use.'],
     ['cpu_frequency', Sim_Attr_Required, 'f',
      'Processor frequency in MHz.'],
     ['timebase_frequency', Sim_Attr_Required, 'f',
      'Time-base frequency in MHz.'],
     ['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.'],
     ['rtc_time', Sim_Attr_Required, 's',
      'The data and time of the Real-Time clock.']],
    top_level = True)
