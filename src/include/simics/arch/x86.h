/*
 * simics/arch/x86.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_ARCH_X86_H
#define _SIMICS_ARCH_X86_H

/* <add-type id="x86_access_type_t"> </add-type> */
typedef enum x86_access_type {
        X86_Other,               /* Access that is not categorized (rare) */
        X86_Vanilla,             /* "Normal" access, such as a MOV to/from
                                    memory. X86_Vanilla operations use the STCs. */
        X86_Instruction,         /* Instruction fetch */
        X86_Clflush,             /* Cache line flush from CLFLUSH */
        X86_Fpu_Env,             /* Floating point environment (FLDENV, FNSTENV,
                                    environment part of FRSTOR, FNSAVE) */
        X86_Fpu_State,           /* Register part of FRSTOR and FNSAVE */
        X86_Idt,                 /* Interrupt descriptor table */
        X86_Gdt,                 /* Global descriptor table */
        X86_Ldt,                 /* Local descriptor table */
        X86_Task_Segment,        /* Task segment */
        X86_Task_Switch,         /* Task save/restore during a task switch */
        X86_Far_Call_Parameter,  /* Parameter copy in far call */
        X86_Stack,               /* Stack accesses during complex control flow
                                    operations (exception handling, etc.) */
        X86_Pml4,                /* Page map level 4 table */
        X86_Pdp,                 /* Page directory pointer table */
        X86_Pd,                  /* Page directory table */
        X86_Pt,                  /* Page table */
        X86_Sse,                 /* 16-byte operations to/from SSE registers */
        X86_Fpu,                 /* 10-byte and 16-byte operations to/from
                                    X87 registers */
        X86_Access_Simple,       /* Device accesses (DMA) */
        X86_Microcode_Update,    /* Data read when performing a processor
                                    microcode update */
        X86_Non_Temporal,        /* Non temporal store (example: MOVNTI) */
        X86_Prefetch_3DNow,      /* Prefetch with PREFETCH (3DNow!) */
        X86_Prefetchw_3DNow,     /* Prefetch with PREFETCHW (3DNow!) */
        X86_Prefetch_T0,         /* Prefetch with PREFETCHT0 (SSE) */
        X86_Prefetch_T1,         /* Prefetch with PREFETCHT1 (SSE) */
        X86_Prefetch_T2,         /* Prefetch with PREFETCHT2 (SSE) */
        X86_Prefetch_NTA,        /* Prefetch with PREFETCHNTA (SSE) */
        X86_Loadall,             /* State read by the loadall instruction */
        X86_Atomic_Info,         /* Transaction sent with size 0 to
                                    finish an atomic transaction */
        X86_Cmpxchg16b,          /* CMPXCHG16B instruction */
        X86_Smm_State            /* SMM state structure */
} x86_access_type_t;

/* <add-type id="x86_memory_type_t"> </add-type> */
typedef enum {
        X86_None,
        X86_Strong_Uncacheable,    /* UC */
        X86_Uncacheable,           /* UC- */
        X86_Write_Combining,       /* WC */
        X86_Write_Through,         /* WT */
        X86_Write_Back,            /* WB */
        X86_Write_Protected        /* WP */
} x86_memory_type_t;

/*
   <add id="simics arch api types">
   <name index="true">x86_sync_instruction_type_t</name>
   <doc>
   <doc-item name="NAME">x86_sync_instruction_type_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="x86_sync_instruction_type_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   Type of synchronisation instruction for x86. Used in the <tt>Core_Sync_Instruction</tt> hap.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="x86_sync_instruction_type_t def"></add-type> */
typedef enum {
        X86_SFence = 1,
        X86_LFence = 2,
        X86_MFence = 3
} x86_sync_instruction_type_t;


/*
   <add id="arch_register_id_t def">
   <insert id="x86_register_id type"/>
   </add>

   <add id="arch_register_id_t desc">
   For x86 the <type>x86_register_id_t</type> can be used to refer to
   the different registers.
   </add>
*/

/* NOTE: do not change the numbers of RAX-RDI */

/* <add-type id="x86_register_id type"><ndx>x86_register_id_t</ndx>
   </add-type> */
