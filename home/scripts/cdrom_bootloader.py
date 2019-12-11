
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
# cdrom_bootloader.py
#
# Hack to add CD-ROM boot support to simics. Hooks into a slightly
# modified bios (hooks present in version 2.28 and later) through a magic
# service with special calling conventions.
#
# Does not support hard disk emulation.
#
# Cannot handle cases where memory accesses fail due to exceptions (can
# only happen in protected mode).
#
# Magnus Christensson
#

from array import array

class cdrom_bootloader:
	pass

x86_linear_to_physical = {}

# The linear read write functions will raise an exception if the write
# fails. Ok.

def read_linear(cpu, laddr, size):
        global x86_linear_to_physical
	value = 0L
	for i in range(size):
		paddr = x86_linear_to_physical[cpu](cpu, 1, laddr + i)
		sub_value = SIM_read_phys_memory(cpu, paddr, 1)
		value = value | ((sub_value & 0xff) << (i * 8))
	return value

def write_linear(cpu, laddr, value, size):
        global x86_linear_to_physical
	for i in range(size):
		paddr = x86_linear_to_physical[cpu](cpu, 1, laddr + i)
		sub_value = (value >> (i * 8)) & 0xff
		SIM_write_phys_memory(cpu, paddr, sub_value, 1)

def emulate_int19(loader, cpu):
        global x86_linear_to_physical
        x86_linear_to_physical[cpu] = cpu.iface.x86.linear_to_physical

	if cpu.cr0 & 1:
		raise "emulate_int19() not protected mode safe"
	bootloader_print("---- Booting from CD-ROM emulated ----")
	if not conf.cd0.cd_media:
		SIM_break_simulation("Trying to boot from non-existing CD-ROM")
		return
	boot_cd = conf.cd0.cd_media.file
	conf.cd0.unit_attension = 0 # Drive has been accessed, clear unit attension
	loader.boot_file = open(boot_cd, "rb")

	# Read Boot Record
	loader.boot_file.seek(0x11 * 0x800)
	boot_record = loader.boot_file.read(0x800)
	if ord(boot_record[0]) != 0:
                loader.boot_file.close()
		raise "Boot record validation failed (0x%x)" % ord(boot_record[0])
	iso_id = array('b', boot_record[1:6]).tostring()
	if iso_id != "CD001":
                loader.boot_file.close()
		raise "Boot record validation failed (%s)" % iso_id
	if ord(boot_record[6]) != 1:
                loader.boot_file.close()
		raise "Boot record validation failed (0x%x)" % ord(boot_record[6])
	sys_id = array('b', boot_record[7:0x27]).tostring()
	if sys_id != "EL TORITO SPECIFICATION\0\0\0\0\0\0\0\0\0":
                loader.boot_file.close()
		raise "Boot record validation failed (%s : %d)	" % (sys_id, len(sys_id))
	boot_catalog_ptr = (((long(ord(boot_record[0x47])) & 0xff) << 0) |
                            ((long(ord(boot_record[0x48])) & 0xff) << 8) |
                            ((long(ord(boot_record[0x49])) & 0xff) << 16) |
                            ((long(ord(boot_record[0x4a])) & 0xff) << 24))
	bootloader_print("Boot catalog at sector 0x%x" % boot_catalog_ptr)

	# Read Boot Catalog
	loader.boot_file.seek(boot_catalog_ptr * 0x800)
	boot_catalog = loader.boot_file.read(0x800)
	if ord(boot_catalog[0]) != 1:
                loader.boot_file.close()
		raise "Boot catalog validation failed (0x%x)" % ord(boot_catalog[0])
	if ord(boot_catalog[1]) != 0:
                loader.boot_file.close()
		raise "Platform ID not 80x86 (0x%x)" % ord(boot_catalog[1])
	if ord(boot_catalog[2]) != 0:
                loader.boot_file.close()
		raise "Reserved field set (0x%x)" % ord(boot_catalog[2])
	if ord(boot_catalog[3]) != 0:
                loader.boot_file.close()
		raise "Reserved field set (0x%x)" % ord(boot_catalog[3])
	manufacturer = array('b', boot_catalog[4:0x1c]).tostring()
	bootloader_print("Manufacturer '%s'" % manufacturer)
	# Checksum assumed ok
	if ord(boot_catalog[0x1e]) != 0x55:
                loader.boot_file.close()
		raise "Boot catalog validation failed (0x%x)" % ord(boot_catalog[0x1e])
	if ord(boot_catalog[0x1f]) != 0xaa:
                loader.boot_file.close()
		raise "Boot catalog validation failed (0x%x)" % ord(boot_catalog[0x1f])

	# Read initial/default entry
	if ord(boot_catalog[0x20+0]) != 0x88:
                loader.boot_file.close()
		raise "Initial/default entry not bootable (0x%x)" % ord(boot_catalog[0x20+0])

	loader.emulation_type = ord(boot_catalog[0x20+1])
	if loader.emulation_type == 0:
		loader.emulated_drive = 0xe0
		loader.emulated_tracks = 0x50
		loader.emulated_heads = 0x02
		loader.emulated_sectors = 0x00
		bootloader_print("Boot media type: No emulation")
	elif loader.emulation_type == 1:
		loader.emulated_drive = 0x00
		loader.emulated_tracks = 0x50
		loader.emulated_heads = 0x02
		loader.emulated_sectors = 0x0F
		loader.emulated_media = 2
		bootloader_print("Boot media type: 1.2 Mb diskette")
	elif loader.emulation_type == 2:
		loader.emulated_drive = 0x00
		loader.emulated_tracks = 0x50
		loader.emulated_heads = 0x02
		loader.emulated_sectors = 0x12
		loader.emulated_media = 4
		bootloader_print("Boot media type: 1.44 Mb diskette")
	elif loader.emulation_type == 3:
		loader.emulated_drive = 0x00
		loader.emulated_tracks = 0x50
		loader.emulated_heads = 0x02
		loader.emulated_sectors = 0x24
		loader.emulated_media = 5
		bootloader_print("Boot media type: 2.88 Mb diskette")
	elif loader.emulation_type == 4:
                loader.boot_file.close()
		loader.emulated_drive = 0x00
		bootloader_print("Boot media type: hard disk")
		raise "Hard disk emulation not supported"
	else:
                loader.boot_file.close()
		raise "Unknown boot media type (0x%x)" % ord(boot_catalog[0x20+1])

	# Patch floppy area at segment(0x7a):offset(0x78), TODO

	loader.load_segment = (((long(ord(boot_catalog[0x20+2])) & 0xff) << 0) |
			       ((long(ord(boot_catalog[0x20+3])) & 0xff) << 8))
	if loader.load_segment == 0:
		loader.load_segment = 0x7c0
	bootloader_print("Load segment is 0x%x" % loader.load_segment)
	bootloader_print("System type is 0x%x" % ord(boot_catalog[0x20+4]))
	loader.sector_count = (((long(ord(boot_catalog[0x20+6])) & 0xff) << 0) |
			       ((long(ord(boot_catalog[0x20+7])) & 0xff) << 8))
	loader.load_rba = (((long(ord(boot_catalog[0x20+8])) & 0xff) << 0) |
		           ((long(ord(boot_catalog[0x20+9])) & 0xff) << 8) |
		    	   ((long(ord(boot_catalog[0x20+0xa])) & 0xff) << 16) |
		           ((long(ord(boot_catalog[0x20+0xb])) & 0xff) << 24))
	bootloader_print("Loading %d sectors from address 0x%x" % (loader.sector_count, loader.load_rba))

	# Read boot image
	loader.boot_file.seek(loader.load_rba * 0x800)
	boot_image = loader.boot_file.read(loader.sector_count * 0x800)

	# Write to memory
	for i in range(loader.sector_count * 0x800):
		SIM_write_phys_memory(cpu, loader.load_segment * 16 + i, ord(boot_image[i]), 1)

	# Set CS:IP
	bootloader_print("Modifying CS:RIP")
	cpu.eax = 0xC001

	# Setting DL to boot drive
	cpu.edx = loader.emulated_drive

        loader.boot_file.close()

