
from cli import *
import re, os.path
from sim_commands import local_print_disassemble_line

def new_symtable_cmd(name, file, start, t):
    if not name:
        seq = 0
        if file:
            # try deriving an object name from the first valid part of the
            # file name
            m = re.match(r'[^a-zA-Z]*([a-zA-Z][a-zA-Z0-9_-]*)',
                         os.path.basename(file))
            if m:
                name = m.group(1)
                # strip bad characters from object name
                name = re.sub(r'[^a-zA-Z0-9_-]', '-', name)
                seq = -1
        if not name:
            name = "st0"
        try:
            while 1:
                SIM_get_object(name)
                seq = seq + 1
                name = "st%d" % seq
        except SimExc_General:
            pass
            
    try:
        st = SIM_new_object("symtable", name)
    except SimExc_General, msg:
        pr("Failed creating object %s: %s\n" % (name, msg))
        return
    print "Created symbol table '%s'" % name

    if file:
        from mod_symtable_commands import obj_load_symbols_cmd
        obj_load_symbols_cmd(st, file, start, t)
        print "ABI for", name, "is", st.abi

    try:
        cpu = current_processor()
        ctx = cpu.current_context
    except:
        cpu = ctx = None
    if ctx and not ctx.symtable:
        from mod_symtable_commands import ctx_archs
        archs = ctx_archs(ctx)
        if len(archs) == 1:
            # All cpus have the same architecture: use it
            ctx_arch = list(archs)[0]
            if st.arch_compat[ctx_arch]:
                st.arch = ctx_arch
                ctx.symtable = st
                print "%s set for context %s" % (st.name, ctx.name)
            else:
                print "Symbols loaded for", st.arch, "- symtable not attached"
        else:
            print "Context", ctx.name, "is heterogenous: symtable not attached"
    return (name, )

new_command("new-symtable", new_symtable_cmd,
            [arg(str_t, "name", "?", ""),
             arg(filename_t(exist = 1, simpath = 1), "file", "?", ""),
             arg(int_t, "start", "?", -1),
             arg(flag_t, "-t")],
            type = ["Symbolic Debugging"],
            see_also = ['<symtable>.load-symbols', 'set-context'],
            short = "create new symbol table",
            doc = """
Creates a new symbol table, calling it <i>name</i> (or inventing a new name if
omitted), and optionally loads debug info from <i>file</i>, using the Simics
search path to do so.
If <i>start</i> is given, it is the (absolute) starting address of the
file's code. If <tt>-t</tt> is specified, <i>start</i> is interpreted
as the address of the .text section (similarly to GDB); otherwise
<i>start</i> is taken to be the address of the first executable
segment.
If the current context of the selected cpu does not have an associated
symbol table, it will be set to the newly created symbol table.""", filename="/mp/simics-3.0/src/extensions/symtable/gcommands.py", linenumber="62")
