# A simple Open Firmware implementation for Simics
#

# MODULE: ppc-of
# CLASS: ppc-of

class_name = "ppc-of"

from sim_core import *
from cli import *
import sim_commands

import sys
import re
import string
import time

# PCI bridge accessible through RTAS
if "pci_bridge" not in dir():
    try:
        pci_bridge = conf.pci_bus0_conf
    except:
        pass

class pnode:
    pnodes = {}                         # indexed by phandle
    def __init__(self, phandle, name, properties = {}, children = [],
                 methods = {}):
        self.phandle = phandle
        self.name = name
        properties.setdefault('name', name)
        self.properties = properties
        self.children = children
        self.methods = methods
        pnode.pnodes[phandle] = self

    def set_parents(self, parent = None):
        self.parent = parent
        for p in self.children:
            p.set_parents(self)

    def get_path(self):
        if self.parent:
            if self.parent.parent:
                sep = "/"
            else:
                sep = ""
            return self.parent.get_path() + sep + self.name
        else:
            return "/"

    def sibling(self):
        if self.parent:
            chn = self.parent.children
            n = len(chn)
            for i in range(n):
                if chn[i] == self:
                    if i + 1 < n:
                        return chn[i + 1]
                    else:
                        return None
        else:
            return None

class instance:
    instances = {}                      # indexed by ihandle
    def __init__(self, ihandle, parent_ihandle, pnode):
        self.ihandle = ihandle
        self.parent_ihandle = parent_ihandle
        self.pnode = pnode
        instance.instances[ihandle] = self

    def get_path(self):
        return self.pnode.get_path()

# return pnode with given node name (not path)
def pnode_by_name(name):
    for ph in pnode.pnodes:
        if pnode.pnodes[ph].name == name:
            return pnode.pnodes[ph]
    return None

def mmu_translate(inst, args):
    print "METHOD mmu-translate, args", repr(args)
    noyeim("mmu_translate")

# remove rtas breakpoints
def deinstantiate_rtas(obj):
    SIM_delete_breakpoint(obj.object_data.rtas_bid)
    SIM_hap_delete_callback_id("Core_Breakpoint", obj.object_data.rtas_hid)
    obj.object_data.rtas_bid = -1
    obj.object_data.rtas_hid = -1

# /rtas method: instantiate-rtas (base-addr -- rtas-entry-point)
def instantiate_rtas(obj, cpu, inst, args):
    if len(args) != 1:
        SIM_log_message(obj, 1, 0, Sim_Log_Error,
                        "instantiate-rtas: expected 1 arg, got %d" % len(args))
        return [1]
    [rtas_base] = args
    # just put the entry point in the block passed to us and put a return
    # address there, and break on it
    rtas_entry_point = rtas_base
    insert_return(cpu, rtas_entry_point)
    rtas_bid = SIM_breakpoint(cpu.physical_memory, Sim_Break_Physical, 4,
                              rtas_entry_point, 1, Sim_Breakpoint_Simulation)
    rtas_hid = SIM_hap_add_callback_index("Core_Breakpoint", rtas_handler,
                                          obj, rtas_bid)
    if obj.object_data.rtas_bid != -1 or obj.object_data.rtas_bid != -1:
        SIM_log_message(obj, 1, 0, Sim_Log_Error, "RTAS entry point error")
    obj.object_data.rtas_bid = rtas_bid
    obj.object_data.rtas_hid = rtas_hid
    obj.object_data.rtas_break[0] = 1
    obj.object_data.rtas_break[1] = rtas_entry_point
    SIM_log_message(obj, 3, 0, Sim_Log_Info,
                    "/rtas:instantiate-rtas 0x%x -> 0x%x"
                    % (rtas_base, rtas_entry_point))
    return [0, rtas_entry_point]

def rtas_handler(of, obj, type, bp_id, dummy1, dummy2):
    cpu = of.object_data.cpu
    r3 = cpu.gprs[3]
    token = read_phys_mem(cpu, r3, 4)
    nargs = read_phys_mem(cpu, r3 + 4, 4)
    nret = read_phys_mem(cpu, r3 + 8, 4)
    if rtasfuncs.has_key(token):
        args = [read_phys_mem(cpu, r3 + 12 + 4 * i, 4) for i in range(nargs)]
        n = nargs
        for x in rtasfuncs[token][1](of, args, nret):
            write_phys_mem(cpu, r3 + 12 + 4 * n, 4, x)
            n = n + 1
        if n == nargs + nret:
            cpu.gprs[3] = 0
            return
        SIM_log_message(obj, 1, 0, Sim_Log_Error, "RTAS: bad number of return values!")
    else:
        SIM_log_message(obj, 1, 0, Sim_Log_Error, "Unknown RTAS token %x" % (token))
    cpu.gprs[3] = -1

