from cli import *
import string
import fp_to_string
import sim_commands
import sim_profile_commands

def global_set_names(obj):
    return obj.global_set_names

def local_pending_exception(cpu):
    if cpu.pending_trap:
        id = cpu.pending_trap
    elif (cpu.pending_interrupt
          and cpu.extra_irq_enable
          and SIM_read_register(cpu, SIM_get_register_number(cpu, "pstate")) & 2):
        id = cpu.pending_interrupt
        if id < 0x16:
            id = 0x40 + cpu.pending_interrupt
    else:
        return None
    try:
        str = SIM_get_exception_name(cpu, id)
    except:
        str = "Unknown"
    return "Pending trap (0x%x) %s" % (id, str)

local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun()

#
# -------------------- local-pregs --------------------
#

def sparc_read_int_register(obj, regname):
    return obj.iface.int_register.read(obj, obj.iface.int_register.get_number(obj, regname))
                           
def local_pregs(obj, all, print_control_regs = 1):
    if all:
        pregs_all_cmd(obj)
        return
        
    print "Processor %s:" % obj.name

    fn = sim_commands.get_obj_funcs(obj)['global_set_names']
    global_bank = fn(obj)[obj.current_globals]
    
    print "    %%g %-8s            %%o                   %%l                  %%i" % global_bank
    
    for i in range(8):
        print "%d %s  %s  %s  %s" % (i,
                                     "0x%016x" % sparc_read_int_register(obj, "g"+`i`),
                                     "0x%016x" % sparc_read_int_register(obj, "o"+`i`),
                                     "0x%016x" % sparc_read_int_register(obj, "l"+`i`),
                                     "0x%016x" % sparc_read_int_register(obj, "i"+`i`))
                                     
    print
    if print_control_regs:
        print_control_registers(obj, 0)

def print_control_registers(obj, all):

    print "          %pc                %npc                %tba                %cwp"
    print "  0x%016x  0x%016x  0x%016x  0x%016x" % (
        sparc_read_int_register(obj, "pc"),
        sparc_read_int_register(obj, "npc"),
        sparc_read_int_register(obj, "tba"),
        sparc_read_int_register(obj, "cwp"))
    
    print "          %ccr               %fprs               %fsr                %pstate"
    print "  0x%016x  0x%016x  0x%016x  0x%016x\n" % (
        sparc_read_int_register(obj, "ccr"),
        sparc_read_int_register(obj, "fprs"),
        sparc_read_int_register(obj, "fsr"),
        sparc_read_int_register(obj, "pstate"))
    
    print "          %asi               %gsr                %tl                 %pil"
    print "  0x%016x  0x%016x  0x%016x  0x%016x" % (
        sparc_read_int_register(obj, "asi"),
        sparc_read_int_register(obj, "gsr"),
        sparc_read_int_register(obj, "tl"),
        sparc_read_int_register(obj, "pil"))
    
    print "          %cansave           %canrestore         %cleanwin           %otherwin"
    print "  0x%016x  0x%016x  0x%016x  0x%016x" % (
        sparc_read_int_register(obj, "cansave"),
        sparc_read_int_register(obj, "canrestore"),
        sparc_read_int_register(obj, "cleanwin"),
        sparc_read_int_register(obj, "otherwin"))
    
    print "          %softint           %wstate             %y                  $globals"
    print "  0x%016x  0x%016x  0x%016x  0x%016x" % (
        sparc_read_int_register(obj, "softint"),
        sparc_read_int_register(obj, "wstate"),
        sparc_read_int_register(obj, "y"),
        SIM_get_attribute(obj, "current-globals"))

    try:
        # dummy to check if reg exists (UIII only)
        sparc_read_int_register(obj, "stick")
        stick_head = "          %stick              %stick_cmpr"
        stick_value = " 0x%016x  0x%016x" % (
            sparc_read_int_register(obj, "stick"),
            sparc_read_int_register(obj, "stick_cmpr"))
    except:
        stick_head = ""
        stick_value = ""

    print "          %tick              %tick_cmpr" + stick_head
    print "  0x%016x  0x%016x %s\n" % (
        sparc_read_int_register(obj, "tick"),
        sparc_read_int_register(obj, "tick_cmpr"),
        stick_value)
        
    if all:
        print "          %tpc               %tnpc               %tt"
        for i in range(1, SIM_get_attribute(obj, "max-trap-levels") + 1):
            print "%d 0x%016x  0x%016x  0x%016x" % (
                i,
                sparc_read_int_register(obj, "tpc"+`i`),
                sparc_read_int_register(obj, "tnpc"+`i`),
                sparc_read_int_register(obj, "tt"+`i`))
        print

        print "              CCR    ASI PSTATE    CWP"
        for i in range(1, SIM_get_attribute(obj, "max-trap-levels") + 1):
            print ("%%tstate %d = " % i),
            tstate = sparc_read_int_register(obj, "tstate"+`i`)
            print "0x%2.2x   0x%2.2x  0x%3.3x   0x%2.2x                    = 0x%016x" % (
                (tstate >> 32) & 0xff, (tstate >> 24) & 0xff,
                (tstate >> 8) & 0x3ff, tstate & 0x1f,
                tstate)
    else:
        print "          %tpc               %tnpc               %tstate             %tt"
        for i in range(1, SIM_get_attribute(obj, "max-trap-levels") + 1):
            print "%d 0x%016x  0x%016x  0x%016x  0x%016x" % (
                i,
                sparc_read_int_register(obj, "tpc"+`i`),
                sparc_read_int_register(obj, "tnpc"+`i`),
                sparc_read_int_register(obj, "tstate"+`i`),
                sparc_read_int_register(obj, "tt"+`i`))

    irq = SIM_get_attribute(obj, "pending_interrupt")
    trp = SIM_get_attribute(obj, "pending_trap")
    
    if irq:
        print "   pending irq (%d) %s\n" % (irq, SIM_get_exception_name(obj, irq))

    if trp:
        print "   pending trap (%d) %s\n" % (trp, SIM_get_exception_name(obj, trp))


