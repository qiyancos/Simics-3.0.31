# MODULE: sunfire-components
# CLASS: sunfire-3500-backplane
# CLASS: sunfire-4500-backplane
# CLASS: sunfire-6500-backplane
# CLASS: sunfire-cpu-board
# CLASS: sunfire-sbus-board
# CLASS: sunfire-pci-board
# CLASS: sun-sbus-fas-hme

import time
from sim_core import *
from components import *
from configuration import convert_to_pre_objects
from sunfire_obp import register_obp_commands, write_idprom_to_nvram

SIM_source_python_in_module('%s/home/scripts/flash_memory.py'
                            % conf.sim.simics_base, __name__)

BOARD_BASE = 0x1c000000000
UPA_SPACE_SIZE = 0x200000000

def write_memory(space, addr, value, size):
    data = [0] * size
    for i in range(size):
        data[i] = (value >> ((size - 1) * 8) - (i * 8)) & 0xff
    space.memory[[addr, addr + size - 1]] = data

def read_memory(space, addr):
    return space.memory[[addr, addr]][0]

freq_list = {168 : [ 336, 0, 2], # sys-freq  84 ok
             200 : [ 400, 0, 2], # sys-freq 100 ok
             248 : [ 248, 3, 3], # sys-freq  82 ok
             296 : [ 296, 3, 3], # sys-freq  98 ok
             336 : [ 336, 3, 2], # sys-freq 168 ok
             360 : [ 360, 3, 2], # sys-freq 180 ok
             400 : [ 200, 3, 4], # sys-freq  80 ok
             464 : [ 232, 3, 4], # sys-freq  92 ok
             496 : [ 248, 3, 4], # sys-freq  99 ok
             592 : [ 296, 3, 1], # sys-freq  98 ok
             720 : [ 360, 3, 0], # sys-freq 180 ok
             800 : [ 400, 3, 0], # sys-freq 200 ok
             992 : [ 496, 3, 4]} # sys-freq 198 ok


### SunFire 3500/4500/6500 Backplane


