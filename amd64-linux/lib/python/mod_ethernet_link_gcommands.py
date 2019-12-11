from cli import *
import os, re, sys

if sys.platform[:5] == "win32":
    raw_uses_pcap = 1
else:
    import posix
    raw_uses_pcap = 0

def net_adapter_expander(string):
    if sys.platform[:5] == "linux":
        res = []
        f = open('/proc/net/dev', 'r')
        while 1:
            line = f.readline()
            if not line:
                break
            match = re.match('^ *([A-Za-z0-9_]+):', line)
            if not match:
                continue
            res = res + [ match.group(1) ]
        f.close()
        return get_completions(string, res)

    if sys.platform[:5] == "sunos":
        f = os.popen('/sbin/ifconfig -a', 'r')
        res = []
        while 1:
            line = f.readline()
            if not line:
                break;
            match = re.match('^ *([A-Za-z0-9_]+):', line)
            if not match:
                continue
            res = res + [ match.group(1) ]
        f.close()
        return get_completions(string, res)

    return []

def host_access_expander(string):
    return get_completions(string, ["tap", "raw"])

def connection_error(link, msg):
    SIM_command_has_problem()
    print "\nFailed connecting link '%s' to the real network." % link.name
    if msg:
        print msg
    return


def already_connected(link):
    # first check if ethernet-link already gets real packets
    # (only allow one for now)
    rns = [x for x in SIM_all_objects() if instance_of(x, "real_network")
           and x.link == link]
    if len(rns):
        print ("Ethernet-link '%s' is already connected to the real"
               "network using '%s'." % (link.name, rns[0].name))
        return 1
    return 0


def tun_tap_error(msg, tun_tap_possible, probe_only):
    if probe_only == 1:
        return 0
    print msg
    if tun_tap_possible:
        print ("Either install and configure TUN/TAP properly, or try a " +
               "command that uses PCAP or accesses the real network " +
               "interface directly.")
    else:
        print ("Try a command that uses PCAP or accesses the real network " +
               "interface directly.")
    print
    SIM_command_has_problem()
    return 0

# check if TUN/TAP exists
def tun_tap_available(tap_only = 0, probe_only = 0):
    if sys.platform[:5] == "sunos":
        if tap_only:
            msg = "Solaris does not support TAP, only TUN."
            return tun_tap_error(msg, 0, probe_only)
        # TODO:
        msg = "No TUN support for Solaris yet."
        return tun_tap_error(msg, 0, probe_only)
    elif sys.platform[:5] == "linux":
        device_name = "/dev/net/tun"
    else:
        # TODO: actually check if the TAP driver is installed
        return 1
        # msg = "Simics does not support TUN/TAP on %s." % sys.platform
        # return tun_tap_error(msg, 0, probe_only)

    try:
        posix.stat(device_name)
        have_tun = 1
        try:
            fd = open(device_name, "rw")
            fd.close()
            tun_ok = 1
        except:
            tun_ok = 0
    except:
        have_tun = 0

    if have_tun == 0:
        msg = "TUN/TAP not supported on this host. (No %s found)." % device_name
        return tun_tap_error(msg, 1, probe_only)
    elif tun_ok == 0:
        msg = ("TUN/TAP device not accessible. (Check permissions of the " +
               "%s device file.)" % device_name)
        return tun_tap_error(msg, 1, probe_only)
    return 1


def create_real_net_object(link, class_name, attrs):
    try:
        rn_num = 0
        while True:
            rn_name = "real-net%d" % rn_num
            SIM_get_object(rn_name)
            rn_num += 1
    except:
        pass

    try:
        real_net = SIM_create_object(class_name, rn_name, attrs)
    except Exception, msg:
        connection_error(link, msg)
        raise Exception
    try:
        return SIM_get_object(rn_name)
    except:
        connection_error(link, None)
        raise Exception

#
# ------------ connect-real-network-host --------------
#