typedef enum {
        X86_Reg_Id_Rax = 0,
        X86_Reg_Id_Rcx = 1,
        X86_Reg_Id_Rdx = 2,
        X86_Reg_Id_Rbx = 3,
        X86_Reg_Id_Rsp = 4,
        X86_Reg_Id_Rbp = 5,
        X86_Reg_Id_Rsi = 6,
        X86_Reg_Id_Rdi = 7,

        X86_Reg_Id_R8  = 8,
        X86_Reg_Id_R9  = 9,
        X86_Reg_Id_R10 = 10,
        X86_Reg_Id_R11 = 11,
        X86_Reg_Id_R12 = 12,
        X86_Reg_Id_R13 = 13,
        X86_Reg_Id_R14 = 14,
        X86_Reg_Id_R15 = 15,

        X86_Reg_Id_Xmm0  = 16,
        X86_Reg_Id_Xmm1  = 17,
        X86_Reg_Id_Xmm2  = 18,
        X86_Reg_Id_Xmm3  = 19,
        X86_Reg_Id_Xmm4  = 20,
        X86_Reg_Id_Xmm5  = 21,
        X86_Reg_Id_Xmm6  = 22,
        X86_Reg_Id_Xmm7  = 23,

        X86_Reg_Id_Xmm8  = 24,
        X86_Reg_Id_Xmm9  = 25,
        X86_Reg_Id_Xmm10 = 26,
        X86_Reg_Id_Xmm11 = 27,
        X86_Reg_Id_Xmm12 = 28,
        X86_Reg_Id_Xmm13 = 29,
        X86_Reg_Id_Xmm14 = 30,
        X86_Reg_Id_Xmm15 = 31,

        X86_Reg_Id_Mm0 = 32,
        X86_Reg_Id_Mm1 = 33,
        X86_Reg_Id_Mm2 = 34,
        X86_Reg_Id_Mm3 = 35,
        X86_Reg_Id_Mm4 = 36,
        X86_Reg_Id_Mm5 = 37,
        X86_Reg_Id_Mm6 = 38,
        X86_Reg_Id_Mm7 = 39,

        X86_Reg_Id_PC  = 40,    /* this is RIP */

        X86_Reg_Id_CF  = 41,    /* integer condition code flags */
        X86_Reg_Id_DST = 42,    /* DST field used to cache PF flag */
        X86_Reg_Id_AF  = 43,
        X86_Reg_Id_ZF  = 44,
        X86_Reg_Id_SF  = 45,
        X86_Reg_Id_OF  = 46,
        X86_Reg_Id_DF  = 47,

        X86_Reg_Id_EFLAGS = 48, /* the whole 32 bits eflags */

        X86_Reg_Id_C0 = 49,     /* floating point cc flags */
        X86_Reg_Id_C1 = 50,
        X86_Reg_Id_C2 = 51,
        X86_Reg_Id_C3 = 52,
        X86_Reg_Id_Top = 53,    /* floating point stack top */
        X86_Reg_Id_Not_Used,    /* dummy number that can be used */

        X86_Reg_Id_Local_Max    /* keep this one last */
} x86_register_id_t;

/* <add-type id="x86_memory_or_io_t"> </add-type> */
typedef enum {
        X86_Memory,
        X86_IO
} x86_memory_or_io_t;

#define X86_REG_ID_RAX_BIT (1ULL << X86_Reg_Id_Rax)
#define X86_REG_ID_RCX_BIT (1ULL << X86_Reg_Id_Rcx)
#define X86_REG_ID_RDX_BIT (1ULL << X86_Reg_Id_Rdx)
#define X86_REG_ID_RBX_BIT (1ULL << X86_Reg_Id_Rbx)
#define X86_REG_ID_RSP_BIT (1ULL << X86_Reg_Id_Rsp)
#define X86_REG_ID_RBP_BIT (1ULL << X86_Reg_Id_Rbp)
#define X86_REG_ID_RSI_BIT (1ULL << X86_Reg_Id_Rsi)
#define X86_REG_ID_RDI_BIT (1ULL << X86_Reg_Id_Rdi)

