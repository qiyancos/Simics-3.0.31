
##  Copyright 2003-2007 Virtutech AB
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
import time, re

#constants (per cpu)
num_dimms = 4

mem_sizes = {
    # mem-size, banks, rows, column-bits
     256: [2, 1, 12],
     512: [2, 1, 13],
    1024: [2, 2, 13],
    2048: [2, 2, 14],
    4096: [2, 2, 15],
    8192: [4, 2, 15],
   16384: [8, 2, 15] # Enchilada only with 2 cpus
}

max_cpus         = { "Taco" :    1, "Enchilada" :     2}
num_tomatillos   = { "Taco" :    1, "Enchilada" :     2}
num_pci_slots    = { "Taco" :    6, "Enchilada" :     8}
adm_i2c_addr     = { "Taco" : 0x2e, "Enchilada" :  0x2c}
seeprom_i2c_addr = { "Taco" : 0x54, "Enchilada" :  0x51}
dram_i2c_addr    = { "Taco" : 0x50, "Enchilada" :  0x5b}

max_mem = [0, 8192, 16384] # index with number of cpus 

obp_files      = { "Taco"      : [["openbootprom.ta", "ro", 0, 0x100000]],
                   "Enchilada" : [["openboot_enchilada.bin", "ro",0, 463192]]}
fru_files      = { "Taco"      : [["885-0086-10.bin", "ro", 0, 0x2000]],
                   "Enchilada" : [["885-0143-09.bin", "ro", 0, 0x2000]]}

# some global variables for the configuration
object_list = {}
global_cpu_freq = {}
global_time = {}
total_mem = {}
cpu_list = {}
host_id = {}
mac = {}
num_disks = {}
num_cdroms = {}
num_processors = {}
num_gfx_consoles = {}
num_slots = {}

machine_list = []
have_sim_object = 0
have_pgx64_prom = 0
cassini_proms = []

conf_list = []
machine = ""

if not SIM_get_quiet():
    print
    print "Machines based on fiesta_conf.py are only provided for backward "
    print "compatibility. The new component based machines in simics/targets/"
    print "are recommended instead."
    print

def handle_error(msg):
    print
    print "Fiesta configuration error:"
    print
    print msg
    print
    SIM_command_has_problem()
    if VT_remote_control():
        VT_send_control_msg(['startup-failure', 0, str(msg)])

def configuration_loaded(func):
    if SIM_initial_configuration_ok() != 0:
        print "The function '%s' cannot be used once a configuration is loaded" % func
        SIM_command_has_problem()
        return 1
    else:
        return 0    

def mac_string_to_list(mac_address):
    ether = []
    eth = string.split(mac_address, ":")
    for i in range(0, len(eth)):
        ether.append(int(eth[i], 16))
    return ether

def set_machine(mach):
    global machine, conf_list
    machine = mach
    try:
        conf_list = object_list[machine]
    except:
        pass

def set_global_config(system, hostid, cpu_freq, mac_address, tod, num_cpus, mb, obp_file = None, fru_file = None):
    global conf_list, global_time, mac, host_id, global_cpu_freq, total_mem, machine_list
    global have_sim_object, num_disks, num_cdroms, fru_files
    if configuration_loaded("set_global_config"):
        return

    machine_list += [machine]
    global_cpu_freq[machine] = cpu_freq
    global_time[machine] = tod
    host_id[machine] = hostid
    cpu_list[machine] = []
    mac[machine] = mac_string_to_list(mac_address)
    num_disks[machine] = 0
    num_cdroms[machine] = 0
    num_gfx_consoles[machine] = 0
    num_processors[machine] = num_cpus
    
    if not system in max_cpus:
        handle_error("No Fiesta system with the name '%s' supported." % system)

    if system == "Enchilada":
        print "WARNING: The Enchilada architecture is not supported."

    if mb > max_mem[num_cpus]:
        handle_error("Unsupported memory size.")
    
    num_slots[machine] = num_pci_slots[system]

    if not obp_file:
        obp_file = obp_files[system]

    if not fru_file:
        fru_file = fru_files[system]

    if num_cpus > max_cpus[system]:
        handle_error("Illegal number of cpus (%d). "
                     + "The %s system only supports %d cpus."
                     % (num_cpus, system, max_cpus[system]))

    try:
        mem = mem_sizes[mb]
    except:
        mems = mem_sizes.keys()
        mems.sort()
        return handle_error("Illegal memory size. Allowed sizes are: " + `mems`)

    total_mem[machine] = mb * 1024 * 1024
    mem_map = []
    mem_maps = mem[0] * mem[1] / 2
    map_size = total_mem[machine] / mem_maps
    for i in range(0, mem_maps):
        mem_map += [[0x100000000 * i, OBJ(machine + "memory" + `i`), 0, map_size * i, map_size]]

    # one cpu, one tomatillo
    presence = 0x21L     # port 5, 0
    if num_cpus == 2:
        presence |= 0x02 # port 1 (only a guess)
    if num_tomatillos[system] == 2:
        presence |= 0x40 # port 6 (only a guess)

    for i in range(0, num_cpus):
        cpu_list[machine].append(i)
    object_list[machine] = ([OBJECT(machine + "phys_mem0", "memory-space",
                                    map = mem_map)] + 
                            [OBJECT(machine + "phys_io0", "memory-space",
                                    map = [])] +
                            [OBJECT(machine + "memory" + `i`, "ram",
                                    image = OBJ(machine + "memory_image"))
                             for i in range(0, mem_maps)] +
                            [OBJECT(machine + "memory_image", "image",
                                    size = total_mem[machine],
                                    queue = "<queue>")] +
                            [OBJECT(machine + "rec0", "recorder")] +
                            [OBJECT(machine + "irqbus0", "sparc-irq-bus")] +
                            [OBJECT(machine + "cpu" + `i`, "ultrasparc-iii-i",
                                    queue = OBJ(machine + "cpu" + `i`),
                                    control_registers = [["mid", i],
                                                         ["safari_config", ((presence << 51)
                                                                            | (presence << 44)
                                                                            | (i << 17))],
                                                         ["ver", 0x3e001655000000L]],
                                    cpu_group = OBJ(machine + "irqbus0"),
                                    freq_mhz = global_cpu_freq[machine],
                                    system_tick_frequency = 12.0,
                                    processor_number = get_next_cpu_number(),
                                    mmu = OBJ(machine + "jpmmu" + `i`),
                                    physical_io = OBJ(machine + "phys_io0"),
                                    physical_memory = OBJ(machine + "phys_mem0"))
                             for i in range(0, num_cpus)] +
                            [OBJECT(machine + "jpmmu" + `i`, "jalapeno-mmu")
                             for i in range(0, num_cpus)])
    mem = get_attribute(object_list[machine], machine + "phys_io0", "map")
    for i in range(0, num_cpus):
        mem += [[0x40000000000 + (i << 23), OBJ(machine + "jpmmu" + `i`), 0x0, 0, 0x800000]]
    set_attribute(object_list[machine], machine + "phys_io0", "map", mem)

    add_tomatillo(30, system, num_cpus, fru_file)
    if num_tomatillos[system] == 2:
        add_tomatillo(28, system, num_cpus, fru_file)
    elif num_tomatillos[system] > 2:
        handle_error("Unsupported number of Tomatillos: %d" % num_tomatillos[system])
    
    conf_list = object_list[machine]
    if have_sim_object == 0:
        have_sim_object = 1
        object_list[machine] += [OBJECT("sim", "sim", handle__outside__memory = 1)]
    object_list[machine] += ([OBJECT(machine + "fiesta_cpuprom", "flash-memory",
                                     queue = "<queue>",
                                     cfi_compatible = 0,
                                     intel_compatible = 0,
                                     jedec_compatible = 0,
                                     amd_compatible = 1,
                                     interleave =  1,
                                     bus_width =  1,
                                     vendor_id =  0x1,
                                     device_id =  0xd5,
                                     sectors   =  16,
                                     sector_size = 0x10000,
                                     storage_ram =  OBJ(machine + "flash-ram"))] +
                             [OBJECT(machine + "flash-ram", "ram",
                                     image = OBJ(machine + "fiesta_cpuprom_image"))] +
                             [OBJECT(machine + "fiesta_cpuprom_image", "image",
                                     size = 0x100000,
                                     files = obp_file,
                                     queue = "<queue>")])
