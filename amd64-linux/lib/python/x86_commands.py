from cli import *
import sim_commands
import sim_profile_commands
import fp_to_string
import sim_core

column_size = { }

def local_pending_exception(cpu):
    if cpu.pending_exception or cpu.pending_interrupt:
        if cpu.pending_exception:
            return "Pending trap %d" % cpu.pending_exception
        else: # cpu.pending_interrupt
            if cpu.pending_vector_valid:
                return "Pending interrupt, vector 0x%x" % cpu.pending_vector
            else:
                return "Pending interrupt"
    else:
        return None

def x86_print_opcode(cpu, paddr, length):
    b = []
    try:
        for i in range(length):
            b.append("%02x" % SIM_read_phys_memory(cpu, paddr + i, 1))
    except:
        pass
    pr("%-17s" % " ".join(b))
local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun(
    default_instr_len = 1, disasm = SIM_disassemble,
    virtual_address_prefix = "cs", print_opcode = x86_print_opcode)

def local_translate_to_physical(cpu, address):
    p = address[0]
    a = address[1]

    if p == "":
        p = "ds"

    if p == "l" or p == "ld":
        return cpu.iface.x86.linear_to_physical(cpu, 1, a)
    if p == "li":
        return cpu.iface.x86.linear_to_physical(cpu, 0, a)
    elif p == "es":
        return cpu.iface.x86.linear_to_physical(cpu, 1, SIM_get_attribute(cpu, "es")[7] + a)
    elif p == "ds":
        return SIM_logical_to_physical(cpu, 1, a)
    elif p == "cs":
        return SIM_logical_to_physical(cpu, 0, a)
    elif p == "ss":
        return cpu.iface.x86.linear_to_physical(cpu, 1, SIM_get_attribute(cpu, "ss")[7] + a)
    elif p == "fs":
        return cpu.iface.x86.linear_to_physical(cpu, 1, SIM_get_attribute(cpu, "fs")[7] + a)
    elif p == "gs":
        return cpu.iface.x86.linear_to_physical(cpu, 1, SIM_get_attribute(cpu, "gs")[7] + a)

    raise Exception, "Illegal address prefix " + p

def local_get_address_prefix():
    return "ds"

#
# --- Used to read integer register
#

# This shouldn't really be needed, since the generic handling in
# read_reg_cmd in src/core/common/commands.py handles anything
# exported by the register API.  But x86 doesn't expose all below
# through the register API.
def local_read_int_register(obj, reg_name):
    try:
        val = SIM_get_attribute(obj, reg_name)
        if reg_name in ["cs", "ss", "ds", "es", "fs", "gs", "tr", "ldtr"]:
            val = val[0]
    except SimExc_Attribute, msg:
        raise Exception, "Unknown register '" + reg_name + "'"
    return val

def local_write_int_register(obj, reg_name, val):
    try:
        if reg_name in ["cs", "ss", "ds", "es", "fs", "gs"]:
            old = SIM_get_attribute(obj, reg_name)
            old[0] = val & 0xffff
            val = old
        SIM_set_attribute(obj, reg_name, val)
    except SimExc_Attribute, msg:
        raise Exception, "Unknown register '" + reg_name + "'"
    return val

#
# -------------------- local-pregs --------------------
#

def print_eflags(ef):
    pr("eflags = %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d = 0x%s\n" % (
        (ef >> 21) & 1,
        (ef >> 20) & 1,
        (ef >> 19) & 1,
        (ef >> 18) & 1,
        (ef >> 17) & 1,
        (ef >> 16) & 1,
        0,
        (ef >> 14) & 1,
        (ef >> 13) & 1,
        (ef >> 12) & 1,
        (ef >> 11) & 1,
        (ef >> 10) & 1,
        (ef >> 9) & 1,
        (ef >> 8) & 1,
        (ef >> 7) & 1,
        (ef >> 6) & 1,
        0,
        (ef >> 4) & 1,
        0,
        (ef >> 2) & 1,
        1,
        (ef >> 0) & 1,
        hex_str(ef,8)))
    pr("         I V V A V R - N I I O D I T S Z - A - P - C\n")
    pr("         D I I C M F   T O O F F F F F F   F   F   F\n")
    pr("           P F           P P                        \n")
    pr("                         L L                        \n")

def local_string(val, aa64):
	if aa64:
		return "0x%016x" % val
	else:
		return "0x" + hex_str(val, 8)

def get_seg_attribute(obj, segregname):
        return SIM_read_register(obj, SIM_get_register_number(obj, "%s_attr" % segregname))

def get_seg_valid(obj, segregname):
        if SIM_get_attribute(obj, segregname)[9]:
                return ""
        else:
                return ", invalid"

def debug_break_desc(obj, num):
    dr7 = obj.dr7
    enabled = dr7 & (3 << (num * 2))
    rw = (dr7 >> ((num * 4) + 16)) & 3
    len = (dr7 >> ((num * 4) + 18)) & 3
    rw_desc = ("execution", "write", "I/O", "read/write")
    len_desc = ("1 byte", "2 bytes", "8 bytes", "4 bytes")
    if not enabled:
        return "disabled"
    else:
        return "%s, %s" % (len_desc[len], rw_desc[rw])

