from cli import *
import sim_commands

class cpuregs:
        def __init__(self, cpu):
                self.cpu = cpu
                
        def __getitem__(self, reg):
                regno = SIM_get_register_number(self.cpu, reg)
                return SIM_read_register(self.cpu, regno)


def short_name(name):
        if len(name) > 3 and name[2] == '.':
                return name[3:]
        return name


def local_diff_regs(obj):
	all = SIM_get_all_registers(obj)
	return map(lambda x: SIM_get_register_name(obj, x), all)

#
# -------------------- pregs --------------------
#

def local_pregs(cpu, all):
        regs = cpuregs(cpu)
        r_gr0  = SIM_get_register_number(cpu, 'r0')
        r_nat0 = SIM_get_register_number(cpu, 'r0.nat')
        r_pr0  = SIM_get_register_number(cpu, 'p0')
        r_ar0  = SIM_get_register_number(cpu, 'ar0')
        r_cr0  = SIM_get_register_number(cpu, 'cr0')

        ar_names = [ short_name(SIM_get_register_name(cpu, ar))
                     for ar in range(r_ar0, r_ar0+127) ]
        cr_names = [ short_name(SIM_get_register_name(cpu, cr))
                     for cr in range(r_cr0, r_cr0+127) ]

        sof  = regs['cfm.sof']
        sol  = regs['cfm.sol']
        sor  = regs['cfm.sor']
        ip   = regs['ip']
        slot = regs['slot']
        psr  = regs['psr']

        bank = (psr >> 44) & 1

        # Make pr string
        pr_str = ""
        for i in range(0, 64):
                if SIM_read_register(cpu, r_pr0+i):
                        pr_str += "1"
                else:
                        pr_str += "0"

        pr( 'pc   = [ip:%016x slot:%d]\n' % (ip, slot) )
        pr( 'pr   = [%s]\n' % pr_str )
        pr( 'GR bank = %d\n' % bank )

        for i in range(0, 128):
                output = 0
                line = ""
                if i < 32 + sof:
                        name = SIM_get_register_name(cpu, r_gr0 + i)
                        nat = SIM_read_register(cpu, r_nat0 + i)
                        #if nat:  value = "----------------"
			if nat:  natc = "*"
                        else:    natc = " "

                        value = "%016x" % SIM_read_register(cpu, r_gr0 + i)

                        if i >= 32 and i < 32+sor:   local = "R"
                        elif i >= 32 and i < 32+sol: local = "L"
                        else:                        local = " "


                        line += '%-4s =%s[%s]%s  ' % (name, natc, value, local)
                        output = 1
                else:
                        line += '                            '

                if i < 45:
                        name = ar_names[i]
                        line += "%-8s = [%016x] " % (name, SIM_read_register(cpu, r_ar0 + i))
                        output = 1

                if 45 <= i < 48:
                        name = ar_names[i + 19]
                        line += "%-8s = [%016x] " % (name,
                                                      SIM_read_register(cpu, r_ar0 + i + 19))
                        output = 1
                        
                if i < 26:
                        name = cr_names[i]
                        line += "%-4s = [%016x]" % (name, SIM_read_register(cpu, r_cr0 + i))
                        output = 1
                        
                if 26 <= i < 44:
                        name = cr_names[i + 38]
                        line += "%-4s = [%016x]" % (name, SIM_read_register(cpu, r_cr0+i+38))
                        output = 1
                        
                if output:
                        pr( line + '\n' )


#
# -------------------- print disassemble line --------------------
#

def ia64_instr_len(address):
	slot = address & 0xf
	address = address - slot
	if slot < 2:
		return 1
	else:
		return 16 - slot
def ia64_disasm(cpu, address, type):
	length, asm = SIM_disassemble(cpu, address, type)
	return (ia64_instr_len(address), asm)
def ia64_print_opcode(cpu, paddr, length):
	slot = paddr & 0xf
	paddr -= slot
	b = []
 	if sim_commands.disassembly_settings["partial-opcode"]:
		if slot == 2:
			length = 4
		else:
			length = 6
		clength = 6
		start = paddr + 6*slot
	else:
		length = 16
		clength = length
		start = paddr
	try:
		for i in range(length):
			b.append("%02x" % SIM_read_phys_memory(cpu, start + i, 1))
	except:
		pass
	pr("%-*s" % (3*clength - 1, " ".join(b)))
