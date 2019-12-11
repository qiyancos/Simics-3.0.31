
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

object_list = {}
machine_list = []

if not "machine" in dir(): machine = ""

SIM_source_python_in_module("../scripts/pci_conf.py", __name__)

if not SIM_get_quiet():
    print
    print "Machines based on ppc4xx_conf.py are only provided for backward "
    print "compatibility. The new component based machines in simics/targets/"
    print "are recommended instead."
    print

def handle_error(msg):
    print
    print "PPC4xx configuration error:"
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

def set_machine(mach):
    global machine, conf_list
    machine = mach
    conf_list = object_list.setdefault(machine, [])

def obj_name(name):
    global machine
    if len(machine) != 0:
        return machine + name
    else:
        return name

def console_title(name):
    global machine
    if len(machine) != 0:
        return machine + ": " + name
    else:
        return name

# Returns list of port space mappings for dcr
def dcr_memory_map(devices):
    mapping = []
    for d in devices:
        if len(d) < 3:
            print "invalid dcr mapping:",
            print d
            return    
        obj = OBJ(obj_name(d[0]))
        fn  = d[1]
        dcr_map = d[2]
        # Go through all dcr addresses
        for m in dcr_map:
            (ofs, dcr) = m
            ofs = ofs * 4
            if isinstance(dcr,int):
                mapping += [[dcr*4, obj, fn, ofs, 4]]
            elif len(dcr) == 2:
                mapping += [[(dcr[0] + i)*4, obj, fn, ofs+i*4, 4] for i in range(dcr[1] + 1 - dcr[0])]
            else:
                print "invalid dcr type mapping:",
                print d
    return mapping

                
