from sim_core import *
import conf
import sim

# dictionary with list of update functions to call
update_functions = {}

def install_configuration_update(version, f):
    prev = update_functions.get(version, [])
    update_functions[version] = prev + [f]

def update_configuration(set):
    global first_queue
    try:
        if set['sim'].version > conf.sim.version:
            print ('Loading a configuration created in a newer Simics version '
                   '(build %d) is not supported, and may not work. Current '
                   'Simics build is %d.' % (set['sim'].version,
                                            conf.sim.version))
            return
    except:
        if SIM_get_verbose():
            print 'No version information in checkpoint - not updating.'
        return

    for x in set.values():
        try:
            first_queue = x.queue
            break
        except:
            pass

    vers = sorted(update_functions.keys())
    for ver in vers:
        if ver < set['sim'].version:
            continue
        # allow callback on same version
        if ver > conf.sim.version:
            print ("Warning: update_config callback for future version "
                   "found: %s" % ver)
            continue
        if SIM_get_verbose():
            print 'Updating from version %d' % ver
        for f in update_functions[ver]:
            try:
                f(set)
            except Exception, msg:
                print 'Update function for version %d failed: %s' % (ver, msg)

#######################

def all_objects(set, classname):
    return [x for x in set.values() if x.classname == classname]

def for_all_objects(set, classname, function):
    for obj in all_objects(set, classname):
        function(set, obj)

def all_objects_with_attr(set, attrname):
    return [x for x in set.values() if hasattr(x, attrname)]

def remove_attr(obj, name):
    try:
        delattr(obj, name)
    except AttributeError:
        pass

def rename_attr(obj, new_attr, old_attr):
    try:
        setattr(obj, new_attr, getattr(obj, old_attr))
    except AttributeError:
        pass
    remove_attr(obj, old_attr)

def remove_class_attr(set, classname, name):
    for obj in all_objects(set, classname):
        remove_attr(obj, name)

def remove_class(set, classname):
    for l in [x.name for x in set.values() if x.classname == classname]:
        del set[l]

x86_classes = ["x86-386", "x86-386-387", "x86-486dx2", "x86-486sx",
               "x86-pentium", "x86-pentium-mmx", "x86-ppro",
               "x86-p2", "x86-p3", "x86-p4", "x86-p4e",
               "x86-hammer", "x86-k7"]

mips_classes = ["mips-4kc", "mips-5kc", "mips-rm7000-be",
                "mips-e9000-be"]

ppc_classes = ['ppc403gcx', 'ppc405gp', 'ppc440gp', 'ppc440gx', 'ppc603e',
               'ppc7400', 'ppc7447', 'ppc7450', 'ppc7450-36', 'ppc7457',
               'ppc750', 'ppc750fx', 'ppc750gx', 'ppc755', 'ppc970fx',
               'ppce500', 'ppce600', 'ppc-power6']

def remove_class(set, classname):
    for obj in all_objects(set, classname):
        del set[obj.name]

#######################

def update_1396_to_1397(set):
    for obj in (all_objects(set, 'mpc8641-rapidio') +
                all_objects(set, 'mpc8548-rapidio')):
        # misspelt register name
        remove_attr(obj, "regs_LTRETCR")
    
def update_1390_to_1391(set):
    for obj in all_objects(set, 'es_asic'):
        remove_attr(obj, "bar3_CT")
        remove_attr(obj, "page_buffer_crc")

def update_1378_to_1379(set):
    for obj in all_objects(set, 'mpc8641-pic'):
        # create task priority registers for 30 more cores:
        # pad CTPR with zeros until a length of 32
        obj.P_CTPR = obj.P_CTPR + [0]*(32 - len(obj.P_CTPR))

def update_1377_to_1378(set):
    for obj in all_objects(set, 'mpc8641-pcie'):
        remove_attr(obj, "pci_config_device_id")
    for obj in (all_objects(set, "MV64360") +
                all_objects(set, "MV64460") +
                all_objects(set, "MV64470") +
                all_objects(set, "MV64470-EC")):
        remove_attr(obj, "regs_port_GoodOctetsReceived")
        remove_attr(obj, "regs_port_GoodOctetsSent")
    for obj in (all_objects(set, "es_asic")):
        remove_attr(obj, "bar3_REVTO")

def add_pex8111_irq_level(set, obj):
    obj.irq_level = 4

def update_8x4x_rapidio_1371(set, obj):
    for reg in "OMR OSR ODQDPAR OSAR ODPR ODATR ODCR ODQEPAR".split():
            remove_attr(obj, "regs_"+reg)
    for reg in "IMR ISR IFQDPAR IDQEPAR IFQEPAR".split():
            remove_attr(obj, "regs_"+reg)

def update_1370_to_1371(set):
    for obj in (all_objects(set, 'mpc8641-rapidio') +
                all_objects(set, 'mpc8548-rapidio')):
        update_8x4x_rapidio_1371(set, obj)

def update_1367_to_1368(set):
    for_all_objects(set, 'pex8111', add_pex8111_irq_level)

def update_1366_to_1367(set):
    # new partial registers
    for o in (all_objects(set, "MV64360") +
              all_objects(set, "MV64460") +
              all_objects(set, "MV64470") +
              all_objects(set, "MV64470-EC")):
        rename_attr(o, 'partial_regs_IDMA_Interrupt_Cause', 'regs_IDMA_Interrupt_Cause')

def update_8x4x_rapidio_1366(set, obj):
    if not hasattr(obj, "inbound_space"):
        # create local link if network in other simics
        space = pre_conf_object(obj.name + "_inbound_space", 'memory-space')
        set[obj.name + '_inbound_space'] = space
        setattr(obj, "inbound_space", space)
    if obj.classname in ('mpc8641-rapidio', 'mpc8548-rapidio'):
        for reg in "EODQEPAR EOSAR EODQDPAR EIFQEPAR EIFQDPAR".split():
            if hasattr(obj, "regs_"+reg):
                setattr(obj, "regs_M_"+reg, [ getattr(obj, "regs_"+reg), 0 ])
                delattr(obj, "regs_"+reg)

def update_1365_to_1366(set):
    for obj in all_objects(set, 'mpc8641-duart'):
        obj.__class_name__ = 'NS16550'
    for obj in (all_objects(set, 'mpc8641-rapidio') +
                all_objects(set, 'mpc8540-rapidio') +
                all_objects(set, 'mpc8548-rapidio')):
        update_8x4x_rapidio_1366(set, obj)
    for obj in (all_objects(set, 'mpc8641-i2c') +
                all_objects(set, 'mpc8540-i2c') +
                all_objects(set, 'mpc8548-i2c')):
        delattr(obj, 'i2c_device_state')
    # new partial registers
    for o in (all_objects(set, "MV64360") +
              all_objects(set, "MV64460") +
              all_objects(set, "MV64470") +
              all_objects(set, "MV64470-EC")):
        rename_attr(o, 'partial_regs_IDMA_Interrupt_Mask', 'regs_IDMA_Interrupt_Mask')

def update_1364_to_1365(set):
    for obj in all_objects(set, 'mpc8641-gu'):
        # remove all registers, layout have changed.
        # registers are characterized by all capital letters
        for attr in dir(obj):
            if attr.isupper():
                delattr(obj, attr)

def update_1363_to_1364(set):
    max_cpu_num = -1
    for c in all_objects_with_attr(set, 'processor_number'):
        if c.processor_number > max_cpu_num:
            max_cpu_num = c.processor_number

    next_cpu_num = max_cpu_num + 1
    taken_nums = {}
    for c in all_objects_with_attr(set, 'processor_number'):
        if taken_nums.has_key(c.processor_number):
            c.processor_number = next_cpu_num
            next_cpu_num += 1
        else:
            taken_nums[c.processor_number] = True

def rename_mv_pci_access_control_attr(obj):
    for i in range(6):
        remove_attr(obj, 'regs_pci_bus_PCI_Access_Control_Base_%d_L' % i)
        remove_attr(obj, 'regs_pci_bus_PCI_Access_Control_Base_%d_H' % i)
        remove_attr(obj, 'regs_pci_bus_PCI_Access_Control_Size_%d' % i)

def update_1361_to_1362(set):
    for o in (all_objects(set, "MV64360") +
              all_objects(set, "MV64460") +
              all_objects(set, "MV64470") +
              all_objects(set, "MV64470-EC")):
        rename_mv_pci_access_control_attr(o)

