from cli import *
import sim_core

def SIM_get_attribute_attributes(obj, attr):
    return sim_core.sim_core.OLD_get_attribute_attributes(obj, attr)

def SIM_raise_general_exception(msg):
    sim_core.OLD_raise_general_exception(msg)
    
def SIM_check_exception():
    return sim_core.OLD_check_exception()

def SIM_exception_has_occurred():
    return sim_core.OLD_exception_has_occurred()

def VT_get_history_match(str):
    return sim_core.OLD_get_history_match(str)

def SIM_set_screen_size(w, h):
    pass

Sim_PE_Continue = Sim_PE_No_Exception
Sim_PE_IO_Break = Sim_PE_No_Exception
Sim_PE_Error    = Sim_PE_No_Exception
