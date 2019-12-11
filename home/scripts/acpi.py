
##  Copyright 2001-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.

#
# acpi.py
#
# build acpi tables and write to physical memory
#
# Magnus Christensson
#

# The tables created in this assumes the following about the system:
# SMI command port at B2h
# PM1a_evt port at 8000h
# PM1b_cnt port at 8004h
# GPE0_blk port at 8008h
# GPE1_blk port at 800Ch
# PBLK0 port at 8010h
# PBLK1 port at 8018h

# Total memory size in system. Must be continuous starting at 0.
total_megabytes = 0

io_apic_id = 0
max_cpus = 0
cpu0_name = ""
cpu_base_name = ""

# ACPI header values
oem_id = "VTAB  "
oem_table_id = "FOOBAR  "
oem_revision = 4711
vendor_id = 17
creator_revision = 1

# PBLK locations for all cpus
pblk_io_address = 0x8010

# SCI_INT vector in 8259 mode
sci_int_vector = 9

# RSDP at EBDA:0x60. Do not change this without changing the BIOS!
rsdp_addr = 0x9FC0 * 16 + 0x60

# LAPIC address. Must match configuration file.
apic_addr = 0xFEE00000L

# I/O-APIC address. Must match configuration file.
ioapic_addr = 0xFEC00000L

# Memory map descriptors for INT 15h AX=E820. Do not change these
# addresses without changing the BIOS!
high_desc_addr = 0x9FC0 * 16 + 0x90
nvr_desc_addr = 0x9FC0 * 16 + 0xA4
reclaim_desc_addr = 0x9FC0 * 16 + 0xB8
high_desc_addr2 = 0x9FC0 * 16 + 0xcc

if not "add_processors_in_ssdt" in dir():
	if "dsdt_file" in dir():
		add_processors_in_ssdt = 0
	else:
		add_processors_in_ssdt = 1
if not "dsdt_file" in dir():
	dsdt_file = "dsdt-pc-28.2.aml"
else:
	print "Using DSDT from %s" % dsdt_file

def acpi_print(str):
	if SIM_get_verbose():
		print str

def print_table(data):
	index = 0
	for b in data:
		sys.stdout.write("%02x" % b)
		index = index + 1
		if (index & 1) == 0:
			sys.stdout.write(" ")
		if (index & 15) == 0:
			sys.stdout.write("\n")
	sys.stdout.write("\n")

def byte_checksum(data, first, num):
	checksum = 0
	for i in range(first, first+num):
		checksum = (checksum + data[i]) & 0xff
	return (0x100 - checksum) & 0xff

def append_string(data, str):
	for ch in str:
		data.append(ord(ch))

def append_data(data, str):
	for ch in str:
		data.append(ch)

def append_byte(data, byte_data):
	data.append(byte_data)

def append_word(data, word_data):
	append_byte(data, word_data & 0xff)
	append_byte(data, (word_data >> 8) & 0xff)

def append_dword(data, dword_data):
	append_word(data, dword_data & 0xffff)
	append_word(data, (dword_data >> 16) & 0xffff)

def append_qword(data, qword_data):
	append_dword(data, qword_data & 0xffffffffL)
	append_dword(data, (qword_data >> 32) & 0xffffffffL)

def set_byte(data, index, byte_value):
	data[index] = byte_value

def set_word(data, index, word_value):
	set_byte(data, index, word_value & 0xff)
	set_byte(data, index+1, (word_value >> 8) & 0xff)

def set_dword(data, index, dword_value):
	set_word(data, index, dword_value & 0xffff)
	set_word(data, index+2, (dword_value >> 16) & 0xffff)

def create_header(table_id, header_oem_table_id=oem_table_id):
	hdr = []
	append_string(hdr, table_id)
	append_dword(hdr, 0)
	append_byte(hdr, 1)
	append_byte(hdr, 0)
	append_string(hdr, oem_id)
	append_string(hdr, header_oem_table_id)
	append_dword(hdr, oem_revision)
	append_dword(hdr, vendor_id)
	append_dword(hdr, creator_revision)
	return hdr

def append_nameop(data, name):
	append_byte(data, 0x08)
	append_string(data, name)

def append_packageop(data, package_data):
	append_byte(data, 0x12)
	package_len = len(package_data)
	append_byte(data, 0x0a)
	append_byte(data, package_len)
	for b in package_data:
		append_byte(data, 0x0a)
		append_byte(data, b)

