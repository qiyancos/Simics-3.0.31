import sim_commands
import pci_common
from cli import *
import vga_common

vga_name = "ragexl"

sim_commands.new_pci_header_command(vga_name)
vga_common.new_vga_commands(vga_name)

#
# ------------ print GUI register ---------------
#

def pgreg_cmd(obj, reg):
    SIM_set_attribute(obj, "print_greg", reg)

new_command("pgreg", pgreg_cmd,
            [arg(int_t, "reg")], 
            alias = "",
            type  = "%s commands" % vga_name,
            short = "print gui register contents",
	    namespace = vga_name,
            doc = """Print GUI register contents""", filename="/mp/simics-3.0/src/devices/ragexl/commands.py", linenumber="18")


#
# ----------- print setup register --------------
#

def psreg_cmd(obj, reg):
    SIM_set_attribute(obj, "print_sreg", reg)

new_command("psreg", psreg_cmd,
            [arg(int_t, "reg")], 
            alias = "",
            type  = "%s commands" % vga_name,
            short = "print setup register contents",
	    namespace = vga_name,
            doc = """Print Setup register contents""", filename="/mp/simics-3.0/src/devices/ragexl/commands.py", linenumber="34")


#
# -------------------- status --------------------
#

def status_cmd(obj, verbose):
    SIM_set_attribute(obj, "status_cmd", verbose)

new_command("status", status_cmd,
            [arg(int_t, "verbose", "?", 0)], 
            alias = "",
            type  = "%s commands" % vga_name,
            short = "show rage status",
	    namespace = vga_name,
            doc = """
Show information about the current rage state, for example the current resolution,
color depth, desktop image offset etc. Currently the <i>verbose</i> flag has no function.
""", filename="/mp/simics-3.0/src/devices/ragexl/commands.py", linenumber="50")


#
# -------------------- fbdump --------------------
#

def fbdump_cmd(obj, offs, width, height, format, stride):
    SIM_set_attribute(obj, "fbdump", [offs, width, height, format, stride])
#    print "Display Updated"

new_command("fbdump", fbdump_cmd,
            [arg(int_t, "fboffs"), 
             arg(int_t, "width"), 
             arg(int_t, "height"), 
             arg(int_t, "bpp", "?", 0), 
             arg(int_t, "stride", "?", 0)],
            alias = "",
            type  = "%s commands" % vga_name,
            short = "show part of rage framebuffer",
	    namespace = vga_name,
            doc = """
Display part of the %s framebuffer in the console window. <i>fboffs</i> is the starting offset into the
16 MB rage framebuffer. <i>width</i> and <i>height</i> are the pixel dimensions of the area to be shown. 
<i>bpp</i> (bits per pixel) specifies the format of the pixel data and can be one of 8, 16, 24 or 32 (defaults to
current desktop color depth). <i>stride</i> is
the byte offset between adjacent lines (defaults to width * bpp / 8).
""" % vga_name, filename="/mp/simics-3.0/src/devices/ragexl/commands.py", linenumber="70")

