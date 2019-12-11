/*
 * simics/core/types.h
 *
 * This file is part of Virtutech Simics
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_TYPES_H
#define _SIMICS_CORE_TYPES_H

#if !defined(TURBO_SIMICS)

#ifdef HAVE_STDINT_H
#include <stdint.h>
#endif
#ifdef HAVE_INTTYPES_H
#include <inttypes.h>
#endif
#ifdef HAVE_SYS_TYPES_H
#include <sys/types.h>
#endif
#include <limits.h>
#ifdef _WIN32
#include <winsock2.h>
#include <windows.h>
#endif

#include <simics/global.h>

#endif /* !TURBO_SIMICS */

#undef INT64_C
#undef UINT64_C

#if (defined(MSVC_WIN32) || defined(INTEL_WIN32)) && !defined(TURBO_SIMICS)
typedef __int64 integer_t;
typedef unsigned __int64 uinteger_t;
#define INT64_C(x)  x ## i64
#define UINT64_C(x) x ## Ui64
#else
typedef long long integer_t;
typedef unsigned long long uinteger_t;
#define INT64_C(x) x ## LL
#define UINT64_C(x) x ## ULL
#endif /* ! MSVC_WIN32 && ! INTEL_WIN32 */

#define MAX_INTEGER_T  INT64_C(9223372036854775807)
#define MIN_INTEGER_T  (-INT64_C(9223372036854775807) - 1)
#define MAX_UINTEGER_T UINT64_C(18446744073709551615)
#define MIN_UINTEGER_T UINT64_C(0)

#ifndef TURBO_SIMICS
/* <add-type id="tuple_int_string_t def">
   </add-type>
 */
typedef struct {
        int integer;
        const char *string;
} tuple_int_string_t;
#endif

/*
   <add id="simics api types">
   <name index="true">data_or_instr_t</name>
   <doc>
   <doc-item name="NAME">data_or_instr_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="data_or_instr_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This type is used in several API functions and structures to indicate if data or instructions is used.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="data_or_instr_t def">
   </add-type>
 */
typedef enum {
        Sim_DI_Instruction      = 0,
        Sim_DI_Data             = 1
} data_or_instr_t;

#if !defined(TURBO_SIMICS)
/* <add id="simics api types">
   <name index="true">socket_t</name>
   <doc>
   <doc-item name="NAME">socket_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="socket_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   This data type is used to identify a communication socket
   (typically TCP/IP). It is defined to be an <type>int</type> on UNIX
   systems and <type>SOCKET</type> under Windows.
   </doc-item>
   </doc></add>

   <add id="socket_t def">
   <insert-until id="socket_t" text="// JDOCU INSERT-UNTIL socket_t"/>
   </add>
*/
#ifdef _WIN32
typedef SOCKET socket_t;
#else
typedef int socket_t;
#endif /* !_WIN32 */
// JDOCU INSERT-UNTIL socket_t

#ifndef _WIN32
#define INVALID_SOCKET -1
#endif /* !defined(_WIN32) */

#if defined(_MSC_VER) && !defined(TURBO_SIMICS)
typedef SSIZE_T ssize_t;
#endif /* defined(_MSC_VER) && !defined(TURBO_SIMICS) */

#endif /* !defined(TURBO_SIMICS) */

#ifdef __MINGW32__
#include <w32api.h>
#endif

/* winsock2.h defines int32 for us, so we define HAVE_INT32 here if
 * winsock2.h has been included, to avoid conflicts below */
/* this is not true for w32api 1.4. */
#if defined(_WINSOCK2_H) && (__W32API_MAJOR_VERSION == 1 && __W32API_MINOR_VERSION <= 3)
#define HAVE_INT32
#endif

#ifndef HAVE_INT8
typedef signed char int8;
#endif /* ! HAVE_INT8 */
#ifndef HAVE_UINT8
typedef unsigned char uint8;
#endif /* ! HAVE_UINT8 */