def remap_pq2(set, mem_map):
    # Dictionary where class name + mapping function is key, and the old
    # offset is the value
    remap = {'clocks'     + '0' : 0x10c80,
             'brg'        + '0' : 0x119f0,
             'cpm-mux'    + '0' : 0x11b00,
             'cpm-timers' + '0' : 0x10d80,
             'cpm'        + '0' : 0x119c0,
             'fcc'        + '0' : 0x11300,
             'i2c_dev'    + '1' : 0x08afc,
             'ic'         + '0' : 0x10c00,
             'io-port'    + '0' : 0x10d00,
             'mc'         + '0' : 0x10100,
             'mcc'        + '0' : 0x11b30,
             'pci'        + '0' : 0x10430,
             'pci'        + '1' : 0x101ac,
             'scc'        + '0' : 0x11a00,
             'sdma'       + '0' : 0x11018,
             'si'         + '0' : 0x11b20,
             'sit'        + '0' : 0x10220,
             'siu'        + '0' : 0x10000,
             'smc'        + '0' : 0x11a82,
             'spi'        + '0' : 0x11aa0}

    # Remap all PQ2 objects at offset 0
    for e in mem_map.map:
        obj = e[1]
        fun = e[2]
        ofs = e[3]
        if not obj.classname[:8] in ['mpc8260-', 'mpc8270-', 'mpc8280-']:
            continue

        key = obj.classname[8:] + str(fun)
        if remap.has_key(key) and ofs == remap[key]:
            e[3] = 0

def update_1358_to_1359(set):
    for_all_objects(set, 'memory-space', remap_pq2)

def update_1357_to_1358(set):
    for o in (all_objects(set, "MV64360") +
              all_objects(set, "MV64460") +
              all_objects(set, "MV64470") +
              all_objects(set, "MV64470-EC")):
        remove_attr(o, "regs_port_MAC_MIB_Counters")

def update_1354_to_1355(set):
    scc_reg_subst = {
        "armv5te": {
            0:  "main_id",
            1:  "cache_type",
            2:  "control",
            3:  "translation_table_base",
            4:  "domain_access_control",
            6:  "fault_status",
            7:  "fault_address",
        },
        "arm966e-s": {
            0:  "main_id",
            1:  "tcm_size",
            2:  "control",
            10: "trace_process_identifier",
            16: "configuration_control",
            17: "bist_control",
            18: "instruction_bist_address",
            19: "instruction_bist_general",
            22: "data_bist_address",
            23: "data_bist_general",
        }
    }
    for cl in ["armv5te", "arm966e-s"]:
        for o in all_objects(set, cl):
            scc_regs = getattr(o, "scc_regs")
            for (i, name) in scc_reg_subst[cl].iteritems():
                setattr(o, name, scc_regs[i])
                remove_attr(o, "scc_regs")

def update_1350_to_1351(set):
    for pq2_class in ("ep8260", "sbc8260", "cpp8260",
                      "gda8540", "mpc8540ads"):
        for obj in all_objects(set, pq2_class):
            remove_attr(obj, "mac_address0")
            remove_attr(obj, "mac_address1")

def update_1348_to_1349(set):
    for obj in all_objects(set, "sx_asic"):
        rename_attr(obj, 'startup_SRCRST',     'startup_GPIOOUT')
        rename_attr(obj, 'startup_SRCLSRI',    'startup_GPIOIN')
        rename_attr(obj, 'startup_SRCRSTSTAT', 'startup_GPIOCR')
        rename_attr(obj, 'startup_SRCRSTRSN',  'startup_GPIOINT')

def update_1340_to_1341(set):
    # hypersim-patttern-matcher fixes:
    # 1. Add a CPUs attribute
    # 2. Remove sample event from step queue, it will be reposted in time q.
    for o in all_objects(set, "hypersim-pattern-matcher"):
        o.cpus = [o.queue]
    for obj in set.values():
        try:
            SIM_get_class(obj.classname)
        except SimExc_General, msg:
            continue
        if 'processor' not in sim.classes[obj.classname].interfaces:
            continue

        sq = obj.step_queue
        nsq = []
        for e in sq:
            if e[1] != "do pattern match":
                nsq.append(e)
        obj.step_queue = nsq

def update_1334_to_1335(set):
    for cl in x86_classes:
        for o in all_objects(set, cl):
            if "debugctlmsr" in dir(o):
                rename_attr(o, "ia32_debugctl", "debugctlmsr")

def update_1332_to_1333(set):
    msr_translate = [["msr_pat"           , "ia32_cr_pat"],
                     ["msr_syscfg"        , "syscfg"],
                     ["msr_top_mem"       , "top_mem"],
                     ["msr_top_mem2"      , "top_mem2"],
                     ["msr_iorr_base0"    , "iorrbase0"],
                     ["msr_iorr_base1"    , "iorrbase1"],
                     ["msr_iorr_mask0"    , "iorrmask0"],
                     ["msr_iorr_mask1"    , "iorrmask1"],
                     ["msr_hwcr"          , "hwcr"],
                     ["msr_manid"         , "manid"],
                     ["msr_nb_cfg"        , "nb_cfg"],
                     ["msr_fidvid_ctl"    , "fidvid_ctl"],
                     ["msr_fidvid_status" , "fidvid_status"],
                     ["msr_iotrap_addr0"  , "iotrap_addr0"],
                     ["msr_iotrap_addr1"  , "iotrap_addr1"],
                     ["msr_iotrap_addr2"  , "iotrap_addr2"],
                     ["msr_iotrap_addr3"  , "iotrap_addr3"],
                     ["msr_iotrap_ctl"    , "iotrap_ctl"],
                     ["msr_smm_base"      , "smm_base"],
                     ["msr_smm_addr"      , "smm_addr"],
                     ["msr_smm_mask"      , "smm_mask"],
                     ["mcg_status"        , "ia32_mcg_status"],
                     ["mcg_ctl"           , "ia32_mcg_ctl"],
                     ["sysenter_cs"       , "ia32_sysenter_cs"],
                     ["sysenter_eip"      , "ia32_sysenter_eip"],
                     ["sysenter_esp"      , "ia32_sysenter_esp"],
                     ["p5_mc_addr"        , "ia32_p5_mc_addr"],
                     ["p5_mc_type"        , "ia32_p5_mc_type"]]
    # remove wrong MSR from x86 processors
    for cl in ["x86-hammer", "x86-k7"]:
        for o in all_objects(set, cl):
            if "p5_mc_addr" in dir(o):
                remove_attr(o, "p5_mc_addr")
            if "p5_mc_type" in dir(o):
                remove_attr(o, "p5_mc_type")
    # translate old MSRs into new
    for cl in x86_classes:
        for o in all_objects(set, cl):
            if "started" in dir(o):
                remove_attr(o, "started")
            for p in msr_translate:
                old,new = p
                if old in dir(o):
                    rename_attr(o, new, old)
    # build correct threads attribute for hyperthreaded cpus
    shared_state_sets = {}
    for cl in x86_classes:
        for o in all_objects(set, cl):
            if "shared_state" in dir(o):
                if o.shared_state:
                    try:
                        shared_state_sets[o.shared_state].append(o)
                    except:
                        shared_state_sets[o.shared_state] = [o.shared_state, o]
                remove_attr(o, "shared_state")
    for k in shared_state_sets.keys():
        for o in shared_state_sets[k]:
            o.threads = shared_state_sets[k]
    # update apic_p4 to apic with P4 state
    for o in all_objects(set, "apic"):
        if "lvt_thermal_sensor" in dir(o):
            # this is an apic_p4, convert it but let broadcast address untouched
            o.apic_type = "P4"
            o.version = 0x14
        else:
            o.apic_type = "P6"
            o.version = 0x18

def update_1329_to_1330(set):
    for cfg in all_objects(set, "ppc403gcx-cfg"):
        if not "ic" in dir(cfg):
            for m in cfg.cpu.dcr_space.map:
                if m[1].classname == "ppc403gcx-ic":
                    cfg.ic = m[1]
                    break
                
                
def update_pq2_attrs_1329(set):
    # The cpm module now posts event, add queue attribute if none defined
    # Take the queue from associated mcc1 module
    for o in (all_objects(set, "mpc8260-cpm") +
              all_objects(set, "mpc8270-cpm") +
              all_objects(set, "mpc8280-cpm")):
        if not "queue" in dir(o):
            o.queue = o.mcc1.queue
    
    # Remove txbd_monitor references in tx_channels_active in fcc_atm
    for o in all_objects(set, "mpc8260-fcc-atm") + all_objects(set, "mpc8280-fcc-atm"):
        o.tx_channels_active = [x[0] for x in o.tx_channels_active]
        if "fcc" in dir(o):
            o.ram_tx_enabled = not not (o.fcc.reg_GFMR & (1 << 4))
        else:
            o.ram_tx_enabled = 0

    # Fix FCC fast ethernets
    for o in (all_objects(set, "mpc8260-fcc-fast-ethernet") +
              all_objects(set, "mpc8270-fcc-fast-ethernet") +
              all_objects(set, "mpc8280-fcc-fast-ethernet")):        
        remove_attr(o, "txbd_monitor")
        if "fcc" in dir(o):        
            o.tx_enabled = not not (o.fcc.reg_GFMR & (1 << 4))
        else:
            o.tx_enabled = 0

    # Fix SCC UARTs
    for o in (all_objects(set, "mpc8260-scc-uart") +
              all_objects(set, "mpc8270-scc-uart") +
              all_objects(set, "mpc8280-scc-uart")):
        remove_attr(o, "txbd_monitor")
        if "scc" in dir(o):                
            o.ram_tx_enabled = not not (o.scc.reg_GSMR_L & (1 << 4))
        else:
            o.ram_tx_enabled = 0
            
    # Fix SMC UARTs
    for o in (all_objects(set, "mpc8260-smc-uart") +
              all_objects(set, "mpc8270-smc-uart") +
              all_objects(set, "mpc8280-smc-uart")):
        remove_attr(o, "txbd_monitor")
        if "smc" in dir(o):                        
            o.ram_tx_enabled = not not (o.smc.reg_SMCMR & (1 << 1))
        else:
            o.ram_tx_enabled = 0


    # Finally, remove the txbd-monitor objects
    remove_class(set, "mpc8260-txbd-monitor")
    remove_class(set, "mpc8270-txbd-monitor")
    remove_class(set, "mpc8280-txbd-monitor")    





