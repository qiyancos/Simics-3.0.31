/*
 * simics/arch/ppc.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_ARCH_PPC_H
#define _SIMICS_ARCH_PPC_H

#include <simics/core/types.h>
#include <simics/core/generic-spr.h>

/* Possible machine check exceptions */

/* <add-type id="ppc_mc_exc_t type"><ndx>ppc_mc_exc_t</ndx></add-type> */
typedef enum {
        Sim_PPC_Generic_MC,

        Sim_PPC_MC_TEA,
        Sim_PPC_MC_MCP,
        Sim_PPC_Bus_Address_Parity,
        Sim_PPC_Bus_Data_Parity,
        Sim_PPC_Instruction_Cache_Parity,
        Sim_PPC_Data_Cache_Parity,
        Sim_PPC_L2_Data_Parity,
        Sim_PPC_L3_Data_Parity,
        Sim_PPC_L3_Address_Parity,
        
        Sim_PPC970_Data_Cache_Parity,
        Sim_PPC970_Data_Cache_Tag_Parity,
        Sim_PPC970_D_ERAT_Parity,
        Sim_PPC970_TLB_Parity,
        Sim_PPC970_SLB_Parity,
        Sim_PPC970_L2_Load_ECC_Parity,
        Sim_PPC970_L2_Page_Table_ECC_Parity,
        Sim_PPC970_Uncacheable_Load_Parity,
        Sim_PPC970_MC_External
} ppc_mc_exc_t;

/*
   <add id="simics arch api types">
   <name index="true">ppc_mem_instr_origin_t</name>
   <doc>
   <doc-item name="NAME">ppc_mem_instr_origin_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="ppc_mem_instr_origin_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   List of special memory operations that can be send by a PPC processor.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="ppc_mem_instr_origin_t def"></add-type> */
typedef enum {
        /* Normal load or store instructions */
        Normal_Load_Store = 0,

        /* No data touched by the load/store will be placed in cache */
	Caching_Inhibited,

        Instr_Multiple,         /* load/store multiple */
        Instr_String,           /* load/store string */

        Instr_Altivec_Element,  /* Altivec load/store element */

        /* Data cache manipulations */
        Instr_dcbt,             /* data cache block touch */
        Instr_dcbst,            /* data cache block store */
        Instr_dcbtst,           /* data cache block touch for store */
        Instr_dcbi,             /* data cache block invalidate */
        Instr_dcbf,             /* data cache block flush */
        Instr_dcbfl,            /* data cache block flush local */
        Instr_dcba,             /* data cache block allocate */
        Instr_dcbz,             /* data cache block to zero */
        
        /* Instruction cache manipulations */
        Instr_icbi,             /* instruction cache block invalidate */
        
        /* Data stream (Altivec) manipulations */
        Instr_dst,              /* data stream touch */
        Instr_dstt,             /* data stream touch transient */
        Instr_dstst,            /* data stream touch for store */
        Instr_dststt,           /* data stream touch for store transient */

        /* e500 cache lock apu instructions */
        Instr_dcblc_l1,         /* data cache block lock clear (L1) */
        Instr_dcblc_l2,         /* data cache block lock clear (L2) */
        Instr_dcbtls_l1,        /* data cache block touch and lock set (L1)*/
        Instr_dcbtls_l2,        /* data cache block touch and lock set (L1)*/
        Instr_dcbtstls_l1,      /* data cache block touch for store and lock
                                   set (L1)*/
        Instr_dcbtstls_l2,      /* data cache block touch for store and lock
                                   set (L1)*/
        Instr_icblc_l1,         /* instruction cache block clear (L1) */
        Instr_icblc_l2,         /* instruction cache block clear (L2) */
        Instr_icbtls_l1,        /* instruction cache block touch and lock
                                   set (L1) */
        Instr_icbtls_l2,        /* instruction cache block touch and lock
                                   set (L1) */

        /* Other loads/stores or cache affecting instructions */
        Instr_lwarx,
        Instr_stwcx,
        Instr_ldarx,
        Instr_stdcx,
        Instr_lq,
        Instr_stq,

        /* Other cache affecting instructions */
        Instr_sync,
        Instr_eieio,
        Instr_ecowx,
        Instr_eciwx,
        Instr_tlbie,
        Instr_tlbsync,
        Instr_isync,

        Instr_lfdp,             /* Load Floating point Double Pair */
        Instr_stfdp             /* Store Floating point Double Pair */
} ppc_mem_instr_origin_t;

#ifndef TURBO_SIMICS
  
