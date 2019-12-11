
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

# Standard Simics PC
# Highly customizable

from cli import *
from configuration import *

if not "num_processors"          in dir(): num_processors = 1
if not "threads_per_cpu"         in dir(): threads_per_cpu = 1
if not "cpu_class"               in dir(): cpu_class = "x86-p4"
if not "clock_freq_mhz"          in dir(): clock_freq_mhz = 100
if not "apic_bus_freq_mhz"       in dir(): apic_bus_freq_mhz = clock_freq_mhz / 2

# one of: none, local, exported and remote
if not "central_setup"           in dir(): central_setup = "none"
if not "central_host"            in dir(): central_host = "localhost"
if not "real_network"            in dir(): real_network = 0

if not "chipset"                 in dir(): chipset = "440bx"
if not "use_agp"                 in dir(): use_agp = 1
if not "use_piix4_usb"           in dir(): use_piix4_usb = 0
if not "use_piix4_pm"            in dir(): use_piix4_pm = 1
if not "use_ioapic"              in dir(): use_ioapic = 1
if not "use_apic"                in dir(): use_apic = 1
if not "use_generic_shadow"      in dir(): use_generic_shadow = 1

if not "use_lance_ethernet"      in dir(): use_lance_ethernet = 0
if not "lance_ethernet"          in dir(): lance_ethernet = "10:10:10:10:10:26"
if not "lance_irq"               in dir(): lance_irq = 7
if not "lance_dml_module"        in dir(): lance_dml_module = 0

if not "use_dec21041"            in dir(): use_dec21041 = 0
if not "dec21041_ethernet"       in dir(): dec21041_ethernet = "10:10:10:10:10:26"
if not "dec21041_slot"           in dir(): dec21041_slot = 4

if not "use_dec21143"            in dir(): use_dec21143 = 0
if not "dec21143_ethernet"       in dir(): dec21143_ethernet = "10:10:10:10:10:26"
if not "dec21143_slot"           in dir(): dec21143_slot = 4

if not "use_bcm5703c"            in dir(): use_bcm5703c = 0
if not "bcm5703c_ethernet"       in dir(): bcm5703c_ethernet = "10:10:10:10:10:26"
if not "bcm5703c_slot"           in dir(): bcm5703c_slot = 4

if not "memory_megs"             in dir(): memory_megs = 256
if not "ram_priority"            in dir(): ram_priority = 0

if not "num_floppy_drives"       in dir(): num_floppy_drives = 1
if not "floppy_image"            in dir(): floppy_image = None

if not "num_serial_ports"        in dir(): num_serial_ports = 2
if not "serial_port_class"       in dir(): serial_port_class = "NS16450"

if not "init_cmos"               in dir(): init_cmos = 1
if not "boot_time"               in dir(): boot_time = [2001, 5, 30, 17, 0, 0]
if not "boot_dev"                in dir(): boot_dev = "C"
if not "use_acpi"                in dir(): use_acpi = 1

if not "num_ide_controllers"     in dir(): num_ide_controllers = 2
if not "use_ide_disk"            in dir(): use_ide_disk = 1
if not "ide_disk_size"           in dir(): ide_disk_size = 20496236544
if not "disk_files"              in dir(): disk_files = []
if not "use_ide_cd"              in dir(): use_ide_cd = 1

if not "use_vga_isa"             in dir(): use_vga_isa = 0
if not "use_voodoo3_pci"         in dir(): use_voodoo3_pci = not use_agp
if not "use_ragexl_pci"          in dir(): use_ragexl_pci = 0
if not "use_voodoo3_agp"         in dir(): use_voodoo3_agp = use_agp

if not "use_console"             in dir(): use_console = 1
if not "use_video_text_console"  in dir(): use_video_text_console = 0

if not "use_simicsfs"            in dir(): use_simicsfs = 0

if not "linux_acpi_bug_workaround" in dir(): linux_acpi_bug_workaround = 0