# add a route from service-nodes on this network to the real-network router
# unless it already has a default route somewhere else
def add_rn_default_route(rn):
    try:
        ip = rn.ip
    except:
        try:
            ip = rn.host_ip
        except:
            return
    snds = [x for x in SIM_all_objects() if instance_of(x, "service-node-device")
            and x.link == rn.link]
    handled_sns = []
    for snd in snds:
        if snd.service_node in handled_sns:
            continue
        # enable DNS for the real network
        if snd.service_node.allow_real_dns == 0:
            print "Enabling DNS lookup on real network."
            snd.service_node.allow_real_dns = 1
        handled_sns.append(snd.service_node)
        routes = snd.service_node.routing_table
        for rt in routes:
            if rt[0] == "default":
                continue
        routes += [["default", "0.0.0.0", ip, snd]]
        snd.service_node.routing_table = routes
        print "Adding default route to %s in service-node '%s'" % (
            ip, snd.service_node.name)

def del_rn_default_route(rn):
    try:
        ip = rn.ip
    except:
        try:
            ip = rn.host_ip
        except:
            return
    snds = [x for x in SIM_all_objects() if instance_of(x, "service-node-device")
            and x.link == rn.link]
    handled_sns = []
    for snd in snds:
        if snd.service_node in handled_sns:
            continue
        handled_sns.append(snd.service_node)
        routes = snd.service_node.routing_table
        # default route is always last
        if routes[-1][0] != "default":
            continue
        if routes[-1][2] == ip:
            routes = routes[:-1]
            snd.service_node.routing_table = routes
            print "Removing default route to %s from service-node '%s'" % (
                ip, snd.service_node.name)

def report_tun_tap_config(rn):
    print ("\nNOTICE:\n" +
           "Failed getting IP address and netmask of the TUN/TAP " +
           "interface '%s'. Run the shell command 'ifconfig' " +
           "to assign an IP address and a netmask for this " +
           "network interface. (The ifconfig command typically "
           "has to be invoked with system administrator " +
           "privileges.) Use an IP address on the simulated " +
           "network, and a netmask matching the simulated " +
           "network configuration.") % rn.interface
    print
    print "Example: ifconfig %s <ip-address> netmask <netmask>" % rn.interface
    print
    print "Replace <ip-address> and <netmask> with real values."
    print
    if not rn.persistent:
        print ("Use a persistent real-network connection " +
               "(-persistent) to avoid this setup overhead " +
               "each time Simics is started.")
        print

def get_first_queue():
    queue = SIM_next_queue(None)
    if queue == None:
        print "This command requires an existing time queue (processor)."
        SIM_command_has_problem()
        raise Exception
    return queue

def real_network_host_cmd(link, iface, persistent):

    if already_connected(link):
        return

    try:
        queue = get_first_queue()
    except:
        return

    if not tun_tap_available():
        return

    try:
        class_name = SIM_get_class("rn-eth-bridge-tap")
    except Exception, msg:
        print msg
        try:
            class_name = SIM_get_class("rn-ip-tunnel-tun")
        except:
            # Should not happen.
            print "Could not find a real-network class."
            SIM_command_has_problem()
            return

    attrs = [["queue", queue],
             ["link", link]]

    if iface != "":
        attrs += [["interface", iface]]

    if persistent:
        attrs += [["persistent", 1]]

    try:
        real_net = create_real_net_object(link, class_name, attrs)
    except:
        return

    try:
        real_net.connected = 1
        if real_net.connected == 1:
            print "Ethernet-link '%s' connected to real network." % link.name
            add_rn_default_route(real_net)
        else:
            # TUN/TAP not fully configured
            report_tun_tap_config(real_net)
            print "Ethernet-link '%s' *almost* connected to real network." % link.name
    except Exception, msg:
        SIM_delete_object(real_net)
        return connection_error(link, msg)


