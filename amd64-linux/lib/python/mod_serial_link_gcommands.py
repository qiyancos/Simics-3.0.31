from cli import *

#
# -------- new-serial-link --------
#

def new_serial_link(name, throttle):
    if SIM_next_queue(None) == None:
        print "This command requires an existing time queue (processor)."
        SIM_command_has_problem()
        return
    if not name:
        name = get_available_object_name("serlink")

    link = SIM_create_object("serial-link", name, [["throttle", throttle]])
    if SIM_is_interactive():
        print "Created serial-link", name
    return link

new_command("new-serial-link", new_serial_link,
            [arg(str_t, "name", "?", None),
             arg(int_t, "throttle", "?", 115200)],
            type = ["Serial"],
            short = "create a new serial link",
            see_also = ['new-std-serial-link'],
            doc = """
Creates a new <class>serial-link</class> object that can be used to connect Serial devices.
As of Simics 3.0 this command is deprecated. The <cmd>new-std-serial-link</cmd>
command should be used in component based configurations.
""", filename="/mp/simics-3.0/src/devices/serial-link/gcommands.py", linenumber="20")
