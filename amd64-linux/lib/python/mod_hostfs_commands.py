from cli import *
import sim_commands

def root_cmd(obj, root):
    if root:
        obj.host_root = root
    else:
        print obj.host_root

new_command("root", root_cmd,
            [arg(filename_t(dirs=1, exist=1), "dir", "?", "")],
            namespace = "hostfs",
            type = "hostfs commands",
            short = "set or show the hostfs root directory",
            doc = """
Set the host directory that is visible to the simulated machine to
<arg>dir</arg>. If no directory is specified, the current root directory
is shown. Changes may not take effect until next the file system is
mounted.""", filename="/mp/simics-3.0/src/devices/hostfs/commands.py", linenumber="10")

def get_info(obj):
    return [(None,
             [("Host Root", obj.host_root)])]

sim_commands.new_info_command('hostfs', get_info)

def get_status(obj):
    if obj.version == (1L << 64) - 1:
        mount_stat = "no"
    else:
        mount_stat = "yes"
    return [(None,
             [("Mounted", mount_stat)])]

sim_commands.new_status_command('hostfs', get_status)
