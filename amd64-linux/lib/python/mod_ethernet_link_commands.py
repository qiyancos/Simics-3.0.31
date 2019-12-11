from cli import *
import sim_commands

import os, signal, string, struct, sys
import sim

from mod_ethernet_link_gcommands import net_adapter_expander
from mod_ethernet_link_gcommands import host_access_expander
from mod_ethernet_link_gcommands import real_network_host_cmd
from mod_ethernet_link_gcommands import real_network_router_cmd
from mod_ethernet_link_gcommands import real_network_bridge_cmd
from mod_ethernet_link_gcommands import del_rn_default_route

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
    import operator
    devices = obj.devices
    doc = ([(None,
             [#("Timing granularity", fmt_prefixed_unit(obj.frequency, "Hz")),
              ("Latency",
               fmt_prefixed_unit(obj.latency * 1.0 / obj.frequency, "s")),
              ("Distribution", iff(obj.central, "global", "local")),
              ("Filtering", iff(obj.filter_enable, "enabled", "disabled"))]),
            ("Devices",
             [("Local devices",
               ["<%d:%d> %s" % (lid, iff(gid is None, -1, gid), name)
                for gid, lid, name, dev, _ in devices if dev]),
              ("Remote devices",
               ["<%d:%d> %s" % (lid, iff(gid is None, -1, gid), name)
                for gid, lid, name, dev, _ in devices if not dev])])])
    try:
        sns = [x.service_node
               for x in sim.classes['service-node-device'].objects.values()
               if x.link == obj]
    except:
        sns = []
    have_napt = reduce(operator.or_, [x.napt_enable for x in sns], 0)
    rns = [x for x in SIM_all_objects() if instance_of(x, "real_network")
           and x.link == obj]

    try:
        pfs = (sim.classes['port-forward-incoming-server'].objects.values()
               + sim.classes['port-forward-outgoing-server'].objects.values())
    except:
        pfs = []
    pfs_sns = [x.udp for x in pfs] + [x.tcp for x in pfs]
    have_pf = reduce(operator.or_, [(x in sns) for x in pfs_sns], 0)

    rn_list = []
    if len(rns):
        for rn in rns:
            rn_list += [(rn.name,
                         "Host interface '%s'%s" %
                         (rn.interface,
                          iff(rn.connected, "", " not connected")))]
    if have_pf:
        rn_list += [("Port-forwarding", "enabled")]
    if have_napt:
        rn_list += [("NAPT", "enabled")]
    if len(rn_list) == 0:
        rn_list = [("Connected", "No")]

    doc += [ ("Real network connection", rn_list)]
    return doc

def fmt_mac(mac):
    return ":".join(["%02x" % b for b in mac])

def fmt_macs(macs):
    return ", ".join([mac + "/" + mask for mac,mask in macs])

def get_status(obj):
    frames = []
    pending = obj.pending_frames
    for seq, handled, timestamp, sender, hascrc, frame in pending:
        dst = frame[0:6]
        src = frame[6:12]
        frames.append((str(seq),
                       "%s -> %s; size: %d bytes time: %d"
                       % (fmt_mac(src), fmt_mac(dst), len(frame), timestamp)))

    return [(None,
             [("Frames transmitted", obj.nframes),
              ("Bytes transmitted", obj.nbytes)]),
            ("MAC addresses",
             [("<%d:%d> %s" % (lid, iff(gid is None, -1, gid), name),
               iff(promisc, "PROMISCUOUS ", "") + fmt_macs(macs))
              for gid, lid, name, _, (macs, promisc) in obj.devices]),
            ("Frames in transfer", frames)]

sim_commands.new_info_command("ethernet-link", get_info)
sim_commands.new_status_command("ethernet-link", get_status)

#
# real-network commands
#

new_command("connect-real-network-host", real_network_host_cmd,
            [arg(str_t, "interface", "?", "", expander = net_adapter_expander),
             arg(flag_t, "-persistent")],
            type = ["Real Network", "Networking"],
            namespace = "ethernet-link",
            short = "connect to the real network",
            see_also = ['connect-real-network-host',
                        '<ethernet-link>.connect-real-network-bridge',
                        '<ethernet-link>.connect-real-network-router'],
            doc_with = 'connect-real-network-host', filename="/mp/simics-3.0/src/devices/ethernet-link/commands.py", linenumber="117")

