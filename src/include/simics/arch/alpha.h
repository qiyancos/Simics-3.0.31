/*
 * simics/arch/alpha.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_ARCH_ALPHA_H
#define _SIMICS_ARCH_ALPHA_H

#define ALPHA_IPR_ARRAY_SIZE   0x118                    /* the number of processor registers   */
#define ALPHA_SHADOW_ARRAY_SIZE 8
#define IPR_INDEX_BASE   0x100                    /* the offset to the first IPR index   */


/* internal processor registers (IPRs) */
#define EV5_ISR            0x100
#define EV5_ITB_TAG        0x101
#define EV5_ITB_PTE        0x102
#define EV5_ITB_ASN        0x103
#define EV5_ITB_PTE_TEMP   0x104
#define EV5_ITB_IA         0x105
#define EV5_ITB_IAP        0x106
#define EV5_ITB_IS         0x107
#define EV5_SIRR           0x108
#define EV5_ASTRR          0x109
#define EV5_ASTER          0x10A
#define EV5_EXC_ADDR       0x10B
#define EV5_EXC_SUM        0x10C
#define EV5_EXC_MASK       0x10D
#define EV5_PAL_BASE       0x10E
#define EV5_ICM            0x10F
#define EV5_IPLR           0x110
#define EV5_INTID          0x111
#define EV5_IFAULT_VA_FORM 0x112
#define EV5_IVPTBR         0x113
#define EV5_HWINT_CLR      0x115
#define EV5_SL_XMIT        0x116
#define EV5_SL_RCV         0x117
#define EV5_ICSR           0x118
#define EV5_IC_FLUSH_CTL   0x119
#define EV5_ICPERR_STAT    0x11A
#define EV5_PMCTR          0x11C

#define EV5_PALtemp0       0x140
#define EV5_PALtemp1       0x141
#define EV5_PALtemp2       0x142
#define EV5_PALtemp3       0x143
#define EV5_PALtemp4       0x144
#define EV5_PALtemp5       0x145
#define EV5_PALtemp6       0x146
#define EV5_PALtemp7       0x147
#define EV5_PALtemp8       0x148
#define EV5_PALtemp9       0x149
#define EV5_PALtemp10      0x14A
#define EV5_PALtemp11      0x14B
#define EV5_PALtemp12      0x14C
#define EV5_PALtemp13      0x14D
#define EV5_PALtemp14      0x14E
#define EV5_PALtemp15      0x14F
#define EV5_PALtemp16      0x150
#define EV5_PALtemp17      0x151
#define EV5_PALtemp18      0x152
#define EV5_PALtemp19      0x153
#define EV5_PALtemp20      0x154
#define EV5_PALtemp21      0x155
#define EV5_PALtemp22      0x156
#define EV5_PALtemp23      0x157

#define EV5_DTB_ASN        0x200
#define EV5_DTB_CM         0x201
#define EV5_DTB_TAG        0x202
#define EV5_DTB_PTE        0x203
#define EV5_DTB_PTE_TEMP   0x204
#define EV5_MM_STAT        0x205
#define EV5_VA             0x206
#define EV5_VA_FORM        0x207
#define EV5_MVPTBR         0x208
#define EV5_DTB_IAP        0x209
#define EV5_DTB_IA         0x20A
#define EV5_DTB_IS         0x20B
#define EV5_ALT_MODE       0x20C
#define EV5_CC             0x20D
#define EV5_CC_CTL         0x20E
#define EV5_MCSR           0x20F
#define EV5_DC_FLUSH       0x210
#define EV5_DC_PERR_STAT   0x212
#define EV5_DC_TEST_CTL    0x213
#define EV5_DC_TEST_TAG    0x214
#define EV5_DC_TEST_TAG_TEMP 0x215
#define EV5_DC_MODE        0x216
#define EV5_MAF_MODE       0x217


#define EXTERNAL_IRQ_0 0x100000ULL                /* corrected system errors             */
#define EXTERNAL_IRQ_1 0x200000ULL                /* PCI and ISA interrupts              */
#define EXTERNAL_IRQ_2 0x400000ULL                /* interprocessor and timer            */
#define EXTERNAL_IRQ_3 0x800000ULL                /* reserved                            */

/* <add id="simics arch api types">
   <name index="true">palcode_memop_flags_t</name>
   <doc>
   <doc-item name="NAME">palcode_memop_flags_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="palcode_memop_flags_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   PALcode uses hw_ld and hw_st instructions to access memory outside
   of the realm of normal Alpha memory management. These flags are
   used in such operations. 
   </doc-item>
   </doc>
   </add>

   <add-type id="palcode_memop_flags_t def">
   </add-type>
   */
typedef enum palcode_memop_flags {
        
        /* nothing special */
        Pal_memop_normal   = 0x0000,

        /* cleared: the effective address is virtual
           set:     the effective address is physical */
        Pal_memop_physical = 0x0001, 
        
        /* cleared: use current mode for access checks
           set:     use alt mode for access checks */
        Pal_memop_altmode  = 0x0002,    

        /* cleared: check fault-on-read (FOR) and read access violations
           set:     check FOR, fault-on-write and read/write violations */
        Pal_memop_wrtck    = 0x0004,

        /* cleared: length is longword
           set:     length is quadword */
        Pal_memop_quadword = 0x0008,

        /* cleared: normal fetch
           set:     flags a virtual pte fetch */
        Pal_memop_vpte     = 0x0010,

        /* cleared:  normal operation
           set:      load-locked version of hw_ld */
        Pal_memop_lock     = 0x0020,

        /* cleared:  normal operation
           set:      store-conditional version of hw_st */
        Pal_memop_cond     = 0x0040

} palcode_memop_flags_t;

