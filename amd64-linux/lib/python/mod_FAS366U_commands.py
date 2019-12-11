
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

#
# -------------------- info --------------------
#

def info_cmd(obj):
    print "FAS366U information"
    print "==================="
    try:
        irq_dev = SIM_get_attribute(obj, "irq_dev")
        irq_level = SIM_get_attribute(obj, "irq_level")
        dma_dev = SIM_get_attribute(obj, "dma_dev")
        scsi_bus = SIM_get_attribute(obj, "scsi_bus")
        own_id = SIM_get_attribute(obj, "scsi_target")
        command = SIM_get_attribute(obj, "command")
        command_name = SIM_get_attribute_idx(obj, "command_name", command)
        command_state = SIM_get_attribute(obj, "command_state")
        irq_pending = SIM_get_attribute(obj, "stat_interrupt")
        target_id = SIM_get_attribute(obj, "bus_id")
        irq_reg = SIM_get_attribute(obj, "interrupt")
        reselect = SIM_get_attribute(obj, "reselected")

        # FIFO stuff
        fifo = SIM_get_attribute(obj, "fifo")
        t_odd = SIM_get_attribute(obj, "fifo_have_t_odd")
        h_odd = SIM_get_attribute(obj, "fifo_have_h_odd")
        t_odd_byte = SIM_get_attribute(obj, "fifo_t_odd_byte")
        h_odd_byte = SIM_get_attribute(obj, "fifo_h_odd_byte")
        head = SIM_get_attribute(obj, "fifo_head")
        tail = SIM_get_attribute(obj, "fifo_tail")

        
    except Exception, msg:
        print "Error getting info from FAS366U device: %s" % msg
        return
    
    print "      Interrupt device : %s" % irq_dev
    print "       Interrupt level : %d" % irq_level
    print "            DMA device : %s" % dma_dev
    print
    print "         Interrupt reg : 0x%x" % irq_reg
    if irq_pending:
        print "     Interrupt pending : yes"
    else:
        print "     Interrupt pending : no"        
    print
    print "              SCSI bus : %s" % scsi_bus
    print "           Own SCSI id : %d" % own_id
    if (command_state == 0) and (reselect == 0):
        print "                 State : Disconnected"
        print "   Last Target SCSI id : %s" % target_id
        print "          Last Command : %s" % command_name
    else:
        if reselect > 0:
            print "                 State : Reselected Initiator"
        else:
            print "                 State : Initiator"
        print "        Target SCSI id : %s" % target_id
        print "               Command : %s" % command_name
    print
    if (head == tail) and (h_odd == 0):
        print "                  FIFO : empty"
    elif h_odd:
        print "        odd input byte :      0x%02x" % h_odd_byte
    if head != tail:
        pos = head
        while 1:
            if pos == head:
                str = "head"
            elif pos == tail:
                str = "tail"
            else:
                str = "    "
            print "                  %s : 0x%02x 0x%02x" % (str, (fifo[pos] >> 8) & 0xff, fifo[pos] & 0xff)
            pos = (pos + 1) % 16
            if pos == head:
                break
        if t_odd:
            print "       odd output byte : 0x%02x" % t_odd_byte

    
new_command("info", info_cmd,
            [],
            alias = "",
            type  = "FAS366U commands",
            short = "information about current state of the device",
            namespace = "FAS366U",
            doc = """
Print information about the state of the SCSI controller.<br/>
""", filename="/mp/simics-3.0/src/devices/FAS366U/commands.py", linenumber="103")
