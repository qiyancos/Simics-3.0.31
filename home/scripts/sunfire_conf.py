
##  Copyright 2001-2007 Virtutech AB
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

from text_console_common import wait_for_string

SIM_source_python_in_module("../scripts/flash_memory.py", __name__)

# constants
use_hostfs = 1

mem_sizes = {4096 : 2 , 2048 : 2, 1024 : 1, 512 : 2, 256 : 1, 128 : 2, 64 : 1, 0 : 0}
bank_size = [2048L, 1024L, 256L, 64L]
bank_mask = [0x1f, 0x0f, 0x03, 0x00]
bank_stat = [0x62, 0x6f, 0x6b, 0x64]

range_inv = [-1, 3, 0, -1, 1]
divid_inv = [-1, -1, 0, 3, 2, 4, 1]

cpu_freqs = {168 : [ 336, 2, 4], # sys-freq  84 ok
             200 : [ 400, 2, 4], # sys-freq 100 ok
             248 : [ 248, 1, 3], # sys-freq  82 ok
             296 : [ 296, 1, 3], # sys-freq  98 ok
             336 : [ 336, 1, 4], # sys-freq 168 ok
             360 : [ 360, 1, 4], # sys-freq 180 ok
             400 : [ 200, 1, 5], # sys-freq  80 ok
             464 : [ 232, 1, 5], # sys-freq  92 ok
             496 : [ 248, 1, 5], # sys-freq  99 ok
             592 : [ 296, 1, 6], # sys-freq  98 ok
             720 : [ 360, 1, 2], # sys-freq 180 ok
             800 : [ 400, 1, 2], # sys-freq 200 ok
             992 : [ 496, 1, 5]} # sys-freq 198 ok

# some global variables for the configuration
use_hostfs = 1

global_cpu_freq = {}
global_time = {}
mac = {}
host_id = {}
global_cpu = {}
global_mid = {}
num_slots = {}
num_gfx_consoles = {}
have_ttyb_console = {}

object_list = {}
board_list = {}
cpu_list = {}
post_data = {}
mem_list = {}
machine_list = []

have_feps_prom = 0
have_sim_object = 0
have_isp2200_prom = 0
have_isp1040_prom = 0
have_pgx64_prom = 0
cassini_proms = []

machine = ""

if not SIM_get_quiet():
    print
    print "Machines based on sunfire_conf.py are only provided for backward "
    print "compatibility. The new component based machines in simics/targets/"
    print "are recommended instead."
    print

def handle_error(msg):
    print
    print "Sunfire configuration error:"
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

def valid_board(board_no):
    if num_slots[machine] == 5:
        if board_no < 10 and (board_no % 2) == 1:
            return 1
    elif num_slots[machine] == 8:
        if board_no < 8:
            return 1
    else:
        if board_no < 16:
            return 1        
    return 0

def get_free_board():
    max_slot = num_slots[machine]
    for board in range(max_slot):
        if valid_board(board) and board_list[machine].get(board) == None:
            return board
    return None

def mac_string_to_list(mac_address):
    ether = []
    eth = string.split(mac_address, ":")
    for i in range(0, len(eth)):
        ether.append(int(eth[i], 16))
    return ether

def create_cheerio_hme_prom(name):
    object_list[machine] += ([OBJECT(name + "_prom", "rom",
                                     image = OBJ(name + "_prom_image"))] +
                             [OBJECT(name + "_prom_image", "image",
                                     size = 0x1000000,
                                     files = [["cheerio_hme.fcode", "ro", 0, 19488]],
                                     queue = "<queue>")])

def create_isp2200_prom(name):
    global have_isp2200_prom
    object_list[machine] += ([OBJECT(name + "_prom", "rom",
                                     image = OBJ("sunfire_isp2200_prom_image"))])
    if have_isp2200_prom:
        return
    have_isp2200_prom = 1
    object_list[machine] += ([OBJECT("sunfire_isp2200_prom_image", "image",
                                     size = 0x10000,
                                     files = [["isp2200.fcode", "ro", 0, 111356]],
                                     queue = "<queue>")])
    
def create_isp1040_prom(name):
    global have_isp1040_prom
    object_list[machine] += ([OBJECT(name + "_prom", "rom",
                                     image = OBJ("sunfire_isp1040_prom_image"))])
    if have_isp1040_prom:
        return
    have_isp1040_prom = 1
    object_list[machine] += ([OBJECT("sunfire_isp1040_prom_image", "image",
                                     size = 0x10000,
                                     files = [["isp1040.fcode", "ro", 0, 43540]],
                                     queue = "<queue>")])

conf_list = []

def set_machine(mach):
    global machine, conf_list
    machine = mach
    try:
        conf_list = object_list[machine]
    except:
        pass
    
def set_global_config(slots, hostid, cpu_freq, mac_address, tod, ttyb_console = 0):
    global object_list, global_time, mac, host_id, global_cpu_freq, num_slots
    global glob, have_sim_object, conf_list, have_ttyb_console

    if configuration_loaded("set_global_config"):
        return
    
    machine_list.append(machine)
    object_list[machine] = []
    board_list[machine] = {}
    cpu_list[machine] = []
    global_cpu[machine] = ""
    global_mid[machine] = -1
    mem_list[machine] = []
    post_data[machine] = {}
    num_gfx_consoles[machine] = 0
    have_ttyb_console[machine] = ttyb_console

    try:
        cpu_freqs[cpu_freq]
    except KeyError:
        freqs = cpu_freqs.keys()
        freqs.sort()
        return handle_error("Unsupported cpu frequency: Try one of: " + `freqs`)
    if slots != 5 and slots != 8 and slots != 16:
        return handle_error("Only 5, 8 or 16 board slots supported")
    num_slots[machine] = slots
    global_cpu_freq[machine] = cpu_freq
    global_time[machine] = tod
    host_id[machine] = hostid
    mac[machine] = mac_string_to_list(mac_address)
    object_list[machine] = ([OBJECT(machine + "phys_mem0", "memory-space",
                    map = [[0x1fff0000000L, OBJ(machine + "local_space"), 0, 0x0, 0x8000000, OBJ(machine + "phys_mem0")]])] +
            [OBJECT(machine + "local_space", "sun4u-trans2")])
    object_list[machine] += [OBJECT("%s_component" % iff(len(machine), machine, "sunfire"), "dummy-component")]
    conf_list = object_list[machine]
    if have_sim_object == 0:
        have_sim_object = 1
        object_list[machine] += [OBJECT("sim", "sim",handle__outside__memory = 1)]
    for i in range(0, 16):
        post_data[machine][i] = 0x2 # board not present
    # IMPORTANT: the next line doesn't work if object_list[machine]
    # is assigned later. Only additions and inline modifications
    # are ok

def write_post_sram_data():
    post_data_addr = 0x1fff8206700L
    mem_obj = SIM_get_object(machine + "phys_mem0")
    for i in post_data[machine].keys():
        for j in range(0, 8):
            addr = post_data_addr + (i * 8) + j
            mem_obj.memory[[addr, addr]] = [(post_data[machine][i] >> (56 - (j * 8))) & 0xff]
    post_data_addr = 0x1fff82068f8L
    for i in post_data[machine].keys():
        for j in range(0, 8):
            addr = post_data_addr + (i * 8) + j
            mem_obj.memory[[addr, addr]] = [(post_data[machine][i] >> (56 - (j * 8))) & 0xff]

def set_post_cpu_info(board_no, num_cpus, num_banks):
    global post_data
    brd_info = 0xff0f00001e000003L
    if num_cpus > 0:
        brd_info |= 3 << 8
    if num_cpus > 1:
        brd_info |= 3 << 16
    if num_banks > 0:
        brd_info |= 1L << 52
    if num_banks > 1:
        brd_info |= 1L << 54
    post_data[machine][board_no] = brd_info

def set_post_io1_info(board_no):
    global post_data
    post_data[machine][board_no] = 0xff0c00009e07a70bL