def emulate_int13(loader, cpu):
	# INT 13h emulation protocol
	# AX       = 4711h
	# SS:BX+0  = DI
	# SS:BX+2  = SI
	# SS:BX+4  = BP
	# SS:BX+6  = SP
	# SS:BX+8  = BX
	# SS:BX+10 = DX
	# SS:BX+12 = CX
	# SS:BX+14 = AX
	# SS:BX+16 = DS
	# SS:BX+18 = ES
	# SS:BX+20 = FLAGS
	# Return emulation status in DL
	register_addr = cpu.ss[7] + (cpu.ebx & 0xffff)
	DI = read_linear(cpu, register_addr + 0, 2)
	SI = read_linear(cpu, register_addr + 2, 2)
	BP = read_linear(cpu, register_addr + 4, 2)
	SP = read_linear(cpu, register_addr + 6, 2)
	BX = read_linear(cpu, register_addr + 8, 2)
	DX = read_linear(cpu, register_addr + 10, 2)
	CX = read_linear(cpu, register_addr + 12, 2)
	AX = read_linear(cpu, register_addr + 14, 2)
	DS = read_linear(cpu, register_addr + 16, 2)
	ES = read_linear(cpu, register_addr + 18, 2)

	if not ((AX & 0xff00) == 0x4b00 and (DX & 0xff) == 0x7f) and  (DX & 0xff) != loader.emulated_drive:
		cpu.edx = 0
		return

	boot_cd = conf.cd0.cd_media.file
	loader.boot_file = open(boot_cd, "rb")

	if (AX & 0xff00) == 0x4200:
		bootloader_print("---- INT 13h (extended read) emulated ----")
		packet_addr = (DS * 16) + (SI & 0xffff)
		sector_count = read_linear(cpu, packet_addr + 2, 1)
		target_off = read_linear(cpu, packet_addr + 4, 2)
		target_sel = read_linear(cpu, packet_addr + 6, 2)
		lba_addr = read_linear(cpu, packet_addr + 8, 8)
		bootloader_print("%d sectors from lba 0x%x to %x:%x" % (sector_count, lba_addr, target_sel, target_off))
		if sector_count > 0:
			loader.boot_file.seek(lba_addr * 0x800)
			block = loader.boot_file.read(sector_count * 0x800)
			for i in range(sector_count * 0x800):
				write_linear(cpu, target_sel * 16 + target_off + i, ord(block[i]), 1)
			cpu.edx = 1
		else:
			pass

	elif (AX & 0xff00) == 0x1500:
		bootloader_print("---- INT 13h (get disk type) emulated ----")
		# Floppy or other removable with change line support == 2 -> return +1
		cpu.edx = 3

	elif (AX & 0xff00) == 0x0800:
		bootloader_print("---- INT 13h (get drive parameters) emulated ----")
		if loader.emulation_type == 0:
			# Illegal with no emulation
			cpu.edx = 0xff
		else:
			cpu.edx = 1
			new_BX = loader.emulated_media
			new_CX = ((loader.emulated_tracks - 1) << 8) + loader.emulated_sectors
			new_DX = ((loader.emulated_heads - 1) << 8) + 1
			write_linear(cpu, register_addr + 8, new_BX, 2)
			write_linear(cpu, register_addr + 12, new_CX, 2)
			write_linear(cpu, register_addr + 10, new_DX, 2)
			new_DI = read_linear(cpu, 0x0078, 2)
			new_ES = read_linear(cpu, 0x007A, 2)
			write_linear(cpu, register_addr + 0, new_DI, 2)
			write_linear(cpu, register_addr + 18, new_ES, 2)

	elif (AX & 0xff00) == 0x4b00:
		bootloader_print("---- INT 13h (terminate disk emulation) emulated ----")
		packet_addr = (DS * 16) + (SI & 0xffff)
		write_linear(cpu, packet_addr + 0, 0x13, 1)
		write_linear(cpu, packet_addr + 1, loader.emulation_type, 1)
		write_linear(cpu, packet_addr + 2, loader.emulated_drive, 1)
		write_linear(cpu, packet_addr + 3, 0x00, 1)
		write_linear(cpu, packet_addr + 4, loader.load_rba, 4)
		write_linear(cpu, packet_addr + 8, 0x0000, 2)
		write_linear(cpu, packet_addr + 10, 0x0000, 2)
		write_linear(cpu, packet_addr + 12, loader.load_segment, 2)
		write_linear(cpu, packet_addr + 14, loader.sector_count, 2)
		write_linear(cpu, packet_addr + 16, loader.emulated_tracks, 1)
		write_linear(cpu, packet_addr + 17, loader.emulated_sectors, 1)
		write_linear(cpu, packet_addr + 18, loader.emulated_heads, 1)
		if (AX & 0xff) == 0:
			# End emulation
			loader.emulated_drive = 0x4711
			# Restore floppy description area (TODO)
		cpu.edx = 1

	elif (AX & 0xff00) == 0x0000:
		bootloader_print("---- INT 13h (controller reset) emulated ----")
		cpu.edx = 1

	elif (AX & 0xff00) == 0x0200:
		bootloader_print("---- INT 13h (read) emulated ----")
		# AL     number of sectors
		# CH     cylinder
		# CL     sector number (1-63)
		# DH     head
		# ES:BX  data buffer
		CH = (CX >> 8) & 0xff
		CL = CX & 0xff
		DH = (DX >> 8) & 0xff
		lba = CH * loader.emulated_heads * loader.emulated_sectors + DH * loader.emulated_sectors + CL - 1
		target_address = ES * 16 + BX
		bootloader_print("%d sectors from lba 0x%x to %x:%x" % (AX & 0xff, lba, ES, BX))
		loader.boot_file.seek(loader.load_rba * 0x800 + lba * 512)
		block = loader.boot_file.read((AX & 0xff) * 512)
		for i in range((AX & 0xff) * 512):
			write_linear(cpu, target_address + i, ord(block[i]), 1)
		cpu.edx = 1

	elif (AX & 0xff00) == 0x4800:
		bootloader_print("---- INT 13h (get extended drive parameters) emulated ----")
		if loader.emulation_type == 0:
			# Illegal with no emulation
			cpu.edx = 0xff
		else:
			cpu.edx = 1
			packet_addr = (DS * 16) + (SI & 0xffff)
			buffer_size = read_linear(cpu, packet_addr + 0, 2)
			if buffer_size < 26:
				# Illegal buffer size
				cpu.edx = 0xff
			else:
				if buffer_size >= 30:
					write_linear(cpu, packet_addr + 0, 30, 2)
				else:
					write_linear(cpu, packet_addr + 0, 26, 2)
				# Geometry valid, device is removable
				information_flags = (1 << 1) | (1 << 2)
				cylinders = loader.emulated_tracks
				heads = loader.emulated_heads
				spt = loader.emulated_sectors
				total_sectors = spt * heads * cylinders
				bytes_per_sector = 512
				write_linear(cpu, packet_addr + 2, information_flags, 2)
				write_linear(cpu, packet_addr + 4, cylinders, 4)
				write_linear(cpu, packet_addr + 8, heads, 4)
				write_linear(cpu, packet_addr + 12, spt, 4)
				write_linear(cpu, packet_addr + 16, total_sectors, 4)
				# Emulated device cannot have >32-bit sectors
				write_linear(cpu, packet_addr + 20, 0L, 4)
				write_linear(cpu, packet_addr + 24, bytes_per_sector, 2)
				if buffer_size >= 30:
					write_linear(cpu, packet_addr + 26, 0xFFFFFFFFL, 4)

	elif (AX & 0xff00) == 0x4100:
		bootloader_print("---- INT 13h (Check extensions present) emulated ----")
		cpu.edx = 0x21 + 1
		new_BX = 0xaa55
		new_CX = 5
		write_linear(cpu, register_addr + 8, new_BX, 2)
		write_linear(cpu, register_addr + 12, new_CX, 2)

	else:
		bootloader_print("---- INT 13h (AX=0x%x) not emulated ----" % AX)
		cpu.edx = 0
		#raise "Unknown BIOS call AX=0x%x" % AX

        loader.boot_file.close()

