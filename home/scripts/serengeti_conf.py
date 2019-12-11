
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

# constants

if not "openbootprom" in dir(): openbootprom = "openbootprom.sg"
 
# up to 32GB per board - what different configs?
MB_PER_BOARD = (32L * 1024)
CPU_BRD_PER_NODE = 6
IO_BRD_PER_NODE = 4
BRD_PER_NODE = (CPU_BRD_PER_NODE + IO_BRD_PER_NODE)
CPU_PER_BOARD = 4
IO_PER_BOARD = 2
CPU_PER_NODE = (CPU_BRD_PER_NODE * CPU_PER_BOARD)
IO_PER_NODE =  (IO_BRD_PER_NODE  * IO_PER_BOARD)
AID_PER_NODE = (CPU_PER_NODE + IO_PER_NODE)

# mem_sizes is per cpu
mem_sizes = {8192 : 4, 4096 : 2, 2048 : 1, 1024 : 1, 512 : 1, 256 : 1, 128 : 1, 64 : 1, 0 : 0}
bank_mask = {2048 : 0x1f, 1024 : 0xf, 512 : 0x7, 256 : 0x3, 128 : 0x1, 0 : 0x0}

# some global variables for the configuration

cur_node = {}         # per machine
object_list = {}      # per node
board_list = {}       # per node
cpu_list = {}         # per machine
node_list = {}        # per machine
pci_slots = {}        # per machine, index with (low) schizo nid|aid
master_node = {}      # TODO: allow setting
highest_mem = {}      # per machine
first_sbbc = {}       # per node
chassis_list = {}     # per node
num_gfx_consoles = {} # per machine
dist_node_mem = {}    # per machine
cpus_in_machine = {}  # per machine
mem_per_cpu = {}      # per node

machine_list = []     # global
have_sim_object = 0   # global
have_cpu_prom = 0     # global
have_io_prom = 0      # global
have_isp2200_prom = 0 # global
have_isp1040_prom = 0 # global
have_pgx64_prom = 0   # global

cassini_proms = []

global_cpu_class = "obsolete" # global, backward compat
global_cpu_freq = -1          # global, backward compat

machine = ""

try:
    SIM_source_python_in_module("../scripts/serengeti_extras.py", __name__)
except:
    pass

if not SIM_get_quiet():
    print
    print "Machines based on serengeti_conf.py are only provided for backward "
    print "compatibility. The new component based machines in simics/targets/"
    print "are recommended instead."
    print

def handle_error(msg):
    print
    print "Serengeti configuration error:"
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

def valid_cpu_board(board_no):
    if chassis_list[machine][cur_node[machine]] == "SP":
        if board_no == 0 or board_no == 2:
            return 1
    elif chassis_list[machine][cur_node[machine]] != "DS":
        if board_no == 0 or board_no == 2 or board_no == 4:
            return 1
    else: # DS
        if board_no >= 0 and board_no < 6:
            return 1
    return 0

def valid_io_board(board_no):
    if chassis_list[machine][cur_node[machine]] == "SP":
        if board_no == 6 or board_no == 8:
            return 1
    elif chassis_list[machine][cur_node[machine]] != "DS":
        if board_no == 6 or board_no == 8:
            return 1
    else: # DS
        if board_no >= 6 and board_no < 10:
            return 1
    return 0

def mac_string_to_list(mac_address):
    ether = []
    eth = string.split(mac_address, ":")
    for i in range(0, len(eth)):
        ether.append(int(eth[i], 16))
    return ether

def set_current_node(node_no):
    global cur_node
    cur_node[machine] = node_no

def get_cpu_id(board_no, cpu_no):
    return (cur_node[machine] * AID_PER_NODE) + (CPU_PER_BOARD * board_no) + cpu_no

def get_cpu_id_node(node, board_no, cpu_no):
    return (node * AID_PER_NODE) + (CPU_PER_BOARD * board_no) + cpu_no

def get_io_id(board_no, io_no):
    io_board = board_no - CPU_BRD_PER_NODE
    return (cur_node[machine] * AID_PER_NODE) + CPU_PER_NODE + (IO_PER_BOARD * io_board) + io_no

def create_cheerio_hme_prom(name):
    object_list[machine] += ([OBJECT(name + "_prom", "rom",
                                     image = OBJ(name + "_prom_image"))] +
                             [OBJECT(name + "_prom_image", "image",
                                     size = 0x1000000,
                                     files = [["cheerio_hme.fcode", "ro", 0, 19488]],
                                     queue ="<queue" + `cur_node[machine]` + ">")])

def create_isp2200_prom(name):
    global have_isp2200_prom
    object_list[machine] += ([OBJECT(name + "_prom", "rom",
                                     image = OBJ("serengeti_isp2200_prom_image"))])
    if have_isp2200_prom:
        return
    have_isp2200_prom = 1
    object_list[machine] += ([OBJECT("serengeti_isp2200_prom_image", "image",
                                     size = 0x10000,
                                     files = [["isp2200.fcode", "ro", 0, 111356]],
                                     queue ="<queue" + `cur_node[machine]` + ">")])
    
def create_isp1040_prom(name):
    global have_isp1040_prom
    object_list[machine] += ([OBJECT(name + "_prom", "rom",
                                     image = OBJ("serengeti_isp1040_prom_image"))])
    if have_isp1040_prom:
        return
    have_isp1040_prom = 1
    object_list[machine] += ([OBJECT("serengeti_isp1040_prom_image", "image",
                                     size = 0x10000,
                                     files = [["isp1040.fcode", "ro", 0, 43540]],
                                     queue ="<queue" + `cur_node[machine]` + ">")])

conf_list = []

def set_machine(mach):
    global machine, conf_list
    machine = mach
    try:
        conf_list = object_list[machine]
    except:
        pass

first_node = 0

