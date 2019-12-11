from cli import *

#
# VTOC layout: (with unimportant fields removed)
#
                     # OFFSET   SIZE    NUM NAME
                     #     0     128     1  label
VTOC_VERSION   = 128 #   128       4     1  version
                     #   132       8     1  volume name
VTOC_NUMPART   = 140 #   140       2     1  number of partitions
VTOC_PART_S2   = 142 #   142       4     8  partition headers, section 2
                     #                       2 bytes tag
                     #                       2 bytes permission flag
                     #   174       2     1  <pad>
                     #   176       4     3  bootinfo
VTOC_SANITY    = 188 #   188       4     1  sanity
                     #   192       4    10  <reserved>
                     #   232       4     8  partition timestamp
                     #   264       2     1  write reinstruct
                     #   266       2     1  read reinstruct
                     #   268     152     1  <pad>
VTOC_RPM       = 420 #   420       2     1  rpm
VTOC_PHYS_CYL  = 422 #   422       2     1  physical cylinders
VTOC_ALT_P_CYL = 424 #   424       2     1  alternates per cylinder
                     #   426       2     1  <obsolete>
                     #   428       2     1  <obsolete>
VTOC_INTRLV    = 430 #   430       2     1  interleave
VTOC_DATA_CYL  = 432 #   432       2     1  data cylinders
VTOC_ALT_CYL   = 434 #   434       2     1  alt cylinders
VTOC_HEADS     = 436 #   436       2     1  heads
VTOC_TRACKS    = 438 #   438       2     1  sectors per track
                     #   440       2     1  <obsolete>
                     #   442       2     1  <obsolete>
VTOC_PART_S1   = 444 #   444       8     8  partition headers, section 1
                     #                       4 bytes start cylinder
                     #                       4 bytes number of blocks
VTOC_MAGIC     = 508 #   508       2     1  magic = 0xDABE
VTOC_CHECKSUM  = 510 #   510       2     1  checksum

tag_list = { 0 : "unused",
             1 : "boot",
             2 : "root",
             3 : "swap",
             4 : "usr",
             5 : "backup",
             7 : "var",
             8 : "home",
             130 : "Linux swap",
             131 : "Linux" }

flag_list = { 0 : "RW",
              1 : "unmountable",
              2 : "RO" }

def get_tag_str(tag):
    try:
        return "(" + tag_list[tag] + ")"
    except:
        return "(unknown)"

def get_flag_str(flag):
    try:
        return "(" + flag_list[flag] + ")"
    except:
        return "(unknown)"

def calculate_checksum(vtoc):
    chk = 0
    for i in range(0, 510, 2):
        chk ^= get_vtoc_int16(vtoc, i)
    return chk

def get_vtoc_label(vtoc):
    str = ""
    for i in vtoc:
        if i == 0:
            return str
        str += chr(i)

def set_vtoc_label(vtoc, str):
    for i in range(0, len(str)):
        vtoc[i] = ord(str[i])
    for j in range(i + 1, 512):
        vtoc[j] = 0

def get_vtoc_int16(vtoc, offset):
    return (vtoc[offset] << 8) | vtoc[offset + 1]

def set_vtoc_int16(vtoc, offset, value):
    vtoc[offset] = (value >> 8) & 0xff
    vtoc[offset + 1] = value & 0xff

def get_vtoc_int32(vtoc, offset):
    return (get_vtoc_int16(vtoc, offset) << 16) | get_vtoc_int16(vtoc, offset + 2)

def set_vtoc_int32(vtoc, offset, value):
    set_vtoc_int16(vtoc, offset, (value >> 16) & 0xffff)
    set_vtoc_int16(vtoc, offset + 2, value & 0xffff)

def read_block(obj, offset):
    if obj.classname == "scsi-disk":
        return list(obj.sector_data[offset * 512])
    elif obj.classname == "ide-disk":
        block = []
        for i in range(0, 512):
            block.append(obj.image.byte_access[offset * 512 + i])
        return block
    else:
        raise Exception, "Unknown disk type"
        
def write_block(obj, offset, block):
    if obj.classname == "scsi-disk":
        obj.sector_data[offset * 512] = block
    elif obj.classname == "ide-disk":
        for i in range(0, 512):
            obj.image.byte_access[offset * 512 + i] = block[i]
    else:
        raise Exception, "Unknown disk type"
    