def add_tomatillo(id, system, num_cpus, fru_file):
    object_list[machine] += ([OBJECT(machine + "tomatillo" + `id`, "fiesta-tomatillo",
                                     memory__space = OBJ(machine + "phys_mem0"),
                                     io__space = OBJ(machine + "phys_io0"),
                                     irq_bus = OBJ(machine + "irqbus0"),
                                     jpid = id,
                                     i2c_bus = OBJ(machine + "gpio-i2c-bus" + `id`),
                                     pci_busA = OBJ(machine + "pcibus" + `id` + "A"),
                                     pci_busB = OBJ(machine + "pcibus" + `id` + "B"),
                                     queue = "<queue>")] +
                             [OBJECT(machine + "gpio-i2c-bus" + `id`, "i2c-bus")] +
                             [OBJECT(machine + "pcibus" + `id` + "A", "pci-bus",
                                     bridge = OBJ(machine + "tomatillo" + `id`),
                                     memory_space = OBJ(machine + "bus-pcimem" + `id` + "A"),
                                     conf_space = OBJ(machine + "bus-pcicfg" + `id` + "A"),
                                     io_space = OBJ(machine + "bus-pciio" + `id` + "A"))] +
                             [OBJECT(machine + "pcibus" + `id` + "B", "pci-bus",
                                     bridge = OBJ(machine + "tomatillo" + `id`),
                                     memory_space = OBJ(machine + "bus-pcimem" + `id` + "B"),
                                     conf_space = OBJ(machine + "bus-pcicfg" + `id` + "B"),
                                     io_space = OBJ(machine + "bus-pciio" + `id` + "B"))] +
                             [OBJECT(machine + "bus-pcicfg" + `id` + "A", "memory-space")] +
                             [OBJECT(machine + "bus-pcicfg" + `id` + "B", "memory-space")] +
                             [OBJECT(machine + "bus-pcimem" + `id` + "A", "memory-space")] +
                             [OBJECT(machine + "bus-pcimem" + `id` + "B", "memory-space")] +
                             [OBJECT(machine + "bus-pciio" + `id` + "A", "memory-space")] +
                             [OBJECT(machine + "bus-pciio" + `id` + "B", "memory-space")])
    if id == 30:
        object_list[machine] += ([OBJECT(machine + "nvram", "PCF8582C",
                                         i2c_bus = OBJ(machine + "gpio-i2c-bus" + `id`),
                                         image = OBJ(machine + "nvram-image"),
                                         address_bits = 16,
                                         address = 0x57,
                                         address__mask = 0x7f)] +
                                 [OBJECT(machine + "nvram-image", "image",
                                         queue = "<queue>",
                                         size = 0x8000)])
        set_attribute(object_list[machine], machine + "bus-pcimem30A", "map",
                      [[0xf0000000L, OBJ(machine + "fiesta_cpuprom"), 0, 0, 0x100000, OBJ(machine + "flash-ram"), 1, 0]])
    
    mem = get_attribute(object_list[machine], machine + "phys_io0", "map")
    mem += [[0x40000000000 + (id << 23), OBJ(machine + "tomatillo" + `id`), 0x0, 0, 0x800000]]
    mem += [[0x40000000000 + ((id + 1) << 23), OBJ(machine + "tomatillo" + `id`), 0x0, 0, 0x800000]]
    set_attribute(object_list[machine], machine + "phys_io0", "map", mem)
    #
    # now add south bridge
    #
    if id == 30:
        set_attribute(object_list[machine], machine + "pcibus30A", "pci_devices",
                      [[6, 0, OBJ(machine + "sb_pm0")],
                       [7, 0, OBJ(machine + "sb_isa0")],
                       [13, 0, OBJ(machine + "sb_ide0")]])
        set_attribute(object_list[machine], machine + "bus-pciio30A", "map",
                      [[0x00, OBJ(machine + "dma0"), 0, 0, 1],
                       [0x01, OBJ(machine + "dma0"), 0, 1, 1],
                       [0x02, OBJ(machine + "dma0"), 0, 2, 1],
                       [0x03, OBJ(machine + "dma0"), 0, 3, 1],
                       [0x04, OBJ(machine + "dma0"), 0, 4, 1],
                       [0x05, OBJ(machine + "dma0"), 0, 5, 1],
                       [0x06, OBJ(machine + "dma0"), 0, 6, 1],
                       [0x07, OBJ(machine + "dma0"), 0, 7, 1],
                       [0x08, OBJ(machine + "dma0"), 0, 8, 1],
                       [0x0a, OBJ(machine + "dma0"), 0, 0xa, 1],
                       [0x0b, OBJ(machine + "dma0"), 0, 0xb, 1],
                       [0x0c, OBJ(machine + "dma0"), 0, 0xc, 1],
                       [0x0d, OBJ(machine + "dma0"), 0, 0xd, 1],
                       [0x0e, OBJ(machine + "dma0"), 0, 0xe, 1],
                       # 0x0f missing
                       [0x70, OBJ(machine + "rtc0"), 0, 0, 1],
                       [0x71, OBJ(machine + "rtc0"), 0, 1, 1],
                       [0x72, OBJ(machine + "rtc0"), 0, 2, 1],
                       [0x73, OBJ(machine + "rtc0"), 0, 3, 1],
                       [0x81, OBJ(machine + "dma0"), 0, 0x81, 1],
                       [0x82, OBJ(machine + "dma0"), 0, 0x82, 1],
                       [0x83, OBJ(machine + "dma0"), 0, 0x83, 1],
                       [0x87, OBJ(machine + "dma0"), 0, 0x87, 1],
                       [0x89, OBJ(machine + "dma0"), 0, 0x89, 1],
                       [0x8a, OBJ(machine + "dma0"), 0, 0x8a, 1],
                       [0x8b, OBJ(machine + "dma0"), 0, 0x8b, 1],
                       [0x8f, OBJ(machine + "dma0"), 0, 0x8f, 1],
                       [0xc0, OBJ(machine + "dma0"), 0, 0xc0, 1],
                       [0xc2, OBJ(machine + "dma0"), 0, 0xc2, 1],
                       [0xc4, OBJ(machine + "dma0"), 0, 0xc4, 1],
                       [0xc6, OBJ(machine + "dma0"), 0, 0xc6, 1],
                       [0xc8, OBJ(machine + "dma0"), 0, 0xc8, 1],
                       [0xca, OBJ(machine + "dma0"), 0, 0xca, 1],
                       [0xcc, OBJ(machine + "dma0"), 0, 0xcc, 1],
                       [0xce, OBJ(machine + "dma0"), 0, 0xce, 1],
                       [0xd0, OBJ(machine + "dma0"), 0, 0xd0, 1],
                       # 0xd2 missing
                       [0xd4, OBJ(machine + "dma0"), 0, 0xd4, 1],
                       [0xd6, OBJ(machine + "dma0"), 0, 0xd6, 1],
                       [0xd8, OBJ(machine + "dma0"), 0, 0xd8, 1],
                       [0xda, OBJ(machine + "dma0"), 0, 0xda, 1],
                       [0xdc, OBJ(machine + "dma0"), 0, 0xdc, 1],
                       # 0xde missing
                       [0x2e8, OBJ(machine + "com3"), 1, 0, 1],
                       [0x2e9, OBJ(machine + "com3"), 1, 1, 1],
                       [0x2ea, OBJ(machine + "com3"), 1, 2, 1],
                       [0x2eb, OBJ(machine + "com3"), 1, 3, 1],
                       [0x2ec, OBJ(machine + "com3"), 1, 4, 1],
                       [0x2ed, OBJ(machine + "com3"), 1, 5, 1],
                       [0x2ee, OBJ(machine + "com3"), 1, 6, 1],
                       [0x2ef, OBJ(machine + "com3"), 1, 7, 1],
                       [0x320, OBJ(machine + "i2c"),  0, 0, 2],
                       # next is the parallel port, not implemented
                       [0x378, OBJ(machine + "unknown"),  0, 0, 4],
                       [0x3e8, OBJ(machine + "com2"), 1, 0, 1],
                       [0x3e9, OBJ(machine + "com2"), 1, 1, 1],
                       [0x3ea, OBJ(machine + "com2"), 1, 2, 1],
                       [0x3eb, OBJ(machine + "com2"), 1, 3, 1],
                       [0x3ec, OBJ(machine + "com2"), 1, 4, 1],
                       [0x3ed, OBJ(machine + "com2"), 1, 5, 1],
                       [0x3ee, OBJ(machine + "com2"), 1, 6, 1],
                       [0x3ef, OBJ(machine + "com2"), 1, 7, 1],
                       [0x3f0, OBJ(machine + "cfg"),  0, 0, 2],
                       [0x3f8, OBJ(machine + "com1"), 1, 0, 1],
                       [0x3f9, OBJ(machine + "com1"), 1, 1, 1],
                       [0x3fa, OBJ(machine + "com1"), 1, 2, 1],
                       [0x3fb, OBJ(machine + "com1"), 1, 3, 1],
                       [0x3fc, OBJ(machine + "com1"), 1, 4, 1],
                       [0x3fd, OBJ(machine + "com1"), 1, 5, 1],
                       [0x3fe, OBJ(machine + "com1"), 1, 6, 1],
                       [0x3ff, OBJ(machine + "com1"), 1, 7, 1],
                       # System Management Bus
                       [0x600, OBJ(machine + "smb"),  0, 0, 1],
                       [0x601, OBJ(machine + "smb"),  0, 1, 1],
                       [0x602, OBJ(machine + "smb"),  0, 2, 1],
                       [0x603, OBJ(machine + "smb"),  0, 3, 1],
                       [0x604, OBJ(machine + "smb"),  0, 4, 1],
                       [0x605, OBJ(machine + "smb"),  0, 5, 1],
                       [0x606, OBJ(machine + "smb"),  0, 6, 1],
                       [0x607, OBJ(machine + "smb"),  0, 7, 1],
                       # PLL Programming
                       [0x700, OBJ(machine + "unknown"),  0, 0, 2],  # temporary: PLL programming
                       # next is unknown
                       [0x77a, OBJ(machine + "unknown"),  0, 0, 1],
                       # ACPI
                       [0x800, OBJ(machine + "acpi"),  0, 0, 2],
                       [0x802, OBJ(machine + "acpi"),  0, 0, 2],
                       [0x804, OBJ(machine + "acpi"),  0, 0, 2],
                       [0x828, OBJ(machine + "acpi"),  0, 0, 1]])
        object_list[machine] += ([OBJECT(machine + "sb_isa0", "MD1535D-isa",
                                         pci_bus = OBJ(machine + "pcibus" + `id` + "A"),
                                         pci_to_isa_irq = [0, 0, 0, 0],
                                         irq_dev = OBJ(machine + "tomatillo" + `id`))] +
                                 [OBJECT(machine + "sb_pm0", "MD1535D-power",
                                         pci_bus = OBJ(machine + "pcibus" + `id` + "A"))] +
                                 [OBJECT(machine + "sb_ide0", "MD1535D-ide",
                                         pci_bus = OBJ(machine + "pcibus" + `id` + "A"),
                                         memory = OBJ(machine + "bus-pcimem" + `id` + "A"),
                                         primary_ide = OBJ(machine + "ide0"),
                                         secondary_ide = OBJ(machine + "ide1"))] +
                                 [OBJECT(machine + "dma0", "i8237x2",
                                         memory = OBJ(machine + "bus-pcimem" + `id` + "A"))] +
                                 [OBJECT(machine + "rtc0", "M5823",
                                         irq_dev = OBJ(machine + "tomatillo" + `id`),
                                         irq_level = 0x19, # use INO to keep it simple
                                         queue = "<queue>")] +
                                 [OBJECT(machine + "acpi", "MD1535D-acpi")] +
                                 [OBJECT(machine + "cfg", "MD1535D-cfg")] +
                                 [OBJECT(machine + "unknown", "MD1535D-unknown")] +
                                 [OBJECT(machine + "smb", "MD1535D-smb")] +
                                 #[OBJECT(machine + "sb_usb0", "piix4_usb",
                                 #        pci_bus = OBJ(machine + "pcibus" + `id` + "A"))] +
                                 # TODO: move adding of IDE devices to own function
                                 [OBJECT(machine + "ide0", "ide",
                                         irq_dev = OBJ(machine + "tomatillo" + `id`),
                                         irq_level = 0x18, # use INO to keep it simple
                                         primary = 1,
                                         bus_master_dma = OBJ(machine + "sb_ide0"),
                                         interrupt_delay = 1.0e-6,
                                         queue = "<queue>")] +
                                 [OBJECT(machine + "ide1", "ide",
                                         irq_dev = OBJ(machine + "tomatillo" + `id`),
                                         irq_level = 0x18, # use INO to keep it simple
                                         primary = 0,
                                         bus_master_dma = OBJ(machine + "sb_ide0"),
                                         interrupt_delay = 1.0e-6,
                                         queue = "<queue>")] +
                                 [OBJECT(machine + "i2c", "PCF8584",
                                         i2c_bus = OBJ(machine + "i2c-bus"),
                                         irq_dev = OBJ(machine + "tomatillo" + `id`),
                                         irq_level = 0x2e, # use INO to keep it simple
                                         queue = "<queue>")]+
                                 [OBJECT(machine + "i2c-bus", "i2c-bus")] +
                                 [OBJECT(machine + "seeprom-image", "image",
                                         queue = "<queue>",
                                         files = fru_file,
                                         size = 0x4000)] +
                                 [OBJECT(machine + "seeprom", "PCF8582C",
                                         i2c__bus = OBJ(machine + "i2c-bus"),
                                         image = OBJ(machine + "seeprom-image"),
                                         address_bits = 16,
                                         address = seeprom_i2c_addr[system],
                                         address__mask = 0x7f)] +
                                 [OBJECT(machine + "pci-clock", "ICS951601",
                                         i2c__bus = OBJ(machine + "i2c-bus"),
                                         address = 0x69)] +
                                 [OBJECT(machine + "temp", "ADM1031",
                                         i2c__bus = OBJ(machine + "i2c-bus"),
                                         address = adm_i2c_addr[system])] +
                                 [OBJECT(machine + "i2c-dram" + `i` + "-image", "image",
                                         queue = "<queue>",
                                         size = 8192)
                                  for i in range(0, num_dimms)] +
                                 [OBJECT(machine + "i2c-dram" + `i`, "PCF8582C",
                                         i2c__bus = OBJ(machine + "i2c-bus"),
                                         image = OBJ(machine + "i2c-dram" + `i` + "-image"),
                                         address = dram_i2c_addr[system] + i,
                                         address__mask = 0x7f)
                                  for i in range(0, num_dimms)] +
                                 [OBJECT(machine + "com1", "NS16550",
                                         irq_dev = OBJ(machine + "tomatillo" + `id`),
                                         irq_level = 0x2c, # use INO to keep it simple
                                         queue = "<queue>",
                                         recorder = OBJ(machine + "rec0"),
                                         console = OBJ(machine + "con0"),
                                         target_pace_receive = 1)] +
                                 [OBJECT(machine + "com2", "NS16550",
                                         irq_dev = OBJ(machine + "tomatillo" + `id`),
                                         irq_level = 0x2c, # use INO to keep it simple
                                         queue = "<queue>",
                                         recorder = OBJ(machine + "rec0"),
                                         console = OBJ(machine + "con0"),
                                         target_pace_receive = 1)] +
                                 [OBJECT(machine + "com3", "NS16550",
                                         irq_dev = OBJ(machine + "tomatillo" + `id`),
                                         irq_level = 0x2c, # use INO to keep it simple
                                         queue = "<queue>",
                                         recorder = OBJ(machine + "rec0"),
                                         target_pace_receive = 1)] +
                                 [OBJECT(machine + "con0", "xterm-console",
                                         device = OBJ(machine + "com1"),
                                         title = "Simics serial console",
                                         bg__color = "gray",
                                         fg__color = "black",
                                         scrollback = 20000,
                                         output__timeout = 30,
                                         width = 80, height = 24,
                                         queue = "<queue>")])
        if num_cpus == 2:
            object_list[machine] += ([OBJECT(machine + "i2c-dram" + `i` + "-image", "image",
                                             queue = "<queue>",
                                             size = 8192)
                                      for i in range(num_dimms, 2 * num_dimms)] +
                                     [OBJECT(machine + "i2c-dram" + `i`, "PCF8582C",
                                             i2c__bus = OBJ(machine + "i2c-bus"),
                                             image = OBJ(machine + "i2c-dram" + `i` + "-image"),
                                             address = 0x63 + i - 4,
                                             address__mask = 0x7f)
                                      for i in range(num_dimms, 2 * num_dimms)])


