
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

pci_devices = {}
scsi_devices = {}
fc_ports = {}

if not SIM_get_quiet():
    print ("The pci_conf.py script is deprecated and replaced by the "
           "component system.")

class PCIConfException(Exception):
    pass

def pci_device_init(function, device, pci_bus_id, slot_no, slot_exists = 0, use_agp = 0):
    
    if SIM_initial_configuration_ok() != 0:
        SIM_command_has_problem()
        raise PCIConfException, "The function '%s' cannot be used once a configuration is loaded" % function

    if use_agp == 0:
        pci_str = "pci"
        PCI_str = "PCI"
    else:
        pci_str = "agp"
        PCI_str = "AGP"

    if type(slot_no) != type(1):
        SIM_command_has_problem()
        raise PCIConfException, "Cannot add %s: Slot number must be an integer" % device
    
    try:
        pci_bus = machine + pci_str + "_bus" + pci_bus_id
    except:
        SIM_command_has_problem()
        raise PCIConfException, "Illegal id specified for the " + PCI_str + " bus, use a string"

    if not object_exists(object_list[machine], pci_bus):
        SIM_command_has_problem()
        raise PCIConfException, "Cannot add %s: The %s bus %s doesn't exists" % (device, PCI_str, pci_bus)

    if slot_exists == 0:
        if pci_devices[pci_bus].has_key(slot_no):
            SIM_command_has_problem()
            raise PCIConfException, "Cannot add %s: Slot %d already used on %s bus %s" % (device, slot_no, PCI_str, pci_bus)
    else:
        if not pci_devices[pci_bus].has_key(slot_no):
            SIM_command_has_problem()
            raise PCIConfException, "Cannot add %s: Slot %d on %s bus %s is empty" % (device, slot_no, PCI_str, pci_bus)        

    return pci_bus

def add_north_bridge_430fx(new_pci_bus_id):
    add_north_bridge(new_pci_bus_id, "i82437fx")

def add_north_bridge_443bx(new_pci_bus_id, new_agp_bus_id, use_agp = 1):
    try:
        pci_bus = machine + "pci_bus" + new_pci_bus_id
    except:
        handle_error("Illegal id specified for the PCI bus, use a string")
        return
    if use_agp == 1:
        try:
            agp_bus = machine + "agp_bus" + new_agp_bus_id
        except:
            handle_error("Illegal id specified for the agp-bus, use a string")
            return

    add_north_bridge(new_pci_bus_id, "i82443bx")

    if use_agp == 1:
        
        if object_exists(object_list[machine], agp_bus):
            handle_error("Cannot add AGP bus: A PCI bus with the name %s already exists" % agp_bus)
            return

        pci_devices[agp_bus] = {}

        object_list[machine] += ([OBJECT(machine + "pci_to_agp0", "i82443bx_agp",
                                         pci_bus = OBJ(pci_bus),
                                         secondary_bus = OBJ(agp_bus))] +
                                 [OBJECT(agp_bus, "pci-bus",
                                         bridge = OBJ(machine + "pci_to_agp0"),
                                         memory_space = OBJ(agp_bus + "_mem"),
                                         conf_space = OBJ(agp_bus + "_conf"),
                                         io_space = OBJ(agp_bus + "_io"),
                                         pci_devices = [],
                                         interrupt = OBJ(machine + "pci_to_agp0"))] +
                                 [OBJECT(agp_bus + "_mem", "memory-space",
                                         map = [])] +
                                 [OBJECT(agp_bus + "_conf", "memory-space")] +
                                 [OBJECT(agp_bus + "_io", "memory-space",
                                         map = [])])

        pci_devices[pci_bus][1] = OBJ(machine + "pci_to_agp0")
        
        set_attribute(object_list[machine], machine + "north_bridge0", "agp_bridge", OBJ(machine + "pci_to_agp0"))
        devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
        devs += [[1, 0, OBJ(machine + "pci_to_agp0")]]
        set_attribute(object_list[machine], pci_bus, "pci_devices", devs)

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x22, OBJ(machine + "north_bridge0"), 0, 0x22, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)

