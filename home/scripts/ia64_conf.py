
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

object_list = {}      # per node

machine_list = []     # global
have_sim_object = 0   # global

machine = ""

SIM_source_python_in_module("../scripts/pci_conf.py", __name__)

if not SIM_get_quiet():
    print
    print "Machines based on ia64_conf.py are only provided for backward "
    print "compatibility. The new component based machines in simics/targets/"
    print "are recommended instead."
    print

def handle_error(msg):
    print
    print "IA64 configuration error:"
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

conf_list = []

def set_machine(mach):
    global machine, conf_list
    machine = mach
    try:
        conf_list = object_list[machine]
    except:
        pass

def create_system(num_cpus, mhz, mb, cpu_class = "ia64-itanium", use_hostfs = 1, num_pci_buses = 1):
    global machine_list, num_cpu

    if configuration_loaded("create_system"):
        return

    if num_cpus < 1:
        handle_error("At least one cpu must be created")
        return

    if num_pci_buses < 1:
	handle_error("At least one pci bus must be created")
        return

    machine_list += [machine]

    # The variable PCI gap contains memory mapped I/O spaces for all the
    # PCI buses.  The first PCI bus uses the highest a*32MB, the second
    # bus, the next b*32MB, going downwards.  The bottom of the gap must
    # be 64MB aligned, which means that an odd number of 32MB chunks are
    # allocated.
    #
    # We  allocate 64MB for each bus.  This will leave the bottom
    # unaligned, but who cares.
    gap_chunksize = 0x4000000
    pci_gap = [[0xfe000000L - (i+1)*gap_chunksize, OBJ(machine + "sac"), 3, 0, gap_chunksize, OBJ(machine + "pci"+`i`+"-memory")]
	       for i in range(num_pci_buses)]
    
    ipi_block = [[0xfee00000L + i*0x1000, OBJ(machine + "cpu"+`i`), 1, 0, 0x100] for i in range(num_cpus)]
    pal_block = [[0xFF000000L + i*0x100,  OBJ(machine + "cpu"+`i`), 0, 0, 0x100] for i in range(num_cpus)]

    pid_map = [[0x00000000FEC00000L, OBJ(machine + "pid"), 0, 0, 0x1000]]
    io_map  = [[0x00000FFFFC000000L, OBJ(machine + "sac"),  0,  0, 0x4000000, OBJ(machine + "io-space")]]

    firmware_map = [[0x00000000FF800000L, OBJ(machine + "firmware"), 0, 0, 0x800000]]

    if memory_megs > 2048:
        ram_map = [[0x0000000000000000L, OBJ(machine + "ram0"), 0, 0, 0xA0000],
                   [0x00000000000C0000L, OBJ(machine + "ram0"), 0, 0xC0000, 0x80000000L - 0xC0000],
                   [0x0000000100000000L, OBJ(machine + "ram0"), 0, 0x80000000L,
                    memory_megs*1048576 - 0x80000000L]]
    else:
        ram_map = [[0x0000000000000000L, OBJ(machine + "ram0"), 0, 0, 0xA0000],
		   [0x00000000000C0000L, OBJ(machine + "ram0"), 0, 0xC0000, memory_megs * 1048576 - 0xC0000]]
    
    object_list[machine] = ([OBJECT(machine + "cpu" + `i`, cpu_class,
				    queue = OBJ(machine + "cpu" + `i`),
				    freq_mhz = mhz,
				    proc__ratio = [1, 1],
				    itc__ratio = [1, 1],
				    physical_memory = OBJ(machine + "phys_mem0"))
			     for i in range(num_cpus)] +
			    [OBJECT(machine + "pci_bus"+`i`, "pci-bus",
				    queue = OBJ(machine + "cpu0"),
				    bridge = OBJ(machine + "sac"),
				    interrupt = OBJ(machine + "pid"),
				    memory_space = OBJ(machine + "pci"+`i`+"-memory"),
				    io_space = OBJ(machine + "pci"+`i`+"-io"),
				    conf_space = OBJ(machine + "pci"+`i`+"-conf"),
				    pci_devices = [])
			     for i in range(num_pci_buses)] +
			    [OBJECT(machine + "pci"+`i`+"-memory", "memory-space",
				    map = [])
			     for i in range(num_pci_buses)] +
			    [OBJECT(machine + "pci"+`i`+"-io", "memory-space")
			     for i in range(num_pci_buses)] +
			    [OBJECT(machine + "pci"+`i`+"-conf", "memory-space")
			     for i in range(num_pci_buses)] +
			    [OBJECT(machine + "phys_mem0", "memory-space",
				    map = pid_map + io_map + pci_gap + ipi_block + pal_block + ram_map + firmware_map)] +
			    [OBJECT(machine + "io-space", "memory-space",
				    map = [[0x00000000L, OBJ(machine + "lpc-port-space"), 0, 0, 0xcf8],
					   [0x00000CF8L, OBJ(machine + "sac"),            0, 0, 0x008],
					   [0x00001000L, OBJ(machine + "pci_bus0"),       1, 0, 0x1000000]])] +
			    [OBJECT(machine + "sapic-bus0", "sapic-bus",
				    sapics = [OBJ(machine + "cpu"+`i`) for i in range(num_cpus)],
				    iosapic = OBJ(machine + "pid"))] +
			    [OBJECT(machine + "pid", "uPD66566S1016",
				    pci_bus = OBJ(machine + "pci_bus0"),
				    sapic_bus = OBJ(machine + "sapic-bus0"),
				    # this is hopefully the same routing table as
				    # \_SB_.PCI0._PRT of the DSDT of godzilla
				    pci__rt = [[1, -1, 0, 0x23],
					       [1, -1, 1, 0x22],
					       [1, -1, 2, 0x21],
					       [1, -1, 3, 0x20],
					       [2, -1, 0, 0x27],
					       [2, -1, 1, 0x26],
					       [2, -1, 2, 0x25],
					       [2, -1, 3, 0x24],
					       [4, -1, 0, 0x2B],
					       [4, -1, 1, 0x2A],
					       [4, -1, 2, 0x29],
					       [4, -1, 3, 0x28],
					       [3, -1, 0, 0x2E],
					       [3, -1, 1, 0x2E],
					       [3, -1, 2, 0x2F],
					       [3, -1, 3, 0x2F]])] +			     
			    [OBJECT(machine + "ifb-0", "i82468GX_0",
				    iosapic = OBJ(machine + "pid"),
				    pci_bus = OBJ(machine + "pci_bus0"))] +
			    [OBJECT(machine + "lpc-port-space", "port-space",
				    map = [[0x40, OBJ(machine + "pit0"), 0, 0, 1],
					   [0x41, OBJ(machine + "pit0"), 0, 1, 1],
					   [0x42, OBJ(machine + "pit0"), 0, 2, 1],
					   [0x43, OBJ(machine + "pit0"), 0, 3, 1],
					   [0x60, OBJ(machine + "kbd0"), 0, 0, 1],
					   [0x64, OBJ(machine + "kbd0"), 0, 4, 1],
					   [0x70, OBJ(machine + "rtc0"), 0, 0, 1],
					   [0x71, OBJ(machine + "rtc0"), 0, 1, 1],
					   [0x3f8, OBJ(machine + "com1"), 1, 0, 1],
					   [0x3f9, OBJ(machine + "com1"), 1, 1, 1],
					   [0x3fa, OBJ(machine + "com1"), 1, 2, 1],
					   [0x3fb, OBJ(machine + "com1"), 1, 3, 1],
					   [0x3fc, OBJ(machine + "com1"), 1, 4, 1],
					   [0x3fd, OBJ(machine + "com1"), 1, 5, 1],
					   [0x3fe, OBJ(machine + "com1"), 1, 6, 1],
					   [0x3ff, OBJ(machine + "com1"), 1, 7, 1],
					   [0x2f8, OBJ(machine + "com2"), 2, 0, 1],
					   [0x2f9, OBJ(machine + "com2"), 2, 1, 1],
					   [0x2fa, OBJ(machine + "com2"), 2, 2, 1],
					   [0x2fb, OBJ(machine + "com2"), 2, 3, 1],
					   [0x2fc, OBJ(machine + "com2"), 2, 4, 1],
					   [0x2fd, OBJ(machine + "com2"), 2, 5, 1],
					   [0x2fe, OBJ(machine + "com2"), 2, 6, 1],
					   [0x2ff, OBJ(machine + "com2"), 2, 7, 1]])] + 
			    [OBJECT(machine + "pit0", "i8254",
				    irq_dev = OBJ(machine + "ifb-0"),
				    irq_level = 0,
				    gate = [1, 1, 0, 0],
				    out = [1, 1, 1, 0],
				    queue = OBJ(machine + "cpu0"))] +
			    [OBJECT(machine + "rtc0", "DS12887",
				    irq_dev = OBJ(machine + "cpu0"),
				    irq_level = 8,
				    queue = OBJ(machine + "cpu0"))] +
			    [OBJECT(machine + "sac", "i82461GX",
				    physical__memory = OBJ(machine + "phys_mem0"),
				    io__space = OBJ(machine + "io-space"),
				    pci__buses = [[OBJ(machine + "pci_bus"+`i`), 0] for i in range(num_pci_buses)])] +
			    [OBJECT(machine + "ram0", "ram",
				    image = OBJ(machine + "mem0_image"))] +
			    [OBJECT(machine + "mem0_image", "image",
				    queue = OBJ(machine + "cpu0"),
				    size = memory_megs * 1024L * 1024L)] +
			    [OBJECT(machine + "rec0", "recorder")] +
			    [OBJECT(machine + "sim", "sim", icode_dump_freq = 6000000000L)] +
			    [OBJECT(machine + "kbd0", "i8042",
				    irq_dev = OBJ(machine + "ifb-0"),
				    kbd_irq_level = 1,
				    mouse_irq_level = 12,
				    recorder = OBJ(machine + "rec0"),
				    queue = OBJ(machine + "cpu0"))] +
			    [OBJECT(machine + "firmware", "ram",
				    image = OBJ(machine + "firmware_image"))] +
			    [OBJECT(machine + "firmware_image", "image",
				    queue = OBJ(machine + "cpu0"),
				    size = 8 * 1024L * 1024L)] +
			    [OBJECT(machine + "com1", "NS16550",
                                irq_dev = OBJ(machine + "ifb-0"),
                                irq_level = 4,
                                queue = OBJ(machine + "cpu0"),
                                recorder = OBJ(machine + "rec0"),
                                target_pace_receive = 1)] +
			    [OBJECT(machine + "com2", "NS16550",
                                irq_dev = OBJ(machine + "ifb-0"),
                                irq_level = 3,
                                recorder = OBJ(machine + "rec0"),
                                queue = OBJ(machine + "cpu0"))])
	    
    #if use_hostfs == 1:
    #    object_list[machine] += [OBJECT(machine + "hfs0", "hostfs")]
    #	phys_map = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    #   phys_map += [[0xffe81000L, OBJ(machine + "hfs0"), 0, 0, 16, 0]]
    #	set_attribute(object_list[machine], "phys_mem0", "map", phys_map)

    if num_pci_buses >= 1:
        pci0_devs = get_attribute(object_list[machine], machine + "pci_bus0", "pci_devices")
	pci0_devs +=  [[0, 0, OBJ(machine + "ifb-0")], [1, 0, OBJ(machine + "pid")]]
	set_attribute(object_list[machine], machine + "pci_bus0", "pci_devices", pci0_devs)

    for bus in xrange(num_pci_buses):
        # This is to keep pci_conf.py happy
        pci_devices[machine + "pci_bus" + str(bus)] = {0 : OBJ(machine + "ifb-0"),
                                                       1 : OBJ(machine + "pid")}

    conf_list = object_list[machine]