def append_scope(data, scope_name, scope_data):
	append_byte(data, 0x10) # Scope
	scopelen = len(scope_data) + len(scope_name)
	single_byte_len = scopelen + 1
	double_byte_len = scopelen + 2
	if single_byte_len < 64:
		append_byte(data, single_byte_len)
	elif double_byte_len < (1 << 12):
		append_byte(data, (double_byte_len & 0x0f) + (1 << 6))
		append_byte(data, (double_byte_len >> 4) & 0xff)
	else:
		raise "Scope in append_scope to large."
	append_string(data, scope_name)
	append_data(data, scope_data)

def append_gena_zero(data):
	for i in range(12):
		append_byte(data, 0)

def append_gena_io(data, port, bits):
	append_byte(data, 1)
	append_byte(data, bits)
	append_byte(data, 0)
	append_byte(data, 0)
	append_qword(data, port)

#
# SSDT (5.2.10.2)
#
# Offset  Size    Description
#  00     DWORD   "SSDT"
#  04     DWORD   Length
#  08     BYTE    Revision (1)
#  09     BYTE    checksum
#  10     6       OEM ID
#  16     QWORD   OEM table ID
#  24     DWORD   OEM revision
#  28     DWORD   Vendor ID
#  32     DWORD   Creator revision
#  36      -      Definition blocks
#

# Our SSDT only contains the _PR_ scope with all processors

def create_ssdt(processors):
	ssdt = create_header("SSDT", header_oem_table_id = "FOOBAR1 ")
	pr_scope = []
	for cpu_no in range(processors):
		append_byte(pr_scope, 0x5B)
		append_byte(pr_scope, 0x83)
		append_byte(pr_scope, 0x11)
		append_string(pr_scope, "\._PR_CPU%d" % cpu_no)
		append_byte(pr_scope, 1+cpu_no)
		append_dword(pr_scope, pblk_io_address)
		append_byte(pr_scope, 6)
	append_scope(ssdt, "_PR_", pr_scope)
	set_dword(ssdt, 4, len(ssdt))
	set_byte(ssdt, 9, byte_checksum(ssdt, 0, len(ssdt)))
	return ssdt

#
# DSDT (5.2.10.1)
#
# Offset  Size    Description
#  00     DWORD   "DSDT"
#  04     DWORD   Length
#  08     BYTE    Revision (1)
#  09     BYTE    checksum
#  10     6       OEM ID
#  16     QWORD   OEM table ID
#  24     DWORD   OEM revision
#  28     DWORD   Vendor ID
#  32     DWORD   Creator revision
#  36      -      Definition blocks
#

def create_default_dsdt():
	raise "Default DSDT not implemented."

def create_dsdt(dsdt_file):
	if dsdt_file != 0:
		try:
			filename = SIM_lookup_file(dsdt_file)
			if not filename:
				raise Exception, "Cannot find DSDT file '%s'" % dsdt_file
			file = open(filename, "rb")
			dsdt = []
			raw_dsdt_string = file.read()
			append_string(dsdt, raw_dsdt_string)
			file.close()
			acpi_print("DSDT read from '%s'" % filename)
			acpi_print("DSDT checksum: 0x%x" % byte_checksum(dsdt, 0, len(dsdt)))
			return dsdt
		except Exception, msg:
			print "Failed to read DSDT: %s" % msg
			print "   (using default values)"
			return create_default_dsdt()
	else:
		return create_default_dsdt()

#
# FACS (5.2.9)
#
# Offset  Size    Description
#  00     DWORD   "FACS"
#  04     DWORD   Length (64)
#  08     DWORD   Hardware signature (some number)
#  12     DWORD   Firmware waking vector
#  16     DWORD   Global lock
#  20     DWORD   Flags
#                  bit 0    s4bios_f (0)
#                  bit 1-31 reserved (0)
#  24     QWORD   Firmware waking vector
#  32     BYTE    Version (1)
#  33     31      Reserved (0)
#
def create_facs():
	facs = []
	append_string(facs, "FACS")
	append_dword(facs, 64)
	append_dword(facs, 4711)
	append_dword(facs, 0)
	append_dword(facs, 0)
	append_dword(facs, 0)
	append_qword(facs, 0)
	append_byte(facs, 1)
	for i in range(31):
		append_byte(facs, 0)
	if len(facs) != 64:
		raise Exception("FACS length %d != 64" % len(facs))
	return facs