def rtas_read_pci_config(of, args, nret):
    addr = args[0]
    n = args[1]
    val = 0L
    shift = 0
    try:
        for i in pci_bridge.memory[[addr, addr + n - 1]]:
            val = val | (long(i) << shift)
            shift = shift + 8
    except:
        pass
    #SIM_log_message(self.obj, 2, 0, Sim_Log_Info,
    #                "read-pci-config %x %x -- %x" % (addr, n, val))
    return [0, val]

def rtas_write_pci_config(of, args, nret):
    addr = args[0]
    n = args[1]
    val = args[2]
    xxx = [(val >> (8*i)) & 0xff for i in range(n)]

    #if self.obj.log_level >= 2:
    #    log_msg = "write-pci-config %x %x %x    [" % (args[0], args[1], args[2])
    #    for i in xxx:
    #        log_mgs += "%02x" % i,
    #    log_msg += "]"
    #    SIM_log_message(self.obj, 2, 0, Sim_Log_Info, log_msg)
    try:
        pci_bridge.memory[[addr, addr + n - 1]] = xxx
    except:
        pass
    return [0]

def rtas_get_time_of_day(of, args, nret):
    (year, month, day, hour, minute,
     second, weekday, _,_) = time.strptime(of.object_data.time_of_day,
                                           "%Y-%m-%d %H:%M:%S %Z")
    return [0, year, month, day, hour, minute, second, weekday]

rtasfuncs = {
    0x12345678 : ("read-pci-config",    rtas_read_pci_config),
    0x12345679 : ("write-pci-config",   rtas_write_pci_config),
    0x1234567a : ("get-time-of-day",    rtas_get_time_of_day)
}

# ihandles used
ihandle_stdin  = 0x10000
ihandle_stdout = 0x10001
ihandle_memory = 0x10002
ihandle_mmu    = 0x10003
ihandle_cpu    = 0x10004

devtree = None

def setup_instances(obj):
    instance.instances.clear()
    for inst in obj.object_data.instance_list:
        instance(inst[0], inst[1], pnode_by_name(inst[2]))

def of_init(of, cpu, megs):
    global devtree
    devtree = pnode(
                1, "/",
                {'name'              : "device-tree",
                 'device_type'       : "bootrom",
                 '#size-cells'       : 1,
                 '#address-cells'    : 1,
                 'model'             : 'Virtutron',
                 # platform-open-pic: addresses from regs in the openpic node
                 # (first is address of the IDU; then addresses of the ISUs)
                 'platform-open-pic' : [of.map_offset + 0x0fc00000L,
                                        of.map_offset + 0x0fc10000L],
                 },
                [pnode(2, "aliases"),
                 pnode(3, "openprom",
                       {'device_type'          : "BootROM",
                        'model'                : "OpenFirmware 3",
                        'relative-addressing'  : 1,
                        }),
                 pnode(4, "options"),
                 pnode(5, "chosen",
                       {'stdin'                : ihandle_stdin,
                        'stdout'               : ihandle_stdout,
                        'bootpath'             : "/magic-bootdev",
                        'bootargs'             : "ramdisk_size=32768 console=ttyS0",
                        'memory'               : ihandle_memory,
                        'mmu'                  : ihandle_mmu,
                        'cpu'                  : ihandle_cpu,
                        }),
                 pnode(6, "packages"),
                 pnode(7, "interrupt-controller",
                       {'device-type'          : "open-pic",
                        'compatible'           : "open-pic",
                        # needs more stuff
                        }),
                 pnode(8, "cpus",
                       {'#address-cells'       : 1,
                        '#size-cells'          : 0,
                        '#cpus'                : 1,
                        },
                       [pnode(9, "PowerPC",
                              {'device_type'       : "cpu",
                               # reg is zero for uniprocessors
                               'reg'               : 0,
                               'cpu-version'       : 0x003c0000, # ppc970fx
                               '64-bit'            : 1,
                               'd-cache-line-size' : 128,
                               'i-cache-line-size' : 128,
                               'clock-frequency'   : int(cpu.freq_mhz * 1000000),
                               'timebase-frequency': int(cpu.timebase_freq_mhz * 1000000),
                               }),
                        ],
                       {'translate'                : mmu_translate}),
                 pnode(10, "memory",
                       {'device_type'              : "memory",
                        'reg'                      : [0x0,
                                                      megs * 1024 * 1024],
                        }),
                 pnode(11, "pci",
                       {'device_type'               : "pci",
                        # pci ranges: [addr (3 words), phys, size (2 words)]
                        # first one for io-space, then one mem space
                        'ranges'                   : [0x01000000, 0, 0,
                                                      of.map_offset + 0x08000000L,
                                                      0, 0x10000,

                                                      0x02000000, 0, 0,
                                                      0x80000000L,
                                                      0, 0x1000000],
                        # reg: [address, size]
                        'reg'                      : [0x80000000L, 0x1000000L],
                        # must set model to something that Linux recognises
                        'model'                    : "Winnipeg",
                        '#address-cells'           : 3,
                        '#size-cells'              : 2,
                        # first/last bus numbers
                        'bus-range'                : [0, 0],
                        # FIXME: Implement this. see OF/CHRP, page 32.
                        # It is used to ack 8259 interrupts, which are routed
                        # to ISU 0 of the openpic.
                        #'8259-interrupt-acknowledge' : 0xf007ba11,
                        },
                       [pnode(12, "isa",
                              {'device_type'       : "isa",
                               'class-code'        : 0x060100, # isa bus
                               # ranges: [isa (2), pci (3), size (1)]
                               'ranges'            : [1, 0, 0x80000001L, 0, 0,
                                                      0x1000],
                               },
                              [pnode(13, "serial",
                                     {'device_type' : "serial",
                                      'ibm,aix-loc' : "S1",
                                      # reg: [space, address, size]
                                      # (1 is I/O space)
                                      'reg'         : [1, 0x3f8, 8],
                                      }),
                               ]),
                        ]),
                 pnode(14, "rtas",
                       {#'ibm,hypertas-functions'   : [],
                        # the above makes linux believe we're running native
                        # and not under a hypervisor
                        'rtas-size'                : 0x100,
                        },
                       [],
                       {'instantiate-rtas' : lambda x, y: instantiate_rtas(of, cpu, x, y)}),
                 # our magic OF console
                 pnode(15, "magic-console"),
                 # a magic boot device
                 pnode(16, "magic-bootdev"),
                 ])
    devtree.set_parents()

    # add RTAS properties
    rtas_pn = pnode_by_path("/rtas")
    for x in rtasfuncs:
        rtas_pn.properties[rtasfuncs[x][0]] = x

    # now create some instances
    setup_instances(of)

