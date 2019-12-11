from sim_commands import *
from cli import *

def get_info(obj):
    return [ ("Connections",
              [ ("IRQ device", obj.irq_dev),
                ("IRQ level", obj.irq_level) ]) ]

def get_status(obj):
    return [ ("IRQ status",
              [ ("Port 0", iff(obj.input_status & 1, "active", "inactive")),
                ("Port 1", iff(obj.input_status & 2, "active", "inactive")),
                ("Port 2", iff(obj.input_status & 4, "active", "inactive")),
                ("Port 3", iff(obj.input_status & 8, "active", "inactive")) ]),
             ("Overall status",
              [ ("Enable", obj.enable),
                ("Scratchpad", obj.scratch) ]) ]

new_info_command('fourport', get_info)
new_status_command('fourport', get_status)
