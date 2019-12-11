from cli import *
import sim_commands

from mod_ethernet_link_gcommands import net_adapter_expander
from mod_ethernet_link_gcommands import add_rn_default_route
from mod_ethernet_link_gcommands import del_rn_default_route

rn_classes = ["rn-eth-bridge-tap", "rn-eth-proxy-tap",  "rn-ip-tunnel-tun",
              "rn-eth-bridge-raw", "rn-eth-proxy-raw",  "rn-ip-router-raw"]
    
#
# -------------- info --------------
#

def get_info(rn):
    if rn.classname.find("bridge") > 0:
        type = "Ethernet bridge"
    elif rn.classname.find("proxy") > 0:
        type = "Ethernet proxy"
    elif rn.classname.find("ip") > 0:
        type = "IP router/tunnel"
    else:
        type = "Unknown"

    if rn.classname.find("raw") > 0:
        if rn.use_pcap:
            access = "Raw (PCAP)"
        else:
            access = "Raw"
    elif rn.classname.find("tun") > 0 or rn.classname.find("tap") > 0:
        access = "TUN/TAP"
    else:
        access = "Unknown"    

    host_info = []
    try:
        host_info += [("IP", rn.host_ip)]
    except:
        pass
    try:
        host_info += [("Netmask", rn.host_netmask)]
    except:
        pass
    try:
        host_info += [("MAC", rn.host_mac)]
    except:
        pass
    host_info += [("Interface", rn.interface)]

    link_info = []
    try:
        link_info += [("MAC", rn.mac)]
    except:
        pass
    try:
        link_info += [("IP", rn.ip)]
    except:
        pass
    try:
        link_info += [("netmask", rn.netmask)]
    except:
        pass
    try:
        link_info += [("gateway", rn.gateway)]
    except:
        link_info += [("gateway", "<not set>")]

    doc = [(None,
            [("Type", type),
             ("Host access", access),
             ("Connected", iff(rn.connected, "Yes", "No"))]),
           ("Host Network", host_info)]
    if len(link_info) > 0:
        doc += [("Simulated Network", link_info)]
    return doc

for cls in rn_classes:
    sim_commands.new_info_command(cls, get_info)

#
# -------------- status --------------
#

def get_status(rn):
    return [(None,
             [("Connected", iff(rn.connected, "Yes", "No"))])]

for cls in rn_classes:
    sim_commands.new_status_command(cls, get_status)

#
# -------------- disconnect --------------
#

def disconnect_rn_cmd(rn):
    # see also disconnect in ethernet-link (namespace and global)
    del_rn_default_route(rn)
    print "Disconnecting link %s from the real network." % rn.link.name
    SIM_delete_object(rn)

new_command("disconnect-real-network", disconnect_rn_cmd,
            type = "real-network commands",
            namespace = "real_network",
            short = "disconnect from the real network",
            doc = """
Disconnect the real network connection from a simulated
Ethernet link.
""", filename="/mp/simics-3.0/src/extensions/real-network/commands.py", linenumber="101")


#
# -------------- finish-connection --------------
#

def finish_rn_cmd(rn):
    if rn.connected:
        print "Already correctly connected to the real network."
        return
    rn.connected = 1
    if rn.connected == 0:
        print "Failed finishing the connection to the real network."
        SIM_command_has_problem()
        return
    print "Ethernet-link '%s' connected to real network." % rn.link.name
    add_rn_default_route(rn)

for cls in ["rn-eth-bridge-tap", "rn-eth-proxy-tap",  "rn-ip-tunnel-tun"]:
    new_command("finish-connection", finish_rn_cmd,
                type = "real-network commands",
                namespace = cls,
                short = "Finalize a real network connection",
                doc = """
Finish the connection to the real network once the TUN/TAP
interface has been assigned an IP address and network mask
ethat the real-network object has to read. This command
usually isn't needed since Simics will retry getting the
interface configuration when it receives a packet from or
to the real network.
""", filename="/mp/simics-3.0/src/extensions/real-network/commands.py", linenumber="128")


#
# -------------- close-tun-tap-interface --------------
#

def close_iface_cmd(iface):
    try:
        SIM_set_class_attribute("rn-ip-tunnel-tun", "close_iface", iface)
        print "Closed the '%s' interface successfully." % iface
    except Exception, msg:
        print "Failed closing the interface '%s': %s" % (iface, msg)

new_command("close-tun-tap-interface", close_iface_cmd,
            [arg(str_t, "interface", "?", "", expander = net_adapter_expander)],
            type = ["Real Network"],
            short = "close an unused persistent TUN/TAP interface",
            doc = """
Closes an TUN/TAP interface that has been set persistent.
If the interface is currenly is used, it will not be closed
at once, only the persistent state will change. Not applicable for
for TAP-Win32 interfaces.
""", filename="/mp/simics-3.0/src/extensions/real-network/commands.py", linenumber="153")