def add_north_bridge_875P(new_pci_bus_id, new_agp_bus_id, new_csa_bus_id, use_agp = 1, use_csa = 1):
    try:
        pci_bus = machine + "pci_bus" + new_pci_bus_id
    except:
        handle_error("Illegal id specified for the PCI bus, use a string")
        return
    if use_agp == 1:
        try:
            agp_bus = machine + "agp_bus" + new_agp_bus_id
        except:
            handle_error("Illegal id specified for the agp-bus, use a string")
            return
        
    if use_csa == 1:
        try:
            csa_bus = machine + "csa_bus" + new_csa_bus_id
        except:
            handle_error("Illegal id specified for the csa-bus, use a string")
            return    
    
    # Start --- Taken from add_north_bridge ---
    try:
        pci_bus = machine + "pci_bus" + new_pci_bus_id
    except:
        handle_error("Illegal id specified for the PCI bus, use a string")
        return

    if object_exists(object_list[machine], machine + "north_bridge0"):
        handle_error("Only one north bridge supported")
        return
    
    if object_exists(object_list[machine], pci_bus):
        handle_error("The PCI bus %s already exists" % pci_bus)
        return
    
    have_north_bridge[machine] = 1
    pci_devices[pci_bus] = {}
    
    object_list[machine] += ([OBJECT(machine + "north_bridge0", "i82875P",
                                     pci_bus = OBJ(pci_bus))] +
                             [OBJECT(pci_bus, "pci-bus",
                                     bridge = OBJ(machine + "north_bridge0"),
                                     memory_space = OBJ(machine + "pci_mem0"),
                                     conf_space = OBJ(pci_bus + "_conf"),
                                     io_space = OBJ(pci_bus + "_io"),
                                     pci_devices = [[0, 0, OBJ(machine + "north_bridge0")]],
                                     # we need some kind of south bridge for interrupts
                                     interrupt = OBJ(machine + "pci_to_isa0"))] +
                             [OBJECT(pci_bus + "_io", "memory-space")] +
                             [OBJECT(pci_bus + "_conf", "memory-space")])

    pci_devices[pci_bus][0] = machine + "north_bridge0"
    
    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0xcf8, OBJ(machine + "north_bridge0"), 0, 0xcf8, 4],
            [0xcf9, OBJ(machine + "north_bridge0"), 0, 0xcf9, 2],
            [0xcfa, OBJ(machine + "north_bridge0"), 0, 0xcfa, 2],
            [0xcfb, OBJ(machine + "north_bridge0"), 0, 0xcfb, 1],
            [0xcfc, OBJ(machine + "north_bridge0"), 0, 0xcfc, 4],
            [0xcfd, OBJ(machine + "north_bridge0"), 0, 0xcfd, 2],
            [0xcfe, OBJ(machine + "north_bridge0"), 0, 0xcfe, 2],
            [0xcff, OBJ(machine + "north_bridge0"), 0, 0xcff, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)
    set_attribute(object_list[machine], machine + "port_mem0",
                  "default_target", [OBJ(pci_bus + "_io"), 0, 0, OBJ(pci_bus + "_io")])
    # End --- Taken from add_north_bridge ---

    if use_agp == 1:
        
        if object_exists(object_list[machine], agp_bus):
            handle_error("Cannot add AGP bus: A PCI bus with the name %s already exists" % agp_bus)
            return

        pci_devices[agp_bus] = {}

        object_list[machine] += ([OBJECT(machine + "pci_to_agp0", "i82875P_agp",
                                         pci_bus = OBJ(pci_bus),
                                         secondary_bus = OBJ(agp_bus))] +
                                 [OBJECT(agp_bus, "pci-bus",
                                         bridge = OBJ(machine + "pci_to_agp0"),
                                         memory_space = OBJ(agp_bus + "_mem"),
                                         conf_space = OBJ(agp_bus + "_conf"),
                                         io_space = OBJ(agp_bus + "_io"),
                                         pci_devices = [],
                                         interrupt = OBJ(machine + "pci_to_agp0"))] +
                                 [OBJECT(agp_bus + "_mem", "memory-space",
                                         map = [])] +
                                 [OBJECT(agp_bus + "_conf", "memory-space")] +
                                 [OBJECT(agp_bus + "_io", "memory-space",
                                         map = [])])

        pci_devices[pci_bus][1] = OBJ(machine + "pci_to_agp0")

        set_attribute(object_list[machine], machine + "north_bridge0", "agp_bridge", OBJ(machine + "pci_to_agp0"))
        
        devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
        devs += [[1, 0, OBJ(machine + "pci_to_agp0")]]
        set_attribute(object_list[machine], pci_bus, "pci_devices", devs)

    if use_csa == 1:
        
        if object_exists(object_list[machine], csa_bus):
            handle_error("Cannot add CSA bus: A PCI bus with the name %s already exists" % csa_bus)
            return

        pci_devices[csa_bus] = {}

        object_list[machine] += ([OBJECT(machine + "pci_to_csa0", "i82875P_csa",
                                         pci_bus = OBJ(pci_bus),
                                         secondary_bus = OBJ(csa_bus))] +
                                 [OBJECT(csa_bus, "pci-bus",
                                         bridge = OBJ(machine + "pci_to_csa0"),
                                         memory_space = OBJ(machine + "pci_mem0"),
                                         conf_space = OBJ(csa_bus + "_conf"),
                                         io_space = OBJ(pci_bus + "_io"),
                                         pci_devices = [],
                                         interrupt = OBJ(machine + "pci_to_csa0"))] +
                                 [OBJECT(csa_bus + "_conf", "memory-space")])

        #pci_devices[pci_bus][1] = OBJ(machine + "pci_to_csa0")

        set_attribute(object_list[machine], machine + "north_bridge0", "csa_bridge", OBJ(machine + "pci_to_csa0"))
        
        #devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
        #devs += [[1, 0, OBJ(machine + "pci_to_csa0")]]
        #set_attribute(object_list[machine], pci_bus, "pci_devices", devs)
    
    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x22, OBJ(machine + "north_bridge0"), 0, 0x22, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_north_bridge(new_pci_bus_id, north_bridge_class):
    if configuration_loaded("add_north_bridge"):
        return

    try:
        pci_bus = machine + "pci_bus" + new_pci_bus_id
    except:
        handle_error("Illegal id specified for the PCI bus, use a string")
        return

    if object_exists(object_list[machine], machine + "north_bridge0"):
        handle_error("Only one north bridge supported")
        return

    if object_exists(object_list[machine], pci_bus):
        handle_error("The PCI bus %s already exists" % pci_bus)
        return

    have_north_bridge[machine] = 1
    pci_devices[pci_bus] = {}

    object_list[machine] += ([OBJECT(machine + "north_bridge0", north_bridge_class,
                                     memory = OBJ(machine + "pci_mem0"),
                                     pci_bus = OBJ(pci_bus))] +
                             [OBJECT(pci_bus, "pci-bus",
                                     bridge = OBJ(machine + "north_bridge0"),
                                     memory_space = OBJ(machine + "pci_mem0"),
                                     conf_space = OBJ(pci_bus + "_conf"),
                                     io_space = OBJ(pci_bus + "_io"),
                                     pci_devices = [[0, 0, OBJ(machine + "north_bridge0")]],
                                     # we need some kind of south bridge for interrupts
                                     interrupt = OBJ(machine + "pci_to_isa0"))] +
                             [OBJECT(pci_bus + "_io", "memory-space")] +
                             [OBJECT(pci_bus + "_conf", "memory-space")])

    pci_devices[pci_bus][0] = machine + "north_bridge0"

    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0xcf8, OBJ(machine + "north_bridge0"), 0, 0xcf8, 4],
            [0xcf9, OBJ(machine + "north_bridge0"), 0, 0xcf9, 2],
            [0xcfa, OBJ(machine + "north_bridge0"), 0, 0xcfa, 2],
            [0xcfb, OBJ(machine + "north_bridge0"), 0, 0xcfb, 1],
            [0xcfc, OBJ(machine + "north_bridge0"), 0, 0xcfc, 4],
            [0xcfd, OBJ(machine + "north_bridge0"), 0, 0xcfd, 2],
            [0xcfe, OBJ(machine + "north_bridge0"), 0, 0xcfe, 2],
            [0xcff, OBJ(machine + "north_bridge0"), 0, 0xcff, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)
    set_attribute(object_list[machine], machine + "port_mem0",
                  "default_target", [OBJ(pci_bus + "_io"), 0, 0, OBJ(pci_bus + "_io")])


