
##  Copyright 2003-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.

from cli import *

#
# ------------------------ info -----------------------
#

divisor = ("1:2", "1:6", "1:4", "1:3", "1:5")
ranges = (2, 4, 8, 1)

def bit_tst(val, bit):
    if val & (1 << bit):
        return 1
    return 0

def info_cmd(obj):
    try:
        freq = (((obj.clk_reg2 ^ 0x0) & 0x01) << 8) | (obj.clk_reg1 ^ 0xfa)
        div = ((obj.clk_reg3 & 0x1) << 2) | ((obj.clk_reg2 >> 3) & 2) | ((obj.clk_reg2 >> 1) & 1)
        cpu_freq = (float(freq) / float(ranges[(obj.clk_reg2 >> 2) & 0x3]))
        if div == 1 or div == 4:
            cpu_freq *= 2
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return
    print div
    print
    print "sun4u-clockregs (%s)" % obj.name
    print "======================="
    print
    print "  Control base clock frequency : %d" % freq
    print "         Remote console enable : %s" % iff(obj.clk_reg2 & 0x80, "yes", "no")
    print "         Generate reset enable : %s" % iff(obj.clk_reg2 & 0x40, "yes", "no")
    print "              TOD reset enable : %s" % iff(obj.clk_reg2 & 0x20, "yes", "no")
    print "       Clock frequency divisor : %s" % divisor[div]
    print "           Clock range divisor : %d" % ranges[(obj.clk_reg2 >> 2) & 0x3]
    print "           CPU clock frequency : %f MHz" % cpu_freq


