from cli import *
import re
import fp_to_string
import string
import sim_commands
import sim_profile_commands

# Format value as hex string, prepend zeroes according to
# bitness of processor (32 or 64)
def ppc_hex_str(cpu, val):
    return ("0x%." + str(cpu.address_width[1]/4) +"x") % (val)

def ppc_bit32(bit):
	return (0x80000000L >> (bit))

def ppc_bit64(bit):
	return (0x8000000000000000L >> (bit))

# Returns value of bitfield [start:stop] (ppc style) of 32 bit word
def ppc_bf32(v,start,stop):
	return ((v >> (31L-stop)) & ((1L << (1+stop-start))-1))

def ppc_bf40(v,start,stop):
	return ((v >> (39L-stop)) & ((1L << (1+stop-start))-1))

def ppc_bf64(v,start,stop):
	return ((v >> (63L-stop)) & ((1L << (1+stop-start))-1))

def ppc_set_bf32(v,start,stop):
	return ((v << 31L - stop) & ((1L << (31L - start + 1))-1))

def ppc_set_bf40(v,start,stop):
	return ((v << 39L - stop) & ((1L << (39L - start + 1))-1))
    
def print_list(a_list):
	the_ipr_list = a_list
	the_number_of_iprs = len(the_ipr_list)
        the_max_length = max(map(lambda an_entry: len(an_entry), the_ipr_list))
        the_column_width = the_max_length + 1
        the_number_of_columns = 80 / the_column_width
	if the_number_of_columns == 0:
		the_number_of_columns = 1
        the_number_of_rows = (the_number_of_iprs + the_number_of_columns - 1) / the_number_of_columns
        for i in range(the_number_of_rows):
                for j in range(the_number_of_columns):
                        index = i + j * the_number_of_rows
                        if index < the_number_of_iprs:
                                pr("%s " % the_ipr_list[index])
		pr("\n")

local_print_disassemble_line = sim_commands.make_print_disassemble_line_fun()

def bit_string(size, value, separator):
	str = ""
	sep = ""
	for bit in range(size - 1,-1,-1):
		if (value & (1L << bit)):
			str = str + sep + "1"
		else:
			str = str + sep + "0"
		sep = separator
	return str

def bit_representation(size, value, rep_str):
	str = ""
	i = 0
	for bit in range(size - 1,-1,-1):
		if (value & (1L << bit)):
			str = str + rep_str[i]
		else:
			str = str + " "
		i += 1
	return str


def batsize(mask):
    n = count_trailing_zeros32(~mask)
    return (1 << n)

def print_mapping(cpu, batu, batl):
        if (cpu.hid0 & (1 << 17)) != 0:
            BX = (batl >> 2) & 1
            BXPN = (batl >> 9) & 7
        else:
            BX = 0
            BXPN = 0
	bl   = (batu >> 2) & ((1<<15)-1) # Include XBL
	size = (bl + 1) << 17
	bepi = batu >> 17
	brpn = batl >> 17
	Vs_and_Vp = batu & 3
	if Vs_and_Vp == 0:
		pr(" [not enabled mapping]")
		return
	pp = batl & 3
	if pp == 0:
		pr(" [not accessible (protections)]")
		return		
	v_start = bepi << 17
	v_end = v_start + size - 1
	p_start = (brpn << 17) + (BX << 32) + (BXPN << 33)
	p_end = p_start + size - 1
	pr(" [%s-%s -> %s-%s]" % (ppc_hex_str(cpu,v_start), ppc_hex_str(cpu,v_end), ppc_hex_str(cpu,p_start), ppc_hex_str(cpu,p_end)))


def print_spr_list(cpu, spr_list):
    spr_list.sort()
    the_list = []
    cpu_regs = filter(lambda item: item in dir(cpu), spr_list)
    if cpu_regs:
        maxlen = max(map(lambda entry: len(entry), cpu_regs))
    else:
        maxlen = 0
    for spr in cpu_regs:
        the_list.append("%-*s = %s  " % (maxlen, spr, ppc_hex_str(cpu, SIM_get_attribute(cpu, spr))))

    if the_list != []:
        print_list(the_list)
        pr("\n")