# If you use non-default values for the PCI to host interrupt mapping,
# remember to also change the DSDT and the BIOS.
def add_south_bridge_piix4(pci_bus_id, sci_irq = 9, pci_irqa = 10, pci_irqb = 11, pci_irqc = 10, pci_irqd = 11, use_usb = 1, use_power_management = 1):
    add_south_bridge_piix_common("piix4", pci_bus_id, sci_irq, pci_irqa, pci_irqb, pci_irqc, pci_irqd, use_usb, use_power_management)

def add_south_bridge_piix(pci_bus_id):
    add_south_bridge_piix_common("piix", pci_bus_id, 0, 0, 0, 0, 0, 0, 0)

def add_south_bridge_piix_common(piix_class, pci_bus_id, sci_irq = 9, pci_irqa = 10, pci_irqb = 11, pci_irqc = 10, pci_irqd = 11, use_usb = 1, use_power_management = 1):

    try:
        pci_bus = pci_device_init("add_south_bridge_" + piix_class, piix_class, pci_bus_id, 7)
    except PCIConfException, msg:
        handle_error(msg)
        return

    if not object_exists(object_list[machine], machine + "pic0"):
        handle_error("The %s south bridge needs the legacy devices" % piix_class)
        return

    if not object_exists(object_list[machine], machine + "ide0"):
        handle_error("The %s south bridge needs the IDE controller" % piix_class)
        return

    if object_exists(object_list[machine], machine + "pci_to_isa0"):
        handle_error("Only one south bridge supported")
        return

    have_south_bridge[machine] = 1

    object_list[machine] += ([OBJECT(machine + "pci_to_isa0", piix_class + "_isa",
                                     pci_bus = OBJ(pci_bus),
                                     irq_dev = OBJ(machine + "isa0"),
                                     pirqrca = pci_irqa,
                                     pirqrcb = pci_irqb,
                                     pirqrcc = pci_irqc,
                                     pirqrcd = pci_irqd)] +
                             [OBJECT(machine + "pci_to_ide0", piix_class + "_ide",
                                     pci_bus = OBJ(pci_bus),
                                     memory = OBJ(machine + "pci_mem0"))])

    if use_usb:
        object_list[machine] += ([OBJECT(machine + "pci_to_usb0", "piix4_usb",
                                         pci_bus = OBJ(pci_bus))])

    if use_power_management:
        object_list[machine] += ([OBJECT(machine + "apm0", "apm",
                                         pm = OBJ(machine + "power_management0"))] +
                                 [OBJECT(machine + "power_management0", "piix4_power",
                                         queue = OBJ(machine + "cpu0"),
                                         pci_bus = OBJ(pci_bus),
                                         sci_irq_level = sci_irq,
                                         sci_irq_dev = OBJ(machine + "isa0"))])

    pci_devices[pci_bus][7] = machine + "pci_to_isa0"

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs += [[7, 0, OBJ(machine + "pci_to_isa0")],
             [7, 1, OBJ(machine + "pci_to_ide0")]]
    next_function = 2
    if use_usb:
        devs += [[7, next_function, OBJ(machine + "pci_to_usb0")]]
        next_function = next_function + 1
    if use_power_management:
        devs += [[7, next_function, OBJ(machine + "power_management0")]]
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)

    if object_exists(object_list[machine], machine + "ide0"):
        set_attribute(object_list[machine], machine + "pci_to_ide0", "primary_ide", OBJ(machine + "ide0"))
        set_attribute(object_list[machine], machine + "ide0", "bus_master_dma", OBJ(machine + "pci_to_ide0"))

    if object_exists(object_list[machine], machine + "ide1"):
        set_attribute(object_list[machine], machine + "pci_to_ide0", "secondary_ide", OBJ(machine + "ide1"))
        set_attribute(object_list[machine], machine + "ide1", "bus_master_dma", OBJ(machine + "pci_to_ide0"))

    if use_power_management:
        map = get_attribute(object_list[machine], machine + "port_mem0", "map")
        map += [[0xb2, OBJ(machine + "apm0"), 0, 0, 2],
                [0x8000, OBJ(machine + "power_management0"), 0, 0x0, 1],
                [0x8001, OBJ(machine + "power_management0"), 0, 0x1, 1],
                [0x8002, OBJ(machine + "power_management0"), 0, 0x2, 1],
                [0x8003, OBJ(machine + "power_management0"), 0, 0x3, 1],
                [0x8004, OBJ(machine + "power_management0"), 0, 0x4, 1],
                [0x8005, OBJ(machine + "power_management0"), 0, 0x5, 1],
                [0x8006, OBJ(machine + "power_management0"), 0, 0x6, 1],
                [0x8007, OBJ(machine + "power_management0"), 0, 0x7, 1],
                [0x8008, OBJ(machine + "power_management0"), 0, 0x8, 1],
                [0x8009, OBJ(machine + "power_management0"), 0, 0x9, 1],
                [0x800a, OBJ(machine + "power_management0"), 0, 0xa, 1],
                [0x800b, OBJ(machine + "power_management0"), 0, 0xb, 1],
                [0x800c, OBJ(machine + "power_management0"), 0, 0xc, 1],
                [0x800d, OBJ(machine + "power_management0"), 0, 0xd, 1],
                [0x800e, OBJ(machine + "power_management0"), 0, 0xe, 1],
                [0x800f, OBJ(machine + "power_management0"), 0, 0xf, 1],
                [0x8010, OBJ(machine + "power_management0"), 0, 0x10, 1],
                [0x8011, OBJ(machine + "power_management0"), 0, 0x11, 1],
                [0x8012, OBJ(machine + "power_management0"), 0, 0x12, 1],
                [0x8013, OBJ(machine + "power_management0"), 0, 0x13, 1],
                [0x8014, OBJ(machine + "power_management0"), 0, 0x14, 1],
                [0x8015, OBJ(machine + "power_management0"), 0, 0x15, 1],
                [0x8016, OBJ(machine + "power_management0"), 0, 0x16, 1],
                [0x8017, OBJ(machine + "power_management0"), 0, 0x17, 1],
                [0x8018, OBJ(machine + "power_management0"), 0, 0x18, 1],
                [0x8019, OBJ(machine + "power_management0"), 0, 0x19, 1],
                [0x801a, OBJ(machine + "power_management0"), 0, 0x1a, 1],
                [0x801b, OBJ(machine + "power_management0"), 0, 0x1b, 1],
                [0x801c, OBJ(machine + "power_management0"), 0, 0x1c, 1],
                [0x801d, OBJ(machine + "power_management0"), 0, 0x1d, 1],
                [0x801e, OBJ(machine + "power_management0"), 0, 0x1e, 1],
                [0x801f, OBJ(machine + "power_management0"), 0, 0x1f, 1],
                [0x8020, OBJ(machine + "power_management0"), 0, 0x20, 1],
                [0x8021, OBJ(machine + "power_management0"), 0, 0x21, 1],
                [0x8022, OBJ(machine + "power_management0"), 0, 0x22, 1],
                [0x8023, OBJ(machine + "power_management0"), 0, 0x23, 1],
                [0x8024, OBJ(machine + "power_management0"), 0, 0x24, 1],
                [0x8025, OBJ(machine + "power_management0"), 0, 0x25, 1],
                [0x8026, OBJ(machine + "power_management0"), 0, 0x26, 1],
                [0x8027, OBJ(machine + "power_management0"), 0, 0x27, 1],
                [0x8028, OBJ(machine + "power_management0"), 0, 0x28, 1],
                [0x8029, OBJ(machine + "power_management0"), 0, 0x29, 1],
                [0x802a, OBJ(machine + "power_management0"), 0, 0x2a, 1],
                [0x802b, OBJ(machine + "power_management0"), 0, 0x2b, 1],
                [0x802c, OBJ(machine + "power_management0"), 0, 0x2c, 1],
                [0x802d, OBJ(machine + "power_management0"), 0, 0x2d, 1],
                [0x802e, OBJ(machine + "power_management0"), 0, 0x2e, 1],
                [0x802f, OBJ(machine + "power_management0"), 0, 0x2f, 1],
                [0x8030, OBJ(machine + "power_management0"), 0, 0x30, 1],
                [0x8031, OBJ(machine + "power_management0"), 0, 0x31, 1],
                [0x8032, OBJ(machine + "power_management0"), 0, 0x32, 1],
                [0x8033, OBJ(machine + "power_management0"), 0, 0x33, 1],
                [0x8034, OBJ(machine + "power_management0"), 0, 0x34, 1],
                [0x8035, OBJ(machine + "power_management0"), 0, 0x35, 1],
                [0x8036, OBJ(machine + "power_management0"), 0, 0x36, 1],
                [0x8037, OBJ(machine + "power_management0"), 0, 0x37, 1]]
        set_attribute(object_list[machine], machine + "port_mem0", "map", map)

