
##  Copyright 2005-2007 Virtutech AB
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

from string import *
from cli import *
from sim_commands import *

modname = "DS12887-dml"

# Access functions for the NVRAM

def nvram_read(obj, offset):
    return obj.registers_nvram[offset - 14]

def nvram_write(obj, offset, value):
    nvram_values = obj.registers_nvram
    nvram_values[offset - 14] = value
    obj.registers_nvram = nvram_values

# CMOS checksum calculation

def cmos_checksum(obj):
    sum = 0
    for i in range(0x10, 0x2e):
	sum = sum + nvram_read(obj, i)
    nvram_write(obj, 0x2e, (sum >> 8) & 0xff)
    nvram_write(obj, 0x2f, sum & 0xff)

# Optionally convert value to bcd format, depending on the DM bit
def reg_value(obj, value):
    if nvram_read(obj, 11) & 0x4:
        # binary
        return value
    else:
        #bcd
        hi = value / 10
        lo = value - (hi * 10)
        return hi << 4 | lo

#
# -------------------- set-date-time --------------------
#

def set_date_time_cmd(obj, year, month, mday, hour, minute, second, binary, bcd):
    if binary:
        obj.registers_a = obj.registers_a | 0x4
    elif bcd:
        obj.registers_a = obj.registers_a & ~0x4

    try:
        obj.time = "%02d-%02d-%02d %02d:%02d:%02d" % (year % 100, month, mday, hour, minute, second)
    except:
        SIM_command_has_problem()

new_command("set-date-time", set_date_time_cmd,
            [arg(int_t, "year"), arg(int_t, "month"), arg(int_t, "mday"),
             arg(int_t, "hour"), arg(int_t, "minute"), arg(int_t, "second"),
             arg(flag_t, "-binary"), arg(flag_t, "-bcd")],
            alias = "",
            type  = modname + " commands",
            short = "set date and time",
	    namespace = modname,
            doc = """
Set the date and time of the realtime clock. Both month and mday
start counting at one, the other at zero. Year should be in the full
four-digit format. The <cmd>cmos-init</cmd> command must be issued
before this command, unless the simulation was started from a checkpoint.
The <arg>-binary</arg> and <arg>-bcd</arg> flags can be used to
specify the format of the register values. Default is to use BCD, but
some systems use a binary format without checking the binary/BCD status
bit in register B.
""")


#
# -------------------- get-date-time --------------------
#

def get_date_time_cmd(obj):
    print "Time: %s" % obj.time

new_command("get-date-time", get_date_time_cmd,
            [],
            alias = "",
            type  = modname + " commands",
            short = "get date and time",
	    namespace = modname,
            doc = """
Return the date and time of the realtime clock.<br/>
""")


#
# -------------------- cmos-init --------------------
#

def cmos_init_cmd(obj):
    # shutdown status, 0 normal startup
    nvram_write(obj, 0x0f, 0x00)

    # equipment byte.
    # bit 6-7, number of disk drives, (set later)
    # bit 4-5, video: 0 - vga
    # bit 2,   unused (set to 1 in Boch bios)
    # bit 1,   math coprocessor
    # bit 0,   disk drive installed for boot
    nvram_write(obj, 0x14, 0x07)

    # base memory in kB, always 640
    nvram_write(obj, 0x15, 640 & 0xff)
    nvram_write(obj, 0x16, (640 >> 8) & 0xff)

    # system flags:
    # bit 5 - boot A: first, then C:  - A is default
    nvram_write(obj, 0x2d, 0x20)

    # default century
    cmos_century_cmd(obj, 20)

    cmos_checksum(obj)

new_command("cmos-init", cmos_init_cmd,
	    [],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-init or <x86-apic-system>.cmos-init",
            short = "initialize some CMOS values",
	    namespace = modname)


#
# -------------------- cmos-base-mem --------------------
#

