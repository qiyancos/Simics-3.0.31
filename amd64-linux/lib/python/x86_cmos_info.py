import string
from cli import *
from components import get_component

# Access functions for the NVRAM

def nvram_read(rtc, offset):
    if rtc.classname in ["DS12887", "DS17485", "M5823"]:
        return rtc.nvram[offset]
    elif rtc.classname in ["DS12887-dml"]:
        return rtc.registers_nvram[offset - 14]
    else:
        print "Unknown real-time clock class: %s" % rtc.classname

def nvram_write(rtc, offset, value):
    if rtc.classname in ["DS12887", "M5823"]:
        rtc.nvram[offset] = value
    elif rtc.classname == "DS12887-dml":
        nvram_values = rtc.registers_nvram
        nvram_values[offset - 14] = value
        rtc.registers_nvram = nvram_values
    else:
        print "Unknown real-time clock class: %s" % rtc.classname

# CMOS checksum calculation

def cmos_checksum(rtc):
    sum = 0
    for i in range(0x10, 0x2e):
	sum = sum + nvram_read(rtc, i)
    # write checksum
    nvram_write(rtc, 0x2e, (sum >> 8) & 0xff)
    nvram_write(rtc, 0x2f, sum & 0xff)

# Conditionally convert value to bcd format, depending on the DM bit

def reg_value(rtc, value):
    if nvram_read(rtc, 11) & 0x4:
        # binary
        return value
    else:
        #bcd
        hi = value / 10
        lo = value - (hi * 10)
        return hi << 4 | lo

#
# -------------------- cmos-init --------------------
#

def cmos_init_cmd(obj):
    rtc = get_component(obj).rtc

    # shutdown status, 0 normal startup
    nvram_write(rtc, 0x0f, 0x00)

    # equipment byte.
    # bit 6-7, number of disk drives, (set later)
    # bit 4-5, video: 0 - vga
    # bit 2,   unused
    # bit 1,   math coprocessor
    # bit 0,   disk drive installed for boot
    nvram_write(rtc, 0x14, 0x07)

    # base memory in kB, always 640
    nvram_write(rtc, 0x15, 640 & 0xff)
    nvram_write(rtc, 0x16, (640 >> 8) & 0xff)

    # system flags:
    # bit 5 - boot A: first, then C:  - A is default
    nvram_write(rtc, 0x2d, 0x20)

    # default century
    cmos_century(rtc, 20)
    cmos_checksum(rtc)

#
# -------------------- cmos-base-mem --------------------
#

def cmos_base_mem_cmd(obj, size):
    rtc = get_component(obj).rtc
    if size > 640:
	print "Larger than maximal value (640 kB), setting max."
	size = 640

    # store size in kB
    nvram_write(rtc, 0x15, size & 0xff)
    nvram_write(rtc, 0x16, (size >> 8) & 0xff)
    cmos_checksum(rtc)

#
# -------------------- cmos-extended-mem --------------------
#

def cmos_extended_mem_cmd(obj, size):
    rtc = get_component(obj).rtc
    # store size in kB, saturate to 0xffff
    size_in_k = size * 1024
    if size_in_k > 0xffff:
        size_in_k = 0xffff
    nvram_write(rtc, 0x17, size_in_k & 0xff)
    nvram_write(rtc, 0x18, (size_in_k >> 8) & 0xff)
    nvram_write(rtc, 0x30, size_in_k & 0xff)
    nvram_write(rtc, 0x31, (size_in_k >> 8) & 0xff)
    cmos_checksum(rtc)

#
# -------------------- cmos-floppy --------------------
#

disk_types = ["none", "360", "720", "1.2", "1.44", "2.88", "320" ]

def type_expand(string):
    return get_completions(string, disk_types)

def cmos_floppy_cmd(obj, drive, drive_type):
    rtc = get_component(obj).rtc
    drive = string.upper(drive)
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
    val = nvram_read(rtc, 0x10)
    if drive == "A":
	val = (type_num << 4) | (val & 0x0f)
    else:
	val = type_num | (val & 0xf0)
    nvram_write(rtc, 0x10, val)

    drives = 0
    if val & 0xf0:
	drives = 1
    if val & 0x0f:
	drives = drives + 1

    # equipment byte: bit 6-7, number of disk drives
    val = (drives << 6) | (nvram_read(rtc, 0x14) & 0x3f)
    nvram_write(rtc, 0x14, val)
    cmos_checksum(rtc)


#
# -------------------- cmos-hd --------------------
#

hd_regs = ( (0x19, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x21, 0x22, 0x23),
            (0x1a, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c) )

