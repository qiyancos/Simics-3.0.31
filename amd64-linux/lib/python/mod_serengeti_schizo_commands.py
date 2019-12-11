
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

irq_letter=["A", "B", "C", "D"]
irq_names= { 42 : "UPA Slot",
             43 : "UPA Slot",
             48 : "UE (ECC error)",
             49 : "CE (ECC Error)",
             50 : "AE (PCI Bus A Error)",
             51 : "BE (PCI_Bus B Error)",
             52 : "SE (Safari Bus Error)",
             56 : "NewLink",
             57 : "NewLink",
             58 : "NewLink",
             59 : "NewLink",
             60 : "NewLink",
             61 : "NewLink",
             62 : "NewLink"}

def get_irq_name(ino):
    try:
        return irq_names[ino]
    except:
        if ino < 32:
            return "PCI slot %d, INT%s#" % (ino >> 2, irq_letter[ino & 0x3])
        elif ino < 48:
            return "OBIO"
        else:
            return ""

# NOTE/TODO: We would like to have the index into the register
# arrays accessed by name (i.e. get the enum names from c)
#

def info_cmd(obj):
    try:
        print "Safari Registers"
        print "================"
        print "Device ID          : 0x%016x" % obj.safari_regs[0]
        print "Control/Status     : 0x%016x" % obj.safari_regs[17]

        print "PCI-A Mem Match    : 0x%016x   PCI-A Mem Mask     : 0x%016x" % (obj.safari_regs[9], obj.safari_regs[10])
        print "PCI-A Cfg/IO Match : 0x%016x   PCI-A Cfg/IO Mask  : 0x%016x" % (obj.safari_regs[11], obj.safari_regs[12])
        print "PCI-B Mem Match    : 0x%016x   PCI-B Mem Mask     : 0x%016x" % (obj.safari_regs[13], obj.safari_regs[14])
        print "PCI-B Cfg/IO Match : 0x%016x   PCI-B Cfg/IO Mask  : 0x%016x" % (obj.safari_regs[15], obj.safari_regs[16])
        print
    except Exception, msg:
        print "Error reading schizo registers: %s" % msg
        return

def print_pci_regs(obj, pci):
    yes_or_no = ("no", "yes")
    try:
        if pci == 0:
            pci_regs = SIM_get_attribute(obj, "PCI-A-regs")
            print "PCI-A Registers"
        else:
            pci_regs = SIM_get_attribute(obj, "PCI-B-regs")
            print "PCI-B Registers"
        print "================"
        print "Control/Status : 0x%016x" % pci_regs[0]
        print "IOMMU Control  : 0x%016x" % pci_regs[5]
        print "    TSB  Size  : %3dK" % (1 << ((pci_regs[5] >> 16) & 0x7))
        print "    Page Size  : %3dK" % ((((pci_regs[5] >> 2) & 0x1) * 7 + 1) * 8);
        print "      Enabled  :  %3s" % yes_or_no[int(pci_regs[5] & 0x1)]
        print "TSB Base Addr  : 0x%016x" % pci_regs[6]
        print
    except Exception, msg:
        print "Error reading schizo registers: %s" % msg
        return

def print_pci_irqs(obj, pci):
    yes_or_no = ("no", "yes")
    state_name = ("Idle", "Received", "<error>", "Pending")
    try:
        if pci == 0:
            pci_array_regs = SIM_get_attribute(obj, "PCI-A-array-regs")
            pci_irq_state = SIM_get_attribute(obj, "PCI-A-irq-state")
            pci_irq_level = SIM_get_attribute(obj, "PCI-A-irq-level")
            print "PCI-A IRQ Mappings"
        else:
            pci_array_regs = SIM_get_attribute(obj, "PCI-B-array-regs")
            pci_irq_state = SIM_get_attribute(obj, "PCI-B-irq-state")
            pci_irq_level = SIM_get_attribute(obj, "PCI-B-irq-level")
            print "PCI-B IRQ Mappings"
        print "=================="
        print "ino   V   nid aid  IGN INO   state lvl  Source"
        for i in range(64):
            print "%2d   %3s  %2d  %2d   %2d  %2d %8s  %d   %s" % (
                i,
                yes_or_no[(pci_array_regs[0][i] >> 31) & 0x1],
                (pci_array_regs[0][i] >> 21) & 0x1f,
                (pci_array_regs[0][i] >> 26) & 0x1f,
                (pci_array_regs[0][i] >> 6) & 0x1f,
                (pci_array_regs[0][i] >> 0) & 0x3f,
                state_name[pci_irq_state[i]],
                pci_irq_level[i],
                get_irq_name(i))
        print
    except Exception, msg:
        print "Error reading schizo registers: %s" % msg
        return