def add_xterm_console():
    global object_list, machine
    object_list[machine] += [OBJECT(machine + "con0", "xterm-console",
                                    title = "Simics Console",
                                    width = 80, height = 25,
                                    queue = OBJ(machine + "cpu0"))]
    set_attribute(object_list[machine], machine + "kbd0", "console", OBJ(machine + "con0"))
    set_attribute(object_list[machine], machine + "con0", "device", OBJ(machine + "kbd0"))
    set_attribute(object_list[machine], machine + "vga0", "console", OBJ(machine + "con0"))
    
def add_gfx_console():
    object_list[machine] += [OBJECT(machine + "con0", "gfx-console",
                                        x__size = 720,
                                    y__size = 400,
                                    keyboard = OBJ(machine + "kbd0"),
                                    mouse = OBJ(machine + "kbd0"),
                                    double__x__limit = 400,
                                    double__y__limit = 300,
                                    try__open = 1,
                                    queue = OBJ(machine + "cpu0"),
                                    poll__rate = 1000,
                                    auto__release = 1,
                                    rgb__colors = [[0, 0, 0], [0, 0, 168], [0, 168, 0], [0, 168, 168], [168, 0, 0], [168, 0, 168], [168, 168, 0], [168, 168, 168], [0, 0, 84], [0, 0, 252], [0, 168, 84], [0, 168, 252], [168, 0, 84], [168, 0, 252], [168, 168, 84], [168, 168, 252], [0, 84, 0], [0, 84, 168], [0, 252, 0], [0, 252, 168], [168, 84, 0], [168, 84, 168], [168, 252, 0], [168, 252, 168], [0, 84, 84], [0, 84, 252], [0, 252, 84], [0, 252, 252], [168, 84, 84], [168, 84, 252], [168, 252, 84], [168, 252, 252], [84, 0, 0], [84, 0, 168], [84, 168, 0], [84, 168, 168], [252, 0, 0], [252, 0, 168], [252, 168, 0], [252, 168, 168], [84, 0, 84], [84, 0, 252], [84, 168, 84], [84, 168, 252], [252, 0, 84], [252, 0, 252], [252, 168, 84], [252, 168, 252], [84, 84, 0], [84, 84, 168], [84, 252, 0], [84, 252, 168], [252, 84, 0], [252, 84, 168], [252, 252, 0], [252, 252, 168], [84, 84, 84], [84, 84, 252], [84, 252, 84], [84, 252, 252], [252, 84, 84], [252, 84, 252], [252, 252, 84], [252, 252, 252]] + 192 * [[0, 0, 0]])]
    set_attribute(object_list[machine], machine + "kbd0", "console", OBJ(machine + "con0"))
    set_attribute(object_list[machine], machine + "con0", "keyboard", OBJ(machine + "kbd0"))
    set_attribute(object_list[machine], machine + "con0", "mouse", OBJ(machine + "kbd0"))
    set_attribute(object_list[machine], machine + "vga0", "console", OBJ(machine + "con0"))