def cmos_hd_cmd(obj, drive, cylinders, heads, sectors_per_track):
    rtc = get_component(obj).rtc
    drive = string.upper(drive)
    if (drive != "C") and (drive != "D"):
	print "Only drive C and D supported"
	return
    drive_val = 0xf
    if (cylinders == 0) or (heads == 0) or (sectors_per_track == 0):
        if SIM_get_verbose():
	    print "[%s] No drive set on: %s" % (rtc.name, drive)
	drive_val = 0x0
	cylinders = 0
	heads = 0
	sector_per_track = 0

    # Type of hard drive. High nibble drive 0, low nibble drive 1
    # Values: 0x0 - no drive,
    #         0x1 -> 0xe - different type numbers
    #         0xf - read in reg 0x19 instead (0x1a for drive 1).
    val = nvram_read(rtc, 0x12)
    if drive == "C":
	val = (drive_val << 4) | (val & 0x0f)
	drive_num = 0
    else:
	val = (drive_val) | (val & 0xf0)
	drive_num = 1
    nvram_write(rtc, 0x12, val)

    # HD <drive> type, use 47
    if drive_val == 0:
	nvram_write(rtc, hd_regs[drive_num][0], 0x0)
    else:
	nvram_write(rtc, hd_regs[drive_num][0], 0x2f)

    # low and high cylinder word (number of cyls)
    nvram_write(rtc, hd_regs[drive_num][1], cylinders & 0xff)
    nvram_write(rtc, hd_regs[drive_num][2], (cylinders >> 8) & 0xff)
    # number of heads
    nvram_write(rtc, hd_regs[drive_num][3], heads)

    # low precomp cylinder, obsolete set to 0
    nvram_write(rtc, hd_regs[drive_num][4], 0x00)
    nvram_write(rtc, hd_regs[drive_num][5], 0x00)

    # drive control,
    # bit 6, 7 == 0
    # bit 5 - bad map at last cyl + 1, (not used)
    # bit 3 - more that 8 heads
    val = 0x00
    if heads > 8:
	val = val | 0x08
    nvram_write(rtc, hd_regs[drive_num][6], val)

    # low and high landing zone cyl, obsolete set to max cylinder + 1
    nvram_write(rtc, hd_regs[drive_num][7], cylinders & 0xff)
    nvram_write(rtc, hd_regs[drive_num][8], (cylinders >> 8) & 0xff)

    # sectors per track
    nvram_write(rtc, hd_regs[drive_num][9], sectors_per_track)
    cmos_checksum(rtc)

#
# -------------------- cmos-boot-dev --------------------
#

def cmos_boot_dev_cmd(obj, drive):
    rtc = get_component(obj).rtc
    drive = string.upper(drive)
    if drive == "A":
	nvram_write(rtc, 0x2d, 0x20)
    elif drive == "C":
	nvram_write(rtc, 0x2d, 0x00)
    else:
	print "Only drive A and C supported as boot devices"
	return
    cmos_checksum(rtc)


#
# -------------------- cmos-century --------------------
#

def cmos_century(rtc, century):
    nvram_write(rtc, 0x32, reg_value(rtc, century))
    cmos_checksum(rtc)

#
# -------------------- cmos-info -----------------------
#

def cmos_info_cmd(obj):
    rtc = get_component(obj).rtc
    print
    print "    Base memory    : %5d kB" % ((nvram_read(rtc, 0x16) << 8) | nvram_read(rtc, 0x15))
    print "Extended memory (1): %5d kB" % ((nvram_read(rtc, 0x18) << 8) | nvram_read(rtc, 0x17))
    print "Extended memory (2): %5d kB" % ((nvram_read(rtc, 0x31) << 8) | nvram_read(rtc, 0x30))
    print
    print "  Num floppy drives: %d" % ((nvram_read(rtc, 0x14) >> 6) & 0x3)
    try:
        atype = disk_types[nvram_read(rtc, 0x10) >> 4]
    except:
        atype = "Unknown"
    try:
        btype = disk_types[nvram_read(rtc, 0x10) & 0xf]
    except:
        btype = "Unknown"
    print "            A: type: %s" % atype
    print "            B: type: %s" % btype
    print
    drvtype = []
    drvname = ["C", "D"]
    drvtype.append(nvram_read(rtc, 0x12) >> 4)
    drvtype.append(nvram_read(rtc, 0x12) & 0xf)
    for drv in range(0, 2):
        if drvtype[drv] == 0x0:
            print "     %s: Drive type : No disk" % drvname[drv]
        elif drvtype[drv] != 0xf:
            print "     %s: Drive type : 0x%02x (obsolete)" % (drvname[drv], drvtype[drv])
        else:
            print "     %s: Drive type : 0x%02x" % (drvname[drv], nvram_read(rtc, hd_regs[drv][0]))
            print "         Cylinders : %4d" % ((nvram_read(rtc, hd_regs[drv][2]) << 8) | nvram_read(rtc, hd_regs[drv][1]))
            print "             Heads : %4d" % nvram_read(rtc, hd_regs[drv][3])
            print " Sectors per track : %4d" % nvram_read(rtc, hd_regs[drv][9])
            print
    print
    if nvram_read(rtc, 0x2d) == 0x20:
        boot_dev = "A"
    elif nvram_read(rtc, 0x2d) == 0x00:
        boot_dev = "C"
    else:
        boot_dev = "Unknown"
    print "        Boot device: %s" % boot_dev
    print