local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun(
	default_instr_len = ia64_instr_len, disasm = ia64_disasm,
	print_opcode = ia64_print_opcode)

#
# -------------------- RSE status --------------------
#

def rse_status_cmd(cpu):
        if not cpu:
                cpu, _ = get_cpu(kind = ("ia64", "an IA-64 processor"))
        regs = cpuregs(cpu)
        rsc = regs["ar.rsc"]
        if rsc & 3 == 0: mode = "enforced lazy"
        elif rsc & 3 == 1: mode = "store intensive"
        elif rsc & 3 == 2: mode = "load intensive"
        elif rsc & 3 == 3: mode = "eager"

        pfm = regs["ar.pfs"] & 0x1fffffffffL
        pfm_sof = pfm & 0x7f
        pfm_sol = pfm>>7 & 0x7f
        pfm_sor = pfm>>14 & 0xf

        title = "RSE status for %s" % cpu.name
        info = [ (None,
                  [ ("RSE mode", mode),
                    ("Number of physical registers",     str(regs["rse.n_stacked_phys"])),
                    ("Number of dirty register",         str(regs["rse.ndirty"])),
                    ("Number of dirty words",            str(regs["rse.ndirty_words"])),
                    ("Physical register number of r32",  str(regs["rse.bof"])),
                    ("Next stored physical register",    str(regs["rse.storereg"])),
                    ("Last loaded physical register",    str(regs["rse.loadreg"])),
                    ("Backing store load pointer", "%016x" % regs["rse.bspload"]),
                    ("Backing store store pointer","%016x" % regs["ar.bspstore"]),
                    ("Backing store r32 pointer",  "%016x" % regs["ar.bsp"]),
                    ("RNAT bit index",                   str(regs["rse.rnatbitindex"])),
                    ("Current FrameLoad Enable",         str(regs["rse.cfle"])) ]),
                 ("Current Frame",
                  [ ("Frame Size", str(regs["cfm.sof"])),
                    ("local / output / rotating", "%d / %d / %d" % (regs["cfm.sol"],
                                                                    regs["cfm.sof"] - regs["cfm.sol"],
                                                                    regs["cfm.sor"])),
                    ("Rotation base for GR / FR / PR", "%d / %d / %d" % (regs["cfm.rrb.gr"],
                                                                         regs["cfm.rrb.fr"],
                                                                         regs["cfm.rrb.pr"])) ]),
                    
                 ("Parent Frame",
                  [ ("Frame Size", str(pfm_sof)),
                    ("local / output / rotating", "%d / %d / %d" % (pfm_sol,
                                                                    pfm_sof - pfm_sol,
                                                                    pfm_sor)) ]) ]

        ifs = regs["cr.ifs"]
        ifs_v = ifs>>63
        if ifs_v:
                ifs_sof = ifs & 0x7f
                ifs_sol = ifs>>7 & 0x7f
                ifs_sor = ifs>>14 & 0xf
                info.append( ("Interrupted Parent",
                              [ ("Frame Size", str(ifs_sof)),
                                ("local / output / rotating", "%d / %d / %d" % (ifs_sol,
                                                                                ifs_sof - ifs_sol,
                                                                                ifs_sor)) ]) )

	print title
        print_info(info, key_width = 32)


new_command("rse-status", rse_status_cmd,
            [arg(obj_t("IA64 processor", "ia64"), "cpu-name", "?")],
            type  = "general commands",
            short = "display RSE status",
            namespace_copy = ("ia64", rse_status_cmd),
            doc = """
Displays the current status of the Register Stack Engine and its backing store.""", filename="/mp/simics-3.0/src/core/ia64/commands.py", linenumber="211")

#
# -------------------- unwind --------------------
#

# This command is not useful enough

# def print_frame(loc, out):
#         i = 0
#         for val, nat in loc:
#                 name = "loc%d" % i
#                 if val == None:
#                         val_str = "????????????????"
#                 else:
#                         val_str = "%016x" % val
#                 if nat:  natc = "*"
#                 else:    natc = " "
#                 pr('  %-6s =%s[%s]\n' % (name, natc, val_str))
#                 i += 1
#         i = 0
#         for val, nat in out:
#                 name = "out%d" % i
#                 val_str = "%016x" % val
#                 if nat:  natc = "*"
#                 else:    natc = " "
#                 pr('  %-6s =%s[%s]\n' % (name, natc, val_str))
#                 i += 1

