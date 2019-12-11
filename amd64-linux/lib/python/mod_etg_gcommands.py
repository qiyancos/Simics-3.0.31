from cli import *

def object_exists(name):
    try:
        SIM_get_object(name)
        return 1
    except:
        return 0

etg_mac_idx = 0
def new_etg(name, link, ip, netmask, dst, gw, idx, pps, psize):
    if name:
        if object_exists(name):
            print name, "already exists"
            SIM_command_has_problem()
            return
    else:
        name = get_available_object_name('etg')

    if not gw:
        gw = "0.0.0.0"

    if not pps:
        pps = 10

    if not psize:
        psize = 100

    # Select a MAC address
    global etg_mac_idx
    if idx != None:
        etg_mac_idx = idx
    mac = "10:10:10:10:30:%02x" % etg_mac_idx
    etg_mac_idx += 1

    # Pick random queue and recorder
    queue = None
    recorder = None
    for o in SIM_all_objects():
        if instance_of(o, "processor"):
            queue = o
        if o.classname == "recorder":
            recorder = o
        if queue and recorder:
            break
    if not queue:
        print "Couldn't find a CPU to use"
        SIM_command_has_problem()
        return
    if not recorder:
        print "Couldn't find a recorder to use"
        SIM_command_has_problem()
        return

    etg = SIM_create_object("etg", name,
                            [["link", link],
                             ["ip", ip],
                             ["netmask", netmask],
                             ["dst-ip", dst],
                             ["gateway", gw],
                             ["mac-address", mac],
                             ["pps", pps],
                             ["packet-size", psize],
                             ["queue", queue],
                             ["recorder", recorder]])
    if SIM_is_interactive():
        print "Created traffic generator %s.  Use '%s.start' to enable it." % (etg.name, etg.name)

new_command("new-etg", new_etg,
            [arg(str_t, "name", "?"),
             arg(obj_t("link", "ethernet-link"), "link"),
             arg(str_t, "ip"), arg(str_t, "netmask"), arg(str_t, "target"),
             arg(str_t, "gw", "?"),
             arg(int_t, "idx", "?", None),
             arg(int_t, "pps", "?"), arg(int_t, "size", "?")],
            type = ["Ethernet"],
            short = "Create an Ethernet traffic generator",
            doc = """
Create a new <class>etg</class> object.
""", filename="/mp/simics-3.0/src/devices/etg/gcommands.py", linenumber="69")

