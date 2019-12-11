from cli import *

# Common functionality for network devices

def get_nic_info(obj):
    info = [("Recorder",  obj.recorder),
            ("MAC address", obj.mac_address),
            ("Link", obj.link)]
    try:
        bw = obj.tx_bandwidth
        if bw == 0:
            bw = "unlimited"
        elif bw % 1000:
            bw = "%d bit/s" % bw
        else:
            bw = bw // 1000
            if bw % 1000:
                bw = "%d kbit/s" % bw
            else:
                bw = "%d Mbit/s" % (bw // 1000)
        info.append(("Transmit limit", bw))
    except:
        pass
    return [(None, info)]

def get_nic_status(obj):
    return []

# -------------------- connect --------------------

def connect_cmd(obj, auto, network_poly):
    if auto:
        print "The flag '-auto' is deprecated, and shouldn't be used."
        # for now quiet if network doesn't exist when using auto
        if network_poly[0] == str_t:
            return
    if network_poly[0] == str_t:
        print "Argument is not an Ethernet link object."
        SIM_command_has_problem()
        return
    try:
        obj.link = network_poly[1]
    except Exception, msg:
        print "[%s] Connection failed" % obj.name
        print msg

# ------------------- disconnect ------------------

def disconnect_cmd(obj):
    try:
        obj.link = None
    except Exception, msg:
        print "[%s] Disconnection failed (%s)" % (obj.name, msg)


# ------------- command registration --------------

def new_nic_commands(device_name):
    new_command("connect", connect_cmd,
                [arg(flag_t, "-auto"),
                 arg((obj_t("link", "ethernet-link"), str_t), ("link", "link-name"))],
                alias = "",
                type = ["Ethernet", "Networking"],
                short = "connect to a simulated Ethernet link",
                see_also = ['<' + device_name + '>.disconnect'],
                namespace = device_name,
                doc = """
                Connect the device to a simulated Ethernet link.
                The flag '-auto' is deprecated and shouldn't be used.
                """, filename="/mp/simics-3.0/src/extensions/apps-python/nic_common.py", linenumber="59")

    new_command("disconnect", disconnect_cmd,
                [],
                alias = "",
                type = ["Ethernet", "Networking"],
                short = "disconnect from simulated link",
                see_also = ['<' + device_name + '>.connect'],
                namespace = device_name,
                doc = """
                Disconnect the device from a simulated Ethernet link.
                """, filename="/mp/simics-3.0/src/extensions/apps-python/nic_common.py", linenumber="72")
