from cli import *
import string, sys
from socket import inet_aton, inet_ntoa

from mod_ftp_alg_gcommands import enable_ftp_alg_cmd

from components import \
     instantiate_cmd, get_component, connect_cmd, components_connected, \
     component_basename

def get_first_queue():
    queue = SIM_next_queue(None)
    if queue == None:
        print "This command requires an existing time queue (processor)."
        SIM_command_has_problem()
        raise Exception
    return queue

#
# Convert between string and integer representation of IP addresses
#

def ip_stoi(ip):
    ip = inet_aton(ip)
    return ((ord(ip[0]) << 24) | (ord(ip[1]) << 16) |
            (ord(ip[2]) << 8) | (ord(ip[3]) << 0))

def ip_itos(ip):
    ip = "" + (chr((ip >> 24) & 0xff) + chr((ip >> 16) & 0xff) +
               chr((ip >> 8) & 0xff) + chr((ip >> 0) & 0xff))
    return inet_ntoa(ip)

#
# Printing port forwarding info.
#

def get_napt_forwards():
    forwards = []
    sn_devs = [x  for x in SIM_all_objects()
               if instance_of(x, "service-node-device")]
    for sn_dev in sn_devs:
        if sn_dev.service_node and sn_dev.link and sn_dev.service_node.napt_enable:
            forwards.append((sn_dev.link.name, ip_stoi(sn_dev.ip_address)))
    return forwards

def print_napt_forwards(forwards):
    forwards.sort()
    for (link_name, gateway_ip) in forwards:
        print "NAPT enabled with gateway %s on link %s." % (ip_itos(gateway_ip), link_name)

def get_dns_forwards():
    forwards = []
    sn_devs = [x  for x in SIM_all_objects()
               if instance_of(x, "service-node-device")]
    for sn_dev in sn_devs:
        if sn_dev.service_node and sn_dev.link and sn_dev.service_node.allow_real_dns:
            forwards.append((sn_dev.link.name, ip_stoi(sn_dev.ip_address)))
    return forwards

def print_dns_forwards(forwards):
    forwards.sort()
    for (link_name, gateway_ip) in forwards:
        print "Real DNS enabled at %s on link %s." % (ip_itos(gateway_ip), link_name)

def get_incoming_forwards():
    forwards = []
    pfis = [x for x in SIM_all_objects()
            if instance_of(x, "port-forward-incoming-server")]
    for pfi in pfis:
        for (proto, host_port, tgt_ip, tgt_port) in pfi.connections:
            if proto == "tcp":
                protocol = "TCP"
                sn = pfi.tcp
            else:
                protocol = "UDP"
                sn = pfi.udp
            for (route_ip, route_mask, route_gateway_ip, route_dev) in sn.routing_table:
                if route_ip == "default":
                    route_ip = "0.0.0.0"
                if (((ip_stoi(route_ip) ^ ip_stoi(tgt_ip)) & ip_stoi(route_mask)) == 0 and route_dev.link):
                    forwards.append((protocol, host_port, route_dev.link.name, ip_stoi(tgt_ip), tgt_port, ip_stoi(route_gateway_ip)))
                    break
    return forwards

def print_incoming_forwards(forwards):
    forwards.sort()
    for (proto, host_port, link_name, tgt_ip, tgt_port, gateway_ip) in forwards:
        if gateway_ip:
            gateway = "via gateway " + ip_itos(gateway_ip) + " "
        else:
            gateway = ""
        print "Host %s port %d -> %s:%d %son link %s" % (proto, host_port, ip_itos(tgt_ip), tgt_port, gateway, link_name)

def get_outgoing_forwards():
    forwards = []
    pfos = [x for x in SIM_all_objects()
            if instance_of(x, "port-forward-outgoing-server")]
    for pfo in pfos:
        for conn in pfo.connections:
            if len(conn) == 2:
                continue
            (proto, sn_port, sn_ip, tgt_ip, tgt_port) = conn
            if proto == "tcp":
                protocol = "TCP"
                sn = pfo.tcp
            else:
                protocol = "UDP"
                sn = pfo.udp
            sn_devs = [x  for x in SIM_all_objects()
                       if instance_of(x, "service-node-device") and x.service_node == sn and x.link]
            for sn_dev in sn_devs:
                if (sn_dev.link and sn_dev.ip_address == sn_ip):
                    forwards.append((protocol, sn_dev.link.name, sn_ip, sn_port, ip_stoi(tgt_ip), tgt_port))
    return forwards

