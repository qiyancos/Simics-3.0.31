/*
 * simics/utils.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTILS_H
#define _SIMICS_UTILS_H

#include <simics/module-host-config.h>

#ifdef HAVE_UNISTD_H
#include <unistd.h>
#endif
#ifdef HAVE_SYS_SOCKET_H
#include <sys/socket.h>
#endif
#ifdef HAVE_NETINET_TCP_H
#include <netinet/tcp.h>
#endif
#ifdef HAVE_NET_IF_H
#include <net/if.h>
#endif
#ifdef HAVE_NETINET_IF_ETHER_H
#include <netinet/if_ether.h>
#endif

#ifdef _POSIX_THREADS
#include <pthread.h>
#endif

#include <simics/core/types.h>
#include <simics/util/genrand.h>
#include <simics/util/vect.h>
#include <simics/util/data-structs.h>
#include <simics/util/dbuffer.h>
#include <simics/util/bitcount.h>
#include <simics/util/alloc.h>
#include <simics/util/swabber.h>
#include <simics/util/fphex.h>
#include <simics/util/log.h>
#include <simics/util/strbuf.h>

/* os_time_t used to be long, but the arithmetic
 * doesn't work with 64-bit integers.
 */
typedef int os_time_t;
typedef struct os_tm {
	int tm_sec;                   /* Seconds.     [0-60] (1 leap second) */
	int tm_min;                   /* Minutes.     [0-59] */
	int tm_hour;                  /* Hours.       [0-23] */
	int tm_mday;                  /* Day.         [1-31] */
	int tm_mon;                   /* Month.       [0-11] */
	int tm_year;                  /* Year - 1900.  */
	int tm_wday;                  /* Day of week. [0-6] */
	int tm_yday;                  /* Days in year.[0-365] */
	int tm_isdst;                 /* DST.         [-1/0/1]*/
} os_tm_t;

struct os_tm *os_gmtime(const os_time_t *timep);

os_time_t os_timegm(struct os_tm *tmp);

char * os_strptime(const char *str, const char *format, struct os_tm *tm);

integer_t os_get_current_time_usec(void);

integer_t os_get_user_cpu_time_usec(void);


/*
 * Various help macros
 */
#ifndef TRUE
#define TRUE  (1)
#endif

#ifndef FALSE
#define FALSE (0)
#endif

#define SET_BITS(var,lb,s,v) ((var) = (((var) & ~(((UINT64_C(1) << (s))-1) << (lb))) | (((v) & ((UINT64_C(1) << (s))-1)) << (lb))))
#define GET_BITS(var,lb,s) (((var) >> (lb)) & ((UINT64_C(1) << (s))-1))

void not_implemented(int line, const char *file,
                     const char *msg, uint64 addr);

#define NOT_IMPLEMENTED(msg) do {                       \
        not_implemented(__LINE__, __FILE__, msg, 0);    \
} while (0)

#define NOT_IMPLEMENTED_ADDR(msg, addr) do {            \
        not_implemented(__LINE__, __FILE__, msg, addr); \
} while (0)

NORETURN void assert_error(int line, const char *file, const char *mod_date,
                           const char *message);

#ifdef __SUNPRO_C
#pragma does_not_return(assert_error)
#endif

#define ASSERT(exp) ASSERT_MSG(exp, NULL)

#ifdef SIMICS_CORE
#define ASSERT_MSG(exp, msg)                                    \
do {                                                            \
        if (unlikely(!(exp)))                                   \
                assert_error(__LINE__, __FILE__, NULL, msg);    \
} while (0)

#else  /* not SIMICS_CORE */
#ifdef __cplusplus
extern "C" { extern const char _module_date[]; }
#endif

#define ASSERT_MSG(exp, msg)                                            \
do {                                                                    \
        extern const char _module_date[];                               \
        if (unlikely(!(exp)))                                           \
                assert_error(__LINE__, __FILE__, _module_date, msg);    \
} while (0)
#endif /* not SIMICS_CORE */

#define _CASSERT_PASTE2(a, b) __cassert_ ## a ## _ ## b
#define _CASSERT_PASTE(a, b) _CASSERT_PASTE2(a, b)