def add_ide_disk(controller, slot, size, geometry = None, files = ""):
    global num_disks

    if configuration_loaded("add_ide_disk"):
        return

    if not object_exists(object_list[machine], machine + "ide" + `controller`):
        handle_error("Trying to add IDE disk to non-existing controller %d" % controller)
        return

    ide_chip = machine + "ide" + `controller`
    disk_name = machine + "disk" + `num_disks[machine]`

    num_disks[machine] += 1
    
    if slot == "master":
        set_attribute(object_list[machine], ide_chip, "master", OBJ(disk_name))
    elif slot == "slave":
        set_attribute(object_list[machine], ide_chip, "slave", OBJ(disk_name))
    else:
        handle_error("Trying to add IDE disk to non-existing IDE slot %s" % slot)
        return

    if geometry:
        if type([1,2]) != type(geometry) or len(geometry) != 3:
            handle_error("Illegal geometry specification for IDE disk")
            return
    else:
        geometry = [size / (16 * 63 * 512), 16, 63]

    object_list[machine] += ([OBJECT(disk_name, "ide-disk",
                                     disk_sectors = size / 512,
                                     disk_cylinders = geometry[0],
                                     disk_heads = geometry[1],
                                     disk_sectors_per_track = geometry[2],
                                     image = OBJ(disk_name + "_image"))] +
                             [OBJECT(disk_name + "_image", "image",
                                     queue = OBJ(machine + "cpu0"),
                                     size = size)])
    if files != "":
        set_attribute(object_list[machine], disk_name + "_image", "files", files)


