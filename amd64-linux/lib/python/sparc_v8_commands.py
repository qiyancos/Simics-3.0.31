from cli import *
import sim_commands

local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun()

def print_in_columns(lst):
    col_width = max(map(len, lst)) + 1
    ncols = max(1, 80 / col_width)
    nrows = (len(lst) + ncols - 1) / ncols
    for i in range(nrows):
        for j in range(ncols):
	    index = i + j * nrows
	    if index < len(lst):
	        pr(lst[index] + " ")
	pr("\n")


def local_pregs(cpu, all):
    pr("\n");
    try:
        vals = [cpu.gprs[r] for r in range(32)]
        fvals = [cpu.fprs[r] for r in range(32)]
        asrvals = [cpu.asrs[r] for r in range(1,32)]
        pc = cpu.pc
        npc = cpu.npc
        psr = cpu.psr
        wim = cpu.wim
        tbr = cpu.tbr
        fsr = cpu.fsr
        y = cpu.y
        mmu_cr   = cpu.mmu_ctxt_reg
        mmu_cp   = cpu.mmu_ctxt_ptr
        mmu_fa   = cpu.mmu_fault_address
        mmu_ctrl = cpu.mmu_control_reg
        mmu_fs   = cpu.mmu_fault_status
    except Exception, msg:
        print msg
        return
    
    regs = ["g%-3d = 0x%.8x  " % (reg, vals[reg]) for reg in range(8)] \
           +["o%-3d = 0x%.8x  " % (reg, vals[reg+8]) for reg in range(8)] \
           +["l%-3d = 0x%.8x  " % (reg, vals[reg+16]) for reg in range(8)] \
           +["i%-3d = 0x%.8x  " % (reg, vals[reg+24]) for reg in range(8)]
    print_in_columns(regs);
    fregs = ["f%-3d = 0x%.8x  " % (reg, fvals[reg]) for reg in range(32)]
    pr("\n");
    print_in_columns(fregs);
    pr("\n");
    asrs = ["asr%-3d = 0x%.8x  " % (reg, asrvals[reg-1]) for reg in range(1,32)]
    print_in_columns(asrs);
    pr("\n");
    pr("y = 0x%.8x\n" % y);
    pr("pc = 0x%.8x  npc = 0x%.8x\n" % (pc, npc));
    pr("psr = 0x%.8x\n" % psr);
    pr("tbr = 0x%.8x\n" % tbr);
    pr("wim = 0x%.8x\n" % wim);
    pr("fsr = 0x%.8x\n" % fsr);
    
    pr("mmu context pointer = 0x%.8x\n" % mmu_cp);
    pr("mmu context register = 0x%.8x\n" % mmu_cr);
    pr("mmu control register = 0x%.8x\n" % mmu_ctrl);
    pr("mmu fault status = 0x%.8x\n" % mmu_fs);
    pr("mmu fault address = 0x%.8x\n" % mmu_fa);
    
def local_fregs(cpu, all):
    pr("\n");
    try:
        vals = [cpu.fprs[r] for r in range(32)]
        fsr = cpu.fsr
    except Exception, msg:
        print msg
        return
    
    regs = ["f%-3d = 0x%.8x  " % (reg, vals[reg]) for reg in range(32)]
    
    print_in_columns(regs);
    pr("\n");
    pr("fsr = 0x%.8x\n" % fsr);


def local_asrregs(cpu, all):
    pr("\n");
    try:
        vals = [cpu.asrs[r] for r in range(1, 32)]
        fsr = cpu.fsr
    except Exception, msg:
        print msg
        return
    regs = ["asr%-3d = 0x%.8x  " % (reg, vals[reg]) for reg in range(32)]


funcs = { 'print_disassemble_line': local_print_disassemble_line,
          'pregs': local_pregs,
          'pasrs': local_asrregs }