def set_post_io3_info(board_no):
    global post_data
    post_data[machine][board_no] = 0xff0c00009ff80313L

def set_post_cb_info():
    global post_data
    post_data[machine][16] = 0x00001f0080001d1fL

def add_clock_board(cpu_mid):
    global object_list
    board_no = cpu_mid >> 1

    all_cpus = []
    for i in cpu_list[machine]:
        all_cpus.append(OBJ(machine + "cpu" + `i`))

    conf = ([OBJECT(machine + "clock_board", "memory-space",
                    map = [[0x0000000, OBJ(machine + "clks"), 0x0, 0, 0x10],
                           [0x0002000, OBJ(machine + "serial"), 0x0, 0, 0x10],
                           [0x0004000, OBJ(machine + "kbd"), 0x0, 0, 0x10],
                           [0x0006000, OBJ(machine + "sysreg"), 0x0, 0, 0x80],
                           [0x0008000, OBJ(machine + "rtc_cb"), 0x0, 0, 0x2000],
                           [0x000a000, OBJ(machine + "remote_cons"), 0x0, 0, 0x10],
                           [0x000c000, OBJ(machine + "fhc" + `board_no`), 0x2, 0, 0x8]])] +
            [OBJECT(machine + "rec0", "recorder")] +
            [OBJECT(machine + "irqbus0", "sparc-irq-bus")] +
            [OBJECT(machine + "clks", "sun4u-clockregs")] +
            [OBJECT(machine + "sysreg", "sun4u-systemregs",
                    slots = num_slots[machine])] +
            [OBJECT(machine + "kbd", "Z8530",
                    irq_dev = OBJ(machine + "fhc" + `board_no`),
                    irq_level = 2,
                    recorder = OBJ(machine + "rec0"),
                    a_port = OBJ(machine + "kbd-a-port"),
                    b_port = OBJ(machine + "kbd-b-port"),
                    queue = "<queue>")] +
            [OBJECT(machine + "kbd-a-port", "Z8530-port",
                    master = OBJ(machine + "kbd"))]+
            [OBJECT(machine + "kbd-b-port", "Z8530-port",
                    master = OBJ(machine + "kbd"))]+
            [OBJECT(machine + "serial", "Z8530",
                    irq_dev = OBJ(machine + "fhc" + `board_no`),
                    irq_level = 2,
                    recorder = OBJ(machine + "rec0"),
                    a_port = OBJ(machine + "serial-a-port"),
                    b_port = OBJ(machine + "serial-b-port"),
                    queue = "<queue>")] +
            [OBJECT(machine + "serial-a-port", "Z8530-port",
                    console = OBJ(machine + "con0"),
                    master = OBJ(machine + "serial"))] +
            [OBJECT(machine + "serial-b-port", "Z8530-port",
                    master = OBJ(machine + "serial"))] +
            [OBJECT(machine + "con0", "xterm-console",
                    title = machine + "con0: Console on tty-a",
                    device = OBJ(machine + "serial-a-port"),
                    width = 80, height = 24,
                    bg__color = "yellow",
                    fg__color = "black",
                    queue = "<queue>")] +
            [OBJECT(machine + "rtc_cb", "MK48T08",
                    time = global_time[machine],
                    queue = "<queue>")] +
            [OBJECT(machine + "remote_cons", "rom",
                    image = OBJ(machine + "remote_cons_image"))] +
            [OBJECT(machine + "remote_cons_image", "image",
                    size = 0x2000,
                    queue = "<queue>")] +
            [OBJECT(machine + "system", "sunfire-system",
                    master_cpu = OBJ(global_cpu[machine]),
                    all_cpus = all_cpus,
                    max_mem_address = tot_mem[machine])])

    if have_ttyb_console[machine] == 1:
        conf += [OBJECT(machine + "con1", "xterm-console",
                        title = machine + "con1: Console on tty-b",
                        device = OBJ(machine + "serial-b-port"),
                        width = 80, height = 24,
                        bg__color = "yellow",
                        fg__color = "black",
                        queue = "<queue>")]
        set_attribute(conf, machine + "serial-b-port", "console", OBJ(machine + "con1"))

    for brd in board_list[machine].keys():
        mem = get_attribute(object_list[machine], machine + "board_" + `brd` + "_space", "map")
        mem += [[0x0900000, OBJ(machine + "clock_board"), 0, 0x0, 0x100000]]
        set_attribute(object_list[machine], machine + "board_" + `brd` + "_space", "map", mem)
    set_post_cb_info()
    object_list[machine] += conf
    if num_gfx_consoles[machine] > 0:
        object_list[machine] += ([OBJECT(machine + "keyboard", "sun-keyboard",
                         device = OBJ(machine + "kbd-a-port"),
                         recorder = OBJ(machine + "rec0"))] +
                 [OBJECT(machine + "mouse", "sun-mouse",
                         device = OBJ(machine + "kbd-b-port"),
                         recorder = OBJ(machine + "rec0"))])
        set_attribute(object_list[machine], machine + "kbd-a-port", "console", OBJ(machine + "keyboard"))
        set_attribute(object_list[machine], machine + "kbd-b-port", "console", OBJ(machine + "mouse"))

