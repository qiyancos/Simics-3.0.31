from cli import *
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

#
# --------------- <central-server>.info ---------------
#

def get_server_info(server):
    unix_socket = server.unix_socket
    connections = server.connections
    local_conn = None
    unix_conns = []
    tcp_conns = []
    for _,_,x,_,_ in server.connections:
        if hasattr(x, 'server'):
            local_conn = x
        elif x == unix_socket:
            unix_conns.append(x)
        else:
            tcp_conns.append(x)

    info = [(None,
             [("Global clock frequency", "%s" % fmt_prefixed_unit(server.frequency, "Hz")),
              ("Minimum latency", "%s" % fmt_prefixed_unit(server.min_latency * 1.0 / server.frequency,
                                                            "s")),
              ("Local client", local_conn)]),
            ("TCP/IP connections",
             [("Listen port", server.tcp_port),
              ("Clients", len(tcp_conns))]),
            ("File socket connections",
             [("Socket file", unix_socket),
              ("Clients", len(unix_conns))]),
            ("Links",
             [(name, "id=%d class=%s master=%d" % (id, cls, master))
              for id, name, cls, master in server.links])]

    return info

sim_commands.new_info_command("central-server", get_server_info)

#
# -------------- connections --------------
#

def connections_obj_cmd(obj):
    try:
        c = obj.connections
    except Exception, msg:
        print msg
        return
    else:
        print_columns([Just_Left, Just_Left, Just_Left, Just_Left, Just_Left],
                      [["ID", "Proto", "Addr", "Version", "Description"]] + c)

new_command("connections", connections_obj_cmd,
            [],
            type  = "central commands",
            short = "list current connections",
            namespace = "central-server",
            see_also = ["new-central-server"],
            doc = """
List all available connections, including the target,
the type, and the current status of the connection.
""", filename="/mp/simics-3.0/src/extensions/central/commands.py", linenumber="74")

#
# -------------- disconnect --------------
#

#def disconnect_obj_cmd(obj, poly):
#    if poly[0] == flag_t:
#        try:
#            c = obj.connections
#        except Exception, msg:
#            print msg
#            return
#        for x in c:
#            try:
#                obj.disconnect = x[0]
#            except Exception, msg:
#                print msg
#    else:
#        try:
#            obj.disconnect = poly[1]
#        except Exception, msg:
#            print msg
#
#new_command("disconnect", disconnect_obj_cmd,
#            [arg((flag_t,int_t), ("-all", "id"))],
#            type  = "central commands",
#            short = "remove connection",
#            namespace = "central",
#            doc = """
#Remove connection with specified ID.
#""")

#
# --------------- <central-client>.info ---------------
#

def get_client_info(client):
    info = [(None,
             [("Identification", client.description),
              ("Server", client.server)])]
    return info

sim_commands.new_info_command("central-client", get_client_info)

#
# -------------- <central-client>.connect --------------
#

def client_connect_cmd(client, server):
    _, server, _ = server
    client.server = server

new_command("connect", client_connect_cmd,
            [arg((str_t, obj_t("server", "central-server")), ("server", "obj"))],
            type = "central commands",
            namespace = "central-client",
            short = "connect to Simics Central",
            see_also = ["connect-central", "new-central-server", "<central-client>.disconnect"],
            doc = """
Connect Simics to a Simics Central server.

The <arg>server</arg> argument specifies the server to connect to.  It
is either of the form <tt>&lt;addr&gt;[:&lt;port&gt;]</tt> if a TCP
connection should be used, or a file name if a file socket should be
used.

To connect to a server object in the same Simics, use the
<arg>obj</arg> argument instead.
""", filename="/mp/simics-3.0/src/extensions/central/commands.py", linenumber="136")


#
# -------------- <central-client>.disconnect --------------
#

def client_disconnect_cmd(client):
    client.server = None

new_command("disconnect", client_disconnect_cmd,
            [],
            type = "central commands",
            namespace = "central-client",
            short = "disconnect from Simics Central",
            see_also = ["connect-central", "new-central-server", "<central-client>.connect"],
            doc = """
Disconnect from the Simics Central server.

This will make this Simics process standalone, and no longer part of a
distributed simulation session.
""", filename="/mp/simics-3.0/src/extensions/central/commands.py", linenumber="162")

#
# -------- <central-client>.links --------
#

def client_links_cmd(client):
    links = client.links
    print_columns([Just_Right, Just_Left, Just_Left],
                  [["ID", "Name", "Class"]] +
                  [[iff(id == 0xffffffffffffffffL or id == -1,
                        '-', str(id)), obj.name, obj.classname] for [id,obj] in links])

new_command("links", client_links_cmd,
            [],
            type = "central commands",
            namespace = "central-client",
            short = "list connected links",
            doc = """
List the link objects in this process that are shared in a distributed
session.

When connected to a Simics Central, the link object in this list will
be distributed.
""", filename="/mp/simics-3.0/src/extensions/central/commands.py", linenumber="186")
