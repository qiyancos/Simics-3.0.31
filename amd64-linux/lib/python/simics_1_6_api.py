from cli import *
import sim_core

from simics_1_8_api import *
from simics_2_0_api import *
from simics_2_2_api import *

def SIM_read_fp_register_i(cpu, reg):
    return sim_core.OLD_read_fp_register_i(cpu, reg)

def SIM_read_fp_register_x(cpu, reg):
    return sim_core.OLD_read_fp_register_x(cpu, reg)

def SIM_read_fp_register_s(cpu, reg):
    return sim_core.OLD_read_fp_register_s(cpu, reg)

def SIM_read_fp_register_d(cpu, reg):
    return sim_core.OLD_read_fp_register_d(cpu, reg)

def SIM_write_fp_register_i(cpu, reg, value):
    sim_core.OLD_write_fp_register_i(cpu, reg, value)

def SIM_write_fp_register_x(cpu, reg, value):
    sim_core.OLD_write_fp_register_x(cpu, reg, value)

def SIM_write_fp_register_s(cpu, reg, value):
    sim_core.OLD_write_fp_register_s(cpu, reg, value)

def SIM_write_fp_register_d(cpu, reg, value):
    sim_core.OLD_write_fp_register_d(cpu, reg, value)

def SIM_read_fp_register(cpu, reg):
    return sim_core.OLD_read_fp_register(cpu, reg)

def SIM_write_fp_register(cpu, reg, value):
    sim_core.OLD_write_fp_register(cpu, reg, value)
    
def SIM_clear_atomic_reservation_bit(cpu):
    sim_core.OLD_clear_atomic_reservation_bit(cpu)

def SIM_get_stack_pointer(cpu):
    sim_core.OLD_get_stack_pointer(cpu)

def SIM_get_base_pointer(cpu):
    sim_core.OLD_get_base_pointer(cpu)

def SIM_device_log(obj, msg):
    sim_core.OLD_device_log(obj, msg)

No_Exception = Sim_PE_No_Exception
Stall_Cpu = Sim_PE_Stall_Cpu
Continue = Sim_PE_Continue
