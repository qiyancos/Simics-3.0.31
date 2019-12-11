/*
 * simics/arch/ia64.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_ARCH_IA64_H
#define _SIMICS_ARCH_IA64_H

#define IA64_NUM_INTERRUPTIONS 81

/* This is a classification of interruptions. */

/*
   <add id="simics arch api types">
   <name index="true">ia64_interruption_type_t</name>
   <doc>
   <doc-item name="NAME">ia64_interruption_type_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="ia64_interruption_type_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   Defines the different type of interruptions in the IA-64 architecture.
   </doc-item>
   </doc>
   </add>
   
   <add-type id="ia64_interruption_type_t def"></add-type> */
typedef enum {
        IT_abort,
        IT_interrupt,
        IT_fault,
        IT_trap
} ia64_interruption_type_t;

/*
   <add id="simics arch api types">
   <name index="true">ia64_interruption_t</name>
   <doc>
   <doc-item name="NAME">ia64_interruption_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="ia64_interruption_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   These are the interruptions that can occur in an ia64 processor.
   The numbers correspond to the numbers given by the Intel
   architecture manuals.  They are, among other things, used by the
   Core_Exception hap.
   </doc-item>
   </doc>
   </add>
   
   <add-type id="ia64_interruption_t def"></add-type> */
typedef enum {
        IA64_Abort_RESET = 1,
        IA64_Abort_MCA,
        IA64_Int_INIT,
        IA64_Int_PMI,
        IA64_Int_INT,
        IA64_Fault_IR_unimplmented_data_address,
        IA64_Fault_IR_data_nested_tlb,
        IA64_Fault_IR_alternate_data_tlb,
        IA64_Fault_IR_vhpt_data,
        IA64_Fault_IR_data_tlb,
        IA64_Fault_IR_data_page_not_present,
        IA64_Fault_IR_data_nat_page_consumption,
        IA64_Fault_IR_data_key_miss,
        IA64_Fault_IR_data_key_permission,
        IA64_Fault_IR_data_access_rights,
        IA64_Fault_IR_data_access_bit,
        IA64_Fault_IR_data_debug,
        IA64_Fault_IA32_instruction_breakpoint,
        IA64_Fault_IA32_code_fetch,
        IA64_Fault_alternate_instruction_tlb,
        IA64_Fault_vhpt_instruction,
        IA64_Fault_instruction_tlb,
        IA64_Fault_instruction_page_not_present,
        IA64_Fault_instruction_nat_page_consumption,
        IA64_Fault_instruction_key_miss,
        IA64_Fault_instruction_key_permission,
        IA64_Fault_instruction_access_rights,
        IA64_Fault_instruction_access_bit,
        IA64_Fault_instruction_debug,
        IA64_Fault_IA32_instruction_length,
        IA64_Fault_IA32_invalid_opcode,
        IA64_Fault_IA32_instruction_intercept,
        IA64_Fault_illegal_operation,
        IA64_Fault_illegal_dependency,
        IA64_Fault_break_instruction,
        IA64_Fault_privileged_operation,
        IA64_Fault_disabled_floating_point_register,
        IA64_Fault_diabled_instruction_set_transition,
        IA64_Fault_IA32_device_not_available,
        IA64_Fault_IA32_fp_error,
        IA64_Fault_register_nat_consumption,
        IA64_Fault_reserved_register_field,
        IA64_Fault_unimplemented_data_address,
        IA64_Fault_privileged_register,
        IA64_Fault_speculative_operation,
        IA64_Fault_IA32_stack_exception,
        IA64_Fault_IA32_general_protection,
        IA64_Fault_data_nested_tlb,
        IA64_Fault_alternate_data_tlb,
        IA64_Fault_vhpt_data,
        IA64_Fault_data_tlb,
        IA64_Fault_data_page_not_present,
        IA64_Fault_data_nat_page_consumption,
        IA64_Fault_data_key_miss,
        IA64_Fault_data_key_permission,
        IA64_Fault_data_access_rights,
        IA64_Fault_data_dirty_bit,
        IA64_Fault_data_access_bit,
        IA64_Fault_data_debug,
        IA64_Fault_unaligned_data_reference,
        IA64_Fault_IA32_alignment_check,
        IA64_Fault_IA32_locked_data_reference,
        IA64_Fault_IA32_segment_not_present,
        IA64_Fault_IA32_divide_by_zero,
        IA64_Fault_IA32_bound,
        IA64_Fault_IA32_sse_numeric_error,
        IA64_Fault_unsupported_data_reference,
        IA64_Fault_floating_point,
        IA64_Trap_unimplemented_instruction_address,
        IA64_Trap_floating_point,
        IA64_Trap_lower_privilege_transfer,
        IA64_Trap_taken_branch,
        IA64_Trap_single_step,
        IA64_Trap_IA32_system_flag_intercept,
        IA64_Trap_IA32_gate_intercept,
        IA64_Trap_IA32_into,
        IA64_Trap_IA32_breakpoint,
        IA64_Trap_IA32_software_interrupt,
        IA64_Trap_IA32_data_breakpoint,
        IA64_Trap_IA32_taken_branch,
        IA64_Trap_IA32_single_step
} ia64_interruption_t;

