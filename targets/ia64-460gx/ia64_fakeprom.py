
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

import os, sim_core

# This file contains some utility functions for the ia64-fakeprom.  It
# also contains a handler for the simics-console print magic.
#
# The function of interest are:
#
#   load_ramdisk(file, address = ...)
#       - Load a ramdisk from a file.  The address default to the
#         correct value
#
#   sal_setup(entry, iobase)
#       - Setup some parameter for the fakeprom before it is started.
#         The first parameter is the entrypoint to the kernel, and the
#         iobase is the address where the I/O space is mapped.



# Read/write a register value to the current cpu
def read_reg(cpu, reg):
    return SIM_read_register(cpu, SIM_get_register_number(cpu, reg))

def write_reg(cpu, reg, val):
    SIM_write_register(cpu, SIM_get_register_number(cpu, reg), val)

# Load a ramdisk from a file to the standard location, and then set r4
# to convey the ramdisk size to the fakeprom
def load_ramdisk(file, address):
    cpu, _ = cli.get_cpu()
    simics_file = SIM_lookup_file(file)
    if not simics_file:
        print "Can't find file " + file
        return None
    # Not necessary any more -jojo
    # simics_file = SIM_native_path(simics_file)
    _,_,_,_,_,_,size,_,_,_ = os.stat(simics_file)
    SIM_load_file(cpu.physical_memory, simics_file, address, 0)
    # write_reg(cpu, "r4", size)
    return size


def sal_setup(cpu_list, num_cpus_in_machine,
              memory_megs,
              salentry, linuxentry = None, iobase = 0x00000ffffc000000L, fake_efi = 1,
              ramdisk_start = 0, ramdisk_size = 0, debug = 0,
              cmdline = ""):

    ram_size = memory_megs * 1024*1024

    # First, setup boot processor (BSP)
    cpu = cpu_list[0]

    if SIM_get_verbose():
        print "salentry = 0x%x" % salentry
    SIM_set_program_counter(cpu, salentry)
    
    # This can be any valid address that doesn't overwrite anything.
    cmdline_addr = 0x1000000
    for i in range(0, len(cmdline)):
        SIM_write_phys_memory(cpu,  cmdline_addr + i, ord(cmdline[i]), 1)
    SIM_write_phys_memory(cpu,  cmdline_addr + len(cmdline), 0, 1)

    write_reg(cpu, "r32", fake_efi)
    write_reg(cpu, "r33", debug)
    write_reg(cpu, "r34", iobase)
    write_reg(cpu, "r35", linuxentry)
    write_reg(cpu, "r36", ramdisk_start)
    write_reg(cpu, "r37", ramdisk_size)
    write_reg(cpu, "r38", cmdline_addr)
    write_reg(cpu, "r39", num_cpus_in_machine)
    write_reg(cpu, "r40", ram_size)

    # Now setup secondary processors to wait for wakeup
    for n in range(1, num_cpus_in_machine):
        # We really want linux to think that cpu0 is the first
        # processor and cpu1 is the second etc.  For this, we cannot
        # trust SIM_proc_no_2_ptr().
        cpu = cpu_list[n]
        SIM_set_program_counter(cpu, salentry)
        SIM_disable_processor(cpu)
        write_reg(cpu, "r32", 2)
        write_reg(cpu, "r39", n)


def read_bytes(address, size):
    try:
        bytes = SIM_current_processor().physical_memory.memory[[address, address + size - 1]]
    except:
        print "failed to access p:0x%x" % address
    else:
        return bytes

def read_byte(cpu, address):
    return SIM_read_phys_memory(cpu, address, 1)

def read_string(cpu, address):
    c = read_byte(cpu, address)
    s = ""
    while c != 0:
        s += chr(c)
        address += 1
        c = read_byte(cpu, address)
    return s



hap_Magic_Instruction = SIM_hap_get_number("Core_Magic_Instruction")

