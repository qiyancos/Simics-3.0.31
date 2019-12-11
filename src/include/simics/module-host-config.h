/*
 * simics/module-host-config.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_MODULE_HOST_CONFIG_H
#define _SIMICS_MODULE_HOST_CONFIG_H

#ifndef _HOST_CONFIG_H_
#define _HOST_CONFIG_H_

#ifdef _WIN32

  #define DIR_SEP "\\"
  #define DIR_SEP_CHAR '\\'
  #define PATH_SEP ";"
  #define PATH_SEP_CHAR ';'

  #define HAVE_LIBZ 1

  #if defined(__INTEL_COMPILER)

    #define HAVE_FCNTL_H 1
    #define HAVE_SYS_STAT_H 1
    #define HAVE_VARARG_MACROS 1

  #elif defined(__MINGW32__)

    #define HAVE_STDINT_H 1
    #define HAVE_INTPTR_T 1
    #define HAVE_UINTPTR_T 1
    #define HAVE_FCNTL_H 1
    #define HAVE_SYS_STAT_H 1
    #define HAVE_VARARG_MACROS 1

  #else
  #warning fix module-host-config.h for this platform
  #endif

#elif defined(__sun)

  #define DIR_SEP "/"
  #define DIR_SEP_CHAR '/'
  #define PATH_SEP ":"
  #define PATH_SEP_CHAR ':'

  #define HAVE_AF_UNIX 1
  #define HAVE_ALLOCA_H
  #define HAVE_ARPA_INET_H 1
  #define HAVE_DIRENT_H 1
  #define HAVE_FCNTL_H 1
  #define HAVE_INTPTR_T
  #define HAVE_INTTYPES_H 1
  #define HAVE_LIBZ 1
  #define HAVE_NETDB_H 1
  #define HAVE_NETINET_IF_ETHER_H 1
  #define HAVE_NETINET_IN_H 1
  #define HAVE_NETINET_IN_SYSTM_H 1
  #define HAVE_NETINET_IP_H 1
  #define HAVE_NETINET_IP_ICMP_H 1
  #define HAVE_NETINET_TCP_H 1
  #define HAVE_NETINET_UDP_H 1
  #define HAVE_NET_IF_H 1
  #define HAVE_STRUCT_TIMESPEC 1
  #define HAVE_STROPTS_H 1
  #define HAVE_SYS_STROPTS_H 1
  #define HAVE_SYS_IPC_H 1
  #define HAVE_SYS_SHM_H 1
  #define HAVE_SYS_IOCTL_H 1
  #define HAVE_SYS_SOCKET_H 1
  #define HAVE_SYS_STATVFS_H 1
  #define HAVE_SYS_STAT_H 1
  #define HAVE_SYS_TIME_H 1
  #define HAVE_SYS_TYPES_H 1
  #define HAVE_SYS_UN_H 1
  #define HAVE_SYS_UIO_H 1
  #define HAVE_SYS_VFS_H 1
  #define HAVE_SYS_SOCKIO_H 1
  #define HAVE_TERMIOS_H 1
  #define HAVE_TERMIO_H 1
  #define HAVE_UINTPTR_T
  #define HAVE_UNISTD_H 1
  #define HAVE_USLEEP
  #define HAVE_UTIME_H 1
  #define HAVE_VARARG_MACROS 1

#elif defined(__linux__)

  #define DIR_SEP "/"
  #define DIR_SEP_CHAR '/'
  #define PATH_SEP ":"
  #define PATH_SEP_CHAR ':'

  #define HAVE_AF_UNIX 1
  #define HAVE_ALLOCA_H
  #define HAVE_ARPA_INET_H 1
  #define HAVE_DIRENT_H 1
  #define HAVE_FCNTL_H 1
  #define HAVE_INTPTR_T 1
  #define HAVE_LIBXPM 1
  #define HAVE_LIBZ 1
  #define HAVE_NETDB_H 1
  #define HAVE_NETINET_ETHER_H 1
  #define HAVE_NETINET_IF_ETHER_H 1
  #define HAVE_NETINET_IN_H 1
  #define HAVE_NETINET_IN_SYSTM_H 1
  #define HAVE_NETINET_IP_H 1
  #define HAVE_NETINET_IP_ICMP_H 1
  #define HAVE_NETINET_TCP_H 1
  #define HAVE_NETINET_UDP_H 1
  #define HAVE_NET_IF_H 1
  #define HAVE_STDINT_H 1
  #define HAVE_STRUCT_TIMESPEC 1
  #define HAVE_SYS_IOCTL_H 1
  #define HAVE_SYS_IPC_H 1
  #define HAVE_SYS_SHM_H 1
  #define HAVE_SYS_SOCKET_H 1
  #define HAVE_SYS_STAT_H 1
  #define HAVE_SYS_TIME_H 1
  #define HAVE_SYS_TYPES_H 1
  #define HAVE_SYS_UN_H 1
  #define HAVE_SYS_WAIT_H 1
  #define HAVE_SYS_VFS_H 1
  #define HAVE_SYS_STATVFS_H 1
  #define HAVE_TERMIOS_H 1
  #define HAVE_TERMIO_H 1
  #define HAVE_UINTPTR_T 1
  #define HAVE_UNISTD_H 1
  #define HAVE_USLEEP 1
  #define HAVE_UTIME_H 1
  #define HAVE_VARARG_MACROS 1

#else
#warning fix module-host-config.h for this platform
#endif

/* keep it simple; disable restrict in C++-code */
#define cplusplus_restrict
#if defined(CPU_MODULE)
#define c_restrict restrict
#endif
/* For compilers supporting restrict we could set c_restrict to restrict */

#endif  /* _HOST_CONFIG_H_ */

#endif /* _SIMICS_MODULE_HOST_CONFIG_H */
