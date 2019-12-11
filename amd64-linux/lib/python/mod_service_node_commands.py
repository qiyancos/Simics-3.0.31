from cli import *
import sim_commands
import nic_common
import string

from mod_service_node_gcommands import get_first_queue

def get_sn_devs(obj):
    return [x for x in SIM_all_objects()
            if instance_of(x, "service-node-device") and x.service_node == obj]

def fmt_lease_time(t):
    if t == 0xffffffffL:
        return "infinite"
    else:
        return "%s s" % t

def ip_mask_shorthand(ip):
    ip = ip.split('/', 2)
    if len(ip) == 1:
        return ip[0], None
    ip, n = ip
    n = int(n)
    if n <= 8:
        mask = '%d.0.0.0' % (-(1 << (8 - n)) & 0xff)
    elif n <= 16:
        mask = '255.%d.0.0' % (-(1 << (16 - n)) & 0xff)
    elif n <= 24:
        mask = '255.255.%d.0' % (-(1 << (24 - n)) & 0xff)
    else:
        mask = '255.255.255.%d' % (-(1 << (32 - n)) & 0xff)
    return ip, mask

def dotted_decimal(ip_addr):
    if ip_addr == 0:
        return "*"
    else:
        return "%d.%d.%d.%d" % ((ip_addr >> 24) & 0xff, (ip_addr >> 16) & 0xff, (ip_addr >> 8) & 0xff, ip_addr & 0xff)

def add_route(obj, net, mask, gw, snd):
    rt = obj.routing_table
    rt.append([net, mask, gw, snd])
    obj.routing_table = rt


def get_info(obj):
    snds = get_sn_devs(obj)
    doc = []
    for snd in snds:
        doc += [("Interface '%s'" % snd.name,
                 [("Network", snd.link),
                  ("MAC address", snd.mac_address),
                  ("IP address", snd.ip_address),
                  ("Netmask", snd.netmask),
                  ("MTU", snd.mtu)])]
    doc += [ ("DHCP",
              [("Maximum lease time", fmt_lease_time(obj.dhcp_max_lease_time))])]
    port_forward_info = []
    for o in SIM_all_objects():
        if o.classname == "port-forward-outgoing-server" and o.tcp == obj:
            for out_conn in o.connections:
                if out_conn[1] == 0:
                    listen_port = "All %s output ports" % out_conn[0]
                else:
                    listen_port = "Output %s %s:%d" % (out_conn[0], out_conn[2], out_conn[1])
                if len(out_conn) > 2:
                    forward_port = "Forwarded to %s:%d" % (out_conn[3], out_conn[4])
                else:
                    if obj.napt_enable:
                        forward_port = "Forwarded with NAPT"
                    else:
                        forward_port = "Useless with napt_enable."
                port_forward_info.append((listen_port, forward_port))
    ports = []
    output = {}
    for o in SIM_all_objects():
        if o.classname == "port-forward-incoming-server" and o.tcp == obj:
            for in_conn in o.connections:
                ports.append((in_conn[0], in_conn[1]))
                output[(in_conn[0], in_conn[1])] = (("Input %s port %5d" % (in_conn[0], in_conn[1]), "Forwarded to %s:%d" % (in_conn[2], in_conn[3])))
            for in_conn in o.temporary_connections:
                ports.append((in_conn[0], in_conn[1]))
                output[(in_conn[0], in_conn[1])] = (("Input %s port %5d" % (in_conn[0], in_conn[1]), "Temporarily forwarded to %s:%d" % (in_conn[2], in_conn[3])))
    ports.sort()
    for p in ports:
        port_forward_info.append(output[p])
    if len(port_forward_info):
        doc += [ ("Port forwarding", port_forward_info) ]
    return doc

def get_tftp_status(obj):
    return [("TFTP sessions",
             [("%s:%d" % (ip, ctid), "%s %s (%d blocks)" % (method, filename, blocks))
              for stid, ctid, method, ip, filename, blocks in obj.tftp_sessions])]

def get_status(obj):
    snds = get_sn_devs(obj)
    doc = []
    svc_list = map(lambda x: [x[0], iff(x[1], 'en', 'dis') + 'abled'],
                   obj.services.items())
    doc += [("Service Status", svc_list)]
    for snd in snds:
        if snd.link:
            doc += [("ARP table network %s" % snd.link.name,
                     snd.arp_table)]
    return doc + get_tftp_status(obj)

sim_commands.new_info_command("service-node", get_info)
sim_commands.new_status_command("service-node", get_status)

def get_host_name(node, ip):
    hosts = node.hosts
    for h in hosts:
        if h[1] == ip:
            if len(h[3]) > 0:
                return h[2] + "." + h[3]
            else:
                return h[2]
    else:
        return ""