def add_vga(use_video_xterm_console = 0):

    global object_list, machine

    if configuration_loaded("add_vga"):
        return

    filename = SIM_lookup_file("vgamem.raw")
    if not filename:
	SIM_command_has_problem()
	raise "Can't find vgamem.raw"
    f = open(filename, "rb")
    data = f.read()
    data = tuple([ord(x) for x in data])

    object_list[machine] += [OBJECT(machine + "vga0_image", "image",
                                    size = 0x40000),
                             OBJECT(machine + "vga0", "vga",
                                    queue = OBJ(machine + "cpu0"),
				    console = OBJ(machine + "con0"),
                                    image = OBJ(machine + "vga0_image"),
				    memory_space = OBJ(machine + "pci0-memory"),
				    crtc_regs = [95, 79, 80, 2, 85, 129, 191, 31, 0, 79, 13, 14, 0, 0, 0, 0, 156, 14, 143, 40, 0, 150, 185, 35, 255],
				    crtc_next = 24,
				    attrib_regs = [0, 1, 2, 3, 4, 5, 20, 7, 56, 57, 58, 59, 60, 61, 62, 63, 12, 0, 15, 8, 0],
				    attrib_next_index = 1,
				    attrib_next_reg = 20,
				    attrib_video_enable = 1,
				    seq_regs = [0, 32, 3, 0, 2],
				    seq_next = 1,
				    gfx_regs = [0, 0, 0, 0, 0, 16, 14, 0, 255],
				    gfx_next = 8,
				    gfx_latch = [0, 0, 0, 0],
				    pel_mask = 255,
				    pel_addr = 24,
				    pel_next_color = 0,
				    pel_pal = [[0, 0, 0], [0, 0, 42], [0, 42, 0], [0, 42, 42], [42, 0, 0], [42, 0, 42], [42, 42, 0], [42, 42, 42], [0, 0, 21], [0, 0, 63], [0, 42, 21], [0, 42, 63], [42, 0, 21], [42, 0, 63], [42, 42, 21], [42, 42, 63], [0, 21, 0], [0, 21, 42], [0, 63, 0], [0, 63, 42], [42, 21, 0], [42, 21, 42], [42, 63, 0], [42, 63, 42], [0, 21, 21], [0, 21, 63], [0, 63, 21], [0, 63, 63], [42, 21, 21], [42, 21, 63], [42, 63, 21], [42, 63, 63], [21, 0, 0], [21, 0, 42], [21, 42, 0], [21, 42, 42], [63, 0, 0], [63, 0, 42], [63, 42, 0], [63, 42, 42], [21, 0, 21], [21, 0, 63], [21, 42, 21], [21, 42, 63], [63, 0, 21], [63, 0, 63], [63, 42, 21], [63, 42, 63], [21, 21, 0], [21, 21, 42], [21, 63, 0], [21, 63, 42], [63, 21, 0], [63, 21, 42], [63, 63, 0], [63, 63, 42], [21, 21, 21], [21, 21, 63], [21, 63, 21], [21, 63, 63], [63, 21, 21], [63, 21, 63], [63, 63, 21], [63, 63, 63], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
				    vga_memory = data,
				    misc_reg = 103,
				    h_cnt = 3,
				    v_cnt = 3)]
    
    # vga memory
    map = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    map += [[0x000A0000, OBJ(machine + "vga0"), 1, 0, 0x20000]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", map)

    map = get_attribute(object_list[machine], machine + "lpc_port_space", "map")
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
    set_attribute(object_list[machine], machine + "lpc_port_space", "map", map)

    if use_video_xterm_console:
        add_xterm_console()
    else:
        add_gfx_console()

def add_ragexl(gfx_console = 1, text_console = 0):

    global object_list, machine
    
    ragexl_dev_id = 5
    ragexl_bus = "pci_bus0"
    ragexl_class = "ragexl"
    video_bios = "ragexl-pci-bios.bin"
    video_bios_size = 32768
    
    filename = SIM_lookup_file("ragexl.raw")
    if not filename:
        SIM_command_has_problem()
        raise "Can't find ragexl.raw"
    f = open(filename, "rb")
    vga_memory = f.read(0x40000)
    vga_memory = tuple([ord(x) for x in vga_memory])

    object_list[machine] += [OBJECT(machine + "vga0_image", "image",
                                    size = 0x800000),
                             OBJECT("vga0", ragexl_class,
                                    queue = OBJ(machine + "cpu0"),
                                    memory_space = OBJ(machine + "pci0-memory"),
                                    pci_bus = OBJ(ragexl_bus),
                                    image = OBJ(machine + "vga0_image"),
                                    config__registers = [0x47521002, 0x2800003, 0x300005c, 0, 0xf1000000, 0x2101, 0xf2001000, 0, 0, 0, 0, 0x841002, 0, 96, 0, 0x8010a, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                    mappings = [[16, 0xf1000000, 0x1000000, 0, 2],
                                                [20, 0x2100, 256, 1, 3],
                                                [24, 0xf2001000, 0x1000, 0, 4]],
                                    console = OBJ(machine + "con0"),
                                    crtc_regs = [95, 79, 80, 2, 85, 129, 191, 31,
                                                 0, 79, 13, 14, 0, 0, 2, 560,
                                                 156, 14, 143, 40, 0, 150, 185, 35,
                                                 255],
                                    crtc_next = 15,
                                    attrib_regs = [0, 1, 2, 3, 4, 5, 20, 7,
                                                   56, 57, 58, 59, 60, 61, 62, 63,
                                                   12, 0, 15, 8, 0],
                                    attrib_next_index = 1,
                                    attrib_next_reg = 0,
                                    attrib_video_enable = 1,
                                    seq_regs = [0, 0, 3, 0, 2],
                                    seq_next = 4,
                                    gfx_regs = [0, 0, 0, 0, 0, 16, 14, 0, 255],
                                    gfx_next = 5,
                                    gfx_latch = [0, 0, 0, 0],
                                    pel_mask = 255,
                                    pel_addr = 64,
                                    pel_next_color = 0,
                                    pel_pal = [[0, 0, 0], [0, 0, 42], [0, 42, 0], [0, 42, 42],
                                               [42, 0, 0], [42, 0, 42], [42, 42, 0], [42, 42, 42],
                                               [0, 0, 21], [0, 0, 63], [0, 42, 21], [0, 42, 63],
                                               [42, 0, 21], [42, 0, 63], [42, 42, 21], [42, 42, 63],
                                               [0, 21, 0], [0, 21, 42], [0, 63, 0], [0, 63, 42],
                                               [42, 21, 0], [42, 21, 42], [42, 63, 0], [42, 63, 42],
                                               [0, 21, 21], [0, 21, 63], [0, 63, 21], [0, 63, 63],
                                               [42, 21, 21], [42, 21, 63], [42, 63, 21], [42, 63, 63],
                                               [21, 0, 0], [21, 0, 42], [21, 42, 0], [21, 42, 42],
                                               [63, 0, 0], [63, 0, 42], [63, 42, 0], [63, 42, 42],
                                               [21, 0, 21], [21, 0, 63], [21, 42, 21], [21, 42, 63],
                                               [63, 0, 21], [63, 0, 63], [63, 42, 21], [63, 42, 63],
                                               [21, 21, 0], [21, 21, 42], [21, 63, 0], [21, 63, 42],
                                               [63, 21, 0], [63, 21, 42], [63, 63, 0], [63, 63, 42],
                                               [21, 21, 21], [21, 21, 63], [21, 63, 21], [21, 63, 63],
                                               [63, 21, 21], [63, 21, 63], [63, 63, 21], [63, 63, 63],
                                               [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                                    vga_memory = vga_memory,
                                    misc_reg = 103,
                                    h_cnt = 2,
                                    v_cnt = 2,
                                    refresh__rate = 1000,
                                    sregs = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 75, 2,
                                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 72, 40, 56, 0,
                                             0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 242, 7, 96, 5,
                                             181, 5, 248, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 56, 128, 0,
                                             0, 4, 4, 4, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                             0, 0, 166, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                             0, 160, 51, 115, 0, 0, 0, 0, 0, 0, 0, 0, 1, 12, 0, 100,
                                             123, 58, 117, 16, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 10, 32, 0, 128, 0, 0, 0, 0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 113, 1, 0, 0, 0, 0, 0, 0, 66, 60, 0, 0,
                                             66, 71, 0, 124, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

                                    )]

    map = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    map += [[0x000A0000, OBJ(machine + "vga0"), 1, 0, 0x20000]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", map)

    devs = get_attribute(object_list[machine], ragexl_bus, "pci_devices")
    devs.append([ragexl_dev_id, 0, OBJ(machine + "vga0")])
    set_attribute(object_list[machine], ragexl_bus, "pci_devices", devs)

    if use_video_xterm_console:
        add_xterm_console()
    else:
        add_gfx_console()

def get_configuration():
    global object_list, machine
    all_objs = []
    for mach in machine_list:
        machine = mach
        all_objs += object_list[machine]
    return all_objs

def post_configuration():
    global machine
    for mach in machine_list:
        machine = mach

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