class sunfire_backplane_component(component_object):
    connectors = {
        'central-cpu' : { 'type' : 'sunfire-central-cpu', 'direction' : 'down',
                          'empty_ok' : False, 'hotplug' : False,
                          'multi' : False},
        'remote_console' : {'type' : 'serial', 'direction' : 'down',
                            'empty_ok' : True, 'hotplug' : True,
                            'multi' : False},
        'ttya'        : {'type' : 'serial', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'ttyb'        : {'type' : 'serial', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'keyboard'    : {'type' : 'serial', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'mouse'       : {'type' : 'serial', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.obp_bugfix_done = False

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if not freq_list.has_key(val):
            SIM_attribute_error('Unsupported processor frequency')
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

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

    def get_obp_bugfix_done(self, idx):
        return self.obp_bugfix_done

    def set_obp_bugfix_done(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.obp_bugfix_done = val
        return Sim_Set_Ok

    def get_master_cpu(self, idx):
        return self.master_cpu

    def set_master_cpu(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.master_cpu = val
        return Sim_Set_Ok

    def change_memory(self, board_no, mb):
        self.board_mem[board_no] = mb
        mem = self.o.phys_mem.map
        [mem_map] = [x for x in mem if x[1] == self.o.mem]
        mem.remove(mem_map)
        mem_map[4] = 0x100000 * sum(self.board_mem)
        self.o.phys_mem.map = mem + [mem_map]
        self.o.mem_image.size = mem_map[4]
        
    def change_frequency(self, freq_mhz):
        freq = freq_list[freq_mhz][0] ^ 0xfa
        range = freq_list[freq_mhz][1]
        divide = freq_list[freq_mhz][2]
        self.o.clks.clk_reg1 = freq & 0xff
        self.o.clks.clk_reg2 = ((1 << 7)
                              | (((divide >> 1) & 1) << 4)
                              | ((range & 3) << 2)
                              | ((divide & 1) << 1)
                              | ((freq >> 8) & 1))
        self.o.clks.clk_reg3 = (divide >> 2) & 1

    def lock_entry_callback(self, arg, obj, access, bp_id, reg_ptr, size):
        SIM_log_message(self.obj, 2, 0, Sim_Log_Info,
                        "Locking entry 1 in D-TLB (temporarily).")
        mmu_trans = self.master_cpu.mmu.dtlb_daccess
        mmu_trans[1] = 0xc000020003c00076
        self.master_cpu.mmu.dtlb_daccess = mmu_trans
        self.obp_bugfix_done = True
        VT_revexec_barrier()
        
    def lock_entry(self):
        # set a breakpoint where we only run once per boot
        bp_id = SIM_breakpoint(self.master_cpu.physical_memory,
                               Sim_Break_Physical, Sim_Access_Execute,
                               0x03c465c8, 4,
                               Sim_Breakpoint_Simulation
                               | Sim_Breakpoint_Temporary)
        SIM_hap_add_callback_index("Core_Breakpoint", self.lock_entry_callback,
                                   None, bp_id)

    def add_objects(self):
        self.fhc_list = []
        self.cpu_list = [None] * 32
        self.post_info = [2] * 17 # max 16 boards + clock board, 2 = empty
        self.board_mem = [0 for i in range(len(self.board_nums))]
        self.o.simicsfs = pre_obj('simicsfs', 'hostfs')
        self.o.mem_image = pre_obj('memory_image', 'image')
        self.o.mem_image.size = 0
        self.o.mem = pre_obj('memory', 'ram')
        self.o.mem.image = self.o.mem_image
        self.o.irqbus = pre_obj('irqbus', 'sparc-irq-bus')
        self.o.central_space = pre_obj('central_space', 'memory-space')
        self.o.clock_space = pre_obj('clock_space', 'memory-space')
        self.o.clock_space.map = []
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.phys_mem.map = [[0x00000000000, self.o.mem, 0, 0, 0x00000000]]
        # clock board devices
        self.o.clks = pre_obj('clks', 'sun4u-clockregs')
        self.o.empty = pre_obj('empty$', 'empty-device')
        self.o.sysreg = pre_obj('sysregs', 'sun4u-systemregs')
        self.o.sysreg.slots = len(self.board_nums)
        self.o.rcons_a_port = pre_obj('rcons_a_port', 'Z8530-port')
        self.o.rcons_b_port = pre_obj('rcons_b_port', 'Z8530-port') # unused
        self.o.remote_cons = pre_obj('remote_cons', 'Z8530')
        self.o.remote_cons.a_port = self.o.rcons_a_port
        self.o.remote_cons.b_port = self.o.rcons_b_port
        self.o.remote_cons.irq_level = 0 # not used
        self.o.rcons_a_port.master = self.o.remote_cons
        self.o.rcons_b_port.master = self.o.remote_cons
        self.o.rtc = pre_obj('rtc_cb', 'MK48T08')
        self.o.rtc.time = self.tod
        self.o.kbd_a_port = pre_obj('kbd_a_port', 'Z8530-port')
        self.o.kbd_b_port = pre_obj('kbd_b_port', 'Z8530-port')
        self.o.ser_a_port = pre_obj('ser_a_port', 'Z8530-port')
        self.o.ser_b_port = pre_obj('ser_b_port', 'Z8530-port')
        self.o.kbd = pre_obj('kbd_port', 'Z8530')
        self.o.kbd.irq_level = 2
        self.o.kbd.a_port = self.o.kbd_a_port
        self.o.kbd.b_port = self.o.kbd_b_port
        self.o.serial = pre_obj('serial', 'Z8530')
        self.o.serial.irq_level = 2
        self.o.serial.a_port = self.o.ser_a_port
        self.o.serial.b_port = self.o.ser_b_port
        self.o.kbd_a_port.master = self.o.kbd
        self.o.kbd_b_port.master = self.o.kbd
        self.o.ser_a_port.master = self.o.serial
        self.o.ser_b_port.master = self.o.serial
        self.o.clock_space = pre_obj('clock_board_space', 'memory-space')
        self.o.clock_space.map = [
            [0x0000000, self.o.clks,        0, 0,   0x10],
            [0x0002000, self.o.serial,      0, 0,   0x10],
            [0x0004000, self.o.kbd,         0, 0,   0x10],
            [0x0006000, self.o.sysreg,      0, 0,   0x80],
            [0x0008000, self.o.rtc,         0, 0, 0x2000],
            [0x000a000, self.o.remote_cons, 0, 0,   0x10],
            [0x000c000, self.o.empty,       0, 0,    0x8]]
        self.change_frequency(self.freq_mhz)
        self.post_info[16] = 0x00001f0080001d1f

    def add_connector_info(self):
        for i in self.board_nums:
            self.connector_info['slot%d' % i] = [i,  self.o.phys_mem,
                                                 self.o.clock_space,
                                                 self.o.irqbus, self.tod,
                                                 self.freq_mhz]
        self.connector_info['central-cpu'] = [self.o.simicsfs]
        self.connector_info['ttya'] = [None, self.o.ser_a_port, 'ttya']
        self.connector_info['ttyb'] = [None, self.o.ser_b_port, 'ttyb']
        self.connector_info['keyboard'] = [None, self.o.kbd_a_port,
                                           'keyboard port']
        self.connector_info['mouse'] = [None, self.o.kbd_b_port, 'mouse port']
        self.connector_info['remote_console'] = [None, self.o.rcons_a_port,
                                                 'remote console']

    def connect_sunfire_backplane(self, connector, upa0_space, upa1_space,
                                  cpu0, cpu1, fhc, mb, post_info):
        board_no = self.connector_info[connector][0]
        # map board-space into phys-mem
        offset = BOARD_BASE + board_no * 2 * UPA_SPACE_SIZE
        for upa in [upa0_space, upa1_space]:
            self.o.phys_mem.map += [[offset, upa, 0, 0, UPA_SPACE_SIZE]]
            offset += UPA_SPACE_SIZE
        self.cpu_list[2 * board_no + 0] = cpu0
        self.cpu_list[2 * board_no + 1] = cpu1
        # TODO: remove next two when we use idle-loop optimizer instead?
        all_cpus = [x for x in self.cpu_list if x]
        if len(all_cpus):
            self.master_cpu = all_cpus[0]
        self.all_cpus = all_cpus
        #
        if cpu0:
            cpu0.simicsfs = self.o.simicsfs
        if cpu1:
            cpu1.simicsfs = self.o.simicsfs
        self.change_memory(board_no, mb)
        self.post_info[board_no] = post_info
        # update the list of fhc devices
        self.fhc_list.append(fhc)
        for o in self.fhc_list:
            o.fhc_list = self.fhc_list

    def connect_sunfire_central_cpu(self, connector, master_space, fhc):
        self.o.phys_mem.map += [[0x1fff8000000, master_space,
                                 0, 0, 0x08000000]]
        self.o.kbd.irq_dev = fhc
        self.o.serial.irq_dev = fhc

    def connect_serial(self, connector, link, console):
        if connector == 'ttya':
            if link:
                self.o.ser_a_port.link = link
            else:
                self.o.ser_a_port.console = console
        elif connector == 'ttyb':
            if link:
                self.o.ser_b_port.link = link
            else:
                self.o.ser_b_port.console = console
        elif connector == 'keyboard':
            if link:
                self.o.kbd_a_port.link = link
            else:
                self.o.kbd_a_port.console = console
        elif connector == 'mouse':
            if link:
                self.o.kbd_b_port.link = link
            else:
                self.o.kbd_b_port.console = console
        elif connector == 'remote_console':
            if link:
                self.o.rcons_a_port.link = link
            else:
                self.o.rcons_a_port.console = console

    def disconnect_serial(self, connector):
        if connector == 'ttya':
            # TODO: self.o.ser_a_port.link = None
            self.o.ser_a_port.console = None
        elif connector == 'ttyb':
            # TODO: self.o.ser_b_port.link = None
            self.o.ser_b_port.console = None
        elif connector == 'keyboard':
            # TODO: self.o.kbd_a_port.link = None
            self.o.kbd_a_port.console = None
        elif connector == 'mouse':
            # TODO: self.o.kbd_b_port.link = None
            self.o.kbd_b_port.console = None
        elif connector == 'remote_console':
            # TODO: self.o.rcons_a_port.link = None
            self.o.rcons_a_port.console = None

    def write_post_info_to_sram(self):
        for i in range(len(self.post_info)):
            write_memory(self.o.phys_mem, 0x1fff8206700 + i * 8,
                         self.post_info[i], 8)
            write_memory(self.o.phys_mem, 0x1fff82068f8 + i * 8,
                         self.post_info[i], 8)

    def get_clock(self):
        return self.master_cpu

    def get_processors(self):
        return self.all_cpus

    def set_processors(self, cpus):
        self.all_cpus = cpus

    def instantiation_done(self):
        component_object.instantiation_done(self)
        for i in range(len(self.fhc_list)):
            self.fhc_list[i] = SIM_get_object(self.fhc_list[i].name)
        for i in range(len(self.all_cpus)):
            self.all_cpus[i] = SIM_get_object(self.all_cpus[i].name)
        self.master_cpu = SIM_get_object(self.master_cpu.name)
        self.write_post_info_to_sram()
        write_idprom_to_nvram(self.obj, self.hostid, self.mac)
        conf.sim.handle_outside_memory = 1
        system = self.obj.name
        eval_cli_line('%s.set-prom-defaults' % system)
        eval_cli_line('%s.set-prom-env input-device ttya' % system)
        eval_cli_line('%s.set-prom-env sbus-probe-default "3120"' % system)
        eval_cli_line('%s.set-prom-env boot-command "boot disk1 -v"' % system)
        if 'keyboard' in [x[0] for x in self.connections]:
            # for now we assume a gfx terminal if a keyboard exists
            eval_cli_line('%s.set-prom-env input-device keyboard' % system)
            eval_cli_line('%s.set-prom-env output-device screen' % system)
            eval_cli_line('%s.set-prom-env "screen-#rows" 34' % system)
        else:
            eval_cli_line('%s.set-prom-env input-device ttya' % system)
            eval_cli_line('%s.set-prom-env output-device ttya' % system)
            eval_cli_line('%s.set-prom-env "screen-#rows" 24' % system)
        # OBP bug workaround
        self.lock_entry()

    def finalize_instance(self):
        component_object.finalize_instance(self)
        if self.instantiated and not self.obp_bugfix_done:
            # OBP bug workaround
            self.lock_entry()

def set_key_switch(obj, pos):
    fhc = get_component(obj).o.kbd.irq_dev
    sysreg = get_component(obj).o.sysreg
    fhcs = get_component(obj).fhc_list
    if sysreg.sys_stat1 & (1 << 5):
        if fhc.fhc_board_status & (1 << 6):
            cur = 'insecure'
        else:
            cur = 'diag'
    else:
        cur = 'secure'
    if pos == '':
        print 'Key-switch is in the "%s" position.' % cur
        return
    elif pos == 'diag':
        for fhc in fhcs:
            fhc.fhc_board_status = ((fhc.fhc_board_status & 0x00ffffbf)
                                    | (1 << 5))
        sysreg.sys_stat1 |= 1 << 5
    elif pos == 'insecure':
        for fhc in fhcs:
            fhc.fhc_board_status = ((fhc.fhc_board_status & 0x00ffffdf)
                                    | (1 << 6))
        sysreg.sys_stat1 |= 1 << 5
    elif pos == 'secure':
        for fhc in fhcs:
            fhc.fhc_board_status |= (1 << 6) | (1 << 5)
        sysreg.sys_stat1 &= 0xffffffdf
    else:
        print 'Illegal key-switch position "%s"' % pos
        SIM_command_has_problem()
        return
    if cur != pos:
        print '[%s] Changing key-switch to "%s" position' % (obj.name, pos)
    else:
        print '[%s] Keeping key-switch in "%s" position' % (obj.name, pos)
    
def key_expand(string):
    return get_completions(string, ['diag', 'insecure', 'secure'])

class sunfire_3500_backplane_component(sunfire_backplane_component):
    classname = 'sunfire-3500-backplane'
    basename = 'system'
    description = ('The "sunfire-3500-backplane" component represents the '
                   'chassis, backplane and clock-board of a Sun Enterprise '
                   '3500 server, with slots for up to five boards.')
    board_nums = range(1, 11, 2)
    for i in board_nums:
        sunfire_backplane_component.connectors['slot%d' % i] = {
            'type' : 'sunfire-backplane', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

class sunfire_4500_backplane_component(sunfire_backplane_component):
    classname = 'sunfire-4500-backplane'
    basename = 'system'
    description = ('The "sunfire-4500-backplane" component represents the '
                   'chassis, backplane and clock-board of a Sun Enterprise '
                   '4500 server, with slots for up to eight boards.')
    board_nums = range(8)
    for i in board_nums:
        sunfire_backplane_component.connectors['slot%d' % i] = {
            'type' : 'sunfire-backplane', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

class sunfire_6500_backplane_component(sunfire_backplane_component):
    classname = 'sunfire-6500-backplane'
    basename = 'system'
    description = ('The "sunfire-6500-backplane" component represents the '
                   'chassis, backplane and clock-board of a Sun Enterprise '
                   '6500 server, with slots for up to sixteen boards.')
    board_nums = range(16)
    for i in board_nums:
        sunfire_backplane_component.connectors['slot%d' % i] = {
            'type' : 'sunfire-backplane', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

freq_str = string.join(map(str, sorted(freq_list.keys())), ', ')

for model in [3500, 4500, 6500]:
    register_component_class(
        eval('sunfire_%s_backplane_component' % model),
        [['cpu_frequency', Sim_Attr_Required, 'i',
          'Processor frequency in MHz. Supported frequencies are %s.'
          % freq_str],
         ['hostid', Sim_Attr_Required, 'i',
          'The hostid of the machine.'],
         ['mac_address', Sim_Attr_Required, 's',
          'The main MAC address is the machine.'],
         ['rtc_time', Sim_Attr_Required, 's',
          'The date and time of the Real-Time clock.']],
        [['obp_bugfix_done', Sim_Attr_Optional, 'b',
          'Internal attribute.'],
         ['master_cpu', Sim_Attr_Optional, 's|o',
          'Internal attribute.']],
        top_level = True)
    register_obp_commands(eval('sunfire_%s_backplane_component' % model).classname)

    new_command('key-switch', set_key_switch,
                [arg(str_t, 'position', '?', '', expander = key_expand)],
                short = 'Change key switch position',
                namespace = 'sunfire-%d-backplane' % model,
                doc = 'Changes the position of the key-switch on the '
                'clock-board. Possible arguments are "diag", "insecure" and '
                '"secure". If no argument is specified, the current position '
                'is reported.')


### SunFire CPU Board


class sunfire_cpuboard_component(component_object):
    classname = 'sunfire-cpu-board'
    basename = 'board'
    description = ('The "sunfire-cpu-board" component represents a processor '
                   'board with up to two UltraSPARC II processors and 4GB of '
                   'memory, for use in Sun Enterprise 3500-6500 servers.')
    connectors = {
        'backplane'   : {'type' : 'sunfire-backplane', 'direction' : 'up',
                         'empty_ok' : False, 'hotplug' : False,
                         'multi' : False},
        'central-cpu' : {'type' : 'sunfire-central-cpu', 'direction' : 'up',
                         'empty_ok' : True, 'hotplug' : False,
                         'multi' : False}}
    for i in range(2):
        connectors['cache-cpu%d' % i] = {
            'type' : 'timing-model', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : True, 'multi' : False}
                
                   
    mem_banks = { 4096 : 2, 2048 : 2, 1024 : True, 512 : 2,
                  256 :  1,  128 : 2,   64 : True,   0 : False}
    bank_info = {2048 : { 'mask' : 0x1f, 'stat' : 0x62},
                 1024 : { 'mask' : 0x0f, 'stat' : 0x6f},
                  256 : { 'mask' : 0x03, 'stat' : 0x6b},
                   64 : { 'mask' : 0x00, 'stat' : 0x64}}
                 
    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.cpu = [None, None]
        self.o.mmu = [None, None]
        self.o.space = [None, None]
        self.o.cpu_space = [None, None]

    def get_num_cpus(self, idx):
        return self.num_cpus

    def set_num_cpus(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.num_cpus = val
        return Sim_Set_Ok

    def get_memory_megs(self, idx):
        return self.memory_megs

    def set_memory_megs(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if not val in self.mem_banks:
            SIM_attribute_error('Unsupported memory size')
            return Sim_Set_Illegal_Value
        self.memory_megs = val
        return Sim_Set_Ok

    def add_objects(self):
        flash, x = flash_create_memory('cpuprom$', 'Am29F040B',
                                       1, 8,
                                       [['openbootprom.sf', 1, 0, 0x80000]])
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.prom = flash_pre['cpuprom$']
        self.o.prom_image = flash_pre['cpuprom$_image']
        self.o.prom_ram = flash_pre['cpuprom$_ram']
        self.o.local_devices = pre_obj('board(x)_devices', 'memory-space')
        for i in [0, 1]:
            self.o.space[i] = pre_obj('upa(x * 2 + %d)_space' % i,
                                      'memory-space')
            self.o.space[i].map = [[0xf8000000, self.o.local_devices,
                                    0, 0, 0x08000000]]
        for i in range(self.num_cpus):
            self.o.cpu_space[i] = pre_obj('cpu(x * 2 + %d)_space' % i,
                                          'memory-space')
            self.o.cpu_space[i].map = [[0x1fff0000000, self.o.local_devices, 0,
                                        0, 0x08000000]]
            self.o.mmu[i] = pre_obj('mmu(x * 2 + %d)' % i, 'spitfire-mmu')
            self.o.cpu[i] = pre_obj('cpu(x * 2 + %d)' % i, 'ultrasparc-ii')
            self.o.cpu[i].processor_number = get_next_cpu_number()
            self.o.cpu[i].mmu = self.o.mmu[i]
            self.o.cpu[i].control_registers = [['mid', i]]
            self.o.cpu[i].physical_memory = self.o.cpu_space[i]
            self.o.cpu[i].queue = self.o.cpu[i]
        if self.num_cpus:
            self.component_queue = self.o.cpu[0]
        self.o.sram_image = pre_obj('sram(x)_image', 'image')
        self.o.sram_image.size = 0x8000
        self.o.sram = pre_obj('sram(x)', 'ram')
        self.o.sram.image = self.o.sram_image
        self.o.dtags_image = pre_obj('dtags(x)_image', 'image')
        self.o.dtags_image.size = 0x1000000
        self.o.dtags = pre_obj('dtags(x)', 'rom')
        self.o.dtags.image = self.o.dtags_image
        self.o.temp = pre_obj('temp(x)', 'sun4u-temperature')
        self.o.sstat = pre_obj('sstat(x)', 'sun4u-simm-status')
        self.o.ac = pre_obj('ac(x)', 'sun4u-ac')
        self.o.ac.brd_conf = 0
        self.o.fhc = pre_obj('fhc(x)', 'sun4u-fhc')
        self.o.local_devices.map = [
            [0x0000000, self.o.prom,  0, 0,   0x80000, self.o.prom_ram, 1, 1],
            [0x0200000, self.o.sram,   0, 0,    0x8000],
            [0x0400000, self.o.temp,   0, 0,      0x10],
            [0x0600000, self.o.sstat,  0, 0,      0x10],
            [0x0800000, self.o.fhc,    0, 0,    0xe020],
            [0x1000000, self.o.ac,     0, 0,    0x6030],
            [0x2000000, self.o.dtags,  0, 0, 0x1000000]]
        self.configure_memory(0)

    def add_connector_info(self):
        post_info = 0xff0f00001e000003
        num_banks = self.mem_banks[self.memory_megs]
        if self.num_cpus > 0:
            post_info |= 3 << 8
        if self.num_cpus > 1:
            post_info |= 3 << 16
        if num_banks > 0:
            post_info |= 1 << 52
        if num_banks > 1:
            post_info |= 1 << 54
        self.connector_info['backplane'] = [self.o.space[0], self.o.space[1],
                                            self.o.cpu[0], self.o.cpu[1],
                                            self.o.fhc, self.memory_megs,
                                            post_info]
        self.connector_info['central-cpu'] = [self.o.local_devices, self.o.fhc]
        for i in range(2):
            self.connector_info['cache-cpu%d' % i] = [i, self.o.cpu[i]]

    def configure_memory(self, start_addr):
        connector = [0 for i in range(16)]
        num_banks = self.mem_banks[self.memory_megs]
        for i in [0, 1]:
            exec "self.o.ac.bank%d_valid = 0" % i
            exec "self.o.ac.bank%d_mask = 0" % i
            exec "self.o.ac.bank%d_match = 0" % i
        for i in range(num_banks):
            mb = self.memory_megs / num_banks
            exec "self.o.ac.bank%d_valid = 1" % i
            exec "self.o.ac.bank%d_mask = self.bank_info[mb]['mask']" % i
            exec "self.o.ac.bank%d_match = start_addr >> 26" % i
            for j in range(8):
                connector[j + i * 8] = self.bank_info[mb]['stat']
        self.o.sstat.connector = connector

    def connect_sunfire_backplane(self, connector, board_no, phys_mem,
                                  clock_space, irq_bus, tod, freq_mhz):
                                  
        self.rename_component_objects(str(board_no))
        brd_upa = board_no * 2
        for i in range(self.num_cpus):
            self.o.cpu[i].cpu_group = irq_bus
            self.o.cpu[i].control_registers = [['mid', brd_upa + i]]
            self.o.cpu[i].freq_mhz = freq_mhz
        # 5 << 17 is 4MB if cache
        self.o.ac.brd_conf |= (((0x70 | board_no) << 24)
                               | (board_no << 20) | (5 << 17))
        self.o.fhc.mid = brd_upa
        self.o.fhc.irq_bus = irq_bus
        self.o.fhc.fhc_board_status = (((brd_upa & 1) << 16)
                                       | ((brd_upa & 0xe) << 12)
                                       | (5 << 10)
                                       | (5 << 7)
                                       | (1 << 6)
                                       | (1 << 1))
        for i in range(self.num_cpus):
            self.o.cpu_space[i].map += [
                [0x00000000000, phys_mem, 0, 0x00000000000, 0x1fff0000000],
                [0x1fff8000000, phys_mem, 0, 0x1fff8000000, 0x00008000000]]
        self.o.local_devices.map += [[0x0900000, clock_space, 0, 0, 0x100000]]

    def connect_sunfire_central_cpu(self, connector, simicsfs):
        # this board decodes the central space
        self.o.ac.brd_conf |= 1 << 31 | 1 << 15
        self.o.local_devices.map += [[0x0101000, simicsfs, 0, 0,    0x10]]

    def connect_timing_model(self, connector, cache):
        id = self.connector_info[connector][0]
        if id >= self.num_cpus:
            # ignore
            return
        self.o.cpu_space[id].timing_model = cache

    def disconnect_timing_model(self, connector):
        id = self.connector_info[connector][0]
        self.o.cpu_space[id].timing_model = None

    def instantiation_done(self):
        component_object.instantiation_done(self)
        # Write magic and cpu version to local SRAM
        for i in range(self.num_cpus):
            write_memory(self.o.local_devices, 0x00207800 + 0x400 * i,
                         0x5350495446495245, 8) 
            write_memory(self.o.local_devices, 0x00207830 + 0x400 * i,
                         0x0000001100000000, 8)
        # Patch POR reset to go directly to OBP
        write_memory(self.o.local_devices, 0x00000020, 0x30800028, 4)
        write_memory(self.o.local_devices, 0x00000024, 0x01000000, 4)
        # Pass POST info to OBP in registers
        for i in range(self.num_cpus):
            cpu = self.o.cpu[i]
            SIM_write_register(cpu, SIM_get_register_number(cpu, 'o2'),
                               0x1fff8206700)
            SIM_write_register(cpu, SIM_get_register_number(cpu, 'o3'),
                               0x6000)
    
register_component_class(
    sunfire_cpuboard_component,
    [['num_cpus', Sim_Attr_Required, 'i',
      'Number of processors on the board (1 or 2).'],
     ['memory_megs', Sim_Attr_Required, 'i',
      'The amount of RAM in megabytes on the processor board.']])


### SunFire SBus Board


class sunfire_sbusboard_component(component_object):
    classname = 'sunfire-sbus-board'
    basename = 'board'
    description = ('The "sunfire-sbus-board" component represents an I/O '
                   'board with slots for up to three SBus cards, for use in '
                   'Sun Enterprise 3500-6500 servers. The board has one '
                   'HME ethernet controller and one FAS SCSI controller '
                   'on-board. <insert id="sunfire-sbus-board-extras"/>')
    connectors = {
        'backplane' : {'type' : 'sunfire-backplane', 'direction' : 'up',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'scsi-bus'  : {'type' : 'scsi-bus', 'direction' : 'down',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet'  : {'type' : 'ethernet-link', 'direction' : 'down',
                       'empty_ok' : True, 'hotplug' : True, 'multi' : False}}
    for i in range(3):
        connectors['slot%d' % i] = {
            'type' : 'sun-sbus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    slot_to_upa = {0 : True, 1 : False, 2 : False, 3 : True, 0xd : False}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.space = [None, None]
        self.o.sysio = [None, None]
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
        flash, x = flash_create_memory('io1prom$', 'Am29F040B',
                                       1, 8,
                                       [['io1prom', 1, 0, 0x80000]])
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.prom = flash_pre['io1prom$']
        self.o.prom_image = flash_pre['io1prom$_image']
        self.o.prom_ram = flash_pre['io1prom$_ram']
        self.o.rtc = pre_obj('rtc(x)', 'MK48T08')
        self.o.ac = pre_obj('ac(x)', 'sun4u-ac')
        self.o.fhc = pre_obj('fhc(x)', 'sun4u-fhc')
        self.o.sspeed = pre_obj('sspeed(x)', 'sun4u-sbus-speed')
        for i in [0, 1]:
            self.o.sysio[i] = pre_obj('sysio(x * 2 + %d)' % i, 'sunfire-sysio')
            self.o.space[i] = pre_obj('upa(x * 2 + %d)_space' % i,
                                      'memory-space')
        self.o.temp = pre_obj('temp(x)', 'sun4u-temperature')
        self.o.sbus0_1_space = pre_obj('sbus(x * 2 + 0)_1_space',
                                       'memory-space')
        self.o.sbus0_2_space = pre_obj('sbus(x * 2 + 0)_2_space',
                                       'memory-space')
        self.o.sbus1_0_space = pre_obj('sbus(x * 2 + 1)_0_space',
                                       'memory-space')
        self.o.sbus1_3_space = pre_obj('sbus(x * 2 + 1)_3_space',
                                       'memory-space')
        self.o.local_devices = pre_obj('board(x)_devices', 'memory-space')
        self.o.space[0].map = [
            [0x0000000000, self.o.sysio[0],      0, 0,     0x6000],
            [0x00f8000000, self.o.local_devices, 0, 0, 0x08000000],
            [0x0110000000, self.o.sbus0_1_space, 0, 0, 0x10000000],
            [0x0120000000, self.o.sbus0_2_space, 0, 0, 0x10000000]]
        self.o.space[1].map = [
            [0x0000000000, self.o.sysio[1],      0, 0,     0x6000],
            [0x00f8000000, self.o.local_devices, 0, 0, 0x08000000],
            [0x0100000000, self.o.sbus1_0_space, 0, 0, 0x10000000],
            [0x0130000000, self.o.sbus1_3_space, 0, 0, 0x10000000]]
        # on-board devices
        self.o.fasdma = pre_obj('fasdma$', 'sun4u-fasdma')
        self.o.fas = pre_obj('fas$', 'FAS366U')
        self.o.fas.scsi_target = self.scsi_id
        self.o.fas.dma_dev = self.o.fasdma
        self.o.fas.dma_channel = 0
        self.o.hme = pre_obj('hme$', 'sbus-hme')
        self.o.hme.mac_address = mac_as_list(self.mac)
        self.o.fasdma.memory = self.o.sbus1_3_space
        self.o.fas.irq_dev = self.o.sysio[1]
        self.o.fas.irq_level = 3 * 8 + 3
        self.o.hme.irq_dev = self.o.sysio[1]
        self.o.hme.irq_level = 3 * 8 + 4
        self.o.hme.memory = self.o.sbus1_3_space
        self.o.local_devices.map = [
            [0x0000000, self.o.prom,   0, 0,   0x80000, self.o.prom_ram, 1, 1],
            [0x0300000, self.o.rtc,    0, 0,    0x2000],
            [0x0400000, self.o.temp,   0, 0,      0x10],
            [0x0500000, self.o.sspeed, 0, 0,      0x10],
            [0x0800000, self.o.fhc,    0, 0,    0xe020],
            [0x1000000, self.o.ac,     0, 0,    0x6030]]
        self.o.sbus0_1_space.map = []
        self.o.sbus0_2_space.map = []
        self.o.sbus1_0_space.map = []
        self.o.sbus1_3_space.map = [
            [0x08800000, self.o.fasdma, 0, 0,    0x18],
            [0x08810000, self.o.fas,    0, 0,   0x200],
            [0x08c00000, self.o.hme,    0, 0, 0x10000],
            [0x0c800000, self.o.hme,    1, 0,    0x1a]]

    def add_connector_info(self):
        self.connector_info['ethernet'] = []
        self.connector_info['scsi-bus'] = [self.o.fas, self.scsi_id]
        post_info = 0xff0c00009e07a70b
        self.connector_info['backplane'] = [self.o.space[0], self.o.space[1],
                                            None, None, self.o.fhc, 0,
                                            post_info]
        for i in range(3):
            upa = self.slot_to_upa[i]
            self.connector_info['slot%d' % i] = [
                i,
                self.o.sysio[upa],
                eval('self.o.sbus%d_%d_space' % (upa, i))]

    def connect_sunfire_backplane(self, connector, board_no, phys_mem,
                                  clock_space, irq_bus, tod, freq_mhz):
        self.rename_component_objects(str(board_no))
        brd_upa = board_no * 2
        self.o.ac.brd_conf = (((0x70 | board_no) << 24)
                            | (board_no << 20) | (0 << 17))
        self.o.fhc.mid = brd_upa
        self.o.fhc.irq_bus = irq_bus
        self.o.fhc.fhc_board_status = (((brd_upa & 1) << 16)
                                       | ((brd_upa & 0xe) << 12)
                                       | (5 << 10)
                                       | (5 << 7)
                                       | (1 << 6)
                                       | (1 << 1))
        self.o.rtc.time = tod
        for upa in [0, 1]:
            self.o.sysio[upa].mid = brd_upa + upa
            self.o.sysio[upa].irq_bus = irq_bus
            self.o.sysio[upa].memory = phys_mem
        for i in range(4):
            upa = self.slot_to_upa[i]
            exec "mem = self.o.sbus%d_%d_space.map" % (upa, i)
            mem += [[0x80000000, self.o.sysio[upa], i, 0,
                     0x80000000, phys_mem, 0, 0x2000, 0]]
            exec "self.o.sbus%d_%d_space.map = mem" % (upa, i)

    def connect_sun_sbus(self, connector):
        pass

    def connect_scsi_bus(self, connector, bus):
        self.o.fas.scsi_bus = bus

    def connect_ethernet_link(self, connector, link):
        self.o.hme.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.hme.link = None

register_component_class(
    sunfire_sbusboard_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the onboard Ethernet adapter.'],
     ['scsi_id', Sim_Attr_Optional, 'i',
      'The ID on the SCSI bus.']])


### SunFire PCI Board


class sunfire_pciboard_component(component_object):
    classname = 'sunfire-pci-board'
    basename = 'board'
    description = ('The "sunfire-pci-board" component represents an I/O '
                   'board with slots for up to two PCI cards, for use in '
                   'Sun Enterprise 3500-6500 servers. The board has one '
                   'HME ethernet controller and one ISP SCSI controller '
                   'on-board. <insert id="sunfire-pci-board-extras"/>')
    connectors = {
        'backplane' : {'type' : 'sunfire-backplane', 'direction' : 'up',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'pci-slot0': {'type' : 'pci-bus', 'direction' : 'down',
                       'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'pci-slot2': {'type' : 'pci-bus', 'direction' : 'down',
                       'empty_ok' : True, 'hotplug' : False, 'multi' : False},
        'scsi-bus'  : {'type' : 'scsi-bus', 'direction' : 'down',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'ethernet'  : {'type' : 'ethernet-link', 'direction' : 'down',
                       'empty_ok' : True, 'hotplug' : False, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.space = [None, None]
        self.o.psycho = [None, None]
        self.o.pcicfg = [None, None]
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
        flash, x = flash_create_memory('io3prom$', 'Am29F040B',
                                       1, 8,
                                       [['io3prom', 1, 0, 0x80000]])
        flash_pre = convert_to_pre_objects(flash, pre_obj)
        self.o.prom = flash_pre['io3prom$']
        self.o.prom_image = flash_pre['io3prom$_image']
        self.o.prom_ram = flash_pre['io3prom$_ram']
        self.o.rtc = pre_obj('rtc(x)', 'MK48T08')
        self.o.ac = pre_obj('ac(x)', 'sun4u-ac')
        self.o.fhc = pre_obj('fhc(x)', 'sun4u-fhc')
        self.o.temp = pre_obj('temp(x)', 'sun4u-temperature')
        self.o.local_devices = pre_obj('board(x)_devices', 'memory-space')
        for i in [0, 1]:
            self.o.space[i] = pre_obj('upa(x * 2 + %d)_space' % i,
                                      'memory-space')
            self.o.psycho[i] = pre_obj('psycho(x * 2 + %d)' % i,
                                       'sunfire-psycho')
            self.o.pcicfg[i] = pre_obj('pcicfg(x * 2 + %d)' % i,
                                       'memory-space')
        for upa in [0, 1]:
            self.o.psycho[upa].io_space = self.o.space[upa]
            for bus in ['A', 'B']:
                ids = '%d%s' % (upa, bus)
                idx = '(x * 2 + %d)%s' % (upa, bus)
                exec ("self.o.pcibus%s = pre_obj('pcibus%s', 'pci-bus')"
                      % (ids, idx))
                exec ("self.o.pciio%s = pre_obj('pciio%s', 'memory-space')"
                      % (ids, idx))
                exec ("self.o.pcimem%s = pre_obj('pcimem%s', 'memory-space')"
                      % (ids, idx))
                exec ("self.o.psycho[upa].pci_bus%s = self.o.pcibus%s"
                      % (bus, ids))
                exec "self.o.pcibus%s.bridge = self.o.psycho[upa]" % ids
                exec "self.o.pcibus%s.memory_space = self.o.pcimem%s" % (ids,
                                                                         ids)
                exec "self.o.pcibus%s.io_space = self.o.pciio%s" % (ids, ids)
                exec "self.o.pcibus%s.conf_space = self.o.pcicfg[upa]" % ids
                exec "self.o.pcibus%s.pci_devices = []" % ids
            self.o.space[upa].map = [
                [0x00000000, self.o.psycho[upa],   0, 0, 0x0000d000],
                [0xf8000000, self.o.local_devices, 0, 0, 0x08000000]]
        self.o.local_devices.map = [
            [0x0000000, self.o.prom, 0, 0, 0x80000, self.o.prom_ram, 1, 1],
            [0x0300000, self.o.rtc,  0, 0,  0x2000],
            [0x0400000, self.o.temp, 0, 0,    0x10],
            [0x0800000, self.o.fhc,  0, 0,  0xe020],
            [0x1000000, self.o.ac,   0, 0,  0x6030]]
        # on-board devices, isp: (upa + 1) slot 3 ; hme: (upa + 0) slot 1
        self.o.isp = pre_obj('isp$', 'ISP1040')
        self.o.isp.scsi_id = self.scsi_id
        self.o.isp.pci_bus = self.o.pcibus1B
        self.o.pcibus1B.pci_devices = [[3, 0, self.o.isp]]
        self.o.hme = pre_obj('hme$', 'cheerio-hme')
        self.o.hme.pci_bus = self.o.pcibus0B
        self.o.hme.mac_address = mac_as_list(self.mac)
        self.o.e2bus = pre_obj('e2bus$', 'cheerio-e2bus')
        self.o.e2bus.pci_bus = self.o.pcibus0B
        self.o.pcibus0B.pci_devices = [[1, 0, self.o.e2bus],
                                       [1, 1, self.o.hme]]

    def add_connector_info(self):
        post_info = 0xff0c00009ff80313
        self.connector_info['backplane'] = [self.o.space[0], self.o.space[1],
                                            None, None, self.o.fhc, 0,
                                            post_info]
        self.connector_info['scsi-bus'] = [self.o.isp, self.scsi_id]
        self.connector_info['pci-slot0'] = [2, self.o.pcibus0A]
        self.connector_info['pci-slot2'] = [2, self.o.pcibus1A]
        self.connector_info['ethernet'] = []

    def connect_sunfire_backplane(self, connector, board_no, phys_mem,
                                  clock_space, irq_bus, tod, freq_mhz):
        self.rename_component_objects(str(board_no))
        brd_upa = board_no * 2
        self.o.ac.brd_conf = (((0x70 | board_no) << 24)
                            | (board_no << 20) | (0 << 17))
        self.o.fhc.mid = brd_upa
        self.o.fhc.irq_bus = irq_bus
        self.o.fhc.fhc_board_status = (((brd_upa & 1) << 16)
                                       | ((brd_upa & 0xe) << 12)
                                       | (5 << 10)
                                       | (5 << 7)
                                       | (1 << 6)
                                       | (1 << 1))
        self.o.rtc.time = tod
        for upa in [0, 1]:
            self.o.psycho[upa].mid = brd_upa + upa
            self.o.psycho[upa].irq_bus = irq_bus
            self.o.psycho[upa].memory = phys_mem

    def connect_scsi_bus(self, connector, bus):
        self.o.isp.scsi_bus = bus

    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        devs = bus.pci_devices
        for dev in device_list:
            devs += [[slot, dev[0], dev[1]]]
        bus.pci_devices = devs

    def connect_ethernet_link(self, connector, link):
        self.o.hme.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.hme.link = None

register_component_class(
    sunfire_pciboard_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the onboard Ethernet adapter.'],
     ['scsi_id', Sim_Attr_Optional, 'i',
      'The ID on the SCSI bus.']])


### Sun Fas/Hme SBus Device


class sun_sbus_fas_hme_component(component_object):
    classname = 'sun-sbus-fas-hme'
    basename = 'scsi_eth'
    description = ('The "sun-sbus-fas-hme" component represents an SBus '
                   'card with one HME ethernet controller and one FAS SCSI '
                   'controller for use in Sun systems.')
    connectors = {
        'sbus'     : {'type' : 'sun-sbus', 'direction' : 'up',
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
        self.o.fasdma = pre_obj('fasdma$', 'sun4u-fasdma')
        self.o.fas = pre_obj('fas$', 'FAS366U')
        self.o.fas.scsi_target = self.scsi_id
        self.o.fas.dma_dev = self.o.fasdma
        self.o.fas.dma_channel = 0
        self.o.hme = pre_obj('hme$', 'sbus-hme')
        self.o.hme.mac_address = mac_as_list(self.mac)
        self.o.prom_image = pre_obj('feps_prom$_image', 'image')
        self.o.prom_image.size = 0x8000
        self.o.prom_image.files = [['sunswift.prom', 1, 0, 32144]]
        self.o.prom = pre_obj('feps_prom$', 'rom')
        self.o.prom.image = self.o.prom_image

    def add_connector_info(self):
        self.connector_info['sbus'] = []
        self.connector_info['ethernet'] = []
        self.connector_info['scsi-bus'] = [self.o.fas, self.scsi_id]
        
    def connect_sun_sbus(self, connector, slot_no, sysio, space):
        self.o.fasdma.memory = space
        self.o.fas.irq_dev = sysio
        self.o.fas.irq_level = slot_no * 8 + 3
        self.o.hme.irq_dev = sysio
        self.o.hme.irq_level = slot_no * 8 + 4
        self.o.hme.memory = space
        space.map += [[0x00000000, self.o.prom,   0, 0,  0x8000],
                      [0x08800000, self.o.fasdma, 0, 0,    0x18],
                      [0x08810000, self.o.fas,    0, 0,   0x200],
                      [0x08c00000, self.o.hme,    0, 0, 0x10000],
                      [0x0c800000, self.o.hme,    1, 0,    0x1a]]

    def connect_scsi_bus(self, connector, bus):
        self.o.fas.scsi_bus = bus

    def connect_ethernet_link(self, connector, link):
        self.o.hme.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.hme.link = None

register_component_class(
    sun_sbus_fas_hme_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.'],
     ['scsi_id', Sim_Attr_Optional, 'i',
      'The ID on the SCSI bus.']])