def add_ide_cdrom(controller, slot, file = ""):
    global num_cdroms

    if configuration_loaded("add_ide_cdrom"):
        return

    if not object_exists(object_list[machine], machine + "ide" + `controller`):
        handle_error("Trying to add IDE CD-ROM to non-existing controller %d" % controller)
        return

    ide_chip = machine + "ide" + `controller`
    cd_name = machine + "cd" + `num_cdroms[machine]`
    host_cd_name = machine + "host-cd" + `num_cdroms[machine]`
    file_cd_name = machine + "file-cd" + `num_cdroms[machine]`
    
    num_cdroms[machine] += 1
    
    if slot == "master":
        set_attribute(object_list[machine], ide_chip, "master", OBJ(cd_name))
    elif slot == "slave":
        set_attribute(object_list[machine], ide_chip, "slave", OBJ(cd_name))
    else:
        handle_error("Trying to add IDE CD-ROM to non-existing IDE slot %s" % slot)
        return

    object_list[machine] += [OBJECT(cd_name, "ide-cdrom")]

    if file == "":
        return
    elif string.find(file, "/dev/") == 0 or string.find(file, "/vol/rdsk/") == 0:
        object_list[machine] += [OBJECT(host_cd_name, "host-cdrom", file = file)]
        set_attribute(object_list[machine], cd_name, "cd_media", OBJ(host_cd_name))
        print "setting media %s" % host_cd_name
    else:
        object_list[machine] += [OBJECT(file_cd_name, "file-cdrom", file = file)]
        set_attribute(object_list[machine], cd_name, "cd_media", OBJ(file_cd_name))
        print "setting media %s" % file_cd_name
        

