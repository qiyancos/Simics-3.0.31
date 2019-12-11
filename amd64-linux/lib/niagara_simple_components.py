# MODULE: niagara-simple-components
# CLASS: niagara-simple-system

import os, time

from sim_core import *
from components import *
from fiesta_nvram import register_nvram_commands, write_idprom_to_nvram

STRANDS = 4
CORES   = 8
MAXCPUS = STRANDS * CORES

md_files = {1 : '1up-md.bin',
            2 : '1g2p-md.bin',
            32: '1g32p-md.bin'}

hv_files = {1 : '1up-hv.bin',
            2 : '1g2p-hv.bin',
            32: '1g32p-hv.bin'}

def file_size(f):
    return os.stat(SIM_lookup_file(f))[6]

class niagara_simple_component(component_object):
    classname = 'niagara-simple-system'
    basename = 'system'
    description = ('The "niagara-simple-system" component represents a fake '
                   'Sun Fire T2000 server with an UltraSPARC T1 processor '
                   'memory and a single disk image, but with no other '
                   'devices.It is currently not possible to change the '
                   'configuration, except for the number of processors.')

    connectors = {
        'com1'        : {'type' : 'serial', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False},
        'com2'        : {'type' : 'serial', 'direction' : 'down',
                         'empty_ok' : True, 'hotplug' : True, 'multi' : False}
        }

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.resetprom = ('reset.bin', 768)
        self.qprom = ('q.bin', 163216)
        self.openprom = ('openboot.bin', 349708)
        self.megs = 256
        self.num_cores = CORES
        self.strands_per_core = STRANDS
        self.o.cpu = [None] * MAXCPUS
        self.o.mmu = [None] * MAXCPUS
        self.o.cmmu = [None] * CORES

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def get_rtc_time(self, idx):
        return self.tod

    def set_rtc_time(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        try:
            time_tuple = time.strptime(val, '%Y-%m-%d %H:%M:%S %Z')
        except Exception, msg:
            SIM_attribute_error(str(msg))
            return Sim_Set_Illegal_Value
        self.tod = val
        return Sim_Set_Ok

    def get_num_cores(self, idx):
        return self.num_cores

    def set_num_cores(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.num_cores = val
        if val not in (1, 2, 8):
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_strands_per_core(self, idx):
        return self.strands_per_core

    def set_strands_per_core(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if val not in (1, 4):
            return Sim_Set_Illegal_Value
        self.strands_per_core = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.irqbus = pre_obj('irqbus', 'sparc-irq-bus')
        self.o.cpu_mem = pre_obj('cpu_mem', 'memory-space')
        self.o.phys_mem = pre_obj('phys_mem', 'memory-space')
        self.o.simicsfs = pre_obj('simicsfs', 'hostfs')
        for i in range(self.num_cores * STRANDS):
            c = i / STRANDS
            t = i % STRANDS
            if t == 0:
                self.o.cmmu[c] = pre_obj('cmmu%d' % c, 'niagara-core-mmu')
            self.o.cpu[i] = pre_obj('cpu%d_%d' % (c, t), "ultrasparc-t1")
            self.o.mmu[i] = pre_obj('mmu%d_%d' % (c, t), "niagara-strand-mmu")
            self.o.cpu[i].control_registers = [["mid", i],
                                               ["strand_status", 1]]
            self.o.cpu[i].processor_number = get_next_cpu_number()
            self.o.cpu[i].strand_id = t
            self.o.cpu[i].cpu_group = self.o.irqbus
            self.o.cpu[i].freq_mhz = self.freq_mhz
            self.o.cpu[i].mmu = self.o.mmu[i]
            self.o.cpu[i].physical_memory = self.o.cpu_mem
            self.o.cpu[i].simicsfs = self.o.simicsfs
            #
            self.o.mmu[i].cmmu = self.o.cmmu[c]
            self.o.mmu[i].cpu = self.o.cpu[i]
            self.o.mmu[i].queue = self.o.cpu[i]
        #
        for i in range(self.num_cores * STRANDS):
            first = i & ~(STRANDS - 1)
            last = first + STRANDS
            self.o.cpu[i].other_strands = ([x for x in self.o.cpu[first:last]
                                            if x !=  self.o.cpu[i]])
        #
        self.o.com2 = pre_obj('com2', 'NS16550')
        self.o.com2.xmit_time = 5
        self.o.com2.target_pace_receive = 1
        self.o.dram_ctl = pre_obj('dram_ctl', 'niagara-dram-ctl')
        self.o.iob = pre_obj('iob', 'niagara-iob')
        self.o.iob.vcores = self.o.cpu
        self.o.l2c = pre_obj('l2c', 'niagara-l2c')
        self.o.prom_image = pre_obj('prom_image', 'image')
        self.o.prom_image.size = 0x100000
        self.o.prom_image.files = [
            [self.resetprom[0], "ro",       0, self.resetprom[1]],
            [self.qprom[0],     "ro", 0x10000, self.qprom[1]],
            [self.openprom[0],  "ro", 0x80000, self.openprom[1]]]
        self.o.prom = pre_obj('prom', 'rom')
        self.o.prom.image = self.o.prom_image
        self.o.rtc = pre_obj('rtc', 'sun4v-rtc')
        time_tuple = time.strptime(self.tod, '%Y-%m-%d %H:%M:%S %Z')
        self.o.rtc.start_time = int(time.mktime(time_tuple))
        #
        self.o.cpu_mem.map = [
            [0x00000000000, self.o.phys_mem, 0, 0x00000000000, 0x02000000000],
           # 0x08000000000 - 0x08010000000 JBI internal CSRs
            [0x0800e000000, self.o.phys_mem, 0, 0x4000e000000, 0x00002000000],
            [0x08010000000, self.o.phys_mem, 0, 0x00000000000, 0x000f0000000],
            [0x09700000000, self.o.dram_ctl, 0,             0, 0x00000004000],
            [0x09800000000, self.o.iob,      0,             0, 0x00100000000],
            [0x0a000000000, self.o.l2c,      0,             0, 0x01f00000000],
            [0x0c000000000, self.o.phys_mem, 0, 0x7c000000000, 0x03f00000000],
           # 0x0ff00000000 - 0x0fff0000000 SSI Internal regs
            [0x0fff0000000, self.o.prom,     0, 0x00000000000, 0x00000100000],
            [0x0fff0c1fff8, self.o.rtc,      0, 0,          8],
            [0x0fff0c2c000, self.o.com2,     1, 0,          8, None, 0, 1]]
        #
        self.o.com1 = pre_obj('com1', 'NS16550')
        self.o.com1.xmit_time = 5
        self.o.com1.target_pace_receive = 1
        self.o.disk_image = pre_obj('disk_image', 'image')
        self.o.disk_image.size = 0x20100000
        self.o.disk = pre_obj('disk', 'ram')
        self.o.disk.image = self.o.disk_image
        self.o.hv_image = pre_obj('hv_image', 'image')
        self.o.hv_image.size = 0x4000
        idx = self.num_cores * self.strands_per_core
        self.o.hv_image.files = [[hv_files[idx], "ro", 0,
                                  file_size(hv_files[idx])]]
        self.o.hv = pre_obj('hv', 'ram')
        self.o.hv.image = self.o.hv_image
        self.o.md_image = pre_obj('md_image', 'image')
        self.o.md_image.size = 0x4000
        self.o.md_image.files = [[md_files[idx], "ro", 0,
                                  file_size(md_files[idx])]]
        self.o.md = pre_obj('md', 'ram')
        self.o.md.image = self.o.md_image
        self.o.hv_memory_image = pre_obj('hv_memory_image', 'image')
        self.o.hv_memory_image.size = 0x4000000
        self.o.hv_memory = pre_obj('hv_memory', 'ram')
        self.o.hv_memory.image = self.o.hv_memory_image
        self.o.nvram_image = pre_obj('nvram_image', 'image')
        self.o.nvram_image.size = 0x4000
        self.o.nvram = pre_obj('nvram', 'ram')
        self.o.nvram.image = self.o.nvram_image
        self.o.memory_image = pre_obj('memory_image', 'image')
        self.o.memory_image.size = self.megs * 0x100000
        self.o.memory = pre_obj('memory', 'ram')
        self.o.memory.image = self.o.memory_image
        #
        self.o.phys_mem.map = [
            [0x00000000000, self.o.hv_memory, 0, 0,  0x4000000],
            [0x00080000000, self.o.memory,    0, 0, self.megs * 0x100000],
            [0x01f10000000, self.o.com1,      1, 0,          8, None, 0, 1],
            [0x01f11000000, self.o.nvram,     0, 0,     0x4000],
            [0x01f12000000, self.o.md,        0, 0,     0x4000],
            [0x01f12080000, self.o.hv,        0, 0,     0x4000],
            [0x01f40000000, self.o.disk,      0, 0, 0x20100000]]

    def add_connector_info(self):
        self.connector_info['com1'] = [None, self.o.com1, 'com1']
        self.connector_info['com2'] = [None, self.o.com1, 'com2']

    def connect_serial(self, connector, link, console):
        if link:
            exec('self.o.%s.link = link' % connector)
        else:
            exec('self.o.%s.console = console' % connector)

    def disconnect_serial(self, connector):
        exec('self.o.%s.link = None' % connector)
        exec('self.o.%s.console = None' % connector)

    def get_clock(self):
        return self.o.cpu[0]

    def get_processors(self):
        return [x for x in self.o.cpu if x]

    def instantiation_done(self):
        component_object.instantiation_done(self)
        self.o.nvram_image.iface.image.set_persistent(self.o.nvram_image)
        # TODO: write_idprom_to_nvram(self.obj, self.hostid, self.mac)

register_component_class(
    niagara_simple_component,
    [['cpu_frequency', Sim_Attr_Required, 'i',
      'Processor frequency in MHz.'],
     ['num_cores', Sim_Attr_Required, 'i',
      'Number of processor cores in the system. 1 or 8.'],
     ['strands_per_core', Sim_Attr_Required, 'i',
      'Number of active processor strands per core in the system. '
      '1, 2 or 4. There are always 4 strands created.'],
     ['rtc_time', Sim_Attr_Required, 's',
      'The date and time of the Real-Time clock.']],
    top_level = True)


register_nvram_commands(niagara_simple_component.classname, 0x0d7b17d7, False)
