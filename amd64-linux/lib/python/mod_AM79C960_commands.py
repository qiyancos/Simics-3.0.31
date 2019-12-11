from cli import *
from string import *
import nic_common
import sim_commands


def checkbit(a, bit):
    if a & (1 << bit):
        return 1
    else:
        return 0
    
def get_info(obj):
    return [ (None,
              [ ("IRQ device", obj.irq_dev),
                ("IRQ number", obj.irq_level) ]),
             ("AM79C960 initblock (from memory)",
              [ ("Mode", "0x%x" % obj.mode),
                ("Phys addr", obj.mac_address),
                ("Log addr", obj.log_addr),
                ("Rx addr", "0x%x" % obj.rx_ptr),
                ("Rx len", "0x%x" % obj.rx_len),
                ("Tx addr", "0x%x" % obj.tx_ptr),
                ("Tx len", "0x%x" % obj.tx_len) ]),
             ] + nic_common.get_nic_info(obj)

def get_status(obj):
    csr = obj.csr0
    csr0a = "INIT=%d STRT=%d STOP=%d TDMD=%d TXON=%d RXON=%d INEA=%d INTR=%d" % (
        checkbit(csr, 0), checkbit(csr, 1), checkbit(csr, 2), checkbit(csr, 3),
        checkbit(csr, 4), checkbit(csr, 5), checkbit(csr, 6), checkbit(csr, 7))
    csr0b = "IDON=%d TINT=%d RINT=%d MERR=%d MISS=%d CERR=%d BABL=%d ERR=%d" % (
        checkbit(csr, 8), checkbit(csr, 9), checkbit(csr, 10), checkbit(csr, 11),
        checkbit(csr, 12), checkbit(csr, 13), checkbit(csr, 14), checkbit(csr, 15))
    log = obj.log_addr
    log_addr = "%x.%x.%x.%x.%x.%x.%x.%x" % (
        log[0], log[1], log[2], log[3], log[4], log[5], log[6], log[7])
    if obj.connected == 1:
        connected = "yes"
    else:
        connected = "no"

    return ([ (None,
               [ ("CSR", csr0a),
                 (None,  csr0b),
                 ("CSR1", "0x%x" % obj.csr1),
                 ("CSR2", "0x%x" % obj.csr2),
                 ("CSR3", "BCON=%d ACON=%d BSWP=%d" % (
        (checkbit(obj.csr3, 0), checkbit(obj.csr3, 1), checkbit(obj.csr3, 2)))),
                 ("RAP", obj.rap) ]),
              (None,
               [("Packets sent", obj.pkt_snt),
                ("Packets received", obj.pkt_rec)])] +
            nic_common.get_nic_status(obj))

nic_common.new_nic_commands('AM79C960')

sim_commands.new_info_command('AM79C960', get_info)
sim_commands.new_status_command('AM79C960', get_status)
