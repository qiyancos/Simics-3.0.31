from cli import *
from sim_commands import *

#
# ------------------------ info -----------------------
#

def yn(val):
	return iff(val, "yes", "no")
	
def timer_info(obj, c):
	return [ ("Frequency, Hz", obj.clock_freq_hz[c])]

def timer_status(obj, c):
	return [ ("Counter", obj.count[c]),
		 ("Count Register", obj.initial_count[c]),
		 ("Counting", yn(obj.counting[c])),
		 ("Latched Counter", obj.latched_count[c]),
		 ("Latched Status", obj.latched_status[c]),
		 ("Status Latched", yn(obj.latched_s[c])),
		 ("Counter Latched", yn(obj.latched[c])),
		 ("Command", obj.cmd_names[obj.cmd[c]]),
		 ("Mode", obj.mode_names[obj.mode[c]]),
		 ("Out", obj.out[c]),
		 ("Gate", obj.gate[c]),
		 ("BCD format", yn(obj.bcd[c]))]

def get_info(obj):
        return [ (None,
                  [ ("IRQ device", obj.irq_dev),
                    ("IRQ number", obj.irq_level) ]),
                 ("Timer 0 - system timing", timer_info(obj, 0)),
		 ("Timer 1 - DRAM refresh", timer_info(obj, 1)),
		 ("Timer 2 - Speaker", timer_info(obj, 2)) ]

def get_status(obj):
        return [ ("General",
                  [ ("IRQ requested", obj.interrupt_pin),
		    ("Refresh clock", obj.refresh_clock),
                    ("Speaker enabled", obj.speaker) ]),
                 ("Timer 0 - system timing", timer_status(obj, 0)),
		 ("Timer 1 - DRAM refresh", timer_status(obj, 1)),
		 ("Timer 2 - Speaker", timer_status(obj, 2)) ]

new_info_command('i8254', get_info)
new_status_command('i8254', get_status)
