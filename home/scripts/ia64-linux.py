
##  Copyright 2001-2007 Virtutech AB
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

import string, traceback, sim_core

# ---------------------------------------------------------------------------
#
#  read/write cpu registers
#
# ---------------------------------------------------------------------------

r0 = SIM_get_register_number(conf.cpu0, "r0")
nat0 = SIM_get_register_number(conf.cpu0, "r0.nat")
ar_kr6 = SIM_get_register_number(conf.cpu0, "ar.kr6")

def read_gr(regno):
    cpu = SIM_current_processor()
    return SIM_read_register(cpu, r0 + regno), SIM_read_register(cpu, nat0 + regno)

def read_register(reg):
    return SIM_read_register(SIM_current_processor(), SIM_get_register_number(conf.cpu0, reg))

# Signed read
def sread_register(reg):
    val = read_register(reg)
    if val & 0x8000000000000000L:
        val -= 0x10000000000000000L
    return val

def read_cr(cr):
    return read_register("cr." + cr)


# ---------------------------------------------------------------------------
#
#  read/write physical memory
#
# ---------------------------------------------------------------------------

def linux_read_bytes(cpu, address, size):
    return cpu.physical_memory.memory[[address, address + size - 1]]

def linux_read_byte(cpu, address):
    return linux_read_bytes(cpu, address, 1)[0]

def linux_read_word(cpu, address):
    word = linux_read_bytes(cpu, address, 4)
    return (word[3] << 24) | (word[2] << 16) | (word[1] << 8) | word[0]

# ---------------------------------------------------------------------------
#
#  read logical memory
#
# ---------------------------------------------------------------------------

def linux_read_string(cpu, address, maxlen):
    s = ""
    try:
        while len(s) < maxlen:
            p = SIM_logical_to_physical(cpu, 1, address)
            c = SIM_read_phys_memory(cpu, p, 1)
            if c == 0:
                return s
            s += char(c)
        s += "..."
    except:
        s += "???"
    return s

# ---------------------------------------------------------------------------
#
#  system calls
#
# ---------------------------------------------------------------------------

def format_stringbuf(regno):
    cpu = SIM_current_processor()
    va = SIM_read_register(cpu, r0 + regno)
    len = SIM_read_register(cpu, r0 + regno + 1)
    s = "0x%x = \"" % va
    for i in xrange(0, len):
        if i > 64:
            return s + "\" ..."
        try:
            pa = SIM_logical_to_physical(cpu, 1, va + i)
        except:
            return s + "\" ..."
        b = linux_read_byte(cpu, pa)
        if b == 9:
            s += "\\t"
        elif b == 10:
            s += "\\n"
        elif b == 13:
            s += "\\r"
        elif b == 92:
            s += "\\\\"
        elif b >= 32 and b < 127:
            s += chr(b)
        else:
            s += "<%02x>" % b
    return s + "\""

def fmt_pipe_ret(regno):
    cpu = SIM_current_processor()
    fd1 = SIM_read_register(cpu, r0 + 8)
    fd2 = SIM_read_register(cpu, r0 + 9)
    if fd1 < 0:
        return str(fd1)
    return "[%d, %d]" % (fd1, fd2)

def fmt_wait4_ret(ignored_regno):
    try:
        cpu = SIM_current_processor()
        s = "%d" % SIM_read_register(cpu, r0 + 8)
        statusp = SIM_read_register(cpu, r0 + 33)
        rusagep = SIM_read_register(cpu, r0 + 35)
        if statusp != 0:
            try:
                statusp = SIM_logical_to_physical(cpu, 1, statusp)
                status = SIM_read_phys_memory(cpu, statusp, 2)
                s += " status: %d" % ((status & 0xff00) >> 8)
                if status & 0xf7:
                    s += " signal(%d)" % (status & 0xf7)
            except:
                s += " status: <not in tlb>"
        return s
    except:
        traceback.print_exc()


