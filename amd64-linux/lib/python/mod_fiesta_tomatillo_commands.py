
##  Copyright 2002-2007 Virtutech AB
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
irq_names= { 24 : "Primary IDE",
             25 : "RTC Power on",
             26 : "Secondary IDE",
             27 : "SB System Mngmnt",
             28 : "Broadcom LAN (Slot 4)",
             32 : "Power Button",
             33 : "PCIA PME#",
             34 : "Smart Card",
             35 : "PCIB PME#",
             36 : "Audio",
             38 : "USB2",
             39 : "USB1",
             42 : "UPA Slot",
             43 : "UPA Slot",
             44 : "Serial Port",
             45 : "Parallel Port",
             46 : "I2C Device",
             47 : "CPU Overheat",
             48 : "UE (ECC error)",
             49 : "CE (ECC Error)",
             50 : "AE (PCI Bus A Error)",
             51 : "BE (PCI_Bus B Error)",
             52 : "SE (JBus Error)"}

irq_remap = ["err", 3, 2, 1, 0, 5]

def get_irq_name(ino):
    if ino >= 4 and ino < 24:
        return "PCI slot %d, INT%s#" % (irq_remap[ino >> 2], irq_letter[ino & 0x3])
    try:
        return irq_names[ino]
    except:
        return ""

# NOTE/TODO: We would like to have the index into the register
# arrays accessed by name (i.e. get the enum names from c)
#

def info_cmd(obj):
    try:
        print "Safari Registers"
        print "================"
        print "Device ID          : 0x%016x" % obj.jbus_regs[0]
        print "Control/Status     : 0x%016x" % obj.jbus_regs[13]

        print "PCI-A Mem Match    : 0x%016x   PCI-A Mem Mask     : 0x%016x" % (obj.jbus_regs[5], obj.jbus_regs[6])
        print "PCI-A Cfg/IO Match : 0x%016x   PCI-A Cfg/IO Mask  : 0x%016x" % (obj.jbus_regs[7], obj.jbus_regs[8])
        print "PCI-B Mem Match    : 0x%016x   PCI-B Mem Mask     : 0x%016x" % (obj.jbus_regs[9], obj.jbus_regs[10])
        print "PCI-B Cfg/IO Match : 0x%016x   PCI-B Cfg/IO Mask  : 0x%016x" % (obj.jbus_regs[11], obj.jbus_regs[12])
        print
    except Exception, msg:
        print "Error reading tomatillo registers: %s" % msg
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
        print "IOMMU Control  : 0x%016x" % pci_regs[10]
        print "    TSB  Size  : %3dK" % (1 << ((pci_regs[10] >> 16) & 0x7))
        print "    Page Size  : %3dK" % ((((pci_regs[10] >> 2) & 0x1) * 7 + 1) * 8);
        print "      Enabled  :  %3s" % yes_or_no[int(pci_regs[10] & 0x1)]
        print "TSB Base Addr  : 0x%016x" % pci_regs[11]
        print
    except Exception, msg:
        print "Error reading tomatillo registers: %s" % msg
        return

def irq_cmd(obj):
    yes_or_no = ("no", "yes")
    state_name = ("Idle", "Received", "<error>", "Pending")
    try:
        pci_array_regs = SIM_get_attribute(obj, "PCI-A-array-regs")
        pci_irq_state = SIM_get_attribute(obj, "PCI-A-irq-state")
        pci_irq_level = SIM_get_attribute(obj, "PCI-A-irq-level")
        print "PCI IRQ Mappings"
        print "================"
        print "ino   V   nid aid  IGN INO   state lvl  Source"
        for i in range(64):
            print "%2d   %3s  %2d  %2d   %2d  %2d %8s  %d   %s" % (
                i,
                yes_or_no[(pci_array_regs[3][i] >> 31) & 0x1],
                (pci_array_regs[3][i] >> 21) & 0x1f,
                (pci_array_regs[3][i] >> 26) & 0x1f,
                (pci_array_regs[3][i] >> 6) & 0x1f,
                (pci_array_regs[3][i] >> 0) & 0x3f,
                state_name[pci_irq_state[i]],
                pci_irq_level[i],
                get_irq_name(i))
        print
    except Exception, msg:
        print "Error reading tomatillo registers: %s" % msg
        return

def pci_a_cmd(obj):
    print_pci_regs(obj, 0)
    
def pci_b_cmd(obj):
    print_pci_regs(obj, 1)

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
            type  = "fiesta-tomatillo commands",
            short = "print tomatillo registers",
            namespace = "fiesta-tomatillo",
            doc = """
Print the general registers in the tomatillo device<br/>
""", filename="/mp/simics-3.0/src/devices/fiesta-tomatillo/commands.py", linenumber="145")

new_command("pci-a-regs", pci_a_cmd,
            [],
            alias = "",
            type  = "fiesta-tomatillo commands",
            short = "print PCI-A registers",
            namespace = "fiesta-tomatillo",
            doc = """
Print the PCI-A registers in the tomatillo device.<br/>
""", filename="/mp/simics-3.0/src/devices/fiesta-tomatillo/commands.py", linenumber="155")

new_command("pci-b-regs", pci_b_cmd,
            [],
            alias = "",
            type  = "fiesta-tomatillo commands",
            short = "print PCI-A registers",
            namespace = "fiesta-tomatillo",
            doc = """
Print the PCI-A registers in the tomatillo device.<br/>
""", filename="/mp/simics-3.0/src/devices/fiesta-tomatillo/commands.py", linenumber="165")

new_command("pci-irqs", irq_cmd,
            [],
            alias = "",
            type  = "fiesta-tomatillo commands",
            short = "print PCI interrupts",
            namespace = "fiesta-tomatillo",
            doc = """
Print the PCI-A interrupt status and mappings in the tomatillo device.<br/>
""", filename="/mp/simics-3.0/src/devices/fiesta-tomatillo/commands.py", linenumber="175")

new_command("pci-a-iommu-translate", pci_a_xlate_cmd,
            [arg(uint64_t, "pci-address")],
            alias = "",
            type  = "fiesta-tomatillo commands",
            short = "translate PCI-A IOMMU address",
            namespace = "fiesta-tomatillo",
            doc = """
Translate a PCI-A address using the IOMMU.<br/>
""", filename="/mp/simics-3.0/src/devices/fiesta-tomatillo/commands.py", linenumber="185")

new_command("pci-b-iommu-translate", pci_b_xlate_cmd,
            [arg(uint64_t, "pci-address")],
            alias = "",
            type  = "fiesta-tomatillo commands",
            short = "translate PCI-B IOMMU address",
            namespace = "fiesta-tomatillo",
            doc = """
Translate a PCI-B address using the IOMMU.<br/>
""", filename="/mp/simics-3.0/src/devices/fiesta-tomatillo/commands.py", linenumber="195")