#
# mhz: CPU clock
# mac0: ethernet mac address of first ethernet
# mac1: ethernet mac address of second ethernet
# hide_2nd_console: set to 1 to hide "serial B"
#
def create_ppc440gp_soc(mhz, mac0, mac1, hide_2nd_console = 0, simicsfs = 0):
    global object_list
    global machine_list
    machine_list.append(machine)
    if configuration_loaded("create_system"):
        return

    dcr_map = dcr_memory_map([
        # Object  Fn  Idx    DCR (or range in case of list)
        ["mc0",   0, [(0x0,  [0x10, 0x11])]],
        ["ebc0",  0, [(0x0,  [0x12, 0x13])]],
        ["cpc0",  0, [(0x0,  [0xb0, 0xb3]),
                      (0x30, [0xe0, 0xef])]],
        ["uic0",  0, [(0x0,  0xc0),
                      (0x2,  [0xc2, 0xc8])]],        
        ["uic1",  0, [(0x0,  0xd0),
                      (0x2,  [0xd2, 0xd8])]],
        ["dma0",  0, [(0x0,  [0x100, 0x120]),
                      (0x23, 0x123),
                      (0x25, 0x125),
                      (0x26, 0x126)]],
        ["mal0",  0, [(0x0,  [0x180, 0x182]),
                      (0x4,  [0x184,0x195]),
                      (0x20, [0x1a0,0x1a3]),
                      (0x40, [0x1c0, 0x1c1]),
                      (0x60, [0x1e0, 0x1e1])]]])
    
    plb = [[0x140000200,    OBJ(obj_name("uart0")),       0,           0,           1],
           [0x140000201,    OBJ(obj_name("uart0")),       0,           1,           1],
           [0x140000202,    OBJ(obj_name("uart0")),       0,           2,           1],
           [0x140000203,    OBJ(obj_name("uart0")),       0,           3,           1],
           [0x140000204,    OBJ(obj_name("uart0")),       0,           4,           1],
           [0x140000205,    OBJ(obj_name("uart0")),       0,           5,           1],
           [0x140000206,    OBJ(obj_name("uart0")),       0,           6,           1],
           [0x140000207,    OBJ(obj_name("uart0")),       0,           7,           1],
           [0x140000300,    OBJ(obj_name("uart1")),       0,           0,           1],
           [0x140000301,    OBJ(obj_name("uart1")),       0,           1,           1],
           [0x140000302,    OBJ(obj_name("uart1")),       0,           2,           1],
           [0x140000303,    OBJ(obj_name("uart1")),       0,           3,           1],
           [0x140000304,    OBJ(obj_name("uart1")),       0,           4,           1],
           [0x140000305,    OBJ(obj_name("uart1")),       0,           5,           1],
           [0x140000306,    OBJ(obj_name("uart1")),       0,           6,           1],
           [0x140000307,    OBJ(obj_name("uart1")),       0,           7,           1],
           
           [0x140000400,    OBJ(obj_name("iic0")),        0,        0x00,         0x2],
           [0x140000402,    OBJ(obj_name("iic0")),        0,        0x02,         0x2],
           [0x140000404,    OBJ(obj_name("iic0")),        0,        0x04,         0x1],
           [0x140000405,    OBJ(obj_name("iic0")),        0,        0x05,         0x1],
           [0x140000406,    OBJ(obj_name("iic0")),        0,        0x06,         0x1],
           [0x140000407,    OBJ(obj_name("iic0")),        0,        0x07,         0x1],
           [0x140000408,    OBJ(obj_name("iic0")),        0,        0x08,         0x1],
           [0x140000409,    OBJ(obj_name("iic0")),        0,        0x09,         0x1],
           [0x14000040a,    OBJ(obj_name("iic0")),        0,        0x0a,         0x1],
           [0x14000040b,    OBJ(obj_name("iic0")),        0,        0x0b,         0x1],
           [0x14000040c,    OBJ(obj_name("iic0")),        0,        0x0c,         0x1],
           [0x14000040d,    OBJ(obj_name("iic0")),        0,        0x0d,         0x1],
           [0x14000040e,    OBJ(obj_name("iic0")),        0,        0x0e,         0x1],
           [0x14000040f,    OBJ(obj_name("iic0")),        0,        0x0f,         0x1],
           [0x140000410,    OBJ(obj_name("iic0")),        0,        0x10,         0x1],
           
           [0x140000500,    OBJ(obj_name("iic1")),        0,        0x00,         0x2],
           [0x140000502,    OBJ(obj_name("iic1")),        0,        0x02,         0x2],
           [0x140000504,    OBJ(obj_name("iic1")),        0,        0x04,         0x1],
           [0x140000505,    OBJ(obj_name("iic1")),        0,        0x05,         0x1],
           [0x140000506,    OBJ(obj_name("iic1")),        0,        0x06,         0x1],
           [0x140000507,    OBJ(obj_name("iic1")),        0,        0x07,         0x1],
           [0x140000508,    OBJ(obj_name("iic1")),        0,        0x08,         0x1],
           [0x140000509,    OBJ(obj_name("iic1")),        0,        0x09,         0x1],
           [0x14000050a,    OBJ(obj_name("iic1")),        0,        0x0a,         0x1],
           [0x14000050b,    OBJ(obj_name("iic1")),        0,        0x0b,         0x1],
           [0x14000050c,    OBJ(obj_name("iic1")),        0,        0x0c,         0x1],
           [0x14000050d,    OBJ(obj_name("iic1")),        0,        0x0d,         0x1],
           [0x14000050e,    OBJ(obj_name("iic1")),        0,        0x0e,         0x1],
           [0x14000050f,    OBJ(obj_name("iic1")),        0,        0x0f,         0x1],
           [0x140000510,    OBJ(obj_name("iic1")),        0,        0x10,         0x1],
           
           [0x140000700,    OBJ(obj_name("gpio0")),       0,           0,         128],            
           [0x140000780,    OBJ(obj_name("zmii0")),       0,           0,           4],
           [0x140000784,    OBJ(obj_name("zmii0")),       0,           1,           4],
           [0x140000788,    OBJ(obj_name("zmii0")),       0,           2,           4],
           [0x140000800,    OBJ(obj_name("emac0")),       0,           0,         256],
           [0x140000900,    OBJ(obj_name("emac1")),       0,           1,         256],
           [0x208000000,    OBJ(obj_name("pci0")),  4,           0, 0x000010000, OBJ(obj_name("pci-bus0-io"))],
           [0x20EC00000,    OBJ(obj_name("pci0")),  1,           0, 0x000000008],
           [0x20EC80000,    OBJ(obj_name("pci0")),  2, 0x20EC80000, 0x000000100],
           [0x20ee00000,    OBJ(obj_name("pci0")),  3,           0, 0xdf1200000, OBJ(obj_name("pci-bus0-memory"))]]

    if simicsfs:
        plb += [[0x0ff660000L,    OBJ(obj_name("simicsfs")),      0,           0,        0x10]]
    
    m         = ([OBJECT(obj_name("cpu0"), "ppc440gp",
                         queue = OBJ(obj_name("cpu0")),
                         freq_mhz = mhz,
                         timebase_freq_mhz = mhz,
                         physical_memory = OBJ(obj_name("plb")),
                         dcr_space = OBJ(obj_name("dcr-space"))
                         )] +
                 [OBJECT(obj_name("plb"), "memory-space",
                         map = plb[0:])] +
                 [OBJECT(obj_name("dcr-space"), "memory-space",
                         map = dcr_map[0:])] +
                 [OBJECT(obj_name("dma0"), "ppc440gp-dma",
                         interrupt_device = OBJ(obj_name("uic0")),
                         cpu = OBJ(obj_name("cpu0")),
                         memory = OBJ(obj_name("plb")))] +
                 [OBJECT(obj_name("ebc0"), "ppc440gp-ebc",
                         cpu = OBJ(obj_name("cpu0"))
                         )] +
                 [OBJECT(obj_name("gpio0"), "ppc440gp-gpio")] +
                 [OBJECT(obj_name("uart0"), "NS16550",
                         recorder = OBJ(obj_name("rec0")),
                         irq_dev = OBJ(obj_name("uic0")),
                         irq_level = 0,
                         console = OBJ(obj_name("con0")),
                         queue = OBJ(obj_name("cpu0")))] +
                 [OBJECT(obj_name("con0"), "xterm-console",
                         queue = OBJ(obj_name("cpu0")),
                         device = OBJ(obj_name("uart0")),
                         title = console_title("System Console, Serial A"))] +
                 [OBJECT(obj_name("uart1"), "NS16550",
                         recorder = OBJ(obj_name("rec0")),
                         irq_dev = OBJ(obj_name("uic0")),
                         irq_level = 1,
                         console = OBJ(obj_name("con1")),
                         queue = OBJ(obj_name("cpu0")))] +
                 [OBJECT(obj_name("con1"), "xterm-console",
                         queue = OBJ(obj_name("cpu0")),
                         device = OBJ(obj_name("uart1")),
                         no_window = hide_2nd_console,    # show by default
                         title = console_title("System Console, Serial B"))] +
                 [OBJECT(obj_name("uic0"), "ppc440gp-uic",
                         queue = OBJ(obj_name("cpu0")),
                         target = OBJ(obj_name("cpu0")),
                         target_level = 0,
                         critical_target = OBJ(obj_name("cpu0")),
                         critical_target_level = 0)] +
                 [OBJECT(obj_name("uic1"), "ppc440gp-uic",
                         queue = OBJ(obj_name("cpu0")),
                         target = OBJ(obj_name("uic1")),
                         target_level = 30,
                         critical_target = OBJ(obj_name("uic0")),
                         critical_target_level = 31)] +
                 [OBJECT(obj_name("rec0"), "recorder")] +
                 [OBJECT(obj_name("cpc0"), "ppc440gp-cpc")] +
                 [OBJECT(obj_name("iic0"), "ppc440gp-iic",
                         queue = OBJ(obj_name("cpu0")),
                         i2c_bus = OBJ(obj_name("i2c0")),
                         interrupt_device = OBJ(obj_name("uic0")),
                         interrupt_level = 2)] +
                 [OBJECT(obj_name("iic1"), "ppc440gp-iic",
                         queue = OBJ(obj_name("cpu0")),
                         i2c_bus = OBJ(obj_name("i2c1")),
                         interrupt_device = OBJ(obj_name("uic0")),
                         interrupt_level = 3)] +                 
                 [OBJECT(obj_name("i2c0"), "i2c-bus")] +
                 [OBJECT(obj_name("i2c1"), "i2c-bus")] +
                 [OBJECT(obj_name("mc0"), "ppc440gp-mc",
                         memory = OBJ(obj_name("plb")))] +
                 [OBJECT(obj_name("emac0"), "ppc440gp-emac",
                         queue = OBJ(obj_name("cpu0")),
                         recorder = OBJ(obj_name("rec0")),
                         mac_address = mac0,
                         mal = OBJ(obj_name("mal0")))] +
                 [OBJECT(obj_name("emac1"), "ppc440gp-emac",
                         queue = OBJ(obj_name("cpu0")),
                         recorder = OBJ(obj_name("rec0")),
                         mac_address = mac1,
                         mal = OBJ(obj_name("mal0")))] +
                 [OBJECT(obj_name("mal0"), "ppc440gp-mal",
                         memory = OBJ(obj_name("plb")),
                         cpu = OBJ(obj_name("cpu0")),                         
                         interrupts = [OBJ(obj_name("uic0")),
                                       OBJ(obj_name("uic0"))])] +
                 [OBJECT(obj_name("zmii0"), "ppc440gp-zmii")] +
                 [OBJECT(obj_name("pci0"), "ppc440gp-pci",
                         pci_bus = OBJ(obj_name("pci_bus0")),
                         plb = OBJ(obj_name("plb")),
                         irq_routing = [[1, OBJ(obj_name("uic0")), 23],
                                        [2, OBJ(obj_name("uic0")), 24],
                                        [3, OBJ(obj_name("uic0")), 25],
                                        [4, OBJ(obj_name("uic0")), 26]])] +
                 [OBJECT(obj_name("pci_bus0"), "pci-bus",
                         bridge = OBJ(obj_name("pci0")),
                         interrupt = OBJ(obj_name("pci0")),
                         memory_space = OBJ(obj_name("pci_bus0_memory")),
                         io_space = OBJ(obj_name("pci_bus0_io")),
                         conf_space = OBJ(obj_name("pci_bus0_conf")),
                         pci_devices = [[0, 0, OBJ(obj_name("pci0"))]])] +
                 [OBJECT(obj_name("pci-bus0-memory"), "memory-space")] +
                 [OBJECT(obj_name("pci-bus0-io"), "memory-space")] +
                 [OBJECT(obj_name("pci-bus0-conf"), "memory-space")])

    if simicsfs:
        m += ([OBJECT(obj_name("simicsfs"), "hostfs")])
        
    object_list[machine] += m
    conf_list = object_list[machine]

