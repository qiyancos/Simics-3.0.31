from cli import *
import re
import string
import sim_commands
import sim_profile_commands

def mips_hex_str(bits, val):
        if bits == 64:
                return "0x%.16x" % (val)
        else:
                return "0x%.8x" % (val)


def print_list(a_list):
	the_ipr_list = a_list
	the_number_of_iprs = len(the_ipr_list)
        the_max_length = max(map(lambda an_entry: len(an_entry), the_ipr_list))
        the_column_width = the_max_length + 1
        the_number_of_columns = 80 / the_column_width
	if the_number_of_columns == 0:
		the_number_of_columns = 1
        the_number_of_rows = (the_number_of_iprs + the_number_of_columns - 1) / the_number_of_columns
        for i in range(the_number_of_rows):
                for j in range(the_number_of_columns):
                        index = i + j * the_number_of_rows
                        if index < the_number_of_iprs:
                                pr("%s " % the_ipr_list[index])
		pr("\n")



def bit_string(size, value):
	str = ""
	for bit in range(size-1,-1,-1):
		if (value & 1<<bit):
			str = str + "1 "
		else:
			str = str + "0 "
	return str


#
# -------------------- print disassemble line --------------------
#

def local_pending_exception(cpu):
	if (cpu.cause & cpu.status & 0xFF00) and (cpu.status & (1 << 0)) and not (cpu.status & (1 << 1)):
		return "Pending interrupt"
	else:
		return None

local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun()

def bit_string(size, value):
	str = ""
	for bit in range(size-1,-1,-1):
		if (value & 1<<bit):
			str = str + "1 "
		else:
			str = str + "0 "
	return str