# def obj_unwind(cpu, frame):
#         pr( 'Frame %d:\n' % frame )
#         sof = SIM_read_register(cpu, r_sof)
#         sol = SIM_read_register(cpu, r_sol)
#         if frame == 0:
#                 print_frame([ (SIM_read_register(cpu, r_gr0 + i),
#                                SIM_read_register(cpu, r_nat0 + i))
#                               for i in xrange(32, 32 + sol) ],
#                             [ (SIM_read_register(cpu, r_gr0 + i),
#                                SIM_read_register(cpu, r_nat0 + i))
#                               for i in xrange(32 + sol, 32 + sof) ])
#         elif frame == 1:
#                 regs = cpuregs(cpu)
#                 pgr = cpu.pgr
#                 pfm = regs["ar.pfs"] & 0x1fffffffffL
#                 pfm_sof = pfm & 0x7f
#                 pfm_sol = pfm>>7 & 0x7f
#                 pfm_sor = pfm>>14 & 0xf

#                 unknowns = pfm_sol - len(pgr)
#                 if unknowns < 0: unknowns = 0
                
#                 print_frame([ (None, None)
#                               for i in xrange(0, unknowns) ]
#                             + pgr[-pfm_sol + unknowns:],
#                             [ (SIM_read_register(cpu, r_gr0 + i),
#                                SIM_read_register(cpu, r_nat0 + i))
#                               for i in xrange(32, 32 + pfm_sof - pfm_sol) ])
#         else:
#                 pr( '??\n' )

# def unwind_command(cpu_name, frame):
#         cpu, name = get_cpu(cpu_name)
#         obj_unwind(cpu, frame)

# new_command("unwind", unwind_command,
#             [arg(obj_t("ia64 processor object", "ia64"), "cpu-name", "?"),
#              arg(int_t, "frame", "?", 0)],
#             type  = "inspect/change commands",
#             short = "print stacked register frame",
#             namespace_copy = ("ia64", obj_unwind),
#             doc = """
# Print the input/local and output registers in a register stack frame.  Frame 0 means the current frame.""")

#
# -------------------- Interrupt status --------------------
#

def obj_int_status_cmd(cpu):
        regs = cpuregs(cpu)
        psr = regs["psr"]
        irr0 = regs["cr.irr0"]
        irr1 = regs["cr.irr1"]
        irr2 = regs["cr.irr2"]
        irr3 = regs["cr.irr3"]

        in_service = cpu.in_service
        if len(in_service):
                in_service_s = ""
                for vector in in_service:
                        if vector == 2:   in_service_s += " NMI"
                        elif vector == 0: in_service_s += " ExtINT"
                        else:             in_service_s += " %d" % vector
        else:
                in_service_s = "none"

        pending = ""
        if irr0 & 1: pending += " NMI"
        if irr0 & 4: pending += " ExtINT"
        for b in range(16,64):
                if irr0 & (1L << b): pending += " %d" % b
        for b in range(0,64):
                if irr1 & (1L << b): pending += " %d" % (b + 64)
        for b in range(0,64):
                if irr2 & (1L << b): pending += " %d" % (b + 128)
        for b in range(0,64):
                if irr3 & (1L << b): pending += " %d" % (b + 192)
        if pending == "":
                pending = "none"

        title = "Interrupt status for %s" % cpu.name
        info = [ (None,
                  [ ("Interrupt Collection", iff(psr & 0x0000000000002000L, "Enabled", "Disabled")),
                    ("Interrupt Activation", iff(psr & 0x0000000000004000L, "Enabled", "Disabled")),
                    ("In-service", in_service_s),
                    ("Pending", pending) ]) ]
	print title
        print_info(info)



def int_status_cmd(cpu):
    if not cpu:
        cpu,_ = get_cpu(kind = ("ia64", "an IA-64 processor"))
    obj_int_status_cmd(cpu)