def create_serengeti_node(cpu_freq = -1, node_no = 0, chassis = "DS", cpu_class = "obsolete", node_mem = 0):
    global object_list, global_cpu_freq, cur_node, mem_node, master_node, chassis_list
    global have_cpu_prom, have_sim_object, conf_list, global_cpu_class
    global first_node
    if configuration_loaded("create_serengeti_node"):
        return

    try:
        # check if it is a new machine
        node_list[machine]
    except Exception, msg:
        machine_list.append(machine)
        first_node = 0

    if first_node == 0:
        board_list[machine] = {}      # per node
        cpu_list[machine] = []        # global
        node_list[machine] = []       # global
        pci_slots[machine] = {}       # global, index with (low) schizo nid|aid
        master_node[machine] = -1     # TODO: allow setting
        highest_mem[machine] = 0      # global
        first_sbbc[machine] = {}      # per node
        chassis_list[machine] = {}    # per node
        mem_per_cpu[machine]= {}      # per node
        num_gfx_consoles[machine] = 0
        dist_node_mem[machine] = 0
        object_list[machine] = [OBJECT("%s_component" % iff(len(machine), machine, "serengeti"), "dummy-component")]
        first_node = 1

    cur_node[machine] = node_no
    board_list[machine][cur_node[machine]] = {}
    node_list[machine].append(cur_node[machine])
    mem_per_cpu[machine][cur_node[machine]] = {}
    global_cpu_class = cpu_class
    if cpu_class != "obsolete":
        print "Warning: using obsolete cpu_class argument in create_serengeti_node()"
    if cpu_freq != -1:
        print "Warning: using obsolete cpu_freq argument in create_serengeti_node()"
    global_cpu_freq = cpu_freq
    conf = []
    conf_list = object_list[machine]

    # set master node first time
    chassis_list[machine][node_no] = chassis
    if node_mem != 0:
        dist_node_mem[machine] = 1
    if master_node[machine] == -1:
        master_node[machine] = node_no
    if node_mem == 0 and cur_node[machine] != master_node[machine]:
        mem_node = master_node[machine]
    else:
        mem_node = cur_node[machine]
        if have_cpu_prom == 0:
            have_cpu_prom = 1
            object_list[machine] += ([OBJECT("serengeti_fpost_code", "rom",
                                             image = OBJ("serengeti_fpost_code_image"))] +
                                     [OBJECT("serengeti_fpost_code_image", "image",
                                             size = 0x2000,
                                             queue = "<queue" + `cur_node[machine]` + ">")] +
                                     [OBJECT("serengeti_cpuprom", "rom",
                                             image = OBJ("serengeti_cpuprom_image"))] +
                                     [OBJECT("serengeti_cpuprom_image", "image",
                                             size = 0xbd3b0,
                                             files = [["sgcpu.flash", 1, 0, 0xbd3b0]],
                                             queue = "<queue" + `cur_node[machine]` + ">")])
        conf = ([OBJECT(machine + "phys_mem" + `mem_node`, "memory-space",
                        map = [])] +
                [OBJECT(machine + "phys_io" + `mem_node`, "memory-space",
                        map = [[0x7fff0000000L, OBJ("serengeti_cpuprom"),                          0x0, 0, 0xbd3b0],
                               [0x7fff0102000L, OBJ("serengeti_fpost_code"),                       0x0, 0, 0x2000],
                               [0x7fff0104000L, OBJ(machine + "fpost_data" + `cur_node[machine]`), 0x0, 0, 0x2000],
                               [0x7fff0800060L, OBJ(machine + "empty0_" + `cur_node[machine]`),    0x0, 0x60,   0x10],
                               [0x7fff091e000L, OBJ(machine + "empty1_" + `cur_node[machine]`),    0x0, 0,  0x120]])] +
                [OBJECT(machine + "empty0_" + `cur_node[machine]`, "ram",
                        image = OBJ(machine + "empty0_" + `cur_node[machine]` + "_image"))] +
                [OBJECT(machine + "empty1_" + `cur_node[machine]`, "ram",
                        image = OBJ(machine + "empty1_" + `cur_node[machine]` + "_image"))] +
                [OBJECT(machine + "fpost_data" + `cur_node[machine]`, "ram",
                        image = OBJ(machine + "fpost_data" + `cur_node[machine]` + "_image"))] +
                [OBJECT(machine + "fpost_data" + `cur_node[machine]` + "_image", "image",
                        size = 0x2000,
                        queue = "<queue" + `cur_node[machine]` + ">")] +
                [OBJECT(machine + "empty0_" + `cur_node[machine]` + "_image", "image",
                        size = 0x2000,
                        queue = "<queue" + `cur_node[machine]` + ">")] +
                [OBJECT(machine + "empty1_" + `cur_node[machine]` + "_image", "image",
                        size = 0x2000,
                        queue = "<queue" + `cur_node[machine]` + ">")])
    if cur_node[machine] == master_node[machine]:
        conf += ([OBJECT(machine + "rec0", "recorder")] +
                 [OBJECT(machine + "irqbus0", "sparc-irq-bus")])
    if have_sim_object == 0:
        have_sim_object = 1
        conf += [OBJECT("sim", "sim", handle__outside__memory = 1)]
    object_list[machine] += conf

def add_system_console(hostid, mac_address, tod):
    global object_list
    if configuration_loaded("add_system_console"):
        return
    mac = mac_string_to_list(mac_address)
    if cur_node[machine] != 0:
        return handle_error("There System Console must currently be on node 0")
    conf = ([OBJECT(machine + "nvci" + `cur_node[machine]`, "nvci",
                    security__badlogins = "0",
                    oem__bannerQ = "true",
                    oem__banner = "Simics Serengeti System",
                    nvramrc = "devalias disk /ssm@0,0/pci@19,700000/scsi@2/disk@0,0",
                    use__nvramrcQ = "true",
                    boot__device = "disk",
                    diag__device = "disk",
                    error__reset__recovery = "none",
                    auto__bootQ = "true",
                    boot__command = "boot -v",
                    input__device = "/sgcn",
                    output__device = "/sgcn",
                    fcode__debugQ = "true",
                    use__4xfcodeQ = "true",
                    silent__modeQ = "false",
                    diag__switchQ = "true")] +
            [OBJECT(machine + "sc" + `cur_node[machine]`, "serengeti-console",
                    queue = "<queue" + `cur_node[machine]` + ">",
                    console = OBJ(machine + "con" + `cur_node[machine]`),
                    nvci = OBJ(machine + "nvci" + `cur_node[machine]`),
                    irq_bus = OBJ(machine + "irqbus0"),
                    time = tod,
                    chassis__type = chassis_list[machine][cur_node[machine]],
                    mem__slices = [],
                    boards = [],
                    idprom = mac +
                             [0x39, 0xd0, 0xee, 0xb6] +
                             [(hostid >> 24) & 0xff, (hostid >> 16) & 0xff, (hostid >> 8) & 0xff, hostid & 0xff],
                    recorder = OBJ(machine + "rec0"))] +
            [OBJECT(machine + "con" + `cur_node[machine]`, "xterm-console",
                    title = machine + "System Console",
                    device = OBJ(machine + "sc" + `cur_node[machine]`),
                    char_1c_is_abort = 1,
                    output__timeout = 30,
                    width = 80, height = 24,
                    bg__color = "yellow",
                    fg__color = "black",
                    queue = "<queue" + `cur_node[machine]` + ">")])

    object_list[machine] += conf