def print_remaining_regs(obj, aa64):
    reg = local_read_int_register
    pr("\n")
    pr("%s   = 0x%04x, base = 0x%s, limit = 0x%x, attr = 0x%x%s\n" % ("es", reg(obj, "es"), hex_str(SIM_get_attribute(obj, "es")[7],8), SIM_get_attribute(obj, "es")[8], get_seg_attribute(obj, "es"), get_seg_valid(obj, "es")))
    pr("%s   = 0x%04x, base = 0x%s, limit = 0x%x, attr = 0x%x%s\n" % ("cs", reg(obj, "cs"), hex_str(SIM_get_attribute(obj, "cs")[7],8), SIM_get_attribute(obj, "cs")[8], get_seg_attribute(obj, "cs"), get_seg_valid(obj, "cs")))
    pr("%s   = 0x%04x, base = 0x%s, limit = 0x%x, attr = 0x%x%s\n" % ("ss", reg(obj, "ss"), hex_str(SIM_get_attribute(obj, "ss")[7],8), SIM_get_attribute(obj, "ss")[8], get_seg_attribute(obj, "ss"), get_seg_valid(obj, "ss")))
    pr("%s   = 0x%04x, base = 0x%s, limit = 0x%x, attr = 0x%x%s\n" % ("ds", reg(obj, "ds"), hex_str(SIM_get_attribute(obj, "ds")[7],8), SIM_get_attribute(obj, "ds")[8], get_seg_attribute(obj, "ds"), get_seg_valid(obj, "ds")))
    pr("%s   = 0x%04x, base = %s, limit = 0x%x, attr = 0x%x%s\n" % ("fs", reg(obj, "fs"), local_string(SIM_get_attribute(obj, "fs")[7],aa64), SIM_get_attribute(obj, "fs")[8], get_seg_attribute(obj, "fs"), get_seg_valid(obj, "fs")))
    pr("%s   = 0x%04x, base = %s, limit = 0x%x, attr = 0x%x%s\n\n" % ("gs", reg(obj, "gs"), local_string(SIM_get_attribute(obj, "gs")[7],aa64), SIM_get_attribute(obj, "gs")[8], get_seg_attribute(obj, "gs"), get_seg_valid(obj, "gs")))
    pr("%s   = 0x%04x, base = %s, limit = 0x%x%s\n" % ("tr", reg(obj, "tr"), local_string(SIM_get_attribute(obj, "tr")[7],aa64), SIM_get_attribute(obj, "tr")[8], get_seg_valid(obj, "tr")))
    pr("%s = 0x%04x, base = %s, limit = 0x%x%s\n\n" % ("ldtr", reg(obj, "ldtr"), local_string(SIM_get_attribute(obj, "ldtr")[7],aa64), SIM_get_attribute(obj, "ldtr")[8], get_seg_valid(obj, "ldtr")))

    pr("idtr: base = %s, limit = %05x\n" % ( local_string(SIM_get_attribute(obj, "idtr_base"),aa64), SIM_get_attribute(obj, "idtr_limit")))
    pr("gdtr: base = %s, limit = %05x\n" % ( local_string(SIM_get_attribute(obj, "gdtr_base"),aa64), SIM_get_attribute(obj, "gdtr_limit")))

    try:
        efer = reg(obj, "efer")
        pr("\nefer = %d %d - %d -- %d = 0x%s\n" % (
            (efer  >> 11) & 1,
            (efer  >> 10) & 1,
            (efer >> 8) & 1,
            (efer) & 1,
            hex_str(efer,8)))
        pr("       N L   L    S\n")
        pr("       X M   M    C\n")
        pr("       E A   E    E\n")
    except:
        pass

    cr0 = reg(obj, "cr0")

    pr("\ncr0 = %d %d %d -- %d - %d -- %d %d %d %d %d %d = 0x%s\n" % (
       (cr0 >> 31) & 1, 
       (cr0 >> 30) & 1, 
       (cr0 >> 29) & 1, 
       (cr0 >> 18) & 1, 
       (cr0 >> 16) & 1, 
       (cr0 >> 5) & 1, 
       (cr0 >> 4) & 1, 
       (cr0 >> 3) & 1, 
       (cr0 >> 2) & 1, 
       (cr0 >> 1) & 1, 
       (cr0 >> 0) & 1,
       hex_str(cr0,8)))
    pr("      P C N    A   W    N E T E M P\n")
    pr("      G D W    M   P    E T S M P E\n\n")

    pr("cr2 = %s\n" % local_string(reg(obj, "cr2"),aa64))
    pr("cr3 = %s\n\n" % local_string(reg(obj, "cr3"),aa64))

    try:
        cr4 = reg(obj, "cr4")

        pr("cr4 = %d %d %d %d %d %d %d %d %d %d %d = 0x%s\n" % (
            (cr4 >> 10) & 1,
            (cr4 >> 9) & 1,
            (cr4 >> 8) & 1,
            (cr4 >> 7) & 1,
            (cr4 >> 6) & 1,
            (cr4 >> 5) & 1,
            (cr4 >> 4) & 1,
            (cr4 >> 3) & 1,
            (cr4 >> 2) & 1,
            (cr4 >> 1) & 1,
            (cr4 >> 0) & 1,
            hex_str(cr4,8)))
        
        pr("      O O P P M P P D T P V\n")
        pr("      S S C G C A S E S V M\n")
        pr("      X F E E E E E   D I E\n")
        pr("      M X\n")
        pr("      M S\n")
        pr("      E R\n")
        pr("      X\n")
        pr("      C\n")
        pr("      P\n")
        pr("      T\n\n")
    except:
        pass

    try:
        pr("dr0 = %s %s\n" % (local_string(reg(obj, "dr0"),aa64), debug_break_desc(obj, 0)))
        pr("dr1 = %s %s\n" % (local_string(reg(obj, "dr1"),aa64), debug_break_desc(obj, 1)))
        pr("dr2 = %s %s\n" % (local_string(reg(obj, "dr2"),aa64), debug_break_desc(obj, 2)))
        pr("dr3 = %s %s\n" % (local_string(reg(obj, "dr3"),aa64), debug_break_desc(obj, 3)))

        dr6 = reg(obj, "dr6")
        pr("\ndr6 = %d %d %d -- %d %d %d %d = 0x%s\n" % (
            (dr6 >> 15) & 1,
            (dr6 >> 14) & 1,
            (dr6 >> 13) & 1,
            (dr6 >> 3) & 1,
            (dr6 >> 2) & 1,
            (dr6 >> 1) & 1,
            (dr6 >> 0) & 1,
            hex_str(dr6, 4)))
        pr("      B B B    B B B B\n")
        pr("      T S D    3 2 1 0\n")

        pr("\ndr7 = %s\n\n" % hex_str(reg(obj, "dr7"), 8))
    except:
        pass

    try:
        reg(obj, "fpu_control")
        pregs_fpu_cmd(obj, 0, 0, 0, 0)
        pr("\n")
    except:
        pass

    try:
        reg(obj, "mxcsr")
        pregs_sse_cmd(obj, 0, 0, 0, 0, 0, 0)
    except:
        pass

