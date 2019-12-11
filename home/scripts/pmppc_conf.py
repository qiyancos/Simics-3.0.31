
##  Copyright 2004-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.

from sim_core import *
from cli import *
from configuration import *
import string

# some global variables for the configuration
object_list = {}
global_cpu_freq = {}
total_mem = {}
mac = {}
num_disks = {}
num_cdroms = {}
num_gfx_consoles = {}

machine_list = []
have_sim_object = 0
have_cpu_prom = 0

conf_list = []
machine = ""

if not SIM_get_quiet():
    print
    print "Machines based on pmppc_conf.py are only provided for backward "
    print "compatibility. The new component based machines in simics/targets/"
    print "are recommended instead."
    print

def set_machine(mach):
    global machine, conf_list
    machine = mach
    try:
        conf_list = object_list[machine]
    except:
        pass


def configuration_loaded(func):
    if SIM_initial_configuration_ok() != 0:
        print "The function '%s' cannot be used once a configuration is loaded" % func
        SIM_command_has_problem()
        return 1
    else:
        return 0    

def create_pmppc_board(ppc_model, cpu_freq, tb_freq, eth0_mac = [0x00, 0x80, 0xf9, 0x52, 0x0c, 0x18], use_mmap_memory=0):
    global conf_list, global_cpu_freq, total_mem, machine_list
    global have_sim_object, have_cpu_prom, num_disks, num_cdroms
    if configuration_loaded("set_global_config"):
        return

    machine_list += [machine]
    global_cpu_freq[machine] = cpu_freq

    # The CPU
    object_list[machine] = ([OBJECT(machine + "cpu0", ppc_model,
                                    processor_number = get_next_cpu_number(),
                                    queue = OBJ(machine + "cpu0"),
                                    freq_mhz = global_cpu_freq[machine],
                                    physical_memory = OBJ(machine + "phys_mem0"),                                    
                                    timebase_freq_mhz = tb_freq)])

    # Default physical memory mapping
    phys_map = [[0x00000000L, OBJ(machine + "memory0"),            0,          0L, 0x10000000],
                [0x70000000L, OBJ(machine + "flash0"),             0,          0L,  0xfe00000],                
                [0x7fe00000L, OBJ(machine + "eth0"),               0,          0L,   0x100000],
                [0x7ff00000L, OBJ(machine + "rtc0"),               0,          0L,     0x2000],
                [0x7ff40000L, OBJ(machine + "pm-ppc"),             0, 0x7ff40000L,    0x40000],
                [0x7ff80000L, OBJ(machine + "memory0"),            0, 0x7ff80000L,    0x80000],
                [0x80000000L, OBJ(machine + "pci-bus0-memory"),    0, 0x80000000L, 0x78000000],
                [0xf8000000L, OBJ(machine + "pci-bridge0"),       11,          0L,    0x10000],
                [0xf8800000L, OBJ(machine + "pci-bridge0"),       11,   0x800000L,  0x3800000],
                [0xfec00000L, OBJ(machine + "pci-bridge0"),       10, 0xfec00000L,          8],
                [0xff400000L, OBJ(machine + "pci-bridge0"),       10, 0xff400000L,   0x100000],                
                [0xff500000L, OBJ(machine + "pi0"),                0, 0xff500000L,          8],
                [0xff500008L, OBJ(machine + "mc0"),                0, 0xff500008L,          8],
                [0xff500880L, OBJ(machine + "uic0"),               0,          0,       0x24],
                [0xff600300L, OBJ(machine + "uart0"),              0,        0x0,         0x1],
                [0xff600301L, OBJ(machine + "uart0"),              0,        0x1,         0x1],
                [0xff600302L, OBJ(machine + "uart0"),              0,        0x2,         0x1],
                [0xff600303L, OBJ(machine + "uart0"),              0,        0x3,         0x1],
                [0xff600304L, OBJ(machine + "uart0"),              0,        0x4,         0x1],
                [0xff600305L, OBJ(machine + "uart0"),              0,        0x5,         0x1],
                [0xff600306L, OBJ(machine + "uart0"),              0,        0x6,         0x1],
                [0xff600307L, OBJ(machine + "uart0"),              0,        0x7,         0x1],
                [0xff600400L, OBJ(machine + "uart1"),              0,        0x0,         0x1],
                [0xff600401L, OBJ(machine + "uart1"),              0,        0x1,         0x1],
                [0xff600402L, OBJ(machine + "uart1"),              0,        0x2,         0x1],
                [0xff600403L, OBJ(machine + "uart1"),              0,        0x3,         0x1],
                [0xff600404L, OBJ(machine + "uart1"),              0,        0x4,         0x1],
                [0xff600405L, OBJ(machine + "uart1"),              0,        0x5,         0x1],
                [0xff600406L, OBJ(machine + "uart1"),              0,        0x6,         0x1],
                [0xff600407L, OBJ(machine + "uart1"),              0,        0x7,         0x1],
                [0xff620000L, OBJ(machine + "iic0"),               0,        0x0,         0x2],
                [0xff620002L, OBJ(machine + "iic0"),               0,        0x2,         0x2],
                [0xff620004L, OBJ(machine + "iic0"),               0,        0x4,         0x1],
                [0xff620005L, OBJ(machine + "iic0"),               0,        0x5,         0x1],
                [0xff620006L, OBJ(machine + "iic0"),               0,        0x6,         0x1],
                [0xff620007L, OBJ(machine + "iic0"),               0,        0x7,         0x1],
                [0xff620008L, OBJ(machine + "iic0"),               0,        0x8,         0x1],
                [0xff620009L, OBJ(machine + "iic0"),               0,        0x9,         0x1],
                [0xff62000aL, OBJ(machine + "iic0"),               0,        0xa,         0x1],
                [0xff62000bL, OBJ(machine + "iic0"),               0,        0xb,         0x1],
                [0xff62000cL, OBJ(machine + "iic0"),               0,        0xc,         0x1],
                [0xff62000dL, OBJ(machine + "iic0"),               0,        0xd,         0x1],
                [0xff62000eL, OBJ(machine + "iic0"),               0,        0xe,         0x1],
                [0xff62000fL, OBJ(machine + "iic0"),               0,        0xf,         0x1],
                [0xff620010L, OBJ(machine + "iic0"),               0,        0x10,        0x1],
                [0xff630000L, OBJ(machine + "iic1"),               0,        0x0,         0x2],
                [0xff630002L, OBJ(machine + "iic1"),               0,        0x2,         0x2],
                [0xff630004L, OBJ(machine + "iic1"),               0,        0x4,         0x1],
                [0xff630005L, OBJ(machine + "iic1"),               0,        0x5,         0x1],
                [0xff630006L, OBJ(machine + "iic1"),               0,        0x6,         0x1],
                [0xff630007L, OBJ(machine + "iic1"),               0,        0x7,         0x1],
                [0xff630008L, OBJ(machine + "iic1"),               0,        0x8,         0x1],
                [0xff630009L, OBJ(machine + "iic1"),               0,        0x9,         0x1],
                [0xff63000aL, OBJ(machine + "iic1"),               0,        0xa,         0x1],
                [0xff63000bL, OBJ(machine + "iic1"),               0,        0xb,         0x1],
                [0xff63000cL, OBJ(machine + "iic1"),               0,        0xc,         0x1],
                [0xff63000dL, OBJ(machine + "iic1"),               0,        0xd,         0x1],
                [0xff63000eL, OBJ(machine + "iic1"),               0,        0xe,         0x1],
                [0xff63000fL, OBJ(machine + "iic1"),               0,        0xf,         0x1],
                [0xff630010L, OBJ(machine + "iic1"),               0,        0x10,        0x1],
                [0xff650000L, OBJ(machine + "gpt0"),               0,          0,       0x100],
                [0xff660000L, OBJ(machine + "hfs0"),               0,          0,        0x10],
                [0xffe00000L, OBJ(machine + "memory0"),            0,0xffe00000L,    0x200000]]                                
    
    # The physical memory space
    object_list[machine] += ([OBJECT(machine + "phys_mem0", "memory-space", map = phys_map)])


    object_list[machine] += ([OBJECT(machine + "memory0", "ram",
                                     image = OBJ(machine + "memory0-image"))] +
                             [OBJECT(machine + "memory0-image", "image",
                                     queue   = OBJ(machine + "cpu0"),
                                     size    = 0x100000000L)] +
                             [OBJECT(machine + "uic0", "cpc700-uic",
                                     irq_dev = OBJ(machine + "cpu0"),
                                     queue   = OBJ(machine + "cpu0"))] +
                             [OBJECT(machine + "uart0", "NS16550",
                                     recorder = OBJ(machine + "rec0"),
                                     irq_dev = OBJ(machine + "uic0"),
                                     irq_level = 28,
                                     console = OBJ(machine + "con0"),
                                     queue   = OBJ(machine + "cpu0"))] +
                             [OBJECT(machine + "uart1", "NS16550",
                                     recorder = OBJ(machine + "rec0"),
                                     irq_dev = OBJ(machine + "uic0"),
                                     irq_level = 27,
                                     queue   = OBJ(machine + "cpu0"))] +
                             [OBJECT(machine + "mc0", "cpc700-mc")] +
                             [OBJECT(machine + "pi0", "cpc700-pi")] +
                             [OBJECT(machine + "iic0", "cpc700-iic",
                                     i2c_bus = OBJ(machine + "i2c-bus0"))] +                             
                             [OBJECT(machine + "iic1", "cpc700-iic",
                                     i2c_bus = OBJ(machine + "i2c-bus1"))] +                             
                             [OBJECT(machine + "i2c-bus0", "i2c-bus")] +
                             [OBJECT(machine + "i2c-bus1", "i2c-bus")] +
                             [OBJECT(machine + "con0", "text-console",
                                     title = machine + " System Console, Serial A",
                                     queue = OBJ(machine + "cpu0"),
                                     bg_color = "black",
                                     fg_color = "green",
                                     output_timeout =  120,
                                     device = OBJ(machine + "uart0"))] +
                             [OBJECT(machine + "pm-ppc", "artesyn-pm-ppc",
                                     board_config_reg0= 0xa1,
                                     board_config_reg1= 0x66,
                                     led_board_id_reg = 0x10,
                                     queue = OBJ(machine + "cpu0"),                                     
                                     irq_dev = OBJ(machine + "uic0"),
                                     irq_base_level = 11)] +
                             [OBJECT(machine + "rtc0", "DS17485",
                                     irq_dev = OBJ(machine + "uic0"),
                                     irq_level = 6,
                                     queue = OBJ(machine + "cpu0"))]+
                             [OBJECT(machine + "eeprom", "AT24C164",
                                     i2c_bus = OBJ(machine + "i2c-bus0"),
                                     a210 = 3,
                                     memory = DATA(0x800, "eeprom.raw", 0x200)
                                     )] +
                             [OBJECT(machine + "eth0", "CS8900A",
                                     recorder = OBJ(machine + "rec0"),
                                     mac_address = eth0_mac,
                                     irq_dev = OBJ(machine + "uic0"),
                                     irq_level = 7,
                                     queue = OBJ(machine + "cpu0"))]+
                             [OBJECT(machine + "pci-bridge0", "cpc700-pci",
                                     pci_bus = OBJ(machine + "pci-bus0"),
                                     memory = OBJ(machine + "phys_mem0"),
                                     # This are needed since normally the PROM initilize the pci-bridge
                                     config_registers= [0xf91014, 0x2000006, 0x6000001, 0x700, 0, 0,
                                                        0x8000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                        0, 0, 0, 0, 0, 0, 0, 0, 0],
                                     pmm0la= 0x80000000,
                                     pmm0ma= 0xc0000001,
                                     pmm0pcila= 0x80000000,
                                     pmm0pciha= 0,
                                     pmm1la= 0,
                                     pmm1ma= 0xfffff000,
                                     pmm1pcila= 0,
                                     pmm1pciha= 0,
                                     pmm2la= 0,
                                     pmm2ma= 0xfffff000,
                                     pmm2pcila= 0,
                                     pmm2pciha= 0,
                                     ptm1ms= 0xf8000001,
                                     ptm1la= 0,
                                     ptm2ms= 0xfffff001,
                                     ptm2la= 0x7ff40000,
                                     pcicfgadr= 0x80000048)]+
                             [OBJECT(machine + "pci-bus0", "pci-bus",
                                     bridge = OBJ(machine + "pci-bridge0"),
                                     memory_space = OBJ(machine + "pci-bus0-memory"),
                                     io_space = OBJ(machine + "pci-bus0-io"),
                                     conf_space = OBJ(machine + "pci-bus0-conf"),
                                     interrupt = OBJ(machine + "pm-ppc"),
                                     pci_devices = [[0,0,OBJ(machine + "pci-bridge0")],
                                                    [6,0,OBJ(machine + "scsi-ctrl0")]])]+
                             [OBJECT(machine + "pci-bus1", "pci-bus",
                                     bridge = OBJ(machine + "pci-to-pci0"),
                                     memory_space = OBJ(machine + "pci-bus1-memory"),
                                     io_space = OBJ(machine + "pci-bus1-io"),
                                     conf_space = OBJ(machine + "pci-bus1-conf"),
                                     interrupt = OBJ(machine + "pci-to-pci0"))]+
                             [OBJECT(machine + "pci-to-pci0", "i21152",
                                     pci_bus = OBJ(machine + "pci-bus0"),
                                     secondary_bus = OBJ(machine + "pci-bus1"))]+
                             [OBJECT(machine + "pci-bus0-memory", "memory-space")]+
                             [OBJECT(machine + "pci-bus1-memory", "memory-space")]+
                             [OBJECT(machine + "pci-bus0-io", "memory-space")]+
                             [OBJECT(machine + "pci-bus1-io", "memory-space")]+
                             [OBJECT(machine + "pci-bus0-conf", "memory-space")]+
                             [OBJECT(machine + "pci-bus1-conf", "memory-space")]+                             
                             [OBJECT(machine + "rec0", "recorder")]+
                             [OBJECT(machine + "gpt0", "cpc700-gpt",
                                     queue = OBJ(machine + "cpu0"),
                                     irq_dev = OBJ(machine + "uic0"),
                                     irq_base_level = 24)]+
                             [OBJECT(machine + "flash0", "strata-flash",
                                     device_count = 1)]+
                             [OBJECT(machine + "hfs0", "hostfs")]+
                             [OBJECT(machine + "scsi_ctrl0", "SYM53C810",
                                     queue = OBJ(machine + "cpu0"),
                                     pci_bus = OBJ(machine + "pci-bus0"),
                                     scsi_bus = OBJ(machine + "scsi_bus0"))]+
                             [OBJECT(machine + "scsi_bus0", "scsi-bus",
                                     queue = OBJ(machine + "cpu0"),
                                     targets = [[0, OBJ(machine + "sda"), 0],
                                                [1, OBJ(machine + "sdb"), 0],
                                                [3, OBJ(machine + "cdrom0"), 0],
                                                [7, OBJ(machine + "scsi_ctrl0"), 0]])]+
                             [OBJECT(machine + "sda", "scsi-disk",
                                     queue = OBJ(machine + "cpu0"),
                                     image = OBJ(machine + "sda_image"),
                                     scsi_bus = OBJ(machine + "scsi_bus0"),
                                     scsi_target = 0,
                                     geometry = [ 2735, 19, 80])]+
                             [OBJECT(machine + "sda_image", "image", 
                                     queue = OBJ(machine + "cpu0"),
                                     size = 2128486400, # 2735*19*80*512
                                     files = [["orange1.craff", "ro", 0, 2128486400]])]+
                             [OBJECT(machine + "sdb", "scsi-disk",
                                     queue = OBJ(machine + "cpu0"),
                                     image = OBJ(machine + "sdb_image"),
                                     scsi_bus = OBJ(machine + "scsi_bus0"),
                                     scsi_target = 1,
                                     geometry = [ 2735, 19, 80])]+
                             [OBJECT(machine + "sdb_image", "image", 
                                     queue = OBJ(machine + "cpu0"),
                                     size = 2128486400  # 2735*19*80*512
                                     )]+
                             [OBJECT(machine + "cdrom0", "scsi-cdrom",
                                     queue = OBJ(machine + "cpu0"),
                                     scsi_bus = OBJ(machine + "scsi_bus0"),
                                     scsi_target = 3)])

    if use_mmap_memory:
        set_attribute(object_list[machine], machine + "memory0-image", "mapfile_dir", "/tmp")
        set_attribute(object_list[machine], machine + "cpu0", "turbo_mmap_memory", 1)

    conf_list = object_list[machine]


def get_configuration():
    global machine
    all_objs = []
    
    for mach in machine_list:
        all_objs += object_list[mach]
    return all_objs


def post_configuration():
    global machine