def local_pregs(cpu, all):
	the_list = []
	gprs = cpu.gprs
	for i in range(0, 32):
		the_name = "r%d" % (i)
		the_value = gprs[i]
		the_list.append("%-4s = %s  " % (the_name, ppc_hex_str(cpu, the_value)))
	print_list(the_list)
	pr("\n")

	# Condition register
	cr = SIM_read_register(cpu, SIM_get_register_number(cpu, "cr"));
	pr("\n                    ");
	for i in range(0, 8):
		pr("  f%d  " % i);
	pr("\n   cr = 0x%.8x  " % cr);
	for i in range(0, 8):
		f = cr >> (28 - i * 4);
		pr(" %s%s%s%s " % (iff(f & 8, "<", " "),
				   iff(f & 4, ">", " "),
				   iff(f & 2, "=", " "),
				   iff(f & 1, "^", " ")));
	pr("\n\n")

	# XER register
	xer = SIM_read_register(cpu, SIM_get_register_number(cpu, "xer"));
        if cpu.classname in ["ppc-power6"]:
            xer_width = 16
        else:
            xer_width = 8
	pr("  xer = 0x%.*x  %s%s%s byte count %d\n" %
	   (xer_width,
            xer, 
	    iff(xer & 0x80000000, "SO ", ""),
	    iff(xer & 0x40000000, "OV ", ""),
	    iff(xer & 0x20000000, "CA ", ""),
	    xer & 0x7f));

	# Link register and count register
	pr("   lr = %s\n" % ppc_hex_str(cpu,cpu.lr))
	pr("  ctr = %s\n" % ppc_hex_str(cpu,cpu.ctr))
	pr("   pc = %s\n" % ppc_hex_str(cpu,cpu.pc))		

	if all:
		pr("\nVEA & OEA registers:\n")
		pr("====================\n")
                # Configuration/status registers
                conf_spr = ["pvr",
                            "pir",
                            "hid0",
                            "hid1",
                            "hid2",
                            "hid4",
                            "hid5",
                            "rstcfg",
                            "ccr0",
                            "sprg0",
                            "sprg1",
                            "sprg2",
                            "sprg3",
                            "sprg4",
                            "sprg5",
                            "sprg6",
                            "sprg7",
                            "svr",
                            "hsprg0",
                            "hsprg1",
                            "usprg0",
                            "vrsave",
                            "spefcsr",
                            "lpcr",
                            "lpidr",
                            "ctrl",
                            "tfmr",
                            "tscr",
                            "ttr",
                            "ppr"]

                # Misc. (breakpoints, perf counters etc)
                misc_spr = ["bamr",
                            "iabr",
                            "iabr2",
                            "ibcr",
                            "dabr",
                            "dabr2",
                            "dabrx",
                            "dac1",
                            "dac2",
                            "dbcr",
                            "dbcr0",
                            "dbcr1",
                            "dbcr2",
                            "dbdr",
                            "dbsr",
                            "ictct",
                            "thrm1",
                            "thrm2",
                            "thrm3",
                            "thrm4",
                            "pmc1",
                            "pmc2",
                            "pmc3",
                            "pmc4",
                            "pmc5",
                            "pmc6",
                            "pmc7",
                            "pmc8",
                            "iac1",
                            "iac2",
                            "iac3",
                            "iac4",
                            "iarr",
                            "mmcr0",
                            "mmcr1",
                            "mmcra",
                            "mmcrh",
                            "npidr1",
                            "hmisr",
                            "pcr"]

                # Cache & branch buffers
                cache_spr = ["cdbcr",
                             "dccr",
                             "dcdbtrh",
                             "dcdbtrl",
                             "bbear",
                             "bbtar",
                             "buscr",
                             "dcwr",
                             "dnv0",
                             "dnv1",
                             "dnv2",
                             "dnv3",
                             "dtv0",
                             "dtv1",
                             "dtv2",
                             "dtv3",
                             "dvc1",
                             "dvc2",
                             "dvclim",
                             "ear",
                             "icdbdr",
                             "iccr",
                             "icdbdr",
                             "icdbr",
                             "icdbtrh",
                             "icdbtrl",
                             "ictrl",
                             "inv0",
                             "inv1",
                             "inv2",
                             "inv3",
                             "itv0",
                             "itv1",
                             "itv2",
                             "itv3",
                             "ivlim",
                             "l1cfg0",
                             "l1cfg1",
                             "l1csr0",
                             "l1csr1",
                             "l2captdatahi",
                             "l2captdatalo",
                             "l2captecc",
                             "l2cr",
                             "l2errdet",
                             "l2errdis",
                             "l2errinten",
                             "l2errattr",
                             "l2erraddr",
                             "l2erreaddr",
                             "l2errctl",
                             "l2errinjhi",
                             "l2errinjlo",
                             "l2errinjctl"
                             "l2pm",                             
                             "l3cr",
                             "l3ohcr",
                             "l3itcr0",
                             "l3itcr1",
                             "l3itcr2",
                             "l3itcr3",
                             "l3pm",
                             "dscr"]

                # Exception/interrupt
                irq_spr = ["srr0",
                           "srr1",
                           "srr2",
                           "srr3",
                           "hsrr0",
                           "hsrr1",
                           "csrr0",
                           "csrr1",
                           "dar",
                           "hdar",
                           "hdsisr",
                           "dear",
                           "dmiss",
                           "imiss",
                           "dsisr",
                           "esr",
                           "evpr",
                           "ivor0",
                           "ivor1",
                           "ivor2",
                           "ivor3",
                           "ivor4",
                           "ivor5",
                           "ivor6",
                           "ivor7",
                           "ivor8",
                           "ivor9",
                           "ivor10",
                           "ivor11",
                           "ivor12",
                           "ivor13",
                           "ivor14",
                           "ivor15",
                           "ivor16",
                           "ivor32",
                           "ivor33",
                           "ivor34",
                           "ivor35",
                           "ivpr",
                           "mcar",
                           "mcsr",
                           "mcsrr0",
                           "mcsrr1",
                           "hmer",
                           "hmeer"]
                # Timers
                timer_spr = ["tbu",
                             "tbl",
                             "tbhi",
                             "tblo",
                             "dec",
                             "hdec",
                             "decar",
                             "tcr",
                             "tsr",
                             "pit",
                             "purr",
                             "spurr"]
                # MMU
                mmu_spr = ["asr",
                           "amr",
                           "dcmp",
                           "icmp",
                           "sdr1",
                           "su0r",
                           "pid",
                           "pid0",
                           "pid1",
                           "pid2",
                           "pbl1",
                           "pbl2",
                           "pbl3",
                           "pbl4",
                           "tlb0cfg",
                           "tlb1cfg",
                           "ptehi",
                           "ptelo",
                           "hash1",
                           "hash2",
                           "sgr",
                           "sler",
                           "rpa",
                           "rmor",
                           "hrmor",
                           "tlbmiss",
                           "mmucfg",
                           "mmucr",
                           "mmucsr0",
                           "msscr0",
                           "msscr1"
                           "zpr",
                           "ldstcr",
                           "mbar",
                           "mas0",
                           "mas1",
                           "mas2",
                           "mas3",
                           "mas4",
                           "mas5",
                           "mas6"]

                # Debug/trace registers
                debug_spr = ["cfar",
                             "imc",
                             "sdar",
                             "siar",
                             "sprc",
                             "sprd",
                             "trace",
                             "trig0",
                             "trig1",
                             "trig2"]

                print_spr_list(cpu, conf_spr)
                print_spr_list(cpu, misc_spr)
                print_spr_list(cpu, cache_spr)
                print_spr_list(cpu, irq_spr)
                print_spr_list(cpu, timer_spr)
                print_spr_list(cpu, mmu_spr)
                print_spr_list(cpu, debug_spr)

                if "sr" in dir(cpu):
                    # SR[0-15]
                    the_list = []
                    sr = cpu.sr
                    for i in range(16):
			the_name = "sr%d" % (i)
			the_value = sr[i]
			the_list.append("%-4s = 0x%.8x  " % (the_name, the_value))
                    print_list(the_list)
                    pr("\n")
                                       
		# IBAT/DBAT[0-3]
		if "ibat" in dir(cpu):
			if cpu.address_width[1] == 64:
				pr("\n                                                         virtual                                  physical");
			else:
				pr("\n                                         virtual                  physical");
			for i in range(len(cpu.ibat)):
				batu = cpu.ibat[i][0]
				batl = cpu.ibat[i][1]
				pr("\nibat%du = %s ibat%dl = %s" % (i, ppc_hex_str(cpu,batu), i, ppc_hex_str(cpu,batl)))
				print_mapping(cpu, batu, batl)
			pr("\n")
		if "dbat" in dir(cpu): 							
			if cpu.address_width[1] == 64:
				pr("\n                                                         virtual                                  physical");
			else:
				pr("\n                                         virtual                  physical");
			for i in range(len(cpu.dbat)):
				batu = cpu.dbat[i][0]
				batl = cpu.dbat[i][1]
				pr("\ndbat%du = %s dbat%dl = %s" % (i, ppc_hex_str(cpu,batu), i, ppc_hex_str(cpu,batl)))
				print_mapping(cpu, batu, batl)
			pr("\n\n")

                show_msr(cpu)