/*
   <add id="simics arch api types">
   <name index="true">ia64_iva_offset_t</name>
   <doc>
   <doc-item name="NAME">ia64_iva_offset_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="ia64_iva_offset_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   The location of the Interruption Vector Table (IVT) is stored in
   the <tt>cr.iva</tt> control register.  These constants describe the offsets
   of the different vectors in the table.
   </doc-item>
   </doc>
   </add>

   <add-type id="ia64_iva_offset_t def"></add-type> */
typedef enum {
        IVA_vhpt_trans      = 0x0000,
        IVA_instr_tlb       = 0x0400,
        IVA_data_tlb        = 0x0800,
        IVA_alt_instr_tlb   = 0x0c00,
        IVA_alt_data_tlb    = 0x1000,
        IVA_data_nested     = 0x1400,
        IVA_instr_key_miss  = 0x1800,
        IVA_data_key_miss   = 0x1c00,
        IVA_dirty_bit       = 0x2000,
        IVA_instr_acc_bit   = 0x2400,
        IVA_data_acc_bit    = 0x2800,
        IVA_break           = 0x2c00,
        IVA_ext_int         = 0x3000,
        IVA_page_not_pres   = 0x5000,
        IVA_key_perm        = 0x5100,
        IVA_instr_acc_right = 0x5200,
        IVA_data_acc_right  = 0x5300,
        IVA_gen_exc         = 0x5400,
        IVA_dis_fp          = 0x5500,
        IVA_nat_cons        = 0x5600,
        IVA_spec            = 0x5700,
        IVA_debug           = 0x5900,
        IVA_unal_ref        = 0x5a00,
        IVA_unsup_data_ref  = 0x5b00,
        IVA_fp              = 0x5c00,
        IVA_fp_trap         = 0x5d00,
        IVA_lp_trans_trap   = 0x5e00,
        IVA_tak_br_trap     = 0x5f00,
        IVA_ss_trap         = 0x6000,
        IVA_ia32_exc        = 0x6900,
        IVA_ia32_intercept  = 0x6a00,
        IVA_ia32_interrupt  = 0x9b00
} ia64_iva_offset_t;

/* <add id="simics arch api types">
   <name index="true">ia64_memory_transaction_t</name>
   <doc>
   <doc-item name="NAME">ia64_memory_transaction_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="ia64_memory_transaction_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   The <i>s</i> field contains generic information about memory
   operations (see <tt>generic_transaction_t</tt>).
   
   The <i>privilege_level</i> is the current privilege level (0-3) of the cpu.

   The <i>speculative</i> flag indicates that the memory operation is
   caused by control speculation.

   The <i>advanced</i> flag indicates an advanced load, i.e. that the
   memory operation is caused by data speculation.

   The <i>isr_code</i> is used to help the MMU fill in the correct
   values in the cr.isr register on a fault.

   The <i>rse</i> flag indicates that the memory operation is caused
   by a mandatory RSE operation, and the <i>rse_ir</i> whether the
   current frame is incomplete.  This is used to raise the appropriate
   faults on failure.

   The <i>deferred_fault</i> is set by the MMU when a speculative
   memory operation fails.

   </doc-item>
   </doc>
   </add> */

/* <add-type id="ia64_memory_transaction_t def">
   </add-type> 
*/
typedef struct ia64_memory_transaction {

        /* generic transaction */
        generic_transaction_t s;

        int privilege_level;
        int speculative;
        int advanced;
        int non_access;
        uint16 isr_code;

        int rse;
        int rse_ir;

        /* "Output" */
        int deferred_fault;
} ia64_memory_transaction_t;

