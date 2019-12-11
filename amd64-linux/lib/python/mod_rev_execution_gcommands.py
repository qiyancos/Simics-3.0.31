from cli import *

import os, sys
from rev_exec import re, backer, output
from rev_limit import restore_state_with_id, delete_state, stop_rexec

#######################################################################
# bookmark commands
#######################################################################

def bookmark_expander(comp):
    s = [x[0] for x in re.obj.bookmarks]
    return get_completions(comp, s)

def cmd_set_bookmark(name):
    def get_bookmark_names():
        return [x[0] for x in re.obj.bookmarks]

    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return

    # throw an exception if no processors are present
    current_processor()

    if name is not None:
        if name in get_bookmark_names():
            re.obj.delete_bookmark = name
            print "bookmark %s moved to current time" % name
    else:
        bookmark_num = len(get_bookmark_names())
        while ("bookmark%d" % bookmark_num) in get_bookmark_names():
            bookmark_num += 1
        name = "bookmark%d" % bookmark_num
        print "bookmark %s set current time" % name

    output.divert(re.obj.state_level)
    re.obj.add_bookmark = name
    output.undivert()

    # checkpoint engine is started from the Core_Rexec_Activated hap

def cmd_delete_bookmark(name):
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return

    if name[0] == str_t:
        re.obj.delete_bookmark = name[1]
    else:
        cpy = re.obj.bookmarks[:]
        for x in cpy:
            re.obj.delete_bookmark = x[0]

    if not len(re.obj.states[:]):
        stop_rexec()


def make_now_bookmark():
    cpu = SIM_current_processor()
    ret = ["<current execution point>", cpu.processor_number, []]
    for i in range(0, SIM_number_processors()):
        cpu = SIM_proc_no_2_ptr(i)
        ret[2] += [[SIM_step_count(cpu), SIM_cycle_count(cpu)]]
    return ret

def cmd_list_bookmarks():
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return

    bookmarks = re.obj.bookmarks
    bookmarks += [make_now_bookmark()]
    print " name                                      steps"
    print "-------------------------------------------------"
    def time_comp(x1, x2):
        _,_,cnts1 = x1
        _,_,cnts2 = x2
        return [0, -1, 1][(cnts1 < cnts2) - (cnts1 > cnts2)]

    sorted = bookmarks
    sorted.sort(time_comp)
    cpu = current_processor()
    for x in sorted:
        name, _, cnts = x
        (steps, cycles) = cnts[cpu.processor_number]
        print " %-28s" % name,
        print "%18s" % number_str(steps, 10)
    print "-------------------------------------------------"


##########################################################################

def label_expander(comp):
    s = []
    for x in re.obj.labels:
        if x != None and x[0] != '<':
            s.append(x)
    return get_completions(comp, s)

def poly_to_index(poly):
    if poly[0] == str_t:
        if poly[1][0] == 'i':
            try:
                return int(poly[1][1:])
            except:
                pass

        index = re.iface.get_idx(poly[1])
        if index < 0:
            raise SimExc_General, "State '%s' not found" % poly[1]
        return index

    elif poly[0] == sint32_t:
        return poly[1]
    raise SimExc_General, "Unexpected argument"

def cmd_save_state(name):
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return
    VT_save_micro_checkpoint(name, Sim_MC_ID_User | Sim_MC_Persistent)

def cmd_restore_state(poly):
    if SIM_simics_is_running():
        raise CliError, "Can't restore state while Simics is running"
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return
    index = poly_to_index(poly)
    re.iface.restore(index)

def cmd_delete_state(poly):
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return
    index = poly_to_index(poly)
    re.iface.remove(index)

def cmd_list_states():
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return

    s1 = " name                          steps    "
    s2 = "-----------------------------------------------------------------------"
    s1 = " index   " + s1 + "spages   zero-pages"
    print s1
    print s2
    pnum = current_processor().processor_number
    sinfo = re.obj.state_info[:]
    st = re.obj.states[:]
    spages_tot, zpages_tot = 0, 0
    for ind in range(len(st) - 1, -1, -1):
        flags, curcpu, ptimes = st[ind]
        name, spages, zpages = sinfo[ind]
        print "  %4d  " % ind,
        print " %-18s" % name,
        print "%16s " % number_str(ptimes[pnum], 10),
        print "%8s %12s" % (number_str(spages, 10), number_str(zpages, 10)),
        print
        spages_tot += spages
        zpages_tot += zpages
    print s2
    if not spages_tot:
        return
    spages_mem = spages_tot * (1 << VT_get_storage_page_size())
    print " %.1f MB used" % (re.obj.mem_usage / 1024.0 / 1024.0),
    print "(%.1f MB spages, %.1f%% zero pages)" % (spages_mem / 1024.0 / 1024.0,
                                                   100.0 * zpages_tot / (zpages_tot + spages_tot))