def show_msr(cpu):
    if cpu.address_width[1] == 64:
        sep = ""
    else:
        sep = " "

    bit_names = cpu.msr_bit_names    
    active = ""
    for i in range(cpu.address_width[1]-1,-1,-1):
        if cpu.msr & 1L<<i:
            active += "%s " % (bit_names[i])
    pr("msr  = %s [%s]\n" % (ppc_hex_str(cpu,cpu.msr), string.strip(active)))
    pr("       %s\n" % (bit_string(cpu.address_width[1], cpu.msr, sep)))
    row = 0
    while 1:
        cont = 0        
        str = "       "        
        for i in range(cpu.address_width[1]-1,-1,-1):
            if len(bit_names[i]) > row:
                str += bit_names[i][row] + sep
                cont = 1
            else:
                str += " " + sep
        print str
        row += 1
        if not cont:
            break
    

register_regexp = re.compile('^(fr?|r)([0-9]+)$');

def local_write_int_register(cpu, reg_name, a_value):
	try:
		match = register_regexp.search(reg_name)
		if match != None:
			n = string.atoi(match.group(2))
			if n < 0 or n > 31:
				raise Exception, "Bad register number"
			if match.group(1) == "r":
				cpu.gprs[n] = a_value;
			else:
				cpu.fprs[n] = a_value;
		else:
			the_number = SIM_get_register_number(cpu, reg_name)
			SIM_write_register(cpu, the_number, a_value)
	except Exception, the_message:
		print the_message

def local_read_int_register(cpu, reg_name):
	try:
		match = register_regexp.search(reg_name)
		if match != None:
			n = string.atoi(match.group(2))
			if n < 0 or n > 31:
				raise Exception, "Bad register number"
			if match.group(1) == "r":
				val = cpu.gprs[n]
			else:
				val = cpu.fprs[n]
		else:
			val = SIM_get_attribute(cpu, reg_name)
	except Exception, message:
		print message
		raise Exception, "Unknown register '" + reg_name + "'"
	return val

def obj_temperature_cmd(obj, temp):
	if temp == -1:
		print "%d C" % obj.temperature
	else:
		obj.temperature = temp


def print_altivec_regs(cpu):
	the_list = []
	try:
		vrs = cpu.vrs
	except:
		pr("This processor doesn't support the Altivec unit\n")
		return
       	for i in range(0,32):
		the_name = "v%d" % (i)
		high_part_value = vrs[i][0]
		low_part_value  = vrs[i][1]
		the_list.append("%-4s = 0x%.16x,%.16x " % (the_name, high_part_value,low_part_value))
	print_list(the_list)
	pr("\n\n");
	pr("vscr   = 0x%.8x [%s%s]\n" % (cpu.vscr,
	   iff(cpu.vscr & ppc_bit32(15), "NJ ",""),
	   iff(cpu.vscr & ppc_bit32(31), "SAT","")))
	pr("vrsave = 0x%.8x\n" % (cpu.vrsave))
	pr("cr6    = 0x%.1x\n" % ((cpu.cr >> 4) & 0xf))	


def pregs_altivec_cmd(cpu):
    if not cpu:
        (cpu, _) = get_cpu(kind = ("ppc", "a PowerPC processor"))
    print_altivec_regs(cpu)

def obj_pregs_altivec_cmd(obj):
    print_altivec_regs(obj)


