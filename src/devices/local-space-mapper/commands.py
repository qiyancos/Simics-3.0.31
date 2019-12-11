
##  Copyright 2003-2007 Virtutech AB

from cli import *
import sim_commands

def get_info(obj):
    spaces = obj.memory_spaces
    
    return [("Space translations",
             [(spaces[i][0].name, spaces[i][1].name)
              for i in range(len(spaces))])]

sim_commands.new_info_command("local-space-mapper", get_info)
