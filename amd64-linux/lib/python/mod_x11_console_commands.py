from cli import *
from gfx_console_common import *


#
# ------------------ save-break-xy -------------------
#

def save_break_xy_cmd(obj, fname, left, top, right, bottom, comment):
    SIM_set_attribute(obj, "save_break", [fname, left, top, right, bottom, comment])

new_command("save-break-xy", save_break_xy_cmd,
            [arg(filename_t(), "filename"),
             arg(int_t, "left"),
             arg(int_t, "top"),
             arg(int_t, "right"),
             arg(int_t, "bottom"),
             arg(str_t, "comment", "?", "No comment")],
            alias = "",
            type  = "gfx-console commands",
            short = "specify and save a graphical breakpoint",
	    namespace = "gfx-console",
            doc = """
Lets the user select a rectangular area inside the graphics console by
specifying the top left corner (<arg>left</arg>, <arg>top</arg>) and the bottom
right corner (<arg>right</arg>, <arg>bottom</arg>). The selected area will be
saved as a binary graphical breakpoint file. An optional comment may be added
that will be put in the beginning of the file.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="12")

#
# --------------------- break -----------------------
#

def break_cmd(obj, fname):
    id = SIM_get_attribute_idx(obj, "break", fname)
    print "Created graphical breakpoint", id

new_command("break", break_cmd,
            [arg(filename_t(exist = 1, simpath = 1), "filename")],
            alias = "",
            type  = "gfx-console commands",
            short = "break on a graphics event specified by filename",
	    namespace = "gfx-console",
            doc = """
Activates a previously saved breakpoint specified by <i>filename</i>
and returns a breakpoint id. When a graphical breakpoint is reached it
is immediately deleted and a hap with id "<b>Gfx_Break_String</b>" is
triggered. If no callbacks for this hap were registered Simics halts
execution and returns to the command prompt.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="39")

#
# --------------------- delete -----------------------
#

def delete_cmd(obj, id):
    SIM_set_attribute(obj, "delete", id)

new_command("delete", delete_cmd,
            [arg(int_t, "id")],
            alias = "",
            type  = "gfx-console commands",
            short = "delete breakpoint",
	    namespace = "gfx-console",
            doc = """Delete breakpoint given by <i>id</i>""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="60")


#
# -------------------- poll-rate --------------------
#

def poll_rate_cmd(obj, delay):
    if delay < 1:
	old = SIM_get_attribute(obj, "poll-rate")
	print "[%s] Current poll-rate: %d Hz"  % (obj.name, old)
	return
    SIM_set_attribute(obj, "poll-rate", delay)
    if not SIM_get_quiet():
        print "[%s] Setting poll-rate: %d Hz" % (obj.name, delay)

new_command("poll-rate", poll_rate_cmd,
            [arg(int_t, "rate", "?", 0)],
            alias = "",
            type  = "gfx-console commands",
            short = "set poll rate",
	    namespace = "gfx-console",
            doc = """
Set the rate for inputs polling and display updates.
The rate for updates is the only argument, and specified
in Hz (simulated time). Default is 1000, but this may vary depending on 
the config file used. When called with no arguments, the
current polling frequency is reported.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="82")
#
# -------------------- refresh --------------------
#

def refresh_cmd(obj):
    SIM_set_attribute(obj, "refresh", 1)

new_command("refresh", refresh_cmd,
            [],
            alias = "",
            type  = "gfx-console commands",
            short = "refresh console",
	    namespace = "gfx-console",
            doc = """
Redraws all changes to the graphics console
The console display is normally only updated at intervals
specified by the <i>poll-rate</i> command. This command
causes the (full) display to be redrawn.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="102")


#
# -------------------- disable-input --------------------
#

def disable_input_cmd(obj):
    try:
	SIM_set_attribute(obj, "input-enable", 0)
	if not SIM_get_quiet():
            print "[%s] Input disabled" % obj.name
    except Exception, msg:
	print "[%s] Cannot disable input" % obj.name

new_command("disable-input", disable_input_cmd,
            [], # <b>disable-input</b>
            alias = "",
            type  = "gfx-console commands",
            short = "ignore console input",
	    namespace = "gfx-console",
            see_also = ['<gfx-console>.enable-input'],
            doc = """
Ignore all inputs received from the console.
Use this command to avoid sending input to the
simulated machine if determinism is desired.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="128")

#
# -------------------- enable-input --------------------
#

