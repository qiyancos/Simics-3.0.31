
##  Copyright 2002-2007 Virtutech AB
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


from configuration import *

config_error = 0
cpu_list = []
space_list = {}

def collect_cpus(cpu, arg):
    global config_error

    if config_error:
        return

    space_list[cpu] = [cpu.physical_memory]
    try:
        if cpu.physical_io != cpu.physical_memory:
            space_list[cpu].append(cpu.physical_io)
    except:
        pass

    for space in space_list[cpu]:
        try:
            if space.timing_model != None:
                print ("The memory-space '%s' already has a"
                       "timing-model connected." % space.name)
                print "Cannot add cache to it - please check the configuration."
                config_error = 1
                return
        except:
            pass
    cpu_list.append(cpu)


def common_setup_start(func):
    if not SIM_initial_configuration_ok():
        print "%s() cannot run until a configuration exists." % func
        print
        SIM_command_has_problem()
        return 1

    SIM_for_all_processors(collect_cpus, 0)
    if config_error:
        # error message already printed
        SIM_command_has_problem()
        return 1
    return 0


def common_setup_end(conf):
    try:
        SIM_set_configuration(conf)
    except Exception, msg:
        print "Failed adding cache to the configuration: %s" % msg
        print
        SIM_command_has_problem()
        return 1

    try:
        print cpu_list
        for cpu in cpu_list:
            print space_list            
            for space in space_list[cpu]:
                if space:
                    space.timing_model = SIM_get_object("cache_%s" % cpu.name)
            if cpu.classname.find("x86") >= 0:
                cpu.instruction_fetch_mode = "instruction-fetch-trace"
            else:
                cpu.instruction_fetch_mode = "instruction-cache-access-trace"
    except Exception, msg:
        print "Failed adding cache thelloo the configuration: %s" % msg
        print
        SIM_command_has_problem()
        return 1
    return 0


# simple combined instruction and data L1 cache

def add_g_caches(size_kb = 16):
    if common_setup_start("add_g_caches"):
        return
    
    conf = []
    cache_list = []
    for cpu in cpu_list:
        cache_list.append("cache_%s"% cpu.name)
        conf += [OBJECT("cache_%s" % cpu.name, "g-cache",
                        config_line_number = size_kb * 1024 / 32,
                        config_line_size = 32,
                        config_assoc = 4,
                        cpus = OBJ(cpu.name),
                        queue = OBJ(cpu.name))]        

    common_setup_end(conf)

    # add snoopers is multipro
    if len(cpu_list) > 1:
        # get a list of objects
        cache_olist = []
        for cache in cache_list:
            cache_olist.append(SIM_get_object(cache))

        # create a snooper list for each cache
        for cache in cache_olist:
            # add all caches but the cache itself
            current_list = []
            for c in cache_olist:
                if c != cache:
                    current_list.append(c)
            cache.snoopers = current_list;

# UltraSPARC III/III+ only:
# cheetah cache system with I and D L1 caches, L2 cache,
# prefetch cache and write buffer

def add_cheetah_caches():

    if common_setup_start("add_cheeetah_caches"):
        return

    conf = []
    cache_list = []
    for cpu in cpu_list:
        cache_list.append("cache_%s)" %cpu.name)
        conf += ([OBJECT("cache_%s" % cpu.name, "u3-cache",
                         dcache = OBJ("dcache_%s" % cpu.name),
                         icache = OBJ("icache_%s" % cpu.name),
                         ecache = OBJ("ecache_%s" % cpu.name),
                         pcache = OBJ("pcache_%s" % cpu.name),
                         wcache = OBJ("wcache_%s" % cpu.name))] +
                 # 64 Kb 4-way set associative data cache
                 [OBJECT("dcache_%s" % cpu.name,"u3-dcache",
                         lines = 2048,
                         lsize = 32,
                         assoc = 4,
                         cpu = OBJ(cpu.name),
                         enabled = 1,
                         queue = OBJ(cpu.name))] +
                 # 32 Kb 4-way set associative instruction cache
                 [OBJECT("icache_%s" % cpu.name,"u3-icache",
                         lines = 1024,
                         lsize = 32,
                         assoc = 4,
                         cpu = OBJ(cpu.name),
                         enabled = 1,
                         queue = OBJ(cpu.name))] +
                 # 1024 Kb direct mapped L2 cache
                 [OBJECT("ecache_%s" % cpu.name,"u3-ecache",
                         lines = 16384,
                         lsize = 64,
                         assoc = 1,
                         cpu = OBJ(cpu.name),
                         enabled = 1,
                         queue = OBJ(cpu.name))] +
                 # prefetch cache                     
                 [OBJECT("pcache_%s" % cpu.name,"u3-pcache",
                         enabled = 1,
                         cpu = OBJ(cpu.name),
                         queue = OBJ(cpu.name))] +
                 # write cache
                 [OBJECT("wcache_%s" % cpu.name,"u3-wcache",
                         enabled = 1,
                         cpu = OBJ(cpu.name),
                         queue = OBJ(cpu.name))])

    common_setup_end(conf)