#
# FADT 5.2.8
# Offset  Size    Description
#  00     DWORD   "FACP"
#  04     DWORD   Length (244)
#  08     BYTE    Revision (1)
#  09     BYTE    checksum
#  10     6       OEM ID
#  16     QWORD   OEM table ID
#  24     DWORD   OEM revision
#  28     DWORD   Vendor ID
#  32     DWORD   Creator revision
#  36     DWORD   Physical address of FACS
#  40     DWORD   Physical address of DSDT
#  44     BYTE    Reserved (0)
#  45     BYTE    Preferred PM profile: 1==desktop, 3==workstation, 4==enterprise server
#  46     WORD    System vector for SCI_INT in 8259 mode
#  48     DWORD   SMI command port
#  52     BYTE    Value to write to SMI_CMD to enable OSPM control of ACPI.
#                 SMI sets the SCI_EN bit when finished.
#  53     BYTE    Value to write to SMI_CMD to enable SMI control of ACPI
#  54     BYTE    Value to write to SMI_CMD to enter S4BIOS state.
#                 Zero in S4BIOS_F implies S4BIOS not supported.
#  55     BYTE    Value to write to SMI_CMD to take over processor performance state control
#  56     DWORD   PM1a_evt port
#  60     DWORD   PM1b_evt port (optional)
#  64     DWORD   PM1a_cnt port
#  68     DWORD   PM1b_cnt port (optional)
#  72     DWORD   PM2_cnt port (optional)
#  76     DWORD   PM_TMR port
#  80     DWORD   GPE0_BLK (optional)
#  84     DWORD   GPE1_BLK (optional)
#  88     BYTE    PM1_EVT_LEN (4)
#  89     BYTE    PM1_CTL_LEN (2)
#  90     BYTE    PM2_CTL_LEN (0)
#  91     BYTE    PM_TMR_LEN (4)
#  92     BYTE    GPE0_BLK_LEN (0)
#  93     BYTE    GPE1_BLK_LEN (0)
#  94     BYTE    GPE1_BASE (0)
#  95     BYTE    CST_CNT. Value written to SCI_CMD to indicate OS support for
#                  _CST object and C states changed notification
#  96     WORD    P_LVL2_LAT. Worst case latency to enter C2 (us). >100 -> C2 not supported.
#  98     WORD    P_LVL3_LAT. Worst case latency to enter C3 (us). >1000 -> C3 not supported.
#  100    WORD    Obsolete (0)
#  102    WORD    Obsolete (0)
#  104    BYTE    Duty cycle offset within P_CNT
#  105    BYTE    Duty cycle field width in bits
#  106    BYTE    DAY_ALRM (optional)
#  107    BYTE    MON_ALRM (optional)
#  108    BYTE    CENTURY (optional)
#  109    WORD    Boot flags
#                  bit 0    legacy devices (1)
#                  bit 1    8042 (1)
#                  bit 2-15 reserved (0)
#  111    BYTE    Reserved (0)
#  112    DWORD   Fixed feature flags
#                  bit 0    wbinvd (1)
#                  bit 1    wbinvd_flush (1)
#                  bit 2    proc_c1 (0)
#                  bit 3    p_lvl2_up (1)
#                  bit 4    pwr_button (1)
#                  bit 5    slp_button (1)
#                  bit 6    fix_rtc (1)
#                  bit 7    stc_s4 (0)
#                  bit 8    tmr_val_ext (0)
#                  bit 9    dck_cap (0)
#                  bit 10   reset_reg_sup (0)
#                  bit 11   sealed_case (0)
#                  bit 12   headless (0)
#                  bit 13   cpu_sw_slp (1)
#                  bit 14-31 reserved (0)
#  116    GENA    Reset register (optional)
#  128    BYTE    Reset value (optional)
#  129    3       Reserved (0)
#  132    QWORD   64-bit pa of FACS
#  140    QWORD   64-bit pa of DSDT
#  148    GENA    PM1a_evt port
#  160    GENA    PM1b_evt port (optional)
#  172    GENA    PM1a_cnt port
#  184    GENA    PM1b_cnt port (optional)
#  196    GENA    PM2_cnt port (optional)
#  208    GENA    PM_TMR port
#  220    GENA    GPE0_BLK (optional)
#  232    GENA    GPE1_BLK (optional)
#
def create_fadt(facs_addr, dsdt_addr):
	fadt = create_header("FACP")
	append_dword(fadt, facs_addr)
	append_dword(fadt, dsdt_addr)
	append_byte(fadt, 0)
	append_byte(fadt, 3)
	append_word(fadt, sci_int_vector)
	append_dword(fadt, 0xB2)
	append_byte(fadt, 0xF0)
	append_byte(fadt, 0xF1)
	append_byte(fadt, 0x00)
	append_byte(fadt, 0x00)
	append_dword(fadt, 0x8000)
	append_dword(fadt, 0)
	append_dword(fadt, 0x8004)
	append_dword(fadt, 0)
	append_dword(fadt, 0)
	append_dword(fadt, 0x8008)
	append_dword(fadt, 0x800C)
	append_dword(fadt, 0)
	append_byte(fadt, 4)
	append_byte(fadt, 2)
	append_byte(fadt, 0)
	append_byte(fadt, 4)
	append_byte(fadt, 4)
	append_byte(fadt, 0)
	append_byte(fadt, 0)
	append_byte(fadt, 0)
	append_word(fadt, 0x0A)
	append_word(fadt, 0x14)
	append_word(fadt, 0)
	append_word(fadt, 0)
	append_byte(fadt, 1)
	append_byte(fadt, 0)
	append_byte(fadt, 0)
	append_byte(fadt, 0)
	append_byte(fadt, 0)
	append_word(fadt, 0x0003)
	append_byte(fadt, 0)
	append_dword(fadt, 0x0000207B)
	append_gena_zero(fadt)
	append_byte(fadt, 0)
	append_byte(fadt, 0)
	append_byte(fadt, 0)
	append_byte(fadt, 0)
	append_qword(fadt, facs_addr)
	append_qword(fadt, dsdt_addr)
	append_gena_io(fadt, 0x8000, 16)
	append_gena_zero(fadt)
	append_gena_io(fadt, 0x8004, 16)
	append_gena_zero(fadt)
	append_gena_zero(fadt)
	append_gena_io(fadt, 0x8008, 32)
	append_gena_io(fadt, 0x800C, 32)
	append_gena_zero(fadt)
	if len(fadt) != 244:
		raise Exception("FADT length %d != 244" % len(fadt))
	set_dword(fadt, 4, len(fadt))
	set_byte(fadt, 9, byte_checksum(fadt, 0, len(fadt)))
	return fadt