def enable_input_cmd(obj):
    SIM_set_attribute(obj, "input-enable", 1)
    if not SIM_get_quiet():
        print "[%s] Input enabled" % obj.name

new_command("enable-input", enable_input_cmd,
            [],
            alias = "",
            type  = "gfx-console commands",
            short = "enable console input",
	    namespace = "gfx-console",
            see_also = ['<gfx-console>.disable-input'],
            doc = """
Enable inputs from the console. New consoles will have
input enabled.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="150")


#
# -------------------- auto-release --------------------
#

def auto_release_cmd(obj, state):
    if state is None:
        print "auto-release is %s" % iff(SIM_get_attribute(obj, "auto-release"), "on", "off");
    else:
        SIM_set_attribute(obj, "auto-release", state)

new_command("auto-release", auto_release_cmd,
            [arg(int_t, "state", "?", None)],
            alias = "",
            type  = "gfx-console commands",
            short = "get/set auto-release flag",
	    namespace = "gfx-console",
            doc = """
Get or set the auto-release attribute on the gfx-console.
If set, automatic release events will be sent for any keys
still pressed when the window focus is lost.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="173")


def close_cmd(obj):
    SIM_set_attribute(obj, "try-open", 0)
    
new_command("close", close_cmd,
            [],
            alias = "",
            type  = "gfx-console commands",
            short = "close console window",
	    namespace = "gfx-console",
            see_also = ['<gfx-console>.open'],
            doc = """
Close the console window.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="189")


def open_cmd(obj):
    SIM_set_attribute(obj, "try-open", 1)
    objs = SIM_all_objects()
    try:
        for a in objs:
            if instance_of(a, "VGA"):
                if SIM_get_attribute(a, "console") == obj.name:
                    run("%s.redraw" % a.name, "")
    except:
        pass

new_command("open", open_cmd,
            [],
            alias = "",
            type  = "gfx-console commands",
            short = "open console window",
	    namespace = "gfx-console",
            see_also = ['<gfx-console>.close'],
            doc = """
Open the console window.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="212")

#
# -------------------- grab-setup --------------------
#

def button_expander(string, obj):
    return get_completions(string, ["left", "right", "middle"])
    
def mod_expander(string, obj):
    return get_completions(string, ["control", "alt", "shift", "none"])

def grab_setup_cmd(obj, button, modifier):
    if button == "inquiry":
        mod = obj.grab_modifier
        if mod == "none":
            mod_str = ""
        else:
            mod_str = 'left "%s" key + ' % mod
        print 'Input is currently grabbed with: %s%s mouse button.' % (
            mod_str, obj.grab_button)
        return
    try:
        obj.grab_button = button
    except Exception, msg:
        print "Failed setting selected grab button (%s)" % msg
        SIM_command_has_problem()
        return
    try:
        obj.grab_modifier = modifier
    except Exception, msg:
        print "Failed setting selected grab modifier (%s)" % msg
        SIM_command_has_problem()
        return
    if SIM_get_quiet() == 0:
        print "Setting grab/ungrab to: %s mouse button, modifier: %s" % (button, modifier)
        
new_command("grab-setup", grab_setup_cmd,
            [arg(str_t, "button", "?", "inquiry", expander = button_expander),
             arg(str_t, "modifier", "?", "none", expander = mod_expander)],
            alias = "",
            type  = "gfx-console commands",
            short = "set grab button and modifier",
	    namespace = "gfx-console",
            doc = """
The grab button specifies which mouse button that is used to grab
and ungrab input for the console. A keyboard modifier can also be
specified that must be pressed for grabbing to occur. Valid buttons
are left, middle and right, while valid modifiers are alt, control,
shift and none. Only the left side modifier are currently used.
When called with no arguments, the currently selected button and
modifier will be printed.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="258")

#
# -------------------- input --------------------
#

def insert_cmd(obj, string, e):
    if e:
        # Input emacs-style key combination
        release = []
        for key in string.split('-'):
            for stroke in emacs_to_keystrokes(key):
                if stroke[0] == 1:
                        release.append(stroke)
                else:
                        obj.input_key_event = [stroke[0], stroke[1]]
        for stroke in release:
            obj.input_key_event = [stroke[0], stroke[1]]
    else:
        # Input the raw string
        try:
	    for ch, stroke in string_to_keystrokes(string):
                obj.input_key_event = [stroke[0], stroke[1]]
        except Exception, msg:
            print "[%s] Failed writing string" % obj.name
            print msg

new_command("input", insert_cmd,
            [arg(str_t, "string"),
             arg(flag_t, "-e")],
            alias = "",
            type  = "gfx-console commands",
            short = "send string to a console",
            namespace = "gfx-console",
            doc = """          
Input string on console.

The -e switch enables emacs-style keystrokes. The following characters are
accepted: 'C' (Control), 'A' (Alt), 'Del', 'Up', 'Down', 'Left', 'Right',
'Esc', 'F1' to 'F12' and 'Enter'. They can be combined using the '-'
character. For example "C-a" will input Control and a pressed
together. "C-A-Del" will produce the famous Control-Alt-Del sequence.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="300")