def pregs_fpu_cmd(obj, f, x, i, b):
    fpu_regs = SIM_get_attribute(obj, "fpu_regs")
    fpu_status = SIM_get_attribute(obj, "fpu_status")
    fpu_control = SIM_get_attribute(obj, "fpu_control")
    if f + x + i + b == 0:
        x = 1
    if f + x + i + b > 1:
	print "Only one flag of -f, -x, -i, -b can be given to the command"
	return
    for fnum in range(8):
        pr("f%d (ST%d) = " % (fnum, (fnum - ((fpu_status >> 11) & 7)) & 7))
        byte_list_le = fpu_regs[fnum][1:]
        byte_list_le.reverse()
        int_val = 0L
        for byte in byte_list_le:
            int_val = (int_val << 8) | byte
        if x:
            pr("0x")
            for b in byte_list_le:
                pr("%02x" % b)
            if fpu_regs[fnum][0]:
                pr(" empty")
            else:
                pr(" valid")
        elif i:
            pr("%d" % int_val)
        elif f:
            pr(fp_to_string.fp_to_string("ed", int_val, 20))
        elif b:
            pr(fp_to_string.fp_to_binstring("ed", int_val))
        pr("\n")
    pr("\n")
    pr("fcw = %d %d %d -- %d %d %d %d %d %d = %s\n" % (
       (fpu_control >> 12) & 1,
       (fpu_control >> 10) & 3,
       (fpu_control >> 8) & 3,
       (fpu_control >> 5) & 1,
       (fpu_control >> 4) & 1,
       (fpu_control >> 3) & 1,
       (fpu_control >> 2) & 1,
       (fpu_control >> 1) & 1,
       (fpu_control >> 0) & 1,
       hex_str(fpu_control, 8)))
    pr("      X R P    P U O Z D I\n")
    pr("        C C    M M M M M M\n\n")

    pr("fsw = %d %d %d %d %d %d %d %d %d %d %d %d %d %d = %s\n" % (
       (fpu_status >> 15) & 1,
       (fpu_status >> 14) & 1,
       (fpu_status >> 11) & 7,
       (fpu_status >> 10) & 1,
       (fpu_status >> 9) & 1,
       (fpu_status >> 8) & 1,
       (fpu_status >> 7) & 1,
       (fpu_status >> 6) & 1,
       (fpu_status >> 5) & 1,
       (fpu_status >> 4) & 1,
       (fpu_status >> 3) & 1,
       (fpu_status >> 2) & 1,
       (fpu_status >> 1) & 1,
       (fpu_status >> 0) & 1,
       hex_str(fpu_status, 8)))
    pr("      B C T C C C E S P U O Z D I\n")
    pr("        3 O 2 1 0 S F E E E E E E\n")
    pr("          P\n\n")

    pr("ftw = %s\n" % hex_str(SIM_get_attribute(obj, "fpu_tag"), 8))

    aa64 = 0
    if SIM_class_has_attribute(obj.classname, "rax"):
        aa64 = 1
    else:
        aa64 = 0
    pr("\nLast operation:\n")
    pr("    Instruction  0x%04x:%s\n" % (obj.fpu_last_instr_selector0, local_string(obj.fpu_last_instr_pointer0, aa64)))
    pr("    Opcode       0x%x\n" % obj.fpu_last_opcode0)
    pr("    Operand      0x%04x:%s\n" % (obj.fpu_last_operand_selector0, local_string(obj.fpu_last_operand_pointer0, aa64)))

def current_x86_mode(obj):
	efer = 0
	try:
		efer = SIM_get_attribute(obj, "efer")
	except SimExc_General:
		pass
	cs = SIM_get_attribute(obj, "cs")
	cr0 = SIM_get_attribute(obj, "cr0")
	eflags = SIM_get_attribute(obj, "eflags")
	cr4 = SIM_get_attribute(obj, "cr4")

	mode = "unknown mode"
	if ((efer >> 10) & 1):
		if cs[10]:
			# EFER.LMA and CS.L
			mode = "64-bit mode"
		elif cs[1]:
			# EFER.LMA and !CS.L and CS.D_B
			mode = "32-bit compatibility mode"
		else:
			# EFER.LMA and !CS.L and !CS.D_B
			mode = "16-bit compatibility mode"
	elif (cr0 & 1):
		if (eflags >> 17) & 1:
			if cr4 & 1:
				# !EFER.LMA and CR0.PE and EFLAGS.VM and CR4.VME
				mode = "legacy ev86 mode"
			else:
				# !EFER.LMA and CR0.PE and EFLAGS.VM and !CR4.VME
				mode = "legacy v86 mode"
		elif cs[1]:
			# !EFER.LMA and CR0.PE and CS.D_B
			mode = "32-bit legacy protected mode"
		else:
			# !EFER.LMA and CR0.PE and !CS.D_B
			mode = "16-bit legacy protected mode"
	else:
		# !EFER.LMA and !CR0.PE
		if cs[1]:
			mode = "32-bit legacy real mode"
		else:
			mode = "16-bit legacy real mode"

        if SIM_class_has_attribute(obj.classname, "in_smm") and SIM_get_attribute(obj, "in_smm"):
            mode += " (system management mode)"
	return mode

