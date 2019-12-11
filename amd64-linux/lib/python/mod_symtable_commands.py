# Python commands for symtable

# TODO:
# - add a way to specify format for "psym" (how? /x?)
# - maybe add a command to print a symbol value directly
#   (no mem access, can be done directly on a symtable)
# - add options to stack-trace to print more or less details (sp, fp etc)
# - add source file functions (print selected source lines etc)
# - add commands to step source lines (into and over functions)
#   (set a virtual breakpoints in that context)

from cli import *
import re, os.path
from sim_commands import local_print_disassemble_line

selfprof_enabled = True

stif = SIM_get_class_interface('symtable', 'symtable')

# print one stack frame. If frame_no >= 0, print frame number
def print_frame(cpu, symtable, frame_no, frame):
    global filecache
    w = 0                               # current line width
    pc = frame[0]
    spath = get_source_path(symtable)
    if frame_no >= 0:
        pre = "#%d 0x%x in " % (frame_no, pc)
        pr(pre)
        w = len(pre)
    if symtable:
        # 'pc' in the current frame (#0) points to the next instruction.
        # 'pc' in other frames means the return address, and needs to be
        # adjusted to point inside the call instruction.
        # Same logic is used in gdb (frame_unwind_address_in_block)
        if frame_no > 0:
            src = symtable.source_at[pc - 1]
        else:
            src = symtable.source_at[pc]
        if src:
            args = stif.fun_args(cpu, frame)
            pr("%s (" % src[2])
            if args:
                w += len(src[2]) + 2
                nargs = len(args)
                for i in range(nargs):
                    astr = "%s=%s" % (args[i][0], args[i][1])
                    if i < nargs - 1:
                        astr += ","
                    alen = len(astr)
                    if i == 0:
                        # first line
                        pr(astr)
                        w += alen
                    elif w + alen + 1 < terminal_width():
                        # fits on the same line
                        pr(" " + astr)
                        w += alen + 1
                    else:
                        # wrap to new line
                        pr("\n    " + astr)
                        w = 4 + alen
            pr(")")
            tail = "\n"
            if src[1] == 0:
                if src[0]:
                    tail = " in " + src[0] + "\n"
            else:
                f = filecache.getfile(src[0], spath)
                if f:
                    file = f.host_file
                else:
                    file = src[0]
                tail = " at %s:%d\n" % (file, src[1])
            if w + len(tail) > terminal_width():
                tail = "\n   " + tail
            pr(tail)
        else:
            pr("?? ()\n")
    else:
        pr("?? ()\n")
    
def cpu_context(cpu):
    try:
        return cpu.current_context
    except AttributeError:
        return None

def cpu_symtable(cpu):
    ctx = cpu_context(cpu)
    if ctx:
        return ctx.symtable
    else:
        return None

def stack_trace_cmd(cpu, maxdepth):
    if cpu == None:
        cpu = current_processor()
    st = cpu_symtable(cpu)
    if not st:
        pr("No symbols loaded\n")
        return
    frames = stif.stack_trace(cpu, maxdepth)
    i = 0
    for fr in frames:
        print_frame(cpu, st, i, fr)
        i += 1

# If ns is true, return fun. Otherwise, return a function that, when
# called, calls fun with the same arguments except that None is added
# as the first argument.
def ns_fun(ns, fun):
    if ns:
        return fun
    else:
        def f(*args):
            return fun(None, *args)
        return f

for ns in ("", "processor"):
    new_command("stack-trace", ns_fun(ns, stack_trace_cmd),
                [arg(range_t(0, 1000, "max stack depth"),
                     "maxdepth", "?", 64)],
                namespace = ns,
                alias = ["bt", "where"],
                type = ["Symbolic Debugging"],
                see_also = ["frame"],
                short = "display stack trace",
                doc = """

Displays a stack trace in the current context of the specified
processor, or the current processor if none was specified. At most
<i>maxdepth</i> frames are shown, 64 by default.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="120")

def obj_load_symbols_cmd(st, file, start, t):
    if t:
        st.load_symbol_file = [file, start]
    else:
        st.symbol_file[file] = start
    if SIM_is_interactive():
        print_current_source_pos()

new_command("load-symbols", obj_load_symbols_cmd,
            [arg(filename_t(exist = 1, simpath = 1), "file"),
             arg(int_t, "start", "?", -1),
             arg(flag_t, "-t")],
            namespace = "symtable",
            type = ["Symbolic Debugging"],
            see_also = ['new-symtable', '<symtable>.plain-symbols'],
            short = "load symbols from file",
            doc = """
Loads symbolic debugging information from <i>file</i>. If <i>start</i> is
given, it is the (absolute) starting address of the file's code.
If <tt>-t</tt> is specified, <i>start</i> is interpreted as the address
of the .text section (similarly to GDB); otherwise <i>start</i> is taken to be
the address of the first executable segment. The Simics search path is used
to locate <i>file</i>.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="142")