def fmt_uname_ret(ignored_regno):
    try:
        cpu = SIM_current_processor()
        lutsp = SIM_read_register(cpu, r0 + 32)

        s = "%d" % SIM_read_register(cpu, r0 + 8)

        try:
            putsp = SIM_logical_to_physical(cpu, 1, lutsp)
        except:
            return s

        sysname = linux_read_string(cpu, lutsp, 65)
        nodename = linux_read_string(cpu, lutsp + 65, 65)
        release = linux_read_string(cpu, lutsp + 130, 65)
        version = linux_read_string(cpu, lutsp + 195, 65)
        machine = linux_read_string(cpu, lutsp + 260, 65)
        domainname = linux_read_string(cpu, lutsp + 325, 65)

        return s + (" { %s, %s, %s, %s, %s, %s }" %
                    (sysname, nodename, release, version, machine, domainname))
    except:
        traceback.print_exc()

def fmt_swapflags(regno):
    cpu = SIM_current_processor()
    swapflags = SIM_read_register(cpu, regno)
    s = "%d" % (swapflags & 0x7fff)
    if swapflags & 0x8000:
        s += "|PREFER"
    return s
    

linux_syscalls = {

     1024 : [ "ni_syscall",		""],
     1025 : [ "exit",			"d:v"],
     1026 : [ "read",			"dxd:d"],
     1027 : [ "write",			(["d", format_stringbuf, "d"], "d")],
     1028 : [ "open",			"sd:d"],
     1029 : [ "close",			"d:d"],
     1030 : [ "creat",			"sd:d"],
     1031 : [ "link",			"ss:d"],
     1032 : [ "unlink",			"s:d"],
     1033 : [ "execve",			"sxx:v"],
     1034 : [ "chdir",			"s:d"],
     1035 : [ "fchdir",			"d:d"],
     1036 : [ "utimes",			""],
     1037 : [ "mknod",			""],
     1038 : [ "chmod",			""],
     1039 : [ "chown",			""],
     1040 : [ "lseek",			"ddd:d"],
     1041 : [ "getpid",			":d"],
     1042 : [ "getppid",		""],
     1043 : [ "mount",			""],
     1044 : [ "umount",			""],
     1045 : [ "setuid",			""],
     1046 : [ "getuid",			""],
     1047 : [ "geteuid",		""],
     1048 : [ "ptrace",			""],
     1049 : [ "access",			"sd:d"],
     1050 : [ "sync",			""],
     1051 : [ "fsync",			""],
     1052 : [ "fdatasync",		""],
     1053 : [ "kill",			"dd:d"],
     1054 : [ "rename",			""],
     1055 : [ "mkdir",			""],
     1056 : [ "rmdir",			""],
     1057 : [ "dup",			"d:d"],
     1058 : [ "pipe",			("x", fmt_pipe_ret)],
     1059 : [ "times",			""],
     1060 : [ "brk",			"x:x"],
     1061 : [ "setgid",			""],
     1062 : [ "getgid",			""],
     1063 : [ "getegid",		""],
     1064 : [ "acct",			""],
     1065 : [ "ioctl",			"dxx:d"],
     1066 : [ "fcntl",			"dxx:d"],
     1067 : [ "umask",			""],
     1068 : [ "chroot",			"s:d"],
     1069 : [ "ustat",			""],
     1070 : [ "dup2",			"dd:d"],
     1071 : [ "setreuid",		""],
     1072 : [ "setregid",		""],     
     1073 : [ "getresuid",		""],
     1074 : [ "setresuid",		""],
     1075 : [ "getresgid",		""],
     1076 : [ "setresgid",		""],
     1077 : [ "getgroups",		""],
     1078 : [ "setgroups",		""],
     1079 : [ "getpgid",		""],
     1080 : [ "setpgid",		""],
     1081 : [ "setsid",			""],
     1082 : [ "getsid",			""],
     1083 : [ "sethostname",		""],
     1084 : [ "setrlimit",		""],
     1085 : [ "getrlimit",		""],
     1086 : [ "getrusage",		""],
     1087 : [ "gettimeofday",		""],
     1088 : [ "settimeofday",		""],
     1089 : [ "select",			""],
     1090 : [ "poll",			""],
     1091 : [ "symlink",		""],
     1092 : [ "readlink",		"sxd:d"],
     1093 : [ "uselib",			""],
     1094 : [ "swapon",			(["s", fmt_swapflags], "d")],
     1095 : [ "swapoff",		"s:d"],
     1096 : [ "reboot",			""],
     1097 : [ "truncate",		""],
     1098 : [ "ftruncate",		""],
     1099 : [ "fchmod",			""],
     1100 : [ "fchown",			""],
     1101 : [ "getpriority",		""],
     1102 : [ "setpriority",		""],
     1103 : [ "statfs",			""],
     1104 : [ "fstatfs",		""],    
     1106 : [ "semget",			""],
     1107 : [ "semop",			""],
     1108 : [ "semctl",			""],
     1109 : [ "msgget",			""],
     1110 : [ "msgsnd",			""],
     1111 : [ "msgrcv",			""],
     1112 : [ "msgctl",			""],
     1113 : [ "shmget",			""],
     1114 : [ "shmat",			""],
     1115 : [ "shmdt",			""],
     1116 : [ "shmctl",			""],
     1117 : [ "syslog",			""],
     1118 : [ "setitimer",		""],
     1119 : [ "getitimer",		""],
     1120 : [ "old_stat",		""],
     1121 : [ "old_lstat",		""],
     1122 : [ "old_fstat",		""],
     1123 : [ "vhangup",		""],
     1124 : [ "lchown",			""],
     1125 : [ "vm86",			""],
     1126 : [ "wait4",			("dxdx", fmt_wait4_ret)],
     1127 : [ "sysinfo",		""],
     1128 : [ "clone",			"xxxx:d"],
     1129 : [ "setdomainname",		""],
     1130 : [ "uname",			("x", fmt_uname_ret)],
     1131 : [ "adjtimex",		""],
     1132 : [ "create_module",		""],
     1133 : [ "init_module",		""],
     1134 : [ "delete_module",		""],
     1135 : [ "get_kernel_syms",	""],
     1136 : [ "query_module",		""],
     1137 : [ "quotactl",		""],
     1138 : [ "bdflush",		""],
     1139 : [ "sysfs",			""],
     1140 : [ "personality",		""],
     1141 : [ "afs_syscall",		""],
     1142 : [ "setfsuid",		""],
     1143 : [ "setfsgid",		""],
     1144 : [ "getdents",		""],
     1145 : [ "flock",			""],
     1146 : [ "readv",			""],
     1147 : [ "writev",			""],
     1148 : [ "pread",			""],
     1149 : [ "pwrite",			""],
     1150 : [ "_sysctl",		""],
     1151 : [ "mmap",			"xxdxxx:x"],
     1152 : [ "munmap",			"xx:d"],
     1153 : [ "mlock",			""],
     1154 : [ "mlockall",		""],
     1155 : [ "mprotect",		""],
     1156 : [ "mremap",			""],
     1157 : [ "msync",			""],
     1158 : [ "munlock",		""],
     1159 : [ "munlockall",		""],
     1160 : [ "sched_getparam",		""],
     1161 : [ "sched_setparam",		""],
     1162 : [ "sched_getscheduler",	""],
     1163 : [ "sched_setscheduler",	""],
     1164 : [ "sched_yield",		""],
     1165 : [ "sched_get_priority_max",	""],
     1166 : [ "sched_get_priority_min",	""],
     1167 : [ "sched_rr_get_interval",	""],
     1168 : [ "nanosleep",		""],
     1169 : [ "nfsservctl",		""],
     1170 : [ "prctl",			""],
     1172 : [ "mmap2",			""],
     1173 : [ "pciconfig_read",		""],
     1174 : [ "pciconfig_write",	""],
     1175 : [ "perfmonctl",		""],
     1176 : [ "sigaltstack",		""],
     1177 : [ "rt_sigaction",		"dxxd:d"],
     1178 : [ "rt_sigpending",		"xd:d"],
     1179 : [ "rt_sigprocmask",		"dxxd:d"],
     1180 : [ "rt_sigqueueinfo",	"ddx:d"],
     1181 : [ "rt_sigreturn",		""],
     1182 : [ "rt_sigsuspend",		""],
     1183 : [ "rt_sigtimedwait",	"xxxd:d"],
     1184 : [ "getcwd",			""],
     1185 : [ "capget",			""],
     1186 : [ "capset",			""],
     1187 : [ "sendfile",		""],
     1188 : [ "getpmsg",		""],
     1189 : [ "putpmsg",		""],
     1190 : [ "socket",			"ddd:d"],
     1191 : [ "bind",			""],
     1192 : [ "connect",		""],
     1193 : [ "listen",			""],
     1194 : [ "accept",			""],
     1195 : [ "getsockname",		""],
     1196 : [ "getpeername",		""],
     1197 : [ "socketpair",		""],
     1198 : [ "send",			""],
     1199 : [ "sendto",			""],
     1200 : [ "recv",			""],
     1201 : [ "recvfrom",		""],
     1202 : [ "shutdown",		""],
     1203 : [ "setsockopt",		""],
     1204 : [ "getsockopt",		""],
     1205 : [ "sendmsg",		""],
     1206 : [ "recvmsg",		""],
     1207 : [ "pivot_root",		""],
     1208 : [ "mincore",		""],
     1209 : [ "madvise",		""],
     1210 : [ "stat",			"sx:d"],
     1211 : [ "lstat",			"sx:d"],
     1212 : [ "fstat",			"dx:d"],
     1213 : [ "clone2",			""],
     1214 : [ "getdents64",		""],
     
}


