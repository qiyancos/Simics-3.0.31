
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

import os
import sim_commands

#
# -------------------- save-diff-file ----------------
#

def image_save_diff(obj, file):
    sim_commands.image_save_diff(obj.image, file)

new_command("save-diff-file", image_save_diff,
	    [ arg(filename_t(), "filename") ],
	    type = "scsi-disk commands",
	    short = "save diff file to disk",
            see_also = ['<scsi-disk>.add-diff-file', '<image>.save-diff-file'],
	    namespace = "scsi-disk",
	    doc = """
Writes changes to the image as a diff file in craff format. This is basically
the same command as &lt;image&gt;.safe-diff-file.
""", filename="/mp/simics-3.0/src/extensions/scsi-disk/commands.py", linenumber="34")

#
# -------------------- add-diff-file ----------------
#

def image_add_diff(obj, file):
    sim_commands.image_add_diff(obj.image, file)

new_command("add-diff-file", image_add_diff,
	    [ arg(filename_t(), "filename") ],
	    type = "scsi-disk commands",
	    short = "add a diff file to the image",
            see_also = ['<scsi-disk>.save-diff-file', '<image>.add-diff-file'],
	    namespace = "scsi-disk",
	    doc = """
Add a diff file to the list of files for an disk. The diff file
was typically created with the 'save-diff-file' command, or by
a saved configuration. This is basically the same command as
&lt;image&gt;.add-diff-file.
""", filename="/mp/simics-3.0/src/extensions/scsi-disk/commands.py", linenumber="52")

#
# -------------------- add-partial-diff-file ----------------
#

def image_add_partial_diff(obj, file, start, size):
    sim_commands.image_add_partial_diff(obj.image, file, start, size)

new_command("add-diff-partial-file", image_add_partial_diff,
	    [ arg(filename_t(), "filename"), arg(int_t, "start"), arg(int_t, "size") ],
            type = "scsi-disk commands",
            short = "add a partial diff file to the image",
            see_also = ['<scsi-disk>.save-diff-file', '<image>.add-diff-file'],
            namespace = "scsi-disk",
            doc = """
Add a diff file to the list of files for an disk. The diff file was
typically created with the 'save-diff-file' command, by one of the
dump-*-partition commands, or by a saved configuration. This is
basically the same command as &lt;image&gt;.add-diff-file.
""", filename="/mp/simics-3.0/src/extensions/scsi-disk/commands.py", linenumber="72")


#
# -------------------- info --------------------
#

def get_info(obj):
    if obj.classname == "scsi-cdrom":
        if obj.cd_media:
            media = [("Connected media", "%s (file: %s)" % (obj.cd_media.name,
                                                            obj.cd_media.file))]
        else:
            media = [("Connected media", "empty")]
    else:
        geom = obj.geometry
        media = [("Sectors", "%d" % (geom[0] * geom[1] * geom[2]))]

    return [(None,
             [("Vendor", obj.vendor),
              ("Model", obj.model),
              ("Revision", obj.revision),
              ("Serial", obj.vendor_specific_id)]
             + media),
            (None,
             [("SCSI bus", obj.scsi_bus.name),
              ("SCSI ID", "%d" % obj.scsi_target)])]

def get_status(obj):
    lun = obj.lun
    # fix for init value
    if lun < 0 or lun > 100000:
        lun = 0

    sense = obj.sense_key
    lastcmd = obj.command
    lastmsg = obj.mesg_buffer
    cmd_name = obj.scsi_commands[lastcmd[0]]
    bus = obj.scsi_bus
    if lastmsg == 0x01: # extended message
        msg_name = bus.scsi_messages[lastmsg[2]]
    else:
        msg_name = bus.scsi_ext_messages[lastmsg[0]]

    if obj.reselect_op > 0:
        resel_tgt = "%d" % obj.reselect_id
    else:
        resel_tgt = "none"

    st = [("Last command", "%d (%s)" % (lastcmd[0], cmd_name)),
          # TODO: check if extended message, then print actual message
          ("Last message (in or out)", "%d (%s)" % (lastmsg[0], msg_name)),
          ("Last selected LUN", "%d" % lun),
          ("Last SENSE key", "%d" % sense),
          ("Target to reselect", resel_tgt)]

    if obj.classname == "scsi-disk":
        st += [("Sectors read",
                "%d  ( = %d bytes)" % (obj.sectors_read, obj.sectors_read * 512)),
               ("Sectors written",
                "%d  ( = %d bytes)" % (obj.sectors_written, obj.sectors_written * 512))]
    else:
        st += [("Sectors read",
                "%d  ( = %d bytes)" % (obj.sectors_read, obj.sectors_read * 2048)),
               ("Sectors written",
                "%d  ( = %d bytes)" % (obj.sectors_written, obj.sectors_written * 2048))]
    return [(None, st)]

# will only be called for scsi-disk itself
sim_commands.new_info_command("scsi-disk", get_info)
sim_commands.new_status_command("scsi-disk", get_status)

try:
    from sun_vtoc_commands import *
    create_sun_vtoc_commands("scsi-disk")
except:
    pass

try:
    from pc_disk_commands import *
    create_pc_partition_table_commands("scsi-disk")
except:
    pass
