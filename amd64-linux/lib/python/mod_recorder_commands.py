from cli import *
import sim_commands

#
# -------------------- info, status --------------------
#

def get_info(obj):
    return [('Clients',
             [(x.name, x.classname) for x in obj.clients])]

sim_commands.new_info_command("recorder", get_info)

def get_status(obj):
    if obj.recording:
        rec = "yes (file: %s)" % obj.out_file
    else:
        rec = "no"
    if obj.playback:
        play = "yes (file: %s)" % obj.in_file
    else:
        play = "no"
    return [(None,
             [("Recording", rec),
              ("Playing back", play)])]

sim_commands.new_status_command("recorder", get_status)

#
# -------------------- playback-start --------------------
#

def playback_start_cmd(obj, filename):
    try:
        SIM_set_attribute(obj, "in_file", filename)
        SIM_set_attribute(obj, "playback", 1)
        print "Playback from input file %s" % filename
    except Exception, msg:
        print "Error starting playback: %s" % msg

new_command("playback-start", playback_start_cmd,
            [arg(filename_t(exist = 1), "input-file")],
            alias = "",
            type  = "recorder commands",
            short = "play back recorded I/O",
            namespace = "recorder",
            doc = """
Starts playback from specified file.
The I/O traffic in the file that is to be played
back must have been recorded using a machine configuration
identical to the current configuration. It is highly recommended
that console input is blocked when you play back I/O, or the
session may lose its synchronization.
""", filename="/mp/simics-3.0/src/extensions/recorder/commands.py", linenumber="41")

#
# -------------------- playback-stop --------------------
#

def playback_stop_cmd(obj):
    try:
        SIM_set_attribute(obj, "playback", 0)
    except Exception, msg:
        print "%s" % msg
        

new_command("playback-stop", playback_stop_cmd,
            [],
            alias = "",
            type  = "recorder commands",
            short = "stop playback",
            namespace = "recorder",
            doc = """
Stop the I/O playback.
Note that once playback has been stopped in cannot
be restarted.<br/>
""", filename="/mp/simics-3.0/src/extensions/recorder/commands.py", linenumber="67")


#
# -------------------- recorder-start --------------------
#

def recorder_start_cmd(obj, filename):
    try:
        SIM_set_attribute(obj, "out_file", filename)
        SIM_set_attribute(obj, "recording", 1)
        print "Recording to output file %s" % filename
    except Exception, msg:
        print "Error starting recording: %s" % msg

new_command("recorder-start", recorder_start_cmd,
            [arg(filename_t(exist = 0), "output-file")],
            alias = "",
            type  = "recorder commands",
            short = "record input to file",
            namespace = "recorder",
            doc = """
Record input data to specified file.
I/O is recorded from all devices that are recording aware (that
includes all devices that are shipped in standard distributions).<br/>
""", filename="/mp/simics-3.0/src/extensions/recorder/commands.py", linenumber="92")

#
# -------------------- recorder-stop --------------------
#

def recorder_stop_cmd(obj):
    try:
        SIM_set_attribute(obj, "recording", 0)
    except Exception, msg:
        print "%s" % msg
        
new_command("recorder-stop", recorder_stop_cmd,
            [],
            alias = "",
            type  = "recorder commands",
            short = "stop recorder",
            namespace = "recorder",
            doc = """
Stop the recording of incoming data.<br/>
""", filename="/mp/simics-3.0/src/extensions/recorder/commands.py", linenumber="114")

#
# -------------------- recorder-save --------------------
#

def recorder_save_cmd(obj, filename):
    try:
        SIM_set_attribute(obj, "save_file", filename)
    except Exception, msg:
        print "%s" % msg
        
new_command("recorder-save", recorder_save_cmd,
            [arg(filename_t(exist = 0), "output-file")],
            alias = "",
            type  = "recorder commands",
            short = "save recorder",
            namespace = "recorder",
            doc = """
Save recorded playback data.<br/>
""", filename="/mp/simics-3.0/src/extensions/recorder/commands.py", linenumber="134")