def cmos_base_mem_cmd(obj, size):
    if size > 640:
	print "Larger than maximal value (640 kB), setting max."
	size = 640

    # store size in kB
    nvram_write(obj, 0x15, size & 0xff)
    nvram_write(obj, 0x16, (size >> 8) & 0xff)
    cmos_checksum(obj)

new_command("cmos-base-mem", cmos_base_mem_cmd,
            [arg(int_t, "kilobytes")], # <b>cmod-base-mem</b> <i>size_in_kB</i>
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-base-mem or <x86-apic-system>.cmos-base-mem",
	    short = "set base memory size",
	    namespace = modname)


#
# -------------------- cmos-extended-mem --------------------
#

def cmos_extended_mem_cmd(obj, size):
    # store size in kB, saturate to 0xffff
    size_in_k = size * 1024L
    if size_in_k > 0xffff:
        size_in_k = 0xffff
    nvram_write(obj, 0x17, size_in_k & 0xff)
    nvram_write(obj, 0x18, (size_in_k >> 8) & 0xff)
    nvram_write(obj, 0x30, size_in_k & 0xff)
    nvram_write(obj, 0x31, (size_in_k >> 8) & 0xff)
    cmos_checksum(obj)

new_command("cmos-extended-mem", cmos_extended_mem_cmd,
            [arg(int_t, "megabytes")], # <b>cmod-extended-mem</b> <i>size_in_MB</i>
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-extended-mem or <x86-apic-system>.cmos-extended-mem",
	    short = "set extended memory size",
	    namespace = modname)


#
# -------------------- cmos-floppy --------------------
#

disk_types = ["none", "360", "720", "1.2", "1.44", "2.88", "320" ]

def type_expand(string):
    return get_completions(string, disk_types)

def cmos_floppy_cmd(obj, drive, drive_type):
    drive = upper(drive)
    if (drive != "A") and (drive != "B"):
	print "Only drive A and B supported"
	return
    try:
	type_num = disk_types.index(drive_type)
    except:
	print "Unknown disk type"
	print "Try one of:"
	print disk_types
        SIM_command_has_problem()
	return

    # high nibble drive 0, low drive 1
    val = nvram_read(obj, 0x10)
    if drive == "A":
	val = (type_num << 4) | (val & 0x0f)
    else:
	val = type_num | (val & 0xf0)
    nvram_write(obj, 0x10, val)

    drives = 0
    if val & 0xf0:
	drives = 1
    if val & 0x0f:
	drives = drives + 1

    # equipment byte: bit 6-7, number of disk drives
    val = (drives << 6) | (nvram_read(obj, 0x14) & 0x3f)
    nvram_write(obj, 0x14, val)
    cmos_checksum(obj)


new_command("cmos-floppy", cmos_floppy_cmd,
            [arg(str_t, "drive"), arg(str_t, "type", expander=type_expand)],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-floppy or <x86-apic-system>.cmos-floppy",
            short = "set floppy parameters",
	    namespace = modname)

#
# -------------------- cmos-hd --------------------
#

hd_regs = ( (0x19, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x21, 0x22, 0x23),
            (0x1a, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c) )

