from cli import *
import sim_commands
import nic_common

def get_info(obj):
    return ([("IP configuration",
              [("IP address", obj.ip),
               ("Netmask", obj.netmask),
               ("Target", obj.dst_ip),
               ("Gateway", obj.gateway)]),
             ("Traffic parameters",
              [("Rate", "%d pps" % obj.pps),
               ("Size", "%d bytes" % obj.packet_size)])] +
            nic_common.get_nic_info(obj))

def get_status(obj):
    left = obj.count
    if left is None:
        left = "unlimited"
    return ([ (None,
               [ ("Enabled", iff(obj.enabled, "yes", "no")),
                 ("Packets left to send", left),
                 ("Packets sent", obj.total_tx_packets),
                 ("Packets received", obj.total_rx_packets)])] +
            nic_common.get_nic_status(obj))

sim_commands.new_info_command("etg", get_info)
sim_commands.new_status_command("etg", get_status)

def start(obj, count):
    if count:
        obj.count = count
    if not obj.enabled:
        print "Starting", obj.name
        obj.enabled = 1

new_command("start", start,
            [arg(int_t, "count", "?")],
            type = "etg commands",
            short = "Start generating traffic",
            namespace = "etg",
            doc = """
Start the traffic generator.
""", filename="/mp/simics-3.0/src/devices/etg/commands.py", linenumber="37")

def stop(obj):
    if obj.enabled:
        print "Stopping", obj.name
        obj.enabled = 0

new_command("stop", stop,
            [],
            type = "etg commands",
            short = "Stop generating traffic",
            namespace = "etg",
            doc = """
Stop the traffic generator.
""", filename="/mp/simics-3.0/src/devices/etg/commands.py", linenumber="51")            

def packet_rate(obj, pps):
    if pps is None:
        print "Packet rate is %d packets/second" % obj.pps
    else:
        obj.pps = pps

new_command("packet-rate", packet_rate,
            [arg(int_t, "rate", "?")],
            type = "etg commands",
            short = "Set or display the packets per second rate",
            namespace = "etg",
            doc = """
Set the rate, in packets per second, at which packets are sent by the traffic generator.

If no rate is given, the current rate is displayed.
""", filename="/mp/simics-3.0/src/devices/etg/commands.py", linenumber="66")

def packet_size(obj, size):
    if size is None:
        print "Packet size is %d bytes" % obj.packet_size
    else:
        obj.packet_size = size

new_command("packet-size", packet_size,
            [arg(int_t, "size", "?")],
            type = "etg commands",
            short = "Set or display the packet size",
            namespace = "etg",
            doc = """
Set the size of the packets that are sent by the traffic generator.

If no size is given, the current size is displayed.
""", filename="/mp/simics-3.0/src/devices/etg/commands.py", linenumber="83")
