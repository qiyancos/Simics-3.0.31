from cli import *

# Common functionality for PCI devices

def get_pci_info(obj):
    info = [("PCI bus",  obj.pci_bus)]
    return [(None, info)]

def get_pci_status(obj):
    return []

def print_config_regs_cmd(obj, verbose):
    reg_info = obj.config_register_info
    config_regs = obj.config_registers
    regs = []
    for i in range(len(reg_info)):
        val = 0
        for j in range(reg_info[i][2]):
            word_indx = (reg_info[i][0] + j) / 4
            byte_indx = (reg_info[i][0] + j) - word_indx*4
            word_val = config_regs[word_indx]
            byte_val = (word_val >> (byte_indx * 8)) & 0xff
            val = val | (byte_val << (j * 8))
        regs.append(["0x%02x" % reg_info[i][0], reg_info[i][1], reg_info[i][2], hex_str(reg_info[i][3], reg_info[i][2] * 2), hex_str(val, reg_info[i][2] * 2)])
    if verbose:
        print_columns([Just_Left, Just_Left, Just_Left, Just_Left, Just_Left],
                      [ [ "Offset", "Name", "Size", "Write-mask", "Value" ] ] + regs)
    else:
        print_columns([Just_Left, Just_Left, Just_Left],
                      [ [ "Offset", "Name", "Value" ] ] + map(lambda x: [x[0], x[1], x[4]], regs))

# ------------- command registration --------------

def new_pci_commands(device_name):
    if SIM_class_has_attribute(device_name, "config_register_info") and SIM_class_has_attribute(device_name, "config_registers"):
        new_command("print-config-regs", print_config_regs_cmd,
                    [arg(flag_t, "-v")],
                    short = "print configuration registers",
                    namespace = device_name,
                    doc = """
                    Print the PCI device's configuration space registers. Use
                    the <arg>-v</arg> flag for more verbose output.
                    """, filename="/mp/simics-3.0/src/extensions/apps-python/pci_common.py", linenumber="36")
