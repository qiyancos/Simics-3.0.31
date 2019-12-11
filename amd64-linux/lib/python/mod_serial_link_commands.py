from cli import *
import os, re
import sim_commands

prefixes_up =   [ '',  'k', 'M', 'G', 'T' ]
prefixes_down = [ '', 'm', 'u', 'n', 'p' ]
def fmt_prefixed_unit(val, unit):
    "Format val as a string using prefixes to keep the number of digits down"
    if val == 0.0:
        return "%.3g %s" % (val, unit)
    elif abs(val) >= 1.0:
        pre = prefixes_up
        while val >= 1000.0 and len(pre) > 1:
            val = val / 1000.0
            pre = pre[1:]
        return "%.3g %s%s" % (val, pre[0], unit)
    else: # abs(val) < 1.0:
        pre = prefixes_down
        while val < 1.0 and len(pre) > 1:
            val = val * 1000.0
            pre = pre[1:]
        return "%.3g %s%s" % (val, pre[0], unit)


def get_info(obj):
    devices = obj.devices
    doc = ([(None,
             [("Timing granularity", fmt_prefixed_unit(obj.frequency, "Hz")),
              ("Latency", fmt_prefixed_unit(obj.latency * 1.0 / obj.frequency, "s")),
              ("Maximum throughput", iff(obj.throttle,
                                         "%s bps" % obj.throttle,
                                         "unlimited"))]),
            ("Devices",
             [("Local devices",  ["<%d:%d> %s" % (lid, iff(gid is None, -1, gid), name)
                                  for gid, lid, name, dev, _ in devices if dev]),
              ("Remote devices", ["<%d:%d> %s" % (lid, iff(gid is None, -1, gid), name)
                                  for gid, lid, name, dev, _ in devices if not dev])])])
    return doc

def get_status(obj):
    return []

sim_commands.new_info_command("serial-link", get_info)
sim_commands.new_status_command("serial-link", get_status)