def update_1328_to_1329(set):
    update_pq2_attrs_1329(set)

def update_mdio_attrs(set):
    for x in set.values():
        # Purge all data on ongoing MDIO transfers as the format have
        # changed.
        remove_attr(x, 'mii_nvram_read_bit')
        remove_attr(x, 'mii_nvram_last_clock')
        remove_attr(x, 'mii_nvram_addr')
        remove_attr(x, 'mii_nvram_data_in')
        remove_attr(x, 'mii_nvram_op')
        remove_attr(x, 'mii_nvram_word')
        remove_attr(x, 'mii_nvram_in_size')
        remove_attr(x, 'nvram_read_bit')
        remove_attr(x, 'nvram_last_clock')
        remove_attr(x, 'nvram_addr')
        remove_attr(x, 'nvram_data_in')
        remove_attr(x, 'nvram_in_size')
        remove_attr(x, 'nvram_op')
        remove_attr(x, 'nvram_word')
        remove_attr(x, 'serial_reg')
        remove_attr(x, 'serial_op')
        remove_attr(x, 'serial_addr')
        remove_attr(x, 'serial_word')
        remove_attr(x, 'serial_read_bit')
        remove_attr(x, 'serial_in_size')


def update_1327_to_1328(set):
    for cpu in all_objects(set, "MV64360") + all_objects(set, "MV64470"):
        rename_attr(cpu, 'partial_regs_pci_bus_PCI_Configuration_Data', 'regs_pci_bus_PCI_Configuration_Data')
    update_mdio_attrs(set)
    
    for cls in x86_classes:
        for obj in all_objects(set, cls):
            # Convert in_halt_state to activity_state
            in_halt_state = getattr(obj, "in_halt_state")
            activity_state = 0
            if in_halt_state:
                activity_state = 1
            setattr(obj, "activity_state", activity_state)
            remove_attr(obj, "in_halt_state")

            # Remove useless pending_device attribute
            if hasattr(obj, "pending_device"):
                remove_attr(obj, "pending_device")

            # Rename pni_enabled to cpuid_sse3
            if hasattr(obj, "pni_enabled"):
                rename_attr(obj, "cpuid_sse3", "pni_enabled")

            # Temporary interrupt mask
            q = getattr(obj, "step_queue")
            has_interrupt_mask = 0
            for e in q:
                if e[1] == "release temporary interrupt mask":
                    has_interrupt_mask = 1
            q = filter(lambda a: a[1] != "release temporary interrupt mask", q)
            setattr(obj, "step_queue", q)
            temp_mask = 0
            if has_interrupt_mask:
                temp_mask = 1 # Block_By_Sti
            setattr(obj, "temporary_interrupt_mask", temp_mask)

            if (hasattr(obj, "pending_debug_exceptions") and
                    getattr(obj, "pending_debug_exceptions")):
                setattr(obj, "pending_debug_exception", 1)
            rename_attr(obj, "pending_debug_exception_dr6", "pending_debug_exceptions")

def mv_for_all_objects(set, classname, function, mv_obj):
    for obj in all_objects(set, classname):
        function(set, obj, mv_obj)

def replace_mv64xxx_gbe_ptr_1326(set, gbe_obj):
    def update_mv64xxx_gbe_maps(set, space, mv_obj):
        try:
            maplist = space.map
        except:
            return
        if len([x for x in maplist if (x[1].classname == 'MV64360-gbe' or x[1].classname == 'MV64470-gbe')]) == 0:
            return
        for i in range(len(maplist)):
            if (maplist[i][1].classname == 'MV64360-gbe' or maplist[i][1].classname == 'MV64470-gbe'):
                maplist[i][1] = mv_obj
        space.map = maplist

    def update_mv64xxx_phys(set, phy, mv_obj):
        if (phy.mac.classname == 'MV64360-gbe' or phy.mac.classname == 'MV64470-gbe'):
            phy.mac = mv_obj

    try:
        mv_obj = set[(gbe_obj.name).strip('_gbe')]
    except:
        return
    mv_for_all_objects(set, "memory-space", update_mv64xxx_gbe_maps, mv_obj)
    mv_for_all_objects(set, "BCM5421S", update_mv64xxx_phys, mv_obj);

def copy_mv64xxx_attrs_1326(set, gbe_obj):
    try:
        mv_obj = set[(gbe_obj.name).strip('_gbe')]
    except:
        return
    SIM_get_class('MV64360')
    for gbe_attr in dir(gbe_obj):
        for mv_attr in sim.classes['MV64360'].attributes:
            if gbe_attr == mv_attr and not gbe_attr[0:2] == "__":
                exec "mv_obj.%s = gbe_obj.%s" % (gbe_attr, gbe_attr)

def update_mv64xxx_pci_1326(set, obj):
    setattr(obj, 'pci_config_header_type', 0x80)

def update_system_cmp_object_list_1326(set, system_classname, obj_classname):
    for obj in all_objects(set, system_classname):
        for l in [x for x in obj.object_list if x[-4:] == "_gbe"]:
            del obj.object_list[l]

def update_rtc_time_1326(set, obj):
    import time
    val = getattr(obj, "rtc_time")
    try:
        time.strptime(val, '%Y-%m-%d %H:%M:%S %Z')
    except Exception, msg:
        val = val[:len("yyyy-mm-dd HH:MM:SS")]+" UTC"
    setattr(obj, "rtc_time", val)

def update_1326_to_1327(set):
    # remove mv64xxx_gbe pointers
    for_all_objects(set, 'MV64360-gbe', replace_mv64xxx_gbe_ptr_1326)
    for_all_objects(set, 'MV64470-gbe', replace_mv64xxx_gbe_ptr_1326)

    # copy attrs from mv64xxx-gbe to mv64xxx
    for_all_objects(set, 'MV64360-gbe', copy_mv64xxx_attrs_1326)
    for_all_objects(set, 'MV64470-gbe', copy_mv64xxx_attrs_1326)

    # remove mv64xxx-gbe
    remove_class(set, 'MV64360-gbe')
    remove_class(set, 'MV64470-gbe')

    # remove from mv64xxx-gbe system component list
    update_system_cmp_object_list_1326(set, 'sbc750gx-board', 'MV64360-gbe')
    update_system_cmp_object_list_1326(set, 'daredevil-board', 'MV64470-gbe')
    update_system_cmp_object_list_1326(set, 'atlantis-board', 'MV64360-gbe')

    # make sure mv64xxx_pci_fx header_type[7] = 1
    for_all_objects(set, 'MV64360-pci-f0', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64360-pci-f1', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64360-pci-f2', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64360-pci-f3', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64360-pci-f4', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64470-pci-f0', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64470-pci-f1', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64470-pci-f2', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64470-pci-f3', update_mv64xxx_pci_1326)
    for_all_objects(set, 'MV64470-pci-f4', update_mv64xxx_pci_1326)

    # Permit loading of checkpoints with invalid rtc_time, but which
    # could be loaded before
    for_all_objects(set, 'x86-apic-system', update_rtc_time_1326)

def update_etherlink_1321(set, link):
    # network interfaces should now register for the broadcast address
    bcast = ["ff:ff:ff:ff:ff:ff"]*2
    for (x, y, name, dev, (listen_macs, promics)) in link.devices:
        if bcast not in listen_macs:
            listen_macs.append(bcast)

def rename_piix4_usb_1322(set, obj):
    obj.__class_name__ = 'piix4_usb_dummy'

def rename_ppc440gx_obp_1322(set, obj):
    obj.__class_name__ = 'ppc440gx-opb'

def update_1321_to_1322(set):
    # Incorrect name of class
    for_all_objects(set, 'ppc440gx-obp', rename_ppc440gx_obp_1322)

    # Use dummy PIIX4 USB for old checkpoints
    for_all_objects(set, 'piix4_usb', rename_piix4_usb_1322)