def print_outgoing_forwards(forwards):
    forwards.sort()
    for (proto, link_name, sn_ip, sn_port, tgt_ip, tgt_port) in forwards:
        print "%s %s port %d on link %s -> host %s:%d" % (sn_ip, proto, sn_port, link_name, ip_itos(tgt_ip), tgt_port)

#
# Creating new service nodes
#

def new_service_node(name, ethlink, ip, netmask):
    # Get a processor to use as queue for the objects
    try:
        queue = get_first_queue()
    except:
        return

    if (not ethlink) != (not ip):
        pr("Error: Either specify link and ip, or none of them\n")
        SIM_command_has_problem()
        return

    if not name:
        if ethlink:
            name = get_available_object_name(ethlink.name + "_sn")
        else:
            name = get_available_object_name("sn")

    sn = SIM_create_object("service-node", name, [["queue", queue]])
    if SIM_is_interactive():
        print "Created service-node", name

    # This is identical to running the command sn.connect
    if ethlink:
        import mod_service_node_commands
        mod_service_node_commands.connect_node_cmd(sn, ethlink, ip, netmask)
    return (name, )

new_command("new-service-node", new_service_node,
            [arg(str_t, "name", "?", None),
             arg(obj_t("link", "ethernet-link"), "link", "?", None),
             arg(str_t, "ip", "?", ""),
             arg(str_t, "netmask", "?", "")],
            type = ["Ethernet"],
            short = "create a new service node",
            see_also = ['new-std-service-node', '<service-node>.connect'],
            doc = """
Creates a new <class>service-node</class> object, and optionally
connects it to an Ethernet link.

As of Simics 3.0 this command is deprecated. The
<cmd>new-std-service-node</cmd> command should be used in component based
configurations.

If an <arg>link</arg> argument is provided, it should be the name of
an existing <class>ethernet-link</class> object.  When a link is
specified, the <arg>ip</arg> argument should give the IP address that
the service node will use on the link, and the <arg>netmask</arg>
argument the netmask.  Optionally, the netmask may be given in the
<arg>ip</arg> argument as a <tt>/bits</tt> suffix.  The netmask may
also left out entirely, in which case it will default to
<tt>255.255.255.0</tt>.

""", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="153")


#
# port-forwarding commands
#

service_list = { "ftp"    : [ 21, "tcp"],
                 "ssh"    : [ 22, "tcp"],
                 "telnet" : [ 23, "tcp"],
                 "tftp"   : [ 69, "udp"],
                 "http"   : [ 80, "tcp"] }

def service_name(port):
    srv = service_list.values()
    for i in range(len(srv)):
        if srv[i][0] == port:
            return service_list.keys()[i]
    return ""

default_pf_dest = None

def default_pf_target_cmd(ip):
    global default_pf_dest
    if ip:
        try:
            inet_aton(ip)
        except:
            print "Malformed IP address '%s'." % ip
            SIM_command_has_problem()
            return
        default_pf_dest = ip
        if SIM_is_interactive():
            print ("Setting '%s' as default port-forwarding target." %
                   default_pf_dest)
    else:
        if not default_pf_dest:
            print "No default port-forwarding target set."
        else:
            print "Default port-forwarding target: '%s'" % default_pf_dest

new_command("default-port-forward-target", default_pf_target_cmd,
            [arg(str_t, "target-ip", "?", None)],
            type = ["Real Network"],
            short = "set default port forwarding target",
            see_also = ['connect-real-network',
                        'connect-real-network-port-in'],
            doc = """
Sets the IP address of a simulated machine that will be used by
the <cmd>connect-real-network</cmd> command if none is given as
argument. This is useful in single machine configurations where
the same IP is used all the time.
""", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="219")