#ifndef HAVE_INT16
typedef short int16;
#endif /* ! HAVE_INT16 */
#ifndef HAVE_UINT16
typedef unsigned short uint16;
#endif /* ! HAVE_UINT16 */

#ifndef HAVE_INT32
typedef int int32;
#endif /* ! HAVE_INT32 */
#ifndef HAVE_UINT32
typedef unsigned int uint32;
#endif /* ! HAVE_UINT32 */

#if (defined(MSVC_WIN32) || defined(INTEL_WIN32)) && !defined(TURBO_SIMICS)
#ifndef HAVE_INT64
typedef unsigned __int64 uint64;
#endif /* ! HAVE_INT64 */
#ifndef HAVE_UINT64
typedef __int64 int64;
#endif /* ! HAVE_UINT64 */

#else /* ! (MSVC_WIN32 || INTEL_WIN32) */

#ifndef HAVE_UINT64
typedef unsigned long long uint64;
#endif /* ! HAVE_UINT64 */
#ifndef HAVE_INT64
typedef long long int64;
#endif /* ! HAVE_INT64 */

#endif /* ! (MSVC_WIN32 || INTEL_WIN32) */

/* Definitions for intptr_t, uintptr_t */
#if !defined(HAVE_INTPTR_T) || defined(TURBO_SIMICS)
#ifdef HOST_64_BIT
typedef int64 intptr_t;
#else  /* ! HOST_64_BIT */
typedef int32 intptr_t;
#endif /* ! HOST_64_BIT */
#endif /* ! HAVE_INTPTR_T */

#if !defined(HAVE_UINTPTR_T) || defined(TURBO_SIMICS)
#ifdef HOST_64_BIT
typedef uint64 uintptr_t;
#else /* ! HOST_64_BIT */
typedef uint32 uintptr_t;
#endif /* ! HOST_64_BIT */
#endif /* ! HAVE_UINTPTR_T */

/* Export a conf_object-compatible definition to the API for now.
 * If possible, export it to obsolete-api instead. */
#ifndef NO_FAKE_PROCESSOR_T
typedef struct conf_object processor_t;
#endif

#ifndef TURBO_SIMICS            /* Turbo does not understand size_t */
typedef struct {
        size_t len;
        uint8 *str; /* NOT null-terminated! */
} byte_string_t;
#endif /* not TURBO_SIMICS */

/* <add-type id="logical_address_t">
    </add-type>
*/
typedef uint64 logical_address_t;
/* <add-type id="physical_address_t">
    </add-type>
*/
typedef uint64 physical_address_t;
/* <add-type id="generic_address_t">
    </add-type>
*/
typedef uint64 generic_address_t;
/* <add-type id="linear_address_t">
    </add-type>
*/
typedef uint64 linear_address_t;

/* <add-type id="addr_space_t def"><ndx>addr_space_t</ndx></add-type> */
typedef enum {
        Sim_Addr_Space_Conf,
        Sim_Addr_Space_IO,
        Sim_Addr_Space_Memory
} addr_space_t;

/* <add id="simics api types">
   <name index="true">processor_mode_t</name>
   <doc>
   <doc-item name="NAME">processor_mode_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="processor_mode_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   The <type>processor_mode_t</type> data type is used to specify if a
   CPU is running in user mode or in a privileged mode (often called
   supervisor mode). For processor architectures with several
   privilege levels, the non-user levels are all identified as
   <const>Sim_CPU_Mode_Supervisor</const>.
   </doc-item>
   </doc>
   </add>

   <add-type id="enum types|processor_mode_t def"></add-type> */
typedef enum {
        Sim_CPU_Mode_User       = 0,
        Sim_CPU_Mode_Supervisor = 1,
        Sim_CPU_Mode_Hypervisor
} processor_mode_t;

/* <add id="simics api types">
   <name index="true">read_or_write_t</name>
   <doc>
   <doc-item name="NAME">read_or_write_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="read_or_write_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   Whether a memory access is a <i>read</i> (from memory) or a <i>write</i>
   (to memory).
   </doc-item>
   </doc>
   </add>

   <add-type id="read_or_write_t def"></add-type> */
