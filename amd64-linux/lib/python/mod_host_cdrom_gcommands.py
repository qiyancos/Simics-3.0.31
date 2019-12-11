from cli import *
import re

def new_host_cdrom_cmd(device, name):
    if not name:
        # Make up a name by taking the first alphanumerical part from the
        # basename of the file
        m = re.search(r'([a-zA-Z][a-zA-Z0-9_-]*)[^/]*$', device)
        if m:
            name = m.group(1)
            seq = -1
        if not name:
            name = "iso0"
        try:
            while 1:
                SIM_get_object(name)
                seq += 1
                name = "iso%d" % seq
        except:
            pass

    # strip bad characters from object name
    name = re.sub(r'[^a-zA-Z0-9_-]', '-', name)
    try:
        obj = SIM_new_object("host-cdrom", name)
    except:
        pr("Failed creating object '%s'\n" % name)
        return
    try:
        obj.file = device
        pr("CD-ROM '%s' created\n" % obj.name)
        return (obj.name, )
    except Exception, msg:
        pr("Failed using device '%s' as media: %s\n" % (name, msg))
        SIM_delete_object(obj)

new_command("new-host-cdrom", new_host_cdrom_cmd,
            [arg(filename_t(exist = 1, simpath = 1), "device"),
             arg(str_t, "name", "?", "")],
            type = ["CD-ROM", "Disk"],
            short = "create new host-cdrom object",
            doc = """
Create a new host-cdrom object from <i>device</i> (which should be a valid
CD-ROM device, e.g. <tt>/dev/cdrom</tt> on linux.  If <i>name</i> is not given,
an object name is derived from the device name. This object can then be inserted
into a simulated CD-ROM device using the <b>&lt;device&gt;.insert</b> command.""", filename="/mp/simics-3.0/src/extensions/host-cdrom/gcommands.py", linenumber="37")

