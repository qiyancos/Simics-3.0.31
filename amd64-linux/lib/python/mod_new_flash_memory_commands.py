from sim_commands import *

def command_set(cmd_set):
    all = ["None", "Intel", "AMD", "Intel (extended)", "AMD (extended)"]
    if cmd_set < len(all):
        return all[cmd_set]
    else:
        return "Unknown (%s)" % cmd_set

def get_info(obj):
    timing_info = [[state, "%g s"%secs] for state, secs in
                   dict(obj.timing_model).items() if secs != 0.0 ]

    return [(None,
             [("Command set", command_set(obj.command_set)),
              ("Device", obj.device_id),
              ("Manufacturer", obj.manufacturer_id),
              ("Interleave", "%d" % obj.interleave),
              ("Bus width", "%d bits" % obj.bus_width)]),
            ("Timing model",
             timing_info)]

def get_status(obj):
    return [(None,
             [("Mode", obj.chip_mode)])]

new_info_command('generic-flash-memory', get_info)
new_status_command('generic-flash-memory', get_status)
