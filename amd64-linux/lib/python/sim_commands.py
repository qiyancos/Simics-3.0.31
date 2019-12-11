import sys, os, time, string, types

if os.environ.has_key('SIMICS_PYCHECKER'):
    os.environ['PYCHECKER'] = ('--no-shadowbuiltin --no-argsused'
                               + ' --no-implicitreturns --no-shadow')
    import pychecker.checker

from cli import *
from refmanual import *
from re import *
from string import join
import os.path
import sim, __main__

def cast(cli_int_type, value):
    return cli_int_type([("int", value)])[0]

# checks that we either have no CPU's or that we're not running
def assert_not_running():
    try:
        current_processor()
    except:
        return
    if SIM_simics_is_running():
        raise CliError, "This command cannot be used when Simics is running."

# ok, this is duplicated, which it shouldn't be

def conf_object_expander(string):
    return get_completions(string, conf.all_object_names)

#
# -------------------- class-specific stuff --------------------
#

class_funcs = {}

def set_class_funcs(cls, funcs):
    class_funcs[cls] = funcs

def get_class_funcs(cls):
    if class_funcs.has_key(cls):
        return class_funcs[cls]
    else:
        return { }

def get_obj_funcs(obj):
    return get_class_funcs(obj.class_data)

def info_cmd(obj):
    title = "Information about %s [class %s]" % (obj.name, obj.classname)
    print title
    print "=" * len(title)
    try:
        fn = get_obj_funcs(obj)['get_info']
        info = fn(obj)
        if info:
            print_info(info, 30)
        else:
            print "No information available"
    except Exception, msg:
        print "Problem getting info for %s: %s" % (obj.name, msg)


def status_cmd(obj):
    title = "Status of %s [class %s]" % (obj.name, obj.classname)
    print title
    print "=" * len(title)
    try:
        fn = get_obj_funcs(obj)['get_status']
        info = fn(obj)
        if info:
            print_info(info, 30)
        else:
            print "No status available"
    except Exception, msg:
        print "Problem getting status for %s: %s" % (obj.name, msg)


# <add-fun id="simics api python">
# <short>define a new info command</short>
# <namespace>sim_commands</namespace>
#
# Define a new <cmd>info</cmd> command for a given device.
# <param>cls</param> is the class for which the <cmd>info</cmd> command
# should be registered. <param>get_info</param> is a function returning
# the information to be printed. <param>get_info()</param> should return
# a data structure of the following kind:
# <tt>
# [(SectionName1, [(DataName1.1, DataValue1.1),
#                  (DataName1.2, DataValue1.2), ...]),
#  (SectionName2, [(DataName2.1, DataValue2.1),
#                  (DataName2.2, DataValue2.2), ...]),
#  ...]
# </tt>
#
# Each section will be printed separately. Each piece of data will be printed
# on one line. If no sections are necessary, just provide <tt>None</tt> as
# the only section's name, followed by the list of data.
#
# </add-fun>
def new_info_command(cls, get_info, ctype = None):
    if ctype == None:
        ctype = cls+" commands"
    class_funcs = get_class_funcs(cls)
    if class_funcs.has_key('get_info'):
        print "Duplicate definitions of <%s>.info" % cls
        return
    class_funcs['get_info'] = get_info
    set_class_funcs(cls, class_funcs)
    new_command("info", info_cmd,
                [],
                alias = "",
                type = ctype,
                short = "print information about the device",
                namespace = cls,
                doc = "Print detailed information about the configuration of the device.", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="111")

# <add-fun id="simics api python">
# <short>define a new status command</short>
# <namespace>sim_commands</namespace>
#
# Define a new <cmd>status</cmd> command for a given device.
# <param>cls</param> is the class for which the <cmd>status</cmd> command
# should be registered. <param>get_status</param> is a function returning
# the information to be printed. <param>get_status()</param> should return
# a data structure of the same kind as in <fun>new_info_command()</fun>.
#
# <di name="SEE ALSO">sim_commands.new_info_command</di>
# </add-fun>
def new_status_command(cls, get_status, ctype = None):
    if ctype == None:
        ctype = cls+" commands"
    class_funcs = get_class_funcs(cls)
    if class_funcs.has_key('get_status'):
        print "Duplicate definitions of <%s>.status" % cls
        return
    class_funcs['get_status'] = get_status
    set_class_funcs(cls, class_funcs)
    new_command("status", status_cmd,
                [],
                alias = "",
                type = ctype,
                short = "print status of the device",
                namespace = cls,
                doc = "Print detailed information about the current status of the device.", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="140")

# This function is kindof unnecessary, really
def new_info_commands(cls, get_info, get_status):
    new_info_command(cls, get_info)
    new_status_command(cls, get_status)

# after info/status commands
import components

def local_print_disassemble_line(cpu, address, type, print_cpu = 1, mnemonic = None):
    f = get_obj_funcs(cpu)['print_disassemble_line']
    return f(cpu, address, type, print_cpu, mnemonic)

# Opcode print function for targets with four-byte instructions. Print
# the opcode as a word rather than as a sequence of bytes.
def fourbyte_print_opcode(cpu, paddr, length):
    try:
        word = "0x%08x" % SIM_read_phys_memory(cpu, paddr, 4)
    except:
        word = ""
    pr("%-*s" % (10, word))

# Return a local_print_disassemble_line function.
# default_instr_len(address) says how many bytes an instruction is
# considered to be if that could not be determined by the disassembly
# function. disasm is the disassembly function to use.
# virtual_address_prefix is the prefix to use when printing virtual
# addresses. print_opcode is the function that prints the opcode
# bytes. address_filter is applied to the address before it is used.
def make_print_disassemble_line_fun(default_instr_len = 4,
                                    disasm = SIM_disassemble,
                                    virtual_address_prefix = "v",
                                    print_opcode = fourbyte_print_opcode,
                                    address_filter = lambda address: address):

    # default_instr_len can be either a function or a number. If it is
    # a number, make a function that returns that number.
    try:
        deflen = int(default_instr_len)
        default_instr_len = lambda address: deflen
    except:
        pass

    # Translate address to (virtual, physical) pair, setting virtual
    # address to None if type indicades physical address. May raise an
    # Exception.
    def translate_address(cpu, address, type):
        if type == 1: # address is virtual
            vaddr = address
            try:
                paddr = SIM_logical_to_physical(cpu, 0, vaddr)
            except SimExc_Memory:
                raise Exception, "address not in TLB"
            except OverflowError:
                raise Exception, "illegal address"
        else: # address is physical
            vaddr = None # no way to get a well-defined virtual address
            paddr = address
        return (vaddr, paddr)

    # Print address profile views set for this processor.
    aprof_column_size = {}
    def print_aprof_views(cpu, vaddr, paddr, length):
        pr(" ")
        for ap, view in cpu.aprof_views:
            ifc = ap.iface.address_profiler
            if ifc.physical_addresses(ap, view):
                start = paddr
            else:
                start = vaddr
            id = (ap.name, view)
            if start != None:
                count = ifc.sum(ap, view, start, start + length - 1)
                aprof_column_size[id] = max(aprof_column_size.get(id, 1),
                                            len("%d" % count))
                pr("%*d " % (aprof_column_size[id], count))
            else:
                # Profiler is indexed by an address we can't compute.
                pr("%*s " % (aprof_column_size.get(id, 1), "?"))

    # Return the smallest number of hex digits sufficient to represent
    # the given number of bits.
    def bits_to_hex_digits(bits):
        return (bits + 3)/4

    # A local_print_disassemble_line function. To be returned.
    def lpdl_fun(cpu, address, type, print_cpu, name):
        if print_cpu:
            pr("[%s] " % cpu.name)
        address = address_filter(address)
        paddr_bits, vaddr_bits = cpu.address_width
        length = default_instr_len(address)
        try:
            vaddr, paddr = translate_address(cpu, address, type)
        except Exception, e:
            # Could not get physical address.
            paddr_err_string = e
            paddr = None
            vaddr = address
        if vaddr != None:
            pr("%s:0x%0*x " % (virtual_address_prefix,
                               bits_to_hex_digits(vaddr_bits), vaddr))
        if paddr is None:
            pr("<%s>\n" % paddr_err_string)
            return length
        if vaddr == None or disassembly_settings["physaddr"]:
            pr("p:0x%0*x " % (bits_to_hex_digits(paddr_bits), paddr))
        length = -1
        try:
            length, asm = disasm(cpu, address, type)
            if name != None:
                asm = name
        except SimExc_Memory, e:
            asm = "<whole instruction not in memory>"
        except SimExc_General, e:
            asm = "<%s>" % e
        if length > 0:
            if len(cpu.aprof_views) > 0:
                print_aprof_views(cpu, vaddr, paddr, length)
            if disassembly_settings["opcode"]:
                pr(" ")
                print_opcode(cpu, paddr, length)
                pr(" ")
        pr(" %s\n" % asm)
        return length

    return lpdl_fun

disassembly_settings = {
    "opcode":         0,
    "physaddr":       1,
    "partial-opcode": 1,
    }
disassembly_setting_desc = {
    "opcode":         "Print opcode bytes                           ",
    "physaddr":       "Print physical translation of virtual address",
    "partial-opcode": "Show only part of the opcode (ia64 only)     ",
    }

def disassemble_settings_cmd(opcode, physaddr, partial_opcode):
    if not (opcode or physaddr or partial_opcode):
        print "Current disassemble settings:"
        for name in disassembly_settings.keys():
            print "  %s %s" % (disassembly_setting_desc[name],
                               ["No", "Yes"][disassembly_settings[name]])
    if opcode:
        disassembly_settings["opcode"] = (opcode == "on")
    if physaddr:
        disassembly_settings["physaddr"] = (physaddr == "on")
    if partial_opcode:
        disassembly_settings["partial-opcode"] = (partial_opcode == "on")

def on_off_expander(string):
    return get_completions(string, ("on", "off"))
new_command("disassemble-settings", disassemble_settings_cmd,
            [arg(str_t, "opcode", "?", None, expander = on_off_expander),
             arg(str_t, "physaddr", "?", None, expander = on_off_expander),
             arg(str_t, "partial-opcode", "?", None,
                 expander = on_off_expander)],
            type = ["Command-Line Interface", "Output", "Execution", "Memory"],
            short = "change disassembly output settings",
            see_also = ["disassemble"],
            doc = """
Change disassemble output settings. Each of these settings can be set
to <tt>on</tt> or <tt>off</tt>.

<i>opcode</i> indicates whether to print the raw bytes of the
instruction in addition to the disassembly. If <i>partial-opcode</i>
is set, and the opcode encodes more than one instruction, the opcode
bytes will be divided among the instructions so that the entire opcode
has been printed exactly once when all the instructions have been
disassembled. If <i>partial-opcode</i> is not set, the entire opcode
will be printed for every instruction. (The only Simics target with
multiple instructions per opcode is ia64.)

<i>physaddr</i> indicates whether to compute and display the physical
address if the virtual address was specified (if the physical address
was specified, the virtual address is never printed).

Without arguments, the current settings will be shown.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="301")

def local_pregs(cpu, all):
    f = get_obj_funcs(cpu)['pregs']
    return f(cpu, all)

# Common functionality for PCI devices

# cross 32-bit reads not supported
def read_config(obj, offset, size):
    reg = offset / 4
    off = (offset % 4) * 8
    return 0L + (obj.config_registers[reg] >> off) & ((1L << size * 8) - 1)

def read_config_str(obj, offset, size):
    format = "0x%%0%dx" % (2 * size)
    return "%10s" % (format % read_config(obj, offset, size))

def get_pci_header_old(obj):
    if read_config(obj, 0xe, 1) != 1:
        # header type 0
        reg_list = [("Base Address 2", read_config_str(obj, 0x18, 4)),
                    ("Base Address 3", read_config_str(obj, 0x1c, 4)),
                    ("Base Address 4", read_config_str(obj, 0x20, 4)),
                    ("Base Address 5", read_config_str(obj, 0x24, 4)),
                    ("Cardbus CIS Ptr", read_config_str(obj, 0x28, 4)),
                    ("Subsystem Vendor ID", read_config_str(obj, 0x2c, 2)),
                    ("Subsystem Device ID", read_config_str(obj, 0x2e, 2)),
                    ("Expansion ROM Base", read_config_str(obj, 0x30, 4)),
                    ("Capabilities Ptr", read_config_str(obj, 0x34, 1)),
                    ("Interrupt Line", read_config_str(obj, 0x3c, 1)),
                    ("Interrupt Pin", read_config_str(obj, 0x3d, 1)),
                    ("Min Gnt", read_config_str(obj, 0x3e, 1)),
                    ("Max Lat", read_config_str(obj, 0x3f, 1))]
    else:
        # header type 1
        reg_list = [("Primary Bus Number", read_config_str(obj, 0x18, 1)),
                    ("Secondary Bus Number", read_config_str(obj, 0x19, 1)),
                    ("Subordinate Bus Number", read_config_str(obj, 0x1a, 1)),
                    ("Secondary Latency Timer", read_config_str(obj, 0x1b, 1)),
                    ("IO Base", read_config_str(obj, 0x1c, 1)),
                    ("IO Limit", read_config_str(obj, 0x1d, 1)),
                    ("Secondary Status", read_config_str(obj, 0x1e, 2)),
                    ("Memory Base", read_config_str(obj, 0x20, 2)),
                    ("Memory Limit", read_config_str(obj, 0x22, 2)),
                    ("Prefetchable Memory Base", read_config_str(obj, 0x24, 2)),
                    ("Prefetchable Memory Limit", read_config_str(obj, 0x26, 2)),
                    ("Prefetchable Base Upper", read_config_str(obj, 0x28, 4)),
                    ("Prefetchable Limit Upper", read_config_str(obj, 0x2c, 4)),
                    ("IO Base Upper", read_config_str(obj, 0x30, 2)),
                    ("IO Limit Upper", read_config_str(obj, 0x32, 2)),
                    ("Capabilities Ptr", read_config_str(obj, 0x34, 1)),
                    ("Expansion ROM Base", read_config_str(obj, 0x38, 4)),
                    ("Interrupt Line", read_config_str(obj, 0x3c, 1)),
                    ("Interrupt Pin", read_config_str(obj, 0x3d, 1)),
                    ("Bridge Control", read_config_str(obj, 0x3e, 2))]

    return [ ("Generic Registers",
              [ ("Vendor ID", read_config_str(obj, 0x0, 2)),
                ("Device ID", read_config_str(obj, 0x2, 2)),
                ("Command", read_config_str(obj, 0x4, 2)),
                ("Status", read_config_str(obj, 0x6, 2)),
                ("Revision ID", read_config_str(obj, 0x8, 1)),
                ("Class Code", read_config_str(obj, 0x9, 3)),
                ("Cache Line Size", read_config_str(obj, 0xc, 1)),
                ("Latency Timer", read_config_str(obj, 0xd, 1)),
                ("Header Type", read_config_str(obj, 0xe, 1)),
                ("BIST", read_config_str(obj, 0xf, 1)),
                ("Base Address 0", read_config_str(obj, 0x10, 4)),
                ("Base Address 1", read_config_str(obj, 0x14, 4))] +
              reg_list)]

def get_pci_header(obj):
    try:
        config_register_info = obj.config_register_info
    except:
        return get_pci_header_old(obj)
    header = []
    for x in config_register_info:
        header.append((x[1], read_config_str(obj, x[0], x[2])))
    return [ ("Configuration Registers", header) ]

def pci_header_cmd(obj):
    title = "PCI Header for %s [class %s]" % (obj.name, obj.classname)
    print title
    print "=" * len(title)
    # additional regs are optional
    fn = get_obj_funcs(obj)['get_conf']
    if fn:
        try:
            info = fn(obj)
        except Exception, msg:
            print "Problem getting header for %s: %s" % (obj.name, msg)
            info = []
    else:
        info = []
    print_info(get_pci_header(obj) + info, 30)

def new_pci_header_command(cls, get_conf = None):
    class_funcs = get_class_funcs(cls)
    if class_funcs.has_key('get_conf'):
        print "Duplicate definitions of <%s>.pci-header" % cls
        return
    class_funcs['get_conf'] = get_conf
    set_class_funcs(cls, class_funcs)
    new_command("pci-header", pci_header_cmd,
                [],
                alias = "",
                type  = cls + " commands",
                short = "print PCI device header",
                namespace = cls,
                doc = "Print the PCI header, i.e the configuration registers.", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="431")

def space_info(m, mem_on, io_on):
    dis = 0
    if m[5] & 4:
        name = "Expansion ROM"
        if not (m[5] & 1):
            dis = 1
    elif m[3] == 0: # memory
        if m[5] & 2:
            name = "64-bit Memory"
        else:
            name = "Memory"
        if not mem_on:
            dis = 1
    elif m[3] == 1: # I/O
        name = "IO"
        if not mem_on:
            dis = 1
    else:
        name = "Unknown"
    if not dis:
        desc = "base 0x%x size 0x%x (function %d)" % (m[1], m[2], m[4])
    else:
        desc = "base 0x%x size 0x%x (disabled)" % (m[1], m[2])
    return ("%s BAR 0x%x" % (name, m[0]), desc)

def get_pci_info(obj):
    try:
        rom = obj.expansion_rom
    except:
        # C++ implementations lack this attribute
        rom = None
    if rom:
        rom = "%s, function %d (0x%x bytes)" % (
            rom[0].name, obj.expansion_rom[2], obj.expansion_rom[1])
    else:
        rom = "none"
    try:
        maps = obj.mappings
    except:
        # C++ implementations lack this attribute
        maps = []
    io_on = obj.config_registers[1] & 1
    mem_on = obj.config_registers[1] & 2
    infos = []
    for m in maps:
        infos.append(space_info(m, mem_on, io_on))
    memory_mappings = [(None,
                        [ ("Memory mappings", iff(mem_on, "enabled", "disabled")),
                          ("IO mappings", iff(io_on, "enabled", "disabled"))])]
    if len(infos):
        memory_mappings += [("Supported Mappings", infos)]

    return [ ("PCI information",
              [ ("PCI bus", obj.pci_bus),
                ("Expansion ROM", rom),
                ])] + memory_mappings

def get_pci_status(obj):
    return []


#
# -------------------- tracker class --------------------
#

# This class provides a command factory for break-* and trace-*
# functions.  It is used by break-io, break-cr, and break-hap.  It
# shouldn't be used directly, but instead be subclassed with the
# specifics.
#
# Ths stop parameter to __init__ decides if it breaks or traces.
#
# The callback method is ususally used as a hap callback.  It can be
# given to SIM_hap_add_callback().  However, it can not be used
# in SIM_hap_callback_exists(), since the function pointer will be
# different each time.
#
# if namespace is None, global commands will be created
# if namespace is processor, a namespace command will be created
#
class tracker:
    def __init__(self, stop, cmd, target_name, expander,
                 short, doc,
                 namespace = None,
                 group = "breakpoint",
                 see_also = [],
                 expander_cpu = None):
        self.cmd = cmd
        self.stop = stop
        uncmd = "un"+cmd
        if type(target_name) == types.StringType:
            target_types = (str_t,)
            target_names = (target_name,)
            expander = (expander,)
            expander_cpu = (expander_cpu,)
        elif type(target_name) == types.TupleType:
            target_types, target_names = target_name
            if type(target_types) != types.TupleType:
                target_types = (target_types,)
                target_names = (target_names,)
        else:
            raise TypeError
        
        args = [arg(target_types + (flag_t, flag_t),
                    target_names + ("-all", "-list"),
                    expander = expander + (0, 0))]

        self.namespace = namespace
        if self.namespace:
            new_command(cmd, self.do_namespace_cmd, args, type=group,
                        short=short,
                        namespace = namespace,
                        see_also = see_also,
                        doc=doc, filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="548")

            new_command(uncmd, self.do_namespace_uncmd, args, type=group,
                        namespace = namespace,
                        short=short,
                        doc_with='<' + namespace + '>.' + cmd, filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="554")
            
            # if it's a processor, register commands on current processor
            if self.namespace == "processor":
                # use new args with expander_cpu instead
                cpu_args = [arg(target_types + (flag_t, flag_t),
                                target_names + ("-all", "-list"),
                                expander = expander_cpu + (0, 0))]

                new_command(cmd, self.do_cpu_cmd, cpu_args, type=group,
                            short=short,
                            doc_with='<' + namespace + '>.' + cmd, filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="566")

                new_command(uncmd, self.do_cpu_uncmd, cpu_args, type=group,
                            short=short,
                            doc_with='<' + namespace + '>.' + cmd, filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="570")

        else:
            new_command(cmd, self.do_cmd, args, type=group,
                        short=short,
                        see_also = see_also,
                        doc=doc, filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="575")

            new_command(uncmd, self.do_uncmd, args, type=group,
                        short=short,
                        doc_with=cmd, filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="580")

    def filter(self, *args):
        # Override this in your subclass if you want to ignore some
        # callbacks.
        if self.namespace:
            obj = args[0]
        return 1
    
    def resolve_target(self, *args):
        # This function translates the string given by the command to
        # something internally more useful, such as a configuration
        # object or something like that.  Override in a subclass.
        if self.namespace:
            obj, target = args
        else:
            target = args[0]
        return target

    def show(self, *args):
        # This function is called to print that something happened.
        # It should obviously be overridden in a subclass.
        if self.namespace:
            obj = args[0]
        print "Something happened"

    def list(self, *args):
        # This function is called to list the tracked things, in
        # response to the -list parameter.
        if self.namespace:
            obj = args[0]
        print "Cannot list"

    def is_tracked(self, *args):
        # This function is called to check if somthing is already
        # tracked.  Override it with something more useful.  Remember
        # that you can't use SIM_hap_callback_exists(self.callback).
        if namespace:
            obj = args[0]
        return 0

    def track_all(self, *args):
        # This function is called to set tracking on all possible choices.
        # Override it with something more useful.
        if namespace:
            obj = args[0]
            
    def track_none(self, *args):
        # This function is called to remove tracking on all possible choices.
        # Override it with something more useful.
        if namespace:
            obj = args[0]

    def track_on(self, *args):
        # This function is called to set tracking on a target.
        # Override it with something more useful.
        if self.namespace:
            obj = args[0]
            target = args[1]
        else:
            target = args[0]

    def track_off(self, *args):
        # This function is called to remove tracking on a target.
        # Override it with something more useful.
        if self.namespace:
            obj = args[0]
            target = args[1]
        else:
            target = args[0]

    def callback(self, *args):
        # Do not override this without a very good reason.
        if not self.filter(*args):
            return

        self.show(*args)
        if self.stop:
            raise SimExc_Break, self.cmd
        return 0

    def do_namespace_cmd(self, obj, target_desc):
        type, target_name, param = target_desc
        try:
            if type == flag_t and param == "-all":
                if obj:
                    self.track_all(obj)
                else:
                    self.track_all()
            elif type == flag_t and param == "-list":
                if obj:
                    self.list(obj)
                else:
                    self.list()
            else:
                if obj:
                    target = self.resolve_target(obj, target_name)
                    if not self.is_tracked(obj, target):
                        self.track_on(obj, target)
                else:
                    target = self.resolve_target(target_name)
                    if not self.is_tracked(target):
                        self.track_on(target)
        except SimExc_Index, msg:
            print msg
            SIM_command_has_problem()
            return
    
    def do_cmd(self, target_desc):
        self.do_namespace_cmd(None, target_desc)

    def do_cpu_cmd(self, target_desc):
        self.do_namespace_cmd(SIM_current_processor(), target_desc)

    def do_namespace_uncmd(self, obj, target_desc):
        type, target_name, param = target_desc
        try:
            if type == flag_t and param == "-all":
                if obj:
                    self.track_none(obj)
                else:
                    self.track_none()
            elif type == flag_t and param == "-list":
                if obj:
                    self.list(obj)
                else:
                    self.list()
            else:
                if obj:
                    target = self.resolve_target(obj, target_name)
                    if self.is_tracked(obj, target):
                        self.track_off(obj, target)
                else:
                    target = self.resolve_target(target_name)
                    if self.is_tracked(target):
                        self.track_off(target)                    
        except SimExc_Index, msg:
            print msg
            SIM_command_has_problem()
            return

    def do_uncmd(self, target_desc):
        self.do_namespace_uncmd(None, target_desc)

    def do_cpu_uncmd(self, target_desc):
        self.do_namespace_uncmd(SIM_current_processor(), target_desc)

#
# -------------------- -> --------------------
#

def attribute_cmd(o, a, rw, v):
    try:
        o = o.replace('-', '_')
        o = SIM_get_object(o)
    except SimExc_General:
        print 'There is no object called "%s"' % o
        SIM_command_has_problem()
        return
    
    a = a.replace('-', '_')
    if rw[2] == '-w':
        try:
            SIM_set_attribute(o, a, v[1])
        except SimExc_AttrNotFound:
            SIM_command_has_problem()
            print 'The "%s" object has no attribute "%s"' % (o.name, a)
            return
        except Exception, msg:
            try:
                if v[0] == str_t and v[1] in sim.objects:
                    SIM_set_attribute(o, a, SIM_get_object(v[1]))
                elif v[0] in (int_t, float_t) and v[1] == 0:
                    SIM_set_attribute(o, a, None)
                else:
                    raise
            except Exception, msg:
                SIM_command_has_problem()
                print 'Failed writing attribute %s in %s: %s' % (a, o.name, msg)
                return            
    else:
        try:
            val = SIM_get_attribute(o, a)
        except SimExc_AttrNotFound:
            SIM_command_has_problem()
            print 'The "%s" object has no attribute "%s"' % (o.name, a)
            return
        except Exception, msg:
            SIM_command_has_problem()
            print 'Failed reading attribute %s from %s: %s' % (a, o.name, msg)
            return
        if (isinstance(val, str)
            or isinstance(val, (int, long))):
            return val
        elif type(val) == type(conf.sim):
            return val.name
        elif isinstance(val, float):
            return val
        elif val == None:
            return 0
        else:
            print val

new_command("->", attribute_cmd,
            [arg(str_t, 'object'),
             arg(str_t, 'attribute'),
             arg((flag_t, flag_t), ('-r', '-w')),
             arg((int_t, str_t, float_t), ('ival', 'sval', 'fval'),
                 "?", doc = 'value')],
            type = ["Command-Line Interface"],
            pri = 700, infix = 1,
            group_short = "access object attribute",
            short = "access object attribute",
            doc = """
Get the value of <arg>attribute</arg> from <arg>object</arg>. Only object,
string, float and integer attributes can be returned by the command. Other
attribute types will be printed, but the command will not return anything.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="785")


#
# -------------------- + --------------------
#

def plus(a, b):
    if a[0] == b[0]:
        return a[1] + b[1]
    return str(a[1]) + str(b[1])

new_command("+", plus, [arg((int_t, str_t), ('isrc1', 'ssrc1'), doc = 'arg1'),
                        arg((int_t, str_t), ('isrc2', 'ssrc2'), doc = 'arg2')],
            type = ["Command-Line Interface"],
            pri = 150, infix = 1,
            group_short = "arithmetic addition",
            short = "arithmetic addition",
            doc = """
Arithmetic addition.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="811")

#
# -------------------- - --------------------
#

def minus(a, b):
    return a - b

new_command("-", minus, [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 150, infix = 1,
            short="arithmetic subtraction",
            doc="""
Arithmetic subtraction.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="828")

#
# -------------------- * --------------------
#

def muls(a, b):
    return a * b