/*
  <add-macro id="utility assertions">
  <short>compile-time assertion</short>
  This macro generates a compile-time assertion that <i>what</i> is true,
  or a compilation error will ensue.
  <i>name</i> is an identifier unique to the source file where the assertion
  is used.
  It may be used anywhere where typedefs are allowed.
  </add-macro>
  */
#define CASSERT(name, what) typedef int			\
	_CASSERT_PASTE(__LINE__, name)[(what) ? 1 : -1]

/*
  <add-macro id="utility assertions">
  <short>compile-time assertion</short>
  This macro generates a compile-time assertion by defining a typedef of an
  <tt>int</tt> array with negative length with the name 
  <tt>__cassert_stmt</tt> (in a code block of its own) unless 
  <tt><i>what</i></tt> is true.
  It may be used anywhere where statements are allowed.
  </add-macro>
  */
#define CASSERT_STMT(what) do { CASSERT(stmt, what); } while (0)

#undef MIN
#undef MAX
#define MIN(a, b)	((a) < (b) ? (a) : (b))
#define MAX(a, b)	((a) > (b) ? (a) : (b))

#define ALEN(a) ((int)(sizeof (a) / sizeof (a)[0]))

/* create a string from the definition of the CPP sympol n */ 
#define SYMBOL_TO_STRING2(n) #n
#define SYMBOL_TO_STRING(n) SYMBOL_TO_STRING2(n)

struct ucontext;

void VT_install_stack_trace(void (*st)(struct ucontext *));

typedef int (*simics_symbol_lookup_t)(uintptr_t addr,
                                      const char **file_ret,
                                      const char **var_ret,
                                      uintptr_t *offset_ret);

void VT_install_symbol_lookup(simics_symbol_lookup_t func);
void VT_install_symbol_handler(void (*sh)(void));
int VT_lookup_simics_symbol(uintptr_t addr,
                            const char **file_ret,
                            const char **var_ret,
                            uintptr_t *offset_ret);

void clean_path(char *path);

int is_absolute_path(const char *file);

NORETURN void problem(const char *str);
#if defined(__SUNPRO_C)
#pragma does_not_return(problem)
#endif

#define ntohll(a) CONVERT_BE64(a)
#define htonll ntohll

int unsigned_divide_128_by_64(uint64 dividend_high, uint64 dividend_low,
                              uint64 divisor,
                              uint64 *quotient, uint64 *remainder);
int signed_divide_128_by_64(int64 divident_high, int64 dividend_low,
                            int64 divisor, int64 *quotient, int64 *remainder);
void unsigned_multiply_64_by_64(uint64 a, uint64 b,
                                uint64 *prod_h, uint64 *prod_l);
void signed_multiply_64_by_64(uint64 a, uint64 b,
                              uint64 *prod_h, uint64 *prod_l);
uint64 unsigned_multiply_64_by_64_high(uint64 a, uint64 b);
uint64 signed_multiply_64_by_64_high(uint64 a, uint64 b);


/* Pthread-Win32's pthread.h also has a definition of timespec, so if
 * pthread.h has been included, don't redefine it here. Also make sure
 * that if pthread.h is included later, it won't redefine it. */
#if defined(_WIN32) && defined(_POSIX_THREADS) && !defined(HAVE_STRUCT_TIMESPEC)
#define HAVE_STRUCT_TIMESPEC
#endif

#ifndef HAVE_STRUCT_TIMESPEC
struct timespec {
	long tv_sec;
	long tv_nsec;
};
#define HAVE_STRUCT_TIMESPEC
#endif /* HAVE_STRUCT_TIMESPEC */

/* Dynamic linking */
#ifndef HINSTANCE
#define HINSTANCE void *
#endif
#ifndef FARPROC
#define FARPROC void *
#endif
#ifdef _WIN32
typedef HINSTANCE os_dlhandle_t;
typedef FARPROC os_dlsymbol_t;
#else
typedef void *os_dlhandle_t;
typedef void *os_dlsymbol_t;
#endif


os_dlhandle_t os_dlopen(const char *filename, int flags);
int os_dlclose(os_dlhandle_t handle);
os_dlsymbol_t os_dllookup(os_dlhandle_t handle, const char *symbol);

int os_get_last_error(void);
int os_last_error_was_error(void);
char *os_describe_last_error(void);
char *os_describe_last_dlerror(void);
char *os_describe_last_socket_error(void);

