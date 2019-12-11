# MODULE: serengeti-components
# CLASS: serengeti-3800-chassis
# CLASS: serengeti-4800-chassis
# CLASS: serengeti-4810-chassis
# CLASS: serengeti-6800-chassis
# CLASS: serengeti-cluster-chassis
# CLASS: serengeti-us-iii-cpu-board
# CLASS: serengeti-us-iii-plus-cpu-board
# CLASS: serengeti-us-iv-cpu-board
# CLASS: serengeti-us-iv-plus-cpu-board
# CLASS: serengeti-pci8-board
# CLASS: serengeti-cpci4-board
# CLASS: serengeti-sp-cpci6-board
# CLASS: sun-cpci-hme-isp
# CLASS: sun-cpci-isp-isp
# CLASS: sun-cpci-qlc-qlc

import time
from sim_core import *
from components import *
from serengeti_obp import register_obp_commands

MB_PER_BOARD     = 32 * 1024 # 32 GB
CPU_BRD_PER_NODE = 6
IO_BRD_PER_NODE  = 4
BOARDS_PER_NODE  = CPU_BRD_PER_NODE + IO_BRD_PER_NODE
AID_PER_NODE     = 32

# number of banks for memory (in MB)
banks_per_cpu = {8192 : 4, 4096 : 2, 2048 : 1, 1024 : 1,
                 512 : 1, 256 : 1, 128 : 1, 64 : 1, 0 : 0}
bank_mask = {2048 : 0x1f, 1024 : 0xf, 512 : 0x7, 256 : 0x3, 128 : 0x1, 0 : 0x0}


### Serengeti Chassis


