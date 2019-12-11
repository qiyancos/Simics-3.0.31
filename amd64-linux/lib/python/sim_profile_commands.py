from cli import *
import sim_commands

#
# -------------------- branch recorder commands --------------------
#

def supports_branch_profiling(cpu):
    if cpu.branch_prof_support:
        try:
            cpu.branch_recorders
            return 1
        except:
            print ("%s processors only support branch profiling in"
                   + " -stall mode.") % cpu.classname
            return 0
    else:
        print "%s processors do not support branch profiling." % cpu.classname
        return 0

address_types = ["physical", "virtual"]
def branch_recorder_address_type_expander(string):
    return get_completions(string, address_types)

def new_branch_recorder_cmd(name, address_type, cpu_type):
    if not supports_branch_profiling(cpu_type):
        return

def new_branch_recorder_cmd(name, address_type):
    try:
        SIM_get_object(name)
        pr("An object called '%s' already exists.\n" % name)
        return
    except:
        at = VT_addr_type_from_str(address_type)
        if at == Addr_Type_Invalid:
            print ("'%s': Illegal address type! Valid types are: %s."
                   % (address_type, ", ".join(address_types)))
            return
        try:
            brec = SIM_create_object("branch_recorder", name,
                                     [["address_type", at]])
        except:
            pr("Error creating branch recorder '%s'\n" % name)

new_command("new-branch-recorder", new_branch_recorder_cmd,
            args = [arg(str_t, "name"),
                    arg(str_t, "address_type",
                        expander = branch_recorder_address_type_expander)],
            type  = ["Profiling"],
            short = "create a new branch recorder",
            doc = """
Create a new branch recorder object called <i>name</i>, to record
branches using addresses of type <i>address_type</i> (either
<tt>physical</tt> or <tt>virtual</tt>). The branch recorder is
initially not bound to any processor.""", filename="/mp/simics-3.0/src/core/common/profile_commands.py", linenumber="46")

def clean_branch_recorder_cmd(brec):
    brec.clean = None

new_command("clean", clean_branch_recorder_cmd,
            args = [],
            namespace = "branch_recorder",
            type  = ["Profiling"],
            short = "delete all branch arcs in the branch recorder",
            doc = """
Delete all branch arcs stored in the branch recorder.""", filename="/mp/simics-3.0/src/core/common/profile_commands.py", linenumber="61")

def attach_branch_recorder_to_processor_cmd(cpu, brec):
    if supports_branch_profiling(cpu):
        VT_attach_branch_recorder_to_processor(cpu, brec)

def detach_branch_recorder_from_processor_cmd(cpu, brec):
    if supports_branch_profiling(cpu):
        VT_detach_branch_recorder_from_processor(cpu, brec)

new_command("attach-branch-recorder", attach_branch_recorder_to_processor_cmd,
            [arg(obj_t("branch_recorder", "branch_recorder"), "branch_recorder")],
            namespace = "processor",
            type  = ["Profiling"],
            short = "attach a branch recorder to a processor",
            see_also = ['<processor>.detach-branch-recorder'],
            doc = """
Attach the branch recorder <i>branch_recorder</i> to the processor, so
that it will record its branches. Note that once you have attached a
branch recorder to a processor, it adapts to that processor type and
you cannot attach it to other processors of different types.""", filename="/mp/simics-3.0/src/core/common/profile_commands.py", linenumber="77")

new_command("detach-branch-recorder", detach_branch_recorder_from_processor_cmd,
            [arg(obj_t("branch_recorder", "branch_recorder"), "branch_recorder")],
            namespace = "processor",
            type  = ["Profiling"],
            short = "detach a branch recorder from a processor",
            see_also = ['<processor>.attach-branch-recorder'],
            doc = """
Detach the branch recorder <i>branch_recorder</i> from the processor.
""", filename="/mp/simics-3.0/src/core/common/profile_commands.py", linenumber="89")

