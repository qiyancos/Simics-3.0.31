
##  Copyright 2005-2007 Virtutech AB
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

#
# The configuration looks as follows:
#   + A single memory space, 'phys_mem'
#   + In this memory space, a RAM 'ram' of 256 MB,
#     is mapped at 0x10000000 to 0x2000000
#   + User devices can be mapped at any other address
# 
# Run this python file to gain access to device setup functions, using the
# command "run-python-file vacuum_setup.py"
#
# Then add devices using "add_device()".
#

def add_config(obj_list):
    try:
        SIM_add_configuration(obj_list, None)
        return 1
    except Exception, msg:
        SIM_clear_exception()
        print "Failed loading the configuration in Simics. This is probably"
        print "due to some misconfiguration, or that some required file is"
        print "missing."
        print
        print "Error message: ", msg
        print
        SIM_command_has_problem()
        if VT_remote_control():
            VT_send_control_msg(['startup-failure', 0, str(msg)])
        return 0

#
# Function to add new device
# 
# Call like '@add_device('my0', 'myclass', 0x1000, 0x10)' from a Simics script
#
def add_device(obj_name, obj_class, map_base_addr, map_length,
               map_fn = 0, map_offset = 0, map_target = None):
    obj = pre_conf_object(obj_name, obj_class)
    if add_config([obj]):
        conf.phys_mem.map += [[map_base_addr, sim.objects[obj_name],
                               map_fn, map_offset, map_length, map_target]]

ram_image = pre_conf_object('ram_image', 'image')
ram_image.size = 0x10000000
ram = pre_conf_object('ram', 'ram')
ram.image = ram_image
space = pre_conf_object('phys_mem', 'memory-space')
#             base         object  function  offset  length
space.map = [[0x10000000,  ram,    0,        0,      0x10000000]]
clock = pre_conf_object('timer', 'clock')
clock.freq_mhz = 20

if add_config((ram_image, ram, space, clock)):
    print
    print "Welcome to vacuum, a machine for testing devices in isolation."
    print
    print "To read from memory or device, use 'phys_mem.get <addr>'."
    print "To write to memory or device, use 'phys_mem.set <addr> <value>."
    print
    print "For help on get/set options regarding transfer sizes, use "
    print "'help phys_mem.get' or 'help phys_mem.set'"
    print
