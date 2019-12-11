
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

# Dredd features
#  - Standard PC system
#  - 256 Mb memory
#  - 20 MHz processor(s)
#  - DEC21143 PCI Ethernet adapter
#  - Voodoo3 AGP graphics device

if not "central_host"            in dir(): central_host = "localhost"
# one of: none, local, exported and remote
if not "central_setup"           in dir(): central_setup = "local"
if not "real_network"            in dir(): real_network = 0

if not "cpu_class"		 in dir(): cpu_class = "x86-p4"
if not "clock_freq_mhz"          in dir(): clock_freq_mhz = 20
if not "memory_megs"             in dir(): memory_megs = 256

if not "use_dec21143"            in dir(): use_dec21143 = 1
if not "dec21143_ethernet"       in dir(): dec21143_ethernet = "10:10:10:10:10:26"
if not "dec21143_slot"           in dir(): dec21143_slot = 4
if not "use_agp"                 in dir(): use_agp = 1
if not "use_voodoo3_agp"         in dir(): use_voodoo3_agp = 1
if not "num_ide_controllers"     in dir(): num_ide_controllers = 2
if not "use_piix4_usb"           in dir(): use_piix4_usb = 0
if not "use_piix4_pm"            in dir(): use_piix4_pm = 1

if not "boot_time"               in dir(): boot_time = [2001, 5, 30, 17, 0, 0]

if not "ide_disk_size"           in dir(): ide_disk_size = 20496236544

SIM_source_python(SIM_lookup_file("../x86-test-machine/pc-common.py"))
