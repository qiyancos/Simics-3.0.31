
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

# ============================================================================
# ============================================================================
#
#     CONFIGURATION
#
# ============================================================================
# ============================================================================



kernel_virtual_base  = 0x00000000000L
kernel_virtual_top   = 0x00000010000L
kernel_physical_base = 0x00000000000L

user_virtual_base   = 0x00000010000L
user_virtual_top    = 0x10000000000L

user_context = 1

user_stack = 0xF800000L


const_page_size = 0x2000L
const_page_mask = const_page_size - 1L

# ============================================================================
# ============================================================================
#
#     GLOBALS, CONSTANTS, ETC.
#
# ============================================================================
# ============================================================================

# symbolic names for solaris signals
signal_names = [
    
    "SIGHUP",
    "SIGINT",
    "SIGQUIT",
    "SIGILL",
    "SIGTRAP",
    "SIGIOT",
    "SIGEMT",
    "SIGFPE",
    "SIGKILL",
    "SIGBUS",
    "SIGSEGV",
    "SIGSYS",
    "SIGPIPE",
    "SIGALRM",
    "SIGTERM",
    "SIGUSR1",
    "SIGUSR2",
    "SIGCLD",
    "SIGPWR",
    "SIGWINCH",
    "SIGURG",
    "SIGPOLL",
    "SIGSTOP",
    "SIGTSTP",
    "SIGCONT",
    "SIGTTIN",
    "SIGTTOU",
    "SIGVTALRM",
    "SIGPROF",
    "SIGXCPU",
    "SIGXFSZ",
    "SIGWAITING",
    "SIGLWP",
    "SIGFREEZE",
    "SIGTHAW",
    "SIGCANCEL",
    "SIGLOST"

    ]

# symbolic constants for lseek
lseek_constants = [

    "SEEK_SET",
    "SEEK_CUR",
    "SEEK_END"

    ]

# list of saved register windows (used by spill/fill traps)
window_stack = []

# next entry to be used in the instruction TLB
itlb_index = 0

# next entry to be used in the data TLB
dtlb_index = 0

# retry/done instruction words
retry_instruction = 0x83f00000
done_instruction = 0x81f00000


# ============================================================================
# ============================================================================
#
#     MEMORY ACCESS
#
# ============================================================================
# ============================================================================

# read a list of bytes
def read_bytes(address, size):
    return SIM_current_processor().physical_memory.memory[[address, address + size - 1]]

# write a list of bytes
def write_bytes(address, bytes):
    SIM_current_processor().physical_memory.memory[[address, address + len(bytes) - 1]] = bytes

def read_byte(address):
    return read_bytes(address, 1)[0]

def write_byte(address, byte):
    write_bytes(address, [byte])

# read 32 bit word
def read_word(address):
    word = read_bytes(address, 4)
    return ((word[0] & 0xFF) << 24) | ((word[1] & 0xFF) << 16) | ((word[2] & 0xFF) << 8) | (word[3] & 0xFF)

# write 32 bit word
def write_word(address, word):
    word = [ (word >> 24 & 0xFF), (word >> 16 & 0xFF), (word >> 8 & 0xFF), (word & 0xFF) ]
    write_bytes(address, word)

# read data as string
def read_data(address, size):
    string = ""
    for i in range(size):
        string += chr(read_byte(address + i))
    return string

# write data (given as string)
def write_data(address, data):
    if len(data):
        write_bytes(address, map(lambda x: ord(x), data))

# read null-terminated data as string
def read_string(address):
    c = read_byte(address)
    if c != 0:     
        return chr(c) + read_string(address + 1)
    else:
        return ""

