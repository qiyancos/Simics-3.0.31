from cli import *

pc_partition_types = { 0 : "unused",
                    1 : "DOS 12-bit FAT",
                    4 : "DOS 3.0+ 16-bit FAT",
                    5 : "DOS 3.3+ extended",
                    6 : "DOS 3.31+ 16-bit FAT",
                    7 : "OS/2 IFS",
                  0xa : "OS/2 boot manager",
                  0xb : "Win95 32-bit FAT",
                  0xc : "Win95 32-bit FAT, LBA",
                  0xe : "Win95 16-bit FAT, LBA",
                  0xf : "Win95 extended, LBA",
                 0x82 : "Linux swap",
                 0x83 : "Linux native",
                 0x85 : "Linux extended",
                 0x8e : "Linux LVM",
                 0xa5 : "BSD/386",
                 0xa6 : "OpenBSD",
                 0xa9 : "NetBSD",
                 0xeb : "BeOS" }

partition_keys = pc_partition_types.keys()
partition_keys.sort()
partition_desc = map(lambda x: "\"%s\" (0x%x)" % (pc_partition_types[x], x), partition_keys)

def pc_partition_type_expander(string, obj):
	return get_completions(string, pc_partition_types.values())

def build_32bit(a, b, c, d):
	return (long(a) << 0) | (long(b) << 8) | (long(c) << 16) | (long(d) << 24)

def print_partition_table_cmd(obj):
	# Read first sector
	sector = range(512)
	for i in range(512):
		sector[i] = obj.image.byte_access[i]
        print "Partition table for %s:" % obj.name
	print "Id BI  St  C/  H/ S   E  C/  H/ S  LBA ----  Size ---  Offset -----  Type"
	for i in range(4):
		part_entry = sector[0x1be + 16 * i : 0x1be + 16 * i + 16]
		type_name = "foo"
		try:
			type_name = pc_partition_types[part_entry[4]]
		except KeyError:
			type_name = "0x%x" % part_entry[4]
		print " %d %02x   %4d/%3d/%2d   %4d/%3d/%2d  %8u  %8u  %12u  %s" % (
                         i,
			 part_entry[0],
		         ((part_entry[2] >> 6) << 8) | part_entry[3],
		         part_entry[1],
		         part_entry[2] & 0x3f,
		         ((part_entry[6] >> 6) << 8) | part_entry[7],
		         part_entry[5],
		         part_entry[6] & 0x3f,
                         build_32bit(part_entry[8], part_entry[9], part_entry[10], part_entry[11]),
                         build_32bit(part_entry[12], part_entry[13], part_entry[14], part_entry[15]),
		         build_32bit(part_entry[8], part_entry[9], part_entry[10], part_entry[11]) * 512L,
		         type_name)

def print_partition_info_cmd(obj, i, filename):
	# Read first sector
	sector = range(512)
	for j in range(512):
		sector[j] = obj.image.byte_access[j]

	if i < 0 or i >= 4:
		print "Partition number %d out of range (0 .. 3 allowed)." % i
		SIM_command_has_problem()
		return

	part_entry = sector[0x1be + 16 * i : 0x1be + 16 * i + 16]
	type_name = "foo"
	try:
		type_name = pc_partition_types[part_entry[4]]
	except KeyError:
		type_name = "0x%x" % part_entry[4]
	print "Id BI  St  C/  H/ S   E  C/  H/ S  LBA ----  Size ---  Offset -----  Type"
	offset = build_32bit(part_entry[8], part_entry[9], part_entry[10], part_entry[11]) * 512L
	print " %d %02x   %4d/%3d/%2d   %4d/%3d/%2d  %8u  %8u  %12u  %s" % (
		i,
		part_entry[0],
		((part_entry[2] >> 6) << 8) | part_entry[3],
		part_entry[1],
		part_entry[2] & 0x3f,
		((part_entry[6] >> 6) << 8) | part_entry[7],
		part_entry[5],
		part_entry[6] & 0x3f,
		build_32bit(part_entry[8], part_entry[9], part_entry[10], part_entry[11]),
		build_32bit(part_entry[12], part_entry[13], part_entry[14], part_entry[15]),
		offset,
		type_name)

	if filename:
		f = open(filename, "w")
		image_files = obj.image.files
		f.write("(")
		first_file = 1
		for sub_file in image_files:
			if first_file:
				first_file = 0
			else:
				f.write(",\n")
			offset_remaining = offset
			start = sub_file[2]
			length = sub_file[3]
			file_offset = sub_file[4]
			if start > 0:
				if start >= offset:
					start -= offset
					offset_remaining = 0
				else:
					offset_remaining -= start
					start = 0
			if offset_remaining:
				length -= offset_remaining
				file_offset += offset_remaining
			f.write("(\"%s\", \"ro\", %d, %d, %d)" % (sub_file[0], start, length, file_offset))
		f.write(")\n")
		f.close()