# NOT SUPPORTED - FOR TESTING ONLY!
def add_south_bridge_md1535d(pci_bus_id):
    
    try:
        pci_bus = pci_device_init("add_south_bridge_md1535d", "MD1535D", pci_bus_id, 7)
    except PCIConfException, msg:
        handle_error(msg)
        return
    
    if not object_exists(object_list[machine], machine + "pic0"):
        handle_error("The MD1535D south bridge needs the legacy devices")
        return
    
    if not object_exists(object_list[machine], machine + "ide0"):
        handle_error("The MD1535D south bridge needs the IDE controller")
        return
    
    if object_exists(object_list[machine], machine + "pci_to_isa0"):
        handle_error("Only one south bridge supported")
        return
    
    have_south_bridge[machine] = 1
    
    object_list[machine] += ([OBJECT("pci_to_isa0", "MD1535D-isa",
                                     pci_bus = OBJ(pci_bus),
                                     pci_to_isa_irq = [9, 10, 11, 12],
                                     irq_dev = OBJ(machine + "isa0"))] +
                             [OBJECT("pci_to_pm0", "MD1535D-power",
                                     pci_bus = OBJ(pci_bus))] +
                             [OBJECT("pci_to_ide0", "MD1535D-ide",
                                     pci_bus = OBJ(pci_bus),
                                     memory = OBJ(machine + "pci_mem0"))] +
                             [OBJECT("cfg", "MD1535D-cfg")] +
                             [OBJECT("smb", "MD1535D-smb")])
    
    pci_devices[pci_bus][6] = OBJ(machine + "pci_to_pm0")
    pci_devices[pci_bus][7] = OBJ(machine + "pci_to_isa0")
    pci_devices[pci_bus][13] = OBJ(machine + "pci_to_ide0")
    
    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs += [[ 6, 0, OBJ(machine + "pci_to_pm0")],
             [ 7, 0, OBJ(machine + "pci_to_isa0")],
             [13, 0, OBJ(machine + "pci_to_ide0")]]
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)
    
    if object_exists(object_list[machine], machine + "ide0"):
        set_attribute(object_list[machine], machine + "pci_to_ide0", "primary_ide", OBJ(machine + "ide0"))
        set_attribute(object_list[machine], machine + "ide0", "bus_master_dma", OBJ(machine + "pci_to_ide0"))
    
    if object_exists(object_list[machine], machine + "ide1"):
        set_attribute(object_list[machine], machine + "pci_to_ide0", "secondary_ide", OBJ(machine + "ide1"))
        set_attribute(object_list[machine], machine + "ide1", "bus_master_dma", OBJ(machine + "pci_to_ide0"))
    
    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0x3f0, OBJ("cfg"),  0, 0, 2],
            # System Management Bus
            [0x600, OBJ("smb"),  0, 0, 1],
            [0x601, OBJ("smb"),  0, 1, 1],
            [0x602, OBJ("smb"),  0, 2, 1],
            [0x603, OBJ("smb"),  0, 3, 1],
            [0x604, OBJ("smb"),  0, 4, 1],
            [0x605, OBJ("smb"),  0, 5, 1],
            [0x606, OBJ("smb"),  0, 6, 1],
            [0x607, OBJ("smb"),  0, 7, 1],
            # ACPI
            [0x800, OBJ("cfg"),  0, 0, 2],  # temporary: ACPI
            [0x802, OBJ("cfg"),  0, 0, 2],
            [0x804, OBJ("cfg"),  0, 0, 2],
            [0x828, OBJ("cfg"),  0, 0, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)