# ---------------------------------------------------------------------------
#
#  read data from current task_struct
#
# ---------------------------------------------------------------------------

task_name_offset = 0x57a
task_pid_offset = 0xcc

def current_task(cpu):
    return SIM_read_register(cpu, ar_kr6)

def current_comm():
    comm = linux_read_bytes(read_register("ar.kr6") + task_name_offset, 16)
    name = ""
    for c in comm:
        if c == 0:
            break
        name += chr(c)
    return name

def current_process(cpu, task = None):
    if not task:
        task = SIM_read_register(cpu, ar_kr6)
    try:
        pid = SIM_read_phys_memory(cpu, task + task_pid_offset, 4)
        comm = linux_read_bytes(cpu, task + task_name_offset, 16)
        name = ""
        for c in comm:
            if c == 0:
                break
            name += chr(c)        
        return pid, name
    except sim_core.SimExc_Memory:
        return None, None


# ---------------------------------------------------------------------------
#
#  parse system call name and arguments
#
# ---------------------------------------------------------------------------

def string_argument(regno):
    cpu = SIM_current_processor()
    va, nat = read_gr(regno)
    if nat:
        return "NaT"
    s = "\""
    for i in xrange(0, 64):
        try:
            pa = SIM_logical_to_physical(cpu, 1, va + i)
        except:
            return "0x%x" % va
        b = linux_read_byte(cpu, pa)
        if b == 0:
            return s + "\""
        elif b == 9:
            s += "\\t"
        elif b == 10:
            s += "\\n"
        elif b == 13:
            s += "\\r"
        elif b >= 32:
            s += chr(b)
        else:
            s += "<%02x>"
    return s + "\""

