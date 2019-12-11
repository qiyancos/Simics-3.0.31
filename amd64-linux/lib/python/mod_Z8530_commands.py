
##  Copyright 2000-2007 Virtutech AB

from cli import *
import string

#
# -------------------- kbd-abort --------------------
#

def kbd_abort_cmd(obj, tty):
    try:
        port = SIM_get_attribute(obj, string.lower(tty + "-port"))
        port.abort = 1
    except Exception, msg:
	print "[%s : tty-%s] Failed sending abort signal" % (obj.name, tty)
	print msg

new_command("kbd-abort", kbd_abort_cmd,
            [arg(str_t, "tty")],
            alias = "",
            type  = "Z8530 commands",
            short = "send a keyboard abort signal",
	    namespace = "Z8530",
            doc = """
Send keyboard signal abort to a <i>tty</i>""", filename="/mp/simics-3.0/src/devices/Z8530/commands.py", linenumber="19")