def add_cpu_board(board_no, num_cpus, mb, cpu_class = "ultrasparc-iii-plus", cpu_freq = 75):
    global object_list, highest_mem
    if configuration_loaded("add_cpu_board"):
        return
    if not valid_cpu_board(board_no):
        return handle_error("Cannot add CPU board.\nInvalid board number %d, in %s chassis." % (board_no, chassis_list[machine][cur_node[machine]]))
    if num_cpus > CPU_PER_BOARD:
        return handle_error("Cannot add CPU board.\nOnly 0 to %d cpus supported on a board" % CPU_PER_BOARD)
    if board_no >= CPU_BRD_PER_NODE:
        return handle_error("Cannot add CPU board.\nBoard numbers from 0 to %d valid for cpu boards." % (CPU_BRD_PER_NODE - 1))
    if board_list[machine][cur_node[machine]].get(board_no) != None:
        return handle_error("Cannot add CPU board.\nBoard %d already defined on node %d" % (board_no, cur_node[machine]))
    board_list[machine][cur_node[machine]][board_no] = "cpu"

    # backward compatilibity hack
    if global_cpu_class != "obsolete":
        cpu_class = global_cpu_class
        
    if cpu_class == "ultrasparc-iii":
        mmu_class = "cheetah-mmu"
    elif cpu_class == "ultrasparc-iii-plus":
        mmu_class = "cheetah-plus-mmu"
    else:
        return handle_error("Unsupported cpu type: %s" % cpu_class)

    # backward compatilibity hack
    if global_cpu_freq != -1:
        cpu_freq = global_cpu_freq

    mem_per_cpu[machine][cur_node[machine]][board_no] = {}
    
    tot_mb = mb
    max_mem_per_cpu = mem_sizes.keys()
    max_mem_per_cpu.sort()
    for i in range(0, num_cpus):
        cpu_id = get_cpu_id(board_no, i)
        mem_per_cpu[machine][cur_node[machine]][board_no][i] = 0
        for j in range(len(max_mem_per_cpu) - 1, -1, -1):
            if max_mem_per_cpu[j] <= tot_mb:
                tot_mb -= max_mem_per_cpu[j]
                mem_per_cpu[machine][cur_node[machine]][board_no][i] = max_mem_per_cpu[j]
                break # leave j loop
            
    if tot_mb != 0:
        return handle_error("Illegal memory size on board %d. Maximum %d MB per cpu." % (board_no, max_mem_per_cpu[-1:][0]))
    
    conf = ([OBJECT(machine + "cpu" + `i`, cpu_class,
                    queue = OBJ(machine + "cpu" + `i`),
                    control_registers = [["mid", i]],
                    freq_mhz = cpu_freq,
                    mmu = OBJ(machine + "chmmu" + `i`),
                    cpu_group = OBJ(machine + "irqbus0"),
                    processor_number = get_next_cpu_number(),
                    physical_io = OBJ(machine + "phys_io" + `mem_node`),
                    physical_memory = OBJ(machine + "phys_mem" + `mem_node`))
             for i in range(get_cpu_id(board_no, 0), get_cpu_id(board_no, num_cpus))] +
            [OBJECT(machine + "chmmu" + `i`, mmu_class)
             for i in range(get_cpu_id(board_no, 0), get_cpu_id(board_no, num_cpus))])

    mem = get_attribute(object_list[machine], machine + "phys_io" + `mem_node`, "map")
    for i in range(get_cpu_id(board_no, 0), get_cpu_id(board_no, num_cpus)):
        cpu_list[machine].append(i)
        mem += [[0x40000400000L + (i << 23), OBJ(machine + "chmmu" + `i`), 0x0, 0, 0x48]]
    set_attribute(object_list[machine], machine + "phys_io" + `mem_node`, "map", mem)
    object_list[machine] += conf
    if mb > 0:
        bytes = mb * 1024L * 1024
        slice = (CPU_BRD_PER_NODE * cur_node[machine]) + board_no
        mem_start = slice * MB_PER_BOARD * 1024L * 1024
        mem = get_attribute(object_list[machine], machine + "phys_mem" + `mem_node`, "map")
        mem += [[mem_start, OBJ(machine + "memory" + `slice`), 0x0, 0, bytes]]
	highest_mem[machine] = max(highest_mem[machine], mem_start + bytes)
        set_attribute(object_list[machine], machine + "phys_mem" + `mem_node`, "map", mem)
        slices = get_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "mem-slices")
        slices += [[slice, mem_start, bytes, OBJ(machine + "phys_mem" + `mem_node`)]]
        set_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "mem-slices", slices)
        conf = ([OBJECT(machine + "memory" + `slice`, "ram",
                        image = OBJ(machine + "memory" + `slice` + "_image"))] +
                [OBJECT(machine + "memory" + `slice` + "_image", "image",
                        size = bytes,
                        queue = "<queue" + `cur_node[machine]` + ">")])
        object_list[machine] += conf
    boards = get_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "boards")
    boards += [[BRD_PER_NODE * cur_node[machine] + board_no, "cpu", num_cpus, cpu_freq]]
    set_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "boards", boards)

def add_pci_generic(board_no, brd_type, slots):
    global object_list, have_io_prom
    if board_no < CPU_BRD_PER_NODE or board_no >= BRD_PER_NODE:
        return handle_error("Cannot add PCI board.\nBoard numbers from %d to %d valid for IO boards." % (CPU_BRD_PER_NODE, BRD_PER_NODE - 1))
    if board_list[machine][cur_node[machine]].get(board_no) != None:
        return handle_error("Cannot add PCI board.\nBoard %d already defined" % board_no)
    board_list[machine][cur_node[machine]][board_no] = brd_type
    sbbc_aid = get_io_id(board_no, 0)
    try:
        if sbbc_aid < first_sbbc[machine][cur_node[machine]]:
            first_sbbc[machine][cur_node[machine]] = sbbc_aid
    except:
        first_sbbc[machine][cur_node[machine]] = sbbc_aid
    pci_slots[machine][sbbc_aid] = slots
    if have_io_prom == 0:
        have_io_prom = 1
        object_list[machine] += ([OBJECT("serengeti-ioprom", "rom",
                                         image = OBJ("serengeti_ioprom_image"))] +
                                 [OBJECT("serengeti_ioprom_image", "image",
                                          size = 0x3ae50,
                                          files = [["sgpci.flash", 1, 0, 0x3ae50]],
                                          queue = "<queue" + `cur_node[machine]` + ">")])
    conf = ([OBJECT(machine + "schizo" + `i`, "serengeti-schizo",
                    memory__space = OBJ(machine + "phys_mem" + `mem_node`),
                    io__space = OBJ(machine + "phys_io" + `mem_node`),
                    irq_bus = OBJ(machine + "irqbus0"),
                    aid = i,
                    nid = cur_node[machine],
                    pci__busA = OBJ(machine + "pcibus" + `i` + "A"),
                    pci__busB = OBJ(machine + "pcibus" + `i` + "B"),
                    queue = "<queue" + `cur_node[machine]` + ">")
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "pcibus" + `i` + "A", "pci-bus",
                    bridge = OBJ(machine + "schizo" + `i`),
                    memory_space = OBJ(machine + "bus-pcimem" + `i` + "A"),
                    conf_space = OBJ(machine + "bus-pcicfg" + `i` + "A"),
                    io_space = OBJ(machine + "bus-pciio" + `i` + "A"))
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "pcibus" + `i` + "B", "pci-bus",
                    bridge = OBJ(machine + "schizo" + `i`),
                    memory_space = OBJ(machine + "bus-pcimem" + `i` + "B"),
                    conf_space = OBJ(machine + "bus-pcicfg" + `i` + "B"),
                    io_space = OBJ(machine + "bus-pciio" + `i` + "B"))
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "bus-pcicfg" + `i` + "A", "memory-space")
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "bus-pcicfg" + `i` + "B", "memory-space")
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "bus-pcimem" + `i` + "A", "memory-space")
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "bus-pcimem" + `i` + "B", "memory-space")
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "bus-pciio" + `i` + "A", "memory-space")
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "bus-pciio" + `i` + "B", "memory-space")
             for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2))] +
            [OBJECT(machine + "sbbc-pci" + `sbbc_aid`, "sbbc-pci",
                    pci_bus = OBJ(machine + "pcibus" + `sbbc_aid` + "B"),
                    sc = OBJ(machine + "sc" + `cur_node[machine]`),
                    queue = "<queue" + `cur_node[machine]` + ">")])
    set_attribute(conf, machine + "pcibus" + `sbbc_aid` + "B", "pci_devices",
                  [[4, 0, OBJ(machine + "sbbc-pci" + `sbbc_aid`)]])
    set_attribute(conf, machine + "bus-pcimem" + `sbbc_aid` + "B", "map",
                  [[0x0, OBJ("serengeti-ioprom"), 0, 0, 0x3ae50]])
    object_list[machine] += conf
    mem = get_attribute(object_list[machine], machine + "phys_io" + `mem_node`, "map")
    for i in range(get_io_id(board_no, 0), get_io_id(board_no, 2)):
        mem += [[0x40000000000L + (i << 23), OBJ(machine + "schizo" + `i`), 0x0, 0, 0x800000]]
    set_attribute(object_list[machine], machine + "phys_io" + `mem_node`, "map", mem)    
    boards = get_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "boards")
    boards += [[BRD_PER_NODE * cur_node[machine] + board_no, brd_type]]
    set_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "boards", boards)