def real_network_bridge_cmd(link, iface, access, no_xlate, persistent,
                            prop_link_status):

    if already_connected(link):
        return

    try:
        queue = get_first_queue()
    except:
        return

    if not access in ["raw", "tap", ""]:
        print "Unsupported real-network host access: '%s'" % access
        SIM_command_has_problem()
        return

    if access == "tap":
        have_tap = tun_tap_available(tap_only = 1)
        if have_tap == 0:
            return
    elif access == "":
        have_tap = tun_tap_available(tap_only = 1, probe_only = 1)
        if sys.platform[:5] == "linux" and not have_tap:
            print "Using 'raw' host access since preferred 'TAP' is not available."
        access = iff(have_tap, "tap", "raw")

    if persistent and access != "tap":
        print "The -persistent flag is only used for TAP connections."

    class_name = "rn-eth-%s-%s" % (iff(no_xlate, "bridge", "proxy"), access)

    attrs = [["queue", queue],
             ["link", link]]

    if iface != "":
        attrs += [["interface", iface]]

    if access == "tap":
        attrs += [["tap_bridge", 1]]
        if persistent:
            attrs += [["persistent", 1]]

    if access == "raw":
        attrs += [["use_pcap", raw_uses_pcap]]

    if prop_link_status:
        if sys.platform[:5] != "linux":
            print "Link status propagation not supported on %s" % sys.platform
        else:
            devs = []
            for link_dev in link.devices:
                devs += [link_dev[3]]
            attrs += [["link-status-devices", devs]]

    try:
        real_net = create_real_net_object(link, class_name, attrs)
    except:
        return

    try:
        real_net.connected = 1
        if real_net.connected == 1:
            if prop_link_status and sys.platform[:5] == "linux":
                real_net.link_status_enabled = True
            print "Ethernet-link '%s' connected to real network." % link.name
        elif access == "tap":
            # TAP not fully configured (not an error)
            print ("The TAP device does not appear to be configured " +
                   "properly as a bridge on the host since no IP address " +
                   "and netmask could be read from it. Check the TAP " +
                   "configuration before continuing.")
            print "Ethernet-link '%s' *almost* connected to real network." % link.name
        else:
            # should not happen
            raise Exception, "Unknown connection error"
    except Exception, msg:
        SIM_delete_object(real_net)
        return connection_error(link, msg)


def real_network_router_cmd(link, ip, netmask, gateway, iface):

    if already_connected(link):
        return

    try:
        queue = get_first_queue()
    except:
        return

    try:
        class_name = SIM_get_class("rn-ip-router-raw")
    except:
        print "IP router connection not supported."
        SIM_command_has_problem()
        return

    attrs = [["queue", queue],
             ["link", link],
             ["ip", ip],
             ["netmask", netmask],
             ["use_pcap", raw_uses_pcap]]

    if gateway != "":
        attrs += [["gateway", gateway]]

    if iface != "":
        attrs += [["interface", iface]]

    try:
        real_net = create_real_net_object(link, class_name, attrs)
    except:
        return

    try:
        real_net.connected = 1
        print "Ethernet-link '%s' connected to real network." % link.name
        add_rn_default_route(real_net)
    except Exception, msg:
        SIM_delete_object(real_net)
        return connection_error(link, msg)


####### global connect-real-network commands


def network_helper_cmd(pcap, helper):
    global raw_uses_pcap
    if pcap:
        raw_uses_pcap = 1
    elif helper:
        raw_uses_pcap = 0
        SIM_set_class_attribute("rn-ip-router-raw", "iface_helper", helper)
    else:
        if raw_uses_pcap:
            helper = "PCAP"
        else:
            helper = SIM_get_class_attribute("rn-ip-router-raw", "iface_helper")
        print "Interface helper is", helper

new_command("network-helper", network_helper_cmd,
            [arg(flag_t, "-pcap"),
             arg(filename_t(exist=1), "helper", "?", None)],
            type = ["Real Network", "Networking"],
            short = "set/show name of host network helper",
            doc = """
Sets the file name of the helper executable that opens the host network
interface for real-network connections using raw access. This helper,
<cmd>openif</cmd> in the distribution, needs privileges to run and should be
installed in such a way that it is run as root, typically by installing it as
setuid root. Simics can use PCAP to read packets from the network device
instead of accessing it directly. Set the <arg>-pcap</arg> flag, and no
<arg>handler</arg> to use PCAP instead. Without arguments, displays the
current setting.

This command has no effect under Windows.""", filename="/mp/simics-3.0/src/devices/ethernet-link/gcommands.py", linenumber="420")