# Return pnode, searching by path name
# Note: Only absolute paths may be used, and no arguments etc.
def pnode_by_path(path, pnode = None, prefix = ""):
    if not pnode:
        pnode = devtree
    name = prefix + pnode.name
    if name == path:
        return pnode
    if name != "/":
        name += "/"
    for p in pnode.children:
        pp = pnode_by_path(path, p, name)
        if pp:
            return pp
    return None

def phandle_by_pnode(pnode):
    if pnode:
        return pnode.phandle
    else:
        return -1


# The OpenFirmware services, this should be inherited by a target specific
# OpenFirmware handler.
class openfirmware_services:
    def __init__(self, cpu):
        self.cpu = cpu

    # finddevice
    #     IN:  [string] device-specifier
    #     OUT: phandle
    def finddevice(self, argv):
        if len(argv) != 1:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "finddevice: expected 1 arg, got %d" % len(argv))

        devspec = string_from_memory(self.cpu, argv[0])
        phandle = phandle_by_pnode(pnode_by_path(devspec))

        SIM_log_message(self.obj, iff(phandle == -1, 2, 3), 0, Sim_Log_Info,
                        "finddevice '%s' -> %d" % (devspec, phandle))

        return [phandle]

    # getproplen
    #    IN:  phandle, [string] name
    #    OUT: size
    def getproplen(self, argv):
        if len(argv) != 2:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "getprop: expected 4 args, got %d" % len(argv))

        phandle = argv[0]
        name    = string_from_memory(self.cpu, argv[1])

        error = ""
        prop = None
        size  = -1
        if pnode.pnodes.has_key(phandle):
            p = pnode.pnodes[phandle]
            if p.properties.has_key(name):
                prop = p.properties[name]
                size = get_obj_size(prop)
            else:
                error = "No property " + name + " for node: " + p.name
        else:
            error = "No phandle %d found" % phandle

        SIM_log_message(self.obj, iff(error != "", 2, 3), 0, Sim_Log_Info,
                        "getproplen %d, '%s', -> %d %s" % (phandle, name, size, error))
        return [size]

    # getprop
    #    IN:  phandle, [string] name, [address] buf, buflen
    #    OUT: size
    def getprop(self, argv):
        if len(argv) != 4:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "getprop: expected 4 args, got %d" % len(argv))

        phandle = argv[0]
        name    = string_from_memory(self.cpu, argv[1])
        buf     = argv[2]
        blen    = argv[3]

        error = ""
        prop = None
        size  = -1
        if pnode.pnodes.has_key(phandle):
            p = pnode.pnodes[phandle]
            if p.properties.has_key(name):
                prop = p.properties[name]
                size = obj_to_phys_mem(self.cpu, buf, prop)
            else:
                error = "No property " + name + " for node: " + p.name
        else:
            error = "No phandle %d found" % phandle

        SIM_log_message(self.obj, iff(error != "", 2, 3), 0, Sim_Log_Info,
                        "getprop %d, '%s', 0x%x, %d -> [0x%x]=%s %d %s"
                        % (phandle, name, buf, blen, buf, prop, size, error))

        return [size]

    # instance-to-path
    #    IN:  ihandle, [address] buf, buflen
    #    OUT: length
    def instance_to_path(self, argv):
        if len(argv) != 3:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "instance-to-path: expected 3 args, got %d" % len(argv))

        ihandle = argv[0]
        buf     = argv[1]
        blen    = argv[2]

        length = -1
        path = None

        if instance.instances.has_key(ihandle):
            inst = instance.instances[ihandle]
            path = inst.get_path()
            length = obj_to_phys_mem(self.cpu, buf, path)
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "instance-to-path: bad ihandle: 0x%x" % ihandle)

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info,
                        "instance-to-path 0x%x, 0x%x, %d -> [0x%x]=%s %d"
                        % (ihandle, buf, blen, buf, path, length))

        return [length]

    # instance-to-package
    #    IN:  ihandle
    #    OUT: phandle
    def instance_to_package(self, argv):
        if len(argv) != 1:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "instance-to-package: expected 1 arg, got %d" % len(argv))

        ihandle = argv[0]

        if instance.instances.has_key(ihandle):
            phandle = instance.instances[ihandle].pnode.phandle
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "[of] instance-to-package: bad ihandle %d" % ihandle)
            phandle = -1

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info,
                        "instance-to-package 0x%x -> 0x%x" % (ihandle, phandle))

        return [phandle]

    # canon
    #    IN:  [string] device-specifier, [address] buf, buflen
    #    OUT: length
    def canon(self, argv):
        if len(argv) != 3:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "canon: expected 3 args, got %d" % len(argv))

        devspec = string_from_memory(self.cpu, argv[0])
        buf     = argv[1]
        blen    = argv[2]

        # Not fully implemented - always returns its argument unchanged
        s = devspec
        length = obj_to_phys_mem(self.cpu, buf, s)

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info,
                        "canon %s, 0x%x, %d -> %s %d"
                        % (devspec, buf, blen, s, length))

        return [length]

    # peer
    #    IN:  phandle
    #    OUT: sibling-phandle
    def peer(self, argv):
        if len(argv) != 1:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "peer: expected 1 arg, got %d" % len(argv))

        phandle = argv[0]
        sibling = 0
        if phandle == 0:
            sibling = devtree.phandle
        else:
            if pnode.pnodes.has_key(phandle):
                s = pnode.pnodes[phandle].sibling()
                if s:
                    sibling = s.phandle
            else:
                SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "peer: bad phandle %d" % phandle)

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "peer %d -> %d" % (phandle, sibling))

        return [sibling]

    # parent
    #    IN:  phandle
    #    OUT: parent-phandle
    def parent(self, argv):
        if len(argv) != 1:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "parent: expected 1 arg, got %d" % len(argv))

        phandle = argv[0]
        if pnode.pnodes.has_key(phandle):
            p = pnode.pnodes[phandle]
            if p.parent:
                parent = p.parent.phandle
            else:
                parent = 0
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "parent: bad phandle %d" % phandle)

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "parent %d -> %d" % (phandle, parent))
        return [parent]

    # child
    #    IN:  phandle
    #    OUT: child-phandle
    def child(self, argv):
        if len(argv) != 1:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "child: expected 1 arg, got %d" % len(argv))

        phandle = argv[0]
        if pnode.pnodes.has_key(phandle):
            p = pnode.pnodes[phandle]
            if p.children:
                childp = p.children[0].phandle
            else:
                childp = 0
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "child: bad phandle %d" % phandle)

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "child %d -> %d" % (phandle, childp))
        return [childp]

    # write
    #    IN:  ihandle, [address] addr, str_len
    #    OUT: actual
    def write(self, argv):
        if len(argv) != 3:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "write: expected 3 args, got %d" % len(argv))
        ihandle = argv[0]
        addr    = argv[1]
        str_len = argv[2]
        # Get actual string to write
        s = reduce(lambda a, b: a + b, map(chr, bytes_from_memory(self.cpu, addr, str_len)))

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info,
                        "write 0x%x, 0x%x (%s), %d" % (ihandle, addr, repr(s), str_len))
        if ihandle == ihandle_stdout:
            if self.echo_stdout and self.obj.log_level < 3:
                SIM_log_message(self.obj, 0, 0, Sim_Log_Info, s)
            else:
                con = conf.con0.iface.serial_device
                obj = conf.con0
                for c in s:
                    con.write(obj, ord(c))
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "[of] Request to write to ihandle %d" % ihandle)

        return [str_len]

    # read
    #    IN:  ihandle, [address] addr, len
    #    OUT: actual
    def read(self, argv):
        if len(argc) != 3:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "read: expected 3 args, got %d" % argc)
        ihandle = argv[0]
        addr    = argv[1]
        str_len = argv[2]
        SIM_log_message(self.obj, 1, 0, Sim_Log_Unimplemented, "read called, not implemented!!")
        obj_to_phys_mem(self.cpu, addr, "f")
        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "read 0x%x, 0x%x, %d"
                        % (ihandle, addr, str_len))
        return [1]

    # open
    #    IN:  [string] device-specifier
    #    OUT: ihandle
    def open(self, argv):
        if len(argv) != 1:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "open: expected 1 arg, got %d" % len(argv))

        name    = string_from_memory(self.cpu, argv[0])
        ihandle = 0
        p = pnode_by_path(name)
        if p:
            # TODO: We should really open all parent nodes as well
            inst = instance(self.next_ihandle, 0, p)
            ihandle = self.next_ihandle
            self.next_ihandle += 1

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "open %s -> 0x%x" % (name, ihandle))

        return [ihandle]

    # close
    #    IN:  ihandle
    #    OUT: none
    def close(self, argv):
        if len(argv) != 1:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "close: expected 1 arg, got %d" % len(argv))
        ihandle = argv[0]
        if instance.instances.has_key(ihandle):
            del instance.instances[ihandle]
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "close: bad ihandle %d" % ihandle)
        return []


    # call-method
    #    IN:  [string] method, ihandle, stack-arg1....
    #    OUT: catch-result, stack-result1....
    def call_method(self, argv):
        method  = string_from_memory(self.cpu, argv[0])
        ihandle = argv[1]

        arg = []
        for i in range(2,len(argv)):
            arg.append(argv[i])

        values = [-1]
        if instance.instances.has_key(ihandle):
            inst = instance.instances[ihandle]
            if inst.pnode.methods.has_key(method):
                values = inst.pnode.methods[method](inst, arg)
            else:
                SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                                "call-method: node %s has no method %s(), ignoring it."
                                % (inst.pnode.name, method))
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "call-method: bad ihandle %d for method %s()" % (ihandle, method))

        SIM_log_message(self.obj, 2, 0, Sim_Log_Info, "call-method %s %d %s" % (method, ihandle, arg))

        return values

    # nextprop
    #    IN:  phandle, [string] previous, [address] buf
    #    OUT: flag
    def nextprop(self, argv):
        if len(argv) != 3:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "nextprop: expected 3 args, got %d" % len(argv))

        phandle  = argv[0]
        previous_ptr = argv[1]
        if previous_ptr:
            previous = string_from_memory(self.cpu, previous_ptr)
        else:
            previous = ""
        buf     = argv[2]

        flag = -1
        nextprop = ""
        if pnode.pnodes.has_key(phandle):
            p = pnode.pnodes[phandle]
            propnames = p.properties.keys()
            if previous:
                for i in range(len(propnames)):
                    if propnames[i] == previous:
                        if i + 1 < len(propnames):
                            nextprop = propnames[i + 1]
                            flag = 1
                        else:
                            flag = 0
                        break
            else:
                # first property name
                if propnames:
                    nextprop = propnames[0]
                    flag = 1
                else:
                    flag = 0
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "nextprop: bad phandle %d" % phandle)

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "nextprop %d '%s' %x -> '%s' %d"
                        % (phandle, previous, buf, nextprop, flag))

        if nextprop:
            obj_to_phys_mem(self.cpu, buf, nextprop)
        return [flag]

    # package-to-path
    #    IN:  ihandle, [address] buf, buflen
    #    OUT: length
    def package_to_path(self, argv):
        if len(argv) != 3:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "package-to-path: expected 3 args, got %d" % len(argv))

        phandle = argv[0]
        buf     = argv[1]
        blen    = argv[2]
        size = -1
        path = None

        if pnode.pnodes.has_key(phandle):
            path = pnode.pnodes[phandle].get_path()
            size = obj_to_phys_mem(self.cpu, buf, path)
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                            "package-to-path: bad phandle %d", phandle)


        SIM_log_message(self.obj, 3, 0, Sim_Log_Info,
                        "package-to-path %d, 0x%x, %d -> [0x%x]=%s %d"
                        % (phandle, buf, blen, buf, path, size))

        return [size]

    # quiesce
    #    IN:  [string] device-specifier
    #    OUT: ihandle
    def quiesce(self, argv):
        if len(argv) != 0:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "quiesce: expected 0 args, got %d" % len(argv))

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "quiesce")
        return []


    # claim
    #     IN:  [address] virt, size, align
    #     OUT: [address] baseaddr
    def claim(self, argv):
        if len(argv) != 3:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "claim: expected 3 arg, got %d" % argc)

        virt = argv[0]
        sz   = argv[1]
        align= argv[2]

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "claim 0x%x 0x%x %d -> 0x%x" % (virt,sz,align,virt))

        return [virt]

    # seek
    #     IN:  ihandle, pos.hi, pos.lo
    #     OUT: status
    def seek(self, argv):
        if len(argv) != 3:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "seek: expected 3 arg, got %d" % argc)

        ihandle = argv[0]
        hi      = argv[1]
        lo      = argv[2]
        pos = hi << 32 + lo

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "seek %d 0x%x 0x%x" % (ihandle,hi,lo))

        return [0]

    # interpret
    #     IN:  [string] cmd, stack-arg1 ... stack-argP
    #     OUT: catch-result, stack-result1, ... stack-resultQ
    def interpret(self, argv):
        cmd = string_from_memory(self.cpu, argv[0])
        arg = []
        for i in range(1,argc):
            arg.append(argv[i])

        SIM_log_message(self.obj, 3, 0, Sim_Log_Info, "interpret:\n%s args: %s" % (cmd, str(arg)))

        return [0]



