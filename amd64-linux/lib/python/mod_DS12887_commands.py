
##  Copyright 2000-2007 Virtutech AB
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

# shared source
modname = get_last_loaded_module()
if modname == "DS17845":
    modname = "DS17485"

def cmos_checksum(obj):
    sum = 0
    for i in range(0x10, 0x2e):
	sum = sum + obj.nvram[i]
    # write checksum
    obj.nvram[0x2e] = (sum >> 8) & 0xff
    obj.nvram[0x2f] = sum & 0xff

def reg_value(obj, value):
    if obj.nvram[11] & 0x4:
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
    if year < 1990 or year >= 2038:
        print "Year %d out of range." % year
        return
    if month <= 0 or month > 12:
        print "Month %d out of range [1, 12]." % month
        return
    if mday <= 0 or mday > 31:
        print "Mday %d out of range." % mday
        return
    if hour < 0 or hour >= 24:
        print "Hour %d out of range [0, 23]." % hour
        return
    if minute < 0 or minute >= 60:
        print "Minute %d out of range [0, 59]." % minute
        return
    if second < 0 or second >= 60:
        print "Second %d out of range [0, 59]." % second
        return

    if binary:
        obj.nvram[11] = obj.nvram[11] | 4
    elif bcd:
        obj.nvram[11] = obj.nvram[11] & ~0x4

    if modname == "DS17485":
        # For DS17485 only, has a dedicated register for century
        obj.nvram_bank1[0x48 - 0x40] = year / 100
    else:
        # TODO: only update CMOS checksum after changing century on x86?
        cmos_century_cmd(obj, year / 100)

    try:
	obj.year = year
	obj.month = month
	obj.mday = mday
	obj.hour = hour
	obj.minute = minute
	obj.second = second
    except Exception, y:
	print "Error setting time in " + modname + " device: %s" % y
        SIM_command_has_problem()

new_command("set-date-time", set_date_time_cmd,
            [arg(int_t, "year"), arg(int_t, "month"), arg(int_t, "mday"),
             arg(int_t, "hour"), arg(int_t, "minute"), arg(int_t, "second"),
             arg(flag_t, "-binary"), arg(flag_t, "-bcd")],
            type  = modname + " commands",
            short = "set date and time",
	    namespace = modname,
            doc = """
Set the date and time of the real-time clock. Both month and mday
start counting at one, the other at zero. Year should be in the full
four-digit format. The <cmd>cmos-init</cmd> command must be issued
before this command, unless the simulation was started from a checkpoint.
The <arg>-binary</arg> and <arg>-bcd</arg> flags can be used to
specify the format of the register values. Default is to use BCD, but
some systems use a binary format without checking the binary/BCD status
bit in register B.
""", filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="95")



#
# -------------------- get-date-time --------------------
#

def get_date_time_cmd(obj):
    print "Time: %04d-%02d-%02d %02d:%02d:%02d" % (
        obj.year, obj.month,obj.mday,
        obj.hour, obj.minute, obj.second)

new_command("get-date-time", get_date_time_cmd,
            [],
            type  = modname + " commands",
            short = "get date and time",
	    namespace = modname,
            doc = """
Return the date and time of the real-time clock.<br/>
""", filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="124")


#
# -------------------- cmos-init --------------------
#

def cmos_init_cmd(obj):
    # shutdown status, 0 normal startup
    obj.nvram[0x0f] = 0x00

    # equipment byte.
    # bit 6-7, number of disk drives, (set later)
    # bit 4-5, video: 0 - vga
    # bit 2,   unused (set to 1 in Boch bios)
    # bit 1,   math coprocessor
    # bit 0,   disk drive installed for boot
    obj.nvram[0x14] = 0x07

    # base memory in kB, always 640
    obj.nvram[0x15] = 640 & 0xff
    obj.nvram[0x16] = (640 >> 8) & 0xff

    # system flags:
    # bit 5 - boot A: first, then C:  - A is default
    obj.nvram[0x2d] = 0x20

    # default century
    cmos_century_cmd(obj, 20)

    cmos_checksum(obj)

new_command("cmos-init", cmos_init_cmd,
	    [],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-init",
            short = "initialize some CMOS values",
	    namespace = modname, filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="163")

#
# -------------------- cmos-base-mem --------------------
#

def cmos_base_mem_cmd(obj, size):
    if size > 640:
	print "Larger than maximal value (640 kB), setting max."
	size = 640

    # store size in kB
    obj.nvram[0x15] = size & 0xff
    obj.nvram[0x16] = (size >> 8) & 0xff
    cmos_checksum(obj)

new_command("cmos-base-mem", cmos_base_mem_cmd,
            [arg(int_t, "kilobytes")],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-base-mem",
	    short = "set base memory size",
	    namespace = modname, filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="184")

#
# -------------------- cmos-extended-mem --------------------
#

