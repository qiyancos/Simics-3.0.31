import os

from cli import *
import sim_commands
import sim
from components import \
     instantiate_cmd, get_component, connect_cmd, component_basename, \
     disconnect_cmd

device_name = get_last_loaded_module()
if device_name == "xterm-console" or device_name == "win32-text-console":
    device_name = "text-console"
if device_name == "server-console-c":
    device_name = "server-console"

#
# -------------------- input --------------------
#

def insert_cmd(obj, str, delay):
    try:
        if delay == 0.0:
            obj.input = str
        else:
            obj.input_delayed = [ str, delay ]
    except Exception, msg:
	print "[%s] Failed writing string" % obj.name
	print msg

new_command("input", insert_cmd,
            [arg(str_t, "string"), arg(float_t, "delay", spec="?", default=0.01)],
            alias = "",
            type  = device_name + " commands",
            short = "send string to a console",
	    namespace = device_name,
            doc = """
Send string to a text console. The text is delayed by default, to wait
for the simulated software to be ready after a previous break on string.
To input the string immediately, specify delay = 0""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="30")

#
# -------------------- input-file --------------------
#

def insert_file_cmd(obj, file_name, binary):
    try:
        size = os.stat(file_name).st_size
    except OSError, msg:
        print "[%s] Error accessing file \'%s\': %s" % (obj.name, file_name, msg)
        raise CliError
    try:
        input_file = file(file_name, "rb")
        data = input_file.read(size)
        # Replace Windows line endings with Unix line endings to avoid getting
        # the effect of pressing enter twice after each line.
        if not binary:
            data = data.replace("\r\n", "\n")
        obj.input = [tuple(map(ord, data)), binary]
        input_file.close()
    except IOError, msg:
        print "[%s] Error accessing file \'%s\': %s" % (obj.name, file_name, msg)
        raise CliError

new_command("input-file", insert_file_cmd,
            args  = [arg(filename_t(exist = 1, simpath = 0), "file"),
                     arg(flag_t, "-binary")],
            alias = "",
            type  = device_name + " commands",
            short = "input a file into a console",
	    namespace = device_name,
            doc = """
Inputs the contents of <arg>file</arg> into the text console.  If the <arg>-binary</arg>
flag is specified, the file is treated as a binary file.""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="64")

#
# -------------------- break --------------------
#

def break_cmd(obj, string):
    try:
	obj.break_string = string
    except Exception, msg:
	print "[%s] Failed setting break string" % obj.name
        obj.unbreak_string = string
	raise CliError, msg

new_command("break", break_cmd,
            [arg(str_t, "string")],
            alias = "",
            type  = device_name + " commands",
            short = "set a string to break on",
	    namespace = device_name,
            see_also = ['<text-console>.unbreak',
                        '<text-console>.list-break-strings'],
            doc = """
Set a string to break on for the console. The simulation will stop
when this string is written on the console. If text output is intermixed
with control sequences for colors/positioning, the break command may
fail breaking on the string.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="87")

#
# -------------------- unbreak --------------------
#

def unbreak_cmd(obj, string):
    try:
	obj.unbreak_string = string
    except Exception, msg:
	print "[%s] Failed removing break string" % obj.name
	print msg

new_command("unbreak", unbreak_cmd,
            [arg(str_t, "string")],
            alias = "",
            type  = device_name + " commands",
            short = "stop breaking on string",
	    namespace = device_name,
            see_also= ['<text-console>.break',
                       '<text-console>.list-break-strings'],
            doc = """
Stop breaking on specified string.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="113")

#
# -------------------- unbreak-id --------------------
#

def unbreak_id_cmd(obj, id):
    try:
	obj.unbreak_id = id
    except Exception, msg:
	print "[%s] Failed removing break id" % obj.name
	print msg

new_command("unbreak-id", unbreak_id_cmd,
            [arg(int_t, "id")],
            alias = "",
            type  = device_name + " commands",
            short = "remove a breakpoint",
	    namespace = device_name,
            see_also = ['<text-console>.break',
                        '<text-console>.list-break-strings'],
            doc = """
Remove the breakpoint with specified id.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="136")

#
# -------------------- list-break-strings --------------------
#

def list_break_cmd(obj):
    try:
	list = obj.break_string
        print "Will break on the following strings:"
        for i in list:
            bp_str = i[0]
            print '"%s", id %s' % (bp_str, " ".join(map(str, i[1])))
    except Exception, msg:
	print "[%s] Failed reading break strings" % obj.name
	print msg

new_command("list-break-strings", list_break_cmd,
            [],
            alias = "",
            type  = device_name + " commands",
            short = "list all strings the console will break on",
	    namespace = device_name,
            see_also = ['<text-console>.break',
                        '<text-console>.unbreak'],
            doc = """
Print a listing of all strings that the console will break on.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="163")

