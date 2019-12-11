
##  Copyright 2004-2007 Virtutech AB
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

# Starts linux boot on pm-ppc machine

from text_console_common import wait_for_string

# This functions automatically takes care of entering the correct
# commands on the keyboard to force the pm-ppc card to boot up Linux.
#
# The function should be called from a script branch, such as:
# @start_branch(branch_start_linux). This will force the python
# branch to run as a seperate thread.
#
# You need to supply to arguments to this function via python
# variables. These are:
# linux_kernel - The name of the kernel to be loaded (with load file)
# boot_param   - The linux kernel boot parameters you want to start with

def branch_start_linux(con0):
    # Disable interactive keyboard input
    con0.read_only = 1
    # Type 's' to get into the monitor setup early
    con0.input = "s"
    # Wait for the prompt
    wait_for_string(con0, "PM/PPC[Ver 1.")
    # Load the kernel directly into memory
    cmd = "load-file %s 0x400000" % (linux_kernel)
    eval_cli_line(cmd)
    # Jump to the kernel start address
    con0.input = "call 400000\n"
    # Wait for the kernel to show the boot params
    wait_for_string(con0, "console=ttyS0,9600 root=nfs rw")
    # Adjust the boot parameters
    con0.input = "\b\b\b\b\b\b\b\b\b\b\b"
    con0.input = boot_param
    con0.input = "\n"
    # Enable interactive keyboard input again
    con0.read_only = 0    

def branch_start_linux_no_prom(args):
    (prefix, prompt, boot_param) = args
    con0 = SIM_get_object("%scon0" % prefix)
    # Disable interactive keyboard input
    con0.read_only = 1
    # Wait for the kernel to show the boot params
    wait_for_string(con0, prompt)
    # Adjust the boot parameters
    con0.input = boot_param
    con0.input = "\n"
    # Enable interactive keyboard input again
    con0.read_only = 0    

def branch_start_linux_no_prom_login_network_setup(args):
    (prefix, prompt, boot_param, ipaddr) = args
    con0 = SIM_get_object("%scon0" % prefix)
    # Disable interactive keyboard input
    con0.read_only = 1
    # Wait for the kernel to show the boot params
    wait_for_string(con0, prompt)
    # Adjust the boot parameters
    con0.input = boot_param
    con0.input = "\n"
    # Wait for linux login prompt
    wait_for_string(con0,"(none) login:")
    con0.input = "root\n"
    wait_for_string(con0,"# ")
    con0.input = "ifconfig eth0 %s netmask 255.255.255.0\n" % (ipaddr)
    # Enable interactive keyboard input again
    con0.read_only = 0    
    