# write a "struct stat" (used by stat, fstat, lstat etc.) to memory
def write_struct_stat(address, stat):
    # The  value is a tuple of at least 10 integers giving
    # the most important (and portable) members of the stat
    # structure, in the order st_mode, st_ino, st_dev, st_nlink,
    # st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime.    
    write_word(address,      stat[2]) # st_dev
    write_word(address + 16, stat[1]) # st_ino
    write_word(address + 20, stat[0]) # st_mode
    write_word(address + 24, stat[3]) # st_nlink
    write_word(address + 28, stat[4]) # st_uid
    write_word(address + 32, stat[5]) # st_gid
    write_word(address + 36, 0)       # st_rdev
    write_word(address + 40, stat[6]) # st_size
    write_word(address + 44, stat[7]) # st_atime
    write_word(address + 48, stat[8]) # st_mtime
    write_word(address + 52, stat[9]) # st_ctime


# write a "struct stat64" (used by stat, fstat, lstat etc.) to memory
def write_struct_stat64(address, stat):
    # The  value is a tuple of at least 10 integers giving
    # the most important (and portable) members of the stat
    # structure, in the order st_mode, st_ino, st_dev, st_nlink,
    # st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime.    

    write_word(address +  0, stat[2]) # st_dev
    write_word(address + 16, stat[1]) # st_ino
    write_word(address + 24, stat[0]) # st_mode
    write_word(address + 28, stat[3]) # st_nlink
    write_word(address + 32, stat[4]) # st_uid
    write_word(address + 36, stat[5]) # st_gid
    write_word(address + 40, 0)       # st_rdev
    write_word(address + 56, stat[6]) # st_size
    write_word(address + 64, stat[7]) # st_atime
    write_word(address + 72, stat[8]) # st_mtime
    write_word(address + 80, stat[9]) # st_ctime

# ============================================================================
# ============================================================================
#
#     REGISTER ACCESS
#
# ============================================================================
# ============================================================================

def read_global(r):
    return SIM_read_register(SIM_current_processor(), SIM_get_register_number(SIM_current_processor(), "g%d" % r))

def write_global(r, v):
    SIM_write_register(SIM_current_processor(), SIM_get_register_number(SIM_current_processor(), "g%d" % r), v)

def read_output(r):
    return SIM_read_register(SIM_current_processor(), SIM_get_register_number(SIM_current_processor(), "o%d" % r))

def write_output(r, v):
    SIM_write_register(SIM_current_processor(), SIM_get_register_number(SIM_current_processor(), "o%d" % r), v)

def read_ctrl_reg(r):
    return SIM_read_register(SIM_current_processor(), SIM_get_register_number(SIM_current_processor(), r))

def write_ctrl_reg(r, v):
    SIM_write_register(SIM_current_processor(), SIM_get_register_number(SIM_current_processor(), r), v)

def read_win_reg(win, reg):
    return SIM_read_window_register(SIM_current_processor(), win, reg)

def write_win_reg(win, reg, val):
    SIM_write_window_register(SIM_current_processor(), win, reg, val)

def read_sp():
    return read_output(6)

def write_sp(value):
    write_output(6, value)


# ============================================================================
# ============================================================================
#
#     STACK OPERATIONS
#
# ============================================================================
# ============================================================================

# push a word to the stack
def push_word(word):
    sp = read_sp() - 4
    write_word(sp, word)
    write_sp(sp)

# push string to stack - return new sp
def push_string(string):
    sp = read_sp() - len(string) - 1
    write_bytes(sp, map(lambda x: ord(x), string) + [0])
    write_sp(sp)

# push a list of strings to stack - return list of pointers
def push_string_list(string_list):
    p = []
    for x in string_list:
        push_string(x)
        p.append(read_sp())
    return p


# ============================================================================
# ============================================================================
#
#     UTILITIES
#
# ============================================================================
# ============================================================================

def debug_log(level, message):
    if level < 1:
        print message

