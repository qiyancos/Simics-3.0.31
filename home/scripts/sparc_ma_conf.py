
##  Copyright 2004-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.

proc_num = 0

from configuration import *

if "add_cc" not in dir(): add_cc = 0
if "add_cache" not in dir(): add_cache = 1
if "add_mem_staller" not in dir(): add_mem_staller = 1

if "micro_arch_class" not in dir(): micro_arch_class = "sample_micro_arch"

if "cache_penalty_read" not in dir(): cache_penalty_read = 1
if "cache_penalty_write" not in dir(): cache_penalty_write = 1
if "cache_penalty_miss" not in dir(): cache_penalty_miss = 10

if "reorder_buffer_size" not in dir(): reorder_buffer_size = 32

def for_proc(cpu, data):
    global proc_num, add_cc

    #adding a cache for each cpu

    next = None

    if add_mem_staller:
        staller_name = "trans_staller" + `proc_num`
        SIM_set_configuration([OBJECT(staller_name, "trans-staller", 
                                      stall_time = cache_penalty_miss)])
        
        next = SIM_get_object(staller_name)
        print "adding " + next.name + " to " + cpu.name
        
    if add_cache:
        cache_name = "cache" + `proc_num`
        SIM_set_configuration([OBJECT(cache_name, "g-cache-ooo", 
                                      penalty_read = cache_penalty_read,
                                      penalty_write = cache_penalty_write,
                                      config_line_number = 128,
                                      config_line_size = 32,
                                      config_assoc = 4,
                                      config_virtual_index = 0,
                                      config_write_back = 1,
                                      timing_model = next,
                                      cpus = [cpu])])
        
        next = SIM_get_object(cache_name)

        print "adding " + next.name + " to " + cpu.name

    if add_cc:
        cc_name = "cc" + `proc_num`
        SIM_set_configuration([OBJECT(cc_name, "consistency-controller",
                                      load_load = 1,
                                      load_store = 1,
                                      store_load = 1,
                                      store_store = 1,
                                      prefetch = 0,
                                      log_level = 0,
                                      timing_model = next)])

        next = SIM_get_object(cc_name)
        
        print "adding " + next.name + " to " + cpu.name

    cpu.physical_memory.timing_model = next
    try:
        cpu.physical_io.timing_model = next
    except:
        pass

    cpu.reorder_buffer_size = reorder_buffer_size
    #cpu.auto_speculate_cwp = 1

    SIM_set_configuration([OBJECT("ma"+`proc_num`, micro_arch_class,
                                  cpu = cpu)])

    proc_num = proc_num + 1
    
SIM_for_all_processors(for_proc, 0)
