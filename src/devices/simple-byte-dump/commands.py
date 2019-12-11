
##  Copyright 2004-2007 Virtutech AB

from cli import *
import sim_commands

def get_sbd_info(obj):
    return []

sim_commands.new_info_command('simple-byte-dump', get_sbd_info)

def get_sbd_status(obj):
    return [(None,
             [("Output file: ", obj.filename)])]

sim_commands.new_status_command('simple-byte-dump', get_sbd_status)

def set_output_file_cmd(obj, filename):
    try:
        obj.filename = filename
    except Exception, msg:
        print "Could not set output filename: %s" % msg

new_command("set-output-file", set_output_file_cmd,
            [arg(str_t, "filename")],
            alias = "",
            type  = "simple-byte-dump commands",
            short = "sets file to output to",
	    namespace = "simple-byte-dump",
            doc = """
Sets the name of the file to which bytes will be written.
""")