#
# XSDT 5.2.7
# Offset  Size    Description
#  00     DWORD   "XSDT"
#  04     DWORD   Length
#  08     BYTE    Revision (1)
#  09     BYTE    checksum
#  10     6       OEM ID
#  16     QWORD   OEM table ID (must match FADT)
#  24     DWORD   OEM revision
#  28     DWORD   Vendor ID
#  32     DWORD   Creator revision
#  36     -       64-bit physical addresses of other tables
#
def create_xsdt(table_addresses):
	xsdt = create_header("XSDT")
	for addr in table_addresses:
		append_qword(xsdt, addr)
	if len(xsdt) != (36 + len(table_addresses * 8)):
		raise Exception("XSDT length %d != %d" % (len(xsdt), (36 + len(table_addresses * 8))))
	set_dword(xsdt, 4, len(xsdt))
	set_byte(xsdt, 9, byte_checksum(xsdt, 0, len(xsdt)))
	return xsdt

#
# RSDT 5.2.6
# Offset  Size    Description
#  00     DWORD   "RSDT"
#  04     DWORD   Length
#  08     BYTE    Revision (1)
#  09     BYTE    checksum
#  10     6       OEM ID
#  16     QWORD   OEM table ID (must match FADT)
#  24     DWORD   OEM revision
#  28     DWORD   Vendor ID
#  32     DWORD   Creator revision
#  36     -       Physical addresses of other tables
#
def create_rsdt(table_addresses):
	rsdt = create_header("RSDT")
	for addr in table_addresses:
		append_dword(rsdt, addr)
	if len(rsdt) != (36 + len(table_addresses * 4)):
		raise Exception("RSDT length %d != %d" % (len(rsdt), (36 + len(table_addresses * 4))))
	set_dword(rsdt, 4, len(rsdt))
	set_byte(rsdt, 9, byte_checksum(rsdt, 0, len(rsdt)))
	return rsdt

