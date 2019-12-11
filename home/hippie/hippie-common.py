
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

# Hippie features
#  - Standard PC system
#  - 256 Mb memory
#  - 40 MHz processor(s)
#  - AM79C960 NIC (ISA Lance)
#  - Voodoo3 PCI graphics device

if not "central_host"            in dir(): central_host = "localhost"
# one of: none, local, exported and remote
if not "central_setup"           in dir(): central_setup = "none"
if not "real_network"            in dir(): real_network = 0

if not "cpu_class"		 in dir(): cpu_class = "x86-p4"
if not "clock_freq_mhz"          in dir(): clock_freq_mhz = 40
if not "memory_megs"             in dir(): memory_megs = 256

if not "use_lance_ethernet"      in dir(): use_lance_ethernet = 1
if not "lance_ethernet"          in dir(): lance_ethernet = "10:10:10:10:10:20"
if not "use_simicsfs"            in dir(): use_simicsfs = 1
if not "use_agp"                 in dir(): use_agp = 0
if not "use_voodoo3_agp"         in dir(): use_voodoo3_agp = 0
if not "use_voodoo3_pci"         in dir(): use_voodoo3_pci = 1
if not "num_ide_controllers"     in dir(): num_ide_controllers = 1
if not "use_piix4_usb"           in dir(): use_piix4_usb = 1

if not "boot_time"               in dir(): boot_time = [2002, 9, 11, 10, 45, 0]
if not "use_dhcp"                in dir(): use_dhcp = 0

ide_disk_size = 1056964608
disk_files = [["hippie3-rh62.craff", "ro", 0, 1056964608, 0]]
if use_dhcp:
        disk_files += [["hippie3.1-dhcp.craff", "ro", 0, 1056964608, 0]]

SIM_source_python(SIM_lookup_file("../x86-test-machine/pc-common.py"))