def cmos_extended_mem_cmd(obj, size):
    # store size in kB, saturate to 0xffff
    size_in_k = size * 1024L
    if size_in_k > 0xffff:
        size_in_k = 0xffff
    obj.nvram[0x17] = size_in_k & 0xff
    obj.nvram[0x18] = (size_in_k >> 8) & 0xff
    obj.nvram[0x30] = size_in_k & 0xff
    obj.nvram[0x31] = (size_in_k >> 8) & 0xff
    cmos_checksum(obj)

new_command("cmos-extended-mem", cmos_extended_mem_cmd,
            [arg(int_t, "megabytes")],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-extended-mem",
	    short = "set extended memory size",
	    namespace = modname, filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="206")


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
    val = SIM_get_attribute_idx(obj, "nvram", 0x10)
    if drive == "A":
	val = (type_num << 4) | (val & 0x0f)
    else:
	val = type_num | (val & 0xf0)
    obj.nvram[0x10] = val

    drives = 0
    if val & 0xf0:
	drives = 1
    if val & 0x0f:
	drives = drives + 1

    # equipment byte: bit 6-7, number of disk drives
    val = (drives << 6) | (SIM_get_attribute_idx(obj, "nvram", 0x14) & 0x3f)
    obj.nvram[0x14] = val
    cmos_checksum(obj)


new_command("cmos-floppy", cmos_floppy_cmd,
            [arg(str_t, "drive"), arg(str_t, "type", expander=type_expand)],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-floppy",
            short = "set floppy parameters",
	    namespace = modname, filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="257")

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
    val = SIM_get_attribute_idx(obj, "nvram", 0x12)
    if drive == "C":
	val = (drive_val << 4) | (val & 0x0f)
	drive_num = 0
    else:
	val = (drive_val) | (val & 0xf0)
	drive_num = 1
    obj.nvram[0x12] = val

    # HD <drive> type, use 47
    if drive_val == 0:
	obj.nvram[hd_regs[drive_num][0]] = 0x0
    else:
	obj.nvram[hd_regs[drive_num][0]] = 0x2f

    # low and high cylinder word (number of cyls)
    obj.nvram[hd_regs[drive_num][1]] = cylinders & 0xff
    obj.nvram[hd_regs[drive_num][2]] = (cylinders >> 8) & 0xff
    # number of heads
    obj.nvram[hd_regs[drive_num][3]] = heads

    # low precomp cylinder, obsolete set to 0
    obj.nvram[hd_regs[drive_num][4]] = 0x00
    obj.nvram[hd_regs[drive_num][5]] = 0x00

    # drive control,
    # bit 6, 7 == 0
    # bit 5 - bad map at last cyl + 1, (not used)
    # bit 3 - more that 8 heads
    val = 0x00
    if heads > 8:
	val = val | 0x08
    obj.nvram[hd_regs[drive_num][6]] = val

    # low and high landing zone cyl, obsolete set to max cylinder + 1
    obj.nvram[hd_regs[drive_num][7]] = cylinders & 0xff
    obj.nvram[hd_regs[drive_num][8]] = (cylinders >> 8) & 0xff

    # sectors per track
    obj.nvram[hd_regs[drive_num][9]] = sectors_per_track
    cmos_checksum(obj)

new_command("cmos-hd", cmos_hd_cmd,
            [arg(str_t, "drive"), arg(int_t, "cylinders"),
             arg(int_t, "heads"), arg(int_t, "sectors_per_track")],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-hd",
            short = "set fixed disk parameters",
	    namespace = modname, filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="331")

#
# -------------------- cmos-boot-dev --------------------
#

def cmos_boot_dev_cmd(obj, drive):
    drive = upper(drive)
    if drive == "A":
	obj.nvram[0x2d] = 0x20
    elif drive == "C":
	obj.nvram[0x2d] = 0x00
    else:
	print "Only drive A and C supported as boot devices"
	return
    cmos_checksum(obj)


new_command("cmos-boot-dev", cmos_boot_dev_cmd,
            [arg(str_t, "drive")], # <b>cmos-boot-dev</b> A|C
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-boot-dev",
            short = "set boot drive",
	    namespace = modname, filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="355")

#
# -------------------- cmos-century --------------------
#

def cmos_century_cmd(obj, century):
    if (century < 19) or (century > 30):
	print "Invalid century specified."
	return
    obj.nvram[0x32] = reg_value(obj, century)
    cmos_checksum(obj)
    if modname == "DS17485":
        # For DS17485 only, has a dedicated register for century
        obj.nvram_bank1[0x48 - 0x40] = century

new_command("cmos-century", cmos_century_cmd,
            [arg(int_t, "century")],
            type  = "deprecated commands",
            deprecated = "<" + modname + ">.set-date-time",
            short = "set date century",
	    namespace = modname, filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="376")

#
# -------------------- cmos-info -----------------------
#