# This is the PowerPC fake implementation of OpenFirware
class ppc_of_instance(openfirmware_services):
    def __init__(self, obj):
        # Update the mapping from configuration objects to this instance,
        # and the other way.
        obj.object_data = self
        self.obj = obj
        # Initialize instance variables (we only have one).
        self.entry_point = 0
        self.cpu = None
        self.memory_megs = 0
        self.next_ihandle = 0x10005
        self.rtas_bid = -1
        self.rtas_hid = -1
        self.rtas_break = [0, 0, 0]
        self.instance_list = [[ihandle_stdin,  0, "magic-console"],
                              [ihandle_stdout, 0, "magic-console"],
                              [ihandle_memory, 0, "memory"],
                              [ihandle_cpu,    0, "PowerPC"],
                              [ihandle_mmu,    0, "PowerPC"]]
        self.map_offset = 0xf0000000
        self.time_of_day = "2006-06-06 06:06:06 UTC"

    def setup_of(self, of_entry_point, cpu):
        global ihandle_stdin
        global ihandle_stdout
        global ihandle_memory
        global ihandle_mmu
        global ihandle_cpu

        openfirmware_services.__init__(self, cpu)
        insert_return(cpu, of_entry_point)
        self.bid = SIM_breakpoint(cpu.physical_memory, Sim_Break_Physical, 4,
                                  of_entry_point, 1, Sim_Breakpoint_Simulation)
        SIM_hap_add_callback_index("Core_Breakpoint", self.entry_point_func, 0,
                                   self.bid)
        SIM_log_message(self.obj, 1, 0, Sim_Log_Info,
                        "OpenFirmware python layer hooked in at 0x%x" % (of_entry_point))
        self.echo_stdout = 0
        self.devtree = devtree

    #
    # This is the OpenFirware entry point
    # r3 contains the pointer to the structure:
    #    char *service 32bits
    #    long argc
    #    long nrets
    #    .... arg buffer
    #    .....ret buffer
    def entry_point_func(self, obj, cb_data, type, bp_id, reg, size):
        r3 = self.cpu.gprs[3]
        service = string_indirect(self.cpu, r3)
        argc = read_phys_mem(self.cpu, r3 + 4, 4)
        #nrets = read_phys_mem(self.cpu, r3 + 8, 4)
        argv = []
        for i in range(0,argc):
            argv.append(read_phys_mem(self.cpu, r3 + 12 + (i*4), 4))

        # Convert "-" to "_" to generate ok python method names
        service = string.replace(service,"-","_")
        if service in dir(self):
            # Call handler:
            # (we should actually return a success value in r3 (0 or -1)
            # according to the specs, but this seems not to be used by
            # the Linux kernel.)
            retl = eval("self." + service + "(argv)")

            # Write back the return
            write_phys_mem(self.cpu, r3 + 8, 4, len(retl)) # nargs returned
            for i in range(len(retl)):
                write_phys_mem(self.cpu, r3 + 12 + argc*4 + (i*4), 4, retl[i])
        else:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Error, "No handler for OF service: %s" % str(service))