def create_ppc440gx_soc(mhz, mac0, mac1, simicsfs = 0):
    global object_list
    global machine_list
    if not machine in machine_list:
        machine_list.append(machine)
    if configuration_loaded("create_system"):
        return

    dcr_map = dcr_memory_map([
        # Object  Fn  Idx    DCR (or range in case of list)
        ["cpr0",  0, [(0x0,  [0x00c, 0x00d])]],
        ["sdr0",  0, [(0x0,  [0x00e, 0x00f])]],
        ["sdram0",0, [(0x0,  [0x010, 0x011])]],
        ["ebc0",  0, [(0x0,  [0x012, 0x013])]],
        ["sram0", 0, [(0x0,  [0x020, 0x02a])]],
        ["l2c0",  0, [(0x0,  [0x030, 0x037])]],
        ["plb0",  0, [(0x0,  [0x082, 0x084]),
                      (0x5,  [0x085, 0x086])]],
        ["obp0",  0, [(0x0,  [0x0a8, 0x0ac])]],
        ["uic0",  0, [(0x0,  0xc0),
                      (0x2,  [0x0c2, 0x0c8])]],
        ["uic1",  0, [(0x0,  0xd0),
                      (0x2,  [0x0d2, 0x0d8])]],
        ["dma0",  0, [(0x0,  [0x100, 0x120]),
                      (0x23, 0x123),
                      (0x25, 0x125),
                      (0x26, 0x126)]],
        ["mal0",  0, [(0x0,  [0x180, 0x189]),
                      (0x10, [0x190, 0x195]),
                      (0x20, [0x1a0, 0x1a3]),
                      (0x40, [0x1c0, 0x1c3]),
                      (0x60, [0x1e0, 0x1e3])]],
        ["uicb",  0, [(0x0,  0x200),
                      (0x2,  [0x202, 0x208])]],
        ["uic2",  0, [(0x0,  0x210),
                      (0x2,  [0x212, 0x218])]]])
    
    plb = [[0x140000200,    OBJ(obj_name("uart0")),       0,           0,           1],
           [0x140000201,    OBJ(obj_name("uart0")),       0,           1,           1],
           [0x140000202,    OBJ(obj_name("uart0")),       0,           2,           1],
           [0x140000203,    OBJ(obj_name("uart0")),       0,           3,           1],
           [0x140000204,    OBJ(obj_name("uart0")),       0,           4,           1],
           [0x140000205,    OBJ(obj_name("uart0")),       0,           5,           1],
           [0x140000206,    OBJ(obj_name("uart0")),       0,           6,           1],
           [0x140000207,    OBJ(obj_name("uart0")),       0,           7,           1],
           [0x140000300,    OBJ(obj_name("uart1")),       0,           0,           1],
           [0x140000301,    OBJ(obj_name("uart1")),       0,           1,           1],
           [0x140000302,    OBJ(obj_name("uart1")),       0,           2,           1],
           [0x140000303,    OBJ(obj_name("uart1")),       0,           3,           1],
           [0x140000304,    OBJ(obj_name("uart1")),       0,           4,           1],
           [0x140000305,    OBJ(obj_name("uart1")),       0,           5,           1],
           [0x140000306,    OBJ(obj_name("uart1")),       0,           6,           1],
           [0x140000307,    OBJ(obj_name("uart1")),       0,           7,           1],
           
           [0x140000400,    OBJ(obj_name("iic0")),        0,        0x00,         0x2],
           [0x140000402,    OBJ(obj_name("iic0")),        0,        0x02,         0x2],
           [0x140000404,    OBJ(obj_name("iic0")),        0,        0x04,         0x1],
           [0x140000405,    OBJ(obj_name("iic0")),        0,        0x05,         0x1],
           [0x140000406,    OBJ(obj_name("iic0")),        0,        0x06,         0x1],
           [0x140000407,    OBJ(obj_name("iic0")),        0,        0x07,         0x1],
           [0x140000408,    OBJ(obj_name("iic0")),        0,        0x08,         0x1],
           [0x140000409,    OBJ(obj_name("iic0")),        0,        0x09,         0x1],
           [0x14000040a,    OBJ(obj_name("iic0")),        0,        0x0a,         0x1],
           [0x14000040b,    OBJ(obj_name("iic0")),        0,        0x0b,         0x1],
           [0x14000040c,    OBJ(obj_name("iic0")),        0,        0x0c,         0x1],
           [0x14000040d,    OBJ(obj_name("iic0")),        0,        0x0d,         0x1],
           [0x14000040e,    OBJ(obj_name("iic0")),        0,        0x0e,         0x1],
           [0x14000040f,    OBJ(obj_name("iic0")),        0,        0x0f,         0x1],
           [0x140000410,    OBJ(obj_name("iic0")),        0,        0x10,         0x1],
           
           [0x140000500,    OBJ(obj_name("iic1")),        0,        0x00,         0x2],
           [0x140000502,    OBJ(obj_name("iic1")),        0,        0x02,         0x2],
           [0x140000504,    OBJ(obj_name("iic1")),        0,        0x04,         0x1],
           [0x140000505,    OBJ(obj_name("iic1")),        0,        0x05,         0x1],
           [0x140000506,    OBJ(obj_name("iic1")),        0,        0x06,         0x1],
           [0x140000507,    OBJ(obj_name("iic1")),        0,        0x07,         0x1],
           [0x140000508,    OBJ(obj_name("iic1")),        0,        0x08,         0x1],
           [0x140000509,    OBJ(obj_name("iic1")),        0,        0x09,         0x1],
           [0x14000050a,    OBJ(obj_name("iic1")),        0,        0x0a,         0x1],
           [0x14000050b,    OBJ(obj_name("iic1")),        0,        0x0b,         0x1],
           [0x14000050c,    OBJ(obj_name("iic1")),        0,        0x0c,         0x1],
           [0x14000050d,    OBJ(obj_name("iic1")),        0,        0x0d,         0x1],
           [0x14000050e,    OBJ(obj_name("iic1")),        0,        0x0e,         0x1],
           [0x14000050f,    OBJ(obj_name("iic1")),        0,        0x0f,         0x1],
           [0x140000510,    OBJ(obj_name("iic1")),        0,        0x10,         0x1],
           
           [0x140000700,    OBJ(obj_name("gpio0")),       0,           0,         128],
           [0x140000780,    OBJ(obj_name("zmii0")),       0,           0,           4],
           [0x140000784,    OBJ(obj_name("zmii0")),       1,           0,           4],
           [0x140000788,    OBJ(obj_name("zmii0")),       2,           0,           4],

           [0x140000790,    OBJ(obj_name("rgmii0")),      0,           0,           4],
           [0x140000794,    OBJ(obj_name("rgmii0")),      1,           0,           4],
           
           [0x140000800,    OBJ(obj_name("emac0")),       0,           0,         256],
           [0x140000900,    OBJ(obj_name("emac1")),       1,           0,         256],
           [0x140000C00,    OBJ(obj_name("emac2")),       2,           0,         256],
           [0x140000E00,    OBJ(obj_name("emac3")),       3,           0,         256],
           [0x208000000,    OBJ(obj_name("pci0")),  4,           0, 0x000010000, OBJ(obj_name("pci-bus0-io"))],
           [0x20EC00000,    OBJ(obj_name("pci0")),  1,           0, 0x000000008],
           [0x20EC80000,    OBJ(obj_name("pci0")),  2, 0x20EC80000, 0x000000100],
           [0x20ee00000,    OBJ(obj_name("pci0")),  3,           0, 0xdf1200000, OBJ(obj_name("pci-bus0-memory"))]]

    if simicsfs:
        plb += [[0x0ff660000L,    OBJ(obj_name("simicsfs")),      0,           0,        0x10]]
    
    m         = ([OBJECT(obj_name("cpu0"), "ppc440gx",
                         queue = OBJ(obj_name("cpu0")),
                         freq_mhz = mhz,
                         timebase_freq_mhz = mhz,
                         physical_memory = OBJ(obj_name("plb")),
                         disable_watchdog_reboots = 1,
                         dcr_space = OBJ(obj_name("dcr-space"))
                         )] +
                 [OBJECT(obj_name("dcr-space"), "memory-space",
                         map = dcr_map[0:])] +                 
                 [OBJECT(obj_name("plb"), "memory-space",
                         map = plb[0:])] +
                 [OBJECT(obj_name("dma0"), "ppc440gx-dma",
                         interrupt_device = OBJ(obj_name("uic0")),
                         cpu = OBJ(obj_name("cpu0")),
                         memory = OBJ(obj_name("plb")))] +
                 [OBJECT(obj_name("ebc0"), "ppc440gx-ebc",
                         cpu = OBJ(obj_name("cpu0")))] +
                 [OBJECT(obj_name("gpio0"), "ppc440gx-gpio")] +
                 [OBJECT(obj_name("uart0"), "NS16550",
                         recorder = OBJ(obj_name("rec0")),
                         irq_dev = OBJ(obj_name("uic0")),
                         irq_level = 0,
                         console = OBJ(obj_name("con0")),
                         queue = OBJ(obj_name("cpu0")))] +
                 [OBJECT(obj_name("con0"), "xterm-console",
                         queue = OBJ(obj_name("cpu0")),
                         device = OBJ(obj_name("uart0")),
                         title = console_title("System Console, Serial A"))] +
                 [OBJECT(obj_name("uart1"), "NS16550",
                         recorder = OBJ(obj_name("rec0")),
                         irq_dev = OBJ(obj_name("uic0")),
                         irq_level = 1,
                         console = OBJ(obj_name("con1")),
                         queue = OBJ(obj_name("cpu0")))] +
                 [OBJECT(obj_name("con1"), "xterm-console",
                         queue = OBJ(obj_name("cpu0")),
                         device = OBJ(obj_name("uart1")),
                         title = console_title("System Console, Serial B"))] +
                 [OBJECT(obj_name("uic0"), "ppc440gx-uic",
                         queue = OBJ(obj_name("cpu0")),
                         target = OBJ(obj_name("cpu0")),
                         target_level = 0,
                         critical_target = OBJ(obj_name("cpu0")),
                         critical_target_level = 0)] +
                 [OBJECT(obj_name("uic1"), "ppc440gx-uic",
                         queue = OBJ(obj_name("cpu0")),
                         target = OBJ(obj_name("uic1")),
                         target_level = 30,
                         critical_target = OBJ(obj_name("uic0")),
                         critical_target_level = 31)] +
                 [OBJECT(obj_name("uicb"), "ppc440gx-uic",
                         queue = OBJ(obj_name("cpu0")),
                         target = OBJ(obj_name("cpu0")),
                         target_level = 0,
                         critical_target = OBJ(obj_name("cpu0")),
                         critical_target_level = 0)] +
                 [OBJECT(obj_name("uic2"), "ppc440gx-uic",
                         queue = OBJ(obj_name("cpu0")),
                         target = OBJ(obj_name("uic1")),
                         target_level = 30,
                         critical_target = OBJ(obj_name("uic0")),
                         critical_target_level = 31)] +
                 [OBJECT(obj_name("rec0"), "recorder")] +
                 [OBJECT(obj_name("cpc0"), "ppc440gx-cpc")] +
                 [OBJECT(obj_name("l2c0"), "ppc440gx-l2c")] +
                 [OBJECT(obj_name("plb0"), "ppc440gx-plb")] +
                 [OBJECT(obj_name("obp0"), "ppc440gx-opb")] +
                 [OBJECT(obj_name("cpr0"), "ppc440gx-cpr")] +
                 [OBJECT(obj_name("sdr0"), "ppc440gx-sdr",
                         uic = [OBJ(obj_name("uic0")), OBJ(obj_name("uic1")), OBJ(obj_name("uic2")), OBJ(obj_name("uicb"))],
                         cpu = OBJ(obj_name("cpu0")))] +
                 [OBJECT(obj_name("sram0"), "ppc440gx-sram",
                         sram = OBJ(obj_name("sram0_memory")),
                         plb = OBJ(obj_name("plb")))] +
                 [OBJECT(obj_name("sram0_memory"), "ram",
                         image = OBJ(obj_name("sram0_image")))] +
                 [OBJECT(obj_name("sram0_image"), "image",
                         queue = OBJ(obj_name("cpu0")),
                         size = 0x40000)] +
                 [OBJECT(obj_name("iic0"), "ppc440gx-iic",
                         queue = OBJ(obj_name("cpu0")),
                         i2c_bus = OBJ(obj_name("i2c0")),
                         interrupt_device = OBJ(obj_name("uic0")),
                         interrupt_level = 2)] +
                 [OBJECT(obj_name("iic1"), "ppc440gx-iic",
                         queue = OBJ(obj_name("cpu0")),
                         i2c_bus = OBJ(obj_name("i2c1")),
                         interrupt_device = OBJ(obj_name("uic0")),
                         interrupt_level = 3)] +                 
                 [OBJECT(obj_name("i2c0"), "i2c-bus")] +
                 [OBJECT(obj_name("i2c1"), "i2c-bus")] +
                 [OBJECT(obj_name("sdram0"), "ppc440gx-sdram",
                         memory = OBJ(obj_name("plb")))] +
                 [OBJECT(obj_name("emac0"), "ppc440gx-emac",
                         queue = OBJ(obj_name("cpu0")),
                         recorder = OBJ(obj_name("rec0")),
                         mac_address = mac0,
                         mal = OBJ(obj_name("mal0")))] +
                 [OBJECT(obj_name("emac1"), "ppc440gx-emac",
                         queue = OBJ(obj_name("cpu0")),
                         recorder = OBJ(obj_name("rec0")),
                         mac_address = mac1,
                         mal = OBJ(obj_name("mal0")))] +
                 [OBJECT(obj_name("emac2"), "ppc440gx-emac",
                         queue = OBJ(obj_name("cpu0")),
                         recorder = OBJ(obj_name("rec0")),
                         mac_address = mac1,
                         mal = OBJ(obj_name("mal0")))] +
                 [OBJECT(obj_name("emac3"), "ppc440gx-emac",
                         queue = OBJ(obj_name("cpu0")),
                         recorder = OBJ(obj_name("rec0")),
                         mac_address = mac1,
                         mal = OBJ(obj_name("mal0")))] +
                 [OBJECT(obj_name("mal0"), "ppc440gx-mal",
                         memory = OBJ(obj_name("plb")),
                         cpu = OBJ(obj_name("cpu0")),
                         interrupts = [OBJ(obj_name("uic0")),
                                       OBJ(obj_name("uic0"))])] +
                 [OBJECT(obj_name("zmii0"), "ppc440gx-zmii")] +
                 [OBJECT(obj_name("rgmii0"), "ppc440gx-rgmii")] +
                 [OBJECT(obj_name("pci0"), "ppc440gx-pci",
                         pci_bus = OBJ(obj_name("pci_bus0")),
                         plb = OBJ(obj_name("plb")),
                         irq_routing = [[1, OBJ(obj_name("uic0")), 23],
                                        [2, OBJ(obj_name("uic0")), 24],
                                        [3, OBJ(obj_name("uic0")), 25],
                                        [4, OBJ(obj_name("uic0")), 26]])] +
                 [OBJECT(obj_name("pci_bus0"), "pci-bus",
                         bridge = OBJ(obj_name("pci0")),
                         interrupt = OBJ(obj_name("pci0")),
                         memory_space = OBJ(obj_name("pci_bus0_memory")),
                         io_space = OBJ(obj_name("pci_bus0_io")),
                         conf_space = OBJ(obj_name("pci_bus0_conf")),
                         pci_devices = [[0, 0, OBJ(obj_name("pci0"))]])] +
                 [OBJECT(obj_name("pci-bus0-memory"), "memory-space")] +
                 [OBJECT(obj_name("pci-bus0-io"), "memory-space")] +
                 [OBJECT(obj_name("pci-bus0-conf"), "memory-space")])

    if simicsfs:
        m += ([OBJECT(obj_name("simicsfs"), "hostfs")])
        
    object_list[machine] += m
    conf_list = object_list[machine]