typedef enum {
        Sim_RW_Read  = 0,
        Sim_RW_Write = 1
} read_or_write_t;

/* <add-type id="ini_type_t"></add-type> */
typedef enum {
        Sim_Initiator_Illegal         = 0x0,    /* catch uninitialized */
        Sim_Initiator_CPU             = 0x1000,
        Sim_Initiator_CPU_V9          = 0x1100,
        Sim_Initiator_CPU_UII         = 0x1101,
        Sim_Initiator_CPU_UIII        = 0x1102,
        Sim_Initiator_CPU_UIV         = 0x1103,
        Sim_Initiator_CPU_UT1         = 0x1104, /* 1105, 1106 internal */
        Sim_Initiator_CPU_X86         = 0x1200,
        Sim_Initiator_CPU_PPC         = 0x1300,
        Sim_Initiator_CPU_Alpha       = 0x1400,
        Sim_Initiator_CPU_IA64        = 0x1500,
        Sim_Initiator_CPU_MIPS        = 0x1600,
        Sim_Initiator_CPU_MIPS_RM7000 = 0x1601,
        Sim_Initiator_CPU_MIPS_E9000  = 0x1602,
        Sim_Initiator_CPU_ARM         = 0x1700,
        Sim_Initiator_Device          = 0x2000,
        Sim_Initiator_PCI_Device      = 0x2010,
        Sim_Initiator_Cache           = 0x3000, /* The transaction is a cache
                                                   transaction as defined by
                                                   g-cache */
        Sim_Initiator_Other           = 0x4000  /* initiator == NULL */
} ini_type_t;

/* <add id="simics api types">
   <name index="true">endianness_t</name>
   <doc>
   <doc-item name="NAME">endianness_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="endianness_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   Specifies the endianness to use for certain memory operations. When
   <const>Sim_Endian_Target</const> is used, the data from memory is
   copied without any endian conversion. 
   <const>Sim_Endian_Host_From_BE</const> and
   <const>Sim_Endian_Host_From_LE</const> copies data between a
   big-endian, or little-endian, memory and a host
   buffer. <const>Sim_Endian_Host</const> is obsolete and should not
   be used.
   </doc-item>
   </doc>
   </add>

   <add-type id="endianness_t def"></add-type> */
typedef enum {
        Sim_Endian_Target,
        Sim_Endian_Host_From_BE,
        Sim_Endian_Host_From_LE,
        Sim_Endian_Host          /* Obsolete. Do not use */
} endianness_t;

/* <add id="simics api types">
   <name index="true">pseudo_exceptions_t</name>
   <doc>
   <doc-item name="NAME">pseudo_exceptions_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="pseudo_exceptions_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   Used to signal simulator exceptions for memory accesses. Memory
   access functions in Simics use <tt>exception_type_t</tt> to return
   errors. Errors usually corresponds to hardware exceptions, but in
   some cases additional return values are needed, and then pseudo
   exceptions are used. The most common is <tt>Sim_PE_No_Exception</tt>,
   indicating that no error has occurred. Most pseudo exceptions are
   Simics internals, but some are used by devices and memory spaces.
   <dl>
   <dt>Sim_PE_No_Exception</dt><dd>No exception.</dd>
   <dt>Sim_PE_IO_Not_Taken</dt><dd>Access to unmapped memory. In the
   PCI memory spaces interpreted as master abort.</dd>
   <dt>Sim_PE_IO_Error</dt><dd>Accessed device returned error. In the
   PCI memory spaces interpreted as target abort.</dd>
   <dt>Sim_PE_Inquiry_Outside_Memory</dt><dd>Same as Sim_PE_IO_Not_Taken,
   but for inquiry accesses.</dd>
   <dt>Sim_PE_Inquiry_Unhandled</dt><dd>The accessed device does not
   support inquiry operations.</dd>
   <dt>Sim_PE_Stall_Cpu</dt><dd>Timing model requested stall</dd>
   <dt>Sim_PE_Default_Semantics</dt><dd>Used by ASI handlers on SPARC,
   and for user decoders to signal that the default semantics should
   be run.</dd>
   <dt>Sim_PE_Ignore_Semantics</dt><dd>Used by ASI handlers on SPARC
   to signal no update of destination registers.</dd>
   <dt>Internal:</dt><dd>Sim_PE_Silent_Break, Sim_PE_Return_Break,
   Sim_PE_Interrupt_Break,
   Sim_PE_Interrupt_Break_Take_Now, Sim_PE_Exception_Break,
   Sim_PE_Hap_Exception_Break, Sim_PE_Instruction_Finished,
   Sim_PE_Invalid_Address, Sim_PE_Speculation_Failed,
   Sim_PE_MAI_Return, Sim_PE_Last.</dd>
   </dl>
   </doc-item>
   </doc>
   </add>
   <add-type id="pseudo_exceptions_t def"></add-type> */