def int_argument(regno):
    i, nat = read_gr(regno)
    if nat:
        return "NaT"
    if i & 0x8000000000000000L:
        i -= 0x10000000000000000L
    return "%d" % i

def uint_argument(regno):
    i, nat = read_gr(regno)
    if nat:
        return "NaT"
    return "%d" % i

def hex_argument(regno):
    addr, nat = read_gr(regno)
    if nat:
        return "NaT"
    return "0x%x" % addr

def format_reg(regno, fmt):
    try:
        if fmt == 'd':
            return int_argument(regno)
        if fmt == 'u':
            return uint_argument(regno)
        if fmt == 'x':
            return hex_argument(regno)
        if fmt == 's':
            return string_argument(regno)
        return fmt(regno)
    except sim_core.SimExc_Index:
        return "<can't read r%d>" % regno
    except TypeError:
        traceback.print_exc()
        raise "Unknown format element: %s" % fmt

def format_params(params):
    s = ""
    for i in range(0, len(params)):
        if i != 0:
            s += ", "
        s += format_reg(32 + i, params[i])
    return s


# ---------------------------------------------------------------------------
#
#  handle break instruction
#
# ---------------------------------------------------------------------------

pre_syscall  = 0
post_syscall = 0

# To get around a misfeature in Simics' hap callback handling, we have to store
# references to all data that is sent as callback data in
# SIM_hap_add_callback_index.  We do this in this dictionary.
hap_data = { }