def add_ram(name, address, size):
    global machine
    global object_list
    object_list[machine] += ([OBJECT(obj_name(name), "ram",
                                     image = OBJ(obj_name(name + "-image")))] +
                             [OBJECT(obj_name(name + "-image"), "image",
                                     queue = OBJ(obj_name("cpu0")),
                                     size = size)])
    map = get_attribute(object_list[machine], obj_name("plb"), "map")
    map += [[address, OBJ(obj_name(name)), 0, 0, size]]
    set_attribute(object_list[machine], obj_name("plb"), "map", map)

def add_flash_memory(name, address, size, cfi = 1, intel = 0, amd = 0, jedec = 1, interleave = 1,
                     bus_width = 1, vendor_id = 0x01, device_id = 0xAD, sectors = 0, files = []):
    global machine
    global object_list
    object_list[machine] += ([OBJECT(obj_name(name), "flash-memory",
                                     queue = OBJ(obj_name("cpu0")),
                                     cfi_compatible = cfi,
                                     intel_compatible = intel,
                                     amd_compatible = amd,
                                     jedec_compatible = jedec,
                                     interleave = interleave,
                                     bus_width = bus_width,
                                     vendor_id = vendor_id,
                                     device_id = device_id,
                                     sectors = sectors,
                                     sector_size = size / sectors,
                                     storage_ram = OBJ(obj_name(name + "-ram")))] +
                             [OBJECT(obj_name(name + "-ram"), "ram",
                                     image = OBJ(obj_name(name + "-image")))] +
                             [OBJECT(obj_name(name + "-image"), "image",
                                     queue = OBJ(obj_name("cpu0")),
                                     size = size,
                                     files = files)])
    map = get_attribute(object_list[machine], obj_name("plb"), "map")
    map += [[address, OBJ(obj_name(name)), 0, 0, size, OBJ(obj_name(name + "-ram"))]]
    set_attribute(object_list[machine], obj_name("plb"), "map", map)