#define X86_REG_ID_XMM0_BIT (1ULL << X86_Reg_Id_Xmm0)
#define X86_REG_ID_XMM1_BIT (1ULL << X86_Reg_Id_Xmm1)
#define X86_REG_ID_XMM2_BIT (1ULL << X86_Reg_Id_Xmm2)
#define X86_REG_ID_XMM3_BIT (1ULL << X86_Reg_Id_Xmm3)
#define X86_REG_ID_XMM4_BIT (1ULL << X86_Reg_Id_Xmm4)
#define X86_REG_ID_XMM5_BIT (1ULL << X86_Reg_Id_Xmm5)
#define X86_REG_ID_XMM6_BIT (1ULL << X86_Reg_Id_Xmm6)
#define X86_REG_ID_XMM7_BIT (1ULL << X86_Reg_Id_Xmm7)

#ifdef TARGET_X86_64
#define X86_REG_ID_R8_BIT  (1ULL << X86_Reg_Id_R8)
#define X86_REG_ID_R9_BIT  (1ULL << X86_Reg_Id_R9)
#define X86_REG_ID_R10_BIT (1ULL << X86_Reg_Id_R10)
#define X86_REG_ID_R11_BIT (1ULL << X86_Reg_Id_R11)
#define X86_REG_ID_R12_BIT (1ULL << X86_Reg_Id_R12)
#define X86_REG_ID_R13_BIT (1ULL << X86_Reg_Id_R13)
#define X86_REG_ID_R14_BIT (1ULL << X86_Reg_Id_R14)
#define X86_REG_ID_R15_BIT (1ULL << X86_Reg_Id_R15)

#define X86_REG_ID_XMM8_BIT  (1ULL << X86_Reg_Id_Xmm8)
#define X86_REG_ID_XMM9_BIT  (1ULL << X86_Reg_Id_Xmm9)
#define X86_REG_ID_XMM10_BIT (1ULL << X86_Reg_Id_Xmm10)
#define X86_REG_ID_XMM11_BIT (1ULL << X86_Reg_Id_Xmm11)
#define X86_REG_ID_XMM12_BIT (1ULL << X86_Reg_Id_Xmm12)
#define X86_REG_ID_XMM13_BIT (1ULL << X86_Reg_Id_Xmm13)
#define X86_REG_ID_XMM14_BIT (1ULL << X86_Reg_Id_Xmm14)
#define X86_REG_ID_XMM15_BIT (1ULL << X86_Reg_Id_Xmm15)
#endif /* defined(TARGET_X86_64) */

#define X86_REG_ID_MM0_BIT (1ULL << X86_Reg_Id_Mm0)
#define X86_REG_ID_MM1_BIT (1ULL << X86_Reg_Id_Mm1)
#define X86_REG_ID_MM2_BIT (1ULL << X86_Reg_Id_Mm2)
#define X86_REG_ID_MM3_BIT (1ULL << X86_Reg_Id_Mm3)
#define X86_REG_ID_MM4_BIT (1ULL << X86_Reg_Id_Mm4)
#define X86_REG_ID_MM5_BIT (1ULL << X86_Reg_Id_Mm5)
#define X86_REG_ID_MM6_BIT (1ULL << X86_Reg_Id_Mm6)
#define X86_REG_ID_MM7_BIT (1ULL << X86_Reg_Id_Mm7)

#define X86_REG_ID_PC_BIT (1ULL << X86_Reg_Id_PC)

#define X86_REG_ID_CF_BIT (1ULL << X86_Reg_Id_CF)
#define X86_REG_ID_DST_BIT (1ULL << X86_Reg_Id_DST)
#define X86_REG_ID_AF_BIT (1ULL << X86_Reg_Id_AF)
#define X86_REG_ID_ZF_BIT (1ULL << X86_Reg_Id_ZF)
#define X86_REG_ID_SF_BIT (1ULL << X86_Reg_Id_SF)
#define X86_REG_ID_OF_BIT (1ULL << X86_Reg_Id_OF)
#define X86_REG_ID_DF_BIT (1ULL << X86_Reg_Id_DF)

#define X86_REG_ID_EFLAGS_BIT (1ULL << X86_Reg_Id_EFLAGS)

