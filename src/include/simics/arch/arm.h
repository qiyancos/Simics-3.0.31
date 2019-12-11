/*
 * simics/arch/arm.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_ARCH_ARM_H
#define _SIMICS_ARCH_ARM_H

#ifndef TURBO_SIMICS

/* <add id="simics arch api types">
   <name index="true">arm_memory_transaction_t</name>
   <doc>
   <doc-item name="NAME">arm_memory_transaction_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="arm_memory_transaction_t def"/>
   </doc-item>
   <doc-item name="DESCRIPTION">

   This is the ARM specific memory transaction data structure.
   The generic data is stored in the <var>s</var> field.

   The <var>mode</var> field specifies the processor mode the MMU
   should assume when processing the transaction. This is the same as
   the current mode of the processor, except that it is always
   <const>Sim_CPU_Mode_User</const> for ldrbt, ldrt, strbt and strt
   instructions.

   </doc-item>
   </doc>
   </add>

   <add-type id="arm_memory_transaction_t def"></add-type>
*/
typedef struct arm_memory_transaction {

        /* generic transaction */
        generic_transaction_t s;

        /* processor mode */
        processor_mode_t mode;

        int rotate;

        /* if non-zero, the id needed to calculate the program counter */
        intptr_t turbo_miss_id;
} arm_memory_transaction_t;

/* <add id="arm_interface_t">
   This interface is implemented by ARM processors to provide various
   functionality that is specific for this class of processors.

   The <fun>read_register_mode</fun> and <fun>write_register_mode</fun>
   functions are used to access banked copies of the registers. They are used
   just like the <fun>SIM_read_register</fun> and <fun>SIM_write_register</fun>
   functions, except that they take an extra parameter <param>mode</param> that
   specifies which register bank should be used. <param>mode</param> should be
   the mode bits in the cpsr corresponding to the mode shifted right to bits
   0-4.

   <insert-until text="// END INTERFACE arm"/>
   </add> */



typedef struct arm_interface {
        uinteger_t (*read_register_mode)(conf_object_t *processor_obj,
                                         int reg_num,
                                         int mode);
        void (*write_register_mode)(conf_object_t *processor_obj,
                                    int reg_num,
                                    int mode,
                                    uinteger_t value);
} arm_interface_t;

#define ARM_INTERFACE "arm"

#define ARM_INT_IRQ 0 /* Used by simple-interrupt to raise an IRQ */
#define ARM_INT_FIQ 1 /* Used by simple-interrupt to raise an FIQ */

// END INTERFACE arm

/* <add id="arm_coprocessor_interfacce_t">

   A coprocessor for the ARM has to provide the
   arm_coprocessor_interface. This interface
   defines the functions that will be called when
   the coprocessor instructions (cdp, ldc, mcr, mrc, stc)
   are executed.

   The interface also defines a flag, finished, which indicates
   whether a memory transfer operation is finished or not.

   The function reset is called when the cpu is reset,
   and allows the coprocessor to also do a reset,
   the argument hard_reset indicates whether the reset
   was soft (0) or hard (1).

   </add> */
typedef struct {
        void (*process_data)(conf_object_t *obj,
                               uint32 CRd,
                               uint32 opcode_1,
                               uint32 CRn,
                               uint32 CRm,
                               uint32 opcode_2,
                               int type);
        void (*load_coprocessor)(conf_object_t *obj,
                               uint32 CRd,
                               uint32 N,
                               uint32 Options,
                               uint32 value,
                               int type);

        uint32  (*read_register)(conf_object_t *obj,
                                 uint32 opcode_1,
                                 uint32 CRn,
                                 uint32 CRm,
                                 uint32 opcode_2,
                                 int type);
        void (*write_register)(conf_object_t *obj,
                               uint32 value,
                               uint32 opcode_1,
                               uint32 CRn,
                               uint32 CRm,
                               uint32 opcode_2,
                               int type);
        uint32 (*store_coprocessor)(conf_object_t *obj,
                               uint32 CRd,
                               uint32 N,
                               uint32 Options,
                               int type);
        void (*reset)(conf_object_t *obj, int hard_reset);

        uint32 finished;
} arm_coprocessor_interface_t;

#define ARM_COPROCESSOR_INTERFACE "arm_coprocessor"
// ADD INTERFACE arm_coprocessor_interface

#endif /* TURBO_SIMICS */

#endif /* _SIMICS_ARCH_ARM_H */