def create_outgoing_port_forward(sn):
    try:
        pfo = SIM_get_object("%s_port_forward_out" % sn.name)
    except:
        pfo = SIM_create_object("port-forward-outgoing-server",
                                "%s_port_forward_out" % sn.name,
                                [["tcp", sn],
                                 ["udp", sn]])
    return pfo

def setup_outgoing_port_forward(sn):
    pfo = create_outgoing_port_forward(sn)
    try:
        old_connections = pfo.connections
        new_connections = old_connections + [["tcp", 0], ["udp", 0]]
        pfo.connections = new_connections
    except Exception, msg:
        print "Failed to setup outgoing port-forward service: %s" % msg
    return pfo

def create_incoming_port_forward(sn):
    try:
        pfi = SIM_get_object("%s_port_forward_in" % sn.name)
    except:
        pfi = SIM_create_object("port-forward-incoming-server",
                                "%s_port_forward_in" % sn.name,
                                [["tcp", sn],
                                 ["udp", sn]])
    return pfi

def setup_incoming_port_forward(sn, pfo):
    create_incoming_port_forward(sn)

def setup_outgoing_connection(sn, sn_ip, protocol, sn_port, tgt_ip, tgt_port):
    forwards_before = get_outgoing_forwards()

    pfo = create_outgoing_port_forward(sn)
    # TODO: should check if the port is used for other things too
    old_connections = pfo.connections
    for conn in old_connections:
        if len(conn) == 2:
            continue
        (conn_proto, conn_sn_port, conn_sn_ip, conn_tgt_ip, conn_tgt_port) = conn
        if conn_sn_ip == sn_ip and conn_sn_port == sn_port and conn_proto == protocol:
            print "%s %s:%d of service-node %s already forwarded to host %s:%d." % (iff (conn_proto == "tcp", "TCP", "UDP"), conn_sn_ip, sn_port, sn.name, conn_tgt_ip, conn_tgt_port)
            SIM_command_has_problem()
            return
    new_connections = old_connections + [[protocol, sn_port, sn_ip, tgt_ip, tgt_port]]
    pfo.connections = new_connections

    forwards_after = get_outgoing_forwards()
    new_forwards = [x for x in forwards_after if not (x in forwards_before)]
    if new_forwards:
        print_outgoing_forwards(new_forwards)
    else:
        print "Port forwarding setup failed."
        SIM_command_has_problem()

def setup_incoming_connection(sn, protocol, ext_port, int_ip, int_port, strict_host_port):
    forwards_before = get_incoming_forwards()

    pfi = create_incoming_port_forward(sn)
    try:
        old_connections = pfi.connections
        for old_conn in old_connections:
            (c_protocol, c_ext_port, c_int_ip, c_int_port) = old_conn
            if c_protocol == protocol and c_int_ip == int_ip and c_int_port == int_port:
                print "Input %s port %d is already forwarded to %s:%d" % (protocol, c_ext_port, c_int_ip, c_int_port)
                SIM_command_has_problem()
                return
        new_connections = old_connections + [[protocol, ext_port, int_ip, int_port]]
        pfi.connections = new_connections
        if strict_host_port:
            # Check that assigned host port is the same as specified
            conn = pfi.connections
            created_ext_port = pfi.connections[-1:][0][1]
            if created_ext_port != ext_port:
                pfi.connections = old_connections                
                print "Failed to assign host port %d for %s" % (ext_port, protocol)
                SIM_command_has_problem()
                return                        
    except SimExc_General:
        print "Port forwarding setup failed."
        SIM_command_has_problem()
        return

    forwards_after = get_incoming_forwards()
    new_forwards = [x for x in forwards_after if not (x in forwards_before)]
    if new_forwards:        
        print_incoming_forwards(new_forwards)
    else:
        print "Port forwarding setup failed."
        SIM_command_has_problem()