#define X86_REG_ID_C0_BIT  (1ULL << X86_Reg_Id_C0)
#define X86_REG_ID_C1_BIT  (1ULL << X86_Reg_Id_C1)
#define X86_REG_ID_C2_BIT  (1ULL << X86_Reg_Id_C2)
#define X86_REG_ID_C3_BIT  (1ULL << X86_Reg_Id_C3)
#define X86_REG_ID_TOP_BIT (1ULL << X86_Reg_Id_Top)

#define REGISTER_ID_T

#define SIM_DI_PREFIX_F0_BIT           (1 << 0)
#define SIM_DI_PREFIX_F2_BIT           (1 << 1)
#define SIM_DI_PREFIX_F3_BIT           (1 << 2)
#define SIM_DI_PREFIX_CS_BIT           (1 << 3)
#define SIM_DI_PREFIX_SS_BIT           (1 << 4)
#define SIM_DI_PREFIX_DS_BIT           (1 << 5)
#define SIM_DI_PREFIX_ES_BIT           (1 << 6)
#define SIM_DI_PREFIX_FS_BIT           (1 << 7)
#define SIM_DI_PREFIX_GS_BIT           (1 << 8)
#define SIM_DI_PREFIX_OPERAND_SIZE_BIT (1 << 9)
#define SIM_DI_PREFIX_66_BIT           SIM_DI_PREFIX_OPERAND_SIZE_BIT
#define SIM_DI_PREFIX_ADDRESS_SIZE_BIT (1 << 10)
#define SIM_DI_PREFIX_SSE_BIT          (1 << 11)
#define SIM_DI_PREFIX_REX_BIT          (1 << 12)

#define SIM_DI_PREFIX_REX_POS          16
#define SIM_DI_PREFIX_REX_POS_B        16
#define SIM_DI_PREFIX_REX_POS_X        17
#define SIM_DI_PREFIX_REX_POS_R        18
#define SIM_DI_PREFIX_REX_POS_W        19

/* <add id="simics arch api types">
   <name index="true">x86_memory_transaction_t</name>
   <doc>
   <doc-item name="NAME">x86_memory_transaction_t, 
                    <idx>p2_memory_transaction_t</idx></doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="x86_memory_transaction_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">

   The <i>s</i> field contains generic information about memory
   operations (see <tt>generic_transaction_t</tt>).
   
   The <i>mode</i> is the current mode (user or supervisor) of the cpu.

   The <i>linear_address</i> contains the address for transactions
   with linear addresses.

   The <i>access_linear</i> flag is set for all transactions with
   linear addresses.

   The <i>access_type</i> field contains the type of the transaction.
   <ndx>x86_access_type_t</ndx>
   <smaller>
   <insert id="x86_access_type_t"/>
   </smaller>

   The effective memory type for the access is contained in
   <i>effective_type</i>. The MMU calculates the effective memory type
   using both the PAT type (in <i>pat_type</i>) and the MTRR type (in
   <i>mtrr_type</i>).
   <ndx>x86_memory_type_t</ndx>
   <smaller>
   <insert id="x86_memory_type_t"/>
   </smaller>
   </doc-item>
   </doc>

   </add> */

/* <add id="x86_memory_transaction_t def">
   <insert-until id="x86_and_p2_memory_transaction_t" 
                 text="// JDOCU INSERT-UNTIL x86_ and p2_memory_transaction_t"/>
   </add-type> 
*/
typedef struct x86_memory_transaction {
        generic_transaction_t s;                /* Superclass */
        processor_mode_t      mode;
        linear_address_t      linear_address;   
        uint16                selector;         /* Segment selector */
        unsigned              access_linear:1;  /* Linear access */
        unsigned              io:1;             /* I/O (port) access */
        unsigned              fault_as_if_write:1;
        x86_access_type_t     access_type;
        x86_memory_type_t     pat_type;
        x86_memory_type_t     mtrr_type;
        x86_memory_type_t     effective_type;
        int                   sequence_number; /* used for -stall */

        /* if non-zero, the id needed to calculate the program counter */
        intptr_t turbo_miss_id;
} x86_memory_transaction_t;

typedef struct x86_memory_transaction p2_memory_transaction_t;
// JDOCU INSERT-UNTIL x86_ and p2_memory_transaction_t

