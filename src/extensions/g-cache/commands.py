## commands.py

##  Copyright 2003-2007 Virtutech AB
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

from cli import *
from gcache_common import *

def gc_info_cmd(gc):
    gc_default_info_cmd(gc)
    print "Read penalty          :", gc.penalty_read, "cycle" + iff(gc.penalty_read == 0 or gc.penalty_read == 1, "", "s")
    
    print "Read-next penalty     :", gc.penalty_read_next, "cycle" + iff(gc.penalty_read_next == 0 or gc.penalty_read_next == 1, "", "s")
    
    print "Write penalty         :",  gc.penalty_write, "cycle" + iff(gc.penalty_write == 0 or gc.penalty_write == 1, "", "s")
    
    print "Write-next penalty    :", gc.penalty_write_next, "cycle" + iff(gc.penalty_write_next == 0 or gc.penalty_write_next == 1, "", "s")

    print
    
    c_list = gc.snoopers
    if c_list:
        pr(   "Snoopers              : ")
        for c in c_list:
            pr(c.name + " ")
        pr("\n")
    
    c_list = gc.higher_level_caches
    if c_list:
        pr(   "Higher level caches   : ")
        for c in c_list:
            pr(c.name + " ")
        pr("\n")
        
def gc_stats_cmd(gc):
    gc_default_stats_cmd(gc, 1)

gc_define_cache_commands("g-cache", None, gc_info_cmd, gc_stats_cmd, None)
