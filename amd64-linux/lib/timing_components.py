# MODULE: timing-components
# CLASS: sample-gcache
# CLASS: sample-ma-model
# CLASS: sample-x86-ma-model
# CLASS: sample-ooo-model

from sim_core import *
from components import *


### Sample g-cache, simple combined L1 instruction and data cache


class sample_gcache_component(component_object):
    classname = 'sample-gcache'
    basename = 'g_cache'
    description = 'A pre-configured combined L1 instruction and data cache'
    connectors = {
        'cpu-space' : {'type' : 'timing-model', 'direction' : 'up',
                       'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    # TODO: add parameters as attributes
        
    def add_objects(self):
        self.o.cache = pre_obj('cache_(x)', 'g-cache')
        self.o.cache.config_line_number = 512
        self.o.cache.config_line_size = 32
        self.o.cache.config_assoc = 4

    def add_connector_info(self):
        self.connector_info['cpu-space'] = [self.o.cache]

    def connect_timing_model(self, connector, cpu_id, cpu):
        if cpu == None:
            # ignore
            return
        self.rename_component_objects(cpu.name)
        self.o.cache.cpus = cpu

    def disconnect_timing_model(self, connector):
        self.o.cache.cpus = None

register_component_class(sample_gcache_component, [])


### Sample MAI model


class sample_ma_model_component(component_object):
    classname = 'sample-ma-model'
    basename = 'ma_model'
    description = 'A sample SPARC MAI model with a simple cache'
    connectors = {
        'cpu-space' : {'type' : 'timing-model', 'direction' : 'up',
                       'empty_ok' : True, 'hotplug' : True, 'multi' : False}}
    micro_arch_class = 'sample_micro_arch'

    # TODO: add parameters as attributes

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.add_staller = 1
        self.add_cache = 1
        self.add_cc = 0
        self.cache_penalty_miss = 10
        self.cache_penalty_read = 1
        self.cache_penalty_write = 1
        self.reorder_buffer_size = 32

    def add_objects(self):
        next = None
        self.o.cache = None
        if self.add_staller:
            self.o.staller = pre_obj('staller_(x)', 'trans-staller')
            self.o.staller.stall_time = self.cache_penalty_miss
            next = self.o.staller
        if self.add_cache:
            self.o.cache = pre_obj('cache_(x)', 'g-cache-ooo')
            self.o.cache.penalty_read = self.cache_penalty_read
            self.o.cache.penalty_write = self.cache_penalty_write
            self.o.cache.config_line_number = 128
            self.o.cache.config_line_size = 32
            self.o.cache.config_assoc = 4
            self.o.cache.config_virtual_index = 0
            self.o.cache.config_write_back = 1
            self.o.cache.timing_model = next
            next = self.o.cache
        if self.add_cc:
            self.o.cc = pre_obj('cc_(x)', 'consistency-controller')
            self.o.cc.load_load = 1
            self.o.cc.load_store = 1
            self.o.cc.store_load = 1
            self.o.cc.store_store = 1
            self.o.cc.prefetch = 0
            self.o.cc.log_level = 0
            self.o.cc.timing_model = next
            next = self.o.cc
        self.o.ma = pre_obj('ma_(x)', self.micro_arch_class)
        self.last_cache = next

    def add_connector_info(self):
        self.connector_info['cpu-space'] = [self.last_cache]

    def connect_timing_model(self, connector, cpu_id, cpu):
        if cpu == None:
            # ignore
            return
        self.rename_component_objects(cpu.name)
        if self.o.cache:
            self.o.cache.cpus = cpu
        cpu.reorder_buffer_size = self.reorder_buffer_size
        self.o.ma.cpu = cpu

    def disconnect_timing_model(self, connector):
        if self.o.cache:
            self.o.cache.cpus = None
        self.o.ma.cpu = None

register_component_class(sample_ma_model_component, [])


class sample_x86_ma_model_component(sample_ma_model_component):
    classname = 'sample-x86-ma-model'
    basename = 'x86_ma_model'
    description = 'A sample x86 MAI model'
    micro_arch_class = 'sample_micro_arch_x86'

    def add_objects(self):
        sample_ma_model_component.add_objects(self)
        self.o.ma.fetches_per_cycle = 4
        self.o.ma.executes_per_cycle = 7
        self.o.ma.retires_per_cycle = 5
        self.o.ma.commits_per_cycle = 3
        self.o.ma.branch_miss_penalty = 10
        self.o.ma.max_in_flight = 16

register_component_class(sample_x86_ma_model_component, [])


class sample_ooo_model_component(sample_ma_model_component):
    classname = 'sample-ooo-model'
    basename = 'ooo_model'
    description = """
A sample SPARC MAI model based on <class>ooo_micro_arch</class>
and a simple cache.
"""
    micro_arch_class = 'ooo_micro_arch'

register_component_class(sample_ooo_model_component, [])