# Traditional PPC TLB (not 4xx)
def print_tlb(tlb):
	print "Row LRU0 TAG0       PTE0                LRU1 TAG1       PTE1"
	print "--- ---- ---------- ------------------  ---- ---------- ------------------"	
	for i in range(0,len(tlb)):
		if tlb[i][0][0] == 1:
			way0 = "%d   0x%08x 0x%016x" % (tlb[i][0][1], tlb[i][0][2], tlb[i][0][4])
		else:
			way0 = "<invalid entry>"
		if tlb[i][0][1] == 1:
			way1 = "%d   0x%08x 0x%016x" % (tlb[i][1][1], tlb[i][1][2], tlb[i][1][4])
		else:
			way1 = "<invalid entry>"			
		print "%02d   %-34s  %-34s" % (i, way0, way1)


def print_itlb_cmd(cpu):
    if not cpu:
        (cpu, _) = get_cpu(kind = ("ppc", "a PowerPC processor"))
    obj_print_itlb_cmd(cpu)

def obj_print_itlb_cmd(obj):
    try:
        tlb = obj.itlb
    except:
        print "This CPU does not have a separate I-TLB."
        return
    print_tlb(tlb)

def print_dtlb_cmd(cpu):
    if not cpu:
        (cpu, _) = get_cpu(kind = ("ppc", "a PowerPC processor"))
    obj_print_dtlb_cmd(cpu)

def obj_print_dtlb_cmd(obj):
    try:
        tlb = obj.dtlb
    except:
        print "This CPU does not have a separate D-TLB."
        return
    print_tlb(tlb)


def print_40x_utlb(obj):
	print " #  PTEHI       PTELO      PID XW Logical               Physical              ZSEL ZPR[ZSEL]"
	print "--- ----------- ---------- --- -- --------------------- --------------------- ---- ---------"
	tlb = obj.utlb
	for i in range(0,len(tlb)):
		tlbhi = tlb[i][0]
		tlblo = tlb[i][1]
		print " %02d 0x%09x 0x%08x" % (i, tlbhi, tlblo),
		# Check valid bit
		if not tlbhi & (1<<10):
			print " <---- Not enabled ---->"
			continue
		pid = tlbhi & 0xff
		# Size of the mapping
		sz = (tlbhi & (0x7<<11)) >> 11
		size = 1 << (10+sz*2)

		# Check WR bit
		if tlblo & (1<<8):
			wr = 'W'
		else:
			wr = ' '
		# Check EX bit
		if tlblo & (1<<9):
			ex = 'X'
		else:
			ex = ' '
		# ZSEL
		zsel = (tlblo >> 4) & 0xf
		zpr = (obj.zpr >> 30-zsel*2) & 0x3
		if zpr == 0:
			ua = "No access"
			sa = "As TLB"
		elif zpr == 1:
			ua = sa = "As TLB"
		elif zpr == 2:
			ua = "As TLB"
			sa = "XW granted"
		elif zpr == 3:
			ua = sa = "XW granted"			
		# Logical address
		la_start = ((tlbhi >> 14) << 10) & ~((1<<(11+sz*2))-1)
		la_end = la_start + size -1
		# Physical address
		pa_start = tlblo & ~((1<<(11+sz*2))-1)
		pa_end = pa_start + size -1
		print "%03d %c%c 0x%08x-0x%08x 0x%08x-0x%08x %3d    %3d" % (pid,ex,wr,la_start, la_end, pa_start, pa_end, zsel, zpr)
	

def print_440_tlb(obj, tlb):
	print " #  Logical            Physical            TS TID U[0123] WIMGE S[XWR] U[XWR]"
	print "--- ------------------ ------------------- -- ---  ------ -----  ----   -----"	
	for i in range(0,len(tlb)):
		w0 = tlb[i][0]
		w1 = tlb[i][1]
		w2 = tlb[i][2]
		V = ppc_bf40(w0, 22, 22)
		
		if not V:
			# Not valid
			#print "[%02d] Invalid" % (i)
			continue
		
		TS   = ppc_bf40(w0, 23,23)
		SIZE = ppc_bf40(w0, 24,27)
		TID  = ppc_bf40(w0, 32,39)
		size_bits = (SIZE) << 1
		EPN  = ppc_bf40(w0, 0, 21-size_bits)

		ERPN = ppc_bf32(w1, 28, 31)
		RPN  = ppc_bf32(w1, 0, 21-size_bits)

		U03  = ppc_bf32(w2, 16, 19)
		WIMGE = ppc_bf32(w2, 20, 24)
		UXWR  = ppc_bf32(w2, 26, 28)
		SXWR  = ppc_bf32(w2, 29, 31)		

		# Convert to user-friendy representation
		size = 1 << (size_bits + 10)
		v_start = EPN << (10 + size_bits)		
		p_start = (ERPN << 32) | (RPN << (10 + size_bits))
		
		u03_string = bit_string(4, U03,"")
		wimge_string = bit_representation(5, WIMGE, "WIMGE")
		sxwr_string = bit_representation(3, SXWR, "XWR")
		uxwr_string = bit_representation(3, UXWR, "XWR")		

		print "[%2d] %08x-%08x %09x-%09x" % (i,
						     v_start,
						     v_start+size-1,
						     p_start,
						     p_start+size-1),
		print " %d  %02x   %s  %s   %s    %s" % (TS,
							 TID,
							 u03_string,
							 wimge_string,
							 sxwr_string,
							 uxwr_string)



# 4xx TLB
def print_utlb(obj):
	try:
		tlb = obj.utlb
	except:
                # This function is registered automatically for processors
                # with a utlb attribute, so if this function is called on
                # one for which the attribute is missing, something's
                # very wrong indeed.

                raise Exception, "Processor %s has no unified TLB attribute, but yet a command to print it" % obj.classname
	if obj.classname[0:6] == "ppc440":
		print_440_tlb(obj, tlb)
	elif obj.classname == "ppc405gp" or obj.classname == "ppc403gcx":
		print_40x_utlb(obj)
        else:
            raise Exception, "Processor %s has utlb attribute but no defined print_utlb function" % obj.classname


