# MODULE: x86-components
# CLASS: x86-system
# CLASS: x86-apic-system
# CLASS: x86-separate-mem-io-system
# CLASS: x86-apic-bus-system
# CLASS: x86-e7520-system
# CLASS: i386-cpu
# CLASS: i486sx-cpu
# CLASS: i486dx2-cpu
# CLASS: pentium-cpu
# CLASS: pentium-mmx-cpu
# CLASS: pentium-pro-cpu
# CLASS: pentium-ii-cpu
# CLASS: pentium-iii-cpu
# CLASS: pentium-m-cpu
# CLASS: pentium-4-cpu
# CLASS: xeon-prestonia-cpu
# CLASS: pentium-4e-cpu
# CLASS: pentium-4e-2ht-cpu
# CLASS: pentium-4e-4ht-cpu
# CLASS: x86-hammer-cpu
# CLASS: opteron-cpu
# CLASS: north-bridge-443bx
# CLASS: north-bridge-443bx-agp
# CLASS: north-bridge-875p
# CLASS: north-bridge-e7520
# CLASS: north-bridge-k8
# CLASS: legacy-pc-devices

import os, time
from sim_core import *
from components import *
from base_components import standard_pc_devices_component
from base_components import find_device, get_highest_2exp
from x86_cmos_info import register_cmos_commands


### X86 Legacy System