def local_pregs(cpu, all):
	try:
                address_bits = cpu.address_width[1]
		the_list = []
		gprs = cpu.gprs
		for i in range(0, 32):
			the_name = "%4s %5s" % (SIM_get_register_name(cpu, i), "[r%d]" % (i))
			the_value = gprs[i]
			the_list.append("%-10s = %s   " % (the_name, mips_hex_str(address_bits, the_value)))
		print_list(the_list)
		pr("\n");
		print "HI       %s" % mips_hex_str(address_bits, cpu.hi)
		print "LO       %s" % mips_hex_str(address_bits, cpu.lo)
		print "PC       %s" % mips_hex_str(address_bits, cpu.pc)
		print "NPC      %s" % mips_hex_str(address_bits, cpu.npc)
		print

		if all:
			print "Coprocessor 0 registers:"
			print "------------------------"
			print "PRId     0x%.8x" % (cpu.prid)
			print "Config   0x%.8x" % (cpu.config)
			print "    %s" % (bit_string(32, cpu.config))
			#          3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1                    "
			#          1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
			print "    M K K K K K K - - - - M - M M B B A A A A A M M M - - - - K K K"
			print "      2 2 2 U U U         D   M M M E T T R R R T T T         0 0 0"
			print "      3 3 3 2 1 0         U           1 0 2 1 0 2 1 0         2 1 0"
			print
			print "Config1  0x%.8x" % (cpu.config1)
			print "    %s" % (bit_string(32, cpu.config1))
			#          3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1                    "
			#          1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
			print "    - M M M M M M I I I I I I I I I D D D D D D D D D - - P W C E F"
			print "      M M M M M M S S S L L L A A A S S S L L L A A A     C R A P P"
			print "      U U U U U U 2 1 0 2 1 0 2 1 0 2 1 0 2 1 0 2 1 0              "
			print
			print "Status   0x%.8x" % (cpu.status)
			print "    %s" % (bit_string(32, cpu.status))
			#          3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1                    "
			#          1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
                        if address_bits == 64:
				if SIM_class_has_attribute(cpu.classname, "fprs"):
					print "    C C C C R F R - - B T S N - - - I I I I I I I I K S U K K E E I"
					print "    U U U U P R E     E S R M       M M M M M M M M X X X S S R X E"
					print "    3 2 1 0           V     I       7 6 5 4 3 2 1 0       U U L L  "
				else:
					print "    C C C C R - R - - B T S N - - - I I I I I I I I K S U K K E E I"
					print "    U U U U P   E     E S R M       M M M M M M M M X X X S S R X E"
					print "    3 2 1 0           V     I       7 6 5 4 3 2 1 0       U U L L  "
                        else:
				print "    C C C C R - R - - B T S N - - - I I I I I I I I - - - U - E E I"
				print "    U U U U P   E     E S R M       M M M M M M M M       M   R X E"
				print "    3 2 1 0           V     I       7 6 5 4 3 2 1 0           L L  "
			print
			print "Cause    0x%.8x" % (cpu.cause)
			print "    %s" % (bit_string(32, cpu.cause))
			#          3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1                    "
			#          1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
			print "    B - C C - - - - I W - - - - - - I I I I I I I I - E E E E E - -"
			print "    D   E E         V P             P P P P P P P P   X X X X X    "
			print "        1 0                         7 6 5 4 3 2 1 0   C C C C C    "
			print
			print "Count    0x%.8x" % (cpu.count)
			print "Compare  0x%.8x" % (cpu.compare)
			print "EPC      %s" % mips_hex_str(address_bits, cpu.epc)
			print "ErrorEPC %s" % mips_hex_str(address_bits, cpu.errorepc)
			print "DEPC     %s" % mips_hex_str(address_bits, cpu.depc)
			print
			print "LLAddr   %s" % mips_hex_str(address_bits, cpu.lladdr)
			print "WatchLo  %s" % mips_hex_str(address_bits, cpu.watchlo)
			print "WatchHi  0x%.8x" % (cpu.watchhi)
			print "TagLo    0x%.8x" % (cpu.taglo)
			print "DataLo   0x%.8x" % (cpu.datalo)
			print "DeSave   0x%.8x" % (cpu.desave)
			print "Debug    %s" % mips_hex_str(address_bits, cpu.debug)
			print
			print "Index    0x%.8x" % (cpu.index)
			print "Random   0x%.8x" % (cpu.random)
			print "Wired    0x%.8x" % (cpu.wired)
			print "EntryLo0 %s" % mips_hex_str(address_bits, cpu.entrylo0)
			print "EntryLo1 %s" % mips_hex_str(address_bits, cpu.entrylo1)
			print "EntryHi  %s" % mips_hex_str(address_bits, cpu.entryhi)
			print "Context  %s" % mips_hex_str(address_bits, cpu.context)
                        if address_bits == 64:
                                print "XContext %s" % mips_hex_str(address_bits, cpu.xcontext)
			print "PageMask 0x%.8x" % (cpu.pagemask)
			print "BadVAddr %s" % mips_hex_str(address_bits, cpu.badvaddr)
			print
						       
	except Exception, the_message:
		print the_message

register_regex = re.compile('^\([fr]\)\([0-9][0-9]?\)$');


def tlb_info(cpu, tlb):
        address_bits   = cpu.address_width[1]
        virtual_base   = tlb[0]
	page_size_log2 = tlb[1]
	asid           = tlb[2]
	g              = tlb[3]
        physical_base0 = tlb[4][0]
	c0             = tlb[4][1]
	d0             = tlb[4][2]
	v0             = tlb[4][3]
	physical_base1 = tlb[5][0]
	c1             = tlb[5][1]
	d1             = tlb[5][2]
	v1             = tlb[5][3]

        page_size = 1 << page_size_log2
	virt0_start = virtual_base
	virt0_end   = virtual_base + page_size - 1
	virt1_start = virtual_base + page_size
	virt1_end   = virtual_base + 2 * page_size - 1

	str0 = "[%s-%s %s %d %d %d]" % (mips_hex_str(address_bits, virt0_start), mips_hex_str(address_bits, virt0_end), mips_hex_str(address_bits, physical_base0), d0, v0, c0)
	str1 = "[%s-%s %s %d %d %d]" % (mips_hex_str(address_bits, virt1_start), mips_hex_str(address_bits, virt1_end), mips_hex_str(address_bits, physical_base1), d1, v1, c1)

	return "%4d %d %s\n                %s" % (asid, g, str0, str1)