def find_first_link():
    links = [x for x in SIM_all_objects() if instance_of(x, "ethernet-link")]
    if len(links) == 0:
        link = new_ethernet_link()[0]
        # connect devices to our new net
        devs = [x for x in SIM_all_objects()
                if instance_of(x, "ethernet_device")]
        for dev in devs:
            if SIM_is_interactive():
                print "Connecting %s to %s" % (dev.name, link.name)
            dev.link = link
        return link
    elif len(links) > 1:
        print ("More than one Ethernet link found. Use the namespace " +
               "version of this command to connect a selected link to " +
               "the real network.")
        print "Available Ethernet links: "
        for l in links:
            print l.name,
        print
        SIM_command_has_problem()
        raise Exception
    else:
        return links[0]

def global_real_network_host_cmd(iface, persistent):
    try:
        get_first_queue() # make sure we have a queue
        link = find_first_link()
    except:
        return
    real_network_host_cmd(link, iface, persistent)

def global_real_network_bridge_cmd(iface, access, no_xlate, persistent,
                                   prop_link_status):
    try:
        get_first_queue() # make sure we have a queue
        link = find_first_link()
    except:
        return
    real_network_bridge_cmd(link, iface, access, no_xlate, persistent,
                            prop_link_status)

def global_real_network_router_cmd(ip, netmask, gateway, iface):
    try:
        get_first_queue() # make sure we have a queue
        link = find_first_link()
    except:
        return
    real_network_router_cmd(link, ip, netmask, gateway, iface)

def global_disconnect_cmd():
    # see also disconnect in real-net and ethernet-link
    rns = [x for x in SIM_all_objects() if instance_of(x, "real_network")]
    for rn in rns:
        del_rn_default_route(rn)
        print "Disconnecting link %s from the real network." % rn.link.name
        SIM_delete_object(rn)

# TODO: add TUN support for Solaris, and win32-tap
new_command("connect-real-network-host", global_real_network_host_cmd,
            [arg(str_t, "interface", "?", "", expander = net_adapter_expander),
             arg(flag_t, "-persistent")],
            type = ["Real Network", "Networking"],
            short = "connect real host to the simulated network",
            see_also = ['connect-real-network',
                        '<ethernet-link>.connect-real-network-host',
                        'connect-real-network-bridge',
                        'connect-real-network-router'],
            doc = """
Connects a TAP interface of the simulation host to a simulated Ethernet link.

The optional <arg>interface</arg> argument specifies the TAP interface of the
host to use.

The <arg>-persistent</arg> is for backward compatibility and should not be
used.

See the <em>Connecting to a Real Network</em> chapter of the <em>Simics User
Guide</em> for more information about how to connect to a real network.

This command is currently not supported on Solaris hosts.
""", filename="/mp/simics-3.0/src/devices/ethernet-link/gcommands.py", linenumber="497")