new_command("info", info_cmd,
            [],
            alias = "",
            type  = "sun4u-clockregs commands",
            short = "print information about the device",
	    namespace = "sun4u-clockregs",
            doc = """
Print detailed information about the clockregs device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-devices/commands.py", linenumber="59")

#
# ------------------------ info -----------------------
#

def info_cmd(obj):
    cnt = []
    lim = []
    per = []
    ien = []
    pnd = []
    try:
        cnt.append(SIM_get_attribute(obj, "count0"))
        cnt.append(SIM_get_attribute(obj, "count1"))
        lim.append(SIM_get_attribute(obj, "limit0"))
        lim.append(SIM_get_attribute(obj, "limit1"))
        per.append(SIM_get_attribute(obj, "periodic0"))
        per.append(SIM_get_attribute(obj, "periodic1"))
        ien.append(SIM_get_attribute(obj, "inten0"))
        ien.append(SIM_get_attribute(obj, "inten1"))
        pnd.append(SIM_get_attribute(obj, "irq_pending0"))
        pnd.append(SIM_get_attribute(obj, "irq_pending1"))
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return
    print
    print "sun4u-counter (%s)" % obj.name
    print "====================="
    print
    for i in range(2):
        print "Counter %d:" % i
        print "     Value   : 0x%08x" % cnt[i]
        print "     Limit   : 0x%08x" % lim[i]
        print "  Periodic   : %s" % iff(per[i], "yes", "no")
        print " Irq enabled : %s" % iff(ien[i], "yes", "no")
        print " Irq pending : %s" % iff(pnd[i], "yes", "no")

new_command("info", info_cmd,
            [],
            alias = "",
            type  = "sun4u-counter commands",
            short = "print information about the device",
	    namespace = "sun4u-counter",
            doc = """
Print detailed information about the counter device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-devices/commands.py", linenumber="105")


#
# ------------------------ info -----------------------
#

state_char = "ITRP"

def info_cmd(obj):
    try:
        mid = SIM_get_attribute(obj, "mid")
        valid = SIM_get_attribute(obj, "valid")
        tid = SIM_get_attribute(obj, "tid")
        state = SIM_get_attribute(obj, "state")
        level = SIM_get_attribute(obj, "level")
        irq_names = SIM_get_attribute(obj, "irq-names")
        tot_irq = len(irq_names)
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return
    print
    print "sun4u-fhc"
    print "========="
    print "    name : %s" % obj.name
    print "     MID : %d" % mid
    print
    print "Interrupt            Valid   TID   State"

    for i in range(tot_irq):
        print "%-20s    %d      %d     %c%c" % (
              irq_names[i], valid[i], tid[i], state_char[state[i]], iff(level[i], '+', ' '))
    

new_command("info", info_cmd,
            [],
            alias = "",
            type  = "sun4u-fhc commands",
            short = "print information about the device",
	    namespace = "sun4u-fhc",
            doc = """
Print detailed information about the fhc device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-devices/commands.py", linenumber="147")

#
# ------------------------ info -----------------------
#

num_connectors = 16
connector_number = (3100, 3101, 3200, 3201, 3300, 3301, 3400, 3401, 3500, 3501, 3600, 3601, 3700, 3701, 3800, 3801)
speed_grade = (50, 80, 70, 60)

def simm_size(no):
    if (no == 0x04):
        return "1Mx72 (8 MB)"
    elif (no == 0x0b):
        return "4Mx72 (32 MB)"
    elif (no == 0x0f):
        return "16Mx72 (128 MB)"
    else:
        return "Unknown"

def info_cmd(obj):
    try:
        connector = SIM_get_attribute(obj, "connector")
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return
    print
    print "sun4u-simm-status (%s)" % obj.name
    print "====================="
    for i in range(num_connectors):
        print "Connector   %d :   %s  %d ns    %s" % (connector_number[i],
                                                      iff(connector[i] & 0x80, "Parity", "ECC   "),
                                                      speed_grade[(connector[i] & 0x60) >> 5],
                                                      simm_size(connector[i] & 0x1f))
    print


new_command("info", info_cmd,
            [],
            alias = "",
            type  = "sun4u-simm-status commands",
            short = "print information about the device",
	    namespace = "sun4u-simm-status",
            doc = """
Print detailed information about the simm-status device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-devices/commands.py", linenumber="192")

#
# ------------------------ info -----------------------
#

slots = [0, 16, 5, 8]

def info_cmd(obj):
    try:
        ctrl = SIM_get_attribute(obj, "sys_ctrl")
        stat1 = SIM_get_attribute(obj, "sys_stat1")
        stat2 = SIM_get_attribute(obj, "sys_stat2")
        ppp_stat = SIM_get_attribute(obj, "ppp_stat")
        pwr_stat = SIM_get_attribute(obj, "pwr_stat")
        pwr_pres = SIM_get_attribute(obj, "pwr_pres")
        temp = SIM_get_attribute(obj, "temp")
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return
    print
    print "sun4u-systemregs (%s)" % obj.name
    print "======================="
    print
    print "Clock Board System Registers"
    print "System Control:"
    print "           Irq on fan fail : %sabled" % iff(ctrl & 0x80, "En", "Dis")
    print "  Irq on power supply fail : %sabled" % iff(ctrl & 0x40, "En", "Dis")
    print "      Irq on AC power fail : %sabled" % iff(ctrl & 0x20, "En", "Dis")
    print "  Irq on NOT_BRD_PRES chng : %sabled" % iff(ctrl & 0x10, "En", "Dis")
    print "          Left (green) LED : %s" % iff(ctrl & 0x04, "on", "off")
    print "       Middle (yellow) LED : %s" % iff(ctrl & 0x02, "on", "off")
    print "         Right (green) LED : %s" % iff(ctrl & 0x01, "on", "off")
    print
    print "System Status 1"
    print "  Nbr of slots            : %d" % slots[(stat1 & 0xc0) >> 6]
    print "  Key switch in secure pos: %s" % iff(stat1 & 0x20, "no", "yes")
    print "  Power Supply in loc 5   : %s" % iff(stat1 & 0x10, "yes", "no")
    print "  NOT_BRD_PRES = 0 in FHC : %s" % iff(stat1 & 0x08, "no", "yes")
    print "  Power Supply 0 Present  : %s" % iff(stat1 & 0x04, "no", "yes")
    print "  Sys reset from TOD      : %s" % iff(stat1 & 0x02, "no", "yes")
    print "  Sys reset after freq chg: %s" % iff(stat1 & 0x01, "no", "yes")
    print
    print "System Status 2"
    print "  Reset by remote console : %s" % iff(stat2 & 0x80, "yes", "no")
    print "  Peripherial power ok    : %s" % iff(stat2 & 0x40, "yes", "no")
    print "  3.3V on clock-board ok  : %s" % iff(stat2 & 0x20, "yes", "no")
    print "  5V on clock-board ok    : %s" % iff(stat2 & 0x10, "yes", "no")
    print "  AC Power fail           : %s" % iff(stat2 & 0x08, "yes", "no")
    print "  Rack/Disk fan fail      : %s" % iff(stat2 & 0x04, "yes", "no")
    print "  AC/Peripherial fan OK   : %s" % iff(stat2 & 0x02, "yes", "no")
    print "  Keyswitch fan OK        : %s" % iff(stat2 & 0x01, "yes", "no")
    print
    pr("Power Supply Status       : ")
    for i in range(8):
        pr("%d-%s  " % (i, iff(pwr_stat & (1 << i), "ok  ", "fail")))
    pr("\n")
    pr("Power Supply Precence     : ")
    for i in range(8):
        pr("%d-%s  " % (i, iff(pwr_pres & (1 << i), "no  ", "yes ")))
    pr("\n")
    print
    print "Precharge and Peripherial Power Status"
    print "  Current-share system    : %s" % iff(ppp_stat & 0x80, "no", "yes")
    print "  Peripherial 5V          : %s" % iff(ppp_stat & 0x40, "ok", "fail")
    print "  Peripherial 12V         : %s" % iff(ppp_stat & 0x20, "ok", "fail")
    print "  Auxiliary 5V            : %s" % iff(ppp_stat & 0x10, "ok", "fail")
    print "  Peripherial 5V Prech.   : %s" % iff(ppp_stat & 0x08, "ok", "fail")
    print "  Peripherial 12V Prech.  : %s" % iff(ppp_stat & 0x04, "ok", "fail")
    print "  System 3.3V             : %s" % iff(ppp_stat & 0x02, "ok", "fail")
    print "  System 5V               : %s" % iff(ppp_stat & 0x01, "ok", "fail")
    print
    print "Temperature Register      : %d" % temp
    print


new_command("info", info_cmd,
            [],
            alias = "",
            type  = "sun4u-systemregs commands",
            short = "print information about the device",
	    namespace = "sun4u-systemregs",
            doc = """
Print detailed information about the systemregs device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-devices/commands.py", linenumber="276")

def show_leds_cmd(obj):
    obj.show_leds = 1

new_command("show-leds", show_leds_cmd,
            [],
            alias = "",
            type  = "sun4u-systemregs commands",
            short = "Show changes to the system LEDs",
	    namespace = "sun4u-systemregs",
            doc = """
Show when any of the three system LEDs are turned
on or off.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-devices/commands.py", linenumber="289")

def hide_leds_cmd(obj):
    obj.show_leds = 0

new_command("hide-leds", hide_leds_cmd,
            [],
            alias = "",
            type  = "sun4u-systemregs commands",
            short = "Don't show changes to the system LEDs",
	    namespace = "sun4u-systemregs",
            doc = """
Don't show when the system LEDs are turned on or off.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-devices/commands.py", linenumber="303")

#
# ------------------------ info -----------------------
#

def info_cmd(obj):
    try:
        temp = SIM_get_attribute(obj, "temp")
    except Exception, msg:
        print "Problem reading attributes from device: %s" % msg
        return
    print
    print "sun4u-temperature (%s)" % obj.name
    print "========================"
    print "  Temperature Register (raw) : %d" % temp
    print


new_command("info", info_cmd,
            [],
            alias = "",
            type  = "sun4u-temperature commands",
            short = "print information about the device",
	    namespace = "sun4u-temperature",
            doc = """
Print detailed information about the temperature device.<br/>
""", filename="/mp/simics-3.0/src/devices/sunfire-devices/commands.py", linenumber="330")