new_command("interrupt-status", int_status_cmd,
            [arg(obj_t("ia64 processor object", "ia64"), "cpu-name", "?")],
            type  = "general commands",
            short = "display interrupt status",
            namespace_copy = ("ia64", obj_int_status_cmd),
            doc = """
Displays the current status of pending external interrupts.""", filename="/mp/simics-3.0/src/core/ia64/commands.py", linenumber="342")

#
# -------------------- TLB status --------------------
#

def obj_tlb_status_cmd(cpu):
        dtlb = cpu.dtlb
        itlb = cpu.itlb

        print "Data TLB"
        pr('---p-ma-a-d-pl-ar--------------ppn-ed-ps------key--------------vpn------rid\n')

        label = 'TR'
        for e in dtlb[0]:
                if e[0]:
                        pr('%s %d %2d %d %d %2d %2d %16x %2d %02x %8x %16x %8x\n' %
                           (label, e[3], e[4], e[5], e[6], e[7], e[8],
                            e[9], e[10], e[11], e[12], e[13], e[14]))
                label = '  '
                        

        label = 'TC'
        for e in dtlb[1]:
                if e[0]:
                        pr('%s %d %2d %d %d %2d %2d %16x %2d %02x %8x %16x %8x\n' %
                           (label, e[3], e[4], e[5], e[6], e[7], e[8],
                            e[9], e[10], e[11], e[12], e[13], e[14]))
                label = '  '
        pr('------------------------------------------------------------------\n')
        
        print
        print "Instruction TLB"
        pr('---p-ma-a-d-pl-ar--------------ppn-ed-ps------key--------------vpn------rid\n')

        label = 'TR'
        for e in itlb[0]:
                if e[0]:
                        pr('%s %d %2d %d %d %2d %2d %16x %2d %02x %8x %16x %8x\n' %
                           (label, e[3], e[4], e[5], e[6], e[7], e[8],
                            e[9], e[10], e[11], e[12], e[13], e[14]))
                        label = '  '
                        

        label = 'TC'
        for e in itlb[1]:
                if e[0]:
                        pr('%s %d %2d %d %d %2d %2d %16x %2d %02x %8x %16x %8x\n' %
                           (label, e[3], e[4], e[5], e[6], e[7], e[8],
                            e[9], e[10], e[11], e[12], e[13], e[14]))
                        label = '  '
        pr('------------------------------------------------------------------\n')
        

def tlb_status_cmd(cpu):
    if not cpu:
        cpu,_ = get_cpu(kind = ("ia64", "an IA-64 processor"))
    obj_tlb_status_cmd(cpu)

new_command("tlb-status", tlb_status_cmd,
            [arg(obj_t("ia64 processor object", "ia64"), "cpu-name", "?")],
            type  = "general commands",
            short = "display tlb status",
            namespace_copy = ("ia64", obj_tlb_status_cmd),
            doc = """
Displays the current status of the two TLBs.""", filename="/mp/simics-3.0/src/core/ia64/commands.py", linenumber="407")

#
# -------------------- pfregs --------------------
#

def obj_pfregs_command(cpu, fr):

        fregs = cpu.fr[0:128]

	start = -1
        if not fr:
                start = 0
                stop = 128
        elif fr[0] == "f":
		try:
			start = int(fr[1:])
		except:
			pass
                stop = start+1
	if start < 0 or stop > 128:
                pr("Unknown FP register: %s\n" % fr)
                SIM_command_has_problem()
                return
        
	for i in range(start, stop):
                reg = fregs[i]
                significand = reg[0]
                bexp = reg[1]
                
		# raw = (long(reg[2]) << 81) | (long(exp) << 64) | long(significand)
                if reg[2]: sg = -1.0
                else:      sg =  1.0

		if bexp == 0 and significand == 0:
			str = '%f' % 0
		if bexp == 0x1003E:
			if (significand & (1L << 63)):
				str = '%d' % (significand - 0x10000000000000000L)
			else:
				str = '%d' % significand
                elif bexp == 0x1fffe:
                        str = "NaT"
                elif bexp == 0x1ffff and significand == (1L<<63):
                        if reg[2]:
                                str = "-INF"
                        else:
                                str = "INF"
                elif bexp == 0x1ffff and significand & (1L<<63):
                        str = "NaN"
                else:
                        if bexp == 0:
                                exp = -16382
                        else:
                                exp = bexp - 65535

                        if -1022 <= exp <= 1023:
                            f = sg * ((2.0)**float(exp)) * (float(significand)/float(1L << 63))
                            str = '%f' % f
                        else:
                            str = "%f*2^%d" % ((float(significand)/float(1L << 63)), exp)
		
		pr("f%-3d = %-20s  (%d:%05x:%08x)\n" % (i, str, reg[2], bexp, significand))