def obj_plain_symbols_cmd(st, file, start):
    LOCAL  = 0x00
    GLOBAL = 0x01
    WEAK   = 0x02
    DATA   = 0x00
    CODE   = 0x10

    infos = { 't': CODE | LOCAL, 'T': CODE | GLOBAL,
              'd': DATA | LOCAL, 'D': DATA | GLOBAL,
              'b': DATA | LOCAL, 'B': DATA | GLOBAL,
              'r': DATA | LOCAL, 'R': DATA | GLOBAL,
              'W': CODE | WEAK }

    syms = []
    try:
        f = open(SIM_native_path(file))
    except:
        raise CliError, "Cannot open %s" % file
    for line in f.readlines():
        m = re.match(r'([\da-f]+) ([a-tv-z?]) (\S+)', line, re.I)
        if m:
            (value, kind, name) = m.group(1, 2, 3)
            value = long(value, 16)
            info = infos.get(kind, CODE | GLOBAL)
            size = 0                    # unknown
            syms.append([name, info, value + start, size])
            if len(syms) % 10000 == 0:
                print len(syms), "symbols read"

    program_name = "<unnamed>"
    st.symbol_list[program_name] = syms
    pr("Read %d symbol%s\n" % (len(syms), ["s", ""][len(syms) == 1]))

new_command("plain-symbols", obj_plain_symbols_cmd,
            [arg(filename_t(exist = 1), "file"),
             arg(int_t, "start", "?", 0)],
            namespace = "symtable",
            type = ["Symbolic Debugging"],
            see_also = ['new-symtable', '<symtable>.load-symbols'],
            short = "read raw symbols in nm format",
            doc = """
Reads "plain" symbols in BSD <b>nm(1)</b> output format. Each line looks like:

<i>value</i> <i>type</i> <i>symbol</i>

where <i>value</i> is the symbol value (usually the address) in hex, and
<i>type</i> is a code letter describing the type of the symbol: <b>B</b>,
<b>D</b> or <b>R</b> are treated as data symbols, and <b>T</b> as text (code)
symbols. File-local symbols have their type letters in lower case, global
symbols in upper case. If <i>start</i> is specified, it is added to the value
of each symbol.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="191")

# find set of architectures used by cpus using given context
def ctx_archs(ctx):
    return set([c.architecture
                for c in SIM_all_objects()
                if (SIM_object_is_processor(c)
                    and cpu_context(c) == ctx)])

def obj_abi_cmd(st, abi):
    if abi:
        st.abi = abi
    else:
        abi = st.abi
        if abi == '':
            print "No ABI set"
        else:
            print abi

def abi_expander(s):
    return get_completions(s, SIM_get_class_attribute('symtable', 'all_abis'))

new_command("abi", obj_abi_cmd,
            [arg(str_t, "abi", "?", "", expander = abi_expander)],
            namespace = "symtable",
            type = ["Symbolic Debugging"],
            see_also = ['<symtable>.plain-symbols'],
            short = "set ABI to use",
            doc = """
Set the ABI to <i>abi</i>, or show the current ABI. This is normally not
needed when loading debug info from a binary, but is needed when using
<cmd>plain-symbols</cmd>.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="230")

def obj_symtable_cmd(ctx, st_name):
    if not st_name:
        if ctx.symtable:
            print ctx.symtable.name
        else:
            pr("%s has no symbol table\n" % ctx.name)
        return

    try:
        st = SIM_get_object(st_name)
    except SimExc_General, msg:
        try:
            st = SIM_new_object('symtable', st_name)
        except SimExc_General, msg:
            print "Failed creating %s: %s" % (st_name, msg)
            raise CliError
    if st.classname != "symtable":
        print st.name, "is not a symtable"
        return

    # If all cpus having this context set are of the same architecture,
    # set the architecture and ABI of the new symtable to that.
    archs = ctx_archs(ctx)
    if len(archs) == 1:
        ctx_arch = list(archs)[0]
        if st.arch_compat[ctx_arch]:
            st.arch = ctx_arch
            ctx.symtable = st
        else:
            print ("Architecture of context (%s) does not match symtable (%s)"
                   % (ctx_arch, st.arch))
            print "- symtable not attached"
    elif len(archs) > 1:
        print "Context", ctx.name, "is heterogenous: symtable not attached"
    else:
        ctx.symtable = st

