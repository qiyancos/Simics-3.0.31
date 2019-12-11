
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

if get_last_loaded_module() == 'swerver-thread-mmu':
    mmu_name = 'niagara-strand-mmu'
elif get_last_loaded_module() == 'swerver2-thread-mmu':
    mmu_name = 'niagara2-strand-mmu'
else:
    print "Unknown niagara mmu module: ", get_last_loaded_module()

# TODO: * Support p->v translation in i-probe and d-probe

#
# -------------------- chmmu-regs --------------------
#

def stmmu_regs_cmd(obj):
    true_false = ("false", "true")
    try:
	reg_ctx_prim = obj.ctxt_primary
        reg_ctx_sec =  obj.ctxt_secondary
	reg_ctx_nuc =  obj.ctxt_nucleus
	reg_lsu =      obj.lsu_ctrl
    
	reg_isfsr =    obj.isfsr
	reg_itsb8k =   obj.itsbp8k
	reg_itsb64k =  obj.itsbp64k
	reg_itsb =     obj.itsb
	reg_itag_acc = obj.itag_access
	reg_itag_tgt = obj.itag_target
	
        reg_dsfar =    obj.dsfar
        reg_dsfsr =    obj.dsfsr
        reg_dtsb8k =   obj.dtsbp8k
        reg_dtsb64k =  obj.dtsbp64k
        reg_dtsbpd =   obj.dtsbpd
        reg_dtsb =     obj.dtsb
        reg_dtag_acc = obj.dtag_access
        reg_dtag_tgt = obj.dtag_target

    except Exception, msg:
	print "Error reading MMU registers: %s" % msg
	return

    print "Context registers:"
    print "  Primary ctxt:   0x%04x   Secondary ctxt: 0x%04x   Nucleus ctxt:   0x%04x   " % (
	reg_ctx_prim & 0x1fff, reg_ctx_sec & 0x1fff, reg_ctx_nuc & 0x1fff)

    print "LSU control register: 0x%016x" % reg_lsu

    print ("  D-MMU enable:   %s    D-cache enable: %s"
           % (true_false[int((reg_lsu >> 3) & 1)],
              true_false[int((reg_lsu >> 1) & 1)]))
    
    print ("  I-MMU enable:   %s    I-cache enable: %s"
           % (true_false[int((reg_lsu >> 2) & 1)],
              true_false[int((reg_lsu >> 0) & 1)]))

    print "D-MMU sync fault status register:"
    print "  asi: 0x%02x  ft: 0x%02x  e: %d  ct: %d  pr: %d  w: %d ow: %d fv: %d" % (
	(reg_dsfsr >> 16) & 0xff,
	(reg_dsfsr >> 7) & 0x7f,
	(reg_dsfsr >> 6) & 1,
	(reg_dsfsr >> 4) & 3,
	(reg_dsfsr >> 3) & 1,
	(reg_dsfsr >> 2) & 1,
	(reg_dsfsr >> 1) & 1,
	(reg_dsfsr >> 0) & 1)
    
    print "I-MMU sync fault status register:"
    print "  asi: 0x%02x  ft: 0x%02x  e: %d  ct: %d  pr: %d  w: %d ow: %d fv: %d" % (
	(reg_isfsr >> 16) & 0xff,
	(reg_isfsr >> 7) & 0x7f,
	(reg_isfsr >> 6) & 1,
	(reg_isfsr >> 4) & 3,
	(reg_isfsr >> 3) & 1,
	(reg_isfsr >> 2) & 1,
	(reg_isfsr >> 1) & 1,
	(reg_isfsr >> 0) & 1)
        
    print "D-MMU sync fault address register:"
    print "  va: 0x%016x" % reg_dsfar

    print "D-MMU tag access register:"
    print ("  va: 0x%016x  context: 0x%04x"
           % (reg_dtag_acc & 0xffffffffffffe000L, int(reg_dtag_acc & 0x1fffL)))

    print "I-MMU tag access register:"
    print ("  va: 0x%016x  context: 0x%04x"
           % (reg_itag_acc & 0xffffffffffffe000L, int(reg_itag_acc & 0x1fffL)))

    print "D tsbp8k     0x%016x    I tsbp8k     0x%016x" % (reg_dtsb8k, reg_itsb8k)
    print "D tsbp64k    0x%016x    I tsbp64k    0x%016x" % (reg_dtsb64k, reg_itsb64k)
    print "D tsbpd      0x%016x    I tsbpd      0x%016x" % (reg_dtsbpd, 0)
    print "D tsb        0x%016x    I tsb        0x%016x" % (reg_dtsb, reg_itsb)
    print "D tag_target 0x%016x    I tag_target 0x%016x" % (reg_dtag_tgt, reg_itag_tgt)

new_command("regs", stmmu_regs_cmd,
            [],
            alias = "",
            type  = "%s commands" % mmu_name,
            short = "print mmu registers",
	    namespace = "%s" % mmu_name,
            doc = """
Print the content of the %s MMU registers<br/>
""" % mmu_name, filename="/mp/simics-3.0/src/devices/swerver-thread-mmu/commands.py", linenumber="117")