def local_pregs(obj, a):
    aa64 = 0
    if SIM_class_has_attribute(obj.classname, "rax"):
        aa64 = 1
    else:
        aa64 = 0
    mode = current_x86_mode(obj)
    pr("%s\n" % mode)
    reg = local_read_int_register
    if aa64:
	pr("rax = 0x%016x             r8  = 0x%016x\n" % (reg(obj, "rax"),
                                                          reg(obj, "r8")))
	pr("rcx = 0x%016x             r9  = 0x%016x\n" % (reg(obj, "rcx"),
                                                          reg(obj, "r9")))
	pr("rdx = 0x%016x             r10 = 0x%016x\n" % (reg(obj, "rdx"),
                                                          reg(obj, "r10")))
	pr("rbx = 0x%016x             r11 = 0x%016x\n" % (reg(obj, "rbx"),
                                                          reg(obj, "r11")))
	pr("rsp = 0x%016x             r12 = 0x%016x\n" % (reg(obj, "rsp"),
                                                          reg(obj, "r12")))
	pr("rbp = 0x%016x             r13 = 0x%016x\n" % (reg(obj, "rbp"),
                                                          reg(obj, "r13")))
	pr("rsi = 0x%016x             r14 = 0x%016x\n" % (reg(obj, "rsi"),
                                                          reg(obj, "r14")))
	pr("rdi = 0x%016x             r15 = 0x%016x\n" % (reg(obj, "rdi"),
                                                          reg(obj, "r15")))
	pr("\n")
	cs = SIM_get_attribute(obj, "cs")
	pr("rip = 0x%016x, linear = 0x%016x\n" % (reg(obj, "rip"),
                                                  reg(obj, "rip")+cs[7]))
    else:
        pr("%s = 0x%s, %s = 0x%04x, %s = 0x%02x, %s = 0x%02x\n" % ("eax", hex_str(reg(obj, "eax"),8), "ax", reg(obj, "eax") & 0xffff, "ah", (reg(obj, "eax") >> 8) & 0xff, "al", reg(obj, "eax") & 0xff))
        pr("%s = 0x%s, %s = 0x%04x, %s = 0x%02x, %s = 0x%02x\n" % ("ecx", hex_str(reg(obj, "ecx"),8), "cx", reg(obj, "ecx") & 0xffff, "ch", (reg(obj, "ecx") >> 8) & 0xff, "cl", reg(obj, "ecx") & 0xff))
        pr("%s = 0x%s, %s = 0x%04x, %s = 0x%02x, %s = 0x%02x\n" % ("edx", hex_str(reg(obj, "edx"),8), "dx", reg(obj, "edx") & 0xffff, "dh", (reg(obj, "edx") >> 8) & 0xff, "dl", reg(obj, "edx") & 0xff))
        pr("%s = 0x%s, %s = 0x%04x, %s = 0x%02x, %s = 0x%02x\n" % ("ebx", hex_str(reg(obj, "ebx"),8), "bx", reg(obj, "ebx") & 0xffff, "bh", (reg(obj, "ebx") >> 8) & 0xff, "bl", reg(obj, "ebx") & 0xff))
        pr("%s = 0x%s, %s = 0x%04x\n" % ("esp", hex_str(reg(obj, "esp"),8), "sp", reg(obj, "esp") & 0xffff))
        pr("%s = 0x%s, %s = 0x%04x\n" % ("ebp", hex_str(reg(obj, "ebp"),8), "bp", reg(obj, "ebp") & 0xffff))
        pr("%s = 0x%s, %s = 0x%04x\n" % ("esi", hex_str(reg(obj, "esi"),8), "si", reg(obj, "esi") & 0xffff))
        pr("%s = 0x%s, %s = 0x%04x\n" % ("edi", hex_str(reg(obj, "edi"),8), "di", reg(obj, "edi") & 0xffff))   
        pr("\n")
        pr("eip = 0x%s, linear = 0x%s\n" % (hex_str(reg(obj, "eip"),8), hex_str(reg(obj, "eip") + SIM_get_attribute(obj, "cs")[7],8)))

    pr("\n")
    ef = reg(obj, "eflags")
    print_eflags(ef)
    if a:
	print_remaining_regs(obj, aa64)

def pregs_sse_cmd(obj, s, d, f, x, i, b):
    try:
        xmm_regs = obj.xmm
    except AttributeError, msg:
        print "Processor does not support SSE."
        return
    iter = 0
    if f + x + i + b == 0:
        x = 1
    if s + d == 0:
        d = 1
    if f + x + i + b > 1:
	print "Only one flag of -f, -x, -i, -b can be given to the command"
	return
    if s + d > 1:
	print "Only one flag of -s and -d can be given to the command"
	return
    for reg in xmm_regs:
        pr("xmm%2d = " % iter)
        if d:
            sub = (reg[1], reg[0])
        else:
            sub = ((reg[1] >> 32) & 0xffffffffL, reg[1] & 0xffffffffL, (reg[0] >> 32) & 0xffffffffL, reg[0] & 0xffffffffL)
        for r in sub:
            if f:
                if d:
                    pr(fp_to_string.fp_to_string_fixed("d", r, 15, 23) + " ")
                else:
                    pr(fp_to_string.fp_to_string_fixed("s", r, 8, 16) + " ")
            elif x:
                if d:
                    pr("%016x " % r)
                else:
                    pr("%08x " % r)
            elif i:
                if d:
                    pr("%20d " % r)
                else:
                    pr("%10d " % r)
            elif b:
                if d:
                    pr(fp_to_string.fp_to_binstring("d", r))
                else:
                    pr(fp_to_string.fp_to_binstring("s", r))
        pr("\n")
        iter = iter + 1
    mxcsr = obj.mxcsr
    pr("\nmxcsr = %d %d %d %d %d %d %d %d - %d %d %d %d %d %d = 0x%08x\n" % (
        (mxcsr >> 15) & 1,
        (mxcsr >> 13) & 3,
        (mxcsr >> 12) & 1,
        (mxcsr >> 11) & 1,
        (mxcsr >> 10) & 1,
        (mxcsr >> 9) & 1,
        (mxcsr >> 8) & 1,
        (mxcsr >> 7) & 1,
        (mxcsr >> 5) & 1,
        (mxcsr >> 4) & 1,
        (mxcsr >> 3) & 1,
        (mxcsr >> 2) & 1,
        (mxcsr >> 1) & 1,
        mxcsr & 1,
        mxcsr))
    pr("        F R P U O Z D I   P U O Z D I\n")
    pr("        Z C M M M M M M   E E E E E E\n")

new_command("pregs-sse", pregs_sse_cmd,
            [arg(flag_t, "-s"), arg(flag_t, "-d"), arg(flag_t, "-f"), arg(flag_t, "-x"), arg(flag_t, "-i"), arg(flag_t, "-b")],
            namespace = "x86",
            type  = "inspect/change commands",
            short = "print the sse registers",
            doc = """
Prints the contents of the SSE registers.<br/>
This command can take one subregister size flag and one formatting flag.<br/>
The subregister size is selected using the either the -s flag (32-bit), or the -d flag (64-bit).<br/>
The formatting flags -f, -x, and -i select the formatting of the output.
The -f flag prints the floating-point values of the registers as decimal numbers.
The -x flag prints the contents of the registers as hexadecimal integers.
The -i flag prints the contents of the registers as decimal integers.
With the -b flag, the registers are printed in binary floating point form.
""", filename="/mp/simics-3.0/src/core/x86/commands.py", linenumber="506")

