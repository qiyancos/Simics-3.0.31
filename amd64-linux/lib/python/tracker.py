# Common stuff for process trackers.

from cli import *

def str2cpu(str):
    try:
        cpu = SIM_get_object(str)
    except:
        print "There is no object named '%s'." % str
        return None
    if SIM_object_is_processor(cpu):
        return cpu
    print "%d is not a processor." % str
    return None

def add_processor_cmd(tracker, cpu):
    cpu = str2cpu(cpu)
    if cpu != None:
        tracker.iface.tracker.add_processor(tracker, cpu)

new_command("add-processor", add_processor_cmd,
            [arg(str_t, "processor", expander = object_expander("processor"))],
            namespace = "tracker",
            type = "Debugging",
            see_also = ["<tracker>.remove-processor"],
            short = "track processes on this processor",
            doc = """

Add a processor to the set of processors that the process tracker
watches.""", filename="/mp/simics-3.0/src/extensions/apps-python/tracker.py", linenumber="21")

def remove_processor_cmd(tracker, cpu):
    cpu = str2cpu(cpu)
    if cpu != None:
        tracker.iface.tracker.remove_processor(tracker, cpu)

new_command("remove-processor", add_processor_cmd,
            [arg(str_t, "processor", expander = object_expander("processor"))],
            namespace = "tracker",
            type = "Debugging",
            see_also = ["<tracker>.add-processor"],
            short = "do not track processes on this processor",
            doc = """

Remove a processor from the set of processors that the process tracker
watches.""", filename="/mp/simics-3.0/src/extensions/apps-python/tracker.py", linenumber="37")

def activate_cmd(tracker):
    tracker.iface.tracker.activate(tracker)

new_command("activate", activate_cmd, [],
            namespace = "tracker",
            type = "Debugging",
            see_also = ["<tracker>.deactivate"],
            short = "activate tracker",
            doc = """

Activate a tracker. For performance reasons, trackers are inactive by
default and need to be activated before they start tracking processes.
If the tracker is used by another object, such as a context switcher,
it is the responsibility of that object to activate the tracker; but
if you want to use it directly, you must activate it yourself.""", filename="/mp/simics-3.0/src/extensions/apps-python/tracker.py", linenumber="51")

def deactivate_cmd(tracker):
    tracker.iface.tracker.deactivate(tracker)

new_command("deactivate", deactivate_cmd, [],
            namespace = "tracker",
            type = "Debugging",
            see_also = ["<tracker>.activate"],
            short = "deactivate tracker",
            doc = """

Deactivate a tracker. This command undoes the effects of one
<cmd>activate</cmd> command; when all of them are undone, the tracker
will stop tracking processes (and consuming resources).""", filename="/mp/simics-3.0/src/extensions/apps-python/tracker.py", linenumber="67")

#
# -------------------- process tracker list --------------------
#

trackers = {}

def register_tracker(classname):
    trackers[classname] = None

def get_tracker_list(arg, obj, idx):
    return list(trackers.keys())

SIM_register_typed_attribute(
    "sim", "tracker_list", get_tracker_list, None, None, None,
    Sim_Attr_Pseudo | Sim_Attr_Internal, "[s*]", None,
    "List of registered trackers.")
