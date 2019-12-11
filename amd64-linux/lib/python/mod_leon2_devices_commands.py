from cli import *
import sim_commands
import string

def info(obj):
    return []

def status(obj):
    return [ (None,
              [ ("Attribute a", "%d" % obj.a)])]

    
sim_commands.new_info_command("sample_device_dml", info)
sim_commands.new_status_command("sample_device_dml", status)