def slot_to_pci_name(board_no, slot_no):
    schizos = [0, 0, 1, 1]
    buses = ["B", "A", "B", "A"]
    aid = get_io_id(board_no, 0)
    slots = pci_slots[machine][aid]
    slot = 0
    for i in range(0, 4):
        if slot_no < (slot + slots[i]):
            return (aid + schizos[i], buses[i], slot_no - slot + 1)
        slot += slots[i]
    raise StandardError, "Illegal PCI slot number %d. Allowed are 0 .. %d" % (slot_no, slot - 1)

def add_pci_glm(board_no, slot_no):
    global object_list
    if configuration_loaded("add_pci_glm"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add glm device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add glm device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "glm" + slot_name, "SYM53C875",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    scsi_bus = OBJ(machine + "sb" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sb" + slot_name, "scsi-bus",
                    targets = [[7, OBJ(machine + "glm" + slot_name), 0]],
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "glm" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    

def add_pci_pgx64(board_no, slot_no):
    global object_list, num_gfx_consoles, have_pgx64_prom
    if configuration_loaded("add_pci_pgx64"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add pgx64 device.\n%s" % msg)
    num_gfx_consoles[machine] += 1
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add pgx64 device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    object_list[machine] += ([OBJECT(machine + "pgx" + slot_name, "ragexl",
                                     memory_space = OBJ(machine + "bus-pcimem" + bus_name),
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     console = OBJ(machine + "con" + `num_gfx_consoles[machine]`),
                                     expansion_rom = [OBJ(machine + "pgx" + slot_name + "_prom"), 0x20000, 0],
                                     queue = "<queue" + `cur_node[machine]` + ">")] +
                             [OBJECT(machine + "pgx" + slot_name + "_prom", "rom",
                                     image = OBJ("serengeti_pgx64_prom_image"))] +
                             [OBJECT(machine + "con" + `num_gfx_consoles[machine]`, "gfx-console",
                                     x__size = 640,
                                     y__size = 400,
                                     queue = "<queue" + `cur_node[machine]` + ">")])
    if not have_pgx64_prom:
        have_pgx64_prom = 1
        object_list[machine] += ([OBJECT("serengeti_pgx64_prom_image", "image",
                                         size = 0x20000,
                                         files = [["pgx64.fcode", "ro", 0, 65536]],
                                         queue = "<queue" + `cur_node[machine]` + ">")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "pgx" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    

def add_pci_glm_glm(board_no, slot_no):
    global object_list
    if configuration_loaded("add_pci_glm_glm"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add glm+glm device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add glm+glm device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "glm" + slot_name + "_0", "SYM53C875",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    scsi_bus = OBJ(machine + "sb" + slot_name + "_0"),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sb" + slot_name + "_0", "scsi-bus",
                    targets = [[7, OBJ(machine + "glm" + slot_name + "_0"), 0]],
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "glm" + slot_name + "_1", "SYM53C875",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    scsi_bus = OBJ(machine + "sb" + slot_name + "_1"),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sb" + slot_name + "_1", "scsi-bus",
                    targets = [[7, OBJ(machine + "glm" + slot_name + "_1"), 0]],
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "glm" + slot_name + "_0")],
                 [pci_slot, 1, OBJ(machine + "glm" + slot_name + "_1")]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    

def add_pci_hme_simple(board_no, slot_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_hme"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add hme device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add hme device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "hme" + slot_name, "cheerio-hme",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    expansion_rom = [OBJ(machine + "hme" + slot_name + "_prom"), 0x1000000, 0],
                    recorder = OBJ(machine + "rec0"),
                    mac_address = mac_address,
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    create_cheerio_hme_prom(machine + "hme" + slot_name)
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "hme" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    

def add_pci_hme(board_no, slot_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_hme"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add hme device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add hme device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "hme" + slot_name, "cheerio-hme",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    expansion_rom = [OBJ(machine + "hme" + slot_name + "_prom"), 0x1000000, 0],
                    recorder = OBJ(machine + "rec0"),
                    mac_address = mac_address,
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "e2bus" + slot_name, "cheerio-e2bus",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    create_cheerio_hme_prom(machine + "hme" + slot_name)
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "e2bus" + slot_name)],
                 [pci_slot, 1, OBJ(machine + "hme" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    

def add_pci_qlc(board_no, slot_no, loop_id):
    global object_list
    if configuration_loaded("add_pci_qlc"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add qlc device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add qlc device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    object_list[machine] += ([OBJECT(machine + "qlc" + slot_name, "ISP2200",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     loop_id = loop_id,
                                     expansion_rom = [OBJ(machine + "qlc" + slot_name + "_prom"), 0x10000, 0],
                                     queue = "<queue" + `cur_node[machine]` + ">")])
    create_isp2200_prom(machine + "qlc" + slot_name)
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "qlc" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    

def add_pci_qlc_qlc(board_no, slot_no, loop_id0, loop_id1):
    global object_list
    if configuration_loaded("add_pci_qlc_qlc"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add qlc+qlc device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add qlc+qlc device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "bridge" + slot_name, "i21152",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    secondary_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sub-pcibus" + slot_name, "pci-bus",
                    bridge = OBJ(machine + "bridge" + slot_name),
                    pci_devices = [[4, 0, OBJ(machine + "qlc" + slot_name + "_0")],
                                   [5, 0, OBJ(machine + "qlc" + slot_name + "_1")]],
                    memory_space = OBJ(machine + "sub-pcimem" + slot_name),
                    conf_space = OBJ(machine + "sub-pcicfg" + slot_name),
                    io_space = OBJ(machine + "sub-pciio" + slot_name))] +
            [OBJECT(machine + "sub-pciio" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcicfg" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcimem" + slot_name, "memory-space")] +
            [OBJECT(machine + "qlc" + slot_name + "_0", "ISP2200",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    loop__id = loop_id0,
                    expansion_rom = [OBJ(machine + "qlc" + slot_name + "_0" + "_prom"), 0x10000, 0],
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "qlc" + slot_name + "_1", "ISP2200",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    expansion_rom = [OBJ(machine + "qlc" + slot_name + "_1" + "_prom"), 0x10000, 0],
                    loop__id = loop_id1,
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    create_isp2200_prom(machine + "qlc" + slot_name + "_0")
    create_isp2200_prom(machine + "qlc" + slot_name + "_1")
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "bridge" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)

def add_pci_hme_isp(board_no, slot_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_hme_isp"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add hme+isp device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add hme+isp device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "bridge" + slot_name, "i21152",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    secondary_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sub-pcibus" + slot_name, "pci-bus",
                    bridge = OBJ(machine + "bridge" + slot_name),
                    pci_devices = [[0, 0, OBJ(machine + "e2bus" + slot_name)],
                                   [0, 1, OBJ(machine + "hme" + slot_name)],
                                   [4, 0, OBJ(machine + "isp" + slot_name)]],
                    memory_space = OBJ(machine + "sub-pcimem" + slot_name),
                    conf_space = OBJ(machine + "sub-pcicfg" + slot_name),
                    io_space = OBJ(machine + "sub-pciio" + slot_name))] +
            [OBJECT(machine + "sub-pciio" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcicfg" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcimem" + slot_name, "memory-space")] +
            [OBJECT(machine + "sb" + slot_name, "scsi-bus",
                    targets = [[7, OBJ(machine + "isp" + slot_name), 0]],
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "isp" + slot_name, "ISP1040",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    scsi_id = 7,
                    expansion_rom = [OBJ(machine + "isp" + slot_name + "_prom"), 0x10000, 0],
                    scsi_bus = OBJ(machine + "sb" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "e2bus" + slot_name, "cheerio-e2bus",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "hme" + slot_name, "cheerio-hme",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    expansion_rom = [OBJ(machine + "hme" + slot_name + "_prom"), 0x1000000, 0],
                    recorder = OBJ(machine + "rec0"),
                    mac_address = mac_address,
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    create_cheerio_hme_prom(machine + "hme" + slot_name)
    create_isp1040_prom(machine + "isp" + slot_name)
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "bridge" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)


def add_pci_ce_single(board_no, slot_no, mac_address):
    global object_list, cassini_proms
    if configuration_loaded("add_pci_ce"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add ce device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add ce device.\n"
                            "No PCI bus exists on board %d with slot %d" % (board_no, slot_no))

    object_list[machine] += ([OBJECT(machine + "ce" + slot_name, "cassini",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     mac_address = mac_address,
                                     expansion_rom = [OBJ(machine + "ce" + slot_name + "_prom"), 0x100000, 0],
                                     recorder = OBJ(machine + "rec0"),
                                     queue = "<queue" + `cur_node[machine]` + ">")] +
                             [OBJECT(machine + "ce_sub1_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 1)] +
                             [OBJECT(machine + "ce_sub2_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 2)] +
                             [OBJECT(machine + "ce_sub3_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 3)] +
                             [OBJECT(machine + "ce" + slot_name + "_prom", "rom",
                                     image = OBJ(machine + "cassini_prom_image" + slot_name))] +
                             [OBJECT(machine + "cassini_prom_image" + slot_name, "image",
                                     size = 0x10000,
                                     files = [["cassini_plus.fcode", "ro", 0, 0x10000]],
                                     queue ="<queue" + `cur_node[machine]` + ">")])
    cassini_proms += [[machine + "cassini_prom_image" + slot_name, mac_address]]
    try:
        pci_devs = get_attribute(object_list[machine],
                                 machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "ce" + slot_name)]]
    set_attribute(object_list[machine],
                  machine + "pcibus" + bus_name, "pci_devices", pci_devs)    


def add_pci_ce(board_no, slot_no, mac_address):
    global object_list, cassini_proms
    if configuration_loaded("add_pci_ce"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add ce device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add ce device.\n"
                            "No PCI bus exists on board %d with slot %d" % (board_no, slot_no))

    object_list[machine] += ([OBJECT(machine + "bridge" + slot_name, "i21152",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     secondary_bus = OBJ(machine + "sub-pcibus" + slot_name),
                                     queue = "<queue" + `cur_node[machine]` + ">")] +
                             [OBJECT(machine + "sub-pcibus" + slot_name, "pci-bus",
                                     bridge = OBJ(machine + "bridge" + slot_name),
                                     pci_devices = [[0, 0, OBJ(machine + "ce" + slot_name)],
                                                    [0, 1, OBJ(machine + "ce_sub1_" + slot_name)],
                                                    [0, 2, OBJ(machine + "ce_sub2_" + slot_name)],
                                                    [0, 3, OBJ(machine + "ce_sub3_" + slot_name)]],
                                     memory_space = OBJ(machine + "sub-pcimem" + slot_name),
                                     conf_space = OBJ(machine + "sub-pcicfg" + slot_name),
                                     io_space = OBJ(machine + "sub-pciio" + slot_name),
                                     interrupt = OBJ(machine + "bridge" + slot_name))] +
                             [OBJECT(machine + "sub-pciio" + slot_name, "memory-space")] +
                             [OBJECT(machine + "sub-pcicfg" + slot_name, "memory-space")] +
                             [OBJECT(machine + "sub-pcimem" + slot_name, "memory-space")] +
                             [OBJECT(machine + "ce" + slot_name, "cassini",
                                     pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                                     mac_address = mac_address,
                                     expansion_rom = [OBJ(machine + "ce" + slot_name + "_prom"), 0x100000, 0],
                                     recorder = OBJ(machine + "rec0"),
                                     queue = "<queue" + `cur_node[machine]` + ">")] +
                             [OBJECT(machine + "ce_sub1_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 1)] +
                             [OBJECT(machine + "ce_sub2_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 2)] +
                             [OBJECT(machine + "ce_sub3_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 3)] +
                             [OBJECT(machine + "ce" + slot_name + "_prom", "rom",
                                     image = OBJ(machine + "cassini_prom_image" + slot_name))] +
                             [OBJECT(machine + "cassini_prom_image" + slot_name, "image",
                                     size = 0x10000,
                                     files = [["cassini_plus.fcode", "ro", 0, 0x10000]],
                                     queue ="<queue" + `cur_node[machine]` + ">")])
    cassini_proms += [[machine + "cassini_prom_image" + slot_name, mac_address]]
    try:
        pci_devs = get_attribute(object_list[machine],
                                 machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "bridge" + slot_name)]]
    set_attribute(object_list[machine],
                  machine + "pcibus" + bus_name, "pci_devices", pci_devs)


def add_pci_bge(board_no, slot_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_bge"):
        return
    ether = mac_string_to_list(mac_address)
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add bge device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add bge device.\n"
                            "No PCI bus exists on board %d with slot %d" % (board_no, slot_no))

    object_list[machine] += ([OBJECT(machine + "bge" + slot_name, "BCM5703C",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     recorder = OBJ(machine + "rec0"),
                                     mac_address = ether,
                                     queue ="<queue" + `cur_node[machine]` + ">")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "bge" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    

def add_pci_dual_bge(board_no, slot_no, mac_address0, mac_address1):
    global object_list
    if configuration_loaded("add_pci_bge"):
        return
    ether0 = mac_string_to_list(mac_address0)
    ether1 = mac_string_to_list(mac_address1)
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add dual bge device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add dual bge device.\n"
                            "No PCI bus exists on board %d with slot %d" % (board_no, slot_no))

    object_list[machine] += ([OBJECT(machine + "bge" + slot_name + "_0", "BCM5704C",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     recorder = OBJ(machine + "rec0"),
                                     mac_address = ether0,
                                     is_mac1 = 0,
                                     other_bcm = OBJ(machine + "bge" + slot_name + "_1"),
                                     queue ="<queue" + `cur_node[machine]` + ">")] +
                             [OBJECT(machine + "bge" + slot_name + "_1", "BCM5704C",
                                     pci_bus = OBJ(machine + "pcibus" + bus_name),
                                     recorder = OBJ(machine + "rec0"),
                                     mac_address = ether1,
                                     is_mac1 = 1,
                                     other_bcm = OBJ(machine + "bge" + slot_name + "_0"),
                                     queue ="<queue" + `cur_node[machine]` + ">")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "bge" + slot_name + "_0")],
                 [pci_slot, 1, OBJ(machine + "bge" + slot_name + "_1")]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    


def add_cpci_qlc_qlc(board_no, slot_no, loop_id0, loop_id1):
    global object_list
    if configuration_loaded("add_cpci_qlc_qlc"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add qlc+qlc device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add qlc+qlc device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "bridge_prim_" + slot_name, "i21554-prim",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    scnd_interface = OBJ(machine + "bridge_scnd_" + slot_name),
                    # default setup values
                    base_setup = [0xfffff000, 0xffff0001, 0xfc000000, 0x00000000, 0x00000000, 0x80000000, 0xe0000000],
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "bridge_scnd_" + slot_name, "i21554-scnd",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    prim_interface = OBJ(machine + "bridge_prim_" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sub-pcibus" + slot_name, "pci-bus",
                    bridge = OBJ(machine + "bridge_scnd_" + slot_name),
                    pci_devices = [[5, 0, OBJ(machine + "qlc" + slot_name + "_0")],
                                   [6, 0, OBJ(machine + "qlc" + slot_name + "_1")]],
                    memory_space = OBJ(machine + "sub-pcimem" + slot_name),
                    conf_space = OBJ(machine + "sub-pcicfg" + slot_name),
                    io_space = OBJ(machine + "sub-pciio" + slot_name))] +
            [OBJECT(machine + "sub-pciio" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcicfg" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcimem" + slot_name, "memory-space")] +
            [OBJECT(machine + "qlc" + slot_name + "_0", "ISP2200",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    expansion_rom = [OBJ(machine + "qlc" + slot_name + "_0" + "_prom"), 0x10000, 0],
                    loop__id = loop_id0,
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "qlc" + slot_name + "_1", "ISP2200",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    expansion_rom = [OBJ(machine + "qlc" + slot_name + "_1" + "_prom"), 0x10000, 0],
                    loop__id = loop_id1,
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    create_isp2200_prom(machine + "qlc" + slot_name + "_0")
    create_isp2200_prom(machine + "qlc" + slot_name + "_1")
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "bridge_prim_" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)    


def add_cpci_hme_isp(board_no, slot_no, mac_address):
    global object_list
    if configuration_loaded("add_cpci_hme_isp"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add hme+isp device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add hme+isp device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "bridge_prim_" + slot_name, "i21554-prim",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    scnd_interface = OBJ(machine + "bridge_scnd_" + slot_name),
                    # default setup values
                    base_setup = [0xfffff000, 0xffff0001, 0xfc000000, 0x00000000, 0x00000000, 0x80000000, 0xe0000000],
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "bridge_scnd_" + slot_name, "i21554-scnd",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    prim_interface = OBJ(machine + "bridge_prim_" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sub-pcibus" + slot_name, "pci-bus",
                    bridge = OBJ(machine + "bridge_scnd_" + slot_name),
                    pci_devices = [[1, 0, OBJ(machine + "e2bus" + slot_name)],
                                   [1, 1, OBJ(machine + "hme" + slot_name)],
                                   [5, 0, OBJ(machine + "isp" + slot_name)]],
                    memory_space = OBJ(machine + "sub-pcimem" + slot_name),
                    conf_space = OBJ(machine + "sub-pcicfg" + slot_name),
                    io_space = OBJ(machine + "sub-pciio" + slot_name))] +
            [OBJECT(machine + "sub-pciio" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcicfg" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcimem" + slot_name, "memory-space")] +
            [OBJECT(machine + "sb" + slot_name, "scsi-bus",
                    targets = [[7, OBJ(machine + "isp" + slot_name), 0]],
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "isp" + slot_name, "ISP1040",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    scsi_id = 7,
                    expansion_rom = [OBJ(machine + "isp" + slot_name + "_prom"), 0x10000, 0],
                    scsi_bus = OBJ(machine + "sb" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "e2bus" + slot_name, "cheerio-e2bus",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "hme" + slot_name, "cheerio-hme",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    expansion_rom = [OBJ(machine + "hme" + slot_name + "_prom"), 0x1000000, 0],
                    recorder = OBJ(machine + "rec0"),
                    mac_address = mac_address,
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    create_cheerio_hme_prom(machine + "hme" + slot_name)
    create_isp1040_prom(machine + "isp" + slot_name)
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "bridge_prim_" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)


def add_cpci_isp_isp(board_no, slot_no):
    global object_list
    if configuration_loaded("add_cpci_isp_isp"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add isp+isp device.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    slot_name = bus_name + "_" + `pci_slot`
    if not object_exists(object_list[machine], machine + "pcibus" + bus_name):
        return handle_error("Cannot add isp+isp device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "bridge_prim_" + slot_name, "i21554-prim",
                    pci_bus = OBJ(machine + "pcibus" + bus_name),
                    scnd_interface = OBJ(machine + "bridge_scnd_" + slot_name),
                    # default setup values
                    base_setup = [0xfffff000, 0xffff0001, 0xfc000000, 0x00000000, 0x00000000, 0x80000000, 0xe0000000],
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "bridge_scnd_" + slot_name, "i21554-scnd",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    prim_interface = OBJ(machine + "bridge_prim_" + slot_name),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sub-pcibus" + slot_name, "pci-bus",
                    bridge = OBJ(machine + "bridge_scnd_" + slot_name),
                    pci_devices = [[5, 0, OBJ(machine + "isp" + slot_name + "_0")],
                                   [6, 0, OBJ(machine + "isp" + slot_name + "_1")]],
                    memory_space = OBJ(machine + "sub-pcimem" + slot_name),
                    conf_space = OBJ(machine + "sub-pcicfg" + slot_name),
                    io_space = OBJ(machine + "sub-pciio" + slot_name))] +
            [OBJECT(machine + "sub-pciio" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcicfg" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcimem" + slot_name, "memory-space")] +
            [OBJECT(machine + "sb" + slot_name + "_0", "scsi-bus",
                    targets = [[7, OBJ(machine + "isp" + slot_name + "_0"), 0]],
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "isp" + slot_name + "_0", "ISP1040",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    scsi_id = 7,
                    expansion_rom = [OBJ(machine + "isp" + slot_name + "_0" + "_prom"), 0x10000, 0],
                    scsi_bus = OBJ(machine + "sb" + slot_name + "_0"),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "isp" + slot_name + "_1", "ISP1040",
                    pci_bus = OBJ(machine + "sub-pcibus" + slot_name),
                    scsi_id = 7,
                    expansion_rom = [OBJ(machine + "isp" + slot_name + "_1" + "_prom"), 0x10000, 0],
                    scsi_bus = OBJ(machine + "sb" + slot_name + "_1"),
                    queue = "<queue" + `cur_node[machine]` + ">")] +
            [OBJECT(machine + "sb" + slot_name + "_1", "scsi-bus",
                    targets = [[7, OBJ(machine + "isp" + slot_name + "_1"), 0]],
                    queue = "<queue" + `cur_node[machine]` + ">")])
    object_list[machine] += conf
    create_isp1040_prom(machine + "isp" + slot_name + "_0")
    create_isp1040_prom(machine + "isp" + slot_name + "_1")
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[pci_slot, 0, OBJ(machine + "bridge_prim_" + slot_name)]]
    set_attribute(object_list[machine], machine + "pcibus" + bus_name, "pci_devices", pci_devs)


def add_scsi_disk(board_no, slot_no, scsi_target, geometry = None, size = None, controller = -1, files = ""):
    global object_list
    if configuration_loaded("add_scsi_disk"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add SCSI disk.\n%s" % msg)

    if geometry:
        print "add_scsi_disk(): Warning, using obsolete argument 'geometry'"
        g_size = geometry[0] * geometry[1] * geometry[2] * 512
        if size and g_size != size:
            handle_error("add_scsi_disk(): Geometry and size does not match")
            return
        size = g_size
    elif not size:
        # check for size since is is still optional
        handle_error("add_scsi_disk(): Size of disk not specified")
        return
    else:
        geometry = [size / 512, 1, 1]

    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    if controller == -1:
        slot_name = bus_name + "_" + `pci_slot`
    else:
        slot_name = bus_name + "_" + `pci_slot` + "_" + `controller`
    tgt_name = slot_name + "_" + `scsi_target`
    if not object_exists(object_list[machine], machine + "sb" + slot_name):
        if object_substr_exists(object_list[machine], "sb" + slot_name):
            return handle_error("Cannot add SCSI disk.\nMultiple SCSI buses exist on board %d, slot %d" % (board_no, slot_no))
        return handle_error("Cannot add SCSI disk.\nNo SCSI bus exists on board %d, slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "sd" + tgt_name, "scsi-disk",
                    image = OBJ(machine + "sd" + tgt_name + "_image"),
                    scsi_bus = OBJ(machine + "sb" + slot_name),
                    scsi_target = scsi_target,
                    queue = "<queue" + `cur_node[machine]` + ">",
                    geometry = geometry)] +
            [OBJECT(machine + "sd" + tgt_name + "_image", "image",
                    size = size,
                    queue = "<queue" + `cur_node[machine]` + ">")])
    if files != "":
        set_attribute(conf, machine + "sd" + tgt_name + "_image", "files", files)
    object_list[machine] += conf
    tgts = get_attribute(object_list[machine], machine + "sb" + slot_name, "targets")
    tgts += [[scsi_target, OBJ(machine + "sd" + tgt_name), 0]]
    set_attribute(object_list[machine], machine + "sb" + slot_name, "targets", tgts)

def add_fc_disk(board_no, slot_no, loop_id, node_name, port_name, geometry = None, size = None, controller = -1, files = ""):
    global object_list
    if configuration_loaded("add_fc_disk"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add FC disk.\n%s" % msg)

    if geometry:
        print "add_fc_disk(): Warning, using obsolete argument 'geometry'"
        g_size = geometry[0] * geometry[1] * geometry[2] * 512
        if size and g_size != size:
            handle_error("add_fc_disk(): Geometry and size does not match")
            return
        size = g_size
    elif not size:
        # check for size since is is still optional
        handle_error("add_fc_disk(): Size of disk not specified")
        return        
    else:
        geometry = [size / 512, 1, 1]

    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    if controller == -1:
        slot_name = bus_name + "_" + `pci_slot`
    else:
        slot_name = bus_name + "_" + `pci_slot` + "_" + `controller`
    tgt_name = slot_name + "_" + `loop_id`
    if not object_exists(object_list[machine], machine + "qlc" + slot_name):
        if object_substr_exists(object_list[machine], "qlc" + slot_name):
            return handle_error("Cannot add FC disk.\nMultiple FC controllers exist on board %d, slot %d" % (board_no, slot_no))
        return handle_error("Cannot add FC disk.\nNo FC controller exists on board %d, slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "fc" + tgt_name, "fc-disk",
                    image = OBJ(machine + "fc" + tgt_name + "_image"),
                    fc__controller = OBJ(machine + "qlc" + slot_name),
                    loop__id = loop_id,
                    queue = "<queue" + `cur_node[machine]` + ">",
                    node__name = node_name,
                    port__name = port_name,
                    geometry = geometry)] +
            [OBJECT(machine + "fc" + tgt_name + "_image", "image",
                    size = size,
                    queue = "<queue" + `cur_node[machine]` + ">")])
    if files != "":
        set_attribute(conf, machine + "fc" + tgt_name + "_image", "files", files)
    object_list[machine] += conf

def add_scsi_cdrom(board_no, slot_no, scsi_target, controller = -1, file = ""):
    global object_list
    if configuration_loaded("add_scsi_cdrom"):
        return
    try:
        slot_id = slot_to_pci_name(board_no, slot_no)
    except Exception, msg:
        return handle_error("Cannot add SCSI CD-ROM.\n%s" % msg)
    bus_name = `slot_id[0]` + slot_id[1]
    pci_slot = slot_id[2]
    if controller == -1:
        slot_name = bus_name + "_" + `pci_slot`
    else:
        slot_name = bus_name + "_" + `pci_slot` + "_" + `controller`
    tgt_name = slot_name + "_" + `scsi_target`
    if not object_exists(object_list[machine], machine + "sb" + slot_name):
        if object_substr_exists(object_list[machine], "sb" + slot_name):
            return handle_error("Cannot add SCSI CD-ROM.\nMultiple SCSI buses exist on board %d, slot %d" % (board_no, slot_no))
        return handle_error("Cannot add SCSI CD-ROM.\nNo SCSI bus exists on board %d, slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "cd" + tgt_name, "scsi-cdrom",
                    scsi_bus = OBJ(machine + "sb" + slot_name),
                    scsi_target = scsi_target,
                    queue = "<queue" + `cur_node[machine]` + ">")])
    if file == "":
        pass
    elif string.find(file, "/dev/") == 0 or string.find(file, "/vol/rdsk/") == 0:
        conf += [OBJECT(machine + "host-cd" + tgt_name, "host-cdrom", file = file)]
        set_attribute(conf, machine + "cd" +tgt_name, "cd-media", OBJ(machine + "host-cd" + tgt_name))
        print "setting media %s" % ("host-cd" + tgt_name)
    else:
        conf += [OBJECT(machine + "file-cd" + tgt_name, "file-cdrom", file = file)]
        set_attribute(conf, machine + "cd" +tgt_name, "cd-media", OBJ(machine + "file-cd" + tgt_name))
        print "setting media %s" % ("file-cd" + tgt_name)
    object_list[machine] += conf
    tgts = get_attribute(object_list[machine], machine + "sb" + slot_name, "targets")
    tgts += [[scsi_target, OBJ(machine + "cd" + tgt_name), 0]]
    set_attribute(object_list[machine], machine + "sb" + slot_name, "targets", tgts)

def add_pci8_board(board_no):
    if not valid_io_board(board_no):
        return handle_error("Cannot add 8 slot PCI board.\nInvalid board number %d, in %s chassis." % (board_no, chassis_list[machine][cur_node[machine]]))
    if chassis_list[machine][cur_node[machine]] == "SP":
        return handle_error("8 slot PCI board not allowed in 'SP' chassis")
    if configuration_loaded("add_pci8_board"):
        return
    add_pci_generic(board_no, "pci",  [3, 1, 3, 1])

def add_cpci4_board(board_no):
    if not valid_io_board(board_no):
        return handle_error("Cannot add 4 slot cPCI board.\nInvalid board number %d, in %s chassis." % (board_no, chassis_list[machine][cur_node[machine]]))
    if chassis_list[machine][cur_node[machine]] == "SP":
        return handle_error("4 slot cPCI board not allowed in 'SP' chassis")
    if configuration_loaded("add_cpci4_board"):
        return
    add_pci_generic(board_no, "cpci4", [1, 1, 1, 1])
    pass

def add_sp_cpci6_board(board_no):
    if not valid_io_board(board_no):
        return handle_error("Cannot add 6 slot cPCI board.\nInvalid board number %d, in %s chassis." % (board_no, chassis_list[machine][cur_node[machine]]))
    if chassis_list[machine][cur_node[machine]] != "SP":
        return handle_error("6 slot cPCI board only allowed in 'SP' chassis")
    if configuration_loaded("add_sp_cpci6_board"):
        return
    add_pci_generic(board_no, "sp-cpci6", [2, 1, 2, 1])
    pass


def set_memory_conf(node, board):
    global object_list
    bank_info = []
    cpus_with_mem = mem_per_cpu[machine][node][board].keys()
    mem_on_cpu = mem_per_cpu[machine][node][board].values()

    # first find all banks
    for cpu in range(0, len(cpus_with_mem)):
        cpu_mem = mem_on_cpu[cpu]
        num_banks = mem_sizes[cpu_mem]
        for i in range(0, num_banks):
            bank_info.append([cpus_with_mem[cpu], i + 1, cpu_mem / num_banks, -1])


    # go through all banks and calculate start offset
    mem_start = ((CPU_BRD_PER_NODE * node) + board) * MB_PER_BOARD
    bank_sizes = bank_mask.keys()
    bank_sizes.sort()
    bank_sizes.reverse()
    for i in bank_sizes:
        for j in bank_info:
            if j[2] == i:
                j[3] = (mem_start * 1024 * 1024L)
                mem_start += i

    # finally set the bank info for each cpu bank
    banks = []
    for bank in bank_info:
        cpu_id = get_cpu_id_node(node, board, bank[0])
        banks.append([cpu_id] + bank[1:3])
        # print "cpu %d - MADR: %d %dMB (mask = 0x%x) start 0x%x" % (cpu_id, bank[1], bank[2], bank_mask[bank[2]], bank[3])
        madr = ((1L << 63)                          # valid
                | ((0L + bank_mask[bank[2]]) << 41) # mask  (UK)
                | ((bank[3] >> 26) << 20)           # match (UM)
                | (0xf << 14)                       # mask  (LK) 1-way interleave
                | (0x0 << 8))                       # match (LM)
        mmu = get_attribute(object_list[machine], machine + "cpu%d" % cpu_id, "mmu")
        set_attribute(object_list[machine], get_conf_object_name(mmu), "madr_%d" % bank[1], madr)

    # also tell the Serengeti Console about the memory configuration
    try:
        all_banks = get_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "mem-banks")
    except:
        all_banks = []
    all_banks += banks
    set_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "mem-banks", all_banks)

global_cpu = {}

def set_global_cpu(node):
    global global_cpu
    objs = []
    global_cpu[machine][node] = None
    for i in object_list[machine]:
        if i[1][:10] == "ultrasparc":
            cpu = i[0]
            # works while we only set mid in the list
            mid = get_attribute(object_list[machine], i[0], "control_registers")[0][1]
            if node == (mid / 32):
                global_cpu[machine][node] = cpu
                break
    if global_cpu[machine][node] == None:
        handle_error("No processor defined on node %d" % node)
    for i in object_list[machine]:
        try:
            queue = get_attribute(object_list[machine], i[0], "queue")
            if queue == "<queue" + `node` + ">":
                set_attribute(object_list[machine], i[0], "queue", OBJ(global_cpu[machine][node]))
        except:
            pass
    # TODO: handle more correct
    if node == master_node[machine]:
        set_attribute(object_list[machine], machine + "sc" + `master_node[machine]`, "master-cpu", OBJ(global_cpu[machine][node]))

def create_cpu_spaces():
    global object_list
    for i in object_list[machine]:
        if i[1][:10] == "ultrasparc":
            space = machine + "%s_mem" % i[0]
            set_attribute(object_list[machine], i[0], "physical_memory", OBJ(space))
            object_list[machine] += [OBJECT(space, "memory-space",
                                            map = [[0, OBJ(machine + "phys_mem0"), 0, 0, 0xffffffffffffffff]])]
            space = machine + "%s_io" % i[0]
            set_attribute(object_list[machine], i[0], "physical_io", OBJ(space))
            object_list[machine] += [OBJECT(space, "memory-space",
                                            map = [[0, OBJ(machine + "phys_io0"), 0, 0, 0xffffffffffffffff]])]

def init_cheerio_hme_prom():
    dat = (0x90, 0x28, 0x00, 0x4e, 0x41, 0x06)
    for o in object_list[machine]:
        if o[1] == "cheerio-hme":
            try:
                obj = SIM_get_object(o[0])
                image = obj.expansion_rom[0].image
                mac = mac_string_to_list(get_attribute(object_list[machine], o[0], "mac_address"))
                for i in range(6):
                    image.byte_access[0xc010 + i] = dat[i]
                for i in range(len(mac)):
                    image.byte_access[0xc016 + i] = mac[i]
            except:
                pass

def get_configuration():
    global object_list, machine
    all_objs = []
    for mach in machine_list:
        machine = mach

        all_cpus = []
        for i in cpu_list[machine]:
            all_cpus.append(OBJ(machine + "cpu" + `i`))

        global_cpu[machine] = {}
        for n in node_list[machine]:
            set_global_cpu(n)
            # setup memory registers
            for brd in board_list[machine][n].keys():
                if board_list[machine][n][brd] == "cpu":
                    set_memory_conf(n, brd)
            try:
                # check if we have sc on this node
                queue = get_attribute(object_list[machine], machine + "sc" + `n`, "queue")
                set_attribute(object_list[machine], machine + "sc" + `n`, "iosram-sbbc",
                              OBJ(machine + "sbbc-pci%d" % first_sbbc[machine][n]))
                io_spaces = []
                for nn in node_list[machine]:
                    if dist_node_mem[machine] == 0:
                        io_spaces.append([nn, OBJ(machine + "phys_io" + `master_node[machine]`)])
                    else:
                        io_spaces.append([nn, OBJ(machine + "phys_io" + `nn`)])
                set_attribute(object_list[machine], machine + "sc" + `n`, "io_spaces", io_spaces)
            except:
                pass # "No sc on node %d" % n

        object_list[machine] += ([OBJECT(machine + "system", "serengeti-system",
                                         master_cpu = OBJ(global_cpu[machine][0]),
                                         all_cpus = all_cpus,
                                         nvci = OBJ(machine + "nvci0"),
                                         max_mem_address = highest_mem[machine])])

        #finally add hostfs
        mem = get_attribute(object_list[machine], machine + "phys_mem" + `master_node[machine]`, "map")
        mem += [[0x7fff07ffff0, OBJ(machine + "hfs0"), 0, 0x0, 0x10]]
        mem = set_attribute(object_list[machine], machine + "phys_mem" + `master_node[machine]`, "map", mem)
        hfs_conf = ([OBJECT(machine + "hfs0", "hostfs")])
        object_list[machine] += hfs_conf
        all_objs += object_list[machine]
    return all_objs

def post_configuration():
    global machine

    # highest address - (prom offset) - (address set in the file)
    for mach in machine_list:
        machine = mach
        init_cheerio_hme_prom()
        offset = highest_mem[machine] - 0x00800000L - 0xf0000000L
        # handle wrap around
        if (offset < 0):
            offset = 0x10000000000000000L + offset
        SIM_load_binary(eval("conf.%sphys_mem%d" % (machine, master_node[machine])), openbootprom, offset, 0, 0)
        newpc = SIM_load_binary(eval("conf.%sphys_io%d" % (machine, master_node[machine])), "fpost", 0, 0, 0)
        newpc |= 0xfffffffff0000000L
        for i in object_list[machine]:
            if i[1][:10] == "ultrasparc":
                pc = SIM_get_program_counter(SIM_get_object(i[0]))
                instr = 0x10800000 | ((newpc - pc) >> 2) # branch to OBP
                pc &= 0x7ffffffffff # physical address
                eval_cli_line("%sphys-io%d.set 0x%x 0x%x 4" %
                              (machine, master_node[machine], pc,     instr))      # ba
                eval_cli_line("%sphys-io%d.set 0x%x 0x%x 4" %
                              (machine, master_node[machine], pc + 4, 0x01000000)) # nop
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
