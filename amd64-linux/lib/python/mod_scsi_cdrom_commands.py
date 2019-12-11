
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

try:
    # commands from scsi-disk
    from mod_scsi_disk_commands import *
    sim_commands.new_info_command("scsi-cdrom", get_info)
    sim_commands.new_status_command("scsi-cdrom", get_status)
except:
    print "Cannot include scsi-disk commands"

#
# -------------------- insert --------------------
#

def insert_cmd(obj, medium):
    try:
        obj.cd_media = medium
        print "Inserting medium '%s' in CD-ROM drive" % medium.name
    except Exception, msg:
        print "Error inserting medium: %s" % msg

new_command("insert", insert_cmd,
            [arg(obj_t("object", "cdrom_media"), "medium")],
            alias = "",
            type  = "scsi-cdrom commands",
            short = "insert medium in CD-ROM drive",
            namespace = "scsi-cdrom",
            doc = """
Insert a medium in the CD-ROM drive. The medium is the name of
a CD-ROM media object, e.g. a file-cdrom or host-cdrom object.<br/>
""", filename="/mp/simics-3.0/src/extensions/scsi-cdrom/commands.py", linenumber="43")

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
            type  = "scsi-cdrom commands",
            short = "eject media from CD-ROM drive",
            namespace = "scsi-cdrom",
            doc = """
Eject a media from the CD-ROM drive. The media must have been
previously inserted with the 'insert' command.<br/>
""", filename="/mp/simics-3.0/src/extensions/scsi-cdrom/commands.py", linenumber="65")