class x86_system_component(component_object):
    classname = 'x86-system'
    basename = 'system'
    description = ('The "x86-system" component represents a legacy ISA based '
                   'x86 system with a single processor.')
    connectors = {
        'cpu0'     : {'type' : 'x86-processor', 'direction' : 'down',
                      'empty_ok' : False, 'hotplug' : False, 'multi' : False},
        'chipset'   : {'type' : 'x86-chipset', 'direction' : 'down',
                       'empty_ok' : 1, 'hotplug' : False, 'multi' : False},
        'reset'     : {'type' : 'x86-reset-bus', 'direction' : 'down',
                       'empty_ok' : 1, 'hotplug' : False, 'multi' : False}}
    bios = None
    cpus = []
    
    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)

        self.break_on_reboot = False

        self.use_acpi = 0
        self.do_create_acpi_tables = 1
        self.do_init_cmos = 1
        self.use_shadow = 1
        self.use_hostfs = 1
        self.do_init_mtrrs = 1
        self.linux_acpi_bug_workaround = 1
        self.map_ram = 1
        self.disable_ap_cpus = 1

    def get_memory_megs(self, idx):
        return self.memory_megs

    def set_memory_megs(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if val < 1:
            SIM_attribute_error('Unsupported memory size')
            return Sim_Set_Illegal_Value
        self.memory_megs = val
        return Sim_Set_Ok

    def get_rtc_time(self, idx):
        return self.tod

    def set_rtc_time(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        try:
            time.strptime(val, '%Y-%m-%d %H:%M:%S %Z')
        except Exception, msg:
            SIM_attribute_error(str(msg))
            return Sim_Set_Illegal_Value
        self.tod = val
        return Sim_Set_Ok

    def get_bios(self, idx):
        return self.bios

    def set_bios(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if self.instantiated:
            # allow checkpoint to be loaded, bios isn't used once instantiated
            self.bios = val
            return Sim_Set_Ok
        if not SIM_lookup_file(val):
            # TODO: use exception
            print 'Could not locate bios file %s' % val
            return Sim_Set_Illegal_Value
        self.bios_size = os.stat(SIM_lookup_file(val)).st_size

        # Default bios contains trailing garbage
        if val[:10] == 'rombios-2.':
            self.bios_size = 64 * 1024
        if self.bios_size > 0x100000:
            # TODO: use exception
            print 'BIOS size %d is larger than max (%d)' % (
                self.bios_size, 0x100000)
            return Sim_Set_Illegal_Value
        self.bios = val
        return Sim_Set_Ok

    def add_objects(self):
        self.cpus_per_slot = []

        # RAM
        self.o.dram_space = pre_obj('dram$', 'memory-space')
        self.o.ram_image = pre_obj('ram$_image', 'image')
        self.o.ram_image.size = self.memory_megs * 1024 * 1024
        self.o.ram = pre_obj('ram$', 'ram')
        self.o.ram.image = self.o.ram_image
        self.o.dram_space.map = [[0, self.o.ram, 0, 0,
                                  self.memory_megs * 1024 * 1024]]

        self.o.reset_bus = pre_obj('reset$', 'x86-reset-bus')
        self.o.reset_bus.reset_targets = []
        self.o.conf = pre_obj('conf$', 'pc-config')
        
        if self.bios:
            self.o.rom_image = pre_obj('rom$_image', 'image')
            self.o.rom_image.size = self.bios_size
            self.o.rom = pre_obj('rom$', 'rom')
            self.o.rom.image = self.o.rom_image
            
        if self.use_hostfs:
            self.o.hfs = pre_obj('hfs$', 'hostfs')

        # Port space
        self.o.port_space = pre_obj('port_mem$', 'port-space')
        self.o.port_space.map = [
            [0xfff0, self.o.conf, 0,     0, 1],
            [0xfff1, self.o.conf, 1,     0, 1]]

        # Northbridge memory-space
        self.o.phys_mem = pre_obj('phys_mem$', 'memory-space')
        self.o.phys_mem.map = []

        # Southbridge memory-space
        self.o.pci_mem = pre_obj('pci_mem$', 'memory-space')
        self.o.pci_mem.map = []

        self.o.phys_mem.default_target = [self.o.pci_mem, 0, 0, None]
        
        if self.bios:
            self.o.pci_mem.map += [
                [0x100000000 - self.bios_size, self.o.rom, 0, 0,
                 self.bios_size]]
        if self.use_hostfs:
            self.o.pci_mem.map += [
                [0x0ffe81000, self.o.hfs,    0, 0, 0x10]]
            
        if self.use_shadow:
            self.o.shadow = pre_obj('core$', 'pc-shadow')
            self.o.shadow_mem = pre_obj('shadow$', 'memory-space')
            self.o.shadow_mem.map = [[0x100000,
                                      self.o.dram_space, 0, 0, 0x100000]]
            self.o.port_space.map += [
                [0xfff4, self.o.shadow, 0,     0, 1],
                [0xfff5, self.o.shadow, 0,     1, 1]]
        if self.bios:
            self.o.pci_mem.map += [
                [0x000f0000, self.o.rom, 0, self.bios_size - 0x10000, 0x10000]]
        if self.linux_acpi_bug_workaround:
            self.o.rom1_image = pre_obj('rom$_image', 'image')
            self.o.rom1_image.size = 0x10000
            self.o.rom1 = pre_obj('rom$', 'rom')
            self.o.rom1.image = self.o.rom1_image
            self.o.pci_mem.map += [
                [0x000e0000, self.o.rom1, 0, 0, 0x10000]]

        # Map RAM
        if self.map_ram and self.bios:
            ram_map = [[0x000000000, self.o.dram_space,    0, 0, 0xa0000]]
            high_mem = 4096 - 256
            if self.memory_megs > high_mem:
                high_mem *= 1024 * 1024
                highest = (self.memory_megs * 1024 * 1024) - high_mem
                ram_map += [
                    [0x000100000, self.o.dram_space, 0, 0x100000, high_mem,
                     None, 0],
                    [0x100000000, self.o.dram_space, 0, high_mem, highest,
                     None, 0]]
            else:
                megs = (self.memory_megs - 1) * 1024 * 1024
                ram_map += [
                    [0x000100000, self.o.ram, 0, 0x100000, megs,     None, 0]]
            self.o.phys_mem.map += ram_map
        elif self.map_ram and not self.bios:
            ram_map = [[0x00000000, self.o.dram_space, 0, 0, self.memory_megs * 1024 * 1024]]
            self.o.phys_mem.map += ram_map

    def add_connector_info(self):
        self.connector_info['cpu0'] = [0,
                                       self.o.phys_mem,
                                       self.o.port_space]
        self.connector_info['chipset'] = [self.o.phys_mem,
                                          self.o.pci_mem,
                                          self.o.port_space]
        if "dram_space" in dir(self.o):
            self.connector_info['chipset'] += [ self.o.dram_space]
        else:
            self.connector_info['chipset'] += [None]
        self.connector_info['reset'] = [self.o.reset_bus]

    def load_bios(self):
        # Write the bios into the ROM area, so that checkpoints not
        # depend on the BIOS file being available all time.
        f = open(SIM_lookup_file(self.bios), "rb")
        base = 0x100000000 - self.bios_size
        data = map(ord, f.read(self.bios_size))
        self.o.pci_mem.iface.memory_space.write(self.o.pci_mem, None,
                                                base, tuple(data), 1)
        f.close()

    def set_cmos_info(self):
        self.rtc = find_device(self.o.port_space, 0x70)
        if not self.rtc:
            #print "CMOS device not found - can not write information."
            return
        # set nvram info
        eval_cli_line('%s.cmos-init' % self.obj.name)
        eval_cli_line('%s.cmos-base-mem 640' % self.obj.name)
        eval_cli_line('%s.cmos-extended-mem %d' %
                      (self.obj.name, self.memory_megs - 1))
        m = re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', self.tod)
        eval_cli_line(('%s.set-date-time '
                       + 'year=%s month=%s mday=%s '
                       + 'hour=%s minute=%s second=%s')
                      % ((self.rtc.name,) + m.groups()))
        eval_cli_line('%s.cmos-boot-dev C' % self.obj.name)
        flp = find_device(self.o.port_space, 0x3f2)
        if flp:
            if len(flp.drives):
                eval_cli_line('%s.cmos-floppy A "1.44"' % self.obj.name)
            if len(flp.drives) > 1:
                eval_cli_line('%s.cmos-floppy B "1.44"' % self.obj.name)
        ide0 = find_device(self.o.port_space, 0x1f0)
        if ide0 and ide0.master:
            size = ide0.master.disk_sectors
            # Our BIOS does LBA directly: set sectors 63 and heads to x * 16
            bios_S = 63
            # The following would probably work if our BIOS had support
            # for proper 'translation'. Now it seems to fail.
            #if size < 504 * 1024 * 1024 / 512:
            #    bios_H = 16
            #elif size < 1008 * 1024 * 1024 / 512:
            #    bios_H = 32
            #elif size < 2016 * 1024 * 1024 / 512:
            #    bios_H = 64
            #elif size < 4032 * 1024 * 1024 / 512:
            #    bios_H = 128
            if size < 4032 * 1024 * 1024 / 512:
                bios_H = 16
            else:
                # 255 is de facto standard since DOS and early Windows can't
                # handle 256 heads, this is known as the 4GB limit
                bios_H = 255
            bios_C = size / (bios_H * bios_S)
            #if bios_C * bios_H * bios_S != size:
            #    print 'Disk size can not be translated to exact BIOS CHS'
            #    print 'Using CHS: %d %d %d' % (bios_C, bios_H, bios_S)
            eval_cli_line('%s.cmos-hd C %d %d %d' % (self.obj.name,
                                                     bios_C, bios_H, bios_S))

    def calc_mtrr_mask(self, classname, size):
	return (~(size - 1)
                & ((1 << sim.classes[classname].classattrs.physical_bits) - 1))

    def set_mtrr(self, cpu):
        if not SIM_class_has_attribute(cpu.classname, 'mtrr_def_type'):
            return
        cpu.mtrr_def_type = 0xc00
        megs_remaining = self.memory_megs
        next_mtrr = 0
        next_base = 0
        while megs_remaining:
            if next_mtrr > 7:
                print ('Warning: %d megabytes of memory not mapped by '
                       'MTRRs' % megs_remaining)
                break
            this_size = get_highest_2exp(megs_remaining)
            exec 'cpu.mtrr_base%d = next_base | 0x06' % next_mtrr
            mask = self.calc_mtrr_mask(cpu.classname, this_size * 1024 * 1024)
            exec 'cpu.mtrr_mask%d = mask | 0x800' % next_mtrr
            megs_remaining = megs_remaining - this_size
            next_base = next_base + this_size * 1024 * 1024
            next_mtrr += 1
        cpu.mtrr_fix_64k_00000 = 0x0606060606060606
        cpu.mtrr_fix_16k_80000 = 0x0606060606060606
        cpu.mtrr_fix_16k_a0000 = 0
        cpu.mtrr_fix_4k_c0000 = 0
        cpu.mtrr_fix_4k_c8000 = 0
        cpu.mtrr_fix_4k_d0000 = 0
        cpu.mtrr_fix_4k_d8000 = 0
        cpu.mtrr_fix_4k_f0000 = 0
        cpu.mtrr_fix_4k_f8000 = 0

        
    def instantiation_done(self):
        component_object.instantiation_done(self)
        for i in range(len(self.cpus)):
            self.cpus[i] = SIM_get_object(self.cpus[i].name)

        if self.bios:
            self.load_bios()
        conf.sim.handle_outside_memory = 1
        if self.do_init_cmos:
            self.set_cmos_info()

        self.install_reset_callback(self.cpus[0])

    def add_cpu(self, id, cpu):
        if len(self.cpus_per_slot) <= id:
            self.cpus_per_slot += [None] * (id + 1 - len(self.cpus_per_slot))
        if self.cpus_per_slot[id] == None:
            self.cpus_per_slot[id] = [cpu]
        else:
            self.cpus_per_slot[id].append(cpu)
        self.cpus = []
        for l in self.cpus_per_slot:
            if l:
                for c in l:
                    self.cpus.append(c)
        self.o.reset_bus.reset_targets = self.cpus
        cpu.cpu_group = self.o.reset_bus

    def connect_x86_processor(self, connector, cpu):
        self.add_cpu(0, cpu)

    def connect_x86_chipset(self, connector):
        if self.use_shadow:
            # move all mappings to shadow memory
            self.o.shadow_mem.map += ([x for x in self.o.pci_mem.map
                                       if x[0] >= 0xc0000 and x[0] < 0x100000])
            self.o.pci_mem.map = [x for x in self.o.pci_mem.map
                                  if x[0] < 0xc0000 or x[0] >= 0x100000]
            self.o.pci_mem.map += ([
                [0x0000c0000, self.o.shadow, 0, 0, 0x40000,
                 self.o.shadow_mem, 1]])
            
    def connect_x86_reset_bus(self, connector):
        pass

    def get_clock(self):
        return self.cpus[0]

    def get_processors(self):
        return self.cpus

    def set_processors(self, cpus):
        self.cpus = cpus

    def on_reset_hap(self, udata, cpu, hard_reset):
        self.on_reboot()

    def on_triple_fault(self, udata, cpu, exc_no):
        self.on_reboot()

    def on_reboot(self):
        SIM_log_message(self.obj, 1, 0, Sim_Log_Info,
                        "System rebooted. Note that the reboot support in"
                        " Simics is experimental at this point.")
        if self.break_on_reboot:
            SIM_log_message(self.obj, 1, 0, Sim_Log_Info,
                "You will probably want to save the disk content and continue"
                " from that in another Simics session.\nTo disable breaking,"
                " change the break_on_reboot attribute.")
            SIM_break_simulation("Break on system reboot")

    def install_reset_callback(self, cpu):
        SIM_hap_add_callback_obj("X86_Processor_Reset", cpu, 0,
                                 self.on_reset_hap, None)
        excno = cpu.iface.exception.get_number(cpu, "Triple_Fault")
        SIM_hap_add_callback_obj_index("Core_Exception", cpu, 0,
                                       self.on_triple_fault, None,
                                       excno)

    def set_break_on_reboot(self, val, idx):
        self.break_on_reboot = val
        return Sim_Set_Ok

    def get_break_on_reboot(self, idx):
        return self.break_on_reboot

    def finalize_instance(self):
        component_object.finalize_instance(self)
        if self.instantiated:
            for connector, cpu, dst_conn in self.connections:
                if connector == 'cpu0':
                    break
            else:
                SIM_log_message(self.obj, 1, 0, Sim_Log_Error,
                                "No cpu to install reset callback on!")
                return
            cpu = cpu.object_list['cpu[0]']
            self.install_reset_callback(cpu)

system_attributes = [
    ['memory_megs', Sim_Attr_Required, 'i',
     'The amount of RAM in megabytes on the processor board.'],
    ['rtc_time', Sim_Attr_Required, 's',
     'The date and time of the Real-Time clock.'],
    ['break_on_reboot', Sim_Attr_Optional, 'b',
     'If true, the simulation will stop when machine is rebooted.']]

bios_attribute = [['bios', Sim_Attr_Optional, 's',
                   'The x86 BIOS file to use.']]

apic_attribute = [['apic_id_list', Sim_Attr_Optional, '[i*]',
                   'The APIC id to use for each processor']]

register_component_class(x86_system_component,
                         system_attributes + bios_attribute,
                         top_level = True)
register_cmos_commands(x86_system_component.classname)


### X86 Apic Bus System


class x86_apic_bus_system_component(x86_system_component):
    classname = 'x86-apic-bus-system'
    basename = 'system'
    description = ('The "x86-apic-bus-system" component represents a '
                   'multi-processor capable x86 system with up to 255 cpus.')
    connectors = x86_system_component.connectors.copy()
    del connectors['cpu0']    
    connectors['io-apic'] = {
        'type' : 'apic-bus', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi' : True}
    for i in range(255):
        connectors['cpu%d' % i] = {
            'type' : 'x86-apic-processor', 'direction' : 'down',
            'empty_ok' : i != 0, 'hotplug' : False, 'multi' : False}

    def __init__(self, parse_obj):
        x86_system_component.__init__(self, parse_obj)
        self.linux_acpi_bug_workaround = 0
        self.use_acpi = 0
        self.use_hostfs = 0
        self.use_shadow = 0
        self.do_create_acpi_tables = 0
        self.do_init_cmos = 0
        self.do_init_mtrrs = 1
        self.map_ram = 0
        self.disable_ap_cpus = 1
        # default APIC id list that respects more or less Intel's manuals
        self.apic_id_list = [ 0, 1, 6, 7, 4, 5, 2, 3,
                              8, 9,14,15,12,13,10,11]
        
    def add_connector_info(self):
        x86_system_component.add_connector_info(self)
        self.connector_info['io-apic'] = [self.o.apic_bus]
        if "dram_space" in dir(self.o):
            self.connector_info['io-apic'] += [ self.o.dram_space]
        for i in range(255):
            self.connector_info['cpu%d' % i] = [i,
                                                self.o.phys_mem,
                                                self.o.port_space,
                                                self.o.apic_bus]

    def connect_x86_apic_processor(self, connector, cpus):
        id = self.connector_info[connector][0]
        for i in range(len(cpus)):
            self.add_cpu(id, cpus[i])
            if self.do_init_mtrrs:
                self.set_mtrr(cpus[i])

    def connect_apic_bus(self, connector):
        pass

    def add_objects(self):
        x86_system_component.add_objects(self)
        self.o.apic_bus = pre_obj('apic_bus$', 'apic-bus')
        self.o.apic_bus.apics = []
        self.o.apic_bus.ioapic = []

    def set_apic_id_list(self, val, idx):
        self.apic_id_list = val
        return Sim_Set_Ok

    def get_apic_id_list(self, idx):
        return self.apic_id_list

    def instantiation_done(self):
        x86_system_component.instantiation_done(self)
        apics_list = []
        la = len(self.apic_id_list)
        for i in range(len(self.cpus)):
            apics_list += [self.cpus[i].apic]
            a_id = (i/la)*la + self.apic_id_list[i % la]
            self.cpus[i].apic.apic_id = a_id
            try:
                self.cpus[i].cpuid_physical_apic_id = a_id
            except:
                pass
        self.o.apic_bus.apics = apics_list
        i = len(self.cpus)
        for ioapic in self.o.apic_bus.ioapic:
            try:
                ioapic.ioapic_id = ((i/la)*la + self.apic_id_list[i % la]) << 24
            except:
                ioapic.ioapic_id = i << 24
            i = i + 1
        self.cpus[0].bsp = 1
        if self.disable_ap_cpus:
            for c in self.cpus[1:]:
                c.activity_state = 3 # waiting for SIPI
                SIM_disable_processor(c)

register_component_class(
    x86_apic_bus_system_component,
    system_attributes,
    top_level = True)
register_cmos_commands(x86_apic_bus_system_component.classname)


### X86/APIC Multipro System


class x86_apic_system_component(x86_apic_bus_system_component):
    classname = 'x86-apic-system'
    basename = 'system'
    description = ('The "x86-apic-system" component represents a '
                   'multi-processor capable x86 system with up to 255 cpus.')
    connectors = x86_apic_bus_system_component.connectors.copy()
    del connectors['io-apic']
    connectors['interrupt'] = {
        'type' : 'sb-interrupt', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    def __init__(self, parse_obj):
        x86_apic_bus_system_component.__init__(self, parse_obj)
        self.linux_acpi_bug_workaround = 1
        self.use_hostfs = 1
        self.use_shadow = 1
        self.do_create_acpi_tables = 1
        self.do_init_cmos = 1
        self.do_init_mtrrs = 1
        self.map_ram = 1
        self.use_acpi = 1
        self.disable_ap_cpus = 1

    def get_acpi(self, idx):
        return self.use_acpi

    def set_acpi(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.use_acpi = val
        return Sim_Set_Ok

    def add_objects(self):
        x86_apic_bus_system_component.add_objects(self)
        self.o.ioapic = pre_obj('ioapic$', 'io-apic')
        self.o.ioapic.apic_bus = self.o.apic_bus
        self.o.ioapic.ioapic_id = 0
        self.o.apic_bus.ioapic = [self.o.ioapic]
        self.o.pci_mem.map += [
             [0xfec00000, self.o.ioapic, 0, 0, 0x20]]

    def add_connector_info(self):
        x86_apic_bus_system_component.add_connector_info(self)
        for i in range(255):
            self.connector_info['cpu%d' % i] = [i,
                                                self.o.phys_mem,
                                                self.o.port_space,
                                                self.o.apic_bus]
        self.connector_info['interrupt'] = [self.o.apic_bus,
                                            self.o.ioapic]

    def connect_sb_interrupt(self, connector, pic):
        pass

    def instantiation_done(self):
        x86_apic_bus_system_component.instantiation_done(self)
        # create the ACPI tables if necessary
        if self.do_create_acpi_tables:
            import x86_acpi_setup
            rsdp_base = iff(self.linux_acpi_bug_workaround, 0xef000, 0)
            bios_params = x86_acpi_setup.bios_params_holder()
            if self.bios and self.bios.endswith("rombios-2.68"):
                # this BIOS have larger data area and other offsets
                bios_params.ebda_base = 0x9f800
                bios_params.rsdp_offs = 0x400
                bios_params.high_desc_offs = 0x424
                bios_params.nvr_desc_offs = 0x438
                bios_params.reclaim_desc_offs = 0x44c
                bios_params.high_desc_offs2 = 0x460
                bios_params.smem_offs = 0x488
            x86_acpi_setup.create_acpi_tables(
                build_acpi_tables = self.use_acpi,
                cpu_list = self.cpus,
                megs = self.memory_megs,
                ioapic_id = self.o.apic_bus.ioapic[0].ioapic_id >> 24,
                user_rsdp_address = rsdp_base,
                bios_params = bios_params)

register_component_class(
    x86_apic_system_component,
    system_attributes
    + bios_attribute
    + [['acpi', Sim_Attr_Optional, 'b',
        'TRUE if the machine uses ACPI. Default is TRUE.']],
    top_level = True)
register_cmos_commands(x86_apic_system_component.classname)


# X86 Separate APIC System


class x86_separate_apic_system_component(x86_apic_system_component):
    classname = 'x86-separate-mem-io-system'
    basename = 'system'
    description = ('The "x86-separate-mem-io-system" component represents a '
                   'multi-processor capable x86 system with up to 15 cpus.')
    connectors = x86_apic_system_component.connectors.copy()

    def __init__(self, parse_obj):
        x86_apic_system_component.__init__(self, parse_obj)
        self.use_acpi = 0
        self.use_shadow = 0
        self.do_create_acpi_tables = 0
        self.do_init_cmos = 0
        self.do_init_mtrrs = 1
        self.map_ram = 0

    def add_objects(self):
        x86_apic_system_component.add_objects(self)
        self.o.post_log = pre_obj('post$', 'amibios8-post-log')
        self.o.port_space.map += [[0x80, self.o.post_log, 0, 0, 1]]

    def add_cpu(self, id, cpu):
        x86_apic_system_component.add_cpu(self, id, cpu)
        cpu.physical_io = self.o.pci_mem
        cpu.physical_dram = self.o.dram_space
        cpu.physical_memory.default_target = [cpu, 0, 0, self.o.dram_space]
        self.o.pci_mem.default_target = [self.o.dram_space, 0, 0,
                                         self.o.dram_space]

register_component_class(
    x86_separate_apic_system_component,
    system_attributes + bios_attribute,
    top_level = True)
register_cmos_commands(x86_separate_apic_system_component.classname)



# E7520 system component


class x86_e7520_system_component(x86_apic_bus_system_component):
    classname = 'x86-e7520-system'
    basename = 'system'
    description = ('The "x86-e7520-system" component represents a E7520-based '
                   'multi-processor capable system with up to 15 cpus.')
    fm2_callback_called = 0
    fm2_target = 1
    bios_name = ""
    
    def define_bp_targets(self):
        if self.memory_megs == 2048:
            self.fm2_target = 2
        elif self.memory_megs == 4096:
            self.fm2_target = 2
        elif self.memory_megs == 8192:
            self.fm2_target = 4
            
        if self.bios_name == "out_1024":
            # p:0x0000f1d76  wrmsr
            self.fix_cache_start = 0x0000f1d76
            # p:0x0000f1dd2  wrmsr
            self.fix_cache_end   = 0x0000f1dd2
            # p:0x0000f2544  cmp bl,0x0
            self.fix_mem_1       = 0x0000f2544
            # p:0x0000f290e  cmp byte ptr ss:[0x7],0x0
            fix_mem_2       = 0x0000f290e
        elif self.bios_name == "goose-bios":
            # p:0x0000f1f7a  wrmsr
            self.fix_cache_start = 0x0000f1f7a
            # p:0x0000f1fd6  wrmsr
            self.fix_cache_end   = 0x0000f1fd6
            # p:0x0000f2751  cmp bl,0x0
            self.fix_mem_1       = 0x0000f2751
            # p:0x0000f2b1b  cmp byte ptr ss:[0x7],0x0
            self.fix_mem_2       = 0x0000f2b1b
        else:
            print "Unknown BIOS, no patch available"
            self.fix_cache_start = -1
            self.fix_cache_end   = -1
            self.fix_mem_1       = -1
            self.fix_mem_2       = -1

    def fcs_callback(self, dummy, obj, bp, memop):
        cp = self.cpus[0].name
        print "Setting-up fake cache for %s" % (cp)
        eval_cli_line("%s_mem.add-map device = %s_cache_space " % (cp, cp) +
                      "base = 0xE0000 length = 0x2000")

    def fce_callback(self, dummy, obj, bp, memop):
        cp = self.cpus[0].name
        print "Removing fake cache for %s" % (cp)
        eval_cli_line("%s_mem.del-map device = %s_cache_space" % (cp, cp))

    def fm1_callback(self, dummy, obj, bp, memop):
        cpu = self.cpus[0]
        print "Patch memory calibration results (#1) for %s" % (cpu.name)
        cpu.bl = 0

    def fm2_callback(self, dummy, obj, bp, memop):
        cp = self.cpus[0].name
        if self.fm2_callback_called < self.fm2_target:
            print "Patch memory calibration results (#2) for %s" % (cp)
            eval_cli_line("%s_mem.set -l 0xe0007 size = 1 value = 0" % (cp))
            self.fm2_callback_called += 1

    def get_fm2_callback_called(self, idx):
        return self.fm2_callback_called

    def set_fm2_callback_called(self, val, idx):
        self.fm2_callback_called = val
        return Sim_Set_Ok
            
    def set_bp(self):
        pm = self.cpus[0].physical_memory
        if self.fix_cache_start != -1:
            fcs = SIM_breakpoint(pm, 0, 4, self.fix_cache_start, 1, 2)
            SIM_hap_add_callback_index("Core_Breakpoint_Memop",
                                       self.fcs_callback, None, fcs)
        if self.fix_cache_end != -1:
            fce = SIM_breakpoint(pm, 0, 4, self.fix_cache_end, 1, 2)
            SIM_hap_add_callback_index("Core_Breakpoint_Memop",
                                       self.fce_callback, None, fce)
        if self.fix_mem_1 != -1:
            fm1 = SIM_breakpoint(pm, 0, 4, self.fix_mem_1, 1, 2)
            SIM_hap_add_callback_index("Core_Breakpoint_Memop",
                                       self.fm1_callback, None, fm1)
        if self.fix_mem_2 != -1:
            fm2 = SIM_breakpoint(pm, 0, 4, self.fix_mem_2, 1, 2)
            SIM_hap_add_callback_index("Core_Breakpoint_Memop",
                                       self.fm2_callback, None, fm2)

    def set_bios_name(self, val, idx):
        self.bios_name = val
        return Sim_Set_Ok

    def get_bios_name(self, idx):
        return self.bios_name

    def finalize_instance(self):
        x86_apic_bus_system_component.finalize_instance(self)
        if self.instantiated:
            self.define_bp_targets()
            self.set_bp()

    def instantiation_done(self):
        x86_apic_bus_system_component.instantiation_done(self)
        self.define_bp_targets()
        self.set_bp()

register_component_class(
    x86_e7520_system_component,
    system_attributes
    + [['bios_name', Sim_Attr_Optional, 's',
        'The x86 BIOS filename (to set correct breakpoints).']],
    [['fm2_callback_called', Sim_Attr_Optional, 'i',
      'Internal']],
    top_level = True)
register_cmos_commands(x86_e7520_system_component.classname)




### X86 Processor Base Class


class x86_processor_component(component_object):
    connectors = {
        'cache-cpu' : {'type' : 'timing-model', 'direction' : 'down',
                       'empty_ok' : True, 'hotplug' : True, 'multi' : False}}
    connectors['direct-pins'] = {
        'type' : 'x86-pins', 'direction' : 'down',
        'empty_ok' : True, 'hotplug' : False, 'multi' : False}

    def get_cpu_frequency(self, idx):
        return self.freq_mhz

    def set_cpu_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.freq_mhz = val
        return Sim_Set_Ok

    def get_cpi(self, idx):
        try:
            return self.cpi
        except:
            return 1

    def set_cpi(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if not val in (1, 2, 4, 8, 16, 32, 64, 128):
            return Sim_Set_Illegal_Value
        self.cpi = val
        return Sim_Set_Ok

    def __init__(self, parse_obj, cpu_threads = 1):
        component_object.__init__(self, parse_obj)
        self.cpu_threads = cpu_threads
        self.o.space = [None] * cpu_threads
        self.o.cpu = [None] * cpu_threads
        self.o.tlb = [None] * cpu_threads

    def add_objects(self):
        thread_list = []
        for i in range(self.cpu_threads):
            if self.cpu_threads == 1:
                self.o.space[i] = pre_obj('cpu(x)_mem', 'memory-space')
                self.o.cpu[i] = pre_obj('cpu(x)', self.cpuclass)
                self.o.tlb[i] = pre_obj('cpu(x)_tlb', 'x86-tlb')

            else:
                self.o.space[i] = pre_obj('cpu(x)_%d_mem'%i, 'memory-space')
                self.o.cpu[i] = pre_obj('cpu(x)_%d'%i, self.cpuclass)
                self.o.tlb[i] = pre_obj('cpu(x)_%d_tlb'%i, 'x86-tlb')
            thread_list.append(self.o.cpu[i])
            self.o.space[i].map = []
            self.o.cpu[i].processor_number = get_next_cpu_number()
            self.o.cpu[i].freq_mhz = self.freq_mhz
            try:
                self.cpi
                self.o.cpu[i].step_rate = [1, self.cpi, 0]
            except:
                pass
            self.o.cpu[i].physical_memory = self.o.space[i]
            self.o.tlb[i].cpu = self.o.cpu[i]
            self.o.tlb[i].type = "unlimited"
            self.o.cpu[i].tlb = self.o.tlb[i]
        if self.cpu_threads > 1:
            for i in range(self.cpu_threads):
                self.o.cpu[i].threads = thread_list

    def add_connector_info(self):
        if self.cpu_threads == 1:
            self.connector_info['cache-cpu'] = [0, self.o.cpu[0]]
        else:
            for i in range(self.cpu_threads):
                self.connector_info['cache-cpu%d' % i] = [i, self.o.cpu[i]]
        self.connector_info['direct-pins'] = [self.o.cpu]

    def get_cpu_threads(self, idx):
        return self.cpu_threads

    def connect_x86_processor(self, connector, id, mem_space, port_space):
        self.rename_component_objects('%d' % id)
        for i in range(self.cpu_threads):
            self.o.space[i].default_target = [mem_space, 0, 0, None]
            self.o.cpu[i].port_space = port_space

    def connect_x86_pins(self, connector):
        pass

    def connect_timing_model(self, connector, cache):
        id = self.connector_info[connector][0]
        self.o.space[id].timing_model = cache

    def disconnect_timing_model(self, connector):
        id = self.connector_info[connector][0]
        self.o.space[id].timing_model = None


### Legacy X86 Processor


class x86_legacy_processor_component(x86_processor_component):
    connectors = x86_processor_component.connectors.copy()
    connectors['system'] = {
        'type' : 'x86-processor', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['interrupt'] = {
        'type' : 'sb-interrupt', 'direction' : 'down',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}

    def __init__(self, parse_obj):
        x86_processor_component.__init__(self, parse_obj)

    def add_objects(self):
        x86_processor_component.add_objects(self)
        self.o.x87 = pre_obj('x87_exc$', 'x87_exception')
        self.o.x87.irq_level = 13
        self.o.x87.ignne_target = self.o.cpu[0]
        self.o.cpu[0].ferr_target = self.o.x87

    def add_connector_info(self):
        x86_processor_component.add_connector_info(self)
        self.connector_info['system'] = [self.o.cpu[0]]
        self.connector_info['interrupt'] = [self.o.cpu[0], None]

    def connect_sb_interrupt(self, connector, pic):
        self.o.x87.irq_dev = pic

class i386_processor_component(x86_legacy_processor_component):
    classname = 'i386-cpu'
    basename = 'cpu'
    description = ('The "i386-cpu" component represents an Intel 386 '
                   'processor.')
    cpuclass = 'x86-386'

class i486sx_processor_component(x86_legacy_processor_component):
    classname = 'i486sx-cpu'
    basename = 'cpu'
    description = ('The "i486sx-cpu" component represents an Intel 486sx '
                   'processor.')
    cpuclass = 'x86-486sx'

class i486dx2_processor_component(x86_legacy_processor_component):
    classname = 'i486dx2-cpu'
    basename = 'cpu'
    description = ('The "i486dx2-cpu" component represents an Intel 486dx2 '
                   'processor.')
    cpuclass = 'x86-486dx2'

for model in ['i386', 'i486sx', 'i486dx2']:
    register_component_class(
        eval('%s_processor_component' % model),
        [['cpu_frequency', Sim_Attr_Required, 'i',
          'Processor frequency in MHz.'],
         ['cpi', Sim_Attr_Optional, 'i',
          'Cycles per instruction.']])


###  X86/APIC Processor


class x86_apic_processor_component(x86_processor_component):
    connectors = x86_processor_component.connectors.copy()
    connectors['system'] = {
        'type' : 'x86-apic-processor', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    # default APIC is a P4-type apic
    apic_type = "P4"

    def __init__(self, parse_obj, cpu_threads = 1):
        x86_processor_component.__init__(self, parse_obj, cpu_threads)
        self.o.apic = [None] * cpu_threads
        self.apic_freq_mhz = 10

    def get_apic_frequency(self, idx):
        return self.apic_freq_mhz

    def set_apic_frequency(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.apic_freq_mhz = val
        return Sim_Set_Ok

    def add_objects(self):
        x86_processor_component.add_objects(self)
        for i in range(self.cpu_threads):
            if self.cpu_threads == 1:
                self.o.apic[i] = pre_obj('cpu(x)_apic', 'apic')
            else:
                self.o.apic[i] = pre_obj('cpu(x)_%d_apic'%i, 'apic')
            self.o.apic[i].cpu = self.o.cpu[i]
            self.o.apic[i].queue = self.o.cpu[i]
            self.o.apic[i].cpu_bus_divisor = (float(self.freq_mhz)
                                              / self.apic_freq_mhz)
            if self.apic_type == "P4":
                self.o.apic[i].physical_broadcast_address = 255;
                self.o.apic[i].version = 0x14;
                self.o.apic[i].apic_type = "P4"
            elif self.apic_type == "P6":
                self.o.apic[i].physical_broadcast_address = 15;
                self.o.apic[i].version = 0x18;
                self.o.apic[i].apic_type = "P6"
            else:
                raise "Unknown APIC type %s" % self.apic_type
            self.o.cpu[i].apic = self.o.apic[i]
            if self.cpu_threads > 1:
                self.o.cpu[i].cpuid_logical_processor_count = self.cpu_threads
            else:
                self.o.cpu[i].cpuid_logical_processor_count = 0
            self.o.space[i].map += [
                [0xfee00000, self.o.apic[i], 0, 0, 0x4000]]

    def add_connector_info(self):
        x86_processor_component.add_connector_info(self)
        self.connector_info['system'] = [self.o.cpu]

    def connect_x86_apic_processor(self, connector, id,
                                   mem_space, port_space, apic_bus):
        self.connect_x86_processor(connector, id, mem_space, port_space)
        for i in range(self.cpu_threads):
            self.o.cpu[i].bsp = 0
            self.o.apic[i].apic_id = 0     # temporary value
            if self.cpu_threads > 1:
                self.o.cpu[i].cpuid_physical_apic_id = 0
            self.o.apic[i].apic_bus = apic_bus


###  X86/HyperThreaded Processor, 2 Threads


class x86_2ht_processor_component(x86_apic_processor_component):
    connectors = x86_apic_processor_component.connectors.copy()
    del connectors['cache-cpu']
    for i in range(2):
        connectors['cache-cpu%d' % i] = {
            'type' : 'timing-model', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : True, 'multi' : False}

    def __init__(self, parse_obj):
        x86_apic_processor_component.__init__(self, parse_obj, 2)


###  X86/HyperThreaded Processor, 4 Threads


class x86_4ht_processor_component(x86_apic_processor_component):
    connectors = x86_apic_processor_component.connectors.copy()
    del connectors['cache-cpu']
    for i in range(4):
        connectors['cache-cpu%d' % i] = {
            'type' : 'timing-model', 'direction' : 'down',
            'empty_ok' : True, 'hotplug' : True, 'multi' : False}

    def __init__(self, parse_obj):
        x86_apic_processor_component.__init__(self, parse_obj, 4)


class pentium_processor_component(x86_apic_processor_component):
    classname = 'pentium-cpu'
    basename = 'cpu'
    description = ('The "pentium-cpu" component represents an Intel Pentium '
                   'processor.')
    cpuclass = 'x86-pentium'
    apic_type = "P6"

class pentium_mmx_processor_component(x86_apic_processor_component):
    classname = 'pentium-mmx-cpu'
    basename = 'cpu'
    description = ('The "pentium-mmx-cpu" component represents an Intel '
                   'Pentium MMX processor.')
    cpuclass = 'x86-pentium-mmx'
    apic_type = "P6"

class pentium_pro_processor_component(x86_apic_processor_component):
    classname = 'pentium-pro-cpu'
    basename = 'cpu'
    description = ('The "pentium-pro-cpu" component represents an Intel '
                   'Pentium Pro (P6) processor.')
    cpuclass = 'x86-ppro'
    apic_type = "P6"

class pentium_ii_processor_component(x86_apic_processor_component):
    classname = 'pentium-ii-cpu'
    basename = 'cpu'
    description = ('The "pentium-ii-cpu" component represents an Intel '
                   'Pentium II processor.')
    cpuclass = 'x86-p2'
    apic_type = "P6"

class pentium_iii_processor_component(x86_apic_processor_component):
    classname = 'pentium-iii-cpu'
    basename = 'cpu'
    description = ('The "pentium-iii-cpu" component represents an Intel '
                   'Pentium III processor.')
    cpuclass = 'x86-p3'
    apic_type = "P6"

class pentium_m_processor_component(x86_apic_processor_component):
    classname = 'pentium-m-cpu'
    basename = 'cpu'
    description = ('The "pentium-m-cpu" component represents an Intel '
                   'Pentium M processor.')
    cpuclass = 'x86-pentium-m'
  	 
    def add_objects(self):
        x86_apic_processor_component.add_objects(self)
        for i in range(self.cpu_threads):
            cpu = self.o.cpu[i]
            # 512kb L2 cache
            cpu.cpuid_2_eax = 0x03020101;
            cpu.cpuid_2_ebx = 0;
            cpu.cpuid_2_ecx = 0;
            cpu.cpuid_2_edx = 0x430c0804;
            cpu.cpuid_family = 6
            cpu.cpuid_model = 9
            cpu.cpuid_stepping = 5
            cpu.cpuid_brand_id = 22
            cpu.cpuid_processor_name = "Virtutech Pentium M Processor"
            # Sane speedstep frequency/voltage limits. Prevents division by
            # zero on some software.
            cpu.ia32_perf_sts = 0x01010F0F00000000

class pentium_4_processor_component(x86_apic_processor_component):
    classname = 'pentium-4-cpu'
    basename = 'cpu'
    description = ('The "pentium-4-cpu" component represents an Intel '
                   'Pentium 4 processor.')
    cpuclass = 'x86-p4'

class xeon_prestonia_processor_component(x86_apic_processor_component):
    classname = 'xeon-prestonia-cpu'
    basename = 'cpu'
    description = ('The "xeon-prestonia-cpu" component represents a 32-bit Intel '
                   'Xeon processor.')
    cpuclass = 'x86-p4'
  	 
    def add_objects(self):
        x86_apic_processor_component.add_objects(self)
        for i in range(self.cpu_threads):
            cpu = self.o.cpu[i]
            cpu.cpuid_family = 0xf
            cpu.cpuid_model = 2
            cpu.cpuid_stepping = 9
            cpu.cpuid_brand_id = 0xb
            cpu.cpuid_processor_name = "Virtutech Xeon Processor"

class pentium_4e_processor_component(x86_apic_processor_component):
    connectors = x86_apic_processor_component.connectors.copy()
    classname = 'pentium-4e-cpu'
    basename = 'cpu'
    description = ('The "pentium-4e-cpu" component represents an Intel '
                   '64-bit Pentium 4E processor.')
    cpuclass = 'x86-p4e'

class pentium_4e_2ht_processor_component(x86_2ht_processor_component):
    connectors = x86_2ht_processor_component.connectors.copy()
    classname = 'pentium-4e-2ht-cpu'
    basename = 'cpu'
    description = ('The "pentium-4e-2ht-cpu" component represents an Intel '
                   '64-bit Pentium 4E processor, with 2 hyper threads.')
    cpuclass = 'x86-p4e'

class pentium_4e_4ht_processor_component(x86_4ht_processor_component):
    connectors = x86_4ht_processor_component.connectors.copy()
    classname = 'pentium-4e-4ht-cpu'
    basename = 'cpu'
    description = ('The "pentium-4e-4ht-cpu" component represents an Intel '
                   '64-bit Pentium 4E processor, with 4 hyper threads.')
    cpuclass = 'x86-p4e'

class x86_hammer_processor_component(x86_apic_processor_component):
    classname = 'x86-hammer-cpu'
    basename = 'cpu'
    description = ('The "x86-hammer-cpu" component represents a generic '
                   '64-bit AMD Athlon 64 or Opteron processor without '
                   'on-chip devices.')
    cpuclass = 'x86-hammer'

class opteron_processor_component(x86_apic_processor_component):
    connectors = x86_apic_processor_component.connectors.copy()
    classname = 'opteron-cpu'
    basename = 'cpu'
    description = ('The "opteron-cpu" component represents an '
                   'Opteron 240 processor.')
    connectors['pci-bus'] = {
        'type' : 'pci-bus', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    cpuclass = 'x86-hammer'

    def opteron_brand_id(self, num):
        major = num / 100
        minor = num % 100
        mult = (minor - 38) / 2
        if major == 1:
            return (0xc << 6) | mult
        elif major == 2:
            return (0x10 << 6) | mult
        elif major == 8:
            return (0x14 << 6) | mult

    def opteron_vid(self, millivolts):
        if millivolts > 1550 or millivolts < 800 or (millivolts % 25) != 0:
            raise "VID undefined"
        steps = (millivolts - 800) / 25
        return 0x1e - steps

    def opteron_fid(self, mhz):
        if (mhz % 200) != 0:
            raise "FID undefined"
        multiplier = mhz / 200
        if multiplier < 4 or multiplier > 25:
            raise "FID undefined"
        return (multiplier - 4) << 1

    def instantiation_done(self):
        x86_apic_processor_component.instantiation_done(self)
        for i in range(self.cpu_threads):
            cpu = SIM_get_object(self.o.cpu[i].name)
            print "[%s] Setting cpu type to Opteron 240." % cpu.name
            # 0xf5a is revision CG
            cpu.cpuid_family=0xf
            cpu.cpuid_model=5
            cpu.cpuid_stepping=0xa
            cpu.edx=0xf5a
            cpu.cpuid_brand_id=self.opteron_brand_id(240)
            cpu.fidvid_status = ((self.opteron_vid(1500) << 48) |
                                 (self.opteron_vid(1500) << 40) |
                                 (self.opteron_vid(1500) << 32) |
                                 (self.opteron_vid(1500) << 24) |
                                 (self.opteron_fid(cpu.freq_mhz) << 16) |
                                 (self.opteron_fid(cpu.freq_mhz) << 8) |
                                 (self.opteron_fid(cpu.freq_mhz) << 0))

    def add_objects(self):
        x86_apic_processor_component.add_objects(self)
        self.o.hypertransport = pre_obj(self.o.cpu[0].name + '_hypertransport$', 'k8_hypertransport')
        self.o.address_map = pre_obj(self.o.cpu[0].name + '_address_map$', 'k8_address_map')
        self.o.dram = pre_obj(self.o.cpu[0].name + '_dram$', 'k8_dram')
        self.o.misc = pre_obj(self.o.cpu[0].name + '_misc$', 'k8_misc')
        self.o.hypertransport.misc_function = self.o.misc
        self.o.address_map.misc_function = self.o.misc

    def add_connector_info(self):
        x86_apic_processor_component.add_connector_info(self)
        self.connector_info['pci-bus'] = [[[0, self.o.hypertransport],
                                           [1, self.o.address_map],
                                           [2, self.o.dram],
                                           [3, self.o.misc]]]

    def connect_pci_bus(self, connector, slot, pci_bus):
        self.o.hypertransport.pci_bus = pci_bus
        self.o.address_map.pci_bus = pci_bus
        self.o.dram.pci_bus = pci_bus
        self.o.misc.pci_bus = pci_bus


for model in ['pentium', 'pentium_mmx', 'pentium_pro',
              'pentium_ii', 'pentium_iii', 'pentium_m', 'pentium_4',
              'pentium_4e', 'pentium_4e_2ht', 'pentium_4e_4ht',
              'x86_hammer', 'opteron', 'xeon_prestonia']:
    register_component_class(
        eval('%s_processor_component' % model),
        [['cpu_frequency', Sim_Attr_Required, 'i',
          'Processor frequency in MHz.'],
         ['cpi', Sim_Attr_Optional, 'i',
          'Cycles per instruction.'],
         ['apic_frequency', Sim_Attr_Optional, 'i',
          'APIC bus frequency in MHz, default is 10 MHz.'],
         ['cpu_threads', Sim_Attr_Pseudo, 'i',
          'The number of hyper threads in the processor.']])



### North Bridge base class


class north_bridge_component(component_object):
    connectors = {
        'system' : {'type' : 'x86-chipset', 'direction' : 'up',
                    'empty_ok' : False, 'hotplug' : False, 'multi' : False}}
    for i in range(24):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : False}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        if not "pci_bus_class" in dir(self):
            self.pci_bus_class = 'pci-bus'

    def add_objects(self):
        self.o.pci_conf = pre_obj('pci_conf$', 'memory-space')
        self.o.pci_io = pre_obj('pci_io$', 'memory-space')
        self.o.pci_io.map = []
        self.o.pci_bus = pre_obj('pci_bus$', self.pci_bus_class)
        self.o.pci_bus.conf_space = self.o.pci_conf
        self.o.pci_bus.io_space = self.o.pci_io
        self.o.pci_bus.pci_devices = []

    def add_connector_info(self):
        self.connector_info['system'] = []
        for i in range(24):
            self.connector_info['pci-slot%d' % i] = [i, self.o.pci_bus]
        self.connector_info['southbridge'] = [self.o.pci_bus]

    def connect_x86_chipset(self, connector, phys_space, pci_space,
                            port_space, ram):
        self.o.pci_bus.memory_space = pci_space
        port_space.map += [
            [0xcf8, self.o.bridge, 0, 0xcf8, 4],
            [0xcf9, self.o.bridge, 0, 0xcf9, 2],
            [0xcfa, self.o.bridge, 0, 0xcfa, 2],
            [0xcfb, self.o.bridge, 0, 0xcfb, 1],
            [0xcfc, self.o.bridge, 0, 0xcfc, 4],
            [0xcfd, self.o.bridge, 0, 0xcfd, 2],
            [0xcfe, self.o.bridge, 0, 0xcfe, 2],
            [0xcff, self.o.bridge, 0, 0xcff, 1]]
        port_space.default_target = [self.o.pci_io, 0, 0, None]
        pci_space.default_target = [ram, 0, 0, None]
        
    def connect_pci_bus(self, connector, device_list):
        slot = self.connector_info[connector][0]
        bus = self.connector_info[connector][1]
        devs = bus.pci_devices
        for dev in device_list:
            devs += [[slot, dev[0], dev[1]]]
        bus.pci_devices = devs


### Intel 443BX North Bridge without AGP


class north_bridge_443bx_component(north_bridge_component):
    classname = 'north-bridge-443bx'
    basename = 'north_bridge'
    description = ('The "north-bridge-443bx" component represents an Intel '
                   '443BX North Bridge (host-to-PCI bridge) without AGP.')

    def add_objects(self):
        north_bridge_component.add_objects(self)
        self.o.bridge = pre_obj('north_bridge$', 'i82443bx')
        self.o.bridge.pci_bus = self.o.pci_bus
        self.o.pci_bus.bridge = self.o.bridge
        self.o.pci_bus.pci_devices = [[0, 0, self.o.bridge]]

    def connect_x86_chipset(self, connector, phys_space, pci_space,
                            port_space, ram):
        north_bridge_component.connect_x86_chipset(
            self, connector, phys_space, pci_space, port_space, ram)
        self.o.bridge.memory = phys_space
        port_space.map += [[0x22, self.o.bridge, 0, 0x22, 1]]


register_component_class(north_bridge_443bx_component, [])


### Intel 443BX North Bridge with AGP


class north_bridge_443bx_agp_component(north_bridge_443bx_component):
    classname = 'north-bridge-443bx-agp'
    basename = 'north_bridge'
    description = ('The "north-bridge-443bx" component represents an Intel '
                   '443BX North Bridge (host-to-PCI bridge) with AGP.')
    connectors = north_bridge_443bx_component.connectors.copy()
    connectors['agp-slot0'] = {
        'type' : 'agp-bus', 'direction' : 'down',
        'empty_ok' : 1, 'hotplug' : False, 'multi' : False}

    def add_objects(self):
        north_bridge_443bx_component.add_objects(self)
        self.o.agp_conf = pre_obj('agp_conf$', 'memory-space')
        self.o.agp_io = pre_obj('agp_io$', 'memory-space')
        self.o.agp_io.map = []
        self.o.agp_mem = pre_obj('agp_mem$', 'memory-space')
        self.o.agp_mem.map = []
        self.o.agp_bus = pre_obj('agp_bus$', 'pci-bus')
        self.o.agp_bus.conf_space = self.o.agp_conf
        self.o.agp_bus.io_space = self.o.agp_io
        self.o.agp_bus.memory_space = self.o.agp_mem
        self.o.agp_bus.pci_devices = []
        self.o.agp = pre_obj('pci_to_agp$', 'i82443bx_agp')
        self.o.agp.pci_bus = self.o.pci_bus
        self.o.agp.secondary_bus = self.o.agp_bus
        self.o.agp_bus.bridge = self.o.agp
        self.o.bridge.agp_bridge = self.o.agp
        self.o.pci_bus.pci_devices += [[1, 0, self.o.agp]]

    def add_connector_info(self):
        north_bridge_443bx_component.add_connector_info(self)
        self.connector_info['agp-slot0'] = [0, self.o.agp_bus]

    def connect_x86_chipset(self, connector, phys_space, pci_space,
                            port_space, ram):
        north_bridge_443bx_component.connect_x86_chipset(
            self, connector, phys_space, pci_space, port_space, ram)

    def connect_agp_bus(self, connector, device_list):
        self.connect_pci_bus(connector, device_list)

register_component_class(north_bridge_443bx_agp_component, [])


### Intel 875P North Bridge


class north_bridge_875p_component(north_bridge_component):
    classname = 'north-bridge-875p'
    basename = 'north_bridge'
    description = ('The "north-bridge-875p" component represents an Intel '
                   '875P North Bridge (host-to-PCI bridge).')
    connectors = north_bridge_component.connectors.copy()
    connectors['agp-slot0'] = {
        'type' : 'agp-bus', 'direction' : 'down',
        'empty_ok' : 1, 'hotplug' : False, 'multi' : False}

    def add_objects(self):
        north_bridge_component.add_objects(self)
        self.o.bridge = pre_obj('north_bridge$', 'i82875P')
        self.o.bridge.pci_bus = self.o.pci_bus
        self.o.pci_bus.bridge = self.o.bridge
        self.o.pci_bus.pci_devices = [[0, 0, self.o.bridge]]
        self.o.agp_conf = pre_obj('agp_conf$', 'memory-space')
        self.o.agp_io = pre_obj('agp_io$', 'memory-space')
        self.o.agp_io.map = []
        self.o.agp_mem = pre_obj('agp_mem$', 'memory-space')
        self.o.agp_mem.map = []
        self.o.agp_bus = pre_obj('agp_bus$', 'pci-bus')
        self.o.agp_bus.conf_space = self.o.agp_conf
        self.o.agp_bus.io_space = self.o.agp_io
        self.o.agp_bus.memory_space = self.o.agp_mem
        self.o.agp_bus.pci_devices = []
        self.o.agp = pre_obj('pci_to_agp$', 'i82875P_agp')
        self.o.agp.pci_bus = self.o.pci_bus
        self.o.agp.secondary_bus = self.o.agp_bus
        self.o.agp_bus.bridge = self.o.agp
        self.o.bridge.agp_bridge = self.o.agp
        self.o.pci_bus.pci_devices += [[1, 0, self.o.agp]]

    def add_connector_info(self):
        north_bridge_component.add_connector_info(self)
        self.connector_info['agp-slot0'] = [0, self.o.agp_bus]

    def connect_x86_chipset(self, connector, phys_space, pci_space,
                            port_space, ram):
        north_bridge_component.connect_x86_chipset(
            self, connector, phys_space, pci_space, port_space, ram)
        self.o.bridge.memory = phys_space
        port_space.map += [[0x22, self.o.bridge, 0, 0x22, 1]]

    def connect_agp_bus(self, connector, device_list):
        self.connect_pci_bus(connector, device_list)

register_component_class(north_bridge_875p_component, [])


### Intel E7520 North Bridge


class north_bridge_e7520_component(north_bridge_component):
    classname = 'north-bridge-e7520'
    basename = 'north_bridge'
    description = ('The "north-bridge-e7520" component represents an Intel '
                   'E7520 North Bridge (host-to-PCI bridge).')

    connectors = north_bridge_component.connectors.copy()
    connectors['southbridge'] = {
        'type' : 'hub-link', 'direction' : 'down',
        'empty_ok' : 1, 'hotplug' : False, 'multi' : False}

    connectors['pcie-a-slot'] = {
            'type' : 'pcie-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : True}
    connectors['pcie-a1-slot'] = {
            'type' : 'pcie-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : True}
    connectors['pcie-b-slot'] = {
            'type' : 'pcie-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : True}
    connectors['pcie-b1-slot'] = {
            'type' : 'pcie-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : True}
    connectors['pcie-c-slot'] = {
            'type' : 'pcie-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : True}
    connectors['pcie-c1-slot'] = {
            'type' : 'pcie-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : True}

    for i in range(24):
        del connectors['pci-slot%d' % i]

    def add_objects(self):
        self.pci_bus_class = 'pcie-switch'
        north_bridge_component.add_objects(self)

        self.o.bridge = pre_obj('mch$', 'e7520')
        self.o.bridge.pci_bus = self.o.pci_bus
        
        self.o.mch_error = pre_obj('mch$_error', 'e7520_error')
        self.o.mch_error.pci_bus = self.o.pci_bus

        self.o.mch_dma = pre_obj('mch$_dma', 'e7520_dma')
        self.o.mch_dma.pci_bus = self.o.pci_bus

        self.o.mch_extended = pre_obj('mch$_extended', 'e7520_extended')
        self.o.mch_extended.pci_bus = self.o.pci_bus

        # PCIE-A
        self.o.mch_pcie_a = pre_obj('mch$_pcie_a', 'e7520_pcie_port')
        self.o.mch_pcie_a.pci_config_device_id = 0x3595;
        self.o.mch_pcie_a.pci_bus              = self.o.pci_bus
        self.o.mch_pcie_a_bus  = pre_obj('mch$_pcie_a_bus',  'pcie-switch')
        self.o.mch_pcie_a_bus.pci_devices  = []
        self.o.mch_pcie_a_conf = pre_obj('mch$_pcie_a_conf', 'memory-space')
        self.o.mch_pcie_a_io   = pre_obj('mch$_pcie_a_io$',  'memory-space')
        self.o.mch_pcie_a_mem  = pre_obj('mch$_pcie_a_mem$', 'memory-space')
        self.o.mch_pcie_a_bus.conf_space   = self.o.mch_pcie_a_conf
        self.o.mch_pcie_a_bus.io_space     = self.o.mch_pcie_a_io
        self.o.mch_pcie_a_bus.memory_space = self.o.mch_pcie_a_mem
        self.o.mch_pcie_a_bus.bridge       = self.o.mch_pcie_a
        self.o.mch_pcie_a.secondary_bus    = self.o.mch_pcie_a_bus

        # PCIE-A1
        self.o.mch_pcie_a1 = pre_obj('mch$_pcie_a1', 'e7520_pcie_port')
        self.o.mch_pcie_a1.pci_config_device_id = 0x3595;
        self.o.mch_pcie_a1.pci_bus              = self.o.pci_bus
        self.o.mch_pcie_a1_bus  = pre_obj('mch$_pcie_a1_bus',  'pcie-switch')
        self.o.mch_pcie_a1_bus.pci_devices  = []
        self.o.mch_pcie_a1_conf = pre_obj('mch$_pcie_a1_conf', 'memory-space')
        self.o.mch_pcie_a1_io   = pre_obj('mch$_pcie_a1_io$',  'memory-space')
        self.o.mch_pcie_a1_mem  = pre_obj('mch$_pcie_a1_mem$', 'memory-space')
        self.o.mch_pcie_a1_bus.conf_space   = self.o.mch_pcie_a1_conf
        self.o.mch_pcie_a1_bus.io_space     = self.o.mch_pcie_a1_io
        self.o.mch_pcie_a1_bus.memory_space = self.o.mch_pcie_a1_mem
        self.o.mch_pcie_a1_bus.bridge       = self.o.mch_pcie_a1
        self.o.mch_pcie_a1.secondary_bus    = self.o.mch_pcie_a1_bus

        # PCIE-B
        self.o.mch_pcie_b = pre_obj('mch$_pcie_b', 'e7520_pcie_port')
        self.o.mch_pcie_b.pci_config_device_id = 0x3595;
        self.o.mch_pcie_b.pci_bus              = self.o.pci_bus
        self.o.mch_pcie_b_bus  = pre_obj('mch$_pcie_b_bus',  'pcie-switch')
        self.o.mch_pcie_b_bus.pci_devices  = []
        self.o.mch_pcie_b_conf = pre_obj('mch$_pcie_b_conf', 'memory-space')
        self.o.mch_pcie_b_io   = pre_obj('mch$_pcie_b_io$',  'memory-space')
        self.o.mch_pcie_b_mem  = pre_obj('mch$_pcie_b_mem$', 'memory-space')
        self.o.mch_pcie_b_bus.conf_space   = self.o.mch_pcie_b_conf
        self.o.mch_pcie_b_bus.io_space     = self.o.mch_pcie_b_io
        self.o.mch_pcie_b_bus.memory_space = self.o.mch_pcie_b_mem
        self.o.mch_pcie_b_bus.bridge       = self.o.mch_pcie_b
        self.o.mch_pcie_b.secondary_bus    = self.o.mch_pcie_b_bus

        # PCIE-B1
        self.o.mch_pcie_b1 = pre_obj('mch$_pcie_b1', 'e7520_pcie_port')
        self.o.mch_pcie_b1.pci_config_device_id = 0x3595;
        self.o.mch_pcie_b1.pci_bus              = self.o.pci_bus
        self.o.mch_pcie_b1_bus  = pre_obj('mch$_pcie_b1_bus',  'pcie-switch')
        self.o.mch_pcie_b1_bus.pci_devices  = []
        self.o.mch_pcie_b1_conf = pre_obj('mch$_pcie_b1_conf', 'memory-space')
        self.o.mch_pcie_b1_io   = pre_obj('mch$_pcie_b1_io$',  'memory-space')
        self.o.mch_pcie_b1_mem  = pre_obj('mch$_pcie_b1_mem$', 'memory-space')
        self.o.mch_pcie_b1_bus.conf_space   = self.o.mch_pcie_b1_conf
        self.o.mch_pcie_b1_bus.io_space     = self.o.mch_pcie_b1_io
        self.o.mch_pcie_b1_bus.memory_space = self.o.mch_pcie_b1_mem
        self.o.mch_pcie_b1_bus.bridge       = self.o.mch_pcie_b1
        self.o.mch_pcie_b1.secondary_bus    = self.o.mch_pcie_b1_bus

        # PCIE-C
        self.o.mch_pcie_c = pre_obj('mch$_pcie_c', 'e7520_pcie_port')
        self.o.mch_pcie_c.pci_config_device_id = 0x3595;
        self.o.mch_pcie_c.pci_bus              = self.o.pci_bus
        self.o.mch_pcie_c_bus  = pre_obj('mch$_pcie_c_bus',  'pcie-switch')
        self.o.mch_pcie_c_bus.pci_devices  = []
        self.o.mch_pcie_c_conf = pre_obj('mch$_pcie_c_conf', 'memory-space')
        self.o.mch_pcie_c_io   = pre_obj('mch$_pcie_c_io$',  'memory-space')
        self.o.mch_pcie_c_mem  = pre_obj('mch$_pcie_c_mem$', 'memory-space')
        self.o.mch_pcie_c_bus.conf_space   = self.o.mch_pcie_c_conf
        self.o.mch_pcie_c_bus.io_space     = self.o.mch_pcie_c_io
        self.o.mch_pcie_c_bus.memory_space = self.o.mch_pcie_c_mem
        self.o.mch_pcie_c_bus.bridge       = self.o.mch_pcie_c
        self.o.mch_pcie_c.secondary_bus    = self.o.mch_pcie_c_bus

        # PCIE-C1
        self.o.mch_pcie_c1 = pre_obj('mch$_pcie_c1', 'e7520_pcie_port')
        self.o.mch_pcie_c1.pci_config_device_id = 0x3595;
        self.o.mch_pcie_c1.pci_bus              = self.o.pci_bus
        self.o.mch_pcie_c1_bus  = pre_obj('mch$_pcie_c1_bus',  'pcie-switch')
        self.o.mch_pcie_c1_bus.pci_devices  = []        
        self.o.mch_pcie_c1_conf = pre_obj('mch$_pcie_c1_conf', 'memory-space')
        self.o.mch_pcie_c1_io   = pre_obj('mch$_pcie_c1_io$',  'memory-space')
        self.o.mch_pcie_c1_mem  = pre_obj('mch$_pcie_c1_mem$', 'memory-space')
        self.o.mch_pcie_c1_bus.conf_space   = self.o.mch_pcie_c1_conf
        self.o.mch_pcie_c1_bus.io_space     = self.o.mch_pcie_c1_io
        self.o.mch_pcie_c1_bus.memory_space = self.o.mch_pcie_c1_mem
        self.o.mch_pcie_c1_bus.bridge       = self.o.mch_pcie_c1
        self.o.mch_pcie_c1.secondary_bus    = self.o.mch_pcie_c1_bus

        self.o.bridge.pcie_mem = [self.o.mch_pcie_a_mem,
                                  self.o.mch_pcie_a1_mem,
                                  self.o.mch_pcie_b_mem,
                                  self.o.mch_pcie_b1_mem,
                                  self.o.mch_pcie_c_mem,
                                  self.o.mch_pcie_c1_mem]
        
        self.o.pci_bus.bridge = self.o.bridge
        self.o.pci_bus.pci_devices = [[0, 0, self.o.bridge],
                                      [0, 1, self.o.mch_error],
                                      [1, 0, self.o.mch_dma],
                                      [2, 0, self.o.mch_pcie_a],
                                      [3, 0, self.o.mch_pcie_a1],
                                      [4, 0, self.o.mch_pcie_b],
                                      [5, 0, self.o.mch_pcie_b1],
                                      [6, 0, self.o.mch_pcie_c],
                                      [7, 0, self.o.mch_pcie_c1],
                                      [8, 0, self.o.mch_extended]]

    def add_connector_info(self):
        north_bridge_component.add_connector_info(self)
        self.connector_info['southbridge']  = [self.o.pci_bus]
        self.connector_info['pcie-a-slot']  = [self.o.mch_pcie_a_bus]
        self.connector_info['pcie-a1-slot'] = [self.o.mch_pcie_a1_bus]
        self.connector_info['pcie-b-slot']  = [self.o.mch_pcie_b_bus]
        self.connector_info['pcie-b1-slot'] = [self.o.mch_pcie_b1_bus]
        self.connector_info['pcie-c-slot']  = [self.o.mch_pcie_c_bus]
        self.connector_info['pcie-c1-slot'] = [self.o.mch_pcie_c1_bus]

    def check_pcie_bus(self, connector, device_list):
        bus = self.connector_info[connector][0]
        used = {}
        for d in bus.pci_devices:
            slot, fun, dev = d
            used[(slot, fun)] = 1
        for d in device_list:
            slot, fun, dev = d
            if used.has_key((slot, fun)):
                raise Exception, "Slot %d Function %d already in use." % (slot, fun)

    def connect_pcie_bus(self, connector, device_list):
        bus = self.connector_info[connector][0]
        bus.pci_devices += device_list

    def connect_x86_chipset(self, connector, phys_space, pci_space,
                            port_space, ram):
        north_bridge_component.connect_x86_chipset(
            self, connector, phys_space, pci_space, port_space, ram)
        self.o.bridge.ram = ram.map[0][1] # real RAM object
        self.o.bridge.dram = ram
        self.o.bridge.cpu_memory = phys_space
        self.o.bridge.pci_memory = pci_space
        # static translator
        phys_space.map += [
            [0x000C0000, self.o.bridge, 10, 0xC0000, 0x40000, pci_space, 1,0,0]]
        
    def connect_hub_link(self, connector):
        pass

register_component_class(north_bridge_e7520_component, [])


### AMD K8 integrated north bridge


class north_bridge_k8_component(north_bridge_component):
    connectors = north_bridge_component.connectors.copy()
    for i in range(24,32):
        connectors['pci-slot%d' % i] = {
            'type' : 'pci-bus', 'direction' : 'down',
            'empty_ok' : 1, 'hotplug' : False, 'multi' : False}

    classname = 'north-bridge-k8'
    basename = 'north_bridge'
    description = ('The "north-bridge-k8" component represents the '
                   'integrated north bridge on an AMD Athlon 64 or '
                   'AMD Opteron chip.')

    def add_objects(self):
        north_bridge_component.add_objects(self)
        self.o.bridge = pre_obj('north_bridge$', 'k8_host_bridge')
        self.o.bridge.pci_bus = self.o.pci_bus
        self.o.pci_bus.bridge = self.o.bridge

    def add_connector_info(self):
        north_bridge_component.add_connector_info(self)
        for i in range(24,32):
            self.connector_info['pci-slot%d' % i] = [i, self.o.pci_bus]

    def connect_x86_chipset(self, connector, phys_space, pci_space,
                            port_space, ram):
        north_bridge_component.connect_x86_chipset(
            self, connector, phys_space, pci_space, port_space, ram)
        self.o.bridge.memory = phys_space

    def connect_pci_bus(self, connector, device_list):
        north_bridge_component.connect_pci_bus(self, connector, device_list)


register_component_class(north_bridge_k8_component, [])


### Legacy PC Devices


class legacy_pc_devices_component(standard_pc_devices_component):
    classname = 'legacy-pc-devices'
    basename = 'legacy'
    description = ('The "legacy-pc-devices" component represents the legacy '
                   'devices found in PC/AT compatible computers. This '
                   'component can be used as system chipset in ISA based '
                   'x86 machines without PCI support.')
    connectors = standard_pc_devices_component.connectors.copy()
    connectors['system'] =  {
        'type' : 'x86-chipset', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['interrupt'] = {
        'type' : 'sb-interrupt', 'direction' : 'up',
        'empty_ok' : False, 'hotplug' : False, 'multi' : False}
    connectors['isa-bus'] = {
        'type' : 'isa-bus', 'direction' : 'down',
        'empty_ok' : 1, 'hotplug' : False, 'multi' : True}

    def add_objects(self):
        self.used_ports = []
        standard_pc_devices_component.add_objects(self)
        self.mem_space = None

    def add_connector_info(self):
        standard_pc_devices_component.add_connector_info(self)
        self.connector_info['system'] = []
        self.connector_info['interrupt'] = [self.o.isa]
        self.connector_info['isa-bus'] = [self.o.isa_bus, None,
                                          self.o.isa, self.o.dma]

    def connect_x86_chipset(self, connector, phys_space, pci_space,
                            port_space, ram):
        self.mem_space = phys_space
        self.o.dma.memory = phys_space
        port_space.default_target = [self.o.isa_bus, 0, 0, None]
        self.connector_info['isa-bus'] = [self.o.isa_bus, phys_space,
                                          self.o.isa, self.o.dma]

    def connect_sb_interrupt(self, connector, irq_dst, ioapic):
        self.o.pic.irq_dev = irq_dst

    def check_isa_bus(self, connector, ports):
        for p in ports:
            if p in self.used_ports:
                # TODO: use specific exception
                raise Exception, "Port 0x%x already in use." % p
        self.used_ports += ports

    def connect_isa_bus(self, connector):
        pass

register_component_class(legacy_pc_devices_component, [])