# Magic print callback
magic_print_level = 0
def magic_print(foo, cpu, arg):
    if read_reg(cpu, "r32") > magic_print_level:
        return
    try:
        s = read_string(cpu, read_reg(cpu, "r30"))
    except sim_core.SimExc_Memory:
        s = "<unreadable at 0x%x>\n" % read_reg(cpu, "r30")
    cli.pr("[%s] %s" % (cpu.name, s))
    if len(s) == 0 or s[-1] != "\n":
        cli.pr(" [...]\n")
    return 0

hap = SIM_hap_add_callback_index("Core_Magic_Instruction", magic_print, None, 0xffffe)


# Magic break callback
def magic_break(foo, cpu, bar):
    SIM_break_simulation("magic panic")

hap = SIM_hap_add_callback_index("Core_Magic_Instruction", magic_break, None, 0xffffd)




# ---------------------------------------------------------------------------
#
#  read/write physical memory
#

from struct import *

def ia64_fw_read_bytes(cpu, address, size):
    return cpu.physical_memory.memory[[address, address + size - 1]]

def ia64_fw_write_bytes(cpu, address, bytes):
    cpu.physical_memory.memory[[address, address + len(bytes) - 1]] = bytes

def ia64_fw_read_uint(cpu, address, size):
    bytes = ia64_fw_read_bytes(cpu, address, size)
    value = 0
    for i in range(0, size):
        value = value + (long(bytes[i]) << (i * size))
    return value

def ia64_fw_write_uint(cpu, address, size, value):
    bytes = range(0, size)
    for i in range(0, size):
        bytes[i] = value >> (i * size) & 0xFF
    ia64_fw_write_bytes(cpu, address, bytes)

def ia64_fw_read_uint64(cpu, address):
    return ia64_fw_read_uint(cpu, address, 8)

def ia64_fw_write_uint64(cpu, address, value):
    ia64_fw_write_uint(cpu, address, 8, value)

def ia64_fw_read_string(cpu, address, size):
    bytes = ia64_fw_read_bytes(cpu, address, size)
    string = ""
    for i in range(size):
        string += chr(bytes[i])
    return string

def ia64_fw_write_string(cpu, address, string):
    ia64_fw_write_bytes(cpu, address, map(lambda x: ord(x), string))

def ia64_fw_read_struct(cpu, address, format):
    return unpack(format, ia64_fw_read_string(cpu, address, calcsize(format)))

def ia64_fw_write_struct(cpu, address, format, values):
    string = apply(pack, tuple(list([format]) + list(values)))
    ia64_fw_write_string(cpu, address, string)


# ---------------------------------------------------------------------------
#
#  find scsi disks/cdroms in the current configuration
#

def ia64_fw_get_scsi_disks():
    objects = SIM_all_objects()
    scsi_disks = []
    for obj in objects:
        if SIM_get_attribute(obj, "classname") == "scsi-disk":
            scsi_disks.append(obj)
    return scsi_disks

def ia64_fw_get_scsi_cdroms():
    objects = SIM_all_objects()
    scsi_cdroms = []
    for obj in objects:
        if SIM_get_attribute(obj, "classname") == "scsi-cdrom":
            scsi_cdroms.append(obj)
    return scsi_cdroms

def ia64_fw_get_scsi_devices():
    return ia64_fw_get_scsi_disks() + ia64_fw_get_scsi_cdroms()

def ia64_fw_bios_device_number_to_object(device_number):
    scsi_disks  = ia64_fw_get_scsi_disks()
    scsi_cdroms = ia64_fw_get_scsi_cdroms()
    if device_number >= 0x80 and device_number < (0x80 + len(scsi_disks)):
        return scsi_disks[device_number - 0x80]
    elif device_number >= 0xE0 and device_number < (0xE0 + len(scsi_cdroms)):
        return scsi_cdroms[device_number - 0xE0]
    else:
        SIM_break_simulation("unknown bios device number: 0x%x" % device_number)

# ---------------------------------------------------------------------------
#
#  salcb_getmediainfo
#