def add_pci_bridge_i21152(pci_bus_id, slot_no, new_pci_bus_id):
    try:
        pci_bus = pci_device_init("add_pci_bridge_i21152", "i21152", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    try:
        sub_bus = machine + "pci_bus" + new_pci_bus_id
    except:
        handle_error("Illegal id specified for the new PCI bus, use a string")
        return
    
    if object_exists(object_list[machine], sub_bus):
        handle_error("Cannot add the i21152 bridge: The PCI bus %s already exists" % sub_bus)
        return

    dev_name = machine + "bridge" + pci_bus_id + "_" + `slot_no`

    pci_devices[sub_bus] = {}

    object_list[machine] += ([OBJECT(dev_name, "i21152",
                                     pci_bus = OBJ(pci_bus),
                                     secondary_bus = OBJ(sub_bus),
                                     queue = OBJ(machine + "cpu0"))] +
                             [OBJECT(sub_bus, "pci-bus",
                                     bridge = OBJ(dev_name),
                                     pci_devices = [],
                                     memory_space = OBJ(sub_bus + "_mem"),
                                     conf_space = OBJ(sub_bus + "_conf"),
                                     io_space = OBJ(sub_bus + "_io"),
                                     interrupt = OBJ(dev_name))] +
                             [OBJECT(sub_bus + "_conf", "memory-space")] +
                             [OBJECT(sub_bus + "_io", "memory-space")] +
                             [OBJECT(sub_bus + "_mem", "memory-space")])

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)


def add_pci_dec21143(pci_bus_id, slot_no, mac_address):

    try:
        pci_bus = pci_device_init("add_pci_dec21143", "DEC21143", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    dev_name = machine + "dec" + pci_bus_id + "_" + `slot_no`

    pci_devices[pci_bus][slot_no] = dev_name

    object_list[machine] += [OBJECT(dev_name, "DEC21143",
                                    queue = OBJ(machine + "cpu0"),
                                    recorder = OBJ(machine + "rec0"),
                                    mac__address = mac_address,
                                    pci_bus = OBJ(pci_bus))]

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)


def add_pci_voodoo3(pci_bus_id, slot_no, gfx_console = 1, text_console = 0):
    
    try:
        pci_bus = pci_device_init("add_pci_voodoo3", "voodoo3", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    if gfx_console == 1 and text_console == 1:
        handle_error("Cannot use both text and graphics console at once")
        return

    bios_file = "voodoo3-pci-bios.bin"
    bios_size = 0x8000
    if not SIM_lookup_file(bios_file):
        print "Voodoo3 PCI BIOS '%s' not found." % bios_file
        handle_error("Cannot use Voodoo3 PCI device without any VGA BIOS.")
        return
    
    dev_name = machine + "vga" + `num_gfx_consoles[machine]`

    pci_devices[pci_bus][slot_no] = dev_name

    object_list[machine] += ([OBJECT(dev_name, "voodoo3",
                                     queue = OBJ(machine + "cpu0"),
                                     expansion_rom = [OBJ(dev_name + "_prom"), bios_size, 0],
                                     image = OBJ(dev_name + "_image"),
                                     pci_bus = OBJ(pci_bus))] +
                             [OBJECT(dev_name + "_prom", "rom",
                                     image = OBJ(dev_name + "_prom_image"))] +
                             [OBJECT(dev_name + "_image", "image",
                                     size = 0x1000000,
                                     queue = OBJ(machine + "cpu0"))] +
                             [OBJECT(dev_name + "_prom_image", "image",
                                     size = bios_size,
                                     files = [[bios_file, "ro", 0, bios_size]],
                                     queue = OBJ(machine + "cpu0"))])

    # the following line is only needed for BIOSs without full PCI support
    #add_vga_bios(vga_bios = bios_file, bios_size = 32768)
    add_vga_generic(gfx_console, text_console, video_interface = 1)

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)


def add_agp_voodoo3(agp_bus_id, slot_no, gfx_console = 1, text_console = 0):
    
    try:
        agp_bus = pci_device_init("add_agp_voodoo3", "voodoo3-agp", agp_bus_id, slot_no, use_agp = 1)
    except PCIConfException, msg:
        handle_error(msg)
        return

    if gfx_console == 1 and text_console == 1:
        handle_error("Cannot use both text and graphics console at once")
        return

    bios_file = "voodoo3-agp-bios.bin"
    bios_size = 0x10000
    if not SIM_lookup_file(bios_file):
        print "Voodoo3 AGP BIOS '%s' not found." % bios_file
        handle_error("Cannot use Voodoo3 AGP device without any VGA BIOS.")
        return
        
    dev_name = machine + "vga" + `num_gfx_consoles[machine]`

    pci_devices[agp_bus][slot_no] = dev_name

    object_list[machine] += ([OBJECT(dev_name, "voodoo3-agp",
                                     queue = OBJ(machine + "cpu0"),
                                     expansion_rom = [OBJ(dev_name + "_prom"), bios_size, 0],
                                     image = OBJ(dev_name + "_image"),
                                     pci_bus = OBJ(agp_bus))] +
                             [OBJECT(dev_name + "_prom", "rom",
                                     image = OBJ(dev_name + "_prom_image"))] +
                             [OBJECT(dev_name + "_image", "image",
                                     size = 0x1000000,
                                     queue = OBJ(machine + "cpu0"))] +
                             [OBJECT(dev_name + "_prom_image", "image",
                                     size = bios_size,
                                     files = [[bios_file, "ro", 0, bios_size]],
                                     queue = OBJ(machine + "cpu0"))])

    # the following line is only needed for BIOSs without full PCI support
    #add_vga_bios(vga_bios = bios_file, bios_size = bios_size)
    add_vga_generic(gfx_console, text_console, video_interface = 1, mem_space=agp_bus+"_mem", port_space=agp_bus+"_io")
    
    devs = get_attribute(object_list[machine], agp_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], agp_bus, "pci_devices", devs)