typedef enum {
        Sim_PE_No_Exception = 1025,
        Sim_PE_Code_Break,
        Sim_PE_Silent_Break,
        Sim_PE_Inquiry_Outside_Memory,
        Sim_PE_Inquiry_Unhandled,
        Sim_PE_IO_Not_Taken,
        Sim_PE_IO_Error,
        Sim_PE_Interrupt_Break,
        Sim_PE_Interrupt_Break_Take_Now,
        Sim_PE_Exception_Break,
        Sim_PE_Hap_Exception_Break,
        Sim_PE_Stall_Cpu,
        Sim_PE_Locked_Memory,
        Sim_PE_Return_Break,
        Sim_PE_Instruction_Finished,
        Sim_PE_Default_Semantics,
        Sim_PE_Ignore_Semantics,
        Sim_PE_Speculation_Failed,
        Sim_PE_Invalid_Address,
        Sim_PE_MAI_Return,
        Sim_PE_Last
} pseudo_exceptions_t;
/* make sure the above matches pseudo_exception_name() in exceptions.c */

/* Accommodate all kinds of exceptions (and pseudo-exceptions) in a single
   type: using an int is easiest, since C does not have true union types */
/*
   <add id="simics api types">
   <name index="true">exception_type_t</name>
   <doc>
   <doc-item name="NAME">exception_type_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="exception_type_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   Accommodate all kinds of exceptions and pseudo-exceptions in a single
   type.
   </doc-item>
   </doc>
   </add>
*/
/* <add-type id="exception_type_t def"></add-type> */
typedef int exception_type_t;

#define IS_PSEUDO_EXCEPTION(exp)   ((exp) > Sim_PE_No_Exception)

/* <add-type id="map_info_t def"></add-type> */
typedef enum swap_mode {
        Sim_Swap_None       = 0,
        Sim_Swap_Bus        = 1,
        Sim_Swap_Bus_Trans  = 2,
        Sim_Swap_Trans      = 3
} swap_mode_t;


/* <add id="simics api types">
   <name>simtime_t, cycles_t, pc_step_t, nano_secs_t</name>
   <doc>
   <doc-item name="NAME">
   <idx>simtime_t</idx>, <idx>cycles_t</idx>, <idx>pc_step_t</idx>,
   <idx>nano_secs_t</idx>
   </doc-item>
   <doc-item name="SYNOPSIS">
   <insert id="simtime_t def"/>
   <insert id="cycles_t def"/>
   <insert id="pc_step_t def"/>
   <insert id="nano_secs_t def"/>
   </doc-item>
   <doc-item name="DESCRIPTION">
   These are the types used for keeping track of time in Simics.

   <type>cycles_t</type> is used when the time is specified in cycles,
   <type>pc_step_t</type> is used when the time is specified in steps,
   and <type>simtime_t</type> is used in places where it is unknown
   whether the time is in steps or cycles. See the chapter "The Simics
   Simulator" in the <i>Simics User Guide</i> for a discussion about
   the difference between steps and cycles.

   <type>nano_secs_t</type> is used to express a number of nanoseconds
   (<math>10^{-9}</math> seconds).
   </doc-item>
   </doc></add>
*/

