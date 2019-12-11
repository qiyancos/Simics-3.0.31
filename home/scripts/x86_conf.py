
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
import os

machine_list = []
object_list = {}
apic_present = {}
ioapic_present = {}
num_cpu = {}
rtc_date = {}
boot_device = {}
num_gfx_consoles = {}
total_megs = {}
num_disks = {}
num_cdroms = {}
bios_geometry = {}
initialize_cmos = {}
have_isa_vga = {}
num_floppies = {}
acpi_machine = {}
acpi_bug_workaround_present = {}
create_mem_map = {}
have_sim_object = 0
le_max_processors = 2

max_rombios_size = 1*1024*1024

have_north_bridge = {}
have_south_bridge = {}

x86_class_name = {}

if not "machine" in dir(): machine = ""
if not "additional_acpi_tables" in dir(): additional_acpi_tables = ()

# Set 'show_le_checksum' if you want to display the LE checksum on startup.
# Causes the LE-permissions object to be created even if not running under
# a LE-license, enabling the le-checksum command.
if not "show_le_checksum" in dir(): show_le_checksum = 0

SIM_source_python_in_module("../scripts/pci_conf.py", __name__)
SIM_source_python_in_module("../scripts/acpi.py", __name__)

if not SIM_get_quiet():
    print
    print "Machines based on x86_conf.py are only provided for backward "
    print "compatibility. The new component based machines in simics/targets/"
    print "are recommended instead."
    print

try:
    SIM_source_python_in_module("../scripts/pci_ec.py", __name__)
except:
    pass

def handle_error(msg):
    return configuration_error(msg)

def configuration_loaded(func):
    if SIM_initial_configuration_ok() != 0:
        print "The function '%s' cannot be used once a configuration is loaded" % func
        SIM_command_has_problem()
        return 1
    else:
        return 0

conf_list = []

def set_machine(mach):
    global machine, conf_list
    machine = mach
    try:
        conf_list = object_list[machine]
    except:
        pass

def get_machine():
    global machine
    return machine