#
# Main function that emulates various INT calls
#
def bootloader_handler(group_loader, cpu, arg):
	if not cpu in group_loader[0]:
		return

	if (cpu.eax & 0xffff) == 0x4711:
		emulate_int19(group_loader[1], cpu)

	elif (cpu.eax & 0xffff) == 0x4712:
		emulate_int13(group_loader[1], cpu)

def bootloader_print(str):
	if SIM_get_verbose():
		print str
	pass

installed_bootloaders = []

def install_cdrom_bootloader(cpu_group):
	global installed_bootloaders
	new_loader = cdrom_bootloader()
	handle = SIM_hap_add_callback("Core_Magic_Instruction", bootloader_handler, (cpu_group, new_loader))
	installed_bootloaders.append((handle, cpu_group))
	print "CD-ROM bootloader for CPU group %s installed" % cpu_group

def remove_cdrom_bootloader(cpu):
	global installed_bootloaders
	hap_number = SIM_hap_get_number("Core_Magic_Instruction")
	for i in range(len(installed_bootloaders)):
		if cpu in installed_bootloaders[i][1]:
			print "Removing CD-ROM bootloader for CPU group %s" % installed_bootloaders[i][1]
			SIM_hap_remove_callback(hap_number, installed_bootloaders[i][0])
			del installed_bootloaders[i]
			return