def pci_a_cmd(obj):
    print_pci_regs(obj, 0)
    
def pci_b_cmd(obj):
    print_pci_regs(obj, 1)

def irq_a_cmd(obj):
    print_pci_irqs(obj, 0)
    
def irq_b_cmd(obj):
    print_pci_irqs(obj, 1)

def pci_a_xlate_cmd(obj, va):
    try:
        pa = obj.PCI_A_IOMMU_translation[va]
        return pa
    except:
        print "Failed translating PCI address 0x%x" % va

def pci_b_xlate_cmd(obj, va):
    try:
        pa = obj.PCI_B_IOMMU_translation[va]
        return pa
    except:
        print "Failed translating PCI address 0x%x" % va

new_command("pregs", info_cmd,
            [],
            alias = "",
            type  = "serengeti-schizo commands",
            short = "print schizo registers",
            namespace = "serengeti-schizo",
            doc = """
Print the general registers in the schizo device<br/>
""", filename="/mp/simics-3.0/src/devices/serengeti-schizo/commands.py", linenumber="149")

new_command("pci-a-regs", pci_a_cmd,
            [],
            alias = "",
            type  = "serengeti-schizo commands",
            short = "print PCI-A registers",
            namespace = "serengeti-schizo",
            doc = """
Print the PCI-A registers in the schizo device.<br/>
""", filename="/mp/simics-3.0/src/devices/serengeti-schizo/commands.py", linenumber="159")

new_command("pci-b-regs", pci_b_cmd,
            [],
            alias = "",
            type  = "serengeti-schizo commands",
            short = "print PCI-A registers",
            namespace = "serengeti-schizo",
            doc = """
Print the PCI-A registers in the schizo device.<br/>
""", filename="/mp/simics-3.0/src/devices/serengeti-schizo/commands.py", linenumber="169")

new_command("pci-a-irqs", irq_a_cmd,
            [],
            alias = "",
            type  = "serengeti-schizo commands",
            short = "print PCI-A interrupts",
            namespace = "serengeti-schizo",
            doc = """
Print the PCI-A interrupt status and mappings in the schizo device.<br/>
""", filename="/mp/simics-3.0/src/devices/serengeti-schizo/commands.py", linenumber="179")

new_command("pci-b-irqs", irq_b_cmd,
            [],
            alias = "",
            type  = "serengeti-schizo commands",
            short = "print PCI-B interrupts",
            namespace = "serengeti-schizo",
            doc = """
Print the PCI-A interrupt status and mappings in the schizo device.<br/>
""", filename="/mp/simics-3.0/src/devices/serengeti-schizo/commands.py", linenumber="189")

new_command("pci-a-iommu-translate", pci_a_xlate_cmd,
            [arg(uint64_t, "pci-address")],
            alias = "",
            type  = "serengeti-schizo commands",
            short = "translate PCI-A IOMMU address",
            namespace = "serengeti-schizo",
            doc = """
Translate a PCI-A address using the IOMMU.<br/>
""", filename="/mp/simics-3.0/src/devices/serengeti-schizo/commands.py", linenumber="199")

new_command("pci-b-iommu-translate", pci_b_xlate_cmd,
            [arg(uint64_t, "pci-address")],
            alias = "",
            type  = "serengeti-schizo commands",
            short = "translate PCI-B IOMMU address",
            namespace = "serengeti-schizo",
            doc = """
Translate a PCI-B address using the IOMMU.<br/>
""", filename="/mp/simics-3.0/src/devices/serengeti-schizo/commands.py", linenumber="209")