def slot_to_pci_name(slot_no):
    # we only have support for one tomatillo now - but prepare for two
    tomatillo = [30, 30, 30, 30, 30, 30, 28, 28]
    buses = ["A", "A", "A", "A", "B", "B", "B", "B"]
    offset = [ 2, 2, 2, 2, -2, -2, -2, -4, -4]
    if slot_no > num_slots[machine]:
        raise StandardError, "Illegal PCI slot number %d. Allowed are 0 .. 5" % (
            slot_no, num_slots[machine])
    return (tomatillo[slot_no], buses[slot_no], slot_no + offset[slot_no])


# TODO: add pci stuff here
# The following is for testing only and may change
def add_pci_pgx64(slot_no):
    global object_list, num_gfx_consoles, have_pgx64_prom
    if configuration_loaded("add_pci_pgx64"):
        return
    num_gfx_consoles[machine] += 1
    try:
        (jid, bus, slot) = slot_to_pci_name(slot_no)
    except msg:
        return handle_error("Cannot add pgx64 device.\n Invalid slot number. Slot %d" % slot_no)
    if not object_exists(object_list[machine], machine + "pcibus" + `jid` + bus):
        return handle_error("Cannot add pgx64 device.\nNo PCI bus exists with slot %d" % slot_no)
    object_list[machine] += ([OBJECT(machine + "pgx" + `slot_no`, "ragexl",
                                     memory_space = OBJ(machine + "bus-pcimem" + `jid` + bus),
                                     pci_bus = OBJ(machine + "pcibus" + `jid` + bus),
                                     console = OBJ(machine + "con" + `num_gfx_consoles[machine]`),
                                     expansion_rom = [OBJ(machine + "pgx" + `slot_` + "_prom"), 0x20000, 0],
                                     queue = "<queue>")] +
                             [OBJECT(machine + "pgx" + `slot_no` + "_prom", "rom",
                                     image = OBJ("fiesta_pgx64_prom_image"))] +
                             [OBJECT(machine + "con" + `num_gfx_consoles[machine]`, "gfx-console",
                                     x__size = 640,
                                     y__size = 400,
                                     #mouse = OBJ(machine + "mouse"),
                                     #keyboard = OBJ(machine + "keyboard"),
                                     queue = "<queue>")])
    if not have_pgx64_prom:
        have_pgx64_prom = 1
        object_list[machine] += ([OBJECT("fiesta_pgx64_prom_image", "image",
                                         size = 0x20000,
                                         files = [["pgx64.fcode", "ro", 0, 65536]],
                                         queue = "<queue>")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + `jid` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot, 0, OBJ(machine + "pgx" + `slot_no`)]]
    set_attribute(object_list[machine], machine + "pcibus" + `jid` + bus, "pci_devices", pci_devs)    