def ia64_fw_salcb_getmediainfo(foo, cpu, bar):
    media_type  = read_reg(cpu, "r32")
    buffer_size = read_reg(cpu, "r33")
    buffer      = read_reg(cpu, "r34")
    print "salcb_getmediainfo(%d, %d, 0x%x)" % (media_type, buffer_size, buffer)
    # cdrom
    if media_type == 1:
        cdroms = ia64_fw_get_scsi_cdroms()
        write_reg(cpu, "r9", len(cdroms))
        write_reg(cpu, "r10", 0)
        write_reg(cpu, "r11", 0)
        if buffer_size < 16 * len(cdroms):
            write_reg(cpu, "r8", -3L)
        else:
            write_reg(cpu, "r8", 0)
            for i in range(0, len(cdroms)):
                ia64_fw_write_uint64(cpu, buffer + i * 16, 0xE0 + i)
                ia64_fw_write_uint64(cpu, buffer + i * 16  + 8, 0)
    # ls120
    elif media_type == 2:
        write_reg(cpu, "r8", 0)
        write_reg(cpu, "r9", 0)
        write_reg(cpu, "r10", 0)
        write_reg(cpu, "r11", 0)
    else:
        SIM_break_simulation("salcb_getmediainfo: unknown media_type %d" % media_type)
  

class ia64_fw_bios_registers:
    def __init__(self):
        self.reg       = []
        self.eax       = 0
        self.ecx       = 0
        self.edx       = 0
        self.ebx       = 0
        self.esp       = 0
        self.ebp       = 0
        self.esi       = 0
        self.edi       = 0
        self.flags     = 0
        self.eip       = 0
        self.cs        = 0
        self.ds        = 0
        self.es        = 0
        self.fs        = 0
        self.gs        = 0
        self.ss        = 0
        self.reserved1 = 0
        self.reserved2 = 0
    
    def read(self, cpu):
        self.reg       = list(ia64_fw_read_struct(cpu, read_reg(cpu, "r32"), "=10I6HIQ"))
        self.eax       = self.reg[0]
        self.ecx       = self.reg[1] 
        self.edx       = self.reg[2] 
        self.ebx       = self.reg[3] 
        self.esp       = self.reg[4] 
        self.ebp       = self.reg[5] 
        self.esi       = self.reg[6] 
        self.edi       = self.reg[7] 
        self.flags     = self.reg[8] 
        self.eip       = self.reg[9] 
        self.cs        = self.reg[10]
        self.ds        = self.reg[11]
        self.es        = self.reg[12]
        self.fs        = self.reg[13]
        self.gs        = self.reg[14]
        self.ss        = self.reg[15]
        self.reserved1 = self.reg[16]
        self.reserved2 = self.reg[17]
    
    def write(self, cpu):
        self.reg[0]  = self.eax
        self.reg[1]  = self.ecx      
        self.reg[2]  = self.edx      
        self.reg[3]  = self.ebx      
        self.reg[4]  = self.esp      
        self.reg[5]  = self.ebp      
        self.reg[6]  = self.esi      
        self.reg[7]  = self.edi      
        self.reg[8]  = self.flags    
        self.reg[9]  = self.eip      
        self.reg[10] = self.cs       
        self.reg[11] = self.ds       
        self.reg[12] = self.es       
        self.reg[13] = self.fs       
        self.reg[14] = self.gs       
        self.reg[15] = self.ss       
        self.reg[16] = self.reserved1
        self.reg[17] = self.reserved2
        ia64_fw_write_struct(cpu, read_reg(cpu, "r32"), "=10I6HIQ", tuple(self.reg))
        
# ---------------------------------------------------------------------------
#
#  edd_check_extensions_present
#

