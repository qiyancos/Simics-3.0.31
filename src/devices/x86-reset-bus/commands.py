
##  Copyright 2005-2007 Virtutech AB

from cli import *
import sim_commands

def get_info(obj):
    return [("Connected processors:",
             [('', tgt.name)
              for tgt in obj.reset_targets])]

sim_commands.new_info_command("x86-reset-bus", get_info)