new_command("symtable", obj_symtable_cmd,
            [arg(str_t, "symtable", "?", "",
                 expander = object_expander("symtable"))],
            namespace = "context",
            type = ["Symbolic Debugging"],
            see_also = ['set-context', 'new-symtable'],
            short = "set the symbol table of a context",
            doc = """
Sets the symbol table of the context to <i>symtable</i>, or displays the name
of the symtable currently bound to the context. The symbol table is created
if it does not already exist.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="278")

source_paths = {}

def get_source_path(st):
    return source_paths.get(st.name, "")

def set_source_path(st, newpath):
    global filecache
    source_paths[st.name] = newpath
    filecache.flush()

def obj_source_path_cmd(st, path):
    old = get_source_path(st)
    if not path:
        print old
        return
    if path[:1] == "+":
        newpath = old + ";" + path[1:]
    elif path[-1] == "+":
        newpath = path[:-1] + ";" + old
    else:
        newpath = path
    set_source_path(st, newpath)

new_command("source-path", obj_source_path_cmd,
            [arg(str_t, "path", "?", "")],
            namespace = "symtable",
            type = ["Symbolic Debugging"],
            see_also = ['<symtable>.load-symbols', 'new-symtable'],
            short = "set source search path for debug info",
            doc = """
Sets the source search path to <i>path</i>. If no <i>path</i> is given, the
current search path will be displayed. The source search path is used when
translating file names in debug information to the appropriate place in the
host machine's file system.

Each component of the (semicolon-separated) search path is either a path name,
added to the beginning of source file names, or a string of the form
<i>a</i><tt>></tt><i>b</i>, replacing <i>a</i> with <i>b</i> at the beginning
of source file names.

Example: The source path <tt>/usr/src>/pkg/source;/usr>/misc</tt> would cause
the file name <tt>/usr/src/any.c</tt> to be translated to
<tt>/pkg/source/any.c</tt>, or, if no such file exists, to
<tt>/misc/src/any.c</tt>.

Another example: The source path <tt>/usr/src>C:\\My\\Source</tt> would
translate the file name <tt>/usr/src/any/file.c</tt> to
<tt>C:\\My\\Source\\any\\file.c</tt>. """, filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="313")

def host_source_at_cmd(obj, address):
    print SIM_get_attribute_idx(obj, "host-source-at", address)

new_command("host-source-at", host_source_at_cmd,
            [arg(int_t, "address")],
            namespace = "symtable",
            type = "symbolic debugging commands",
            short = "return the source code position for a given address",
            doc = """
Return the source code position (file, line, function) corresponding to a given address.            
""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="342")


# Debugging state: in order to keep this up-to-date, always call update()
# before accessing any of these

class Debug_state:
    def __init__(self, cpu):
        self.steps = -1
        self.cpu = cpu
        self.context = cpu_context(cpu)
        self.function = None
        self.current_frame_no = 0
        self.current_frame = []
        self.displayed_steps = -2

    def update(self):
        s = SIM_step_count(self.cpu)
        if s != self.steps or cpu_context(self.cpu) != self.context:
            # instructions have been executed or context changed
            # since last update --- invalidate cached state
            self.current_frame_no = 0
            self.current_frame = []
            self.steps = s

    def set_function(self, fun):
        self.function = fun

    def set_displayed_steps(self):
        self.displayed_steps = self.steps

    def set_stack_frame(self, frame_no):
        if frame_no != self.current_frame_no or not self.current_frame:
            st = cpu_symtable(self.cpu)
            if not st:
                pr("No symtable\n")
                return []
            try:
                tr = stif.stack_trace(self.cpu, frame_no + 1)
            except:
                tr = []
            if len(tr) > frame_no:
                self.current_frame = tr[frame_no]
                self.current_frame_no = frame_no
            else:
                self.current_frame = []
        return self.current_frame

debug_states = {}

def debug_state(cpu):
    global debug_states
    d = debug_states.get(cpu)
    if not d:
        d = debug_states[cpu] = Debug_state(cpu)
    d.update()
    return d

def eval_sym(cpu, expr, fmt):
    if cpu == None:
        cpu = current_processor()
    ds = debug_state(cpu)
    fr = ds.set_stack_frame(ds.current_frame_no)
    try:
        return stif.eval_sym(cpu, expr, fr, fmt)[1]
    except SimExc_General, msg:
        raise CliError, msg

def psym_cmd(cpu, expr):
    res = eval_sym(cpu, expr, '')
    pr("%s\n" % res)

for ns in ("", "processor"):
    new_command("psym", ns_fun(ns, psym_cmd),
                [arg(str_t, "expression")],
                namespace = ns,
                type = ["Symbolic Debugging"],
                see_also = ['stack-trace', 'frame', 'symval'],
                short = "print value of symbolic expression",
                doc = """
Evaluates <i>expression</i> in the current stack frame, and prints the result
in a human-readable form. The only C operators allowed are casts, indirection,
member selection, and <tt>sizeof</tt> (thus no arithmetic). You may need to
surround the <i>expression</i> by double quotes if it contains certain
meta-characters.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="422")

def symval_cmd(cpu, expr):
    return eval_sym(cpu, expr, 'v')

for ns in ("", "processor"):
    new_command("symval", ns_fun(ns, symval_cmd),
                [arg(str_t, "expression")],
                namespace = ns,
                alias = "sym",
                pri = 1000,
                type = ["Symbolic Debugging"],
                see_also = ['stack-trace', 'frame', 'psym'],
                short = "evaluate symbolic expression",
                doc = """
Evaluates <i>expression</i> in the current stack frame. The only C operators
allowed are casts, indirection, member selection, and <tt>sizeof</tt> (thus no
arithmetic). You may need to surround the <i>expression</i> by double quotes if
it contains certain meta-characters. In contrast to <b>psym</b>, the result is
returned as an unadorned value that can be used in CLI expressions.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="439")

