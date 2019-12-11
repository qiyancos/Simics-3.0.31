from cli import *
import sim_commands

def get_empty(obj):
    return []

# cpc700-uic

def uic_get_info(obj):
    return [ (None,
              [("interrupt device", obj.irq_dev)])]

def uic_get_status(obj):
    return [ (None,
              [("UICSR (status)",    number_str(obj.uicsr,16)),
               ("UICER (enable)",    number_str(obj.uicer,16)),
               ("UICCR (critical)",  number_str(obj.uiccr,16)),
               ("UICVCR (vector)",   number_str(obj.uicvcr,16))])]

sim_commands.new_info_command("cpc700-uic", uic_get_info)
sim_commands.new_status_command("cpc700-uic", uic_get_status)

# cpc700-mc

sim_commands.new_info_command("cpc700-mc", get_empty)
sim_commands.new_status_command("cpc700-mc", get_empty)

# cpc700-gpt

sim_commands.new_info_command("cpc700-gpt", get_empty)
sim_commands.new_status_command("cpc700-gpt", get_empty)

# cpc700-pi

sim_commands.new_info_command("cpc700-pi", get_empty)
sim_commands.new_status_command("cpc700-pi", get_empty)

# cpc700-pci

sim_commands.new_info_command("cpc700-pci", get_empty)
sim_commands.new_status_command("cpc700-pci", get_empty)

# cpc700-iic

sim_commands.new_info_command("cpc700-iic", get_empty)
sim_commands.new_status_command("cpc700-iic", get_empty)
