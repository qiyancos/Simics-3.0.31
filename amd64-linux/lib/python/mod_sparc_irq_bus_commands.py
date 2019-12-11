
##  Copyright 2003-2007 Virtutech AB

from cli import *
import sim_commands

def get_info(obj):
    tgts = obj.object_list

    return [("Connected processors",
             [(("%2d" % tgts[i][0]), tgts[i][1].name)
              for i in range(len(tgts))])]

sim_commands.new_info_command("sparc-irq-bus", get_info)