def convert_oflag(oflag):
    if (oflag & 3) == 0:
        flag_str = "O_RDONLY"
        flags = os.O_RDONLY
    elif (oflag & 3) == 1:
        flag_str = "O_WRONLY"
        flags = os.O_WRONLY
    elif (oflag & 3) == 2:
        flag_str = "O_RDWR"
        flags = os.O_RDWR
    if oflag & 0x100:
        flag_str += "|O_CREAT"
        flags |= os.O_CREAT
    if oflag & 0x200:
        flag_str += "|O_TRUNC"
        flags |= os.O_TRUNC
    if oflag & 0x400:
        flag_str += "|O_EXCL"
        flags |= os.O_EXCL
    return [flags, flag_str]

def syscall_failed():
    # set carry
    ccr = read_ctrl_reg("ccr")
    ccr |= 0x11
    write_ctrl_reg("ccr", ccr)

def syscall_succeeded():
    # clear carry
    ccr = read_ctrl_reg("ccr")
    ccr &= 0xEE
    write_ctrl_reg("ccr", ccr)


# ============================================================================
# ============================================================================
#
#     SYSTEM CALLS
#
# ============================================================================
# ============================================================================

# ----------------------------------------------------------------------------
#
#     exit, _exit - terminate process
#
#     void exit(int status);
#

def sys_exit():
    status = read_output(0)
    debug_log(1, "exit(%d)" % status)
    raise SimExc_Break

# ----------------------------------------------------------------------------
#
#     read, readv, pread - read from file
#
#     ssize_t read(int fildes, void *buf, size_t nbyte);
#

def sys_read():
    fildes = read_output(0)
    buf = read_output(1)
    nbyte = read_output(2)
    try:
        str = os.read(fildes, nbyte)
    except:
        n = 0
        syscall_failed()
    else:
        n = len(str)
        write_data(buf, str)
        syscall_succeeded()
    write_output(0, n)
    debug_log(1, "read(%d, 0x%x, %d) = %d" % (fildes, buf, nbyte, n))

# ----------------------------------------------------------------------------
#
#     write, pwrite, writev - write on a file
#
#     ssize_t write(int fildes, const void *buf, size_t nbyte);
#

def sys_write():
    fildes = read_output(0)
    buf = read_output(1)
    nbyte = read_output(2)
    if fildes == 2:
        for i in range(nbyte):
            sys.stdout.write(chr(read_byte(buf + i)))
        n = nbyte
        sys.stdout.flush()
    else:
        data = read_data(buf, nbyte)
        try:
            n = os.write(fildes, data)
        except:
            n = 0
            syscall_failed()
        else:
            syscall_succeeded()
    write_output(0, n)
    debug_log(1, "write(%d, 0x%x, %d) = %d" % (fildes, buf, nbyte, n))

# ----------------------------------------------------------------------------
#
#     open - open a file
#
#     int open(const char *path, int oflag, /* mode_t mode */...);
#

def sys_open():
    path = read_string(read_output(0))
    oflag = read_output(1)
    mode = read_output(2)
    [oflag, oflag_str] = convert_oflag(oflag)
    if oflag & os.O_CREAT:
        fildes = os.open(path, oflag, mode)
        debug_log(1, "open(\"%s\", %s, 0%o) = %d" % (path, oflag_str, mode, fildes))
    else:
        fildes = os.open(path, oflag)
        debug_log(1, "open(\"%s\", %s) = %d" % (path, oflag_str, fildes))
    write_output(0, fildes)

# ----------------------------------------------------------------------------
#
#     open64 - open a file
#
#     int open64(const char *path, int oflag, /* mode_t mode */...);
#

def sys_open64():
    return sys_open()

# ----------------------------------------------------------------------------
#
#     close - close a file descriptor
#
#     int close(int fildes);
#

def sys_close():
    fildes = read_output(0)
    try:
        os.close(fildes)
    except:
        ret = -1
        syscall_failed()
    else:
        ret = 0
    write_output(0, ret)
    debug_log(1, "close(%d) = %d" % (fildes, ret))    