def add_pci_bge(slot_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_bge"):
        return
    try:
        (jid, bus, slot) = slot_to_pci_name(slot_no)
    except msg:
        return handle_error("Cannot add bge device.\n Invalid slot number. Slot %d" % slot_no)
    if not object_exists(object_list[machine], machine + "pcibus" + `jid` + bus):
        return handle_error("Cannot add bge device.\nNo PCI bus exists with slot %d" % slot_no)
    object_list[machine] += ([OBJECT(machine + "bge" + `slot_no`, "BCM5703C",
                                     pci_bus = OBJ(machine + "pcibus" + `jid` + bus),
                                     recorder = OBJ(machine + "rec0"),
                                     mac_address = mac_address,
                                     queue = "<queue>")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + `jid` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot, 0, OBJ(machine + "bge" + `slot_no`)]]
    set_attribute(object_list[machine], machine + "pcibus" + `jid` + bus, "pci_devices", pci_devs)    


def add_pci_dual_bge(slot_no, mac_address0, mac_address1):
    global object_list
    if configuration_loaded("add_pci_dual_bge"):
        return
    try:
        (jid, bus, slot) = slot_to_pci_name(slot_no)
    except msg:
        return handle_error("Cannot add bge device.\n Invalid slot number. Slot %d" % slot_no)
    if not object_exists(object_list[machine], machine + "pcibus" + `jid` + bus):
        return handle_error("Cannot add bge device.\nNo PCI bus exists with slot %d" % slot_no)
    object_list[machine] += ([OBJECT(machine + "bge" + `slot_no` + "_0", "BCM5704C",
                                     pci_bus = OBJ(machine + "pcibus" + `jid` + bus),
                                     recorder = OBJ(machine + "rec0"),
                                     is_mac1 = 0,
                                     other_bcm = OBJ(machine + "bge" + `slot_no` + "_1"),
                                     mac_address = mac_address0,
                                     queue = "<queue>")] +
                             [OBJECT(machine + "bge" + `slot_no` + "_1", "BCM5704C",
                                     pci_bus = OBJ(machine + "pcibus" + `jid` + bus),
                                     recorder = OBJ(machine + "rec0"),
                                     is_mac1 = 1,
                                     other_bcm = OBJ(machine + "bge" + `slot_no` + "_0"),
                                     mac_address = mac_address1,
                                     queue = "<queue>")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + `jid` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot, 0, OBJ(machine + "bge" + `slot_no` + "_0")],
                 [slot, 1, OBJ(machine + "bge" + `slot_no` + "_1")]]
    set_attribute(object_list[machine], machine + "pcibus" + `jid` + bus, "pci_devices", pci_devs)    


def add_pci_bcm5703c(slot_no, mac_address):
    print "Obsolete function 'add_pci_bcm5703c()': use 'add_pci_bge()' instead."
    add_pci_bge(slot_no, mac_address)
    
def add_pci_bcm5704c(slot_no, mac_address0, mac_address1):
    print "Obsolete function 'add_pci_bcm5704c()': use 'add_pci_dual_bge()' instead."
    add_pci_bge(slot_no, mac_address0, mac_address1)

def add_pci_ce(slot_no, mac_address):
    global object_list, cassini_proms
    if configuration_loaded("add_pci_ce"):
        return
    try:
        (jid, bus, slot) = slot_to_pci_name(slot_no)
    except msg:
        return handle_error("Cannot add ce device.\n"
                            "Invalid slot number. Slot %d" % slot_no)
    if not object_exists(object_list[machine], machine + "pcibus" + `jid` + bus):
        return handle_error("Cannot add ce device.\n"
                            "No PCI bus exists with slot %d" % slot_no)
    object_list[machine] += ([OBJECT(machine + "bridge" + `slot_no`, "i21152",
                                     pci_bus = OBJ(machine + "pcibus" + `jid` + bus),
                                     secondary_bus = OBJ(machine + "sub-pcibus" + `slot_no`),
                                     queue = "<queue>")] +
                             [OBJECT(machine + "sub-pcibus" + `slot_no`, "pci-bus",
                                     bridge = OBJ(machine + "bridge" + `slot_no`),
                                     pci_devices = [[0, 0, OBJ(machine + "ce" + `slot_no`)],
                                                    [0, 1, OBJ(machine + "ce_sub1_" + `slot_no`)],
                                                    [0, 2, OBJ(machine + "ce_sub2_" + `slot_no`)],
                                                    [0, 3, OBJ(machine + "ce_sub3_" + `slot_no`)]],
                                     memory_space = OBJ(machine + "sub-pcimem" + `slot_no`),
                                     conf_space = OBJ(machine + "sub-pcicfg" + `slot_no`),
                                     io_space = OBJ(machine + "sub-pciio" + `slot_no`),
                                     interrupt = OBJ(machine + "bridge" + `slot_no`))] +
                             [OBJECT(machine + "sub-pciio" + `slot_no`, "memory-space")] +
                             [OBJECT(machine + "sub-pcicfg" + `slot_no`, "memory-space")] +
                             [OBJECT(machine + "sub-pcimem" + `slot_no`, "memory-space")] +
                             [OBJECT(machine + "ce" + `slot_no`, "cassini",
                                     pci_bus = OBJ(machine + "sub-pcibus" + `slot_no`),
                                     recorder = OBJ(machine + "rec0"),
                                     mac_address = mac_address,
                                     expansion_rom = [OBJ(machine + "ce" + `slot_no` + "_prom"), 0x100000, 0],
                                     queue = "<queue>")] +
                             [OBJECT(machine + "ce_sub1_" + `slot_no`, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pcibus" + `slot_no`),
                                     main_object = OBJ(machine + "ce" + `slot_no`),
                                     pci_function = 1)] +
                             [OBJECT(machine + "ce_sub2_" + `slot_no`, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pcibus" + `slot_no`),
                                     main_object = OBJ(machine + "ce" + `slot_no`),
                                     pci_function = 2)] +
                             [OBJECT(machine + "ce_sub3_" + `slot_no`, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pcibus" + `slot_no`),
                                     main_object = OBJ(machine + "ce" + `slot_no`),
                                     pci_function = 3)] +
                             [OBJECT(machine + "ce" + `slot_no` + "_prom", "rom",
                                     image = OBJ(machine + "cassini_prom_image" + `slot_no`))] +
                             [OBJECT(machine + "cassini_prom_image" + `slot_no`, "image",
                                     size = 0x10000,
                                     files = [["cassini_plus.fcode", "ro", 0, 0x10000]],
                                     queue = "<queue>")])
    cassini_proms += [[machine + "cassini_prom_image" + `slot_no`, mac_address]]
    try:
        pci_devs = get_attribute(object_list[machine],
                                 machine + "pcibus" + `jid` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot, 0, OBJ(machine + "bridge" + `slot_no`)]]
    set_attribute(object_list[machine],
                  machine + "pcibus" + `jid` + bus, "pci_devices", pci_devs)
    # set mac address in VPN (offset is fcode file specific)
    