def ia64_fw_edd_check_extensions_present(foo, cpu, bar):
    bios_registers = ia64_fw_bios_registers()
    bios_registers.read(cpu);
    #regs = list(ia64_fw_read_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ"))
    #eax = regs[0]
    #edx = regs[2]
    #ebx = regs[3]
    #ds = regs[11]
    #dl = edx & 0xFF
    dl = bios_registers.edx & 0xFF
    #if (eax >> 8) != 0x41:
    if (bios_registers.eax >> 8) != 0x41:
        SIM_break_simulation("edd_check_extensions_present: ah != 0x41")
    #if ebx != 0x55AA:
    if bios_registers.ebx != 0x55AA:
        #print "0x%x" % ebx
        print "0x%x" % bios_registers.ebx
        SIM_break_simulation("edd_check_extensions_present: bx != 0xAA55")
    if dl >= 0xE0:
        #regs[1] = 0x0b
        bios_registers.ecx = 0x0b
    else:
        #regs[1] = 0x09
        bios_registers.ecx = 0x09
    bios_registers.eax = 0x3000
    #regs[0] = 0x3000
    bios_registers.ebx = 0xAA55
    #regs[3] = 0xAA55
    # setup register values for successful exit
    bios_registers.flags &= 0xFFFFFFFE
    #regs[8] = regs[8] & 0xFFFFFFFE
    bios_registers.write(cpu)
    #ia64_fw_write_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ", tuple(regs))

# ---------------------------------------------------------------------------
#
#  edd_extended_read
#

def ia64_fw_edd_extended_read(foo, cpu, bar):
    bios_registers = ia64_fw_bios_registers()
    bios_registers.read(cpu);
    #regs = list(ia64_fw_read_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ"))    
    #esi = regs[6]
    #ds = regs[11]
    foo = bios_registers.ds << 4 | bios_registers.esi
    #dev_addr_packet = ia64_fw_read_struct(cpu, ds << 4 | esi, "=4BI2Q2I")
    dev_addr_packet = ia64_fw_read_struct(cpu, foo, "=4BI2Q2I")
    #device_number = regs[2] & 0xFF
    device_number = bios_registers.edx & 0xFF
    device = ia64_fw_bios_device_number_to_object(device_number)
    if device_number >= 0xE0:
        block_size = 2048
    else:
        block_size = 512
    logical_block_address = dev_addr_packet[5]
    if dev_addr_packet[2] == 0xFF:
        host_transfer_buffer = dev_addr_packet[6]
        count = dev_addr_packet[7]
    else:
        count = dev_addr_packet[2]
        if dev_addr_packet[4] == 0xFFFFFFFFL:
            host_transfer_buffer = dev_addr_packet[6]
        else:
            host_transfer_buffer = dev_addr_packet[4]
    print "edd_extended_read: %s: 0x%x block(s) from 0x%x to 0x%x" % (
        device.name, count, logical_block_address, host_transfer_buffer)
    # read blocks one by one
    try:
        for i in range(count):
            block = SIM_get_attribute_idx(device, "sector_data", logical_block_address + i)
            ia64_fw_write_bytes(cpu, host_transfer_buffer + i * block_size, block)
    except:
       print "*** ia64_fw_edd_extended_read failed ***"
       #regs[0] = 0
       #regs[8] = regs[8] | 0x01
       bios_registers.eax = 0
       bios_registers.flags |= 0x01
    else:
        # SIM_break_simulation("ia64_fw_edd_extended_read")
        # setup register values for successful exit
        bios_registers.eax = 0
        #regs[0] = 0
        #regs[8] = regs[8] & 0xFFFFFFFE
        bios_registers.flags &= ~1
    bios_registers.write(cpu)
    #ia64_fw_write_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ", tuple(regs))


# ---------------------------------------------------------------------------
#
#  edd_extended_write
#