def brec_get_info(obj):
    return [(None,
             [("Address type", VT_addr_type_to_str(obj.address_type)),
              ("CPU type", obj.cpu_type)])]

def brec_get_status(obj):
    plist = []
    for cpu in obj.processors:
        plist.append(cpu.name)
    return [(None,
             [("Number of arcs", obj.num_arcs),
              ("Attached processors", ", ".join(plist))])]

sim_commands.new_info_command("branch_recorder", brec_get_info,
                              "profiling commands")
sim_commands.new_status_command("branch_recorder", brec_get_status,
                                "profiling commands")

def start_instruction_profiling_cmd(cpu):
    if not supports_branch_profiling(cpu):
        return

    bname = "%s_branch_recorder" % cpu.name
    try:
        SIM_get_object(bname)
        print "Error! An object called %s already exists." % bname
        return
    except:
        pass
    try:
        brec = SIM_new_object("branch_recorder", bname)
        SIM_set_attribute(brec, "address_type", Addr_Type_Physical)
        VT_attach_branch_recorder_to_processor(cpu, brec)
    except:
        print "Error! Could not create a branch recorder for %s." % cpu.name
        return
    print """
Created a branch recorder called %(bname)s and attached it to
the %(cputype)s %(cpu)s. Type

   help %(cpu)s.start-instruction-profiling

for tips on what to do with it.
""" % { "bname": bname, "cpu": cpu.name, "cputype": cpu.classname }

new_command("start-instruction-profiling", start_instruction_profiling_cmd,
            args = [],
            namespace = "processor",
            type  = ["Profiling"],
            short = "get started with instruction profiling",
            see_also = ['new-branch-recorder',
                        '<processor>.attach-branch-recorder',
                        '<address_profiler>.address-profile-data'],
            doc = """
This command gets you started with instruction profiling quickly by
creating a branch recorder for you and attaching it to the processor.
If you want more control, use other profiling commands instead.

It creates a branch recorder and attaches it to the processor, just as
if you had typed

<tt>new-branch-recorder</tt> <i>branch_recorder</i> <tt>physical</tt>

<i>cpu</i><tt>.attach-branch-recorder</tt> <i>branch_recorder</i>

The branch recorder will (as the name implies) record branches taken
by the processor (by physical addresses); various useful numbers can
be computed from them. You can for example display execution count
statistics by typing

<i>branch_recorder</i><tt>.address-profile-data</tt>

(but you will not see anything interesting until you have let the
processor run a few instructions).
""", filename="/mp/simics-3.0/src/core/common/profile_commands.py", linenumber="144")

#
# -------------------- debugging --------------------
#

def dbg_print_branch_arcs(addr_bits, arcs):
    def fix_sign(num):
        if num > (1L<<63):
            return num - (1L<<64)
        else:
            return num
    cnt_width = 12
    addr_width = addr_bits/4
    print_header = "%*s  %*s  %*s"
    print_list   = "%*s  %*s  %*d  %s"
    fnl_list     = "%*s  %*s  %*s  %s:%d"
    print print_header % (addr_width, "from", addr_width,
                          "to", cnt_width, "count")
    for arc in arcs:
        if len(arc) == 6:
            fa, ta, cnt, type, file, line = arc
            file = file.split("/")[-1]
        else:
            fa, ta, cnt, type = arc
            file = line = None
        if fa == None:
            fa = ""
        else:
            fa = "%0*x" % (addr_width, fa)
        if ta == None:
            ta = ""
        else:
            ta = "%0*x" % (addr_width, ta)
        print print_list % (addr_width, fa, addr_width,
                            ta, cnt_width, fix_sign(cnt), type)
        if (file and line):
            print fnl_list % (addr_width, "", addr_width, "", cnt_width, "",
                              file, line)