/* <add-type id="simtime_t def"></add-type> */
typedef integer_t simtime_t;
/* <add-type id="cycles_t def"></add-type> */
typedef simtime_t cycles_t;
/* <add-type id="pc_step_t def"></add-type> */
typedef simtime_t pc_step_t;
/* <add-type id="nano_secs_t def"></add-type> */
typedef simtime_t nano_secs_t;

#if defined(GULP_PYTHON)
typedef struct _object PyObject;
typedef PyObject lang_void;
typedef struct _typed_object typed_lang_void;
#else  /* ! GULP */
/* <add id="simics api types">
   <name index="true">lang_void</name>
   <doc>
   <doc-item name="NAME">lang_void</doc-item>
   <doc-item name="SYNOPSIS">
   <insert id="lang_void def"/>
   <insert id="typed_lang_void def"/></doc-item>
   <doc-item name="DESCRIPTION">
   In some places in the Simics API, arguments of type 
   <type><nobr>lang_void *</nobr></type> are used. This data type is used to
   allow transparent passing of any data type in the current programming
   language as argument. In C, this works exactly like a 
   <tt><nobr>void *</nobr></tt> and in Python, it is any Python
   object. The type <tt>typed_lang_void</tt> is equivalent to <tt>lang_void</tt>
   in the Simics API.

   Typically, this is used by iterator functions in the API which take callback
   functions as arguments. The callback function is later called with the
   <type>lang_void</type> data and the object being iterated over.
   </doc-item>

   <doc-item name="SEE ALSO">SIM_for_all_processors, SIM_register_typed_attribute,
   SIM_hap_add_callback</doc-item>
   </doc></add>
*/
/* <add-type id="lang_void def"></add-type> */
typedef void lang_void;
/* <add-type id="typed_lang_void def"><ndx>typed_lang_void</ndx></add-type> */
typedef void typed_lang_void;
#endif /* ! GULP */

#ifndef TURBO_SIMICS
typedef void *ignored_pointer_t;
#endif

#ifndef NO_FAKE_HAP_TYPE_T
/* <add id="simics api types">
   <name index="true">hap_type_t</name>
   <doc>
   <doc-item name="NAME">hap_type_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="hap_type_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   This data type is used to represent hap (occurrence) types. This is
   a runtime number that may change between different Simics
   invocations. Haps are normally identified by strings, but by
   calling <fun>SIM_hap_get_number()</fun>, a lookup from such a name
   to a <type>hap_type_t</type> can be made.
   <doc-item name="SEE ALSO">SIM_hap_get_number, SIM_hap_add_type,
   SIM_for_all_hap_types</doc-item>
   </doc-item>
   </doc></add>
*/
/* <add-type id="hap_type_t def"></add-type>
 */
typedef int hap_type_t;
#endif