def save_bmp_cmd(obj, fname):
    try:
        obj.save_bmp = fname
	print "[%s]: BMP file saved as \'%s\'" % (obj.name, fname)
    except Exception, msg:
	print "[%s]: Error saving BMP file: %s" % (obj.name, msg)

new_command("save-bmp", save_bmp_cmd,
            [arg(filename_t(), "filename")],
            alias = "",
            type  = "gfx-console commands",
            short = "save BMP image",
	    namespace = "gfx-console",
            doc = """
This command saves the current console window contents to an image
file in BMP format.""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="324")

#
# -------------------- fullscreen-on ----------------
#

def fullscreen_on_cmd(obj):
    obj.fullscreen = 1
    print "Fullscreen mode enabled"

if get_last_loaded_module() == "sdl-console":
    new_command("fullscreen-on", fullscreen_on_cmd,
                alias = "",
                type  = "gfx-console commands",
                short = "enable fullscreen mode",
                namespace = "gfx-console",
                see_also = ['<gfx-console>.fullscreen-off'],
                doc = """
Enable fullscreen mode. The console will try to reopen itself
in fullscreen mode the next time input is grabbed. When input
grabbing is later disabled, the console will go back to a normal
window.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="343")

#
# -------------------- toggle fullscreen ----------------
#

def fullscreen_off_cmd(obj):
    obj.fullscreen = 0
    print "Fullscreen mode disabled"

if get_last_loaded_module() == "sdl-console":
    new_command("fullscreen-off", fullscreen_off_cmd,
                alias = "",
                type  = "gfx-console commands",
                short = "disable fullscreen mode",
                namespace = "gfx-console",
                see_also = ['<gfx-console>.fullscreen-on'],
                doc = """
Disable fullscreen mode.
""", filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="365")

#
# ---------------- switch-to-text-console -------------
#

def switch_to_other_class(con, classname, attribs):
    name = con.name
    try:
        kbd_dev = con.keyboard
    except:
        print "No keyboard connected to console '%s'" % con.name
        SIM_command_has_problem()
        return
    video_dev = con.video
    if not video_dev:
        print "No video connected to console '%s'" % con.name
        SIM_command_has_problem()
        return

    newname = "new_" + name
    try:
        obj = SIM_create_object(classname, newname,
                                attribs + [['device', kbd_dev]])
    except:
        print "Failed creating %s '%s'" % (classname, newname)
        SIM_command_has_problem()
        return

    video_dev.console = obj
    kbd_dev.console = obj
    try:
        SIM_delete_object(con)
    except:
        print "Failed removing existing console '%s'" % con.name
        SIM_command_has_problem()
        return
    try:
        VT_rename_object(obj, name)
    except SimExc_General, msg:
        # this shouldn't happen - we know the name is unused
        print "Error renaming %s to %s: %s" % (newname, name, msg)
        return

    if not SIM_get_quiet():
        print ("Keyboard '%s' and video '%s' now connected to %s '%s'."
               % (kbd_dev.name, video_dev.name, classname, obj.name))

    eval_cli_line("%s.redraw" % video_dev.name)

def switch_to_text_cmd(con):
    switch_to_other_class(con, "text-console",
                          [['queue', SIM_current_processor()],
                           ['vt_height', 25],
                           ['title', 'Console ' + con.name]])

new_command("switch-to-text-console", switch_to_text_cmd,
            [],
            alias = "",
            type  = "gfx-console commands",
            short = "replace graphics console with text console",
            namespace = "gfx-console",
            doc = """
            Replace the graphics with a text console.
            """, filename="/mp/simics-3.0/src/extensions/graphics-console/commands.py", linenumber="429")