# ----------------------------------------------------------------------------
#
#     unlink - remove directory entry
#
#     int unlink(const char *path);
#

def sys_unlink():
    path = read_string(read_output(0))
    try:
        os.unlink(path)
    except:
        ret = -1
        syscall_failed()
    else:
        ret = 0
    write_output(0, ret)
    debug_log(1, "unlink(\"%s\") = %d" % (path, ret))


# ----------------------------------------------------------------------------
#
#     chmod, fchmod - change access permission mode of file
#
#     int chmod(const char *path, mode_t mode);
#

def sys_chmod():
    path = read_string(read_output(0))
    mode = read_output(1)
    try:
        os.chmod(path, mode)
    except:
        ret = -1
        syscall_failed()
    else:
        ret = 0
    write_output(0, ret)
    debug_log(1, "chmod(\"%s\", O%o) = %d" % (path, mode, ret))

# ----------------------------------------------------------------------------
#
#     chown, lchown, fchown - change owner and group of a file
#
#     int chown(const char *path, uid_t owner, gid_t group);
#

def sys_chown():
    path = read_string(read_output(0))
    owner = read_output(1)
    group = read_output(2)    
    try:
        os.chown(path, owner, group)
    except:
        ret = -1
        syscall_failed()
    else:
        ret = 0
    write_output(0, ret)
    debug_log(1, "chown(\"%s\", %d, %d) = %d" % (path, owner, group, ret))

# ----------------------------------------------------------------------------
#
#     brk, sbrk - change the amount of  space  allocated  for  the
#     calling process's data segment
#
#     void *sbrk(intptr_t incr);
#

def sys_brk():
    incr = read_output(0)
    # treat as "nop"
    debug_log(1, "brk(0x%x)" % incr)

# ----------------------------------------------------------------------------
#
#     stat, lstat, fstat - get file status
#
#     int stat(const char *path, struct stat *buf);
#

def sys_stat():
    path = read_string(read_output(0))
    buf = read_output(1)
    try: 
        stat = os.stat(path)
    except:
        ret = 2
        syscall_failed()
    else:
        ret = 0
        write_struct_stat(buf, stat)
        syscall_succeeded()
    write_output(0, ret)
    debug_log(1, "stat(\"%s\", 0x%x) = %d" % (path, buf, ret))

def sys_stat64():
    path = read_string(read_output(0))
    buf = read_output(1)
    try: 
        stat = os.stat(path)
    except:
        ret = 2
        syscall_failed()
    else:
        ret = 0
        write_struct_stat64(buf, stat)
        syscall_succeeded()
    write_output(0, ret)
    debug_log(1, "stat64(\"%s\", 0x%x) = %d" % (path, buf, ret))

def sys_fstat64():
    fildes = read_output(0)
    buf = read_output(1)
    try:        
        stat = os.fstat(fildes)
    except:
        ret = 2
        syscall_failed()
    else:
        ret = 0
        write_struct_stat64(buf, stat)
        syscall_succeeded()
    write_output(0, ret)
    debug_log(1, "fstat64(%d, 0x%x) = %d" % (fildes, buf, ret))

# ----------------------------------------------------------------------------
#
#     getuid - get user identity
#
#     uid_t getuid(void);
#

def sys_getuid():
    debug_log(1, "getuid(\"\") = 0")
    write_output(0, 0)

# ----------------------------------------------------------------------------
#
#     getpid - get process identification
#
#     pid_t getuid(void);
#

def sys_getpid():
    debug_log(1, "getpid(\"\") = 0")
    write_output(0, 0)

# ----------------------------------------------------------------------------
#
#     utime - set file access and modification times
#
#     int utime(const char *path, const struct utimbuf *times);
#