#
# -------------------- read-only --------------------
#

def read_only_cmd(obj):
    try:
	old = obj.read_only
        if (old == 0):
            obj.read_only =  1
            print "Changing to read-only mode"
        else:
            obj.read_only = 0
            print "Changing to read/write mode"
    except Exception, msg:
	print "[%s] Failed changing read-only mode" % obj.name
	print msg

if device_name == "text-console":
    new_command("read-only", read_only_cmd,
                [],
                alias = "",
                type  = device_name + " commands",
                short = "toggle read-only mode",
                namespace = device_name,
                see_also = ['<text-console>.input'],
                doc = """
                Toggle the read-only mode in the console. Console input is only accepted if the
                console is in read/write mode. If the console is in read-only mode, all input
                is discarded, except input generated by the &lt;text-console&gt;.insert command.
                """, filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="193")


#
# -------------------- quiet --------------------
#

def quiet_cmd(obj):
    try:
	old = obj.quiet
        if (old == 0):
            obj.quiet = 1
            print "Disabling text console output redirection."
        else:
            obj.quiet = 0
            print "Enabling text console output redirection."
    except Exception, msg:
	print "[%s] Failed toggle console redirection" % obj.name
	print msg

def enable_quiet_cmd(obj):
    if obj.quiet:
        print "Text console output redirection already disabled."
    else:
        try:
            obj.quiet = 1
            print "Disabling text console output redirection."
        except Exception, msg:
            print "[%s] Failed toggle console redirection" % obj.name
            print msg

def disable_quiet_cmd(obj):
    if obj.quiet:
        print "Text console output redirection already enabled."
    else:
        try:
            obj.quiet = 0
            print "Enabling text console output redirection."
        except Exception, msg:
            print "[%s] Failed toggle console redirection" % obj.name
            print msg

if device_name == "text-console":
    new_command("quiet", quiet_cmd,
                [],
                alias = "",
                type  = device_name + " commands",
                short = "toggle console output redirection",
                namespace = device_name,
                see_also = ['<text-console>.close',
                            '<text-console>.capture-start'],
                doc = """
                This command toggles if text-console output is redirected to the Simics
                console when the console window is closed. See also the
                &lt;text-console&gt;.capture-start command.
                """, filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="247")
    new_command("enable-quiet", quiet_cmd,
                [],
                alias = "",
                type  = device_name + " commands",
                short = "disable output redirection",
                namespace = device_name,
                doc_with = "<text-console>.quiet", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="260")
    new_command("disable-quiet", quiet_cmd,
                [],
                alias = "",
                type  = device_name + " commands",
                short = "enable output redirection",
                namespace = device_name,
                doc_with = "<text-console>.quiet", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="267")

#
# -------------------- no-window --------------------
#

def open_window_cmd(obj):
    if not obj.no_window:
        print "Window already opened."
    else:
        try:
            obj.no_window = 0
            print "Opening console window."
        except Exception, msg:
            print "[%s] Failed opening console window." % obj.name
            print msg

def close_window_cmd(obj):
    if obj.no_window:
        print "Window already closed."
    else:
        try:
            obj.no_window = 1
            print "Closing console window."
        except Exception, msg:
            print "[%s] Failed closing console window." % obj.name
            print msg

# obsolete
def enable_window_cmd(obj):
    open_window_cmd(obj)
    
# obsolete
def disable_window_cmd(obj):
    close_window_cmd(obj)
    
# obsolete
def no_window_cmd(obj):
    try:
	old = obj.no_window
        if (old == 0):
            obj.no_window = 1
            print "Closing console window."
        else:
            obj.no_window = 0
            print "Opening console window."
    except Exception, msg:
        print "[%s] Failed changing no-window mode" % obj.name
	print msg


