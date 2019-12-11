import sparc_v9_commands
from cli import *

def global_set_names(obj):
    return ["gl0", "gl1", "gl2", "gl3"]

funcs = { 'print_disassemble_line':
          sparc_v9_commands.local_print_disassemble_line,
          'pregs':
          sparc_v9_commands.local_pregs,
          'print_pstate_bits':
          sparc_v9_commands.print_pstate_bits,
          'global_set_names':
          global_set_names,
          'get_pending_exception_string':
          sparc_v9_commands.local_pending_exception }

class_funcs = { 'ultrasparc-t1': funcs }

sparc_v9_commands.register_diff_registers(funcs, "ultrasparc-t1")

#
# -------------------- pregs-hyper --------------------
#

def pregs_hyper_cmd(cpu_name, all):
    ( cpu, _ ) = get_cpu(cpu_name)
    obj_pregs_hyper_cmd(cpu, all)
    
def obj_pregs_hyper_cmd(obj, all):
    print
    print "    hpstate             htba                hintp              hsystick_cmpr"
    print "  0x%016x  0x%016x  0x%016x  0x%016x" % (
        sparc_v9_commands.sparc_read_int_register(obj, "hpstate"),
        sparc_v9_commands.sparc_read_int_register(obj, "htba"),
        sparc_v9_commands.sparc_read_int_register(obj, "hintp"),
        sparc_v9_commands.sparc_read_int_register(obj, "hstick_cmpr"))
    
    print
    print "    gl"
    print "  0x%016x" % (sparc_v9_commands.sparc_read_int_register(obj, "gl"))

    print
    print "          %htstate"
    for i in range(1, obj.max_trap_levels + 1):
            print "%d 0x%016x" % (
                i,
                sparc_v9_commands.sparc_read_int_register(obj, "htstate"+`i`))
    if all:
        print
        print "              RED   HPRIV TLZ"
        for i in range(1, obj.max_trap_levels + 1):
            print ("%%htstate %d = " % i),
            htstate = sparc_v9_commands.sparc_read_int_register(obj, "htstate"+`i`)
            print "%d     %d     %d                                = 0x%016x" % (
                (htstate >> 5) & 0x1, (htstate >> 2) & 0x1, htstate & 0x1, htstate)
        print
        print "              ENB   RED   HPRIV TLZ"
        print "  %hpstate = ",
        hpstate = sparc_v9_commands.sparc_read_int_register(obj, "hpstate");
        print "%d     %d     %d     %d                          = 0x%016x" % (
            (hpstate >> 11) & 1, (hpstate >> 5) & 0x1, (hpstate >> 2) & 0x1, hpstate & 0x1, hpstate)
        print

new_command("pregs-hyper", pregs_hyper_cmd,
            [arg(str_t, "cpu-name", "?", "", expander = cpu_expander), arg(flag_t, "-all")],
            type  = "inspect commands",
            short = "print hypervisor registers",
            namespace_copy = ("processor", obj_pregs_hyper_cmd),
            see_also = ["pregs", "pregs-all"],
            doc = """
Prints the UltraSPARC T1 specific hypervisor registers for cpu
<i>cpu-name</i>. <arg>-all</arg> will provide a complete listing. If no CPU is
specified, the currently selected frontend processor will be used.
""", filename="/mp/simics-3.0/src/cpu/sparc-niagara/commands.py", linenumber="65")
