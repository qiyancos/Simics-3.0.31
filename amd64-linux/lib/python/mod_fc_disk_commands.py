
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

from cli import *

#
# -------------------- info --------------------
#

def info_cmd(obj):
    dev_name = obj.classname
    print "%s information" % dev_name
    print "====================="
    try:
        if dev_name == "fc-disk":
            geom = SIM_get_attribute(obj, "geometry")
        tgt = SIM_get_attribute(obj, "loop-id")

        ctrl = SIM_get_attribute(obj, "fc-controller")
        sense = SIM_get_attribute(obj, "sense_key")
        lastcmd = SIM_get_attribute(obj, "last-command")
        cmd_name = SIM_get_attribute_idx(obj, "scsi_commands", lastcmd)
    except Exception, msg:
        print "Error getting info from %s: %s" % (dev_name, msg)
        return

    print "                Cylinders: %5d" % geom[0]
    print "                   Heads : %5d" % geom[1]
    print "       Sectors per track : %5d" % geom[2]
    print

    print "           FC Controller : %s" % ctrl
    print "                 Loop ID : %d" % tgt
    print
    print "            Last command : %d (%s)" % (lastcmd, cmd_name)
    print "          Last SENSE key : %d" % sense
    print
    print "        Sectors read     : %d  ( = %d bytes)" % (obj.sectors_read, obj.sectors_read * 512)
    print "        Sectors written  : %d  ( = %d bytes)" % (obj.sectors_written, obj.sectors_written * 512)
    print

new_command("info", info_cmd,
            [],
            alias = "",
            type  = "fc-disk commands",
            short = "information about current state of the fibre-channel disk",
            namespace = "fc-disk",
            doc = """
Print information about the state of the fibre-channel disk.<br/>
""", filename="/mp/simics-3.0/src/devices/fc-disk/commands.py", linenumber="59")

try:
    from sun_vtoc_commands import *
    create_sun_vtoc_commands("fc-disk")
except:
    pass
