
##  Copyright 2005-2007 Virtutech AB

from cli import *
from sim_commands import *

device_name = get_last_loaded_module()

def get_info(obj):
    return [(None,
             [("Current output level", "%d" % obj.level)])]

def get_status(obj):
    target_list = []
    for tgt in iff(obj.targets, obj.targets, []):
        if type(tgt) == list:
            target_list += [[tgt[0].name, "Port '%s'" % tgt[1]]]
        else:
            target_list += [[tgt.name, ""]]
                                                                 
    return [("Connected devices",
             [(("%s" % tgt[0], "%s" % tgt[1])) for tgt in target_list])]

new_info_command(device_name, get_info)
new_status_command(device_name, get_status)
