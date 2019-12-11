
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
# disk.py
#
# set disk geometry and size from a simnow-style disk image
#
# Magnus Christensson
#

import os

# offset 2(2)    disk_cylinders
# offset 6(2)    disk_heads
# offset 12(2)   disk_sectors_per_track
# offset 114(4)  disk_sectors
# offset 256(4)  cmos cyls
# offset 260(2)  cmos hds
# offset 262(2)  cmos spt

def read_uchar(fp):
	return ord(fp.read(1))

def read_ushort(fp):
	return read_uchar(fp) + 256L * read_uchar(fp)

def read_ulong(fp):
	return read_ushort(fp) + 256L * 256L * read_ushort(fp)

def get_file_size(file):
	return os.stat(file).st_size

def get_size_from_identify_block(image_file_name):
        lookup_file_name = SIM_lookup_file(image_file_name)
        if not lookup_file_name:
                print "Can't find image file:", image_file_name
                SIM_command_has_problem()
                return -1
        return get_file_size(lookup_file_name)

def get_geometry_from_identify_block(image_file_name):
        print "Reading geometry data from %s..." % image_file_name
        lookup_file_name = SIM_lookup_file(image_file_name)
        if not lookup_file_name:
                print "Can't find image file:", image_file_name
                SIM_command_has_problem()
                return
	fp = open(lookup_file_name, "rb")
	fp.seek(2)
	disk_cylinders = read_ushort(fp)
	print "IDE cylinders = %d" % disk_cylinders
	fp.seek(6)
	disk_heads = read_ushort(fp)
	print "IDE heads = %d" % disk_heads
	fp.seek(12)
	disk_spt = read_ushort(fp)
	print "IDE spt = %d" % disk_spt
	fp.seek(114)
	disk_sectors = read_ulong(fp)
	print "IDE sectors = %d" % disk_sectors
	if disk_heads > 16 or disk_spt > 63 or (disk_cylinders * disk_heads * disk_spt) > disk_sectors:
		print "WARNING. Weird values read from simnow header!"
	conf.disk0.disk_cylinders = disk_cylinders
	conf.disk0.disk_heads = disk_heads
	conf.disk0.disk_sectors_per_track = disk_spt
	conf.disk0.disk_sectors = disk_sectors
	fp.seek(256)
	cmos_cyls = read_ulong(fp)
	print "BIOS cylinders = %d" % cmos_cyls
	fp.seek(260)
	cmos_hds = read_ushort(fp)
	print "BIOS heads = %d" % cmos_hds
	fp.seek(262)
	cmos_spt = read_ushort(fp)
	print "BIOS spt = %d" % cmos_spt
	run("rtc0.cmos-hd C %d %d %d" % (cmos_cyls, cmos_hds, cmos_spt), "")
	if cmos_cyls == 0 or cmos_hds < 10 or cmos_hds > 255 or cmos_spt < 10 or cmos_spt > 63:
		print "*** This does not look like a valid BIOS geometry, override with 'rtc0.cmos-hd C <cyls> <hds> <spt>'."
	fp.close()
	conf.disk0_image.files = [[lookup_file_name, 1, 0, get_file_size(lookup_file_name) - 512, 512]]