if device_name == "text-console":
    new_command("open", open_window_cmd,
                [],
                type  = device_name + " commands",
                short = "open console window",
                namespace = device_name,
                see_also = ['<text-console>.quiet', '<text-console>.close'],
                doc = "Open the console window", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="325")
    new_command("close", close_window_cmd,
                [],
                type  = device_name + " commands",
                short = "close console window",
                namespace = device_name,
                see_also = ['<text-console>.quiet', '<text-console>.open'],
                doc = """Close the console window. When the console window is
                closed, any output is redirected to the main Simics window.
                This can be suppressed with the &lt;text-console&gt;.quiet
                command. To provide input to the target machine while the
                console is closed, use the &lt;text-console&gt;.input command.
                """, filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="332")
    new_command("no-window", no_window_cmd,
                [],
                alias = "",
                type  = "deprecated commands",
                deprecated = "<text-console>.close",
                short = "show/hide console window",
                namespace = device_name,
                doc = "Show/hide the console window.", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="344")
    new_command("enable-window", enable_window_cmd,
                [],
                alias = "",
                type  = "deprecated commands",
                deprecated = "<text-console>.open",
                short = "show console window",
                namespace = device_name,
                doc_with = "<text-console>.no-window", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="352")
    new_command("disable-window", disable_window_cmd,
                [],
                type  = "deprecated commands",
                deprecated = "<text-console>.close",
                short = "hide console window",
                namespace = device_name,
                doc_with = "<text-console>.no-window", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="360")

#
# -------------------- kbd-abort --------------------
#

def kbd_abort_cmd(obj):
    try:
	obj.abort =1
    except Exception, msg:
	print "[%s] Failed sending abort signal" % obj.name
	print msg

new_command("kbd-abort", kbd_abort_cmd,
            [],
            alias = "",
            type  = device_name + " commands",
            short = "send a keyboard abort signal",
	    namespace = device_name,
            doc = """
Send a serial line abort signal to the attached device.
This is only useful when the text-console is connected
to a serial device.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="379")

#
# -------------------- info --------------------
#


on_off_str = ("no", "yes")

def get_info(obj):
    if obj.classname == "server-console":
        return []
    else:
        return [(None,
                 [("No-window mode", on_off_str[obj.no_window]),
                  ("Quiet mode", on_off_str[obj.quiet])])]

sim_commands.new_info_command(device_name, get_info)

#
# -------------------- status --------------------
#

def get_status(obj):
    strings = map(lambda x: x[0], obj.break_string)
    return [(None,
             [("Current break strings", [ repr(s) for s in strings ])])]

sim_commands.new_status_command(device_name, get_status)

#
# -------------------- capture-start -----------------
#

def cap_start_cmd(obj, filename):
    try:
	obj.output_file = filename
    except Exception, msg:
	print "[%s] Failed starting capture." % obj.name
	print "Error was: %s" % msg

new_command("capture-start", cap_start_cmd,
            [arg(filename_t(), "filename")],
            alias = "",
            type  = device_name + " commands",
            short = "capture output to file",
	    namespace = device_name,
            see_also = ['<text-console>.capture-stop'],
            doc = """
Capture all output from the console to a file.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="430")

#
# -------------------- capture-stop -----------------
#

def cap_stop_cmd(obj):
    filename = obj.output_file
    obj.output_file = ""
    print "[%s] Capture to file '%s' stopped." % (obj.name, filename)