new_command("pregs-fpu", pregs_fpu_cmd,
            [arg(flag_t, "-f"), arg(flag_t, "-x"), arg(flag_t, "-i"), arg(flag_t, "-b")],
            namespace = "x86",
            type  = "inspect/change commands",
            short = "print the x87 registers",
            doc = """
Prints the x87 floating-point registers.<br/>
This command takes one of the formatting flags -f, -x, or -i.<br/>
The -f flag prints the floating-point values of the registers.
The -x flag prints the contents of the registers as hexadecimal integers.
The -i flag prints the contents of the registers as decimal integers.
With the -b flag, the registers are printed in binary floating point form.
""", filename="/mp/simics-3.0/src/core/x86/commands.py", linenumber="522")



#
# Register pseudo attributes
#

def get_lower_32bits(reg, obj, idx):
        value = SIM_get_attribute(obj, reg)
        return value & 0xFFFFFFFFL

def set_lower_32bits(reg, obj, val, idx):
        if type(val) != type(1) and type(val) != type(1L):
                return Sim_Set_Need_Integer
        value = 0
        try:
                value = SIM_get_attribute(obj, reg)
        except SimExc_Attribute:
                return Sim_Set_Attribute_Not_Found
        value = value & 0xFFFFFFFF00000000L
        value = value | (val & 0xFFFFFFFFL)
        return SIM_set_attribute(obj, reg, value)

def get_lower_16bits(reg, obj, idx):
        value = SIM_get_attribute(obj, reg)
        return value & 0xFFFFL

def set_lower_16bits(reg, obj, val, idx):
        if type(val) != type(1) and type(val) != type(1L):
                return Sim_Set_Need_Integer
        value = 0
        try:
                value = SIM_get_attribute(obj, reg)
        except SimExc_Attribute:
                return Sim_Set_Attribute_Not_Found
        value = value & 0xFFFFFFFFFFFF0000L
        value = value | (val & 0xFFFFL)
        return SIM_set_attribute(obj, reg, value)

def get_lower_8bits(reg, obj, idx):
        value = SIM_get_attribute(obj, reg)
        return value & 0xFFL

def set_lower_8bits(reg, obj, val, idx):
        if type(val) != type(1) and type(val) != type(1L):
                return Sim_Set_Need_Integer
        value = 0
        try:
                value = SIM_get_attribute(obj, reg)
        except SimExc_Attribute:
                return Sim_Set_Attribute_Not_Found
        value = value & 0xFFFFFFFFFFFFFF00L
        value = value | (val & 0xFFL)
        return SIM_set_attribute(obj, reg, value)

def get_mid_8bits(reg, obj, idx):
        value = SIM_get_attribute(obj, reg)
        return (value >> 8) & 0xFFL

def set_mid_8bits(reg, obj, val, idx):
        if type(val) != type(1) and type(val) != type(1L):
                return Sim_Set_Need_Integer
        value = 0
        try:
                value = SIM_get_attribute(obj, reg)
        except SimExc_Attribute:
                return Sim_Set_Attribute_Not_Found
        value = value & 0xFFFFFFFFFFFF00FFL
        value = value | ((val & 0xFFL) << 8)
        return SIM_set_attribute(obj, reg, value)

def register_x86_pseudo_attributes(callback_data, obj):
	try:
		SIM_get_interface(obj, "x86")
	except SimExc_Lookup:
		return
	class_name = obj.classname
	if SIM_class_has_attribute(class_name, "ah"):
		return
	is_x86_64 = SIM_class_has_attribute(class_name, "rax")
	if is_x86_64:
		reg_l = "r"
	else:
		reg_l = "e"
	for reg in ("ax", "bx", "cx", "dx", "di", "si", "bp", "sp", "ip"):
		if is_x86_64:
	        	SIM_register_attribute(class_name, "e" + reg, get_lower_32bits, "r" + reg, set_lower_32bits, "r" + reg, 4, "Register e" + reg + " (lower 32 bits of " + reg_l + reg + ").")
		SIM_register_attribute(class_name, reg, get_lower_16bits, reg_l + reg, set_lower_16bits, reg_l + reg, 4, "Register " + reg + " (lower 16 bits of " + reg_l + reg + ").")

	for reg in ("a", "b", "c", "d"):
		SIM_register_attribute(class_name, reg + "l", get_lower_8bits, reg_l + reg + "x", set_lower_8bits, reg_l + reg + "x", 4, "Register " + reg + "l (lower 8 bits of " + reg_l + reg + "x).")
		SIM_register_attribute(class_name, reg + "h", get_mid_8bits, reg_l + reg + "x", set_mid_8bits, reg_l + reg + "x", 4, "Register " + reg + "h (bits 8-15 from " + reg_l + reg + "x).")
	if is_x86_64:
		for reg in ("di", "si", "bp", "sp"):
			SIM_register_attribute(class_name, reg + "l", get_lower_8bits, "r" + reg, set_lower_8bits, "r" + reg, 4, "Register " + reg + "l (lower 8 bits of " + reg_l + reg + ").")
		for reg in ("r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"):
			SIM_register_attribute(class_name, reg + "d", get_lower_32bits, reg, set_lower_32bits, reg, 4, "Register " + reg + "d (lower 32 bits of " + reg + ").")
			SIM_register_attribute(class_name, reg + "w", get_lower_16bits, reg, set_lower_16bits, reg, 4, "Register " + reg + "w (lower 16 bits of " + reg + ").")
			SIM_register_attribute(class_name, reg + "b", get_lower_8bits, reg, set_lower_8bits, reg, 4, "Register " + reg + "b (lower 8 bits of " + reg + ").")

# Register the register pseudo-attributes handler
SIM_hap_add_callback("Core_Conf_Object_Create", register_x86_pseudo_attributes, 0)


def print_instruction_queue(verbose):
    cpu = current_processor();
    ifc = SIM_get_interface(cpu, "processor")
    ifc.print_instruction_queue(cpu, verbose)