def pos_cmd(ns_obj, arg):
    if ns_obj == None:
        cpu = current_processor()
        st = cpu_symtable(cpu)
    elif SIM_object_is_processor(ns_obj):
        cpu = ns_obj
        st = cpu_symtable(cpu)
    else:
        cpu = None
        st = ns_obj
    if not st:
        pr("No symbols loaded.\n")
        return
    (type, val, _) = arg
    file = ""
    function = ""
    line = 0
    if type == int_t:
        line = val
    else:
        colon = val.rfind(':')
        if colon < 0:
            function = val
        else:
            file = val[:colon]
            rest = val[colon + 1:]
            if rest.isdigit():
                line = int(rest)
            else:
                function = rest
    if line and not file:
        if cpu == None:
            pr("Must specify a file when called from the"
               + " symtable namespace.\n")
            return
        else:
            pc = SIM_get_program_counter(cpu)
            pos = st.source_at[pc]
            if pos:
                file = pos[0]
    ret = st.addr_of[[file, line, function]]
    if ret == None:
        pr("Address not found.\n")
    return ret

for ns in ("", "processor", "symtable"):
    new_command("pos", ns_fun(ns, pos_cmd),
                [arg((int_t, str_t), ("line", "function"))],
                namespace = ns,
                type = ["Symbolic Debugging"],
                see_also = ['stack-trace', 'psym', 'symval'],
                short = "address of line or function",
                doc = """

Finds the address of a source line or a function in a given file
(e.g., <tt>myfile.c:4711</tt> or <tt>myfile.c:myfunction</tt>). If
only a line number is specified, the command looks at the current
value of the program counter to determine the current file. (If this
command is called from the symtable namespace, no current file is
defined.) It may be necessary to put the argument inside double quotes
for it to be parsed correctly.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="500")

def whereis_cmd(st, data_only, address):
    if st == None:
        st = cpu_symtable(current_processor())
    if not st:
        pr("No symbols loaded.\n")
        return
    if not data_only:
        pos = st.source_at[address]
        if pos:
            [file, line, fun] = pos
            pr("in %s()" % fun)
            if line:
                pr(" at %s:%d" % (file, line))
            pr("\n")
            return
    pos = st.data_at[address]
    if pos:
        [file, var, type, ofs] = pos
        pr("%s" % var)
        if ofs:
            pr("+0x%x" % ofs)
        if type:
            pr(" (type %s)" % type)
        if file:
            pr(" in %s" % file)
        pr("\n")
    else:
        pr("Address 0x%x is not in any known location.\n" % address)

for ns in ("", "symtable"):
    new_command("whereis", ns_fun(ns, whereis_cmd),
                [arg(flag_t, "-d"), arg(int_t, "address")],
                namespace = ns,
                type = ["Symbolic Debugging"],
                see_also = ['pos', 'psym'],
                short = "find symbol by address",
                doc = """
Displays the function or variable and (if possible) the source file and line
number corresponding to <i>address</i>. If <tt>-d</tt> is specified, searches
only data symbols. Does not look for stack-allocated variables.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="546")

def frame_cmd(cpu, frame_no):
    if cpu == None:
        cpu = current_processor()
    ds = debug_state(cpu)
    if frame_no == None:
        frame_no = ds.current_frame_no
    if frame_no < 0:
        pr("Cannot go that far down the stack\n")
        return
    f = ds.set_stack_frame(frame_no)
    if f:
        print_frame(cpu, cpu_symtable(cpu), frame_no, f)
    else:
        pr("No frame %d found.\n" % frame_no)

for ns in ("", "processor"):
    new_command("frame", ns_fun(ns, frame_cmd),
                [arg(int_t, "frame-number", "?", None)],
                namespace = ns,
                alias = "f",
                type = ["Symbolic Debugging"],
                see_also = ['stack-trace', 'psym', 'up', 'down'],
                short = "change current stack frame",
                doc = """
Changes current stack frame to <i>frame-number</i>, or displays the current
frame.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="573")

def up_cmd(cpu, n):
    if cpu == None:
        cpu = current_processor()
    frame_cmd(cpu, debug_state(cpu).current_frame_no + n)

for ns in ("", "processor"):
    new_command("up", ns_fun(ns, up_cmd),
                [arg(int_t, "N", "?", 1)],
                namespace = ns,
                type = ["Symbolic Debugging"],
                see_also = ['frame', 'down', 'stack-trace'],
                short = "go up N stack frames",
                repeat = ns_fun(ns, up_cmd),
                doc = """
Moves <i>N</i> frames up the stack (towards the outermost frame).
<i>N</i> defaults to one.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="590")

def down_cmd(cpu, n):
    if cpu == None:
        cpu = current_processor()
    frame_cmd(cpu, debug_state(cpu).current_frame_no - n)