def update_1320_to_1321(set):
    # fix MV64360/MV64470 checkpoints to use new PCI classes
    objs = all_objects(set, 'MV64360-pci') + all_objects(set, 'MV64470-pci')
    for obj in objs:
        obj.__class_name__ = obj.classname + "-f%d" % obj.function
        remove_attr(obj, "function")

    # fix x86-components that are missing phys_mem
    objs = (  all_objects(set, 'x86-system')
            + all_objects(set, 'x86-apic-bus-system')
            + all_objects(set, 'x86-apic-system')
            + all_objects(set, 'x86-separate-mem-io-system'))
    for obj in objs:
        obj.object_list['phys_mem'] = obj.object_list['pci_mem']

    for_all_objects(set, "ethernet-link", update_etherlink_1321)

def update_1318_to_1319(set):
    # some broken checkpoints do not have a cpu_list attribute in the top
    # level component, set a dummy (possibly incorrect) attribute as workaround
    cpu = None
    patch_list = []
    for obj in set.values():
        try:
            SIM_get_class(obj.classname)
        except:
            continue
        if 'processor' in sim.classes[obj.classname].interfaces:
            cpu = obj
        elif 'component' in sim.classes[obj.classname].interfaces:
            try:
                if obj.top_level and not hasattr(obj, 'cpu_list'):
                    patch_list += [obj]
            except:
                pass
    for obj in patch_list:
        obj.cpu_list = [cpu]

def update_1317_to_1318(set):
    reg_aliases = ['ubamr', 'uctrl', 'ummcr0', 'ummcr1', 'ummcr2', 'ummcra',
                   'ummcrh', 'upmc1', 'upmc2', 'upmc3', 'upmc4', 'upmc5',
                   'upmc6', 'upmc7', 'upmc8', 'usdar', 'usiar', 'usprg3',
                   'usprg4', 'usprg5', 'usprg6', 'usprg7', 'utbl', 'utbu',
                   'utrace']
    for obj in set.values():
        if obj.classname in ppc_classes:
            for reg_alias in reg_aliases:
                remove_attr(obj, reg_alias)

def update_ppc440_pci_1316(set, space):
    try:
        maplist = space.map
    except:
        return
    if len([x for x in maplist if x[1].classname == 'ppc440gp-pci']) == 0:
        return
    for i in range(len(maplist)):
        if (maplist[i][1].classname == 'ppc440gp-pci'
            and maplist[i][2] == 1):
            maplist[i][3] = 0
    space.map = maplist

def update_1316_to_1317(set):
    for_all_objects(set, "memory-space", update_ppc440_pci_1316)
    objs = (all_objects(set, 'ddr2-memory-module')
            + all_objects(set, 'ddr-memory-module')
            + all_objects(set, 'sdram-memory-module'))
    for obj in objs:
        if obj.registered:
            obj.module_type = "RDIMM"
        else:
            obj.module_type = "UDIMM"
        remove_attr(obj, 'registered')

def update_1304_to_1305(set):
    remove_class(set, 'le-permissions')

def update_tlb_1302_970(set, cpu):
    tlb = cpu.tlb
    for i in range(len(tlb)):
        for j in range(len(tlb[i])):
            tlb[i][j].append(tlb[i][j][4])
            tlb[i][j].append(tlb[i][j][5])
            tlb[i][j][5] = 0 # large page encoding
            tlb[i][j][4] = 0 # big segment encoding

    cpu.tlb = tlb

def update_1302_to_1303(set):
    for_all_objects(set, "ppc970fx", update_tlb_1302_970)

def update_pending_exceptions_1301(set, cpu, table, excvec_bits):
    pending = cpu.pending_exceptions
    exceptions = []

    for i in range(excvec_bits):
        exc = (pending >> (excvec_bits - 1 - i)) & 1
        if not exc:
            continue
        exc_name = table[i]
        exceptions += [exc_name]

    cpu.pending_exceptions = exceptions

def update_pending_exceptions_1301_4xx(set, cpu):
    table = ["Critical_Input", "Machine_check", "DSI", "ISI",
             "External_interrupt", "Alignment", "Program", "System_call",
             "PIT", "FIT", "Watchdog", "Data_TLB_miss", "Instruction_TLB_miss",
             "Debug"]
    update_pending_exceptions_1301(set, cpu, table, 32)

def update_pending_exceptions_1301_booke(set, cpu):
    table = ["Critical_interrupt", "Machine_check", "DSI", "ISI",
             "External_interrupt", "Alignment", "Program",
             "Floating-point_unavailable", "System_call",
             "Auxiliary_processor_unavailable", "Decrementer", "FIT",
             "Watchdog", "Data_TLB_miss", "Instruction_TLB_miss", "Debug",
             "reserved_16", "reserved_17", "reserved_18", "reserved_19",
             "reserved_20", "reserved_21", "reserved_22", "reserved_23",
             "reserved_24", "reserved_25", "reserved_26", "reserved_27",
             "reserved_28", "reserved_29", "reserved_30", "reserved_31",
             "SPE_APU_unavailable", "SPE_floating-point_data",
             "SPE_floating-point_round", "Performance_monitor"]
    update_pending_exceptions_1301(set, cpu, table, 64)

def update_pending_exceptions_1301_750(set, cpu):
    table = ["Reserved", "System_reset", "Machine_check", "Data_storage",
             "Data_segment", "Instruction_storage", "Instruction_segment",
             "External_interrupt", "Alignment", "Program",
             "Floating-point_unavailable", "Decrementer", "Reserved_a",
             "Reserved_b", "System_call", "Trace", "Reserved_e",
             "Performance_monitor", "Altivec_Unavailable",
             "Instruction_Tlb_miss", "Data_Tlb_Load_miss",
             "Data_Tlb_Store_miss", "Instruction_address_breakpoint",
             "System_management_interrupt", "Reserved_15", "Altivec_Assist",
             "Thermal_management_interrupt"]
    update_pending_exceptions_1301(set, cpu, table, 32)

def update_add_ftp_alg_in(set, forward_in_obj):
    sn = forward_in_obj.tcp
    forward_out_obj = forward_in_obj.forward_handler
    alg_name = sn.name + "_ftp_alg"

    if set.has_key(alg_name):
        alg_obj = set[alg_name]
    else:
        alg_obj = pre_conf_object(alg_name, "ftp-alg")
        set[alg_name] = alg_obj
        alg_obj.forward_handler = forward_out_obj
        alg_obj.incoming_handler = forward_in_obj
    forward_out_obj.algs = [alg_obj]
    forward_in_obj.algs = [alg_obj]
    remove_attr(forward_in_obj, "forward_handler")


pcmcia_dev = None
slot0_att = None
slot1_att = None
slot0_cmn = None
slot1_cmn = None

def update_pcmcia_1301_map(set, space):
    try:
        maplist = space.map
    except:
        return
    if len([x for x in maplist if x[1] == pcmcia_dev]) == 0:
        return
    newlist = []
    map_functions = [0, 0x100, 0x200, 0x210, 0x300, 0x310]
    for m in maplist:
        if m[1] == pcmcia_dev:
            if m[2] == 2:
                m[1] = slot0_att
            elif m[2] == 3:
                m[1] = slot1_att
            elif m[2] == 4:
                m[1] = slot0_cmn
            elif m[2] == 5:
                m[1] = slot1_cmn
            if m[2] != 255: # PCI config-space
                m[2] = map_functions[m[2]]
        newlist.append(m)
    space.map = newlist

def update_pcmcia_mappings(set, obj, slot):
    global slot0_att, slot1_att, slot0_cmn, slot1_cmn
    if slot == 0:
        ide = obj.slot0_ata
    else:
        ide = obj.slot1_ata
    slot_cmn = pre_conf_object(ide.name + '_cmn', "memory-space")
    slot_att = pre_conf_object(ide.name + '_att', "memory-space")
    set[ide.name + '_cmn'] = slot_cmn
    set[ide.name + '_att'] = slot_att
    # TODO: read data
    cis_image = pre_conf_object(ide.name + '_cis_image', "image")
    cis_image.size = 768
    cis = pre_conf_object(ide.name + '_cis', "rom")
    cis.image = cis_image
    set[ide.name + 'cis'] = cis
    set[ide.name + 'cis_image'] = cis_image
    slot_cmn.map = [
        [0, ide, 0, 0, 8],
        [0xe, ide, 0, 8, 1]]
    for i in range(0x400, 0x800, 2):
        slot_cmn.map.append([i, ide, 0, 0x0, 0x2])
    slot_att.map = [[0x0, cis, 0, 0, 0x300]]
    if slot == 0:
        remove_attr(obj, 'slot0_ata')
        remove_attr(obj, 'slot0_cis')
        obj.slot0_spaces = [slot_att, slot_cmn, slot_cmn]
        slot0_att = slot_att
        slot0_cmn = slot_cmn
    else:
        remove_attr(obj, 'slot1_ata')
        remove_attr(obj, 'slot1_cis')
        obj.slot1_spaces = [slot_att, slot_cmn, slot_cmn]
        slot1_att = slot_att
        slot1_cmn = slot_cmn

