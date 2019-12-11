from sim_commands import *

def get_info(obj):
    return [ (None,
              [ ("Upstream interrupt device", obj.irq_dev) ] ) ]

def irq_bits(val, offset):
    master_req = ""
    for i in range(8):
        if val & (1 << i):
            master_req = master_req + ("%s " % (i + offset))
    if master_req == "":
        master_req = "None"
    return master_req

def get_status(obj):
    return [ (None,
              [ ("Output interrupt line", iff(obj.irq_requested, "active", "inactive")) ] ),
             ("Master",
              [ ("Interrupt vector base", obj.vba[0]),
                ("Special mask mode", obj.special_mask[0]),
                ("Auto end of interrupt", obj.aeoi[0]),
                ("Special fully nested mode", obj.sfnm[0]),
                ("Poll command mode", obj.poll[0]),
                ("Lowest priority interrupt", obj.low_irq_pri[0]),
                ("Level triggered inputs", irq_bits(obj.level[0], 0)),
                ("IRQs masked", irq_bits(obj.irq_mask[0], 0)),
                ("IRQs requested", irq_bits(obj.request[0], 0)),
                ("IRQs queued", irq_bits(obj.queued[0], 0)),
                ("IRQs issued", irq_bits(obj.issued[0], 0)) ] ),
             ("Slave",
              [ ("Interrupt vector base", obj.vba[1]),
                ("Special mask mode", obj.special_mask[1]),
                ("Auto end of interrupt", obj.aeoi[1]),
                ("Poll command mode", obj.poll[1]),
                ("Lowest priority interrupt", obj.low_irq_pri[1]),
                ("Level triggered inputs", irq_bits(obj.level[1], 8)),
                ("IRQs masked", irq_bits(obj.irq_mask[1], 8)),
                ("IRQs requested", irq_bits(obj.request[1], 8)),
                ("IRQs queued", irq_bits(obj.queued[1], 8)),
                ("IRQs issued", irq_bits(obj.issued[1], 8)) ] ) ]

new_info_command('i8259x2', get_info)
new_status_command('i8259x2', get_status)