#
# RSDP 5.2.4.3
# Offset  Size    Description
#  00     QWORD   "RSD PTR "
#  08     BYTE    checksum first 20 bytes
#  09     6       OEM ID
#  15     BYTE    Revision 0==1.0 2==2.0
#  16     DWORD   RSDT address
#  20     DWORD   Length (36)
#  24     QWORD   XSDT address
#  32     BYTE    checksum entire table
#  33     3       reserved
#
def create_rsdp(rsdt_addr, xsdt_addr):
	rsdp = []
	append_string(rsdp, "RSD PTR ")
	append_byte(rsdp, 0)
	append_string(rsdp, oem_id)
	append_byte(rsdp, 2)
	append_dword(rsdp, rsdt_addr)
	append_dword(rsdp, 36)
	append_qword(rsdp, xsdt_addr)
	append_byte(rsdp, 0)
	append_byte(rsdp, 0)
	append_byte(rsdp, 0)
	append_byte(rsdp, 0)
	if len(rsdp) != 36:
		raise Exception("RSDP length %d != 36" % len(rsdp))
	set_byte(rsdp, 8, byte_checksum(rsdp, 0, 20))
	set_byte(rsdp, 32, byte_checksum(rsdp, 0, len(rsdp)))
	return rsdp

#
# MADT 5.2.10.4
# Offset  Size    Description
#  00     DWORD   "APIC"
#  04     DWORD   Length
#  08     BYTE    Revision (1)
#  09     BYTE    checksum
#  10     6       OEM ID
#  16     QWORD   OEM table ID
#  24     DWORD   OEM revision
#  28     DWORD   Vendor ID
#  32     DWORD   Creator revision
#  36     DWORD   APIC address
#  40     DWORD   Flags
#                  bit 0    pcat_compat (1)
#  44     -       APIC tables
#
def create_madt(apic_addr, ioapic_addr):
	madt = create_header("APIC")
	append_dword(madt, apic_addr)
	append_dword(madt, 1)
	if len(madt) != 44:
		raise Exception("MADT length %d != 44" % len(madt))
	apic_tables = create_lapic_tables()
	apic_tables.append(create_ioapic_table(ioapic_addr))
	apic_tables.append(create_interrupt_overrides())
	#apic_tables.append(create_nmi())
	apic_tables.append(create_lapic_nmi())
	for table in apic_tables:
		for b in table:
			madt.append(b)
	set_dword(madt, 4, len(madt))
	set_byte(madt, 9, byte_checksum(madt, 0, len(madt)))
	return madt

#
# LAPIC 5.2.10.5
# Offset  Size    Description
#  00     BYTE    0
#  01     BYTE    Length (8)
#  02     BYTE    Processor ID
#  03     BYTE    APIC ID
#  04     DWORD   Flags
#                  bit 0    enabled (1)
#
# First all physical processors, then all logical processors
#
def create_lapic_tables():
	tables = []
	for logical_only in (0,1):
		for cpu_no in range(max_cpus):
			cpu_obj = SIM_get_object("%s%d" % (cpu_base_name, cpu_no))
			is_logical = SIM_class_has_attribute(cpu_obj.classname, "shared_state") and cpu_obj.shared_state != None
			if (not logical_only and not is_logical) or (logical_only and is_logical):
				table = []
				append_byte(table, 0)
				append_byte(table, 8)
				append_byte(table, cpu_no+1)
				append_byte(table, cpu_no)
				append_dword(table, 1)
				tables.append(table)
	return tables

#
# I/O APIC 5.2.10.6
# Offset  Size    Description
#  00     BYTE    1
#  01     BYTE    Length (12)
#  02     BYTE    I/O APIC ID
#  03     BYTE    Reserved
#  04     DWORD   Address
#  08     DWORD   Interrupt base
#
def create_ioapic_table(ioapic_addr):
	table = []
	append_byte(table, 1)
	append_byte(table, 12)
	append_byte(table, io_apic_id)
	append_byte(table, 0)
	append_dword(table, ioapic_addr)
	append_dword(table, 0)
	return table