def create_system(num_cpus, mhz, mb, cpu_class = "x86-p4", threads_per_cpu = 1,
                  use_hostfs = 1, use_apics = 1, use_acpi = 0, io_apic_id = -1,
                  bios = "", ioapic = 1, init_cmos = 1,
                  linux_acpi_bug_workaround = 0, apic_bus_divisor = 1,
                  use_mmap_memory = 0, ram_priority = 0):
    global machine_list, apic_present, num_cpu, num_gfx_consoles
    global ioapic_present, acpi_bug_workaround_present
    global rtc_date, boot_device, have_sim_object, total_megs, num_disks
    global bios_geometry, have_isa_vga, num_floppies, acpi_machine, conf_list
    global create_mem_map
    global x86_class_name

    if configuration_loaded("create_system"):
        return

    if num_cpus < 1:
        handle_error("At least one cpu must be created")
        return

    num_cpus *= threads_per_cpu

    machine_list += [machine]
    apic_present[machine] = use_apics
    ioapic_present[machine] = ioapic
    num_cpu[machine] = num_cpus
    total_megs[machine] = mb
    num_gfx_consoles[machine] = 0
    rtc_date[machine] = 0
    boot_device[machine] = 0
    num_disks[machine] = 0
    num_cdroms[machine] = 0
    bios_geometry[machine] = [[[0,0,0], [0,0,0]], [[0,0,0], [0,0,0]]]
    have_isa_vga[machine] = 0
    num_floppies[machine] = 0
    acpi_machine[machine] = use_acpi
    acpi_bug_workaround_present[machine] = linux_acpi_bug_workaround
    have_north_bridge[machine] = 0
    have_south_bridge[machine] = 0
    x86_class_name[machine] = cpu_class
    initialize_cmos[machine] = init_cmos
    create_mem_map[machine] = init_cmos

    if SIM_lookup_file(bios) == None:
        handle_error("Could not locate bios file %s" % bios)
        return
    bios_size = os.stat(SIM_lookup_file(bios)).st_size

    # Default bios contains trailing garbage
    if bios[:10] == "rombios-2.":
        bios_size = 64*1024

    if bios_size > max_rombios_size:
        handle_error("BIOS size %u is larger than max (%u)" % (bios_size, max_rombios_size))
        return

    if io_apic_id == -1:
        io_apic_id = num_cpus

    mem_map = [[0x00000000, OBJ(machine + "ram0"), 0, 0, 0xA0000],
               [0x000F0000, OBJ(machine + "rom0"), 0, bios_size - 0x10000, 0x10000],
               [0x100000000 - bios_size, OBJ(machine + "rom0"), 0, 0, bios_size]]
    if linux_acpi_bug_workaround:
        mem_map += [[0x000E0000, OBJ(machine + "rom1"), 0, 0, 0x10000]]
    if mb > (4096 - 256):
        if SIM_get_class_attribute(cpu_class, "address-width")[0] == 32:
            handle_error("Class '%s' cannot handle addresses wider than 32 bits. Max memory size is 3840 Mb." % cpu_class)
            return
        split_hi = 1
        high_mem = (4096 - 256)
        hi = mb - high_mem
        mem_map.append([0x000100000, OBJ(machine + "ram0"), 0, 0x100000, high_mem * 1024 * 1024, None, ram_priority])
        mem_map.append([0x100000000, OBJ(machine + "ram0"), 0, high_mem * 1024 * 1024, hi * 1024 * 1024, None, ram_priority])
    else:
        mem_map.append([0x000100000, OBJ(machine + "ram0"), 0, 0x100000, (mb - 1) * 1024 * 1024, None, ram_priority])

    object_list[machine] = ([OBJECT(machine + "cpu" + `i`, x86_class_name[machine],
                                    tlb = OBJ(machine + "tlb" + `i`),
                                    processor_number = get_next_cpu_number(),
                                    queue = OBJ(machine + "cpu" + `i`),
                                    freq_mhz = mhz,
                                    physical_memory = OBJ(machine + "phys_mem" + `i`),
                                    port_space = OBJ(machine + "port_mem0"))
                             for i in range(num_cpus)] +
                            [OBJECT(machine + "tlb" + `i`, "x86-tlb",
                                    cpu = OBJ(machine + "cpu" + `i`),
                                    type = "unlimited")
                             for i in range(num_cpus)] +
                            [OBJECT(machine + "phys_mem" + `i`, "memory-space",
                                    map = [],
                                    default_target = [OBJ(machine + "pci_mem0"), 0, 0, OBJ(machine + "pci_mem0")])
                             for i in range(num_cpus)] +
                            [OBJECT(machine + "pci_mem0", "memory-space",
                                    map = mem_map[0:])] +
                            [OBJECT(machine + "reset0", "x86-reset-bus")])

    object_list[machine] += [OBJECT("%s_component" % iff(len(machine), machine, "x86"), "dummy-component")]

    if apic_present[machine] == 1:
        object_list[machine] += ([OBJECT(machine + "apic" + `i`, "apic",
                                         apic_id = i,
                                         apic_bus = OBJ(machine + "apic_bus0"),
                                         cpu = OBJ(machine + "cpu" + `i`),
                                         cpu_bus_divisor = float(apic_bus_divisor),
                                         queue = OBJ(machine + "cpu" + `i`))
                                  for i in range(num_cpus)] +
                                 [OBJECT(machine + "apic_bus0", "apic-bus",
                                         apics = [OBJ(machine + "apic" + `i`) for i in range(num_cpus)])])

	if ioapic_present[machine]:
            set_attribute(object_list[machine], machine + "apic_bus0", "ioapic", OBJ(machine + "ioapic0"))
	    object_list[machine] += ([OBJECT(machine + "ioapic0", "io-apic",
                                         apic_bus = OBJ(machine + "apic_bus0"),
                                         ioapic_id = (io_apic_id << 24))])

        for i in range(num_cpus):
            if threads_per_cpu > 1:
                set_attribute(object_list[machine], machine + "cpu" + `i`, "cpuid_logical_processor_count", threads_per_cpu)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "cpuid_physical_apic_id", i)
                if (i % threads_per_cpu) != 0:
                    set_attribute(object_list[machine], machine + "cpu" + `i`,
                                  "shared_state", OBJ(machine + "cpu" + `int(i / threads_per_cpu)`))
            set_attribute(object_list[machine], machine + "cpu" + `i`, "apic", OBJ(machine + "apic" + `i`))
            set_attribute(object_list[machine], machine + "cpu" + `i`, "bsp", i==0)
            map = get_attribute(object_list[machine], machine + "phys_mem" + `i`, "map")
            # TODO: put back?
            #map += [[0xFEC00000, OBJ(machine + "ioapic0"), 0, 0, 0x20],
            #        [0xFEE00000, OBJ(machine + "apic" + `i`), 0, 0, 0x4000]]
            map += [[0xFEE00000L, OBJ(machine + "apic" + `i`), 0, 0, 0x4000]]
            set_attribute(object_list[machine], machine + "phys_mem" + `i`, "map", map)

        map = get_attribute(object_list[machine], machine + "pci_mem0", "map")
        if ioapic_present[machine]:
            map += [[0xFEC00000L, OBJ(machine + "ioapic0"), 0, 0, 0x20]]
        set_attribute(object_list[machine], machine + "pci_mem0", "map", map)

    object_list[machine] += ([OBJECT(machine + "port_mem0", "port-space",
                                     map = [[0xfff0, OBJ(machine + "conf0"), 0, 0, 1],
                                            [0xfff1, OBJ(machine + "conf0"), 1, 0, 1]])] +
                             [OBJECT(machine + "conf0", "pc-config")] +
                             [OBJECT(machine + "rec0", "recorder")] +
                             [OBJECT(machine + "ram0", "ram",
                                     image = OBJ(machine + "mem0_image"))] +
                             [OBJECT(machine + "mem0_image", "image",
                                     queue = OBJ(machine + "cpu0"),
                                     size = mb * 1024 * 1024)] +
                             [OBJECT(machine + "rom0", "rom",
                                     image = OBJ(machine + "rom0_image"))] +
                             [OBJECT(machine + "rom0_image", "image",
                                     queue = OBJ(machine + "cpu0"),
                                     size = max_rombios_size + 0x10000,
                                     files = [[bios, 1, 0, bios_size]])])
    if linux_acpi_bug_workaround:
        object_list[machine] += ([OBJECT(machine + "rom1", "rom",
                                         image = OBJ(machine + "rom1_image"))] +
                                 [OBJECT(machine + "rom1_image", "image",
                                         queue = OBJ(machine + "cpu0"),
                                         size = 0x10000)])
    if have_sim_object == 0:
        have_sim_object = 1
        object_list[machine] += [OBJECT("sim", "sim",
                                        handle__outside__memory = 1,
                                        icode_dump_freq = 6000000000)]
    if use_hostfs == 1:
        object_list[machine] += [OBJECT(machine + "hfs0", "hostfs")]
        for i in range(num_cpus):
            phys_map = get_attribute(object_list[machine], machine + "phys_mem"+`i`, "map")
            phys_map += [[0xffe81000L, OBJ(machine + "hfs0"), 0, 0, 16]]
            set_attribute(object_list[machine], machine + "phys_mem"+`i`, "map", phys_map)

    if use_mmap_memory:
        set_attribute(object_list[machine], machine + "mem0_image", "mapfile_dir", "/tmp")
        set_attribute(object_list[machine], machine + "cpu0", "turbo_mmap_memory", 1)

    conf_list = object_list[machine]