if not "pci_irqa"                in dir(): pci_irqa = 10
if not "pci_irqb"                in dir(): pci_irqb = 11
if not "pci_irqc"                in dir(): pci_irqc = 10
if not "pci_irqd"                in dir(): pci_irqd = 11

if not "rombios"                 in dir(): rombios = "rombios-2.65.2.5"

if not "omit_pc_common_prologue_epilogue"  in dir():
        eval_cli_line('run-python-file ../scripts/extrapath.py')
        eval_cli_line('add-directory "%simics%/import/x86"')
        eval_cli_line('add-directory "%simics%/import/x86_64"')

if not "serial_3f8_console"      in dir(): serial_3f8_console = 0
if not "serial_2f8_console"      in dir(): serial_2f8_console = 0
if not "serial_3e8_console"      in dir(): serial_3e8_console = 0
if not "serial_2e8_console"      in dir(): serial_2e8_console = 0
if not "serial_2a0_console"      in dir(): serial_2a0_console = 0
if not "serial_2a8_console"      in dir(): serial_2a8_console = 0
if not "serial_2b0_console"      in dir(): serial_2b0_console = 0
if not "serial_2b8_console"      in dir(): serial_2b8_console = 0
if not "serial_1a0_console"      in dir(): serial_1a0_console = 0
if not "serial_1a8_console"      in dir(): serial_1a8_console = 0
if not "serial_1b0_console"      in dir(): serial_1b0_console = 0
if not "serial_1b8_console"      in dir(): serial_1b8_console = 0

if not "use_mmap_memory"         in dir(): use_mmap_memory = 0

if not "rtc_dml_module"          in dir(): rtc_dml_module = 0

#################

x86_conf.create_system(num_cpus = num_processors,
		       mhz = clock_freq_mhz,
		       mb = memory_megs,
		       cpu_class = cpu_class,
		       use_hostfs = use_simicsfs,
		       use_acpi = use_acpi,
		       ioapic = use_ioapic,
		       init_cmos = init_cmos,
		       threads_per_cpu = threads_per_cpu,
		       linux_acpi_bug_workaround = linux_acpi_bug_workaround,
		       use_apics = use_apic,
		       bios = rombios,
		       apic_bus_divisor = clock_freq_mhz / apic_bus_freq_mhz,
		       use_mmap_memory = use_mmap_memory,
                       ram_priority = ram_priority)

x86_conf.add_legacy_devices(year = boot_time[0],
			    month = boot_time[1],
			    mday = boot_time[2],
			    hour = boot_time[3],
			    minute = boot_time[4],
			    second = boot_time[5],
			    boot_dev = boot_dev,
                            rtc_dml_module = rtc_dml_module)

x86_conf.add_legacy_keyboard()

if num_serial_ports > 0:
	num_legacy_serial = num_serial_ports
	if num_legacy_serial > 4:
		num_legacy_serial = 4
        x86_conf.add_legacy_serial(num_ports = num_legacy_serial,
				   uart_class = serial_port_class,
				   use_console0 = serial_3f8_console,
				   use_console1 = serial_2f8_console,
				   use_console2 = serial_3e8_console,
				   use_console3 = serial_2e8_console)
	fourport_serial = num_serial_ports - num_legacy_serial
	if fourport_serial == 4:
		x86_conf.add_fourport(base_address = 0x2a0, irq = 5,
				      use_console0 = serial_2a0_console,
				      use_console1 = serial_2a8_console,
				      use_console2 = serial_2b0_console,
				      use_console3 = serial_2b8_console)
	elif fourport_serial == 8:
		x86_conf.add_fourport(base_address = 0x2a0, irq = 5,
				      use_console0 = serial_2a0_console,
				      use_console1 = serial_2a8_console,
				      use_console2 = serial_2b0_console,
				      use_console3 = serial_2b8_console)
		x86_conf.add_fourport(base_address = 0x1a0, irq = 5,
				      use_console0 = serial_1a0_console,
				      use_console1 = serial_1a8_console,
				      use_console2 = serial_1b0_console,
				      use_console3 = serial_1b8_console)
	elif fourport_serial != 0:
		handle_error("Invalid num_serial_ports setting")