def print_shadow_tlb(obj):
    print "Shadow I-TLB"
    print "============"    
    print_440_tlb(obj, obj.sitlb)
    print
    print "Shadow D-TLB"
    print "============"
    print_440_tlb(obj, obj.sdtlb)
		
def print_utlb_cmd(cpu):
    print "Unified TLB"
    print "==========="    	
    print_utlb(cpu)


def print_shadow_tlb_cmd(cpu_name):
    ( cpu, _ ) = get_cpu(cpu_name, kind = ("ppc", "a PowerPC processor"))
    print_shadow_tlb(cpu)

def obj_print_shadow_tlb_cmd(obj):
    print_shadow_tlb(obj)


    
def obj_print_slb_cmd(cpu):
    try:
        slb = cpu.slb
    except:
        print "This CPU does not have an SLB."
	return
    nvalid = 0
    big_seg_cpus = ["ppc-power6"]

    if cpu.classname in big_seg_cpus:
        print "ix          VSID Ks Kp N C B L LP TA      ESID"
    else:
        print "ix          VSID Ks Kp N L C      ESID"

    for i in range(len(slb[None])):
        slbe = slb[i]
	if (slbe[1] >> 27) & 1:
            nvalid += 1

            if cpu.classname in big_seg_cpus:
                B = (slbe[0] >> 62) & 0x3
                vsid = (slbe[0] >> 12) & ((1L << 50) - 1)
            else:
                vsid = (slbe[0] >> 12) & ((1L << 52) - 1)
	    Ks = (slbe[0] >> 11) & 1
	    Kp = (slbe[0] >> 10) & 1
	    N = (slbe[0] >> 9) & 1
	    L = (slbe[0] >> 8) & 1
	    C = (slbe[0] >> 7) & 1
            TA = (slbe[0] >> 6) & 1
            LP = (slbe[0] >> 4) & 0x3
	    esid = (slbe[1] >> 28) & ((1L << 36) - 1)

            if cpu.classname in big_seg_cpus:
                esid_bits = 36
                if B == 1:  # B=1 is the only architectured B encoding
                    esid_bits_diff = 40 - 28
                    esid >>= esid_bits_diff
                    esid_bits = 36 - esid_bits_diff
                esid_field_length = esid_bits / 4
                esid_spaces = ' ' * (36 / 4 - esid_field_length)

                print ("%2d %013x  %1d  %1d %1d %1d %1d %1d %2d %2d %s%0*x"
                       % (i, vsid, Ks, Kp, N, C, B, L, LP, TA,
                          esid_spaces, esid_field_length, esid))
            else:
                print ("%2d %013x  %1d  %1d %1d %1d %1d %09x"
                       % (i, vsid, Ks, Kp, N, L, C, esid))

    if nvalid == 0:
        print "(no valid entries in the SLB)"



def obj_print_tlb64_cmd(cpu):
    try:
        tlb = cpu.tlb
    except:
        print "This CPU does not have a 64-bit unified TLB."
        return
    nvalid = 0
    print " ix               VPN L           RPN C WIMG PP               EA"
    for i in range(len(tlb)):
        for tlbe in tlb[i]:
            (vsid, page, valid, large, big_seg_enc, lp, pte1, epa) = tlbe
            if not valid:
                continue
            nvalid += 1
            rpn = (pte1 >> 12) & ((1L << 50) - 1)
            C = (pte1 >> 7) & 1
            W = (pte1 >> 6) & 1
            I = (pte1 >> 5) & 1
            M = (pte1 >> 4) & 1
            G = (pte1 >> 3) & 1
            pp = (pte1 & 2) << 3 | (pte1 & 1) # so it looks right in hex
            print ("%3d %013x%04x %1d %013x %1d %1d%1d%1d%1d %02x %016x"
                   % (i, vsid, page, large, rpn,
                      C, W, I, M, G, pp, epa))
    if nvalid == 0:
        print "(No valid entries in the TLB)"

def print_l2tlb_entry(tlb, tlbe, idx, assoc):
    mas0 = tlbe[0]
    mas1 = tlbe[1]
    mas2 = tlbe[2]
    mas3 = tlbe[3]
    
    V = ppc_bf64(mas1, 32, 32)
    if V:        
        TS =  ppc_bf64(mas1, 51, 51)
        TID = ppc_bf64(mas1, 36, 47)
        EPN = ppc_bf64(mas2, 32, 51)

        RPN = ppc_bf64(mas3, 32, 51)
        if tlb == 0:
            # 4K mappings only
            TSIZE = 1
        else:
            IPROT = ppc_bf64(mas1, 33, 33)            
            TSIZE = ppc_bf64(mas1, 52, 55)

        U03  = ppc_bf64(mas3, 54, 57)

        WIMGE = ppc_bf64(mas2, 59, 63)
        SXWR = (ppc_bf64(mas3, 59, 59) << 2) | (ppc_bf64(mas3, 61, 61) << 1) | (ppc_bf64(mas3, 63, 63))
        UXWR = (ppc_bf64(mas3, 58, 58) << 2) | (ppc_bf64(mas3, 60, 60) << 1) | (ppc_bf64(mas3, 62, 62))        

        # Make readable presentations
        size = 1 << (10+TSIZE*2)
        v_start = EPN << 12
        v_end   = v_start + size -1
        p_start = RPN << 12
        p_end   = p_start + size -1

        u03_string = bit_string(4, U03,"")
        wimge_string = bit_representation(5, WIMGE, "WIMGE")        
        sxwr_string = bit_representation(3, SXWR, "XWR")
        uxwr_string = bit_representation(3, UXWR, "XWR")		
        
        if tlb == 0:
            print "[%3d-%d] %08x-%08x %08x-%08x  %d %3d   %s  %s   %s    %s" % (idx,
                                                                                assoc,                                                    
                                                                                v_start,
                                                                                v_end,
                                                                                p_start,
                                                                                p_end,
                                                                                TS,
                                                                                TID,
                                                                                u03_string,
                                                                                wimge_string,
                                                                                sxwr_string,
                                                                                uxwr_string)
        else:
            print "[%2d] %08x-%08x %08x-%08x  %d %3d   %s  %s   %s    %s   %d" % (idx,
                                                                                v_start,
                                                                                v_end,
                                                                                p_start,
                                                                                p_end,
                                                                                TS,
                                                                                TID,                                                                         
                                                                                u03_string,
                                                                                wimge_string,                                                                         
                                                                                sxwr_string,
                                                                                uxwr_string,
                                                                                IPROT)

