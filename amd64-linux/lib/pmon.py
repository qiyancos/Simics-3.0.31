# This file implements the PMON firmware's LEON2 boot setup. It does not
# implement the serial port boot loading, only the initial setup.
# The PMON firmware for the LEON2 comes with a number of preprocessor defines
# that the user typically changes to match the hardware configuration.

# The PMON emulation function takes all these parameters as function arguments,
# with the exception of the clock frequency, that is picked from the cpu.

import conf
from sim_core import *


def _pmon_start(cpu, stack_init):
    cpu.wim = 2
    cpu.psr = 0x10e0
    cpu.gprs[14] = stack_init # %sp = STACK_INIT
    cpu.gprs[1] = SIM_read_phys_memory(cpu, 0x80000014, 4)
    cpu.psr = cpu.psr | 7
    cpu.gprs[14] = stack_init - 0x40

def _pmon_init(cpu, memcfg1, memcfg2, timer_scaler_val, uart_scaler_val):
    SIM_write_phys_memory(cpu, 0x80000014, 0x1000f, 4)          # cache_ctrl
    SIM_write_phys_memory(cpu, 0x800000a4, 0xaa00, 4)           # io_port_dir
    SIM_write_phys_memory(cpu, 0x80000090, 0, 4)                # irq_mask
    SIM_write_phys_memory(cpu, 0x80000094, 0, 4)                # irq_pending
    SIM_write_phys_memory(cpu, 0x80000098, 0, 4)                # irq_force
    SIM_write_phys_memory(cpu, 0x80000000, memcfg1, 4)      # memcfg1
    SIM_write_phys_memory(cpu, 0x80000004, memcfg2, 4)      # memcfg2
    SIM_write_phys_memory(cpu, 0x80000060, timer_scaler_val, 4) # prescaler_counter
    SIM_write_phys_memory(cpu, 0x80000064, timer_scaler_val, 4) # prescaler_reload
    SIM_write_phys_memory(cpu, 0x80000044, 0xffffffff, 4)       # t1_reload (-1)
    SIM_write_phys_memory(cpu, 0x80000048, 7, 4)                # t1_control
    SIM_write_phys_memory(cpu, 0x8000007c, uart_scaler_val, 4)  # uart1_scaler
    SIM_write_phys_memory(cpu, 0x8000008c, uart_scaler_val, 4)  # uart2_scaler
    SIM_write_phys_memory(cpu, 0x80000074, 0, 4)                # uart1_status
    SIM_write_phys_memory(cpu, 0x80000084, 0, 4)                # uart2_status
    SIM_write_phys_memory(cpu, 0x80000078, 3, 4)                # uart1_control
    SIM_write_phys_memory(cpu, 0x80000088, 3, 4)                # uart2_control


def pmon_setup(cpu, timer_scale, baud_rate, bank_size, ram_banks, mcfg1, mcfg2):
    cpu_freq = int(cpu.freq_mhz * 1000000.0)
    stack_init = 0x40000000 + ((bank_size * ram_banks) - 16)
    timer_scaler_val = (cpu_freq/timer_scale -1)
    uart_scaler_val = ((((cpu_freq*10) / (8 * baud_rate))-5)/10)
    
    _pmon_start(cpu, stack_init)
    _pmon_init(cpu, mcfg1, mcfg2, timer_scaler_val, uart_scaler_val)