def get_service_node(link, tgt_ip, sn_ip, create_sn):

    queue = get_first_queue() # may raise exception
    link_created = 0
    sn_cmp = None

    if not link:
        links = [x for x in SIM_all_objects()
                 if instance_of(x, "ethernet-link")]
        if len(links) > 1:
            SIM_command_has_problem()
            print ("There are more than one ethernet-link, please specify " +
                   "which one the simulated machine is connected to.")
            raise Exception
        elif len(links) == 0:
            # create component
            SIM_get_class('std-ethernet-link')
            basename = component_basename('std-ethernet-link')
            link_cmp = SIM_create_object(
                'std-ethernet-link',
                get_available_object_name(basename), [])
            instantiate_cmd(False, [link_cmp])
            link = get_component_object(link_cmp, "link")
            link_created = 1
            if SIM_is_interactive():
                print "No ethernet-link found, creating '%s'." % link.name
        else:
            link = links[0]
    link_cmp = link.component
    # find service nodes on link
    sns = [x.service_node for x in SIM_all_objects()
           if instance_of(x, "service-node-device") and x.link == link]
    if len(sns) == 0:
        if not create_sn:
            return None
        if not sn_ip:
            if not tgt_ip:
                return None
            sn_ip = inet_ntoa(inet_aton(tgt_ip)[0:3] + '\x01')
        # create component
        SIM_get_class('std-service-node')
        basename = component_basename('std-service-node')
        sn_cmp = SIM_create_object(
            'std-service-node',
            get_available_object_name(basename), [])
        instantiate_cmd(False, [sn_cmp])
        get_component(sn_cmp).add_connector(sn_ip, "255.255.255.0")
        sn = get_component_object(sn_cmp, "sn")
        if SIM_is_interactive():
            print ("No service-node found, creating '%s' with IP '%s'."
                   % (sn.name, sn_ip))
    else:
        sn = sns[0]
        if sn_ip and sn_ip != get_sn_ip(sn, link):
            print ("Using already existing service node with IP %s."
                   % get_sn_ip(sn, link))
    if len(sns) > 1:
        print "More than one service-node, using '%s'." % sn.name

    # connect devices to our newly created link
    if link_created:
        devs = [x for x in SIM_all_objects()
                if instance_of(x, "ethernet_device")]
        for dev in devs:
            if not dev.link:
                dev_cmp = dev.component
                if dev_cmp and link_cmp:
                    if components_connected(dev_cmp, link_cmp):
                        continue
                    # connect using components
                    connect_cmd(link_cmp, None, dev_cmp, None, True)
                    print ("Connecting component '%s' to '%s'"
                           % (dev_cmp.name, link_cmp.name))
                else:
                    dev.link = link
                    print ("Connecting device '%s' to '%s'"
                           % (dev.name, link.name))
    elif sn_cmp:
        # a service-node component was created, but no link
        if link_cmp:
            # connect using components
            connect_cmd(link_cmp, None, sn_cmp, None, True)
            print ("Connecting component '%s' to '%s'"
                   % (sn_cmp.name, link_cmp.name))
        else:
            snd = [x for x in SIM_all_objects()
                   if (instance_of(x, "service-node-device")
                       and x.service_node == sn
                       and x.ip_address == sn_ip
                       and x.netmask == "255.255.255.0")][0]
            snd.link = link
            print ("Connecting device '%s' to '%s'"
                   % (snd.name, link.name))
    return (link, sn)

def service_expander(string):
    return get_completions(string, service_list.keys())

def parse_port_service_poly(poly):
    proto = None
    if poly[0] == str_t:
        try:
            port = service_list[poly[1]][0]
            proto = service_list[poly[1]][1]
        except Exception, msg:
            print msg
            SIM_command_has_problem()
            print "Unknown service %s, use the port number instead." % poly[1]
            raise Exception
    else:
        port = poly[1]
    return (proto, port)

def connect_real_network_port_in(poly, ext_port, tgt_ip, sn, tcp, udp, strict_host_port):
    (proto, port) = parse_port_service_poly(poly)

    if tcp and udp:
        proto = None
    elif tcp:
        proto = "tcp"
    elif udp:
        proto = "udp"

    if proto:
        setup_incoming_connection(sn, proto, ext_port, tgt_ip, port, strict_host_port)
    else:
        setup_incoming_connection(sn, "udp", ext_port, tgt_ip, port, strict_host_port)
        setup_incoming_connection(sn, "tcp", ext_port, tgt_ip, port, strict_host_port)