#ifndef TURBO_SIMICS
/* <add-type id="conf conf_object_t"></add-type> */
typedef struct conf_object conf_object_t;
typedef struct conf_class conf_class_t;
/* <add-type id="map_list_t def"></add-type> */
typedef struct map_list map_list_t;
typedef struct memory_space_interface memory_space_interface_t;
/* <add-type id="conf log_object_t"></add-type> */
typedef struct log_object log_object_t;
/* <add-type id="conf attr_value_t"></add-type> */
typedef struct attr_value attr_value_t;
/* <add-type id="object_vector_t typedef"></add-type> */
typedef struct object_vector object_vector_t;
/* <add-type id="class_vector_t typedef"></add-type> */
typedef struct class_vector class_vector_t;
/* <add-type id="generic_transaction_t def"></add-type> */
typedef struct generic_transaction generic_transaction_t;
/* <add-type id="breakpoint_range_t def"><ndx>breakpoint_range_t</ndx></add-type> */
typedef struct breakpoint_range breakpoint_range_t;
/* <add-type id="breakpoint_t def"><ndx>breakpoint_t</ndx></add-type> */
typedef struct breakpoint breakpoint_t;
/* <add-type id="interval_set_t def"><ndx>interval_set_t</ndx></add-type> */
typedef struct interval_set interval_set_t;
#define HAVE_INTERVAL_SET_T
/* <add-type id="interval_set_iter_t def"><ndx>interval_set_iter_t</ndx></add-type> */
typedef struct interval_set_iter interval_set_iter_t;
typedef struct breakpoint_interface breakpoint_interface_t;
typedef struct event_poster_interface event_poster_interface_t;
/* <add-type id="icode_page_t def"><ndx>page_t</ndx></add-type> */
typedef struct icode_page icode_page_t;
/* <add-type id="page_t def"><ndx>page_t</ndx></add-type> */
typedef struct page page_t;
typedef struct apic_cpu_interface apic_cpu_interface_t;
typedef struct pin_interface pin_interface_t;
typedef struct signal_interface signal_interface_t;

typedef struct icode_mode icode_mode_t;

/* <add-type id="reg_info type"><ndx>reg_info_t</ndx></add-type> */
typedef struct reg_info reg_info_t;
/* <add-type id="instr_info_dep type"><ndx>instr_info_dep_t</ndx></add-type> */
typedef struct instr_info_dep instr_info_dep_t;

typedef void (*hap_func_t)(lang_void *);
typedef void (*str_hap_func_t)(lang_void *);
typedef void (*obj_hap_func_t)(lang_void *, conf_object_t *ini_obj);
#endif /* ndef TURBO_SIMICS */

/* <add-type id="hap_handle_t def"><ndx>hap_handle_t</ndx></add-type> */
typedef int hap_handle_t;

#ifndef TURBO_SIMICS
/* <add id="breakpoint_kind_t">
   <ndx>breakpoint_kind_t</ndx>
   <insert-upto text=";"/>
   </add>
 */
typedef enum {
        Sim_Break_Physical = 0,
        Sim_Break_Virtual  = 1,
        Sim_Break_Linear   = 2      /* x86 only */
} breakpoint_kind_t;
#endif

/* All combinations are allowed (logical or)
   <add id="access_t">
   <ndx>access_t</ndx>
   <insert-upto text=";"/>
   </add>
*/
typedef enum {
        Sim_Access_Read = 1,
        Sim_Access_Write = 2,
        Sim_Access_Execute = 4
} access_t;

/* <add-type id="breakpoint_id_t"><ndx>breakpoint_id_t</ndx></add-type> */
typedef int breakpoint_id_t;

/* used in register_info() interface function */
/* <add id="ireg_info_t"><ndx>ireg_info_t</ndx><insert-upto text=";"/></add> */
typedef enum {
        Sim_RegInfo_Catchable
} ireg_info_t;

/*
 * Branch arc types.
 * <add-type id="arc_type_t def"><ndx>arc_type_t</ndx></add-type>
 */
typedef enum {
        /* Arc caused by a regular branch instruction. */
        Arc_None,
        Arc_Taken_Branch,
        Arc_Init,
        Arc_Cache_Line_Start,
        Arc_User,
        Arc_Compensate,
        Arc_Interrupt,
        Arc_Page_Start,
        /* Arm */
        /* Arc caused by a software interrupt instruction. */
        Arc_Exception_Counted,
        /* Arc caused by some other exception than software interrupt. This
           kind of branch arc is special in that it is not subtracted from the
           number of times the instruction has been executed. */
        Arc_Exception_Not_Counted,
        /* Arc caused by an ALU instruction with pc as rd and the s bit set,
           i.e, probably a return from an exception. */
        Arc_Return_From_Exception,
        /* Arc caused by the execution entering or leaving the interpreter. */
        Arc_To_From_Interpreter,
        /* Arc caused by a fall through from one storage page to the next. */
        Arc_End_Of_Page,

        /* Just to avoid comma problems with the ifdefs... */
        Arc_Dummy
} arc_type_t;