def add_spd(name = "sdram-spd", address = 0x53):
    global machine
    global object_list
    object_list[machine] += ([OBJECT(obj_name(name), "PCF8582C",
                                     i2c_bus = OBJ(obj_name("i2c0")),
                                     address = address,
                                     address_mask = 0xFF,
                                     image = OBJ(obj_name(name + "-image")))] +
                             [OBJECT(obj_name(name + "-image"), "image",
                                     queue = OBJ(obj_name("cpu0")),
                                     size = 0x100000)])

def add_fpga():
    global machine
    global object_list
    object_list[machine] += ([OBJECT(obj_name("fpga"), "rom",
                                     image = OBJ(obj_name("fpga-image")))] +
                             [OBJECT(obj_name("fpga-image"), "image",
                                     queue = OBJ(obj_name("cpu0")),
                                     size = 8192)])
    map = get_attribute(object_list[machine], obj_name("plb"), "map")
    map += [[0x148300000, OBJ(obj_name("fpga")), 0, 0, 16]]
    set_attribute(object_list[machine], obj_name("plb"), "map", map)

def add_ebony_fpga():
    global machine
    global object_list
    object_list[machine] += ([OBJECT(obj_name("fpga"), "ebony-fpga")])
    map = get_attribute(object_list[machine], obj_name("plb"), "map")
    map += [[0x148300000, OBJ(obj_name("fpga")), 0, 0, 3]]
    set_attribute(object_list[machine], obj_name("plb"), "map", map)


