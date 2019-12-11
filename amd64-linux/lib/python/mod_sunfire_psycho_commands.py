
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
              [ ("MID", obj.mid),
                ("Memory space", obj.io_space)]),
             ("PCI Bus A",
              [ ("Bus object", obj.pci_busA.name),
                ("Bus Number", "0x%x" % obj.PCI_A_pbm_regs[2]),
                ("Subordinate Bus", "0x%x" % obj.PCI_A_pbm_regs[3])]),
             ("PCI Bus B",
              [ ("Bus object", obj.pci_busB.name),
                ("Bus Number", "0x%x" % obj.PCI_B_pbm_regs[2]),
                ("Subordinate Bus", "0x%x" % obj.PCI_B_pbm_regs[3])])]

def get_status(obj):
    return [ ("Stream Buffer",
              [ ("A Enabled", yesno(obj.sbuf_enabled)),
                ("A Diagnostics", yesno(obj.sbuf_diag)),
                ("B Enabled", yesno(obj.sbuf_b_enabled)),
                ("B Diagnostics", yesno(obj.sbuf_b_diag))]),
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
    print "Interrupt            Valid   TID     State (for PCI INTA#, INTB# ...)"
    i = 0
    while i < tot_irq:

        # skip unused ones
        if irq_names[i][0:6] == "Unused":
            i = i + 1
            continue

        if irq_names[i][0:10] == "PCI A Slot" or irq_names[i][0:10] == "PCI B Slot":
            name = irq_names[i][0:12]
        else:
            name = irq_names[i]

        pr("%-20s    %d      %d     " % (name, valid[i], tid[i]))
        
        if irq_names[i][0:10] == "PCI A Slot" or irq_names[i][0:10] == "PCI B Slot":
            for j in range(0, 4):
                pr("%c%c " % (state_char[state[i + j]], iff(level[i + j], '+', ' ')))
            i = i + 4
        else:
            pr("%c%c " % (state_char[state[i]], iff(level[i], '+', ' ')))
            i = i + 1
        
        pr("\n")
    print

new_command("irq-info", irq_info_cmd,
            [],
            alias = "",
            type  = "sunfire-psycho commands",
            short = "print interrupt information",
	    namespace = "sunfire-psycho",
            doc = """
Print detailed information about the interrupt state for the sunfire-psycho device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-psycho/commands.py", linenumber="100")

new_info_command("sunfire-psycho", get_info)
new_status_command("sunfire-psycho", get_status)