def disconnect_real_network_port_in(poly, tgt_ip, sn, tcp, udp):
    (proto, port) = parse_port_service_poly(poly)

    if tcp and udp:
        proto = None
    elif tcp:
        proto = "tcp"
    elif udp:
        proto = "udp"

    try:
        pfi = SIM_get_object("%s_port_forward_in" % sn.name)
    except:
        print "Incoming port forwarding is not configured."
        SIM_command_has_problem()
        return

    old_conns = pfi.connections
    new_conns = filter(lambda x: not ((proto == None or proto == x[0]) and (tgt_ip == x[2]) and (port == x[3])), old_conns)
    if len(new_conns) == len(old_conns):
        print "Could not find port forwarding connection to remove."
        SIM_command_has_problem()
        return
    pfi.connections = new_conns

def connect_real_network_port_out(sn_port, sn_ip, tgt_port, tgt_ip, sn, tcp, udp):
    proto = None

    if tcp and udp:
        proto = None
    elif tcp:
        proto = "tcp"
    elif udp:
        proto = "udp"

    if proto:
        setup_outgoing_connection(sn, sn_ip, proto, sn_port, tgt_ip, tgt_port)
    else:
        setup_outgoing_connection(sn, sn_ip, "udp", sn_port, tgt_ip, tgt_port)
        setup_outgoing_connection(sn, sn_ip, "tcp", sn_port, tgt_ip, tgt_port)

def disconnect_real_network_port_out(sn_port, sn_ip, tgt_port, tgt_ip, sn, tcp, udp):
    proto = None

    if tcp and udp:
        proto = None
    elif tcp:
        proto = "tcp"
    elif udp:
        proto = "udp"

    try:
        pfo = SIM_get_object("%s_port_forward_out" % sn.name)
    except:
        print "Outgoing port forwarding is not configured."
        SIM_command_has_problem()
        return

    old_conns = pfo.connections
    new_conns = filter(lambda x: len(x) == 2 or not ((proto == None or proto == x[0]) and (sn_port == x[1]) and (sn_ip == x[2]) and (tgt_ip == x[3]) and (tgt_port == x[4])), old_conns)
    if len(new_conns) == len(old_conns):
        print "Could not find port forwarding connection to remove."
        SIM_command_has_problem()
        return
    pfo.connections = new_conns

def get_target_ip(tgt_ip):
    if not tgt_ip:
        if not default_pf_dest:
            print ("No target IP given for port forwarding, and no default " +
                   "destination configured.")
            SIM_command_has_problem()
            raise Exception
        tgt_ip = default_pf_dest
    try:
        inet_aton(tgt_ip)
    except:
        print "Malformed IP address '%s'" % tgt_ip
        SIM_command_has_problem()
        raise Exception
    return tgt_ip

def get_sn_ips(service_node):
    return [x.ip_address for x in SIM_all_objects()
            if instance_of(x, "service-node-device") and x.service_node == service_node]

def get_sn_ip_link(service_node, link):
    return [x.ip_address for x in SIM_all_objects()
            if instance_of(x, "service-node-device") and x.service_node == service_node and x.link == link]

def get_sn_ip(service_node, ethernet_link):
    for x in SIM_all_objects():
        if (instance_of(x, "service-node-device") and
            x.service_node == service_node and
            x.link == ethernet_link):
            return x.ip_address
    return None

def connect_real_network_port_in_cmd(tgt_port_poly, link, host_port, tgt_ip, tcp, udp, strict_host_port):
    try:
        # will print error message itself
        tgt_ip = get_target_ip(tgt_ip)
        sn_info = get_service_node(link, tgt_ip, None, 0)
        if sn_info == None:
            print "No service node found on link %s" % link.name
            SIM_command_has_problem()
            return
        (link, sn) = sn_info
        if tgt_ip in get_sn_ips(sn):
            print "Cannot port forward to the service node"
            SIM_command_has_problem()
            return
        if host_port == None:
            connect_real_network_port_in(tgt_port_poly, 4000, tgt_ip, sn, tcp, udp, strict_host_port)
        else:
            connect_real_network_port_in(tgt_port_poly, host_port, tgt_ip, sn, tcp, udp, strict_host_port)
    except Exception, msg:
        print msg
        return