new_command("connect-real-network-bridge", real_network_bridge_cmd,
            [arg(str_t, "interface", "?", "", expander = net_adapter_expander),
             arg(str_t, "host-access", "?", "", expander = host_access_expander),
             arg(flag_t, "-no-mac-xlate"),
             arg(flag_t, "-persistent"),
             arg(flag_t, "-propagate-link-status")],
            type = ["Real Network", "Networking"],
            namespace = "ethernet-link",
            short = "connect to the real network",
            see_also = ['connect-real-network-bridge',
                        '<ethernet-link>connect-real-network-host',
                        '<ethernet-link>.connect-real-network-router'],
            doc_with = 'connect-real-network-bridge', filename="/mp/simics-3.0/src/devices/ethernet-link/commands.py", linenumber="128")

new_command("connect-real-network-router", real_network_router_cmd,
            [arg(str_t, "ip"),
             arg(str_t, "netmask", "?", "255.255.255.0"),
             arg(str_t, "gateway", "?", ""),
             arg(str_t, "interface", "?", "", expander = net_adapter_expander)],
            type = ["Real Network", "Networking"],
            namespace = "ethernet-link",
            short = "connect to the real network",
            see_also = ['connect-real-network-router',
                        '<ethernet-link>.connect-real-network-host',
                        '<ethernet-link>.connect-real-network-bridge'],
            doc_with = 'connect-real-network-router', filename="/mp/simics-3.0/src/devices/ethernet-link/commands.py", linenumber="142")

def disconnect_cmd(link):
    # see also disconnect in real-net and global command below
    rns = [x for x in SIM_all_objects() if instance_of(x, "real_network")
           and x.link == link]
    for rn in rns:
        del_rn_default_route(rn)
        print "Disconnecting link %s from the real network." % rn.link.name
        SIM_delete_object(rn)

new_command("disconnect-real-network", disconnect_cmd,
            type = ["Real Network", "Networking"],
            short = "disconnect from the real network",
            namespace = "ethernet-link",
            see_also = ['connect-real-network-host',
                        'connect-real-network-bridge',
                        'connect-real-network-router'],
            doc_with = 'disconnect-real-network', filename="/mp/simics-3.0/src/devices/ethernet-link/commands.py", linenumber="164")

#
# Commands previously in netutils.py
#

def find_in_path(binary):
    path = os.environ['PATH']
    path = path.split(':')
    for p in path:
        full_path = p + "/" + binary
        if os.path.exists(full_path):
            return full_path
    return None

def capture_frame_from_link(fd, link, timestamp):
    sec = timestamp / 1000000000
    usec = (timestamp % 1000000000) / 1000
    frame = link.last_frame
    frame = string.join(map(chr, frame), "")
    header = struct.pack("IIII", sec, usec, len(frame), len(frame))
    try:
        os.write(fd, header)
        os.write(fd, frame)
    except OSError:
        SIM_hap_delete_callback_obj("Ethernet_Frame", link, capture_frame_from_link, fd)

def capture_frame_from_device(fd, object):
    time = SIM_time(object)
    sec = int(time)
    usec = int((time - sec) * 1000000000.0)
    frame = string.join(map(chr, object.last_frame), "")
    header = struct.pack("IIII", sec, usec, len(frame), len(frame))
    try:
        os.write(fd, header)
        os.write(fd, frame)
    except OSError:
        SIM_hap_delete_callback_obj("Ethernet_Receive", object, capture_frame_from_device, fd)
        SIM_hap_delete_callback_obj("Ethernet_Transmit", object, capture_frame_from_device, fd)

def write_pcap_header(fd):
    magic = 0xa1b2c3d4
    major = 2
    minor = 4
    thiszone = 0
    sigfigs = 0
    snaplen = 2048
    linktype = 1
    header = struct.pack("IHHIIII", magic, major, minor, thiszone, sigfigs, snaplen, linktype)
    os.write(fd, header)

def kill_process(pid, unused):
    os.kill(pid, signal.SIGTERM)

def object_expander(string):
    return get_completions(string, conf.all_object_names)

def start_capture(link, device, pid, fd):
    if pid:
        SIM_hap_add_callback("Core_At_Exit", kill_process, pid)
    write_pcap_header(fd)
    if device:
        SIM_hap_add_callback_obj("Ethernet_Receive", device, 0,
                                 capture_frame_from_device, fd)
        SIM_hap_add_callback_obj("Ethernet_Transmit", device, 0,
                                 capture_frame_from_device, fd)
    else:
        SIM_hap_add_callback_obj("Ethernet_Frame", link, 0,
                                 capture_frame_from_link, fd)

