from cli import *

#
# -------------------- redraw --------------------
#

def redraw_cmd(obj):
    SIM_set_attribute(obj, "redraw", 1)
    print "Display Updated"

#
# ------------------ refresh-rate -----------------
#

def refresh_rate_cmd(obj, rate):
    if rate < 1:
        old = SIM_get_attribute(obj, "refresh-rate")
        print "[%s] Current refresh-rate: %d Hz"  % (obj.name, old)
        return
    SIM_set_attribute(obj, "refresh-rate", rate)
    print "[%s] Setting refresh-rate: %d Hz" % (obj.name, rate)

#
# ------------------ text-dump -----------------
#

def text_dump_cmd(obj):
    try:
        text = SIM_get_attribute(obj, "text-page")
        print
        print "------ START OF TEXT DUMP -----"
        for i in range(len(text)):
            print text[i]
        print "------  END OF TEXT DUMP  -----"
        print
    except Exception, msg:
        print "Problem reading text page. Graphics device is most likely in non-text mode."

#
# ------------------ info -----------------
#

low_high_str = ("low", "high")
dis_en_str = ("Disabled", "Enabled")
clock_freq = (25, 28)
mon_col_str = ("Monochrome", "Color")
func_names = ("None", "AND", "OR", "XOR")
alpha_gfx_str = ("Alphanumeric", "Graphics")

def info_cmd(obj):
    try:
        crtc_regs = SIM_get_attribute(obj, "crtc_regs")
        seq_regs = SIM_get_attribute(obj, "seq_regs")
        attr_regs = SIM_get_attribute(obj, "attrib_regs")
        gfx_regs = SIM_get_attribute(obj, "gfx_regs")
        misc_reg = int(SIM_get_attribute(obj, "misc_reg"))
        view_x = SIM_get_attribute(obj, "view-size-x")
        view_y = SIM_get_attribute(obj, "view-size-y")
        video_en = int(SIM_get_attribute(obj, "attrib_video_enable"))        
    except Exception, msg:
        print "[%s] Problem reading device registers" % obj.name
        print msg
        return
    print "[%s] device '%s'" % (obj.classname, obj.name)
    print
    print "    Sync Polarity     : %d" % ((misc_reg & 0xc0) >> 6)
    print "    Selected 64k Page : %s (Used in modes 0, 1, 2, 3, 7)" % low_high_str[(misc_reg & 0x20) >> 5]
    print "    Video Driver      : %s" % dis_en_str[1 - ((misc_reg & 0x10) >> 4)]
    print "    Clock Selected    : %d MHz" % clock_freq[(misc_reg & 0x04) >> 2]
    print "    CPU Access to RAM : %s" % dis_en_str[(misc_reg & 0x02) >> 1]
    print "    Display Emulation : %s" % mon_col_str[misc_reg & 0x01]
    print "    CRTC:"
    print "      Start Address   : 0x%4x      Cursor Address     : 0x%x" % (
        (crtc_regs[0x0c] << 8) + crtc_regs[0x0d],
        (crtc_regs[0x0f] << 8) + crtc_regs[0x0e])
    print "      Cursor Start    : 0x%4x      Cursor End         : 0x%x" % (
        crtc_regs[0x0a] & 0x1f,
        crtc_regs[0x0b])
    print "      Horiz Total     :   %4d      Horiz Disp End     : %4d (char/line - 1)" % (
        crtc_regs[0x00],
        crtc_regs[0x01])
    print "      Max Scan Line   :   %4d (character height - 1)" % (crtc_regs[0x09] & 0x1f)
    print "      Vertical Total  :   %4d      Vertical Disp End  : %4d" % (
        (((crtc_regs[0x07] & 0x20) << 4) | ((crtc_regs[0x07] & 0x01) << 8) | crtc_regs[0x06]),
        (((crtc_regs[0x07] & 0x40) << 3) | ((crtc_regs[0x07] & 0x02) << 7) | crtc_regs[0x12]))
    print "      Scan Line Offset:   %4d" % crtc_regs[0x13]
    print "      Line compare    :   %d" % (
        (((crtc_regs[0x09] & 0x40) << 3) | ((crtc_regs[0x07] & 0x10) << 4) | crtc_regs[0x18]))
    print "      View 200 on 400 :   %d" % ((crtc_regs[0x09] & 0x80) >> 7)
    print "      Double Word     :   %d" % ((crtc_regs[0x14] & 0x40) >> 6)
    print "      Count by four   :   %d (only of Double Word)" % ((crtc_regs[0x14] & 0x20) >> 5)
    print "      Word/Byte Mode  :   %d (1 = byte)" % ((crtc_regs[0x17] & 0x40) >> 6)
    print "      Horiz Retrace   :   %d (double nbr of scanlines)"  % ((crtc_regs[0x17] & 0x04) >> 2)
    print "      Count by two    :   %d" % ((crtc_regs[0x17] & 0x08) >> 3)
    print "      Address Wrap    :   %d" % ((crtc_regs[0x17] & 0x20) >> 5)
    print "      Not Four Banks  :   %d" % ((crtc_regs[0x17] & 0x02) >> 1)
    print "      Not CGA Compat  :   %d" % (crtc_regs[0x17] & 0x01)
    print "      Viewable Size   :   %dx%d (calculated)" % (view_x, view_y)
    print "    Sequencer:"
    print "      Screen Off      :   %d" % ((seq_regs[0x01] & 0x20) >> 5)
    print "      Shift Four      :   %d" % ((seq_regs[0x01] & 0x10) >> 4)
    print "      Dot Clock       :   %d" % ((seq_regs[0x01] & 0x08) >> 3)
    print "      Shift Load      :   %d" % ((seq_regs[0x01] & 0x04) >> 2)
    print "      Eight dots/char :   %d (else nine)" % (seq_regs[0x01] & 0x01)
    print "      Character Map A :   %d" % (((seq_regs[0x03] & 0x20) >> 3) | ((seq_regs[0x03] & 0x0c) >> 2))
    print "      Character Map B :   %d" % (((seq_regs[0x03] & 0x10) >> 2) | (seq_regs[0x03] & 0x03))
    for i in range(4):
        print ("      Memory Plane %d  :   %s"
               % (i, dis_en_str[int((seq_regs[0x02] >> i) & 0x01)]))
    print "      Chain Four      :   %d" % ((seq_regs[0x04] & 0x08) >> 3)
    print "      Not Odd/Even    :   %d" % ((seq_regs[0x04] & 0x04) >> 2)
    print "      Extended Memory :   %d" % ((seq_regs[0x04] & 0x02) >> 1)
    print "    Attribute:"
    print "      Video           :   %s" % dis_en_str[video_en]
    print "      Palette Size    :   %d" % ((attr_regs[0x10] & 0x80) >> 7)
    p_str = ""
    for i in range(16):
        p_str = p_str + "%d " % attr_regs[i]
    print "      Palette         :   %s" % p_str
    print "      Pixel Clock     :   %d" % ((attr_regs[0x10] & 0x40) >> 6)
    print "      Enable Blink    :   %d" % ((attr_regs[0x10] & 0x08) >> 3)
    print "      Enable Line Gfx :   %d" % ((attr_regs[0x10] & 0x04) >> 2)
    print "      Graphics Mode   :   %d" % (attr_regs[0x10] & 0x01)
    c_str = ""
    for i in range(4):
        c_str = c_str + "%d " % ((attr_regs[0x12] >> i) & 0x01)
    print "      Color Plane 0-4 :   %s" % c_str
    print "    Graphics:"
    print "      Set/Reset       : 0x%x" % gfx_regs[0x00]
    print "      Enable Set/Reset: 0x%x" % gfx_regs[0x01]
    print "      Chain Odd/Even  :   %d" % ((gfx_regs[0x06] & 0x02) >> 1)
    print "      Memory Map      :   %d" % ((gfx_regs[0x06] & 0x0c) >> 2)
    print "      Rotate          :   %d" % (gfx_regs[0x03] & 0x07)
    print ("      Function        :   %s"
           % func_names[int((gfx_regs[0x03] & 0x18) >> 3)])
    print "      Odd/Even        :   %d" % ((gfx_regs[0x05] & 0x10) >> 4)
    print "      Write Mode      :   %d" % (gfx_regs[0x05] & 0x03)
    print "      Read Mode       :   %d" % ((gfx_regs[0x05] & 0x08) >> 3)
    print "      Read Map        :   %d" % gfx_regs[0x04]
    print "      Shift Reg       :   %d" % ((gfx_regs[0x05] & 0x60) >> 5)
    b_str = ""
    for i in range(8):
        b_str = b_str + "%d " % ((gfx_regs[0x08] >> i) & 0x01)
    print "      Bit Mask 0 - 7  :   %s" % b_str
    print ("      Mode (Gfx/Alpha):   %s"
           % alpha_gfx_str[int(gfx_regs[0x06] & 0x01)])
    print

