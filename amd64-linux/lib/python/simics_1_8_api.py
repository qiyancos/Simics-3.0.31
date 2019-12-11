from cli import *
import sim_core

from simics_2_0_api import *
from simics_2_2_api import *

def SIM_breakpoint_action(id, action):
    sim_core.OLD_breakpoint_action(id, action)

def SIM_get_file_size(filename):
    return sim_core.OLD_get_file_size(filename)
