
##  Copyright 2000-2007 Virtutech AB

from cli import *
import sim_commands

#
# -------------------- info --------------------
#

low_high = ("low", "high")

def get_info(obj):
    tgts = obj.targets

    return [("Connected devices",
             [(("%2d" % tgts[i][0]), tgts[i][1])
              for i in range(len(tgts))])]
    
def get_status(obj):
    phase = obj.phase
    phase_name = obj.scsi_phases[phase]
    atn = int(obj.atn)
    init = obj.initiator
    tgt = obj.target

    return [(None,
             [("Current Phase", phase_name),
              ("ATN", low_high[atn]),
              ("Current/last Initiator", "%d" % init),
              ("Current/last Target", "%d" % tgt)])]
    
sim_commands.new_info_command("scsi-bus", get_info)
sim_commands.new_status_command("scsi-bus", get_status)