x86_conf.add_legacy_floppy(num_drives = num_floppy_drives)

if use_lance_ethernet == 1:
        x86_conf.add_isa_lance(mac_address = lance_ethernet,
			       lance_irq = lance_irq,
			       lance_dml_module = lance_dml_module)

if num_ide_controllers > 0:
        x86_conf.add_isa_ide(num_controllers = num_ide_controllers)

if use_ide_disk:
        x86_conf.add_isa_ide_disk(controller = 0, slot = "master",
				  size = ide_disk_size, files = disk_files)

if use_ide_cd:
        x86_conf.add_isa_ide_cdrom(controller = iff(num_ide_controllers > 1, 1, 0), slot = iff(num_ide_controllers > 1, "master", "slave"))

if chipset == "440bx":
        x86_conf.add_north_bridge_443bx(new_pci_bus_id = "0", new_agp_bus_id = "0", use_agp = use_agp)
        x86_conf.add_south_bridge_piix4(pci_bus_id = "0",
					pci_irqa = pci_irqa,
					pci_irqb = pci_irqb,
					pci_irqc = pci_irqc,
					pci_irqd = pci_irqd,
					use_usb = use_piix4_usb,
					use_power_management = use_piix4_pm)
elif chipset == "430fx":
	x86_conf.add_north_bridge_430fx(new_pci_bus_id = "0")
	x86_conf.add_south_bridge_piix(pci_bus_id = "0")
elif chipset == "875p":
	x86_conf.add_north_bridge_875P(new_pci_bus_id = "0",
				       new_agp_bus_id = "0",
				       new_csa_bus_id = "0",
				       use_agp = 1,
				       use_csa = 1)
	x86_conf.add_south_bridge_piix4(pci_bus_id = "0",
					pci_irqa = pci_irqa,
					pci_irqb = pci_irqb,
					pci_irqc = pci_irqc,
					pci_irqd = pci_irqd,
					use_usb = use_piix4_usb,
					use_power_management = use_piix4_pm)
elif chipset != "":
	print "error, chipset %s not found, no chipset created." % chipset

if use_vga_isa:
        x86_conf.add_isa_vga(gfx_console = iff(use_console, not use_video_text_console, 0),
			     text_console = iff(use_console, use_video_text_console, 0))

if use_voodoo3_pci:
        x86_conf.add_pci_voodoo3(pci_bus_id = "0", slot_no = 5,
				 gfx_console = not use_video_text_console,
				 text_console = use_video_text_console)

if use_ragexl_pci:
        x86_conf.add_pci_ragexl(pci_bus_id = "0", slot_no = 2,
				gfx_console = iff(use_console, not use_video_text_console, 0),
				text_console = iff(use_console, use_video_text_console, 0))

if use_voodoo3_agp:
        x86_conf.add_agp_voodoo3(agp_bus_id = "0", slot_no = 0,
				 gfx_console = iff(use_console, not use_video_text_console, 0),
				 text_console = iff(use_console, use_video_text_console, 0))

if use_dec21041:
	x86_conf.add_pci_dec21041("0", dec21041_slot, dec21041_ethernet)

if use_dec21143:
	x86_conf.add_pci_dec21143("0", dec21143_slot, dec21143_ethernet)

if use_bcm5703c:
	x86_conf.add_pci_bcm5703c("0", bcm5703c_slot, bcm5703c_ethernet)

if use_generic_shadow:
        x86_conf.add_generic_shadow(mb = memory_megs)

if not "omit_pc_common_prologue_epilogue"  in dir():
        eval_cli_line("run-command-file ../central/central-include.simics")
        # call the user configuration function before finishing
        if "user_config" in dir():
                user_config()
        if "get_configuration" in dir():
                global_objs = get_configuration()
        else:
                global_objs = []
        x86_conf.finish_configuration(global_objs)
        #if use_console and not use_video_text_console:
        #        eval_cli_line("%scon0.poll-rate 50" % machine)