new_command("save-snapshot", cmd_save_state,
            [arg(str_t, "name", "?", "userstate")],
            alias = ["ss"],
            type = "internal commands",
            short = "save a snapshot of the current simulation state",
            doc = """
Saves an in-memory snapshot of the current simulation state.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="179")

new_command("restore-snapshot", cmd_restore_state,
            args = [arg((str_t, sint32_t), ("name", "index"), "?", (sint32_t, 0),
                        expander = (label_expander, 0))],
            type = "internal commands",
            short = "restore the simulation state from an in-memory snapshot",
            doc = """
Restores the state of the simulation from an in-memory snapshot.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="188")

new_command("delete-snapshot", cmd_delete_state,
            args = [arg((str_t, sint32_t), ("name", "index"), "?", (sint32_t, 0),
                        expander = (label_expander, 0))],
            alias = ["ds"],
            type = "internal commands",
            short = "delete an in-memory snapshot of the simulation",
            doc = """
Deletes the specified in-memory snapshot.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="197")

new_command("list-snapshots", cmd_list_states,
            args = [],
            alias = ["rls"],
            type = "internal commands",
            short = "list in-memory snapshots of the simulation state",
            doc = """
Lists in-memory snapshots of the simulation state.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="207")


##########################################################################

new_command("set-bookmark", cmd_set_bookmark,
            [arg(str_t, "bookmark", "?", None)],
            alias = ["bookmark", "bo"],
            type = ["Reverse Execution"],
            see_also = ["delete-bookmark", "reverse", "skip-to"],
            short = "set a bookmark at the current point in time",
            doc = """
Associates a time bookmark with the current point in the simulation.
The bookmark can be used as a target to the <b>skip-to</b> command.

Reverse operations are possible in the region following the first
(i.e. oldest) time bookmark.

Setting a time bookmark can cause a certain reduction in forward
simulation performance (deleting all bookmarks will restore
the original performance).
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="219")

new_command("delete-bookmark", cmd_delete_bookmark,
            [arg((str_t, flag_t), ("bookmark", "-all"), expander = (bookmark_expander, 0))],
            alias = ["db"],
            type = ["Reverse Execution"],
            see_also = ["set-bookmark", "list-bookmarks", "reverse"],
            short = "delete a time bookmark",
            doc = """
Deletes a time bookmark. Deleting all time bookmarks can
improve forward simulation performance.

Reverse operations are possible in the region following the
first (i.e. oldest) time bookmark.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="237")

new_command("list-bookmarks", cmd_list_bookmarks,
            [],
            alias = ["lb"],
            type = ["Reverse Execution"],
            see_also = ["set-bookmark", "delete-bookmark"],
            short = "list time bookmarks",
            doc = """
Lists time bookmarks.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="251")


#######################################################################
# CLI commands
#######################################################################

# poly -> (cpu, stepcount)
def poly_to_pair(poly):
    try: poly = (uint64_t, long(poly[1]))
    except: pass

    if poly[0] == str_t:
        for x in re.obj.bookmarks:
            name, cpu_nu, cnts = x
            if name != poly[1]:
                continue
            cur_proc_no = current_processor().processor_number
            return (SIM_proc_no_2_ptr(cpu_nu), cnts[cpu_nu][0])
        raise CliError, "Time label %s not found" % poly[1]

    if poly[0] == uint64_t:
        return (current_processor(), poly[1])
    raise CliError, "Target time not specified"

def blurb():
    print "[%s] " % current_processor().name,
    eval_cli_line("da")

def ptime():
    return SIM_step_count(current_processor())

def cmd_reverse(count = -1):
    if SIM_simics_is_running():
        raise CliError, "Simics is already running"
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return
    backer.reverse(count, current_processor())
    blurb()

new_command("reverse", cmd_reverse,
            [arg(uint64_t, "count", "?", -1)],
            alias = ["rev"],
            type = ["Reverse Execution"],
            short = "run simulation backwards",
            repeat = cmd_reverse,
            see_also = ["set-bookmark", "skip-to"],
            doc = """
Runs the simulation in reverse. The simulation will stop at any breakpoints
or after at most <arg>count</arg> instructions (if specified).

Before the machine can be reversed, at least one time bookmark has
to be set. Reverse operations are possible in the region following
the first (oldest) time bookmark.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="301")

