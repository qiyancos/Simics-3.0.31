from sim_commands import *

def get_info(obj):
    return [(None,
             [("Connected to", obj.link or obj.console),
              ("Recorder", obj.recorder),
              ("Transmit interval", "%d ns" % obj.xmit_time),
              ("Interrupt device", obj.irq_dev),
              ("Interrupt level", obj.irq_level)])]

def get_status(obj):
    return []
                
new_info_command('NS16450', get_info)
new_status_command('NS16450', get_status)