# Set up bootinfo records to describe initial ram disk
def setup_bootinfo(cpu, addr, rdstart, rdsize):
    BI_FIRST = 0x1010
    BI_LAST = 0x1011
    BI_INITRD = 0x1014
    write_phys_words(cpu, addr, [BI_FIRST, 12, addr + 28,
                            BI_INITRD, 16, rdstart, rdsize,
                            BI_LAST, 12, addr])

def write_phys_words(cpu, addr, words):
    for i in range(len(words)):
        write_phys_mem(cpu, addr + (i << 2), 4, words[i])


def get_obj_size(obj):
    if type(obj) == type("foo"):
        return len(obj) + 1
    elif type(obj) == type([1]):
        size = 0
        for i in range(len(obj)):
            size += get_obj_size(obj[i])
        return size
    else:
        return 4

# write a string, a vector, or an integer (32-bit) to physical memory
def obj_to_phys_mem(cpu, addr, obj):
    if type(obj) == type("foo"):
        i = 0
        for i in range(len(obj)):
            write_phys_mem(cpu, addr + i, 1, ord(obj[i]))
        write_phys_mem(cpu, addr + i + 1, 1, 0)
        return len(obj) + 1
    elif type(obj) == type([1]):
        size = 0
        for i in range(len(obj)):
            obj_addr = addr + size
            size += obj_to_phys_mem(cpu, obj_addr, obj[i])
        return size
    else:
        write_phys_mem(cpu, addr, 4, obj)
        return 4