for ns in ("", "processor"):
    new_command("down", ns_fun(ns, down_cmd),
                [arg(int_t, "N", "?", 1)],
                namespace = ns,
                type = ["Symbolic Debugging"],
                see_also = ['frame', 'up', 'stack-trace'],
                short = "go down N stack frames",
                repeat = ns_fun(ns, down_cmd),
                doc = """
Moves <i>N</i> frames down the stack (towards the innermost frame).
<i>N</i> defaults to one.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="607")


last_list_file = ''
last_list_line = -1

def list_cmd(ns_obj, flags, arg, maxlines):
    global last_list_file
    global last_list_line
    s_flag = (flags and flags[2] == '-s')
    d_flag = (flags and flags[2] == '-d')
    if ns_obj == None:
        cpu = current_processor()
        st = cpu_symtable(cpu)
    elif SIM_object_is_processor(ns_obj):
        cpu = ns_obj
        st = cpu_symtable(cpu)
    else:
        cpu = None
        st = ns_obj
    if not st:
        pr("No symbols loaded.\n")
        return

    (type, val, _) = arg
    file = ""
    function = ""
    line = 0
    limit = None
    if not maxlines:
        maxlines = 20

    if type == int_t:
        addr = val
    else:
        colon = val.find(':')
        if colon < 0:
            function = val
        else:
            file = val[:colon]
            rest = val[colon + 1:]
            if rest.isdigit():
                line = int(rest)
            else:
                function = rest
                if function == "":
                    print "bad argument"
                    return

    if function:
        fa = st.fun_addr[[function, None]]
        if not fa:
            pr("%s: no such function\n" % function)
            return
        (addr, _, fn_size) = fa
        if fn_size:
            limit = addr + fn_size;
        else:
            pr("Warning: cannot get function size.\n")

    elif line:
        if not file:
            if cpu == None:
                pr("Must specify a file when called from the"
                   + " symtable namespace.\n")
                return
            pc = SIM_get_program_counter(cpu)
            pos = st.source_at[pc]
            if pos:
                file = pos[0]
            else:
                pr("No current file found\n")
                return
        addr = st.addr_of[[file, line, '']]
        
    if not (s_flag or d_flag):
        global selected_profiles, the_source_profile_cache
        if not line:
            pos = st.source_at[addr]
            if not pos or pos[1] == 0:
                pr("No source line corresponding to 0x%x\n" % addr)
                return
            [file, line, fun] = pos
        profs = the_source_profile_cache.get(st, selected_profiles)
        print_source_lines(st, file, line, maxlines, profs)
        last_list_file = file
        last_list_line = line + maxlines - 1
    else:
        if cpu == None:
            pr("Cannot disassemble when called from the symtable namespace.\n")
            return
        if addr == None:
            pr("No address corresponding to %s:%d\n" % (file, line))
            return
        if not line:
            pos = st.source_at[addr]
            if pos:
                line = pos[1]
        linesout = 0
        line = 0
        file = None
        while linesout < maxlines:
            if s_flag:
                lines = st.source_lines[addr] or []
                for (cur_file, cur_line) in lines:
                    if not line or file != cur_file:
                        line = cur_line - 1
                        file = cur_file
                    while line < cur_line:
                        line += 1
                        print_source_lines(st, file, line, 1, [])
                        last_list_file = file
                        last_list_line = line
                        linesout += 1
                        if linesout >= maxlines:
                            return
            len = local_print_disassemble_line(cpu, addr, 1)
            addr += len
            linesout += 1
            if limit and addr > limit:
                break

def list_cmd_repeat(ns_obj, flags, arg, maxlines):
    global last_list_file
    global last_list_line
    list_cmd(ns_obj, flags,
             (str_t, "%s:%d" % (last_list_file, last_list_line + 1), 0),
             maxlines)

for ns in ("", "processor", "symtable"):
    new_command("list", ns_fun(ns, list_cmd),
                [arg((flag_t, flag_t), ("-s", "-d"), "?"),
                 arg((int_t, str_t), ("address", "location")),
                 arg(int_t, "maxlines", "?")],
                namespace = ns,
                repeat = ns_fun(ns, list_cmd_repeat),
                type = ["Symbolic Debugging"],
                see_also = ['disassemble', 'whereis', 'pos', 'symval'],
                short = "list source and/or disassemble",
                doc = """
List the source code corresponding to a given address, function or line.
The location can be specified as

<i>line</i> or <i>file</i><tt>:</tt><i>line</i> --- list from given line

<i>function</i> or <i>file</i><tt>:</tt><i>function</i> --- list that function

<i>address</i> --- list from that address

At most <i>maxlines</i> lines of source or asm are printed.
<tt>-s</tt> produces source intermixed with disassembly, and <tt>-d</tt>
only disassembles.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="746")

#
# profiling commands
#

def function_profile(profiler, maxfuncs, cutoff):
    st = cpu_symtable(current_processor())
    if not st:
        pr("No symbols loaded.\n")
        return
    pif = profiler.iface._data_profiler
    funcs = []
    for fn, file, start, end in st.functions:
        hits = pif.accum_in_range(profiler, start, end - 1)
        if hits >= cutoff:
            funcs.append((hits, fn, file))
    # place hits first in tuple so we can use the built-in sorter
    funcs.sort()
    funcs.reverse()
    pr("     count function                       file\n")
    n = 0
    for hits, fn, file in funcs:
        n += 1
        if n > maxfuncs:
            break
        pr("%10d %-30s %s\n" % (hits, fn, file))
    # FIXME: show the sum of functions shown and the total of that profiler.
    # This requires an interface to an efficient sum-of-all-counters function.

