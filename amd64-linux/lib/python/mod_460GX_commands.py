import sim_commands

def sac_get_info(obj):
    buses = [ o[0].name for o in obj.pci_buses ]
    return [ (None,
              [ ("I/O space", obj.io_space.name) ] +
              [ ("PCI bus %d" % n, bus.name) for [bus,n] in obj.pci_buses ]) ]

sim_commands.new_info_command('i82461GX', sac_get_info)