def new_vga_commands(vga_name, info=1):
    new_command("redraw", redraw_cmd,
                [],
                alias = "",
                type  = "%s commands" % vga_name,
                short = "Redraw display",
                namespace = vga_name,
                doc = """
                This command sends the current frame buffer contents of the simulated
                video device to the graphics console. If a simulated cursor is active,
                it is updated as well.<br/>
                """, filename="/mp/simics-3.0/src/extensions/apps-python/vga_common.py", linenumber="150")

    new_command("refresh-rate", refresh_rate_cmd,
                [arg(int_t, "rate", "?", 0)],
                alias = "",
                type  = "%s commands" % vga_name,
                short = "Set rate at which %s updated display" % vga_name,
                namespace = vga_name,
                doc = """
                Set the rate at which the %s device updates the display.<br/>
                The default is 1000 Hz (simulated). NOTE: The rate is currently
                the same for all %s devices.
                """ % (vga_name, vga_name), filename="/mp/simics-3.0/src/extensions/apps-python/vga_common.py", linenumber="162")

    new_command("text-dump", text_dump_cmd,
                [],
                alias = "",
                type  = "%s commands" % vga_name,
                short = "Print text contents of display",
                namespace = vga_name,
                doc = """
                Print the contents of the display in text mode.<br/>
                """, filename="/mp/simics-3.0/src/extensions/apps-python/vga_common.py", linenumber="174")

    if info:
        new_command("info", info_cmd,
                    [],
                    alias = "",
                    type  = "%s commands" % vga_name,
                    short = "Print device status",
                    namespace = vga_name,
                    doc = """
                    Print information about the device registers.<br/>
                    """, filename="/mp/simics-3.0/src/extensions/apps-python/vga_common.py", linenumber="185")