def sys_utime():
    path = read_string(read_output(0))
    times = read_output(1)
    actime = read_word(times)
    modtime = read_word(times + 4)
    try:
        os.utime(path, [actime, modtime])
    except:
        ret = -1
        syscall_failed()
    else:
        ret = 0
        syscall_succeeded()
    write_output(0, ret)
    debug_log(1, "utime(\"%s\", 0x%x) = %d" % (path, times, ret))

# ----------------------------------------------------------------------------
#
#     pgrpsys - set/get process group
#
#     pid_t getpgrp(void);
#     int setpgrp(void);
#     pid_t getsid(pid_t pid);
#     pid_t setsid(void);
#     pid_t getpgid(pid_t pid);
#     int setpgid(pid_t pid, pid_t pgid);
#

def sys_pgrpsys():
    id = read_output(0)
    if id == 0:
        debug_log(1, "getpgrp() = 0")
    elif id == 1:
        debug_log(1, "setpgrp() = 0")
    elif id == 2:
        pid = read_output(1)
        debug_log(1, "getsid(%d) = 0" % pid)
    elif id == 3:
        debug_log(1, "setsid() = 0")
    elif id == 4:
        pid = read_output(1)
        debug_log(1, "getpgid(%d) = 0" % pid)
    elif id == 5:
        pid = read_output(1)
        pgid = read_output(2)
        debug_log(1, "getpgid(%d, %d) = 0" % (pid, pgid))
    else:
        debug_log(1, "Unknown id in sys_pgrpsys, returning 0")
    write_output(0, 0)


# ----------------------------------------------------------------------------
#
#     getgid - 
#

def sys_getgid():
    debug_log(1, "getgid() = 0")
    write_output(0, 0)

# ----------------------------------------------------------------------------
#
#     stat, lstat, fstat - get file status
#
#     int fstat(int fildes, struct stat *buf);
#

def sys_fstat():
    fildes = read_output(0)
    buf = read_output(1)
    try:        
        stat = os.fstat(fildes)
    except:
        ret = 2
        syscall_failed()
    else:
        ret = 0
        write_struct_stat(buf, stat)
        syscall_succeeded()
    write_output(0, ret)
    debug_log(1, "fstat(%d, 0x%x) = %d" % (fildes, buf, ret))

# ----------------------------------------------------------------------------
#
#     ioctl - control device
#
#     int ioctl(int fildes, int request, /* arg */ ...);
#

def sys_ioctl():
    fildes = read_output(0)
    request = read_output(1)
    write_output(0, 0)
    syscall_succeeded()
    debug_log(1, "ioctl(%d, 0x%x, ...) = 0" % (fildes, request))


def sys_fcntl():
    fildes = read_output(0)
    request = read_output(1)
    syscall_succeeded()
    debug_log(1, "fcntl(%d, 0x%x, ...) = 0" % (fildes, request))

# ----------------------------------------------------------------------------
#
#     stat, lstat, fstat - get file status
#
#     int lstat(const char *path, struct stat *buf);
#

def sys_lstat():
    path = read_string(read_output(0))
    buf = read_output(1)
    try:            
        stat = os.lstat(path)
    except:
        ret = 2
        syscall_failed()
    else:
        ret = 0
        write_struct_stat(buf, stat)
        syscall_succeeded()
    write_output(0, ret)
    debug_log(1, "lstat(\"%s\", 0x%x) = %d" % (path, buf, ret))

# ----------------------------------------------------------------------------
#
#     sigaltstack - 
#
#     int ...
#

def sys_sigaltstack():
    debug_log(1, "sigaltstack() - not implemented")
    write_output(0, 0)

# ----------------------------------------------------------------------------
#
#     sigaction - detailed signal management
#
#     int sigaction(int sig, const struct sigaction  *act,  struct
#     sigaction *oact);
#

def sys_sigaction():
    sig = read_output(0)
    act = read_output(1)
    oact = read_output(2)
    debug_log(1, "sigaction(%s, 0x%x, 0x%x)" % (signal_names[sig - 1], act, oact))
    syscall_succeeded()