def dbg_print_branch_arcs_cmd(brec, start, stop, from_addr, to_addr):
    addr_bits = brec.iface.address_profiler.address_bits(brec, 0)
    if stop == start == None:
        stop = 0
        start = 1
    elif stop == None or start == None:
        print "Must specify both start and stop addresses, or none of them."
        return
    else:
        stop = stop[1]
        start = start[1]
        if stop < start:
            print "Start address must not be greater than stop address."
            return
    if not from_addr and not to_addr:
        # If neither is specified, print arcs sorted by both from and
        # to.
        from_addr = to_addr = 1
    f, t = DBG_get_branch_arcs(brec, start, stop)
    if from_addr and len(f) > 0:
        print ""
        print "Arcs with matching 'from' address, sorted by 'from' address"
        print ""
        dbg_print_branch_arcs(addr_bits, f)
    if to_addr and len(t) > 0:
        print ""
        print "Arcs with matching 'to' address, sorted by 'to' address"
        print ""
        dbg_print_branch_arcs(addr_bits, t)

new_command("dbg-print-branch-arcs", dbg_print_branch_arcs_cmd,
            args = [arg(addr_t, "start", spec = "?", default = None),
                    arg(addr_t, "stop", spec = "?", default = None),
                    arg(flag_t, "-from"),
                    arg(flag_t, "-to")],
            namespace = "branch_recorder",
            type  = "internal commands",
            short = "print branch arcs with debugging info",
            doc = """
Print a subset of the branch arcs in a branch recorder. With no
arguments, print all arcs. Given <i>start</i> and <i>stop</i>
addresses, print only arcs with 'to' or 'from' address in that
interval, depending on whether the <tt>-from</tt> or <tt>-to</tt> flag
was specified (if neither flag was specified, print both sets of
arcs). The list of branch arcs will include arcs that do not
correspond to real branches but were added to compensate for
exceptional circumstances such as the starting or stopping of the
branch recorder, and the type of each arc.""", filename="/mp/simics-3.0/src/core/common/profile_commands.py", linenumber="243")


pbad_directions = {"to": BR_Direction_To, "from": BR_Direction_From}
def print_branch_arcs_direction_expander(string):
    return get_completions(string, pbad_directions.keys())

def print_branch_arcs_cmd(brec, dir, start, stop):
    if stop < start:
        print "Start address must not be greater than stop address."
        return
    try:
        dir = pbad_directions[dir]
    except KeyError:
        print "Direction must be either 'from' or 'to'."
        return
    ifc = brec.iface.branch_arc
    addr_width = int((brec.iface.address_profiler.address_bits(brec, 0) + 3)/4)
    for (from_a, to_a, count, type) in ifc.iter(brec, start, stop, dir):
        if type == Branch_Arc_Exception:
            ptype = "exception"
        elif type == Branch_Arc_Exception_Return:
            ptype = "exception_return"
        else:
            ptype = ""
        print "0x%0*x -> 0x%0*x %12i %s" % (addr_width, from_a,
                                            addr_width, to_a,
                                            count, ptype)

new_command("print-branch-arcs", print_branch_arcs_cmd,
            args = [arg(str_t, "direction", spec = "?", default = "from",
                        expander = print_branch_arcs_direction_expander),
                    arg(int_t, "start", spec = "?", default = 0),
                    arg(int_t, "stop", spec = "?", default = (1L << 64) - 1)],
            namespace = "branch_recorder",
            type  = ["Profiling"],
            short = "print branch arcs",
            doc = """
Print a subset of the branch arcs in a branch recorder. With no
arguments, print all arcs. Given <i>start</i> and <i>stop</i>
addresses, print only arcs with 'to' or 'from' address in that
interval, depending on whether <i>direction</i> is 'to' or 'from' (its
default value is 'from'). The printed arcs are sorted by their 'to' or
'from' address, as specified by <i>direction</i>.""", filename="/mp/simics-3.0/src/core/common/profile_commands.py", linenumber="289")