#
# -------------------- pregs-all --------------------
#

def print_pstate_bits(pstate):
    print "                                                 IG   MG"
    print "  %pstate =                                   ",
    for i in range(11, 9, -1):
        print "   %d" % ((pstate >> i) & 1),
    print
    print "             CLE  TLE   MM  RED  PEF   AM PRIV   IE   AG"
    print "           ",
    for i in range(9, -1, -1):
        if i == 6:
            print "  %d%d" % ((pstate >> (i + 1)) & 1, (pstate >> i) & 1),
        elif i != 7:
            print "   %d" % ((pstate >> i) & 1),
    print " = 0x%016x\n" % pstate;
    

def pregs_all_cmd(cp):
    if not cp:
        cp, _ = get_cpu(kind = ('sparc_v9', 'a SPARC processor'))

    i0 = SIM_get_register_number(cp, "i0")
    l0 = SIM_get_register_number(cp, "l0")
    o0 = SIM_get_register_number(cp, "o0")

    print "Processor %s:" % cp.name

    # global registers
    fn = sim_commands.get_obj_funcs(cp)['global_set_names']
    global_banks = fn(cp)

    print "      %%g (%-9s)      %%g (%-9s)      %%g (%-9s)      %%g (%-9s)" % tuple(global_banks)
        
    for i in range(1,8):
        print "%d 0x%016x  0x%016x  0x%016x  0x%016x" % ( i,
                                      cp.iface.sparc_v9.read_global_register(cp, 0, i),
                                      cp.iface.sparc_v9.read_global_register(cp, 1, i),
                                      cp.iface.sparc_v9.read_global_register(cp, 2, i),
                                      cp.iface.sparc_v9.read_global_register(cp, 3, i))
               
    # register windows
    print "          %i                  %l                  %o"
    for i in range(SIM_get_attribute(cp, "num-windows")):
        print "Window %d:" % i
        for j in range(8):
            print "%d 0x%016x  0x%016x  0x%016x" % (j,
                                       cp.iface.sparc_v9.read_window_register(cp, i, i0 + j),
                                       cp.iface.sparc_v9.read_window_register(cp, i, l0 + j),
                                       cp.iface.sparc_v9.read_window_register(cp, i, o0 + j))

    print
    
    print_control_registers(cp, 1)

    print "\n            N Z V C N Z V C"
    print "     %ccr =",
    ccr = sparc_read_int_register(cp, "ccr");
    for i in range(0, 8):
        print "%d" % ((ccr >> (7 - i)) & 1),
    print "%29s = 0x%016x\n" % ("", ccr);

    # the pstate bits are cpu class specific
    fn = sim_commands.get_obj_funcs(cp)['print_pstate_bits']
    fn(sparc_read_int_register(cp, "pstate"))


