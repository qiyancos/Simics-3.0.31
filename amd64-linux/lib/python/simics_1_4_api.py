from cli import *
import sim_core

from simics_1_6_api import *
from simics_1_8_api import *
from simics_2_0_api import *
from simics_2_2_api import *

def SIM_get_No_Exception():
    return sim_core.OLD_get_No_Exception()

def SIM_get_mmu_data(cpu):
    return sim_core.OLD_get_mmu_data(cpu)

def SIM_get_cpu_by_mid(cpu):
    return sim_core.OLD_get_cpu_by_mid(cpu)

def SIM_install_user_ASI_handler(callback, asi):
    return sim_core.OLD_install_user_ASI_handler(callback, asi)

def SIM_install_default_ASI_handler(callback, asi):
    return sim_core.OLD_install_default_ASI_handler(callback, asi)

def SIM_sparc_ASI_info(cpu, asi, info):
    return sim_core.OLD_sparc_ASI_info(cpu, asi, info)

def SIM_get_trap_time(cpu, tl):
    return sim_core.OLD_get_trap_time(cpu, tl)

def SIM_disassemble_physical(cpu, pa):
    return sim_core.OLD_disassemble_physical(cpu, pa)

def SIM_read_control_register(cpu, reg):
    return sim_core.OLD_read_control_register(cpu, reg)

def SIM_write_control_register(cpu, reg, value):
    return sim_core.OLD_write_control_register(cpu, reg, value)

def SIM_get_control_register_number(cpu, regname):
    return sim_core.OLD_get_control_register_number(cpu, regname)

def SIM_get_control_register_name(cpu, reg):
    return sim_core.OLD_get_control_register_name(cpu, reg)

def SIM_read_window_register(cpu, win, reg):
    return sim_core.OLD_read_window_register(cpu, win, reg)

def SIM_write_window_register(cpu, win, reg, value):
    return sim_core.OLD_write_window_register(cpu, win, reg, value)

def SIM_read_global_register(cpu, set, reg):
    return sim_core.OLD_read_global_register(cpu, set, reg)

def SIM_write_global_register(cpu, set, reg, value):
    return sim_core.OLD_write_global_register(cpu, set, reg, value)

def SIM_num_control_registers(cpu):
    return sim_core.OLD_num_control_registers(cpu)

def SIM_cpu_issue_cycles(cpu):
    return sim_core.OLD_cpu_issue_cycles(cpu)

def SIM_get_register_name(num):
    return sim_core.OLD_get_register_name(num)

def SIM_get_register_number(name):
    return sim_core.OLD_get_register_number(name)

def SIM_get_exception_name(num):
    return sim_core.OLD_get_exception_name(num)

def SIM_get_exception_number(name):
    return sim_core.OLD_get_exception_number(name)