def arp_cmd(obj, del_flag, del_ip):
    snds = get_sn_devs(obj)
    if del_flag:
        if del_ip == "":
            SIM_command_has_problem()
            print "No IP address delete speficied."
            return
        found = 0
        for snd in snds:
            arps = snd.arp_table
            if len([x for x in arps if x[0] == del_ip]):
                found = 1
                snd.arp_table = [x for x in arps if x[0] != del_ip]
        if not found:
            print "IP address %s not found in ARP table." % del_ip
        return

    print "Host                     IP               HWaddress            Interface"
    for snd in snds:
        arps = snd.arp_table
        for arp in arps:
            print "%-24s" % get_host_name(obj, arp[0]),
            print "%-16s" % arp[0],
            print "%-20s" % arp[1],
            print snd.name

new_command("arp", arp_cmd,
            [arg(flag_t, '-d'),
             arg(str_t, 'delete-ip', "?", "")],
            type  = "service-node commands",
            short = "inspect and manipulate ARP table",
            namespace = "service-node",
            doc = """
Prints the ARP table for the service node if called with no
arguments. An ARP entry can be deleted using the -d flag and
the IP address.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="148")

#
# Connect
#

simics_name_cnt = 0

def connect_node_cmd(node, link, ip, netmask):
    try:
        queue = get_first_queue()
    except:
        return

    if not netmask:
        try:
            ip, netmask = ip_mask_shorthand(ip)
        except:
            print "Malformed IP number"
            SIM_command_has_problem()
            return

    if not netmask:
        netmask = "255.255.255.0"

    snds = get_sn_devs(node)
    for snd in snds:
        if snd.link == link:
            SIM_command_has_problem()
            print "Service-node '%s' is already connected to link '%s'." % (
                node.name, link.name)
            return
    if SIM_is_interactive():
        print "Connecting %s to %s" % (node.name, link.name)
    snd = SIM_create_object("service-node-device",
                            "%s_%s_dev" % (node.name, link.name),
                            [['queue', queue],
                             ['link', link],
                             ['service_node', node],
                             ['ip_address', ip],
                             ['netmask', netmask]])
    if SIM_is_interactive():
        print "Setting IP address of %s on network %s to %s" % (node.name,
                                                                link.name,
                                                                ip)
    add_route(node, snd.net_ip, netmask, "0.0.0.0", snd)
    # add to host list, if not already there
    if len([x for x in node.hosts if x[1] == ip]) == 0:
        global simics_name_cnt
        # the domain name will always be 'network.sim'
        add_host_cmd(node, ip, 'simics%d' % simics_name_cnt,
                     None, snd.mac_address)
        simics_name_cnt += 1

new_command("connect", connect_node_cmd,
            [arg(obj_t('link', 'ethernet-link'), "link"),
             arg(str_t, 'ip'),
             arg(str_t, 'netmask', '?', '')],
            type  = "service-node commands",
            short = "connect to an ethernet link",
            namespace = "service-node",
            doc = """
Connect this service node to an Ethernet link object.

The <arg>ip</arg> argument gives the IP address that the service node
will use on the link, and the <arg>netmask</arg> argument the netmask.
Optionally, the netmask may be given in the <arg>ip</arg> argument as
a <tt>/bits</tt> suffix.  The netmask may also left out entirely, in
which case it will default to <tt>255.255.255.0</tt>.

""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="212")

#
# Routing commands
#

def route_obj_cmd(obj, print_port):
    rt = obj.routing_table

    if print_port:
        l = [["Destination", "Netmask", "Gateway", "Port"]]
    else:
        l = [["Destination", "Netmask", "Gateway", "Link"]]

    for r in rt:
        net = r[0]
        mask = r[1]
        gw = r[2]
        port = r[3]
        if net == "default":
            mask = ""
        if gw == "0.0.0.0":
            gw = ""
        if not print_port:
            port = port.link
        l.append([net, mask, gw, port.name])

    print_columns([Just_Left, Just_Left, Just_Left, Just_Left], l)