def add_ds1743p(name, address, nvram):
    global machine
    global object_list
    object_list[machine] += ([OBJECT(obj_name(name), "DS1743P",
                                     queue = OBJ(obj_name("cpu0")),
                                     nvram = nvram)])
    map = get_attribute(object_list[machine], obj_name("plb"), "map")
    map += [[address,          OBJ(obj_name(name)), 0, 0,      0x1ff8],
            [address + 0x1ff8, OBJ(obj_name(name)), 0, 0x1ff8, 0x0001],
            [address + 0x1ff9, OBJ(obj_name(name)), 0, 0x1ff9, 0x0001],
            [address + 0x1ffa, OBJ(obj_name(name)), 0, 0x1ffa, 0x0001],
            [address + 0x1ffb, OBJ(obj_name(name)), 0, 0x1ffb, 0x0001],
            [address + 0x1ffc, OBJ(obj_name(name)), 0, 0x1ffc, 0x0001],
            [address + 0x1ffd, OBJ(obj_name(name)), 0, 0x1ffd, 0x0001],
            [address + 0x1ffe, OBJ(obj_name(name)), 0, 0x1ffe, 0x0001],
            [address + 0x1fff, OBJ(obj_name(name)), 0, 0x1fff, 0x0001]]
    set_attribute(object_list[machine], obj_name("plb"), "map", map)


def get_configuration():
    global machine
    global object_list
    all_objects = []
    for m in object_list.keys():
        all_objects += object_list[m]
    return all_objects

def post_configuration():
    # nothing here yet
    pass

def finish_configuration():
    all_objects = get_configuration()
    try:
        SIM_set_configuration(all_objects)
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

