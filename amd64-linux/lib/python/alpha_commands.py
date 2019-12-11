from cli import *
import string
import sim_commands

# ==============================================================================
# 
#	STATIC DATA
#
# ==============================================================================

# ==============================================================================
# 
#	LOAD ROM
#
# ==============================================================================

def load_rom_cmd(the_rom_file, an_address, the_verbose_flag):
	try:
		current_processor().iface.alpha.load_rom(current_processor(),
                                                         the_rom_file, an_address, the_verbose_flag)	
	except Exception, msg:
		print msg
		SIM_command_has_problem()
		return

new_command("load-rom",
	    load_rom_cmd,
            args = [arg(filename_t(simpath = 1), "rom-file"),
		    arg(int_t, "address"), arg(flag_t, "-v")],
            type  = "inspect/change commands",
            short = "load a ROM image into memory.",
            doc = """The <b>load-rom</b> command loads a rom image
(e.g. the SRM console) from a file into memory. The PC and the PAL
base registers are set to the entry point as specified by the ROM
header.  Information extracted from the ROM header is written to the
console if the verbose flag is set. Use <arg>-verbose</arg> to get more
information during loading.""", filename="/mp/simics-3.0/src/core/alpha/commands.py", linenumber="26")

# ==============================================================================
# 
#	INTEGER REGISTERS
#
# ==============================================================================

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

def make_reg_string(cpu, i):
	name  = "%-4s" % (SIM_get_register_name(cpu, i))
	value = SIM_read_register(cpu, i)
	return "%s 0x%.16x  "  % (name, value)

def print_gpr_regs(cpu):
	the_list = []
	try:
		for i in range(0, 32):
			the_list.append (make_reg_string (cpu, i))
		# Append the PC register
		the_list.append (make_reg_string (cpu, 65))

		print_list(the_list)				
	except Exception, the_message:
		pr(the_message)

def print_fpr_regs(cpu):
	the_list = []
	try:
		for i in range(32, 64):
			the_list.append (make_reg_string (cpu, i))
		# Append the FPCR register
		the_list.append (make_reg_string (cpu, 64))

		print_list(the_list)				
	except Exception, the_message:
		pr(the_message)

def local_pregs(a_conf_object, all):
	print_gpr_regs(a_conf_object)

	if all != 0:
		pr("\n");
		print_fpr_regs(a_conf_object)


local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun(
	address_filter = lambda address: (address & ~3L))

# ==============================================================================
# 
#	INTERNAL PROCESSOR REGISTERS
#
# ==============================================================================

from string import upper


def ipr_list(a_cpu):
	the_ipr_list = []
	for the_number in range(current_processor().iface.alpha.number_of_iprs(current_processor())):
		try:
			the_ipr_list.append(a_cpu.iface.alpha.ipr_name(a_cpu,
                                                                       a_cpu.iface.alpha.ipr_number_to_index(a_cpu, the_number)))
		except SimExc_General, msg:
			pass
	return the_ipr_list;

def ipr_name_expander(the_completion):
	return get_completions(upper(the_completion), ipr_list())

# read-ipr

def read_ipr_command(cpu, a_register):
    if not cpu:
        cpu,_ = get_cpu(kind = ("alpha", "an Alpha processor"))
    return object_read_ipr_command(cpu, a_register)

def object_read_ipr_command(a_cpu, a_register):
	if a_register[2] == "index":
		assert a_register[0] == int_t
		the_index = a_register[1]
		try:
			return a_cpu.iface.alpha.read_ipr(a_cpu, the_index)
		except Exception, the_message:
			print the_message
	if a_register[2] == "name":
		assert a_register[0] == str_t
		the_name = upper(a_register[1])
		try:
			the_index = a_cpu.iface.alpha.ipr_index(a_cpu, the_name)
			return object_read_ipr_command(a_cpu, (int_t, the_index, 'index'))
		except Exception, the_message:
			print the_message
			 
new_command("read-ipr", read_ipr_command,
            args = [arg(obj_t('Alpha processor', 'alpha'), "cpu-name", "?"),
		    arg((int_t, str_t), ("index", "name" ), "?",
			(str_t, "all", "name"),
			expander = (ipr_name_expander, None)) ],
            namespace_copy = ("alpha", object_read_ipr_command),
            type  = "inspect/change commands",
            short = "read/write internal processor register",
            doc = """
	    The Alpha microprocessor contains a file of
	    <i>internal</i><i> </i><i>processor</i><i>
	    </i><i>registers</i> (available only to privileged
	    software through PALcode routines) that allow the
	    operating system to interrogate and modify system state.

	    The <b>read-ipr</b> command reads the value of a single
	    register. The register is specified either by its name
	    (e.g. pal_base) or its index (e.g. 0x10E).

	    The <b>write_ipr</b> commands writes the given value to
	    the specified register.

	    Note that register names and indices differs between
	    different Alpha implementations (EV5, EV6, etc).
	    """, filename="/mp/simics-3.0/src/core/alpha/commands.py", linenumber="147")

