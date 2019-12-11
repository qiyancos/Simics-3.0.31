from cli import *


# ------------------------------------------------------------------------------
#
#  Info command
#
def info_cmd(an_object):

	global the_csrs_attribute

	try:
		the_csrs_attribute = SIM_get_attribute(an_object, "csrs")
	except SimExc_Attribute, msg:
        	raise Exception, "Unable to read control and status registers"

	# ----------------------------------------------------------------------
	#
	#  Get a single register from the file of control and status registers
	#

	global get_register

	def get_register(a_register_offset):
		for entry in the_csrs_attribute:
			if entry[0] == a_register_offset:
				return "0x%016x" % entry[1];
		return "<not available>"
	#
	# ----------------------------------------------------------------------
	

	# ----------------------------------------------------------------------
	#
	#  Print register name and value
	#
	
	def print_register(a_register_name, a_register_offset):
		print "    %-12s %s" % (a_register_name, get_register(a_register_offset))
	#
	# ----------------------------------------------------------------------
	

	print("General Registers:")

	print_register("CIA_REV",      0x00000080)
	print_register("PCI_LAT",      0x000000c0)
	print_register("CIA_CTRL",     0x00000100)
	print_register("CIA_CNFG",     0x00000140)
	print_register("HAE_MEM",      0x00000400)
	print_register("HAE_IO",       0x00000440)
	print_register("CFG",          0x00000480)	
	print_register("CACK_EN",      0x00000600)

	print("")
	print("Diagnostic Registers:")

	print_register("CIA_DIAG",     0x00002000)
	print_register("DIAG_CHECK",   0x00003000)

	print("")
	print("Performance Monitor Registers:")

	print_register("PERF_MONITOR", 0x00004000)
	print_register("PERF_CONTROL", 0x00004040)

	print("")
	print("Error Registers:")

	print_register("CPU_ERR0",     0x00008000)
	print_register("CPU_ERR1",     0x00008040)
	print_register("CIA_ERR",      0x00008200)
	print_register("CIA_STAT",     0x00008240)
	print_register("ERR_MASK",     0x00008280)
	print_register("CIA_SYN",      0x00008300)
	print_register("MEM_ERR0",     0x00008400)
	print_register("MEM_ERR1",     0x00008440)
	print_register("PCI_ERR0",     0x00008800)	
	print_register("PCI_ERR1",     0x00008840)
	print_register("PCI_ERR2",     0x00008880)

	print("")
	print("System Configuration Registers:")

	print_register("MCR",          0x10000000)
	print_register("MBA0",         0x10000600)
	print_register("MBA2",         0x10000680)
	print_register("MBA4",         0x10000700)
	print_register("MBA6",         0x10000780)
	print_register("MBA8",         0x10000800)	
	print_register("MBAA",         0x10000880)	
	print_register("MBAC",         0x10000880)	
	print_register("MBAE",         0x10000900)	
	print_register("MBAA",         0x10000980)	
	print_register("TMG0",         0x10000B00)	
	print_register("TMG1",         0x10000B40)	
	print_register("TMG2",         0x10000B80)

	print("")
	print("PCI Address and Scatter-Gather Registers:")

	print_register("TBIA",         0x20000100)
	print_register("W0_BASE",      0x20000400)
	print_register("W0_MASK",      0x20000440)
	print_register("T0_BASE",      0x20000480)
	print_register("W1_BASE",      0x20000500)
	print_register("W1_MASK",      0x20000540)
	print_register("T1_BASE",      0x20000580)
	print_register("W2_BASE",      0x20000600)
	print_register("W2_MASK",      0x20000640)
	print_register("T2_BASE",      0x20000680)
	print_register("W3_BASE",      0x20000700)
	print_register("W3_MASK",      0x20000740)
	print_register("T3_BASE",      0x20000780)
	print_register("W_DAC",        0x200007c0)

	print("")
	print("Address Translation Registers:")

	print_register("LTB_TAG0",     0x20000800)
	print_register("LTB_TAG1",     0x20000840)
	print_register("LTB_TAG2",     0x20000880)
	print_register("LTB_TAG3",     0x200008c0)

	print_register("TB_TAG0",      0x20000900)
	print_register("TB_TAG1",      0x20000940)
	print_register("TB_TAG2",      0x20000980)
	print_register("TB_TAG3",      0x200009c0)

	print_register("TB0_PAGE0",    0x20001000)
	print_register("TB0_PAGE1",    0x20001040)
	print_register("TB0_PAGE2",    0x20001080)
	print_register("TB0_PAGE3",    0x200010c0)

	print_register("TB1_PAGE0",    0x20001100)
	print_register("TB1_PAGE1",    0x20001140)
	print_register("TB1_PAGE2",    0x20001180)
	print_register("TB1_PAGE3",    0x200011c0)

	print_register("TB2_PAGE0",    0x20001200)
	print_register("TB2_PAGE1",    0x20001240)
	print_register("TB2_PAGE2",    0x20001280)
	print_register("TB2_PAGE3",    0x200012c0)

	print_register("TB3_PAGE0",    0x20001300)
	print_register("TB3_PAGE1",    0x20001340)
	print_register("TB3_PAGE2",    0x20001380)
	print_register("TB3_PAGE3",    0x200013c0)

	print_register("TB4_PAGE0",    0x20001400)
	print_register("TB4_PAGE1",    0x20001440)
	print_register("TB4_PAGE2",    0x20001480)
	print_register("TB4_PAGE3",    0x200014c0)
	
	print_register("TB5_PAGE0",    0x20001500)
	print_register("TB5_PAGE1",    0x20001540)
	print_register("TB5_PAGE2",    0x20001580)
	print_register("TB5_PAGE3",    0x200015c0)
	
	print_register("TB6_PAGE0",    0x20001600)
	print_register("TB6_PAGE1",    0x20001640)
	print_register("TB6_PAGE2",    0x20001680)
	print_register("TB6_PAGE3",    0x200016c0)

	print_register("TB7_PAGE0",    0x20001700)
	print_register("TB7_PAGE1",    0x20001740)
	print_register("TB7_PAGE2",    0x20001780)
	print_register("TB7_PAGE3",    0x200017c0)
	
#
# ------------------------------------------------------------------------------




new_command("info", info_cmd,
            [],
            alias = "",
            type  = "pyxis commands",
            short = "print information about device",
	    namespace = "pyxis",
            doc = """
Print detailed information about the simulated device.<br/>
""", filename="/mp/simics-3.0/src/devices/pyxis/commands.py", linenumber="176")