# ----------------------------------------------------------------------------
#
#     sysconfig - 
#
#     ?
#

sysconf = {23 : "_CONFIG_SIGRT_MIN",
           24 : "_CONFIG_SIGRT_MAX"}

def sys_sysconfig():
    id = read_output(0)
    try:
        desc = sysconf[id]
    except:
        desc = "--unknown--"
    debug_log(1, "sysconfig(%s)" % desc)
    if id == 23:
        # first rt signal number
        write_output(0, 32)
    if id == 24:
        # last rt signal number
        write_output(0, 32)

# ----------------------------------------------------------------------------
#
#     pathconf

def sys_pathconf():
    path = read_string(read_output(0))
    name = read_output(1)
    debug_log(1, "pathconf(%s, %d)" % (path, name))
    if name == 5:
        ret = 128
    else:
        debug_log(1, "Unknown pathconf param: %d" % id)
        ret = 0
    syscall_succeeded()
    write_output(0, ret)
        
# ----------------------------------------------------------------------------
#
#     llseek - move extended read/write file pointer
#
#     offset_t llseek(int fildes, offset_t offset, int whence);
#

def sys_llseek():
    fildes = read_output(0)
    offset = read_output(1)
    whence = read_output(2)
    debug_log(1, "llseek(%d, %d, %s)" % (fildes, offset, lseek_constants[whence]))


# ============================================================================
# ============================================================================
#
#     SYSTEM CALL DISPATCH
#
# ============================================================================
# ============================================================================

syscalls = {
    
    1   : sys_exit,
    3   : sys_read,
    4   : sys_write,
    5   : sys_open,
    6   : sys_close,
    10  : sys_unlink,
    15  : sys_chmod,
    16  : sys_chown,
    17  : sys_brk,
    18  : sys_stat,
    20  : sys_getpid,
    24  : sys_getuid,
    28  : sys_fstat,
    30  : sys_utime,
    39  : sys_pgrpsys,
    47  : sys_getgid,
    54  : sys_ioctl,
    62  : sys_fcntl,
    88  : sys_lstat,
    97  : sys_sigaltstack,
    98  : sys_sigaction,
    113 : sys_pathconf,
    137 : sys_sysconfig,
    175 : sys_llseek,
    215 : sys_stat64,
    217 : sys_fstat64,
    225 : sys_open64
    
    }

def system_call():
    sys_call_num = SIM_read_register(SIM_current_processor(),
                                     SIM_get_register_number(SIM_current_processor(), "g1"))
    try:
        sys_call_func = syscalls[sys_call_num];
    except:
        print "system_call: unimplemented syscall %d" % sys_call_num
        raise SimExc_Break 
    else :
        # assume success, syscall handler will override
        syscall_succeeded()
        sys_call_func()


# ============================================================================
# ============================================================================
#
#     SPILL/FILL TRAP HANDLERS
#
# ============================================================================
# ============================================================================

def spill_trap():
    cansave = read_ctrl_reg("cansave")
    if cansave != 0:
        print "spill_trap with cansave != 0"
        raise SimExc_Break
    write_ctrl_reg("cansave", 1)
    canrestore = read_ctrl_reg("canrestore")
    canrestore -= 1
    write_ctrl_reg("canrestore", canrestore)
    cwp = read_ctrl_reg("cwp")
    cwp = (cwp + 2) % 8
    window = []
    for i in range(16, 32):
        window.append(read_win_reg(cwp, i))
    window_stack.append(window)

def fill_trap():
    cansave = read_ctrl_reg("cansave")
    if cansave == 0:
        print "fill_trap with cansave == 0"
        raise SimExc_Break
    cansave -= 1
    write_ctrl_reg("cansave", cansave)
    canrestore = read_ctrl_reg("canrestore")
    if canrestore != 0:
        print "fill_trap with canrestore != 0"
        raise SimExc_Break
    canrestore += 1
    write_ctrl_reg("canrestore", canrestore)
    cwp = read_ctrl_reg("cwp")
    cwp = (cwp - 1 + 8) % 8
    for i in range(16):
        write_win_reg(cwp, 16 + i, window_stack[-1][i])
    del window_stack[-1]