def add_cpu_board(board_no, num_cpus, mb):
    global object_list
    
    if configuration_loaded("add_cpu_board"):
        return
    if not valid_board(board_no):
        return handle_error("Cannot add CPU board.\nInvalid board number %d, in %d slot system." % (board_no, num_slots[machine]))
    if num_cpus > 2:
        return handle_error("Cannot add CPU board.\nOnly 0 to 2 cpus supported on a board")
    if board_list[machine].get(board_no) != None:
        return handle_error("Cannot add CPU board.\nBoard %d already defined" % board_no)
    board_list[machine][board_no] = "cpu"
    try:
        mem_sizes[mb]
    except:
        mems = mem_sizes.keys()
        mems.sort()
        return handle_error("Illegal memory size on board %s. Allowed sizes are: " + `mems`)
    flash_objects,ignore = flash_create_memory(machine + "sunfire_cpuprom" + `board_no`,
                                               "Am29F040B",
                                               1, 8, [["openbootprom.sf", 1, 0, 0x80000]])
    object_list[machine] += flash_objects
    conf = ([OBJECT(machine + "cpu" + `i`, "ultrasparc-ii",
                    queue = OBJ(machine + "cpu" + `i`),
                    control_registers = [["mid", i]],
                    processor_number = get_next_cpu_number(),
                    cpu_group = OBJ(machine + "irqbus0"),
                    freq_mhz = global_cpu_freq[machine],
                    mmu = OBJ(machine + "sfmmu" + `i`),
                    physical_memory = OBJ(machine + "phys_mem0"))
             for i in range(board_no * 2, board_no * 2 + num_cpus)] +
            [OBJECT(machine + "sfmmu" + `i`, "spitfire-mmu")
             for i in range(board_no * 2, board_no * 2 + num_cpus)] +
            [OBJECT(machine + "board_" + `board_no` + "_space", "memory-space",
                     map = [[0x0000000, OBJ(machine + "sunfire_cpuprom" + `board_no`), 0, 0, 0x80000, OBJ(machine + "sunfire_cpuprom" + `board_no` + "-ram"), 1, 1],
                           [0x0200000, OBJ(machine + "sram" + `board_no`), 0, 0x0, 0x8000],
                           [0x0400000, OBJ(machine + "temp" + `board_no`), 0, 0x0, 0x10],
                           [0x0600000, OBJ(machine + "sstat" + `board_no`), 0, 0x0, 0x10],
                           [0x0800000, OBJ(machine + "fhc" + `board_no`), 0, 0x0, 0xe020],
                           [0x1000000, OBJ(machine + "ac" + `board_no`), 0, 0x0, 0x6030],
                           [0x2000000, OBJ(machine + "dtags" + `board_no`), 0, 0x0, 0x1000000]])] +
            [OBJECT(machine + "sram" + `board_no`, "ram",
                    image = OBJ(machine + "sram" + `board_no` + "_image"))] +
            [OBJECT(machine + "sram" + `board_no` + "_image", "image",
                    size = 0x8000,
                    queue = "<queue>")] +
            [OBJECT(machine + "dtags" + `board_no`, "rom",
                    image = OBJ(machine + "dtags" + `board_no` + "_image"))] +
            [OBJECT(machine + "dtags" + `board_no` + "_image", "image",
                    size = 0x1000000,
                    queue = "<queue>")] +
            [OBJECT(machine + "temp" + `board_no`, "sun4u-temperature")] +
            [OBJECT(machine + "sstat" + `board_no`, "sun4u-simm-status")] +
            [OBJECT(machine + "fhc" + `board_no`, "sun4u-fhc",
                    mid = board_no * 2,
                    irq_bus = OBJ(machine + "irqbus0"),
                    fhc_board_status = (((board_no * 2 & 1) << 16)
                                        | ((board_no *2 & 0xe) << 12)
                                        | (5 << 10)
                                        | (5 << 7)
                                        | (1 << 6)
                                        | (1 << 5)
                                        | (1 << 1)),
                    queue = "<queue>")] +
            [OBJECT(machine + "ac" + `board_no`, "sun4u-ac")])

    set_attribute(conf, machine + "sstat" + `board_no`, "connector", [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,])

    # note: 5 << 17 is 4MB of cache
    set_attribute(conf, machine + "ac" + `board_no`, "brd_conf",
                  ((0x70 | board_no) << 24) | (board_no << 20) | (5 << 17))
    
    mem = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    mem += [[0x1c0f8000000L + (0x400000000L * board_no), OBJ(machine + "board_" + `board_no` + "_space"), 0, 0x0, 0x8000000]]
    mem += [[0x1c2f8000000L + (0x400000000L * board_no), OBJ(machine + "board_" + `board_no` + "_space"), 0, 0x0, 0x8000000]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", mem)
    set_attribute(object_list[machine], machine + "local_space",
                  "board-" + `board_no` + "-device-space", OBJ(machine + "board_" + `board_no` +"_space"))
    object_list[machine] += conf
    num_banks = mem_sizes[mb]
    if num_banks == 1:
        bank_0_mb = mb
        bank_1_mb = 0
    elif num_banks == 2:
        bank_0_mb = mb / 2
        bank_1_mb = mb / 2
    else:
        bank_0_mb = 0
        bank_1_mb = 0
    mem_list[machine].append([0, bank_0_mb, board_no])
    mem_list[machine].append([1, bank_1_mb, board_no])
    set_post_cpu_info(board_no, num_cpus, num_banks)
    for i in range(0, num_cpus):
        cpu_list[machine].append(board_no * 2 + i)

# The following works (on sbus boards )since only slot 1 and 2 are available
# on the first UPA of a board, slot 0 and 3 on the second UPA.
# For pci we simply call the slots 0 - 3. They are actually 1, 2 and 2, 3
def get_upa_from_slot(board_no, slot_no):
    if board_list[machine][board_no] == "sbus":
        if slot_no == 1 or slot_no == 2 or slot_no == 0xd:
            return board_no * 2
        else:
            return board_no * 2 + 1
    elif board_list[machine][board_no] == "pci":
        if slot_no == 0 or slot_no == 1:
            return board_no * 2
        else:
            return board_no * 2 + 1
    else:
        raise "Only Sbus and PCI boards have slots"

def get_actual_slot(board_no, slot_no):
    if board_list[machine][board_no] == "sbus":
        if slot_no < 4:
            return slot_no
        else:
            raise "Illegal slot number"
    elif board_list[machine][board_no] == "pci":
        if slot_no == 0:
            return 2
        elif slot_no == 1:
            return 1
        elif slot_no == 2:
            return 2
        elif slot_no == 3:
            return 3
        else:
            raise "Illegal slot number"
    else:
        raise "Only Sbus and PCI boards have slots"

def add_scsi_disk(board_no, slot_no, scsi_target, geometry = None, size = None, files = ""):
    global object_list
    if configuration_loaded("add_scsi_disk"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
    except:
        return handle_error("Cannot add SCSI disk.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    
    if not object_exists(object_list[machine], machine + "sb" + `upa` + "_" + `slot_no`):
        return handle_error("Cannot add SCSI disk.\nNo SCSI bus exists on board %d, slot %d" % (board_no, slot_no))

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

    tgt_name = `upa` + "_" + `slot_no` + "_" + `scsi_target`
    conf = ([OBJECT(machine + "sd" + tgt_name, "scsi-disk",
                    image = OBJ(machine + "sd" + tgt_name + "_image"),
                    scsi_bus = OBJ(machine + "sb" + `upa` + "_" + `slot_no`),
                    scsi_target = scsi_target,
                    queue = "<queue>",
                    geometry = geometry)] +
            [OBJECT(machine + "sd" + tgt_name + "_image", "image",
                    size = size,
                    queue = "<queue>")])
    if files != "":
        set_attribute(conf, machine + "sd" + tgt_name + "_image", "files", files)
    object_list[machine] += conf
    tgts = get_attribute(object_list[machine], machine + "sb" + `upa` + "_" + `slot_no`, "targets")
    tgts += [[scsi_target, OBJ(machine + "sd" + tgt_name), 0]]
    set_attribute(object_list[machine], machine + "sb" + `upa` + "_" + `slot_no`, "targets", tgts)
        

def add_fc_disk(board_no, slot_no, loop_id, node_name, port_name, geometry = None, size = None, controller = -1, files = ""):
    global object_list
    if configuration_loaded("add_fc_disk"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
    except:
        return handle_error("Cannot add FC disk.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    
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

    if controller == -1:
        slot_name = `upa` + "_" + `slot_no`
    else:
        slot_name = `upa` + "_" + `slot_no` + "_" + `controller`
        
    if not object_exists(object_list[machine], machine + "qlc" + slot_name):
        if object_substr_exists(object_list[machine], machine + "qlc" + slot_name):
            return handle_error("Cannot add FC disk.\nMultiple FC controllers exist on board %d, slot %d" % (board_no, slot_no))
        return handle_error("Cannot add FC disk.\nNo FC controller exists on board %d, slot %d" % (board_no, slot_no))

    tgt_name = slot_name + "_" + `loop_id`
    conf = ([OBJECT(machine + "fc" + tgt_name, "fc-disk",
                    image = OBJ(machine + "fc" + tgt_name + "_image"),
                    fc__controller = OBJ(machine + "qlc" + slot_name),
                    loop__id = loop_id,
                    queue = "<queue>",
                    node__name = node_name,
                    port__name = port_name,
                    geometry = geometry)] +
            [OBJECT(machine + "fc" + tgt_name + "_image", "image",
                    size = size,
                    queue = "<queue>")])
    if files != "":
        set_attribute(conf, machine + "fc" + tgt_name + "_image", "files", files)
    object_list[machine] += conf

def add_scsi_cdrom(board_no, slot_no, scsi_target, file = ""):
    global object_list
    if configuration_loaded("add_scsi_cdrom"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
    except:
        return handle_error("Cannot add SCSI CD-ROM.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    if not object_exists(object_list[machine], machine + "sb" + `upa` + "_" + `slot_no`):
        return handle_error("Cannot add SCSI CD-ROM.\nNo SCSI bus exists on board %d, slot %d" % (board_no, slot_no))
    tgt_name = `upa` + "_" + `slot_no` + "_" + `scsi_target`
    conf = ([OBJECT(machine + "cd" + tgt_name, "scsi-cdrom",
                    scsi_bus = OBJ(machine + "sb" + `upa` + "_" + `slot_no`),
                    scsi_target = scsi_target,
                    queue = "<queue>")])
    if file == "":
        pass
    elif string.find(file, "/dev/") == 0 or string.find(file, "/vol/rdsk/") == 0:
        conf += [OBJECT(machine + "host-cd" + tgt_name, "host-cdrom", file = file)]
        set_attribute(conf, machine + "cd" + tgt_name, "cd-media", OBJ(machine + "host-cd" + tgt_name))
        print "setting media %s" % (machine + "host-cd" + tgt_name)
    else:
        conf += [OBJECT(machine + "file-cd" + tgt_name, "file-cdrom", file = file)]
        set_attribute(conf, machine + "cd" + tgt_name, "cd-media", OBJ(machine + "file-cd" + tgt_name))
        print "setting media %s" % (machine + "file-cd" + tgt_name)
    object_list[machine] += conf
    tgts = get_attribute(object_list[machine], machine + "sb" + `upa` + "_" + `slot_no`, "targets")
    tgts += [[scsi_target, OBJ(machine + "cd" + tgt_name), 0]]
    set_attribute(object_list[machine], machine + "sb" + `upa` + "_" + `slot_no`, "targets", tgts)

def add_sbus_fas_hme(board_no, slot_no, mac_address, no_prom = 0):
    global object_list, have_feps_prom
    if configuration_loaded("add_sbus_fas_hme"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
    except:
        return handle_error("Cannot add fas+hme device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    if not object_exists(object_list[machine], machine + "sysio" + `upa`):
        return handle_error("Cannot add fas+hme.\nNo SBus exists on board %d with slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    conf = ([OBJECT(machine + "fasdma" + slot_name, "sun4u-fasdma",
                    sbus_slot = slot_no,
                    iommu = OBJ(machine + "sysio" + `upa`),
                    memory = OBJ(machine + "phys_mem0"),
                    queue = "<queue>")] +
            [OBJECT(machine + "fas" + slot_name, "FAS366U",
                    irq_dev = OBJ(machine + "sysio" + `upa`),
                    irq_level = slot_no * 8 + 3,
                    dma_dev = OBJ(machine + "fasdma" + slot_name),
                    dma_channel = 0,
                    scsi_target = 7,
                    scsi_bus = OBJ(machine + "sb" + slot_name),
                    queue = "<queue>")] +
            [OBJECT(machine + "sb" + slot_name, "scsi-bus",
                    targets = [[7, OBJ(machine + "fas" + slot_name), 0]],
                    queue = "<queue>")] +
            [OBJECT(machine + "hme" + slot_name, "sbus-hme",
                    sbus_slot = slot_no,
                    irq_dev = OBJ(machine + "sysio" + `upa`),
                    irq_level = slot_no * 8 + 4,
                    iommu = OBJ(machine + "sysio" + `upa`),
                    memory = OBJ(machine + "phys_mem0"),
                    recorder = OBJ(machine + "rec0"),
                    mac_address = mac_address,
                    queue = "<queue>")])
    if no_prom == 0:
        if not have_feps_prom:
            have_feps_prom = 1
            conf += ([OBJECT("sunfire_feps_prom", "rom",
                             image = OBJ("sunfire_feps_prom_image"))] +
                     [OBJECT("sunfire_feps_prom_image", "image",
                             size = 0x8000,
                             queue = "<queue>",
                             files = [["sunswift.prom", 1, 0, 32144]])])
    object_list[machine] += conf
    mem = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    base = 0x1c000000000L + 0x200000000L * upa + 0x10000000L * slot_no
    if no_prom == 0:
        mem += [[base + 0x100000000L, OBJ("sunfire_feps_prom"), 0x0, 0, 0x8000]]
    mem += [[base + 0x108800000L, OBJ(machine + "fasdma" + slot_name), 0x0, 0, 0x18],
            [base + 0x108810000L, OBJ(machine + "fas" + slot_name), 0x0, 0, 0x200],
            [base + 0x108c00000L, OBJ(machine + "hme" + slot_name), 0x0, 0, 0x10000],
            [base + 0x10c800000L, OBJ(machine + "hme" + slot_name), 0x1, 0, 0x1a]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", mem)

# NOTE: only for testing, this does not work
def add_sbus_soc(board_no, wwn_address):
    global object_list
    if configuration_loaded("add_sbus_soc"):
        return
    slot_no = 0xd
    try:
        upa = get_upa_from_slot(board_no, slot_no)
    except:
        return handle_error("Cannot add SOC device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    if not object_exists(object_list[machine], machine + "sysio" + `upa`):
        return handle_error("Cannot add SOC.\nNo SBus exists on board %d with slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    # TODO: change to SOC
    conf = ([OBJECT(machine + "hme" + slot_name, "sbus-hme",
                    sbus_slot = slot_no,
                    irq_dev = OBJ(machine + "sysio" + `upa`),
                    irq_level = slot_no * 8 + 4,
                    iommu = OBJ(machine + "sysio" + `upa`),
                    memory = OBJ(machine + "phys_mem0"),
                    recorder = OBJ(machine + "rec0"),
                    mac_address = wwn_address,
                    queue = "<queue>")])
    object_list[machine] += conf
    mem = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    base = 0x1c000000000L + 0x200000000L * upa + 0x10000000L * slot_no
    mem += [[base + 0x100010000L, OBJ(machine + "hme" + slot_name), 0x0, 0, 0x10000],
            [base + 0x100020000L, OBJ(machine + "hme" + slot_name), 0x0, 1,    0x10]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", mem)


def add_sbus_board(board_no, mac_address):
    global object_list
    if configuration_loaded("add_sbus_board"):
        return
    if not valid_board(board_no):
        return handle_error("Cannot add SBus board.\nInvalid board number %d, in %d slot system." % (board_no, num_slots[machine]))
    if board_list.get(board_no) != None:
        return handle_error("Cannot add SBus board.\nBoard %d already defined" % board_no)
    board_list[machine][board_no] = "sbus"
    flash_objects,ignore = flash_create_memory(machine + "sunfire_io1prom" + `board_no`,
                                               "Am29F040B",
                                               1, 8, [["io1prom", 1, 0, 0x80000]])
    object_list[machine] += flash_objects
    conf = ([OBJECT(machine + "board_" + `board_no` + "_space", "memory-space",
                    map = [[0x0000000, OBJ(machine + "sunfire_io1prom" + `board_no`), 0, 0x0, 0x80000,
                            OBJ(machine + "sunfire_io1prom" + `board_no` + "-ram"), 1, 1],
                           [0x0300000, OBJ(machine + "rtc" + `board_no`), 0, 0x0, 0x2000],
                           [0x0400000, OBJ(machine + "temp" + `board_no`), 0, 0x0, 0x10],
                           [0x0500000, OBJ(machine + "sspeed" + `board_no`), 0, 0x0, 0x10],
                           [0x0800000, OBJ(machine + "fhc" + `board_no`), 0, 0x0, 0xe020],
                           [0x1000000, OBJ(machine + "ac" + `board_no`), 0, 0x0, 0x6030]])] +
            [OBJECT(machine + "rtc" + `board_no`, "MK48T08",
                    time = global_time[machine],
                    queue = "<queue>")] +
            [OBJECT(machine + "temp" + `board_no`, "sun4u-temperature")] +
            [OBJECT(machine + "sspeed" + `board_no`, "sun4u-sbus-speed")] +
            [OBJECT(machine + "fhc" + `board_no`, "sun4u-fhc",
                    mid = board_no * 2,
                    irq_bus = OBJ(machine + "irqbus0"),
                    fhc_board_status = (((board_no * 2 & 1) << 16)
                                        | ((board_no *2 & 0xe) << 12)
                                        | (5 << 10)
                                        | (5 << 7)
                                        | (1 << 6)
                                        | (1 << 5)
                                        | (1 << 1)),
                    queue = "<queue>")] +
            [OBJECT(machine + "ac" + `board_no`, "sun4u-ac")] +
            [OBJECT(machine + "sysio"  + `board_no * 2 + i`, "sunfire-sysio",
                    mid = board_no * 2 + i,
                    memory = OBJ(machine + "phys_mem0"),
                    irq_bus = OBJ(machine + "irqbus0"),
                    queue = "<queue>")
             for i in range(0, 2)])
    
    set_attribute(conf, machine + "ac" + `board_no`, "brd_conf",
                  ((0x70 | board_no) << 24) | (board_no << 20) | (0 << 17))
    
    mem = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    for i in range(0, 2):
        base = 0x1c000000000L + 0x200000000L * (board_no * 2 + i)
        mem += [[base + 0x0000, OBJ(machine + "sysio" + `board_no * 2 + i`), 0x0, 0, 0x6000]]
    mem += [[0x1c0f8000000L + (0x400000000L * board_no), OBJ(machine + "board_" + `board_no` + "_space"), 0, 0x0, 0x8000000]]
    mem += [[0x1c2f8000000L + (0x400000000L * board_no), OBJ(machine + "board_" + `board_no` + "_space"), 0, 0x0, 0x8000000]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", mem)
    set_attribute(object_list[machine], machine + "local_space",
                  "board-" + `board_no` + "-device-space", OBJ(machine + "board_" + `board_no` +"_space"))
    object_list[machine] += conf
    add_sbus_fas_hme(board_no, 3, mac_address, 1)
    set_post_io1_info(board_no)

def add_pci_hme(board_no, slot_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_hme"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
        if slot_no != 2:
            return handle_error("Cannot add hme device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
        bus = "A"
    except:
        return handle_error("Cannot add hme device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    if not object_exists(object_list[machine], machine + "pci-bus" + `upa` + bus):
        return handle_error("Cannot add hme device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "hme" + slot_name, "cheerio-hme",
                    pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                    expansion_rom = [OBJ(machine + "hme" + slot_name + "_prom"), 0x1000000, 0],
                    recorder = OBJ(machine + "rec0"),
                    mac_address = mac_address,
                    queue = "<queue>")] +
            [OBJECT(machine + "e2bus" + slot_name, "cheerio-e2bus",
                     pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                     queue = "<queue>")])
    object_list[machine] += conf
    create_cheerio_hme_prom(machine + "hme" + slot_name)
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot_no, 0, OBJ(machine + "e2bus" + slot_name)], [slot_no, 1, OBJ(machine + "hme" + slot_name)]]
    set_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices", pci_devs)    

def add_pci_pgx64(board_no, slot_no):
    global object_list, num_gfx_consoles, have_pgx64_prom
    if configuration_loaded("add_pci_pgx64"):
        return
    console_id = num_gfx_consoles[machine] + have_ttyb_console[machine] + 1
    num_gfx_consoles[machine] += 1
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
        if slot_no != 2:
            return handle_error("Cannot add pgx64 device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
        bus = "A"
    except:
        return handle_error("Cannot add pgx64 device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    if not object_exists(object_list[machine], machine + "pci-bus" + `upa` + bus):
        return handle_error("Cannot add pgx64 device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    object_list[machine] += ([OBJECT(machine + "pgx" + slot_name, "ragexl",
                                     memory_space = OBJ(machine + "pci-mem" + `upa` + bus),
                                     pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                                     console = OBJ(machine + "con" + `console_id`),
                                     image = OBJ(machine + "pgx" + slot_name + "_image"),
                                     expansion_rom = [OBJ(machine + "pgx" + slot_name + "_prom"), 0x20000, 0],
                                     queue = "<queue>")] +
                             [OBJECT(machine + "pgx" + slot_name + "_image", "image",
                                     size = 0x800000,
                                     queue ="<queue>")] +
                             [OBJECT(machine + "pgx" + slot_name + "_prom", "rom",
                                     image = OBJ("sunfire_pgx64_prom_image"))] +                             
                             [OBJECT(machine + "con" + `console_id`, "gfx-console",
                                     x__size = 640,
                                     y__size = 400,
                                     mouse = OBJ(machine + "mouse"),
                                     keyboard = OBJ(machine + "keyboard"),
                                     queue = "<queue>")])
    if not have_pgx64_prom:
        have_pgx64_prom = 1
        object_list[machine] += ([OBJECT("sunfire_pgx64_prom_image", "image",
                                         size = 0x20000,
                                         files = [["pgx64.fcode", "ro", 0, 65536]],
                                         queue ="<queue>")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot_no, 0, OBJ(machine + "pgx" + slot_name)]]
    set_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices", pci_devs)    

def add_pci_hme_isp(board_no, slot_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_hme_isp"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
        if slot_no != 2:
            return handle_error("Cannot add hme+isp device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
        bus = "A"
    except:
        return handle_error("Cannot add hme+isp device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    if not object_exists(object_list[machine], machine + "pci-bus" + `upa` + bus):
        return handle_error("Cannot add hme+isp device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "bridge" + slot_name, "i21152",
                    pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                    secondary_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                    queue = "<queue>")] +
            [OBJECT(machine + "sub-pci-bus" + slot_name, "pci-bus",
                    bridge = OBJ(machine + "bridge" + slot_name),
                    pci_devices = [[0, 0, OBJ(machine + "e2bus" + slot_name)],
                                   [0, 1, OBJ(machine + "hme" + slot_name)],
                                   [4, 0, OBJ(machine + "isp" + slot_name)]],
                    memory_space = OBJ(machine + "sub-pci-mem" + slot_name),
                    conf_space = OBJ(machine + "sub-pci-cfg" + slot_name),
                    io_space = OBJ(machine + "sub-pci-io" + slot_name))] +
            [OBJECT(machine + "sub-pci-io" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pci-cfg" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pci-mem" + slot_name, "memory-space")] +
            [OBJECT(machine + "sb" + slot_name, "scsi-bus",
                    targets = [[7, OBJ(machine + "isp" + slot_name), 0]],
                    queue = "<queue>")] +
            [OBJECT(machine + "isp" + slot_name, "ISP1040",
                    pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                    scsi_id = 7,
                    expansion_rom = [OBJ(machine + "isp" + slot_name + "_prom"), 0x10000, 0],
                    scsi_bus = OBJ(machine + "sb" + slot_name),
                    queue = "<queue>")] +
            [OBJECT(machine + "e2bus" + slot_name, "cheerio-e2bus",
                     pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                     queue = "<queue>")] +
            [OBJECT(machine + "hme" + slot_name, "cheerio-hme",
                    pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                    expansion_rom = [OBJ(machine + "hme" + slot_name + "_prom"), 0x1000000, 0],
                    recorder = OBJ(machine + "rec0"),
                    mac_address = mac_address,
                    queue = "<queue>")])
    object_list[machine] += conf
    create_cheerio_hme_prom(machine + "hme" + slot_name)
    create_isp1040_prom(machine + "isp" + slot_name)
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot_no, 0, OBJ(machine + "bridge" + slot_name)]]
    set_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices", pci_devs)


def add_pci_ce(board_no, slot_no, mac_address):
    global object_list, cassini_proms
    if configuration_loaded("add_pci_ce"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
        if slot_no != 2:
            return handle_error("Cannot add ce device.\n"
                                "Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
        bus = "A"
    except Exception, msg:
        return handle_error("Cannot add ce device.\n"
                            "Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    if not object_exists(object_list[machine], machine + "pci-bus" + `upa` + bus):
        return handle_error("Cannot ce device.\n"
                            "No PCI bus exists on board %d with slot %d" % (board_no, slot_no))

    object_list[machine] += ([OBJECT(machine + "bridge" + slot_name, "i21152",
                                     pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                                     secondary_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                                     queue = "<queue>")] +
                             [OBJECT(machine + "sub-pci-bus" + slot_name, "pci-bus",
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
                                     pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                                     mac_address = mac_address,
                                     expansion_rom = [OBJ(machine + "ce" + slot_name + "_prom"), 0x100000, 0],
                                     recorder = OBJ(machine + "rec0"),
                                     queue = "<queue>")] +
                             [OBJECT(machine + "ce_sub1_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 1)] +
                             [OBJECT(machine + "ce_sub2_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 2)] +
                             [OBJECT(machine + "ce_sub3_" + slot_name, "cassini_sub",
                                     pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                                     main_object = OBJ(machine + "ce" + slot_name),
                                     pci_function = 3)] +
                             [OBJECT(machine + "ce" + slot_name + "_prom", "rom",
                                     image = OBJ(machine + "cassini_prom_image" + slot_name))] +
                             [OBJECT(machine + "cassini_prom_image" + slot_name, "image",
                                     size = 0x10000,
                                     files = [["cassini_plus.fcode", "ro", 0, 0x10000]],
                                     queue = "<queue>")])
    cassini_proms += [[machine + "cassini_prom_image" + slot_name, mac_address]]
    try:
        pci_devs = get_attribute(object_list[machine],
                                 machine + "pci-bus" + `upa` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot_no, 0, OBJ(machine + "bridge" + slot_name)]]
    set_attribute(object_list[machine],
                  machine + "pci-bus" + `upa` + bus, "pci_devices", pci_devs)    


def add_pci_qlc(board_no, slot_no, loop_id):
    global object_list
    if configuration_loaded("add_pci_qlc"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
        if slot_no != 2:
            return handle_error("Cannot add qlc device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
        bus = "A"
    except:
        return handle_error("Cannot add qlc device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    if not object_exists(object_list[machine], machine + "pci-bus" + `upa` + bus):
        return handle_error("Cannot add qlc device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "qlc" + slot_name, "ISP2200",
                    pci_bus = OBJ(machine + "pci-bus" +  `upa` + bus),
                    expansion_rom = [OBJ(machine + "qlc" + slot_name + "_prom"), 0x10000, 0],
                    loop__id = loop_id,
                    queue = "<queue>")])
    object_list[machine] += conf
    create_isp2200_prom(machine + "qlc" + slot_name)
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot_no, 0, OBJ(machine + "qlc" + slot_name)]]
    set_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices", pci_devs)    

def add_pci_qlc_qlc(board_no, slot_no, loop_id0, loop_id1):
    global object_list
    if configuration_loaded("add_pci_qlc_qlc"):
        return
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
        if slot_no != 2:
            return handle_error("Cannot add qlc+qlc device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
        bus = "A"
    except:
        return handle_error("Cannot add qlc+qlc device.\n Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    if not object_exists(object_list[machine], machine + "pci-bus" + `upa` + bus):
        return handle_error("Cannot add qlc+qlc device.\nNo PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    conf = ([OBJECT(machine + "bridge" + slot_name, "i21152",
                    pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                    secondary_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                    queue = "<queue>")] +
            [OBJECT(machine + "sub-pci-bus" + slot_name, "pci-bus",
                    bridge = OBJ(machine + "bridge" + slot_name),
                    pci_devices = [[4, 0, OBJ(machine + "qlc" + slot_name + "_0")],
                                   [5, 0, OBJ(machine + "qlc" + slot_name + "_1")]],
                    memory_space = OBJ(machine + "sub-pcimem" + slot_name),
                    io_space = OBJ(machine + "sub-pciio" + slot_name),
                    conf_space = OBJ(machine + "sub-pcicfg" + slot_name))] +
            [OBJECT(machine + "sub-pcicfg" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pciio" + slot_name, "memory-space")] +
            [OBJECT(machine + "sub-pcimem" + slot_name, "memory-space")] +
            [OBJECT(machine + "qlc" + slot_name + "_0", "ISP2200",
                    pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                    expansion_rom = [OBJ(machine + "qlc" + slot_name + "_0" + "_prom"), 0x10000, 0],
                    loop__id = loop_id0,
                    queue = "<queue>")] +
            [OBJECT(machine + "qlc" + slot_name + "_1", "ISP2200",
                    pci_bus = OBJ(machine + "sub-pci-bus" + slot_name),
                    expansion_rom = [OBJ(machine + "qlc" + slot_name + "_1" + "_prom"), 0x10000, 0],
                    loop__id = loop_id1,
                    queue = "<queue>")])
    object_list[machine] += conf
    create_isp2200_prom(machine + "qlc" + slot_name + "_0")
    create_isp2200_prom(machine + "qlc" + slot_name + "_1")
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot_no, 0, OBJ(machine + "bridge" + slot_name)]]
    set_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices", pci_devs)


def add_pci_bge(board_no, slot_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_bge"):
        return
    ether = mac_string_to_list(mac_address)
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
        if slot_no != 2:
            return handle_error("Cannot add bge device.\n"
                                "Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
        bus = "A"
    except:
        return handle_error("Cannot add bge device.\n"
                            "Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    if not object_exists(object_list[machine], machine + "pci-bus" + `upa` + bus):
        return handle_error("Cannot add bge device.\n"
                            "No PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    object_list[machine] += ([OBJECT(machine + "bge" + slot_name, "BCM5703C",
                                     pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                                     recorder = OBJ(machine + "rec0"),
                                     mac_address = ether,
                                     queue = "<queue>")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot_no, 0, OBJ(machine + "bge" + slot_name)]]
    set_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices", pci_devs)    


def add_pci_dual_bge(board_no, slot_no, mac_address0, mac_address1):
    global object_list
    if configuration_loaded("add_pci_dual_bge"):
        return
    ether0 = mac_string_to_list(mac_address0)
    ether1 = mac_string_to_list(mac_address1)
    try:
        upa = get_upa_from_slot(board_no, slot_no)
        slot_no = get_actual_slot(board_no, slot_no)
        if slot_no != 2:
            return handle_error("Cannot add bge device.\n"
                                "Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
        bus = "A"
    except:
        return handle_error("Cannot add bge device.\n"
                            "Invalid slot number. Board %d, slot %d" % (board_no, slot_no))
    slot_name = `upa` + "_" + `slot_no`
    if not object_exists(object_list[machine], machine + "pci-bus" + `upa` + bus):
        return handle_error("Cannot add bge device.\n"
                            "No PCI bus exists on board %d with slot %d" % (board_no, slot_no))
    object_list[machine] += ([OBJECT(machine + "bge" + slot_name + "_0", "BCM5704C",
                                     pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                                     recorder = OBJ(machine + "rec0"),
                                     is_mac1 = 0,
                                     other_bcm = OBJ(machine + "bge" + slot_name + "_1"),
                                     mac_address = ether0,
                                     queue = "<queue>")] +
                             [OBJECT(machine + "bge" + slot_name + "_1", "BCM5704C",
                                     pci_bus = OBJ(machine + "pci-bus" + `upa` + bus),
                                     recorder = OBJ(machine + "rec0"),
                                     is_mac1 = 1,
                                     other_bcm = OBJ(machine + "bge" + slot_name + "_0"),
                                     mac_address = ether1,
                                     queue = "<queue>")])
    try:
        pci_devs = get_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices")
    except:
        pci_devs = []
    pci_devs += [[slot_no, 0, OBJ(machine + "bge" + slot_name + "_0")],
                 [slot_no, 1, OBJ(machine + "bge" + slot_name + "_1")]]
    set_attribute(object_list[machine], machine + "pci-bus" + `upa` + bus, "pci_devices", pci_devs)    

def add_pci_board(board_no, mac_address):
    global object_list
    if configuration_loaded("add_pci_board"):
        return
    if not valid_board(board_no):
        return handle_error("Cannot add PCI board.\nInvalid board number %d, in %d slot system." % (board_no, num_slots[machine]))
    if board_list.get(board_no) != None:
        return handle_error("Cannot add PCI board.\nBoard %d already defined" % board_no)
    board_list[machine][board_no] = "pci"
    flash_objects,ignore = flash_create_memory(machine + "sunfire_io3prom" + `board_no`,
                                               "Am29F040B",
                                               1, 8, [["io3prom", 1, 0, 0x80000]])
    object_list[machine] += flash_objects
    conf = ([OBJECT(machine + "board_" + `board_no` + "_space", "memory-space",
                    map = [[0x0000000, OBJ(machine + "sunfire_io3prom" + `board_no`), 0, 0x0, 0x80000,
                            OBJ(machine + "sunfire_io3prom" + `board_no` + "-ram"), 1, 1],
                           [0x0300000, OBJ(machine + "rtc" + `board_no`), 0, 0x0, 0x2000],
                           [0x0400000, OBJ(machine + "temp" + `board_no`), 0, 0x0, 0x10],
                           [0x0500000, OBJ(machine + "sspeed" + `board_no`), 0, 0x0, 0x10],
                           [0x0800000, OBJ(machine + "fhc" + `board_no`), 0, 0x0, 0xe020],
                           [0x1000000, OBJ(machine + "ac" + `board_no`), 0, 0x0, 0x6030]])] +
            [OBJECT(machine + "rtc" + `board_no`, "MK48T08",
                    time = global_time[machine],
                    queue = "<queue>")] +
            [OBJECT(machine + "temp" + `board_no`, "sun4u-temperature")] +
            [OBJECT(machine + "sspeed" + `board_no`, "sun4u-sbus-speed")] +
            [OBJECT(machine + "fhc" + `board_no`, "sun4u-fhc",
                    mid = board_no * 2,
                    irq_bus = OBJ(machine + "irqbus0"),
                    fhc_board_status = (((board_no * 2 & 1) << 16)
                                        | ((board_no *2 & 0xe) << 12)
                                        | (5 << 10)
                                        | (5 << 7)
                                        | (1 << 6)
                                        | (1 << 5)
                                        | (1 << 1)),
                    queue = "<queue>")] +
            [OBJECT(machine + "ac" + `board_no`, "sun4u-ac")] +
            [OBJECT(machine + "psycho"  + `board_no * 2 + i`, "sunfire-psycho",
                    mid = board_no * 2 + i,
                    memory = OBJ(machine + "phys_mem0"),
                    irq_bus = OBJ(machine + "irqbus0"),
                    io__space = OBJ(machine + "phys_mem0"),
                    pci__busB = OBJ(machine + "pci-bus" + `board_no * 2 + i` + "B"),
                    pci__busA = OBJ(machine + "pci-bus" + `board_no * 2 + i` + "A"),
                    queue = "<queue>")
             for i in range(0, 2)] +
            [OBJECT(machine + "pci-bus" + `board_no * 2 + i` + "A", "pci-bus",
                    bridge = OBJ(machine + "psycho"  + `board_no * 2 + i`),
                    memory_space = OBJ(machine + "pci-mem" + `board_no * 2 + i` + "A"),
                    io_space = OBJ(machine + "pci-io" + `board_no * 2 + i` + "A"),
                    conf_space = OBJ(machine + "pci-cfg" + `board_no * 2 + i`))
             for i in range(0, 2)] +
            [OBJECT(machine + "pci-bus" + `board_no * 2 + i` + "B", "pci-bus",
                    bridge = OBJ(machine + "psycho"  + `board_no * 2 + i`),
                    memory_space = OBJ(machine + "pci-mem" + `board_no * 2 + i` + "B"),
                    io_space = OBJ(machine + "pci-io" + `board_no * 2 + i` + "B"),
                    conf_space = OBJ(machine + "pci-cfg" + `board_no * 2 + i`))
             for i in range(0, 2)] +
            [OBJECT(machine + "pci-cfg" + `board_no * 2 + i`, "memory-space")
             for i in range(0, 2)] +
            [OBJECT(machine + "pci-io" + `board_no * 2 + i` + "A", "memory-space")
             for i in range(0, 2)] +
            [OBJECT(machine + "pci-io" + `board_no * 2 + i` + "B", "memory-space")
             for i in range(0, 2)] +
            [OBJECT(machine + "pci-mem" + `board_no * 2 + i` + "A", "memory-space")
             for i in range(0, 2)] +
            [OBJECT(machine + "pci-mem" + `board_no * 2 + i` + "B", "memory-space")
             for i in range(0, 2)])
    # finally on-board devices, isp: (upa + 1) slot 3 ; hme: (upa + 0) slot 1
    slot_name = `board_no * 2 + 1` + "_3"
    conf += ([OBJECT(machine + "sb" + slot_name, "scsi-bus",
                     targets = [[7, OBJ(machine + "isp" + slot_name), 0]],
                     queue = "<queue>")] +
             [OBJECT(machine + "isp" + slot_name, "ISP1040",
                     pci_bus = OBJ(machine + "pci-bus" + `board_no * 2 + 1` + "B"),
                     scsi_id = 7,
                     # no expansion prom
                     scsi_bus = OBJ(machine + "sb" + slot_name),
                     queue = "<queue>")])
    pci_devs = [[3, 0, OBJ(machine + "isp" + slot_name)]]
    set_attribute(conf, machine + "pci-bus" + `board_no * 2 + 1` + "B", "pci_devices", pci_devs)
    slot_name = `board_no * 2` + "_1"
    conf += ([OBJECT(machine + "hme" + slot_name, "cheerio-hme",
                     pci_bus = OBJ(machine + "pci-bus" + `board_no * 2` + "B"),
                     # no expansion rom
                     recorder = OBJ(machine + "rec0"),
                     mac_address = mac_address,
                     queue = "<queue>")] +
             [OBJECT(machine + "e2bus" + slot_name, "cheerio-e2bus",
                     pci_bus = OBJ(machine + "pci-bus" + `board_no * 2` + "B"),
                     queue = "<queue>")])
    pci_devs = [[1, 0, OBJ(machine + "e2bus" + slot_name)], [1, 1, OBJ(machine + "hme" + slot_name)]]
    set_attribute(conf, machine + "pci-bus" + `board_no * 2` + "B", "pci_devices", pci_devs)
    set_attribute(conf, machine + "ac" + `board_no`, "brd_conf",
                  ((0x70 | board_no) << 24) | (board_no << 20) | (0 << 17))
    
    mem = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    for i in range(0, 2):
        base = 0x1c000000000L + 0x200000000L * (board_no * 2 + i)
        mem += [[base + 0x0000, OBJ(machine + "psycho" + `board_no * 2 + i`), 0x0, 0, 0xd000]]
    mem += [[0x1c0f8000000L + (0x400000000L * board_no), OBJ(machine + "board_" + `board_no` + "_space"), 0, 0x0, 0x8000000]]
    mem += [[0x1c2f8000000L + (0x400000000L * board_no), OBJ(machine + "board_" + `board_no` + "_space"), 0, 0x0, 0x8000000]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", mem)
    set_attribute(object_list[machine], machine + "local_space",
                  "board-" + `board_no` + "-device-space", OBJ(machine + "board_" + `board_no` +"_space"))
    object_list[machine] += conf
    set_post_io3_info(board_no)

def set_idprom():
    idprom_base = 0x1fff8909fd8L
    # offset 0 = format (1)
    SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), idprom_base +  0, 1, 1)
    # offset 1, 12-14 = hostid 
    SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), idprom_base +  1, (host_id[machine] >> 24) & 0xff, 1)
    SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), idprom_base + 12, (host_id[machine] >> 16) & 0xff, 1)
    SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), idprom_base + 13, (host_id[machine] >>  8) & 0xff, 1)
    SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), idprom_base + 14, (host_id[machine] >>  0) & 0xff, 1)
    # offset 2 - 7 = ethernet
    for i in range(0, len(mac[machine])):
        SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), idprom_base + 2 + i, mac[machine][i], 1)
    # offset 8 - 11 = date (not used)
    # offset 15 = checksum
    chk = 0
    for i in range(0, 15):
        chk ^= SIM_read_phys_memory(SIM_get_object(global_cpu[machine]), idprom_base + i, 1)
    SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), idprom_base + 15, chk & 0xff, 1)

# later versions of the OBP reads info in the SRAM to get the cpu version number
# we only do a minimal setup
def set_cpu_sram():
    for i in cpu_list[machine]:
        board = i / 2
        cpu = i % 2
        base = 0x1c0f8207800L + 0x400000000L * board
        # write cpu magic
        SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), base + 0x400 * cpu, 0x5350495446495245L, 8)
        # and cpu version
        SIM_write_phys_memory(SIM_get_object(global_cpu[machine]), base + 0x400 * cpu + 0x30, 0x0000001100000000L, 8)

def set_memory_conf():
    global object_list
    banks = {}
    for i in bank_size:
        banks[i] = []
    tot_mem = 0L
    for i in mem_list[machine]:
        if i[1] == 0:
            continue
        tot_mem += i[1] * 1024 * 1024L
        banks[i[1]].append([i[2], i[0]])
    mem = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    mem += [[0x00000000000L, OBJ(machine + "memory0"), 0x0, 0, tot_mem]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", mem)
    object_list[machine] += ([OBJECT(machine + "memory0", "ram",
                                     image = OBJ(machine + "memory0_image"))] +
                             [OBJECT(machine + "memory0_image", "image",
                                     queue = "<queue>",
                                     size = tot_mem)])
    start = 0L
    for i in range(0, len(bank_size)):
        for j in banks[bank_size[i]]:
            set_attribute(object_list[machine], machine + "ac" + `j[0]`, "bank" + `j[1]` + "_mask", bank_mask[i])
            set_attribute(object_list[machine], machine + "ac" + `j[0]`, "bank" + `j[1]` + "_match", start >> 26)
            set_attribute(object_list[machine], machine + "ac" + `j[0]`, "bank" + `j[1]` + "_valid", 1)
            try:
                cnt = get_attribute(object_list[machine], machine + "sstat" + `j[0]`, "connector")
            except:
                cnt = []
                for k in range(0, 16):
                    cnt.append(0)
            if j[1] == 0:
                for k in range(0, 8):
                    cnt[k] = bank_stat[i]
            elif j[1] == 1:
                for k in range(8, 16):
                    cnt[k] = bank_stat[i]
            set_attribute(object_list[machine], machine + "sstat" + `j[0]`, "connector", cnt)
            start += bank_size[i] * 1024 * 1024
    return tot_mem

def set_cpu_params():
    for i in cpu_list[machine]:
        cpu = SIM_get_object(machine + "cpu" + `i`)
        SIM_write_register(cpu, SIM_get_register_number(cpu, "o2"), 0x1fff8206700L)
        SIM_write_register(cpu, SIM_get_register_number(cpu, "o3"), 0x6000)

def set_global_cpu():
    global global_cpu, global_mid, object_list
    objs = []
    # set global_mid to the cpu on the highest board
    global_mid[machine] = -1
    for i in object_list[machine]:
        if i[1] == "ultrasparc-ii":
            idx = len(machine) + len("cpu")
            if global_mid[machine] < int(i[0][idx:]) and (int(i[0][idx:]) % 2) == 0:
	        global_cpu[machine] = i[0]
                global_mid[machine] = int(i[0][idx:])
                break # take the first cpu for now!
    add_clock_board(global_mid[machine])
    for i in object_list[machine]:
        try:
            queue = get_attribute(object_list[machine], i[0], "queue")
            if queue == "<queue>":
                set_attribute(object_list[machine], i[0], "queue", OBJ(global_cpu[machine]))
        except:
            pass

    mem = get_attribute(object_list[machine], machine + "phys_mem0", "map")
    mem += [[0x1fff8000000L, OBJ(machine + "board_" + `global_mid[machine] >> 1` + "_space"), 1, 0x0, 0x8000000]]
    set_attribute(object_list[machine], machine + "phys_mem0", "map", mem)
    # not really needed, but useful for inquiry accesses with no cpu set
    set_attribute(object_list[machine], machine + "local_space", "master-upa", global_mid[machine])
    # list of fhcs
    fhc_list = []
    for o in object_list[machine]:
        if o[1] == "sun4u-fhc":
            fhc_list.append(OBJ(o[0]))
    for o in object_list[machine]:
        if o[1] == "sun4u-fhc":
            set_attribute(object_list[machine], o[0], "fhc-list", fhc_list)
    # set central bits
    brd_conf = get_attribute(object_list[machine], machine + "ac" + `global_mid[machine] >> 1`, "brd_conf")
    brd_conf |= (1 << 31) | (1 << 15)
    set_attribute(object_list[machine], machine + "ac" + `global_mid[machine] >> 1`, "brd_conf", brd_conf)
    # set frequency
    reg_freq = cpu_freqs[global_cpu_freq[machine]][0] ^ 0xfa
    # range set to 3 means division by 1 (on new clock boards)
    range = range_inv[cpu_freqs[global_cpu_freq[machine]][1]]
    divide = divid_inv[cpu_freqs[global_cpu_freq[machine]][2]]
    set_attribute(object_list[machine], machine + "clks", "clk_reg2", (((divide >> 1) & 1) << 4) |
                                                       ((range & 0x3) << 2) |
                                                       ((divide & 1) << 1) |
                                                       ((reg_freq >> 8) & 1))
    set_attribute(object_list[machine], machine + "clks", "clk_reg1", reg_freq & 0xff)
    set_attribute(object_list[machine], machine + "clks", "clk_reg3", (divide >> 2) & 1)
    #finally add hostfs
    if use_hostfs:
        mem = get_attribute(object_list[machine], machine + "board_" + `global_mid[machine] >> 1` + "_space", "map")
        mem += [[0x101000, OBJ(machine + "hfs0"), 0, 0x0, 0x10]]
        set_attribute(object_list[machine], machine + "board_" + `global_mid[machine] >> 1` + "_space", "map", mem)
        conf = ([OBJECT(machine + "hfs0", "hostfs")])
        object_list[machine] += conf

def create_cpu_spaces():
    global object_list
    for i in object_list[machine]:
        if i[1] == "ultrasparc-ii":
            space = machine + "%s_mem" % i[0]
            set_attribute(object_list[machine], i[0], "physical_memory", OBJ(space))
            object_list[machine] += [OBJECT(space, "memory-space",
                            map = [[0, OBJ(machine + "phys_mem0"), 0, 0, 0xffffffffffffffff]])]

def init_cheerio_hme_prom():
    dat = (0x90, 0x28, 0x00, 0x4e, 0x41, 0x06)
    for o in object_list[machine]:
        if o[1] == "cheerio-hme":
            try:
                image = SIM_get_object(o[0] + "_prom_image")
                for i in range(0, 6):
                    image.byte_access[0xc010 + i] = dat[i]
            except:
                pass

tot_mem = {}

def get_configuration():
    global tot_mem, machine
    all_objs = []
    for mach in machine_list:
        machine = mach
        tot_mem[machine] = set_memory_conf()
        set_global_cpu()
        all_objs += object_list[machine]
    return all_objs

def post_configuration():
    global machine

    init_cheerio_hme_prom()
        
    for mach in machine_list:
        machine = mach
        write_post_sram_data()
        set_cpu_sram()
        set_cpu_params()
        set_idprom()
        eval_cli_line(machine + "system.set-prom-defaults")
        # patch POR reset to go directly to OBP
        for board in range(31):
            try:
                if board_list[machine][board] == "cpu":
                    eval_cli_line("%sboard_%d_space.set 0x20 0x30800028 4" % (machine, board))
                    eval_cli_line("%sboard_%d_space.set 0x24 0x01000000 4" % (machine, board))
            except:
                pass
        # set some Simics default values in the nvram
        if num_gfx_consoles[mach] > 0:
            eval_cli_line(machine + "system.set-prom-env input-device keyboard")
            eval_cli_line(machine + "system.set-prom-env output-device screen")
        else:
            eval_cli_line(machine + "system.set-prom-env input-device ttya")
            eval_cli_line(machine + "system.set-prom-env output-device ttya")
            eval_cli_line(machine + "system.set-prom-env \"screen-#rows\" 24")

        eval_cli_line(machine + "system.set-prom-env sbus-probe-default \"3120\"")
        eval_cli_line(machine + "system.set-prom-env boot-command \"boot disk1 -v\"")
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