new_command("capture-stop", cap_stop_cmd,
            [],
            alias = "",
            type  = device_name + " commands",
            short = "stop output capture to file",
	    namespace = device_name,
            see_also = ['<text-console>.capture-start'],
            doc = """
Stop capturing all output from the console.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="450")

#
# ---------------- switch-to-server-console -------------
#

def switch_to_other_class(con, name,
                          cmp_classname, classname, cmp_attribs, attribs):
    if not name:
        name = con.name
    try:
        dev = con.device
    except:
        print "No device connected to console '%s'" % con.name
        raise CliError

    breakpoints = SIM_get_attribute(con, "break-string")

    newname = "new_" + name
    if 'console' in classname:
        obj_name = 'con'
        attribs += [['device', dev]]
    else:
        obj_name = 'link'
    try:
        if dev.component:
            basename = component_basename(cmp_classname)
            obj_cmp = SIM_create_object(
                cmp_classname,
                get_available_object_name(basename), cmp_attribs)
            pre_obj = get_component_object(obj_cmp, obj_name)
            if 'console' in classname:
                pre_obj.device = dev
            instantiate_cmd(False, [obj_cmp])
            obj = get_component_object(obj_cmp, obj_name)
        else:
            # support component-less configurations
            obj = SIM_create_object(classname, newname,
                                    attribs +
                                    [['queue', SIM_current_processor()]])
    except Exception, msg:
        print "Failed creating %s '%s': %s" % (classname, newname, msg)
        raise CliError

    SIM_set_attribute(obj, "break-string", breakpoints)

    if dev.component:
        disconnect_cmd(dev.component, None, con.component, None)
        connectors = [x for x in dev.component.connectors
                      if dev.component.connectors[x]['type'] == 'serial']
        free_cnt = sorted([x for x in connectors if
                           x not in [y[0] for y in dev.component.connections]])
        for cnt in free_cnt:
            connect_cmd(dev.component, cnt, obj.component, None, True)
            if 'console' in dir(sim.objects[dev.name]) and dev.console:
                break # correct connector!
            if 'link' in dir(sim.objects[dev.name]) and dev.link:
                break # correct connector!
            disconnect_cmd(dev.component, cnt, obj.component, None, True)
    else:
        dev.console = obj

    VT_hap_replace_object_references(con, obj)

    if con.component:
        try:
            SIM_delete_object(con.component)
        except:
            print ("Failed removing existing console component '%s'"
                   % con.component.name)
            raise CliError
    else:
        try:
            SIM_delete_object(con)
        except:
            print "Failed removing existing console '%s'" % con.name
            raise CliError
    try:
        VT_rename_object(obj, name)
    except SimExc_General, msg:
        # this shouldn't happen - we know the name is unused
        print "Error renaming %s to %s: %s" % (newname, name, msg)
        return

    if not SIM_get_quiet():
        print ("Device '%s' is now connected to %s '%s'."
               % (dev.name, classname, obj.name))

def switch_to_server_cmd(con, port):
    switch_to_other_class(con, None, "std-server-console", "server-console",
                          [['telnet_port', port]],
                          [['port', port]])

if device_name == "text-console":
    new_command("switch-to-server-console", switch_to_server_cmd,
                [arg(int_t, "port")],
                alias = "",
                type  = device_name + " commands",
                short = "replace text console with server console",
                namespace = device_name,
                doc = """
                Replace the text console with a server console used for
                telnet connections. The argument <param>port</param> is
                the port number that a telnet client can connect to.
                """, filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="553")


#
# ---------------- switch-to-text-console -------------
#

def switch_to_text_cmd(con):
    switch_to_other_class(con, None, "std-text-console", "text-console",
                          [['title', 'Console ' + con.name]],
                          [['title', 'Console ' + con.name]])

if device_name == "server-console":
    new_command("switch-to-text-console", switch_to_text_cmd,
                [],
                alias = "",
                type  = device_name + " commands",
                short = "replace server console with text console",
                namespace = device_name,
                doc = """
                Replace the server console with a standard text console.
                """, filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="576")

#
# ---------------- switch-to-serial-link -------------
#

def switch_to_serial_link_cmd(con, name):
    if name in sim.objects:
        name = get_available_object_name(name)
    switch_to_other_class(con, name, "std-serial-link", "serial-link", [], [])

new_command("switch-to-serial-link", switch_to_serial_link_cmd,
            [arg(str_t, "linkname")],
            alias = "",
            type  = device_name + " commands",
            short = "replace %s with serial link" % device_name,
            namespace = device_name,
            doc = """
            Replace the %s with a serial link. Another serial port, possibly
            in another Simics session can connect to the other end of the link.
            """ % device_name, filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="595")

def wait_for_string_cmd(obj, str):
    if conf.python.iface.python.in_main_branch():
        print "The wait-for-string command is only allowed in script branches."
        raise CliError
    con_name = obj.name
    obj.break_string = str
    # get break id at once
    break_id = obj.break_string_id[str]
    try:
        wait_for_obj_hap("Xterm_Break_String", obj, break_id)
    except SimExc_Break:
        print "Command '%s.wait-for-string' interrupted." % obj.name
        SIM_command_has_problem()
    # At this point the object may have changed (think; switch-to-
    # commands) so we retrieve the object again by the saved name.
    #
    # FIXME: This is a ugly hack to fix bug 5325.  It should be
    # reworked when refactoring the console code.
    obj = SIM_get_object(con_name)
    obj.unbreak_id = break_id

new_command("wait-for-string", wait_for_string_cmd,
            [arg(str_t, "string")],
            alias = "",
            type  = device_name + " commands",
            short = "wait for a string in a script branch",
	    namespace = device_name,
            see_also = ['<text-console>.break',
                        'script-branch',
                        'wait-for-variable',
                        'wait-for-hap',
                        '<text-console>.wait-for-string',
                        '<processor>.wait-for-cycle',
                        '<processor>.wait-for-step'],
            doc = """
Wait for the output of the text <arg>string</arg> on the
console. This command can only be run from a script branch
where it suspends the branch until the string has been
found in the output.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="627")

