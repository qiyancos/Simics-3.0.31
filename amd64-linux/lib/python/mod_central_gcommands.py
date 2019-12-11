from cli import *
import sim_commands
import os
import sys
import socket

def get_username():
    try:
        return os.environ['USER']
    except KeyError:
        return "user"

#
# -------------------- new-central-server --------------------
#

def new_server_cmd(port, filename, min_latency):
    if port == -1:
        port = None
    if not filename:
        filename = None

    if filename and sys.platform == "win32":
        print "UNIX file sockets are not supported on Windows."
        filename = None

    attrs = [["tcp_port", port],
             ["unix_socket", filename],
             ["unix_socket_mode", 0700]]

    if min_latency != None:
        # Specify the frequency just to make sure we scale min_latency
        # correctly.
        attrs.extend([["frequency", 1000000000000],
                      ["min_latency", min_latency * 1000]])

    server = SIM_create_object("central-server", "central-server",
                               attrs)
    print "Created", server.name

if sys.platform == "win32":
    default_unix_file = None
else:
    default_unix_file = "/tmp/simics-central.%s" % get_username()

new_command("new-central-server", new_server_cmd,
            [arg(int_t, "port", "?", 1909),
             arg(str_t, "file", "?", default_unix_file),
             arg(int_t, "min-latency", "?", None)],
            type = ["Distributed Simulation"],
            short = "create a Simics Central server",
            doc = """
Create a Simics Central server object.  The server will by default
listen to Simics Central client connections on TCP port 1909 and, on
systems supporting it, UNIX file socket
<tt>/tmp/simics-central.<i>user</i></tt>.  It will also accept
connections from a Central client in the same Simics process.

The <arg>port</arg> argument can be used to change the TCP listen
port.  By setting it to -1, the server will not listen for TCP
connections.  By setting it to 0, the server will choose an available
TCP port number.  The used port number will be printed when the server
successfully opened the port.

The <arg>file</arg> argument can be used to change the file name for
the UNIX file socket.  And empty string disables it.

The <arg>min-latency</arg> argument specifies the minimum latency in
nanoseconds for inter-simics communication enforced by Simics Central.
""", filename="/mp/simics-3.0/src/extensions/central/gcommands.py", linenumber="46")


#
# -------------------- connect-central --------------------
#

def connect_central_cmd(server, reconnect):
    _, server, _ = server

    if "AF_UNIX" in dir(socket) and server == "localhost":
        server = "/tmp/simics-central.%s" % os.environ["USER"]

    try:
        client = SIM_get_object("central-client")
    except:
        client = SIM_create_object("central-client", "central-client", [])
        print "Created", client.name

    if not client:
        print "Failed to create the central-client object"
        SIM_command_has_problem()
        return

    client.server = server
    client.reconnect = reconnect
    if client.connected:
        print "Connected to Simics Central"

new_command("connect-central", connect_central_cmd,
            [arg((str_t, obj_t("server", "central-server")), ("server", "obj")),
             arg(int_t, "reconnect", "?", 0)],
            type  = ["Distributed Simulation"],
            short = "connect to Simics Central",
            see_also = ["new-central-server", "<central-client>.disconnect", "<central-client>.connect"],
            doc = """
Connect Simics to a Simics Central server.

The <arg>server</arg> argument specifies the server to connect to.  It
is either of the form <tt>&lt;addr&gt;[:&lt;port&gt;]</tt> if a TCP
connection should be used, or a file name if a file socket should be
used. This is the same as the command line argument <tt>-central</tt>,
but can be executed at any time.

To connect to a server object in the same Simics, use the
<arg>obj</arg> argument instead.

The <arg>reconnect</arg> argument gives the time between tries to
connect to the server if a connection can't be established, or if the
connection is lost. A value of zero disables reconnection.  The
default is to not try to reconnect.
""", filename="/mp/simics-3.0/src/extensions/central/gcommands.py", linenumber="99")


def client_connect(arg, _obj):
    if SIM_get_class_attribute("central-client", "connect_at_startup") == 0:
        return
    central_host = SIM_get_class_attribute("central-client", "central_host")

    if "AF_UNIX" in dir(socket) and central_host == "localhost":
        central_host = "/tmp/simics-central.%s" % os.environ["USER"]
    
    obj = None
    for o in SIM_all_objects():
        if o.class_data == "central-client":
            obj = o
            break
    if obj == None:
        obj = SIM_create_object("central-client", "central-client",
                                [["server", central_host]])

SIM_hap_add_callback("Core_Initial_Configuration", client_connect, None)