def print_partitions(obj, vtoc):
    heads = get_vtoc_int16(vtoc, VTOC_HEADS)
    s_per_t = get_vtoc_int16(vtoc, VTOC_TRACKS)
    print "Partition Table:"
    print "Number   Tag             Flag                 Start        End       Size"
    for i in range(0, 8):
        tag = get_vtoc_int16(vtoc, VTOC_PART_S2 + 4 * i + 0)
        flag = get_vtoc_int16(vtoc, VTOC_PART_S2 + 4 * i + 2)
        start = get_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * i + 0)
        blocks = get_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * i + 4)
        if blocks == 0:
            continue
        start *= heads * s_per_t
        print "  %d      %d %-12s  %d %-13s  %9d  %9d  %9d" % (
            i, tag, get_tag_str(tag), flag, get_flag_str(flag),
            start, start + blocks - 1, blocks)
    
def print_sun_vtoc_cmd(obj):
    vtoc = read_block(obj, 0)
    if get_vtoc_int16(vtoc, VTOC_MAGIC) != 0xDABE:
        print "This does not appear to be a Sun Disk."
        print "The magic is %x, expected 0xDABE" % get_vtoc_int16(vtoc, VTOC_MAGIC)
        print
        return
    data_cyl = get_vtoc_int16(vtoc, VTOC_DATA_CYL)
    phys_cyl = get_vtoc_int16(vtoc, VTOC_PHYS_CYL)
    heads = get_vtoc_int16(vtoc, VTOC_HEADS)
    s_per_t = get_vtoc_int16(vtoc, VTOC_TRACKS)
    print
    print "             Label : %s" % get_vtoc_label(vtoc)
    print "               RPM : %s" % get_vtoc_int16(vtoc, VTOC_RPM)
    print "    Data cylinders : %d" % data_cyl
    print "     Alt cylinders : %d" % get_vtoc_int16(vtoc, VTOC_ALT_CYL)
    print "Physical cylinders : %d" % phys_cyl
    print "             Heads : %d" % heads
    print " Sectors per Track : %d" % s_per_t
    print
    print "  Number of data blocks : %d" % (data_cyl * s_per_t * heads)
    print
    print_partitions(obj, vtoc)
    num_part = get_vtoc_int16(vtoc, VTOC_NUMPART)
    chk_sum = get_vtoc_int16(vtoc, VTOC_CHECKSUM)
    if num_part != 8:
        print
        print "### Illegal number of partitions set (%d), only 8 supported" % num_part
    if calculate_checksum(vtoc) != chk_sum:
        print "### Incorrect checksum: %d. Expected: %d" % (chk_sum, calculate_checksum(vtoc))
    print

def write_sun_vtoc_cmd(obj, C, H, S, quiet):
    vtoc = [0] * 512
    if -1 in [C, H, S] and [C, H, S] != [-1, -1, -1]:
        print "Only Partial geometry specified."
        SIM_command_has_problem()
        return
    
    alt = 2
    if [C, H, S] != [-1, -1, -1]:
        cyl = C - alt
        heads = H
        s_per_t = S
    elif obj.classname == "scsi-disk":
        print "No geometry specified for SCSI disk VTOC."
        SIM_command_has_problem()
        return
    elif obj.classname == "ide-disk":
        cyl = obj.disk_cylinders - alt
        heads = obj.disk_heads
        s_per_t = obj.disk_sectors_per_track
        pass
    else:
        raise Exception, "Unknown disk type"
    
    set_vtoc_label(vtoc, "SIMDISK cyl %d alt %d hd %d sec %d" % (cyl, alt, heads, s_per_t))
    set_vtoc_int32(vtoc, VTOC_VERSION, 1)
    set_vtoc_int16(vtoc, VTOC_MAGIC, 0xDABE)
    set_vtoc_int16(vtoc, VTOC_DATA_CYL, cyl)
    set_vtoc_int16(vtoc, VTOC_ALT_CYL, alt)
    set_vtoc_int16(vtoc, VTOC_INTRLV, 1)
    set_vtoc_int16(vtoc, VTOC_PHYS_CYL, cyl + alt)
    set_vtoc_int16(vtoc, VTOC_HEADS, heads)
    set_vtoc_int16(vtoc, VTOC_TRACKS, s_per_t)
    set_vtoc_int16(vtoc, VTOC_NUMPART, 8)
    set_vtoc_int16(vtoc, VTOC_RPM, 7200)
    set_vtoc_int32(vtoc, VTOC_SANITY, 0x600ddeee)
    # set checksum last!
    set_vtoc_int16(vtoc, VTOC_CHECKSUM, calculate_checksum(vtoc))
    write_block(obj, 0, tuple(vtoc))
    # create the backup slice
    write_sun_vtoc_partition_cmd(obj, 2, "backup", "unmountable", 0, cyl * heads * s_per_t, 1)
    if not quiet and SIM_get_quiet() == 0:
        print "New VTOC written to disk:"
        print_sun_vtoc_cmd(obj)