ide_cis = (
    0x01, 0x03, 0xd9, 0x01, 0xff, 0x1c, 0x04, 0x03, 0xd9, 0x01, 0xff, 0x18,
    0x02, 0xdf, 0x01, 0x20, 0x04, 0x01, 0x4e, 0x00, 0x02, 0x15, 0x2b, 0x04,
    0x01, 0x56, 0x69, 0x6b, 0x69, 0x6e, 0x67, 0x20, 0x41, 0x54, 0x41, 0x20,
    0x46, 0x6c, 0x61, 0x73, 0x68, 0x20, 0x43, 0x61, 0x72, 0x64, 0x20, 0x20,
    0x20, 0x20, 0x00, 0x53, 0x54, 0x4f, 0x52, 0x4d, 0x20, 0x20, 0x00, 0x53,
    0x54, 0x42, 0x4d, 0x30, 0x00, 0xff, 0x21, 0x02, 0x04, 0x01, 0x22, 0x02,
    0x01, 0x01, 0x22, 0x03, 0x02, 0x04, 0x5f, 0x1a, 0x05, 0x01, 0x03, 0x00,
    0x02, 0x0f, 0x1b, 0x0b, 0xc0, 0x40, 0xa1, 0x27, 0x55, 0x4d, 0x5d, 0x75,
    0x08, 0x00, 0x21, 0x1b, 0x06, 0x00, 0x01, 0x21, 0xb5, 0x1e, 0x4d, 0x1b,
    0x0d, 0xc1, 0x41, 0x99, 0x27, 0x55, 0x4d, 0x5d, 0x75, 0x64, 0xf0, 0xff,
    0xff, 0x21, 0x1b, 0x06, 0x01, 0x01, 0x21, 0xb5, 0x1e, 0x4d, 0x1b, 0x12,
    0xc2, 0x41, 0x99, 0x27, 0x55, 0x4d, 0x5d, 0x75, 0xea, 0x61, 0xf0, 0x01,
    0x07, 0xf6, 0x03, 0x01, 0xee, 0x21, 0x1b, 0x06, 0x02, 0x01, 0x21, 0xb5,
    0x1e, 0x4d, 0x1b, 0x12, 0xc3, 0x41, 0x99, 0x27, 0x55, 0x4d, 0x5d, 0x75,
    0xea, 0x61, 0x70, 0x01, 0x07, 0x76, 0x03, 0x01, 0xee, 0x21, 0x1b, 0x06,
    0x03, 0x01, 0x21, 0xb5, 0x1e, 0x4d, 0x14)

def add_pcmcia_cis_1301(arg, ini_obj):
    obj = SIM_get_object(arg)
    spaces = [obj.slot0_spaces, obj.slot1_spaces]
    for i in (0, 1):
        if len(spaces[i]) == 1:
            continue
        attr = spaces[i][0]
        for i in range(len(ide_cis)):
            attr.iface.memory_space.write(attr, None,
                                          i * 2, (ide_cis[i], ), 1)
        # Fake some attribute space registers
        attr.iface.memory_space.write(attr, None,
                                      0x204, (0x2e, ), 1)
    SIM_hap_delete_callback("Core_Configuration_Loaded",
                            add_pcmcia_cis_1301, arg)

def update_pcmcia_1301(set, obj):
    global pcmcia_dev
    pcmcia_dev = obj
    obj.config_registers[15] = 0x00000100 # interrupt pin A
    update_pcmcia_mappings(set, obj, 0)
    update_pcmcia_mappings(set, obj, 1)
    if obj.slot0_memory_windows[0][0]:
        obj.slot0_memory_windows[0][1] = 3
    if obj.slot0_memory_windows[4][0]:
        obj.slot0_memory_windows[4][1] = 2
    if obj.slot1_memory_windows[0][0]:
        obj.slot1_memory_windows[0][1] = 3
    if obj.slot1_memory_windows[4][0]:
        obj.slot1_memory_windows[4][1] = 2
    obj.slot0_registers[1] = 0xef
    obj.slot1_registers[1] = 0xef
    for_all_objects(set, "memory-space", update_pcmcia_1301_map)
    SIM_hap_add_callback("Core_Configuration_Loaded",
                         add_pcmcia_cis_1301, obj.name)

def update_uart_1301(set, obj):
    if not hasattr(obj, "interrupt_mask_out2"):
        obj.interrupt_mask_out2 = 1

def update_x86_components_1301(set, obj):
    if 'x87' not in obj.object_list and 'x87[0]' in obj.object_list:
        obj.object_list['x87'] = obj.object_list['x87[0]']
    if 'x87[0]' in obj.object_list:
        del obj.object_list['x87[0]']
    remove_attr(obj, 'num_threads')

def update_1301_to_1302(set):
    for_all_objects(set, "ppc403gcx", update_pending_exceptions_1301_4xx)
    for_all_objects(set, "ppc405gp", update_pending_exceptions_1301_4xx)
    for_all_objects(set, "ppc440gp", update_pending_exceptions_1301_booke)
    for_all_objects(set, "ppc440gx", update_pending_exceptions_1301_booke)
    for_all_objects(set, "ppce500",  update_pending_exceptions_1301_booke)
    for_all_objects(set, "ppc603e",  update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc7400",  update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc7447",  update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc7450",  update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc7457",  update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc750",   update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc750fx", update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc750gx", update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc755",   update_pending_exceptions_1301_750)
    for_all_objects(set, "ppc970fx", update_pending_exceptions_1301_750)
    for_all_objects(set, "CL-PD6729", update_pcmcia_1301)
    for cls in x86_classes:
        remove_class_attr(set, cls, 'smbase')
    for_all_objects(set, "port-forward-incoming-server", update_add_ftp_alg_in)
    for cpu in (all_objects(set, "ultrasparc-ii")
                + all_objects(set, "ultrasparc-iii")
                + all_objects(set, "ultrasparc-iii-plus")
                + all_objects(set, "ultrasparc-iii-i")):
        rename_attr(cpu, 'cpu_group', 'irq_bus')
    for_all_objects(set, "NS16550", update_uart_1301)
    for_all_objects(set, "NS16450", update_uart_1301)
    # somewhere between 1301 and 1325 x86-cpu components become incompatible
    for_all_objects(set, "pentium-4-cpu", update_x86_components_1301)

def update_event_queue_1300(cpu):
    # Read_slot has been removed and should not be present, but we map it
    # to the default slot just in case
    slot_names = ["sync", "pre-update", "update", "update2", "default",
                  "default", "assert", "event-end"]
    ignore_events = set(("User breakpoint",
                         "Internal: update time counter",
                         "Internal: update step counter",
                         "Internal: renew queue",
                         "Head of Time",
                         "Deleted Event",
                         "Check for Async Events"))
    q = [[], []]
    hot_step = 0
    for (evobj, val, slot, queue, time) in cpu.event_queue:
        if evobj == "$simple_event":
            if val == "Head of Time":
                hot_step = time
            if val in ignore_events:
                continue
            evobj = None
        q[queue].append([evobj, val, slot_names[slot], time])

    # compensate for a head of time at step > 0
    q[Sim_Queue_Time] = [[o, v, s, t + hot_step]
                         for [o, v, s, t] in q[Sim_Queue_Time]]

    del cpu.event_queue
    cpu.step_queue = q[Sim_Queue_Step]
    cpu.time_queue = q[Sim_Queue_Time]

def update_1300_to_1301(set):
    # Translate to new event queue attributes:
    for obj in set.values():
        try:
            SIM_get_class(obj.classname)
        except:
            continue
        if 'processor' in sim.classes[obj.classname].interfaces:
            update_event_queue_1300(obj)

create_central_client = False
remote_central = False
remote_host = None
first_queue = None

def remove_default_target_endian_1299(set, obj):
    try:
        if len(obj.default_target) == 5:
            obj.default_target = obj.default_target[:4]
    except:
        pass

def replace_dcr_mapping_1299(set, ppc):
    if len(ppc.dcr):
        dcr_map = {}
        for d in ppc.dcr:
            if dcr_map.has_key(d[0]):
                dcr_map[d[0]].append(d[1])
            else:
                dcr_map[d[0]] = [d[1]]
        mem_map = []
        for obj in dcr_map.keys():
            dcr_list = dcr_map[obj]
            first = dcr_list[0]            
            for dcr in dcr_list:
                mem_map += [[(dcr)*4, set[obj], 0, (dcr-first)*4, 4]]
        dcr_space = ppc.name + '-dcr-space'
        set[dcr_space] = pre_conf_object(dcr_space, 'memory-space')
        ppc.dcr_space = set[dcr_space]
        set[dcr_space].map = mem_map
        remove_attr(ppc, 'dcr')