def add_pci_ragexl(pci_bus_id, slot_no, gfx_console = 1, text_console = 0):
    
    try:
        pci_bus = pci_device_init("add_pci_ragexl", "Rage XL", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    if gfx_console == 1 and text_console == 1:
        handle_error("Cannot use both text and graphics console at once")
        return

    bios_file = "ragexl-bios.bin"
    bios_size = 0x8000
    if not SIM_lookup_file(bios_file):
        print "Rage XL PCI BIOS '%s' not found." % bios_file
        handle_error("Cannot use Rage XL PCI device without any VGA BIOS.")
        return

    dev_name = machine + "vga" + `num_gfx_consoles[machine]`

    pci_devices[pci_bus][slot_no] = dev_name
    
    object_list[machine] += ([OBJECT(dev_name, "ragexl",
                                     expansion_rom = [OBJ(dev_name + "_prom"), bios_size, 0],
                                     queue = OBJ(machine + "cpu0"),
                                     pci_bus = OBJ(pci_bus))] +
                             [OBJECT(dev_name + "_prom", "rom",
                                     image = OBJ(dev_name + "_prom_image"))] +
                             [OBJECT(dev_name + "_prom_image", "image",
                                     size = bios_size,
                                     files = [[bios_file, "ro", 0, bios_size]],
                                     queue = OBJ(machine + "cpu0"))])
    
    # the following line is only needed for BIOSs without full PCI support
    #add_vga_bios(vga_bios = bios_file, bios_size = bios_size)
    add_vga_generic(gfx_console, text_console, video_interface = 0)
    
    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)


def add_pci_sym53c875(pci_bus_id, slot_no):

    try:
        pci_bus = pci_device_init("add_pci_sym53c875", "SYM53C875", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    bios_file = "sym53c875.bin"
    bios_size = 0x8000
    
    dev_name = machine + "sym" + pci_bus_id + "_" + `slot_no`
    sb_name = machine + "sb" + pci_bus_id + "_" + `slot_no`

    pci_devices[pci_bus][slot_no] = dev_name

    scsi_devices[sb_name] = {}
    scsi_devices[sb_name][7] = dev_name
        
    object_list[machine] += ([OBJECT(dev_name, "SYM53C875",
                                     queue = OBJ(machine + "cpu0"),
                                     pci_bus = OBJ(pci_bus),
                                     scsi_bus = OBJ(sb_name))] +
                             [OBJECT(sb_name, "scsi-bus",
                                     targets = [[7, OBJ(dev_name), 0]],
                                     queue = OBJ(machine + "cpu0"))])

    if SIM_lookup_file(bios_file):
        set_attribute(object_list[machine], dev_name,
                      "expansion_rom", [OBJ(dev_name + "_prom"), bios_size, 0])
        object_list[machine] += ([OBJECT(dev_name + "_prom", "rom",
                                         image = OBJ(dev_name + "_prom_image"))] +
                                 [OBJECT(dev_name + "_prom_image", "image",
                                         size = bios_size,
                                         files = [[bios_file, "ro", 0, bios_size]],
                                         queue = OBJ(machine + "cpu0"))])
    else:
        print "Adding SYM53C875 without SCSI BIOS."

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)


def add_pci_sym53c810(pci_bus_id, slot_no):

    try:
        pci_bus = pci_device_init("add_pci_sym53c810", "SYM53C810", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    # The 810 device does not support on-board SCSI BIOS, but some
    # motherboards have a SYMlogic compatible BIOS.
    
    dev_name = machine + "sym" + pci_bus_id + "_" + `slot_no`
    sb_name = machine + "sb" + pci_bus_id + "_" + `slot_no`

    pci_devices[pci_bus][slot_no] = dev_name

    scsi_devices[sb_name] = {}
    scsi_devices[sb_name][7] = dev_name
    
    object_list[machine] += ([OBJECT(dev_name, "SYM53C810",
                                     queue = OBJ(machine + "cpu0"),
                                     pci_bus = OBJ(pci_bus),
                                     scsi_bus = OBJ(sb_name))] +
                             [OBJECT(sb_name, "scsi-bus",
                                     targets = [[7, OBJ(dev_name), 0]],
                                     queue = OBJ(machine + "cpu0"))])

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)


def add_pci_isp1040(pci_bus_id, slot_no):

    try:
        pci_bus = pci_device_init("add_pci_isp1040", "ISP1040", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    bios_file = "isp1040.bin"
    bios_size = 0x10000

    dev_name = machine + "isp" + pci_bus_id + "_" + `slot_no`
    sb_name = machine + "sb" + pci_bus_id + "_" + `slot_no`

    pci_devices[pci_bus][slot_no] = dev_name

    scsi_devices[sb_name] = {}
    scsi_devices[sb_name][7] = dev_name
        
    object_list[machine] += ([OBJECT(dev_name, "ISP1040",
                                     queue = OBJ(machine + "cpu0"),
                                     scsi_id = 7,
                                     pci_bus = OBJ(pci_bus),
                                     scsi_bus = OBJ(sb_name))] +
                             [OBJECT(sb_name, "scsi-bus",
                                     targets = [[7, OBJ(dev_name), 0]],
                                     queue = OBJ(machine + "cpu0"))])

    if SIM_lookup_file(bios_file):
        set_attribute(object_list[machine], dev_name,
                      "expansion_rom", [OBJ(dev_name + "_prom"), bios_size, 0])
        object_list[machine] += ([OBJECT(dev_name + "_prom", "rom",
                                         image = OBJ(dev_name + "_prom_image"))] +
                                 [OBJECT(dev_name + "_prom_image", "image",
                                         size = bios_size,
                                         files = [[bios_file, "ro", 0, bios_size]],
                                         queue = OBJ(machine + "cpu0"))])
    else:
        print "Adding ISP1040 without SCSI BIOS."

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)


