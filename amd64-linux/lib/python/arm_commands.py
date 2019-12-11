from cli import *
import re
import string
import sim_commands

def print_list(a_list):
	the_ipr_list = a_list
	the_number_of_iprs = len(the_ipr_list)
        the_max_length = max(map(lambda an_entry: len(an_entry), the_ipr_list))
        the_column_width = the_max_length + 1
        the_number_of_columns = 80 / the_column_width
	if the_number_of_columns == 0:
		the_number_of_columns = 1
        the_number_of_rows = ((the_number_of_iprs + the_number_of_columns - 1)
                              / the_number_of_columns)
        for i in range(the_number_of_rows):
                for j in range(the_number_of_columns):
                        index = i + j * the_number_of_rows
                        if index < the_number_of_iprs:
                                pr("%s " % the_ipr_list[index])
		pr("\n")

local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun()

def bit_string(size, value):
	str = ""
	for bit in range(size-1,-1,-1):
		if (value & 1<<bit):
			str = str + "1"
		else:
			str = str + "0"
	return str

def _get_mode_number(processor):
        return {0x10:0, 0x13:1, 0x17:2, 0x1b:3,
                0x12:4, 0x11:5, 0x1f:0}[processor.cpsr[0] & 0x1f]

def gprs_names():
        return ("r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", 
               "r8", "r9", "r10", "r11", "r12", "sp", "lr", "pc");

def pscc_regs_command(processor):
	try:
                # Get the name and value of all attribute accessible registers
                regs = [[reg[2], reg[3]] for reg in processor.scc_list if not reg[12]]
                max_width = max(map(lambda (name, value) : len(name), regs))
                format = "%%-%ds 0x%%08x" % max_width
                for (name, value) in regs:
                        print format % (name, value)
	except Exception, the_message:
		print the_message

new_command("pscc-regs", pscc_regs_command,
            args = [],
            namespace = "arm",
            see_also = ["pregs"],
            short = "print coprocessor 15 (scc) registers.",
            doc = """
Prints the current scc register file of coprocessor 15 (scc).
	    """, filename="/mp/simics-3.0/src/core/arm/commands.py", linenumber="53")


def cp_pregs_command(obj):
	try:
                pr("\n")
                the_list = []
                api = SIM_get_interface(obj, "int_register")
                regs = [api.get_name(obj, r) for r in api.all_registers(obj) ]
                values = [api.read(obj, r) for r in api.all_registers(obj) ]
                for i in range(0, len(values)):
                        the_list.append("%-6s = 0x%.8x  "
                                        % (regs[i],
                                           values[i]))
                print_list(the_list)
                pr("\n")
  
	except Exception, the_message:
		print the_message

new_command("pregs", cp_pregs_command,
            args = [],
            namespace = "arm_coprocessor",
            type  = ["Registers", "Inspecting Simulated State",
                     "ARM specific commands"],
            see_also = ["<arm_coprocessor>.read-reg, <arm_coprocessor>.write-reg"],
            short = "print coprocessor registers.",
            doc = """
Prints the current register file of the given ARM coprocessor.
	    """, filename="/mp/simics-3.0/src/core/arm/commands.py", linenumber="80")


def exp_regs(comp, obj):
        try:
                api = SIM_get_interface(obj, "int_register")
                regs = [api.get_name(obj, r) for r in api.all_registers(obj) ]
                return get_completions(comp, regs)
	except Exception, the_message:
		print the_message

def p_regs_command(obj, reg_name):
        api = obj.iface.int_register
        return api.read(obj, api.get_number(obj, reg_name))


new_command("read-reg", p_regs_command,
            args = [ arg(str_t, "reg-name", expander = exp_regs)],
            namespace = "arm_coprocessor",
            type  = ["Registers", "Inspecting Simulated State"],
            see_also = ["<arm_coprocessor>.pregs, <arm_coprocessor>.write-reg"],
            short = "print coprocessor registers.",
            doc = """
Read the value of the given ARM coprocessor register.
	    """, filename="/mp/simics-3.0/src/core/arm/commands.py", linenumber="105")

def w_regs_command(obj, reg_name, value):
        api = obj.iface.int_register
        return api.write(obj, api.get_number(obj, reg_name), value)


new_command("write-reg", w_regs_command,
            args = [ arg(str_t, "reg-name", expander = exp_regs),
                     arg(integer_t, "value"),],
            namespace = "arm_coprocessor",
            type  = ["Registers", "Changing Simulated State"],
            see_also = ["<arm_coprocessor>.pregs, <arm_coprocessor>.read-reg"],
            short = "write coprocessor register.",
            doc = """
Set the value of an ARM coprocessor register. For example, to
set the <tt>c0</tt> register on the CP-14 coprocessor <obj>cp14</obj> to 3
write: <cmd>cp14.write-reg c0 3</cmd>.
	    """, filename="/mp/simics-3.0/src/core/arm/commands.py", linenumber="120")



def p_sr_key():
        pr("                    NZCVQ-------------------IFTMMMMM\n")
        
def local_pregs(processor, all):
	try:
                gpr_names = gprs_names()
                mode_names = "usr", "svc", "abt", "und", "irq", "fiq"

                pr("\n")
		if all:
                        for mode in range(0, 6):
                                pr("Mode: " + mode_names[mode] + "\n\n")
                                the_list = []
                                for i in range(0, 16):
                                        the_list.append("%-4s = 0x%.8x  "
                                                        % (gpr_names[i],
                                                           processor.gprs[mode][i]))
                                print_list(the_list)
                                pr("\n")
                                if mode != 0:
                                        pr("spsr = 0x%.8x : %s\n"
                                           % (processor.spsr[mode],
                                              bit_string(32, processor.spsr[mode])))
                                        p_sr_key()
                                        pr("\n")
                else:
                        mode = _get_mode_number(processor)
                        the_list = []
                        for i in range(0, 16):
                                the_list.append("%-4s = 0x%.8x  "
                                                % (gpr_names[i],
                                                   processor.gprs[mode][i]))
                        print_list(the_list)
                        pr("\n")
                        if mode != 0:
                                pr("spsr = 0x%.8x : %s\n"
                                   % (processor.spsr[mode],
                                      bit_string(32, processor.spsr[mode])))
                                p_sr_key()
                                pr("\n")

                pr("cpsr = 0x%.8x : %s\n" % (processor.cpsr[0],
                                             bit_string(32, processor.cpsr[0])))
                p_sr_key()
                pr("\n")

	except Exception, the_message:
		print the_message


def arm_diff_regs(obj):
        def name(x):
                return SIM_get_register_name(obj, x)
        return map(name, SIM_get_all_registers(obj))


def local_exception_names(exc):
        exception = ("Reset", "Data Abort", "FIQ", "IRQ", "Prefetch Abort",
                      "Undefined", "Software Intereupt")
        exc_list = []
        for  i in range(0, 7):
                if exc & (1 << i):
                        exc_list.append(exception[i])
        return exc_list

                

def local_pending_exception(cpu):
        if cpu.pending_exception:
                return ("Pending exception: %s"
                        % local_exception_names(cpu.pending_exception))
        else:
                return None
