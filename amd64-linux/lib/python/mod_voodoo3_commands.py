from cli import *
import vga_common

vga_name = "voodoo3"
vga_common.new_vga_commands(vga_name, info=0)

#
# -------------------- info --------------------
#

def info_cmd(obj, verbose):
    SIM_set_attribute(obj, "info", verbose)

new_command("info", info_cmd,
            [arg(int_t, "verbose", "?", 0)], 
            alias = "",
            type  = "%s commands" % vga_name,
            short = "show voodoo3 info",
	    namespace = vga_name,
            doc = """
Show some information about the voodoo3 card.""", filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="14")

#
# -------------------- status --------------------
#

def status_cmd(obj, verbose):
    SIM_set_attribute(obj, "status", verbose)

new_command("status", status_cmd,
            [arg(int_t, "verbose", "?", 0)], 
            alias = "",
            type  = "%s commands" % vga_name,
            short = "show voodoo3 status",
	    namespace = vga_name,
            doc = """
Show information about the current voodoo3 state, for example the current resolution,
color depth, desktop image offset etc. Currently the <i>verbose</i> flag has no function.
""", filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="30")



#
# -------------------- render --------------------
#

def render_cmd(obj, on):
    SIM_set_attribute(obj, "render", on)
    print "Display Updated"

new_command("render", render_cmd,
            [arg(int_t, "bool", "?", 1)], 
            alias = "",
            type  = "%s commands" % vga_name,
            short = "toggle 3d rendering on/off",
	    namespace = vga_name,
            doc = """toggle 3d rendering""", filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="51")



#
# -------------- enable-fifo-break ---------------
#

def en_fifobp_cmd(obj):
    SIM_set_attribute(obj, "fifobp", 1)

new_command("enable-fifo-break", en_fifobp_cmd,
            alias = "",
            type  = "%s commands" % vga_name,
            short = "enable fifo breakpoints",
	    namespace = vga_name,
            doc = """When enabled, fifo breakpoints halts simics execution whenever a
                  complete fifo command packet has been sent to and executed by the
                  voodoo3 card.""", filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="68")

#
# -------------- disable-fifo-break ---------------
#

def dis_fifobp_cmd(obj):
    SIM_set_attribute(obj, "fifobp", 0)

new_command("disable-fifo-break", dis_fifobp_cmd,
            alias = "",
            type  = "%s commands" % vga_name,
            short = "disable fifo breakpoints",
	    namespace = vga_name,
            doc = """When enabled, fifo breakpoints halts simics execution whenever a
                  complete fifo command packet has been sent to and executed by the
                  voodoo3 card.""", filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="84")



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
            short = "show part of voodoo3 framebuffer",
	    namespace = vga_name,
            doc = """
Display part of the %s framebuffer in the console window. <i>fboffs</i> is the starting offset into the
16 MB voodoo3 framebuffer. <i>width</i> and <i>height</i> are the pixel dimensions of the area to be shown. 
<i>bpp</i> (bits per pixel) specifies the format of the pixel data and can be one of 8, 16, 24 or 32 (defaults to
current desktop color depth). <i>stride</i> is
the byte offset between adjacent lines (defaults to width * bpp / 8).
""" % vga_name, filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="103")

#
# ------------------ read init register -----------------
#

def ioreg_cmd(obj, reg):
    try:
        ioregs = SIM_get_attribute(obj, "io_base_regs")
    except (StandardError), msg:
        print "[%s] Problem reading device registers" % conf_object_name_get(obj)
        print msg
        return
    index = 0
    if (reg < 0) or (reg > 63):
	print "IO register %d doesn't exist" % reg
	return
    while index < 128:
	if index == reg:
            print "IO register 0x%x = 0x%x (%d)" % (index,ioregs[index],ioregs[index])
	    break
        index=index+1	

    print "IO register 0x%x = 0x%x (%d)" % (reg,ioregs[reg],ioregs[reg])

new_command("ioreg", ioreg_cmd,
            [arg(int_t, "register")],
            alias = "",
            type  = "%s commands" % vga_name,
            short = "print IO register",
	    namespace = vga_name,
            doc = """
Print value in an IO register.
""", filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="144")

#
# ------------------ read 2d register -----------------
#

def reg2d_cmd(obj, reg):
    try:
        regs_2d = SIM_get_attribute(obj, "mem_base_2d_regs")
    except (StandardError), msg:
        print "[%s] Problem reading device registers" % conf_object_name_get(obj)
        print msg
        return
    if (reg < 0) or (reg > 127):
	print "2D register %d doesn't exist" % reg
	return
    index = 0	
    while index < 128:
	if index == reg:
            print "2D register 0x%x = 0x%x (%d)" % (index,regs_2d[index],regs_2d[index])
	    break
        index=index+1	

    print "2D register 0x%x = 0x%x (%d)" % (reg,regs_2d[reg],regs_2d[reg])

new_command("reg2d", reg2d_cmd,
            [arg(int_t, "register")],
            alias = "",
            type  = "%s commands" % vga_name,
            short = "print 2D register",
	    namespace = vga_name,
            doc = """
Print value in a 2D command register.
""", filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="177")


#
# ------------------ read 3d register -----------------
#

def reg3d_cmd(obj, reg):
    try:
        regs_3d = SIM_get_attribute(obj, "mem_base_3d_regs")
    except (StandardError), msg:
        print "[%s] Problem reading device registers" % conf_object_name_get(obj)
        print msg
        return
    if (reg < 0) or (reg > 255):
	print "3D register %d doesn't exist" % reg
	return	
    index = 0
    while index < 256:
	if index == reg:
            print "3D register 0x%x = 0x%x (%d)" % (index,regs_3d[index],regs_3d[index])
	    break
        index=index+1	

    print "3D register 0x%x = 0x%x (%d)" % (reg,regs_3d[reg],regs_3d[reg])

new_command("reg3d", reg3d_cmd,
            [arg(int_t, "register")],
            alias = "",
            type  = "%s commands" % vga_name,
            short = "print 3D register",
	    namespace = vga_name,
            doc = """
Print value in a 3D register.
""", filename="/mp/simics-3.0/src/devices/voodoo3/commands.py", linenumber="211")