if (VT_get_current_loading_module()[-3:] == "-ma"):
    new_command("print-instruction-queue", print_instruction_queue,
            [arg(flag_t, "-v")],
            type  = "inspect/change commands",
            short = "print instruction queue",
            alias = "piq",
            doc = """
            
Prints the instruction queue (tree) for current processor. The
instructions are numbered from 0 and up, where 0 is the root of the
tree. If an instruction have an alternative execution path all
instructions in the second path will be indented a few spaces. The
first instructions in both paths will have the same number, i.e. the
numbering corresponds to the depth in the tree.

After the number the virtual address of the instruction is printed
followed by the disassembly string and the phase of the
instruction. 'I' means initiated, 'F' fetched, 'D' decoded, 'E'
executed. The built in mode will only display 'D' and 'E' since
instructions are initiated, fetched and decoded direcly. If an
instruction is stalling on a memory request the memory transaction id
is printed together with the stalling physical address. CC blocked is
printed if the Consistency Controller (previously Store Buffer) has
blocked the transaction according to its rules.

S is printed in the Micro Architectural Interface mode if the
instruction is speculative.

If the -v flag is used all register values used by the instruction is
printed, both input and output values.""", filename="/mp/simics-3.0/src/core/x86/commands.py", linenumber="645")

import re
from string import atoi

def msrs_cmd(obj):
    try:
        msr_list = obj.msr_list
        if not msr_list:
            return
    except:
        return
    print_list = []
    for m in msr_list:
        (no, name, desc, value, pc, hvr, hvw, shared, rnop, wnop, alias,
         pseudo, noattr) = m
        print_list.append([name, "0x%x"%no, "0x%x"%value,
                           iff(shared, "shared", "")])
    print_columns([Just_Left, Just_Right, Just_Right, Just_Right],
                  [[ "MSR Name", "Index", "Value", "" ]] + print_list)

new_command("msrs", msrs_cmd,
            [],
            namespace = "x86",
            type = "inspect/change commands",
            short = "print MSRs",
            doc = """
Print model specific registers. MSRs not included in the output
are either not supported, not implemented, read-only, or must
be accessed through other attributes.
""", filename="/mp/simics-3.0/src/core/x86/commands.py", linenumber="694")

def descriptor_description(idt, low_word, high_word, long_mode=0, low_word_2=0, high_word_2=0):
	if high_word & (1 << 15):
                if idt and long_mode:
                        sel = (low_word >> 16) & 0xffff
                        offs = (low_word & 0xffff) | (high_word & 0xffff0000) | (low_word_2 << 32)
                        if ((high_word >> 8) & 0x1f) == 0xe:
                                return ("64-bit interrupt gate", sel, offs)
                        elif ((high_word >> 8) & 0x1f) == 0xf:
                                return ("64-bit trap gate", sel, offs)
                elif idt:
			if high_word & (1 << 11):
				bit = "32-bit"
			else:
				bit = "16-bit"
                        sel = (low_word >> 16) & 0xffff
                        offs = (low_word & 0xffff) | (high_word & 0xffff0000)
                        if ((high_word >> 8) & 7) == 5:
                                return ("task gate", sel, 0)
                        elif ((high_word >> 8) & 7) == 6:
                                return (bit + " interrupt gate", sel, offs)
                        elif ((high_word >> 8) & 7) == 7:
                                return (bit + " trap gate", sel, offs)
                        else:
                                return None
		elif high_word & (1 << 12):
                    
			if high_word & (1 << 22):
				bit = "32-bit"
			elif (high_word & (1 << 21)) and (high_word & (1 << 11)) and long_mode:
                                bit = "64-bit"
                        else:
				bit = "16-bit"
			base = ((low_word >> 16) & 0xffff) | ((high_word & 0xff) << 16) | (high_word & 0xff000000)
			limit = (low_word & 0xffff) | (high_word & 0xf0000)
			if (high_word >> 23) & 1:
				limit = limit * 4 * 1024 + 4 * 1024 - 1
			# Code/data
			type = ("read-only", "read-only (a)", "read/write", "read/write (a)", "expand down, read-only", "expand down, read-only (a)", "expand-down, read/write", "expand down, read/write (a)", "execute-only", "execute-only (a)", "execute/read", "execute/read (a)", "conforming, execute-only", "conforming, execute-only (a)", "conforming, execute/read", "conforming, execute/read (a)")[(high_word >> 8) & 0xf]
			return ("%s %s" % (bit, type), base, limit)
		else:
			# System
                        if long_mode and ((high_word >> 8) & 0xf) != 2 and ((high_word_2 >> 8) & 0x1f) != 0:
                                return None
			base = ((low_word >> 16) & 0xffff) | ((high_word & 0xff) << 16) | (high_word & 0xff000000)
                        if long_mode:
                                base = base | (low_word_2 << 32)
			limit = (low_word & 0xffff) | (high_word & 0xf0000)
                        if long_mode:
                                type = ("reserved", "reserved", "LDT", "reserved", "reserved", "reserved", "reserved", "reserved", "reserved", "64-bit tss (avail)", "reserved", "64-bit tss (busy)", "64-bit call gate", "reserved", "64-bit interrupt gate", "64-bit trap gate")[(high_word >> 8) & 0xf]
                        else:
                                type = ("reserved", "16-bit tss (avail)", "LDT", "16-bit tss (busy)", "16-bit call gate", "task gate", "16-bit interrupt gate", "16-bit trap gate", "reserved", "32-bit tss (avail)", "reserved", "32-bit tss (busy)", "32-bit call gate", "reserved", "32-bit interrupt gate", "32-bit trap gate")[(high_word >> 8) & 0xf]
			return (type, base, limit)
	else:
		return None

def cpu_long_mode(obj):
	efer = 0
	try:
		efer = obj.efer
	except AttributeError:
		pass
        return ((efer >> 10) & 1)

def word_from_bytes(bytes, index):
        return bytes[index] | (bytes[index+1] << 8) | (bytes[index+2] << 16) | (bytes[index+3] << 24)