def post_syscall_hap(sc, obj, type, bp_id, dummy1, dummy2):
    name, params, retfmt, task = sc
    cpu = SIM_current_processor()
    # Same context?
    if task != current_task(cpu):
        return
    # print "post_syscall_hap(%s, %s, %s, %s, %s)" % (sc, type, bp_id, dummy1, dummy2)
    SIM_delete_breakpoint(bp_id)
    SIM_hap_delete_callback("Core_Breakpoint", post_syscall_hap, sc);
    del hap_data[bp_id]
    if not retfmt:
        ret = "??"
    else:
        ret = format_reg(8, retfmt)
    pid, comm = current_process(cpu)
    print "[%s] %d [%d:%s] %s(%s) -> %s" % (cpu.name, SIM_cycle_count(cpu),
                                            pid, comm,
                                            name, format_params(params), ret)


def syscall():
    global pids, pid_default, ia64_linux_loaded
    cpu = SIM_current_processor()
    pid, comm = current_process(cpu)
    if not pids.get(pid, pid_default):
        return
    try:
        r15 = read_register("r15")
        sc = linux_syscalls[r15]
    except:
        print "<--- syscall() failed --->"
    else:
        name = sc[0]
        if not sc[1]:
            params = []
            retfmt = None
        elif type(sc[1]) == type(""):
            [params, retfmt] = sc[1].split(":")
        else:
            params,retfmt = sc[1]
                        
        if pre_syscall:
            print "[%s] %d [%d:%s] %s(%s)" % (cpu.name, SIM_cycle_count(cpu),
                                              pid, comm,
                                              name, format_params(params))
        if not pre_syscall and post_syscall and retfmt == "v":
            # Give at least some indication
            print "[%s] %d [%d:%s] %s(%s) -> no return" % (cpu.name, SIM_cycle_count(cpu),
                                                           pid, comm,
                                                           name, format_params(params))

        if len(sc) > 2:
            for fn in sc[2]:
                fn(r15)

        if post_syscall and retfmt != "v":
            iip = read_cr("iip")
            isr_ei = (read_register("cr.isr") >> 41) & 0x3
            if isr_ei == 2:
                next_ip = iip + 16
            else:
                next_ip = iip + isr_ei + 1
            ia64_linux_loaded = 1
            context = SIM_get_object("primary-context")
            id = SIM_breakpoint(context, Sim_Break_Virtual, 4, next_ip, 1, 0);
            data = (name, params, retfmt, current_task(cpu))
            hap_data[id] = data
            hap_id = SIM_hap_add_callback_index("Core_Breakpoint", post_syscall_hap, data, id);

