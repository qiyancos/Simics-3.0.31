from cli import *
import sim_commands

def get_info(obj):
    return [(None,
             [])]

sim_commands.new_info_command('v9-sol9-idle-opt', get_info)

def get_status(obj):
    return [(None,
             [("Enabled", iff(obj.enabled, "yes", "no")),
              ("Auto-detect", iff(obj.auto_detect, "yes", "no")),
              ("Multi-pro", iff(obj.multi_pro, "yes", "no")),
              ("Memory space", obj.memory_space),
              ("Address", "0x%x" % obj.address),
              ("Idle speed", obj.idle_speed),
              ("Busy speed", obj.busy_speed)])]

sim_commands.new_status_command('v9-sol9-idle-opt', get_status)

def v9_sol9_idle_opt_cmd(memory_space, multi_pro):
    i = 0
    done = 0
    while not done:
        try:
            obj_name = "idle-opt-%d" % i
            SIM_get_object(obj_name) != None
            i = i + 1
        except:
            done = 1
            obj = SIM_create_object("v9-sol9-idle-opt", obj_name, [["memory_space", memory_space], ["multi_pro", multi_pro]])
    SIM_log_message(obj, 1, 0, Sim_Log_Info, "Created.")

new_command("v9-sol9-idle-opt", v9_sol9_idle_opt_cmd,
            [arg(obj_t("memory-space", "memory-space"), "memory-space"),
             arg(flag_t, "-multi-pro")],
            type  = ["Speed"],
            short = "enable idle loop optimization",
            doc = """
            Adds idle loop optimization to a simulated SPARC machine running
            Solaris 9. The <arg>memory_space</arg> argument must specify the
            physical memory space of the simulated machine. The
            <arg>-multi-pro</arg> flag must be specified for simulated
            multi-pro machines.
            """, filename="/mp/simics-3.0/src/extensions/v9-sol9-idle-opt/commands.py", linenumber="35")