# write-ipr

def write_ipr_command(cpu, reg, value):
    if not cpu:
        cpu,_ = get_cpu(kind = ("alpha", "an Alpha processor"))
    return object_write_ipr_command(cpu, reg, value)

 
def object_write_ipr_command(a_cpu, a_register, a_value):
	if a_register[2] == "index":
		assert a_register[0] == int_t
		the_index = a_register[1]
		try:
			return a_cpu.iface.alpha.write_ipr(a_cpu, the_index, a_value)
		except Exception, the_message:
			print the_message
	if a_register[2] == "name":
		assert a_register[0] == str_t
		the_name = upper(a_register[1])
		try:
			the_index = a_cpu.iface.alpha.ipr_index(a_cpu, the_name)
			return object_write_ipr_command(a_cpu, (int_t, the_index, 'index'), a_value)
		except Exception, the_message:
			print the_message
			
new_command("write-ipr", write_ipr_command,
            args = [arg(obj_t('Alpha processor', 'alpha'), "cpu-name", "?"),
		    arg((int_t, str_t), ("index", "name" ), expander = (ipr_name_expander, None)),
		    arg(int_t, "value") ],
            namespace_copy = ("alpha", object_write_ipr_command),
            type  = "inspect/change commands",
            short = "write internal processor register",
	    doc_with = "read-ipr", filename="/mp/simics-3.0/src/core/alpha/commands.py", linenumber="198")

# piprs


def piprs_command(a_cpu_name, verbose):
    if not cpu:
        cpu,_ = get_cpu(kind = ("alpha", "an Alpha processor"))
    object_piprs_command(cpu, verbose)
	
def object_piprs_command(a_cpu, a_verbose_flag):
	the_max_length = max(map(lambda an_entry: len(an_entry), ipr_list(a_cpu)))
	print "max length %d" % the_max_length
	the_ipr_list = []
	for the_number in range(a_cpu.iface.alpha.number_of_iprs(a_cpu)):
		try:
			the_index = a_cpu.iface.alpha.ipr_number_to_index(a_cpu, the_number)
			the_name = a_cpu.iface.alpha.ipr_name(a_cpu, the_index)
			the_value = a_cpu.iface.alpha.read_ipr(a_cpu, the_index)
			the_entry = "%*s = 0x%.16x" % (the_max_length, the_name, the_value)
			if a_verbose_flag:
				the_description = a_cpu.iface.alpha.ipr_description(a_cpu, the_index)
				if the_description != "":
					the_entry = the_entry + " (" + the_description + ")"
			the_ipr_list.append(the_entry)
		except SimExc_General, msg:
			pass
	print_list(the_ipr_list)

new_command("piprs", piprs_command,
            [arg(obj_t('Alpha processor', 'alpha'), "cpu-name", "?"),
	     arg(flag_t, "-verbose")],
            type  = "inspect/change commands",
            short = "print internal processor registers",
            namespace_copy = ("alpha", object_piprs_command),            
            doc = """	    
	    Print the contents of all internal registers of processor
	    <i>cpu-name</i>. If no CPU is specified the current CPU
	    will be selected. With <arg>-verbose</arg>, <cmd>piprs</cmd>
            will also print the description of each register.""", filename="/mp/simics-3.0/src/core/alpha/commands.py", linenumber="234")


# ------------------------------------------------------------------------------
#
#  pfregs
#


def pfregs_command():
	the_list = []
	the_cpu = current_processor()
	try:
		for i in range(0, 32):			
			the_value = SIM_get_attribute_idx(the_cpu, "fregs", i)
			the_list.append("F%-2d = 0x%.16x" % (i, the_value))
		print_list(the_list)				
	except Exception, the_message:
		print the_message

        
new_command("pfregs", pfregs_command,
            [],
	    deprecated = "pregs",
            type  = "inspect/change commands",
            short = "print floating point registers",
            doc_items = [('NOTE', 'The values printed may be inaccurate on hosts that are not IEEE-754 compliant.')],
            doc = """
Print binary contents of the floating point registers in hexadecimal form.""", filename="/mp/simics-3.0/src/core/alpha/commands.py", linenumber="265")