/* <add id="simics arch api types">
   <name index="true">ia64_fp_register_t</name>
   <doc>
   <doc-item name="NAME">ia64_fp_register_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="ia64_fp_register_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   Representation of an IA64 floating-point register.
   </doc-item>
   </doc>
   </add>

   <add-type id="ia64_fp_register_t def">
   </add-type>
   */
typedef struct ia64_fp_register {
        uint64   significand;
        uint32   exponent;
        unsigned sign:1;
        unsigned nat:1;
} ia64_fp_register_t;

/* <add id="ia64_interface_t">
   IA-64 specific functions.

   This interface is implemented by IA-64 processors to provide
   various functionality that is specific for this class of processors.

   The <fun>read_fp_register</fun> and <fun>write_fp_register</fun>
   functions are used to read and write floating point registers in a
   processor.

   <insert-until text="// ADD INTERFACE ia64_interface"/>
   </add>
*/

typedef struct ia64_interface {
        ia64_fp_register_t (*read_fp_register)(conf_object_t *cpu, int reg);
        void (*write_fp_register)(conf_object_t *cpu, int reg, ia64_fp_register_t val);
} ia64_interface_t;

#define IA64_INTERFACE "ia64"
// ADD INTERFACE ia64_interface


typedef enum { SAPIC_Physical = 0, SAPIC_Logical = 1 } sapic_destination_mode_t;
typedef enum { SAPIC_Fixed0 = 0, SAPIC_Fixed1 = 1, SAPIC_PMI = 2, SAPIC_NMI = 4, SAPIC_INIT = 5, SAPIC_Ext_INT = 7 } sapic_delivery_mode_t;
typedef enum { SAPIC_Bus_Accepted = 0, SAPIC_Bus_Retry = 1,
               SAPIC_Bus_No_Target = 2, SAPIC_Bus_Invalid = 3 } sapic_bus_status_t;
typedef enum { SAPIC_Edge = 0, SAPIC_Level = 1 } sapic_trigger_mode_t;
typedef enum { SAPIC_Idle = 0, SAPIC_Send_Pending = 1 } sapic_delivery_status_t;
typedef enum { SAPIC_RR_Invalid = 0, SAPIC_RR_Pending = 1, SAPIC_RR_Valid = 2 } sapic_rr_status_t;

/* <add-type id="sapic_interface_t">
 * The sapic interface is imlemented by the CPU.  It is used to send
 * interrupts from the SAPIC bus.
 * </add-type>
 */
typedef struct {
        void (*interrupt)(conf_object_t *obj,
                          sapic_delivery_mode_t delivery_mode,
                          uint8 vector);
} sapic_interface_t;
#define SAPIC_INTERFACE "sapic"
/* ADD INTERFACE sapic_interface */


/* <add-type id="iosapic_interface_t">
 * The iosapic interface is implemented by the interrupt controller
 * (I/O SAPIC).  In the 460GX documenation, this is called the "pid".
 * This interface is used by devices to signal interrupts that should
 * be forwarded to a CPU.
 * </add-type>
 */
typedef struct {
#if 0
        void (*eoi)(conf_object_t *obj, int vector);
#endif
        void (*interrupt)(conf_object_t *obj, int pin);
        void (*interrupt_clear)(conf_object_t *obj, int pin);
} iosapic_interface_t;
#define IOSAPIC_INTERFACE "iosapic"
/* ADD INTERFACE iosapic_interface */


/* <add-type id="sapic_bus_interface_t">
 * The sapic-bus interface is implemented by the SAPIC bus, which
 * arbitrates interrupts to the SAPICs (CPUs).  The caller is usually
 * the I/O SAPIC.
 * </add-type>
 */
typedef struct {
        sapic_bus_status_t (*interrupt)(conf_object_t *obj,
                                        sapic_delivery_mode_t delivery_mode,
                                        int level_assert,
                                        sapic_trigger_mode_t trigger_mode,
                                        uint8 vector,
                                        uint16 destination);
} sapic_bus_interface_t;
#define SAPIC_BUS_INTERFACE "sapic-bus"
/* ADD INTERFACE sapic_bus_interface */

#endif /* _SIMICS_ARCH_IA64_H */