new_command("pregs-all", pregs_all_cmd,
            [arg(obj_t('SPARC processor', 'sparc_v9'), "cpu-name", "?")],
            type  = "inspect/change commands",
            short = "print all cpu registers",
            doc = """
SPARC V9 command. Displays the integer processor registers in all windows, as well as
some most control registers such as the program counter.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="220")

#
# -------------------- read-fp-reg-i --------------------
#

def read_fp_reg_i_cmd(num):
    cp = current_processor()
    if not instance_of(cp, "sparc_v9"):
        print "This command is only available for SPARC processors"
        return
    return cp.iface.sparc_v9.read_fp_register_i(cp, num)

new_command("read-fp-reg-i", read_fp_reg_i_cmd,
            [arg(int_t, "reg-num")],
            type  = "inspect/change commands",
            short = "print floating point single register as integer",
            doc = """
SPARC V9 command. Prints a specific floating point register, as integer.
This command supports the 32 single precision registers.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="239")

#
# -------------------- write-fp-reg-i --------------------
#

def write_fp_reg_i_cmd(num, value):
    cp = current_processor()
    cp.iface.sparc_v9.write_fp_register_i(cp, num, value)

new_command("write-fp-reg-i", write_fp_reg_i_cmd,
            [arg(int_t, "reg-num"), arg(int_t, "value")],
            type  = "inspect/change commands",
            short = "write floating point single register as integer",
            doc = """
SPARC V9 command. Writes floating point register (as integer).<br/>
Allows you to selectively modify a floating point register.
Note: takes new value in 32 bit integer format.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="255")

#
# -------------------- read-fp-reg-x --------------------
#

def read_fp_reg_x_cmd(num):
    cp = current_processor()
    return cp.iface.sparc_v9.read_fp_register_x(cp, num)

new_command("read-fp-reg-x", read_fp_reg_x_cmd,
            [arg(int_t, "reg-num")],
            type  = "inspect/change commands",
            short = "print floating point double register as integer",
            doc = """
SPARC V9 command. Prints a specific floating point register, as integer.
This command supports the 32 double precision registers.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="272")

#
# -------------------- write-fp-reg-d --------------------
#

def write_fp_reg_x_cmd(num, value):
    cp = current_processor()
    cp.iface.sparc_v9.write_fp_register_x(cp, num, value)

new_command("write-fp-reg-x", write_fp_reg_x_cmd,
            [arg(int_t, "reg-num"), arg(int_t, "value")], # <b>write-fp-reg-d</b> <i>reg</i> <i>value</i>
            type  = "inspect/change commands",
            short = "write floating point double register as integer",
            doc = """
SPARC V9 command. Writes floating point register (as 64 bit integer).<br/>
Allows you to selectively modify a floating point register.<br/>
Note: takes new value in 64 bit integer format.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="288")

#
# -------------------- print-float-regs --------------------
#

def print_float_regs_cmd():
    cp = current_processor()
    pr("Processor %d:\n" % SIM_get_proc_no(cp))
    pr("           0 - 7            8 - 15            16 - 23            24 - 31\n")
    for i in range(8):
        tmp1 = cp.iface.sparc_v9.read_fp_register_s(cp,  0 + i);
        tmp2 = cp.iface.sparc_v9.read_fp_register_s(cp,  8 + i);
        tmp3 = cp.iface.sparc_v9.read_fp_register_s(cp, 16 + i);
        tmp4 = cp.iface.sparc_v9.read_fp_register_s(cp, 24 + i);
        pr("%d  %-+.10e  %-+.10e  %-+.10e  %-+.10e\n" % (i, tmp1, tmp2, tmp3, tmp4))

    pr("\n");
    print_control_registers(cp, 0)
        
new_command("print-float-regs", print_float_regs_cmd,
            [],
            type  = "obsolete commands",
            short = "print floating point registers",
            doc_items = [('NOTE', 'The values printed may be inaccurate on hosts that are not IEEE-754 compliant.')],
            deprecated = "<sparc_v9>.pregs-fpu",
            see_also = ['print-double-regs', 'print-float-regs-raw'],
            doc = """
SPARC V9 command. Prints contents of the single-precision floating point
registers in exponent form (32 of them).""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="315")