#
# Interrupt source overrides 5.2.10.8
# Offset  Size    Description
#  00     BYTE    2
#  01     BYTE    Length (10)
#  02     BYTE    Bus (0)
#  03     BYTE    Source
#  04     DWORD   Interrupt
#  08     WORD    Flags
#                  bit 0-1  polarity (0==default)
#                  bit 2-3  trigger mode (0==default)
#
def create_interrupt_overrides():
	table = []
	append_byte(table, 2)
	append_byte(table, 10)
	append_byte(table, 0)
	append_byte(table, 0) # IRQ0
	append_dword(table, 2) # Interrupt 2
	append_word(table, 0)
	return table

#
# NMIs 5.2.10.9
# Offset  Size    Description
#  00     BYTE    3
#  01     BYTE    Length (8)
#  02     WORD    Flags
#                  bit 0-1  polarity (0==default)
#                  bit 2-3  trigger mode (0==default)
#  04     DWORD   Interrupt
#
def create_nmi():
	table = []
	append_byte(table, 3)
	append_byte(table, 8)
	append_word(table, 0)
	append_dword(table, 9)
	return table

#
# LAPIC NMIs 5.2.10.10
# Offset  Size    Description
#  00     BYTE    4
#  01     BYTE    Length (6)
#  02     BYTE    ACPI processor id
#  03     WORD    Flags
#                  bit 0-1  polarity (0==default)
#                  bit 2-3  trigger mode (0==default)
#  05     BYTE    LINT#
#
def create_lapic_nmi():
	table = []
	append_byte(table, 4)
	append_byte(table, 6)
	append_byte(table, 1)
	append_word(table, 0)
	append_byte(table, 1)
	return table

#
# Memory map
# Offset  Size    Description
#  00     QWORD   Base address
#  08     QWORD   Length
#  10     WORD    Type (1==memory, 2==reserved, 3==reclaim, 4==nvs)
#  12     QWORD   0
#
def create_memory_map(base_addr, length, type):
	table = []
	append_qword(table, base_addr)
	append_qword(table, length)
	append_word(table, type)
	append_qword(table, 0)
	return table

#
# SRAT support
#
#  To create the example SRAT from the specification (but without hot
#  pluggable memory):
#
# srat =
#  create_srat( ((0, 0), # cpu0 on domain 0
#                (1, 0), # cpu1 on domain 0
#                (2, 1), # cpu2 on domain 1
#                (3, 1)),# cpu3 on domain 1
#               ((0, 639*(2<<10), 0),            # 0-639k on domain 0
#                (1*(2L<<20), 1535*(2L<<20), 0), # 1M-1.5G on domain 0
#                (4*(2L<<30), 2*(2L<<30), 0),    # 4G-6G on domain 0
#                (1536*(2L<<20), 1536*(2L<<20), 1), # 1.5G-3G on domain 1
#                (6*(2L<<30), 2*(2L<<30), 1)))   # 6G-8G on domain 1
#
# Then pass this as an additional table to create_acpi_tables.
#

#
# SRAT msft specification
# Offset  Size    Description
#  00     DWORD   "SRAT"
#  04     DWORD   Length
#  08     BYTE    Revision (1)
#  09     BYTE    checksum
#  10     6       OEM ID
#  16     QWORD   OEM table ID
#  24     DWORD   OEM revision
#  28     DWORD   Vendor ID
#  32     DWORD   Creator revision
#  36     DWORD   SRAT revision (1)
#  40     -       SRAT structures
#
def create_srat(cpus, memories):
	srat = create_header("SRAT")
	append_dword(srat, 1) # srat revision
	if len(srat) != 40:
		raise Exception("SRAT length %d != 40" % len(srat))
	print cpus
	print memories
	for cpu in cpus:
		srat = srat + create_processor_affinity_structure(cpu[0], cpu[1])
	for memory in memories:
		srat = srat + create_memory_affinity_structure(memory[0], memory[1], memory[2])
	set_dword(srat, 4, len(srat))
	print srat
	set_byte(srat, 9, byte_checksum(srat, 0, len(srat)))
	return srat

