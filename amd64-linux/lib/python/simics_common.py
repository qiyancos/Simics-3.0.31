#
# File with Python code for simics-common. Run early at startup.
#

import os, re, sys
from cli import *
import sim_core, __main__

def enable_hindsight(arg, obj):
    if not SIM_next_queue(None):
        return
    SIM_hap_delete_callback("Core_Configuration_Loaded", enable_hindsight, 0)
    if conf.prefs.enable_hindsight and VT_hindsight_available():
        eval_cli_line('set-bookmark start')

SIM_hap_add_callback("Core_Configuration_Loaded", enable_hindsight, 0)

class pre_conf_object(object):
    def __init__(self, object_name, class_name):
        self.__object_name__ = object_name
        self.__class_name__ = class_name

    def __setattr__(self, name, val):
        # TODO: check that attribute exists
        if name == "name":
            self.__object_name__ = val
        else:
            object.__setattr__(self, name, val)

    def __getattribute__(self, name):
        if name == "name":
            return self.__object_name__
        elif name == "classname":
            return self.__class_name__
        elif name == "configured":
            return 0
        else:
            return object.__getattribute__(self, name)

sim_core.pre_conf_object = pre_conf_object
__main__.pre_conf_object = pre_conf_object


### global preferences


main_version = re.match('.*?([0-9]*\.[0-9]*).*', SIM_version()).group(1)

if 'win' in conf.sim.host_os:
    import _winreg
    keyname = "Software\\Virtutech\\Simics-%s" % main_version

    try:
        simics_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, keyname)
    except:
        simics_key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, keyname)

    def write_global_prefs(name, value):
        _winreg.SetValue(simics_key, name, _winreg.REG_SZ, str(value))

    def read_global_prefs(name):
        try:
            return _winreg.QueryValue(simics_key, name)
        except:
            return None

else:
    glob_file = os.path.expanduser('~') + '/.simics-%s-globals' % main_version
    try:
        glob_lines = open(glob_file).readlines()
    except:
        glob_lines = []
    globals = {}
    for l in glob_lines:
        try:
            pair = l.strip().split('=')
            globals[pair[0]] = pair[1]
        except:
            pass

    def _write_globals():
        try:
            file = open(glob_file, "w")
        except:
            return
        for p in globals.items():
            file.write('%s=%s\n' % (p[0], p[1]))
        file.close()

    def write_global_prefs(name, value):
        globals[name] = str(value)
        _write_globals()

    def read_global_prefs(name):
        return globals.get(name, None)

# global preferences, common code

def workspace_change(arg, obj):
    if conf.sim.gui_mode != "no":
        # TODO: always in Simics 3.2?
        write_global_prefs('simics-workspace', conf.sim.workspace)

if conf.sim.gui_mode != "no":
    # TODO: always in Simics 3.2
    workspace = read_global_prefs('simics-workspace')
else:
    workspace = None
if workspace and not conf.sim.workspace:
    conf.sim.workspace = workspace
elif conf.sim.workspace and workspace != conf.sim.workspace:
    workspace_change(None, None)

SIM_hap_add_callback("Core_Workspace_Changed", workspace_change, None)


### Ask for SLA accept


def check_sla_accept():
    # called for licenses that require run-time accept of the SLA
    license_ack = read_global_prefs('sla-accepted')
    if license_ack:
        conf.sim.gui_ready = 2
        return
    elif conf.sim.batch_mode:
        print "Simics SLA not accepted. Exiting since in batch-mode."
        conf.sim.gui_ready = 1
        return 
    filename = os.path.join(conf.sim.simics_base, 'doc',
                            'NON_COMMERCIAL_SLA')
    try:
        license = open(filename).readlines()
    except:
        print "Failed to access the license file. Corrupt installation?\n"
        conf.sim.gui_ready = 1
        return
    if conf.sim.gui_mode != 'no':
        try:
            import winsome.win_main
            winsome.win_main.win_sla_accept(license)
            return
        except:
            # use cli version if gui failed
            pass
    count = 0
    print
    for line in range(len(license)):
        print license[line],
        if (line + 1) % (terminal_height() - 4) == 0:
            print
            print "    Press return to continue..."
            sys.stdin.readline()
    print '\nTo print the license, use the file:\n%s\n' % filename
    while 1:
        print "Accept license? (yes/no)"
        accept = sys.stdin.readline().strip().lower()
        if accept == 'no':
            conf.sim.gui_ready = 1
            return
        elif accept == 'yes':
            write_global_prefs('sla-accepted', 'yes')
            conf.sim.gui_ready = 2
            return