def ia64_fw_edd_extended_write(foo, cpu, bar):
    regs = list(ia64_fw_read_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ"))
    esi = regs[6]
    ds = regs[11]
    dev_addr_packet = ia64_fw_read_struct(cpu, ds << 4 | esi, "=4BI2Q2I")
    device_number = regs[2] & 0xFF
    device = ia64_fw_bios_device_number_to_object(device_number)
    if device_number >= 0xE0:
        regs[0] = 0
        regs[8] = regs[8] | 0x01
        ia64_fw_write_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ", tuple(regs))
        return
    else:
        block_size = 512
    logical_block_address = dev_addr_packet[5]
    if dev_addr_packet[2] == 0xFF:
        host_transfer_buffer = dev_addr_packet[6]
        count = dev_addr_packet[7]
    else:
        count = dev_addr_packet[2]
        if dev_addr_packet[4] == 0xFFFFFFFFL:
            host_transfer_buffer = dev_addr_packet[6]
        else:
            host_transfer_buffer = dev_addr_packet[4]
    print "edd_extended_write: %s: 0x%x block(s) to 0x%x" % (
        device.name, count, logical_block_address)
    try:
        for i in range(count):
            block = ia64_fw_read_bytes(cpu, host_transfer_buffer + i * block_size, block_size)
            SIM_set_attribute_idx(device, "sector_data", logical_block_address + i, block)
            
    except:
       print "*** ia64_fw_edd_extended_write failed ***"
       regs[0] = 0
       regs[8] = regs[8] | 0x01
    else:
        # SIM_break_simulation("ia64_fw_edd_extended_read")
        # setup register values for successful exit
        regs[0] = 0
        regs[8] = regs[8] & 0xFFFFFFFE
    ia64_fw_write_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ", tuple(regs))
    
    
# ---------------------------------------------------------------------------
#
#  edd_get_device_parameters
#

def ia64_fw_edd_get_device_parameters(foo, cpu, bar):
    regs = list(ia64_fw_read_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ"))
    esi = regs[6]
    ds = regs[11]
    pb = ds << 4 | esi
    dl = regs[2] & 0xFF
    if dl >= 0x80 and dl < (0x80 + len(ia64_fw_get_scsi_disks())):
        device = ia64_fw_get_scsi_disks()[dl - 0x80]
        geometry = device.geometry;
        bytes_per_sector = 512
    elif dl >= 0xE0 and dl < (0xE0 + len(ia64_fw_get_scsi_cdroms())):
        device = ia64_fw_get_scsi_cdroms()[dl - 0xE0]
        geometry = [0, 0, 0]
        bytes_per_sector = 2048
    print "edd_get_device_parameters: %s" % device.name
    # device is our scsi device (disk or cdrom)
    for x in device.scsi_bus.targets:
        # is this a pci-scsi adapter?
        if cli.instance_of(x[1], "pci_device"):
            for y in x[1].pci_bus.pci_devices:
                if y[2] == x[1]:
                    pci_bus = 0 # don't really know how to detect this
                    pci_slot = y[0]
                    pci_function = y[1]
    scsi_id = device.scsi_target
    scsi_lun = 0
    # set the interface path in the result buffer
    interface_path = pack("=4BI", pci_bus, pci_slot, pci_function, 0, 0)
    # set the device path in the result buffer
    device_path = pack("=HQHI", scsi_id, scsi_lun, 0, 0)
    # write back the result buffer
    ia64_fw_write_struct(cpu, pb, "=2H3IQHIH2BH4s8s8s16sBB", (
        30,         # maximum buffer length
        0,          # flags
        geometry[0],
        geometry[1],
        geometry[2],
        geometry[0] * geometry[1] * geometry[2],
        bytes_per_sector, # bytes per sector
        0xFFFFFFFF, # dpte
        0x0BEDD, # key
        44, # length
        0, # reserved
        0, # reserved,
        "PCI ", # host bus type
        "SCSI    ", # interface type
        interface_path,
        device_path,
        0,
        0
        ))
    # setup register values for successful exit
    regs[0] = 0
    regs[8] = regs[8] & 0xFFFFFFFE
    ia64_fw_write_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ", tuple(regs))


# ---------------------------------------------------------------------------
#
#  int13_get_drive_parameters
#

def ia64_fw_int13_get_drive_parameters(foo, cpu, bar):
    regs = list(ia64_fw_read_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ"))
    dl = regs[2] & 0xFF
    if dl >= 0x80 and dl < (0x80 + len(ia64_fw_get_scsi_disks())):
        device = ia64_fw_get_scsi_disks()[dl - 0x80]
        geometry = device.geometry;
        print "int13_get_drive_parameters: %s" % device.name
        regs[0] = 0
        regs[10] = 0
        regs[11] = 0
        regs[8] = regs[8] & 0xFFFFFFFE
    elif dl >= 0xE0 and dl < (0xE0 + len(ia64_fw_get_scsi_cdroms())):
        device = ia64_fw_get_scsi_cdroms()[dl - 0xE0]
        geometry = [1, 1, 1]
        print "int13_get_drive_parameters: %s" % device.name
        regs[0] = 0
        regs[10] = 0
        regs[11] = 0
        regs[8] = regs[8] & 0xFFFFFFFE        
    else:
        regs[0] = 0x0700        
        regs[8] = regs[8] | 1
    ia64_fw_write_struct(cpu, read_reg(cpu, "r32"), "=IIIIIIIIIIHHHHHHIQ", tuple(regs))





def ia64_fw_install_magic_call(fnc, num):
    SIM_hap_add_callback_index("Core_Magic_Instruction", fnc, None, num)

ia64_fw_install_magic_call(ia64_fw_salcb_getmediainfo, 0xff402)
ia64_fw_install_magic_call(ia64_fw_int13_get_drive_parameters, 0xff508)
ia64_fw_install_magic_call(ia64_fw_edd_check_extensions_present, 0xff600)
ia64_fw_install_magic_call(ia64_fw_edd_extended_read, 0xff601)
ia64_fw_install_magic_call(ia64_fw_edd_extended_write, 0xff602)
ia64_fw_install_magic_call(ia64_fw_edd_get_device_parameters, 0xff607)


# -----------------------------------------------------------------------------------
#
#

# Utilities for EFI

guids = {
    "5B1B31A1-9562-11D2-8E3F-00A0C969723B" : "LOADED_IMAGE_PROTOCOL",
    "09576E91-6D3F-11D2-8E39-00A0C969723B" : "DEVICE_PATH_PROTOCOL",
    "E0C14753-F9BE-11D2-9A0C-0090273FC14D" : "DEVICE_PATH_MESSAGING_PC_ANSI",
    "DFA66065-B419-11D3-9A2D-0090273FC14D" : "DEVICE_PATH_MESSAGING_VT_100",
    "AF6AC311-84C3-11D2-8E3C-00A0C969723B" : "DEVICE_IO_PROTOCOL",
    "387477C1-69C7-11D2-8E39-00A0C969723B" : "SIMPLE_INPUT_PROTOCOL",
    "387477C2-69C7-11D2-8E39-00A0C969723B" : "SIMPLE_TEXT_OUTPUT_PROTOCOL",
    "964E5B21-6459-11D2-8E39-00A0C969723B" : "BLOCK_IO_PROTOCOL",
    "CE345171-BA0B-11D2-8E4F-00A0C969723B" : "DISK_IO_PROTOCOL",
    "964E5B22-6459-11D2-8E39-00A0C969723B" : "SIMPLE_FILE_SYSTEM_PROTOCOL",
    "09576E92-6D3F-11D2-8E39-00A0C969723B" : "EFI_FILE_INFO_ID",
    "09576E93-6D3F-11D2-8E39-00A0C969723B" : "EFI_FILE_SYSTEM_INFO_ID",
    "DB47D7D3-FE81-11D3-9A35-0090273FC14D" : "EFI_FILE_SYSTEM_VOLUME_LABEL_ID",
    "56EC3091-954C-11D2-8E3F-00A0C969723B" : "LOAD_FILE_PROTOCOL",
    "BB25CF6F-F1D4-11D2-9A0C-0090273FC1FD" : "SERIAL_IO_PROTOCOL",
    "1D85CD7F-F43D-11D2-9A0C-0090273FC14D" : "UNICODE_COLLATION_PROTOCOL",
    "03C4E603-AC28-11D3-9A2D-0090273FC14D" : "EFI_PXE_BASE_CODE_PROTOCOL",
    "245DCA21-FB7B-11D3-8F01-00A0C969723B" : "EFI_PXE_BASE_CODE_CALLBACK_PROTOCOL",
    "A19832B9-AC25-11D3-9A2D-0090273FC14D" : "EFI_SIMPLE_NETWORK_PROTOCOL",
    "E18541CD-F755-4F73-928D-643C8A79B229" : "EFI_NETWORK_INTERFACE_IDENTIFIER_PROTOCOL",
    "8BE4DF61-93CA-11D2-AA0D-00E098032B8C" : "EFI_GLOBAL_VARIABLE",

    "82F86881-282B-11D4-BC7D-0080C73C8881" : "ADAPTER_DEBUG_PROTOCOL",
    "0E3D6310-6FE4-11d3-BB81-0080C73C8881" : "BGA_CLASS_DRIVER_PROTOCOL",
    
    }

def guid_at(address):
    cpu, name = cli.get_cpu()
    raw = memobj(cpu).memory[[address, address + 16]]
    cooked = ("%02X%02X%02X%02X-%02X%02X-%02X%02X-%02X%02X-%02X%02X%02X%02X%02X%02X" %
              (raw[0], raw[1], raw[2],  raw[3],  raw[4],  raw[5],  raw[6],  raw[7],
               raw[8], raw[9], raw[10], raw[11], raw[12], raw[13], raw[14], raw[15]))
    return (cooked, guids.get(cooked))
    


def get_symbol_map(file):
    symbols = {}
    try:
        f = open(SIM_lookup_file(file))
        for l in f.readlines():
            a = l.split()
            if len(a) >= 4 and a[0][4] == ":" and a[2][0] == "0":
                symbols[a[1]] = int(a[2], 16)
    except:
        return {}
    return symbols

def read_word(address):
    return read_bytes(address, 2)[0]

def read_wstring(address):
    c = read_word(address)
    if c != 0:     
        return chr(c) + read_wstring(address + 2)
    else:
        return ""

def populate_symtable(symtab):
    syms = []
    efi_symbols = get_symbol_map("Sal64.map")
    for sym in efi_symbols.keys():
        syms.append([sym[1:], 0x11, efi_symbols[sym], 0])
    symtab.symbol_list["Sal64.exe"] = syms

def break_on_symbol(symbol, hap_handler = None):
    efi_symbols = get_symbol_map("Sal64.map")
    print "Trapping symbol %s" % symbol
    cpu,_ = cli.get_cpu()
    bp_id = SIM_breakpoint(cpu.physical_memory,
                           Sim_Break_Physical, 4, efi_symbols[symbol], 1, 0)
    if hap_handler:
        hap = SIM_hap_add_callback_index("Core_Breakpoint", hap_handler, None, bp_id)


if not "trace_efi_output" in dir():
    trace_efi_output = 1

#def _DbgOut(dummy1, dummy2, bp_id, dummy3, dummy4):
#    global trace_efi_output
#    if not trace_efi_output:
#        return
#    cpu,_ = cli.get_cpu()
#    str = read_wstring(read_reg(cpu, "r33"))
#    for ln in str.split("\n"):
#        if ln != "":
#            pr("EFI: %s\n" % ln)
#    return 0

# def DbgAssert(dummy1, dummy2, bp_id, dummy3, dummy4):
#     cpu,_ = cli.get_cpu()
#     print "EFI assertion: %s:%d:%s" % (read_string(read_reg(cpu, "r32")),
#                                         read_reg(cpu, "r33"),
#                                         read_string(read_reg(cpu, "r34")))
#     SIM_break_simulation("EFI asssertion")

#break_on_symbol("._DbgOut", _DbgOut)
#break_on_symbol(".DbgAssert")


# read disk image
def magic_disk(data, cpu, exc):
    cpu,_ = cli.get_cpu()
    mem = cpu.physical_memory
    buf = read_reg(cpu, "r32")
    start = read_reg(cpu, "r33")
    count = read_reg(cpu, "r34")
    print "copying data from disk image"

    addr = buf
    start = 0x0001000000000000L + start * 512
    while count:
        # addr = SIM_logical_to_physical(cpu, 1, buf)
        # print "0x%x -> 0x%x (0x%x)" % (start, addr, buf)
        mem.memory[[addr, addr+511]] = mem.memory[[start, start+511]]
        addr += 512
        start += 512
        count -= 1

    # SIM_break_simulation("disk magic")

hap = SIM_hap_add_callback_index("Core_Magic_Instruction", magic_disk, None, 0xffffc)


# ============================================================================

# write a list of bytes
def write_bytes(address, bytes):
    SIM_current_processor().physical_memory.memory[[address, address + len(bytes) - 1]] = bytes

def read_uint64(address):
    word = read_bytes(address, 8)
    return (long(word[7]) << 56) | (long(word[6]) << 48) | (long(word[5]) << 40) | (long(word[4]) << 32) | (long(word[3]) << 24) | (long(word[2]) << 16) | (long(word[1]) << 8) | long(word[0])

def write_uint64(addr, val):
    b = []
    for i in range(0, 8):
        b.append(val >> i * 8 & 0xFF)
    write_bytes(addr, b)

def read_uint32(address):
    word = read_bytes(address, 4)
    return (long(word[3]) << 24) | (long(word[2]) << 16) | (long(word[1]) << 8) | long(word[0])

def write_uint32(addr, val):
    b = []
    for i in range(0, 4):
        b.append(val >> i * 4 & 0xFF)
    write_bytes(addr, b)

def read_uint16(address):
    word = read_bytes(address, 2)
    return (long(word[1]) << 8) | long(word[0])


def efi_memory_map_cmd():
    efi_symbols = get_symbol_map("Sal64.map")
    memory_map = efi_symbols["MemoryMap"]
    link = read_uint64(memory_map)
    print "map 0x%x" % memory_map
    print "link 0x%x" % link
    i = 0
    while link != memory_map:
        if read_uint64(link - 8) != 0x70616d6d:
            print "illegal memory map"
            break
        else:
            print "entry %d:" % i
            print "           Start: 0x%x" % read_uint64(link + 24)
            print "             End: 0x%x" % read_uint64(link + 32)
            print "    VirtualStart: 0x%x" % read_uint64(link + 40)
            print ""
            i += 1
            link = read_uint64(link)
    

#new_command("efi-memory-map", efi_memory_map_cmd,
#            [],
#            type  = "efi commands",
#            short = "view the EFI memory map",
#            doc = """
#Set the syscall trace mode.
#""")


# ============================================================================


def realloc_ptr(map, addr):
    # what's the page size?
    ps = 4 * 1024
    # go through the map and try to find a descriptor that matches
    for i in range(0, len(map)):
        if addr >= map[i][1] and addr < (map[i][1] + map[i][3] * ps):
            return addr - map[i][1] + map[i][2]
    return addr

def reloc(virtual_map):
    reloc_section = 0x5c2000
    reloc_size = 0x381a
    image_base = 0x400000
    x = reloc_section
    while x < (reloc_section + reloc_size):
        block_start = x
        page_rva    = read_uint32(x); x += 4
        block_size  = read_uint32(x); x += 4
        while x < (block_start + block_size):
            fixup_entry  = read_uint16(x); x += 2
            fixup_type   = fixup_entry >> 12 & 0xF
            fixup_offset = fixup_entry & 0xFFF
            if fixup_type == 0xA:
                addr = image_base + page_rva + fixup_offset
                write_uint64(addr, realloc_ptr(virtual_map, read_uint64(addr)))
            else:
                print "*** unknown fixup type: %d" % fixup_type


def realloc_efi(foo, bar, gurgel):
    verbose = 0
    cpu,_ = cli.get_cpu()
    mem = cpu.physical_memory
    map_size  = read_reg(cpu, "r32")
    desc_size = read_reg(cpu, "r33")
    memmap    = read_reg(cpu, "r34")
    # load memory descriptors for this virtual mapping
    if verbose:
        pr("Reallocating EFI according to memory map:\n")
    virtual_map = []
    for i in range(0, map_size, desc_size):
        desc = []
        for j in range(0, desc_size, 8):
            desc.append(read_uint64(memmap + i + j))
        if verbose:
            pr("+%-5d: Type          = 0x%016x\n" % (i, desc[0]))
            pr("         PhysicalStart = 0x%016x\n" % (desc[1]))
            pr("         VirtualStart  = 0x%016x\n" % (desc[2]))
            pr("         NumberOfPages = 0x%016x\n" % (desc[3]))
            pr("         Attribute     = 0x%016x\n" % (desc[4]))
        virtual_map.append(desc)
    reloc(virtual_map)

hap = SIM_hap_add_callback_index("Core_Magic_Instruction", realloc_efi, None, 0xffffb)
