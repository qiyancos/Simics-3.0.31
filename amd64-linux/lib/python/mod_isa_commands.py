from sim_commands import *
from cli import *

def get_info(obj):
    return [ ("Connections",
              [ ("Legacy PIC", obj.pic),
                ("I/O-APIC", obj.ioapic) ]),
             ("IRQ to I/O-APIC pin assignment",
              [("IRQ %d" % i, "Pin %d" % obj.irq_to_pin[i]) for i in range(len(obj.irq_to_pin))]) ]

def get_status(obj):
    return [ ("IRQ status",
              [("IRQ %d" % i, iff(obj.irq_status[i], "active", "inactive")) for i in range(len(obj.irq_status))]) ]

new_info_command('ISA', get_info)
new_status_command('ISA', get_status)