/* memory transaction specific to the alpha architecture */

/* <add id="simics arch api types">
   <name index="true">alpha_memory_transaction_t</name>
   <doc>
   <doc-item name="NAME">alpha_memory_transaction_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="alpha_memory_transaction_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">

   The <i>s</i> field contains generic information about memory operations (see
   <tt>generic_transaction_t</tt>).  The <i>mode</i> is the current mode of the
   alpha cpu.  The values of <i>palcode_flags</i>, used by hw_ld and hw_st
   instructions, see <type>palcode_memop_flags_t</type> datatype.

   </doc-item>
   </doc>

   </add>
*/

/* <add-type id="alpha_memory_transaction_t def"></add-type> */
typedef struct alpha_memory_transaction {

        /* generic transaction */
        generic_transaction_t s;

        /* mode of the current alpha cpu */
        int mode;

        /* flags used by hw_ld / hw_st instructions */
        palcode_memop_flags_t palcode_flags;

        /* The pte is needed the Icache module, since it needs the ASM bit. */
        uint64 pte;

        /* if non-zero, the id needed to calculate the program counter */
        intptr_t turbo_miss_id;
} alpha_memory_transaction_t;

/* <add id="simics arch api types">
   <name index="true">alpha_cpu_mode_t</name>
   <doc>
   <doc-item name="NAME">alpha_cpu_mode_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller><insert id="alpha_cpu_mode_t def"/>
   </smaller></doc-item>
   <doc-item name="DESCRIPTION">
   The <type>alpha_cpu_mode_t</type> corresponds to the <i>current
   mode (CM)</i> field of the processor status register.
   </doc-item>
   </doc>
   </add> */

/* <add-type id="alpha_cpu_mode_t def">
   </add-type>
 */
typedef enum {
        Sim_Alpha_Mode_Kernel     = 0,
        Sim_Alpha_Mode_Executive  = 1,
        Sim_Alpha_Mode_Supervisor = 2,
        Sim_Alpha_Mode_User       = 3
} alpha_cpu_mode_t;


/* <add id="alpha_interface_t">
   Alpha specific functions.

   This interface is implemented by ALpha processors to provide
   various functionality that is specific for this class of processors.

   The <fun>read_fp_register</fun> functions are used to read the floating
   point register in a processor. The The <tt>_x</tt> version uses double-
   precision (64bit) with integer representation, the and the <tt>_d</tt>
   version uses double-precision and double float representation.

   <fun>load_rom</fun> loads a ROM image into memory and intialize the PC
   and PAL base to the entry point as specified by the ROM header. Information
   extracted from the ROM header is written to standard output if the verbose
   flag is set.

   <fun>number_of_iprs</fun> returns the number of internal processor registers.

   <fun>ipr_index</fun> is used to look up the index number of the internal
   processor register with name <tt>name</tt>. The number of the ipr is returned
   or -1 if not found.

   <fun>ipr_number_to_index</fun> is used to look up the index number of internal
   processor register number <tt>number</tt>. N.b., Simics internally uses indices
   and not ipr numbers to identify IPRs.

   <fun>ipr_name</fun> returns the name of the internal processor register with
   index number <tt>index</tt>.

   <fun>ipr_description</fun> returns a short descrption of the internal processor
   register with index number <tt>index</tt>.

   <fun>write_ipr</fun> writes an integer value to an internal processor register (IPR).
   The register is specified with an index, and the index must represent a valid IPR.
   Writing a register with this function does not have any side effects,
   i.e. only the register contents itself is altered.

   <fun>read_ipr</fun> reads an integer value from an internal processor register (IPR).
   The register is specified with an index, and the index must represent a valid IPR.
   Reading a register with this function does not have any side effects,
   no simulator state is altered.

   <insert-until text="// ADD INTERFACE alpha_interface"/>
   </add>
*/

typedef struct alpha_interface {
        uint64 (*read_fp_register_x)(conf_object_t *cpu, int reg);
        double (*read_fp_register_d)(conf_object_t *cpu, int reg);
        
        void (*load_rom)(conf_object_t *cpu, const char *file_name, int64 address, int verbose_flag);
        
        int (*number_of_iprs)(conf_object_t *cpu);
        int (*ipr_index)(conf_object_t *cpu, const char *name);
        int (*ipr_number_to_index)(conf_object_t *cpu, int number);
        const char *(*ipr_name)(conf_object_t *cpu, int index);
        const char *(*ipr_description)(conf_object_t *cpu, int index);
        uint64 (*read_ipr)(conf_object_t *cpu, int index);
        void (*write_ipr)(conf_object_t *cpu, int index, uint64 value);

} alpha_interface_t;

#define ALPHA_INTERFACE "alpha"
// ADD INTERFACE alpha_interface

#endif /* _SIMICS_ARCH_ALPHA_H */