def add_legacy_devices(year, month, mday, hour, minute, second, boot_dev = "C", rtc_irq = 8, rtc_dml_module = 0):
    global boot_device, rtc_date

    if configuration_loaded("add_legacy_devices"):
        return

    if object_exists(object_list[machine], machine + "pic0"):
        handle_error("Can only have one instance of legacy devices");
        return

    boot_device[machine] = boot_dev
    rtc_date[machine] = [year, month, mday, hour, minute, second]

    if rtc_dml_module:
        rtc = [OBJECT(machine + "rtc0", "DS12887_dml",
                      irq_dev = OBJ(machine + "isa0"),
                      irq_level = rtc_irq,
                      registers_a = 0x20,
                      registers_b = 0x02,
                      queue = OBJ(machine + "cpu0"))]
    else:
        rtc = [OBJECT(machine + "rtc0", "DS12887",
                      irq_dev = OBJ(machine + "isa0"),
                      irq_level = rtc_irq,
                      queue = OBJ(machine + "cpu0"))]

    object_list[machine] += ([OBJECT(machine + "isa0", "ISA",
                                     pic = OBJ(machine + "pic0"),
                                     irq_to_pin = [2, 1, 0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
                                                   19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31])] +
                             [OBJECT(machine + "pit0", "i8254",
                                     irq_dev = OBJ(machine + "isa0"),
                                     irq_level = 0,
                                     gate = [1, 1, 0, 0],
                                     out = [1, 1, 1, 0],
                                     queue = OBJ(machine + "cpu0"))] +
                             [OBJECT(machine + "dma0", "i8237x2",
                                     memory = OBJ(machine + "pci_mem0"))] +
                             [OBJECT(machine + "pic0", "i8259x2",
                                     queue = OBJ(machine + "cpu0"))] +
                             rtc +
                             [OBJECT(machine + "x87_exc0", "x87_exception",
                                     irq_dev = OBJ(machine + "pic0"),
                                     irq_level = 13,
                                     ignne_target = OBJ(machine + "cpu0"),
                                     queue = OBJ(machine + "cpu0"))])
    set_attribute(object_list[machine], machine + "cpu0", "ferr_target", OBJ(machine + "x87_exc0"))

    if ioapic_present[machine] == 1:
        set_attribute(object_list[machine], machine + "isa0", "ioapic", OBJ(machine + "ioapic0"))
        set_attribute(object_list[machine], machine + "pic0", "irq_dev", OBJ(machine + "apic_bus0"))
    else:
        set_attribute(object_list[machine], machine + "pic0", "irq_dev", OBJ(machine + "cpu0"))

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x40, OBJ(machine + "pit0"), 0, 0, 1],
            [0x41, OBJ(machine + "pit0"), 0, 1, 1],
            [0x42, OBJ(machine + "pit0"), 0, 2, 1],
            [0x43, OBJ(machine + "pit0"), 0, 3, 1],
            [0x61, OBJ(machine + "pit0"), 1, 0, 1],
            [0x00, OBJ(machine + "dma0"), 0, 0, 1],
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
            [0xd4, OBJ(machine + "dma0"), 0, 0xd4, 1],
            [0xd6, OBJ(machine + "dma0"), 0, 0xd6, 1],
            [0xd8, OBJ(machine + "dma0"), 0, 0xd8, 1],
            [0x20, OBJ(machine + "pic0"), 0, 0x20, 1],
            [0x21, OBJ(machine + "pic0"), 0, 0x21, 1],
            [0xa0, OBJ(machine + "pic0"), 0, 0xa0, 1],
            [0xa1, OBJ(machine + "pic0"), 0, 0xa1, 1],
            [0x4d0, OBJ(machine + "pic0"), 0, 0x4d0, 1],
            [0x4d1, OBJ(machine + "pic0"), 0, 0x4d1, 1],
            [0x70, OBJ(machine + "rtc0"), 0, 0, 1],
            [0x71, OBJ(machine + "rtc0"), 0, 1, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_legacy_keyboard(kbd_irq = 1, mouse_irq = 12):

    if configuration_loaded("add_legacy_keyboard"):
        return

    if object_exists(object_list[machine], machine + "kbd0"):
        handle_error("Only one legacy keyboard supported")
        return

    object_list[machine] += [OBJECT(machine + "kbd0", "i8042",
                                    irq_dev = OBJ(machine + "isa0"),
                                    kbd_irq_level = kbd_irq,
                                    mouse_irq_level = mouse_irq,
                                    recorder = OBJ(machine + "rec0"),
                                    queue = OBJ(machine + "cpu0"))]

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x60, OBJ(machine + "kbd0"), 0, 0, 1],
            [0x64, OBJ(machine + "kbd0"), 0, 4, 1],
            [0x92, OBJ(machine + "kbd0"), 0, 0x92-0x60, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_fourport(use_console0 = 0, use_console1 = 0, use_console2 = 0, use_console3 = 0, base_address = 0x2a0, irq = 2, uart_class = "NS16450"):

    if configuration_loaded("add_fourport"):
        return

    if base_address == 0x2a0:
        base_name = "fourport_std"
        com_base = 5
    elif base_address == 0x1a0:
        base_name = "fourport_alt"
        com_base = 9
    else:
        handle_error("Invalid base address to add_fourport")
        return

    if irq < 2 or irq > 7:
        handle_error("Invalid irq to add_fourport")
        return

    object_list[machine] += ([OBJECT(machine + base_name + `i`, uart_class,
                                     irq_dev = OBJ(machine + base_name + "_irq"),
                                     irq_level = i,
                                     interrupt_mask_out2 = 0,
                                     queue = OBJ(machine + "cpu0"),
                                     recorder = OBJ(machine + "rec0"))
                              for i in range(4)])

    object_list[machine] += ([OBJECT(machine + base_name + "_irq", "fourport",
                                     irq_dev = OBJ(machine + "isa0"),
                                     irq_level = irq)])

    use_consoles = (use_console0, use_console1, use_console2, use_console3)
    for i in range(4):
        if use_consoles[i]:
            object_list[machine] += [OBJECT(machine + "com" + `com_base + i` + "_con", "text-console",
                                        title = machine + "com" + `com_base + i` + " console",
                                        width = 80,
                                        height = 25,
                                        queue = OBJ(machine + "cpu0"),
                                        device = OBJ(machine + base_name + `i`))]
            set_attribute(object_list[machine], machine + base_name + `i`, "console", OBJ(machine + "com" + `com_base + i` + "_con"))

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    for i in range(4):
        map += [[base_address + i*8 + 0, OBJ(machine + base_name + `i`), com_base + i, 0, 1],
                [base_address + i*8 + 1, OBJ(machine + base_name + `i`), com_base + i, 1, 1],
                [base_address + i*8 + 2, OBJ(machine + base_name + `i`), com_base + i, 2, 1],
                [base_address + i*8 + 3, OBJ(machine + base_name + `i`), com_base + i, 3, 1],
                [base_address + i*8 + 4, OBJ(machine + base_name + `i`), com_base + i, 4, 1],
                [base_address + i*8 + 5, OBJ(machine + base_name + `i`), com_base + i, 5, 1],
                [base_address + i*8 + 6, OBJ(machine + base_name + `i`), com_base + i, 6, 1]]
    for i in range(3):
        map += [[base_address + i*8 + 7, OBJ(machine + base_name + `i`), com_base + i, 7, 1]]
    map += [[base_address + 3 * 8 + 7, OBJ(machine + base_name + "_irq"), 0, 0, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_legacy_serial(num_ports, use_console0 = 0, use_console1 = 0, use_console2 = 0, use_console3 = 0, com1_irq = 4, com2_irq = 3, com3_irq = 4, com4_irq = 3, uart_class = "NS16450"):

    if configuration_loaded("add_legacy_serial"):
        return

    if object_exists(object_list[machine], machine + "com1"):
        handle_error("Legacy serial ports already added")
        return

    if num_ports > 4:
        handle_error("More that 4 legacy serial ports is not supported")
        return

    if num_ports < 1:
        return

    object_list[machine] += [OBJECT(machine + "com1", uart_class,
                                    irq_dev = OBJ(machine + "isa0"),
                                    irq_level = com1_irq,
                                    interrupt_mask_out2 = 1,
                                    queue = OBJ(machine + "cpu0"),
                                    recorder = OBJ(machine + "rec0"),
                                    target_pace_receive = 1)]
    if use_console0:
        object_list[machine] += [OBJECT(machine + "com1_con", "text-console",
                                        title = machine + "com1 console",
                                        width = 80,
                                        height = 25,
                                        queue = OBJ(machine + "cpu0"),
                                        device = OBJ(machine + "com1"))]
        set_attribute(object_list[machine], machine + "com1", "console", OBJ(machine + "com1_con"))
    if num_ports > 1:
        object_list[machine] += [OBJECT(machine + "com2", uart_class,
                                        irq_dev = OBJ(machine + "isa0"),
                                        irq_level = com2_irq,
                                        queue = OBJ(machine + "cpu0"),
                                        recorder = OBJ(machine + "rec0"))]
        if use_console1:
            object_list[machine] += [OBJECT(machine + "com2_con", "text-console",
                                            title = machine + "com2 console",
                                            width = 80,
                                            height = 25,
                                            queue = OBJ(machine + "cpu0"),
                                            device = OBJ(machine + "com2"))]
            set_attribute(object_list[machine], machine + "com2", "console", OBJ(machine + "com2_con"))
    if num_ports > 2:
        object_list[machine] += [OBJECT(machine + "com3", uart_class,
                                        irq_dev = OBJ(machine + "isa0"),
                                        irq_level = com3_irq,
                                        queue = OBJ(machine + "cpu0"),
                                        recorder = OBJ(machine + "rec0"))]
        if use_console2:
            object_list[machine] += [OBJECT(machine + "com3_con", "text-console",
                                            title = machine + "com3 console",
                                            width = 80,
                                            height = 25,
                                            queue = OBJ(machine + "cpu0"),
                                            device = OBJ(machine + "com3"))]
            set_attribute(object_list[machine], machine + "com3", "console", OBJ(machine + "com3_con"))
    if num_ports > 3:
        object_list[machine] += [OBJECT(machine + "com4", uart_class,
                                        irq_dev = OBJ(machine + "isa0"),
                                        irq_level = com4_irq,
                                        queue = OBJ(machine + "cpu0"),
                                        recorder = OBJ(machine + "rec0"))]
        if use_console3:
            object_list[machine] += [OBJECT(machine + "com4_con", "text-console",
                                            title = machine + "com4 console",
                                            width = 80,
                                            height = 25,
                                            queue = OBJ(machine + "cpu0"),
                                            device = OBJ(machine + "com4"))]
            set_attribute(object_list[machine], machine + "com4", "console", OBJ(machine + "com4_con"))

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x3f8, OBJ(machine + "com1"), 1, 0, 1],
            [0x3f9, OBJ(machine + "com1"), 1, 1, 1],
            [0x3fa, OBJ(machine + "com1"), 1, 2, 1],
            [0x3fb, OBJ(machine + "com1"), 1, 3, 1],
            [0x3fc, OBJ(machine + "com1"), 1, 4, 1],
            [0x3fd, OBJ(machine + "com1"), 1, 5, 1],
            [0x3fe, OBJ(machine + "com1"), 1, 6, 1],
            [0x3ff, OBJ(machine + "com1"), 1, 7, 1]]
    if num_ports > 1:
        map += [[0x2f8, OBJ(machine + "com2"), 2, 0, 1],
                [0x2f9, OBJ(machine + "com2"), 2, 1, 1],
                [0x2fa, OBJ(machine + "com2"), 2, 2, 1],
                [0x2fb, OBJ(machine + "com2"), 2, 3, 1],
                [0x2fc, OBJ(machine + "com2"), 2, 4, 1],
                [0x2fd, OBJ(machine + "com2"), 2, 5, 1],
                [0x2fe, OBJ(machine + "com2"), 2, 6, 1],
                [0x2ff, OBJ(machine + "com2"), 2, 7, 1]]
    if num_ports > 2:
        map += [[0x3e8, OBJ(machine + "com3"), 3, 0, 1],
                [0x3e9, OBJ(machine + "com3"), 3, 1, 1],
                [0x3ea, OBJ(machine + "com3"), 3, 2, 1],
                [0x3eb, OBJ(machine + "com3"), 3, 3, 1],
                [0x3ec, OBJ(machine + "com3"), 3, 4, 1],
                [0x3ed, OBJ(machine + "com3"), 3, 5, 1],
                [0x3ee, OBJ(machine + "com3"), 3, 6, 1],
                [0x3ef, OBJ(machine + "com3"), 3, 7, 1]]
    if num_ports > 3:
        map += [[0x2e8, OBJ(machine + "com4"), 4, 0, 1],
                [0x2e9, OBJ(machine + "com4"), 4, 1, 1],
                [0x2ea, OBJ(machine + "com4"), 4, 2, 1],
                [0x2eb, OBJ(machine + "com4"), 4, 3, 1],
                [0x2ec, OBJ(machine + "com4"), 4, 4, 1],
                [0x2ed, OBJ(machine + "com4"), 4, 5, 1],
                [0x2ee, OBJ(machine + "com4"), 4, 6, 1],
                [0x2ef, OBJ(machine + "com4"), 4, 7, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_legacy_floppy(num_drives = 1, irq_num = 6, floppy_dma = 2):

    if configuration_loaded("add_legacy_floppy"):
        return

    if object_exists(object_list[machine], machine + "flp0"):
        handle_error("Legacy floppy drives already added")
        return

    if num_drives > 2:
        handle_error("Only 2 legacy floppy drives supported")
        return

    num_floppies[machine] = num_drives

    object_list[machine] += ([OBJECT(machine + "flp0", "i82077",
                                     irq_dev = OBJ(machine + "isa0"),
                                     irq_level = irq_num,
                                     dma_dev = OBJ(machine + "dma0"),
                                     dma_channel = floppy_dma,
                                     drives = [OBJ(machine + "fd0"),
                                               OBJ(machine + "fd1")],
                                     queue = OBJ(machine + "cpu0"))] +
                             [OBJECT(machine + "fd0", "floppy-drive")] +
                             [OBJECT(machine + "fd1", "floppy-drive")])

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x3f2, OBJ(machine + "flp0"), 0, 0, 1],
            [0x3f4, OBJ(machine + "flp0"), 0, 2, 1],
            [0x3f5, OBJ(machine + "flp0"), 0, 3, 1],
            [0x3f7, OBJ(machine + "flp0"), 0, 5, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)

def add_vga_bios(vga_bios, bios_size):
    global num_gfx_consoles

    files = get_attribute(object_list[machine], machine + "rom0_image", "files")
    files += [[vga_bios, 1, max_rombios_size, bios_size]]
    set_attribute(object_list[machine], machine + "rom0_image", "files", files)

    id = num_gfx_consoles[machine]

    if id == 0:
        # vga bios
        map = get_attribute(object_list[machine], machine + "pci_mem0", "map")
        map += [[0xC0000, OBJ(machine + "rom0"), 0, max_rombios_size, bios_size]]
        set_attribute(object_list[machine], machine + "pci_mem0", "map", map)

def add_vga_generic(gfx_console, text_console, video_interface, mem_space=None, port_space=None):
    global num_gfx_consoles

    if not mem_space:
        mem_space = machine + "pci_mem0"
    if not port_space:
        port_space = machine + "port_mem0"

    id = num_gfx_consoles[machine]

    if id == 0:
        # vga memory
        map = get_attribute(object_list[machine], mem_space, "map")
        map += [[0x000A0000, OBJ(machine + "vga0"), 1, 0x0000, 128*1024]]
        set_attribute(object_list[machine], mem_space, "map", map)
        set_attribute(object_list[machine], machine + "vga0", "memory-space", OBJ(mem_space))

    if text_console == 1:
        object_list[machine] += [OBJECT(machine + "con" + `id`, "xterm-console",
                                        title = "Simics Console",
                                        width = 80, height = 25,
                                        queue = OBJ(machine + "cpu0"))]
    elif gfx_console == 1:
        object_list[machine] += [OBJECT(machine + "con" + `id`, "gfx-console",
                                        x__size = 720,
                                        y__size = 400,
                                        queue = OBJ(machine + "cpu0"))]
    if text_console == 1:
        if id == 0:
            set_attribute(object_list[machine], machine + "kbd0", "console", OBJ(machine + "con0"))
        set_attribute(object_list[machine], machine + "con" + `id`, "device", OBJ(machine + "kbd0"))
        set_attribute(object_list[machine], machine + "vga" + `id`, "console", OBJ(machine + "con" + `id`))
    elif gfx_console == 1:
        if id == 0:
            set_attribute(object_list[machine], machine + "kbd0", "console", OBJ(machine + "con0"))
        set_attribute(object_list[machine], machine + "con" + `id`, "keyboard", OBJ(machine + "kbd0"))
        set_attribute(object_list[machine], machine + "con" + `id`, "mouse", OBJ(machine + "kbd0"))
        set_attribute(object_list[machine], machine + "vga" + `id`, "console", OBJ(machine + "con" + `id`))
        if video_interface == 1:
            set_attribute(object_list[machine], machine + "con" + `id`, "video", OBJ(machine + "vga" + `id`))

    num_gfx_consoles[machine] += 1

    if id == 0:
        map = get_attribute(object_list[machine], port_space, "map")
        map += [[0x3c0, OBJ(machine + "vga0"), 0, 0x3c0, 1],
                [0x3c1, OBJ(machine + "vga0"), 0, 0x3c1, 1],
                [0x3c2, OBJ(machine + "vga0"), 0, 0x3c2, 1],
                [0x3c4, OBJ(machine + "vga0"), 0, 0x3c4, 1],
                [0x3c5, OBJ(machine + "vga0"), 0, 0x3c5, 1],
                [0x3c6, OBJ(machine + "vga0"), 0, 0x3c6, 1],
                [0x3c7, OBJ(machine + "vga0"), 0, 0x3c7, 1],
                [0x3c8, OBJ(machine + "vga0"), 0, 0x3c8, 1],
                [0x3c9, OBJ(machine + "vga0"), 0, 0x3c9, 1],
                [0x3cc, OBJ(machine + "vga0"), 0, 0x3cc, 1],
                [0x3ce, OBJ(machine + "vga0"), 0, 0x3ce, 1],
                [0x3cf, OBJ(machine + "vga0"), 0, 0x3cf, 1],
                [0x3da, OBJ(machine + "vga0"), 0, 0x3da, 1],
                [0x3ba, OBJ(machine + "vga0"), 0, 0x3ba, 1],
                [0x3b4, OBJ(machine + "vga0"), 0, 0x3b4, 1],
                [0x3b5, OBJ(machine + "vga0"), 0, 0x3b5, 1],
                [0x3d4, OBJ(machine + "vga0"), 0, 0x3d4, 1],
                [0x3d5, OBJ(machine + "vga0"), 0, 0x3d5, 1]]
        set_attribute(object_list[machine], port_space, "map", map)

if not "isa_vga_bios" in dir(): isa_vga_bios = "VGABIOS-elpin-2.20"
if not "isa_vga_bios_size" in dir(): isa_vga_bios_size = 32768

def add_isa_vga(gfx_console = 1, text_console = 0):

    if configuration_loaded("add_isa_vga"):
        return

    if gfx_console == 1 and text_console == 1:
        handle_error("Cannot use both text and graphics console at once")
        return

    if have_isa_vga[machine] == 1:
        handle_error("Cannot add ISA VGA: Only one device supported")
        return

    have_isa_vga[machine] = 1

    object_list[machine] += [OBJECT(machine + "vga0_image", "image",
                                    size = 0x40000),
                             OBJECT(machine + "vga0", "vga",
                                    image = OBJ(machine + "vga0_image"),
                                    queue = OBJ(machine + "cpu0"))]

    add_vga_bios(vga_bios = isa_vga_bios, bios_size = isa_vga_bios_size)
    add_vga_generic(gfx_console, text_console, video_interface = 1)


def add_isa_lance(mac_address, lance_irq = 7, lance_dml_module = 0):

    if configuration_loaded("add_isa_lance"):
        return

    if object_exists(object_list[machine], machine + "lance0"):
        handle_error("Only one ISA lance supported")
        return

    if lance_dml_module == 1:
        object_list[machine] += [OBJECT(machine + "lance0", "AM79C960_dml",
                                        irq_dev = OBJ(machine + "isa0"),
                                        irq_level = lance_irq,
                                        memory = OBJ(machine + "pci_mem0"),
                                        queue = OBJ(machine + "cpu0"))]
    else:
        object_list[machine] += [OBJECT(machine + "lance0", "AM79C960",
                                        irq_dev = OBJ(machine + "isa0"),
                                        irq_level = lance_irq,
                                        memory = OBJ(machine + "pci_mem0"),
                                        mac__address = mac_address,
                                        recorder = OBJ(machine + "rec0"),
                                        queue = OBJ(machine + "cpu0"))]

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x300, OBJ(machine + "lance0"), 0, 0x00, 1],
            [0x301, OBJ(machine + "lance0"), 0, 0x01, 1],
            [0x302, OBJ(machine + "lance0"), 0, 0x02, 1],
            [0x303, OBJ(machine + "lance0"), 0, 0x03, 1],
            [0x304, OBJ(machine + "lance0"), 0, 0x04, 1],
            [0x305, OBJ(machine + "lance0"), 0, 0x05, 1],
            [0x306, OBJ(machine + "lance0"), 0, 0x06, 1],
            [0x307, OBJ(machine + "lance0"), 0, 0x07, 1],
            [0x308, OBJ(machine + "lance0"), 0, 0x08, 1],
            [0x309, OBJ(machine + "lance0"), 0, 0x09, 1],
            [0x30a, OBJ(machine + "lance0"), 0, 0x0a, 1],
            [0x30b, OBJ(machine + "lance0"), 0, 0x0b, 1],
            [0x30c, OBJ(machine + "lance0"), 0, 0x0c, 1],
            [0x30d, OBJ(machine + "lance0"), 0, 0x0d, 1],
            [0x30e, OBJ(machine + "lance0"), 0, 0x0e, 1],
            [0x30f, OBJ(machine + "lance0"), 0, 0x0f, 1],
            [0x310, OBJ(machine + "lance0"), 0, 0x10, 2],
            [0x312, OBJ(machine + "lance0"), 0, 0x12, 2],
            [0x314, OBJ(machine + "lance0"), 0, 0x14, 2],
            [0x316, OBJ(machine + "lance0"), 0, 0x16, 2]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_isa_sb16(dsp_dev = "dsp.bin", sb_irq = 5, sb8_dma = 1, sb16_dma = 5):

    if configuration_loaded("add_isa_sb16"):
        return

    if object_exists(object_list[machine], machine + "sb0"):
        handle_error("Only one ISA lance supported")
        return

    object_list[machine] += [OBJECT(machine + "sb0", "sb16",
                                    queue = OBJ(machine + "cpu0"),
                                    irq_dev = OBJ(machine + "isa0"),
                                    irq_level = sb_irq,
                                    dma_dev = OBJ(machine + "dma0"),
                                    dma_channel_8 = sb8_dma,
                                    dma_channel_16 = sb16_dma,
                                    dsp_dev = dsp_dev)]

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x220, OBJ(machine + "sb0"), 0, 0x0, 1],
            [0x221, OBJ(machine + "sb0"), 0, 0x1, 1],
            [0x222, OBJ(machine + "sb0"), 0, 0x2, 1],
            [0x223, OBJ(machine + "sb0"), 0, 0x3, 1],
            [0x224, OBJ(machine + "sb0"), 0, 0x4, 1],
            [0x225, OBJ(machine + "sb0"), 0, 0x5, 1],
            [0x226, OBJ(machine + "sb0"), 0, 0x6, 1],
            [0x227, OBJ(machine + "sb0"), 0, 0x7, 1],
            [0x228, OBJ(machine + "sb0"), 0, 0x8, 1],
            [0x229, OBJ(machine + "sb0"), 0, 0x9, 1],
            [0x22a, OBJ(machine + "sb0"), 0, 0xa, 1],
            [0x22c, OBJ(machine + "sb0"), 0, 0xc, 1],
            [0x22e, OBJ(machine + "sb0"), 0, 0xe, 1],
            [0x22f, OBJ(machine + "sb0"), 0, 0xf, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_isa_ide(num_controllers, primary_irq = 14, secondary_irq = 15):

    if configuration_loaded("add_isa_ide"):
        return

    if num_controllers > 2:
        handle_error("More that 2 ISA IDE controllers is not supported")
        return

    if num_controllers < 1:
        return

    if object_exists(object_list[machine], machine + "ide0"):
        handle_error("ISA IDE controllers already added")
        return

    object_list[machine] += [OBJECT(machine + "ide0", "ide",
                                    irq_dev = OBJ(machine + "isa0"),
                                    irq_level = primary_irq,
                                    primary = 1,
                                    interrupt_delay = 1.0e-5,
                                    queue = OBJ(machine + "cpu0"))]
    if num_controllers > 1:
        object_list[machine] += [OBJECT(machine + "ide1", "ide",
                                        irq_dev = OBJ(machine + "isa0"),
                                        irq_level = secondary_irq,
                                        primary = 0,
                                        interrupt_delay = 1.0e-5,
                                        queue = OBJ(machine + "cpu0"))]

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x1f0, OBJ(machine + "ide0"), 0, 0x0, 4],
            [0x1f1, OBJ(machine + "ide0"), 0, 0x1, 1],
            [0x1f2, OBJ(machine + "ide0"), 0, 0x2, 1],
            [0x1f3, OBJ(machine + "ide0"), 0, 0x3, 1],
            [0x1f4, OBJ(machine + "ide0"), 0, 0x4, 1],
            [0x1f5, OBJ(machine + "ide0"), 0, 0x5, 1],
            [0x1f6, OBJ(machine + "ide0"), 0, 0x6, 1],
            [0x1f7, OBJ(machine + "ide0"), 0, 0x7, 1],
            [0x3f6, OBJ(machine + "ide0"), 0, 0x8, 1]]

    if num_controllers > 1:
        map += [[0x170, OBJ(machine + "ide1"), 0, 0x0, 4],
                [0x171, OBJ(machine + "ide1"), 0, 0x1, 1],
                [0x172, OBJ(machine + "ide1"), 0, 0x2, 1],
                [0x173, OBJ(machine + "ide1"), 0, 0x3, 1],
                [0x174, OBJ(machine + "ide1"), 0, 0x4, 1],
                [0x175, OBJ(machine + "ide1"), 0, 0x5, 1],
                [0x176, OBJ(machine + "ide1"), 0, 0x6, 1],
                [0x177, OBJ(machine + "ide1"), 0, 0x7, 1],
                [0x376, OBJ(machine + "ide1"), 0, 0x8, 1]]

    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_isa_ide_disk(controller, slot, size, geometry = None, files = ""):
    global num_disks, bios_geometry

    if configuration_loaded("add_isa_ide_disk"):
        return

    if not object_exists(object_list[machine], machine + "ide" + `controller`):
        handle_error("Trying to add IDE disk to non-existing controller %d" % controller)
        return

    ide_chip = machine + "ide" + `controller`
    disk_name = machine + "disk" + `num_disks[machine]`

    num_disks[machine] += 1

    if slot == "master":
        set_attribute(object_list[machine], ide_chip, "master", OBJ(disk_name))
        slot_no = 0
    elif slot == "slave":
        set_attribute(object_list[machine], ide_chip, "slave", OBJ(disk_name))
        slot_no = 1
    else:
        handle_error("Trying to add IDE disk to non-existing IDE slot %s" % slot)
        return

    # to override bios geometry, use the 'rtc0.cmos-hd' command
    # our BIOS does LBA directly: set sectors to 63 and heads a multiple of 16
    bios_S = 63

    #TODO: finish the geometry stuff soon...

    # the following would probably work if our BIOS did "translation"
    # now it seems to fail miserably

    #if size < 504L * 1024 * 1024:
    #    bios_H = 16
    #elif size < 1008L * 1024 * 1024:
    #    bios_H = 32
    #elif size < 2016L * 1024 * 1024:
    #    bios_H = 64
    #elif size < 4032L * 1024 * 1024:
    #    bios_H = 128

    # Limit at 4GB or 8GB?
    if size < 4032L * 1024 * 1024:
        bios_H = 16
    else:
        # 255 is de facto standard since DOS and early Windows can't handle 256 heads
        # this is known as the 4GB limit
        bios_H = 255
    bios_C = size / (bios_H * bios_S * 512)
    #if bios_C * bios_H * bios_S * 512 != size:
    #    print "add_isa_ide_disk(): Warning disk size can not be translated to exact BIOS CHS"
    #    print "                    Using %d %d %d" % (bios_C, bios_H, bios_S)
    bios_geometry[machine][controller][slot_no] = [bios_C, bios_H, bios_S]

    if geometry:
        if type([1,2]) != type(geometry) or len(geometry) != 3:
            handle_error("Illegal geometry specification for IDE disk")
            return
        # allow user to override IDE geometry
        ide_S = geometry[2]
        ide_H = geometry[1]
        ide_C = geometry[0]
    else:
        ide_S = 63
        ide_H = 16
        ide_C =  size / (ide_H * ide_S * 512)
        if ide_C > 16383:
            # set 16363x63x16 for disks larger than 8GB
            ide_C = 16383
    if ide_C < 16383 and ide_C * ide_H * ide_S * 512 != size:
        print "add_isa_ide_disk(): Warning disk size can not be translated to exact IDE CHS"
        print "                    Using %d %d %d" % (ide_C, ide_H, ide_S)

    object_list[machine] += ([OBJECT(disk_name, "ide-disk",
                                     disk_sectors = size / 512,
                                     disk_cylinders = ide_C,
                                     disk_heads = ide_H,
                                     disk_sectors_per_track = ide_S,
                                     image = OBJ(disk_name + "_image"))] +
                             [OBJECT(disk_name + "_image", "image",
                                     queue = OBJ(machine + "cpu0"),
                                     size = size)])
    if files != "":
        set_attribute(object_list[machine], disk_name + "_image", "files", files)


