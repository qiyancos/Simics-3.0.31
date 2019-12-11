from cli import *
from sim_commands import *

#
# ------------------------ info -----------------------
#

def get_info(obj):
        return [ (None,
                  [ ("Connected on bus", obj.apic_bus),
                    ("APIC id", obj.apic_id),
                    ("CPU", obj.cpu) ]) ]

new_info_command('apic', get_info)

def get_status(obj):
        lvt_timer = obj.lvt_timer
        lvt_lint0 = obj.lvt_lint0
        lvt_lint1 = obj.lvt_lint1
        lvt_error = obj.lvt_error
        lvt_perf_counter = obj.lvt_performance_counter

        delivery_mode = ("Fixed", "Reserved", "SMI", "Reserved", "NMI", "INIT", "Reserved", "ExtINT")

        return [ ("LVT Timer",
                  [ ("Mode", iff(lvt_timer & 0x20000, "Periodic", "One-shot")),
                    ("Mask", iff(lvt_timer & 0x10000, "Masked", "Not masked")),
                    ("Delivery status", iff(lvt_timer & 0x1000, "Send pending", "Idle")),
                    ("Vector", lvt_timer & 0xff) ]),
                 ("LVT LINT0",
                  [ ("Mode", iff(lvt_lint0 & 0x20000, "Periodic", "One-shot")),
                    ("Mask", iff(lvt_lint0 & 0x10000, "Masked", "Not masked")),
                    ("Trigger", iff(lvt_lint0 & 0x8000, "Level", "Edge")),
                    ("Remote IRR", iff(lvt_lint0 & 0x4000, "1", "0")),
                    ("Input polarity", iff(lvt_lint0 & 0x2000, "1", "0")),
                    ("Delivery status", iff(lvt_lint0 & 0x1000, "Send pending", "Idle")),
                    ("Delivery mode", delivery_mode[(lvt_lint0 >> 8) & 0x7]),
                    ("Vector", lvt_lint0 & 0xff) ]),
                 ("LVT LINT1",
                  [ ("Mode", iff(lvt_lint1 & 0x20000, "Periodic", "One-shot")),
                    ("Mask", iff(lvt_lint1 & 0x10000, "Masked", "Not masked")),
                    ("Trigger", iff(lvt_lint1 & 0x8000, "Level", "Edge")),
                    ("Remote IRR", iff(lvt_lint1 & 0x4000, "1", "0")),
                    ("Input polarity", iff(lvt_lint1 & 0x2000, "1", "0")),
                    ("Delivery status", iff(lvt_lint1 & 0x1000, "Send pending", "Idle")),
                    ("Delivery mode", delivery_mode[(lvt_lint1 >> 8) & 0x7]),
                    ("Vector", lvt_lint1 & 0xff) ]),
                 ("LVT Error",
                  [ ("Mask", iff(lvt_error & 0x10000, "Masked", "Not masked")),
                    ("Delivery status", iff(lvt_error & 0x1000, "Send pending", "Idle")),
                    ("Vector", lvt_error & 0xff) ]),
		 ("LVT Performance Counter",
                  [ ("Mask", iff(lvt_perf_counter & 0x10000, "Masked", "Not masked")),
                    ("Delivery status", iff(lvt_perf_counter & 0x1000, "Send pending", "Idle")),
                    ("Vector", lvt_perf_counter & 0xff) ])]

new_status_command('apic', get_status)

def get_apic_bus_info(obj):
	return [ (None,
		  [ ("Connected APIC(s)", obj.apics),
		    ("I/O-APIC", obj.ioapic) ]) ]

new_info_command('apic-bus', get_apic_bus_info)

def get_apic_bus_status(obj):
	return []

new_status_command('apic-bus', get_apic_bus_status)