def idt_cmd(obj):
        print "Processor %s IDT (%s)" % (obj.name, current_x86_mode(obj))
        if obj.cr0 & 1:
                table_base = obj.idtr_base
                table_limit = obj.idtr_limit
                in_long_mode = cpu_long_mode(obj)
                if in_long_mode:
                        descriptor_size = 16
                else:
                        descriptor_size = 8
                if table_limit >= 256 * descriptor_size:
                        table_limit = 256 * descriptor_size - 1
                num_bytes = 0
                bytes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                descs = []
                for i in range(table_limit + 1):
                        phys_addr = obj.iface.x86.linear_to_physical(obj, Sim_DI_Data, table_base + i)
                        bytes[num_bytes] = SIM_read_phys_memory(obj, phys_addr, 1)
                        num_bytes = num_bytes + 1
                        if num_bytes == descriptor_size:
                                low_word = word_from_bytes(bytes, 0)
                                high_word = word_from_bytes(bytes, 4)
                                upper_low_word = word_from_bytes(bytes, 8)
                                upper_high_word = word_from_bytes(bytes, 12)
                                desc = descriptor_description(1, low_word, high_word, in_long_mode, upper_low_word, upper_high_word)
                                if desc != None:
                                        descs.append([i / descriptor_size, desc[0], "%x" % desc[1], "%x" % desc[2]])
                                num_bytes = 0
                print_columns([Just_Left, Just_Left, Just_Left, Just_Left],
                              [ [ "Vector", "Type", "Segment", "Offset" ] ] + descs)
        else:
                descs = []
                for i in range(256):
                        offset = SIM_read_phys_memory(obj, obj.idtr_base + i * 4, 2)
                        selector = SIM_read_phys_memory(obj, obj.idtr_base + i * 4 + 2, 2)
                        descs.append([i, "%04x" % selector, "%04x" % offset])
                print_columns([Just_Left, Just_Left, Just_Left],
                              [ [ "Vector", "Segment", "Offset" ] ] + descs)

new_command("print-idt", idt_cmd,
            [],
            namespace = "x86",
            type = "inspect/change commands",
            short = "print IDT",
            doc = """
Print all descriptors in the Interrupt Descriptor Table (IDT).
""", filename="/mp/simics-3.0/src/core/x86/commands.py", linenumber="810")

def gdt_cmd(obj):
        if obj.cr0 & 1:
                print "Processor %s GDT (%s)" % (obj.name, current_x86_mode(obj))
                table_base = obj.gdtr_base
                table_limit = obj.gdtr_limit
                num_bytes = 0
                bytes = [0, 0, 0, 0, 0, 0, 0, 0]
                prev_bytes = [1, 1, 1, 1, 1, 1, 1, 1]
                descs = []
                descriptor_failed = 0
                in_long_mode = cpu_long_mode(obj)
                last_selector = -1
                for i in range(table_limit+1):
                        try:
                            phys_addr = obj.iface.x86.linear_to_physical(obj, Sim_DI_Data, table_base + i)
                        except sim_core.SimExc_Memory:
                            descriptor_failed = 1
                        if not descriptor_failed:
                            bytes[num_bytes] = SIM_read_phys_memory(obj, phys_addr, 1)
                        num_bytes = num_bytes + 1
                        if num_bytes == 8:
                                if not descriptor_failed:
                                    low_word = word_from_bytes(bytes, 0)
                                    high_word = word_from_bytes(bytes, 4)
                                    desc = descriptor_description(0, low_word, high_word, in_long_mode, 0xffffffff, 0xffffffff)
                                    if desc != None:
                                        last_selector = i - 7
                                        descs.append(["%04x" % last_selector, desc[0], "%x" % desc[1], "%x" % desc[2]])
                                    elif in_long_mode:
                                        low_2 = word_from_bytes(prev_bytes, 0)
                                        high_2 = word_from_bytes(prev_bytes, 4)
                                        desc = descriptor_description(0, low_2, high_2, in_long_mode, low_word, high_word)
                                        if desc != None and last_selector != (i - 15):
                                            last_selector = i - 15
                                            descs.append(["%04x" % (i - 15), desc[0], "%x" % desc[1], "%x" % desc[2]])
                                num_bytes = 0
                                descriptor_failed = 0
                                prev_bytes = bytes[:]
                print_columns([Just_Left, Just_Left, Just_Left, Just_Left],
                              [ [ "Selector", "Type", "Base", "Limit" ] ] + descs)
        else:
                print "Processor %s is in %s, GDT not available" % (obj.name, current_x86_mode(obj))

new_command("print-gdt", gdt_cmd,
            [],
            namespace = "x86",
            type = "inspect/change commands",
            short = "print GDT",
            doc = """
Print all descriptors in the Global Descriptor Table (GDT). Only usable in protected mode.
""", filename="/mp/simics-3.0/src/core/x86/commands.py", linenumber="862")

def mtrr_type_name(encoding):
	if encoding == 0:
		return "uncacheable"
	elif encoding == 1:
		return "write-combining"
	elif encoding == 4:
		return "write-through"
	elif encoding == 5:
		return "write-protect"
	elif encoding == 6:
		return "write-back"
	else:
		return "unknown (0x%x)" % encoding