# Returns a value read from memory (len must be in range [1-8])
def read_phys_mem(cpu, addr,len):
    val = 0L
    for i in cpu.physical_memory.memory[[addr, addr + len - 1]]:
        val = (val << 8) | i
    return val

# Write a value to memory
def write_phys_mem(cpu, addr,len,value):
    t = []
    for i in range(len):
        t.append(value & 0xff)
        value = value >> 8
    t.reverse() # big-endian
    cpu.physical_memory.memory[[addr,addr+len-1]] = t

# Reads a NUL terminated string from memory, this string is returned
def string_from_memory(cpu, addr):
    str = ""
    while 1:
        c = read_phys_mem(cpu, addr, 1)
        if c != 0:
            str += chr(c)
            addr += 1
        else:
            break
    return str

# Reads len bytes from memory, returned back as a list
def bytes_from_memory(cpu, addr,len):
    l = []
    for i in range(len):
        b = read_phys_mem(cpu, addr + i, 1)
        l.append(b)
    return l


def string_indirect(cpu, addr):
    ptr = read_phys_mem(cpu, addr, 4)
    return string_from_memory(cpu, ptr)


def bytes_indirect(cpu,addr,len):
    ptr = read_phys_mem(cpu, addr, 4)
    return bytes_from_memory(cpu, ptr, len)