new_command("route", route_obj_cmd,
            [arg(flag_t, "-port")],
            type  = "service-node commands",
            short = "show the routing table",
            namespace = "service-node",
            doc = """
Print the routing table.

By default, the name of the link on which traffic will be send is
printed in the last column, but if the <param>-port</param> flag is
use, the port device will be printed instead.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="257")

def route_add_obj_cmd(obj, net, mask, gw, link):
    if instance_of(link, "service-node-device"):
        snd = link
    else:
        snds = [ x for x in get_sn_devs(obj) if x.link == link]
        if not snds:
            SIM_command_has_problem()
            print "Cannot add route to a network without a connection."
            return
        snd = snds[0]
    # Do not use 'link' after this point

    if not mask:
        try:
            net, mask = ip_mask_shorthand(net)
        except:
            print "Malformed network number"
            SIM_command_has_problem()
            return

    if not mask:
        print "Missing netmask"
        SIM_command_has_problem()
        return

    if gw == "":
        gw = "0.0.0.0"

    add_route(obj, net, mask, gw, snd)

new_command("route-add", route_add_obj_cmd,
            [arg(str_t, "net"),
             arg(str_t, "netmask", "?", ""),
             arg(str_t, "gateway", "?", ""),
             arg(obj_t('link', 'ethernet-link'), "link")],
            type  = "service-node commands",
            short = "add an entry to the routing table",
            namespace = "service-node",
            doc = """
Add to the routing table.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="300")

#
# DHCP commands
#

def add_host_cmd(obj, ip, name, domain, mac):
    hosts = obj.hosts

    host = [x for x in hosts if x[1] == ip]
    if len(host):
        hosts.remove(host[0])
        host = host[0]
    else:
        host = None

    n = name.split('.')
    name = n[0]
    d = string.join(n[1:], ".")
    if d and domain:
        print "Domain name specified twice."
        SIM_command_has_problem()
        return
    elif d:
        domain = d

    if domain:
        pass
    elif host:
        domain = host[3]
    else:
        domain = 'network.sim'

    if mac:
        pass
    elif host:
        mac = host[0]
    else:
        mac = None

    dups = [x for x in hosts if x[2] == name and x[3] == domain]
    if len(dups):
        print ("Host %s.%s is already in database with IP %s"
               % (name, domain, ip))
        SIM_command_has_problem()
        return

    if SIM_is_interactive():
        print ("%s host info for IP %s: %s.%s  %s %s"
               % (iff(host, "Changing", "Adding"),
                  ip, name, domain,
                  iff(mac, "MAC:", ""),
                  iff(mac, mac, "")))

    hosts.append([mac, ip, name, domain])
    try:
        obj.hosts = hosts
    except Exception, msg:
        print "Failed adding host information."
        SIM_command_has_problem()

new_command("add-host", add_host_cmd,
            [arg(str_t, "ip"),
             arg(str_t, "name"),
             arg(str_t, "domain", "?", None),
             arg(str_t, "mac", "?", None)],
            type = "service-node commands",
            short = "add host entry",
            namespace = "service-node",
            see_also = ['<service-node>.list-host-info'],
            doc = """
Add a host entry to the DHCP and DNS server tables.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="371")

def list_host_info_cmd(obj):
    l = [["IP", "name.domain", "MAC"]]
    for host in obj.hosts:
        l.append([host[1],
                  "%s.%s" % (host[2], host[3]),
                  iff(host[0], host[0], "")])
    print_columns([Just_Left, Just_Left, Just_Left], l)

new_command("list-host-info", list_host_info_cmd,
            [],
            type = "service-node commands",
            short = "print host info database",
            namespace = "service-node",
            see_also = ['<service-node>.add-host'],
            doc = """
Print the host information database, used by the DHCP
and DNS server.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="392")

def dhcp_add_pool_cmd(obj, poolsize, ip, name, domain):
    pools = obj.host_pools

    if not name:
        name = 'dhcp'

    if not domain:
        domain = 'network.sim'

    pools.append([poolsize, ip, name, domain, []])
    obj.host_pools = pools

new_command("dhcp-add-pool", dhcp_add_pool_cmd,
            [arg(int_t, "pool-size"),
             arg(str_t, "ip"),
             arg(str_t, "name", "?", None),
             arg(str_t, "domain", "?", None)],
            type = "service-node commands",
            short = "add DHCP pool",
            namespace = "service-node",
            doc = """
Add an IP address pool to the DHCP server.  The
<param>pool-size</param> parameter defines the number of available
addresses in the pool, starting with address <param>ip</param>.  The
DNS server will map the addresses to a name that is the
<param>name</param> parameter with a number appended, in the
<param>domain</param> domain.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="415")

def lease_obj_cmd(obj):
    # Pick any CPU to get a time stamp from.  We only need approximate
    # second granularity anyway.
    cpu = SIM_next_queue(None)

    leases = obj.dhcp_leases
    l = [["IP", "MAC", "Lease time", "Time left"]]
    for r in leases:
        ip = r[0]
        mac = r[1]
        client_id = r[2]
        time = r[3]
        timestamp = r[4]
        if time == 0xffffffffL:
            left = "-"
        else:
            age = long(SIM_time(cpu)) - timestamp
            left = time - age
            left = "%d s" % left
        l.append([ip, mac, fmt_lease_time(time), left])
    print_columns([Just_Left, Just_Left, Just_Left, Just_Left], l)

new_command("dhcp-leases", lease_obj_cmd,
            [],
            type  = "service-node commands",
            short = "show DHCP leases",
            namespace = "service-node",
            doc = """
Print the list of active DHCP leases.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="454")