def add_pci_isp2200(pci_bus_id, slot_no, loop_id):

    try:
        pci_bus = pci_device_init("add_pci_isp2200", "ISP2200", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    bios_file = "isp2200.bin"
    bios_size = 0x20000

    dev_name = machine + "qlc" + pci_bus_id + "_" + `slot_no`

    pci_devices[pci_bus][slot_no] = dev_name

    fc_ports[dev_name] = {}
    fc_ports[dev_name][loop_id] = dev_name

    object_list[machine] += [OBJECT(dev_name, "ISP2200",
                                    queue = OBJ(machine + "cpu0"),
                                    loop__id = loop_id,
                                    pci_bus = OBJ(pci_bus))]

    if SIM_lookup_file(bios_file):
        set_attribute(object_list[machine], dev_name,
                      "expansion_rom", [OBJ(dev_name + "_prom"), bios_size, 0])
        object_list[machine] += ([OBJECT(dev_name + "_prom", "rom",
                                         image = OBJ(dev_name + "_prom_image"))] +
                                 [OBJECT(dev_name + "_prom_image", "image",
                                         size = bios_size,
                                         files = [[bios_file, "ro", 0, bios_size]],
                                         queue = OBJ(machine + "cpu0"))])
    else:
        print "Adding ISP2200 without SCSI BIOS."

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)


def add_scsi_disk(pci_bus_id, slot_no,  scsi_target, geometry = None, size = None, files = ""):

    try:
        pci_bus = pci_device_init("add_scsi_disk", "SCSI disk", pci_bus_id, slot_no, slot_exists = 1)
    except PCIConfException, msg:
        handle_error(msg)
        return

    if geometry:
        print "add_scsi_disk(): Warning, using obsolete argument 'geometry'"
        g_size = geometry[0] * geometry[1] * geometry[2] * 512
        if size and g_size != size:
            handle_error("add_scsi_disk(): Geometry and size does not match")
            return
        size = g_size
    elif not size:
        # check for size since is is still optional
        handle_error("add_scsi_disk(): Size of disk not specified")
        return        
    
    ctrl_name = pci_devices[pci_bus][slot_no]
    sb_name = machine + "sb" + pci_bus_id + "_" + `slot_no`
    disk_name = machine + "sd" + pci_bus_id + "_" + `slot_no` + "_" + `scsi_target`

    if not object_exists(object_list[machine], sb_name):
        handle_error("Cannot add SCSI disk: No SCSI bus found in slot %d on PCI bus %s" % (slot_no, pci_bus))
        return

    if scsi_devices[sb_name].has_key(scsi_target):
        handle_error("Cannot add SCSI disk: SCSI target %d already occupied on SCSI bus %s" % (scsi_target, sb_name))
        return

    scsi_devices[sb_name][scsi_target] = disk_name

    object_list[machine] += ([OBJECT(disk_name, "scsi-disk",
                                     queue = OBJ(machine + "cpu0"),
                                     scsi_bus = OBJ(sb_name),
                                     geometry = [size / 512, 1, 1],
                                     scsi_target = scsi_target,
                                     image = OBJ(disk_name + "_image"))] +
                             [OBJECT(disk_name + "_image", "image",
                                     size = size,
                                     queue = OBJ(machine + "cpu0"))])
    if files != "":
        set_attribute(object_list[machine], disk_name + "_image", "files", files)

    tgts = get_attribute(object_list[machine], sb_name, "targets")
    tgts += [[scsi_target, OBJ(disk_name), 0]]
    set_attribute(object_list[machine], sb_name, "targets", tgts)


def add_scsi_cdrom(pci_bus_id, slot_no,  scsi_target, file = ""):

    try:
        pci_bus = pci_device_init("add_scsi_cdrom", "SCSI CD-ROM", pci_bus_id, slot_no, slot_exists = 1)
    except PCIConfException, msg:
        handle_error(msg)
        return

    ctrl_name = pci_devices[pci_bus][slot_no]
    sb_name = machine + "sb" + pci_bus_id + "_" + `slot_no`
    cd_name = machine + "cd" + pci_bus_id + "_" + `slot_no` + "_" + `scsi_target`
    hcd_name = machine + "host_cd" + pci_bus_id + "_" + `slot_no` + "_" + `scsi_target`
    fcd_name = machine + "file_cd" + pci_bus_id + "_" + `slot_no` + "_" + `scsi_target`

    if not object_exists(object_list[machine], sb_name):
        handle_error("Cannot add SCSI CD-ROM: No SCSI bus found in slot %d on PCI bus %s" % (slot_no, pci_bus))
        return

    if scsi_devices[sb_name].has_key(scsi_target):
        handle_error("Cannot add SCSI CD-ROM: SCSI target %d already occupied on SCSI bus %s" % (scsi_target, sb_name))
        return

    scsi_devices[sb_name][scsi_target] = cd_name

    object_list[machine] += [OBJECT(cd_name, "scsi-cdrom",
                                    queue = OBJ(machine + "cpu0"),
                                    scsi_bus = OBJ(sb_name),
                                    scsi_target = scsi_target)]
    if file == "":
        pass
    elif string.find(file, "/dev/") == 0 or string.find(file, "/vol/rdsk/") == 0:
        object_list[machine] += [OBJECT(hcd_name, "host-cdrom", file = file)]
        set_attribute(object_list[machine], cd_name, "cd-media", OBJ(hcd_name))
        print "setting media %s" % hcd_name
    else:
        object_list[machine] += [OBJECT(fcd_name, "file-cdrom", file = file)]
        set_attribute(object_list[machine], cd_name, "cd-media", OBJ(hcd_name))
        print "setting media %s" % fcd_name

    tgts = get_attribute(object_list[machine], sb_name, "targets")
    tgts += [[scsi_target, OBJ(cd_name), 0]]
    set_attribute(object_list[machine], sb_name, "targets", tgts)