def print_tlb(cpu):
        address_bits = cpu.address_width[1]
	print "TLB contents"
	print "------------"
        if address_bits == 64:
        	print "         ASID G [Virtual                               Physical           D V C]"
        else:
        	print "         ASID G [Virtual               Physical   D V C]"
	for i in range(0, len(cpu.jtlb)):
		print "JTLB-%02d: %s" % (i, tlb_info(cpu, cpu.jtlb[i]))

def print_tlb_cmd(cpu):
    if not cpu:
        (cpu, _) = get_cpu(kind = ("mips", "a MIPS processor"))
    print_tlb(cpu)

def obj_print_tlb_cmd(obj):
    print_tlb(obj)

new_command("print-tlb", obj_print_tlb_cmd,
            [],
            type  = "inspect/change commands",
            short = "print TLB contents",
            namespace = "mips",
            doc = """
Prints the contents of the TLB of the processor.
""", filename="/mp/simics-3.0/src/core/mips/commands.py", linenumber="204")

new_command("print-tlb", print_tlb_cmd,
            [arg(obj_t('MIPS processor', 'mips'), "cpu-name", "?")],
            type  = "deprecated commands",
            short = "print TLB contents",
            deprecated = "<mips>.print-tlb",
            doc = """
Prints the contents of the TLB of the processor
<i>cpu_name</i>. If no CPU is specified, the current CPU will be
selected.
""", filename="/mp/simics-3.0/src/core/mips/commands.py", linenumber="213")

def pregs_fpu_cmd(cpu):
        address_bits = cpu.address_width[1]

        try:
                dummy = cpu.fcsr
        except:
                print "The processor %s doesn't have a floating-point coprocessor." % cpu.name
                return

        for n in range(0, 16):
                print "%3s = %s    %3s = %s" % ("f%d" % n, mips_hex_str(address_bits, cpu.fprs[n]), "f%d" % (n + 16), mips_hex_str(address_bits, cpu.fprs[n+16]))
        print
	print "FCSR     0x%.8x" % (cpu.fcsr)
	print "    %s" % (bit_string(32, cpu.fcsr))
	print
	print "    F F F F F F F F F - - - - - C C C C C C E E E E E F F F F F R R"
	print "    C C C C C C C S C           E V Z O U I V Z O U I V Z O U I M M"
	print "    C C C C C C C   C                                              "
	print "    7 6 5 4 3 2 1   0                                              "

new_command("pregs-fpu", pregs_fpu_cmd, [],
            namespace = "mips",
            type  = "inspect/change commands",
            short = "print the floating point registers",
            doc = "Prints the contents of the floating point registers.", filename="/mp/simics-3.0/src/core/mips/commands.py", linenumber="244")

def get_mips_info(obj):
    desciption = VT_get_class_info(obj.class_data, 0, 0)[0]
    address_bits = obj.address_width[1]
    return [("Capabilities", [
              ("Model", desciption),
              ("Word Size", "%d bits"%address_bits),
              ("Byte Order", obj.big_endian and "Big Endian" or "Little Endian"),
              ("Architecture", obj.architecture),
            ]),("Simulation parameters", [
              ("Processor Number", obj.processor_number),
              ("Frequency", "%d MHz"%obj.freq_mhz),
              ("Physical Memory", obj.physical_memory),
            ])
           ]

def get_mips_status(obj):
    address_bits = obj.address_width[1]
    return [(None, [
              ("Cycles", obj.cycles),
              ("Program counter", "0x%0*x"%(address_bits/4,
                                            SIM_get_program_counter(obj))),
              ("Context", obj.current_context),
              ("Interrupts", obj.status & 1 and "Enabled" or "Disabled"),
            ])
           ]

sim_commands.new_status_command('mips', get_mips_status)
sim_commands.new_info_command('mips', get_mips_info)

def get_diff_regs(cpu):
    diff_regs = SIM_get_all_registers(cpu)
    diff_regs = [ SIM_get_register_name(cpu, i) for i in diff_regs ]
    diff_regs.remove('pc')
    diff_regs.remove('count')
    return diff_regs

funcs = { 'print_disassemble_line':
          local_print_disassemble_line,
          'pregs':
          local_pregs,
          'get_pending_exception_string':
          local_pending_exception,
          'get_info':
          get_mips_info,
          'get_status':
          get_mips_status,
          'diff_regs':
          get_diff_regs}
