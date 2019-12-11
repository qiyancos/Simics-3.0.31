from cli import *
from sim_commands import *

#
# -------------------- key-down, key-up --------------------
#

def key_down_cmd(obj, key_code):
    SIM_set_attribute_idx(obj, "key-event", key_code, 0)


def key_up_cmd(obj, key_code):
    SIM_set_attribute_idx(obj, "key-event", key_code, 1)

new_command("key-down", key_down_cmd,
            [arg(int_t, "key-code")], # <b>key-down</b> <i>keycode</i>
            alias = "",
            type  = "i8042 commands",
            short = "send key event",
	    namespace = "i8042",
            doc = """
Send a key press to the keyboard controller.
The argument is the internal Simics keycode.
""", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="15")

new_command("key-up", key_up_cmd,
            [arg(int_t, "key-code")], # <b>key-up</b> <i>keycode</i>
            alias = "",
            type  = "i8042 commands",
            short = "send key event",
	    namespace = "i8042",
            doc_with = "<i8042>.key-down", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="26")

#
# -------------------- left-button, right-button --------------------
#

def right_button_cmd(obj, dir):
    if dir == "up":
        SIM_set_attribute_idx(obj, "button-event", 1, 1)
    elif dir == "down":
        SIM_set_attribute_idx(obj, "button-event", 1, 0)
    else:
	print "Unknown button direction: %s" % dir


def left_button_cmd(obj, dir):
    if dir == "up":
        SIM_set_attribute_idx(obj, "button-event", 0, 1)
    elif dir == "down":
        SIM_set_attribute_idx(obj, "button-event", 0, 0)
    else:
	print "Unknown button direction: %s" % dir

def middle_button_cmd(obj, dir):
    if dir == "up":
        SIM_set_attribute_idx(obj, "button-event", 2, 1)
    elif dir == "down":
        SIM_set_attribute_idx(obj, "button-event", 2, 0)
    else:
	print "Unknown button direction: %s" % dir

def i8042_up_down_expander(string):
	return get_completions(string, ("up", "down"))

new_command("right-button", right_button_cmd,
            [arg(str_t, "direction", expander = i8042_up_down_expander)], # <b>right-button</b> up|down
            alias = "",
            type  = "i8042 commands",
            short = "set button state",
	    namespace = "i8042",
            doc = """
Set the state of the left or right mouse button.
Valid arguments are "up" and "down".""", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="66")

new_command("left-button", left_button_cmd,
            [arg(str_t, "direction", expander = i8042_up_down_expander)], # <b>left-button</b> up|down
            alias = "",
            type  = "i8042 commands",
            short = "set button state",
	    namespace = "i8042",
            doc_with = "<i8042>.right-button", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="76")

new_command("middle-button", middle_button_cmd,
            [arg(str_t, "direction", expander = i8042_up_down_expander)], # <b>middle-button</b> up|down
            alias = "",
            type  = "i8042 commands",
            short = "set button state",
	    namespace = "i8042",
            doc_with = "<i8042>.right-button", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="84")

#
# -------------------- mouse-up, mouse-down, mouse-left, mouse-right --------------------
#

def mouse_up_cmd(obj, delta):
    SIM_set_attribute_idx(obj, "mouse-event", 0, delta)

def mouse_down_cmd(obj, delta):
    SIM_set_attribute_idx(obj, "mouse-event", 1, delta)

def mouse_left_cmd(obj, delta):
    SIM_set_attribute_idx(obj, "mouse-event", 2, delta)

def mouse_right_cmd(obj, delta):
    SIM_set_attribute_idx(obj, "mouse-event", 3, delta)

new_command("mouse-up", mouse_up_cmd,
            [arg(int_t, "millimeters")],
            alias = "",
            type  = "i8042 commands",
            short = "move mouse",
	    namespace = "i8042",
            doc = """
Move the mouse up/down/left/right a specified number of millimeters.<br/>
""", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="108")

new_command("mouse-down", mouse_down_cmd,
            [arg(int_t, "millimeters")],
            alias = "",
            type  = "i8042 commands",
            short = "move mouse",
	    namespace = "i8042",
            doc_with = "<i8042>.mouse-up", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="118")