#
# -------------------- print-float-regs-raw --------------------
#

def print_float_regs_raw_cmd():
    cp = current_processor()
    pr("Processor %d:\n" % SIM_get_proc_no(cp))
    pr("       %f0 - %f14         %f16 - %f30");
    pr("        %f32 - %f46        %f48 - %f62\n");
    for i in range(8):
        i2 = i * 2;
        f0 = cp.iface.sparc_v9.read_fp_register_x(cp,  0 + i2);
        f1 = cp.iface.sparc_v9.read_fp_register_x(cp, 16 + i2);
        f2 = cp.iface.sparc_v9.read_fp_register_x(cp, 32 + i2);
        f3 = cp.iface.sparc_v9.read_fp_register_x(cp, 48 + i2);
        pr("%2d 0x%016x 0x%016x 0x%016x 0x%016x\n"
           % (i2, f0, f1, f2, f3))
    pr("\n");
    
    print_control_registers(cp, 0);

new_command("print-float-regs-raw", print_float_regs_raw_cmd,
            [],
            type  = "obsolete commands",
            short = "print raw floating point register contents",
            deprecated = "<sparc_v9>.pregs-fpu",
            see_also = ["print-float-regs", "print-double-regs"],
            doc = """
The entire floating point register bank is printed as integers, each
double-precision register as a 64-bit number. The first half corresponds to the
32 single precision floating-point registers and the first 16 double precision
registers, the second half is the rest of the doubles.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="347")

#
# -------------------- print-double-regs --------------------
#

def print_double_regs_cmd():
    cp = current_processor()
    pr("Processor %d:\n" % SIM_get_proc_no(cp))
    pr("          0 - 14            16 - 30            32 - 46            48 - 62\n")
    for i in range(8):
        tmp1 = cp.iface.sparc_v9.read_fp_register_d(cp,  0 + i*2);
        tmp2 = cp.iface.sparc_v9.read_fp_register_d(cp,  8 + i*2);
        tmp3 = cp.iface.sparc_v9.read_fp_register_d(cp, 16 + i*2);
        tmp4 = cp.iface.sparc_v9.read_fp_register_d(cp, 24 + i*2);
        pr("%2d  %-+.10e  %-+.10e  %-+.10e  %-+.10e\n" % (i*2, tmp1, tmp2, tmp3, tmp4))

    pr("\n");
    print_control_registers(cp, 0)

new_command("print-double-regs", print_double_regs_cmd,
            [],
            type  = "obsolete commands",
            short = "print floating point registers as doubles",
            doc_items = [('NOTE', 'The values printed may be inaccurate on hosts that are not IEEE-754 compliant')],
            deprecated = "<sparc_v9>.pregs-fpu",
            see_also = ['print-float-regs', 'print-float-regs-raw'],
            doc = """
SPARC V9 command. Prints contents of the 32 double precision floating point registers.
Note that the first 16 overlaps with the 32 single precision floating
points registers.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="377")

#
# --- pregs-fpu ---
#