new_command("function-profile", function_profile,
            [arg(obj_t("profiler", "data-profiler"), "profiler"),
             arg(int_t, "maxfuncs", "?", 10),
             arg(int_t, "cutoff", "?", -1)],
            type = ["Profiling"],
            short = "list functions sorted by profile counts",
            doc = """
Lists the most interesting functions by their number of profile
counts, as determined by <arg>profiler</arg>. No more than
<arg>maxfuncs</arg> functions (10 by default) are listed, and not
functions with fewer hits than <arg>cutoff</arg>.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="797")

selected_profiles = []

def select_profiles(profiles):
    global selected_profiles
    selected_profiles = profiles

new_command("select-profiles", select_profiles,
            [arg(obj_t("profiler", "data-profiler"), "profiler", "*", "")],
            type = ["Profiling"],
            short = "set profilers to display in source listing",
            doc = """
Specifies what profiles, if any, should be shown in subsequent source code
listings, and in what order. Use without argument to show none.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="815")

def timestamp():
    return [ SIM_cycle_count(o) for o in SIM_all_objects()
             if SIM_object_is_processor(o) ]

# Source-level mapping of a profile
class source_profile:
    def __init__(self, profile, symtable):
        self.files = {}                 # file -> line -> count
        for f in stif.source_profile(symtable, profile):
            file = f[0]
            lines = {}
            for l, c in f[1:]:
                lines[l] = c
            self.files[file] = lines

    def line_prof(self, file):
        return self.files.get(file, {})

# Cache of source profiles
class source_profile_cache:
    def __init__(self):
        self.timestamp = None
        self.symtable = None
        self.src_profs = {}             # profile -> source_profile

    # retrieve source profiles corresponding to a given list of profiles
    def get(self, symtable, profiles):
        now = timestamp()
        if self.timestamp != now or self.symtable != symtable:
            self.src_profs = {}
            self.timestamp = now
            self.symtable = symtable

        for p in profiles:
            if not self.src_profs.has_key(p):
                self.src_profs[p] = source_profile(p, symtable)

        return [ self.src_profs[p] for p in profiles ]

the_source_profile_cache = source_profile_cache()

#
# Commands for self-profiling (internal)
#

def simics_symbols_cmd(load_all, verbose, name):
    try:
        st = SIM_get_object(name)
    except:
        name = re.sub(r'[^a-zA-Z0-9-_]', '-', name)
        st = SIM_create_object("symtable", name, [])
        pr("Created symbol table '%s'\n" % name)
    print "Loading Simics symbols",
    if load_all:
        val = 1
        print " (with detailed debug info)",
    else:
        val = 0
    print "..."
    try:
        st.simics_symbols = [val, verbose]
    except SimExc_General:
        global selfprof_enabled
        print "Self-profiling not supported."
        selfprof_enabled = False

new_command("simics-symbols", simics_symbols_cmd,
            [arg(flag_t, "-a"),
             arg(flag_t, "-v"),
             arg(str_t, "name", "?", "internal-symbols")],
            type = "internal commands",
            see_also = ['selfprof-start'],
            short = "load debugging symbols from Simics itself",
            doc = """
Load debugging symbols from the Simics binary itself into the symtable
<i>name</i> (created if it does not already exist. <i>name</i> defaults to
"internal-symbols". The <tt>-a</tt> switch causes all detailed debug info to be
loaded; this is not necessary for self-profiling but gives better stack
traces. The <tt>-v</tt> switch runs the command in verbose mode, printing more
information about where symbols are loaded from.
""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="889")

def selfprof_dump_cmd(file):
    st = get_internal_symtable()
    st.selfprof_dump_flat = file

new_command("selfprof-dump", selfprof_dump_cmd,
            [arg(filename_t(exist = 0), "file")],
            type = "internal commands",
            see_also = ['selfprof-start'],
            short = "dump Simics profiling information to a file",
            doc = """
Write the result of a flat profiling run to <i>file</i>. Several files with
the given name as prefix will be created.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="909")

def selfprof_start_cmd(flat, skip, call_bufs):
    if not selfprof_enabled:
        print "Self-profiling not supported!"
        return
    try:
        st = conf.internal_symbols
    except:
        simics_symbols_cmd(0, 0, "internal-symbols")
        try:
            st = conf.internal_symbols
        except Exception, msg:
            print "Failed to read symbols:", msg
            raise CliError

    try:
        st.selfprof_active = [skip, call_bufs, flat]
        print "Started self-profiling."
    except Exception, msg:
        print "Failed starting selfprof:" , msg
        raise CliError

