from cli import *
import sim_commands

def get_info(obj):
    return [("Connected processors",
             [(i, obj.cpu_list[i].name)
              for i in range(len(obj.cpu_list))])]

sim_commands.new_info_command("cpu-group", get_info)