def register_cmos_commands(class_name):
    new_command("cmos-init", cmos_init_cmd,
                [],
                short = "initialize some CMOS values",
                namespace = class_name,
                doc = "Set initial CMOS values in the RTC device.<br/>"
                "This is miscellaneous data that is not set by any of the "
                "other cmos-* commands. Note that the CMOS values only has "
                "to be set if not running from a saved configuration. A "
                "saved configuration will have all values stored in the "
                "NVRAM area, and the cmos-* commands need only be used if "
                "some values have to be changed.", filename="/mp/simics-3.0/src/extensions/apps-python/x86_cmos_info.py", linenumber="295")

    new_command("cmos-base-mem", cmos_base_mem_cmd,
                [arg(int_t, "kilobytes")],
                short = "set base memory size",
                namespace = class_name,
                doc = "Sets the amount of base memory (in kB).<br/>"
                "This command will update the proper location in the CMOS so "
                "that the BIOS will know how much memory is installed in the "
                "system. Operating system that use the BIOS to find out the "
                "memory size will get confused if this size is set "
                "incorrectly (especially if it is set too high). The maximum "
                "amount that can be set is 640kB.", filename="/mp/simics-3.0/src/extensions/apps-python/x86_cmos_info.py", linenumber="307")

    new_command("cmos-extended-mem", cmos_extended_mem_cmd,
                [arg(int_t, "megabytes")],
                short = "set extended memory size",
                namespace = class_name,
            doc = "Sets the amount of extended memory (in MB).<br/>"
                "This command will update the proper location in the CMOS so "
                "that the BIOS will know how much memory is installed in the "
                "system. Operating system that use the BIOS to find out the "
                "memory size will get confused if this size is set "
                "incorrectly (especially if it is set too high). The maximum "
                "amount that can be set is 63MB.", filename="/mp/simics-3.0/src/extensions/apps-python/x86_cmos_info.py", linenumber="319")

    new_command("cmos-floppy", cmos_floppy_cmd,
                [arg(str_t, "drive"),
                 arg(str_t, "type", expander=type_expand)],
                short = "set floppy parameters",
                namespace = class_name,
                doc = "Sets information in the CMOS about floppy drives.<br/>"
                "Drive is either A (primary drive) or B (secondary drive), "
                "and type is the maximal drive size (in kB or MB); 360, 720, "
                "1.2, 1.44, 2.88. Setting <i>type</i> to \"none\" indicates "
                "to the OS/BIOS that no drive is present. Since both "
                "arguments are strings, quoting is sometimes necessary.<br/>", filename="/mp/simics-3.0/src/extensions/apps-python/x86_cmos_info.py", linenumber="331")

    new_command("cmos-hd", cmos_hd_cmd,
                [arg(str_t, "drive"),
                 arg(int_t, "cylinders"),
                 arg(int_t, "heads"),
                 arg(int_t, "sectors_per_track")],
                short = "set fixed disk parameters",
                namespace = class_name,
                doc = "Sets information in the CMOS about the primary hard "
                "disk (\"C\") and the secondary hard disk (\"D\").", filename="/mp/simics-3.0/src/extensions/apps-python/x86_cmos_info.py", linenumber="343")

    new_command("cmos-boot-dev", cmos_boot_dev_cmd,
                [arg(str_t, "drive")],
                short = "set boot drive",
                namespace = class_name,
                doc = "Specifies boot device for the BIOS in the CMOS.<br/>"
                "Parameters: A or C, or floppy or HD boot. "
                "Default is C.", filename="/mp/simics-3.0/src/extensions/apps-python/x86_cmos_info.py", linenumber="353")

    new_command("cmos-info", cmos_info_cmd,
                [],
                short = "print information about the CMOS area",
                namespace = class_name,
                doc = "Print detailed information about the CMOS information "
                "from the RTC device.", filename="/mp/simics-3.0/src/extensions/apps-python/x86_cmos_info.py", linenumber="361");
