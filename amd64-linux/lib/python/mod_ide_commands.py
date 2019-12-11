
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

from cli import *
import sim_commands

#
# -------------------- insert --------------------
#

def insert_cmd(obj, medium):
    try:
        obj.cd_media = medium
        print "Inserting media '%s' in CD-ROM drive" % medium.name
    except Exception, msg:
        print "Error inserting media: %s" % msg

new_command("insert", insert_cmd,
            [arg(obj_t("object", "cdrom_media"), "media")],
            alias = "",
            type  = "ide-cdrom commands",
            short = "insert media in CD-ROM drive",
            namespace = "ide-cdrom",
            doc = """
Insert a media in the CD-ROM drive. The media is the name of
a CD-ROM media object, e.g. a file-cdrom or host-cdrom object.<br/>
""", filename="/mp/simics-3.0/src/devices/ide/commands.py", linenumber="35")

#
# -------------------- eject --------------------
#

def eject_cmd(obj):
    try:
        obj.cd_media = None
        print "Ejecting media from CD-ROM drive"
    except Exception, msg:
        print "Error ejecting media: %s" % msg

new_command("eject", eject_cmd,
            [],
            alias = "",
            type  = "ide-cdrom commands",
            short = "eject media from CD-ROM drive",
            namespace = "ide-cdrom",
            doc = """
Eject a media from the CD-ROM drive. The media must have been
previously inserted with the 'insert' command.<br/>
""", filename="/mp/simics-3.0/src/devices/ide/commands.py", linenumber="57")

def get_info(obj):
    if obj.classname == "ide-cdrom":
        if obj.cd_media:
            media = [("Connected media", "%s (file: %s)" % (obj.cd_media.name,
                                                            obj.cd_media.file))]
        else:
            media = [("Connected media", "empty")]
    else:
        media = [("Cylinders", "%5d" % obj.disk_cylinders),
                 ("Heads", "%5d" % obj.disk_heads),
                 ("Sectors per track", "%5d" % obj.disk_sectors_per_track),
                 ("Total sector count", "%5d" % obj.disk_sectors)]

    return [(None,
             [("Model ID", obj.model_id),
              ("Firmware ID", obj.firmware_id),
              ("Serial Number", obj.serial_number)]
             + media)]

sim_commands.new_info_command("ide-cdrom", get_info)
sim_commands.new_info_command("ide-disk", get_info)
# No status commands, since there isn't much status to show

#
# -------------- default-translation ------------
#
#disk_cylinders disk_heads disk_sectors_per_track
def translation_cmd(obj, c, h, s):

    if c == -1 & h == -1 & s == -1:
        str = "Current"
    else:
        str = "New"

    try:
        if c == -1:
            c = SIM_get_attribute(obj, "disk_cylinders")
        else:
            SIM_set_attribute(obj, "disk_cylinders", c)
        if h == -1:
            h = SIM_get_attribute(obj, "disk_heads")
        else:
            SIM_set_attribute(obj, "disk_heads", h)
        if s == -1:
            s = SIM_get_attribute(obj, "disk_sectors_per_track")
        else:
            SIM_set_attribute(obj, "disk_sectors_per_track", s)
    except Exception, msg:
        print "Error setting/getting disk information: %s", msg

    print "%s translation: C=%d H=%d S=%d" % (str, c, h, s)


new_command("default-translation", translation_cmd,
            [arg(int_t, "C", "?", -1), arg(int_t, "H", "?", -1), arg(int_t, "S", "?", -1)],
            alias = "",
            type  = "ide-disk commands",
            short = "get or set the default CHS translation",
            namespace = "ide-disk",
            doc = """
Set the default CHS translation of a disk, or get the current one
if no arguments are given.<br/>
""", filename="/mp/simics-3.0/src/devices/ide/commands.py", linenumber="121")

import os
import sim_commands

#
# -------------------- save-diff-file ----------------
#

def image_save_diff(obj, file):
    sim_commands.image_save_diff(obj.image, file)

new_command("save-diff-file", image_save_diff,
	    [ arg(filename_t(), "filename") ],
	    type = "ide-disk commands",
	    short = "save diff file to disk",
            see_also = ['<ide-disk>.add-diff-file', '<image>.save-diff-file'],
	    namespace = "ide-disk",
	    doc = """
Writes changes to the image as a diff file in craff format. This is basically
the same command as &lt;image&gt;.safe-diff-file.
""", filename="/mp/simics-3.0/src/devices/ide/commands.py", linenumber="142")

#
# -------------------- add-diff-file ----------------
#

def image_add_diff(obj, file):
    sim_commands.image_add_diff(obj.image, file)

new_command("add-diff-file", image_add_diff,
	    [ arg(filename_t(), "filename") ],
	    type = "ide-disk commands",
	    short = "add a diff file to the image",
            see_also = ['<ide-disk>.save-diff-file', '<image>.add-diff-file'],
	    namespace = "ide-disk",
	    doc = """
Add a diff file to the list of files for an disk. The diff file
was typically created with the 'save-diff-file' command, or by
a saved configuration. This is basically the same command as
&lt;image&gt;.add-diff-file.
""", filename="/mp/simics-3.0/src/devices/ide/commands.py", linenumber="160")

#
# -------------------- add-partial-diff-file ----------------
#

def image_add_partial_diff(obj, file, start, size):
    sim_commands.image_add_partial_diff(obj.image, file, start, size)

new_command("add-diff-partial-file", image_add_partial_diff,
            [ arg(filename_t(), "filename"), arg(int_t, "start"), arg(int_t, "size") ],
            type = "ide-disk commands",
            short = "add a partial diff file to the image",
            see_also = ['<ide-disk>.save-diff-file', '<image>.add-diff-file'],
            namespace = "ide-disk",
            doc = """
Add a diff file to the list of files for an disk. The diff file was
typically created with the 'save-diff-file' command, by one of the
dump-*-partition commands, or by a saved configuration. This is
basically the same command as &lt;image&gt;.add-diff-file.
""", filename="/mp/simics-3.0/src/devices/ide/commands.py", linenumber="180")

#
# -------------------- ide info commands ----------------
# 

def ide_get_info(obj):
    return [ (None,
              [ ("IRQ device", obj.irq_dev),
                ("IRQ number", obj.irq_level),
                ("Interrupt delay", obj.interrupt_delay),
                ("Model DMA delay", obj.model_dma_delay),
                ("Master", obj.master),
                ("Slave", obj.slave),
                ("Bus master DMA", obj.bus_master_dma) ] ) ]

def ide_get_status(obj):
    return [ (None,
              [ ("Selected drive", obj.selected_drive),
                ("LBA mode", obj.lba_mode),
                ("Interrupt request status", obj.interrupt_pin),
                ("DMA ready", obj.dma_ready) ] ) ]
                 
sim_commands.new_info_command("ide", ide_get_info)
sim_commands.new_status_command("ide", ide_get_status)


try:
	from pc_disk_commands import *
	create_pc_partition_table_commands("ide-disk")
except:
	pass

try:
    from sun_vtoc_commands import *
    create_sun_vtoc_commands("ide-disk")
except:
    pass