/*
   <add id="simics arch api types">
   <name index="true">ppc_memory_transaction_t</name>
   <doc>
   <doc-item name="NAME">ppc_memory_transaction_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="ppc_memory_transaction_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">

   This is the PPC specific memory transaction data structure.
   The generic data is stored in the <var>s</var> field.

   The current processor mode when generating this transaction is stored in the
   <var>mode</var> field.

   The type of instruction generating the memory transactions is provided by
   the <var>instr_origin</var> field. Note that it is mainly provided for
   special memory accesses like cache block operations..

   The <var>wimg</var> field is filled in by the MMU with the corresponding
   WIMG bits during the translation.

   The <var>alignment</var> field contains the size on which the transaction is
   required to be aligned.

   The <var>inhibit_exception</var> field is set for operations that should be
   ignored if triggering an exception.

   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="ppc_memory_transaction_t def">
   </add-type>
*/
typedef struct ppc_memory_transaction {

        /* generic transaction */
        generic_transaction_t s;

        processor_mode_t mode;
        ppc_mem_instr_origin_t instr_origin;
        logical_address_t ea_origin;
	uint8 wimg;
        uint8 alignment;

        /* cache operations may flag this to cause prefetches to be no-ops */
        uint8 inhibit_exception;

        intptr_t turbo_miss_id;
} ppc_memory_transaction_t;

/* redefined for compatibility */
typedef gen_spr_user_setter_func_t ppc_spr_user_setter_func_t;
typedef gen_spr_user_getter_func_t ppc_spr_user_getter_func_t;
typedef gen_spr_ret_t ppc_spr_ret_t;
typedef gen_spr_access_type_t ppc_spr_access_type_t;

/* <add id="ppc_interface_t">
   <insert-until text="// ADD INTERFACE ppc_interface"/>

   The <fun>clear_atomic_reservation_bit()</fun> function clears the
   reservation bit which is set by an <tt>lwarx</tt> instruction.  Clearing the
   reservation will cause a following <tt>stwcx.</tt> instruction to fail.
   This function is typically used by a cache hierarchy supporting SMP.

   The <fun>raise_machine_check_exception()</fun> function raises a machine
   check exception. The <param>exc</param> argument is of the following type:

   <insert id="ppc_mc_exc_t type"/>

   The <fun>register_spr_user_handlers</fun> function will register user
   implemented get and set functions that will be called every time a
   read or write access is made to the SPR with number <param>spr</param>.
   The <param>getter</param> and <param>setter</param> function is of the
   following type:

   <insert id="ppc_spr_user_getter_func_t type"/>

   The <param>type</param> parameter in the get and set functions is one of
   the following, depending on where from the access originated:

   <insert id="ppc_spr_access_type_t def"/>

   Both the get and the set functions must return one of these enum values:

   <insert id="ppc_spr_ret_t def"/>

   If <param>privilege_checks</param> is not zero, Simics will do privilege
   checks when a mfspr/mtspr instruction is executed. If this does not produce
   the desired results, you can register the SPR handlers with
   <param>privilege_checks</param> set to zero, and do you own checks in your
   handlers.

   The functions <fun>unregister_spr_user_handlers</fun> will remove any
   registered user handlers for a particular SPR.

   The function <fun>spr_set_target_value</fun> should be called from the get
   function. The <param>value</param> will be written to the target register
   for instruction accesses, and returned for attribute and int register
   interface accesses. If this function is not called, the target register is
   not changed for instruction accesses (and the mfspr thus acts as a nop).

   The functions <fun>spr_stash_value</fun> and <fun>spr_fetch_value</fun> can
   be used to store a SPR value in the processor. This is useful if only the
   getter (or only the setter) has been overridden with a user handler.

   Sometimes it may be desirable to let the processor take care of the access.
   The functions <fun>spr_default_getter</fun> and
   <fun>spr_default_setter</fun> exist for this purpose.

   The function <fun>spr_get_name</fun> takes <param>spr_number</param>
   as parameter and returns the name of the SPR.

   The function <fun>spr_get_number</fun> takes the <param>spr_name</param>
   and returns the SPR number.

   Note that the following registers cannot be overridden with user handlers:
   <em>xer</em>, <em>lr</em> and <em>ctr</em>.

   </add>
 */
typedef struct {
        void (*clear_atomic_reservation_bit)(conf_object_t *cpu);
        void (*raise_machine_check_exception)(conf_object_t *cpu,
                                              ppc_mc_exc_t exc);
        void (*register_spr_user_handlers)(integer_t spr_number,
                                           ppc_spr_user_getter_func_t getter,
                                           lang_void *user_getter_data,
                                           ppc_spr_user_setter_func_t setter,
                                           lang_void *user_setter_data,
                                           int privilege_checks);
        void (*unregister_spr_user_handlers)(integer_t spr_number);
        void (*spr_set_target_value)(conf_object_t *cpu, uinteger_t value);
        void (*spr_stash_value)(conf_object_t *cpu, integer_t spr_number,
                                uinteger_t value);
        uinteger_t (*spr_fetch_value)(conf_object_t *cpu,
                                      integer_t spr_number);
        ppc_spr_ret_t (*spr_default_getter)(conf_object_t *cpu,
                                            integer_t spr_number,
                                            ppc_spr_access_type_t type);
        ppc_spr_ret_t (*spr_default_setter)(conf_object_t *cpu,
                                            integer_t spr_number,
                                            uinteger_t value,
                                            ppc_spr_access_type_t type);
        const char* (*spr_get_name)(integer_t spr_number);
        integer_t (*spr_get_number)(const char *spr_name);
} ppc_interface_t;