def write_sun_vtoc_partition_cmd(obj, nbr, tag_str, flag_str, start, blocks, quiet):
    if nbr < 0 or nbr > 7:
        print "Partitions are numbered 0 ..7\n"
        return
    try:
        tag = tag_list.keys()[tag_list.values().index(tag_str)]
    except:
        print "Unknown tag type '%s'" % tag_str
        print "Try one of:"
        for i in tag_list.values():
            print "   " + i
        print
        return
    try:
        flag = flag_list.keys()[flag_list.values().index(flag_str)]
    except:
        print "Unknown flag '%s'" % flag_str
        print "Try one of:"
        for i in flag_list.values():
            print "   " + i
        print
        return
    vtoc = read_block(obj, 0)
    heads = get_vtoc_int16(vtoc, VTOC_HEADS)
    s_per_t = get_vtoc_int16(vtoc, VTOC_TRACKS)
    set_vtoc_int16(vtoc, VTOC_PART_S2 + 4 * nbr + 0, tag)
    set_vtoc_int16(vtoc, VTOC_PART_S2 + 4 * nbr + 2, flag)
    set_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * nbr + 0, start / (heads * s_per_t))
    set_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * nbr + 4, blocks)
    # set checksum last!
    set_vtoc_int16(vtoc, VTOC_CHECKSUM, calculate_checksum(vtoc))
    write_block(obj, 0, tuple(vtoc))
    if not quiet and SIM_get_quiet() == 0:
        print_partitions(obj, vtoc)
        print

def delete_sun_vtoc_partition_cmd(obj, nbr, quiet):
    if nbr < 0 or nbr > 7:
        print "Partitions are numbered 0 ..7\n"
        return
    vtoc = read_block(obj, 0)
    set_vtoc_int16(vtoc, VTOC_PART_S2 + 4 * nbr + 0, 0)
    set_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * nbr + 4, 0)
    # set checksum last!
    set_vtoc_int16(vtoc, VTOC_CHECKSUM, calculate_checksum(vtoc))
    write_block(obj, 0, tuple(vtoc))
    if not quiet and SIM_get_quiet() == 0:
        print_partitions(obj, vtoc)
        print

def dump_sun_partition_cmd(obj, nbr, file):
    if nbr < 0 or nbr > 7:
        print "Partitions are numbered 0 ..7\n"
        return
    vtoc = read_block(obj, 0)
    heads = get_vtoc_int16(vtoc, VTOC_HEADS)
    s_per_t = get_vtoc_int16(vtoc, VTOC_TRACKS)
    start = get_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * nbr) * heads * s_per_t
    blocks = get_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * nbr + 4)
    if blocks == 0:
        print "No partition %d.\n" % nbr
        return
    print "Dumping partition %d. Start block %d. Size in blocks: %d" % (nbr, start, blocks)
    # index with list, since python doesn't have 4 bit indexes
    try:
        obj.image.dump[[file, start * 512, blocks * 512]]
    except Exception, msg:
        print "Failed getting a dump from the disk image."
        print "Error message was: %s\n" % msg
        return
    print "Partition dumped successfully.\n"

def add_sun_partition_cmd(obj, nbr, file):
    if nbr < 0 or nbr > 7:
        print "Partitions are numbered 0 ..7\n"
        return
    vtoc = read_block(obj, 0)
    heads = get_vtoc_int16(vtoc, VTOC_HEADS)
    s_per_t = get_vtoc_int16(vtoc, VTOC_TRACKS)
    start = get_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * nbr) * heads * s_per_t
    blocks = get_vtoc_int32(vtoc, VTOC_PART_S1 + 8 * nbr + 4)
    if blocks == 0:
        print "No partition %d.\n" % nbr
        return
    print "Adding partition %d. Start block %d. Size in blocks: %d" % (nbr, start, blocks)
    # index with list, since python doesn't have 4 bit indexes
    files = obj.image.files
    files += [[file, "ro", start * 512, blocks * 512]]
    try:
       obj.image.files = files
    except Exception, msg:
        print "Failed adding the diff file '%s' to image '%s'." % (file, obj.name)
        print "Error message was: %s\n" % msg
        return
    print "Partition added.\n"

def tag_expander(string, obj):
    return get_completions(string, tag_list.values())

def flag_expander(string, obj):
    return get_completions(string, flag_list.values())