#
# SRAT processor local APIC/SAPIC affinity structure
# Offset  Size    Description
#  00     BYTE    Type (0)
#  01     BYTE    Length (16)
#  02     BYTE    Proximity domain
#  03     BYTE    Local APIC ID
#  04     DWORD   Flags
#                  bit 0     enabled
#                  bit 1..31 reserved
#  08     BYTE    SAPIC EID (0 for x86)
#  09     7       Reserved
#
def create_processor_affinity_structure(apic_id, proximity_domain):
	table = []
	append_byte(table, 0)
	append_byte(table, 16)
	append_byte(table, proximity_domain)
	append_byte(table, apic_id)
	append_dword(table, 1) # enabled
	append_qword(table, 0)
	return table

#
# SRAT memory affinity structure
# Offset  Size    Description
#  00     BYTE    Type (1)
#  01     BYTE    Length (40)
#  02     BYTE    Proximity domain
#  03     5       Reserved
#  08     DWORD   Base address low
#  12     DWORD   Base address high
#  16     DWORD   Length low
#  20     DWORD   Length high
#  24     DWORD   Reserved
#  28     DWORD   Flags
#                  bit 0     enabled
#                  bit 1     hot pluggable
#                  bit 2..31 reserved
#  32     QWORD   Reserved
#
def create_memory_affinity_structure(base_addr, length, proximity_domain):
	table = []
	append_byte(table, 1)
	append_byte(table, 40)
	append_byte(table, proximity_domain)
	append_byte(table, 0)
	append_dword(table, 0)
	append_qword(table, base_addr)
	append_qword(table, length)
	append_dword(table, 0)
	append_dword(table, 1) # enabled, not hot pluggable
	append_qword(table, 0)
	return table

def align_16(addr):
	if ((addr & 0xfffffff0L) == addr):
		return addr
	else:
		return (addr & 0xfffffff0L) + 16

def write_table(table, addr):
	mem = SIM_get_attribute(SIM_get_object(cpu0_name), "physical_memory")
	for val in table:
		if val < 0 or val > 0xff:
			raise Exception("Value %s out of range" % val)
		SIM_set_attribute_idx(mem, "memory", [addr, addr], [val])
		addr = addr + 1

