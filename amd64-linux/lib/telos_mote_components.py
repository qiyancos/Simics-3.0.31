# MODULE: telos-mote-components
# CLASS: telos-mote

from sim_core import *
from components import *

# Telos Mote 
class telos_mote_component(component_object):
    classname = 'telos-mote'
    basename = 'system'
    description = "A Telos Mote, based on the msp430 processor"
    # connectors:
    connectors = {
        # serial 0
        'usart0' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        # serial 1
        'usart1' : {'type' : 'serial', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        # zigbee radio
        'zigbee' : {'type' : 'zigbee-link', 'direction' : 'down',
                   'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    # settings attributes in the components: get & set functions
    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    # x,y,z location as three attributes, as the CLI cannot
    # represent lists. This is the most compatible way.
    def get_location_x(self, idx):
        return self.location_x

    def set_location_x(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.location_x = val
        return Sim_Set_Ok

    def get_location_y(self, idx):
        return self.location_y

    def set_location_y(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.location_y = val
        return Sim_Set_Ok
    
    def get_location_z(self, idx):
        return self.location_z

    def set_location_z(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.location_z = val
        return Sim_Set_Ok    

    # adding all the objects found in a mote
    def add_objects(self):
        # forward declare all objects in the mote
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.cpu = pre_obj('cpu', 'msp430')
        self.o.ram = pre_obj('memory', 'ram')
        self.o.ram_image = pre_obj('memory_image', 'image')
        self.o.io_ports = pre_obj('io_ports','telos-io-ports')
        self.o.sfr = pre_obj('sfr','telos-sfr')
        self.o.usart0 = pre_obj('usart0','telos-usart')
        self.o.usart1 = pre_obj('usart1','telos-usart')
        self.o.timer_a = pre_obj('timer_a','telos-timer')
        self.o.timer_b = pre_obj('timer_b','telos-timer')
        self.o.basic_clock = pre_obj('basic_clock','telos-basic-clock')
        self.o.reset_button = pre_obj('reset_button','telos-button')
        self.o.environment = pre_obj('environment','telos-environment')
        # interrupt mapping space (not a pre object, just attribute for CPU)
        # list devices here to have them automatically acknowledged by CPU
        self.interrupt_source_list = [None for i in range(16)]
        self.interrupt_source_list[13] = self.o.timer_b
        self.interrupt_source_list[9] = self.o.usart0
        self.interrupt_source_list[8] = self.o.usart0
        self.interrupt_source_list[6] = self.o.timer_a
        self.interrupt_source_list[3] = self.o.usart1
        self.interrupt_source_list[2] = self.o.usart1
        # CPU object
        self.o.cpu.physical_memory = self.o.phys_mem
        self.o.cpu.freq_mhz = self.freq_mhz  # parameter to setup
        self.o.cpu.interrupt_sources = self.interrupt_source_list
        self.o.cpu.environment = self.o.environment
        # RAM memory image
        self.o.ram_image.size = 0x10000
        self.o.ram_image.queue = self.o.cpu
        # RAM object
        self.o.ram.image = self.o.ram_image
        # sfr
        self.o.sfr.queue = self.o.cpu
        self.o.sfr.usart0_dev = self.o.usart0
        self.o.sfr.usart1_dev = self.o.usart1
        # io ports
        self.o.io_ports.queue = self.o.cpu
        # usart 0
        self.o.usart0.queue = self.o.cpu
        self.o.usart0.irq_dev = self.o.cpu
        self.o.usart0.tx_vector = 9
        self.o.usart0.rx_vector = 8
        self.o.usart0.sfr_dev = self.o.sfr
        # usart 1
        self.o.usart1.queue = self.o.cpu
        self.o.usart1.irq_dev = self.o.cpu
        self.o.usart1.tx_vector = 3
        self.o.usart1.rx_vector = 2
        self.o.usart1.sfr_dev = self.o.sfr
        # timer A
        self.o.timer_a.is_timer_a = True
        self.o.timer_a.aclk_freq = 1.0 * (1 << 15)    # 32 kHz
        self.o.timer_a.smclk_freq = 1.0 * (1 << 20)   # 1 MHz
        self.o.timer_a.queue = self.o.cpu
        self.o.timer_a.irq_dev = self.o.cpu
        self.o.timer_a.irq_vector_ccr0 = 6
        self.o.timer_a.irq_vector_tmiv = 5
        # timer B
        self.o.timer_b.is_timer_a = False
        self.o.timer_b.aclk_freq = 1.0 * (1 << 15)    # 32 kHz
        self.o.timer_b.smclk_freq = 1.0 * (1 << 20)   # 1 MHz
        self.o.timer_b.queue = self.o.cpu
        self.o.timer_b.irq_dev = self.o.cpu
        self.o.timer_b.irq_vector_ccr0 = 13
        self.o.timer_b.irq_vector_tmiv = 12
        # basic clock
        self.o.basic_clock.queue = self.o.cpu
        #  buttons
        self.o.reset_button.irq_dev = self.o.cpu
        self.o.reset_button.irq_level = 15
        # Memory map
        self.o.phys_mem.map = [
            # Memory is all considered as RAM, including what is
            # really FLASH. This works for the currently tested code.
            [0x00000200, self.o.ram, 0, 0x200, 0x10000 - 0x200],
            # sfr registers
            [0x00000000, self.o.sfr, 0, 0, 6],
            # HOLE -- all holes are used to enable tracing accesses
            #         to devices which are not implemented 
            [0x00000006, self.o.ram, 0, 6, 0x18 - 0x6],      ## HOLE
            # Digital IO ports
            [0x00000018, self.o.io_ports, 3, 0, 4],
            [0x0000001c, self.o.io_ports, 4, 0, 4],
            [0x00000020, self.o.io_ports, 1, 0, 7],
            [0x00000028, self.o.io_ports, 2, 0, 7],
            [0x00000030, self.o.io_ports, 5, 0, 4],
            [0x00000034, self.o.io_ports, 6, 0, 4],
            # HOLE
            [0x00000038, self.o.ram, 0, 0x38, 0x56 - 0x38], ## HOLE
            # basic clock
            [0x00000056, self.o.basic_clock, 0, 0, 3],
            # HOLE
            [0x00000059, self.o.ram, 0, 0x59, 0x70 - 0x59], ## HOLE
            # serial ports
            [0x00000070, self.o.usart0, 0, 0, 8],
            [0x00000078, self.o.usart1, 0, 0, 8],
            # HOLE
            [0x00000080, self.o.ram, 0, 0x80, 0x11e - 0x80], ## HOLE
            # timer B
            [0x0000011e, self.o.timer_b, 1, 0, 2],
            # HOLE
            [0x00000120, self.o.ram, 0, 0x120, 0x12e - 0x120], ## HOLE
            # timer A
            [0x0000012e, self.o.timer_a, 1, 0, 2],
            # HOLE
            [0x00000130, self.o.ram, 0, 0x130, 0x160 - 0x130], ## HOLE
            # timer A, part 2
            [0x00000160, self.o.timer_a, 0, 0, 0x20],
            # timer B, part 2
            [0x00000180, self.o.timer_b, 0, 0, 0x20],
            # HOLE
            [0x000001a0, self.o.ram, 0, 0x1a0, 0x200 - 0x1a0] ## HOLE
            ]
        # environment parameters
        self.o.environment.location_x = self.location_x
        self.o.environment.location_y = self.location_y
        self.o.environment.location_z = self.location_z
        self.o.environment.temperature = 293  # nice default value

        
    # connector information
    def add_connector_info(self):
        self.connector_info['usart0'] = [None, self.o.usart0, self.o.usart0.name]
        self.connector_info['usart1'] = [None, self.o.usart1, self.o.usart1.name]
        self.connector_info['zigbee'] = []

    # serial port connectors
    def connect_serial(self, connector, link, console):
        if connector == 'usart0':
            if link:
                self.o.usart0.link = link
            else:
                print "Mote cannot connect to console"
        if connector == 'usart1':
            if link: 
                self.o.usart1.link = link
            else:
                print "Mote cannot connect to console"

    def disconnect_serial(self, connector):
        if connector == 'usart0':
            self.o.usart0.link = None
            self.o.usart0.console = None
        if connector == 'usart1':
            self.o.usart0.link = None
            self.o.usart0.console = None

    # zigbee connector, dummy implementation
    def connect_zigbee_link(self, connector, link):
        print "Zigbee currently at dummy level"

    def disconnect_zigbee_link(self, connector):
        print "Zigbee currently at dummy level"

    # supporting functions
    def get_clock(self):
        return self.o.cpu

    def get_processors(self):
        return [self.o.cpu]

    # reset this processor after the configuration is complete
    # note that this does  not help much, as the software has
    # not been loaded yet, so any software load has to be
    # followed by a reset command
    def instantiation_done(self):
        component_object.instantiation_done(self)
        import cli
        cli.eval_cli_line("%s.reset"%(self.o.cpu.name))


register_component_class(
    telos_mote_component,
    [['cpu_frequency', Sim_Attr_Required, 'f',
      'Processor frequency in MHz.'],
     ['location_x',Sim_Attr_Required, 'i',
      'initial X location of mote'],
     ['location_y',Sim_Attr_Required, 'i',
      'initial Y location of mote'],
     ['location_z',Sim_Attr_Required, 'i',
      'initial Z location of mote']],
    top_level = True)