#define PPC_INTERFACE "ppc"
// ADD INTERFACE ppc_interface

#endif /* TURBO_SIMICS */

#define PBIT4(n) (0x8U >> (n))
#define PBIT5(n) (0x10U >> (n))
#define PBIT8(n) (0x80U >> (n))
#define PBIT32(n) (0x80000000U >> (n))
#define PBIT64(n) (UINT64_C(0x8000000000000000) >> (n))

#define PGETBIT32(var, n) (((var) >> (31 - (n))) & 1)
#define PGETBIT36(var, n) (((var) >> (35 - (n))) & 1)
#define PGETBIT40(var, n) (((var) >> (39 - (n))) & 1)
#define PGETBIT53(var, n) (((var) >> (52 - (n))) & 1)
#define PGETBIT64(var, n) (((var) >> (63 - (n))) & 1)

#define PHASBIT32(var, n) ((var) & PBIT32(n))
#define PHASBIT64(var, n) ((var) & PBIT64(n))

#define PSETBIT32(var, n) do {                  \
	(var) |= PBIT32(n);                     \
} while (0)
#define PCLEARBIT32(var, n) do {		\
	(var) &= ~PBIT32(n);			\
} while (0)

#define PSETBIT32V(var, n)                      \
	((var) | PBIT32(n))
#define PSETBIT64V(var, n)                      \
        ((var) | PBIT64(n))

#define PCLEARBIT32V(var, n)                    \
	((var) & ~PBIT32(n))
#define PCLEARBIT64V(var, n)                    \
        ((var) & ~PBIT64(n))

#define PMASK32(n, w)                           \
	(((PBIT32(0) >> (n)) << 1)              \
         - ((PBIT32(0) >> (n)) >> ((w) - 1)))

#define PMASK64(n, w)                           \
	(((PBIT64(0) >> (n)) << 1)              \
         - ((PBIT64(0) >> (n)) >> ((w) - 1)))

#define PGETF16(val, n, w) (((val) >> (16 - (n) - (w))) & ((1 << (w)) - 1))
#define PGETF19(val, n, w) (((val) >> (19 - (n) - (w))) & ((1 << (w)) - 1))
#define PGETF32(val, n, w) (((val) >> (32 - (n) - (w))) & ((1 << (w)) - 1))
#define PGETF36(val, n, w) (((val) >> (36 - (n) - (w))) & ((1 << (w)) - 1))

#define PGETF39(val, n, w) \
        (((val) >> (39 - (n) - (w))) & (((uint64)1 << (w)) - 1))
#define PGETF40(val, n, w) \
        (((val) >> (40 - (n) - (w))) & (((uint64)1 << (w)) - 1))
#define PGETF52(val, n, w) \
        (((val) >> (52 - (n) - (w))) & (((uint64)1 << (w)) - 1))
#define PGETF53(val, n, w) \
        (((val) >> (53 - (n) - (w))) & (((uint64)1 << (w)) - 1))
#define PGETF64(val, n, w) \
        (((val) >> (64 - (n) - (w))) & (((uint64)1 << (w)) - 1))

#define PSETF32(var, n, w, val) do {                            \
	(var) = (((var) & ~PMASK32(n, w))                       \
                 | ((uint32)(val) << (32 - (n) - (w))));        \
} while (0)

#define PSETF32_SPEC(var_d, var_s, n, w, val) do {      \
	var_d(((var_s()) & ~PMASK32(n, w))              \
              | ((uint32)(val) << (32 - (n) - (w))));   \
} while (0)

#define PSETF64(var, n, w, val) do {                            \
	(var) = (((var) & ~PMASK64(n, w))                       \
                 | ((uint64)(val) << (64 - (n) - (w))));        \
} while (0)

#define PSETF32V(var, n, w, val) \
	(((var) & ~PMASK32(n, w)) | ((uint32)(val) << (32 - (n) - (w))))
#define PSETF64V(var, n, w, val) \
	(((var) & ~PMASK64(n, w)) | ((uint64)(val) << (64 - (n) - (w))))

#define PMAKEF32(n, w, val) \
	((uint32)(val) << (32 - (n) - (w)))
#define PMAKEF64(n, w, val) \
	((uint64)(val) << (64 - (n) - (w)))

#endif /* _SIMICS_ARCH_PPC_H */