def obj_print_l2tlb_cmd(cpu):
    # L2 TLB0, 4K Entries only
    print "L2 TLB0"
    print "   # W  Logical           Physical          TS TID U[0123] WIMGE S[XWR] U[XWR]"
    print "------  ----------------- ----------------- -- ---  ------ -----  ----   -----"	
    for i in range(len(cpu.tlb0)):
        for a in range(len(cpu.tlb0[i])):
            tlbe = cpu.tlb0[i][a]
            print_l2tlb_entry(0, tlbe, i, a)            

    # L2 TLB1, variable size mappings fully associated
    print    
    print "L2 TLB1"
    print " #  Logical            Physical          TS TID U[0123] WIMGE S[XWR] U[XWR] IPROT"
    print "--- ------------------ ----------------- -- ---  ------ -----  ----   ----- -----"	
    for i in range(len(cpu.tlb1)):
        tlbe = cpu.tlb1[i]
        print_l2tlb_entry(1, tlbe, i, 0)
    
    
#
# --- pregs-fpu ---
#

def print_fpu_regs(cpu, f, x, i, b):
	if f + x + i + b == 0:
		x = 1
	if f + x + i + b > 1:
		print "Only one flag of -f, -x, -i, -b can be given to the command"
		return

	pr("Double precision (64-bit), ")
	fp_regs = cpu.fprs[None]
	prec = "d"
	mult = 1
	fdigits = 15
	fsize = 23
	
	if f:
		pr("floating point view\n")
	if x:
		pr("hexadecimal integer view\n")
	if i:
		pr("decimal integer view\n")
	if b:
		pr("binary floating point view\n")
	for c in range(len(fp_regs)):
		pr("%%f%-2d " % (c * mult))
		if f:
			pr("%s\n" % fp_to_string.fp_to_string_fixed(prec, fp_regs[c], fdigits, fsize))
		if x:
			pr("0x%x\n" % fp_regs[c])
		if i:
			pr("%d\n" % fp_regs[c])
		if b:
			pr("%s\n" % fp_to_string.fp_to_binstring(prec, fp_regs[c]))
	pr("\n")
	# Floating point status and control register (optional)
	fpscr = SIM_read_register(cpu, SIM_get_register_number(cpu, "fpscr"));
	round_kind = [ "round-nearest", "round-zero", "round-pinf", "round-ninf" ];
        fpscr_64bit_targets = ['ppc-power6']
        if cpu.classname in fpscr_64bit_targets:
            fpscr_field_length = 16
        else:
            fpscr_field_length = 8
	pr("fpscr = 0x%.*x   " % (fpscr_field_length, fpscr));
	pr("%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s %s\n" %
	   (iff(fpscr & 0x80000000, "FX ", ""),
	    iff(fpscr & 0x40000000, "FEX ", ""),
	    iff(fpscr & 0x20000000, "VX ", ""),
	    iff(fpscr & 0x10000000, "OX ", ""),
	    iff(fpscr & 0x08000000, "UX ", ""),
	    iff(fpscr & 0x04000000, "ZX ", ""),
	    iff(fpscr & 0x02000000, "XX ", ""),
	    iff(fpscr & 0x01000000, "VXSNAN ", ""),
	    iff(fpscr & 0x00800000, "VXISI ", ""),
	    iff(fpscr & 0x00400000, "VXIDI ", ""),
	    iff(fpscr & 0x00200000, "VXZDZ ", ""),
	    iff(fpscr & 0x00100000, "VXIMZ ", ""),
	    iff(fpscr & 0x00080000, "VXVC ", ""),
	    iff(fpscr & 0x00040000, "FR ", ""),
	    iff(fpscr & 0x00020000, "FI ", ""),
	    ("FPRF[%s%s%s%s%s] " %
	     (iff (fpscr & 0x00010000, "C", ""),
	      iff (fpscr & 0x00008000, "<", ""),
	      iff (fpscr & 0x00004000, ">", ""),
	      iff (fpscr & 0x00002000, "=", ""),
	      iff (fpscr & 0x00001000, "?", ""))),
	    iff(fpscr & 0x00000400, "VXSOFT ", ""),
	    iff(fpscr & 0x00000200, "VXSQRT ", ""),
	    iff(fpscr & 0x00000100, "VXCVI ", ""),
	    iff(fpscr & 0x00000080, "VE ", ""),
	    iff(fpscr & 0x00000040, "OE ", ""),
	    iff(fpscr & 0x00000020, "UE ", ""),
	    iff(fpscr & 0x00000010, "ZE ", ""),
	    iff(fpscr & 0x00000008, "XE ", ""),
	    iff(fpscr & 0x00000004, "NI ", ""),
		    round_kind[fpscr & 3]));

def pregs_fpu_cmd(cpu, f, x, i, b):
    if not cpu:
        ( cpu, _ ) = get_cpu(kind = ("ppc", "a PowerPC processor"))
    print_fpu_regs(cpu, f, x, i, b)