def tcpdump_cmd(link, device, tcpdump_flags):
    if link and device:
        print "Specify at most one of link or device"
        SIM_command_has_problem()
    xterm_path = find_in_path("xterm")
    if not xterm_path:
        print "No 'xterm' binary found in PATH.", msg
        SIM_command_has_problem()
        return
    tcpdump_path = find_in_path("tcpdump")
    if not tcpdump_path:
        print "No 'tcpdump' binary found in PATH."
        SIM_command_has_problem()
        return
    (read_fd, write_fd) = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(write_fd)
        os.setsid()
        os.execl(xterm_path, "xterm", "-title", "tcpdump", "-e", "/bin/sh", "-c", (tcpdump_path + " -r - %s <&%d" % (tcpdump_flags, read_fd)))
        os._exit(1)
    os.close(read_fd)
    start_capture(link, device, pid, write_fd)

if sys.platform[:5] != "win32":
    new_command("tcpdump", tcpdump_cmd,
                [arg(obj_t("ethernet link object", "ethernet_link"), "link", "?"),
                 arg(obj_t("ethernet device object", "ethernet_device"), "device", "?"),
                 arg(str_t, "tcpdump-flags", "?", "-n -v")],
                type  = "network commands",
                short = "run the tcpdump program",
                doc = """\
                Runs the <b>tcpdump</b> program in a separate console, with network
                traffic captured from simulated ethernet networks. The
                <i>tcpdump-flags</i> are passed on unmodified to <b>tcpdump</b>.""", filename="/mp/simics-3.0/src/devices/ethernet-link/commands.py", linenumber="266")

def ethereal_cmd(link, device, flags):
    if link and device:
        print "Specify at most one of link or device"
        SIM_command_has_problem()
    ethereal_path = find_in_path("ethereal")
    wireshark_path = find_in_path("wireshark")
    if not ethereal_path and not wireshark_path:
        print "No 'ethereal' or 'wireshark' binary found in PATH."
        SIM_command_has_problem()
        return
    # prefer wireshark
    if wireshark_path:
        ethereal_path = wireshark_path
        prog = "wireshark"
    else:
        prog = "ethereal"
    (read_fd, write_fd) = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(write_fd)
        os.setsid()
        os.dup2(read_fd, 0)
        os.close(read_fd)
        os.execv(ethereal_path, [prog, "-k", "-i", "-"] + flags.split())
        os._exit(1)
    os.close(read_fd)
    start_capture(link, device, pid, write_fd)

if sys.platform[:5] != "win32":
    new_command("ethereal", ethereal_cmd,
                [arg(obj_t("ethernet link object", "ethernet_link"), "link", "?"),
                 arg(obj_t("ethernet device object", "ethernet_device"), "device", "?"),
                 arg(str_t, "ethereal-flags", "?", "-S -l")],
                type  = "network commands",
                short = "run the ethereal program",
                doc = """\
                Runs the <b>wireshark</b> or <b>ethereal</b> program
                in a separate console, with network traffic captured
                from simulated ethernet networks. The
                <i>ethereal-flags</i> are passed on unmodified to
                program.""", filename="/mp/simics-3.0/src/devices/ethernet-link/commands.py", linenumber="306")

def pcapdump_cmd(filename, link, device):
    if link and device:
        print "Specify at most one of link or device"
        SIM_command_has_problem()
    try:
        O_BINARY = os.O_BINARY
    except:
        O_BINARY = 0
    try:
        fd = os.open(filename, os.O_WRONLY | os.O_CREAT | O_BINARY )
    except:
        print "failed to open %s" % filename
        return
    start_capture(link, device, None, fd)

new_command("pcapdump", pcapdump_cmd,
            [arg(filename_t(), "filename"),
             arg(obj_t("ethernet link object", "ethernet_link"), "link", "?"),
             arg(obj_t("ethernet device object", "ethernet_device"), "device", "?")],
            type  = "network commands",
            short = "save traffic in libpcap format",
            doc = """\
A trace of network traffic is saved to a file, in the format
implemented by <b>libpcap</b>, for use with libpcap based applications
such as <b>tcpdump</b> and <b>ethereal</b>.""", filename="/mp/simics-3.0/src/devices/ethernet-link/commands.py", linenumber="334")