def disconnect_real_network_port_in_cmd(tgt_port_poly, link, tgt_ip, tcp, udp):
    try:
        # will print error message itself
        tgt_ip = get_target_ip(tgt_ip)
        sn_info = get_service_node(link, tgt_ip, None, 0)
        if sn_info == None:
            print "No service node found on link %s" % link.name
            SIM_command_has_problem()
            return
        (link, sn) = sn_info
        disconnect_real_network_port_in(tgt_port_poly, tgt_ip, sn, tcp, udp)
    except Exception, msg:
        print msg
        return

def connect_real_network_port_out_cmd(sn_port, link, tgt_ip, tgt_port, tcp, udp):
#    try:
        # will print error message itself
        tgt_ip = get_target_ip(tgt_ip)
        sn_info = get_service_node(link, tgt_ip, None, 0)
        if sn_info == None:
            print "No service node found on link %s" % link.name
            SIM_command_has_problem()
            return
        (link, sn) = sn_info
        print "Got service node %s for %s" % (sn.name, link.name)
        if tgt_ip in get_sn_ips(sn):
            print "Cannot port forward to the service node"
            SIM_command_has_problem()
            return
        sn_ip_link = get_sn_ip_link(sn, link)
        if len(sn_ip_link) != 1:
            print "Cannot get service node IP"
            SIM_command_has_problem()
            return
        connect_real_network_port_out(sn_port, sn_ip_link[0], tgt_port, tgt_ip, sn, tcp, udp)
#    except Exception, msg:
#        print msg
#        return

def disconnect_real_network_port_out_cmd(sn_port, link, tgt_ip, tgt_port, tcp, udp):
    try:
        # will print error message itself
        tgt_ip = get_target_ip(tgt_ip)
        sn_info = get_service_node(link, tgt_ip, None, 0)
        if sn_info == None:
            print "No service node found on link %s" % link.name
            SIM_command_has_problem()
            return
        (link, sn) = sn_info
        sn_ip_link = get_sn_ip_link(sn, link)
        if len(sn_ip_link) != 1:
            print "Cannot get service node IP"
            SIM_command_has_problem()
            return
        disconnect_real_network_port_out(sn_port, sn_ip_link[0], tgt_port, tgt_ip, sn, tcp, udp)
    except Exception, msg:
        print msg
        return

def connect_real_network_napt_cmd(link):
    try:
        sn_info = get_service_node(link, None, None, 0)
        if sn_info == None:
            print "No service node found on link %s" % link.name
            SIM_command_has_problem()
            return
        (link, sn) = sn_info
        if sn.napt_enable:
            print "NAPT already enabled."
            return

        forwards_before = get_napt_forwards()

        sn.napt_enable = 1
        pfo = setup_outgoing_port_forward(sn)
        setup_incoming_port_forward(sn, pfo) # Empty in for ALG hooks

        forwards_after = get_napt_forwards()
        new_forwards = [x for x in forwards_after if not (x in forwards_before)]
        if new_forwards:
            print_napt_forwards(new_forwards)
        else:
            print "Port forwarding setup failed."
            SIM_command_has_problem()
    except Exception, msg:
        print msg
        return

default_port = 4000
def connect_real_network_cmd(tgt_ip, link, sn_ip):
    global default_port
    try:
        tgt_ip = get_target_ip(tgt_ip)
        (link, sn) = get_service_node(link, tgt_ip, sn_ip, 1)
        if tgt_ip in get_sn_ips(sn):
            print "Cannot port forward to the service node"
            SIM_command_has_problem()
            return
        connect_real_network_napt_cmd(link)
        connect_real_network_port_in([str_t, "ftp"],
                                     default_port + 21, tgt_ip, sn, 1, 0, 0)
        connect_real_network_port_in([str_t, "telnet"],
                                     default_port + 23, tgt_ip, sn, 1, 0, 0)
        connect_real_network_port_in([str_t, "http"],
                                     default_port + 80, tgt_ip, sn, 1, 0, 0)

        forwards_before = get_dns_forwards()
        sn.allow_real_dns = 1
        forwards_after = get_dns_forwards()
        new_forwards = [x for x in forwards_after
                        if not (x in forwards_before)]
        print_dns_forwards(new_forwards)

        enable_ftp_alg_cmd(sn, check_enabled = False)

        default_port += 1000
    except Exception, msg:
        print msg
        return