def fix_405_uic_1299(set, uic):
    print "WARNING: Converting an old 405 based configuration"
    print "The interrupt controller has changed so that irq levels are according"
    print "to documentation. Will try to patch devices but there might be more"
    print "devices connected to the UIC which needs to be patched manually."
    print "Typically obj.irq_level = 31 - old_irq_level"
    uic.target = uic.irq_dev
    uic.critical_target = uic.irq_dev    
    uic.target_level = 0
    uic.critical_target_level = 1
    remove_attr(uic, 'irq_dev')
    rename_attr(uic, 'UICx_CR', 'uiccr')
    rename_attr(uic, 'UICx_ER', 'uicer')
    rename_attr(uic, 'UICx_PR', 'uicvpr')
    rename_attr(uic, 'UICx_SR', 'uicsr')
    rename_attr(uic, 'UICx_TR', 'uictr')
    rename_attr(uic, 'UICx_VCR', 'uicvcr')
    for obj in all_objects(set, 'ppc405gp-iic'):
        if obj.interrupt_device == uic:
            print "Patching %s (level %d -> %d)" % (obj.name, obj.interrupt_level,
                                                    31 - obj.interrupt_level)
            obj.interrupt_level = 31 - obj.interrupt_level
    for obj in all_objects(set, 'ppc405gp-pci'):
        irqs = obj.irq_routing
        new_irq = []
        for i in irqs:
            if i[1] == uic.name:
                print "Patching %s (level %d -> %d)" % (obj.name, i[2], 31 - i[2])
                new_irq.append([i[0], i[1], 31 - i[2]])
            else:
                new_irq.append(i)
        obj.irq_routing = new_irq
    for obj in all_objects(set, 'NS16550'):
        if obj.irq_dev == uic:
            print "Patching %s (level %d -> %d)" % (obj.name, obj.interrupt_pin,
                                                    31 - obj.interrupt_pin)            
            obj.interrupt_pin = 31 - obj.interrupt_pin

def remove_uic_attributes_1299(set, uic):
    remove_attr(uic, 'UICx_VR')
    remove_attr(uic, 'UICx_MSR')            

def add_cpu_obj_1299(set, obj):
    # Find which CPU this object is mapped into
    cpus =  all_objects(set, 'ppc405gp') + all_objects(set, 'ppc440gp') + all_objects(set, 'ppc440gx')
    for cpu in cpus:
        space = cpu.dcr_space
        map = space.map
        for m in map:
            if m[1] == obj:
                obj.cpu = cpu
                break

def change_memory_attr_1299(set, obj):
    if hasattr(obj, 'memory') and type(obj.memory) == str:
        obj.memory = set[obj.memory]

def change_mal_attr_1299(set, obj):
    if hasattr(obj, 'mal') and type(obj.mal) == str:
        obj.mal = set[obj.mal]

def change_irq_attr_1299(set, obj):
    if hasattr(obj, 'irq_routing') and type(obj.irq_routing) == list:
        for i in range(len(obj.irq_routing)):
            if type(obj.irq_routing[i][1]) == str:
                obj.irq_routing[i][1] = set[obj.irq_routing[i][1]]

def rename_ioapic_1299(set, obj):
    obj.__class_name__ = 'io-apic'

def rename_cheetah_plus_mmu_1299(set, obj):
    obj.__class_name__ = 'cheetah-plus-mmu'

def rename_ultrasparc_iii_plus_1299(set, obj):
    obj.__class_name__ = 'ultrasparc-iii-plus'

def rename_ultrasparc_iv_plus_1299(set, obj):
    obj.__class_name__ = 'ultrasparc-iv-plus'

def set_dec_srom_width_1299(set, obj):
    obj.srom_address_width = 6

def fix_fb_mem_1299(set, obj):
    name = "%s-image" % obj.name
    image = pre_conf_object(name, 'image')
    if obj.classname == 'ragexl':
        image.size = 0x800000
    elif obj.classname.startswith('vga'):
        image.size = 0x40000
    elif obj.classname.startswith('voodoo3'):
        image.size = 0x1000000
    set[name] = image
    obj.image = image

def update_1299_to_1300(set):
    for_all_objects(set, 'ragexl', fix_fb_mem_1299)
    for_all_objects(set, 'vga', fix_fb_mem_1299)
    for_all_objects(set, 'vga_pci', fix_fb_mem_1299)
    for_all_objects(set, 'voodoo3', fix_fb_mem_1299)
    for_all_objects(set, 'voodoo3-agp', fix_fb_mem_1299)

    for_all_objects(set, 'ppc403gcx', replace_dcr_mapping_1299)
    for_all_objects(set, 'ppc405gp', replace_dcr_mapping_1299)
    for_all_objects(set, 'ppc440gp', replace_dcr_mapping_1299)
    for_all_objects(set, 'ppc440gx', replace_dcr_mapping_1299)

    for_all_objects(set, 'ppc405gp-uic', fix_405_uic_1299)
    for_all_objects(set, 'ppc440gp-uic', remove_uic_attributes_1299)
    for_all_objects(set, 'ppc440gx-uic', remove_uic_attributes_1299)

    for_all_objects(set, 'ppc405gp-dma', add_cpu_obj_1299)
    for_all_objects(set, 'ppc440gp-dma', add_cpu_obj_1299)
    for_all_objects(set, 'ppc440gx-dma', add_cpu_obj_1299)
    for_all_objects(set, 'ppc405gp-ebc', add_cpu_obj_1299)
    for_all_objects(set, 'ppc440gp-ebc', add_cpu_obj_1299)
    for_all_objects(set, 'ppc440gx-ebc', add_cpu_obj_1299)
    for_all_objects(set, 'ppc405gp-mal', add_cpu_obj_1299)
    for_all_objects(set, 'ppc440gp-mal', add_cpu_obj_1299)
    for_all_objects(set, 'ppc440gx-mal', add_cpu_obj_1299)
    for_all_objects(set, 'misc-dcr', add_cpu_obj_1299)

    for_all_objects(set, 'ppc405gp-dma', change_memory_attr_1299)
    for_all_objects(set, 'ppc440gp-dma', change_memory_attr_1299)
    for_all_objects(set, 'ppc440gx-dma', change_memory_attr_1299)
    for_all_objects(set, 'ppc405gp-mal', change_memory_attr_1299)
    for_all_objects(set, 'ppc440gp-mal', change_memory_attr_1299)
    for_all_objects(set, 'ppc440gx-mal', change_memory_attr_1299)

    for_all_objects(set, 'ppc405gp-emac', change_mal_attr_1299)
    for_all_objects(set, 'ppc440gp-emac', change_mal_attr_1299)
    for_all_objects(set, 'ppc440gx-emac', change_mal_attr_1299)

    for_all_objects(set, 'ppc405gp-pci', change_irq_attr_1299)
    for_all_objects(set, 'ppc440gp-pci', change_irq_attr_1299)
    for_all_objects(set, 'ppc440gx-pci', change_irq_attr_1299)

    for_all_objects(set, 'memory-space', remove_default_target_endian_1299)
    for_all_objects(set, 'port-space', remove_default_target_endian_1299)
    for_all_objects(set, 'I/O-APIC', rename_ioapic_1299)
    for_all_objects(set, 'cheetah+mmu', rename_cheetah_plus_mmu_1299)
    for_all_objects(set, 'ultrasparc-iii+', rename_ultrasparc_iii_plus_1299)
    for_all_objects(set, 'ultrasparc-iv+', rename_ultrasparc_iv_plus_1299)
    try:
        SIM_get_object('dummy-component')
        set['system-component'] = pre_conf_object('system-component',
                                                  'dummy-component')
    except:
        pass
    for cls in ['DEC21041', 'DEC21140A', 'DEC21143']:
        for_all_objects(set, cls, set_dec_srom_width_1299)

    for obj in all_objects(set, 'i82077'):
        try:
            obj.drives = [x[1] for x in obj.drives]
        except:
            pass
    for cls in mips_classes:
        remove_class_attr(set, cls, 'itlb')
        remove_class_attr(set, cls, 'dtlb')
    for obj in all_objects(set, 'i8042'):
        if hasattr(obj, 'reset_targets') and len(obj.reset_targets) > 0:
            bus = pre_conf_object(obj.name + '_reset', 'x86-reset-bus')
            set[obj.name + '_reset'] = bus
            bus.reset_targets = obj.reset_targets
            obj.reset_target = bus
        remove_attr(obj, 'a20_target')
        remove_attr(obj, 'reset_targets')

    for cls in x86_classes:
        remove_class_attr(set, cls, 'stc_segreg_enabled')