new_command("selfprof-start", selfprof_start_cmd,
            [arg(flag_t, "-f"),
             arg(int_t, "skip", "?", 0),
             arg(int_t, "call-buffers", "?", 10000)],
            type = "internal commands",
            see_also = ['selfprof-stop', 'selfprof-continue'],
            short = "start self-profiling",
            doc = """
Start profiling of Simics itself. If the debugging symbols are not already read
in, it is done first. <i>skip</i> is the number of stack frames to skip from
the call root (since the first functions are always the same, like main);
default not to skip any . <i>call-buffers</i> the number of call entry buffers to
allocate; only raise it from the default (10000) if you get a warning in a
previous run. The <tt>-f</tt> switch turns on flat profiling.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="939")

def get_internal_symtable():
    try:
        return SIM_get_object("internal-symbols")
    except:
        raise CliError, "No internal-symbols object found."

def selfprof_stop_cmd():
    st = get_internal_symtable()
    try:
        st.selfprof_active = 0
    except Exception, msg:
        print "Failed stopping self-profiling:", msg
        raise CliError

new_command("selfprof-stop", selfprof_stop_cmd,
            [],
            type = "internal commands",
            see_also = ['selfprof-start', 'selfprof-continue'],
            short = "stop self-profiling",
            doc = """
Stop profiling. The profiling run can be resumed with
<b>selfprof-continue</b>.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="968")

def selfprof_continue_cmd():
    st = get_internal_symtable()
    try:
        st.selfprof_active = 1
    except Exception, msg:
        print "Failed continuing self-profiling:", msg
        raise CliError

new_command("selfprof-continue", selfprof_continue_cmd,
            [],
            type = "internal commands",
            see_also = ['selfprof-start', 'selfprof-stop'],
            short = "continue self-profiling",
            doc = """
Continue an already started profiling run.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="985")

def selfprof_list_cmd(flag, n, func, file):
    st = get_internal_symtable()
    st.selfprof_list = [n, func, flag, file]

new_command("selfprof-list", selfprof_list_cmd,
            [arg(flag_t, "-a"),
             arg(int_t, "n", "?", 10),
             arg(str_t, "func", "?", ""),
             arg(str_t, "file", "?", "")],
            type = "internal commands",
            see_also = ['selfprof-start', 'selfprof-stop', 'selfprof-graph'],
            short = "list static profile",
            doc = """
List the <i>n</i> most executed functions during the previous profile run,
defaulting to 10. If <tt>-a</tt> is given, list functions in order of
accumulated times (including time spent in callees). If <i>func</i> is given,
only list functions whose name start with that string. If <i>file</i> is given,
only functions in that file are listed.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="997")

page_types = ['A1', 'A2', 'A3', 'A4']

def selfprof_graph_cmd(func, cutoff, dot_file, page_type):
    if page_type[-1] == 'L':
        page_type = page_type[:-1]
        landscape = True
    else:
        landscape = False
    try:
        page = page_types.index(page_type) + 1
    except Exception, msg:
        print "Unknown page type %s, use one of %s" % (page_type,
                                                       ' '.join(page_types))
        raise CliError
    st = get_internal_symtable()
    try:
        st.selfprof_graph = [func, cutoff, dot_file, page, landscape]
    except Exception, msg:
        print "Failed getting selfprof-graph: %s" % msg
        raise CliError
    if dot_file:
        print "File %s generated." % dot_file
        (file, ext) = dot_file.rsplit('.', 1)
        try:
            os.system('dot -Tps -o %s.ps %s' % (file, dot_file))
            print "Converted to Postscript. File: %s.ps" % file
        except Exception:
            pass