#
# -------------------- d-tlb, i-tlb ------------------
#
def dump_tlb_entry(i, daccess, tagread):
    va = tagread & 0x00ffffffffffe000
    if va & (1 << 55):
        addr |= 0xff00000000000000
    print "%2d %04x 0x%016x  %d  %d %d  %d  %d  %d  0x%016x %d  %d  %d %d %d %d %d" % (
	i,
	tagread & 0x1fff,
        va,
	(tagread >> 61) & 3,
	(daccess >> 63) & 1,
        (daccess >> 46) & 4 | (daccess >> 61) & 3,
        (tagread >> 60) & 1,
	(daccess >> 60) & 1,
	(daccess >> 59) & 1,
	(daccess & 0xfffffffe000),
	(daccess >> 6) & 1,
	(daccess >> 5) & 1,
	(daccess >> 4) & 1,
	(daccess >> 3) & 1,
	(daccess >> 2) & 1,
	(daccess >> 1) & 1,
	(daccess >> 41) & 1)

def stmmu_dtlb_cmd(obj):
    dtlb_dacc_regs = obj.cmmu.dtlb_daccess
    dtlb_tags_regs = obj.cmmu.dtlb_tagread
    print " ==== D-TLB ===="
    print " # CTXT ------- VA ------- PID V SZ R NFO IE ------- PA ------- L CP CV E P W U"
    for i in range(len(dtlb_dacc_regs)):
        dump_tlb_entry(i, dtlb_dacc_regs[i], dtlb_tags_regs[i])


def stmmu_itlb_cmd(obj):
    itlb_dacc_regs = obj.cmmu.itlb_daccess
    itlb_tags_regs = obj.cmmu.itlb_tagread
    print " ==== I-TLB ===="
    print " # CTXT ------- VA ------- PID V SZ R NFO IE ------- PA ------- L CP CV E P W U"
    for i in range(len(itlb_dacc_regs)):
        dump_tlb_entry(i, itlb_dacc_regs[i], itlb_tags_regs[i])

new_command("d-tlb", stmmu_dtlb_cmd,
            [],
            alias = "",
            short = "print data tlb contents",
            namespace = "%s" % mmu_name,
            see_also = ["<%s>." % mmu_name + 'i-tlb',
                        "<%s>." % mmu_name + 'd-probe'],
            doc = """
Print the content of the data TLB<br/>
""", filename="/mp/simics-3.0/src/devices/swerver-thread-mmu/commands.py", linenumber="170")

new_command("i-tlb", stmmu_itlb_cmd,
            [],
            alias = "",
            short = "print instruction tlb contents",
            namespace = "%s" % mmu_name,
            see_also = ["<%s>." % mmu_name + 'd-tlb',
                        "<%s>." % mmu_name + 'i-probe'],
            doc_with = "<%s>.d-tlb" % mmu_name, filename="/mp/simics-3.0/src/devices/swerver-thread-mmu/commands.py", linenumber="181")

#
# ----------------- d-probe, i-probe -----------------
#

def stmmu_probe_cmd(obj, la, tlb):
    if la[0] not in ["", "v"]:
	print "Only virtual addresses can be translated"
	return
    try:
        if tlb == 0:
            pa = obj.d_translation[la[1]]
        else:
            pa = obj.i_translation[la[1]]
    except SimExc_Memory, y:
	print "Not in tlb"
	return
    except Exception, y:
	print "TLB Error: %s" % y
        return
    print "0x%016x  ->  0x%016x" % (la[1], pa)

def stmmu_dprobe_cmd(obj, la):
    stmmu_probe_cmd(obj, la, 0)

def stmmu_iprobe_cmd(obj, la):
    stmmu_probe_cmd(obj, la, 1)

new_command("d-probe", stmmu_dprobe_cmd,
            [arg(addr_t, "address") ],
            alias = "",
            type  = "%s commands" % mmu_name,
            short = "check data tlb for translation",
	    namespace = "%s" % mmu_name,
            see_also = ["<%s>" % mmu_name + '.d-tlb', "<%s>" % mmu_name + '.i-probe'],
            doc = """
Translate a virtual address to physical<br/>
The translation is based on the mappings in the
instruction or data TLB.<br/>
""", filename="/mp/simics-3.0/src/devices/swerver-thread-mmu/commands.py", linenumber="217")

new_command("i-probe", stmmu_iprobe_cmd,
            [arg(addr_t, "address")],
            alias = "",
            type  = "%s commands" % mmu_name,
            short = "check instruction tlb for translation",
	    namespace = "%s" % mmu_name,
            see_also = ["<%s>" % mmu_name + '.i-tlb', "<%s>" % mmu_name + '.d-probe'],
	    doc_with = "<%s>.d-probe" % mmu_name, filename="/mp/simics-3.0/src/devices/swerver-thread-mmu/commands.py", linenumber="230")