class serengeti_chassis_component(component_object):
    connectors = {
        'console' : {'type' : 'serial', 'direction' : 'down',
                     'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

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

    def update_memory(self):
        cpu_megs = reduce(lambda x, y: x + y, self.cpu_megs.values())
        self.o.memory_image.size = sum(cpu_megs) * 1024 * 1024
        mem = self.o.phys_mem.map
        mem = [x for x in mem if x[1] != self.o.memory]
        last_size = 0
        self.o.sc.mem_slices = []
        self.o.sc.mem_banks = []
        for brd in self.cpu_megs.keys():
            node = brd / BOARDS_PER_NODE
            board = brd % BOARDS_PER_NODE
            mem_start = (((CPU_BRD_PER_NODE * node) + board) * MB_PER_BOARD
                         * 1024 * 1024)
            mem_size = sum(self.cpu_megs[brd]) * 1024 * 1024
            if mem_size == 0:
                continue
            self.o.sc.mem_slices += [
                [node * CPU_BRD_PER_NODE + board,
                 mem_start, mem_size, self.o.phys_mem]]
            mem += [[mem_start, self.o.memory, 0, last_size, mem_size]]
            last_size += mem_size
            self.max_mem_address = mem_start + mem_size
            # set all memory-banks
            for i in range(len(self.cpu_megs[brd])):
                cpu = node * AID_PER_NODE + board * 4 + i
                banks = banks_per_cpu[self.cpu_megs[brd][i]]
                for j in range(1, banks + 1):
                    self.o.sc.mem_banks += [
                        [cpu, j, self.cpu_megs[brd][i] / banks]]
        self.o.phys_mem.map = mem

    def add_objects(self):
        self.o.memory_image = pre_obj('memory_image', 'image')
        self.o.memory_image.size = 0
        self.o.memory = pre_obj('memory', 'ram')
        self.o.memory.image = self.o.memory_image
        self.o.fpost_code_image = pre_obj('fpost_code_image', 'image')
        self.o.fpost_code_image.size = 0x2000
        self.o.fpost_code = pre_obj('fpost_code', 'rom')
        self.o.fpost_code.image = self.o.fpost_code_image
        self.o.fpost_data_image = pre_obj('fpost_data_image', 'image')
        self.o.fpost_data_image.size = 0x2000
        self.o.fpost_data = pre_obj('fpost_data', 'ram')
        self.o.fpost_data.image = self.o.fpost_data_image
        self.o.empty0_image = pre_obj('empty0_image', 'image')
        self.o.empty0_image.size = 0x2000
        self.o.empty0 = pre_obj('empty0', 'ram')
        self.o.empty0.image = self.o.empty0_image
        self.o.empty1_image = pre_obj('empty1_image', 'image')
        self.o.empty1_image.size = 0x2000
        self.o.empty1 = pre_obj('empty1', 'ram')
        self.o.empty1.image = self.o.empty1_image
        self.o.cpuprom_image = pre_obj('cpuprom_image', 'image')
        self.o.cpuprom_image.size = 0xbd3b0
        self.o.cpuprom_image.files = [['sgcpu.flash', 1, 0, 0xbd3b0]]
        self.o.cpuprom = pre_obj('cpuprom', 'rom')
        self.o.cpuprom.image = self.o.cpuprom_image
        self.o.simicsfs = pre_obj('simicsfs', 'hostfs')
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.phys_mem.map = [
            [0x00000000000, self.o.memory,     0,    0,       0],
            [0x7fff07ffff0, self.o.simicsfs,   0,    0,    0x10]]
        self.o.phys_io = pre_obj('phys_io', 'memory-space')
        self.o.phys_io.map = [
            [0x7fff0000000, self.o.cpuprom,    0,    0, 0xbd3b0],
            [0x7fff0102000, self.o.fpost_code, 0,    0,  0x2000],
            [0x7fff0104000, self.o.fpost_data, 0,    0,  0x2000],
            [0x7fff0800060, self.o.empty0,     0, 0x60,    0x10],
            [0x7fff091e000, self.o.empty1,     0,    0,   0x120]]
        self.o.irqbus = pre_obj('irqbus', 'sparc-irq-bus')
        self.o.nvci = pre_obj('nvci', 'nvci')
        self.o.nvci.security_badlogins = '0'
        self.o.nvci.oem_bannerQ = 'true'
        self.o.nvci.oem_banner = 'Simics Serengeti System'
        self.o.nvci.nvramrc = (
            'devalias disk /ssm@0,0/pci@19,700000/scsi@2/disk@0,0')
        self.o.nvci.use_nvramrcQ = 'true'
        self.o.nvci.boot_device = 'disk'
        self.o.nvci.diag_device = 'disk'
        self.o.nvci.error_reset_recovery = 'none'
        self.o.nvci.auto_bootQ = 'true'
        self.o.nvci.boot_command = 'boot -v'
        self.o.nvci.input_device = '/sgcn'
        self.o.nvci.output_device = '/sgcn'
        self.o.nvci.fcode_debugQ = 'true'
        self.o.nvci.use_4xfcodeQ = 'true'
        self.o.nvci.silent_modeQ = 'false'
        self.o.nvci.diag_switchQ = 'true'
        self.o.sc = pre_obj('sc', 'serengeti-console')
        self.o.sc.nvci = self.o.nvci
        self.o.sc.irq_bus = self.o.irqbus
        self.o.sc.time = self.tod
        self.o.sc.io_spaces = [[0, self.o.phys_io]]
        self.o.sc.boards = []
        self.o.sc.chassis_type = self.chassis
        self.nvci = self.o.nvci
        self.all_cpus = []
        self.master_mid = 1000000
        self.cpu_megs = {}
        self.o.sc.idprom = (mac_as_list(self.mac) +
                            [0x39, 0xd0, 0xee, 0xb6] +
                            [(self.hostid >> 24) & 0xff,
                             (self.hostid >> 16) & 0xff,
                             (self.hostid >> 8) & 0xff,
                             self.hostid & 0xff])

    def add_connector_info(self):
        self.connector_info['console'] = [None, self.o.sc, 'Serengeti Console']
        for i in self.cpu_slots:
            self.connector_info['cpu-slot%d' % i] = [
                i,
                (i / 10) * 32 + (i % 10) * 4,
                self.o.phys_mem, self.o.phys_io, self.o.irqbus]
        for i in self.io_slots:
            self.connector_info['io-slot%d' % i] = [
                i,
                (i / 10 * 32) + (CPU_BRD_PER_NODE * 4)
                + ((i % 10) - CPU_BRD_PER_NODE) * 2,
            self.o.phys_mem, self.o.phys_io, self.o.irqbus, self.o.sc]

    def connect_serengeti_cpu_board(self, connector, board_type,
                                    num_cpus, freq_mhz, cpus, cpu_megs):
        brdid = self.connector_info[connector][0]
        self.o.sc.boards += [[brdid, board_type, num_cpus, freq_mhz]]
        self.cpu_megs[brdid] = cpu_megs
        self.all_cpus += cpus
        for c in cpus:
            c.simicsfs = self.o.simicsfs
        for c in self.all_cpus:
            mid = [x[1] for x in c.control_registers if x[0] == 'mid'][0]
            if mid < self.master_mid:
                self.master_mid = mid
                self.master_cpu = c
                self.o.sc.master_cpu = c
        self.update_memory()

    def connect_serengeti_io_board(self, connector, board_type, sbbc):
        brdid = self.connector_info[connector][0]
        self.o.sc.boards += [[brdid, board_type]]
        self.o.sc.iosram_sbbc = sbbc

    def connect_serengeti_sp_io_board(self, connector, board_type, sbbc):
        return self.connect_serengeti_io_board(connector, board_type, sbbc)

    def connect_serial(self, connector, link, console):
        if link:
            self.o.sc.link = link
        else:
            self.o.sc.console = console

    def disconnect_serial(self, connector):
        # TODO: self.o.sc.link = None
        self.o.sc.console = None

    def get_clock(self):
        return self.master_cpu

    def get_processors(self):
        return self.all_cpus

    def set_processors(self, cpus):
        self.all_cpus = cpus

    def instantiation_done(self):
        component_object.instantiation_done(self)
        offset = self.max_mem_address - 0x00800000 - 0xf0000000
        for i in range(len(self.all_cpus)):
            self.all_cpus[i] = SIM_get_object(self.all_cpus[i].name)
        self.master_cpu = SIM_get_object(self.master_cpu.name)
        # handle wrap-around
        if offset < 0:
            offset = 0x10000000000000000 + offset
        SIM_load_binary(self.o.phys_mem, 'openbootprom.sg', offset, 0, 0)
        newpc = SIM_load_binary(self.o.phys_io, 'fpost', 0, 0, 0)
        newpc |= 0xfffffffff0000000
        for cpu in self.all_cpus:
            pc = SIM_get_program_counter(cpu)
            instr = 0x10800000 | ((newpc - pc) >> 2) # branch to OBP
            pc &= 0x7ffffffffff # physical address
            eval_cli_line('%s.set 0x%x 0x%x 4' % (
                self.o.phys_io.name, pc, instr)) # ba
            eval_cli_line('%s.set 0x%x 0x%x 4' % (
                self.o.phys_io.name, pc + 4, 0x01000000)) # nop
        conf.sim.handle_outside_memory = 1

class serengeti_3800_chassis_component(serengeti_chassis_component):
    classname = 'serengeti-3800-chassis'
    basename = 'system'
    description = ('The "sunfire-3800-chassis" component represents the '
                   'chassis, backplane and system-console of a Sun Fire 3800 '
                   'server, with slots for up to two processor boards and '
                   'two I/O boards. The system is sometimes called SP for '
                   'Service Provider server.')
    cpu_slots = (0, 2)
    io_slots = (6, 8)
    chassis = 'SP'
    connectors = serengeti_chassis_component.connectors.copy()
    for i in cpu_slots:
        connectors['cpu-slot%d' % i] = {
            'type' : 'serengeti-cpu-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    for i in io_slots:
        connectors['io-slot%d' % i] = {
            'type' : 'serengeti-sp-io-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

class serengeti_4800_chassis_component(serengeti_chassis_component):
    classname = 'serengeti-4800-chassis'
    basename = 'system'
    description = ('The "sunfire-4800-chassis" component represents the '
                   'chassis, backplane and system-console of a Sun Fire 4800 '
                   'server, with slots for up to three processor boards and '
                   'two I/O boards. The system is sometimes called MD for '
                   'Midrange Desk-side server.')
    cpu_slots = (0, 2, 4)
    io_slots = (6, 8)
    chassis = 'MD'
    connectors = serengeti_chassis_component.connectors.copy()
    for i in cpu_slots:
        connectors['cpu-slot%d' % i] = {
            'type' : 'serengeti-cpu-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    for i in io_slots:
        connectors['io-slot%d' % i] = {
            'type' : 'serengeti-io-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

class serengeti_4810_chassis_component(serengeti_chassis_component):
    classname = 'serengeti-4810-chassis'
    basename = 'system'
    description = ('The "sunfire-4810-chassis" component represents the '
                   'chassis, backplane and system-console of a Sun Fire 4810 '
                   'server, with slots for up to three processor boards and '
                   'two I/O boards. The system is sometimes called ME for '
                   'Midrange Enterprise server.')
    cpu_slots = (0, 2, 4)
    io_slots = (6, 8)
    chassis = 'ME'
    connectors = serengeti_chassis_component.connectors.copy()
    for i in cpu_slots:
        connectors['cpu-slot%d' % i] = {
            'type' : 'serengeti-cpu-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    for i in io_slots:
        connectors['io-slot%d' % i] = {
            'type' : 'serengeti-io-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

class serengeti_6800_chassis_component(serengeti_chassis_component):
    classname = 'serengeti-6800-chassis'
    basename = 'system'
    description = ('The "sunfire-6800-chassis" component represents the '
                   'chassis, backplane and system-console of a Sun Fire 6800 '
                   'server, with slots for up to six processor boards and '
                   'four I/O boards. The system is sometimes called DS for '
                   'Datacenter Server.')
    cpu_slots = range(6)
    io_slots = range(6, 10)
    chassis = 'DS'
    connectors = serengeti_chassis_component.connectors.copy()
    for i in cpu_slots:
        connectors['cpu-slot%d' % i] = {
            'type' : 'serengeti-cpu-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    for i in io_slots:
        connectors['io-slot%d' % i] = {
            'type' : 'serengeti-io-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

class serengeti_cluster_chassis_component(serengeti_chassis_component):
    classname = 'serengeti-cluster-chassis'
    basename = 'cluster'
    description = ('The "sunfire-cluster-chassis" component represents the '
                   'chassis, backplane and system-console of up to sixteen '
                   'Sun Fire 6800 servers connected in a cluster. This setup '
                   'is to be considered experimental, and Solaris does not '
                   'support all possible configurations of this component.')
    cpu_slots = []
    io_slots = []
    for node in range(16):
        cpu_slots += range(node * 10, node * 10 + 6)
        io_slots  += range(node * 10 + 6, node * 10 + 10)
    chassis = 'DS'
    connectors = serengeti_chassis_component.connectors.copy()
    for i in cpu_slots:
        connectors['cpu-slot%d' % i] = {
            'type' : 'serengeti-cpu-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}
    for i in io_slots:
        connectors['io-slot%d' % i] = {
            'type' : 'serengeti-io-board', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

for model in ['3800', '4800', '4810', '6800', 'cluster']:
    register_component_class(
        eval('serengeti_%s_chassis_component' % model),
        [['hostid', Sim_Attr_Required, 'i',
          'The hostid of the machine.'],
         ['mac_address', Sim_Attr_Required, 's',
          'The main MAC address is the machine.'],
         ['rtc_time', Sim_Attr_Required, 's',
          'The date and time of the Real-Time clock.']],
        top_level = True)
    register_obp_commands(
        eval('serengeti_%s_chassis_component' % model).classname)


### Serengeti CPU Board


class serengeti_cpuboard_component(component_object):
    connectors = {
        'chassis' : {'type' : 'serengeti-cpu-board', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False}}
    dualcore = 0
    for i in range(4 + 4 * dualcore):
        connectors['cache-cpu%d' % i] = {
            'type' : 'timing-model', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : True, 'multi' : False}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.cpu = [None] * 8
        self.o.mmu = [None] * 8
        self.o.cpu_space = [None] * 8
        self.o.cpu_iospace = [None] * 8
        self.cpu_spaces = 0
        self.first_id = 0

    def get_num_cpus(self, idx):
        return self.num_cpus

    def set_num_cpus(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if val > 4:
            return Sim_Set_Illegal_Value
        self.num_cpus = val
        self.num_cores = iff(self.dualcore, val * 2, val)
        return Sim_Set_Ok

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def get_memory_megs(self, idx):
        return sum(self.cpu_megs)

    def set_memory_megs(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        mb = val
        self.cpu_megs = []
        mem_sizes = sorted(banks_per_cpu.keys(), reverse = True)
        for i in range(self.num_cpus):
            self.cpu_megs.append(0)
            for j in mem_sizes:
                if mb >= j:
                    self.cpu_megs[i] = j
                    mb -= j
                    break
        if mb != 0:
            SIM_attribute_error('Unsupported memory size %s' % val)
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def add_cpu_spaces(self):
        self.cpu_spaces = 1
        for i in range(self.num_cores):
            aid = self.first_id + iff(self.dualcore, i / 2 + (i % 2) * 512, i)
            self.o.cpu_space[i] = pre_obj('cpu(x + %d)_space' % aid,
                                          'memory-space')
            old = self.o.cpu[i].physical_memory
            self.o.cpu[i].physical_memory = self.o.cpu_space[i]
            if old:
                self.o.cpu_space[i].default_target = [old, 0, 0, None]
            self.o.cpu_iospace[i] = pre_obj('cpu(x + %d)_iospace' % aid,
                                            'memory-space')
            old = self.o.cpu[i].physical_io
            self.o.cpu[i].physical_io = self.o.cpu_iospace[i]
            if old:
                self.o.cpu_iospace[i].default_target = [old, 0, 0, None]

    def add_objects(self):
        for i in range(self.num_cores):
            aid = iff(self.dualcore, i / 2 + (i % 2) * 512, i)
            self.o.mmu[i] = pre_obj('mmu(x + %d)' % aid, self.mmuclass)
            self.o.cpu[i] = pre_obj('cpu(x + %d)' % aid, self.cpuclass)
            self.o.cpu[i].processor_number = get_next_cpu_number()
            self.o.cpu[i].mmu = self.o.mmu[i]
            self.o.cpu[i].control_registers = [['mid', aid]]
            self.o.cpu[i].freq_mhz = self.freq_mhz
        if self.dualcore:
            for i in range(self.num_cores):
                core = i % 2
                self.o.cpu[i].core_id = core
                self.o.cpu[i].other_cores = [self.o.cpu[i + 1 - 2 * core]]
        
        if self.num_cpus:
            self.component_queue = self.o.cpu[0]

    def add_connector_info(self):
        cpus = [x for x in self.o.cpu if x]
        self.connector_info['chassis'] = [self.board_type,
                                          self.num_cpus, self.freq_mhz,
                                          cpus, self.cpu_megs]
        for i in range(4 + 4 * self.dualcore):
            self.connector_info['cache-cpu%d' % i] = [i, self.o.cpu[i]]

    def connect_serengeti_cpu_board(self, connector, brdid, id,
                                    mem, io, irqbus):
        self.rename_component_objects(str(id))
        self.first_id = id
        for i in range(self.num_cores):
            aid = iff(self.dualcore, i / 2 + (i % 2) * 512, i)
            self.o.cpu[i].control_registers = [['mid', id + aid]]
            self.o.cpu[i].cpu_group = irqbus
            if aid < 4:
                io.map += [[0x40000400000 + ((id + aid) << 23),
                            self.o.mmu[i], 0, 0, 0x48]]
            if self.cpu_spaces:
                self.o.cpu[i].physical_memory.default_target = [mem, 0, 0,None]
                self.o.cpu[i].physical_io.default_target = [io, 0, 0, None]
            else:
                self.o.cpu[i].physical_memory = mem
                self.o.cpu[i].physical_io = io                
                
        node = id / AID_PER_NODE
        board = brdid % BOARDS_PER_NODE
        # clear old MADR (per core)
        for i in range(self.num_cpus):
            for j in range(1, 5):
                exec('self.o.mmu[i].madr_%d = 0' % j)
        # set all memory-banks
        mem_start = (((CPU_BRD_PER_NODE * node) + board) * MB_PER_BOARD
                     * 0x100000)
        for i in range(len(self.cpu_megs)):
            banks = banks_per_cpu[self.cpu_megs[i]]
            if banks == 0:
                continue
            bank_mb = self.cpu_megs[i] / banks
            for j in range(1, banks + 1):
                #print "cpu %d - MADR: %d %dMB (mask = 0x%x) start 0x%x" % (
                #    id + i, j, bank_mb, bank_mask[bank_mb], mem_start)
                madr = ((1 << 63)                     # valid
                        | (bank_mask[bank_mb] << 41)  # mask  (UK)
                        | ((mem_start >> 26) << 20)   # match (UM)
                        | (0xf << 14)                 # mask  (LK) 1-way intrlv
                        | (0x0 << 8))                 # match (LM)
                mem_start += bank_mb * 0x100000
                exec('self.o.mmu[i].madr_%d = madr' % j)

    def connect_timing_model(self, connector, cache):
        id = self.connector_info[connector][0]
        if id >= self.num_cores:
            # ignore
            return
        if not self.cpu_spaces:
            self.add_cpu_spaces()
        self.o.cpu[id].physical_memory.timing_model = cache
        self.o.cpu[id].physical_io.timing_model = cache

    def disconnect_timing_model(self, connector):
        id = self.connector_info[connector][0]
        self.o.cpu[id].physical_memory.timing_model = None
        self.o.cpu[id].physical_io.timing_model = None

class serengeti_us_iii_cpuboard_component(serengeti_cpuboard_component):
    classname = 'serengeti-us-iii-cpu-board'
    basename = 'board'
    description = ('The "serengeti-us-iii-cpu-board" component represents a '
                   'processor board with up to four UltraSPARC III processors '
                   'and 32GB of memory, for use in Sun Fire 3800-6800 '
                   'servers.')
    cpuclass = 'ultrasparc-iii'
    mmuclass = 'cheetah-mmu'
    board_type = 'cpu'
    dualcore = 0

class serengeti_us_iii_plus_cpuboard_component(serengeti_cpuboard_component):
    classname = 'serengeti-us-iii-plus-cpu-board'
    basename = 'board'
    description = ('The "serengeti-us-iii-plus-cpu-board" component '
                   'represents a processor board with up to four UltraSPARC '
                   'III Cu processors and 32GB of memory, for use in Sun '
                   'Fire 3800-6800 servers.')
    cpuclass = 'ultrasparc-iii-plus'
    mmuclass = 'cheetah-plus-mmu'
    board_type = 'cpu'
    dualcore = 0

class serengeti_us_iv_cpuboard_component(serengeti_cpuboard_component):
    classname = 'serengeti-us-iv-cpu-board'
    basename = 'board'
    description = ('The "serengeti-us-iv-cpu-board" component represents a '
                   'processor board with up to four dual-core UltraSPARC IV '
                   'processors and 32GB of memory, for use in Sun Fire '
                   '3800-6800 servers.')
    cpuclass = 'ultrasparc-iv'
    mmuclass = 'jaguar-mmu'
    board_type = 'cpu-v3'
    dualcore = 1

class serengeti_us_iv_plus_cpuboard_component(serengeti_cpuboard_component):
    classname = 'serengeti-us-iv-plus-cpu-board'
    basename = 'board'
    description = ('The "serengeti-us-iv-plus-cpu-board" component represents '
                   'a processor board with up to four dual-core UltraSPARC '
                   'IV+ processors and 32GB of memory, for use in Sun Fire '
                   '3800-6800 servers.')
    cpuclass = 'ultrasparc-iv-plus'
    mmuclass = 'panther-mmu'
    board_type = 'cpu-v3'
    dualcore = 1

for model in ['us_iii', 'us_iii_plus', 'us_iv', 'us_iv_plus']:
    register_component_class(
        eval('serengeti_%s_cpuboard_component' % model),
        [['num_cpus', Sim_Attr_Required, 'i',
          'Number of processors on the board (0 to 4).'],
         ['memory_megs', Sim_Attr_Required, 'i',
          'The amount of RAM in megabytes on the processor board.'],
         ['cpu_frequency', Sim_Attr_Required, 'i',
          'Processor frequency in MHz.']])


### Serengeti PCI Board


class serengeti_pciboard_component(component_object):
    connectors = {
        'chassis' : {'type' : 'serengeti-io-board', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.o.schizo = [None, None]
        self.o.pcibusA = [None, None]
        self.o.pcibusB = [None, None]
        self.o.pcicfgA = [None, None]
        self.o.pcicfgB = [None, None]
        self.o.pciioA = [None, None]
        self.o.pciioB = [None, None]
        self.o.pcimemA = [None, None]
        self.o.pcimemB = [None, None]

    def add_objects(self):
        for i in [0, 1]:
            self.o.pcicfgA[i] = pre_obj('pcicfg(x + %d)A' % i, 'memory-space')
            self.o.pcicfgB[i] = pre_obj('pcicfg(x + %d)B' % i, 'memory-space')
            self.o.pciioA[i] = pre_obj('pciio(x + %d)A' % i, 'memory-space')
            self.o.pciioB[i] = pre_obj('pciio(x + %d)B' % i, 'memory-space')
            self.o.pcimemA[i] = pre_obj('pcimem(x + %d)A' % i, 'memory-space')
            self.o.pcimemB[i] = pre_obj('pcimem(x + %d)B' % i, 'memory-space')
            self.o.pcibusA[i] = pre_obj('pcibus(x + %d)A' % i, 'pci-bus')
            self.o.pcibusB[i] = pre_obj('pcibus(x + %d)B' % i, 'pci-bus')
            self.o.pcibusA[i].conf_space = self.o.pcicfgA[i]
            self.o.pcibusB[i].conf_space = self.o.pcicfgB[i]
            self.o.pcibusA[i].io_space = self.o.pciioA[i]
            self.o.pcibusB[i].io_space = self.o.pciioB[i]
            self.o.pcibusA[i].memory_space = self.o.pcimemA[i]
            self.o.pcibusB[i].memory_space = self.o.pcimemB[i]
            self.o.schizo[i] = pre_obj('schizo(x + %d)' % i,
                                       'serengeti-schizo')
            self.o.schizo[i].pci_busA = self.o.pcibusA[i]
            self.o.schizo[i].pci_busB = self.o.pcibusB[i]
            self.o.pcibusA[i].bridge = self.o.schizo[i]
            self.o.pcibusB[i].bridge = self.o.schizo[i]
            self.o.pcibusA[i].pci_devices = []
            self.o.pcibusB[i].pci_devices = []
        self.o.rom_image = pre_obj('ioprom(x)_image', 'image')
        self.o.rom_image.size = 0x3ae50
        self.o.rom_image.files = [['sgpci.flash', 1, 0, 0x3ae50]]
        self.o.rom = pre_obj('ioprom(x)', 'rom')
        self.o.rom.image = self.o.rom_image
        self.o.sbbc = pre_obj('sbbc(x)', 'sbbc-pci')
        self.o.sbbc.pci_bus = self.o.pcibusB[0]
        self.o.pcibusB[0].pci_devices = [[4, 0, self.o.sbbc]]
        self.o.pcimemB[0].map = [[0x0, self.o.rom, 0, 0, 0x3ae50]]

    def add_connector_info(self):
        self.connector_info['chassis'] = [self.board_type, self.o.sbbc]
        self.add_pci_connector_info()

    def connect_serengeti_io_board(self, connector, brdid, id,
                                   mem, io, irqbus, sc):
        self.rename_component_objects(str(id))
        for i in [0, 1]:
            self.o.schizo[i].memory_space = mem
            self.o.schizo[i].io_space = io
            self.o.schizo[i].irq_bus = irqbus
            self.o.schizo[i].aid = id + i
            self.o.schizo[i].nid = id / AID_PER_NODE
            io.map += [[0x40000000000 + ((id + i) << 23),
                        self.o.schizo[i], 0, 0, 0x800000]]
        self.o.sbbc.sc = sc

    def connect_serengeti_sp_io_board(self, connector, brdid, id,
                                      mem, io, irqbus, sc):
        return self.connect_serengeti_io_board(connector, brdid, id,
                                               mem, io, irqbus, sc)

    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        devs = bus.pci_devices
        for dev in device_list:
            devs += [[slot, dev[0], dev[1]]]
        bus.pci_devices = devs

    def connect_cpci_bus(self, connector, device_list):
        return self.connect_pci_bus(connector, device_list)

class serengeti_pci8_board_component(serengeti_pciboard_component):
    classname = 'serengeti-pci8-board'
    basename = 'board'
    description = ('The "serengeti-pci8-board" component represents an I/O '
                   'board with slots for up to eight PCI cards, for use in '
                   'Sun Fire 4800-6800 servers, i.e. not the SP model.'
                   '<insert id="serengeti-pci8-board-extras"/>')
    board_type = 'pci'
    connectors = serengeti_pciboard_component.connectors.copy()
    for i in range(8):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    def add_pci_connector_info(self):
        self.connector_info['pci-slot0'] = [1, self.o.pcibusB[0]]
        self.connector_info['pci-slot1'] = [2, self.o.pcibusB[0]]
        self.connector_info['pci-slot2'] = [3, self.o.pcibusB[0]]
        self.connector_info['pci-slot3'] = [1, self.o.pcibusA[0]]
        self.connector_info['pci-slot4'] = [1, self.o.pcibusB[1]]
        self.connector_info['pci-slot5'] = [2, self.o.pcibusB[1]]
        self.connector_info['pci-slot6'] = [3, self.o.pcibusB[1]]
        self.connector_info['pci-slot7'] = [1, self.o.pcibusA[1]]

class serengeti_cpci4_board_component(serengeti_pciboard_component):
    classname = 'serengeti-cpci4-board'
    basename = 'board'
    description = ('The "serengeti-cpci4-board" component represents an I/O '
                   'board with slots for up to four CompactPCI cards, for use '
                   'in Sun Fire 4800-6800 servers, i.e. not the SP model.'
                   '<insert id="serengeti-cpci4-board-extras"/>')
    board_type = 'cpci4'
    connectors = serengeti_pciboard_component.connectors.copy()
    for i in range(4):
        connectors['pci-slot%d' % i] = {
            'type' : 'cpci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    def add_pci_connector_info(self):
        self.connector_info['pci-slot0'] = [1, self.o.pcibusB[0]]
        self.connector_info['pci-slot1'] = [1, self.o.pcibusA[0]]
        self.connector_info['pci-slot2'] = [1, self.o.pcibusB[1]]
        self.connector_info['pci-slot3'] = [1, self.o.pcibusA[1]]

class serengeti_cpci6_board_component(serengeti_pciboard_component):
    classname = 'serengeti-cpci6-board'
    basename = 'board'
    description = ('The "serengeti-cpci6-board" component represents an I/O '
                   'board with slots for up to six CompactPCI cards, for use '
                   'in Sun Fire 4800-6800 servers, i.e. not the SP model.'
                   '<insert id="serengeti-cpci6-board-extras"/>')
    board_type = 'cpci6'
    connectors = {
        'chassis' : {'type' : 'serengeti-io-board', 'direction' : 'up',
                     'empty_ok' : False, 'hotplug' : False, 'multi' : False}}
    for i in range(6):
        connectors['pci-slot%d' % i] = {
            'type' : 'cpci-bus', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    def add_pci_connector_info(self):
        self.connector_info['pci-slot0'] = [1, self.o.pcibusB[0]]
        self.connector_info['pci-slot1'] = [2, self.o.pcibusB[0]]
        self.connector_info['pci-slot2'] = [1, self.o.pcibusA[0]]
        self.connector_info['pci-slot3'] = [1, self.o.pcibusB[1]]
        self.connector_info['pci-slot4'] = [2, self.o.pcibusB[1]]
        self.connector_info['pci-slot5'] = [1, self.o.pcibusA[1]]

class serengeti_sp_cpci4_board_component(serengeti_cpci4_board_component):
    classname = 'serengeti-sp-cpci4-board'
    basename = 'board'
    description = ('The "serengeti-sp-cpci4-board" component represents an '
                   'I/O board with slots for up to four CompactPCI cards, for '
                   'use in a Sun Fire 3800 server, i.e. only the SP model.'
                   '<insert id="serengeti-sp-cpci4-board-extras"/>')
    board_type = 'sp-cpci4'
    connectors = serengeti_cpci4_board_component.connectors.copy()
    connectors['chassis'] = {
        'type' : 'serengeti-sp-io-board', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}

class serengeti_sp_cpci6_board_component(serengeti_cpci6_board_component):
    classname = 'serengeti-sp-cpci6-board'
    basename = 'board'
    description = ('The "serengeti-sp-cpci6-board" component represents an '
                   'I/O board with slots for up to six CompactPCI cards, for '
                   'use in a Sun Fire 3800 server, i.e. only the SP model.'
                   '<insert id="serengeti-sp-cpci6-board-extras"/>')
    board_type = 'sp-cpci6'
    connectors = serengeti_cpci6_board_component.connectors.copy()
    connectors['chassis'] = {
        'type' : 'serengeti-sp-io-board', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}

# OBP does not correcly identify cpci6 and sp_cpci4
for model in ['pci8', 'cpci4', 'sp_cpci6']:
    register_component_class(eval('serengeti_%s_board_component' % model), [])


### Sun HME/ISP Compact-PCI Device


class sun_cpci_hme_isp_component(component_object):
    classname = 'sun-cpci-hme-isp'
    basename = 'scsi_eth'
    description = ('The "sun-cpci-hme-isp" component represents an CompactPCI '
                   'card with one HME ethernet controller and one ISP SCSI '
                   'controller for use in Sun systems.')
    connectors = {
        'pci-bus' : {'type' : 'cpci-bus', 'direction' : 'up',
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
        self.o.bridge_p = pre_obj('bridge$_p', 'i21554-prim')
        self.o.bridge_s = pre_obj('bridge$_s', 'i21554-scnd')
        self.o.pcibus = pre_obj('pcibus$', 'pci-bus')
        self.o.bridge_p.scnd_interface = self.o.bridge_s
        # default setup values
        self.o.bridge_p.base_setup = [
            0xfffff000, 0xffff0001, 0xfc000000, 0x00000000,
            0x00000000, 0x80000000, 0xe0000000]
        self.o.bridge_s.pci_bus = self.o.pcibus
        self.o.bridge_s.prim_interface = self.o.bridge_p
        self.o.pcibus.bridge = self.o.bridge_s
        self.o.pcibus.conf_space = self.o.pcicfg
        self.o.pcibus.io_space = self.o.pciio
        self.o.pcibus.memory_space = self.o.pcimem
        self.o.isp = pre_obj('isp$', 'ISP1040')
        self.o.isp.scsi_id = self.scsi_id
        self.o.isp.pci_bus = self.o.pcibus
        self.o.e2bus = pre_obj('e2bus$', 'cheerio-e2bus')
        self.o.e2bus.pci_bus = self.o.pcibus
        self.o.hme = pre_obj('hme$', 'cheerio-hme')
        self.o.hme.mac_address = mac_as_list(self.mac)
        self.o.hme.pci_bus = self.o.pcibus
        self.o.pcibus.pci_devices = [[1, 0, self.o.e2bus],
                                     [1, 1, self.o.hme],
                                     [5, 0, self.o.isp]]
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
        self.connector_info['pci-bus'] = [[[0, self.o.bridge_p]]]
        self.connector_info['ethernet'] = []
        self.connector_info['scsi-bus'] = [self.o.isp, self.scsi_id]

    def instantiation_done(self):
        from sun_components import patch_hme_prom
        component_object.instantiation_done(self)
        patch_hme_prom(self.o.hme_prom_image, self.mac)

    def connect_cpci_bus(self, connector, slot, pci_bus):
        self.o.bridge_p.pci_bus = pci_bus

    def connect_scsi_bus(self, connector, bus):
        self.o.isp.scsi_bus = bus

    def connect_ethernet_link(self, connector, link):
        self.o.hme.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.hme.link = None

register_component_class(
    sun_cpci_hme_isp_component,
    [['mac_address', Sim_Attr_Required, 's',
      'The MAC address of the Ethernet adapter.'],
     ['scsi_id', Sim_Attr_Optional, 'i',
      'The ID on the SCSI bus.']])


### Sun Dual ISP Compact-PCI Device


class sun_cpci_isp_isp_component(component_object):
    classname = 'sun-cpci-isp-isp'
    basename = 'scsi'
    description = ('The "sun-cpci-isp-isp" component represents an CompactPCI '
                   'card with two ISP SCSI controllers for use in Sun '
                   'systems.')
    connectors = {
        'pci-bus'   : {'type' : 'cpci-bus', 'direction' : 'up',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'scsi-bus0' : {'type' : 'scsi-bus', 'direction' : 'down',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'scsi-bus1' : {'type' : 'scsi-bus', 'direction' : 'down',
                       'empty_ok' : False, 'hotplug' : False, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.scsi_id0 = 7
        self.scsi_id1 = 7

    def get_scsi_id0(self, idx):
        return self.scsi_id0

    def set_scsi_id0(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.scsi_id0 = val
        return Sim_Set_Ok

    def get_scsi_id1(self, idx):
        return self.scsi_id1

    def set_scsi_id1(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.scsi_id1 = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.pcicfg = pre_obj('pcicfg$', 'memory-space')
        self.o.pciio = pre_obj('pciio$', 'memory-space')
        self.o.pcimem = pre_obj('pcimem$', 'memory-space')
        self.o.bridge_p = pre_obj('bridge$_p', 'i21554-prim')
        self.o.bridge_s = pre_obj('bridge$_s', 'i21554-scnd')
        self.o.pcibus = pre_obj('pcibus$', 'pci-bus')
        self.o.bridge_p.scnd_interface = self.o.bridge_s
        # default setup values
        self.o.bridge_p.base_setup = [
            0xfffff000, 0xffff0001, 0xfc000000, 0x00000000,
            0x00000000, 0x80000000, 0xe0000000]
        self.o.bridge_s.pci_bus = self.o.pcibus
        self.o.bridge_s.prim_interface = self.o.bridge_p
        self.o.pcibus.bridge = self.o.bridge_s
        self.o.pcibus.conf_space = self.o.pcicfg
        self.o.pcibus.io_space = self.o.pciio
        self.o.pcibus.memory_space = self.o.pcimem
        self.o.isp0 = pre_obj('isp$_0', 'ISP1040')
        self.o.isp0.pci_bus = self.o.pcibus
        self.o.isp0.scsi_id = self.scsi_id0
        self.o.isp1 = pre_obj('isp$_1', 'ISP1040')
        self.o.isp1.pci_bus = self.o.pcibus
        self.o.isp1.scsi_id = self.scsi_id1
        self.o.pcibus.pci_devices = [[5, 0, self.o.isp0],
                                     [6, 0, self.o.isp1]]

        self.o.isp_prom_image = pre_obj('ispprom$_image', 'image')
        self.o.isp_prom_image.size = 0x10000
        self.o.isp_prom_image.files = [['isp1040.fcode', 'ro', 0, 0xaa14]]
        self.o.isp_prom = pre_obj('ispprom$', 'rom')
        self.o.isp_prom.image = self.o.isp_prom_image
        self.o.isp0.expansion_rom = [self.o.isp_prom, 0x10000, 0]
        self.o.isp1.expansion_rom = [self.o.isp_prom, 0x10000, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.bridge_p]]]
        self.connector_info['scsi-bus0'] = [self.o.isp0, self.o.scsi_id0]
        self.connector_info['scsi-bus1'] = [self.o.isp1, self.o.scsi_id1]

    def connect_cpci_bus(self, connector, slot, pci_bus):
        self.o.bridge_p.pci_bus = pci_bus

    def connect_scsi_bus(self, connector, bus):
        if connector == 'scsi-bus0':
            self.o.isp0.scsi_bus = bus
        else:
            self.o.isp1.scsi_bus = bus

register_component_class(
    sun_cpci_isp_isp_component,
    [['scsi_id0', Sim_Attr_Optional, 'i',
      'The ID on the SCSI bus for the first ISP.'],
     ['scsi_id1', Sim_Attr_Optional, 'i',
      'The ID on the SCSI bus for the second ISP.']])


### Sun Dual QLC Compact-PCI Device


class sun_cpci_qlc_qlc_component(component_object):
    classname = 'sun-cpci-qlc-qlc'
    basename = 'board'
    description = ('The "sun-cpci-qlc-qlc" component represents an CompactPCI '
                   'card with two QLC Fibre-Channel SCSI controllers for use '
                   'in Sun systems.')
    connectors = {
        'pci-bus' : {'type' : 'cpci-bus', 'direction' : 'up',
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
        self.o.bridge_p = pre_obj('bridge$_p', 'i21554-prim')
        self.o.bridge_s = pre_obj('bridge$_s', 'i21554-scnd')
        self.o.pcibus = pre_obj('pcibus$', 'pci-bus')
        self.o.bridge_p.scnd_interface = self.o.bridge_s
        # default setup values
        self.o.bridge_p.base_setup = [
            0xfffff000, 0xffff0001, 0xfc000000, 0x00000000,
            0x00000000, 0x80000000, 0xe0000000]
        self.o.bridge_s.pci_bus = self.o.pcibus
        self.o.bridge_s.prim_interface = self.o.bridge_p
        self.o.pcibus.bridge = self.o.bridge_s
        self.o.pcibus.conf_space = self.o.pcicfg
        self.o.pcibus.io_space = self.o.pciio
        self.o.pcibus.memory_space = self.o.pcimem
        self.o.qlc0 = pre_obj('qlc$', 'ISP2200')
        self.o.qlc0.pci_bus = self.o.pcibus
        self.o.qlc0.loop_id = self.loop_id0
        self.o.qlc1 = pre_obj('qlc$', 'ISP2200')
        self.o.qlc1.pci_bus = self.o.pcibus
        self.o.qlc1.loop_id = self.loop_id1
        self.o.pcibus.pci_devices = [[5, 0, self.o.qlc0],
                                     [6, 0, self.o.qlc1]]
        self.o.qlc_prom_image = pre_obj('qlcprom$_image', 'image')
        self.o.qlc_prom_image.size = 0x10000
        self.o.qlc_prom_image.files = [['isp2200.fcode', 'ro', 0, 0x1b2fc]]
        self.o.qlc_prom = pre_obj('qlcprom$', 'rom')
        self.o.qlc_prom.image = self.o.qlc_prom_image
        self.o.qlc0.expansion_rom = [self.o.qlc_prom, 0x10000, 0]
        self.o.qlc1.expansion_rom = [self.o.qlc_prom, 0x10000, 0]

    def add_connector_info(self):
        self.connector_info['pci-bus'] = [[[0, self.o.bridge_p]]]
        self.connector_info['fc-loop0'] = [self.o.qlc0]
        self.connector_info['fc-loop1'] = [self.o.qlc0]

    def connect_cpci_bus(self, connector, slot, pci_bus):
        self.o.bridge_p.pci_bus = pci_bus

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
    sun_cpci_qlc_qlc_component,
    [['loop_id0', Sim_Attr_Required, 'i',
      'The FC loop ID of the first QLC controller.'],
     ['loop_id1', Sim_Attr_Required, 'i',
      'The FC loop ID of the second QLC controller.']])