new_command("mouse-right", mouse_right_cmd,
            [arg(int_t, "millimeters")],
            alias = "",
            type  = "i8042 commands",
            short = "move mouse",
	    namespace = "i8042",
            doc_with = "<i8042>.mouse-up", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="126")

new_command("mouse-left", mouse_left_cmd,
            [arg(int_t, "millimeters")],
            alias = "",
            type  = "i8042 commands",
            short = "move mouse",
	    namespace = "i8042",
            doc_with = "<i8042>.mouse-up", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="134")


# TODO: Extend to a generic key-pressing funktion.
# Not tested yet!
def ctrl_alt_del_cmd(obj):
    print "Sending Ctrl-Alt-Del to %s" % obj.name
    obj.key_event[69] = 0  # SK_CTRL_L down
    obj.key_event[73] = 0  # SK_ALT_L down
    obj.key_event[83] = 0  # SK_GR_DELETE down
    obj.key_event[69] = 1  # SK_CTRL_L up
    obj.key_event[73] = 1  # SK_ALT_L up
    obj.key_event[83] = 1  # SK_GR_DELETE up
    print "Done."

new_command("ctrl-alt-del", ctrl_alt_del_cmd,
            [],
#            alias = "cad",
            type = "i8042 commands",
            short = "send ctrl-alt-del to console",
            namespace = "i8042",
            doc = """
Sends a Ctrl-Alt-Del command to the console. This is useful primarily on
a Windows-hosted Simics to avoid having Ctrl-Alt-Del catched by the host OS.
""", filename="/mp/simics-3.0/src/devices/8042/commands.py", linenumber="155")

#
# ------------------------ info -----------------------
#

def get_info(obj):
    return [ (None,
              [ ("Connected Console", obj.console) ]),
             ("Interrupts",
              [ ("Interrupt Device", obj.irq_dev.name),
                ("Keyboard Interrupt", obj.kbd_irq_level),
                ("Mouse Interrupt", obj.mouse_irq_level) ]),
             ("Mouse",
              [ ("Scaling", iff(obj.mou_two_to_one, 2, 1)),
                ("Resolution", (1 << obj.mou_resolution)),
                ("Sample Rate", obj.mou_sample_rate) ]) ]

new_info_command('i8042', get_info)

def get_status(obj):
    if obj.key_buf_num == 0:
        kbuffer = "Empty"
    else:
        key_buffer = obj.key_buffer
        kbuffer = ""
        for i in range(obj.key_buf_num):
            kbuffer += "0x%0x " % key_buffer[ (obj.key_first + i) % len(key_buffer)]

    if obj.mou_buf_num == 0:
        mbuffer = "Empty"
    else:
        mou_buffer = obj.mou_buffer
        mbuffer = ""
        for i in range(obj.mou_buf_num):
            mbuffer += "0x%0x " % mou_buffer[ (obj.mou_first + i) % len(mou_buffer)]

    return [ ("Controller",
              [ ("Output Buffer", iff(obj.ofull, "0x%x" % obj.obuffer, "Empty")),
                ("Mouse Buffer", iff(obj.mfull, "Full", "Empty")),
                ("Last Access", iff(obj.command_last, "Command", "Data")),
                ("System Flag", obj.selftest_ok),
                ("Scan Convert", iff(obj.scan_convert, "On", "Off")),
                ("Keyboard", iff(obj.kbd_disabled, "Dis", "En")),
                ("Keyboard Irq", iff(obj.kbd_irq_en, "En", "Dis")),
                ("Mouse", iff(obj.mouse_disabled, "Dis", "En")),
                ("Mouse Irq", iff(obj.mouse_irq_en, "En", "Dis")) ]),
             ("Keyboard",
              [ ("State", iff(obj.key_enabled, "Enabled", "Disabled")),
                ("Caps Lock", iff(obj.key_caps_lock, "On", "Off")),
                ("Num Lock", iff(obj.key_num_lock, "On", "Off")),
                ("Scroll Lock", iff(obj.key_scroll_lock, "On", "Off")),
                ("Buffer", kbuffer) ]),
             ("Mouse",
              [ ("State", iff(obj.mou_enabled, "Enabled", "Disabled")),
                ("Left Button", iff(obj.mou_left_button, "Down", "Up")),
                ("Right Button", iff(obj.mou_right_button, "Down", "Up")),
                ("Buffer", mbuffer) ]) ]

new_status_command('i8042', get_status)
