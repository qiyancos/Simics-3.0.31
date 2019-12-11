from cli import *
import sim_commands

def get_usb_uhci_info(obj):
    return []

def get_usb_ehci_info(obj):
    return []

def get_usb_uhci_status(obj):
    devs = []
    dev_list = obj.usb_devices
    for p in range(len(dev_list)):
        devs += [("port[%d]" % p, dev_list[p])]
    return [("Connected USB devices", devs)]

def get_usb_ehci_status(obj):
    devs = []
    dev_list = obj.usb_devices
    for p in range(len(dev_list)):
        devs += [("port[%d]" % p, dev_list[p])]
    cmps = []
    cmp_list = obj.companion_hc
    for p in range(len(cmp_list)):
        cmps += [("port[%d]" % p, cmp_list[p])]
    return [("Connected USB devices", devs),
            ("Companion host controllers", cmps)]