def add_isa_ide_cdrom(controller, slot, file = ""):
    global num_cdroms

    if configuration_loaded("add_isa_ide_cdrom"):
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


def add_le_object(all_objs):
    all_objs += [OBJECT("le_perm0", "le-permissions",
                        module__list = [["AM79C960", 1],
                                        ["DEC21143", 1],
                                        ["DS12887", 1],
                                        ["io-apic", "inf"],
                                        ["NS16450", 2],
                                        ["SYM53C810", "inf"],
                                        ["apic", le_max_processors],
                                        ["apic-bus", 1],
                                        ["apm", 1],
                                        ["dummy-component", 1],
                                        ["floppy-drive", 4],
                                        ["i8042", 1],
                                        ["i82077", 1],
                                        ["i8237x2", 1],
                                        ["i82443bx", 1],
                                        ["i82443bx_agp", 1],
                                        ["i8254", 2],
                                        ["i8259x2", 1],
                                        ["ide", "inf"],
                                        ["ide-cdrom", "inf"],
                                        ["ide-disk", "inf"],
                                        ["ISA", 1],
                                        ["pc-shadow", 1],
                                        ["pci-bus", 2],
                                        ["piix4_ide", 1],
                                        ["piix4_isa", 1],
                                        ["piix4_usb", 1],
                                        ["piix4_power", 1],
                                        ["ram", 1],
                                        ["ram", "mapped_size", "le", 512 * 1024 * 1024],
                                        ["rom", 2],
                                        ["scsi-bus", "inf"],
                                        ["scsi-cdrom", "inf"],
                                        ["scsi-disk", "inf"],
                                        ["set-memory", "inf"],
                                        ["vga", 1],
                                        ["voodoo3", 1],
                                        ["voodoo3-agp", 1],
                                        [x86_class_name.values()[0], le_max_processors],
                                        ["hostfs", "inf"],
                                        ["pc-config", "inf"],
                                        ["context", "inf"],
                                        ["exdi", "inf"],
                                        ["file-cdrom", "inf"],
                                        ["gdb-remote", "inf"],
                                        ["gfx-console", "inf"],
                                        ["host-cdrom", "inf"],
                                        ["host-serial", "inf"],
                                        ["image", "inf"],
                                        ["memory-space", "inf"],
                                        ["port-space", "inf"],
                                        ["python", "inf"],
                                        ["recorder", "inf"],
                                        ["sim", "inf"],
                                        ["simscrit", "inf"],
                                        ["symtable", "inf"],
                                        ["trace-mem-hier", "inf"],
                                        ["base-trace-mem-hier", "inf"],
                                        ["xterm-console", "inf"],
                                        ["x87_exception", "inf"],
                                        ["tlb0", "inf"],
                                        ["x86-reset-bus", "inf"],
                                        ["x86-tlb", "inf"]
                                        ])]