def add_fc_disk(pci_bus_id, slot_no, loop_id, node_name, port_name, geometry = None, size = None, files = ""):

    try:
        pci_bus = pci_device_init("add_fc_disk", "FC disk", pci_bus_id, slot_no, slot_exists = 1)
    except PCIConfException, msg:
        handle_error(msg)
        return

    if geometry:
        print "add_fc_disk(): Warning, using obsolete argument 'geometry'"
        g_size = geometry[0] * geometry[1] * geometry[2] * 512
        if size and g_size != size:
            handle_error("add_fc_disk(): Geometry and size does not match")
            return
        size = g_size
    elif not size:
        # check for size since is is still optional
        handle_error("add_fc_disk(): Size of disk not specified")
        return        

    ctrl_name = pci_devices[pci_bus][slot_no]
    disk_name = machine + "fc" + pci_bus_id + "_" + `slot_no` + "_" + `loop_id`

    if not object_exists(object_list[machine], ctrl_name):
        handle_error("Cannot add FC disk: No FC controller found in slot %d on PCI bus %s" % (slot_no, pci_bus))
        return

    if fc_ports[ctrl_name].has_key(loop_id):
        handle_error("Cannot add FC disk: FC port %d already occupied for controller %s" % (scsi_target, ctrl_name))
        return

    fc_ports[ctrl_name] = disk_name

    object_list[machine] += ([OBJECT(disk_name, "fc-disk",
                                     queue = OBJ(machine + "cpu0"),
                                     fc__controller = OBJ(ctrl_name),
                                     loop__id = loop_id,
                                     node__name = node_name,
                                     port__name = port_name,
                                     geometry = [size / 512, 1, 1],
                                     image = OBJ(disk_name + "_image"))] +
                             [OBJECT(disk_name + "_image", "image",
                                     size = size,
                                     queue = OBJ(machine + "cpu0"))])
    if files != "":
        set_attribute(object_list[machine], disk_name + "_image", "files", files)


def add_pci_bcm5703c(pci_bus_id, slot_no, mac_address):

    try:
        pci_bus = pci_device_init("add_pci_bcm5703c", "BCM5703C", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    dev_name = machine + "bcm" + pci_bus_id + "_" + `slot_no`

    pci_devices[pci_bus][slot_no] = dev_name

    object_list[machine] += [OBJECT(dev_name, "BCM5703C",
                                    queue = OBJ(machine + "cpu0"),
                                    recorder = OBJ(machine + "rec0"),
                                    firmware__loaded = 1,
                                    mac__address = mac_address,
                                    pci_bus = OBJ(pci_bus))]

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs.append([slot_no, 0, OBJ(dev_name)])
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)

def add_pci_bcm5704c(pci_bus_id, slot_no, mac_address0, mac_address1):

    try:
        pci_bus = pci_device_init("add_pci_bcm5704c", "BCM5704C", pci_bus_id, slot_no)
    except PCIConfException, msg:
        handle_error(msg)
        return

    dev_name = machine + "bcm" + pci_bus_id + "_" + `slot_no`

    pci_devices[pci_bus][slot_no] = dev_name + "_0"

    object_list[machine] += ([OBJECT(dev_name + "_0", "BCM5704C",
                                     queue = OBJ(machine + "cpu0"),
                                     recorder = OBJ(machine + "rec0"),
                                     firmware_loaded = 1,
                                     is_mac1 = 0,
                                     other_bcm = OBJ(dev_name + "_1"),
                                     mac_address = mac_address0,
                                     pci_bus = OBJ(pci_bus))] +
                             [OBJECT(dev_name + "_1", "BCM5704C",
                                     queue = OBJ(machine + "cpu0"),
                                     recorder = OBJ(machine + "rec0"),
                                     firmware_loaded = 1,
                                     is_mac1 = 1,
                                     other_bcm = OBJ(dev_name + "_0"),
                                     mac_address = mac_address1,
                                     pci_bus = OBJ(pci_bus))])

    devs = get_attribute(object_list[machine], pci_bus, "pci_devices")
    devs += [[slot_no, 0, OBJ(dev_name + "_0")],
             [slot_no, 1, OBJ(dev_name + "_1")]]
    set_attribute(object_list[machine], pci_bus, "pci_devices", devs)

def extract_shadowed(entry):
    return (entry[0] >= 0xC0000 and entry[0] <= 0xFFFFF)

def extract_nonshadowed(entry):
    return not extract_shadowed(entry)

def add_generic_shadow(mb):
    object_list[machine] += ([OBJECT(machine + "ram_space0", "memory-space",
                                     map = [[0, OBJ(machine + "ram0"), 0, 0, mb * 1024 * 1024]])])
    object_list[machine] += ([OBJECT(machine + "core0", "pc-shadow")])
    pci_map = get_attribute(object_list[machine], machine + "pci_mem0", "map")
    new_pci_map = filter(extract_nonshadowed, pci_map) + [[0xC0000, OBJ(machine + "core0"), 0, 0, 0x40000, OBJ(machine + "shadow0"), 0]]
    set_attribute(object_list[machine], machine + "pci_mem0", "map", new_pci_map)
    shadow_map = filter(extract_shadowed, pci_map) + [[1024 * 1024, OBJ(machine + "ram0"), 0, 0, 1024 * 1024]]
    object_list[machine] += ([OBJECT(machine + "shadow0", "memory-space",
                                     map = shadow_map)])
    map = get_attribute(object_list[machine], machine + "port_mem0", "map")
    map += [[0xfff4, OBJ(machine + "core0"), 0, 0x0, 1],
            [0xfff5, OBJ(machine + "core0"), 0, 0x1, 1]]
    set_attribute(object_list[machine], machine + "port_mem0", "map", map)