def obj_pregs_fpu_cmd(obj, f, x, i, b):
    print_fpu_regs(obj, f, x, i, b)


def obj_bootstrap_tlb_entry_cmd(obj, update_flag, epn, ts, tid, erpn, rpn):
    w0 = obj.bootstrap_tlb_entry[0]
    w1 = obj.bootstrap_tlb_entry[1]
    w2 = obj.bootstrap_tlb_entry[2]

    # Get current values
    V = ppc_bf40(w0, 22, 22)    
    TS   = ppc_bf40(w0, 23,23)
    SIZE = ppc_bf40(w0, 24,27)
    TID  = ppc_bf40(w0, 32,39)
    size_bits = (SIZE) << 1
    EPN  = ppc_bf40(w0, 0, 21-size_bits)
    ERPN = ppc_bf32(w1, 28, 31)
    RPN  = ppc_bf32(w1, 0, 21-size_bits)
    U03  = ppc_bf32(w2, 16, 19)
    WIMGE = ppc_bf32(w2, 20, 24)
    UXWR  = ppc_bf32(w2, 26, 28)
    SXWR  = ppc_bf32(w2, 29, 31)		

    # Update with user selections
    if epn != -1:
        EPN = epn
    if ts != -1:
        TS = ts
    if tid != -1:
        TID = tid
    if erpn != -1:
        ERPN = erpn        
    if rpn != -1:
        RPN = rpn        
    
    size_bits = (SIZE) << 1
    new_w0 = (ppc_set_bf40(V, 22, 22)
              | ppc_set_bf40(TS, 22, 23)
              | ppc_set_bf40(SIZE, 24, 27)
              | ppc_set_bf40(TID, 32, 39)
              | ppc_set_bf40(EPN, 0, 21-size_bits))
    new_w1 = (ppc_set_bf32(ERPN, 28, 31)
              | ppc_set_bf32(RPN, 0, 21-size_bits))
    new_w2 = (ppc_set_bf32(U03, 16, 19)
              | ppc_set_bf32(WIMGE, 20, 24)
              | ppc_set_bf32(UXWR, 26, 28)
              | ppc_set_bf32(SXWR, 29, 31))
    
    # Update & display the mapping we have now
    if new_w0 != w0 or new_w1 != w1 or new_w2 != w2:
        obj.bootstrap_tlb_entry = [new_w0, new_w1, new_w2]
        print "Updated mapping:"
        print "================"
    else:
        print "Current mapping:"
        print "================"                
    print_440_tlb(obj, [obj.bootstrap_tlb_entry])

    if update_flag:
        sitlb = obj.sitlb
        sdtlb = obj.sdtlb
        sitlb[0] = sdtlb[0] = [new_w0, new_w1, new_w2]
        obj.sitlb = sitlb
        obj.sdtlb = sdtlb
        SIM_dump_caches()

def local_pending_exception(cpu):
    if cpu.pending_irq_name != "":
        return "Pending exception (%s)" % cpu.pending_irq_name
    else: 
        return None

def register_diff_registers(user_data, obj):
    # Remove register not interesting to see being changed all the time
    def remove_regs(cpu, regs, rm_regs):
        for r in rm_regs:
            try:
                regs.remove(SIM_get_register_number(cpu, r))
            except:
                pass
        return regs

    ( ppc_model, funcs ) = user_data
    cpu = SIM_next_queue(None)
    while cpu:
        if cpu.classname == ppc_model:
            break
        cpu = SIM_next_queue(cpu)
    if cpu == None:
        # no cpu found, wait for next Configuration_Loaded
        return
    diff_regs = SIM_get_all_registers(cpu)
    diff_regs = remove_regs(cpu, diff_regs,
                            ["pc", "dec", "pit", "purr", "hdec",
                             "tbl", "tbu",
                             "utbl", "utbu",
                             "tbhi", "tblo"])
    SIM_hap_delete_callback("Core_Configuration_Loaded",
                            register_diff_registers, user_data)
    def f(x):
        return SIM_get_register_name(cpu, x)
    funcs['diff_regs'] = map(f, diff_regs)

# Modify the ppc model specific functions
def setup_local_functions(ppc_model, funcs):
    funcs['print_disassemble_line'] = local_print_disassemble_line
    funcs['pregs'] = local_pregs
    funcs['get_pending_exception_string'] = local_pending_exception    
    SIM_hap_add_callback("Core_Configuration_Loaded", register_diff_registers, (ppc_model, funcs))