def pregs_fpu_cmd(obj, s, d, q, f, x, i, b):
	if f + x + i + b == 0:
		x = 1
	if s + d + q == 0:
		d = 1
	if f + x + i + b > 1:
		print "Only one flag of -f, -x, -i, -b can be given to the command"
		return
	if s + d + q > 1:
		print "Only one flag of -s, -d, -q can be given to the command"
		return
	if s:
		pr("Single precision (32-bit), ")
		tmp_fp_regs = obj.fp_registers[:16]
		fp_regs = []
		for c in range(16):
			fp_regs.append((tmp_fp_regs[c] >> 32L) & 0xFFFFFFFFL)
			fp_regs.append(tmp_fp_regs[c] & 0xFFFFFFFFL)
		prec = "s"
		mult = 1
		fdigits = 8
		fsize = 16
	if d:
		pr("Double precision (64-bit), ")
		fp_regs = obj.fp_registers
		prec = "d"
		mult = 2
		fdigits = 15
		fsize = 23
	if q:
		pr("Quad precision (128-bit), ")
		tmp_fp_regs = obj.fp_registers
		fp_regs = []
		for c in range(0,32,2):
			fp_regs.append((tmp_fp_regs[c] << 64L) | (tmp_fp_regs[c+1]))
		prec = "q"
		mult = 4
		fdigits = 22
		fsize = 30
	if f:
		pr("floating point view\n")
	if x:
		pr("hexadecimal integer view\n")
	if i:
		pr("decimal integer view\n")
	if b:
		pr("binary floating point view\n")
	for c in range(len(fp_regs)):
		pr("%%f%-2d " % (c * mult))
		if f:
			pr("%s\n" % fp_to_string.fp_to_string_fixed(prec, fp_regs[c], fdigits, fsize))
		if x:
			pr("0x%x\n" % fp_regs[c])
		if i:
			pr("%d\n" % fp_regs[c])
		if b:
			pr("%s\n" % fp_to_string.fp_to_binstring(prec, fp_regs[c]))
	fsr = sparc_read_int_register(obj, "fsr")
	pr("\n")
	pr("       RD   NVM OFM UFM DZM NXM NS ftt   nva ofa ufa dza nxa nvc ofc ufc dzc nxc\n")
        rnd_str = ("near", "zero", "+inf", "-inf")
        ftt_str = ("none ", "ieee ", "unfin", "unimp", "seq  ", "hwerr", "nvreg")
	pr("%%fsr = %s %d   %d   %d   %d   %d   %d  %s %d   %d   %d   %d   %d   %d   %d   %d   %d   %d\n" %
            (rnd_str[(fsr >> 30 & 3)],
             (fsr >> 27) & 1,
             (fsr >> 26) & 1,
             (fsr >> 25) & 1,
             (fsr >> 24) & 1,
             (fsr >> 23) & 1,
             (fsr >> 22) & 1,
             ftt_str[(fsr >> 14) & 7],
             (fsr >> 9) & 1,
             (fsr >> 8) & 1,
             (fsr >> 7) & 1,
             (fsr >> 6) & 1,
             (fsr >> 5) & 1,
             (fsr >> 4) & 1,
             (fsr >> 3) & 1,
             (fsr >> 2) & 1,
             (fsr >> 1) & 1,
             (fsr >> 0) & 1))

new_command("pregs-fpu", pregs_fpu_cmd,
            [arg(flag_t, "-s"), arg(flag_t, "-d"), arg(flag_t, "-q"), arg(flag_t, "-f"), arg(flag_t, "-x"), arg(flag_t, "-i"), arg(flag_t, "-b")],
            namespace = "sparc_v9",
            type  = "inspect/change commands",
            short = "print the floating point registers",
            doc = """
Prints the contents of the floating point registers.<br/>
This command can take one subregister size flag and one formatting flag.<br/>
The subregister size is selected using the either the -s flag (32-bit single precision), the -d flag (64-bit double precision), or the -q flag (128-bit quad precision).<br/>
The formatting flags -f, -x, and -i select the formatting of the output.
The -f flag prints the floating-point values of the registers.
The -x flag prints the contents of the registers as hexadecimal integers.
The -i flag prints the contents of the registers as decimal integers.
With the -b flag, the registers are printed in binary floating point form.
""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="475")

#
# -------------------- trap-info --------------------
#

def trap_info_cmd():
    cp = current_processor()

    max_tl = SIM_get_attribute(cp, "max-trap-levels")
        
    tl = SIM_read_register(cp, SIM_get_register_number(cp, "tl"));

    pr("Current Trap Level %d\n" % tl)
    pr("Level   Trap (num, name)                    CWP             Step\n")
    for i in range(1, max_tl + 1):
        pr("    %d   " % i)
        tt     = SIM_read_register(cp, SIM_get_register_number(cp, "tt%d" % i))
        tstate = SIM_read_register(cp, SIM_get_register_number(cp, "tstate%d" % i))
        tpc    = SIM_read_register(cp, SIM_get_register_number(cp, "tpc%d" % i))

        if tt == 0:
            pr("0x00\n")
        else:
            pr("0x%02x %-30s  %d  %16s\n"
               % (tt,
                  SIM_get_exception_name(cp, tt),
                  tstate & 0x1f,
                  number_str(cp.trap_times[i - 1], 10)))
            if tpc:
                pr("        PC = %s\n" % number_str(tpc, 16))

    pr("\n")

new_command("trap-info", trap_info_cmd,
            [],
            type  = "inspect/change commands",
            short = "print information about current traps",
            doc = """
Print information about current traps.
This includes info such as trap type, time of trap,
and source reference to trap PC for all trap levels.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="523")