# ============================================================================
# ============================================================================
#
#     TRAP/EXCEPTION HAP CALLBACKS
#
# ============================================================================
# ============================================================================

def software_trap_hap(x, cpu, trap):
    debug_log(3, "software_trap_hap: 0x%x" % trap)
    # Syscall is trap 8 only, but interpret all as syscalls for now...
    system_call()
    return 0

def exception_hap(x, cpu, exception):
    if exception >= 0x100:
        return software_trap_hap(x, cpu, exception - 0x100)
    debug_log(3, "exception_hap: 0x%x" % exception)
    if exception == 0x64:
        handle_itlb_miss()
    elif exception == 0x68:
        handle_dtlb_miss()
    elif exception == 0x80:
        spill_trap()
    elif exception == 0xC0:
        fill_trap()
    else:
        debug_log(0, "exception_hap: unimplemented exception 0x%x" % exception)
        raise SimExc_Break
    return 0


# ============================================================================
# ============================================================================
#
#     INITIALIZATION
#
# ============================================================================
# ============================================================================

# ----------------------------------------------------------------------------
#
#     initialize cpu
#

def init_cpu():
    write_ctrl_reg("pstate", 0x18)
    # enable mmu
    SIM_current_processor().mmu.lsu_ctrl=0x0c
    # install trab table
    write_ctrl_reg("tba", kernel_virtual_base)
    # enable fpu
    write_ctrl_reg("fprs", 4)
    # trap level 0
    write_ctrl_reg("tl", 0)
    # set context
    SIM_current_processor().mmu.ctxt_primary = user_context
    # add 3 entries for kernel mapping in the itlb
    add_itlb_entry(17, tlb_tag(kernel_virtual_base, 0),          tlb_data(kernel_physical_base, 1, 0))
    add_itlb_entry(18, tlb_tag(kernel_virtual_base + 0x2000, 0), tlb_data(kernel_physical_base, 1, 0))
    add_itlb_entry(19, tlb_tag(kernel_virtual_base + 0x4000, 0), tlb_data(kernel_physical_base, 1, 0))

# ----------------------------------------------------------------------------
#
#     initialize trap table
#

def init_trap_table():
    write_word(kernel_virtual_base + 0x08 * 32, done_instruction)
    write_word(kernel_virtual_base + 0x64 * 32, retry_instruction)
    write_word(kernel_virtual_base + 0x68 * 32, retry_instruction)
    write_word(kernel_virtual_base + 0x80 * 32, retry_instruction)
    write_word(kernel_virtual_base + 0xC0 * 32, retry_instruction)

# ----------------------------------------------------------------------------
#
#     initialize hap callbacks
#

def init_hap_callbacks():
    SIM_hap_add_callback("Core_Exception", exception_hap, None)


def init_sparc_mini_os():
    init_cpu()
    init_trap_table()
    init_hap_callbacks()


# ============================================================================
# ============================================================================
#
#     TLB ACCESS
#
# ============================================================================
# ============================================================================

def add_itlb_entry(index, tag, data):
    x = SIM_current_processor().mmu.itlb_daccess
    x[index] = data
    SIM_current_processor().mmu.itlb_daccess = x
    x = SIM_current_processor().mmu.itlb_tagread
    x[index] = tag
    SIM_current_processor().mmu.itlb_tagread = x
    
def add_dtlb_entry(index, tag, data):
    x = SIM_current_processor().mmu.dtlb_daccess
    x[index] = data
    SIM_current_processor().mmu.dtlb_daccess = x
    x = SIM_current_processor().mmu.dtlb_tagread
    x[index] = tag
    SIM_current_processor().mmu.dtlb_tagread = x

