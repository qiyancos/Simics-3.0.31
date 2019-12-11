from cli import *
from string import *
import sim_commands

def checkbit(a, bit):
    if a & (1 << bit):
        return 1
    else:
        return 0

#----------------------------------------------------------------------
#  Info & Status for io ports
#----------------------------------------------------------------------
def get_info_io_ports(obj):
    return [ (None,
              [])
             ]

def get_status_io_ports(obj):
    # Present status of the IO ports:
    # Port 0
    #   Bit 0 - peripheral
    #   Bit 1 - io,  output, value=1
    #   Bit 2 - enabled,  input
    #   Bit 3 - enabled,  output, value=0
    # Port 1
    #   ...
    #
    # List: [ ("Port 0", [ ("Bit 0 - ", "disabled"),
    #                      ("Bit 1 - ", "enabled, output, value=1")
    #                    ]
    report_list = []
    # Loop over all ports. Attributes are named "pN_pxin, pxout,
    # pxsel, pxdir" for the basic ports, 3 to 6
    for port in range (1,7):
        pxin  = SIM_get_attribute(obj,"p%d_pxin" % (port))
        pxout = SIM_get_attribute(obj,"p%d_pxout" % (port))
        pxsel = SIM_get_attribute(obj,"p%d_pxsel" % (port))
        pxdir = SIM_get_attribute(obj,"p%d_pxdir" % (port))
        interruptible_port = False
        if (port == 1) | (port == 2):
            # the interrupting settings
            interruptible_port = True
            pxifg = SIM_get_attribute(obj,"p%d_pxifg" % (port))
            pxies = SIM_get_attribute(obj,"p%d_pxies" % (port))
            pxie = SIM_get_attribute(obj,"p%d_pxie" % (port))            
        bit_state_list = []
        for bit in range (0,8):
            bit_name = "bit %d - " % bit
            bit_state = ""
            # common parts to all ports
            if checkbit(pxsel,bit):
                # pxsel = 1 -- used for other peripheral
                bit_state = "peripheral use"
            else:
                # pxsel = 0 -- io use
                bit_state += "io, "
                if checkbit(pxdir,bit):
                    # pxdir = 1 -- output port
                    bit_state +=  "output, value=%d" % checkbit(pxout,bit)
                else:
                    # pxdir = 0 -- input port
                    bit_state += "input,  value=%d" % checkbit(pxin,bit)
            # interruptible ports
            if interruptible_port :
                # interrupt control bits
                bit_state += ", ie=%d, ies=%d, ifg=%d" % (checkbit(pxie,bit),
                                                          checkbit(pxies,bit),
                                                          checkbit(pxifg,bit))
            # complete the bit state list
            bit_state_list += [(bit_name, bit_state)]
        # generate status item for this port
        report_list += [("Port %d" % (port), bit_state_list)]
    # return the completed list
    # print report_list
    return report_list

sim_commands.new_info_command('telos-io-ports', get_info_io_ports)
sim_commands.new_status_command('telos-io-ports', get_status_io_ports)


#----------------------------------------------------------------------
#  Info & Status for environment
#----------------------------------------------------------------------
def get_info_environment(obj):
    return [ (None,
              [])
             ]

def get_status_environment(obj):
    return [ ("Parameter values",
              [("Location.X", "%d" % obj.location_x),
               ("Location.Y", "%d" % obj.location_y),
               ("Location.Z", "%d" % obj.location_z),
               ("Temperature", "%d K / %d C" % (obj.temperature,obj.temperature-273))])]

sim_commands.new_info_command('telos-environment', get_info_environment)
sim_commands.new_status_command('telos-environment', get_status_environment)