def create_pc_partition_cmd(obj, partition, start_cylinder, start_head, start_sector, end_cylinder, end_head, end_sector, type, start_lba, size_in_sectors, boot_indication):
	if boot_indication:
		boot_indication = 0x80
	if partition < 0 or partition > 4:
		print "Partition must be 1, 2, 3, or 4."
		SIM_command_has_problem()
		return
	if start_cylinder < 0 or start_cylinder > 0x3ff or end_cylinder < 0 or end_cylinder > 0x3ff:
		print "Cylinder must be >= 0 and <= %d" % 0x3ff
		SIM_command_has_problem()
		return
	if start_head < 0 or start_head > 0xff or end_head < 0 or end_head > 0xff:
		print "Head must be >= 0 and <= %d" % 0xff
		SIM_command_has_problem()
		return
	if start_sector < 0 or start_sector > 0x3f or end_sector < 0 or end_sector > 0x3f:
		print "Sector must be >= 0 and <= %d" % 0x3f
		SIM_command_has_problem()
		return
	part_entry = range(16)
	part_entry[0] = boot_indication
	part_entry[1] = start_head
	part_entry[2] = start_sector | ((start_cylinder >> 8) << 6)
	part_entry[3] = start_cylinder & 0xff
	if type[0] == str_t:
		try:
			type_id = pc_partition_types.keys()[pc_partition_types.values().index(type[1])]
		except:
			print "Unknown partition type '%s'" % type[1]
			print "Try one of:"
			for i in pc_partition_types.values():
				print "   " + i
			return
	elif type[0] == int_t:
		type_id = type[1]
	else:
		print "Weird type value"
		SIM_command_has_problem()
		return
	part_entry[4] = type_id
	part_entry[5] = end_head
	part_entry[6] = end_sector | ((end_cylinder >> 8) << 6)
	part_entry[7] = end_cylinder & 0xff
	part_entry[8] = (start_lba >> 0) & 0xff
	part_entry[9] = (start_lba >> 8) & 0xff
	part_entry[10] = (start_lba >> 16) & 0xff
	part_entry[11] = (start_lba >> 24) & 0xff
	part_entry[12] = (size_in_sectors >> 0) & 0xff
	part_entry[13] = (size_in_sectors >> 8) & 0xff
	part_entry[14] = (size_in_sectors >> 16) & 0xff
	part_entry[15] = (size_in_sectors >> 24) & 0xff
	for i in range(16):
		obj.image.byte_access[0x1be + 16 * partition + i] = part_entry[i]

def create_pc_partition_table_commands(name):
	new_command("print-partition-table", print_partition_table_cmd,
	            [],
	            type = "%s commands" % name,
	            short = "print the disk's pc-style partition table",
	            namespace = "%s" % name,
	            see_also = ['<' + "%s" % name + '>.' + 'create-partition'],
	            doc = """
Print the PC-style partition table for a disk.
""", filename="/mp/simics-3.0/src/extensions/apps-python/pc_disk_commands.py", linenumber="177")
#  	new_command("create-partition-table", create_partition_table_cmd,
#  	            [],
#  	            type = "%s commands" % name,
#  	            short = "create partition table",
#  	            namespace = "%s" % name,
#  	            doc_items = [('SEE ALSO', 'print-partition-table, create-partition, delete-partition')],
#  	            doc = """
#  Create the header part of the partition table. Use create-partition to add partitions to the table.
#  """)
	new_command("create-partition", create_pc_partition_cmd,
	             [arg(int_t, "partition"),
	              arg(int_t, "start_cylinder"),
	              arg(int_t, "start_head"),
	              arg(int_t, "start_sector"),
	              arg(int_t, "end_cylinder"),
	              arg(int_t, "end_head"),
	              arg(int_t, "end_sector"),
	              arg((int_t, str_t), ("type_id", "type_name"), expander = (pc_partition_type_expander, None)),
	              arg(int_t, "start_lba"),
	              arg(int_t, "size_in_sectors"),
	              arg(flag_t, "-boot-indication")],
	             type = "%s commands" % name,
	             short = "add a partition to disk",
	             namespace = "%s" % name,
	             see_also = ['<' + "%s" % name + '>.' + 'print-partition-table'],
	             doc = """
Add a partition to a disk's partition table. Will create a primary PC-style partition
with number <arg>partition</arg>. Any existing partition will be overwritten. The start
location of the partition is given both in CHS format with <arg>start_cylinder</arg>,
<arg>start_head</arg>, <arg>start_sector</arg>, and in linear format with
<arg>start_lba</arg>. The partition endpoint is specified in CHS format with
<arg>end_cylinder</arg>, <arg>end_head</arg>, and <arg>end_sector</arg>. The size in
512-byte sectors is <arg>size_in_sectors</arg>.

The slight overspecification of the parameters is there because they depend on how
the BIOS translates the disk geometry to the BIOS geometry. All CHS coordinates given
to this command should be in the translated BIOS geometry.

The partition boot bit is enabled with the <arg>-boot-indication</arg> flag (default
off).

The partition type can either raw numerical code, or a symbolic name. The following
symbolic names are understood by the command: %s, and %s.
""" % (", ".join(partition_desc[:len(partition_desc)-1]), partition_desc[len(partition_desc)-1]), filename="/mp/simics-3.0/src/extensions/apps-python/pc_disk_commands.py", linenumber="195")
	new_command("print-partition-info", print_partition_info_cmd,
	            [arg(int_t, "num"),
		     arg(str_t, "filename", "?", None)],
	            type = "%s commands" % name,
	            short = "print info about a pc-style partition",
	            namespace = "%s" % name,
	            doc = """
Print information about a partition. If a filename is given, then suitable
partition parameters for use with image aware e2tools will be written to that file.
""", filename="/mp/simics-3.0/src/extensions/apps-python/pc_disk_commands.py", linenumber="230")