def set_idprom():
    nvram = eval("conf." + machine + "nvram_image")
    idprom_base = 0x1fe0L
    # offset 0 = format (1)
    nvram.byte_access[idprom_base + 0] = 1
    # offset 1, 12-14 = hostid 
    nvram.byte_access[idprom_base + 1]  = (host_id[machine] >> 24) & 0xff
    nvram.byte_access[idprom_base + 12] = (host_id[machine] >> 16) & 0xff
    nvram.byte_access[idprom_base + 13] = (host_id[machine] >>  8) & 0xff
    nvram.byte_access[idprom_base + 14] = (host_id[machine] >>  0) & 0xff
    # offset 2 - 7 = ethernet
    for i in range(0, len(mac[machine])):
        nvram.byte_access[idprom_base + 2 + i] = mac[machine][i]
    # offset 8 - 11 = date (not used?)
    # offset 15 = checksum
    chk = 0
    for i in range(0, 15):
        chk ^= nvram.byte_access[idprom_base + i]
    nvram.byte_access[idprom_base + 15] = chk & 0xff

global_cpu = {}

def set_global_cpu():
    objs = []
    global_cpu[machine] = None
    for i in object_list[machine]:
        if i[1][:10] == "ultrasparc":
            global_cpu[machine] = i[0]
            break
    if global_cpu[machine] == None:
        handle_error("No processor defined")
    for i in object_list[machine]:
        try:
            queue = get_attribute(object_list[machine], i[0], "queue")
            if queue == "<queue>":
                set_attribute(object_list[machine], i[0], "queue", OBJ(global_cpu[machine]))
        except:
            pass