def create_acpi_tables(build_acpi_tables, cpu_base, num_cpus, megs, ioapic_id, user_rsdp_address, additional_tables = ()):
	global io_apic_id, max_cpus, total_megabytes, cpu0_name, cpu_base_name, dsdt_file, add_processors_in_ssdt

	io_apic_id = ioapic_id
	max_cpus = num_cpus
	total_megabytes = megs
	cpu0_name = "%s%d" % (cpu_base, 0)
	cpu_base_name = cpu_base

	if not build_acpi_tables:
		print "ACPI not enabled"

	top_of_memory = megs * 1024L * 1024L
	roof_addr = top_of_memory
	if megs > 4 * 1024 - 256:
		roof_addr = (4 * 1024 - 256) * 1024L * 1024L

	# Make sure that nvr_len + reclaim_len is a multiple of 64k
	nvr_len = 1024
	reclaim_len = 63 * 1024
	nvr_addr = roof_addr - reclaim_len - nvr_len
	reclaim_addr = roof_addr - reclaim_len

	# SMEM is at EBDA:100h
	smem_addr = 639 * 1024 + 0x100

	facs_addr = nvr_addr
	facs = create_facs()
	dsdt_addr = reclaim_addr
	if build_acpi_tables:
		dsdt = create_dsdt(dsdt_file)
		dsdt_checksum = byte_checksum(dsdt, 0, len(dsdt))
		if dsdt_checksum:
			acpi_print("DSDT checksum error (off by 0x%x)" % dsdt_checksum)
		madt_addr = align_16(dsdt_addr + len(dsdt))
	else:
		madt_addr = dsdt_addr
	madt = create_madt(apic_addr, ioapic_addr)
	if add_processors_in_ssdt:
		ssdt_addr = align_16(madt_addr + len(madt))
		ssdt = create_ssdt(max_cpus)
		fadt_addr = align_16(ssdt_addr + len(ssdt))
	else:
		ssdt_addr = 0
		fadt_addr = align_16(madt_addr + len(madt))
	fadt = create_fadt(facs_addr, dsdt_addr)

	table_starts = [fadt_addr, madt_addr]
	tables = [fadt, madt]
	if add_processors_in_ssdt:
		table_starts.append(ssdt_addr)
		tables.append(ssdt)

	# Make room for additional tables
	next_addr = fadt_addr + len(fadt)
	additional_start = next_addr
	for additional_table in additional_tables:
		table_addr = align_16(next_addr)
		table_starts.append(table_addr)
		tables.append(additional_table)
		next_addr = table_addr + len(additional_table)

	rsdt_addr = align_16(next_addr)
	rsdt = create_rsdt(table_starts)
	xsdt_addr = align_16(rsdt_addr + len(rsdt))
	xsdt = create_xsdt(table_starts)

	next_reclaim_addr = xsdt_addr + len(xsdt)
	next_nvr_addr = facs_addr + len(facs)
	rsdp = create_rsdp(rsdt_addr, xsdt_addr)
	nvr = create_memory_map(nvr_addr, nvr_len, 4)

	# Calculate reclaim memory size
	if next_reclaim_addr - reclaim_addr > reclaim_len:
		raise "ACPI reclaim memory pool exhausted"

	# High memory area above 1M
	high_mem_addr = 0x100000

	# Initialize the SMEM data field
	smem = []
	append_dword(smem, total_megabytes * 1024L * 1024L)

	reclaim = create_memory_map(reclaim_addr, reclaim_len, 3)

	high_mem_len = roof_addr - high_mem_addr - reclaim_len - nvr_len

	use_high_mem2 = 0
	# Split high memory range if it would overlap PCI area
	if roof_addr != top_of_memory:
		use_high_mem2 = 1
		high_mem_len2 = total_megabytes*1024L*1024L - high_mem_addr - high_mem_len - reclaim_len - nvr_len
		high_mem2 = create_memory_map(0x100000000L, high_mem_len2, 1)
	high_mem = create_memory_map(high_mem_addr, high_mem_len, 1)
	if build_acpi_tables:
		acpi_print("RSDP at 0x%x len 0x%x" % (rsdp_addr, len(rsdp)))
		acpi_print("RSDT at 0x%x len 0x%x" % (rsdt_addr, len(rsdt)))
		acpi_print("XSDT at 0x%x len 0x%x" % (xsdt_addr, len(xsdt)))
		for i in range(len(tables)):
			table = tables[i]
			table_start = table_starts[i]
			acpi_print("%c%c%c%c at 0x%x len 0x%x" % (table[0], table[1], table[2], table[3], table_start, len(table)))
		acpi_print("FACS at 0x%x len 0x%x" % (facs_addr, len(facs)))
		acpi_print("DSDT at 0x%x len 0x%x" % (dsdt_addr, len(dsdt)))
		acpi_print("SMEM at 0x%x len 0x%x" % (smem_addr, len(smem)))
	acpi_print("NVS memory at 0x%x" % nvr_addr)
	acpi_print("NVS memory size %d (0x%x)" % (nvr_len, nvr_len))
	acpi_print("Free NVS memory %d" % (nvr_len - (next_nvr_addr - nvr_addr)))
	acpi_print("Reclaim memory at 0x%x" % reclaim_addr)
	acpi_print("Reclaim memory size %d (0x%x)" % (reclaim_len, reclaim_len))
	acpi_print("Free reclaim memory %d" % (reclaim_len - (next_reclaim_addr - reclaim_addr)))
	acpi_print("High memory size %d (0x%x)" % (high_mem_len, high_mem_len))
	if use_high_mem2:
		acpi_print("High memory size (above 4GB) %d (0x%x)" % (high_mem_len2, high_mem_len2))
	if build_acpi_tables:
		write_table(facs, facs_addr)
		write_table(dsdt, dsdt_addr)
		write_table(rsdt, rsdt_addr)
		write_table(xsdt, xsdt_addr)
		for i in range(len(tables)):
			table = tables[i]
			table_start = table_starts[i]
			write_table(table, table_start)
		write_table(rsdp, rsdp_addr)
		if user_rsdp_address:
			write_table(rsdp, user_rsdp_address)
		if smem_addr != 0x9fd00:
			print "New SMEM address is 0x%x" % smem_addr
			raise "SMEM address changed, need to rebuild DSDT"
		write_table(smem, smem_addr)
		if ssdt_addr:
			write_table(ssdt, ssdt_addr)
	write_table(high_mem, high_desc_addr)
	write_table(nvr, nvr_desc_addr)
	write_table(reclaim, reclaim_desc_addr)
	if use_high_mem2:
		write_table(high_mem2, high_desc_addr2)