def noyeim(fn):
    print "not yet implemented:", fn
    SIM_break_simulation("whoa")

# insert return instruction at physical address
def insert_return(cpu, physaddr):
    write_phys_mem(cpu, physaddr, 4, 0x4e800020) # blr



# Create a new configuration object and instance object of the class.
# This is called each time a new object of class
# is created. You probably do not need to modify this code.

def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    ppc_of_instance(obj)
    return obj

# The following function is called after the object is created and all
# attributes from the configuration are set. All other objects in the
# machine also exist at this point.

def finalize_instance(obj):
    of_init(obj, obj.object_data.cpu, obj.object_data.memory_megs)
    obj.object_data.setup_of(obj.object_data.entry_point, obj.object_data.cpu)
    if obj.object_data.rtas_break[0] == 1:
        instantiate_rtas(obj, obj.object_data.cpu, None,
                         [obj.object_data.rtas_break[1]])

def get_entry_point(arg, obj, idx):
    return obj.object_data.entry_point

def set_entry_point(arg, obj, val, idx):
    obj.object_data.entry_point = val
    return Sim_Set_Ok

def get_cpu(arg, obj, idx):
    return obj.object_data.cpu

def set_cpu(arg, obj, val, idx):
    obj.object_data.cpu = val
    return Sim_Set_Ok

def get_memory_megs(arg, obj, idx):
    return obj.object_data.memory_megs

def set_memory_megs(arg, obj, val, idx):
    obj.object_data.memory_megs = val
    return Sim_Set_Ok

