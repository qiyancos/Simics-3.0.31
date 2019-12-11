##  Copyright 2005-2007 Virtutech AB
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

# MODULE: ppc970fx-components
# CLASS: ppc970-simple

from sim_core import *
from components import *
from ppc64_simple_components import *

import time


### Simple PPC970FX Based System


class ppc970_simple_component(ppc64_simple_base_component):
    classname = 'ppc970-simple'
    description = 'A simple system containing a ppc970fx processor.'

    def add_objects(self):
        self.o.cpu.append(pre_obj('cpu$', 'ppc970fx'))
        self.o.cpu[0].processor_number = get_next_cpu_number()
        self.o.cpu[0].freq_mhz = self.freq_mhz
        self.o.cpu[0].timebase_freq_mhz = self.freq_mhz / 8
        ppc64_simple_base_component.add_objects(self, self.o.cpu[0])
        self.o.cpu[0].physical_memory = self.o.phys_mem
        self.o.cpu[0].cpu_group = self.o.broadcast_bus

register_component_class(ppc970_simple_component,
                         ppc64_simple_attributes,
                         top_level = True)