def connections_1200(set, obj):
    try:
        connections = obj.connections
    except:
        return
    # <port-forward-outgoing-server>.connections changed from
    # [[si]|[sisi]*]
    # to
    # [[si]|[sissi]*]
    # Find the service-node-device and use that IP
    new_ip = "0.0.0.0"
    for snd in [x for x in set.values()
                if x.classname == 'service-node-device']:
        new_ip = snd.ip_address
        break
    newlist = []
    for sublist in connections:
        if len(sublist) == 2:
            newlist.append(sublist)
        elif len(sublist) == 4:
            newlist.append([sublist[0], sublist[0], new_ip,
                            sublist[2], sublist[3]])
    obj.connections = newlist

def update_1200_to_1201(set):
    for_all_objects(set, "port-forward-outgoing-server", connections_1200)

def sim_1199(set, obj):
    global create_central_client, remote_central, remote_host
    try:
        if obj.remote_simics_central == 1:
            create_central_client = True
            remote_central = True
            remote_host = obj.simics_central_host
    except:
        pass
    remove_attr(obj, 'remote_simics_central')
    remove_attr(obj, 'simics_central_host')
    remove_attr(obj, 'central_debug')

def connect_eth_1199(arg, ini_obj):
    dev = SIM_get_object(arg[0])
    net = SIM_get_object(arg[1])
    dev.link = net
    SIM_hap_delete_callback("Core_Configuration_Loaded",
                            connect_eth_1199, arg)

def eth_device_1199(set, obj):
    global remote_central
    if remote_central:
        # create local link if network in other simics
        link = pre_conf_object('net0', 'ethernet_link')
        set['net0'] = link
        link.central = set['central_client']
        remote_central = False
        link = link.name
    else:
        try:
            link = obj.network
        except:
            pass
    if obj.connected:
        SIM_hap_add_callback("Core_Configuration_Loaded",
                             connect_eth_1199, (obj.name, link))
    remove_attr(obj, 'network')
    remove_attr(obj, 'connected')
    remove_attr(obj, 'min_latency')
    remove_attr(obj, 'backdoor_ok')
    remove_attr(obj, 'auto_connect')
    remove_attr(obj, 'individual_address')

def ethernet_net_1199(set, obj):
    obj.__class_name__ = 'ethernet-link'
    remove_attr(obj, 'frame_loss')
    remove_attr(obj, 'network_id')
    remove_attr(obj, 'handle_dhcp')
    remove_attr(obj, 'shared_media')
    remove_attr(obj, 'netip')
    remove_attr(obj, 'ethernet_central')
    if obj.central_device:
        snd = pre_conf_object('sn0_dev', 'service-node-device')
        set['sn0_dev'] = snd
        snd.service_node = set['sn0']
        snd.arp_table = obj.arp
        snd.mac_address = obj.ownmac
        snd.ip_address = obj.ownip
        snd.netmask = obj.netmask
        snd.queue = first_queue
        set['sn0'].routing_table = [[snd.ip_address, snd.netmask,
                                     '0.0.0.0', snd]]
        snd.link = obj
    try:
        obj.central = set['central_client']
    except:
        pass
    remove_attr(obj, 'central_device')
    remove_attr(obj, 'arp')
    remove_attr(obj, 'ownmac')
    remove_attr(obj, 'ownip')
    remove_attr(obj, 'netmask')

def ethernet_central_1199(set, obj):
    new_dns = []
    for dns in obj.dns:
        new_dns.append([None, dns[0], dns[1], dns[2]])
    set['sn0'].hosts = new_dns
    del set[obj.name]

def central_1199(set, obj):
    global create_central_client
    
    port = obj.ip_port
    file = obj.unix_socket
    del set['central']
    if port == -1 and len(file) == 0:
        return
    # central was used
    cs = pre_conf_object('central_server', 'central-server')
    set['central_server'] = cs
    if len(file):
        cs.unix_socket = file
        cs.unix_socket_mode = 438
    if port != -1:
        cs.tcp_port = port
    create_central_client = True

def update_1199_to_1200(set):
    global remote_host
    for_all_objects(set, 'sim', sim_1199)
    for_all_objects(set, 'central', central_1199)
    if create_central_client:
        cc = pre_conf_object('central_client', 'central-client')
        set['central_client'] = cc
        if remote_host and len(remote_host):
            if not ':' in remote_host and not '/' in remote_host:
                # if port not specified, add default one
                remote_host += ":4711"
            cc.server = remote_host
        elif not remote_central:
            cc.server = pre_conf_object('central_server', 'central-server')
            set['central_server'] = cc.server

    if len(all_objects(set, 'ethernet-central')):
        set['sn0'] = pre_conf_object('sn0', 'service-node')

    for_all_objects(set, 'ethernet-central', ethernet_central_1199)
    for_all_objects(set, 'ethernet-network', ethernet_net_1199)

    for_all_objects(set, 'sbus-hme', eth_device_1199)
    for_all_objects(set, 'cheerio-hme', eth_device_1199)
    for_all_objects(set, 'BCM5703C', eth_device_1199)
    for_all_objects(set, 'BCM57034', eth_device_1199)
    for_all_objects(set, 'AM79C960', eth_device_1199)
    for_all_objects(set, 'cassini', eth_device_1199)
    for_all_objects(set, 'DEC21041', eth_device_1199)
    for_all_objects(set, 'DEC21140A', eth_device_1199)
    for_all_objects(set, 'DEC21143', eth_device_1199)
    for_all_objects(set, 'ppc440gp-emac', eth_device_1199)
    for_all_objects(set, 'CS8900A', eth_device_1199)

    remove_class_attr(set, 'ppc440gp', 'ear')

    for l in [x.name for x in set.values() if x.classname == 'central-links']:
        del set[l]

    remove_class_attr(set, 'ICS951601', 'address_mask')
    remove_class_attr(set, 'NS16450', 'send_while_playing_back')
    remove_class_attr(set, 'NS16550', 'send_while_playing_back')
    remove_class_attr(set, 'M5823', 'irq_disable')
    remove_class_attr(set, 'DS12887', 'irq_disable')
    remove_class_attr(set, 'DS17485', 'irq_disable')
    remove_class_attr(set, 'i8254', 'rw_state')

    for obj in all_objects(set, 'ppc440gp-mal'):
        # both tx and tx to the same irq-device in 440gp-mal
        obj.interrupts[1] = obj.interrupts[0]

    cpus = [x for x in set.values() if x.classname in x86_classes]
    for kbd in all_objects(set, 'i8042'):
        if len(cpus):
            # this is an x86 config
            kbd.reset_targets = cpus

    for obj in all_objects(set, 'port-space'):
        # remove obsolete 6th element (reverse-endian)
        try:
            for m in range(len(obj.map)):
                if len(obj.map[m]) == 6:
                    obj.map[m].pop(-1)
        except:
            pass

def update_1051_to_1052(set):
    remove_class_attr(set, 'server-console', 'data_out')
    remove_class_attr(set, 'server-console', 'poll_interval')

def change_map_endian_1049(set, obj):
    try:
        # align base for serengeti empty mappings
        for i in range(len(obj.map)):
            off = obj.map[i][0] & 0x1fff
            if off == 0x60 and obj.map[i][4] == 0x10:
                obj.map[i][0] &= 0xffffffffffffe000
                obj.map[i][4] &= 0x70

            # change endian. 5 or shorter? - no endian info included
            if len(obj.map[i]) > 5:
                for j in range(5, len(obj.map[i])):
                    if isinstance(obj.map[i][j], int):
                        obj.map[i][j] = 0

            # if length 6 and last is integer -> remove endian
            # since we don't support this format anymore.
            if len(obj.map[i]) == 6 and isinstance(obj.map[i][5], int):
                obj.map[i].pop(-1)

            # TODO: update vga mapping

    except Exception, msg:
        print msg
        pass

def add_vga_memory_1049(set, obj):
    for vga in [x[1] for x in obj.map]:
        if type(vga) == str:
            vga = set[vga]
        if 'vga' in vga.classname or 'voodoo' in vga.classname:
            vga.memory_space = obj