uint64 os_get_file_size(const char *filename);

#ifndef ETHER_ADDR_LEN
#define ETHER_ADDR_LEN 6
#endif

#ifdef _WIN32
struct ether_addr {
        unsigned char ether_addr_octet[ETHER_ADDR_LEN];
};
#endif

struct ether_addr *os_ether_aton(const char *a);
char *os_ether_ntoa(struct ether_addr *n);

#ifndef HAVE_FFS
int ffs(int i);
#endif

/* Using os_[f]open instead of [f]open ensures that shortcuts are
   properly followed under Windows. */
FILE *os_fopen(const char *path, const char *mode);
int os_fclose(FILE *stream);

const char *os_basename(const char *path);
void os_path_join(strbuf_t *path, const char *name);

/* When using VC++, include fcntl.h to get definition of O_BINARY. */
#ifndef _MSC_VER
#ifndef O_BINARY
#define O_BINARY 0
#endif /* O_BINARY */
#endif /* _MSC_VER */

int os_open(const char *path, int flags, ...);
int os_open_vararg(const char *path, int flags, va_list ap);
int64 os_lseek(int fd, int64 off, int whence);

typedef enum {
	Os_No_Error,
	Os_Connection_Refused,
        Os_Connection_Reset,
	Os_Timed_Out,
	Os_Net_Unreach,
	Os_Host_Unreach,
	Os_In_Progress,
	Os_Other
} os_socket_status_t;

void os_initialize_sockets(void);

#ifdef _WIN32
#define OS_INVALID_SOCKET INVALID_SOCKET
#else
#define OS_INVALID_SOCKET -1
#endif


#define os_socket_isvalid(sock) ((sock) != OS_INVALID_SOCKET)

int os_socket_close(int sock);
int os_socket_write(socket_t central_fd, const void *buf, int len);
int os_socket_write_non_blocking(socket_t central_fd, const void *buf, int len);
int os_socket_read(socket_t central_fd, void *buf, int len);
struct hostent *os_gethostbyname(const char *host);
int os_set_socket_non_blocking(socket_t s);
int os_set_socket_reuseaddr(socket_t s);
int os_set_socket_nodelay(socket_t s);
os_socket_status_t os_socket_connect(socket_t s, const struct sockaddr *serv_addr, size_t addr_len);
os_socket_status_t os_socket_get_status(socket_t s);

typedef const char * (*remote_name_func_t)(void);

#ifdef _WIN32
void os_timespec_to_filetime(const struct timespec *ts, FILETIME *ft);
void os_filetime_to_timespec(const FILETIME *ft, struct timespec *ts);
#endif

#define ILLEGAL_IP_ADDRESS 0xFFFFFFFF
uint32 os_inet_network(const char *cp);
const char * os_inet_ntoa(uint32 ip);

int os_copy(const char *src, const char *dst);
int os_rename(const char *src, const char *dst);
char *os_dirname(const char *filename);
char *os_quote_filename(const char *file);

#ifdef _POSIX_THREADS
typedef void * (*pthread_func_t)(void *);
int os_pthread_create(pthread_t *tid, pthread_func_t func, void *arg);
int os_pthread_cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex, nano_secs_t timeout);
#endif /* _POSIX_THREADS */

void os_millisleep(int t);

#if defined(HAVE_ALLOCA_H)
#include <alloca.h>
#endif

#if !defined(HAVE_STRTOK_R) && !defined(strtok_r)
char *strtok_r(char *p, const char *s, char **l);
#endif   /* !HAVE_STRTOK_R */

#if !defined(HAVE_STRLCPY)
size_t strlcpy(char *dst, const char *src, size_t dstsize);
#endif   /* !HAVE_STRLCPY */

#ifdef __MINGW32__
#include <malloc.h>   /* will define alloca as a gcc builtin */
#define os_alloca(sz) alloca(sz)
#define os_freea(p)
#else
#ifdef _WIN32
#define os_alloca(sz) _alloca(sz)
#define os_freea(p)   ((void)0)
#else
#define os_alloca(sz) alloca(sz)
#define os_freea(p)   ((void)0)
#endif /* _WIN32 */
#endif /* __MINGW32__ */

#endif /* _SIMICS_UTILS_H */