def cmos_hd_cmd(obj, drive, cylinders, heads, sectors_per_track):
    drive = upper(drive)
    if (drive != "C") and (drive != "D"):
	print "Only drive C and D supported"
	return
    drive_val = 0xf
    if (cylinders == 0) or (heads == 0) or (sectors_per_track == 0):
        if SIM_get_verbose():
	    print "[%s] No drive set on: %s" % (obj.name, drive)
	drive_val = 0x0
	cylinders = 0
	heads = 0
	sector_per_track = 0

    # Type of hard drive. High nibble drive 0, low nibble drive 1
    # Values: 0x0 - no drive,
    #         0x1 -> 0xe - different type numbers
    #         0xf - read in reg 0x19 instead (0x1a for drive 1).
    val = nvram_read(obj, 0x12)
    if drive == "C":
	val = (drive_val << 4) | (val & 0x0f)
	drive_num = 0
    else:
	val = (drive_val) | (val & 0xf0)
	drive_num = 1
    nvram_write(obj, 0x12, val)

    # HD <drive> type, use 47
    if drive_val == 0:
	nvram_write(obj, hd_regs[drive_num][0], 0x0)
    else:
	nvram_write(obj, hd_regs[drive_num][0], 0x2f)

    # low and high cylinder word (number of cyls)
    nvram_write(obj, hd_regs[drive_num][1], cylinders & 0xff)
    nvram_write(obj, hd_regs[drive_num][2], (cylinders >> 8) & 0xff)
    # number of heads
    nvram_write(obj, hd_regs[drive_num][3], heads)

    # low precomp cylinder, obsolete set to 0
    nvram_write(obj, hd_regs[drive_num][4], 0x00)
    nvram_write(obj, hd_regs[drive_num][5], 0x00)

    # drive control,
    # bit 6, 7 == 0
    # bit 5 - bad map at last cyl + 1, (not used)
    # bit 3 - more that 8 heads
    val = 0x00
    if heads > 8:
	val = val | 0x08
    nvram_write(obj, hd_regs[drive_num][6], val)

    # low and high landing zone cyl, obsolete set to max cylinder + 1
    nvram_write(obj, hd_regs[drive_num][7], cylinders & 0xff)
    nvram_write(obj, hd_regs[drive_num][8], (cylinders >> 8) & 0xff)

    # sectors per track
    nvram_write(obj, hd_regs[drive_num][9], sectors_per_track)
    cmos_checksum(obj)

new_command("cmos-hd", cmos_hd_cmd,
            [arg(str_t, "drive"), arg(int_t, "cylinders"), arg(int_t, "heads"), arg(int_t, "sectors_per_track")],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-hd or <x86-apic-system>.cmos-hd",
            short = "set fixed disk paramters",
	    namespace = modname)

#
# -------------------- cmos-boot-dev --------------------
#

def cmos_boot_dev_cmd(obj, drive):
    drive = upper(drive)
    if drive == "A":
	nvram_write(obj, 0x2d, 0x20)
    elif drive == "C":
	nvram_write(obj, 0x2d, 0x00)
    else:
	print "Only drive A and C supported as boot devices"
	return
    cmos_checksum(obj)


new_command("cmos-boot-dev", cmos_boot_dev_cmd,
            [arg(str_t, "drive")], # <b>cmos-boot-dev</b> A|C
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-boot-dev or <x86-apic-system>.cmos-boot-dev",
            short = "set boot drive",
	    namespace = modname)

#
# -------------------- cmos-century --------------------
#

def cmos_century_cmd(obj, century):
    return

new_command("cmos-century", cmos_century_cmd,
            [arg(int_t, "century")],
            type  = "deprecated commands",
            deprecated = "<" + modname + ">.set-date-time",
            short = "set date century",
	    namespace = modname)

#
# -------------------- cmos-info -----------------------
#

def cmos_info_cmd(obj):
    print
    print "    Base memory    : %5d kB" % ((nvram_read(obj, 0x16) << 8) | nvram_read(obj, 0x15))
    print "Extended memory (1): %5d kB" % ((nvram_read(obj, 0x18) << 8) | nvram_read(obj, 0x17))
    print "Extended memory (2): %5d kB" % ((nvram_read(obj, 0x31) << 8) | nvram_read(obj, 0x30))
    print
    print "  Num floppy drives: %d" % ((nvram_read(obj, 0x14) >> 6) & 0x3)
    try:
        atype = disk_types[nvram_read(obj, 0x10) >> 4]
    except:
        atype = "Unknown"
    try:
        btype = disk_types[nvram_read(obj, 0x10) & 0xf]
    except:
        btype = "Unknown"
    print "            A: type: %s" % atype
    print "            B: type: %s" % btype
    print
    drvtype = []
    drvname = ["C", "D"]
    drvtype.append(nvram_read(obj, 0x12) >> 4)
    drvtype.append(nvram_read(obj, 0x12) & 0xf)
    for drv in range(0, 2):
        if drvtype[drv] == 0x0:
            print "     %s: Drive type : No disk" % drvname[drv]
        elif drvtype[drv] != 0xf:
            print "     %s: Drive type : 0x%02x (obsolete)" % (drvname[drv], drvtype[drv])
        else:
            print "     %s: Drive type : 0x%02x" % (drvname[drv], nvram_read(obj, hd_regs[drv][0]))
            print "         Cylinders : %4d" % ((nvram_read(obj, hd_regs[drv][2]) << 8) | nvram_read(obj, hd_regs[drv][1]))
            print "             Heads : %4d" % nvram_read(obj, hd_regs[drv][3])
            print " Sectors per track : %4d" % nvram_read(obj, hd_regs[drv][9])
            print
    print
    if nvram_read(obj, 0x2d) == 0x20:
        boot_dev = "A"
    elif nvram_read(obj, 0x2d) == 0x00:
        boot_dev = "C"
    else:
        boot_dev = "Unknown"
    print "        Boot device: %s" % boot_dev
    print