def get_highest_2exp(i):
	for b in range(63, -1, -1):
		if (1L << b) <= i:
			return 1L << b
	return 0

def calc_mtrr_mask(classname, size):
	return (~(size - 1)) & ((1L << SIM_get_class_attribute(classname, "physical_bits")) - 1)

def get_configuration():
    global machine
    for mach in machine_list:
        machine = mach
        try:
            if object_exists(object_list[machine], machine + "ide0"):
                get_attribute(object_list[machine], machine + "ide0", "master")
        except:
            handle_error("The IDE controller %s needs a 'master' disk or CD-ROM" % (machine + "ide0"))
            return
        try:
            if object_exists(object_list[machine], machine + "ide1"):
                get_attribute(object_list[machine], machine + "ide1", "master")
        except:
            handle_error("The IDE controller %s needs a 'master' disk or CD-ROM" % (machine + "ide1"))
            return
        if have_north_bridge[machine] and not have_south_bridge[machine]:
            handle_error("Configurations with a north bridge also needs a south bridge")
            return
        # add reset targets to the keyboard device if it exists
        if (object_exists(object_list[machine], machine + "reset0")
            and object_exists(object_list[machine], machine + "kbd0")):
            set_attribute(object_list[machine], machine + "reset0",
                          "reset_targets",
                          [OBJ(machine + "cpu" + `i`) for i in range(num_cpu[mach])])
            set_attribute(object_list[machine], machine + "kbd0",
                          "reset_target",
                          OBJ(machine + "reset0"))
        # set MTRR if available
        for i in range(num_cpu[machine]):
            if not SIM_class_has_attribute(x86_class_name[machine], "mtrr_def_type"):
                pass
            else:
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_def_type", 0xc00)
                megs_remaining = total_megs[machine]
                next_mtrr = 0
                next_base = 0L
                while megs_remaining:
                    if next_mtrr > 7:
                        print "Warning: %d megabytes of memory not happed by MTRRs" % megs_remaining
                        break
                    this_size = get_highest_2exp(megs_remaining)
                    set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_base%d" % next_mtrr, next_base | 0x06)
                    mask = calc_mtrr_mask(x86_class_name[machine], this_size * 1024L * 1024L)
                    set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_mask%d" % next_mtrr, mask | 0x800)
                    megs_remaining = megs_remaining - this_size
                    next_base = next_base + this_size * 1024 * 1024
                    next_mtrr = next_mtrr + 1
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_64k_00000", 0x0606060606060606L)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_16k_80000", 0x0606060606060606L)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_16k_a0000", 0)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_4k_c0000", 0)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_4k_c8000", 0)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_4k_d0000", 0)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_4k_d8000", 0)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_4k_f0000", 0)
                set_attribute(object_list[machine], machine + "cpu" + `i`, "mtrr_fix_4k_f8000", 0)

    all_objs = []
    for mach in machine_list:
        machine = mach
        all_objs += object_list[machine]
    return all_objs