new_command("connect-real-network-bridge", global_real_network_bridge_cmd,
            [arg(str_t, "interface", "?", "",
                 expander = net_adapter_expander),
             arg(str_t, "host-access", "?", "",
                 expander = host_access_expander),
             arg(flag_t, "-no-mac-xlate"),
             arg(flag_t, "-persistent"),
             arg(flag_t, "-propagate-link-status")],
            type = ["Real Network", "Networking"],
            short = "connect bridge between real and simulated network",
            see_also = ['connect-real-network',
                        '<ethernet-link>.connect-real-network-bridge',
                        'connect-real-network-host',
                        'connect-real-network-router'],
            doc = """
Creates an Ethernet bridge between a simulated Ethernet link and a real
network through an Ethernet interface of the simulation host.

The optional <arg>interface</arg> argument specifies the Ethernet or TAP
interface of the host to use.

By default a TAP interface is used, but if the <arg>host-access</arg> argument
is <tt>raw</tt>, raw access to an Ethernet interface is used.

MAC address translation can be disabled with the <arg>-no-mac-xlate</arg> flag.

The <arg>-persistent</arg> is for backward compatibility and should not be
used.

If <arg>-propagate-link-status</arg> is specified, link status changes on
the host interface will be propagated to all devices on the link that
implements the link-status interface. For TUN/TAP, only 'up' and 'down'
status will be propagated (and not 'unconnected'). Link status propagation
is only supported on Linux.

See the <em>Connecting to a Real Network</em> chapter of the <em>Simics User
Guide</em> for more information about how to connect to a real network.
""", filename="/mp/simics-3.0/src/devices/ethernet-link/gcommands.py", linenumber="521")


new_command("connect-real-network-router", global_real_network_router_cmd,
            [arg(str_t, "ip"),
             arg(str_t, "netmask", "?", "255.255.255.0"),
             arg(str_t, "gateway", "?", ""),
             arg(str_t, "interface", "?", "", expander = net_adapter_expander)],
            type = ["Real Network", "Networking"],
            short = "connect router between real and simulated network",
            see_also = ['connect-real-network',
                        '<ethernet-link>.connect-real-network-router',
                        'connect-real-network-host',
                        'connect-real-network-bridge'],
            doc = """
Creates a routed connection between a simulated Ethernet link and a real
network through an Ethernet interface of the simulation host.

The optional <arg>interface</arg> argument specifies the Ethernet interface of
the host to use.

The <arg>ip</arg> and <arg>netmask</arg> arguments specify the IP address and
netmask that the router should use on the simulated Ethernet link.

The <arg>gateway</arg> argument specifies the gateway on the simulated Ethernet
link that router should use for packets from the real network that are not
in the router's subnet.

See the <em>Connecting to a Real Network</em> chapter of the <em>Simics User
Guide</em> for more information about how to connect to a real network.
""", filename="/mp/simics-3.0/src/devices/ethernet-link/gcommands.py", linenumber="561")


new_command("disconnect-real-network", global_disconnect_cmd,
            type = ["Real Network", "Networking"],
            short = "disconnect from the real network",
            see_also = ['<ethernet-link>.disconnect-real-network',
                        'connect-real-network-host',
                        'connect-real-network-bridge',
                        'connect-real-network-router'],
            doc = """
Closes all connections to real networks except port forwarding and NAPT.
""", filename="/mp/simics-3.0/src/devices/ethernet-link/gcommands.py", linenumber="591")

#
# -------- new-ethernet-link --------
#

def new_ethernet_link(name = None, latency = None):
    if SIM_next_queue(None) == None:
        print "This command requires an existing time queue (processor)."
        SIM_command_has_problem()
        return
    if not name:
        name = get_available_object_name("ethlink")

    attrs = []

    if latency != None:
        # Specify the frequency just to make sure we scale latency correctly.
        attrs.extend([["frequency", 1000000000000],
                      ["latency", latency * 1000]])

    link = SIM_create_object("ethernet-link", name, attrs)
    if SIM_is_interactive():
        print "Created ethernet-link", name
    return (link,)

new_command("new-ethernet-link", new_ethernet_link,
            [arg(str_t, "name", "?", None),
             arg(int_t, "latency", "?", None)],
            type = ["Ethernet", "Networking"],
            short = "create a new ethernet link",
            see_also = ['new-std-ethernet-link', 'new-std-service-node'],
            doc = """
Creates a new <class>ethernet-link</class> object that can be used to connect Ethernet devices.

As of Simics 3.0 this command is deprecated. The
<cmd>new-std-ethernet-link</cmd> command should be used in component based
configurations.

The <arg>latency</arg> argument specifies the latency in nanoseconds
for communication over the link.
""", filename="/mp/simics-3.0/src/devices/ethernet-link/gcommands.py", linenumber="626")