new_command("connect-real-network-port-in", connect_real_network_port_in_cmd,
            [arg((int_t, str_t), ("target-port", "service"),
                 expander = (service_expander, None)),
             arg(obj_t("link", "ethernet-link"), "ethernet-link"),
             arg(int_t, "host-port", "?", None),
             arg(str_t, "target-ip", "?", ""),
             arg(flag_t, "-tcp", "?", 0),
             arg(flag_t, "-udp", "?", 0),
             arg(flag_t, "-f", "?", 0)],
            type = ["Real Network"],
            short = "setup port forwarding to a simulated machine",
            see_also = ['connect-real-network',
                        'connect-real-network-port-out',
                        'connect-real-network-napt',
                        'connect-real-network-host',
                        'connect-real-network-bridge',
                        'connect-real-network-router'],
            doc = """
Enables or disables port forwarding from the host that Simics is running on, to
a simulated machine, specified by <arg>target-ip</arg>. The externally
visible port <arg>host-port</arg> on the host is mapped to the port
<arg>target-port</arg> on the simulated machine. For commonly used services
the string argument <arg>service</arg> can be used instead of a port
number. If several Ethernet links exists, the one that the simulated
machine is connected to must be specified.

The flags <arg>-tcp</arg> and <arg>-udp</arg> can be used to specify the
protocol to forward. The default is to forward only the usual protocol
for named services and both tcp and udp for numerically specified
ports.

The flag <arg>-f</arg> can be used to cause the command to fail if the
suggested host port could not be allocated, without the flag the command will
assign the first availble port starting from the specified host port and upwards.

The <arg>host-port</arg> given is only a hint, and the actual port
used may be a different one. The command output shows the actual port
used, and it can also be determined by inspecting the connections
attribute in the appropriate port forwarding object.
""", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="696")

new_command("disconnect-real-network-port-in", disconnect_real_network_port_in_cmd,
            [arg((int_t, str_t), ("target-port", "service"),
                 expander = (service_expander, None)),
             arg(obj_t("link", "ethernet-link"), "ethernet-link"),
             arg(str_t, "target-ip", "?", ""),
             arg(flag_t, "-tcp", "?", 0),
             arg(flag_t, "-udp", "?", 0)],
            type = ["Real Network"],
            short = "remove port forwarding to a simulated machine",
            doc_with = "connect-real-network-port-in", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="737")

new_command("connect-real-network-port-out", connect_real_network_port_out_cmd,
            [arg(int_t, "service-node-port"),
             arg(obj_t("link", "ethernet-link"), "ethernet-link"),
             arg(str_t, "target-ip"),
             arg(int_t, "target-port"),
             arg(flag_t, "-tcp", "?", 0),
             arg(flag_t, "-udp", "?", 0)],
            type = ["Real Network"],
            short = "setup port forwarding to real machine",
            see_also = ['connect-real-network',
                        'connect-real-network-port-in',
                        'connect-real-network-napt',
                        'connect-real-network-host',
                        'connect-real-network-bridge',
                        'connect-real-network-router'],
            doc = """
Enables port forwarding to a machine on the real network. Traffic
targeting port <arg>service-node-port</arg> on the service node connected to
<arg>ethernet-link</arg> will be forwarded to port
<arg>target-port</arg> on <arg>target-ip</arg>.

Both tcp and udp will be forwarded unless one of the <arg>-tcp</arg> or
<arg>-udp</arg> flags are given in which case only that protocol will
be forwarded.
""", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="748")

new_command("disconnect-real-network-port-out", disconnect_real_network_port_out_cmd,
            [arg(int_t, "service-node-port"),
             arg(obj_t("link", "ethernet-link"), "ethernet-link"),
             arg(str_t, "target-ip"),
             arg(int_t, "target-port"),
             arg(flag_t, "-tcp", "?", 0),
             arg(flag_t, "-udp", "?", 0)],
            type = ["Real Network"],
            short = "remove port forwarding to real machine",
            doc_with = "connect-real-network-port-out", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="774")