def cmos_info_cmd(obj):
    print
    print "    Base memory    : %5d kB" % ((obj.nvram[0x16] << 8) | obj.nvram[0x15])
    print "Extended memory (1): %5d kB" % ((obj.nvram[0x18] << 8) | obj.nvram[0x17])
    print "Extended memory (2): %5d kB" % ((obj.nvram[0x31] << 8) | obj.nvram[0x30])
    print
    print "  Num floppy drives: %d" % ((obj.nvram[0x14] >> 6) & 0x3)
    try:
        atype = disk_types[obj.nvram[0x10] >> 4]
    except:
        atype = "Unknown"
    try:
        btype = disk_types[obj.nvram[0x10] & 0xf]
    except:
        btype = "Unknown"
    print "            A: type: %s" % atype
    print "            B: type: %s" % btype
    print
    drvtype = []
    drvname = ["C", "D"]
    drvtype.append(obj.nvram[0x12] >> 4)
    drvtype.append(obj.nvram[0x12] & 0xf)
    for drv in range(0, 2):
        if drvtype[drv] == 0x0:
            print "     %s: Drive type : No disk" % drvname[drv]
        elif drvtype[drv] != 0xf:
            print "     %s: Drive type : 0x%02x (obsolete)" % (drvname[drv], drvtype[drv])
        else:
            print "     %s: Drive type : 0x%02x" % (drvname[drv], obj.nvram[hd_regs[drv][0]])
            print "         Cylinders : %4d" % ((obj.nvram[hd_regs[drv][2]] << 8) | obj.nvram[hd_regs[drv][1]])
            print "             Heads : %4d" % obj.nvram[hd_regs[drv][3]]
            print " Sectors per track : %4d" % obj.nvram[hd_regs[drv][9]]
            print
    print
    if obj.nvram[0x2d] == 0x20:
        boot_dev = "A"
    elif obj.nvram[0x2d] == 0x00:
        boot_dev = "C"
    else:
        boot_dev = "Unknown"
    print "        Boot device: %s" % boot_dev
    print

new_command("cmos-info", cmos_info_cmd,
            [],
            type  = "deprecated commands",
            deprecated = "<x86-system>.cmos-info",
            short = "print information about the CMOS area",
            namespace = modname, filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="430")

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
        rega = obj.nvram[10]
        regb = obj.nvram[11]
        regc = obj.nvram[12]
        regd = obj.nvram[13]
        rsus = obj.period_in_us
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return []

    return [ (None,
              [ ("Register A", "0x%x" % rega),
                ("UIP", "%d" % iff(rega & 0x80, 1, 0)),
                ("DV", (rega >> 4) & 7),
                ("RS", "%d => %d us" % (rega & 0x0f, rsus[rega & 0x0f])),
                ("Register B", "0x%x" % regb),
                ("SET", iff(regb & 0x80, 1, 0)),
                ("PIE", iff(regb & 0x40, 1, 0)),
                ("AIE", iff(regb & 0x20, 1, 0)),
                ("UIA", iff(regb & 0x10, 1, 0)),
                ("SQWE", iff(regb & 0x08, 1, 0)),
                ("DM", iff(regb & 0x04, 1, 0)),
                ("12/24", iff(regb & 0x02, 1, 0)),
                ("DSE", iff(regb & 0x01, 1, 0)),
                # note, the C registers may not be updated in case of polling
                ("Register C", "0x%x" % regc),
                ("IRQF", iff(regc & 0x80, 1, 0)),
                ("PF", iff(regc & 0x40, 1, 0)),
                ("AF", iff(regc & 0x20, 1, 0)),
                ("UF", iff(regc & 0x10, 1, 0)),
                ("Register D", "0x%x" % regd),
                ("VRT", iff(regd & 0x80, 1, 0)) ]),
             ("Date and Time Registers",
              [ ("Sec", "0x%02x" % obj.nvram[0]),
                ("Min", "0x%02x" % obj.nvram[2]),
                ("Hour", "0x%02x" % obj.nvram[4]),
                ("Day", "0x%02x" % obj.nvram[6]),
                ("Date", "0x%02x" % obj.nvram[7]),
                ("Month", "0x%02x" % obj.nvram[8]),
                ("Year", "0x%02x" % obj.nvram[9]) ]),
             ("Alarm Registers",
              [ ("Sec", "0x%02x" % obj.nvram[1]),
                ("Min", "0x%02x" % obj.nvram[3]),
                ("Hour", "0x%02x" % obj.nvram[5]) ])]

new_status_command(modname, get_status)

def nvram_update_hap_handler(arg, obj, index, old_value, new_value):
    count = SIM_step_count(SIM_current_processor())
    print "%s [%d]=%s (old value %s)" % (count, index, new_value, old_value)

def trace_nvram_cmd(obj):
    SIM_hap_add_callback("RTC_Nvram_Update", nvram_update_hap_handler, obj)

new_command("trace-nvram", trace_nvram_cmd,
            [],
            type  = modname + " commands",
            short = "trace nvram updates",
            namespace = modname,
            doc = """
Trace all nvram updates.<br/>
""", filename="/mp/simics-3.0/src/devices/DS12887/commands.py", linenumber="505")