#
# DNS commands
#

def enable_real_dns_cmd(obj):
        obj.allow_real_dns = 1

new_command("enable-real-dns", enable_real_dns_cmd,
            [],
            type  = "service-node commands",
            short = "enable real DNS",
            namespace = "service-node",
            doc = """
Enable forwarding of DNS queries for unknown hosts to the real DNS server.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="470")

def disable_real_dns_cmd(obj):
        obj.allow_real_dns = 0

new_command("disable-real-dns", disable_real_dns_cmd,
            [],
            type  = "service-node commands",
            short = "disable real DNS",
            namespace = "service-node",
            doc = """
Disable forwarding of DNS queries for unknown hosts to the real DNS server.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="482")

#
# UDP/TCP commands
#

def tcp_info_cmd(obj):
    l = [["Protocol", "Service", "Local address", "Foreign Address", "State"]]
    all_pcbs = obj.tcp_pcbs_all
    for r in all_pcbs:
        serv = r[8].name
        if r[10]:
            local = dotted_decimal(r[1]) + ":" + str(r[10])
        else:
            local = dotted_decimal(r[1]) + ":*"
        if r[11]:
            remote = dotted_decimal(r[2]) + ":" + str(r[11])
        else:
            remote = dotted_decimal(r[2]) + ":*"
        state = r[6]
        l.append(["TCP", serv, local, remote, state])
    all_pcbs = obj.udp_pcbs_all
    for r in all_pcbs:
        serv = r[10].name
        if r[7]:
            local = dotted_decimal(r[1]) + ":" + str(r[7])
        else:
            local = dotted_decimal(r[1]) + ":*"
        if r[8]:
            remote = dotted_decimal(r[2]) + ":" + str(r[8])
        else:
            remote = dotted_decimal(r[2]) + ":*"
        l.append(["UDP", serv, local, remote, ""])
    print_columns([Just_Left, Just_Left, Just_Left, Just_Left, Just_Left], l)

new_command("tcpip-info", tcp_info_cmd,
            [],
            type  = "service-node commands",
            short = "show TCP/IP info",
            namespace = "service-node",
            doc = """
Print all TCP/IP connections.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="524")

#
# service-node-device commands
#

def get_dev_info(obj):
    doc = [(None,
             [("Service node", obj.service_node),
              ("Network", obj.link),
              ("MAC address", obj.mac_address),
              ("IP address", obj.ip_address),
              ("Netmask", obj.netmask)])]
    return doc

def get_dev_status(obj):
    doc = [("ARP table",
            obj.arp_table)]
    return doc

sim_commands.new_info_command("service-node-device", get_dev_info)
sim_commands.new_status_command("service-node-device", get_dev_status)

def en_svc_expander(string, obj):
    return get_completions(string, [x[0] for x in obj.services.items()
                                    if not x[1]])

def dis_svc_expander(string, obj):
    return get_completions(string, [x[0] for x in obj.services.items()
                                    if x[1]])

def change_svc_status(obj, name, all, en):
    if all:
        names = obj.services.keys()
    else:
        names = [name]
    for name in names:
        if not name in obj.services:
            print "Unknown network service '%s'" % name
            SIM_command_has_problem()
            return
        if obj.services[name] != en:
            obj.services = {name : en}
            print "Network service '%s' %sabled." % (
                name, iff(en, 'en', 'dis'))
        else:
            print "Network service '%s' already %sabled." % (
                name, iff(en, 'en', 'dis'))

def enable_svc_cmd(obj, name, all):
    change_svc_status(obj, name, all, True)
    
def disable_svc_cmd(obj, name, all):
    change_svc_status(obj, name, all, False)

new_command("enable-service", enable_svc_cmd,
            [arg(str_t, 'name', '?', None, expander = en_svc_expander),
             arg(flag_t, '-all')],
            type  = "service-node commands",
            short = "enable network service",
            namespace = "service-node",
            doc = """
Enable a named network service in the service-node,
or all of the <param>-all</param> flag is used.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="586")

new_command("disable-service", disable_svc_cmd,
            [arg(str_t, 'name', '?', None, expander = dis_svc_expander),
             arg(flag_t, '-all')],
            type  = "service-node commands",
            short = "disable network service",
            namespace = "service-node",
            doc = """
Disable a named network service in the service-node,
or all of the <param>-all</param> flag is used.
""", filename="/mp/simics-3.0/src/extensions/service-node/commands.py", linenumber="597")