def create_sun_vtoc_commands(name):
    new_command("print-sun-vtoc", print_sun_vtoc_cmd,
                [],
                alias = "",
                type  = "%s commands" % name,
                short = "print the VTOC for a Sun disk",
                namespace = "%s" % name,
                see_also = ["<" + "%s" % name + '>.' + 'create-sun-vtoc-header',
                            "<" + "%s" % name + '>.' + 'create-sun-vtoc-partition',
                            "<" + "%s" % name + '>.' + 'delete-sun-vtoc-partition'],
                doc = """
Print the contents of the VTOC (volume table of contents) for a Sun
disk. This is similar to the Solaris 'prtvtoc' command.
""", filename="/mp/simics-3.0/src/extensions/apps-python/sun_vtoc_commands.py", linenumber="317")
    new_command("create-sun-vtoc-header", write_sun_vtoc_cmd,
                [arg(int_t, "C", "?", -1),
                 arg(int_t, "H", "?", -1),
                 arg(int_t, "S", "?", -1),
                 arg(flag_t, "-quiet")],
                alias = "",
                type  = "%s commands" % name,
                short = "write a new VTOC to a Sun disk",
                namespace = "%s" % name,
                see_also = ["<" + "%s" % name + '>.' + 'print-sun-vtoc',
                            "<" + "%s" % name + '>.' + 'create-sun-vtoc-partition',
                            "<" + "%s" % name + '>.' + 'delete-sun-vtoc-partition'],
                doc = """
Create and write a new VTOC to a Sun disk. The geometry information written is
taken from the configuration attribute 'geometry' of the disk, unless specified
with the <b>C</b>, <b>H</b> and <b>S</b> parameters. A new empty partition
table is also created, with only the standard 'backup' partition as number
2. <arg>-quiet</arg> makes the command silent in case of success.
""", filename="/mp/simics-3.0/src/extensions/apps-python/sun_vtoc_commands.py", linenumber="330")
    new_command("create-sun-vtoc-partition", write_sun_vtoc_partition_cmd,
                [arg(int_t, "number"),
                 arg(str_t, "tag", expander = tag_expander),
                 arg(str_t, "flag", expander = flag_expander),
                 arg(int_t, "start-block"),
                 arg(int_t, "num-blocks"),
                 arg(flag_t, "-quiet")],
                alias = "",
                type  = "%s commands" % name,
                short = "write partition data in the VTOC on a Sun disk",
                namespace = "%s" % name,
                see_also = ["<" + "%s" % name + '>.' + 'print-sun-vtoc',
                            "<" + "%s" % name + '>.' + 'create-sun-vtoc-header',
                            "<" + "%s" % name + '>.' + 'delete-sun-vtoc-partition'],
                doc = """
Write partition information to the VTOC on a Sun disk. This command does not
change the format of the disk, and it does not create any file system on the
partition. Only the 'Volume Table Of Contents' is modified. No checking is
performed to make sure that partitions do not overlap, or that they do not
exceed the disk size. <arg>-quiet</arg> makes the command silent in case of
success.
""", filename="/mp/simics-3.0/src/extensions/apps-python/sun_vtoc_commands.py", linenumber="349")
    new_command("delete-sun-vtoc-partition", delete_sun_vtoc_partition_cmd,
                [arg(int_t, "number"),
                 arg(flag_t, "-quiet")],
                alias = "",
                type  = "%s commands" % name,
                short = "delete partition data from the VTOC on a Sun disk",
                namespace = "%s" % name,
                see_also = ["<" + "%s" % name + '>.' + 'print-sun-vtoc',
                            "<" + "%s" % name + '>.' + 'create-sun-vtoc-header',
                            "<" + "%s" % name + '>.' + 'create-sun-vtoc-partition'],
                doc = """
Delete the information in the VTOC on a Sun disk for the specified partition.
No other modification on the disk is performed. <arg>-quiet</arg> makes the
command silent in case of success.
""", filename="/mp/simics-3.0/src/extensions/apps-python/sun_vtoc_commands.py", linenumber="371")
    
    new_command("dump-sun-partition", dump_sun_partition_cmd,
                [arg(int_t, "number"), arg(filename_t(), "file")],
                alias = "",
                type  = "%s commands" % name,
                short = "write partition as a file",
                namespace = "%s" % name,
                see_also = ["<" + "%s" % name + '>.' + 'print-sun-vtoc',
                            "<" + "%s" % name + '>.' + 'add-sun-partition'],
                doc = """
Write all data from a Sun disk partition to the specified file in
raw format.
""", filename="/mp/simics-3.0/src/extensions/apps-python/sun_vtoc_commands.py", linenumber="387")
    new_command("add-sun-partition", add_sun_partition_cmd,
                [arg(int_t, "number"), arg(filename_t(), "file")],
                alias = "",
                type  = "%s commands" % name,
                short = "add partition from a file",
                namespace = "%s" % name,
                see_also = ["<" + "%s" % name + '>.' + 'dump-sun-partition'],
                doc = """
Adds an image or diff as a sun partition to the current disk.
""", filename="/mp/simics-3.0/src/extensions/apps-python/sun_vtoc_commands.py", linenumber="399")
