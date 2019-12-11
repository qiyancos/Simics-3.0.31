from cli import *
import vga_common, sim_commands

vga_name = "vga"
vga_common.new_vga_commands(vga_name)

def vga_get_status(obj):
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
        raise Exception, "[%s] Problem reading device registers" % obj.name

    return [(None,
             [("Sync Polarity", ((misc_reg & 0xc0) >> 6)),
              ("Selected 64k Page",
               "%s (Used in modes 0, 1, 2, 3, 7)" % low_high_str[(misc_reg & 0x20) >> 5]),
              ("Video Driver", dis_en_str[1 - ((misc_reg & 0x10) >> 4)]),
              ("Clock Selected", "%d MHz" % clock_freq[(misc_reg & 0x04) >> 2]),
              ("CPU Access to RAM", dis_en_str[(misc_reg & 0x02) >> 1]),
              ("Display Emulation", mon_col_str[misc_reg & 0x01]) ]),
            ("CRTC",
             [("Start Address", "0x%x" % ((crtc_regs[0x0c] << 8) + crtc_regs[0x0d])),
              ("Cursor Address", "0x%x" % ((crtc_regs[0x0f] << 8) + crtc_regs[0x0e])),
              ("Cursor Start", "0x%x" % (crtc_regs[0x0a] & 0x1f)),
              ("Cursor End", "0x%x" % crtc_regs[0x0b]),
              ("Horiz Total", "%d" % crtc_regs[0x00]),
              ("Horiz Disp End", "%d (char/line - 1)" % crtc_regs[0x01]),
              ("Max Scan Line", "%d (character height - 1)" % (crtc_regs[0x09] & 0x1f)),
              ("Vertical Total", "%d" % (((crtc_regs[0x07] & 0x20) << 4)
                                         | ((crtc_regs[0x07] & 0x01) << 8)
                                         | crtc_regs[0x06])),
              ("Vertical Disp End", "%d" % (((crtc_regs[0x07] & 0x40) << 3)
                                            | ((crtc_regs[0x07] & 0x02) << 7)
                                            | crtc_regs[0x12])),
              ("Scan Line Offset", "%d" % crtc_regs[0x13]),
              ("Line compare", "%d" % (((crtc_regs[0x09] & 0x40) << 3)
                                       | ((crtc_regs[0x07] & 0x10) << 4)
                                       | crtc_regs[0x18])),
              ("View 200 on 400", "%d" % ((crtc_regs[0x09] & 0x80) >> 7)),
              ("Double Word", "%d" % ((crtc_regs[0x14] & 0x40) >> 6)),
              ("Count by four", "%d (only of Double Word)" % ((crtc_regs[0x14] & 0x20) >> 5)),
              ("Word/Byte Mode", "%d (1 = byte)" % ((crtc_regs[0x17] & 0x40) >> 6)),
              ("Horiz Retrace", "%d (double nbr of scanlines)"  % ((crtc_regs[0x17] & 0x04) >> 2)),
              ("Count by two", "%d" % ((crtc_regs[0x17] & 0x08) >> 3)),
              ("Address Wrap", "%d" % ((crtc_regs[0x17] & 0x20) >> 5)),
              ("Not Four Banks", "%d" % ((crtc_regs[0x17] & 0x02) >> 1)),
              ("Not CGA Compat", "%d" % (crtc_regs[0x17] & 0x01)),
              ("Viewable Size", "%dx%d (calculated)" % (view_x, view_y))]),
            ("Sequencer",
             [("Screen Off", "%d" % ((seq_regs[0x01] & 0x20) >> 5)),
              ("Shift Four", "%d" % ((seq_regs[0x01] & 0x10) >> 4)),
              ("Dot Clock", "%d" % ((seq_regs[0x01] & 0x08) >> 3)),
              ("Shift Load", "%d" % ((seq_regs[0x01] & 0x04) >> 2)),
              ("Eight dots/char", "%d (else nine)" % (seq_regs[0x01] & 0x01)),
              ("Character Map A", "%d" % (((seq_regs[0x03] & 0x20) >> 3) | ((seq_regs[0x03] & 0x0c) >> 2))),
              ("Character Map B", "%d" % (((seq_regs[0x03] & 0x10) >> 2) | (seq_regs[0x03] & 0x03)))] +
             [("Memory Plane %d" % i,
               dis_en_str[int((seq_regs[0x02] >> i) & 0x01)])
              for i in range(4)] +
             [("Chain Four", "%d" % ((seq_regs[0x04] & 0x08) >> 3)),
              ("Not Odd/Even", "%d" % ((seq_regs[0x04] & 0x04) >> 2)),
              ("Extended Memory", "%d" % ((seq_regs[0x04] & 0x02) >> 1))]),
            ("Attribute",
             [("Video", dis_en_str[video_en]),
              ("Palette Size", "%d" % ((attr_regs[0x10] & 0x80) >> 7)),
              ("Palette", string.join([ str(attr_regs[i])
                                        for i in range(16) ], ' ')),
              ("Pixel Clock", "%d" % ((attr_regs[0x10] & 0x40) >> 6)),
              ("Enable Blink", "%d" % ((attr_regs[0x10] & 0x08) >> 3)),
              ("Enable Line Gfx", "%d" % ((attr_regs[0x10] & 0x04) >> 2)),
              ("Graphics Mode", "%d" % (attr_regs[0x10] & 0x01)),
              ("Color Plane 0-4", string.join([ str((attr_regs[0x12] >> i) & 0x01)
                                                for i in range(4) ], ' '))]),
            ("Graphics",
             [("Set/Reset", "0x%x" % gfx_regs[0x00]),
              ("Enable Set/Reset", "0x%x" % gfx_regs[0x01]),
              ("Chain Odd/Even", "%d" % ((gfx_regs[0x06] & 0x02) >> 1)),
              ("Memory Map", "%d" % ((gfx_regs[0x06] & 0x0c) >> 2)),
              ("Rotate", "%d" % (gfx_regs[0x03] & 0x07)),
              ("Function", func_names[int((gfx_regs[0x03] & 0x18) >> 3)]),
              ("Odd/Even", "%d" % ((gfx_regs[0x05] & 0x10) >> 4)),
              ("Write Mode", "%d" % (gfx_regs[0x05] & 0x03)),
              ("Read Mode", "%d" % ((gfx_regs[0x05] & 0x08) >> 3)),
              ("Read Map", "%d" % gfx_regs[0x04]),
              ("Shift Reg", "%d" % ((gfx_regs[0x05] & 0x60) >> 5)),
              ("Bit Mask 0 - 7", string.join([ str((gfx_regs[0x08] >> i) & 0x01)
                                               for i in range(8) ], ' ')),
              ("Mode (Gfx/Alpha)",
               alpha_gfx_str[int(gfx_regs[0x06] & 0x01)])])]

sim_commands.new_status_command(vga_name, vga_get_status)