def post_configuration():
    global machine
    for mach in machine_list:
        machine = mach
        # if we have a pic0 it is a legacy system
        if object_exists(object_list[machine], machine + "pic0") and initialize_cmos[machine]:
            eval_cli_line(machine + "rtc0.cmos-init")
            if num_floppies[machine] > 0:
                eval_cli_line(machine + "rtc0.cmos-floppy A \"1.44\"")
            if num_floppies[machine] > 1:
                eval_cli_line(machine + "rtc0.cmos-floppy B \"1.44\"")
            # time & date
            eval_cli_line(machine + "rtc0.set-date-time year=%d month=%d mday=%d hour=%d minute=%d second=%d" % (
                rtc_date[machine][0], rtc_date[machine][1], rtc_date[machine][2],
                rtc_date[machine][3], rtc_date[machine][4], rtc_date[machine][5]))
            # memory
            eval_cli_line(machine + "rtc0.cmos-base-mem 640")
            eval_cli_line(machine + "rtc0.cmos-extended-mem %d" % (total_megs[machine] - 1))
            # harddisk info
            c_geom = [0, 0, 0]
            d_geom = [0, 0, 0]
            for c in [0, 1]:
                for s in [0, 1]:
                    if (c_geom == [0, 0, 0]) and (bios_geometry[machine][c][s] != [0, 0, 0]):
                        c_geom = bios_geometry[machine][c][s]
                    elif (d_geom == [0, 0, 0]) and (bios_geometry[machine][c][s] != [0, 0, 0]):
                        d_geom = bios_geometry[machine][c][s]
            eval_cli_line(machine + "rtc0.cmos-hd C %d %d %d" % (c_geom[0],
                                                                 c_geom[1],
                                                                 c_geom[2]))
            # bios can only handle 1 disk currently
            # eval_cli_line(machine + "rtc0.cmos-hd D %d %d %d" % (d_geom[0],
            #                                                      d_geom[1],
            #                                                      d_geom[2]))
            eval_cli_line(machine + "rtc0.cmos-boot-dev %s" % boot_device[machine])
        elif not object_exists(object_list[machine], machine + "pic0"):
            print "Warning: no legacy devices added - are you sure this is what you want?"

    for mach in machine_list:
        if ioapic_present[mach]:
            id = get_attribute(object_list[mach], mach + "ioapic0", "ioapic_id") >> 24
        else:
            id = 0
        if create_mem_map[mach]:
            create_acpi_tables(build_acpi_tables = acpi_machine[mach],
                               cpu_base = mach + "cpu", num_cpus = num_cpu[mach],
                               megs = total_megs[mach], ioapic_id = id,
                               user_rsdp_address = iff(acpi_bug_workaround_present[machine], 0xef000, 0))

def finish_configuration(global_objs):

    try:
        all_objs = get_configuration() + global_objs

        try:
            if conf.sim.le_license or show_le_checksum:
                add_le_object(all_objs)
        except AttributeError:
            pass

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

    if show_le_checksum:
        print "Checksum of LE permissions object is:"
        eval_cli_line("le-checksum")

    post_configuration()
