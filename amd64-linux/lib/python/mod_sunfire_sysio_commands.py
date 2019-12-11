
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
from sim_commands import *

def yesno(value):
    return iff(value, "yes", "no")

def get_info(obj):
    return [ (None,
              [ ("MID", obj.mid)])]

def get_status(obj):
    return [ ("Stream Buffer",
              [ ("Enabled", yesno(obj.sbuf_enabled)),
                ("Diagnostics", yesno(obj.sbuf_diag)) ]),
             ("Counter 0",
              [ ("Value", "0x%x" % obj.count0),
                ("Limit", "0x%x" % obj.limit0),
                ("Periodic", yesno(obj.periodic0)),
                ("Irq enabled", yesno(obj.inten0)),
                ("Irq pending", yesno(obj.irq_pending0))]),
             ("Counter 1",
              [ ("Value", "0x%x" % obj.count1),
                ("Limit", "0x%x" % obj.limit1),
                ("Periodic", yesno(obj.periodic1)),
                ("Irq enabled", yesno(obj.inten1)),
                ("Irq pending", yesno(obj.irq_pending1))])]

#
# ---------------------- irq-info ----------------------
#

state_char = "ITRP"

def irq_info_cmd(obj):
    valid = obj.valid
    tid = obj.tid
    state = obj.state
    level = obj.level
    irq_names = obj.irq_names[None]
    tot_irq = len(irq_names)
    print
    print "Interrupt          Valid   TID     State (for sbus level 1, 2, ..., 7)"
    i = 0
    while i < tot_irq:

        # skip unused ones
        if irq_names[i][0:6] == "Unused":
            i = i + 1
            continue

        pr("%-20s    %d      %d     " % (irq_names[i], valid[i], tid[i]))
        
        if irq_names[i][0:9] == "SBus Slot":
            for j in range(1, 8):
                pr("%c%c " % (state_char[state[i + j]], iff(level[i + j], '+', ' ')))
            i = i + 8
        else:
            pr("%c%c " % (state_char[state[i]], iff(level[i], '+', ' ')))
            i = i + 1
        
        pr("\n")


new_command("irq-info", irq_info_cmd,
            [],
            alias = "",
            type  = "sunfire-sysio commands",
            short = "print interrupt information",
	    namespace = "sunfire-sysio",
            doc = """
Print detailed information about the interrupt state for the sunfire-sysio device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-sysio/commands.py", linenumber="84")

#
# ---------------------- sbus-info ----------------------
#

slot_id = (0, 1, 2, 3, 13, 14, 15)
ba_sizes = (8, 16, 32, 64)

def sbus_info_cmd(obj):
    try:
        ctrl = SIM_get_attribute(obj, "ctrl")
        cfg = SIM_get_attribute(obj, "sbus_cfg")
        num_sbuses = len(cfg)
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return
    print
    print "           Access Latency : %s" % iff(ctrl & 0x400, "fast", "slow")
    print "  Power Management Wakeup : %sabled" % iff(ctrl & 0x200, "en", "dis")
    print "     SBus Error Interrupt : %sabled" % iff(ctrl & 0x100, "en", "dis")
    print
    print "Sbus DVMA Arbitration"
    for i in range(num_sbuses):
        print "                  Slot %2d :  %sabled" % (slot_id[i], iff(ctrl & (1 << i), "en", "dis"))
    print
    print "SBus Slot Configuration Registers"
    for i in range(num_sbuses):
        print "Slot %d" % slot_id[i]
        print "   Segment Address (SEGA) : 0x%016x" % ((cfg[i] & 0x7ff0000) << 14)
        print "   IOMMU bypass cacheable : %s" % iff(cfg[i] & 0x8000, "yes", "no")
        print "   Extended Transfer Mode : %s" % iff(cfg[i] & 0x4000, "yes", "no")
        print "     SBus Parity Checking : %sabled" % iff(cfg[i] & 0x1000, "en", "dis")
        pr("       Bus Transfer Sizes : ")
        for j in range(4):
            if (cfg[i] >> 1 & 0xf) & (1 << j):
                pr("%d " % ba_sizes[j])
        pr("\n")
        print "        IOMMU Bypass Mode : %sabled" % iff(cfg[i] & 0x1, "en", "dis")

new_command("sbus-info", sbus_info_cmd,
            [],
            alias = "",
            type  = "sunfire-sysio commands",
            short = "print information about the device",
	    namespace = "sunfire-sysio",
            doc = """
Print detailed information about the sbus settings for the sunfire-sysio device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-sysio/commands.py", linenumber="132")

new_info_command("sunfire-sysio", get_info)
new_status_command("sunfire-sysio", get_status)