def install_syscall_callback(syscall, fn):
    if len(linux_syscalls[syscall]) > 2:
        linux_syscalls[syscall][2] += [fn]
    else:
        linux_syscalls[syscall] += [ [fn] ]

def break_instruction():
    iim = read_cr("iim")
    if iim == 0x100000 and (pre_syscall or post_syscall):
        syscall()
    elif iim == 0:
        print "break 0 @ %d" % SIM_cycle_count(SIM_current_processor())


pids = {}
pid_default = 1

def syscall_trace_cmd(mode, incl, excl):
    global pre_syscall, post_syscall, pids, pid_default
    if mode == "enter" or mode == "both":
        pre_syscall = 1
    else:
        pre_syscall = 0
    if mode == "exit" or mode == "both":
        post_syscall = 1
    else:
        post_syscall = 0
    pids = {}
    try:
        if incl:
            for k in incl.split(","): pids[int(k)] = 1
        if excl:
            for k in excl.split(","): pids[int(k)] = 0
    except:
        print "Bad pid list"
    if incl and excl:
        print "Redundant use of incl"
    if incl:
        pid_default = 0
    else:
        pid_default = 1
        

def syscall_mode_expander(comp):
    return get_completions(comp, ["off", "enter", "exit", "both"])

new_command("syscall-trace", syscall_trace_cmd,
            [arg(str_t, "mode", expander = syscall_mode_expander),
             arg(str_t, "include-pids", "?"),
             arg(str_t, "exclude-pids", "?")],
            type  = "linux commands",
            short = "enable or disable syscall tracing",
            doc = """
Set the syscall trace mode.
""")


# ---------------------------------------------------------------------------
#
#  examine the page table
#
# ---------------------------------------------------------------------------

def ptwalk(addr):
    cpu,_ = get_cpu()
    vrn = addr >> 61
    rr = cpu.rr[vrn]
    rr_ps = (rr>>2) & 0x3f
    pt_entries = 1L << (rr_ps - 3)
    pgd = cpu.ar[7]
    print "rr_ps: 0x%x" % rr_ps
    ptd_index = (addr >> rr_ps) & (pt_entries - 1)
    pmd_index = (addr >> (rr_ps + rr_ps-3)) & (pt_entries - 1)
    pgd_index = ((addr >> (rr_ps + rr_ps-3 + rr_ps-3)) & ((pt_entries>>3) - 1) |
                 (vrn << (rr_ps - 6)))
    
    print "pgd_index: 0x%x" % pgd_index
    print "pmd_index: 0x%x" % pmd_index
    print "ptd_index: 0x%x" % ptd_index
    print "pgd: 0x%x" % pgd
    pmd = SIM_read_phys_memory(cpu, pgd + 8*pgd_index, 8)
    print "pmd = pgd[0x%x}: 0x%x" % (pgd_index, pmd)
    ptd = SIM_read_phys_memory(cpu, pmd + 8*pmd_index, 8)
    print "ptd = pmd[0x%x}: 0x%x" % (pmd_index, ptd)
    pte = SIM_read_phys_memory(cpu, ptd + 8*ptd_index, 8)
    print "pte = ptd[0x%x]: 0x%x" % (ptd_index, pte)


# ---------------------------------------------------------------------------
#
#  handle illegal instruction
#
# ---------------------------------------------------------------------------

def exception_hap(data, cpu, exception):
    if exception == 33:
        print "Illegal instruction exception"
        SIM_break_simulation("Illegal instruction")
    elif exception == 35:
        break_instruction()
    return 0

# This is to allow us to reload ia64-linux.py
try:
    if ia64_linux_loaded:
        pass
except:
    print "installing linux callbacks"
    ia64_linux_loaded = 1
    SIM_hap_add_callback("Core_Exception", exception_hap, None)
