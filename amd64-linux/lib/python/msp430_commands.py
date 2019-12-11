from cli import *
import sim_commands

local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun()

def print_list(a_list):
	ipr_list = a_list
	num_iprs = len(ipr_list)
        max_length = max(map(lambda an_entry: len(an_entry), ipr_list))
        column_width = max_length + 1
        num_columns = 80 / column_width
	if num_columns == 0:
		num_columns = 1
	num_rows = (num_iprs + num_columns - 1) / num_columns
        for i in range(num_rows):
                for j in range(num_columns):
                        index = i + j * num_rows
                        if index < num_iprs:
                                pr("%s " % ipr_list[index])
		pr("\n")


def local_pregs(processor, all):
    names = ["pc ", "sp ", "sr ", "#0 ", "r4 ", "r5 ", "r6 ", "r7 ",
	     "r8 ", "r9 ", "r10", "r11", "r12", "r13", "r14", "r15"]
    try:
        pr("\n");
        list = []
        for reg in range(0, 16):
            list.append("%s = 0x%.4x  " % (names[reg],
					   processor.gprs[reg]));
        print_list(list);
        pr("\n");

    except Exception, message:
        print message
    
funcs = { 'print_disassemble_line':
          local_print_disassemble_line,
          'pregs':
          local_pregs,
#          'get_pending_exception_string':
#          local_pending_exception
          }

#
# Reset command, invoking the reset on the processor
#
def hard_reset_command(processor):
	# SIM_reset_processor(processor,1)
	processor.iface.processor.reset(processor, 1)

new_command("reset",hard_reset_command,
	    [],
	    type  = "inspect/change commands",
	    short = "reset the processor",
	    doc = "do a hard reset on the processor",
	    namespace = "msp430", filename="/mp/simics-3.0/src/core/msp430/commands.py", linenumber="53")