def memory_config_cmd(obj):
	if (SIM_class_has_attribute(obj.classname, "syscfg")):
		print "SYSCFG register"
		print "\tTop of memory 2 register: %s" % iff(obj.syscfg & (1 << 21), "enabled", "disabled")
		print "\tTop of memory and I/O range registers: %s" % iff(obj.syscfg & (1 << 20), "enabled", "disabled")
		print "\tRdDram and WrDram modification: %s" % iff(obj.syscfg & (1 << 19), "enabled", "disabled")
		print "\tRdDram and WrDram attributes: %s" % iff(obj.syscfg & (1 << 18), "enabled", "disabled")
	if (SIM_class_has_attribute(obj.classname, "hwcr")):
		print "HWCR register"
		print "\t32-bit address wrap: %s" % iff(obj.hwcr & (1 << 17), "disabled", "enabled")
	if (SIM_class_has_attribute(obj.classname, "top_mem")):
		print "TOP_MEM register"
		print "\tTop of memory: 0x%x (%d Mb)" % (obj.top_mem, obj.top_mem / (1024 * 1024))
	if (SIM_class_has_attribute(obj.classname, "top_mem2")):
		print "TOP_MEM2 register"
		print "\tTop of memory 2: 0x%x (%d Mb)" % (obj.top_mem2, obj.top_mem2 / (1024 * 1024))
	if (SIM_class_has_attribute(obj.classname, "iorr_base0")):
		for i in range(2):
			valid = (obj.iorr_mask0 >> 11) & 1
			if valid:
				print "IORR%d valid" % i
				print "\tBase: 0x%x" % (SIM_get_attribute(obj, "iorr_base%d" % i) & 0xfffffffffffff000L)
				print "\tMask: 0x%x" % (SIM_get_attribute(obj, "iorr_mask%d" % i) & 0xfffffffffffff000L)
				print "\tRead from: %s" % iff(SIM_get_attribute(obj, "iorr_base%d" % i) & (1 << 4), "DRAM", "I/O")
				print "\tWrite to: %s" % iff(SIM_get_attribute(obj, "iorr_base%d" % i) & (1 << 3), "DRAM", "I/O")
			else:
				print "IORR%d invalid" % i
	if (SIM_class_has_attribute(obj.classname, "mtrr_def_type")):
		print "MTRRdefType register"
		print "\tMTRRs: %s" % iff(obj.mtrr_def_type & (1 << 11), "enabled", "disabled")
		print "\tFixed range MTRRs: %s" % iff(obj.mtrr_def_type & (1 << 10), "enabled", "disabled")
		print "\tDefault memory type: %s" % mtrr_type_name(obj.mtrr_def_type & 0xff)
	if (SIM_class_has_attribute(obj.classname, "mtrr_base0")):
		for i in range(8):
			valid = (SIM_get_attribute(obj, "mtrr_mask%d" % i) >> 11) & 1
			if valid:
				print "MTRR%d valid" % i
				print "\tBase: 0x%x" % (SIM_get_attribute(obj, "mtrr_base%d" % i) & 0xfffffffffffff000L)
				print "\tMask: 0x%x" % (SIM_get_attribute(obj, "mtrr_mask%d" % i) & 0xfffffffffffff000L)
				print "\tType: %s" % mtrr_type_name(SIM_get_attribute(obj, "mtrr_base%d" % i) & 0xff)
			else:
				print "MTRR%d invalid" % i
	if (SIM_class_has_attribute(obj.classname, "mtrr_fix_64k_00000")):
		print "Fixed MTRRs"
		for (sub_len, base) in ((64, 0x00000), (16, 0x80000), (16, 0xa0000), (4, 0xc0000), (4, 0xc8000), (4, 0xd0000), (4, 0xd8000), (4, 0xe0000), (4, 0xe8000), (4, 0xf0000), (4, 0xf8000)):
			mtrr_val = SIM_get_attribute(obj, "mtrr_fix_%dk_%05x" % (sub_len, base))
			for i in range(8):
				sub_field = (mtrr_val >> (i * 8)) & 0xff
				if (SIM_class_has_attribute(obj.classname, "syscfg")):
					print "\t0x%08x - 0x%08x %s read: %s write: %s" % (base + i * sub_len * 1024, base + (i + 1) * sub_len * 1024 - 1, mtrr_type_name(sub_field & 7), iff((sub_field & (1 << 4)) and (obj.syscfg & (1 << 18)), "memory", "I/O"), iff((sub_field & (1 << 3)) and (obj.syscfg & (1 << 18)), "memory", "I/O"))
				else:
					print "\t0x%08x - 0x%08x %s" % (base + i * sub_len * 1024, base + (i + 1) * sub_len * 1024 - 1, mtrr_type_name(sub_field))
	if (SIM_class_has_attribute(obj.classname, "smm_mask")):
		if obj.smm_mask & 1:
			print "SMM ASeg enabled"
			print "\tType: %s" % mtrr_type_name((obj.smm_mask >> 8) & 7)
		else:
			print "SMM ASeg disabled"
		if obj.smm_mask & 2:
			print "SMM TSeg enabled"
			print "\tType: %s" % mtrr_type_name((obj.smm_mask >> 12) & 7)
			print "\tBase: 0x%x" % obj.smm_base
			print "\tMask: 0x%x" % obj.smm_mask
		else:
			print "SMM TSeg disabled"
		

        pass

new_command("memory-configuration", memory_config_cmd,
            [],
            namespace = "x86",
            type = "inspect/change commands",
            short = "print memory configuration",
            doc = """
Print the processors memory configuration. Depending on the processor type, this may
include MTRR information, HyperTransport routing information, DRAM configuration,
and other memory configuration related information.
""", filename="/mp/simics-3.0/src/core/x86/commands.py", linenumber="954")

def x86_diff_regs(obj):
    if SIM_class_has_attribute(obj.classname, "rax"):
        aa64 = 1
    else:
        aa64 = 0
    if aa64:
        return ("rax", "rbx", "rcx", "rdx",
                "rsp", "rbp", "rsi", "rdi",
                "r8", "r9", "r10", "r11",
                "r12", "r13", "r14", "r15",
                "eflags",
                "cr0", "cr2", "cr3", "cr4",
                "cs", "cs_attr", "cs_base", "cs_limit",
                "ds", "ds_attr", "ds_base", "ds_limit",
                "ss", "ss_attr", "ss_base", "ss_limit",
                "es", "es_attr", "es_base", "es_limit",
                "fs", "fs_attr", "fs_base", "fs_limit",
                "gs", "gs_attr", "gs_base", "gs_limit")
    else:
        return ("eax", "ebx", "ecx", "edx",
                "esp", "ebp", "esi", "edi",
                "eflags",
                "cr0", "cr2", "cr3", "cr4",
                "cs", "cs_attr", "cs_base", "cs_limit",
                "ds", "ds_attr", "ds_base", "ds_limit",
                "ss", "ss_attr", "ss_base", "ss_limit",
                "es", "es_attr", "es_base", "es_limit",
                "fs", "fs_attr", "fs_base", "fs_limit",
                "gs", "gs_attr", "gs_base", "gs_limit")

def x86_get_info(obj):
    additional = [("Port space", obj.port_space)]
    if SIM_class_has_attribute(obj.classname, "physical_dram"):
        additional += [("DRAM space", obj.physical_dram)]
    return [ (None,
              sim_commands.common_processor_get_info(obj) + additional) ]

funcs = { 'print_disassemble_line':
          local_print_disassemble_line,
          'pregs':
          local_pregs,
          'translate_to_physical':
          local_translate_to_physical,
          'get_address_prefix':
          local_get_address_prefix,
          'diff_regs':
          x86_diff_regs,
          'get_pending_exception_string':
          local_pending_exception,
          'get_info':
          x86_get_info}