def start_recording_cmd(obj):
    obj.recorded_string = ""
    obj.recording = True

new_command("record-start", start_recording_cmd,
            [],
            alias = "",
            type = device_name + " commands",
            short = "start recording of output on the console",
            namespace = device_name,
            see_also = ['<text-console>.record-stop'],
            doc = """
Start recording of output on the console. All previously
recorded output will be discarded. The recorded string can
be read with the <cmd>record-stop</cmd> command.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="651")

def stop_recording_cmd(obj):
    record = obj.recorded_string
    obj.recording = False
    obj.recorded_string = ""
    return record

new_command("record-stop", stop_recording_cmd,
            [],
            alias = "",
            type = device_name + " commands",
            short = "stop recoding of output on the console",
            namespace = device_name,
            see_also = ['<text-console>.record-start'],
            doc = """
Stop recording of output on the console, and return the recorded string.
""", filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="670")

#
# ---------------- playback-start/stop -------------
#

def playback_event(cpu, u):
    while 1:
        line = u.stream.readline()
        u.lineno += 1
        if not line:
            print "[%s] File %s exhausted, playback stopped." %(
                u.bus.name, u.stream.name)
            return
        parts = line.split(':', 1)
        if len(parts) < 2: continue
        (cmd, line) = parts
        cmd = cmd.strip().lower()
        if cmd == "delay":
            try:
                secs = float(line)
            except ValueError:
                print "[%s] %s:%d: Could not parse %r as seconds."%(
                    u.bus.name, u.stream.name, u.lineno, line)
                continue
            SIM_time_post(u.bus.queue, secs,
                          Sim_Sync_Processor, playback_event, u)
            return
        elif cmd == "hexdata":
            data = ""
            for part in line.split():
                try:
                    data += chr(int(part, 16))
                except ValueError:
                    print "[%s] %s:%d: Could not parse %r as hexadecimal byte."%(
                        u.bus.name, u.stream.name, u.lineno, part)
                    continue
            u.bus.input = data

def playback_cmd(bus, filename):
    class X: pass
    u = X()
    try:
        u.stream = file(filename)
    except EnvironmentError, msg:
        raise CliError, msg
    u.bus = bus
    u.lineno = 0
    playback_event(None, u)

def playback_stop_cmd(bus):
    SIM_time_clean(bus.queue, Sim_Sync_Processor, playback_event, None)

new_command("playback-start", playback_cmd,
            args = [arg(filename_t(exist = 1), "filename")],
            short = "start traffic generator",
            doc = "Starts generating bus traffic from a specified file. "
                  "The file should consist of data and delay "
                  "specifications in a \"command: data\" format. "
                  "Examples:\n"
                  "<b>Delay: 0.345</b> will delay 345 milliseconds\n"
                  "<b>Hexdata: 72 6f 6f 74 0a</b> will send the string "
                  "\"root\\n\" to the connected device. Unrecognised lines "
                  "are ignored.",
            type = device_name + " commands",
            namespace = device_name,
            see_also = ["<"+device_name+">.playback-stop"], filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="732")

new_command("playback-stop", playback_stop_cmd,
            args = [],
            short = "stop traffic generation",
            doc = "Stop bus traffic generation previously started with "
                  "playback-start.",
            type = device_name + " commands",
            namespace = device_name,
            see_also = ["<"+device_name+">.playback-start"], filename="/mp/simics-3.0/src/extensions/text-console/commands.py", linenumber="747")