def pfregs_command(cpu, fr):
    if not cpu:
        cpu,_ = get_cpu(kind = ("ia64", "an IA-64 processor"))
    obj_pfregs_command(cpu, fr)


def fr_expander(comp):
        if len(comp) > 0 and comp[0] != "f":
                return []
        l = [ ]
        for f in xrange(0,128):
                fr = "f%d" % f
                if fr[:len(comp)] == comp:
                        l.append(fr)
        return l

new_command("pfregs", pfregs_command,
            [arg(obj_t("ia64 processor object", "ia64"), "cpu-name", "?"),
             arg(str_t, "fr", "?", expander = fr_expander)],
            type  = "inspect/change commands",
            short = "print floating point registers",
            doc_items = [('NOTE', """
The floating-point values printed may be inaccurate depending on differences in the range
and precision between Python floats and IA64 floating point values.""")],
            namespace_copy = ("ia64", obj_pfregs_command),
            doc = """
Prints the floating point register file of the processor <i>cpu-name</i>.
The output includes the values formatted in both floating-point form and
raw hexadecimal form.""", filename="/mp/simics-3.0/src/core/ia64/commands.py", linenumber="493")

#
# -------------------- fpsr --------------------
#

def sf_info(sf):
        rc_names = { 0: "Nearest (or even)",
                     1: "-Infinity",
                     2: "+Infinity",
                     3: "Zero (truncate)" }

        flags = ""
        if sf & 0x0080: flags += "v"
        if sf & 0x0100: flags += "d"
        if sf & 0x0200: flags += "z"
        if sf & 0x0400: flags += "o"
        if sf & 0x0800: flags += "u"
        if sf & 0x1000: flags += "i"

        return [ ("ftz", iff(sf & 1, "Enabled", "Disabled")),
                 ("wre", iff(sf & 2, "Enabled", "Disabled")),
                 ("pc",  (sf >> 2) & 3),
                 ("rc",  rc_names[(sf >> 4) & 3]),
                 ("td",  iff(sf & 64, "Disabled", "Enabled")),
                 ("flags", flags) ]
                 
def obj_fpsr_cmd(cpu):
        fpsr_r = SIM_get_register_number(cpu, "ar.fpsr")
        fpsr = SIM_read_register(cpu, fpsr_r)
        title = "Floating-point status register for %s" % cpu.name
        info = [ ("Traps",
                  [ ("vd", iff(fpsr & 0x0000000000000001L, "Disabled", "Enabled")),
                    ("dd", iff(fpsr & 0x0000000000000002L, "Disabled", "Enabled")),
                    ("zd", iff(fpsr & 0x0000000000000004L, "Disabled", "Enabled")),
                    ("od", iff(fpsr & 0x0000000000000008L, "Disabled", "Enabled")),
                    ("ud", iff(fpsr & 0x0000000000000010L, "Disabled", "Enabled")),
                    ("id", iff(fpsr & 0x0000000000000020L, "Disabled", "Enabled")) ]),
                 ("Status field 0",
                  sf_info(fpsr >> 6)),
                 ("Status field 1",
                  sf_info(fpsr >> 19)),
                 ("Status field 2",
                  sf_info(fpsr >> 32)),
                 ("Status field 3",
                  sf_info(fpsr >> 45)) ]
	print title
        print_info(info)
        

def fpsr_cmd(cpu):
    if not cpu:
        cpu,_ = get_cpu(kind = ("ia64", "an IA-64 processor"))
    obj_fpsr_cmd(cpu)


new_command("fpsr", fpsr_cmd,
            [arg(obj_t("ia64 processor object", "ia64"), "cpu-name", "?")],
            type  = "inspect/change commands",
            short = "print floating point status register",
            namespace_copy = ("ia64", obj_fpsr_cmd),
            doc = """
Prints the fields of the floating point status register (AR.fpsr).""", filename="/mp/simics-3.0/src/core/ia64/commands.py", linenumber="561")