def obj_print_instruction_queue(cpu, verbose):
    ifc = SIM_get_interface(cpu, "processor")
    ifc.print_instruction_queue(cpu, verbose)

def print_instruction_queue(cpu, verbose):
    cpu, _ = get_cpu(kind = ('sparc_v9', 'a SPARC processor'))
    obj_print_instruction_queue(cpu, verbose)

if (VT_get_current_loading_module()[-3:] == "-ma"):
    new_command("print-instruction-queue", print_instruction_queue,
                [arg(obj_t('sparc_v9', 'sparc_v9'), "cpu-name", "?"),
                 arg(flag_t, "-v")],
                type  = "inspect/change commands",
                short = "print instruction queue",
                alias = "piq",
                namespace_copy = ("processor", obj_print_instruction_queue),
                doc = """            
Prints the instruction queue (tree) for the selected processor. The
current selected processor is uses for print-instruction-queue if the
cpu-name is omitted.

The instructions are numbered from 0 and up, where 0 is the root of
the tree. If an instruction have an alternative execution path all
instructions in the second path will be indented a few spaces. The
first instructions in both paths will have the same number, i.e. the
numbering corresponds to the depth in the tree.

After the number the virtual address of the instruction is printed
followed by the disassembly string and the phase of the
instruction. 'I' means initiated, 'F' fetched, 'D' decoded, 'E'
executed, and 'R' retired.

If an instruction is stalling on a memory request the memory
transaction id is printed together with the stalling physical
address. CC blocked is printed if the Consistency Controller is
connected to Simics and has blocked the transaction according to its
rules, or if the transaction needs to be blocked to maintain self
consistency. IO serialized is printed if the transaction is a device
access that needs to be executed ordered.

S is printed if the instruction is speculative.

#1 means that the instruction belongs to synchronous category 1,
i.e. cannot run out of order, and #2 means category 2, i.e. it has to
execute alone in the pipeline.

If the -v flag is used all register values used by the instruction is
printed, both input and output values.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="541")

#
# -------------------- list-asis --------------------
#

def list_asis_cmd(obj, asi):
    if asi < 0:
        asis = obj.asi_names[0:256]
    else:
        asis = [obj.asi_names[asi]]
    for i in range(len(asis)):
        if asis[i] != "Undefined":
            print " 0x%02x - %s" % (i, asis[i])
    print ""

new_command("list-asis", list_asis_cmd,
            [arg(int_t, "asi", "?", -1)],
            type  = "inspect/change commands",
            short = "List all ASIs",
            namespace = "sparc_v9",
            doc = """
Print a list of all ASIs for the currently selected
frontend processor.""", filename="/mp/simics-3.0/src/core/sparc-v9/commands.py", linenumber="595")


# we need a SIM_get_all_registers() that take a class variable
def register_registers(user_data, obj):
    ( funcs, cls_name ) = user_data
    next = SIM_next_queue(None)
    while next:
        if next.classname == cls_name:
            break
        next = SIM_next_queue(next)
    if next == None:
        # no cpu found, wait for next Configuration_Loaded
        return
    diff_regs = SIM_get_all_registers(next)
    diff_regs.remove(SIM_get_register_number(next, "pc"))
    diff_regs.remove(SIM_get_register_number(next, "npc"))
    diff_regs.remove(SIM_get_register_number(next, "tick"))
    try:
        # not all cpus have stick
        diff_regs.remove(SIM_get_register_number(next, "stick"))
    except:
        pass
    SIM_hap_delete_callback("Core_Configuration_Loaded", register_registers, cls_name)
    def f(x):
        return SIM_get_register_name(next, x)
    funcs['diff_regs'] = map(f, diff_regs)

def register_diff_registers(funcs, cls_name):
    SIM_hap_add_callback("Core_Configuration_Loaded", register_registers, (funcs, cls_name))