new_command("connect-real-network-napt", connect_real_network_napt_cmd,
            [arg(obj_t("link", "ethernet-link"), "ethernet-link")],
            type = ["Real Network"],
            short = "enable NAPT from simulated network",
            see_also = ['connect-real-network',
                        'connect-real-network-port-in',
                        'connect-real-network-port-out',
                        'connect-real-network-host',
                        'connect-real-network-bridge',
                        'connect-real-network-router'],
            doc = """
Enables machines on the simulated network to initiate accesses
to real hosts without the need to configure the simulated machine
with a real IP address. NAPT (Network Address Port Translation)
uses the IP address and a port number of the host that Simics
is running on to perform the access. Replies are then translated
back to match the request from the simulated machine. This command
also enables NAPT for accesses that are initiated from the simulated
machine.
""", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="785")

new_command("connect-real-network-napt", connect_real_network_napt_cmd,
            [],
            type = ["Real Network", "Networking"],
            namespace = "ethernet-link",
            short = "enable NAPT from simulated network",
            see_also = ['<ethernet-link>.connect-real-network-host',
                        '<ethernet-link>.connect-real-network-bridge',
                        '<ethernet-link>.connect-real-network-router'],
            doc_with = 'connect-real-network-napt', filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="806")

new_command("connect-real-network", connect_real_network_cmd,
            [arg(str_t, "target-ip", "?", ""),
             arg(obj_t("link, ", "ethernet-link"), "ethernet-link", "?", None),
             arg(str_t, "service-node-ip", "?", "")],
            type = ["Real Network"],
            short = "connect a simulated machine to the real network",
            see_also = ['default-port-forward-target',
                        'connect-real-network-napt',
                        'connect-real-network-port-in',
                        'connect-real-network-port-out',
                        'connect-real-network-host',
                        'connect-real-network-bridge',
                        'connect-real-network-router'],
            doc = """
Enables port forwarding from the host that Simics is running on, to
a simulated machine specified by <arg>target-ip</arg>, allowing
access from real hosts to the simulated one. Ports are opened on the
host for a number of commonly used protocol (such as ftp and telnet),
additional ports can be configured using the
<cmd>connect-real-network-port-in</cmd> command. Port forwarding can be
enabled for several simulated machines at the same time. This command
also enables NAPT for accesses that are initiated from the simulated
machine. If several Ethernet links exists, the one that the simulated
machine is connected to must be specified. If no Ethernet link exists,
one will be created and all Ethernet devices are connected to it.
A <arg>service-node</arg> will also be added to the link if there isn't
one connected already. If a service-node is added it will either get
the IP address <arg>service-node-ip</arg> if it was specified, or the IP
of the target with the lowest byte set to 1. If a default port-forwarding
target has been set using the <cmd>default-port-forward-target</cmd>
command, then the <arg>target-ip</arg> argument can be left out.
""", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="816")

def list_pf_setup_cmd():
    napt_forwards = get_napt_forwards()
    dns_forwards = get_dns_forwards()
    incoming_forwards = get_incoming_forwards()
    outgoing_forwards = get_outgoing_forwards()

    print_napt_forwards(napt_forwards)
    if napt_forwards and dns_forwards:
        print
    print_dns_forwards(dns_forwards)
    if (napt_forwards or dns_forwards) and incoming_forwards:
        print
    print_incoming_forwards(incoming_forwards)
    if (napt_forwards or dns_forwards or incoming_forwards) and outgoing_forwards:
        print
    print_outgoing_forwards(outgoing_forwards)

new_command("list-port-forwarding-setup", list_pf_setup_cmd,
            [],
            type = ["Real Network"],
            short = "view the port forwarding setup",
            see_also = ['connect-real-network',
                        'connect-real-network-napt',
                        'connect-real-network-port-in',
                        'connect-real-network-port-out',],
            doc = """
Lists the current port forwarding and NAPT configuration.
""", filename="/mp/simics-3.0/src/extensions/service-node/gcommands.py", linenumber="866")