# Generic PPC commands
def enable_generic_ppc_commands(ppc_model):
    new_command("temperature", obj_temperature_cmd,
                [arg(int_t, "degrees-celsius", "?", -1)],
                namespace = ppc_model,	    
                type  = "inspect/change commands",
                short = "set or query the temperature of the processor",
                doc = """
                If the simulated PowerPC processor is equipped with a TAU (Thermal Assist Unit),
                this command allows TAU related features to be tested.
                Without any arguments, the command prints the current set temperature.
                The temperature can be changed by specifying the wanted temperature.
                This command accesses the <tt>temperature</tt> attribute on the processor.
                """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1119")


def enable_fpu_commands(ppc_model):
    # Only for processors with FPU
    if not simics_command_exists("pregs-fpu"):
        new_command("pregs-fpu", pregs_fpu_cmd,
                    [arg(obj_t('PPC processor', 'ppc'), "cpu-name", "?"),
                     arg(flag_t, "-f"), arg(flag_t, "-x"), arg(flag_t, "-i"),
                     arg(flag_t, "-b")],
                    namespace_copy = (ppc_model, obj_pregs_fpu_cmd),
                    type  = "inspect/change commands",
                    short = "print the floating point registers",
                    doc = """
                    Prints the contents of the floating point registers.<br/>
                    This command can take one subregister size flag and one formatting flag.<br/>
                    The formatting flags -f, -x, and -i select the formatting of the output.
                    The -f flag prints the floating-point values of the registers.
                    The -x flag prints the contents of the registers as hexadecimal integers.
                    The -i flag prints the contents of the registers as decimal integers.
                    With the -b flag, the registers are printed in binary floating point form.
                    """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1136")

def enable_altivec_commands(ppc_model):    
    # Only for models with Altivec
    if not simics_command_exists("pregs-altivec"):    
        new_command("pregs-altivec", pregs_altivec_cmd,
                    [arg(obj_t('PPC processor', 'ppc'), "cpu-name", "?")],
                    type  = "inspect/change commands",
                    short = "print cpu altivec registers",
                    namespace_copy = (ppc_model, obj_pregs_altivec_cmd),
                    doc = """
                    Prints the altivec vector register file of the processor
                    <i>cpu_name</i>. If no CPU is specified, the current CPU will be
                    selected. 
                    """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1156")

def enable_classic_tlb_commands(ppc_model):
    # 'Classic' MMU ["ppc603e", "ppc750", "ppc750fx", "ppc7400", "ppc7447", "ppc7450"]:
    if not simics_command_exists("print-itlb"):
        new_command("print-itlb", print_itlb_cmd,
                    [arg(obj_t('PPC processor', 'ppc'), "cpu-name", "?")],
                    type  = "deprecated commands",
                    short = "print instruction tlb contents",
                    deprecated = "<"+ppc_model+">.print-itlb",
                    doc = """
                    Prints the contents of the instruction TLB of the processor
                    <i>cpu_name</i>. If no CPU is specified, the current CPU will be
                    selected. 
                    """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1170")
    new_command("print-itlb", obj_print_itlb_cmd,
                [],
                type  = "inspect/change commands",
                short = "print instruction tlb contents",
                namespace = ppc_model,
                doc = """
                Prints the contents of the instruction TLB of the processor.
                """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1180")
    if not simics_command_exists("print-dtlb"):        
        new_command("print-dtlb", print_dtlb_cmd,
                    [arg(obj_t('PPC processor', 'ppc'), "cpu-name", "?")],
                    type  = "deprecated commands",
                    short = "print data tlb contents",
                    deprecated = "<"+ppc_model+">.print-dtlb",
                    doc = """
                    Prints the contents of the data TLB of the processor
                    <i>cpu_name</i>. If no CPU is specified, the current CPU will be
                    selected. 
                    """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1189")
    new_command("print-dtlb", obj_print_dtlb_cmd,
                [],
                type  = "inspect/change commands",
                short = "print data tlb contents",
                namespace = ppc_model,
                doc = """
                Prints the contents of the data TLB of the processor.
                """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1199")

def enable_4xx_tlb_commands(ppc_model):
    # 4xx MMU
    new_command("print-utlb", print_utlb_cmd,
                [],
                type  = "inspect/change commands",
                short = "print unified tlb contents",
                namespace = ppc_model,
                doc = """
                Prints the contents of the unified TLB of the processor.
                """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1210")

def enable_440_tlb_commands(ppc_model):
    new_command("print-shadow-tlb", obj_print_shadow_tlb_cmd,
                [],
                type  = "inspect/change commands",
                short = "print shadow tlb contents",
                namespace = ppc_model,
                doc = """
                Prints the contents of the shadown I and D  TLB of the processor
                <i>cpu_name</i>. If no CPU is specified, the current CPU will be
                selected. Simics caches instruction and data information
                internally, therfore the content of the shadow entries does not
                necessarely match cached entries on the hardware. Support for
                shadow TLBs are mainly maintained by Simics to support the bootstrap.
                """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1220")
    new_command("bootstrap-tlb-entry", obj_bootstrap_tlb_entry_cmd,                
                [arg(flag_t, "-update"),
                 arg(int_t, "EPN", "?", -1),
                 arg(int_t, "TS", "?", -1),
                 arg(int_t, "TID", "?", -1),
                 arg(int_t, "ERPN", "?", -1),
                 arg(int_t, "RPN", "?", -1)],
                type  = "inspect/change commands",
                short = "print or change the default bootstrap mapping",
                namespace = ppc_model,
                doc = """
                Modify or print current default mapping which is copied to shadow
                TLB entry zero when processor is reset. The <flag>-update</flag> causes
                the shadow tlb entry to be updated directly. Several fields, but not all,
                can be modified by specifying the field name and its value.
                """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1233")

def enable_e500_tlb_commands(ppc_model):
    new_command("print-l2tlb", obj_print_l2tlb_cmd,
                type  = "inspect/change commands",
                short = "print L2 TLB contents contents",
                namespace = ppc_model,
                doc = """
                Prints the contents of the L2 TLB0 and TLB1 of the processor.
                The L1 TLBs are invisible to software and not simulated.
                Only valid entries are shown.                
                """, filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1251")

def enable_ppc64_commands(ppc_model):
    new_command("print-slb", obj_print_slb_cmd,
                type  = "inspect/change commands",
                short = "print SLB contents",
                namespace = ppc_model,
                doc = """
                Prints the contents of the SLB (Segment Lookaside Buffer).
                Only valid entries are shown.""", filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1262")
    
    new_command("print-tlb", obj_print_tlb64_cmd,
                type  = "inspect/change commands",
                short = "print 64-bit TLB contents",
                namespace = ppc_model,
                doc = """
                Prints the contents of the TLB in 64-bit PPC implementations.
                Only valid entries are shown.""", filename="/mp/simics-3.0/src/core/ppc/commands.py", linenumber="1270")

funcs = {
    'print_disassemble_line': local_print_disassemble_line,
    'pregs':                  local_pregs,
}
