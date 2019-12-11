/*
 * simics/global.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_GLOBAL_H
#define _SIMICS_GLOBAL_H

/* These are required for Solaris to include the Unix 95 definitions */
#if defined(__sun)
  #if !defined(_XOPEN_SOURCE)
    #define _XOPEN_SOURCE 500
  #endif
  #if !defined(_XOPEN_SOURCE_EXTENDED)
    #define _XOPEN_SOURCE_EXTENDED 1
  #endif
  #if !defined(__EXTENSIONS__)
    #define __EXTENSIONS__ 1
  #endif
#endif

#ifndef TURBO_SIMICS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#endif /* TURBO_SIMICS */

#define FIRST_SIM_VERSION  1000
#include "build-id.h"

/* SIM_VERSION_COMPAT: lowest version that Simics is ABI compatible with */
#define SIM_VERSION_COMPAT 1302

#ifdef __SUNPRO_C
#pragma error_messages (off, E_CONST_PROMOTED_UNSIGNED_LL)
#pragma error_messages (off, E_CONST_PROMOTED_UNSIGNED_LONG)
#pragma error_messages (off, E_STATEMENT_NOT_REACHED)
#pragma error_messages (off, E_END_OF_LOOP_CODE_NOT_REACHED)
#pragma error_messages (off, E_FWD_DECLARING_ENUM)
#pragma error_messages (off, E_LOOP_NOT_ENTERED_AT_TOP)
#pragma error_messages (off, E_TRAILING_COMMA_IN_ENUM)
#pragma error_messages (off, E_USELESS_DECLARATION)
#endif

#ifndef GULP
 #define NOTNULL
#endif

#if defined(__cplusplus)
  #ifdef cplusplus_restrict
    #define RESTRICT cplusplus_restrict
  #else
    #define RESTRICT
  #endif
#else
  #ifdef c_restrict
    #define RESTRICT c_restrict
  #else
    #define RESTRICT
  #endif
#endif


#if defined(__GNUC__)
 #define NORETURN __attribute__ ((noreturn))
 #define HIDDEN __attribute__((visibility ("hidden")))
 #ifndef UNUSED
  #define UNUSED __attribute__ ((unused))
 #endif
#elif defined(_MSC_VER)
 #define NORETURN __declspec(noreturn)
 #define HIDDEN
 #define UNUSED
#else
 #define NORETURN
 #define HIDDEN
 #define UNUSED
#endif

/*
 * GCC (starting with 2.96, somewhere) implements branch annotations, to get
 * the compiler to reorder blocks and emit static predictions correctly.
 *
 * Use thusly:
 *
 * if(likely(some_condition)) { ... }
 */

#if !defined(likely)
 #if defined(__GNUC__) && !(__GNUC__ == 2 && __GNUC_MINOR__ < 96) && !defined(TURBO_SIMICS)
  #define likely(x) __builtin_expect((x), 1)
  #define unlikely(x) __builtin_expect((x), 0)
 #else
  #define likely(x) (x)
  #define unlikely(x) (x)
 #endif
#endif /* not defined(likely) */

#if (defined(__svr4__) && defined(__sun__)) || defined (__sun) || defined(__SunOS_5_5) || defined(__SunOS_5_6) || defined(__SunOS_5_5_1)
/* <add id="config macro">
   <name index="true">SUN_SOLARIS</name>
   Defined if the host operating system is Sun Solaris 2.x (SunOS 5.x).
   Derived automatically from (gcc) compiler enviroment variables.
   </add>m
   */
#define SUN_SOLARIS
#elif defined(__linux__) && defined(__sparc__)
/* <add id="config macro">
   <name index="true">SUN_LINUX</name>
   Defined if the host operating system is Linux/Sparc.
   Derived automatically from (gcc) compiler enviroment variables.
   </add>
   */
#define SUN_LINUX
#elif defined(__FreeBSD__) && defined(__i386__)
/* <add id="config macro">
   <name index="true">X86_FREEBSD</name>
   Defined if the host operating system is FreeBSD/x86.
   Derived automatically from (gcc) compiler enviroment variables.
   </add>
   */
#define X86_FREEBSD
#elif defined(__linux__) && defined(__i386__)
/* <add id="config macro">
   <name index="true">X86_LINUX</name>
   Defined if the host operating system is Linux/x86.
   Derived automatically from (gcc) compiler enviroment variables.
   </add>
   */