def set_boot_info(arg, obj, val, idx):
    setup_bootinfo(obj.object_data.cpu, val[0], val[1], val[2])
    return Sim_Set_Ok

def get_next_ihandle(arg, obj, idx):
    return obj.object_data.next_ihandle

def set_next_ihandle(arg, obj, val, idx):
    obj.object_data.next_ihandle = val
    return Sim_Set_Ok

def get_rtas_breakpoint(arg, obj, idx):
    return obj.object_data.rtas_break

def set_rtas_breakpoint(arg, obj, val, idx):
    obj.object_data.rtas_break = val
    if obj.object_data.rtas_break[0] == 0 and obj.object_data.rtas_bid != -1:
        deinstantiate_rtas(obj)
    return Sim_Set_Ok

def get_instances(arg, obj, idx):
    ret = []
    for inst_key in instance.instances:
        ret += [[instance.instances[inst_key].ihandle,
                 instance.instances[inst_key].parent_ihandle,
                 instance.instances[inst_key].pnode.name]]
    return ret

def set_instances(arg, obj, val, idx):
    obj.object_data.instance_list = val
    return Sim_Set_Ok

def get_map_offset(arg, obj, idx):
    return obj.object_data.map_offset

def set_map_offset(arg, obj, val, idx):
    if obj.configured:
        return Sim_Set_Illegal_Value
    obj.object_data.map_offset = val
    return Sim_Set_Ok

def get_time_of_day(arg, obj, idx):
    return obj.object_data.time_of_day

def set_time_of_day(arg, obj, val, idx):
    if obj.configured:
        return Sim_Set_Illegal_Value
    try:
        time.strptime(val, "%Y-%m-%d %H:%M:%S %Z")
    except Exception, msg:
        SIM_attribute_error(str(msg))
        return Sim_Set_Illegal_Value
    obj.object_data.time_of_day = val
    return Sim_Set_Ok


# The top-level code in the file is run when the module is loaded.
# It should create the implemented configuration classes and register
# all attributes.

# First, register the class with Simics:

class_data = class_data_t()
class_data.new_instance = new_instance           # function defined above
class_data.finalize_instance = finalize_instance # function defined above
class_data.description = """A simple Open Firmware implementation for Simics.""";
SIM_register_class(class_name, class_data)

# Next, register the attributes of this class:

SIM_register_typed_attribute(class_name, "entry-point",
                             get_entry_point, None,
                             set_entry_point, None,
                             Sim_Attr_Required,
                             "i", None,
                             "The OpenFirmware entry-point.")

SIM_register_typed_attribute(class_name, "cpu",
                             get_cpu, None,
                             set_cpu, None,
                             Sim_Attr_Required,
                             "o", None,
                             "The CPU in the configuration.")

SIM_register_typed_attribute(class_name, "memory-megs",
                             get_memory_megs, None,
                             set_memory_megs, None,
                             Sim_Attr_Required,
                             "i", None,
                             "The amount of memory in MB.")

SIM_register_typed_attribute(class_name, "boot-info",
                             None, None,
                             set_boot_info, None,
                             Sim_Attr_Pseudo,
                             "[iii]", None,
                             "Setup boot-info, <i>[boot-info-address, in"
                             "itrd-base-address, initrd-size]</i>")

SIM_register_typed_attribute(class_name, "next-ihandle",
                             get_next_ihandle, None,
                             set_next_ihandle, None,
                             Sim_Attr_Optional,
                             "i", None,
                             "Internal, do not change.")

SIM_register_typed_attribute(class_name, "rtas-breakpoint",
                             get_rtas_breakpoint, None,
                             set_rtas_breakpoint, None,
                             Sim_Attr_Optional,
                             "[iii]", None,
                             "Internal, do not change.")

SIM_register_typed_attribute(class_name, "instances",
                             get_instances, None,
                             set_instances, None,
                             Sim_Attr_Optional,
                             "[[iis]*]", None,
                             "Internal, do not change.")

SIM_register_typed_attribute(class_name, "map_offset",
                             get_map_offset, None,
                             set_map_offset, None,
                             Sim_Attr_Optional,
                             "i", None,
                             "Base address for device mappings")

SIM_register_typed_attribute(class_name, "time-of-day",
                             get_time_of_day, None,
                             set_time_of_day, None,
                             Sim_Attr_Optional,
                             "s", None,
                             "Time of day that will be returned by the RTAS " \
                             "function get_time_of_day")

# info command prints static information
def get_info(obj):
    return []

# status command prints dynamic information
def get_status(obj):
    return [("Registers",
             [("Entry_point", obj.entry_point)])]

sim_commands.new_info_command(class_name, get_info)
sim_commands.new_status_command(class_name, get_status)

