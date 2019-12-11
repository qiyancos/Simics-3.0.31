from cli import *
from string import *
import nic_common
import sim_commands

#
# --------------------- info, status --------------------
#

def get_info(obj):
    return ([(None,
              [("interrupt device", obj.irq_dev.name),
               ("interrupt level",  obj.irq_level)])] +
            nic_common.get_nic_info(obj))


def get_status(obj):
    return ([ ("Status and control registers",
               [("ISQ",      "0x%x" % (obj.ctrl_regs[0])),
                ("RxCFG",    "0x%x" % (obj.ctrl_regs[3])),
                ("RxEvent",  "0x%x" % (obj.ctrl_regs[4])),
                ("RxCTL",    "0x%x" % (obj.ctrl_regs[5])),
                ("TxCFG",    "0x%x" % (obj.ctrl_regs[7])),
                ("TxEvent",  "0x%x" % (obj.ctrl_regs[8])),
                ("TxCMD",    "0x%x" % (obj.ctrl_regs[9])),
                ("BufCFG",   "0x%x" % (obj.ctrl_regs[0xb])),
                ("BufEvent", "0x%x" % (obj.ctrl_regs[0xc])),
                ("RxMISS",   "0x%x" % (obj.ctrl_regs[0x10])),
                ("TxCOL",    "0x%x" % (obj.ctrl_regs[0x12])),
                ("LineCTL",  "0x%x" % (obj.ctrl_regs[0x13])),
                ("LineST",   "0x%x" % (obj.ctrl_regs[0x14])),
                ("SelfCTL",  "0x%x" % (obj.ctrl_regs[0x15])),
                ("SelfST",   "0x%x" % (obj.ctrl_regs[0x16])),
                ("BusCTL",   "0x%x" % (obj.ctrl_regs[0x17])),
                ("BusST",    "0x%x" % (obj.ctrl_regs[0x18])),
                ("TestCTL",  "0x%x" % (obj.ctrl_regs[0x19])),
                ("AUI_TDR",  "0x%x" % (obj.ctrl_regs[0x1c]))])] +
            nic_common.get_nic_status(obj))

nic_common.new_nic_commands("CS8900A")

sim_commands.new_info_command("CS8900A", get_info)
sim_commands.new_status_command("CS8900A", get_status)