# build translation table entry data word
def tlb_data(pa, p, w):
    assert(pa >= 0 and pa < 0x10000000)
    return (1L << 63) | (pa & 0x000000FFFFFFE000L) | (1 << 5) | (1 << 4) | (p << 2) | (w << 1)

# build translation table entry tag word
def tlb_tag(va, context):
    assert(context >= 0 and context < (1L << 13))
    return (va & 0xFFFFFFFFFFFFE000L) | (context & 0x1FFFL)

def handle_itlb_miss():
    global itlb_index
    tag = SIM_current_processor().mmu.itag_access
    debug_log(3, "handle_itb_miss: user tag = 0x%x" % tag)
    if tag < user_virtual_base or tag > user_virtual_top:
        debug_log(0, "handle_itlb_miss: got address outside of specified user space")
        raise SimExc_Break
    add_itlb_entry(itlb_index, tlb_tag(tag, user_context), tlb_data(tag, 0, 1))
    itlb_index = (itlb_index + 1) % 16

def handle_dtlb_miss():
    global dtlb_index
    tag = SIM_current_processor().mmu.dtag_access
    debug_log(3, "handle_dtb_miss: tag = 0x%x" % tag)
    if tag < user_virtual_base or tag > user_virtual_top:
        debug_log(0, "handle_dtlb_miss: got address outside of specified user space")
        raise SimExc_Break
    add_dtlb_entry(dtlb_index, tlb_tag(tag, user_context), tlb_data(tag, 0, 1))
    dtlb_index = (dtlb_index + 1) % 16

    
# ============================================================================
# ============================================================================
#
#     RUN USER APPLICATION
#
# ============================================================================
# ============================================================================

# ----------------------------------------------------------------------------
#
#     initialize stack
#

def init_stack(stack_pointer, env_str_list, arg_str_list):
    write_sp(stack_pointer)
    # push environment strings
    env_str_list.reverse()
    env_ptr_list = push_string_list(env_str_list)
    # push argument strings
    arg_str_list.reverse()
    arg_ptr_list = push_string_list(arg_str_list)
    # estimate stack size
    stack_pointer = read_sp()
    stack_pointer_estimate = stack_pointer - 4 * (2 + 1 + len(env_ptr_list) + 1 + len(arg_ptr_list) + 1 + 16)
    # will we need padding?
    stack_pointer -= stack_pointer_estimate & 7
    write_sp(stack_pointer)
    # push auxiliary vector
    push_word(0)
    push_word(0)
    # push 0 word
    push_word(0)
    # push environment
    for x in env_ptr_list:
        push_word(x)
    # push 0 word
    push_word(0)
    # push arguments
    for x in arg_ptr_list:
        push_word(x)
    # push arg count
    push_word(len(arg_ptr_list))
    # allocate window save area
    stack_pointer = read_sp()
    stack_pointer -= 64
    # make sure this stack is aligned
    if stack_pointer & 7:
        raise SimExc_Break, "missaligned stack"
    # update sp
    write_sp(stack_pointer)
    # make 
    debug_log(3, "environment strings:")
    for x in map(lambda p, s: "    0x%016x: %s" % (p, s), env_ptr_list, env_str_list):
        debug_log(3,x)
    debug_log(3, "arguments:")
    for x in map(lambda p, s: "    0x%016x: %s" % (p, s), arg_ptr_list, arg_str_list):
        debug_log(3,x)
    debug_log(3, "%%sp at 0x%x" % stack_pointer)

# ----------------------------------------------------------------------------
#
#    load and initialize a user level program
#

def run_program(environment, arguments, filename):
    pc = SIM_load_binary(SIM_current_processor().physical_memory, filename, 0, 0, 0)
    SIM_set_program_counter(SIM_current_processor(), pc)
    init_stack(user_stack, environment, arguments)