def set_dimm_config(cpu_no):
    # run for all dimms
    for i in range(cpu_no * num_dimms, (cpu_no + 1) * num_dimms):
        obj = eval("conf." + machine + "i2c_dram%d_image" % i)
        obj.byte_access[0x00] = 0x80  # bytes of info
        obj.byte_access[0x01] = 0x08  # 256 bytes eeprom
        obj.byte_access[0x02] = 0x07  # memory type SDRAM
        mem = mem_sizes[total_mem[machine]/(1024*1024)]
        if i < mem[0]:
            obj.byte_access[0x03] = mem[2] # Num row address bits
        else:
            obj.byte_access[0x03] = 0x00   # Num row address bits
        obj.byte_access[0x04] = 0x0a   # Num col address bits
        obj.byte_access[0x05] = mem[1] # Num module rows
        obj.byte_access[0x06] = 0x48  # Module data width (144 bits)
        obj.byte_access[0x07] = 0x00  # Module data width (cont)
        obj.byte_access[0x08] = 0x04  # Signal voltage (2.5V)
        obj.byte_access[0x09] = 0x75  # SDRAM cycle time (1)
        obj.byte_access[0x0a] = 0x80  # SDRAM access from clock (1)
        obj.byte_access[0x0b] = 0x02  # ECC memory
        obj.byte_access[0x0c] = 0x82  # Self refresh, normal period
        obj.byte_access[0x0d] = 0x08  # SDRAM width (8/device)
        obj.byte_access[0x0e] = 0x08  # Error checking width
        obj.byte_access[0x0f] = 0x01  # Delay back-to-back colum
        obj.byte_access[0x10] = 0x0e  # Burst lengths (8, 4, 2, 1)
        obj.byte_access[0x11] = 0x04  # Num banks / row
        obj.byte_access[0x12] = 0x0c  # CAS latency (4, 3, 2, 1)
        obj.byte_access[0x13] = 0x01  # CS latency (3, 2, 1, 0)
        obj.byte_access[0x14] = 0x02  # WE latency (3, 2, 1, 0)
        obj.byte_access[0x15] = 0x26  # Module attributes
        obj.byte_access[0x16] = 0x00  # Device attributes
        obj.byte_access[0x17] = 0x75  # SDRAM cycle time (2)
        obj.byte_access[0x18] = 0x80  # SDRAM access from clock (2)
        obj.byte_access[0x19] = 0x00  # SDRAM cycle time (3)
        obj.byte_access[0x1a] = 0x00  # SDRAM access from clock (3)
        obj.byte_access[0x1b] = 0x50  # Row Precharge
        obj.byte_access[0x1c] = 0x3c  # Row active to active min
        obj.byte_access[0x1d] = 0x50  # RAS to CAS delay min
        obj.byte_access[0x1e] = 0x32  # Minimun RAS pulse width
        obj.byte_access[0x1f] = 0x40  # density of each row
        obj.byte_access[0x3e] = 0x00  # SPD Data Revision Code

def create_cpu_spaces():
    for i in object_list[machine]:
        if i[1][:10] == "ultrasparc":
            space = machine + "%s_mem" % i[0]
            set_attribute(object_list[machine], i[0], "physical_memory", OBJ(space))
            object_list[machine] += [OBJECT(space, "memory-space",
                                            map = [[0, OBJ(machine + "phys_mem0"), 0, 0, 0xffffffffffffffff]])]

def get_configuration():
    global machine
    all_objs = []
    
    for mach in machine_list:
        #finally add hostfs
        machine = mach

        try:
            get_attribute(object_list[machine], machine + "ide0", "master")
        except:
            handle_error("The IDE controller %s needs a 'master' disk or CD-ROM" % (machine + "ide0"))
            return
        try:
            get_attribute(object_list[machine], machine + "ide1", "master")
        except:
            handle_error("The IDE controller %s needs a 'master' disk or CD-ROM" % (machine + "ide1"))
            return

        set_global_cpu()

        all_cpus = []
        for i in cpu_list[machine]:
            all_cpus.append(OBJ(machine + "cpu" + `i`))
        object_list[machine] += ([OBJECT(machine + "system", "fiesta-system",
                                         master_cpu = OBJ(global_cpu[machine]),
                                         nvram_image = OBJ(machine + "nvram_image"),
                                         all_cpus = all_cpus)])

        mem = get_attribute(object_list[machine], machine + "phys_mem0", "map")
        mem += [[0x7fff07ffff0, OBJ(machine + "hfs0"), 0, 0x0, 0x10]]
        mem = set_attribute(object_list[machine], machine + "phys_mem0", "map", mem)
        hfs_conf = ([OBJECT(machine + "hfs0", "hostfs")])
        object_list[machine] += hfs_conf
        all_objs += object_list[machine]
    return all_objs

def post_configuration():
    global machine
    # some last after config setup stuff
    for mach in machine_list:
        machine = mach

        for i in range(num_processors[machine]):
            set_dimm_config(i)
        eval_cli_line(machine + "system.set-prom-defaults")
        set_idprom()
        m = re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)',
                     global_time[machine])
        eval_cli_line(machine
                      + (("rtc0.set-date-time -binary"
                          + " year=%s month=%s mday=%s"
                          + " hour=%s minute=%s second=%s")
                         % tuple(m.groups())))
    # set MAC address in Cassini VPD:
    # In our file VPN starts at 0xc000. The VPD layout for the
    # 'local-mac-address' properly looks like:
    #   Z9 <1d> I <01> <00> B <06> local-mac-address <00> <binary mac address>
    # Note that in the original image the fourth byte was 0x00 but has
    # to be changed into 0xff for the MAC to be accepted.
    for p in cassini_proms:
        SIM_get_object(p[0]).byte_access[0xc0ea] = 0xff
        SIM_get_object(p[0]).byte_access[[0xc100, 0xc105]] = tuple(mac_string_to_list(p[1]))

def finish_configuration():
    if configuration_loaded("finish_configuration"):
        return
    
    all_objs = get_configuration()
    
    try:
        SIM_set_configuration(all_objs)
    except Exception, msg:
        print
        print msg
        print
        print "Failed loading the configuration in Simics. This is probably"
        print "due to some misconfiguration, or that some required file is"
        print "missing. Please check the above output for error messages"
        print
        SIM_command_has_problem()
        if VT_remote_control():
            VT_send_control_msg(['startup-failure', 0, str(msg)])
        return

    post_configuration()
