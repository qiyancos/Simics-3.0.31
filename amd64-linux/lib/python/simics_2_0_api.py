from cli import *
import sim_core

from simics_2_2_api import *

def SIM_object_by_id(id):
    return sim_core.OLD_object_by_id(id)

def SIM_hap_install_callback(hap, cb, data):
    return sim_core.OLD_hap_install_callback(hap, cb, data)

def SIM_hap_install_callback_idx(hap, cb, idx, data):
    return sim_core.OLD_hap_install_callback_idx(hap, cb, idx, data)

def SIM_hap_install_callback_range(hap, cb, start, end, data):
    return sim_core.OLD_hap_install_callback_range(hap, cb, start, end, data)

def SIM_hap_register_callback(id, cb, data):
    return sim_core.OLD_hap_register_callback(id, cb, data)

def SIM_hap_register_callback_idx(id, cb, idx, data):
    return sim_core.OLD_hap_register_callback_idx(id, cb, idx, data)

def SIM_hap_register_callback_range(id, cb, start, end, data):
    return sim_core.OLD_hap_register_callback_range(id, cb, start, end, data)

def SIM_hap_remove_callback(hap, hdl):
    sim_core.OLD_hap_remove_callback(hap, hdl)
    
def SIM_hap_unregister_callback(id, cb, data):
    sim_core.OLD_hap_unregister_callback(id, cb, data)

def SIM_hap_new_type(id, params, param_desc, index, desc):
    return sim_core.OLD_hap_new_type(id, params, param_desc, index, desc)