revto_mark = []

def cmd_revto(poly):
    global revto_mark
    if SIM_simics_is_running():
        raise CliError, "Simics is already running"
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return

    cpu, steps = poly_to_pair(poly)
    cnt = SIM_step_count(cpu) - steps

    revto_mark = (cpu, steps)
    if cnt > 0:
        backer.reverse(cnt, cpu)
        blurb()

def cmd_revto_rep(dummy_poly):
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return
    (cpu, abscount) = revto_mark
    cnt = SIM_step_count(cpu) - abscount
    if cnt > 0:
        backer.reverse(cnt, cpu)
        blurb()

new_command("reverse-to", cmd_revto,
            args = [arg((str_t, uint64_t), ("bookmark", "instructions"),
                        expander = (bookmark_expander, 0))],
            alias = ["revto"],
            type = ["Reverse Execution"],
            short = "set a temporary time breakpoint and run backwards",
            repeat = cmd_revto_rep,
            see_also = ["set-bookmark"],
            doc = """
Runs the simulation in reverse. The simulation will stop at any breakpoints
or at the specified (absolute) point in time if no breakpoints occurred.

At least one time bookmark has to be set before any reverse operations
are possible.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="347")

def cmd_skip_to(poly):
    if SIM_simics_is_running():
        raise CliError, "Simics is already running"
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return
    cpu, steps = poly_to_pair(poly)
    backer.rewind(steps, cpu)
    blurb()

def cmd_unstep(count):
    if SIM_simics_is_running():
        raise CliError, "Simics is already running"
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return

    pt = ptime()
    backer.rewind(pt - count, current_processor())
    output.divert(re.obj.state_level)
    VT_save_micro_checkpoint("<unstep-mark>", Sim_MC_ID_Tmp | Sim_MC_Persistent)
    output.undivert()

    output.separator()
    count = pt - ptime()
    if count > 0:
        eval_cli_line("si %d" % count)
    output.undivert()

    output.divert(re.obj.state_level)
    restore_state_with_id(Sim_MC_ID_Tmp)
    delete_state(0)
    output.undivert()

new_command("skip-to", cmd_skip_to,
            args = [arg((str_t, uint64_t), ("bookmark", "instructions"),
                        expander = (bookmark_expander, 0))],
            alias = ["st"],
            type = ["Reverse Execution"],
            short = "skip to the specified point in the simulation",
            doc = """
Skips to the specified point in time. The target position can either
be a <arg>label</arg> previously defined by <arg>set-bookmark</arg> or an absolute
instruction count.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="399")

new_command("reverse-step-instruction", cmd_unstep,
            [arg(uint64_t, "count", "?", 1)],
            alias = ["ui", "unstep-instruction", "rstepi", "rsi"],
            type = ["Reverse Execution"],
            short = "reverse step one or more instruction",
            repeat = cmd_unstep,
            see_also = ["reverse-next-instruction", "reverse-next-line", "uncall-function",
                        "reverse-step-line"],
            doc = """
Executes <arg>count</arg> instructions in reverse, printing each instruction
at each step. <arg>count</arg> defaults to one.

The <cmd>reverse-next-instruction</cmd> command is similar except
that it does not reverse into called functions.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="411")


def cmd_clear_recorder():
    if not VT_hindsight_license_check():
        print "Command requires hindsight license."
        SIM_command_has_problem()
        return
    VT_discard_future()

    curr_cnts = []
    for i in range(0, SIM_number_processors()):
        cpu = SIM_proc_no_2_ptr(i)
        curr_cnts += [[SIM_step_count(cpu), SIM_cycle_count(cpu)]]

    for x in re.obj.bookmarks:
        name, _, cnts = x
        for curr, book in zip(curr_cnts, cnts):
            if curr[0] < book[0]:
                re.obj.delete_bookmark = name
                print "discarding future bookmark '%s'." % name

new_command("clear-recorder", cmd_clear_recorder,
            args = [],
            alias = [],
            type = ["Reverse Execution"],
            short = "clear recorded events",
            doc = """
Discard recorded input events (e.g. human console input). This command
allows an alternate future to take place.
""", filename="/mp/simics-3.0/src/extensions/rev-execution/gcommands.py", linenumber="447")