def update_1049_to_1050(set):
    for_all_objects(set, 'memory-space', change_map_endian_1049)
    for_all_objects(set, 'memory-space', add_vga_memory_1049)
    remove_class_attr(set, 'ide-disk', 'tr_rdy_dma')
    remove_class_attr(set, 'ide-disk', 'tr_cmd_return_dma')
    remove_class_attr(set, 'ide-cdrom', 'tr_rdy_dma')
    remove_class_attr(set, 'ide-cdrom', 'tr_cmd_return_dma')
    remove_class_attr(set, 'i82077', 'seek_irq_drive')
    remove_class_attr(set, 'i8042', 'reset_target')
    remove_class_attr(set, 'NS16450', 'com')
    remove_class_attr(set, 'NS16550', 'com')
    remove_class_attr(set, 'i21152', 'first_bus_nonzero')
    remove_class_attr(set, 'i82443bx_agp', 'first_bus_nonzero')
    remove_class_attr(set, 'i82443bx_agp', 'memory')
    # p4 has these before 2.0 (only p2, p3 and ppro)
    remove_class_attr(set, 'x86-p4', 'mc4_ctl')
    remove_class_attr(set, 'x86-p4', 'mc4_addr')
    remove_class_attr(set, 'x86-p4', 'mc4_status')
    remove_class_attr(set, 'x86-p4', 'mc4_misc')
    remove_class_attr(set, 'x86-p4', 'perfevtsel0')
    remove_class_attr(set, 'x86-p4', 'perfevtsel1')
    for cls in x86_classes:
        remove_class_attr(set, cls, 'cr1')
    for cls in ['SYM53C810', 'SYM53C875']:
        for obj in all_objects(set, cls):
            try:
                pin = obj.interrupt_pin
                obj.interrupt_pin = [pin, 0, 0, 0]
            except:
                pass

def update_1042_to_1043(set):
    for obj in all_objects(set, 'Z8530'):
        a = pre_conf_object(obj.name + '-port-a', 'Z8530-port')
        b = pre_conf_object(obj.name + '-port-b', 'Z8530-port')
        obj.a_port = set[a.name] = a
        obj.b_port = set[b.name] = b
        a.master = obj
        b.master = obj
        # only change console if set
        try:
            a.console = obj.a_console
            a.console.device = a
            remove_attr(obj, 'a_console')
        except:
            pass
        try:
            b.console = obj.b_console
            b.console.device = b
            remove_attr(obj, 'b_console')
        except:
            pass

def update_1040_to_1041(set):
    for obj in all_objects(set, 'ultrasparc-iii+'):
        try:
            if obj.report_ultra3i:
                obj.__class_name__ = 'ultrasparc-iii-i'
            remove_attr(obj, 'report_ultra3i')
        except:
            pass
    seg_regs = ["cs", "ds", "ss", "es", "fs", "gs", "tr", "ldtr"]
    for cls in x86_classes:
        for obj in all_objects(set, cls):
            for seg in seg_regs:
                try:
                    reg = getattr(obj, seg)
                    if reg[3]:
                        reg[8] = (reg[8] << 12) | 0xfff
                    setattr(obj, seg, reg)
                except:
                    pass
    for obj in all_objects(set, 'flash-memory'):
        try:
            obj.storage_ram = obj.storage_space.map[0][1]
        except:
            pass
        remove_attr(obj, 'storage_space')

def update_1039_to_1040(set):
    first = 1
    for cls in [x for x in x86_classes if not '486' in x]:
        for obj in all_objects(set, cls):
            # only on first processor, does not work on multi-machines
            obj.bsp = first
            first = 0

def update_1031_to_1032(set):
    # Old versions do not have the udma_enabled attribute. Assume
    # that udma is enabled if udma_mode is non-zero. The new
    # multiword_dma_mode and multiword_dma_enabled attributes
    # will have the correct default values (off and zero).
    for obj in (all_objects(set, 'ide-disk') + all_objects(set, 'ide-cdrom')):
        try:
            if obj.udma_mode:
                obj.udma_enabled = 1
        except:
            pass

def update_1030_to_1031(set):
    for obj in (all_objects(set, 'ultrasparc-ii')
                + all_objects(set, 'ultrasparc-iii')
                + all_objects(set, 'ultrasparc-iii+')):
        remove_attr(obj, 'fp_follow_errata_69')
        remove_attr(obj, 'no_unpriv_nucleus_ifetch')
    for obj in all_objects(set, 'text-console'):
        remove_attr(obj, 'xterm_args')
    for cls in ['ISP1040', 'ISP1040_SUN', 'ISP2200', 'ISP2200_SUN']:
        for obj in all_objects(set, cls):
            # mask to 32 bits
            obj.req_queue_addr &= 0xffffffff
            obj.res_queue_addr &= 0xffffffff
    remove_class_attr(set, 'ram', 'mapped_size')

def update_1019_to_1020(set):
    objs = (all_objects(set, 'ultrasparc-ii')
            + all_objects(set, 'ultrasparc-iii')
            + all_objects(set, 'ultrasparc-iii+')
            + all_objects(set, 'ultrasparc-v')
            + all_objects(set, 'serengeti-schizo')
            + all_objects(set, 'fiesta-tomatillo')
            + all_objects(set, 'sun4u-fhc')
            + all_objects(set, 'sunfire-sysio')
            + all_objects(set, 'sunfire-psycho')
            + all_objects(set, 'serengeti-console')
            + all_objects(set, 'serengeti-console-old'))
    if len(objs):
        irq_bus = pre_conf_object('irq_bus0', 'sparc-irq-bus')
        set['irq_bus0'] = irq_bus
        for obj in objs:
            obj.irq_bus = irq_bus
            remove_attr(obj, 'irq_objs')
            remove_attr(obj, 'cpu_objs')

def update_1010_to_1011(set):
    for cls in ['ISP1040', 'ISP1040_SUN', 'ISP2200', 'ISP2200_SUN']:
        remove_class_attr(set, cls, 'nvram')
        remove_class_attr(set, cls, 'nvram-extra-cycle')

def add_x86_tlb_1009(set, obj):
    name = obj.name + "_tlb"
    set[name] = tlb = pre_conf_object(name, 'x86-tlb')
    tlb.cpu = obj
    obj.tlb = tlb
    for t in ['itlb_large', 'dtlb_large', 'itlb_4k', 'dtlb_4k']:
        try:
            exec "tlb.%s = obj.%s" % (t, t)
            remove_attr(obj, t)
        except:
            pass


def update_1009_to_1010(set):
    remove_class_attr(set, 'ide-disk', 'debug_level')
    remove_class_attr(set, 'ide-cdrom', 'debug_level')
    remove_class_attr(set, 'spitfire-mmu', 'no_unpriv_nucleus_ifetch')
    remove_class_attr(set, 'cheetah-mmu', 'no_unpriv_nucleus_ifetch')
    remove_class_attr(set, 'cheetah+mmu', 'no_unpriv_nucleus_ifetch')
    remove_class_attr(set, 'text-console', 'add_title')
    for obj in all_objects(set, 'serengeti-console'):
        obj.__class_name__ = 'serengeti-console-old'
    for cls in x86_classes:
        for obj in all_objects(set, cls):
            add_x86_tlb_1009(set, obj)


#######################
install_configuration_update(1397, update_1396_to_1397)
install_configuration_update(1391, update_1390_to_1391)
install_configuration_update(1379, update_1378_to_1379)
install_configuration_update(1378, update_1377_to_1378)
install_configuration_update(1370, update_1370_to_1371)
install_configuration_update(1367, update_1367_to_1368)
install_configuration_update(1366, update_1366_to_1367)
install_configuration_update(1365, update_1365_to_1366)
install_configuration_update(1364, update_1364_to_1365)
install_configuration_update(1363, update_1363_to_1364)
install_configuration_update(1361, update_1361_to_1362)
install_configuration_update(1358, update_1358_to_1359)
install_configuration_update(1357, update_1357_to_1358)
install_configuration_update(1354, update_1354_to_1355)
install_configuration_update(1350, update_1350_to_1351)
install_configuration_update(1348, update_1348_to_1349)
install_configuration_update(1339, update_1340_to_1341)
install_configuration_update(1334, update_1334_to_1335)
install_configuration_update(1332, update_1332_to_1333)
install_configuration_update(1329, update_1329_to_1330)
install_configuration_update(1328, update_1328_to_1329)
install_configuration_update(1327, update_1327_to_1328)
install_configuration_update(1326, update_1326_to_1327)
install_configuration_update(1321, update_1321_to_1322)
install_configuration_update(1320, update_1320_to_1321)
install_configuration_update(1318, update_1318_to_1319)
install_configuration_update(1317, update_1317_to_1318)
install_configuration_update(1316, update_1316_to_1317)
install_configuration_update(1305, update_1304_to_1305)
install_configuration_update(1302, update_1302_to_1303)
install_configuration_update(1301, update_1301_to_1302)
install_configuration_update(1300, update_1300_to_1301)
install_configuration_update(1299, update_1299_to_1300)
install_configuration_update(1200, update_1200_to_1201)
install_configuration_update(1199, update_1199_to_1200)
install_configuration_update(1051, update_1051_to_1052)
install_configuration_update(1049, update_1049_to_1050)
install_configuration_update(1042, update_1042_to_1043)
install_configuration_update(1040, update_1040_to_1041)
install_configuration_update(1039, update_1039_to_1040)
install_configuration_update(1031, update_1031_to_1032)
install_configuration_update(1030, update_1030_to_1031)
install_configuration_update(1019, update_1019_to_1020)
install_configuration_update(1010, update_1010_to_1011)
install_configuration_update(1009, update_1009_to_1010)