#define X86_LINUX
#elif defined(__linux__) && defined(__powerpc__)
/* <add id="config macro">
   <name index="true">PPC_LINUX</name>
   Defined if the host operating system is Linux/PPC.
   Derived automatically from (gcc) compiler enviroment variables.
   </add>
   */
#define PPC_LINUX
#elif defined(__linux__) && defined(__x86_64__)
/* <add id="config macro">
   <name index="true">AMD64_LINUX</name>
   Defined if the host operating system is Linux/AMD64.
   Derived automatically from compiler environment variables.
   </add>
   */
#define AMD64_LINUX
#elif defined(__osf__)
/* <add id="config macro">
   <name index="true">DEC_ALPHA_OSF</name>
   Defined if the host operating system is Digital OSF (Alpha)
   Derived automatically from (gcc) compiler enviroment variables.
   </add>
   */
#define DEC_ALPHA_OSF
#elif defined(__alpha__) && defined(__linux__)
/* <add id="config macro">
   <name index="true">ALPHA_LINUX</name>
   Defined if the host operating system is Linux/Alpha
   Derived automatically from (gcc) compiler enviroment variables.
   </add>
   */
#define ALPHA_LINUX
#elif defined(__ia64__) && defined(__linux__)
/* <add id="config macro">
   <name index="true">IA64_LINUX</name>
   Defined if the host operating system is Linux/IA64
   Derived automatically from (gcc) compiler enviroment variables.
   </add>
   */
#define IA64_LINUX
#elif defined(__hppa__) && defined(__hpux__)
/* <add id="config macro">
   <name index="true">HP_UNIX</name>
   Defined if the host operating system is HP Unix (hpux).
   </add>
   */
#define HP_UNIX
#elif defined(_WIN32) && defined(__ICL) 
/* <add id="config macro">
   <name index="true">INTEL_WIN32</name>

   Defined if the host operating system is Windows, and Intel C++ is used.

   </add> */
#define INTEL_WIN32
#elif defined(_MSC_VER) && !defined(__ICL) && !defined(_M_AMD64)
/* <add id="config macro">
   <name index="true">MSVC_WIN32</name>

   Defined if the host operating system is Windows, and MSVC++ is used.

   </add> */
#define MSVC_WIN32
#elif defined(_WIN32) && !defined(__ICL) && !defined(_MSC_VER) && defined(__GNUC__) 
/* <add id="config macro"> 
   <name index="true">GCC_WIN32</name> 
 
   Defined if the host operating system is Windows, and a non-cygwin
   GCC is used. (either MingW's or 'gcc -mno-cygwin').
 
   </add> */ 
#define GCC_WIN32 
#elif defined(_MSC_VER) && defined(_M_AMD64)
/* <add id="config macro"> 
   <name index="true">MSVC_WIN64</name> 
 
   Defined if the host operating system is 64-bit windows,
   and the compiler is MSVC.
 
   </add> */ 
#define MSVC_WIN64
#else
#error "Cannot recognize the operating system you are compiling for"
#endif

#ifdef __linux__
/* <add id="config macro">
   <name index="true">ANY_LINUX</name>
   Defined if the host operating system is Linux, any architecture.
   </add>
   */
#define ANY_LINUX
#endif

#if defined(__sparc) && !defined(__sparcv8) && !defined(__sparcv9)
#define __sparcv8
#endif

#if defined(__sparcv9)
/* <add id="config macro">
   <name index="true">HOST_SPARC_V9</name>
   Defined if the host processor architecture is a Sparc v9.
   Derived automatically from (gcc/ws) compiler enviroment variables.
   </add>
   */
#	define HOST_SPARC_V9
/* <add id="config macro">
   <name index="true">HOST_SPARC</name>
   Defined if the host processor architecture is a Sparc v8/v9.
   Derived automatically from (gcc) compiler enviroment variables.
   </add>
   */
#	define HOST_SPARC
#elif defined(__sparcv8)
/* <add id="config macro">
   <name index="true">HOST_SPARC_V8</name>
   Defined if the host processor architecture is a Sparc v8.
   Derived automatically from (gcc/ws) compiler enviroment variables.
   </add>
   */
#	define HOST_SPARC_V8
#	define HOST_SPARC
#elif defined(__alpha__) || defined(__alpha)
/* <add id="config macro">
   <name index="true">HOST_ALPHA</name>
   Defined if the host processor architecture is Digital Alpha.
   </add>
   */