new_command("*", muls,  [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 200, infix = 1, short="arithmetic multiplication",
            doc="""
Arithmetic multiplication.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="843")

#
# -------------------- / --------------------
#

def div(a, b):
    if b == 0:
        raise CliError, "Division by zero"
    return a / b

new_command("/", div,   [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 200, infix = 1, short="arithmetic division",
            doc="""
Arithmetic division.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="859")

#
# -------------------- & --------------------
#

def and_cmd(a, b):
    return a & b

new_command("&", and_cmd, [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 80, infix = 1, group_short = "various bitwise operators",
            short="bitwise AND operation", doc = """
Bitwise AND operation.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="873")


#
# -------------------- | --------------------
#

def or_cmd(a, b):
    return a | b

new_command("|", or_cmd, [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 60, infix = 1, short="bitwise OR operation",
            doc="""
Bitwise OR operation
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="888")

#
# -------------------- ^ --------------------
#

def xor_cmd(a, b):
    return a ^ b

new_command("^", xor_cmd, [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 70, infix = 1, short="bitwise XOR operation",
            doc="""
Bitwise XOR operation.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="902")

#
# -------------------- >> --------------------
#

def shr_cmd(a, b):
    if b < 0:
        return a << -b
    return a >> b

new_command(">>", shr_cmd, [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 100, infix = 1, short="bitwise right shift",
            doc="""
Bitwise right shift.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="918")

#
# -------------------- << --------------------
#

def shl_cmd(a, b):
    if b < 0:
        return a >> -b
    return a << b

new_command("<<", shl_cmd, [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 100, infix = 1, short="bitwise left shift",
            doc="""
Bitwise left shift.            
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="934")


#
# -------------------- ~ --------------------
#

def not_cmd(a):
    return ~a

new_command("~", not_cmd, [arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 250, check_args = 0, short="bitwise not",
            doc="""
Bitwise not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="949")

#
# -------------------- pow --------------------
#

def pow_cmd(a, b):
    if b >= 0:
        return a ** b
    else:
        raise CliError, "illegal exponent"

new_command("pow", pow_cmd, [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 500, infix = 1, short="power of", doc="""
Return the <arg>arg1</arg> to the power of <arg>arg2</arg>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="966")

#
# -------------------- python --------------------
#

def python_cmd(str):
    try:
        ret = eval(str, __main__.__dict__)
        if type(ret) == type(conf.sim):
            return ret.name
        else:
            return ret
    except SyntaxError:
        try:
            exec str in __main__.__dict__
            return
        except Exception, msg:
            pass
    except Exception, msg:
        pass
    raise CliError, "Error in Python expression: %s" % msg

new_command("python", python_cmd, [arg(str_t, "exp")],
            type = ["Command-Line Interface", "Python"],
            pri = 800, short="evaluate an expression in python",            
            see_also = ['@', 'run-python-file'],
            doc = """
<i>exp</i> will be evaluated in the Python environment and the result
returned to the frontend. This can also be done by enclosing the
Python code within backquotes (`); e.g., <cmd>print -x
`SIM_step_count(SIM_current_processor())`</cmd>.

Both expressions and statements can be run, but for statements the
<cmd>@</cmd> command can be used instead.

<cmd>run-python-file</cmd> uses Simics's Search Path and path markers
(%simics%, %script%) to find the script to run. Refer to Simics User Guide (CLI
chapter) for more information.

""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="993")

#
# -------------------- command-list --------------------
#

def command_list_cmd(name):
    format_commands_as_html(SIM_native_path(name))

new_command("command-list", command_list_cmd,
            [arg(filename_t(), "file")],
            type = ["Help"],
            short="generate html document describing commands",            
            doc = """
Produces a quick reference list of Simics commands in HTML. Note that
Simics commands can be added at runtime, and any particular dynamic
usage will be different from printed manuals. <i>file</i> is the file
to write to.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1019")

def api_help_cmd(str):
    try:
        doc = api_help[str]
        print "Help on API keyword \"%s\":\n" % str
        print_wrap_code(doc, terminal_width() - 1)
        return
    except KeyError, msg:
        pass

    l = []
    for key in api_help.keys():
        if key.find(str) >= 0:
            l.append(key)

    if not l:
        print "No API keyword matching \"%s\" found." % str
        return

    if len(l) == 1:
        return api_help_cmd(l[0])

    l.sort()
    print "The following API keywords contain the substring \"%s\":\n" % str
    print_columns([Just_Left], l, has_title = 0, wrap_space = "  ")
    
def api_help_expander(comp):
    l = []
    for key in api_help.keys():
        if key[:len(comp)] == comp:
            l.append(key)

    return get_completions(comp, l)

new_command("api-help", api_help_cmd,
            [ arg(str_t, "topic", expander = api_help_expander) ],
            short = "get API help",
            type = ["Help"],
            see_also = ["api-apropos", "apropos", "help"],
            doc = """
Prints the declaration of API declarations matching <i>topic</i>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1063")

def api_apropos_cmd(str):
    l = []
    for key in api_help.keys():
        if key.find(str) >= 0 or api_help[key].find(str) >= 0:
            l.append(key)

    if not l:
        print "The string \"%s\" cannot be found in any API documentation." % str
        return

    if len(l) == 1:
        plural = "y"
    else:
        plural = "ies"

    l.sort()
    if str:
        print "The string \"%s\" can be found in the following API help entr%s:\n" % (str, plural)
    else:
        print "The following API help entries exist:\n"
    print_columns([Just_Left], l, has_title = 0, wrap_space = "  ")
    
new_command("api-apropos", api_apropos_cmd,
            [ arg(str_t, "search-string") ],
            short = "search API help",
            type = ["Help"],
            see_also = ["api-help", "apropos", "help"],
            doc = """
Search the API documentation for the string <i>search-string</i>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1094")



#
# -------------------- hex --------------------
#

def int2base(base, value):
    chars = "0123456789abcdef"
    str = ""
    while value > 0:
        str = chars[int(value % base)] + str 
        value = value / base

    if not str:
        str = "0"

    return str

def hex_cmd(value):
    return number_str(value, 16)

new_command("hex", hex_cmd,
            [arg(int_t, "value")],
            alias = "",
            type = ["Command-Line Interface", "Output"],
            short = "display integer in hexadecimal notation",
            see_also = ["print"],
            doc = """
Returns the parameter as a string in hexadecimal notation. This is similar to <b>print</b> -x <i>value</i>.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1124")

#
# -------------------- output-radix --------------------
#
def output_radix_cmd(rad, group):
    if rad == 0 and group < 0:
        group = get_output_group()
        print "The current output-radix is %d." % get_output_radix()
        if group:
            print "Output is grouped in units of %d digits." % group
        return

    if rad != 0 and rad != 2 and rad != 8 and rad != 10 and rad != 16:
        raise CliError, "The radix must be either 2, 8, 10, or 16."

    if group < 0:
        group = get_output_group(rad)

    if rad == 0:
        rad = get_output_radix()

    try:
        set_output_radix(rad, group)
    except ValueError, msg:
        print msg

new_command("output-radix", output_radix_cmd,
            [ arg(int_t, "base", "?", 0),
              arg(int_t, "group", "?", -1) ],
            type = ["Command-Line Interface", "Output"],
            short = "change the default output radix",
            see_also = ["digit-grouping", "print"],
            doc = """
Changes or displays the default output radix for numbers. It can be
set to 2 for binary, 8 for octal, 10 for decimal, or 16 for
hexadecimal output.

If <var>group</var> is non-zero, numbers will be grouped in groups of
<var>group</var> digits, separated by underscores (<tt>_</tt>).

Currently, this only affects the output of the <cmd>print</cmd> command,
and how return values of commands are displayed.

Without arguments, the current setting will be shown.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1158")

#
# -------------------- digit-grouping --------------------
#
def digit_grouping_cmd(rad, group):
    if rad != 2 and rad != 8 and rad != 10 and rad != 16:
        raise CliError, "The radix must be either 2, 8, 10, or 16."
    if group < 0:
        group = get_output_group(rad)
        if group == 0:
            print "Numbers in radix %d are not grouped." % rad
        else:
            print ("Numbers in radix %d are grouped in groups of %d digits."
                   % (rad, group))
        return

    try:
        set_output_radix(rad, group, 0)
    except ValueError, msg:
        print msg

new_command("digit-grouping", digit_grouping_cmd,
            [ arg(int_t, "base"),
              arg(int_t, "digits", "?", -1) ],
            type = ["Command-Line Interface", "Output"],
            short = "set output formatting for numbers",
            see_also = ["output-radix", "print"],
            doc = """
Changes or displays how numbers are formatted for a given radix.
This will separate groups of <arg>digits</arg> digits by an underscore when
they are formatted for output. Separate grouping is maintained for each radix.
If <arg>digits</arg> is zero, no separators are printed for that radix.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1198")

#
# -------------------- print --------------------
#
def print_cmd(f, value, size):
    x = b = o = s = d = 0
    if f[2] == "-x": x = f[1]
    if f[2] == "-o": o = f[1]
    if f[2] == "-b": b = f[1]
    if f[2] == "-s": s = f[1]
    if f[2] == "-d": d = f[1]

    if size == 0:
        size = 64
        had_size = 0
    else:
        had_size = 1
        
    if size not in [8, 16, 32, 64, 128]:
        print "Size must be 8, 16, 32, 64, or 128" 
        return

    if value < 0:
        if value < -(1 << size):
            print "value truncated to", size, "bits."
        value = ((1 << size) + value) & ((1 << size) - 1)
        if not had_size:
            s = 1
    elif value >= (1 << size):
        value = value & ((1 << size) - 1)
        print "value truncated to", size, "bits."

    if x:
        base = 16
    elif d:
        base = 10
    elif o:
        base = 8
    elif b:
        base = 2
    else:
        base = -1
        if s and value >= (1 << (size - 1)):
            value -= 1 << size

    print number_str(value, base)

new_command("print", print_cmd,
            [arg((flag_t,flag_t,flag_t,flag_t,flag_t), ("-x","-o","-b","-s","-d"), "?", (flag_t, 0, "-x")),
             arg(int_t, "value"), arg(int_t, "size", "?", 0)],
            alias = "p",
            repeat = print_cmd,
            pri = -100, #set pri to lower than 0, makes cli evaluate all common commands first
            type = ["Command-Line Interface", "Output"],
            short = "display integer in various bases",
            see_also = ["output-radix"],
            doc = """
Prints <arg>value</arg> in hexadecimal (<arg>-x</arg>), decimal
(<arg>-d</arg>), octal (<arg>-o</arg>), or binary (<arg>-b</arg>)
notation. Default is to use the notation specified by the
<cmd>output-radix</cmd> command.

Use <arg>-s</arg> to convert the value to signed
integers. <arg>size</arg> is the bit width to use. E.g., <cmd>print -x
257 8</cmd> will print 0x1. Valid sizes are 8, 16, 32, 64, and 128
bits. Default size is 64.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1257")


#
# -------------------- echo --------------------
#

def echo_cmd(poly):
    if poly[0] == str_t:
        print poly[1]
    elif poly[0] == float_t:
        print poly[1]
    else:
        print number_str(poly[1])
        
new_command("echo", echo_cmd,
            [arg((int_t, float_t, str_t), ("integer", "float", "string"), "?", (str_t, ""))],
            type = ["Command-Line Interface", "Output"],
            short = "echo a value to screen",
            doc = """
Prints the string, integer, or float. Useful for annotating test scripts.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1291")

#
# -------------------- date --------------------
#

def date_cmd():
    import time
    print time.ctime(time.time())

new_command("date", date_cmd,
            [],
            type = ["Command-Line Interface"],
            short = "host time and date",
            doc = """ 
Prints the current date and time, in the form <tt>Fri Nov  2 12:00:36 2001</tt>.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1306")

#
# -------------------- timer-start --------------------
#

timer_start = 0
timer_stop = 0

def timer_start_cmd():
    global timer_start
    print "Timing of Simics started"
    timer_start = time.clock()

new_command("timer-start", timer_start_cmd,
            [], # timer-start
            type  = "internal commands",
            short = "start user timing",
            see_also = ['timer-stop', 'timer-query'],
            doc = """
Start timing of Simics (user time).""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1325")

#
# -------------------- timer-stop --------------------
#

def timer_stop_cmd():
    global timer_start, timer_stop
    timer_stop = (time.clock() - timer_start)
    print "Timing of Simics stopped"

new_command("timer-stop", timer_stop_cmd,
            [],
            type  = "internal commands",
            short = "end user timing",
            see_also = ['timer-start', 'timer-query'],
            doc = """
End timing of Simics (user time).""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1342")

#
# -------------------- timer-query --------------------
#

def timer_query_cmd():
    global timer_stop
    print "User time (s): %.2f" % timer_stop


new_command("timer-query", timer_query_cmd,
            [],
            type  = "internal commands",
            short = "query user timing",
            see_also = ['timer-start', 'timer-stop'],
            doc = """
Query timing of Simics (user time).""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1359")

#
# -------------------- ls --------------------
#

def ls_cmd():
    l = os.listdir(os.getcwd())
    l.sort()
    print_columns([ Just_Left ], l, has_title = 0, wrap_space = "  ")

new_command("ls", ls_cmd,
            [],
            type = ["Command-Line Interface", "Files and Directories"],
            short = "list files",
            see_also = ["cd", "pwd"],
            doc = """
List files in working directory of Simics.
Works like <tt>ls</tt> in a Unix shell, but does not take any parameters.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1376")

#
# -------------------- cd --------------------
#

def cd_cmd(path):
    try:
        os.chdir(SIM_native_path(path))
    except OSError, msg:
        print msg
    
new_command("cd", cd_cmd,
            [arg(filename_t(dirs=1,exist=1), "path")],
            type = ["Command-Line Interface", "Files and Directories"],
            short = "change working directory",
            see_also = ["ls", "pwd"],
            doc = """
Change working directory of Simics.  Works as if you had done 'cd' at the
shell. Converts <i>param</i> to host native form first (see
<i>native-path</i>).
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1395")


#
# -------------- pushd/popd/dirs --------------
#

_dir_stack = [ ]

def _print_dir_stack():
    print os.getcwd(),
    for d in _dir_stack:
        print d,
    print

def pushd_cmd(no_cd, path):
    global _dir_stack

    if not path and no_cd:
        return
        
    if not path:
        if len(_dir_stack) < 1:
            print "No other directory available on the directory stack."
            return
        dir = _dir_stack[0]
        _dir_stack[0] = os.getcwd()
        
        try:
            os.chdir(SIM_native_path(dir))
        except OSError, msg:
            print msg
            _dir_stack = _dir_stack[1:]
            return
        return

    old_dir = os.getcwd()
    
    if not no_cd:
        try:
            os.chdir(SIM_native_path(path))
        except OSError, msg:
            print msg
            return
    _dir_stack =  [ old_dir ] + _dir_stack
    if not path:
        _print_dir_stack()
        
new_command("pushd", pushd_cmd,
            [arg(flag_t, "-n"),
             arg(filename_t(dirs = 1, exist = 1), "path", "?", 0)],
            type = ["Command-Line Interface", "Files and Directories"],
            short = "push directory on directory stack",
            see_also = ["dirs", "popd"],
            doc = """
Pushes the directory <i>path</i> on top of the directory stack, or
exchanges the topmost two directories on the stack. If <tt>-n</tt> is
given, only change the contents of the stack, but do not change
current working directory.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1452")

def popd_cmd(no_cd):
    global _dir_stack
    
    if len(_dir_stack) < 1:
        print "The directory stack is empty."
        return

    dir = _dir_stack[0]
    if not no_cd:
        try:
            os.chdir(SIM_native_path(dir))
        except OSError, msg:
            print msg
            return
    _dir_stack = _dir_stack[1:]
    if no_cd:
        _print_dir_stack()
        
new_command("popd", popd_cmd,
            [arg(flag_t, "-n")],
            type = ["Command-Line Interface", "Files and Directories"],
            short = "pop directory from directory stack",
            see_also = ["dirs", "pushd"],
            doc = """
Pops a directory off the directory stack and, unless the <tt>-n</tt>
option is specified, change current working directory to that
directory.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1483")

def dirs_cmd():
    _print_dir_stack()

new_command("dirs", dirs_cmd,
            [],
            type = ["Command-Line Interface", "Files and Directories"],
            short = "display directory stack",
            see_also = ["pushd", "popd"],
            doc = """
Shows the contents of the directory stack.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1497")


#
# -------------------- run-command-file --------------------
#

new_command("run-command-file", SIM_run_command_file,
            args = [arg(filename_t(exist = 1, simpath = 1), "file")],
            type = ["Command-Line Interface", "Files and Directories"],
            short = "execute a simics script",
            alias = "include",
            see_also = ["run-python-file", "add-directory"],
            doc = """
This command starts executing a Simics script. A Simics script is an
ordinary text file that contains Simics commands. One command on each
line. The syntax used is exactly the same as when commands are typed
at the Simics prompt. The # character is used as the start of a
comment and applies to the rest of the line.

Python code can also by executed by prefixing the line with
@. Multi-line Python statements can be used by leaving a blank line at
the end of the statement. Only the first line should have an @ in this
case.

Simics scripts usually ends with the suffix ".simics" but this is only a
convention. The suffix is ignored by Simics.

This is an example of a Simics script:

<tt>
# This is a Simics script<br/>
<br/>
break 0xffc000 # set a breakpoint<br/>
run<br/>
echo "breakpoint reached"<br/>
run-command-file another-script.simics<br/>
</tt>

Simics scripts can be executed directly
when Simics has started by using the -x command line option.

If a command fails or the user presses Control-C the Simics script is
interrupted and control returns to the Simics prompt.

<cmd>run-command-file</cmd> uses Simics's Search Path and path markers
(%simics%, %script%) to find the script to run. Refer to Simics User Guide (CLI
chapter) for more information.

""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1511")

#
# -------------------- list-haps --------------------
#

def hap_expander(str):
    try:
        hap_list = [ hap[0] for hap in conf.sim.hap_list ]
        return get_completions(str, hap_list)
    except:
        return []

def hap_list_cmd(name):
    haps = conf.sim.hap_list
    if not name:
        def f(x):
            return [ x[0] ]
        l = map(f, haps)
        print_columns([Just_Left], l, has_title = 0)
        return
    
    for hap in haps:
        if -1 != string.find(hap[0], name):
            pr(bold("\nNAME\n"))
            print "   %s" % hap[0]
            pr(bold("\nCALLBACK TYPE\n"))
            argnames = [ "callback_data", "trigger_obj" ]
            if hap[2] != None:
                argnames = argnames + hap[2]
            pr(hap_c_arguments("noc" + hap[1], argnames, terminal_width() - 5, 3))
            pr("\n")
            pr(bold("\nINDEX\n"))
            print "   %s" % iff(hap[3] == None, "no index", hap[3])
            pr(bold("\nINSTALLED HANDLERS\n"))
            print "   %s" % iff(hap[5], hap[5], "none")
            pr(bold("\nDESCRIPTION\n"))
            pr("   ")
            format_print(hap[4], 3, terminal_width())
            print

new_command("list-haps", hap_list_cmd,
            [arg(str_t, "substring", "?", "", expander = hap_expander)],
            alias="hl",
            type = ["Haps"],
            short="print list of haps",
            doc_items = [],
            doc  = """
Prints a description of all haps whose names contain <i>substring</i>. If the
name is omitted a list of all haps will be printed.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1594")

def find_function(funcs, addr):
    for fn, file, start, end in funcs:
        if start <= addr and addr < end:
            return fn
    return None

def hap_callback_list_cmd(name):
    if name:
        try:
            callbacks = [[name, conf.sim.hap_callbacks[name]]]
        except:
            print "No hap '%s'" % name
            return
    else:
        callbacks = []
        for hap in conf.sim.hap_list:
            cb = conf.sim.hap_callbacks[hap[0]]
            if len(cb):
                callbacks += [[hap[0], cb]]

    try:
        st = SIM_get_object("internal-symbols")
        funcs = st.functions
    except:
        funcs = None
    
    # todo: handle internals
    for hap in callbacks:
        for cb in hap[1]:
            if cb[4]:
                obj = cb[4].name
            else:
                obj = ""
            f = None
            if cb[5][0:2] == "0x" and funcs:
                f = find_function(funcs, string.atol(cb[5], 0))
                if f:
                    f = "(C) '%s()'" % f
            else:
                m = re.match("<function (.*) at 0x(.*)>", cb[5])
                if m:
                    f = "(Python) '%s()'" % m.group(1)
            minus_one = (1 << 64) - 1
            if cb[1] == minus_one and cb[2] == minus_one:
                range = '           '
            elif cb[1] != cb[2]:
                range = 'range %2d-%2d' % (cb[1], cb[2])
            else:
                range = ' index %3d  ' % cb[1]
            print "%-28s id %d %s  Sim: %s  Object: %s" % (
                hap[0], cb[0], range, iff(cb[3] & 1, "yes", "no"), obj)
            fstr = "Function : %-38s" % iff(f, f, cb[5][:68])
            dstr = "User data: %s" % cb[6][:68]
            print fstr,
            if len(fstr) + len(dstr) >= 80:
                print
            print dstr
            print

new_command("list-hap-callbacks", hap_callback_list_cmd,
            [arg(str_t, "hap", "?", "", expander = hap_expander)],
            type = ["Haps"],
            short="print list of hap callbacks",
            doc_items = [],
            doc  = """
Prints a list of all callbacks installed for <arg>hap</arg>, or
for all haps if the argument is omitted.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1663")


#
# -------------------- break-hap, trace-hap --------------------
#

class hap_tracker(tracker):
    def __init__(self, stop, cmd, short, doc, type, see_also = []):
        tracker.__init__(self, stop, cmd, "hap", hap_expander, short, doc,
                         group = type, see_also = see_also)
        self.map = {}
        self.catchall = 0

    def all_haps(self):
        return [self.resolve_target(name) for name in SIM_get_all_hap_types()]

    def show(self, hapname, obj, *args):
        print "got hap %s" % hapname

    def list(self):
        print "%s enabled for these haps:" % iff(self.stop, "breaking", "tracing")
        for hap in self.map.keys():
            print "  %s" % hap

    def resolve_target(self, hapname):
        # check that hap exists
        SIM_hap_get_number(hapname)
        return hapname

    def is_tracked(self, hap):
        return self.map.has_key(hap)

    def install_hap(self, hap):
        self.map[hap] = SIM_hap_add_callback(hap, self.callback, hap)

    def uninstall_hap(self, hap):
        SIM_hap_delete_callback_id(hap, self.map[hap])
        del self.map[hap]

    def track_all(self):
        # TODO: document why these haps aren't tracked when -all is given
        for hap in self.all_haps():
            if hap in ['Core_Hap_Callback_Installed',
                       'Core_Hap_Callback_Removed',
                       'Core_Screen_Resized',
                       'Core_Back_To_Front',
                       'Core_Continuation',
                       'Core_Simulation_Stopped'
                       'Python_Tab_Completion']:
                print 'Skipping %s' % hap
                continue
            if not self.is_tracked(hap):
                self.install_hap(hap)

    def track_none(self):
        for hap in self.map.keys():
            self.uninstall_hap(hap)

    def track_on(self, hap):
        if self.is_tracked(hap):
            return
        self.install_hap(hap)
        
    def track_off(self, hap):
        if self.is_tracked(hap):
            self.uninstall_hap(hap)


trace_hap_cmds = hap_tracker(0, "trace-hap",
                             short = "trace haps",
                             type = "inspect/change",
                             see_also = [ "break-hap", "list-haps" ],
                             doc = """
Enables and disables tracing of haps.  When this is enabled, every
time the specified hap is triggered a message is printed.

The <i>hap</i> parameter specifies the hap.

Instead of a hap, the <tt>-all</tt> flag may be given.  This will
enable or disable tracing of all haps.
""")

break_hap_cmds = hap_tracker(1, "break-hap",
                             short = "break on haps",
                             type = "breakpoint",
                             see_also = [ "trace-hap", "list-haps" ],
                             doc = """
Enables and disables breaking simulation on haps.  When this is
enabled, every time the specified hap is triggered a message is
printed and simulation is stopped.

The <i>hap</i> parameter specifies the hap.

Instead of a hap, the <tt>-all</tt> flag may be given.  This will
enable or disable breaking on all haps.
""")

#
# -------------------- break-on-log-message --------------------
#

def log_hap_callback(udata, trigger, type, message):
    hid, filt_obj, substring, filt_type = udata
    if substring in message and (filt_type is None or filt_type == type) \
           and (not filt_obj or filt_obj == trigger):
        cpu = SIM_current_processor()
        step = SIM_step_count(cpu)
        SIM_hap_delete_callback_id("Core_Log_Message", hid)
        SIM_break_simulation("Log message matched at step %s:%d."%
                             (cpu.name, step))

log_types = {
    'info':      Sim_Log_Info,
    'error':     Sim_Log_Error,
    'spec-viol': Sim_Log_Spec_Violation,
    'tgt-error': Sim_Log_Target_Error,
    'unimpl':    Sim_Log_Unimplemented,
    'undefined': Sim_Log_Undefined,
}

def break_log_cmd(substring, obj, type):
    udata = [ 0, obj, substring, type ]
    udata[0] = SIM_hap_add_callback_obj("Core_Log_Message", obj, 0,
                                        log_hap_callback, udata)

new_command("break-log", break_log_cmd,
            [arg(str_t, "substring", "?", ""),
             arg(obj_t("log object", kind = "log_object"), "object", "?"),
             arg(string_set_t(log_types), "type", "?")],
            short = "break on log message",
            doc = """
Break on log message. With no arguments the simulation will stop when the
next log message is printed. By specifying <arg>object</arg>, <arg>type</arg>,
and/or <arg>substring</arg> it will stop on the next log message matching these
conditions. The break is triggered once only, to break again you need to run
the command again.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1796")

#
# -------------------- pwd --------------------
#

def pwd_cmd():
    return os.getcwd()

new_command("pwd", pwd_cmd,
            [],
            type = ["Command-Line Interface", "Files and Directories"],
            short = "print working directory",
            see_also = ["cd", "ls"],
            doc = """
Print the working directory of Simics. Similar to the shell command 'pwd'
(print working directory).""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1815")

#
# -------------------- set-simics-id --------------------
#

def set_simics_id_cmd(id):
    pass

new_command("set-simics-id", set_simics_id_cmd,
            [arg(int_t, "id")],
            short = "set the global Simics ID number",
            deprecated = "the new central system",
            doc = """
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1831")

#
# -------------------- quit --------------------
#

def quit_cmd(code):
    SIM_quit(code)

new_command("quit", quit_cmd,
            [arg(sint32_t, "status", "?", 0)],
            alias = ["q", "exit"],
            type = ["Command-Line Interface"],
            short = "quit from Simics",
            doc = """
Stop Simics gracefully. The optional argument is the exit status of Simics.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1845")

#
# -------------------- expect --------------------
#

def expect_cmd(i1, i2, v):
    if v:
        print "Value is " + `i1[1]` +" expecting " + `i2[1]`
    if i1[1] != i2[1]:
        print "*** Values differ in expect command:",
        if isinstance(i1[1], (int, long)):
            print number_str(i1[1]),
        else:
            print i1[1],
        if isinstance(i2[1], (int, long)):
            print number_str(i2[1])
        else:
            print i2[1]
        SIM_quit(1)
        
new_command("expect", expect_cmd,
            [arg((int_t, str_t), ("i1", "s1")),
             arg((int_t, str_t), ("i2", "s2")),
             arg(flag_t, "-v")],
            type = ["Test"],
            short = "fail if not equal",
            doc = """
            
If values <arg>i1</arg> and <arg>i2</arg> are not equal the simulator will
print them and exit with error <fun>exit(1)</fun>. <arg>-v</arg> prints the two
values before comparing them.

This can be useful when writing scripts that want to assert a state in
the simulator. Note that it only works with integer and string arguments.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1872")

#
# -------------------- pid --------------------
#

def pid_cmd():
    print os.getpid()

new_command("pid", pid_cmd,
            [],
            type = ["Command-Line Interface"],
            short = "print pid of Simics process",
            doc = """
Outputs the process identity of the Simics process itself, useful for
various things (such as attaching a remote debugger).""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1894")

#
# -------------------- readme --------------------
#

def readme_cmd():
    print SIM_readme()

new_command("readme", readme_cmd,
            [],
            type = ["Help"],
            short = "print information about Simics",
            doc = """
Prints various useful information (README) about Simics.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1909")

#
# -------------------- license --------------------
#

def license_cmd():
    SIM_license()

new_command("license", license_cmd,
            [],
            type = ["Help"],
            short = "print simics license",
            doc = """
Prints the LICENSE that applies to this copy of Simics.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1923")

#
# -------------------- copyright --------------------
#

def copyright_cmd():
    SIM_copyright()

new_command("copyright", copyright_cmd,
            [],
            type = ["Help"],
            short = "print full Simics copyright information",
            doc = """
Prints the complete copyright information that applies to this copy of Simics.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1937")

#
# -------------------- version --------------------
#

def version_cmd(verbose):
    if verbose:
        print "%s (%s)\n" % (SIM_version(), SIM_snapshot_date())
        print "build-id:     %d" % conf.sim.version
        print SIM_version_sub()
    else:
        print SIM_version()
        print
        
new_command("version", version_cmd,
            [arg(flag_t, "-v")],
            type = ["Help"],
            short = "display Simics version",
            doc = """
Prints the Simics version. With the <tt>-v</tt> flag, compiler version
and compile dates are printed as well.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1957");

#
# -------------------- quiet --------------------
#

quiet_mode = 0

def quiet_cmd(mode):
    global quiet_mode

    if mode not in [-1,0,1]:
        print "Illegal mode"
        return

    if mode == -1:
        quiet_mode = 1 - quiet_mode
    else:
        quiet_mode = mode
    
    SIM_set_quiet(quiet_mode)
    if quiet_mode:
        print "[simics] Switching on quiet mode."
    else:
        print "[simics] Switching off quiet mode."

new_command("quiet", quiet_cmd,
            [arg(int_t, "mode", "?", -1)],
            type  = "internal commands",
            short = "toggle quiet mode",
            doc = """
Switches quiet mode to given value.
Sets Simics to 'quiet' mode if the value is 1, or turns off
quiet mode if the value is 0, or toggles if the value is -1.
See also the 'verbose' command. Default is to toggle.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="1990")

#
# -------------------- verbose --------------------
#

verbose_mode = 0

def verbose_cmd(mode):
    global verbose_mode

    if mode not in [-1,0,1]:
        print "Illegal mode"
        return

    if mode == -1:
        verbose_mode = 1 - verbose_mode
    else:
        verbose_mode = mode
    
    SIM_set_verbose(verbose_mode)
    if verbose_mode:
        print "[simics] Switching on verbose mode."
    else:
        print "[simics] Switching off verbose mode."

new_command("verbose", verbose_cmd,
            [arg(int_t, "mode", "?", -1)],
            type  = "internal commands",
            short = "toggle verbose mode",
            doc = """
Switches verbose mode to given value.
Sets Simics to 'verbose' mode if the value is 1, or turns off
verbose mode if the value is 0, or toggles if the value is -1.
See also the 'quiet' command. Default is to toggle.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2024")

#
# -------------------- = --------------------
#

def assignment_command(name, value):
    if name[0] == '%':
        if not value[0] == int_t:
            print "Value is not an integer."
            SIM_command_has_problem()
            return
        (cpu, _) = get_cpu()
        return obj_write_reg_cmd(cpu, name[1:], cast(uint64_t, value[1]))
    elif name.startswith('$$'):
        name = name[2:]
        local = 1
    elif name[0] == '$':
        name = name[1:]
        local = 0
    else:
        local = 0
        print ('Deprecation warning: variable assignment without variable '
               'prefix $.')
        if conf.prefs.fail_on_warnings:
            SIM_quit(1)
    get_current_locals().set_variable_value(name, value[1], local)
    # do not return anything (avoid execution of string assignments)

new_command("=", assignment_command,
            [arg(str_t, doc = "name"),
             arg((int_t, str_t, float_t),
                 ("ival", "sval", "fval"), doc = "value")],
            type = ["Command-Line Interface"],
            short = "set an environment variable",
            pri = -100,
            infix = 1,
            doc = """
Set a Simics environment variable to an integer or string value.
Or assigns a value to a processor register.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2061")


#
# -------------------- [ --------------------
#

def array_command(name, idx, rw, value):
    if name[0] != '$':
        print "Indexing only supported for variables"
        SIM_command_has_problem()
        return
    if name.startswith('$$'):
        name = name[2:]
        local = 1
    else:
        name = name[1:]
        local = 0
    space = get_current_locals()
    if rw[2] == '-r':
        try:
            return getattr(space, name)[idx]
        except Exception, msg:
            return
    else:
        try:
            space.set_variable_value_idx(name, value[1], local, idx)
        except:
            print "Failed setting variable."
            SIM_command_has_problem()
            return

new_command("[", array_command,
            [arg(str_t, "variable"),
             arg(int_t, "idx"),
             arg((flag_t, flag_t), ('-r', '-w')),
             arg((int_t, str_t), ('ival', 'sval'), doc = 'value')],
            type = ["Command-Line Interface"],
            short = "",
            pri = 750,
            infix = 1,
            doc = """
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2103")


#
# -------------------- unset --------------------
#

def unset_command(all, names):
    if all:
        rlist = [x for x in get_current_locals().get_all_variables().keys()
                 if x not in names]
    else:
        rlist = names
    for n in rlist:
        try:
            get_current_locals().remove_variable(n)
        except:
            print 'Unset failed for $%s.' % n

new_command("unset", unset_command,
            [arg(flag_t, "-a"),
             arg(str_t, "variables", "*")],
            type = ["Command-Line Interface"],
            short = "remove a environment variable",
            doc = """
Removes (unsets) a Simics environment variable. The <arg>-a</arg> flag causes
all variables to be removed, <em>except</em> the ones specified as
<arg>variables</arg>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2132")

#
# -------------------- += --------------------
#

def inc_environment_variable(name, value):
    if name[0] == '%':
        if not value[0] == int_t:
            print "Value is not an integer."
            SIM_command_has_problem()
            return
        (cpu, _) = get_cpu()
        value = cast(uint64_t, obj_read_reg_cmd(cpu, name[1:]) + value[1])
        return obj_write_reg_cmd(cpu, name[1:], value)
    elif name[0] == '$':
        name = name[1:]
    else:
        print 'Deprecation warning: variable assignment without variable prefix $.'
        if conf.prefs.fail_on_warnings:
            SIM_quit(1)

    space = get_current_locals()
    if space.get_all_variables().has_key(name):
        old = getattr(space, name)
        if isinstance(old, str):
            old = (str_t, old)
        else:
            old = (int_t, old)
    else:
        if value[0] == int_t:
            old = (value[0], 0)
        else:
            old = (str_t, '')
    setattr(space, name, plus(old, value))
    return getattr(space, name)

new_command("+=", inc_environment_variable,
            [arg(str_t, doc = "name"),
             arg((int_t, str_t), ("ival", "sval"), doc = "value")],
            type = ["Command-Line Interface"],
            short = "set an environment variable",
            pri = -100,
            infix = 1,
            doc = """
Add a string or integer to a Simics environment variable, or an integer
value to a register.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2178")

#
# -------------------- -= --------------------
#

def dec_environment_variable(name, value):
    if name[0] == '%':
        (cpu, _) = get_cpu()
        value = cast(uint64_t, obj_read_reg_cmd(cpu, name[1:]) - value)
        return obj_write_reg_cmd(cpu, name[1:], value)
                                 
    elif name[0] == '$':
        name = name[1:]
    else:
        print 'Deprecation warning: variable assignment without variable prefix $.'
        if conf.prefs.fail_on_warnings:
            SIM_quit(1)

    space = get_current_locals()
    if space.get_all_variables().has_key(name):
        old = getattr(space, name)
        if not isinstance(old, (int, long)):
            print "Variable is not an integer."
            SIM_command_has_problem()
            return
    else:
        old = 0
    setattr(space, name, minus(old, value))
    return getattr(space, name)

new_command("-=", dec_environment_variable,
            [arg(str_t, doc = "name"),
             arg(int_t, "value")],
            type = ["Command-Line Interface"],
            short = "set an environment variable",
            pri = -100,
            infix = 1,
            doc = """
Subtract an integer from a Simics environment variable, or from a
register.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2218")

#
# -------------------- $ --------------------
#

def environment_var_expander(comp):
    return get_completions(comp,
                           get_current_locals().get_all_variables().keys())

def get_environment_variable(name):
    return getattr(get_current_locals(), name)

new_command("$", get_environment_variable,
            [arg(str_t, "name", expander = environment_var_expander)],
            type = ["Command-Line Interface"],
            short = "get the value of an environment variable",
            pri = 2000,
            check_args = 0,
            doc = """
Gets the value of a Simics environment variable, like in <tt>print $var</tt>.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2240")

#
# -------------------- list-vars --------------------
#

def list_vars_cmd():
    l = []
    m = 0
    d = get_current_locals().get_all_variables()
    for k in d.keys():
        l.append((k,d[k]))
        m = max(m, len(k))

    l.sort()
    for v in l:
        print "%-*s =" % (m, v[0]), v[1]

new_command("list-vars", list_vars_cmd,
            [],
            type = ["Command-Line Interface"],
            short = "list environment variables",
            doc = """            

Lists all Simics environment variables and their current
values. Environment variables can be used to store temporary
values. To set a variable, write <tt>variable = value</tt> at the
Simics prompt. The value can be of type integer, string, or float. To
access a variable, prefix the name with a <tt>$</tt>, e.g.,
<tt>$variable</tt>. A variable can be put wherever an expression can be
used. For example:

<tt>simics> tmp = %pc + 4</tt><br/>
<tt>simics> count = 10</tt><br/>
<tt>simics> disassemble $tmp $count</tt><br/>

They can also be accessed from Python by using the name space simenv:

<tt>simics> $foo = 1 + 4 * 4</tt><br/>
<tt>simics> @print simenv.foo</tt><br/>
<tt>17</tt><br/>
<tt>simics> @simenv.bar = "hello"</tt><br/>
<tt>simics> echo $bar</tt><br/>
<tt>hello</tt>
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2265")


#
# -------------------- list-namespaces --------------------
#

def list_namespaces_cmd(name_sort):
    l = []
    i = []
    m = 0

    # Fins all interfaces used as command namespaces
    iface_namespaces = []
    for cmd in simics_commands():
        iface = cmd["namespace"]
        if iface:
            try:
                if SIM_get_class(iface) == iface:
                    iface = None
            except SimExc_General:
                pass
            if iface and not iface in iface_namespaces:
                iface_namespaces.append(iface)

    for o in SIM_get_all_objects():
        namespace = o.name
        classname = o.classname
        l = l + [ [ "<" + classname + ">", namespace ] ]

        for iface in iface_namespaces:
            if instance_of(o, iface):
                i = i + [ [ "<" + iface + ">", namespace ] ]

    if name_sort:
        l.sort(lambda a, b: cmp(a[1], b[1]))
        i.sort(lambda a, b: cmp(a[1], b[1]))
    else:
        l.sort()
        i.sort()

    print_columns([ Just_Left, Just_Left ],
                  [ [ "Class", "Namespace (Object)" ] ] + l)

    print ""
    
    print_columns([ Just_Left, Just_Left ],
                  [ [ "Interface", "Namespace (Object)" ] ] + i)


new_command("list-namespaces", list_namespaces_cmd,
            [arg(flag_t, "-n")],
            type = ["Command-Line Interface", "Help"],
            short = "list all namespaces",
            see_also = ['list-objects'],
            doc = """
Lists all namespaces (objects) and which classes or interfaces they
belong to. A namespace is the same as a configuration object. Many
objects implement commands local to them. These commands are invoked
by giving the object name followed by a period and then the local
command name; e.g., <cmd>rec0.playback-start</cmd>.

If the <arg>-n</arg> flag is given, the output will be sorted on the
object name instead of the class name, which is the default.

Some objects also implement command interfaces. A command interface is
a collection of commands that can be used by an object implementing
this interface. For example, breakpoint is an interface that is
implemented by objects of the <class>memory-space</class> class. This
allows one to write <cmd>phys_mem0.break 0xffc00</cmd> to set a
breakpoint in the memory interface.

Objects implementing command interfaces are listed in the second half
of output from this command.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2341")


#
# -------------------- list-objects --------------------
#

def class_or_iface_expander(string):
    return get_completions(string, sim.classes.keys() + sim.interfaces.keys());

def print_object_list(type, comp, objs, name_sort):
    l = [ ["<" + o.classname + ">", o.name]
          for o in objs
          if not type or instance_of(o, type) ]

    if name_sort:
        l.sort(lambda a, b: cmp(a[1], b[1]))
    else:
        l.sort()

    print_columns([ Just_Left, Just_Left ],
                  [ [ iff(comp, "Component Class", "Class"),
                      "Object" ] ] + l)
    print ""

def list_objects_cmd(type, name_sort, all):
    if type and type not in sim.classes and type not in sim.interfaces:
        print "No such class or interface: '%s'" % type
        return

    if all:
        print_object_list(type, False, sim.objects.values() , name_sort)
    else:
        comp_objs = sim.interfaces['component'].objects.values()
        print_object_list(type, True, comp_objs, name_sort)
        print_object_list(type, False,
                          (o for o in sim.objects.values()
                           if o not in comp_objs),
                          name_sort)

new_command("list-objects", list_objects_cmd,
            [arg(str_t, "type", "?", "", expander = class_or_iface_expander),
             arg(flag_t, "-n"),
             arg(flag_t, "-a")],
            type = ["Configuration"],
            short = "list all objects",
            see_also = ["list-namespaces"],
            doc = """
Lists all configuration objects and the class they belong to.

You can specify a class or interface name as <arg>type</arg>. Only objects of
that class or implementing that interface will then be listed.

The objects are sorted by class name by default. Use the <arg>-n</arg> flag to
sort them by object name instead.

Component objects are printed, first, and then all other objects. To mix all
objects in the same list, use the <arg>-a</arg> flag.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2404")

#
# -------------------- load-module --------------------
#

def module_expander(string):
    nonloaded = []
    def callback(name, file, usr_ver, attrs, nonloaded=nonloaded):
        if "LOADED" not in attrs:
            nonloaded.append(name)
    SIM_for_all_modules(callback)
    return get_completions(string, nonloaded)

def import_module_commands(module, glob):
    if not VT_module_has_commands(module, glob):
        return
    scriptmod = sub("\+", "__", sub("-", "_", module))
    modname = "mod_%s_%scommands" % (scriptmod, iff(glob, "g", ""))
    try:
        moduleobj = __import__(modname)
    except Exception, msg:
        print "Problem importing %scommands for %s: %s" % (
            iff(glob, "global ", ""), module, msg)
        SIM_command_has_problem()
        return
    if not glob and hasattr(moduleobj, 'class_funcs'):
        class_funcs.update(moduleobj.class_funcs)

def module_loaded_callback(dummy, obj, module):
    import_module_commands(module, 0)

def check_for_gcommands():
    for name in [x[0] for x in SIM_get_all_modules()]:
        VT_push_current_loading_module(name);
        import_module_commands(name, 1)
        VT_pop_current_loading_module()

# put it in a try to get documentation working
try:
    SIM_hap_add_callback("Core_Module_Loaded", module_loaded_callback, 0)
except NameError:
    pass

def load_module_cmd(module):
    assert_not_running()

    try:
        SIM_load_module(module)
    except Exception, msg:
        print "Error loading module '%s': %s" % (module, msg)
        SIM_command_has_problem();

new_command("load-module", load_module_cmd,
            [arg(str_t, "module", expander = module_expander)],
            type = ["Configuration", "Modules"],
            see_also = ["list-modules", "list-failed-modules",
                        "module-list-refresh", "unload-module",
                        "add-module-directory"],
            short = "load module into Simics",
            doc = """
Load a module (Simics extension). Simics supports dynamically loadable
modules. Read the <cite>Simics Users Guide</cite> for more info on how
to write modules.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2475")

#
# -------------------- unload-module --------------------
#

def unload_module_cmd(module):
    assert_not_running()

    try:
        SIM_unload_module(module)
        print "Module", module, "unloaded"
    except Exception, msg:
        print "Error unloading module %s: %s" % (module, msg)

new_command("unload-module", unload_module_cmd,
            [arg(str_t, "module")],
            alias = "",
            type = ["Configuration", "Modules"],
            short = "unload module",
            see_also = ["load-module"],
            doc = """
Unload a module (Simics extension). Note that not all modules can be unloaded.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2501")

def module_list_cmd(substr, loaded, verbose):
    mods = [x for x in SIM_get_all_modules() if x[0].find(substr) >= 0]
    if len(mods) == 0:
        print "No modules %sfound." % (
            iff(len(substr), 'matching pattern "%s" ' % substr, ''))
        return
    info = []
    for mod in mods:
        if loaded and not mod[2]:
            continue
        line = [mod[0],
                iff(mod[2], 'Loaded', ''),
                iff(mod[3] != conf.sim.version,
                    mod[3], ''),
                mod[4]]
        if verbose:
            line.append(mod[1])
        info.append(line)
    info.sort()
    title = ['Name', 'Status', 'Version', 'User Version']
    if verbose:
        title.append('Path')
    print_columns((Just_Left,) * len(title), [title] + info)

new_command("list-modules", module_list_cmd,
            [arg(str_t,"substr","?",""),
             arg(flag_t,"-l"),
             arg(flag_t,"-v")],
            alias = "module-list",
            type = ["Configuration", "Modules"],
            see_also = ['list-failed-modules', 'module-list-refresh',
                        'load-module', 'add-module-directory'],
            short = "list loadable modules",
            doc = """
Lists all modules that can be loaded into Simics. If the optional
<arg>substr</arg> argument is specified, only modules with a matching name will
be printed. Use <arg>-v</arg> to get more information on the modules, and
<arg>-l</arg> to only list loaded modules. The ABI version of modules is only
printed if it differs from the current Simics ABI.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2535")

#
# -------------------- list-failed-modules --------------------
#

def module_list_failed_cmd(substr, verbose):

    mods = [x for x in SIM_get_all_failed_modules() if x[0].find(substr) >= 0]
    if len(mods) == 0:
        print "No failed modules %sfound." % (
            iff(len(substr), 'matching pattern "%s" ' % substr, ''))
        return

    print ""
    print "Current ABI version: %d " % conf.sim.version,
    print "Lowest supported: %d" % conf.sim.version_compat
    print ""

    errors = []
    for mod in mods:
        if mod[3]:
            msg = mod[6] or 'unknown linker error'
        elif mod[4] and mod[4] < conf.sim.version_compat:
            msg = 'Unsupported Simics ABI version: %d' % mod[4]
        elif mod[2]:
            msg = 'Duplicated module'
        elif mod[6]:
            msg = mod[6]
        else:
            msg = 'Uknown failure'
        if verbose:
            errors.append([mod[0], msg, mod[1]])
        else:
            errors.append([mod[0], msg])
    errors.sort()
    title = ['Name', 'Error']
    if verbose:
        title.append('Path')
    print_columns((Just_Left,) * len(title), [title] + errors)

new_command("list-failed-modules", module_list_failed_cmd,
            [arg(str_t,"substr","?",""), arg(flag_t, "-v") ],
            alias = "module-list-failed",
            type = ["Configuration", "Modules"],
            see_also = ["list-modules", "module-list-refresh", "load-module",
                        "add-module-directory"],
            short = "list the modules that are not loadable",
            # Whenever you change the columns, make sure to update the
            # example in the programming guide.
            doc = """
Lists the modules (Simics extensions) that are not loadable,
optionally only those matching <arg>substr</arg>.

Similar to <cmd>list-modules</cmd> but shows modules that will not load into
Simics, and the reason why Simics refuses to load them (e.g., missing symbol,
wrong version, ...).

If the -v flag is specified, show verbose information, with the full path to
the module file and any library loader error message.

The <tt>MODULE</tt> column contains the name of the module or the filename of the
shared library file if the module name could not be established.

If the module has the same name as another module, an <tt>X</tt> will
be printed in the <tt>DUP</tt> column.

If the module could not be loaded since it was compiled or written for
a different version of Simics, the version it was built for will be
printed in the <tt>VERSION</tt> column.

The <tt>USR_VERS</tt> will contain the user version string, if provided.

The <tt>LINK</tt> column contains any linker error (cf. the <tt>dlerror(3)</tt>
manpage).

When the -v flag is provided, the <tt>PATH</tt> column will contain
linker information for the module.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2591")

#
# -------------------- module-list-refresh --------------------
#

def module_list_refresh_cmd():
    SIM_module_list_refresh()
    check_for_gcommands()

new_command("module-list-refresh", module_list_refresh_cmd,
            [], # module-list-refresh
            alias = "",
            type = ["Configuration", "Modules"],
            short = "create a new list of loadable modules",
            see_also = ["list-modules", "list-failed-modules", "load-module"],
            doc = """
Refresh (reload) the list of all Simics modules.<br/>
This command causes Simics to re-query all modules currently
not loaded. This can be used after changing or
adding a module that Simics, when started, considered as
non-loadable.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2638")


#
# -------------------- read-configuration --------------------
#

from update_config import update_configuration

def any_object_exists(set, prefix):
    for s in [x for x in set if x not in ['sim', 'python', 'prefs']]:
        try:
            SIM_get_object(prefix + s)
            return True
        except:
            pass
    return False

def py_SIM_read_configuration(file):
    set = VT_get_configuration(file)
    prefix = ''
    idx = 0

    # TODO: remove this check when bug #2389 (cannot create cpu once started)
    # has been fixed.
    if any_object_exists(set, prefix):
        print "Cannot read configuration, object names already used."
        SIM_command_has_problem()
        return

    while any_object_exists(set, prefix):
        prefix = 'machine_%d_' % idx
        idx += 1

    if prefix:
        print "Using object prefix '%s'" % prefix
        for s in set:
            set[s].name = prefix + set[s].name

    update_configuration(set)
    SIM_add_configuration(set, file)

def read_configuration_cmd(file):
    assert_not_running()
    
    try:
        py_SIM_read_configuration(file)
    except Exception, msg:
        SIM_command_has_problem()
        print msg
	print "Failed reading configuration"        

new_command("read-configuration", read_configuration_cmd,
            [arg(filename_t(simpath = 1), "file")],
            type  = ["Configuration"],
            short = "restore configuration",
            see_also = ["write-configuration"],
            doc = """
Read configuration from file. The configuration can be either a checkpoint or
an initial configuration. For information about how to create or modify
configurations, see the <cite>Simics User Guide</cite>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2701")

#
# -------------------- write-configuration --------------------
#

def write_configuration_cmd(file, z, u):
    assert_not_running()

    old_compressed_diff = SIM_get_class_attribute("image", "compressed_diff")
    compr = conf.prefs.compress_images
    if u:
        compr = 0
    if z:
        compr = 1
    SIM_set_class_attribute("image", "compressed_diff", compr)
    try:
        file = SIM_native_path(file)

        if os.path.exists(file):
            pr(("%s already exists. Overwriting checkpoints is not"
                + " supported.\n") % file)
            SIM_command_has_problem()
            return
        try:
            if VT_remote_control():
                print "Writing configuration to:", file

            if SIM_write_configuration_to_file(file):
                print "Failed to write configuration"
                SIM_command_has_problem()

            # If running from a client, the prompt does not always
            # function as "command is complete" indicator.
            if VT_remote_control():
                print "Finished writing configuration."

        except Exception, msg:
            print msg
            print "Failed writing configuration"
            SIM_command_has_problem()
    finally:
        SIM_set_class_attribute("image", "compressed_diff",
                                old_compressed_diff)
    
new_command("write-configuration", write_configuration_cmd,
            [arg(filename_t(),"file"), arg(flag_t, "-z"), arg(flag_t, "-u")],
            type  = ["Configuration"],
            short = "save configuration",
            see_also = ["read-configuration", "save-persistent-state"],
            doc = """
Write configuration to disk. In addition to the main text
configuration file, objects may create additional files with names
starting with <i>file</i>. Note that some classes save their state
incrementally meaning that files from earlier checkpoints (or from the
starting configuration) may be referenced in the new checkpoint.

Use the <tt>-z</tt> flag for compressed images, or <tt>-u</tt>
for uncompressed. The default is taken from the preference object.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2755")

#
# -------------------- save-persistent-state --------------------
#

def save_persistent_cmd(file, z, u):
    assert_not_running()

    old_compressed_diff = SIM_get_class_attribute("image", "compressed_diff")
    compr = conf.prefs.compress_images
    if u:
        compr = 0
    if z:
        compr = 1
    if os.path.exists(file):
        pr(("%s already exists. Overwriting persistent state files is not"
            + " supported.\n") % file)
        SIM_command_has_problem()
        return
    SIM_set_class_attribute("image", "compressed_diff", compr)
    try:
        if VT_write_configuration_persistent(file):
            print "Failed saving persistent state"
            SIM_command_has_problem()
    except Exception, msg:
        print "Failed saving persistent state: %s" % msg
        SIM_command_has_problem()
    SIM_set_class_attribute("image", "compressed_diff", old_compressed_diff)

new_command("save-persistent-state", save_persistent_cmd,
            [arg(filename_t(),"file"), arg(flag_t, "-z"), arg(flag_t, "-u")],
            type  = ["Configuration", "Disk"],
            short = "save persistent simulator state",
            see_also = ["load-persistent-state", "write-configuration"],
            doc = """
Save the persistent simulator state to a file. Persistent data typically
includes disk images, NVRAM and flash memory contents and clock settings,
i.e. data that survive reboots. The persistent state is saved as a
standard Simics configuration file.

Use the <tt>-z</tt> flag for compressed images, or <tt>-u</tt>
for uncompressed. The default is taken from the preference object.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2798")

def is_config_file(filename):
    try:
        f = open(filename, 'r')
        l = f.readline()
        while len(l):
            l = l.strip()
            if len(l) > 0 and not l.startswith('#'):
                if 'OBJECT' in l and 'TYPE' in l and '{' in l:
                    return 1
                else:
                    return 0
            l = f.readline()
    except:
        pass
    return 0

# called from main.c
def run_command_or_checkpt(filename):
    try:
        if is_config_file(filename):
            read_configuration_cmd(filename)
        else:
            SIM_run_command_file(filename)
    except Exception, msg:
        print msg

#
# -------------------- load-persistent-state --------------------
#

from configuration import convert_to_pre_objects
from configuration import OBJECT # for Python-format persistent-state files

def load_persistent_cmd(file, prefix):
    assert_not_running()
    (directory, fname) = os.path.split(file)
    # do an excursion to where it was saved, since file names in the config
    # are relative that directory
    here = os.getcwd()
    try:
        if directory:
            os.chdir(directory)
        try:
            f = open(fname, 'r')
            if is_config_file(fname):
                python_format = False
                config = VT_get_configuration(fname)
            else:
                python_format = True
                config = eval(open(fname, 'r').read())
        except Exception, msg:
            SIM_command_has_problem()
            print "Failed opening persistent state file: %s" % msg
            return

        try:
            if python_format:
                config = convert_to_pre_objects(config)
        except Exception, msg:
            SIM_command_has_problem()
            print "Illegal format in persistent state file: %s" % msg
            return
            
        for phase in (3, 0, 1): # 3 = phase -1
            for objname, obj in config.items():
                if objname not in ('sim', 'python'):
                    objname = prefix + objname
                try:
                    o = SIM_get_object(objname)
                except:
                    print ("Failed applying persistent state to object %s"
                           % objname)
                    print ("Perhaps '%s' refers to some other configuration?"
                           % file)
                    print
                    SIM_command_has_problem()
                    # skip this object
                    continue
                for a, v in [x for x in obj.__dict__.items()
                             if x[0][:2] != '__']:
                    if ((SIM_get_attribute_attributes(o.classname, a)
                         >> Sim_Init_Phase_Shift)
                        & Sim_Init_Phase_Mask) != phase:
                        continue
                    try:
                        SIM_set_attribute(o, a, v)
                    except Exception, msg:
                        print ("Failed setting attribute '%s' in '%s': %s"
                               % (a, objname, msg))
                        SIM_command_has_problem()
    finally:
        os.chdir(here)

new_command("load-persistent-state", load_persistent_cmd,
            [arg(filename_t(simpath = 1), "file"),
             arg(str_t, "prefix", "?", "")],
            type  = ["Configuration", "Disk"],
            short = "load persistent state",
            see_also = ["save-persistent-state", "read-configuration"],
            doc = """
Load persistent simulator state from a file. Persistent data typically
includes disk images, NVRAM and flash memory contents and clock settings,
i.e. data that survive reboots. The <param>prefix</param> argument can be
used to add a name prefix to all objects in the persistent state file.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2905")

#
# -------------------- run-python-file --------------------
#

def run_python_file_cmd(filename):
    try:
        SIM_source_python(filename)
    except Exception, msg:
        print "Failed executing Python file: ", msg
        SIM_command_has_problem()

new_command("run-python-file",
            run_python_file_cmd,
            args  = [arg(filename_t(exist = 1, simpath = 1), "filename")],
            alias = "source",
            type  = ["Python", "Command-Line Interface",
                     "Files and Directories"],
            short = "execute Python file",
            see_also = ["python", "@", "run-command-file", "add-directory"],
            doc = """
Read Python code from <i>filename</i>. Any definitions are entered into the top
level name-space in the Python environment. Uses the Simics search path to
locate <i>filename</i>. This command can be used to start Python scripts inside
Simics. """, filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="2929")

#  def my_command_cmd(arg):
#      ret = SIM_my_api_function(arg)
#      return ret

#  new_command("my-command", my_command_cmd,
#              args  = [arg(int_t, "arg")],
#              alias = "mc",
#              type  = "inspect/change commands",
#              short = "my command does it",
#              doc_items = [("NOTE", "This command is best")],
#              see_also = ["my_other_command"],
#              doc = """
#  <b>my-command</b> is best. 
#  This is its documentation. <i>arg</i> 
#  is the argument.""")

#
#
# -------------------- list-attributes --------------------
#

attr_list = {
    Sim_Attr_Required: "Required",
    Sim_Attr_Optional: "Optional",
    Sim_Attr_Session: "Session ",
    Sim_Attr_Pseudo: "Pseudo "
    }

# TODO: Move this command inside every namespace
def list_attributes_cmd(obj, attrname):
    try:
        attrs = obj.attributes

        def f(attr):
            s = []
            if attr[1] & Sim_Attr_Integer_Indexed:
                s += [ "Integer_Indexed" ]
            if attr[1] & Sim_Attr_String_Indexed:
                s += [ "String_Indexed" ]
            if attr[1] & Sim_Attr_List_Indexed:
                s += [ "List_Indexed" ]
            return [ attr[0], attr_list[int(attr[1] & 0xff)],
                     join(s, " ") ]

        if attrname == None:
            attrs = map(f, attrs)
            attrs.sort()
            print_columns([Just_Left, Just_Left, Just_Left],
                          [ [ "Attribute", "Type", "Flags" ] ] + attrs)
        else:
            found = 0
            
            for a in attrs:
                
                if a[0] == attrname:
                    found = 1
                    help_cmd("attribute:%s.%s" % (obj.name, attrname))

            if not found:
                print "No such attribute found"
                
    except Exception, msg:
	print msg
	print "Failed reading attributes"

new_command("list-attributes", list_attributes_cmd,
            args  = [arg(obj_t('object'), "object",
                         expander = conf_object_expander),
                     arg(str_t, "attribute-name", "?", None)],
            type  = ["Configuration", "Help"],
            short = "list all attributes",
            doc = """
Print a list of all attributes that are registered in an object. For every
attribute the type, as well as additional flags are listed. See the
<fun>SIM_register_typed_attribute()</fun> documentation function for valid
attribute types and flags. If an attribute name is given, the description for
that particular attribute will be displayed.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3008")

def attr_expander(string, obj):
    return get_completions(string, sim.classes[obj.classname].attributes)

new_command("list-attributes", list_attributes_cmd,
            args  = [arg(str_t, "attribute-name", "?",
                         expander = attr_expander)],
            type  = ["Configuration", "Help"],
            short = "list all attributes",
            namespace = 'conf_object_t',
            doc = """
Print a list of all attributes that are registered in an object. For every
attribute the type, as well as additional flags are listed. See the
<fun>SIM_register_typed_attribute()</fun> documentation function for valid
attribute types and flags. If an attribute name is given, the description for
that particular attribute will be displayed.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3025")

#
#
# -------------------- list-classes --------------------
#

def list_classes_cmd(loaded):
    all_classes = sorted(VT_get_all_known_classes())
    classes = sorted(SIM_get_all_classes())

    if loaded:
        if not classes:
            print "There are no classes defined."
            return
        print "The following classes have been registered:\n"
        print_columns([ Just_Left ], classes, has_title = 0)
    else:
        if not all_classes:
            print "There are no classes defined."
            return
        print "The following classes are available:\n"
        print_columns([ Just_Left ], all_classes, has_title = 0)

new_command("list-classes", list_classes_cmd,
            args = [arg(flag_t,"-l")],
            type  = ["Configuration"],
            short = "list all configuration classes",
            doc = """
Print a list of all configuration classes. The <arg>-l</arg> flag
will reduce the list to classes that has been registered by loaded
modules.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3061")

#
# -------------------- dummy commands (@ and !) --------------------
#

def dummy_command(cmd_name):
    # this does not catch ! and @
    print "Arguments missing, or illegal use of '%s' command" % cmd_name
    SIM_command_has_problem()

new_command("!", lambda : dummy_command("!"),
            type  = ["Command-Line Interface"],
            short = "execute a shell command",
            doc = """
Executes the rest of the command line in the system command-line
interpreter. For Unix, this is the default shell. For Windows, this is
<file>cmd.exe</file>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3080")

new_command("@", lambda : dummy_command("@"),
            type  = ["Command-Line Interface", "Python"],
            short = "evaluate a Python statement",
            see_also = ["python", "run-python-file"],
            doc = """
Evaluates the rest of the command line as a Python statement and print its
result.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3089")

new_command("if", lambda : dummy_command("if"),
            type  = ["Command-Line Interface", "Python"],
            see_also = ["while"],
            doc = """
Runs a block of commands conditionally. Some examples:
<pre>
if &lt;condition> { commands }
if &lt;condition> { commands } else { commands }
if &lt;condition> { commands } else if &lt;condition> { commands }
</pre>
The <cmd>if</cmd> command returns the value of the last executed command in
the block.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3098")

new_command("else", lambda : dummy_command("else"),
            type  = ["Command-Line Interface", "Python"],
            doc_with = "if", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3112")

new_command("while", lambda : dummy_command("while"),
            type  = ["Command-Line Interface", "Python"],
            see_also = ["if"],
            doc = """
Runs a block of commands while condition is true.
<pre>
while &lt;condition&gt; { commands }
</pre>
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3116")

new_command("script-branch", lambda : dummy_command("script-branch"),
            type  = ["Command-Line Interface", "Python"],
            see_also = ["list-script-branches",
                        "interrupt-script-branch",
                        "wait-for-variable",
                        "wait-for-hap",
                        "<text-console>.wait-for-string",
                        "<processor>.wait-for-cycle",
                        "<processor>.wait-for-step"],
            doc = """
Starts a block of commands as a separate branch. The <cmd>wait-for-</cmd>
commands can be used to postpone the execution of a script branch until
a selection action occurs.
<pre>
script-branch { commands }
</pre>
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3126")



next_expr_id = 1
expr_list = {}
last_cpu = 0
last_step = -1
display_cb_active = False

def display_expr(id):
    global expr_list
    (expr, typ, tag) = expr_list[id]
    if tag:
        print ">%d<" % id
    else:
        pr(expr + " :\t");
    try:
        if typ == "py":
            exec "print " + expr
        else:
            run(expr, 0)
    except:
        print "display expression %d raised exception" % (id)
    if tag:
        print ">.<"

def display_cb(always):
    global last_step, last_cpu
    now_cpu = SIM_current_processor()
    now_step = SIM_step_count(SIM_current_processor())
    if now_cpu == last_cpu and now_step == last_step and always == 0:
        return
    last_cpu = now_cpu
    last_step = now_step
    for id in expr_list.keys():
        display_expr(id)

def check_display_output():
    if display_cb_active:
        display_cb(0)

def list_displays():
    if expr_list:
        for id in expr_list.keys():
            (expr, typ, tag) = expr_list[id]
            print "%d: %s [%s]" % (id, expr, typ)
    else:
        print "Empty display list"

def display_cmd(expr, l, p, t):
    global next_expr_id, expr_list, display_cb_active
    global last_cpu, last_step
    if l:
        list_displays()
        return
    if expr == "<list>":
        display_cb(1)
        return

    if not display_cb_active:
        display_cb_active = True

    if p:
        type = "py"
    else:
        type = "cli"

    # avoid output first time
    last_cpu = SIM_current_processor()
    last_step = SIM_step_count(SIM_current_processor())

    if p:
        type = "py"
    else:
        type = "cli"
    expr_list[next_expr_id] = (expr, type, t)
    print "display %d: %s" % (next_expr_id, expr)
    next_expr_id += 1

def undisplay_cmd(expr_id):
    global expr_list, display_cb_active
    try:
        del expr_list[expr_id]
    except:
        print "No such display"
        return
    if not expr_list and display_cb_active:
        display_cb_active = False

new_command("display", display_cmd,
            [arg(str_t, "expression", "?", "<list>"),
             arg(flag_t, "-l"),
             arg(flag_t, "-p"),
             arg(flag_t, "-t")],
            alias = "",
            type  = ["Command-Line Interface", "Output"],
            short = "print expression at prompt",
            see_also = ["undisplay"],
            doc = """
Install a Python expression, or a frontend statement that will be printed
when Simics returns to the prompt. The <tt>-p</tt> flag is used to indicate
that the string argument is in Python. To list all installed display
expressions, the <tt>-l</tt> argument should be used. The expressions are
only evaluated and printed if the simulation has run any instructions since
last time, but a re-evaluation can be forced by calling display with no
arguments. The <tt>-t</tt> argument makes the output be tagged in a way
that makes it possible to capture the output by external means.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3232")

new_command("undisplay", undisplay_cmd,
            [arg(int_t, "expression-id")],
            alias = "",
            type  = ["Command-Line Interface", "Output"],
            short = "remove expression installed by display",
            see_also = ["display"],
            doc = """
Remove a Python expression, or a frontend statement that was previously
installed with the display command. The argument is the id number of the
expression, as listed by <tt>display -l</tt>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3252")

def pipe_cmd(cmd, prog):
    if sys.platform.startswith("win32"):
        print "The 'pipe' command is not supported on this host."
        return
    # syntax check of the command
    run(cmd, no_execute=True)
    import subprocess
    p = subprocess.Popen(prog, shell=True, stdin=subprocess.PIPE,
                         close_fds=True)
    # temporary replace fd 1 with the pipe to the command
    ostdout = os.dup(1)
    os.dup2(p.stdin.fileno(), 1)
    p.stdin.close()
    disable_columns()
    try:
        run(cmd)
    except Exception, exc:
        print "Exception!", exc
    enable_columns()
    os.dup2(ostdout, 1)
    os.close(ostdout)
    p.wait()
            
new_command("pipe", pipe_cmd,
            [arg(str_t, "command"), arg(str_t, "pipe")],
            alias = "",
            type  = ["Command-Line Interface", "Output"],
            short = "run commands through a pipe",
            doc = """
This command runs <tt>command</tt> at the Simics prompt and pipes the
output (stdout) through the external program <tt>pipe</tt>'s stdin.
Available on UNIX hosts only.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3287")

log_time_stamp = 0
log_file_only = 0
log_file_fd = None
log_file_name = None

# will only be called when group/type/level matches
def log_callback(arg, obj, type, str):
    if log_time_stamp:
        cpu = SIM_current_processor()
        ts = " {%s 0x%x %d}" % (cpu.name,
                                SIM_get_program_counter(cpu),
                                SIM_step_count(cpu))
    else:
        ts = ""
    if obj == None:
        log_string = "[%s]%s %s" % (conf.sim.log_types[type], ts, str)
    else:
        log_string = "[%s %s]%s %s" % (obj.name, conf.sim.log_types[type], ts, str)
    if not log_file_only:
        print log_string
    if log_file_fd:
        log_file_fd.write(log_string + "\n")

SIM_hap_add_callback("Core_Log_Message", log_callback, None)

#
# -------------------- log-setup --------------------
#

def log_setup_cmd(ts, no_ts, fo, no_fo, no_lf, logfile):
    global log_time_stamp, log_file_only, log_file_fd, log_file_name

    if ts and no_ts:
        print "Both -time-stamp and -no-time-stamp specified in log-setup."
        SIM_command_has_problem()
        return
    if fo and no_fo:
        print "Both -file-only and -no-file-only specified in log-setup."
        SIM_command_has_problem()
        return
    if logfile and no_lf:
        print "Both a log file and -no-log-file specified in log-setup."
        SIM_command_has_problem()
        return

    if (not ts
        and not no_ts
        and not fo
        and not no_fo
        and not no_lf
        and not logfile):
        print "Time stamp   : %sabled" % iff(log_time_stamp, "en", "dis")
        print "Log file only: %sabled" % iff(log_file_only, "en", "dis")
        print "Log file     : %s" % iff(log_file_fd, log_file_name, "Not used")
        return

    if ts:
        log_time_stamp = 1
    elif no_ts:
        log_time_stamp = 0
    if fo:
        log_file_only = 1
    elif no_fo:
        log_file_only = 0

    if logfile:
        try:
            open(logfile, "r")
            SIM_command_has_problem()
            print "File %s already exists." % logfile
            return
        except:
            pass
        try:
            log_file_fd = open(logfile, "w")
            log_file_name = logfile
        except Exception, msg:
            SIM_command_has_problem()
            print "Failed opening log file %s : %s" % (logfile, msg)
            return
    elif no_lf:
        if log_file_fd:
            log_file_fd.close()
            log_file_fd = None
            log_file_name = None


new_command("log-setup", log_setup_cmd,
            args  = [arg(flag_t, "-time-stamp"),
                     arg(flag_t, "-no-time-stamp"),
                     arg(flag_t, "-file-only"),
                     arg(flag_t, "-no-file-only"),
                     arg(flag_t, "-no-log-file"),
                     arg(filename_t(), "logfile", "?", None)],
            type  = ["Output", "Logging"],
            short = "configure log behavior",
            see_also = ["log", "<log_object>.log-group", "log-size",
                        "log-type"],
            doc = """
            The <arg>-time-stamp</arg> flag will cause further log output to
            include a time stamp, i.e. the name of the current processor
            together with the program counter and step count for this CPU. Time
            stamp output is disabled with <arg>-no-time-stamp</arg>. A file
            that receives all log output can be specified with the
            <arg>logfile</arg> argument. <arg>-no-log-file</arg> disables an
            existing log file. Even if a log file is specified, all output is
            printed on the console, unless <arg>-file-only</arg> is used. Use
            <arg>-no-file_only</arg> to re-enable output. Called without
            arguments, the command will print the current setup.
            """, filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3385");

#
# -------------------- log-level --------------------
#

def global_log_level_cmd(level):
    if level == -1:
        print "Current log levels:"
        for obj in SIM_get_all_objects():
            if LOG_OBJECT_INTERFACE in dir(obj.iface):
                print "[%s] %d" % (obj.name, obj.log_level)
        print
        return

    if level < 0 or level > 4:
        print "Illegal log level: %d. Allowed are 0 - 4." % level
        SIM_command_has_problem()
        return
    for obj in SIM_get_all_objects():
        if LOG_OBJECT_INTERFACE in dir(obj.iface):
            obj.log_level = level
    #also change the default log-level
    conf.sim.default_log_level = level
    print "New global log level: %d" % level

new_command("log-level", global_log_level_cmd,
            args  = [arg(int_t, "level", "?", -1)],
            type  = ["Output", "Logging"],
            short = "set or get the global log level",
            see_also = ["log", "<log_object>.log-group", "log-size",
                        "log-type"],
            doc = """
Objects in Simics can generate log messages on different <i>log levels</i>.
These messages will be show in the Simics command line window if the log level
for the object has been set high enough.

The default level is 1, and this is the lowest level that objects can report
messages on. Setting it to 0 will inhibit output of all messages.

Messages are also added to an access log that can be viewed by the <cmd>log</cmd>
command in Simics.

There are four log levels defined:
  1 - important messages printed by default.
  2 - "high-level" informative messages.
  3 - standard debug messages.
  4 - detailed information, such as register accesses.

Not all classes are converted to use this log level scheme.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3433")


#
# -------------------- <obj>.log-level --------------------
#

def log_level_cmd(obj, level):
    old = obj.log_level
    if level == -1:
        print "[%s] Current log level: %d" % (obj.name, old)
        return
    if level < 0 or level > 4:
        print "Illegal log level: %d. Allowed are 0 - 4." % level
        SIM_command_has_problem()
        return
    if level != old:
        obj.log_level = level
        print "[%s] Changing log level: %d -> %d" % (obj.name, old, level)
    else:
        print "[%s] Log level unchanged, level: %d" % (obj.name, old)

new_command("log-level", log_level_cmd,
            args  = [arg(int_t, "level", "?", -1)],
            type  = ["Output", "Logging"],
            namespace = "log_object",
            short = "set or get the log level",
            doc_with = "log-level", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3479")

#
# -------------------- log-type --------------------
#

def log_type_expander(string):
    return get_completions(string, conf.sim.log_types)

def global_log_type_cmd(add_flag, sub_flag, log_type):
    types = conf.sim.log_types

    if log_type == "":
        print "Current log types:"
        for obj in SIM_get_all_objects():
            if LOG_OBJECT_INTERFACE in dir(obj.iface):
                print "[%s] %s" % (obj.name, log_names(types, obj.log_type_mask))
        print
        return

    if log_type == "all":
        new_mask = 0xffffffffL
        change_mask = 0
        if sub_flag:
            print "Cannot remove all log types."
            SIM_command_has_problem()
            return
    else:
        try:
            change_mask = 1 << types.index(log_type)
        except:
            print "Unknown log type: %s " % log_type
            SIM_command_has_problem()
            return
        for obj in SIM_get_all_objects():
            if not LOG_OBJECT_INTERFACE in dir(obj.iface):
                continue
            if add_flag:
                new_mask = obj.log_type_mask | change_mask
            elif sub_flag:
                new_mask = obj.log_type_mask & ~change_mask
            else:
                new_mask = change_mask
            obj.log_type_mask = new_mask

    if add_flag:
        print "Adding global log type: %s" % log_names(types, change_mask)
    elif sub_flag:
        print "Removing global log type: %s" % log_names(types, change_mask)
    else:
        print "Setting global log type: %s" % log_names(types, change_mask)
    


new_command("log-type", global_log_type_cmd,
            args  = [arg(flag_t, "-add"),
                     arg(flag_t, "-sub"),
                     arg(str_t, "log-type", "?", "", expander = log_type_expander)],
            type  = ["Output", "Logging"],
            short = "set or get the current log types",
            see_also = ["log", "<log_object>.log-group", "log-level",
                        "log-size"],
            doc = """
Log messages are categorised into one of the several log types. By default,
messages of all types are handled in the same way. This command can be used
to select one or several types. Only messages of the selected types will be
logged and displayed, as defined by the <cmd>log-level</cmd> command. The
flags <b>-add</b> and <b>-sub</b> can be used to add and remove a single log
type. The log types are documented with the <tt>log_type_t</tt> data type,
and are Info, Error, Undefined, Spec_Violation, Target_Error, Unimplemented.
All types can be enabled by setting <b>log-type</b> to <tt>all</tt>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3538")


#
# -------------------- <obj>.log-type --------------------
#

def log_names(all, mask):
    names = ""
    not_all = 0
    for i in range(len(all)):
        if mask & (1 << i):
            names += all[i] + " "
        else:
            not_all = 1
    if (names == "" and len(all) == 0) or not_all == 0:
        names = "all"
    return names

def log_type_cmd(obj, add_flag, sub_flag, log_type):
    types = conf.sim.log_types
    old_mask = obj.log_type_mask

    if log_type == "":
        print "[%s] Current log types: %s" % (obj.name, log_names(types, old_mask))
        return

    if log_type == "all":
        new_mask = 0xffffffffL
        if sub_flag:
            print "Cannot remove all log types."
            SIM_command_has_problem()
            return
    else:
        try:
            type_id = types.index(log_type)
        except:
            print "Unknown log type: %s " % log_type
            SIM_command_has_problem()
            return
        if add_flag:
            new_mask = obj.log_type_mask | (1 << type_id)
        elif sub_flag:
            new_mask = obj.log_type_mask & ~(1 << type_id)
        else:
            new_mask = 1 << type_id

    obj.log_type_mask = new_mask
    old_names = log_names(types, old_mask)
    new_names = log_names(types, new_mask)
    # compare the names and not the masks (for 'all' to work)
    if old_names != new_names:
        print "[%s] Changing log types: %s -> %s" % (obj.name, old_names, new_names)
    else:
        print "[%s] Unchanged log types: %s" % (obj.name, old_names)


new_command("log-type", log_type_cmd,
            args  = [arg(flag_t, "-add"),
                     arg(flag_t, "-sub"),
                     arg(str_t, "log-type", "?", "", expander = log_type_expander)],
            type  = ["Output", "Logging"],
            namespace = "log_object",
            short = "set or get the current log types",
            doc_with = "log-type", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3612")

#
# -------------------- <obj>.log-group --------------------
#

def log_group_expander(string, obj):
    return get_completions(string, ['all'] + obj.log_groups)

def log_group_cmd(obj, add_flag, sub_flag, log_group):
    groups = obj.log_groups
    old_mask = obj.log_group_mask

    if log_group == "":
        print "[%s] Current log groups: %s" % (obj.name, log_names(groups, old_mask))
        return
    
    if log_group == "all":
        if sub_flag:
            new_mask = 0
        else:
            new_mask = 0xffffffffL
    else:
        try:
            group_id = groups.index(log_group)
        except:
            print "Unknown log group: %s " % log_group
            SIM_command_has_problem()
            return
        if add_flag:
            new_mask = obj.log_group_mask | (1 << group_id)
        elif sub_flag:
            new_mask = obj.log_group_mask & ~(1 << group_id)
        else:
            new_mask = 1 << group_id

    obj.log_group_mask = new_mask
    old_names = log_names(groups, old_mask)
    new_names = log_names(groups, new_mask)
    # compare the names and not the masks (for 'all' to work)
    if old_names != new_names:
        print "[%s] Changing log groups: %s -> %s" % (obj.name, old_names, new_names)
    else:
        print "[%s] Unchanged log groups: %s" % (obj.name, old_names)

new_command("log-group", log_group_cmd,
            args  = [arg(flag_t, "-add"),
                     arg(flag_t, "-sub"),
                     arg(str_t, "log-group", "?", "", expander = log_group_expander)],
            type  = ["Output", "Logging"],
            namespace = "log_object",
            short = "set or get the current log groups",
            see_also = ["log", "log-level", "log-size", "log-type"],
            doc = """
A log object in Simics can specify a number of groups, and each log message
is associated with one group. Groups are typically used to separate log
messages belonging to different aspects of an object such as a device. For
example, a network device can have different group for the receive and transmit
engine, one groups for the host protocol and another for PCI accesses. Having
multiple groups simplifies debugging when only messages of the selected groups
are logged and displayed. By default all groups are active, but a single group
can be set with this command, or groups can be added and removed using the
flags <b>-add</b> and <b>-sub</b> for the command. All groups can be enabled by
setting <b>log-group</b> to <tt>all</tt>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3664")


#
# -------------------- log-size --------------------
#

def global_log_size_cmd(newsize):
    if newsize == -1:
        print "Current log buffer sizes: (number of entries)"
        for obj in SIM_get_all_objects():
            if LOG_OBJECT_INTERFACE in dir(obj.iface):
                print "[%s] %d" % (obj.name, obj.log_buffer_size)
        return

    for obj in SIM_get_all_objects():
        if not LOG_OBJECT_INTERFACE in dir(obj.iface):
            continue
        try:
            obj.log_buffer_size = newsize
        except Exception, msg:
            print "Error changing log buffer size: %s" % msg
            SIM_command_has_problem()
            return
    print "Setting new size of all log buffers: %d" % newsize

new_command("log-size", global_log_size_cmd,
            [arg(int_t, "size", "?", -1)],
            alias = "",
            type  = ["Output", "Logging"],
            short = "set log buffer size",
            see_also = ["log", "<log_object>.log-group", "log-level",
                        "log-type"],
            doc = """
The namespace version of this command changes the buffer size (number of
entries) for log messages and I/O trace entries for an objects. The global
command applies to all log objects. When called with no arguments, the size
of the log buffers are listed.<br/>
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3709")

#
# -------------------- <obj>.log-size --------------------
#

def log_size_cmd(obj, newsize):
    oldsize = obj.log_buffer_size
    if newsize == -1:
        print "Current log buffer size: %d entries" % oldsize
        return

    try:
        obj.log_buffer_size = newsize
    except Exception, msg:
        print "Error changing log buffer size: %s" % msg
        SIM_command_has_problem()
        return
    print "[%s] Changing size of the log buffer: %d -> %d" % (obj.name, oldsize, newsize)

new_command("log-size", log_size_cmd,
            [arg(int_t, "size", "?", -1)],
            alias = "",
            type  = ["Output", "Logging"],
            short = "set log buffer size",
            namespace = "log_object",
            doc_with = "log-size", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3741")


#
# -------------------- log --------------------
#

def trace_sort_func(a, b):
    if a[0][1] > b[0][1]:
        return -1
    if b[0][1] > a[0][1]:
        return 1
    if a[0][0] > b[0][0]:
        return 1
    if b[0][0] > a[0][0]:
        return -1
    return 0

def global_log_cmd(num):
    trace_list = []
    for obj in SIM_get_all_objects():
        if not LOG_OBJECT_INTERFACE in dir(obj.iface):
            continue
        try:
            entry = obj.log_buffer_last
            size = obj.log_buffer_size
            i = 0
            while i < num:
                trace = obj.log_buffer[entry]
                entry = (entry + size - 1) % size
                i = i + 1
                trace[0].insert(0, obj)
                trace_list.append(trace)
        except:
            pass

    trace_list.sort(trace_sort_func)
    count = min(num, len(trace_list))
    for i in range(count):
        display_log_entry(trace_list[i])
    if count == 0:
        print "Empty log buffers"
    elif count < num:
        print "Only %d entries listed (no more in log buffers)" % count

new_command("log", global_log_cmd,
            args = [arg(int_t, "count", "?", 10)],
            alias = "",
            type  = ["Output", "Logging"],
            short = "print log entries for all objects",
            see_also = ["<log_object>.log-group", "log-level", "log-size",
                        "log-type"],
            doc = """
Display entries in log buffers. The namespace version displays the entries
for a specific object, while the global command lists the entries of all
object's log buffers but sorted by time. The optional argument is the number
of entries to list. Only the last 10 entries are listed by default.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3792")


#
# -------------------- <object>.log --------------------
#

read_write_str = ("Read", "Write")

def display_log_entry(trace):
    if trace[0][2]:
        cpu_name = trace[0][2].name
    else:
        cpu_name = "None"
    str = " Timestamp: obj = %s cycle = %d cpu = %-5s pc = 0x%x" % (
        trace[0][0].name, trace[0][1], cpu_name, trace[0][3])
    if trace[1] == []:
        print "   *   %s" % str
    else:
        print "%6d %s" % (trace[1][5], str)
        if trace[1][0]:
            acc_name = trace[1][0].name
        else:
            acc_name = "Unknown"
        str = "        %-5s access from %s. PA = 0x%x" % (read_write_str[trace[1][3]],
                                                          acc_name,
                                                          trace[1][1])
        str = str + " size = %d  data = 0x%x" % (trace[1][2], trace[1][4])
        print str
    for msg in trace[2]:
        grps = msg[1]
        names = ""
        for i in range(32): # 32 groups should be enough for anyone...
            if not grps:
                break
            if grps & 1:
                try:
                    if len(names):
                        names += ", "
                    names += trace[0][0].log_groups[i]
                except:
                    pass # illegal group specified
            grps >>= 1
        print "        [%s - %s] %s" % (conf.sim.log_types[msg[2]], names, msg[0])
    print

def log_cmd(obj, num):
    some_lost = 0
    size = obj.log_buffer_size
    if num > size:
        num = size
        some_lost = 1
    try:
        entry = obj.log_buffer_last
    except Exception, msg:
        print "Empty log buffer"
        return
    try:
        i = 0
        while i < num:
            trace = obj.log_buffer[entry]
            trace[0].insert(0, obj)
            display_log_entry(trace)
            entry = (entry + size - 1) % size
            i = i + 1
    except Exception, msg:
        some_lost = 1
    if some_lost:
        print "Only %d entries listed (no more in buffer)" % i

new_command("log", log_cmd,
            args = [arg(int_t, "count", "?", 10)],
            alias = "",
            type  = ["Output", "Logging"],
            short = "print log entries for all objects",
            namespace = "log_object",
            doc_with = "log", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3874")

#
# -------------------- cpu-switch-time --------------------
#

def cpu_switch_time_cmd(poly):
    try:
        cpu0_freq = SIM_proc_no_2_ptr(0).freq_mhz * 1e6
    except Exception, msg:
        cpu0_freq = None
    
    if poly == -1:
        print "Current CPU switch time: %d cycles" % (conf.sim.cpu_switch_time),
        if cpu0_freq:
            print "(%f seconds)" % (conf.sim.cpu_switch_time / cpu0_freq)
        else:
            print
    else:
        if poly[0] == int_t:
            cycles = poly[1]
        
        elif poly[0] == float_t:
            if cpu0_freq:
                seconds = poly[1]            
                cycles = int(cpu0_freq * seconds)
            else:
                print "Cannot set cpu-switch-time with seconds, no processor defined"
                SIM_command_has_problem()
                return
        else:
            print "invalid argument type passed"
            SIM_command_has_problem()
            return
                        
        try:
            conf.sim.cpu_switch_time = cycles
        except Exception, msg:
            print "Failed changing CPU switch time: %s" % msg
            SIM_command_has_problem()
            return

    try:
        print "The switch time will change to %d cycles (for CPU-0) once" % conf.sim.new_switch_time,
        print "all processors have synchronized."
    except:
        pass

new_command("cpu-switch-time", cpu_switch_time_cmd,
            args = [arg((int_t, float_t),
                        ("cycles", "seconds"),
                        "?", -1)],
            alias = "",
            type  = ["Execution", "Speed"],
            short = "get/set CPU switch time",
            doc = "Change the time, in cycles or seconds, between CPU switches. Simics will "
            "simulate each processor for a specified number of cycles before "
            "switching to the next one. Specifying cycles (which is default) refers to "
            "the number of cycles on the first CPU in Simics. The following CPUs cycle switch "
            "times are calulated from their CPU frequencies. "
            "When issued with no argument, the current switch time is reported.", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3928")

def api_trace_cmd(poly):
    if poly[0] == flag_t:
        if poly[1]:
            if poly[2] == '-stderr':
                conf.sim.api_trace_file = 0
            else:
                conf.sim.api_trace_file = None
            return
        
        trace = conf.sim.api_trace_file
        if type(trace) == type(0):
            print "API calls traced to stderr"
        elif trace == None:
            print "API trace currently off"
        else:
            print "API calls traced to '%s'" % trace
        return

    try:
        conf.sim.api_trace_file = poly[1]
    except SimExc_IOError, msg:
        print "Failed tracing to file '%s': %s" % (poly[1], msg)

try:
    conf.sim.api_trace_file

    new_command('api-trace', api_trace_cmd,
                args = [arg((flag_t, flag_t, str_t),
                            ('-off', '-stderr', 'file'),
                            '?', (flag_t, 0))],
                type = 'general commands',
                short = 'get/set API trace status',
                doc = '''
With no arguments, shows current API trace status.

If called with the <tt>-off</tt> flag, turns off API tracing.

If called with the <tt>-stderr</tt> flag, start tracing to stderr.

If called with a <arg>file</arg> argument, starts tracing to that
file. Its contents is overwritten.

This command is only available when Simics is started with the
<tt>SIMICS_API_TRACE</tt> environment variable set. Its value controls
if tracing is turned on or off when Simics starts. If set to
<tt>on</tt>, API tracing is turned on with output to stderr. If set to
<tt>on:<arg>file</arg></tt>, output is sent to <arg>file</arg>.  For
other values, API tracing is turned off.''', filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="3968")

except:
    pass


#
# -------------------- < --------------------
#

def less_than(a, b):
    return a < b

new_command("<", less_than,  [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 50, infix = 1,
            short = "less than",
            doc = """
Returns 1 if <var>arg1</var> is less than  <var>arg2</var>, and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4002")

#
# -------------------- <= --------------------
#

def less_or_equal(a, b):
    return a <= b

new_command("<=", less_or_equal,  [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 50, infix = 1,
            short = "less or equal",
            doc = """
Returns 1 if <var>arg1</var> is less than or equal to <var>arg2</var>,
and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4017")

#
# -------------------- > --------------------
#

def greater_than(a, b):
    return a > b

new_command(">", greater_than,  [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 50, infix = 1,
            short = "greater than",
            doc = """
Returns 1 if <var>arg1</var> is greater than <var>arg2</var>, and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4033")

#
# -------------------- >= --------------------
#

def greater_or_equal(a, b):
    return a >= b

new_command(">=", greater_or_equal,  [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            pri = 50, infix = 1,
            short = "greater or equal",
            doc = """
Returns 1 if <var>arg1</var> is greater than or equal to <var>arg2</var>,
and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4048")

#
# -------------------- != --------------------
#

def not_equal(a, b):
    return a[1] != b[1]

new_command("!=", not_equal,
            [arg((int_t, str_t), ('i1', 's1'), doc = 'arg1'),
             arg((int_t, str_t), ('i2', 's2'), doc = 'arg2')],
            type = ["Command-Line Interface"],
            pri = 50, infix = 1,
            short = "not equal",
            doc = """
Returns 1 if <var>arg1</var> and <var>arg2</var> are not equal, and 0 if equal.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4064")

#
# -------------------- == --------------------
#

def equal(a, b):
    return a[1] == b[1]

new_command("==", equal,
            [arg((int_t, str_t), ('i1', 's1'), doc = 'arg1'),
             arg((int_t, str_t), ('i2', 's2'), doc = 'arg2')],
            type = ["Command-Line Interface"],
            pri = 50, infix = 1,
            short = "equal",
            doc = """
Returns 1 if <var>arg1</var> and <var>arg2</var> are equal, and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4081")

#
# -------------------- min --------------------
#

def min_cmd(a, b):
    return min(a, b)

new_command("min", min_cmd,  [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            short = "min",
            doc = """
Returns the smaller value of <var>arg1</var> and <var>arg2</var>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4098")

#
# -------------------- max --------------------
#

def max_cmd(a, b):
    return max(a, b)

new_command("max", max_cmd,  [arg(int_t), arg(int_t)],
            type = ["Command-Line Interface"],
            short = "max",
            doc = """
Returns the larger value of <var>arg1</var> and <var>arg2</var>.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4112")

def is_set(a):
    return a or a == ''

#
# ------------------- and --------------------
#

def and_command(a, b):
    return iff(is_set(a[1]) and is_set(b[1]), 1, 0)

new_command("and", and_command,
            [arg((int_t, str_t), ('iarg1', 'sarg1'), doc = 'arg1'),
             arg((int_t, str_t), ('iarg2', 'sarg2'), doc = 'arg2')],
            type = ["Command-Line Interface"],
            pri = 20, infix = 1,
            short = "logical and",
            doc = """
Returns 1 if both <var>arg1</var> and <var>arg2</var> are non-zero,
and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4129")

#
# ------------------- or --------------------
#

def or_command(a, b):
    return iff(is_set(a[1]) or is_set(b[1]), 1, 0)

new_command("or", or_command, 
            [arg((int_t, str_t), ('iarg1', 'sarg1'), doc = 'arg1'),
             arg((int_t, str_t), ('iarg2', 'sarg2'), doc = 'arg2')],
            type = ["Command-Line Interface"],
            pri = 10, infix = 1,
            short = "logical or",
            doc = """
Returns 1 if <var>arg1</var> or <var>arg2</var> is non-zero,
and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4147")

#
# ------------------- not --------------------
#

def not_command(a):
    return iff(is_set(a[1]), 0, 1)

new_command("not", not_command,
            [arg((int_t, str_t), ('iarg', 'sarg'), doc = 'arg')],
            type = ["Command-Line Interface"],
            pri = 30,
            short = "logical not",
            doc = """
Returns 1 if <var>arg</var> is zero, and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4165")

#
# ------------------- defined --------------------
#

def defined_command(v):
    return v in get_current_locals().get_all_variables()

new_command("defined", defined_command,
            [arg(str_t, 'variable')],
            type = ["Command-Line Interface"],
            short = "variable defined",
            pri = 40, # higher than 'not' command
            doc = """
Returns 1 if <var>variable</var> is a defined CLI variable, and 0 if not.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4181")

#
# ------------ wait-for-variable ------------
#

def wait_for_variable_command(name):
    if conf.python.iface.python.in_main_branch():
        SIM_command_has_problem()
        print ("The wait-for-variable command is only allowed "
               "in script branches.")
    else:
        ret = [None, None]
        while ret[1] != name:
            try:
                ret = wait_for_hap("CLI_Variable_Write")
            except SimExc_Break:
                print "Command 'wait-for-variable' interrupted."
                SIM_command_has_problem()

new_command("wait-for-variable", wait_for_variable_command, 
            [arg(str_t, 'variable')],
            short = "wait for a variable to change",
            see_also = ["script-branch",
                        "wait-for-hap",
                        "<text-console>.wait-for-string",
                        "<processor>.wait-for-cycle",
                        "<processor>.wait-for-step"],
            doc = """
Postpones execution of a script branch until a CLI variable is written by some
other script branch or the main thread.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4208")

#
# ------------ wait-for-cycle ------------
#

def wait_for_cycle_command(obj, cycle):
    if conf.python.iface.python.in_main_branch():
        SIM_command_has_problem()
        print ("The wait-for-cycle command is only allowed "
               "in script branches.")
    else:
        try:
            wait_for_obj_hap("Core_Cycle_Count", obj, cycle)
        except SimExc_Break:
            print "Command '%s.wait-for-cycle' interrupted." % obj.name
            SIM_command_has_problem()

new_command("wait-for-cycle", wait_for_cycle_command, 
            [arg(int_t, 'cycle')],
            namespace = "processor",
            short = "wait until reaching cycle",
            see_also = ["script-branch",
                        "wait-for-variable",
                        "wait-for-hap",
                        "<text-console>.wait-for-string",
                        "<processor>.wait-for-step"],
            doc = """
Postpones execution of a script branch until the processor reaches the
specified cycle in the simulation.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4237")

#
# ------------ wait-for-step ------------
#

def wait_for_step_command(obj, step):
    if conf.python.iface.python.in_main_branch():
        SIM_command_has_problem()
        print ("The wait-for-step command is only allowed "
               "in script branches.")
    else:
        try:
            wait_for_obj_hap("Core_Step_Count", obj, step)
        except SimExc_Break:
            print "Command '%s.wait-for-step' interrupted." % obj.name
            SIM_command_has_problem()

new_command("wait-for-step", wait_for_step_command, 
            [arg(int_t, 'step')],
            namespace = "processor",
            short = "wait until reaching step",
            see_also = ["script-branch",
                        "wait-for-variable",
                        "wait-for-hap",
                        "<text-console>.wait-for-string",
                        "<processor>.wait-for-cycle"],
            doc = """
Postpones execution of a script branch until the processor reaches the
specified step in the simulation.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4267")

#
# ------------ wait-for-hap ------------
#

def wait_for_hap_command(hap, obj, idx0, idx1, ret):
    if conf.python.iface.python.in_main_branch():
        SIM_command_has_problem()
        print "The wait-for-hap command is only allowed in script branches."
    else:
        try:
            r = wait_for_obj_hap(hap, obj, idx0, idx1)
        except SimExc_Break:
            print "Command 'wait-for-hap' interrupted."
            SIM_command_has_problem()
        if ret:
            for i in range(len(r)):
                if type(r[i]) == type(conf.sim):
                    r[i] = r[i].name
                simenv.set_variable_value_idx(ret, r[i], 1, i)

new_command("wait-for-hap", wait_for_hap_command,
            [arg(str_t, 'hap', '', expander = hap_expander),
             arg(obj_t('object'), "object", '?', None),
             arg(int_t, 'idx0', '?', -1),
             arg(int_t, 'idx1', '?', -1),
             arg(str_t, 'ret', '?')],
            short = "wait until hap occurs",
            see_also = ["script-branch",
                        "wait-for-variable",
                        "<text-console>.wait-for-string",
                        "<processor>.wait-for-cycle",
                        "<processor>.wait-for-step"],
            doc = """
Postpones execution of a script branch until <arg>hap</arg> occurs. The
optional argument <arg>obj</arg> limits the haps to a specific object, and
<arg>idx0</arg>, <arg>idx1</arg> can be used for indexed and range haps. The
data associated with the hap can be saved into the named variable specified by
<arg>ret</arg>. This variable will be indexed, with local scope.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4301")

def list_script_branch_command():
    print "ID  Object          Hap                Hap-ID  Function"
    for sb in conf.python.script_branches:
        if sb[3]:
            name = sb[3].name
        else:
            name = "None"
        print "%-3d %-15s %-20s  %3d  %s" % (sb[0], name, sb[1], sb[2], sb[4])

new_command("list-script-branches", list_script_branch_command,
            see_also = ["script-branch", "interrupt-script-branch"],
            doc = """
List all currently active script branches.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4330")

def interrupt_script_branch_command(id):
    try:
        conf.python.iface.python.interrupt_branch(id)
        print "Script branch %d interrupted." % id
    except Exception, msg:
        print "Failed interrupting script branch: %s" % msg
        SIM_command_has_problem()
    
new_command("interrupt-script-branch", interrupt_script_branch_command,
            [arg(int_t, 'id')],
            see_also = ["script-branch", "list-script-branches"],
            doc = """
Send a interrupt exception to a scripts branch. The argument is the script
branch ID, that is returned by the <cmd>script-branch</cmd> command, and that
is also listed by the <cmd>list-script-branches</cmd> command. The branch will
wakeup and exit when it receives the exception.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4344")

all_tee_objs = []

def tee_handler(file, buf, count):
    file.write(buf)
    file.flush()

def tee(filename):
    global all_tee_objs
    try:
        file_obj=open(filename, "w")
    except:
        print "Failed to open '%s' for writing" % filename
        SIM_command_has_problem()
        return
    all_tee_objs.append((filename, file_obj))
    SIM_add_output_handler(tee_handler, file_obj)

def remove_tee(filename):
    for i in range(len(all_tee_objs)):
        (name, obj) = all_tee_objs[i]
        if filename == None or name == filename:
            SIM_remove_output_handler(tee_handler, obj)
            obj.close()
            del(all_tee_objs[i])
            if filename:
                return
    if filename:
        print "Output not enabled to file '%s'" % filename
        SIM_command_has_problem()

new_command("output-file-start", tee,
            [ arg(filename_t(), "filename") ],
            type = ["Files and Directories"],
            short = "send output to file",
            see_also = ['output-file-stop'],
            doc = """
Send output to <i>filename</i>. Any output displayed in the Simics console that goes through the output handler API will be written to the file.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4384")

new_command("output-file-stop", remove_tee,
            [ arg(filename_t(), "filename", "?", None) ],
            type = ["Files and Directories"],
            short = "stop sending output to file",
            see_also = ['output-file-start'],
            doc = """
Stop sending output to file. If no filename is given, then the command
will disable all file output.""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4392")

def add_module_path_cmd(path):
    VT_add_module_dir(path)
    SIM_module_list_refresh()
    
new_command("add-module-directory", add_module_path_cmd,
            [arg(filename_t(dirs = 1), "path")],
            type = ["Simics Search Path", "Configuration",
                    "Files and Directories", "Modules"],
            short = "add a directory to the module search path",
            doc = """
Adds a directory to the Simics module search path. This path is used to look
for additional modules, that can be used to extend the functionality of Simics.
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4405")

def signed_cmd(size, value):
    return (value & ((1 << size) - 1)) - ((value << 1) & (1 << size))

new_command("signed", lambda x : signed_cmd(64, x),
            [arg(int_t, "int")],
            type = ["Command-Line Interface", "Output"],
            short = "interpret unsigned integer as signed",
            doc = """
Interpret an integer, <param>int</param>, as a signed value of a specific bit
width. For example <cmd>signed16 0xffff</cmd> will return -1. The
<cmd>signed</cmd> command assumes a 64 bit width. 
""", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4418")

def _signed_cmd(s):
    return lambda x : signed_cmd(s, x)

for i in (8, 16, 32, 64):
    new_command("signed%d" % i, _signed_cmd(i),
                [arg(int_t, "int")],
                type = ["Command-Line Interface", "Output"],
                short = "interpret unsigned integer as signed",
                doc_with = "signed", filename="/mp/simics-3.0/src/core/common/generic_commands.py", linenumber="4432")
import sim_commands

# asserts that Simics is stopped
def assert_stopped():
    assert_cpu()
    if SIM_simics_is_running():
        raise CliError, "Simics is already running."

# internal for commands
def list_processors():
    limit = SIM_number_processors()
    print "Current status:"
    for i in range(limit):
        cpu = SIM_get_processor(i)
        print "Processor", cpu.name, iff(SIM_processor_enabled(cpu), "enabled.", "disabled.")

def conf_object_expander(string):
    return get_completions(string, conf.all_object_names);

#
# -------------- simics-path commands ----------------
#

def add_directory_cmd(path, prepend):
    SIM_add_directory(path, prepend)
    
new_command("add-directory", add_directory_cmd,
            [arg(filename_t(dirs = 1, keep_simics_ref = 1), "path"),
             arg(flag_t, "-prepend")],
            type = ["Simics Search Path", "Configuration",
                    "Files and Directories"],
            short = "add a directory to the Simics search path",
            doc = """
Adds a directory to the Simics search path. The Simics search path is a list of
directories where Simics searches for additional files when loading a
configuration or executing a command like <cmd>load-file</cmd>. 

The value of <arg>path</arg> is normally appended at the end of the list. If
the <i>-prepend</i> flag is given, the path will be added as first in the list.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="27")

def print_directories_cmd():
    dirs = SIM_get_directories()
    print "The current Simics search path is:"
    for dir in dirs:
        print dir
    
new_command("list-directories", print_directories_cmd,
            [],
            type = ["Simics Search Path", "Files and Directories"],
            short = "list directories in Simics search path",
            doc = """
Print a list of all directories in the Simics search path.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="48")

new_command("print-directories", print_directories_cmd,
            [],
            short = "print the directory Simics search path",
            type = "deprecated commands",
            deprecated = "list-directories", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="56")

def clear_directories_cmd():
    SIM_clear_directories()
    print "Simics search path is now empty."
    
new_command("clear-directories", clear_directories_cmd,
            [],
            type = ["Simics Search Path", "Files and Directories"],
            short = "clear the Simics search path",
            doc = """
Empty the Simics search path.
            """, filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="66")


def resolve_file_cmd(filename):
    file = SIM_lookup_file(filename)
    if not file:
        print "Not in search path:", filename
    else:
        return file

new_command("resolve-file", resolve_file_cmd,
            [arg(str_t, "filename")],
            type = ["Simics Search Path", "Files and Directories"],
            short = "resolve a filename",
            alias = "lookup-file",
            doc = """\
Looks for the file <arg>filename</arg> in the Simics search path. If it
is found, its complete path is returned.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="82")

def native_path_cmd(filename):
    return SIM_native_path(filename)

new_command("native-path", native_path_cmd,
            [arg(str_t, "filename")],
            type = ["Files and Directories"],
            short = "convert a filename to host native form",
            doc = """\
Converts a path to its host native form. On Unix, this command returns
<arg>filename</arg> unchanged. On Windows, it translates Cygwin-style paths
to native Windows paths. Refer to the documentation
<b>SIM_native_path()</b>, for a detailed description of the conversions
made.

This command can be used for portability when opening files residing on the
host filesystem.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="95")

# Print a table (list of rows, each a list of strings).
# The alignments list specifies how each column should be aligned,
# each entry being "r" or "l". The string 'spacing' is put between columns.
def print_table(table, alignments, spacing):
    widths = [max(len(table[row][col])
                  for row in xrange(len(table)))
              for col in xrange(len(table[0]))]
    print "\n".join(spacing.join({'l': "%-*s", 'r': "%*s"}[a] % (w, s)
                                 for (s, w, a) in zip(trow, widths,
                                                      alignments))
                    for trow in table)

def print_time_cmd(cpu, steps = False, cycles = False, all = False):
    if all:
        if steps or cycles:
            print "The -s and -c flags cannot be used with -all."
            SIM_command_has_problem()
            return
        cpus = []
        next = SIM_next_queue(None)
        while next:
            cpus.append(next)
            next = SIM_next_queue(next)
    elif cpu:
        cpus = [cpu]
    else:
        cpus = [current_processor()]

    if steps and cycles:
        print "The -s and -c flags cannot be used at the same time."
        SIM_command_has_problem()
        return
    elif steps:
        return SIM_step_count(cpus[0])
    elif cycles:
        return SIM_cycle_count(cpus[0])        

    print_table([["processor", "steps", "cycles", "time [s]"]]
                + [[cpu.name,
                    number_str(SIM_step_count(cpu), 10),
                    number_str(SIM_cycle_count(cpu), 10),
                    "%.3f" % SIM_time(cpu)]
                   for cpu in cpus],
                ["l", "r", "r", "r"], "  ")

for ns in ("", "processor"):
    new_command("print-time", print_time_cmd,
                {"": [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
                      arg(flag_t, "-s"),
                      arg(flag_t, "-c"),
                      arg(flag_t, "-all")],
                 "processor": [ arg(flag_t, "-s"),
                                arg(flag_t, "-c")]}[ns],
                namespace = ns,
                alias = "ptime",
                type  = ["Execution", "Profiling"],
                short = "print number of steps and cycles executed",
                repeat = print_time_cmd,
                doc = """

Prints the number of steps and cycles that a processor has executed.
The cycle count is also displayed as simulated time in seconds.

If called from a processor namespace (e.g., <i>cpu0</i><tt>.print-time</tt>),
the time for that processor is printed. Otherwise, the time for the
current processor is printed, or, if the <arg>-all</arg> flag is
given, the time for all processors.

if the <arg>-c</arg> flag used, the cycle count for the processor is returned
and nothing is printed. The <arg>-s</arg> flag is similar and returns the
step count.

A step is a completed instruction or an exception. An instruction that
fails to complete because of an exception will count as a single step,
including the exception.

""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="156")


#
# -------------------- penable --------------------
#

def penable_cmd(poly): # flag_t or obj_t
    if not poly:
        penable_cmd((obj_t, current_processor()))
    elif poly[0] == flag_t: # -all
        limit = SIM_number_processors()
        for i in range(limit):
            penable_cmd((obj_t, SIM_get_processor(i)))
    else:
        cpu = poly[1]
        try:
            SIM_enable_processor(cpu)
            print "Enabling processor", cpu.name
        except Exception, msg:
            print "Failed enabling processor.", msg

new_command("penable", penable_cmd,
            [arg((obj_t('processor', 'processor'), flag_t),
                 ("cpu-name", "-all"), "?")],
            type = ["Execution", "Changing Simulated State"],
            short = "switch processor on",
            doc = """
Enables a processor. If no processor is specified, the current processor will
be enabled. If the flag <arg>-all</arg> is passed, all processors will be
enabled.

<b>pdisable</b> takes processor as parameter. If no processor is
given, it will list all enabled processors. The method variant can also be used
to disable a processor. A disabled processor is simply stalled for an infinite
amount of time. Make sure that you always have at least one enabled processor.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="208")


def obj_enable_cmd(obj):
    try:
        SIM_enable_processor(obj)
        print "Enabling processor", obj.name
    except Exception, msg:
        print "Failed enabling processor.", msg    

new_command("enable", obj_enable_cmd,
            [],
            namespace = "processor",
            short = "switch processor on",
            doc_with = "penable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="232")

#
# -------------------- pdisable --------------------
#

def pdisable_cmd(poly):
    if not poly:
        pdisable_cmd((obj_t, current_processor()))
    elif poly[0] == flag_t: # -all
        limit = SIM_number_processors()
        for i in range(limit):
            pdisable_cmd((obj_t, SIM_get_processor(i)))
    else:
        cpu = poly[1]
        try:
            SIM_disable_processor(cpu)
            print "Disabling processor", cpu.name
        except Exception, msg:
            print "Failed disabling processor.", msg

new_command("pdisable", pdisable_cmd,
            [arg((obj_t('processor', 'processor'), flag_t),
                 ("cpu-name", "-all"), "?")],
            alias = "",
            short = "switch processor off",
            doc_with = "penable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="257")

def obj_disable_cmd(obj):
    try:
        SIM_disable_processor(obj)
        print "Disabling processor", obj.name
    except Exception, msg:
        print "Failed disabling processor.", msg

new_command("disable", obj_disable_cmd,
            [],
            namespace = "processor",
            short = "switch processor off",
            doc_with = "penable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="271")

#
# -------------------- pstatus --------------------
#

def pstatus_cmd():
    list_processors()
    
new_command("pstatus", pstatus_cmd,
            [],
            alias = "",
            type = ["Execution", "Inspecting Simulated State"],
            short = "show processors' status",
            doc = """
Show the enabled/disabled status of all processors in the Simics session.
            """, filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="284")

#
# -------------------------- memory profiling --------------------------
#

def supports_mem_profiling(cpu):
    try:
        cpu.memory_profilers
    except:
        print "%s does not support memory read/write profiling." % cpu.name
        return 0
    return 1

cpu_mem_prof_type = {"read"  : Sim_RW_Read,
                     "write" : Sim_RW_Write}
def cpu_mem_prof_type_expander(string):
    return get_completions(string, cpu_mem_prof_type.keys())
def print_valid_mem_prof_types():
    print "Valid types are: %s" % ", ".join(cpu_mem_prof_type.keys())

def add_memory_profiler_cmd(cpu, type, obj):
    if not supports_mem_profiling(cpu):
        return

    try:
        i = cpu_mem_prof_type[type]
    except:
        print "'%s' is not a valid profiler type." % type
        print_valid_mem_prof_types()
        return

    if cpu.memory_profilers[i]:
        print ("There is an active profiler for memory %s already: %s"
               % (type, cpu.memory_profilers[i].name))
        return

    if obj:
        cpu.memory_profilers[i] = obj
    else:
        # create a new profiler
        name = "%s_%s_mem_prof" % (cpu.name, type)
        try:
            prof = SIM_get_object(name)
            cpu.memory_profilers[i] = prof
            print ("[%s] Existing profiler added for memory %s: %s"
                   % (cpu.name, type, name))
        except:
            try:
                gran = cpu.memory_profiling_granularity_log2
                desc = "data profiler"
                prof = SIM_create_object('data-profiler', name,
                                         [['description', desc],
                                          ['granularity', gran],
                                          ['physical_addresses', 1]])
                cpu.memory_profilers[i] = prof
                print ("[%s] New profiler added for memory %s: %s"
                       % (cpu.name, type, name))
            except:
                print "Could not add memory profiler."

def remove_memory_profiler_cmd(cpu, type):
    if not supports_mem_profiling(cpu):
        return

    try:
        cpu.memory_profilers[cpu_mem_prof_type[type]] = None
    except:
        print "'%s' is not a valid profiler type." % type
        print_valid_mem_prof_types()

def list_memory_profilers_cmd(cpu):
    if not supports_mem_profiling(cpu):
        return

    for t in cpu_mem_prof_type.keys():
        try:
            name = cpu.memory_profilers[cpu_mem_prof_type[t]].name
        except:
            name = ""
        print "%20s: %s" % (t, name)

new_command("add-memory-profiler", add_memory_profiler_cmd,
            [arg(str_t, "type", expander = cpu_mem_prof_type_expander),
             arg(obj_t("data-profiler", "data-profiler"), "profiler", "?")],
            namespace = "processor",
            type  = ["Memory", "Profiling"],
            short="add a memory profiler to the processor",
            doc  = """
Add a data profiler to the specified processor that will record either
reads or writes to memory (indexed on physical address) depending on
whether the <tt>type</tt> argument is 'read' or 'write'. An existing
data profiler may be specified with the <tt>profiler</tt> argument;
otherwise, a new data profiler will be created.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="373")

new_command("remove-memory-profiler", remove_memory_profiler_cmd,
            [arg(str_t, "type", expander = cpu_mem_prof_type_expander)],
            namespace = "processor",
            type  = ["Memory", "Profiling"],
            short="remove a memory profiler from the processor",
            doc  = """
Remove any memory profiler of the specified <tt>type</tt> ('read' or
'write') currently attached to the processor.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="386")

new_command("list-memory-profilers", list_memory_profilers_cmd,
            [],
            namespace = "processor",
            type  = ["Memory", "Profiling"],
            short="list memory profilers connected to the processor",
            doc  = """
List all memory profilers connected to the processor, and what kind of
data they are collecting.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="395")

#
# -------------------- pstats --------------------
#

def all_processors():
    return filter(SIM_object_is_processor, SIM_get_all_objects())

def print_stat_per_cpu(cpu):
    pr("\nStatistics for cpu %s\n" % cpu.name);

    pr("       User  Supervisor       Total  Description\n");
    elided = 0
    for (name, uval, sval) in cpu.mode_counters:
        if uval or sval:
            pr("%11d %11d %11d  %s\n" % (uval, sval, uval + sval, name))
        else:
            elided = 1
    
    if elided:
        pr("\n(counters whose values are all zero were not displayed)\n")

def pstats_cmd(args):
    if args[0] == flag_t:
        for c in all_processors():
            print_stat_per_cpu(c)
    else:
        cpu = args[1]
        if not cpu:
            cpu, _ = get_cpu()
        print_stat_per_cpu(cpu)

def obj_pstats_cmd(obj):
    pstats_cmd((obj_t, obj))

new_command("print-statistics", pstats_cmd,
            [arg((obj_t('processor', 'processor'), flag_t), ("cpu-name","-all"), "?",
                 (obj_t,None), expander = (cpu_expander,0))],
            type  = ["Profiling"],
            alias = "pstats",
            short = "print various statistics",
            doc = """
Prints various statistics from the simulation. The <b>print-statistics</b>
command prints statistics for the currently selected CPU if no argument
is given and for all CPUs if the -all flag given.
Any statistics that have been compiled into the
simulator are printed, as well as user-defined per-mode counters.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="438")

new_command("print-statistics", obj_pstats_cmd,
            [],
            short = "print various statistics",
            namespace = "processor",
            doc_with = "print-statistics", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="451")

#
# -------------------- step-break-absolute, step-break --------------------
#

def sim_break_absolute_cmd(cpu, cycles):
    if not cpu:
        (cpu, _) = get_cpu()
    sim_break_cmd(cpu, cycles - SIM_step_count(cpu))

def sim_break_cmd(cpu, cycles):
    if (cycles < 0):
        print "Cannot break on negative time"
        return
    if not cpu:
        (cpu, _) = get_cpu()
    SIM_break_step(cpu, cycles)

new_command("step-break-absolute", sim_break_absolute_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(int_t, "instructions")],
            alias = ["sba", "sim-break-absolute"],
            type = ["Execution", "Breakpoints", "Debugging"],
            short = "set absolute time breakpoint",
            group_short = "set step breakpoints",
            namespace_copy = ("processor", sim_break_absolute_cmd),
            see_also = ["step-break-absolute", "cycle-break", "cycle-break-absolute", "list-breakpoints"],
            doc = """
Set a breakpoint so that the selected CPU will stop after its step counter has
reached the <i>instructions</i> value. If the CPU is not specified the selected
frontend processor will be used (see <b>pselect</b>).

To list all breakpoints set use the command <b>list-breakpoints</b>.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="474")

new_command("step-break", sim_break_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(int_t, "instructions")],
            alias = ["sb", "sim-break"],
            short = "set time breakpoint",
            namespace_copy = ("processor", sim_break_cmd),
            see_also = ["step-break-absolute", "cycle-break", "cycle-break-absolute", "list-breakpoints"],
            doc = """
Sets a breakpoint so that the CPU will stop after executing <i>instructions</i>
number of steps from the time the command was issued. If the CPU is not
specified the selected frontend processor will be used (see <b>pselect</b>).

To list all breakpoints set use the command <b>list-breakpoints</b>.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="491")

def cycle_break_absolute_cmd(cpu, cycles):
    if not cpu:
        (cpu, _) = get_cpu()
    if (cycles < SIM_cycle_count(cpu)):
        print "Cannot break on negative time"
        return
    SIM_break_cycle(cpu, cycles - SIM_cycle_count(cpu))

def cycle_break_cmd(cpu, cycles):
    if not cpu:
        (cpu, _) = get_cpu()
    if (cycles < 0):
        print "Cannot break on negative time"
        return
    SIM_break_cycle(cpu, cycles)

new_command("cycle-break-absolute", cycle_break_absolute_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(int_t, "cycles")],
            alias = "cba",
            type = ["Execution", "Breakpoints", "Debugging"],
            short = "set absolute cycle breakpoint",
            namespace_copy = ("processor", cycle_break_absolute_cmd),
            see_also = ["cycle-break", "step-break", "step-break-absolute", "list-breakpoints"],
            doc = """
Set a breakpoint so that the selected CPU will stop after its cycle counter has
reached the <i>cycles</i> value. If the CPU is not specified the selected
frontend processor will be used (see <b>pselect</b>).

To list all breakpoints set use the command <b>list-breakpoints</b>.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="522")

new_command("cycle-break", cycle_break_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(int_t, "cycles")],
            alias = "cb",
            short = "set cycle breakpoint",
            namespace_copy = ("processor", cycle_break_cmd),
            see_also = ["cycle-break-absolute", "step-break", "step-break-absolute", "list-breakpoints"],
            doc = """
Sets a breakpoint so that the CPU will stop after running <i>cycles</i>
number of cycles from the time the command was issued. If the CPU is not
specified the selected frontend processor will be used (see <b>pselect</b>).

To list all breakpoints set use the command <b>list-breakpoints</b>.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="538")


#
# -------------------- run --------------------
#

_do_disassemble = 0
_do_register_trace = 0

hit_user_breakpoint = 0
user_run_continuation = None

def user_continue2(dummy):
    global _do_disassemble, _do_register_trace
    _do_disassemble = 1
    _do_register_trace = 0
    _started_sim()
    SIM_continue(0)

def user_continue():
    global hit_user_breakpoint, _do_disassemble, _do_register_trace

    hit_user_breakpoint = 0
    if conf.python.iface.python.in_main_branch() and SIM_postponing_continue():
        SIM_post_command(user_continue2, None)
    else:
        _do_disassemble = 1
        _do_register_trace = 0
        try:
            _started_sim()
            SIM_continue(0)
        except:
            pass

_sim_stop_handler_id = None
_sim_btof_message = None

def _started_sim():
    global _sim_stop_handler_id

    if _sim_stop_handler_id == None:
        _sim_stop_handler_id = SIM_hap_add_callback("Core_Simulation_Stopped",
                                                    simulation_stopped_handler,
                                                    None)

def simulation_stopped_handler(arg, obj, exc, str):
    global hit_user_breakpoint, user_run_continuation, _do_disassemble
    global _sim_stop_handler_id

    SIM_hap_delete_callback_id("Core_Simulation_Stopped", _sim_stop_handler_id)
    _sim_stop_handler_id = None

    SIM_step_clean(current_processor(), user_time_stop, None)
    SIM_time_clean(current_processor(), Sim_Sync_Processor,
                   user_time_stop, None)
    if hit_user_breakpoint and user_run_continuation != None:
        user_run_continuation()

def back_to_front_dis_handler(arg, obj):
    global _do_disassemble, _sim_btof_message

    if _sim_btof_message and _sim_btof_message != "Received control-c":
        print _sim_btof_message
        _sim_btof_message = None

    if _do_disassemble:
        disassemble_at_prompt()
        _do_disassemble = 0

    check_display_output()

SIM_hap_add_callback("Core_Back_To_Front", back_to_front_dis_handler, None)

old_regs = {}

def disassemble_at_prompt(*dummy):
    global old_regs, _do_register_trace
    new_proc = SIM_current_processor()
    if _do_register_trace:
        try:
            old_regs_cpu = old_regs[new_proc]
        except KeyError, msg:
            old_regs[new_proc] = {}
        else:
            try:
                diff_regs = get_obj_funcs(new_proc)['diff_regs']
            except KeyError, msg:
                pass
            else:
                if callable(diff_regs):
                    diff_regs = diff_regs(new_proc)
                for r in SIM_get_all_registers(new_proc):
                    if SIM_get_register_name(new_proc, r) in diff_regs:
                        new_val = SIM_read_register(new_proc, r)
                        try:
                            old_val = old_regs_cpu[r]
                        except KeyError, msg:
                            old_regs[new_proc][r] = new_val
                        else:
                            if new_val != old_val:
                                old_regs[new_proc][r] = new_val
                                print "\t%s <- %s" % (SIM_get_register_name(new_proc, r), number_str(new_val))
    try:
        pending_exception_func = get_obj_funcs(new_proc)['get_pending_exception_string']
        pending_exception = pending_exception_func(new_proc)
    except KeyError:
        pending_exception = None
    if pending_exception != None:
        local_print_disassemble_line(new_proc, SIM_get_program_counter(new_proc), 1, 1, pending_exception)
    else:
        local_print_disassemble_line(new_proc, SIM_get_program_counter(new_proc), 1)

    if new_proc != current_processor():
        set_current_processor(new_proc)
        print "Setting new inspection cpu: %s" % new_proc.name

def user_time_stop(cpu, dummy):
    global hit_user_breakpoint

    hit_user_breakpoint = 1
    raise SimExc_Break, "hit time breakpoint"

def run_cmd(count):
    global user_run_continuation

    assert_stopped()

    if count > 0:
        SIM_step_post(current_processor(), count, user_time_stop, None)
    user_run_continuation = None
    user_continue()

new_command("run", run_cmd,
            [arg(uint64_t, "count", "?", 0)],
            alias = ["continue", "c", "r"],
            type = ["Execution"],
            repeat = run_cmd,
            short = "start execution",
            see_also = ["step-instruction", "run-cycles"],
            doc = """
Tells Simics to start or continue executing instructions. If a <arg>count</arg>
argument is provided, Simics will execute <arg>count</arg> number of
instructions and stop.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="684")

def run_cycles_cmd(count):
    global user_run_continuation

    assert_stopped()

    if count > 0:
        SIM_time_post_cycle(current_processor(), count, Sim_Sync_Processor, user_time_stop, None)
    user_run_continuation = None
    user_continue()

new_command("run-cycles", run_cycles_cmd,
            [arg(uint64_t, "count", "?", 0)],
            alias = ["continue-cycles", "cc", "rc"],
            type = ["Execution"],
            see_also = ["step-cycle", "run"],
            repeat = run_cycles_cmd,
            short = "start execution",
            doc = """
Tells Simics to start or continue executing instructions. If a <arg>count</arg>
argument is provided, Simics will execute <arg>count</arg> number of cycles and
stop. Note that running <arg>count</arg> cycles may or may not be equivalent to
running <arg>count</arg> instructions depending on the way Simics is
configured. Refer to the chapter Understanding Simics Timing in the Simics User
Guide for more information.
            """, filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="707")

def stop_cmd(all, msg):
    VT_user_interrupt(msg, all)
    if not conf.python.iface.python.in_main_branch():
        wait_for_hap("Core_Simulation_Stopped")

new_command("stop", stop_cmd,
            [arg(flag_t, "-a"),
             arg(str_t, "message", "?", None)],
            type = ["Execution"],
            repeat = stop_cmd,
            short = "interrupt simulation",
            see_also = ["run"],
            doc = """
Stop simulation as soon as possible. If the <param>-a</param> argument is
give, any command script running will also be interrupted. A
<param>message</param> to be printed on the console when the simulation stops
can also be specified.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="728")

#
# -------------------- stepi --------------------
#

stepi_count = 0

def stepi_continuation():
    global stepi_count, _do_disassemble, _do_register_trace

    stepi_count = stepi_count - 1
    if stepi_count <= 0:
        return

    if _do_disassemble:
        disassemble_at_prompt()
        _do_disassemble = 0
    run_stepi(0)

def run_stepi(register_trace):
    global stepi_count, user_run_continuation, _do_disassemble, _do_register_trace
    global old_regs

    cpu = current_processor()
    SIM_step_post(cpu, 1, user_time_stop, None)
    if SIM_postponing_continue():
        user_run_continuation = stepi_continuation
        user_continue()
        return

    while 1:
        _do_disassemble = 1
        _do_register_trace = register_trace
        if register_trace:
            old_regs[cpu] = {}
            for r in SIM_get_all_registers(current_processor()):
                old_regs[cpu][r] = SIM_read_register(cpu, r)
        try:
            _started_sim()
            SIM_continue(0)
        except:
            return
        stepi_count = stepi_count - 1
        if stepi_count <= 0:
            return
        disassemble_at_prompt()
        SIM_step_post(cpu, 1, user_time_stop, None)

def stepi_cmd(count, r):
    global stepi_count

    assert_stopped()

    stepi_count = count

    run_stepi(r)

new_command("step-instruction", stepi_cmd,
            [arg(uint64_t, "count", "?", 1), arg(flag_t, "-r")],
            alias = [ "si", "stepi" ],
            type = ["Execution"],
            short = "step one or more instructions",
            repeat = stepi_cmd,
            see_also = ["run", "step-cycle", "step-cycle-single"],
            doc = """
Executes <arg>count</arg> instructions, printing the next instruction to be
executed at each step. <arg>count</arg> defaults to one. With the <arg>-r</arg>
flag, register changes will also be printed.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="797")

#
# -------------------- step-cycle --------------------
#

stepc_count = 0

def stepc_continuation():
    global stepc_count, _do_disassemble, _do_register_trace

    stepc_count = stepc_count - 1
    if stepc_count <= 0:
        return

    _do_register_trace = 0
    if _do_disassemble:
        disassemble_at_prompt()
        _do_disassemble = 0
    run_stepc()

def run_stepc(*dummy):
    global stepc_count, user_run_continuation, _do_disassemble, _do_register_trace

    SIM_time_post_cycle(current_processor(), 1, Sim_Sync_Processor, user_time_stop, None)
    if SIM_postponing_continue():
        user_run_continuation = stepc_continuation
        user_continue()
        return

    while 1:
        _do_disassemble = 1
        _do_register_trace = 0
        try:
            _started_sim()
            SIM_continue(0)
        except:
            return
        stepc_count = stepc_count - 1
        if stepc_count <= 0:
            return
        disassemble_at_prompt()
        SIM_time_post_cycle(current_processor(), 1, Sim_Sync_Processor, user_time_stop, None)

def step_cycle_cmd(count):
    global stepc_count

    assert_stopped()

    stepc_count = count

    run_stepc()

new_command("step-cycle", step_cycle_cmd,
            [arg(int_t, "count", "?", 1)],
            alias = "sc",
            type = ["Execution"],
            repeat = step_cycle_cmd,
            see_also = ["step-cycle-single", "run", "step-instruction"],
            short = "step one or more cycles",
            doc = """
Executes <arg>count</arg> cycles, printing the next instruction to be executed
at each cycle. <arg>count</arg> defaults to one.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="861")

def step_cycle_single_handler(cpu, dummy):
   raise SimExc_Break, "hit time breakpoint"

def step_cycle_single_cmd(disass):
    global number_of_processors
    number_of_processors = 0

    assert_stopped()

    proc = SIM_current_processor()

    if proc.ooo_mode != 'micro-architecture':
        print "This command is only available in Micro Architecture Mode"
        return
    
    SIM_time_post_cycle(proc, 0, Sim_Sync_Processor, step_cycle_single_handler, None)

    SIM_continue(0)

    new = SIM_current_processor()
    
    if proc != new:
        set_current_processor(new)
        if not disass:
            local_print_disassemble_line(new, SIM_get_program_counter(new), 1)


new_command("step-cycle-single", step_cycle_single_cmd,
            [arg(flag_t, "-n")],
            alias = "scs",
            type = ["Execution"],
            repeat = step_cycle_single_cmd,
            see_also = ["step-cycle", "step-instruction", "run"],
            short = "step one cycle and switch to the next cpu",
            doc = """
Used with the Micro Architectural Interface only. <cmd>step-cycle-single</cmd>
executes one cycle on the current processor, switches to the next processor and
prints the next instruction to be committed. Repeated use will thus advance
each processor in a round robin fashion. <arg>-n</arg> will prevent
<cmd>step-cycle-single</cmd> from printing the next instruction after
executing.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="900")

#
# -------------------- pselect --------------------
#

def pselect_cmd(cpu):
    if not cpu:
        try:
            cpu, name = get_cpu()
            print "Currently selected processor is", name
        except:
            print "There are no processors available"
    else:
        set_current_processor(cpu)


new_command("pselect", pselect_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?")],
            alias = "psel",
            type = ["Command-Line Interface"],
            short = "select a processor",
            doc = """
Use this command to select a default processor for the frontend. Many
commands that have a processor as argument operates on the default
processor when the argument is left out. Note that selecting
processors does not affect in which order they are executed when
multiprocessing is simulated.

Without any argument, this command will print the currently selected
processor.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="931")

#
# -------------------- print-event-queue --------------------
#

def print_event_queue_cmd(cpu, queue, internal):
    if not cpu:
        (cpu, _) = get_cpu()

    def print_queue(q):
        i = 0
        for (obj, desc, time) in cpu.event_desc[q]:
            if not internal and desc.startswith("Internal:"):
                continue
            if obj:
                desc = "[" + obj.name + "] " + desc
            print "%3d :%15s : %s" % (i, number_str(time, 10), desc)
            i += 1

    if queue >= 0:
        if queue > 1:
            print "No queue", queue, "defined."
            return
        print_queue(queue)
    else:
        print "Event          Steps   Description"
        print_queue(Sim_Queue_Step)
        print
        print "Event           Time   Description"
        print_queue(Sim_Queue_Time)

new_command("print-event-queue", print_event_queue_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(int_t, "queue", "?", -1),
             arg(flag_t, "-i")],
            alias = "peq",
            type = ["Inspecting Simulated State"],
            short = "print event queue for processor",
            doc = """
The simulator keeps an event queue for each processor. Interrupts,
exceptions, and other events are posted on this event queue. For each event,
the time to its execution and a brief description of it are printed.
The time unit depends on the timing model of the queue; the default is
the number of instructions before the event is trigged.
If no CPU is specified, the selected frontend CPU is used.
A <i>queue</i> argument of 0 means that only the step queue is printed,
and for 1, only the time queue. Default is to print both queues.
The flag -i enables printing of Simics internal events.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="977")

#
# -------------------- break, tbreak --------------------
#

def do_break(object, t, address, length, r, w, x, temp):
    if length < 1:
        print "The breakpoint length must be >= 1 bytes."
        return

    access = 0
    mode = ""

    if r: access = access | Sim_Access_Read; mode = mode + "r"
    if w: access = access | Sim_Access_Write; mode = mode + "w"
    if x or access == 0:
        access = access | Sim_Access_Execute
        mode = mode + "x"

    id = SIM_breakpoint(object, t, access, address, length, temp)

    if temp:
        pr("Temporary breakpoint ")
    else:
        pr("Breakpoint ")

    pr(`id` + " set on address " + number_str(address, 16))
    if length > 1:
        pr(", length " + number_str(length, 10))
    pr(" with access mode '" + mode + "'\n")

    bp_list = conf.sim.breakpoints[:]
    for i in range(len(bp_list)):
        obj = bp_list[i][11]
        if obj == object:
            try:
                r = SIM_get_attribute_idx(obj, "breakpoints", i+1)
                if i+1 != id and address <= r[2] and address+length-1 >= r[1]:
                    print "Note: overlaps with breakpoint", r[0]
            except:
                pass
    return (id,)

def break_cmd(object, address, len, r, w, x):
    break_type = Sim_Break_Physical
    if object.classname == "context":
        break_type = Sim_Break_Virtual
    return do_break(object, break_type, address, len, r, w, x, 0)

new_command("break", break_cmd,
            [arg(uint64_t, "address"),
             arg(uint64_t, "length", "?", 1),
             arg(flag_t, "-r"), arg(flag_t, "-w"), arg(flag_t, "-x")],
            namespace = "breakpoint",
            type = ["Breakpoints", "Debugging"],
            short="set breakpoint",
            see_also = ["unbreak", "delete", "enable", "ignore", "set-prefix",
                        "set-substr", "set-pattern", "list-breakpoints"],
            doc  = """

Add breakpoint (read, write, or execute) on an object implementing the
breakpoint interface. This is typically a memory space object such as
physical memory; e.g., <cmd>phys_mem0.break 0xff3800</cmd>. Accesses
intersecting the given range will trigger the breakpoint. By default
the breakpoint will only trigger for instruction execution, but any
subset of read, write, and execute accesses can be set to trigger
using combinations of <arg>-r</arg>, <arg>-w</arg>, and <arg>-x</arg>.

<arg>length</arg> is the interval length in bytes (default is 1).

Breakpoints inserted with the <cmd>tbreak</cmd> command are
automatically disabled when they have triggered.

The default action at a triggered breakpoint is to return to the
frontend. This can be changed by using haps. When an execution
breakpoint is triggered, Simics will return to the command prompt
before the instructions is executed, while instructions triggering
read or write breakpoints will complete before control is returned to
the command prompt.

To break on a virtual address, use a context object:

<cmd>primary_context.break 0x1ff00</cmd>

Several breakpoints can be set on the same address and Simics will
break on them in turn. If hap handlers (callback functions) are
connected to the breakpoints they will also be executed in turn. Hap
handlers are called before the access is performed, allowing the user
to read a memory value that may be overwritten by the access. See the
Simics Reference Manual for a description of hap handlers.

Each breakpoint is associated with an id (printed when the breakpoint
is set or by the <cmd>list-breakpoints</cmd> command) which is used
for further references to the breakpoint.

For convenience there are also a <cmd>break</cmd> command which sets a
breakpoint on memory connected to the current frontend CPU (see
<cmd>pselect</cmd>). Default is to break on virtual address accesses
(in the current context). By prefixing the address with <arg>p:</arg>
it is possible to break on physical accesses as well (cf.
<cmd>phys_mem0.break</cmd>); e.g., <cmd>break p:0xffc0</cmd>.

Several attributes can be set for a breakpoint for breaking only when
some conditions are true. See the <cmd>disable</cmd>,
<cmd>enable</cmd>, <cmd>ignore</cmd>, <cmd>set-prefix</cmd>,
<cmd>set-substr</cmd> and <cmd>set-pattern</cmd> commands for more
details.

Breakpoints can be removed using <cmd>delete</cmd>.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1043")

def tbreak_cmd(object, address, len, r, w, x):
    break_type = Sim_Break_Physical
    if object.classname == "context":
        break_type = Sim_Break_Virtual
    else:
        break_type = Sim_Break_Physical
    return do_break(object, break_type, address, len, r, w, x, 1)

new_command("tbreak", tbreak_cmd,
            [arg(int_t, "address"), arg(int_t, "length", "?", 1),
             arg(flag_t, "-r"), arg(flag_t, "-w"), arg(flag_t, "-x")],
            namespace = "breakpoint",
            short="set temporary breakpoint on current processor",
            doc_with = "<breakpoint>.break", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1112")

def classic_break_cmd(address, len, r, w, x):
    if address[0] == "p":
        obj = current_processor().physical_memory
        kind = Sim_Break_Physical
    else:
        obj = current_processor().current_context
        if address[0] == "l":
            kind = Sim_Break_Linear
        else:
            kind = Sim_Break_Virtual
    return do_break(obj, kind, address[1], len, r, w, x, 0)

new_command("break", classic_break_cmd,
            [arg(addr_t, "address"), arg(uint64_t, "length", "?", 1),
             arg(flag_t, "-r"), arg(flag_t, "-w"), arg(flag_t, "-x")],
            alias = "b",
            short="set breakpoint on current processor",
            doc_with = "<breakpoint>.break", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1131")

#
# -------------------- unbreak --------------------
#

_removed_breakpoint = 0

def _remove_breakpoint(id, address, length, access):
    bp = conf.sim.breakpoints[id]
    if not bp or bp[6] & (Sim_Breakpoint_Simulation | Sim_Breakpoint_Private):
        return

    _removed_breakpoint = 1
    try:
        SIM_breakpoint_remove(id, access, address, length)
    except SimExc_General, msg:
        print msg
    
def unbreak_cmd(poly, address, length, r, w, x):
    global _removed_breakpoint

    _removed_breakpoint = 0

    access = 0
    if r: access = access | Sim_Access_Read
    if w: access = access | Sim_Access_Write
    if x or access == 0:
        access = access | Sim_Access_Execute

    if poly[0] == int_t:
        id = poly[1]
    	bp = conf.sim.breakpoints[id]
	if not bp or bp[6] & (Sim_Breakpoint_Simulation | Sim_Breakpoint_Private):
	    print "Cannot change simulation internal breakpoints."
	    return
    	_remove_breakpoint(id, address, length, access)
    else:
        for bp in conf.sim.breakpoints[:]:
            _remove_breakpoint(bp[0], address, length, access)

new_command("unbreak", unbreak_cmd,
            [arg((int_t,flag_t), ("id","-all")), arg(int_t, "address"), arg(int_t, "length"),
             arg(flag_t, "-r"),arg(flag_t, "-w"), arg(flag_t, "-x")],
            type  = ["Breakpoints", "Debugging"],
            short = "remove breakpoint range",
            see_also = ['<breakpoint>.break', 'delete'],
            doc = """
            
Removes an address range from a breakpoint, splitting the breakpoint if
necessary. <arg>-r</arg> (read), <arg>-w</arg> (write) and <arg>-x</arg>
(execute) specify the type of breakpoint that should be removed in the given
address range. It defaults to <em>execute</em> if no flag is
given. <arg>id</arg> is the id number of the breakpoint to operate on. To
operate on all breakpoints at once, use the <arg>-all</arg>
flag. <cmd>list-breakpoints</cmd> prints all breakpoints' id.

""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1177")

#
# -------------------- delete --------------------
#

# get breakpoint id from integer or flag
def get_id(poly):
    if poly[0] == flag_t:
        id = 0l
    else:
        id = poly[1]
    return id

def delete_cmd(poly):
    id = get_id(poly)
    if id:
        bp = conf.sim.breakpoints[id]
        if bp and bp[6] & (Sim_Breakpoint_Simulation | Sim_Breakpoint_Private):
            print "Cannot remove simulation internal breakpoints."
            return
    try:
        SIM_delete_breakpoint(id) # 0 deletes all
    except Exception, msg:
        print msg

new_command("delete", delete_cmd,
            [arg((flag_t,int_t), ("-all", "id"))],
            type  = ["Breakpoints", "Debugging"],
            short = "remove a breakpoint",
            see_also = ['<breakpoint>.break', 'enable', 'ignore', 'set-prefix', 'set-substr', 'set-pattern', 'list-breakpoints'],
            doc = """
Removes a breakpoint. <i>id</i> is the id of the breakpoint to delete. Use
<cmd>list-breakpoints</cmd> to list all breakpoints' id. If the flag
<arg>-all</arg> is given, all breakpoints will be deleted.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1219")

#
# -------------------- enable, disable --------------------
#

def enable_disable_cmd(poly, val):
    id = get_id(poly)
    try:
        if id == 0:
            bps = conf.sim.breakpoints[:]
            for i in range(len(bps)):
                bps[i][5] = val
                conf.sim.breakpoints[bps[i][0]] = bps[i]
        else:
            bp = SIM_get_attribute_idx(conf.sim, "breakpoints", id)
            bp[5] = val
            SIM_set_attribute_idx(conf.sim, "breakpoints", id, bp)
    except Exception, msg:
        print msg

def enable_cmd(poly):
    enable_disable_cmd(poly, 1)

def disable_cmd(poly):
    enable_disable_cmd(poly, 0)

new_command("enable", enable_cmd,
            [arg((flag_t,int_t), ("-all", "id"))],
            type  = ["Breakpoints", "Debugging"],
            short = "enable/disable breakpoint",
            see_also = ['<breakpoint>.break', 'delete', 'ignore', 'list-breakpoints'],
            doc = """
Enable/disable instruction breakpoint.  <i>id</i> is id number of the
breakpoint to enable/disable. Use <b>list-breakpoints</b> to list
breakpoint id:s. If '-all' is given all breakpoints will be
enabled/disabled. Simics will not stop on a disabled breakpoint,
however Simics will still count it.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1255")

new_command("disable", disable_cmd,
            [arg((flag_t,int_t), ("-all", "id"))],
            short = "enable/disable breakpoint",
            doc_with = "enable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1267")

#
# -------------------- ignore --------------------
#

def ignore_cmd(id, num):
    try:
        bp = SIM_get_attribute_idx(conf.sim, "breakpoints", id)
        # activate_at = hits + num + 1
        bp[4] = bp[3] + num + 1
        bp[5] = 0
        SIM_set_attribute_idx(conf.sim, "breakpoints", id, bp)
    except Exception, msg:
        print msg

new_command("ignore", ignore_cmd,
            [arg(int_t, "id"), arg(int_t, "num")],
            type  = ["Breakpoints", "Debugging"],
            short = "set ignore count for a breakpoint",
            see_also = ['enable', 'list-breakpoints'],
            doc = """
Sets the ignore count for a breakpoint. This means that the next <i>num</i>
times the breakpoint is reached it will not trigger (hap handlers will
not be called). To break next time set <i>num</i> to 0.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1286")

#
# -------------------- set-prefix --------------------
#

def set_prefix_cmd(id, prefix):
    try:
        bp = SIM_get_attribute_idx(conf.sim, "breakpoints", id)
        if not (bp[2] & 4):
            print "This can only be applied to execution breakpoints (access type x)."
            return
        bp[7] = prefix
        SIM_set_attribute_idx(conf.sim, "breakpoints", id, bp)
    except Exception, msg:
        print msg

new_command("set-prefix", set_prefix_cmd,
            [arg(int_t, "id"), arg(str_t, "prefix")],
            type  = ["Breakpoints", "Debugging"],
            short = "set a syntax prefix for a breakpoint",
            doc_items = [('Note', 'Only supported for execution breakpoints.')],
            see_also = ['set-substr', 'set-pattern'],
            doc = """
Set a syntax prefix for a breakpoint. When set Simics will only break
on instructions with a certain syntax prefix. For example <b>set-prefix</b> 1
"add" will cause breakpoint 1 only to stop if the instruction begins
with "add". The text to compare the prefix with for an instruction is
the one which the instruction is disassembled to.

Set prefix to the empty string ("") to remove this extra condition.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1311")

#
# -------------------- set-substr --------------------
#

def set_substr_cmd(id, substr):
    try:
        bp = SIM_get_attribute_idx(conf.sim, "breakpoints", id)
        if not (bp[2] & 4):
            print "This can only be applied to execution breakpoints (access type x)."
            return
        bp[8] = substr
        SIM_set_attribute_idx(conf.sim, "breakpoints", id, bp)
    except Exception, msg:
        print msg

new_command("set-substr", set_substr_cmd,
            [arg(int_t, "id"), arg(str_t, "substr")],
            type  = ["Breakpoints", "Debugging"],
            short = "set a syntax substring for a breakpoint",
            doc_items = [('NOTE', 'Only supported for execution breakpoints.')],
            see_also = ['set-prefix', 'set-pattern'],
            doc = """
When set Simics will only break on instructions with a certain syntax
substring. For example <b>set-substr</b> 1 "r31" will make breakpoint 1 only
stop if the instruction has a substring "r31".

Set sub-string to the empty string ("") to remove this extra condition.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1341")


#
# -------------------- set-pattern --------------------
#

def set_pattern_cmd(id, pattern, mask):
    if len(pattern) % 2 == 1 or len(mask) % 2 == 1:
        print "Pattern and mask must have a length that corresponds to one or several bytes."
        return

    try:
        bp = SIM_get_attribute_idx(conf.sim, "breakpoints", id)
        if not (bp[2] & 4):
            print "This can only be applied to execution breakpoints (access type x)."
            return
        bp[9] = pattern
        bp[10] = mask
        SIM_set_attribute_idx(conf.sim, "breakpoints", id, bp)
    except Exception, msg:
        print msg

new_command("set-pattern", set_pattern_cmd,
            [arg(int_t, "id"), arg(str_t, "pattern"), arg(str_t, "mask")],
            type  = ["Breakpoints", "Debugging"],
            short = "set an instruction pattern for a breakpoint",
            doc_items = [('NOTE', 'Only supported for execution breakpoints.')],
            see_also = ['set-prefix', 'set-substr'],
            doc = """
When set for breakpoint <i>id</i> Simics will only break on
instructions with a certain bit-pattern. First the <i>mask</i> will be
applied to the instruction and then the result will be compared with
the <i>pattern</i>. For example <b>set-pattern</b> 1 "0x0100" "0x0101"
will specialize breakpoint 1 to break on instructions whose first byte
has the lowest bit set and the second not.

Since an instruction may be longer than the longest supported
integer in the frontend, both pattern and mask must be supplied
as strings.

Set pattern and mask to the empty string ("") to remove this extra condition.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1375")

#
# -------------------- list-breakpoints --------------------
#

def list_breakpoints_cmd(all):
    found = 0
    
    assert_cpu()

    bp_list = conf.sim.breakpoints[:]

    for (id, type, access, hits, activate_at, active, flags, prefix, substr,
         pattern, mask, obj) in bp_list:

	if flags & (Sim_Breakpoint_Simulation | Sim_Breakpoint_Private) and not all:
	    continue

        ranges = obj.breakpoints[id]
        if len(ranges) == 1:
            print
            continue

        acc = ""
        if access & Sim_Access_Read:    acc = acc + "r"
        if access & Sim_Access_Write:   acc = acc + "w"
        if access & Sim_Access_Execute: acc = acc + "x"

    	if not found:
	    print (" Id Type     Enb %-*s %-*s   Hits Space"
                   % (18, "Start", 18, "Stop"))
            found = 1

        pr("%3d %-8s %-3s 0x%016x 0x%016x %6d %s\n" %
           (id,
            iff(type == Sim_Break_Physical,
                "phys",
                iff(type == Sim_Break_Virtual, "virt", "lin")) + "-" + acc,
            iff(active,"yes","no"),
            ranges[1],
            ranges[2],
            hits,
            obj.name))

        for r in range(3, len(ranges), 2):
            print "%s0x%016x 0x%016x" % (" "*17, ranges[r], ranges[r + 1])

        if activate_at > hits:
            print "    Ignore count:", number_str(activate_at - hits - 1, 10)
        if prefix:
            print "    Prefix:", prefix
        if substr:
            print "    Substr:", substr
        if pattern:
            print "    Pattern: 0x%s, Mask: 0x%s" % (pattern, mask)

    time_bp = 0
    for cpu in all_processors():
        for q in (Sim_Queue_Step, Sim_Queue_Time):
            for (obj, desc, time) in cpu.event_desc[q]:
                if not obj and desc.startswith("User breakpoint"):
                    if q == Sim_Queue_Time:
                        unit = "cycle"
                    else:
                        unit = "step"
                    if found and not time_bp:
                        print
                    time_bp = 1
                    print ("Breakpoint at %-5s %s (%s)"
                           % (unit, number_str(time, 10), cpu.name))

    if not found and not time_bp:
        print "No breakpoints set."
        return


new_command("list-breakpoints", list_breakpoints_cmd,
            [arg(flag_t, "-all")],
            alias = ["ib", "info-breakpoints"],
            type  = ["Breakpoints", "Debugging"],
            short = "print information about breakpoints",
            see_also = ['<breakpoint>.break', 'delete', 'enable', 'ignore', 'set-prefix', 'set-substr', 'set-pattern'],
            doc = """
Prints information about all breakpoints set. The following
information is printed for memory breakpoints: the id (used by other
commands to refer to the breakpoint), if the breakpoint is set on
physical or virtual addresses and the access type (r = read, w =
write, or x = execute), if enabled (see the <b>enable</b> command),
the address range of the breakpoint, how many times the breakpoint
has been triggered, and what memory space or context object it is set in.

If prefix, substring and/or pattern conditions are set it will be
printed as well (see <b>set-prefix</b>, <b>set-substr</b> and
<b>set-pattern</b> command).

Time breakpoints are also listed.

If <arg>-all</arg> is passed as argument, <cmd>list-breakpoints</cmd> will also
list all internal breakpoints set for simulation purposes.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1471")

#
# -------------------- map --------------------
#

def map_cmd(obj):
    map = obj.map
    map.sort()
    print "base               object               fn offs               length"
    for line in map:
        print "0x%016x %-20s %2d 0x%-16x 0x%-16x" % (line[0], line[1].name,
                                                     line[2], line[3],
                                                     line[4])
        if len(line) > 5:
            # map in port-space does not have all fields
            if line[5] and line[5] != line[1]:
                print "            target -> %s" % line[5].name
            if line[6] != 0:
                print "            priority %d" % line[6]
            if line[7] != 0:
                output = "            width %d bytes" % line[7]
                if line[8] == Sim_Swap_Bus:
                    output += ", byte swap on bus width"
                elif line[8] == Sim_Swap_Trans:
                    output += ", byte swap on transaction size"
                elif line[8] == Sim_Swap_Bus_Trans:
                    output += ", byte swap on bus width and transaction size"
                print output

    try:
        deftarg = obj.default_target
        if deftarg:
            print "%-18s %-20s %2d 0x%-16x %-18s" % ("- default -", deftarg[0].name,
                                                     deftarg[1], deftarg[2], '-')
            if deftarg[3]:
                print "            target -> %s" % deftarg[3].name
    except AttributeError:
        pass

new_command("map", map_cmd,
            [],
            namespace = "memory-space",
            type = ["Memory", "Configuration", "Inspecting Simulated State"],
            short = "list memory map",
            see_also = ['<memory-space>.add-map', '<memory-space>.del-map'],
            doc = """
Prints the memory map of the memory space object, one line per entry
in the map attribute of the memory space. The <em>base</em> column is
the starting address of the map. The <em>object</em> column contains
the object mapped at that address. <em>fn</em> is the function number
and <em>offs</em> is the offset for the object. <em>length</em> is the
number of bytes mapped.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1534")

new_command("map", map_cmd,
            [],
            namespace = "port-space",
            short = "list port map",
            type = ["Memory", "Configuration", "Inspecting Simulated State"],
            see_also = ['<port-space>.add-map', '<port-space>.del-map'],
            doc = """
Prints the port map of the port space object, one line per entry
in the map attribute of the port space. The <em>base</em> column is
the starting address of the map. The <em>object</em> column contains
the object mapped at that address. <em>fn</em> is the function number
and <em>offs</em> is the offset for the object. <em>length</em> is the
number of bytes mapped.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1549")

#
# add-map / del-map in memory-space
#

swap_names = {}
swap_names['none'] = Sim_Swap_None
swap_names['bus'] = Sim_Swap_Bus
swap_names['bus-trans'] = Sim_Swap_Bus_Trans
swap_names['trans'] = Sim_Swap_Trans

def add_map_cmd(space, object, base, length, fn, offset, target,
                pri, align_size, swap):
    if swap not in swap_names:
        print "Unknown byte swapping requested: '%s'" % swap
        SIM_command_has_problem()
        return
    try:
        space.map += [[base, object, fn, offset, length, target, pri,
                       align_size, swap_names[swap]]]
    except Exception, msg:
        print "Failed mapping '%s' in '%s': %s" % (object.name,
                                                   space.name, msg)
        SIM_command_has_problem()
        return
    else:
        print "Mapped '%s' in '%s' at address 0x%x." % (object.name,
                                                        space.name, base)

def swap_expander(comp):
    return get_completions(comp, swap_names)

new_command("add-map", add_map_cmd,
            [arg(obj_t('object'), 'device'),
             arg(uint64_t, 'base'),
             arg(uint64_t, 'length'),
             arg(int_t, 'function', '?', 0),
             arg(uint64_t, 'offset', '?', 0),
             arg(obj_t('object'), 'target', '?', None),
             arg(int_t, 'priority', '?', 0),
             arg(uint64_t, 'align-size', '?', 8),
             arg(str_t, 'swap', '?', 'none', expander = swap_expander)],
            namespace = "memory-space",
            type = ["Memory", "Configuration"],
            see_also = ['<memory-space>.map', '<memory-space>.del-map'],
            short = "map device in a memory-space",
            doc = """
Map <param>device</param> into a memory-space at address <param>base</param>
and with length <param>length</param>. Different mappings of the same device
may be indentified by a device specific <param>function</param> number. For
translator and bridge mappings, a <param>target</param> device should be given.
The mapping may specify an offset into the device's memory space, using the
<param>offset</param> argument. If several device mappings overlap, the
<param>priority</param> is used to select what device will receive memory
accesses. The priority is an integer between 0 and 255, where 0 is highest.
For devices that do not support large accesses, the <param>align-size</param>
governs how accesses are split before the device is accessed. A device mapping
may swap the bytes of an access based on the <param>swap</param> argument, that
should be one of <tt>none</tt>, <tt>bus</tt>, <tt>bus-trans</tt> and
<tt>trans</tt>. For a description of these, see the documentation of the
<attr>map</attr> attribute in the <class>memory-space</class> class.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1595")

def del_map_cmd(space, object, fn, base):
    map = [x for x in space.map if
           not (x[1] == object
                and (fn == -1 or fn == x[2])
                and (base == -1 or base == x[0]))]
    if len(map) == len(space.map):
        print "No matching mappings in %s." % (space.name)
        return
    try:
        space.map = map
        if fn == -1:
            func_str = ""
        else:
            func_str = "%d " % fn
        if base == -1:
            addr_str = ""
        else:
            addr_str = "at 0x%x " % base

        if fn == -1 and base == -1:
            print "Removing all mappings of '%s' from '%s'." % (object.name,
                                                                space.name)
        else:
            print ("Removing mapping %sof '%s' %sfrom '%s'."
                   % (func_str, object.name, addr_str, space.name))
    except Exception, msg:
        print "Failed removing mappings for '%s' from '%s': %s" % (object.name,
                                                                   space.name,
                                                                   msg)

def mapped_objs_expander(comp, space):
    objs = [x[1].name for x in space.map]
    return get_completions(comp, objs)
    
new_command("del-map", del_map_cmd,
            [arg(obj_t('object'), 'device', expander = mapped_objs_expander),
             arg(int_t, 'function', '?', -1),
             arg(int_t, 'base', '?', -1)],
            namespace = "memory-space",
            type = ["Memory", "Configuration"],
            see_also = ['<memory-space>.map', '<memory-space>.add-map'],
            short = "remove device map from a memory-space",
            doc = """
Remove the mapping of <param>device</param> from a memory-space. If a function
number is given by the <param>function</param> argument, then only mappings
with a matching number are removed. If an <param>address</param> is given,
only mappings with a matching address are removed. If both a
<param>function</param> and an <param>address</param> are specified, then only
mappings with a matching function number, at the specified address, are
removed.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1660")

#
# add-map / del-map for port-space
#

def add_map_cmd(space, object, base, length, fn, offset):
    try:
        space.map += [[base, object, fn, offset, length]]
    except Exception, msg:
        print "Failed mapping '%s' in '%s': %s" % (object.name,
                                                   space.name, msg)
        SIM_command_has_problem()
        return
    else:
        print "Mapped '%s' in '%s' at address 0x%x." % (object.name,
                                                        space.name, base)

new_command("add-map", add_map_cmd,
            [arg(obj_t('object'), 'device'),
             arg(uint64_t, 'base'),
             arg(uint64_t, 'length'),
             arg(int_t, 'function', '?', 0),
             arg(uint64_t, 'offset', '?', 0)],
            namespace = "port-space",
            type = ["Memory", "Configuration"],
            see_also = ['<port-space>.map', '<port-space>.del-map'],
            short = "map device in a port-space",
            doc = """
Map <param>device</param> into a port-space at address <param>base</param>
and with length <param>length</param>. Different mappings of the same device
may be indentified by a device specific <param>function</param> number. The
mapping may specify an offset into the device's memory space, using the
<param>offset</param> argument.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1694")

def del_map_cmd(space, object, fn):
    map = [x for x in space.map if
           not (x[1] == object and (fn == -1 or fn == x[2]))]
    if len(map) == len(space.map):
        print "No matching mappings in %s." % (space.name)
        return
    space.map = map
    try:
        space.map = map
        if fn == -1:
            print "Removing all mappings of '%s' from '%s'." % (object.name,
                                                                space.name)
        else:
            print "Removing mapping %d of '%s' from '%s'." % (fn, object.name,
                                                              space.name)
    except Exception, msg:
        print "Failed removing mappings for '%s' from '%s': %s" % (object.name,
                                                                   space.name,
                                                                   msg)

def mapped_objs_expander(comp, space):
    objs = [x[1].name for x in space.map]
    return get_completions(comp, objs)
    
new_command("del-map", del_map_cmd,
            [arg(obj_t('object'), 'device', expander = mapped_objs_expander),
             arg(int_t, 'function', '?', -1)],
            namespace = "port-space",
            type = ["Memory", "Configuration"],
            see_also = ['<port-space>.map', '<port-space>.add-map'],
            short = "remove device map from a port-space",
            doc = """
Remove the mapping of <param>device</param> from a port-space. If a function
number is given by the <param>function</param> argument, then only mappings
with a matching number is removed.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1736")


#
# -------------------- set --------------------
#

def obj_set_cmd(obj, address, value, size, little_endian, big_endian):
    if size < 1 or size > 8:
        print "size must be 1-8 bytes."
        return

    try:
        cpu = current_processor()
    except:
        # do not really need a processor
        cpu = None

    if little_endian and big_endian:
        print "Cannot use both -l and -b."
        return

    if not little_endian and not big_endian and size > 1:
        if not cpu:
            print "When no processor exists, -l or -b has to be specified."
            SIM_command_has_problem()
            return
        if cpu.big_endian:
            big_endian = 1
        else:
            little_endian = 1

    val_list = []
    for i in range(size):
        val_list.append(value & 0xff)
        value = value >> 8

    if big_endian:
        val_list.reverse()

    try:
        ex = obj.iface.memory_space.write(obj, cpu,
                                          address, tuple(val_list), 1)
        if ex != Sim_PE_No_Exception:
            print "Failed writing memory (exception %d)" % ex
            SIM_command_has_problem()
    except Exception, msg:
        print "Failed writing memory: %s" % msg
        SIM_command_has_problem()

def set_cmd(address, value, size, le, be):
    obj_set_cmd(current_processor().physical_memory, address, value, size, le, be)

new_command("set", set_cmd,
            [arg(int_t,"address"), arg(int_t,"value"), arg(int_t, "size", "?", 4),
             arg(flag_t,"-l"), arg(flag_t,"-b")],
            type  = ["Memory", "Changing Simulated State"],
            short = "set physical address to specified value",
            see_also = ["get", "x", "pselect"],
            doc = """
Set the <i>size</i> bytes of physical memory at location
<i>address</i> to <i>value</i>. The default <i>size</i> is 4 bytes,
but can be anywhere between 1 and 8 (inclusive).

If <i>value</i> is larger than the specified size, behavior is undefined.

The <i>-l</i> and <i>-b</i> flags are used to select little-endian and
big-endian byte order, respectively.  If neither is given, the byte
order of the currently selected processor is used.

The non-namespace version of this command operates on the physical memory
associated with the current processor.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1800")

new_command("set", obj_set_cmd,
            [arg(int_t,"address"), arg(int_t,"value"), arg(int_t, "size", "?", 4),
             arg(flag_t,"-l"), arg(flag_t,"-b")],
            short = "set physical address to specified value",
            see_also = ["get", "signed"],
            namespace = "memory-space",
            doc_with = "set", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1821")

#
# -------------------- get --------------------
#

def obj_get_cmd(obj, address, size, little_endian, big_endian):
    if size < 1 or size > 8:
        print "size must be 1-8 bytes."
        return

    try:
        cpu = current_processor()
    except:
        # do not really need a processor
        cpu = None

    if little_endian and big_endian:
        print "Cannot use both -l and -b."
        return

    if not little_endian and not big_endian and size > 1:
        if not cpu:
            print "When no processor exists, -l or -b has to be specified."
            SIM_command_has_problem()
            return
        if cpu.big_endian:
            big_endian = 1
        else:
            little_endian = 1

    try:
        bytes = obj.iface.memory_space.read(obj, cpu,
                                            address, size, 1)
    except Exception, msg:
        print "Failed reading memory: %s" % msg
        SIM_command_has_problem()
        return 0

    # Make sure we have the msb in bytes[0]
    if little_endian:
        bytes = list(bytes)
        bytes.reverse()
        
    ret = 0
    for x in bytes:
        ret = (ret << 8) | x
    return ret

def get_cmd(address, size, le, be):
    return obj_get_cmd(current_processor().physical_memory, address, size, le, be)

new_command("get", get_cmd,
            [arg(int_t,"address"), arg(int_t, "size", "?", 4),
             arg(flag_t,"-l"), arg(flag_t,"-b")],
            type  = ["Memory", "Inspecting Simulated State"],
            short = "get value of physical address",
            pri = 1000,
            see_also = ["x", "set", "signed"],
            doc = """
Get value of physical memory location. The size argument specifies how
many bytes should be read. This defaults to 4, but can be any number
of bytes between 1 and 8 (inclusive).

The <i>-l</i> and <i>-b</i> flags are used to select little-endian and
big-endian byte order, respectively.  If neither is given, the byte
order of the currently selected processor is used.

This command operates on the physical memory associated with the
current processor.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1879")

new_command("get", obj_get_cmd,
            [arg(int_t,"address"), arg(int_t, "size", "?", 4),
             arg(flag_t,"-l"), arg(flag_t,"-b")],
            short = "get value of physical address",
            namespace = "memory-space",
            pri = 1000,
            doc_with = "get", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1899")

#
# -------------------- read-reg --------------------
#

def obj_read_reg_cmd(cpu, reg_name):
    try:
        return local_read_int_register(cpu, reg_name)
    except:
        return SIM_read_register(cpu, SIM_get_register_number(cpu, reg_name))

def read_reg_cmd(cpu, reg_name):
    if not cpu:
        (cpu, _) = get_cpu()
    return obj_read_reg_cmd(cpu, reg_name)

def read_default_reg_cmd(reg_name):
    try:
        (cpu, _) = get_cpu()
        val = obj_read_reg_cmd(cpu, reg_name)
    except:
        (exception, value, traceback) = sys.exc_info()
        raise CliError, ("'%' command: reading register '" + reg_name
                         + "' failed (" + str(value) + ").\n\nIf you meant to "
                         + "use a path like %simics%, check that you quote "
                         + "the string properly, i.e., \"%simics%/...\"")
    return val

def exp_regs(comp):
    cpu,_ = get_cpu()
    regs = [ SIM_get_register_name(cpu, r) for r in SIM_get_all_registers(cpu) ]
    return get_completions(comp, regs)

def register_number_cmd(cpu, reg_name):
    return SIM_get_register_number(cpu, reg_name)

new_command("register-number", register_number_cmd,
            [arg(str_t, "reg-name", expander = exp_regs)],
            type  = ["Registers", "Inspecting Simulated State"],
            short = "get the number of a processor register",
            namespace = "processor",
            see_also = ['%', 'read-reg'],
            doc = """
Returns the register number for a named processor register.
The register number is used as hap indexing for example.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1942")

new_command("read-reg", read_reg_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(str_t, "reg-name", expander = exp_regs)],
            type  = ["Registers", "Inspecting Simulated State"],
            short = "read a register",
            namespace_copy = ("processor", obj_read_reg_cmd),
            see_also = ['%', 'write-reg', 'pregs', 'pselect'],
            doc = """
This command reads a CPU register. For example, to read the
<tt>eax</tt> register in an x86 processor called <obj>cpu0</obj>,
write <cmd>read-reg cpu0 eax</cmd>. You can also use the method
variant: <cmd>cpu0.read-reg eax</cmd>, or the more convenient variant
<cmd>%eax</cmd> that reads a register from the selected frontend CPU.

If no <param>cpu-name</param> is supplied, the current frontend
processor is used.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1952")

new_command("%", read_default_reg_cmd,
            [arg(str_t, doc = "reg-name", expander = exp_regs)],
            pri = 1000,
            check_args = 0,
            type  = ["Registers", "Inspecting Simulated State"],
            short = "read register by name",
            repeat = read_default_reg_cmd,
            see_also = ["read-reg", "write-reg", "pregs"],
            doc ="""
Returns the value of the register <arg>reg-name</arg> for the current
processor. This is a convenient way to use register values in expressions like
<cmd>disassemble (%pc <math>-</math> 4*3) 10</cmd>.

Use <cmd>pselect</cmd> to select the current processor.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="1969")

#
# -------------------- write-reg --------------------
#

def obj_write_reg_cmd(cpu, reg_name, value):
    value = uint64_t([("int", value)])[0]
    try:
        local_write_int_register(cpu, reg_name, value)
    except:
        SIM_write_register(cpu, SIM_get_register_number(cpu, reg_name), value)

def write_reg_cmd(cpu, reg_name, value):
    if not cpu:
        (cpu, _) = get_cpu()
    obj_write_reg_cmd(cpu, reg_name, value)

new_command("write-reg", write_reg_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(str_t, "reg-name", expander = exp_regs),
             arg(integer_t, "value")],
            type  = ["Registers", "Changing Simulated State"],
            short = "write to register",
            namespace_copy = ("processor", obj_write_reg_cmd),
            see_also = ['%', 'read-reg', 'pregs', 'pselect'],
            doc = """
Use this command to set the value of a CPU register. For example, to
set the <tt>eax</tt> register on the x86 processor <obj>cpu0</obj> to
3, write <cmd>write-reg cpu0 eax 3</cmd>. You can also use the method
variant: <cmd>cpu0.write-reg eax 3</cmd>.

This function may or may not have the correct side-effects, depending
on target and register. If no <param>cpu-name</param> is given, the
current frontend processor is used.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2000")

#
# -------------------- trace-cr, break-cr --------------------
#

class base_cr_tracker(tracker):
    def __init__(self, stop, cmd, short, doc, type, see_also = []):
        tracker.__init__(self, stop, cmd, "register", self.expander, short, doc,
                         namespace = "processor",
                         see_also = see_also,
                         group = type,
                         expander_cpu = self.expander_cpu)
        self.hap = "Core_Control_Register_Write"
        self.map = {}
        self.catchall = {}

    def expander(self, comp, cpu):
        iface = cpu.iface.int_register
        regs = [ SIM_get_register_name(cpu, r)
                 for r in SIM_get_all_registers(cpu)
                 if iface.register_info(cpu, r, Sim_RegInfo_Catchable) ]
        return get_completions(comp, regs)

    def expander_cpu(self, comp):
        return self.expander(comp, SIM_current_processor())

    # These two are here so that they can be overridden
    def get_register_number(self, obj, regname):
        return SIM_get_register_number(obj, regname)
    def get_register_name(self, obj, reg):
        return SIM_get_register_name(obj, reg)

    def filter(self, *args):
        return SIM_simics_is_running()

    def show(self, regname, obj, regno, value):
        if not regname:
            try:
                regname = self.get_register_name(obj, regno)
            except:
                regname = "[%s] Unknown register %d" % (obj.name, regno)
        if value < 0:
            value += 1 << 64
        print "[%s] %s <- %s" % (obj.name, regname, number_str(value, 16))

    def list(self, obj):
        if obj in self.catchall.keys():
            print "[%s] %s enabled for all control registers" % (obj.name, iff(self.stop, "breaking", "tracing"))
        else:
            print "[%s] %s enabled for these control registers:" % (obj.name, iff(self.stop, "breaking", "tracing"))
            if obj in self.map.keys():
                for reg in self.map[obj].keys():
                    print "  %s" % self.get_register_name(obj, reg)

    def resolve_target(self, obj, regname):
        return (regname, self.get_register_number(obj, regname))

    def is_tracked(self, obj, target):
        regname, regno = target
        return ((obj in self.catchall.keys())
                or (obj in self.map.keys() and self.map[obj].has_key(regno)))

    def track_all(self, obj):
        if self.catchall.has_key(obj):
            return
        if not (obj in self.map.keys()):
            self.map[obj] = {}
        for regno,hdl in self.map[obj].items():
            SIM_hap_delete_callback_obj_id("Core_Control_Register_Write",
                                           obj, hdl)
            del self.map[obj][regno]
        self.catchall[obj] = SIM_hap_add_callback_obj(
            "Core_Control_Register_Write", # hap
            obj,                           # trigger object
            0,                             # flags
            self.callback,                 # callback
            None)                          # user value

    def track_none(self, obj):
        if (obj in self.catchall.keys()):
            SIM_hap_delete_callback_obj_id("Core_Control_Register_Write",
                                           obj,
                                           self.catchall[obj])
            del self.catchall[obj]
        else:
            if not (obj in self.map.keys()):
                self.map[obj] = {}
            for regno,hdl in self.map[obj].items():
                SIM_hap_delete_callback_obj_id("Core_Control_Register_Write",
                                               obj, hdl)
                del self.map[obj][regno]

    def track_on(self, obj, target):
        regname, regno = target
        if obj in self.catchall.keys():
            print "[%s] Already %s all control registers" % (obj.name, iff(self.stop, "breaking on", "tracing"))
            return
        if self.is_tracked(obj, target):
            print "[%s] Already %s %s" % (obj.name, iff(self.stop, "breaking on", "tracing"), regname)
            return
        if not obj.iface.int_register.register_info(obj, regno, Sim_RegInfo_Catchable):
            print "[%s] Cannot %s on %s" % (obj.name, iff(self.stop, "break", "trace"), regname)
            return

        if not (obj in self.map.keys()):
            self.map[obj] = {}
        self.map[obj][regno] = SIM_hap_add_callback_obj_index(
            "Core_Control_Register_Write", # hap
            obj,                           # trigger object
            0,                             # flags
            self.callback,                 # callback
            regname,                       # user value
            regno)                         # index
        
    def track_off(self, obj, target):
        regname, regno = target
        if obj in self.catchall.keys():
            # All tracked, remove all
            self.track_none(obj)
            # Reinstall all catchable registers, except the one removed
            iface = obj.iface.int_register
            for r in SIM_get_all_registers(obj):
                if r != regno:
                    if iface.register_info(obj, r, Sim_RegInfo_Catchable):
                        regname = SIM_get_register_name(obj, r)
                        self.track_on(obj, (regname, r))
            
            return
        if not self.is_tracked(obj, target):
            print "[%s] Not %s %s" % (obj.name, iff(self.stop, "breaking on", "tracing"), regname)
            return
        SIM_hap_delete_callback_obj_id("Core_Control_Register_Write", obj,
                                       self.map[obj][regno])
        del self.map[obj][regno]

cr_tracker = base_cr_tracker

if "cr_tracker" in dir():
    trace_cr_cmds = cr_tracker(0, "trace-cr",
                               short = "trace control register updates",
                               type = "inspect/change",
                               see_also = [ "break-cr" ],
                               doc = """
Enables and disables tracing of control register updates.  When this
is enabled, every time the specified control register is updated
during simulation a message is printed.  The message will name the
register being updated, and the new value.  The new value will be
printed even if it is identical to the previous value.

The <i>reg-name</i> parameter specifies which control register should
be traced.  The available control registers depends on the simulated
target.

Instead of a register name, the <tt>-all</tt> flag may be given.  This
will enable or disable tracing of all control register.
""")

    break_cr_cmds = cr_tracker(1, "break-cr",
                               short = "break on control register updates",
                               type = "breakpoint",
                               see_also = [ "trace-cr", "<breakpoint>.break" ],
                               doc = """
Enables and disables breaking simulation on control register updates.
When this is enabled, every time the specified control register is
updated during simulation a message is printed.  The message will name
the register being updated, and the new value.  The new value will be
printed even if it is identical to the previous value.

The <i>reg-name</i> parameter specifies which control register should
be traced.  The available control registers depends on the simulated
target.

Instead of a register name, the <tt>-all</tt> flag may be given.  This
will enable or disable tracing of all control register.
""")

#
# -------------------- trace-exception, break-exception --------------------
#

class exception_tracker(tracker):
    def __init__(self, stop, cmd, short, doc, type, see_also = []):
        tracker.__init__(self, stop, cmd, ((int_t, str_t), ("number", "name")),
                         (0, self.expander), short, doc,
                         group = type, see_also = see_also)
        self.hap = "Core_Exception"
        self.map = {}
        self.catchall = 0
        self.names = {}

    def expander(self, comp):
        try:
            cpu = current_processor()
        except:
            return []
        if self.names.has_key(cpu):
            names = self.names[cpu]
        else:
            iface = cpu.iface.exception
            names = [ iface.get_name(cpu, exc).replace(' ', '_')
                      for exc in iface.all_exceptions(cpu) ]
            self.names[cpu] = names
        return get_completions(comp, names)

    # These two are here so that they can be overridden
    def get_exception_number(self, excname, cpu = None):
        if not cpu:
            cpu = current_processor()

        return cpu.iface.exception.get_number(cpu, excname)
                
    def get_exception_name(self, exc, cpu = None):
        if not cpu:
            cpu = current_processor()
            
        return cpu.iface.exception.get_name(cpu, exc)

    def show(self, excname, cpu, excno):
        if not excname:
            excname = self.get_exception_name(excno, cpu)
        print ("[%s] (@ cycle %s) Exception %d: %s"
               % (cpu.name, number_str(SIM_cycle_count(cpu), 10),
                  excno, excname))

    def list(self):
        if self.catchall:
            print "%s enabled for all exceptions" % iff(self.stop, "breaking", "tracing")
        else:
            print "%s enabled for these exceptions:" % iff(self.stop, "breaking", "tracing")
            l = self.map.keys()
            l.sort()
            for exc in l:
                print "  %3d %s" % (exc, self.get_exception_name(exc))

    def resolve_target(self, exc):
        if type(exc) == type("hej"):
            try:
                name = exc
                num = self.get_exception_number(exc)
            except:
                # some targets have spaces in the exception name
                name = exc.replace('_', ' ')
                num = self.get_exception_number(name)
        else:
            name = self.get_exception_name(exc)
            num = exc
        return (name, num)

    def is_tracked(self, target):
        excname, excno = target
        return self.catchall or self.map.has_key(excno)

    def track_all(self):
        if self.catchall:
            return
        for key,hdl in self.map.items():
            SIM_hap_delete_callback_id(self.hap, hdl)
            del self.map[key]
        self.catchall = SIM_hap_add_callback(self.hap,
                                             self.callback, None)

    def track_none(self):
        if self.catchall:
            SIM_hap_delete_callback_id(self.hap, self.catchall)
            self.catchall = 0
        else:
            for key,hdl in self.map.items():
                SIM_hap_delete_callback_id(self.hap, hdl)
                del self.map[key]

    def track_on(self, target):
        excname, excno = target
        if self.catchall:
            print "Already %s all exceptions" % iff(self.stop, "breaking", "tracing")
            return
        if self.is_tracked(target):
            print "Already %s %s" % (iff(self.stop, "breaking", "tracing"), excname)
            return
        self.map[excno] = SIM_hap_add_callback_index(self.hap,
                                                     self.callback, excname,
                                                     excno)        

    def track_off(self, target):
        excname, excno = target
        if self.catchall:
            # Remove the global exception handler
            self.track_none()
            # Install new handlers for all exceptions except the one turned off
            cpu = current_processor()
            for e in cpu.iface.exception.all_exceptions(cpu):
                if e != excno:
                    self.track_on(self.resolve_target(e))
            return
        if not self.is_tracked(target):
            print "Not %s %s" % (iff(self.stop, "breaking", "tracing"), excname)
            return
        SIM_hap_delete_callback_id(self.hap, self.map[excno])
        del self.map[excno]


trace_exception_cmds = exception_tracker(0, "trace-exception",
                                         short = "trace exceptions",
                                         type = "inspect/change",
                                         see_also = [ "break-exception" ],
                                         doc = """
Enables and disables tracing of exceptions.  When this
is enabled, every time the specified exception occurs
during simulation a message is printed.

The <i>exception</i> parameter specifies which exception should
be traced.  The available exceptions depends on the simulated
target.

Instead of an exception, the <tt>-all</tt> flag may be given.  This
will enable or disable tracing of all exceptions.
""")

break_exception_cmds = exception_tracker(1, "break-exception",
                                         short = "break on CPU exceptions",
                                         type = "breakpoint",
                                         see_also = [ "trace-exception", "<breakpoint>.break" ],
                                         doc = """
Enables and disables breaking simulation on exceptions.
When this is enabled, every time the specified exception occurs
uring simulation a message is printed.

The <i>exception</i> parameter specifies which exception should
be traced.  The available exceptions depends on the simulated
target.

Instead of an exception, the <tt>-all</tt> flag may be given.  This
will enable or disable tracing of all exceptions.
""")

#
# -------------------- trace-breakpoint --------------------
#

class base_bp_tracker(tracker):
    def __init__(self, stop, cmd, short, doc, type, see_also = []):
        tracker.__init__(self, stop, cmd, "breakpoint", self.expander, short, doc,
                         see_also = see_also, group = type)
        self.hap = "Core_Breakpoint_Memop"
        self.map = {}
        self.catchall = 0

    def expander(self, comp):
        bp_list = conf.sim.breakpoints[:]
        bp_ids = map(lambda x: str(x[0]), bp_list)
        return get_completions(comp, bp_ids)

    def show(self, arg, obj, id, memop):
        step = None
	if memop.ini_ptr:
		step = SIM_step_count(memop.ini_ptr.queue)
        val = ""
        mem_op_type = SIM_get_mem_op_type(memop)
        if mem_op_type == Sim_Trans_Store:
            if memop.size <= 8:
                val = number_str(SIM_get_mem_op_value_cpu(memop), 16) + " "
            else:
                val = ""
        bits = ""
        if mem_op_type != Sim_Trans_Instr_Fetch:
            bits = "%d-bit " % (memop.size * 8)
	print "breakpoint %d (step %s) %s %s%s@ %s" % (id, number_str(step, 10), SIM_get_mem_op_type_name(mem_op_type), bits, val, number_str(memop.logical_address, 16))

    def list(self):
        if self.catchall:
            print "%s enabled for all breakpoints" % iff(self.stop, "breaking", "tracing")
        else:
            print "%s enabled for these breakpoints:" % iff(self.stop, "breaking", "tracing")
            for id in self.map.keys():
                print "  %s" % id # TODO: Print as in list-breakpoints

    def resolve_target(self, id):
        return id

    def is_tracked(self, id):
        return self.catchall or self.map.has_key(id)

    def track_all(self):
        if self.catchall: return
        for id,hdl in self.map.items():
            SIM_hap_delete_callback_id(self.hap, hdl)
            del self.map[id]
        self.catchall = SIM_hap_add_callback(self.hap,
                                             self.callback, None)

    def track_none(self):
        if self.catchall:
            SIM_hap_delete_callback_id(self.hap, self.catchall)
            self.catchall = 0
        else:
            for id,hdl in self.map.items():
                SIM_hap_delete_callback_id(self.hap, hdl)
                del self.map[id]

    def track_on(self, id):
        if self.catchall:
            print "Already tracing all breakpoints"
            return
        if self.is_tracked(id):
            print "Already tracing %s" % id
            return
        self.map[id] = SIM_hap_add_callback_index(self.hap,
                                                  self.callback, id, int(id))
        
    def track_off(self, id):
        if self.catchall:
            print "Disabling tracing of all breakpoints"
            self.track_none()
            return
        if not self.is_tracked(id):
            print "Not tracing %s" % id
            return
        SIM_hap_delete_callback_id(self.hap, self.map[id])
        del self.map[id]

bp_tracker = base_bp_tracker

if "bp_tracker" in dir():
    trace_bp_cmds = bp_tracker(0, "trace-breakpoint",
                               short = "trace breakpoints",
                               type = "inspect/change",
                               see_also = [],
                               doc = """
Enables and disables tracing of breakpoints. When enabled, breakpoint
hits will be traced to the console instead of stopping the simulation.

The <i>id</i> parameter specifies the breakpoint to trace.

Instead of an id, the <tt>-all</tt> flag may be given.  This
will enable or disable tracing of all breakpoints.
""")

#
# -------------------- pregs --------------------
#

def pregs_cmd(cpu, a):
    if not cpu:
        (cpu, _) = get_cpu()
    local_pregs(cpu, a)

def obj_pregs_cmd(obj, all):
    local_pregs(obj, all)

new_command("pregs", pregs_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(flag_t, "-all")],
            type  = ["Registers", "Inspecting Simulated State"],
            short = "print cpu registers",
            namespace_copy = ("processor", obj_pregs_cmd),
            doc = """
Prints the current integer register file of the processor
<i>cpu_name</i>. If no CPU is specified, the current CPU will be
selected. The -all flag causes additional registers, such as control
registers and floating point registers to be printed.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2466")

#
# -------------------- info --------------------
#

def common_processor_get_info(obj):
    exec_mode = "normal"
    if SIM_class_has_attribute(obj.classname, "turbo_execution_mode") and obj.turbo_execution_mode:
        exec_mode = "turbo"
    elif SIM_class_has_attribute(obj.classname, "ooo-mode"):
        exec_mode = obj.ooo_mode
    if obj.freq_mhz == int(obj.freq_mhz):
        clock_freq = "%d" % obj.freq_mhz
    else:
        clock_freq = "%f" % obj.freq_mhz
    try:
        phys_mem = obj.physical_memory.name
    except Exception, e:
        phys_mem = None
    ret = [("Execution mode", exec_mode),
           ("Clock frequency", "%s MHz" % clock_freq),
           ("CPI", "%.2f" % (1.0 * obj.step_rate[1] / obj.step_rate[0])),
           ("Physical memory", phys_mem)]
    if SIM_class_has_attribute(obj.classname, "physical-io") and obj.physical_io != None:
        ret += [("Physical I/O", obj.physical_io.name)]
    return ret

def default_processor_get_info(obj):
    return [ (None,
              common_processor_get_info(obj)) ]

def processor_info_cmd(obj):
    # Add default version if not already defined
    obj_funcs = get_obj_funcs(obj)
    if not obj_funcs.has_key('get_info'):
        obj_funcs['get_info'] = default_processor_get_info
    info_cmd(obj)

new_command("info", processor_info_cmd,
            [],
            short = "print information about the processor",
            namespace = "processor",
            doc = "Print detailed information about the configuration of the processor.", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2516")

#
# -------------------- diff, diff-gen --------------------
#

def diff_gen(cmd, file):
    old_out = sys.stdout
    try:
        fd = open(file, "w")
    except:
        pr("Error while opening file %s for writing\n" % file)
        return

    sys.stdout = fd

    try:
        eval_cli_line(cmd)
        sys.stdout = old_out;
        fd.close()
    except:
        fd.close()
        sys.stdout = old_out;
        raise


new_command("diff-gen", diff_gen,
            [arg(str_t, "cmd"), arg(filename_t(), "file", "?", "last-command-output.txt")],
            type  = "internal commands",
            short = "diff command output",
            doc = """
Writes the output of the command cmd to the file.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2546")

def diff(cmd, file):
    diff_gen(cmd, file+".cmp")
    os.system("diff "+file+" "+file+".cmp")

new_command("diff", diff,
            [arg(str_t, "cmd"),
             arg(filename_t(exist = 1), "file",
                 "?", "last-command-output.txt")],
            type  = "internal commands",
            short = "diff command output",
            doc = """
Uses system diff to compare the output in the file with the output of the
command cmd.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2557")

#
# -------------------- logical-to-physical --------------------
#

def logical_to_physical_cmd(cpu, laddr):
    if not cpu:
        (cpu, _) = get_cpu()
    return translate_to_physical(cpu, laddr)

def obj_logical_to_physical_cmd(obj, laddr):
    return translate_to_physical(obj, laddr)

new_command("logical-to-physical", logical_to_physical_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(addr_t,"address")],
            alias = "l2p",
            type  = ["Memory", "Inspecting Simulated State"],
            short = "translate logical address to physical",
            namespace_copy = ("processor", obj_logical_to_physical_cmd),
            doc = """
Translate the given logical <i>address</i> to a physical one. The
operation is performed as read from processor <i>cpu-name</i>. On x86
a logical address can be given on the form
&lt;segment register&gt;:&lt;offset&gt;
or l:&lt;linear address&gt;. If no prefix is given ds:&lt;offset&gt; will be
assumed. If the CPU is omitted the current CPU will be used. No
side-effects will occur, i.e. if the translation is not in the
TLB. The method variant of this command can also be used.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2579")

#
# -------------------- x --------------------
#

def x_cmd_repeat(cpu, addr_spec, length):
    global _last_x_addr
    _last_x_addr = (_last_x_addr[0], _last_x_addr[1] + length)

    if type(cpu) is types.StringType:
        (cpu, _) = get_cpu(cpu)
    elif not cpu:
        (cpu, _) = get_cpu()

    cpu_x_cmd(cpu, _last_x_addr, length)

def x_cmd(cpu, addr_spec, length):
    if not cpu:
        (cpu, _) = get_cpu()
    cpu_x_cmd(cpu, addr_spec, length)

def cpu_x_cmd(cpu, addr_spec, length):
    global _last_x_addr
    _last_x_addr = addr_spec
    (kind, addr) = addr_spec
    if kind == 'p':
        src = physmem_source(cpu.physical_memory)
    else:
        src = virtmem_source(cpu.physical_memory, cpu, kind)
    try:
        hexdump(src, addr, length)
    except Exception, msg:
        print msg

def memory_space_x_cmd_repeat(obj, addr, length):
    global _last_x_addr
    _last_x_addr = _last_x_addr + length

    memory_space_x_cmd(obj, _last_x_addr, length)

def memory_space_x_cmd(obj, address, length):
    global _last_x_addr
    _last_x_addr = address
    try:
        hexdump(physmem_source(obj), address, length)
    except Exception, msg:
        print msg

def get_address_prefix(cpu):
    try:
        f = get_obj_funcs(cpu)['get_address_prefix']
        return f()
    except KeyError, msg:
        return "v"

def translate_to_physical(cpu, addr):
    try:
        f = get_obj_funcs(cpu)['translate_to_physical']
        return f(cpu, addr)
    except KeyError, msg:
        if addr[0] not in ["", "v"]:
            raise CliError, "Illegal address prefix '" + addr[0] + "'."
        return SIM_logical_to_physical(cpu, 1, addr[1])

def any(pred, set):
    return filter(pred, set) != []

def hexdump(source, addr, length, align=True):
    bpl = 16       # bytes per line
    blen = bpl * 2 + bpl / 2
    if addr + length - 1 <= 0xffffffff:
        addr_fmt = "0x%08x"
    else:
        addr_fmt = "0x%016x"
    addr_prefix = source.addr_prefix()
    line = chars = prefix = ""

    def flush():
        if (line):
            pr(prefix + line + ' ' * (blen - len(line) + 1) + tags + ' '
               + chars + '\n')

    def line_prefix(addr):
        if align:
            addr &= ~(bpl - 1)
        return addr_prefix + addr_fmt % addr + ' '

    def get_tag(addr):
        if have_tags:
            return source.get_tag(addr)
        else:
            return ""

    # Look for tagged memory (need to know if tag column should be displayed)
    have_tags = any(source.have_tag, range(addr, addr + length, 16))

    if align:
        # Align printed lines on a "bytes-per-line" byte boundary
        alignment = addr & (bpl - 1)    # leftmost bytes to skip 
        line += ' ' * (alignment * 2 + (alignment + 1) // 2)
        chars = ' ' * alignment
        tags = get_tag(addr)
        prefix = line_prefix(addr)
    else:
        alignment = 0

    for i in range(length):
        if ((i + alignment) % bpl) == 0:
            flush()
            prefix = line_prefix(addr + i)
            line = chars = ""
            tags = get_tag(addr + i)
        if ((i + alignment) & 1) == 0:
            line += ' '
        val = source.get_byte(addr + i)
        ch = "."
        if isinstance(val, str):
            line += val
        else:
            line += "%02x" % val
            # Until we know how the terminal will display characters > 0x7e,
            # don't print them (see bug 1177)
            if 0x20 <= val < 0x7f:
                ch = chr(val)
        chars += ch
    flush()
    source.finish()

class physmem_source:
    def __init__(self, obj):
        self.obj = obj
        self.unhandled = self.outside = self.tag_unavailable = 0

    def addr_prefix(self):
        return "p:"

    def get_byte(self, addr):
        try:
            [byte] = self.obj.memory[addr]
        except SimExc_InquiryUnhandled, msg:
            self.unhandled = 1
            return "??"
        except SimExc_Memory, msg:
            self.outside = 1
            return "**"
        return byte

    def have_tag(self, addr):
        try:
            return VT_read_phys_memory_tags_mask(self.obj, addr, 1)
        except SimExc_InquiryUnhandled, msg:
            return 0
        except SimExc_Memory, msg:
            return 0

    def get_tag(self, addr):
        try:
            if VT_read_phys_memory_tags_mask(self.obj, addr, 1):
                return "%d" % SIM_read_phys_memory_tags(self.obj, addr, 1)
            else:
                self.tag_unavailable = 1
                return '/'
        except SimExc_InquiryUnhandled, msg:
            return '?'
        except SimExc_Memory, msg:
            return '*'

    def finish(self):
        if self.outside:
            pr("addresses marked \"**\" are outside physical memory\n")
        if self.unhandled:
            pr("addresses marked \"??\" do not support inquiry\n")
        if self.tag_unavailable:
            pr("addresses marked \"/\" do not have tags\n")

class virtmem_source(physmem_source):
    def __init__(self, obj, cpu, kind):
        self.obj = obj
        self.cpu = cpu
        self.kind = kind
        self.unhandled = self.outside = self.no_translation = 0
        self.tag_unavailable = 0

    def addr_prefix(self):
        if self.kind == "":
            return get_address_prefix(self.cpu) + ":"
        else:
            return self.kind + ":"

    def get_byte(self, addr):
        try:
            paddr = translate_to_physical(self.cpu, (self.kind, addr))
        except SimExc_Memory, msg:
            self.no_translation = 1
            return "--"
        return physmem_source.get_byte(self, paddr)

    def have_tag(self, addr):
        try:
            paddr = translate_to_physical(self.cpu, (self.kind, addr))
        except SimExc_Memory, msg:
            self.no_translation = 1
            return 0
        return physmem_source.have_tag(self, paddr)

    def get_tag(self, addr):
        try:
            paddr = translate_to_physical(self.cpu, (self.kind, addr))
        except SimExc_Memory, msg:
            return "-"
        return physmem_source.get_tag(self, paddr)

    def finish(self):
        physmem_source.finish(self)
        if self.no_translation:
            pr("addresses marked \"--\" have no translation\n")

new_command("x", x_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(addr_t, "address"),
             arg(int_t, "size", "?", 16)],
            type  = ["Memory", "Inspecting Simulated State"],
            short = "examine raw memory contents",
            namespace_copy = ("processor", cpu_x_cmd),
            repeat = x_cmd_repeat,
            see_also = ["disassemble", "get", "set"],
            doc = """
Display the contents of a memory space starting at <arg>address</arg>. Either
the memory space is explicitly specified as in
<cmd>&lt;memory-space>.x</cmd> or the CPU connected to the memory space can be
specified; e.g., <cmd>&lt;processor>.x</cmd>. By itself, <cmd>x</cmd> operates
on the memory connected to the current frontend processor.

If the memory is accessed via a CPU, the type of <arg>address</arg> is
specified by a prefix. For physical addresses use
<cmd>p:<var>address</var></cmd>; for virtual addresses,
<cmd>v:<var>address</var></cmd> on non-x86 targets. On x86, use
<cmd><var>segment-register</var>:<var>offset</var></cmd> or
<cmd>l:<var>address</var></cmd> for x86 linear addresses.

If no prefix is given it will be interpreted as a virtual address. On x86 the
default is <cmd>ds:<var>address</var></cmd> (data segment addressing).

The <arg>size</arg> argument specifies the number of bytes to examine. When
examining virtual memory, only addresses which can be found in the TLB or
hardware page tables (if any) are shown. Unmapped addresses are shown
as "<tt>--</tt>", undefined physical addresses as "<tt>**</tt>".""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2812")

new_command("x", memory_space_x_cmd,
            [arg(int_t, "address"), arg(int_t, "size", "?", 16)],
            short = "examine raw memory contents",
            namespace = "memory-space",
            repeat = memory_space_x_cmd_repeat,
            doc_with = "x", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2843")

def sum_mem(obj, cpu, type, addr, length, w8, w16, w32):
    sum8 = 0
    sum16 = 0
    sum32 = 0

    buff = []

    if cpu and type in ["", "v"]:
        type = get_address_prefix(cpu)

    line = ""

    last_byte = [0, 0, 0, 0]

    for i in range(length):
        outside = unhandled = 0

        try:
            if type == "" or type == "p":
                phys_addr = addr + i;
            else:
                phys_addr = translate_to_physical(cpu, (type, addr + i))
            [byte] = obj.memory[[phys_addr,phys_addr]]
        except SimExc_InquiryUnhandled, msg:
            print "Inquiry not handled"
            return
        except SimExc_Memory, msg:
            print "Got exception reading memory"
            return

        if i != 0 and (i % 4) == 0:
            sum32 = sum32 + ((last_byte[0] << 0) | (last_byte[1] << 8) | (last_byte[2] << 16) | (last_byte[3] << 24))
            sum32 = sum32 & 0xFFFFFFFF

        if i != 0 and (i % 2) == 0:
            sum16 = sum16 + ((last_byte[(i - 2) % 4] << 0) | (last_byte[(i - 1) % 4] << 8))
            sum16 = sum16 & 0xFFFF

        last_byte[i % 4] = byte

        sum8 = sum8 + byte
        sum8 = sum8 & 0xFF

    if w8 + w16 + w32 == 0:
        w8 = 1

    if w8:
        print "Checksum 8-bit: %02x" % sum8
    if w16:
        if length % 2:
            print "Range not a multiple of 2 bytes, %d bytes skipped" % (length % 2)
        else:
            last16 = (last_byte[(length - 2) % 4] << 0) | (last_byte[(length - 1) % 4] << 8)
            sum16 = (sum16 + last16) & 0xFFFF
            print "Last 16-bit: %04x" % last16
        print "Checksum 16-bit: %04x" % sum16
    if w32:
        if length % 4:
            print "Range not a multiple of 4 bytes, %d bytes skipped" % (length % 4)
        else:
            last32 = (last_byte[0] << 0) | (last_byte[1] << 8) | (last_byte[2] << 16) | (last_byte[3] << 24)
            sum32 = (sum32 + last32) & 0x0FFFFFFFF
        print "Checksum 32-bit: %08x" % sum32

def sum_cmd(cpu, addr_spec, length, w8, w16, w32):
    if not cpu:
        (cpu, _) = get_cpu()
    try:
        sum_mem(cpu.physical_memory, cpu, addr_spec[0], addr_spec[1], length, w8, w16, w32)
    except Exception, msg:
        print msg

def obj_sum_cmd(obj, address, size, w8, w16, w32):
    sum_cmd(obj.name, address, size, w8, w16, w32)

new_command("sum", sum_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(addr_t, "address"),
             arg(int_t, "size"),
             arg(flag_t, "-w8"),
             arg(flag_t, "-w16"),
             arg(flag_t, "-w32")],
            type = "inspect/change",
            short = "sum a memory range",
            deprecated = "python",
            namespace_copy = ("processor", obj_sum_cmd),
            doc = """
Sum a memory range. The width of the running sum is specified with the
<arg>-w8</arg> (default), <arg>-w16</arg>, or <arg>-w32</arg> flag, standing
for 8, 16, and 32 bits respectively.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="2925")

#
# -------------------- disassemble --------------------
#

_last_disassemble_addr = 0

def disassemble_cmd_sub(cpu, addr, t, count):
    global _last_disassemble_addr
    
    for i in range(count):
        instr_len = local_print_disassemble_line(cpu, addr, t, 0)
        if instr_len == 0:
            break
        addr = addr + instr_len

    # save the last address if repeat
    _last_disassemble_addr = addr

def disassemble_cmd_rep(cpu, address, count):
    global _last_disassemble_addr

    if not cpu:
        (cpu, _) = get_cpu()
        
    if address[0] == "p":
        t = 0
    elif address[0] in ["v", "cs", ""]:
        t = 1
    else:
        raise CliError, "Illegal address prefix '%s'." % address[0]

    t = iff(address[0] == "p", 0, 1)
    addr = _last_disassemble_addr
    disassemble_cmd_sub(cpu, addr, t, count)

def disassemble_cmd(cpu, address, count):
    if not cpu:
        (cpu, _) = get_cpu()

    if address[0] == "p":
        t = 0
    elif address[0] in ["v", "cs", ""]:
        t = 1
    else:
        raise CliError, "Illegal address prefix '%s'." % address[0]

    if count <= 0:
        raise CliError, "Illegal instruction count."
    
    t = iff(address[0] == "p", 0, 1)
    if address[1] == -1:
        if address[0] == "p":
            addr = SIM_logical_to_physical(cpu, Sim_DI_Instruction, SIM_get_program_counter(cpu))
        else:
            addr = SIM_get_program_counter(cpu)
    else:
        addr = address[1]

    disassemble_cmd_sub(cpu, addr, t, count)

new_command("disassemble", disassemble_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name", "?"),
             arg(addr_t, "address", "?", ("v",-1)),
             arg(int_t, "count", "?", 1)],
            alias = "da",
            repeat = disassemble_cmd_rep,
            type  = ["Memory", "Inspecting Simulated State", "Execution"],
            short = "disassemble instructions",
            namespace_copy = ("processor", disassemble_cmd),
            see_also = ["x", "disassemble-settings", "<processor>.aprof-views"],
            doc = """
Disassembles <arg>count</arg> instructions starting at
<arg>address</arg> for processor <arg>cpu-name</arg>. If the processor
is not given the current frontend processor will be used. The method
variant can also be used to select a processor; e.g.,
<cmd>cpu0.disassemble</cmd>.

On some architectures, <arg>address</arg> must be word aligned. A
physical address is given by prefixing the address with <cmd>p:</cmd>
(e.g., <cmd>p:0xf000</cmd>). With no prefix, a virtual address will be
assumed. If the address is omitted the current program counter will be
used. <arg>count</arg> defaults to 1 instruction.

Global disassembly settings, such as whether to print the raw opcodes,
can be set by the <cmd>disassemble-settings</cmd> command.

This command will also include various profiling statistics for the
address of each instruction, one column for each profiler view listed
in the processor attribute <tt>aprof-views</tt>. For descriptions of
the columns, use the <cmd>&lt;processor&gt;.aprof-views</cmd> command.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3002")

#
# -------------------- set-pc --------------------
#

def cpu_set_pc_cmd(cpu_obj, address):
    try:
        SIM_set_program_counter(cpu_obj, address)
    except Exception, msg:
        print "Failed setting program counter: %s" % msg
        SIM_command_has_problem()

def set_pc_cmd(address):
    try:
        SIM_set_program_counter(current_processor(), address)
    except Exception, msg:
        print "Failed setting program counter: %s" % msg
        SIM_command_has_problem()

new_command("set-pc", set_pc_cmd,
            [arg(int_t, "address",)],
            type  = ["Registers", "Changing Simulated State", "Execution"],
            short = "set the current processor's program counter",
            doc = """
Set program counter (instruction pointer) of the CPU (defaults to
the current frontend processor) to <i>address</i>.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3051")

new_command("set-pc", cpu_set_pc_cmd,
            [arg(int_t, "address",)],
            namespace = "processor",
            short = "set the program counter",
            doc_with = "set-pc", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3060")

#
# -------------------- load-binary --------------------
#

def mem_space_load_binary_cmd(obj, the_file, poff, v, use_pa):
    try:
        return SIM_load_binary(obj, the_file, poff, use_pa, v)
    except SimExc_IOError,msg:
        print "Error reading kernel file '%s': %s" % (the_file, msg)
        SIM_command_has_problem()
        return
    except SimExc_Memory, msg:
        print msg
        SIM_command_has_problem()
        return

def load_binary_cmd(the_file, poff, v, use_pa, logical):
    if logical:
        mem = current_processor()
    else:
        mem = current_processor().physical_memory
    return mem_space_load_binary_cmd(mem, the_file, poff, v, use_pa)

new_command("load-binary", load_binary_cmd,
            [arg(filename_t(simpath = 1, exist = 1), "filename"),
             arg(int64_t, "offset", "?", 0),
             arg(flag_t, "-v"), arg(flag_t, "-pa"), arg(flag_t, "-l")],
            type  = ["Memory", "Changing Simulated State", "Execution"],
            short = "load binary (executable) file into memory",
            see_also = ["add-directory"],
            doc = """
Load a binary (executable) file into the given physical or virtual memory
space. The supported formats are ELF, Motorola S-Record, PE32 and PE32+.
If an offset is supplied, it will be added to the load
address taked from the file.

By default the virtual load address from the file is used, but the
physical address can be used instead by specifying the
<param>-pa</param> flag.

The <param>-v</param> flag turns on verbose mode, printing information
about the loaded file.

When used as a global command, it will use the currently selected
processor to find the memory space to load the binary into.  If the
<param>-l</param> flag is given, it will load it into the virtual
memory space, otherwise it will use the physical memory space.

When using the namespace command on a <class>processor</class> object,
it will load the binary into the virtual memory space of that
processor.

When using the namespace command on a <class>memory-space</class>
object, it will load the binary directly into that memory space.

The return value is the address of the execution
entry point. This value is typically used in a call to
<cmd>set-pc</cmd>.

<cmd>load-binary</cmd> uses Simics's Search Path and path markers (%simics%,
%script%) to find the file to load. Refer to Simics User Guide (CLI chapter)
for more information on how Simics's Search Path is used to locate files.

""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3089")

new_command("load-binary", mem_space_load_binary_cmd,
            [arg(filename_t(simpath = 1, exist = 1), "filename"), arg(int_t, "offset", "?", 0),
             arg(flag_t, "-v"), arg(flag_t, "-pa")],
            namespace = "memory-space",
            short = "load binary (executable) file into memory",
            doc_with = "load-binary", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3131")

new_command("load-binary", mem_space_load_binary_cmd,
            [arg(filename_t(simpath = 1, exist = 1), "filename"), arg(int_t, "offset", "?", 0),
             arg(flag_t, "-v"), arg(flag_t, "-pa")],
            namespace = "processor",
            short = "load binary (executable) file into memory",
            doc_with = "load-binary", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3138")


#
# -------------------- load-file --------------------
#

def mem_space_load_file_cmd(obj, the_file, base_address):
    try:
        SIM_load_file(obj, the_file, base_address, 0)
        return
    except (SimExc_Memory, SimExc_IOError), msg:
        print "Error loading '%s' to memory: %s." % (the_file, msg)

    SIM_command_has_problem()

def load_file_cmd(the_file, base_address):
    mem = current_processor().physical_memory
    return mem_space_load_file_cmd(mem, the_file, base_address)

new_command("load-file", load_file_cmd,
            [arg(filename_t(exist = 1, simpath = 1), "filename"), arg(int_t, "offset", "?", 0)],
            type  = ["Memory", "Changing Simulated State"],
            see_also = ["add-directory"],
            short = "load file into memory",
            doc = """
Loads a file with name <i>filename</i> into the memory space
(defaulting to the current frontend processor's physical memory
space), starting at physical address <i>offset</i>. Default offset is
0.

<cmd>load-file</cmd> uses Simics's Search Path and path markers (%simics%,
%script%) to find the file to load. Refer to Simics User Guide (CLI chapter)
for more information on how Simics's Search Path is used to locate files.

""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3163")

new_command("load-file", mem_space_load_file_cmd,
            [arg(filename_t(exist = 1, simpath = 1), "filename"), arg(int_t, "offset", "?", 0)],
            namespace = "memory-space",
            short = "load file into memory",
            doc_with = "load-file", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3180")

#
# -------------------- enable-real-time-mode --------------------
#
def set_real_time_mode_cmd(max_speed, check_interval):
    assert_cpu()
    SIM_set_attribute(conf.sim, "real-time-max-speed", max_speed)
    SIM_set_attribute(conf.sim, "real-time-ms-interval", check_interval)
    SIM_set_attribute(conf.sim, "real-time-enable", 1)

new_command("enable-real-time-mode", set_real_time_mode_cmd,
            [arg(int_t, "speed",          "?", 100),
             arg(int_t, "check_interval", "?", 1000)],
            alias = "",
            type  = ["Execution", "Speed"],
            short = "set real time mode for Simics",
            doc = """
In some cases Simics might run faster (in real-time) than the machine
it simulates; this can happen if the OS is in a tight idle loop or an
instruction halts execution waiting for an interrupt.
Running faster than the simulated machine can cause problems for interactive
programs which might time-out faster than what the user can handle.

With the <cmd>enable-real-time-mode</cmd> command Simics will periodically check
its actual running speed and sleep for a while if it is too high.
This also reduces Simics CPU usage.
<arg>speed</arg> specifies the percentage (as an integer) of the how fast the Simics
target machine is allowed to run compared to the host machine; default is 100%.
<arg>check_interval</arg> specifies how often the measurement should take place in
milliseconds of the simulator time; default is 1000.

The <cmd>disable-real-time-mode</cmd> will deactivate any real-time behavior and
Simics will run as fast as possible again.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3195")



#
# -------------------- disable-real-time-mode --------------------
#
def disable_real_time_mode_cmd():
    assert_cpu()
    SIM_set_attribute(conf.sim, "real-time-enable", 0)

new_command("disable-real-time-mode", disable_real_time_mode_cmd,
            [],
            alias = "",
            short = "disable real time mode for Simics",
            doc_with = "enable-real-time-mode", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3229")


#
# -------------------- other memory-space commands --------------------
#

def get_memory_space_info(obj):
    return [(None,
             [("Snoop device", obj.snoop_device),
              ("Timing model", obj.timing_model)])]

new_info_command("memory-space", get_memory_space_info)

def get_port_space_info(obj):
    return []

new_info_command("port-space", get_port_space_info)

#
# -------------------- context --------------------
#

def context_on_cmd(obj):
    SIM_set_attribute(obj, "active", 1)

def context_off_cmd(obj):
    SIM_set_attribute(obj, "active", 0)

new_command("on", context_on_cmd,
            [],
            namespace = "context",
            type  = ["Symbolic Debugging", "Debugging"],
            short = "switch on context object",
            doc = """
<b>&lt;context&gt;.on</b> activates the effects of a context object,
i.e., breakpoints on virtual addresses.  <b>&lt;context&gt;.off</b> deactivates a
context object.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3262")

new_command("off", context_off_cmd,
            [],
            namespace = "context",
            short = "switch off context object",
            doc_with = "<context>.on", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3272")

def obj_set_context_cmd(cpu, ctx_name):
    try:
        ctx = SIM_get_object(ctx_name)
    except SimExc_General:
        ctx = SIM_new_object("context", ctx_name)
        pr("New context '%s' created.\n" % ctx_name)

    if ctx.classname != "context":
        pr("%s is not a context object.\n" % ctx_name)
        return

    if ctx.symtable:
        st = ctx.symtable
        if not st.arch_compat[cpu.architecture]:
            print ("Context's symtable %s has architecture %s; cannot attach."
                   % (st.name, st.arch))
            return
        st.arch = cpu.architecture
    cpu.current_context = ctx

def set_context_cmd(ctx_name):
    obj_set_context_cmd(current_processor(), ctx_name)

new_command("set-context", set_context_cmd,
            [arg(str_t, "context",
                 expander = object_expander("context"))],
            type  = ["Symbolic Debugging", "Debugging"],
            see_also = ['new-context', '<context>.symtable'],
            short = "set the current context of a CPU",
            doc = """
Sets the current context of the processor <i>cpu</i> (or the selected
cpu) to <i>context</i>. If the context does not exist, it is created.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3301")

new_command("set-context", obj_set_context_cmd,
            [arg(str_t, "context",
                 expander = object_expander("context"))],
            namespace = "processor",
            short = "set the current context of a CPU",
            doc_with = "set-context", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3311")

def new_context_cmd(name):
    try:
        SIM_get_object(name)
        pr("An object called '%s' already exists.\n" % name)
        return
    except:
        try:
            SIM_new_object("context", name)
        except:
            pr("Error creating context '%s'\n" % name)

new_command("new-context", new_context_cmd,
            [arg(str_t, "name")],
            type  = ["Symbolic Debugging", "Debugging"],
            see_also = ['set-context', '<context>.symtable'],
            short = "create a new context",
            doc = """
Create a new context object called <i>name</i>. The context is initially not
bound to any processor.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3329")

def get_context_info(ctx):
    return [(None,
             [("Symbol table", ctx.symtable)])]

new_info_command("context", get_context_info)

def get_context_status(ctx):
    return [(None,
             [("Active", iff(ctx.active, "yes", "no"))])]

new_status_command("context", get_context_status)

def context_until_active(ctx, direction):
    global _do_disassemble

    def context_change(data, ctx, arg):
        SIM_break_simulation("")

    hap_handle = SIM_hap_add_callback_obj(
        "Core_Context_Change", ctx, 0, context_change, None)

    _do_disassemble = 1
    try:
        _started_sim()
        if direction == 'reverse':
            VT_reverse(0)
        else:
            SIM_continue(0)
    finally:
        SIM_hap_delete_callback_id("Core_Context_Change", hap_handle)

def context_run_until_active_cmd(ctx):
    context_until_active(ctx, 'forward')

new_command("run-until-active", context_run_until_active_cmd,
            [],
            namespace = "context",
            short = "run until context becomes active",
            doc = """
Run until context become active.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3372")

def context_reverse_until_active_cmd(ctx):
    context_until_active(ctx, 'reverse')

new_command("reverse-until-active", context_reverse_until_active_cmd,
            [],
            namespace = "context",
            short = "reverse until context becomes active",
            doc = """
Reverse until context become active.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3382")

step_cmds = ((True, "step-line", ["step", "s"],
              Step_State_Command_Step,
              "run to the next source line"),
             (False, "step-instruction", ["stepi", "si"],
              Step_State_Command_Stepi,
              "run to the next instruction"),
             (True, "reverse-step-line", ["rstep", "rs"],
              Step_State_Command_Unstep,
              "back to the previous source line"),
             (False, "reverse-step-instruction", ["rstepi", "rsi",
                                                  "unstep-instruction", "ui"],
              Step_State_Command_Unstepi,
              "back to the previous instruction"),
             (True, "next-line", ["next", "n"],
              Step_State_Command_Next,
              "run to the next source line, skipping subroutine calls"),
             (True, "next-instruction", ["nexti", "ni"],
              Step_State_Command_Nexti,
              "run to the next instruction, skipping subroutine calls"),
             (True, "reverse-next-line", ["rnext", "rn"],
              Step_State_Command_Prev,
              "back to the previous source line, skipping subroutine calls"),
             (True, "reverse-next-instruction", ["rnexti", "rni"],
              Step_State_Command_Previ,
              "back to the previous instruction, skipping subroutine calls"),
             (True, "finish-function", ["finish", "fin"],
              Step_State_Command_Finish,
              "finish the current function"),
             (True, "uncall-function", ["uncall"],
              Step_State_Command_Uncall,
              "go back to when the current function was called"))

def step_cmd(ctx, cmd):
    global _do_disassemble
    def src_step_callback_ordered(ctx, p1, p2):
        SIM_break_simulation("")
    def src_step_callback(data, ctx, cpu):
        VT_in_time_order(ctx, src_step_callback_ordered, 0, 0)
    if ctx == None:
        ctx = SIM_current_processor().current_context
    run = ctx.iface._source_step.source_step(ctx, cmd)
    if (run & (Step_Flag_Forward | Step_Flag_Backward)) != 0:
        _do_disassemble = 1
        hap_handle = SIM_hap_add_callback(
            "Core_Source_Step", src_step_callback, None)
        try:
            if run == Step_Result_Run_Backward:
                VT_reverse(0)
            else:
                SIM_continue(0)
        finally:
            SIM_hap_delete_callback_id("Core_Source_Step", hap_handle)

for glob, name, alias, cmd, desc in step_cmds:
    for namespace in ["context"] + [[], [""]][glob]:
        if namespace:
            f = (lambda cmd: lambda ctx: step_cmd(ctx, cmd))(cmd)
        else:
            f = (lambda cmd: lambda: step_cmd(None, cmd))(cmd)
        new_command(name, f, [],
                    type = ["Symbolic Debugging", "Debugging"],
                    alias = alias,
                    namespace = namespace,
                    repeat = f,
                    see_also = ["<context>.%s" % n for (g, n, a, c, d)
                                in step_cmds if n != name],
                    short = desc,
                    doc = """

<b>step-line</b> causes the simulation to run until it reaches another
source line. <b>reverse-step-line</b> does the same thing, except for
running backwards.

<b>next-line</b> causes the simulation to run until it reaches another
source line, but will not stop in subroutine calls.
<b>reverse-next-line</b> is the same as <b>next-line</b>, except for
running backwards. <b>next-instruction</b> and
<b>reverse-next-instruction</b> are like <b>next-line</b> and
<b>reverse-next-line</b>, respectively, except for stepping just one
instruction instead of an entire source line.

<b>finish-function</b> causes the simulation to run until the current
function has returned. <b>uncall-function</b> causes the simulation to
run backwards until just before the current function was called.

These commands can either be called as context namespace commands,
e.g., <i>context</i><tt>.step-line</tt>, in which case the command
will apply to that context; or not, e.g., <tt>step-line</tt>, in which
case the command will operate on the current context of the current
processor.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3448")

#
# ----------------------- devs -----------------------
#

def devs_cmd(objname):
    all_objs = SIM_get_all_objects()

    if objname == "":
        list = all_objs
    else:
        try:
            list = [ SIM_get_object(objname) ]
        except Exception:
            print "No device object: %s" % objname
            return

    first = 1
    for obj in list:
        try:
            count = obj.access_count
        except Exception, e:
            continue
        dev_name = obj.name
        dev_str = "%8d  %-13s " % (count, dev_name)
        for obj2 in all_objs:
            try:
                map = obj2.map
            except Exception, e:
                continue
            map.sort()
            for line in map:
                if line[1].name == dev_name:
		    if first:
		        print " Count    Device        Space            Range                                   Func"
			first = 0
                    pr(dev_str)
                    dev_str = "                        "
                    pr("%-16s 0x%016x - 0x%016x %4d\n" % (
                       obj2.name,
                       line[0],
                       long(line[0]) + line[4] - 1,
                       line[2]))
    if first:
	print "No mappings found"

new_command("devs", devs_cmd,
            args  = [arg(str_t, "object-name", "?", "", expander = conf_object_expander)],
            type  = ["Configuration", "Inspecting Simulated State"],
            short = "list all devices in Simics",
            doc = """
Print a list of all devices in Simics, with information about how
many times each device has been accessed, and where it is mapped.
The mappings are presented as start and end offsets within a
named memory space. The function number associated with each
different mapping for a device is also printed.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3525")

#
# -------------------- break-io, trace-io --------------------
#

class io_tracker(tracker):
    def __init__(self, stop, cmd, short, doc, type, see_also = []):
        tracker.__init__(self, stop, cmd, "device", self.expander,
                         short, doc, group = type, see_also = see_also)
        self.map = {}

    def show(self, arg, obj, memop):
        if SIM_mem_op_is_from_cpu(memop):
            cpu = memop.ini_ptr
        else:
            cpu = current_processor()
        if memop.size <= 8:
            if cpu.big_endian:
                value = number_str(SIM_get_mem_op_value_be(memop), 16)
            else:
                value = number_str(SIM_get_mem_op_value_le(memop), 16)
            value_string = "%s (%s)" % (value, iff(cpu.big_endian, "BE", "LE"))
        else:
            value_string = ""
        print ("[%s -> %s] %s: %s %d %s"
               % ((memop.ini_ptr and memop.ini_ptr.name), obj.name,
                  iff(SIM_mem_op_is_read(memop), "Read", "Write"),
                  number_str(memop.physical_address, 16),
                  memop.size, value_string))

    def list(self):
        print "%s enabled for these devices:" % iff(self.stop, "breaking", "tracing")
        for obj in self.map.keys():
            print "  %s" % obj.name
        

    def resolve_target(self, target):
        return SIM_get_object(target)

    def is_tracked(self, obj):
        return self.map.has_key(obj)

    def is_device(self, obj):
        try:
            obj.log_buffer
            return 1
        except:
            return 0

    def get_all_devices(self):
        return filter(self.is_device, SIM_get_all_objects())

    def expander(self, string):
        return get_completions(string, [ obj.name for obj in self.get_all_devices() ]);

    def install_hap(self, obj):
        r = SIM_hap_add_callback_obj("Core_Device_Access_Memop", obj, 0, self.callback, None)
        self.map[obj] = r

    def uninstall_hap(self, obj):
        r = self.map[obj]
        SIM_hap_delete_callback_obj_id("Core_Device_Access_Memop", obj, r)
        del self.map[obj]

    def track_all(self):
        for obj in self.get_all_devices():
            if not self.is_tracked(obj):
                self.install_hap(obj)

    def track_none(self):
        for obj in self.map.keys():
            self.uninstall_hap(obj)

    def track_on(self, obj):
        if self.is_tracked(obj):
            return
        if not self.is_device(obj):
            print "I/O breakpoints are not possible on %s" % obj.name
            return
        self.install_hap(obj)
        
    def track_off(self, obj):
        if self.is_tracked(obj):
            self.uninstall_hap(obj)


trace_io_cmds = io_tracker(0, "trace-io",
                           short = "trace device accesses",
                           type = "inspect/change",
                           see_also = [ "break-io" ],
                           doc = """
Enables and disables tracing of device accesses.  When this is
enabled, every time the specified device is accessed during simulation
a message is printed.

The <i>device</i> parameter specifies the device object that should be
traced.

Instead of an object name, the <tt>-all</tt> flag may be given.  This
will enable or disable tracing of all devices.
""")

break_cr_cmds = io_tracker(1, "break-io",
                           short = "break on device accesses",
                           type = "breakpoint",
                           see_also = [ "trace-io", "<breakpoint>.break" ],
                           doc = """

Enables and disables breaking simulation on device accesses.  When
this is enabled, every time the specified device is accessed during
simulation a message is printed and the simulation stops.

The <i>device</i> parameter specifies which device object should be
traced.

Instead of an object name, the <tt>-all</tt> flag may be given.  This
will enable or disable breaking on accesses to all device.
""")


#
# -------------------- magic-break-enable --------------------
#

def magic_enable_cmd():
    VT_magic_break_enable(1)

def magic_disable_cmd():
    VT_magic_break_enable(0)

def magic_query_cmd():
    return VT_magic_break_query()

new_command("magic-break-enable", magic_enable_cmd,
            [],
            type  = ["Breakpoints", "Debugging", "Profiling"],
            short = "install magic instruction hap handler",
            doc = """
Installs (<tt>magic-break-enable</tt>) or removes
(<tt>magic-break-disable</tt>) the magic breakpoint handler. A magic
breakpoint is a magic instruction with argument 0, except on the SPARC
target, where it is a magic instruction with the top 6 bits of the
22-bit parameter field set to 000100 (binary). Note that <tt>break-hap
Core_Magic_Instruction</tt> will break on all magic instructions.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3669")

new_command("magic-break-disable", magic_disable_cmd,
            [],
            short = "remove magic instruction hap handler",
            doc_with = "magic-break-enable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3682")

new_command("magic-break-query", magic_query_cmd,
            [],
            short = "returns 1 if magic instruction handler is installed",
            doc_with = "magic-break-enable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3687")


#
# -------------------- instruction-profile-mode --------------------
#

def ipm_expander(string):
    return get_completions(string, ["no-instruction-profile", "instruction-branch-profile", "instruction-cache-access-trace","instruction-fetch-trace"])

ipm_mode_translation = {"no-instruction-profile" : "no-instruction-fetch",
                        "instruction-branch-profile" : "no-instruction-fetch",
                        "instruction-cache-access-trace" : "instruction-cache-access-trace",
                        "instruction-fetch-trace" : "instruction-fetch-trace"}

def obsolete_ipm_hap(mode, obj):
    for cpu in SIM_get_all_processors():
        cpu.instruction_fetch_mode = mode

def obsolete_ipm(mode):
    print "If you want to profile instructions, use the instruction profiling"
    print "system described in the User Guide."
    print
    print "If you want your memory hierarchy to receive instruction fetches,"
    print "use the instruction-fetch-mode command."
    print
    print "This command will now set the instruction-fetch-mode on all CPUs"
    print "according to the mode given as argument."
    
    if mode:
        if (SIM_initial_configuration_ok()):
            obsolete_ipm_hap(ipm_mode_translation[mode], None)
        else:
            SIM_hap_add_callback("Core_Initial_Configuration", obsolete_ipm_hap, ipm_mode_translation[mode])

new_command("instruction-profile-mode", obsolete_ipm,
            args = [arg(str_t, "mode", "?", "", expander = ipm_expander)],
            alias = "ipm",
            type = "deprecated commands",
            deprecated = "instruction-fetch-mode",
            short="set or get current mode for instruction profiling",
            doc = """
            Sets the instruction fetch mode of all cpus on the system according to the mode passed as argument.
            """, filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3725")

def instruction_fetch_mode(cpu, mode):
    if mode:
        cpu.instruction_fetch_mode = mode
    else:
        print cpu.name + ":", cpu.instruction_fetch_mode

def ifm_expander(string):
    return get_completions(string, ["no-instruction-fetch", "instruction-cache-access-trace", "instruction-fetch-trace"])

new_command("instruction-fetch-mode", instruction_fetch_mode,
            args = [arg(str_t, "mode", "?", "", expander = ifm_expander)],
            alias = "ifm",
            type = ["Execution", "Profiling", "Tracing"],
            namespace = "processor",
            short="set or get current mode for instruction fetching",
            doc = """
This command selects how instruction fetches are sent for the memory hierarchy
during simulation. If set to <i>no-instruction-fetch</i>, the memory hierarchy
won't receive any instruction fetch. If set to
<i>instruction-cache-access-trace</i>, the memory hierarchy will receive one
(and only one) instruction fetch every time a new cache line is accessed. The
size of this cache line is defined by the attribute
<i>instruction-fetch-line-size</i> in the processor object. If set to
<i>instruction-fetch-trace</i>, all instruction fetches will be visible. Note
that on x86 target, <i>instruction-cache-trace-access</i> is not available. On
some other, <i>instruction-fetch-trace</i> is actually
<i>instruction-cache-trace-access</i> with a line size equal to the instruction
size (sparc-v9). Using this command without argument will print out the current
mode.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3744")

def instruction_fetch_mode_global(mode):
    for cpu in SIM_get_all_processors():
        instruction_fetch_mode(cpu, mode)

new_command("instruction-fetch-mode", instruction_fetch_mode_global,
            args = [arg(str_t, "mode", "?", "", expander = ifm_expander)],
            alias = "ifm",
            type = ["Execution", "Profiling", "Tracing"],
            short="set or get current mode for instruction fetching",
            doc_with = "<processor>.instruction-fetch-mode", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3770")

def istc_enable():
    try:
        if conf.sim.istc == "off":
            print "Turning I-STC on"
            conf.sim.istc = "on"
        else:
            print "I-STC was already turned on"
    except:
        print "Enable I-STC failed. Make sure a configuration is loaded."

new_command("istc-enable", istc_enable,
            args = [],
            type = ["Execution", "Speed"],
            short="enable I-STC",
            group_short = "enable or disable internal caches",
            doc = """
These commands are for advanced users only. They allow the user to control the
usage of Simics internal caches. The Simulator Translation Caches (STCs) are
designed to increase execution performance. The D-STC caches data translations
(logical to physical to real (host) address), while the I-STC caches
instruction translations of taken jumps. By default the STCs are <b>on</b>.
When a memory hierarchy is connected (such as a cache module) it must have been
designed to work along with the STCs otherwise it may not be called for all
the memory transactions it is interested in. These commands can be used to
detect if too many translations are kept in the STCs, causing the simulation
to be faulty. Turning the STCs off means that current contents will be
flushed and no more entries will be inserted into the STCs.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3787")

def istc_disable():
    try:
        if conf.sim.istc == "on":
            print "Turning I-STC off and flushing old data"
            conf.sim.istc = "off"
        else:
            print "I-STC was already turned off"
    except:
        print "Disable istc failed. Make sure a configuration is loaded."

new_command("istc-disable", istc_disable,
            args = [],
            short = "disable I-STC",
            doc_with = "istc-enable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3816")

def dstc_enable():
    try:
        if conf.sim.dstc == "off":
            print "Turning D-STC on"
            conf.sim.dstc = "on"
        else:
            print "D-STC was already turned on"
    except:
        print "Enable D-STC failed. Make sure a configuration is loaded."

new_command("dstc-enable", dstc_enable,
            args = [],
            short = "enable D-STC",
            doc_with = "istc-enable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3831")

def dstc_disable():
    try:
        if conf.sim.dstc == "on":
            print "Turning D-STC off and flushing old data"
            conf.sim.dstc = "off"
        else:
            print "D-STC was already turned off"
    except:
        print "Disable D-STC failed. Make sure a configuration is loaded."

new_command("dstc-disable", dstc_disable,
            args = [],
            short = "disable D-STC",
            doc_with = "istc-enable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3846")

def stc_status():
    try:
        if conf.sim.dstc == "on":
            print "D-STC is currently *ON*"
        else:
            print "D-STC is currently *OFF*"
        if conf.sim.istc == "on":
            print "I-STC is currently *ON*"
        else:
            print "I-STC is currently *OFF*"
    except:
        print "Failed getting stc status. Make sure a configuration is loaded."

new_command("stc-status", stc_status,
            args = [],
            short = "show I- and D-STC status",
            doc_with = "istc-enable", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3864")

def default_address_not_mapped_handler(arg, space, pa, access_type, size):
    print "Access at 0x%x in %s where nothing is mapped." % (pa, space.name)
    raise SimExc_Break, "Address not mapped"

try:
    SIM_hap_add_callback("Core_Address_Not_Mapped",
                         default_address_not_mapped_handler, None)
except:
    import sys
    sys.stderr.write("Core_Address_Not_Mapped install failed. "
                     "(Expected during doc-build.)\n")

#
# ram commands
#

def get_ram_info(obj):
    size = obj.image.size
    mult = ''
    if (size % 1024) == 0:
        size = size // 1024
        mult = 'K'
        if (size % 1024) == 0:
            size = size // 1024
            mult = 'M'
            if (size % 1024) == 0:
                size = size // 1024
                mult = 'G'
        
    return [ (None,
              [ ("Image", obj.image),
                ("Image size", "%d%s" % (size, mult)) ] ) ]

sim_commands.new_info_command('ram', get_ram_info)
sim_commands.new_info_command('rom', get_ram_info)
# No status command, since there is no status, really


class image_source:
    def __init__(self, image):
        self.image = image
        self.outside = 0

    def addr_prefix(self):
        return ""

    def get_byte(self, addr):
        try:
            return self.image.byte_access[addr]
        except:
            self.outside = 1
            return "--"

    def have_tag(self, addr):
        return 0

    def finish(self):
        if self.outside:
            pr("addresses marked \"--\" are outside the image\n")

def image_x_cmd_repeat(obj, offset, length):
    global _last_image_x_addr
    _last_image_x_addr += length
    image_x_cmd(obj, _last_image_x_addr, length)

def image_x_cmd(obj, offset, length):
    global _last_image_x_addr
    _last_image_x_addr = offset
    hexdump(image_source(obj), offset, length, align=False)

new_command("x", image_x_cmd,
            [arg(int_t, "offset"), arg(int_t, "size", "?", 16)],
            type = ["Memory", "Inspecting Simulated State"],
            short = "examine image data",
            namespace = "image",
            repeat = image_x_cmd_repeat,
            doc = """
Displays <arg>length</arg> bytes starting at <arg>offset</arg> from the
image.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3939")

def image_set_cmd(image, address, value, size, little_endian, big_endian):
    if size < 1 or size > 8:
        print "size must be 1-8 bytes."
        return

    if little_endian and big_endian:
        print "Cannot use both -l and -b."
        return

    if not little_endian and not big_endian:
        if current_processor().big_endian:
            big_endian = 1
        else:
            little_endian = 1

    if address + size > image.size:
        print "address outside image"
        return

    values = [ (value >> (i * 8)) & 0xff for i in range(size) ]
    if big_endian:
        values.reverse()

    for i in range(size):
        image.byte_access[address + i] = values[i]

new_command("set", image_set_cmd,
            [arg(int_t, "address"),
             arg(int_t, "value"),
             arg(int_t, "size", "?", 4),
             arg(flag_t, "-l"), arg(flag_t, "-b")],
            type = ["Memory", "Changing Simulated State", "Disk"],
            short = "set bytes in image to specified value",
            see_also = ["set"],
            namespace = "image",
            doc = """
Sets <arg>size</arg> bytes in an image at offset <arg>address</arg> to
<arg>value</arg>. The default <arg>size</arg> is 4 bytes, but can be anywhere
between 1 and 8 inclusive.

If <arg>value</arg> is larger than the specified size, behavior is undefined.

The <arg>-l</arg> and <arg>-b</arg> flags are used to select little-endian and
big-endian byte order, respectively. If neither is given, the byte order of the
currently selected processor is used.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="3975")


def image_save(image, filename, start, length):
    try:
        image.iface.image.save_to_file(image, filename, start, length)
    except Exception, msg:
        print msg

new_command("save", image_save,
            [ arg(filename_t(), "filename"),
              arg(int_t, "start-byte", "?", 0),
              arg(int_t, "length", "?", 0) ],
            type = ["Memory", "Disk", "Configuration"],
            short = "save image to disk",
            namespace = "image",
            doc = """
Writes the image binary data (in raw form) to <arg>filename</arg>. If
<arg>start</arg> and/or <arg>length</arg> are given, they specify the start
offset and number of bytes to write respectively; otherwise, the whole image is
copied.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4002")

def image_save_diff(image, filename):
    try:
        os.stat(filename)
        print "%s already exists." % filename
        SIM_command_has_problem()
        return
    except:
        pass
    try:
        image.iface.image.save_diff(image, filename)
    except Exception, msg:
        print msg

new_command("save-diff-file", image_save_diff,
            [ arg(filename_t(), "filename") ],
            type = ["Memory", "Disk", "Configuration"],
            short = "save changes since last checkpoint",
            see_also = ['<image>.add-diff-file', '<image>.save'],
            namespace = 'image',
            doc = """
Writes changes to the image since the last checkpoint to a named file
in craff format.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4028")
    
def image_add_partial_diff(image, filename, start, size):
    files = image.files
    files += [[filename, "ro", start, size]]
    try:
        image.files = files
    except Exception, msg:
        print "Error adding", filename, "to", image.name, ":", msg
        SIM_command_has_problem()

def image_add_diff(image, filename):
    image_add_partial_diff(image, filename, 0, 0)

new_command("add-diff-file", image_add_diff,
            [ arg(filename_t(), "filename") ],
            type = ["Memory", "Disk", "Configuration"],
            short = "add a diff file to the image",
            see_also = ['<image>.save-diff-file'],
            namespace = "image",
            doc = """
Adds a diff file to the list of files for an image. The diff file was typically
created with <cmd>save-diff-file</cmd>, or by a saved configuration.
This should not be done if the image contains changed (unsaved) data.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4050")

new_command("add-partial-diff-file", image_add_partial_diff,
            [ arg(filename_t(), "filename"),
              arg(int_t, "start"),
              arg(int_t, "size") ],
            type = ["Memory", "Disk", "Configuration"],
            short = "add a partial diff file to the image",
            see_also = ['<image>.add-diff-file', '<image>.save-diff-file'],
            namespace = "image",
            doc = """
Adds a partial diff file to the list of files for an image. The diff
file was typically created with the 'save-diff-file' command, by one of
the dump-*-partition commands, or by a saved configuration.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4061")
                
def binary_amount(n):
    suffixes = "Byte kB MB GB TB".split()
    import math
    if n <= 0:
        index = 0
    else:
        index = min(int(math.log(n, 1024)), len(suffixes) - 1)
    return "%.4g %s" % (n / float(1 << (index * 10)), suffixes[index])

def set_memory_limit_cmd(limit, swapdir):
    if limit == None and not swapdir:
        lim = SIM_get_class_attribute("image", "memory-limit")
        if lim:
            print "Image memory limited to", binary_amount(lim)
        else:
            print "Image memory not limited"
        sd = conf.prefs.swap_dir
        print "Swap directory:", sd
        return

    if limit < 0:
        SIM_command_has_problem()
        print "Illegal memory limit."
        return
    elif limit > 0:
        limit = limit << 20
        if limit > conf.sim.host_phys_mem:
            print "Warning: Limit larger than the amount of physical memory."
            return
        sim.classes['image'].classattrs.memory_limit = limit
        print "Image memory limited to", binary_amount(limit)
    elif limit == 0:
        sim.classes['image'].classattrs.memory_limit = limit
        print "Image memory not limited."

    if swapdir:
        conf.prefs.swap_dir = swapdir
        # swap dir may be mangled, so print out the result
        print "Swap dir set to", conf.prefs.swap_dir

new_command("set-memory-limit", set_memory_limit_cmd,
            [ arg(int_t, "limit", "?", None),
              arg(str_t, "swapdir", "?", None) ],
            type = "image commands",
            short = "limit memory usage",
            doc = """
Limits the in-memory footprint of all image objects to <arg>limit</arg>
megabytes. This only limits the memory consumed by image pages in memory.
While this is typically a very large part of Simics's memory usage, other
data structures are not limited by this command.

If <arg>limit</arg> is zero, the memory limit is removed.
If <arg>swapdir</arg> is specified, it indicates a directory to use for
swap files. If no argument is given, the current setting is
displayed.

Simics sets a default memory limit at startup that depends on the amount of
memory, and number of processors, on the host system.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4115")


def set_default_limit():
    total = conf.sim.host_phys_mem
    ncpus = conf.sim.host_num_cpus

    if total > sys.maxint:
        # in 32-bit simics limit to 2GB (more might be OK on some systems)
        total = sys.maxint

    # remove 64MB for system
    total -= 0x4000000

    # lowest limit is 256MB, or the amount of memory in the system
    min_total = min(total, 0x10000000)

    # use less memory on multi-pro
    ncpus = (ncpus + 1) / 2

    # leave some memory for non-image stuff
    total = int(max(total * 0.7 / ncpus, min_total)) & ~0xfffff

    SIM_set_class_attribute("image", "memory-limit", total)

set_default_limit()

#
# ---------------------- data profiler commands ---------------------
#

def data_profiler_clear_cmd(obj):
    try:
        dpi = obj.iface._data_profiler
    except:
        pr("%s is not a data profiler!\n" % obj)
        return
    dpi.clear(obj)

new_command("clear", data_profiler_clear_cmd,
            args = [],
            namespace = "data-profiler",
            type = ["Profiling"],
            short = "clear data profiler",
            doc = """
Reset all counters of the data profiler to zero.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4172")

#
# -------------------- address profiler commands --------------------
#

def address_profile_info_cmd(obj, sum, max):
    try:
        SIM_get_interface(obj, "address-profiler")
        api = obj.iface.address_profiler
    except:
        pr("%s is not an address profiler!\n" % obj)
        return
    num = api.num_views(obj)
    if num == 0:
        pr("%s has no views defined!\n" % obj)
        return
    pr("%s has %d address profiler view%s:\n" % (obj.name, num,
                                                 ["s", ""][num == 1]))
    for i in range(num):
        addr_bits = api.address_bits(obj, i)
        maxaddr = (1 << addr_bits) - 1
        pr("View %d: %s\n" % (i, api.description(obj, i)))
        gran_log2 = api.granularity_log2(obj, i)
        pr("   %d-bit %s addresses, granularity %d byte%s\n" %
           (addr_bits,
            ["virtual", "physical"][api.physical_addresses(obj, i)],
            1 << gran_log2, ["s", ""][gran_log2 == 0]))
        if sum:
            pr("   Total counts: %d\n" % api.sum(obj, i, 0, maxaddr))
        if max:
            pr("   Maximal count: %d\n" % api.max(obj, i, 0, maxaddr))

new_command("address-profile-info", address_profile_info_cmd,
            args = [arg(flag_t, "-sum"), arg(flag_t, "-max")],
            namespace = "address_profiler",
            type = ["Profiling"],
            short = "general info about an address profiler",
            doc = """
Print general info about an object implementing the address-profiler
interface, such as a list of the available views. If the <tt>-sum</tt>
or <tt>-max</tt> flags are given, will also print the sum or max of
each view over the entire address space.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4211")

def aprof_views_cmd(cpu, add, remove, view, clear):

    def indexof(aprof, view):
        index = 0
        for ap, v in cpu.aprof_views:
            if aprof == ap and view == v:
                return index
            index += 1
        return -1

    if clear:
        if add or remove:
            print "Error! Too many options."
            return
        cpu.aprof_views = []
    elif add:
        if remove:
            print "Error! Cannot specify both add and remove."
            return
        index = indexof(add, view)
        if index >= 0:
            print "View %d of %s is already selected." % (view, add.name)
            return
        numviews = add.iface.address_profiler.num_views(add)
        if view < 0 or view >= numviews:
            print "Error! View %d is out of range for %s." % (view, add.name)
            return
        temp = cpu.aprof_views
        temp.append([add, view])
        cpu.aprof_views = temp
    elif remove:
        index = indexof(remove, view)
        if index < 0:
            print "View %d of %s is not selected." % (view, remove.name)
            return
        temp = cpu.aprof_views
        del temp[index]
        cpu.aprof_views = temp
    else:
        if len(cpu.aprof_views) < 1:
            print "No address profiler views selected for %s." % cpu.name
            return
        print ("The following address profiler views are selected for %s:"
               % cpu.name)
        i = 1
        for ap, view in cpu.aprof_views:
            api = ap.iface.address_profiler
            print ("  %d. (%s) View %d of %s (%s)"
                   % (i, ["virtual", "physical"]
                      [api.physical_addresses(ap, view)],
                      view, ap.name, api.description(ap, view)))
            i += 1

aprof_obj_t = obj_t("address_profiler", "address_profiler")
new_command("aprof-views", aprof_views_cmd,
            args = [arg(aprof_obj_t, "add", spec = "?", default = None),
                    arg(aprof_obj_t, "remove", spec = "?", default = None),
                    arg(int_t, "view", spec = "?", default = 0),
                    arg(flag_t, "-clear")],
            namespace = "processor",
            type = ["Profiling"],
            short = "manipulate list of selected address profiling views",
            doc = """
Manipulate the processor attribute <tt>aprof-views</tt>, which
determines which address profiler views are displayed alongside
disassembled code.

The <i>add</i> and <i>view</i> arguments select an address profiler
view to add to the list. Alternatively, the <i>remove</i> and
<i>view</i> arguments specify an address profiler view to remove from
the list. <i>view</i> defaults to 0 if not specified.

If called with the <tt>-clear</tt> flag, remove all address profiler
views from the list.

If called without arguments, print a detailed list of the currently
selected address profiler views for the processor. """, filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4276")

#
# ------- address profiler toplist --------
#
def address_profile_toplist_cmd(ap, symtbl, samples, start, stop, view, cnt_ival):
    try:
        SIM_get_interface(ap, "address-profiler")
        api = ap.iface.address_profiler
    except:
        pr("%s is not an address profiler!\n" % ap)
        return

    num_views = api.num_views(ap)
    if not num_views > view:
        pr("%s does not have view %d!\n" % (ap, view))
    gran = 2**(api.granularity_log2(ap, view))

    #
    # sample_list = [[count, address], ...]
    #
    sample_list = [[0L, 0L]] * samples
    for (count, addr) in api.iter(ap, view, start, stop):
        if count > sample_list[-1][0]:
            sample_list[-1] = [count, addr]
            sample_list.sort(lambda a,b: cmp(b[0], a[0]))
    sample_list.sort(lambda a,b: cmp(a[1], b[1]))

    #
    # top_list = [[count, address, length], ...]
    #
    top_list = []
    for (s_cnt, s_addr) in sample_list:
        match = False
        for entr in top_list:
            if entr[1] + entr[2] == s_addr and entr[0] - cnt_ival <= s_cnt and entr[0] + cnt_ival >= s_cnt:
                match = True
                entr[2] += gran
        if not match:
            top_list.append([s_cnt, s_addr, gran])
    top_list.sort()
    top_list.reverse()

    entry = 1
    if top_list[0][0] == 0:
        return
    print "Data Profile Toplist (count, address, source):"
    for (count, addr, length) in top_list:
        if count == 0:
            break
        if symtbl:
            pos = symtbl.source_at[addr]
            if pos:
                pstr = "%s, %s" % (pos[0], pos[2])
            else:
                pstr = "unknown"
        else:
            pstr = "unknown"
        if length > gran:
            print "%3d. %12d 0x%08x - 0x%08x in %s" % (
                entry, count, addr, addr + length - gran, pstr)
        else:
            print "%3d. %12d 0x%08x %s" % (entry, count, addr, pstr)
        entry += 1


new_command("address-profile-toplist", address_profile_toplist_cmd,
            args = [arg(obj_t("symtable", "symtable"), "symtable", spec = "?", default = None),
                    arg(int_t, "samples", spec = "?", default = 100),
                    arg(int_t, "start", spec = "?", default = 0x0),
                    arg(int_t, "stop", spec = "?", default = 0xfffffffc),
                    arg(int_t, "view", spec = "?", default = 0),
                    arg(int_t, "count_interval", spec = "?", default = 1)],
            namespace = "address_profiler",
            type  = ["Profiling"],
            short = "print toplist of address profiling data",
            doc = """
Print address profiling regions sorted by count. The <i>symtable</i>
attribute can be used to map data profiling regions in form of
physical addresses to source function and file information.

The <i>samples</i> argument specifies the number of sampling points
used to create the list containing the highest count. The sampling
range is determined by <i>start</i> and <i>stop</i>. The default
values are 100 samples in the interval 0x0 - 0xfffffffc. The
granularity is defined by the data profiler object.

The <i>view</i> attribute selects the address profiler view.

The <i>count_interval</i> attribute defines the range in which sampled
data regions will match even thought the data profiler count is not
equal. Ex. Assume that the samples in the region 0x20c - 0x20c has a
count of 4711 and region 0x20d - 0x20f a count of 4713. The regions
will be considered on region if <i>count_interval</i> is 4 but not if
1.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4364")


def rshift_round_up(x, s):
    return (x + (1 << s) - 1) >> s

def pow2_bytes_to_str(n):
    orig_n = n
    if n < 10:
        return "%d byte%s" % (1 << n, ["s", ""][n == 0])
    for prefix in ["kilo", "Mega", "Giga", "Tera", "Peta", "Exa"]:
        n -= 10
        if n < 10:
            return "%d %sbyte%s" % (1 << n, prefix, ["s", ""][n == 0])
    return "2^%d bytes" % orig_n

# Return a string representation of num (positive) of at most maxlen
# characters. Use prefixes (and round up) if necesary. The string
# representations of zero and overflow are configurable. If
# minprefixnum is given, num will be forced to use the prefix that
# minprefixnum would have gotten (or bigger), even in the face of
# precision loss.
def num_to_str(num, maxlen, zero = "0", almostzero = None,
               overflow = "inf", minprefixnum = 0):
    if num == 0:
        return zero
    pnum = max(num, minprefixnum)
    pstr = "%d" % pnum
    if len(pstr) <= maxlen:
        return "%d" % num
    for suffix in ["k", "M", "G", "T", "P", "E"]:
        num = num/1000
        pnum = pnum/1000
        pstr = "%d%s" % (pnum, suffix)
        if len(pstr) <= maxlen:
            if num == 0:
                return almostzero
            return "%d%s" % (num, suffix)
    return overflow

def long_and_short_num(num):
    numstr = num_to_str(num, 6)
    numstr2 = "%d" % num
    if numstr != numstr2:
        numstr = "%s (%s)" % (numstr2, numstr)
    return numstr

def address_profile_data_cmd(ap, view, address, cell_bits, row_bits,
                             table_bits, start, stop, maxlines, sameprefix):

    cell_width = 6
    cells_per_line = 3

    def zero_out_low_bits(x, b):
        return (x >> b) << b

    def print_header():
        cellgran = gran - cells_per_line
        sh = cellgran % 4
        cellgran -= sh
        columns = 1 << cells_per_line
        columnheaderdigits = (cells_per_line + sh + 3)/4
        pr("column offsets:\n")
        pr("%*s*" % (int(2 + addr_size), "0x%x" % (1 << cellgran)))
        for i in range(columns):
            pr(" %*s" % (int(cell_width),
                         "0x%0*x" % (int(columnheaderdigits), i << sh)))
        pr("\n")
        pr("-" * (2 + addr_size + 1 + columns*(1 + cell_width)) + "\n")

    def print_lines(start, numlines, gran):
        cellgran = 1 << (gran - cells_per_line)
        tsum = 0
        left = []
        lines = []
        m = 0
        for i in range(numlines):
            left.append("0x%0*x:" % (int(addr_size), start))
            line = []
            for j in range(1 << cells_per_line):
                c = api.sum(ap, view, start, start + cellgran - 1)
                m = max(m, c)
                line.append(c)
                start += cellgran
                tsum += c
            lines.append(line)

        if sameprefix:
            mp = m
        else:
            mp = 0

        for i in range(len(left)):
            pr(left[i])
            for c in lines[i]:
                pr(" %*s" % (int(cell_width), num_to_str(
                    c, cell_width, zero = ".", almostzero = "o",
                    minprefixnum = mp)))
            pr("\n")
        return tsum

    def find_firstlast_counter(a, b, first):
        if a >= b:
            if a == b:
                return a
            return -1

        # Basecase: linear search.
        if b - a < 100:
            if first:
                start = b + 1
                fun = min
            else:
                start = a - 1
                fun = max
            best = start
            for count, addr in api.iter(ap, view, a, b):
                best = fun(best, addr)
            if best == start:
                return -1
            return best

        # Recursion: split interval in half.
        guess = (b + a)/2
        if first:
            for count, addr in api.iter(ap, view, a, guess):
                return find_firstlast_counter(a, addr, first)
            return find_firstlast_counter(guess + 1, b, first)
        else:
            for count, addr in api.iter(ap, view, guess, b):
                return find_firstlast_counter(addr, b, first)
            return find_firstlast_counter(a, guess - 1, first)

    try:
        SIM_get_interface(ap, "address-profiler")
        api = ap.iface.address_profiler
    except:
        pr("%s is not an address profiler!\n" % ap)
        return

    if api.num_views(ap) == 0:
        pr("%s has no views defined!\n" % ap)
        return

    addr_bits = api.address_bits(ap, view)
    lastaddr = (1 << addr_bits) - 1
    addr_size = rshift_round_up(addr_bits, 2) # address size in hex digits
    prof_gran_bits = api.granularity_log2(ap, view)
    gran = mingran = cells_per_line + prof_gran_bits

    bit_args = 0
    if cell_bits != None:
        bit_args += 1
        if cell_bits < prof_gran_bits:
            print "Cells must contain at least %d bits." % prof_gran_bits
            return
    if row_bits != None:
        bit_args += 1
        if row_bits < mingran:
            print "Rows must contain at least %d bits." % mingran
            return
    if table_bits != None:
        bit_args += 1
        if table_bits < mingran:
            print "Table must contain at least %d bits." % mingran
            return
    if bit_args > 1:
        print ("You may specify at most one of cell-bits, row-bits"
               + " and table-bits.")
        return

    # If no range is specified, find the minimal range that contains
    # all counts.
    if start == None and stop == None and address == None and bit_args == 0:
        start = find_firstlast_counter(0, lastaddr, first = 1)
        if start == -1:
            start = 0
            stop = lastaddr
        else:
            stop = find_firstlast_counter(0, lastaddr, first = 0)

        # If user specified address argument, make sure we include it.
        if address != None:
            start = min(start, address)
            stop = max(stop, address)

    # Determine what interval to display.
    if start != None or stop != None:
        if start == None or stop == None:
            print "You must specify both start and stop (or neither of them)."
            return
        if address != None or bit_args != 0:
            print "You cannot specify both start+stop and address+bits."
            return
        for x in [start, stop]:
            if x < 0 or x >= (1 << addr_bits):
                print "0x%x is not a %d-bit address." % (x, addr_bits)
                return
        stop += 1 # let stop point to first address after interval
        while 1:
            if start > stop:
                tmp = start
                start = stop
                stop = start
            start = zero_out_low_bits(start, gran)
            stop = zero_out_low_bits(stop + (1 << gran) - 1, gran)
            length = stop - start
            numlines = rshift_round_up(length, gran)
            if numlines <= maxlines:
                break
            gran += 1
        stop -= 1 # stop points to last address again
    else:
        if address == None:
            address = 0
        elif bit_args == 0:
            print ("You must specify cell-bits, row-bits or table-bits"
                   + " when address is specified.")
            return
        if address < 0 or address >= (1 << addr_bits):
            print "0x%x is not a %d-bit address!" % (address, addr_bits)
            return
        if table_bits != None:
            if table_bits > addr_bits:
                print "Address space is only %d bits!" % addr_bits
                return
            length = 1 << table_bits
            start = zero_out_low_bits(address, table_bits)
            stop = start + length - 1
            while 1:
                numlines = rshift_round_up(length, gran)
                if numlines <= maxlines:
                    break
                gran += 1
        else:
            if row_bits == None:
                row_bits = cell_bits + cells_per_line
            if row_bits > addr_bits:
                print "Address space is only %d bits!" % addr_bits
                return
            gran = row_bits
            numlines = min(maxlines, 1 << (addr_bits - gran))
            start = max(0, (zero_out_low_bits(address, gran)
                            - numlines*(1 << (gran - 1))))

    gran_log2 = api.granularity_log2(ap, view)
    cellgran = gran - cells_per_line
    totalsum = api.sum(ap, view, 0, lastaddr)

    # Print table.
    print "View %d of %s: %s" % (view, ap.name, api.description(ap, view))
    print ("%d-bit %s addresses, profiler granularity %d byte%s" %
           (api.address_bits(ap, view),
            ["virtual", "physical"][api.physical_addresses(ap, view)],
            1 << gran_log2, ["s", ""][gran_log2 == 0]))
    if totalsum > 0:
        print ("Each cell covers %d address bits (%s)."
               % (cellgran, pow2_bytes_to_str(cellgran)))
        print # empty line
        print_header()
        sum = print_lines(start, numlines, gran)
        print # empty line
        print ("%s counts shown. %s not shown."
               % (long_and_short_num(sum), long_and_short_num(totalsum - sum)))
        print # empty line
    else:
        print # empty line
        print "    Profiler is empty."
        print # empty line

new_command("address-profile-data", address_profile_data_cmd,
            args = [arg(int_t, "view", spec = "?", default = 0),
                    arg(int_t, "address", spec = "?", default = None),
                    arg(int_t, "cell-bits", spec = "?", default = None),
                    arg(int_t, "row-bits", spec = "?", default = None),
                    arg(int_t, "table-bits", spec = "?", default = None),
                    arg(int_t, "start", spec = "?", default = None),
                    arg(int_t, "stop", spec = "?", default = None),
                    arg(int_t, "lines", spec = "?", default = 20),
                    arg(flag_t, "-same-prefix")],
            namespace = "address_profiler",
            type = ["Profiling"],
            short = "linear map of address profiling data",
            doc = """
Display a map of (a part of) the address space covered by the address
profiler, and the counts of one of its views associated with each
address. The view is specified by the <i>view</i> argument; default is
view 0. The default behavior is to display the smallest interval that
contains all counts; you can change this with either the <i>start</i>
and <i>stop</i> or the <i>address</i> and <i>cell-bits</i>,
<i>row-bits</i> or <i>table-bits</i> arguments.

Cells that have zero counts are marked with ".". Cells that have a
non-zero count, but were rounded to zero, are marked with "o".

If one of <i>cell-bits</i>, <i>row-bits</i> or <i>table-bits</i> is
specified, then each cell, or each table row, or the entire table is
limited to that many bits of address space. By default the display
starts at address 0, but if an address is specified with the
<i>address</i> argument, the displayed interval is shifted to make
that address is visible.

If <i>start</i> and <i>stop</i> are specified, the display is limited
to the smallest interval containing both addresses.

The maximum number of lines in the table is limited by the
<i>lines</i> argument (the default is 20 lines). The scale of the map
is adjusted to fit this limit.

Normally, the display chooses an appropriate prefix for the count of
each cell; with the <tt>-same-prefix</tt> flag, all counts will be
forced to have the same prefix. This is useful if a lot of small but
non-zero values makes it hard to spot the really big values.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4663")

def address_profile_summary_cmd(ap, view, lines):

    try:
        SIM_get_interface(ap, "address-profiler")
        api = ap.iface.address_profiler
    except:
        pr("%s is not an address profiler!\n" % ap)
        return

    if api.num_views(ap) == 0:
        pr("%s has no views defined!\n" % ap)
        return

    addr_bits = api.address_bits(ap, view)
    addr_size = rshift_round_up(addr_bits, 2) # address size in hex digits
    minlength = api.granularity_log2(ap, view)
    num_width = 6
    maxlines = lines

    lcount = 0
    hcount = 1
    start  = 2
    length = 3

    def init_lines():
        lc = api.sum(ap, view, 0, (1 << (addr_bits - 1)) - 1)
        hc = api.sum(ap, view, (1 << (addr_bits - 1)), (1 << addr_bits) - 1)
        if hc + lc == 0:
            return None
        line = {lcount: lc, hcount: hc, start: 0, length: addr_bits}
        trim_empty_halves(line)
        return [line]

    def trim_empty_halves(line):
        if line[length] == minlength:
            return
        if line[lcount] == 0:
            line[length] -= 1
            line[start] += (1 << line[length])
            line[lcount] = api.sum(
                ap, view, line[start],
                line[start] + (1 << (line[length] - 1)) - 1)
            line[hcount] -= line[lcount]
            trim_empty_halves(line)
            return
        if line[hcount] == 0:
            line[length] -= 1
            line[hcount] = api.sum(ap, view,
                                   line[start] + (1 << (line[length] - 1)),
                                   line[start] + (1 << line[length]) - 1)
            line[lcount] -= line[hcount]
            trim_empty_halves(line)
            return

    def density(line):
        return float(line[lcount] + line[hcount])/(1 << line[length])

    def add_line(lines, line):
        trim_empty_halves(line)
        d = density(line)
        i = len(lines)
        lines.append(line)
        while i > 0 and d > density(lines[i - 1]):
            lines[i], lines[i - 1] = lines[i - 1], lines[i]
            i -= 1

    def split_last(lines):
        i = len(lines) - 1
        while lines[i][length] == minlength:
            i -= 1
            if i < 0:
                return 0 # no more lines to split
        line = lines.pop(i)
        ilen = 1 << (line[length] - 2)
        c1 = api.sum(ap, view, line[start], line[start] + ilen - 1)
        c2 = line[lcount] - c1
        c3 = api.sum(ap, view, line[start] + 2*ilen, line[start] + 3*ilen - 1)
        c4 = line[hcount] - c3
        line1 = {lcount: c1, hcount: c2, start: line[start],
                 length: (line[length] - 1)}
        add_line(lines, line1)
        line2 = {lcount: c3, hcount: c4, start: line[start] + 2*ilen,
                 length: (line[length] - 1)}
        add_line(lines, line2)
        return 1 # success

    # Find interesting intervals.
    lines = init_lines()
    if lines == None:
        pr("Profiler is empty.\n")
        return
    while len(lines) < maxlines and split_last(lines):
        pass

    # Sort intervals by start address.
    tmplist = [(line[start], line) for line in lines]
    tmplist.sort()
    lines = [line for (key, line) in tmplist]

    # Print intervals.
    pr("  %*s  %*s  %*s  %*s  %s\n"
       % (int(addr_size) + 2, "start",
          int(addr_size) + 2, "end",
          int(num_width), "count",
          int(num_width), "length",
          "counts/byte"))
    sum = 0
    for line in lines:
        count = line[lcount] + line[hcount]
        sum += count
        stop = line[start] + (1 << line[length]) - 1
        pr("  0x%0*x  0x%0*x  %*s  %*s  %f\n"
           % (int(addr_size), line[start],
              int(addr_size), stop,
              int(num_width), num_to_str(count, num_width),
              int(num_width), num_to_str(1 << line[length], num_width),
              density(line)))
    pr("Total sum is %s.\n" % long_and_short_num(sum))

new_command("address-profile-summary", address_profile_summary_cmd,
            args = [arg(int_t, "view", spec = "?", default = 0),
                    arg(int_t, "lines", spec = "?", default = 10)],
            namespace = "address_profiler",
            type = "internal commands",
            short = "short summary of the contents of the address profiler",
            doc = """
Print a short summary of the address intervals that have a nonzero
count.

The view of the address profiler is selected with the <i>view</i>
parameter (default is view 0). <i>lines</i> determines the length of
the summary (the amount of information presented is increased until it
fills the specified number of lines).""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4826")

#
# ----------------- current-processor ----------------
#

def cur_proc_cmd():
    try:
        return SIM_current_processor().name
    except SimExc_Lookup, msg:
        print msg
        SIM_command_has_problem()

new_command("current-processor", cur_proc_cmd,
            type = ["Command-Line Interface"],
            short = "return current processor",
            doc = """
Returns the name of the currently executing processor.
""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4852")

def cli_history_cmd(maxlines):
    hist = conf.sim.cmd_history
    if maxlines != -1:
        hist = hist[max(len(hist) - maxlines, 0):]
    pr("".join("    " + line + "\n" for line in hist))

if sys.platform == "win32":
    new_command("cli-history", cli_history_cmd,
                [arg(integer_t, "maxlines", "?", -1)],
                type = ["Command-Line Interface"],
                short = "display command-line history",
                doc = """
List the most recently typed command lines. If specified, at most
<var>maxlines</var> lines are displayed.""", filename="/mp/simics-3.0/src/core/common/commands.py", linenumber="4866")
# This file should only contain internal commands which should not be
# seen by the end-user.    

from cli import *

#
# VTmem debug commands
#

def mm_list_types_cmd(max):
    DBG_mm_list_types(max)

new_command("mm-list-types", mm_list_types_cmd, [arg(int_t, "max", "?", 0)], type="internal commands", 
            short = "list all object types currently active", doc = """
            Each object created has a type associated to it. This command goes through all active
            objects and creates a list sorted by type and memory footprint.
            """, filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="13")

def mm_list_sites_cmd(file, maxsites):
    DBG_mm_list_sites(file, maxsites, 0)

new_command("mm-list-sites", mm_list_sites_cmd,
            [arg(str_t, "file", "?", '*'),
             arg(int_t, "maxsites", "?", 32)],
            type = "internal commands",
            short = "list busiest allocation sites",
            doc = """
List the <i>maxsites</i> allocation sites that have the most memory allocated.
If <i>file</i> is specified, constrain the list to allocation sites in source
files matching that string (* matches any sequence of characters).""", filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="22")

def mm_snoop_type_cmd(flag, type):
    if flag:
        enable = 0
    else:
        enable = 1
    DBG_mm_snoop_type(type, enable)

new_command("mm-snoop-type", mm_snoop_type_cmd,
            [arg(flag_t, "-d"), arg(str_t, "type")],
            type = "internal commands",
            short = "turn on/off type snooping",
            doc = """
Turn on (or, with <tt>-d</tt>, off) snooping of all allocations/deallocations
of the type <i>type</i>. A <i>type</i> of <tt>*</tt> means that all types
are to be snooped.""", filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="39")

def mm_hash_stat_cmd():
    DBG_mm_hash_stat()

new_command("mm-hash-stat", mm_hash_stat_cmd, [], type = "internal commands",
            short = "show some internal memory statistics",
            doc = """
Shows some esoteric internal memory management hash table statistics only of
interest to the VTmem maintainer.""", filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="51")

#
# ------------------- no-problem -------------------
#
def no_problem_cmd():
    SIM_set_attribute(SIM_get_object("sim"), "no-problem", 1)
    
new_command("no-problem", no_problem_cmd,  [], type="internal commands", 
            short = "disable back to front on problems", doc = """
            Disable back to front on problems.
            """, filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="63")


#
# ------------------- uncatch-signal -------------------
#
def uncatch_signal_cmd(signo):
    if (DBG_uncatch_signal(signo) == -1):
        print "Failed to remove signal handler for %d" % signo
        SIM_command_has_problem()        
    else:
        print "Signal %d not caught by Simics anymore" % signo

    
new_command("uncatch-signal", uncatch_signal_cmd,
            args = [arg(int_t, "signo")],
            type="internal commands", 
            short = "remove signal handler for specified signal number", doc = """
            Disable a Simics installed signal handler, the default behavior will be used instead.
            This can be useful if you have an error which only happens when occasionally and
            you want to generate a core file to analyze the problem when it has happened.
            """, filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="80")



#
# ------------------- dump-sr-stat -------------------
#
def dump_sr_stat_cmd(filename):
    cpu = current_processor()
    try:
        if not cpu.iface.processor.dump_sr_stat(filename):
            print "Failed to dump statistics"
    except:
        print "Simics does not have SR statistics."
        
new_command("dump-sr-stat", dump_sr_stat_cmd,
            [ arg(filename_t(),"file_name") ],
            type = "internal commands", 
            short = "print service routine statistics",
            doc = """
On a Simics compiled with the <b>-gs</b> Simgen flag, this command generates a
file with statistics on which service routines and parameter combinations that
has been executed during this session. This file can be used as an input file
to Simgen (<b>-as</b> and <b>-s</b> flags) to sort and specialize service
routines, making a faster sim.
""", filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="102")

#
# -------------------- dump-dstc --------------------
#

def dump_dstc():
    DBG_dump_dstc(current_processor())

new_command("dstc-dump", dump_dstc,
            [],
            alias = "",
            type  = "internal commands",
            short = "print contents of D-STC",
            doc = """
For debugging Simics internals: lists contents of data STCs. The STC tables
are used to speed up memory access operations, and cache translations
between virtual, physical, and real addresses.Note: this command
will only dump the currently active STC set, if there are multiple.
""", filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="121")

#
# -------------------- infinite-loop --------------------
#

def infinite_loop_cmd():
    DBG_infinite_loop()

new_command("infinite-loop", infinite_loop_cmd,
            [],
            type  = "internal commands",
            short = "enter infinite loop",
            doc = """
For debugging Simics internals: Place Simics in an infinite loop
until an attached debugger clears a flag.""", filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="140")

#
# -------------------- print-last-exceptions -------------
#

def print_last_exceptions_cmd():
    DBG_print_exception_list()

new_command("print-last-exceptions", print_last_exceptions_cmd,
            [],
            type  = "internal commands",
            short = "print the 16 last exceptions",
            doc = """
            Print out the 16 last exceptions, if they were cleared properly and which code line generated them.
            """, filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="155")

#
# -------------------- turbo-debug --------------------
#

def turbo_debug():
    conf.cpu0.rax = 0x0000000000000000L
    conf.cpu0.rbx = 0x0123456789abcdefL
    conf.cpu0.rcx = 0xf0f0f0f0f0f0f0f0L
    conf.cpu0.rdx = 0x0000000012345678L
    conf.cpu0.rsi = 0x0000000000000009L
    DBG_turbo_debug()

new_command("turbo-debug", turbo_debug,
            [],
            alias = "",
            type = "internal commands",
            short = "run some turbo tests",
            doc = "Runs a number of tests of the turbo code generation.", filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="175")

def print_internal_counters(long_descriptions):
    try:
        counters = conf.sim.internal_counters
        desc = conf.sim.internal_counters_desc
    except:
        print "Internal profiling is not available"
        return
    print
    for group, list in desc:
        print "%s" % group
        for name, short_desc, long_desc in list:
            count = str(counters[name])
            pad = "."*(65 - len(count) - len(short_desc))
            print "   %s%s%s" % (short_desc, pad, count)
            if long_descriptions:
                print "      (%s) %s" % (name, long_desc)
                print
        print

new_command("print-internal-counters", print_internal_counters,
            args = [arg(flag_t, "-long-descriptions")],
            type="internal commands",
            short = "print values of internal counters",
            doc = """
Print values of internal debugging counters.""", filename="/mp/simics-3.0/src/core/common/debug_commands.py", linenumber="201")