new_command("selfprof-graph", selfprof_graph_cmd,
            [arg(str_t, "function", "?", None),
             arg(float_t, "cutoff", "?", 0.0),
             arg(str_t, "dot-file", "?", ""),
             arg(str_t, "page-size", "?", "A4")],
            type = "internal commands",
            see_also = ['selfprof-start', 'selfprof-stop', 'selfprof-list'],
            short = "list dynamic profile",
            doc = """
List the call path for <i>function</i> and the accumulated time spent in each
function called from this path. <i>cutoff</i>, if nonzero, limits the display
to paths where at least <i>cutoff</i>% of the time is spent; To print the
result in a dot graphics language file, specify a file name using the
<i>dot-file</i> argument. When <i>dot-file</i> is used, the <i>page-size</i>
argument specify the size of the generated graph and should be one of
A1, A2, A3 and A4.
""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="1041")

def selfprof_info_cmd():
    st = get_internal_symtable()
    st.selfprof_info

new_command("selfprof-info", selfprof_info_cmd,
            [],
            type = "internal commands",
            see_also = ['selfprof-list', 'selfprof-graph'],
            short = "show some profiling info",
            doc = """
Print some information about the last profiling run.""", filename="/mp/simics-3.0/src/extensions/symtable/commands.py", linenumber="1063")

#
# Source line functions
#

# Search for a file in a semicolon-separated path list using path substitution:
# 'A>B' means that the prefix A should be changed to B. No '>'
# means that the path should be prepended as usual.
#
# Return [file, filename], or None if not found.
# The file is opened in binary mode.
#
def open_in_path(name, path):

    def isdelim(ch):
        return ch == "/" or ch == "\\"
    def hasbackslash(path):
        return path.find("\\") >= 0

    # always try an empty path at the end, in case all other rules fail
    for p in path.split(';') + ['']:
        pair = p.split('>')
        if len(pair) > 1:
            old = pair[0]
            new = pair[1]
        else:
            old = ''
            new = p

        # Make sure the substitution prefix is delimiter-terminated if the
        # pattern prefix is (otherwise /foo/>/bar translates /foo/x to /barx)
        if new and not isdelim(new[-1]) and old and isdelim(old[-1]):
            if hasbackslash(path):
                new += "\\"
            else:
                new += "/"
            
        if name[:len(old)] != old:
            continue
        tail = name[len(old):]
        if hasbackslash(new):
            # substitution to a DOS-style path: change all remaining
            # slashes to backslashes, so we don't mix them
            tail = tail.replace("/", "\\")
        if new and isdelim(new[-1]) and tail and isdelim(tail[0]):
            new = new[:-1]              # avoid double delimiters
        pname = os.path.expanduser(new + tail)
        try:
            f = open(SIM_native_path(pname), 'rb')
            return [f, pname]
        except:
            pass
    return None

# make a list of the offsets of the lines of a file
def file_offsets(file):
    # slow but maybe the fastest way to do it in Python?
    # (faster than repeated file.readline() anyway)
    ofslist = [0]
    bufsiz = 16384
    bufofs = 0
    while 1:
        buf = file.read(bufsiz)
        if not buf: break
        k = buf.find('\n', 0)
        while k >= 0:
            ofslist.append(bufofs + k + 1)
            k = buf.find('\n', k + 1)
        bufofs += len(buf)
    return ofslist

class cached_src_file:
    def __init__(self, filename, search_path):
        self.original_filename = filename
        self.original_search_path = search_path
        self.name = filename + " " + search_path
        self.file, self.host_file = open_in_path(filename, search_path)
        self.ofslist = None
        self.mtime = os.stat(self.host_file).st_mtime

    def need_refresh(self):
        return (self.mtime != os.stat(self.host_file).st_mtime)

    # read 'nlines' lines starting from 'line'. Include all line endings
    # (\n or \r\n) in the returned string.
    def getlines(self, line, nlines = 1):
        line -= 1                       # lines are 1-numbered
        if self.ofslist == None or self.need_refresh():
            self.file.close()
            self.file, self.host_file = open_in_path(self.original_filename,
                                                     self.original_search_path)
            self.ofslist = file_offsets(self.file)
            self.mtime = os.stat(self.host_file).st_mtime
        if line < 0 or line >= len(self.ofslist):
            return ""
        self.file.seek(self.ofslist[line])
        lines = ""
        for i in range(nlines):
            lines = lines + self.file.readline()
        return lines

class src_files:
    def __init__(self):
        self.init()

    def init(self):
        self.files = {}
        self.lru = []
        self.max_cached = 16            # max files to cache

    def flush(self):
        self.init()

    def getfile(self, file, search_path):
        index = file + " " + search_path
        f = self.files.get(index)
        if f:
            # file in cache
            self.lru.remove(f)
        else:
            # file not in cache - insert new entry
            try:
                f = cached_src_file(file, search_path)
            except:
                return None
            self.files[index] = f
            if len(self.files) > self.max_cached:
                kick = self.lru[0]
                del self.lru[0]
                del self.files[kick.name]

        self.lru.append(f)
        return f
        
filecache = src_files()

# This variable is not used right now. We want to be able to control emacs
# in a gdb-like way though.
in_emacs = 0

def list_with_line_numbers(lines, linenum, profs):
    for line in (lines.split("\n"))[:-1]:
        profstr = ""
        if profs:
            counters = [ p.get(linenum, 0) for p in profs ]
            if max(counters):
                profstr = " [" + " ".join(["%6d" % c for c in counters]) + "]"
            else:
                profstr = " " * (2 + len(counters) * 7)
        pr("%3d%s   %s\n" % (linenum, profstr, line))
        linenum += 1

def print_source_lines(st, file, line, nlines, src_profs):
    spath = get_source_path(st)
    f = filecache.getfile(file, spath)
    if f:
        lineprofs = [ sp.line_prof(file) for sp in src_profs ]
        list_with_line_numbers(f.getlines(line, nlines), line, lineprofs)

def print_source_pos(st, pos):
    global filecache
    [file, line, fun] = pos
    if line > 0:
        spath = get_source_path(st)
        f = filecache.getfile(file, spath)
        if f:
            if in_emacs:
                pr("\032\032%s:%d:0:beg:0x0\n" % (f.host_file, line))
            else:
                pr("%d\t%s" % (line, f.getlines(line)))
        else:
            pr("%d\t(file %s not found)\n" % (line, file))

def print_current_source_pos():
    try:
        cpu = current_processor()
    except:
        return                          # no config loaded
    ds = debug_state(cpu)
    if ds.steps != ds.displayed_steps:
        st = cpu_symtable(cpu)
        if st:
            pc = SIM_get_program_counter(cpu)
            pos = st.source_at[pc]
            if pos:
                if ds.function != pos[2]:
                    ds.set_function(pos[2])
                    fr = ds.set_stack_frame(ds.current_frame_no)
                    if fr:
                        st = cpu_symtable(cpu)
                        print_frame(cpu, st, -1, fr)
                print_source_pos(st, pos)
                ds.set_displayed_steps()

def prompt_callback(foo, obj):
    if SIM_is_interactive() and SIM_get_class_attribute('symtable',
                                                        'display_position'):
        print_current_source_pos()

SIM_hap_add_callback("Core_Back_To_Front", prompt_callback, 0)