#define HOST_ALPHA
#elif defined(__hppa__)
/* <add id="config macro">
   <name index="true">HOST_ALPHA</name>
   Defined if the host processor architecture is HP Precision Architecture.
   </add>
   */
#define HOST_HPPA
#elif defined(__i386__) || defined(_M_IX86)
/* <add id="config macro">
   <name index="true">HOST_X86</name>
   Defined if the host processor architecture is Intels x86 (386+) Architecture
   </add>
   */
#define HOST_X86
#elif defined(__powerpc__)
/* <add id="config macro">
   <name index="true">HOST_PPC</name>
   Defined if the host processor architecture is Motorola/IBM PowerPC
   </add>
   */
#define HOST_PPC
#elif defined(__ia64__)
/* <add id="config macro">
   <name index="true">HOST_IA64</name>
   Defined if the host processor architecture is Intel IA64
   </add>
   */
#define HOST_IA64
#elif defined(__x86_64__) || defined(_M_AMD64)
/* <add id="config macro">
   <name index="true">HOST_AMD64</name>
   Defined if the host processor architecture is AMD64
   </add>
   */
#define HOST_AMD64
#else
#error "Cannot recognize the host processor architecture you are compiling for"
#endif

/* host bitness... */
#if defined(HOST_SPARC_V9) || defined(HOST_ALPHA) || defined(HOST_IA64) || defined(HOST_AMD64)
/* <add id="config macro">
   <name index="true">HOST_64_BIT</name>
   Defined if the host is 64-bit
   </add>
*/
#	define HOST_64_BIT
#endif

#if defined(HOST_ALPHA) || defined(HOST_X86) || defined(HOST_IA64) || defined(HOST_AMD64)
/* <add id="config macro">
   <name index="true">HOST_LITTLE_ENDIAN</name>
   Defined if the host processor architecture is little endian. External files
   etc are defined to be network endian (essentiall big endian), so a little
   endian host is required to do some extra conversions.
   </add>
   */
#define HOST_LITTLE_ENDIAN
#endif

#if !defined(HOST_LITTLE_ENDIAN)
#define HOST_BIG_ENDIAN
#endif

#if defined(TARGET_X86) || defined(TARGET_ALPHA) || defined(TARGET_IA64) || defined(TARGET_MSP430)
#define TARGET_LITTLE_ENDIAN
#endif

#if defined(TARGET_SPARC_V9) || defined(TARGET_PPC)
#define TARGET_BIG_ENDIAN
#endif

#if defined(TARGET_SPARC_V9) || defined(TARGET_MIPS)
#define TARGET_HAS_DELAY_SLOT
#endif

/*
  Begin adding proper support for cross-endian execution
*/
#if defined(HOST_LITTLE_ENDIAN) != defined(TARGET_LITTLE_ENDIAN)
/* <add id="config macro">
   <name index="true">CROSS_ENDIAN</name>
   Defined if the endianness of the target and host differ. Currently this is
   used for running big endian targets on little endian hosts.
   </add>
   */
#define CROSS_ENDIAN
#endif

/* Function inlining macros */
#ifdef __GNUC__
#  ifdef __OPTIMIZE__
#    if (__GNUC__ < 3) || (__GNUC__ == 3 && __GNUC_MINOR__ < 1)
#      define FORCE_INLINE extern inline
#    else
#      define FORCE_INLINE static inline __attribute__ ((always_inline))
#    endif
#  else  /* !__OPTIMIZE__ */
#    define FORCE_INLINE static inline
#  endif /* !__OPTIMIZE__ */
#else
#  define FORCE_INLINE static inline
#endif /* !defined(__GNUC__) */

#ifdef _MSC_VER
/* Some useful defines for Intel C / MSVC. */
#define vsnprintf _vsnprintf
#define snprintf _snprintf
#define strtoll _strtoi64
#define strtoull _strtoui64
#define pclose _pclose
/* These functions requires "#include <string.h>" */
#define strcasecmp stricmp
#define strncasecmp strnicmp

#define S_IRUSR _S_IREAD
#define S_IWUSR _S_IWRITE
#endif /* _MSC_VER */


#ifndef DLL_EXPORT
#define DLL_EXPORT
#endif

#if !defined(FALSE)
#define FALSE 0
#define TRUE  1
#endif /* ! FALSE */

#endif /* _SIMICS_GLOBAL_H */