/* <add id="x86_tlb_interface_t">
   The x86 tlb interface is used for communication between an x86 cpu
   and its TLB. The TLB is implemented as a separate class for greater
   flexibility.

   <ndx>tagged_physical_address_t</ndx>
   <insert-until text="// ADD INTERFACE x86_tlb_interface"/>

   All functions in the interface get the <i>object</i> implementing
   the interface as their first parameter.

   <b>flush_all</b> is called when all TLB entries should be
   flushed. If <i>keep_global_entries</i> is set, then TLB entries
   with their global bit set should not be flushed.

   <b>flush_page</b> is invoked when pages containing <i>laddr</i> are
   to be removed from the TLB.

   <b>lookup</b> is used by the CPU when a memory access misses the
   STC. It must return true (non-zero) if and only if the memory
   operation specified by <i>mem_tr</i> hits the TLB and does not
   raise an exception. The <i>mode</i>, <i>linear_address</i> are valid when
   the method is invoked. The other fields passed through <i>mem_tr</i>
   are undefined. If the method returns true, the
   <i>s.physical_address</i>, <i>pat_type</i>, and <i>mtrr_type</i>
   fields of <i>mem_tr</i> must be updated by <b>lookup</b>.

   An access that misses in <b>lookup</b> but does not raise a fault
   is inserted into the TLB with <b>add</b>. The <i>page_size</i>
   encoding is 0 for 4 kb pages, 1 for 2 Mb pages, and 2 for 4 Mb
   pages.

   <b>itlb_lookup</b> is a simplified version of <b>lookup</b> used
   only for instruction TLB lookups. If the lookup is successful
   <i>valid</i> and <i>paddr</i> should be set, otherwise <i>valid</i>
   should be cleared.

   It class implementing the interface must make sure that only
   addresses mapped in the TLB are present in the STCs.

   This interface may be changed or replaced with an architecture
   independent interface in future versions of Simics.

   </add> */
typedef struct {
        int                  valid;
        physical_address_t   paddr;
} tagged_physical_address_t;

typedef struct {
        void (*flush_all)(conf_object_t *obj,
                            int keep_global_entries);
        void (*flush_page)(conf_object_t *obj,
                           linear_address_t laddr);
        int (*lookup)(conf_object_t *obj,
                      x86_memory_transaction_t *mem_tr);
        void (*add)(conf_object_t *obj,
                    processor_mode_t mode,
                    read_or_write_t read_or_write,
                    data_or_instr_t data_or_instr,
                    int global_page,
                    x86_memory_type_t pat_type,
                    x86_memory_type_t mtrr_type,
                    linear_address_t laddr,
                    physical_address_t paddr,
                    int page_size);
        tagged_physical_address_t (*itlb_lookup)(conf_object_t *obj,
                                                 linear_address_t laddr,
                                                 processor_mode_t mode);
} x86_tlb_interface_t;

#define X86_TLB_INTERFACE "x86-tlb"
// ADD INTERFACE x86_tlb_interface


/* <add-type id="x86_pin_t"> </add-type> */
typedef enum {
        Pin_Init,
        Pin_Smi,
        Pin_Nmi,
        Pin_Ignne
} x86_pin_t;

/* ADD INTERFACE x86_interface */

/* <add-type id="x86_interface_t">
   The x86 interface allows certain processor pins to be
   set/cleared. It is also used by the apic for the startup IPI.
   <ndx>x86_pin_t</ndx>
   <insert id="x86_pin_t"/>
   </add-type> */
typedef struct {
        void (*set_pin_status)(conf_object_t *obj, x86_pin_t pin, int status);
        void (*start_up)(conf_object_t *obj, uint32 start_address);
        int  (*interrupt_current_cpu)(int (*ack)(conf_object_t *), conf_object_t *data);
        void (*uninterrupt_current_cpu)(int (*ack)(conf_object_t *));
        int  (*has_pending_interrupt)(conf_object_t *obj);
        int  (*has_waiting_interrupt)(conf_object_t *obj);
        physical_address_t (*linear_to_physical)(processor_t *cpu_ptr, data_or_instr_t data_or_instr, linear_address_t address);
} x86_interface_t;

#define X86_INTERFACE "x86"

#endif /* _SIMICS_ARCH_X86_H */
