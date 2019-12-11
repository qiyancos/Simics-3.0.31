
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

from cli import *
from sim_commands import *

#
# ------------------------ info -----------------------
#

def calc_entries(tlb):
	return len(tlb) * len(tlb[0])

def calc_assoc(tlb):
	return len(tlb[0])

def get_info(obj):
    if obj.type == "normal":
	    return [ (None,
		      [ ("CPU", obj.cpu),
			("Mode", obj.type)]),
		     ("Instruction TLB, large pages",
		      [ ("Entries", calc_entries(obj.itlb_large)),
			("Associativity", calc_assoc(obj.itlb_large)) ]),
		     ("Instruction TLB, small pages",
		      [ ("Entries", calc_entries(obj.itlb_4k)),
			("Associativity", calc_assoc(obj.itlb_4k)) ]),
		     ("Data TLB, large pages",
		      [ ("Entries", calc_entries(obj.dtlb_large)),
			("Associativity", calc_assoc(obj.dtlb_large)) ]),
		     ("Data TLB, small pages",
		      [ ("Entries", calc_entries(obj.dtlb_4k)),
			("Associativity", calc_assoc(obj.dtlb_4k)) ]) ]
    else:
	    return [ (None,
		      [ ("CPU", obj.cpu),
			("Mode", obj.type)]) ]

new_info_command("x86-tlb", get_info)

def print_tlb(tlb, desc, size, usage):
    entries_used = 0
    for way in tlb:
        for entry in way:
            if (entry[0] != 1):
                entries_used = entries_used + 1
    if usage:
	    print "%s %s (%d/%d entries used)" % (desc, size, entries_used, calc_entries(tlb))
    else:
	    print "%s %s (%d entries used)" % (desc, size, entries_used)
    if entries_used:
        print "------- LA ------- ------- PA ------- U/S  R/W G PAT  MTRR"
        for way in tlb:
            for entry in way:
                if (entry[0] != 1):
                    print "0x%016x 0x%016x %s %s  %s %-4s %-4s" % (
                        entry[0],
                        entry[1],
                        iff(entry[2], "supr", "user"),
                        iff(entry[3], "ro", "rw"),
                        iff(entry[4], "G", "-"),
                        entry[5],
                        entry[6])

def status_cmd(obj):
    if obj.type == "normal":
	    print_tlb(obj.itlb_large, "Instruction", "%d Mb" % obj.large_tlb_select, 1)
	    print_tlb(obj.itlb_4k, "Instruction", "4 kb", 1)
	    print_tlb(obj.dtlb_large, "Data", "%d Mb" % obj.large_tlb_select, 1)
	    print_tlb(obj.dtlb_4k, "Data", "4 kb", 1)
    else:
	    print_tlb(obj.dtlb_large, "Instruction/Data", "%d Mb" % obj.large_tlb_select, 0)
	    print_tlb(obj.dtlb_4k, "Instruction/Data", "4 kb", 0)

new_command("status", status_cmd,
            [],
            alias = "",
            type  = "x86-tlb commands",
            short = "print status of the device",
            namespace = "x86-tlb",
            doc = """
Print detailed information about the current status of the TLB object.<br/>
""")