new_command("cmos-info", cmos_info_cmd,
            [],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-info or <x86-apic-system>.cmos-info",
            short = "print information about the CMOS area",
            namespace = modname)

#
# ------------------------ info -----------------------
#

def get_info(obj):
        return [ (None,
                  [ ("IRQ device", obj.irq_dev),
                    ("IRQ number", obj.irq_level) ]) ]

new_info_command(modname, get_info)

def get_status(obj):
    try:
        irq_dev  = obj.irq_dev
        irq_lvl  = obj.irq_level
        rega = obj.registers_a
        regb = obj.registers_b
        regc = obj.registers_c
        regd = obj.registers_d
        frequencies = [0, 256, 128, 8192, 4096, 2048, 1024, 512, 256, 128, 64, 32, 16, 8, 4, 2]
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return []

    return [ (None,
              [ ("Register A", "0x%02x" % rega),
                ("UIP", "%d" % iff(rega & 0x80, 1, 0)),
                ("DV", (rega >> 4) & 0x07),
                ("RS", "%d => %d Hz" % (rega & 0x0f, frequencies[rega & 0x0f])),
                ("Register B", "0x%02x" % regb),
                ("SET", iff(regb & 0x80, 1, 0)),
                ("PIE", iff(regb & 0x40, 1, 0)),
                ("AIE", iff(regb & 0x20, 1, 0)),
                ("UIA", iff(regb & 0x10, 1, 0)),
                ("SQWE", iff(regb & 0x08, 1, 0)),
                ("DM", iff(regb & 0x04, 1, 0)),
                ("12/24", iff(regb & 0x02, 1, 0)),
                ("DSE", iff(regb & 0x01, 1, 0)),
                # note, the C registers may not be updated in case of polling
                ("Register C", "0x%02x" % regc),
                ("IRQF", iff(regc & 0x80, 1, 0)),
                ("PF", iff(regc & 0x40, 1, 0)),
                ("AF", iff(regc & 0x20, 1, 0)),
                ("UF", iff(regc & 0x10, 1, 0)),
                ("Register D", "0x%02x" % regd),
                ("VRT", iff(regd & 0x80, 1, 0)) ]),
             ("Date and Time Registers",
              [ ("Sec", "0x%02x" % obj.registers_seconds),
                ("Min", "0x%02x" % obj.registers_minutes),
                ("Hour", "0x%02x" % obj.registers_hours),
                ("Day", "0x%02x" % obj.registers_day_of_the_week),
                ("Date", "0x%02x" % obj.registers_date_of_the_month),
                ("Month", "0x%02x" % obj.registers_month),
                ("Year", "0x%02x" % obj.registers_year) ]),
             ("Alarm Registers",
              [ ("Sec", "0x%02x" % obj.registers_seconds_alarm),
                ("Min", "0x%02x" % obj.registers_minutes_alarm),
                ("Hour", "0x%02x" % obj.registers_hours_alarm) ])]

new_status_command(modname, get_status)