/* Make *sure* this is kept in sync with instr-types.sg */

/*
   <add id="simics api types">
   <name index="true">instr_type_t</name>
   <doc>
   <doc-item name="NAME">instr_type_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="instr_type_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This encodes the type of an instruction, which is composed of ORing
   together the <const>It_</const> constants.
   </doc-item>
   </doc>
   </add>

   <add-type id="instr_type_t def"></add-type>
*/
typedef uint64 instr_type_t;

/* Remember to add new It_ defines to python-frontend/typemaps.h too. */
/* <add id="instr_type_t def">
   <insert-until text="// end of instr_type_t defines"/>
   </add> */
#define It_Other                   UINT64_C(0x1)
#define It_Alu                     UINT64_C(0x2)
#define It_Relbranch               UINT64_C(0x4)
#define It_Load                    UINT64_C(0x8)
#define It_Store                   UINT64_C(0x10)
#define It_Sethi                   UINT64_C(0x20)
#define It_Popc                    UINT64_C(0x40)
#define It_Fp_Triop                UINT64_C(0x80)
#define It_Fp_Diop                 UINT64_C(0x100)
#define It_Fp_Unop                 UINT64_C(0x200)
#define It_Fp_Cmp                  UINT64_C(0x400)
#define It_Swap                    UINT64_C(0x800)
#define It_Vis                     UINT64_C(0x1000)
#define It_Flush                   UINT64_C(0x2000)
#define It_Call                    UINT64_C(0x4000)
#define It_Return                  UINT64_C(0x8000)
#define It_Trap                    UINT64_C(0x10000)
#define It_Trap_Ret                UINT64_C(0x20000)
#define It_Idle                    UINT64_C(0x40000)
#define It_User_Decoder_Defined    UINT64_C(0x80000)
#define It_Varbranch               UINT64_C(0x100000) /* Branchtarget is dynamic */
#define It_Absbranch               UINT64_C(0x200000) /* branch to an immidiate absolute target */
#define It_Fstsw                   UINT64_C(0x400000) /* fstsw */
#define It_Fp                      UINT64_C(0x800000) /* floating point instruction */
#define It_Membar                  UINT64_C(0x1000000)
#define It_Prefetch                UINT64_C(0x2000000)
#define It_Convert                 UINT64_C(0x4000000)
#define It_Cmov                    UINT64_C(0x8000000)
#define It_String                  UINT64_C(0x10000000)
#define It_Mov                     UINT64_C(0x20000000)
#define It_SSE                     UINT64_C(0x40000000)
#define It_MMX                     UINT64_C(0x80000000)
#define It_Cond                    UINT64_C(0x100000000) /* Conditional, i.e it may continue to 
                                                            the sequentially next instruction */
// end of instr_type_t defines

typedef enum {
        Cache_Control_Nop,
        Cache_Control_Fetch_Line,
        Cache_Control_Invalidate_Line,
        Cache_Control_Copyback_Line,
        Cache_Control_Invalidate_Cache
} cache_control_operation_t;

#ifndef TURBO_SIMICS

/* <add-type id="instr_info type"><ndx>instr_info_t</ndx></add-type> */
struct instr_info {
        instr_type_t   type;           /* ORed representation of 
                                          instr_type_t */
        logical_address_t return_pc;   /* (SPARC only) Return program counter
                                          (defined iff It_Call is true) */
        int            delay_slots;    /* (SPARC only) Delay slots for instruction
                                          (defined iff It_Return) */
        int            length;         /* Instruction length in bytes */
        const char    *name;           /* (SPARC and x86) instruction name */

        instr_info_dep_t *dependencies;
};

/* <add-type id="instr_info type"><ndx>instr_info_t</ndx></add-type> */
typedef struct instr_info instr_info_t;

#endif /* not TURBO_SIMICS */

#include <simics/core/callbacks-types.h>

#endif /* _SIMICS_CORE_TYPES_H */
