/*
 * simics/core/obsolete.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_OBSOLETE_H
#define _SIMICS_CORE_OBSOLETE_H

#if defined(SIMICS_1_4_API) || defined(SHOW_OBSOLETE_API)
exception_type_t OLD_get_No_Exception(void);
conf_object_t *OLD_get_mmu_data(processor_t *cpu);
processor_t *OLD_cpu_by_mid(int mid);
#if !defined(GULP)
processor_t * OLD_void_to_processor_t(void *cpu);
#endif   /* !GULP */
void OLD_install_user_ASI_handler(
               exception_type_t (*handler)(generic_transaction_t *), int asi);
void OLD_install_default_ASI_handler(
               exception_type_t (*handler)(generic_transaction_t *), int asi);
int OLD_sparc_ASI_info(processor_t *cpu, int asi, int info);
integer_t OLD_get_trap_time(processor_t *cpu, int trap_level);
const char *OLD_disassemble_physical(processor_t *cpu, physical_address_t pa);
uinteger_t OLD_read_control_register(processor_t *cpu, int reg);
void   OLD_write_control_register(processor_t *cpu, int reg, uinteger_t value);
int    OLD_get_control_register_number(processor_t *cpu, const char *regname);
const char *OLD_get_control_register_name(processor_t *cpu, int reg);
uinteger_t OLD_read_window_register(processor_t *cpu, int window, int reg);
void OLD_write_window_register(processor_t *cpu, int window,
                               int reg, uinteger_t value);
uinteger_t OLD_read_global_register(processor_t *cpu, int globals, int reg);
void OLD_write_global_register(processor_t *cpu, int globals,
                               int reg, uinteger_t value);
int OLD_num_control_registers(processor_t *cpu);
simtime_t OLD_cpu_issue_cycles(processor_t *cpu);
const char *OLD_get_register_name(int num);
int OLD_get_register_number(const char *name);
const char *OLD_get_exception_name(int num);
int OLD_get_exception_number(const char *name);
#endif /* SIMICS_1_4_API || SHOW_OBSOLETE_API */

#if defined(SIMICS_1_4_API) || defined(SIMICS_1_6_API) || defined(SHOW_OBSOLETE_API)
#include <simics/arch/ia64.h>

uint32 OLD_read_fp_register_i(processor_t *cpu, int reg);
uint64 OLD_read_fp_register_x(processor_t *cpu, int reg);
float  OLD_read_fp_register_s(processor_t *cpu, int reg);
double OLD_read_fp_register_d(processor_t *cpu, int reg);
ia64_fp_register_t OLD_read_fp_register(processor_t *cpu, int reg);
void OLD_write_fp_register_i(processor_t *cpu, int reg, uint32 value);
void OLD_write_fp_register_x(processor_t *cpu, int reg, uint64 value);
void OLD_write_fp_register_s(processor_t *cpu, int reg, float value);
void OLD_write_fp_register_d(processor_t *cpu, int reg, double value);
void OLD_write_fp_register(processor_t *cpu, int reg, ia64_fp_register_t val);
void OLD_clear_atomic_reservation_bit(processor_t *cpu);
logical_address_t OLD_get_stack_pointer(conf_object_t *cpu);
logical_address_t OLD_get_base_pointer(conf_object_t *cpu);
void OLD_device_log(conf_object_t *log, const char *msg);
void OLD_time_clean(conf_object_t *obj, event_handler_t func,
                    typed_lang_void *user_data);
#endif   /* SIMICS_1_4_API || SIMICS_1_6_API || SHOW_OBSOLETE_API */

#if defined(SIMICS_1_4_API) || defined(SIMICS_1_6_API) || defined(SIMICS_1_8_API) || defined(SHOW_OBSOLETE_API)
int OLD_breakpoint_action(breakpoint_id_t id, const char *action);
uint64 OLD_get_file_size(const char *filename);
#endif   /* SIMICS_1_4_API || SIMICS_1_6_API || SIMICS_1_8_API || SHOW_OBSOLETE_API */

#if defined(SIMICS_1_4_API) || defined(SIMICS_1_6_API) || defined(SIMICS_1_8_API) || defined(SIMICS_2_0_API) || defined(SHOW_OBSOLETE_API)
conf_object_t *OLD_object_by_id(int id);
hap_handle_t OLD_hap_install_callback(hap_type_t hap, hap_func_t cb,
                                      lang_void *user_data);
hap_handle_t OLD_hap_install_callback_idx(hap_type_t hap, hap_func_t cb,
                                          integer_t index, lang_void *data);
hap_handle_t OLD_hap_install_callback_range(hap_type_t hap, hap_func_t cb,
                                            integer_t start, integer_t end,
                                            lang_void *user_data);
hap_handle_t OLD_hap_register_callback(const char *id, str_hap_func_t cb,
                                       lang_void *user_data);
hap_handle_t OLD_hap_register_callback_idx(const char *id, str_hap_func_t cb,
                                           integer_t idx, lang_void *data);
hap_handle_t OLD_hap_register_callback_range(const char *id, str_hap_func_t cb,
                                             integer_t start, integer_t end,
                                             lang_void *data);
void OLD_hap_remove_callback(hap_type_t hap, hap_handle_t hdl);
void OLD_hap_unregister_callback(const char *id, str_hap_func_t cb,
                                 lang_void *user_data);
hap_type_t OLD_hap_new_type(const char *id, const char *params, 
                            const char *param_descs,
                            const char *index, const char *desc);
#endif   /* SIMICS_1_4_API || SIMICS_1_6_API || SIMICS_1_8_API || SIMICS_2_0_API || SHOW_OBSOLETE_API */

#if defined(SIMICS_1_4_API) || defined(SIMICS_1_6_API) || defined(SIMICS_1_8_API) || defined(SIMICS_2_0_API) || defined(SIMICS_2_2_API) || defined(SHOW_OBSOLETE_API)
attr_attr_t OLD_get_attribute_attributes(conf_object_t *obj, const char *attr);
void OLD_raise_general_exception(const char *msg);
sim_exception_t OLD_check_exception(void);
int OLD_exception_has_occurred(void);
#if !defined(GULP)
void OLD_c_frontend_exception(void *fe, sim_exception_t exc_type,
                              const char *str);
#endif
const char *OLD_get_history_match(const char *str);
#endif /* SIMICS_1_4_API || SIMICS_1_6_API || SIMICS_1_8_API || SIMICS_2_0_API || SIMICS_2_2_API || SHOW_OBSOLETE_API */


#if defined(SIMICS_1_4_API)
#define SIM_get_No_Exception            OLD_get_No_Exception
#define SIM_get_mmu_data                OLD_get_mmu_data
#define SIM_cpu_by_mid                  OLD_cpu_by_mid
#define SIM_void_to_processor_t         OLD_void_to_processor_t
#define SIM_install_user_ASI_handler    OLD_install_user_ASI_handler
#define SIM_install_default_ASI_handler OLD_install_default_ASI_handler
#define SIM_sparc_ASI_info              OLD_sparc_ASI_info
#define SIM_get_trap_time               OLD_get_trap_time
#define SIM_disassemble_physical        OLD_disassemble_physical
#define SIM_read_control_register       OLD_read_control_register
#define SIM_write_control_register      OLD_write_control_register
#define SIM_get_control_register_number OLD_get_control_register_number
#define SIM_get_control_register_name   OLD_get_control_register_name
#define SIM_read_window_register        OLD_read_window_register
#define SIM_write_window_register       OLD_write_window_register
#define SIM_read_global_register        OLD_read_global_register
#define SIM_write_global_register       OLD_write_global_register
#define SIM_num_control_registers       OLD_num_control_registers
#define SIM_cpu_issue_cycles            OLD_cpu_issue_cycles
#define SIM_get_register_name           OLD_get_register_name
#define SIM_get_register_number         OLD_get_register_number
#define SIM_get_exception_name          OLD_get_exception_name
#define SIM_get_exception_number        OLD_get_exception_number

/* allow old simmalloc macros to work */
#define MM_MALLOC_s MM_MALLOC
#define MM_MALLOC_g MM_MALLOC
#define MM_MALLOC_p MM_MALLOC
#define MM_MALLOC0_s MM_MALLOC
#define MM_MALLOC0_g MM_MALLOC
#define MM_MALLOC0_p MM_MALLOC

#define MM_MALLOC_SZ_s MM_MALLOC_SZ
#define MM_MALLOC_SZ_g MM_MALLOC_SZ
#define MM_MALLOC_SZ_p MM_MALLOC_SZ

#define MM_ZALLOC_s MM_ZALLOC
#define MM_ZALLOC_g MM_ZALLOC
#define MM_ZALLOC_p MM_ZALLOC
#define MM_ZALLOC0_s MM_ZALLOC
#define MM_ZALLOC0_g MM_ZALLOC
#define MM_ZALLOC0_p MM_ZALLOC

#define MM_ZALLOC_SZ_s MM_ZALLOC_SZ
#define MM_ZALLOC_SZ_g MM_ZALLOC_SZ
#define MM_ZALLOC_SZ_p MM_ZALLOC_SZ

#define MM_MALIGN_s MM_MALIGN
#define MM_MALIGN_g MM_MALIGN
#define MM_MALIGN_p MM_MALIGN

#define MM_REALLOC0 MM_REALLOC

#define MM_STRDUP_s MM_STRDUP
#define MM_STRDUP_g MM_STRDUP
#define MM_STRDUP_p MM_STRDUP

#endif   /* SIMICS_1_4_API */

#if defined(SIMICS_1_4_API) || defined(SIMICS_1_6_API)

#if defined(SIM_BC_OLD_ENUMS)
#define Instruction     Sim_DI_Instruction
#define Data            Sim_DI_Data
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Space_Memory    Sim_Addr_Space_Memory
#define Space_IO        Sim_Addr_Space_IO
#endif

#if defined(SIM_BC_OLD_ENUMS)
typedef enum mem_op_size {
        Bit8 = 1,
        Bit16 = 2,
        Bit32 = 4,
        Bit64 = 8,
        Bit128 = 16,

        Byte = 1,
        Half = 2,
        Word = 4,
        Dword = 8,
        Qword = 16,
        Block64 = 64
} mem_op_size_t;
#endif

#if TARGET_VA_BITS == 64
typedef uint64 ireg_t;
typedef int64 sreg_t;
#elif TARGET_VA_BITS == 32
typedef uint32 ireg_t;
typedef int32 sreg_t;
#endif /* TARGET_VA_BITS == 32 */

#if defined(SIM_BC_OLD_ENUMS)
#define User            Sim_CPU_Mode_User
#define Supervisor      Sim_CPU_Mode_Supervisor
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Read    Sim_RW_Read
#define Write   Sim_RW_Write
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Initiator_Illegal       Sim_Initiator_Illegal
#define Initiator_CPU           Sim_Initiator_CPU
#define Initiator_CPU_V9        Sim_Initiator_CPU_V9
#define Initiator_CPU_UI        Sim_Initiator_CPU_UI
#define Initiator_CPU_UII       Sim_Initiator_CPU_UII
#define Initiator_CPU_UIII      Sim_Initiator_CPU_UIII
#define Initiator_CPU_UIV       Sim_Initiator_CPU_UIV
#define Initiator_CPU_UV        Sim_Initiator_CPU_UV
#define Initiator_CPU_X86       Sim_Initiator_CPU_X86
#define Initiator_CPU_PPC       Sim_Initiator_CPU_PPC
#define Initiator_CPU_Alpha     Sim_Initiator_CPU_Alpha
#define Initiator_CPU_IA64      Sim_Initiator_CPU_IA64
#define Initiator_CPU_MIPS      Sim_Initiator_CPU_MIPS
#define Initiator_CPU_ARM       Sim_Initiator_CPU_ARM
#define Initiator_Device        Sim_Initiator_Device
#define Initiator_Other         Sim_Initiator_Other
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Host    Sim_Endian_Host
#define Target  Sim_Endian_Target
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Break_Physical  Sim_Break_Physical
#define Break_Virtual   Sim_Break_Virtual
#define Break_Linear    Sim_Break_Linear
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Access_Read     Sim_Access_Read
#define Access_Write    Sim_Access_Write
#define Access_Execute  Sim_Access_Execute
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Prefetch        Sim_Trans_Prefetch
#define St              Sim_Trans_Store
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Sync_Processor  Sim_Sync_Processor
#define Sync_Machine    Sim_Sync_Machine
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Val_Invalid     Sim_Val_Invalid
#define Val_String      Sim_Val_String
#define Val_Integer     Sim_Val_Integer
#define Val_Floating    Sim_Val_Floating
#define Val_List        Sim_Val_List
#define Val_Data        Sim_Val_Data
#define Val_Nil         Sim_Val_Nil
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Required                    Sim_Attr_Required
#define Optional                    Sim_Attr_Optional
#define Session_Attr                Sim_Attr_Session
#define Pseudo_Attr                 Sim_Attr_Pseudo
#define Always_Initialize           Sim_Attr_Required

#define Integer_Indexed             Sim_Attr_Integer_Indexed
#define String_Indexed              Sim_Attr_String_Indexed
#define List_Indexed                Sim_Attr_List_Indexed

#define Attribute_Attr_Mask         Sim_Attr_Flag_Mask

#define Initialization_Phase_0      Sim_Init_Phase_0
#define Initialization_Phase_1      Sim_Init_Phase_1
#define Initialization_Phase_Shift  Sim_Init_Phase_Shift
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Set_Ok                  Sim_Set_Ok
#define Set_Error_Str           Sim_Set_Illegal_Value
#define Set_Need_Integer        Sim_Set_Need_Integer
#define Set_Need_Floating       Sim_Set_Need_Floating
#define Set_Need_String         Sim_Set_Need_String
#define Set_Need_List           Sim_Set_Need_List
#define Set_Need_Data           Sim_Set_Need_Data
#define Set_Need_Object         Sim_Set_Need_Object
#define Set_Object_Not_Found    Sim_Set_Object_Not_Found
#define Set_Interface_Not_Found Sim_Set_Interface_Not_Found
#define Set_Illegal_Value       Sim_Set_Illegal_Value
#define Set_Attribute_Not_Found Sim_Set_Attribute_Not_Found
#endif

#if defined(SIM_BC_OLD_ENUMS)
#define Kind_Vanilla    Sim_Class_Kind_Vanilla
#define Kind_Session    Sim_Class_Kind_Session
#define Kind_Pseudo     Sim_Class_Kind_Pseudo
#endif

#if defined(SIM_BC_OLD_PSEUDO_EX)
#define No_Exception            Sim_PE_No_Exception
#define Code_Break              Sim_PE_Code_Break
#define Silent_Break            Sim_PE_Silent_Break
#define Inquiry_Outside_Memory  Sim_PE_Inquiry_Outside_Memory
#define Inquiry_Unhandled       Sim_PE_Inquiry_Unhandled
#define IO_Break                Sim_PE_IO_Break
#define IO_Not_Taken            Sim_PE_IO_Not_Taken
#define Exception_Break         Sim_PE_Exception_Break
#define Hap_Exception_Break     Sim_PE_Hap_Exception_Break
#define Stall_Cpu               Sim_PE_Stall_Cpu
#define Continue                Sim_PE_Default_Semantics
#define Return_Break            Sim_PE_Return_Break
#define Instruction_Finished    Sim_PE_Instruction_Finished
#define Default_Semantics       Sim_PE_Default_Semantics
#define Speculation_Failed      Sim_PE_Speculation_Failed
#define Error                   Sim_PE_Error
#endif

#define SIM_read_fp_register_i           OLD_read_fp_register_i
#define SIM_read_fp_register_x           OLD_read_fp_register_x
#define SIM_read_fp_register_s           OLD_read_fp_register_s
#define SIM_read_fp_register_d           OLD_read_fp_register_d
#define SIM_read_fp_register             OLD_read_fp_register
#define SIM_write_fp_register_i          OLD_write_fp_register_i
#define SIM_write_fp_register_x          OLD_write_fp_register_x
#define SIM_write_fp_register_s          OLD_write_fp_register_s
#define SIM_write_fp_register_d          OLD_write_fp_register_d
#define SIM_write_fp_register            OLD_write_fp_register
#define SIM_clear_atomic_reservation_bit OLD_clear_atomic_reservation_bit 
#define SIM_get_stack_pointer            OLD_get_stack_pointer
#define SIM_get_base_pointer             OLD_get_base_pointer
#define SIM_device_log                   OLD_device_log
#define SIM_time_clean                   OLD_time_clean

#define SIM_conf_object_to_processor(x) ((processor_t *)(x))
#define SIM_processor_to_conf_object(x) ((conf_object_t *)(x))
#define SIM_add_completion VT_add_completion
#define SIM_filename_completion VT_filename_completion
#define SIM_get_history_match VT_get_history_match

#endif   /* SIMICS_1_4_API || SIMICS_1_6_API */


#if defined(SIMICS_1_4_API) || defined(SIMICS_1_6_API) || defined(SIMICS_1_8_API)

#define SIM_breakpoint_action OLD_breakpoint_action
#define SIM_get_file_size     OLD_get_file_size

#define SIM_instruction_end(cpu, ii)            SIM_instruction_end(ii)
#define SIM_instruction_insert(cpu, pii, ii)    SIM_instruction_insert(pii, ii)
#define SIM_instruction_child(cpu, ii, n)       SIM_instruction_child(ii, n)
#define SIM_instruction_parent(cpu, ii)         SIM_instruction_parent(ii)
#define SIM_instruction_proceed(cpu, ii)        SIM_instruction_proceed(ii)
#define SIM_instruction_fetch(cpu, ii)          SIM_instruction_fetch(ii)
#define SIM_instruction_decode(cpu, ii)         SIM_instruction_decode(ii)
#define SIM_instruction_execute(cpu, ii)        SIM_instruction_execute(ii)
#define SIM_instruction_retire(cpu, ii)         SIM_instruction_retire(ii)
#define SIM_instruction_commit(cpu, ii)         SIM_instruction_commit(ii)
#define SIM_instruction_squash(cpu, ii)         SIM_instruction_squash(ii)
#define SIM_instruction_handle_exception(cpu, ii) SIM_instruction_handle_exception(ii)

#define SIM_instruction_phase(cpu, ii)          SIM_instruction_phase(ii)
#define SIM_instruction_wrong_path(cpu, ii)     SIM_instruction_speculative(ii)
#define SIM_instruction_set_right_path(cpu, ii) SIM_instruction_force_correct(ii)
#define SIM_instruction_type(cpu, ii)           SIM_instruction_type(ii)
#define SIM_instruction_length(cpu, ii)         SIM_instruction_length(ii)
#define SIM_instruction_status(cpu, ii)         SIM_instruction_status(ii)

#define SIM_instruction_get_reg_info(cpu, ii, n) SIM_instruction_get_reg_info(ii, n)
#define SIM_instruction_read_input_reg(cpu, ii, ri) SIM_instruction_read_input_reg(ii, ri)
#define SIM_instruction_read_output_reg(cpu, ii, ri) SIM_instruction_read_output_reg(ii, ri)
#define SIM_instruction_write_input_reg(cpu, ii, ri, v) SIM_instruction_write_input_reg(ii, ri, v)

#define SIM_instruction_is_sync(cpu, ii)        SIM_instruction_is_sync(ii)
#define SIM_instruction_get_user_data(cpu, ii)  SIM_instruction_get_user_data(ii)

#define SIM_instruction_set_user_data(cpu, ii, data) SIM_instruction_set_user_data(ii, data)

#define SIM_instruction_stalling_mem_op(cpu, ii) SIM_instruction_stalling_mem_op(ii)
#define SIM_instruction_remaining_stall_time(cpu, ii) SIM_instruction_remaining_stall_time(ii)

#define SIM_instruction_get_field_value(cpu, ii, f) SIM_instruction_get_field_value(ii, f)

#endif /* SIMICS_1_4_API || SIMICS_1_6_API || SIMICS_1_8_API */

#if defined(SIMICS_1_4_API) || defined(SIMICS_1_6_API) || defined(SIMICS_1_8_API) || defined(SIMICS_2_0_API)
/* obsolete, but always available in 2.0 */
#define SIM_object_by_id                OLD_object_by_id
#define SIM_hap_install_callback        OLD_hap_install_callback
#define SIM_hap_install_callback_idx    OLD_hap_install_callback_idx
#define SIM_hap_install_callback_range  OLD_hap_install_callback_range
#define SIM_hap_register_callback       OLD_hap_register_callback
#define SIM_hap_register_callback_idx   OLD_hap_register_callback_idx
#define SIM_hap_register_callback_range OLD_hap_register_callback_range 
#define SIM_hap_remove_callback         OLD_hap_remove_callback
#define SIM_hap_unregister_callback     OLD_hap_unregister_callback
#define SIM_hap_new_type                OLD_hap_new_type

/* typedefs kept for compatibility */
typedef void (*event_poster_interface_get_event_info_t)
        (attr_value_t *checkpoint_value, 
         conf_object_t *obj, 
         event_handler_t func, 
         lang_void *info);
typedef int (*event_poster_interface_set_event_info_t)
        (conf_object_t *obj, 
         attr_value_t *checkpoint_value, 
         event_handler_t *out_func, 
         lang_void **out_info);
typedef const char *(*event_poster_interface_describe_event_t)
        (conf_object_t *obj, 
         event_handler_t func, 
         lang_void *info);

#endif /* SIMICS_1_4_API || SIMICS_1_6_API || SIMICS_1_8_API || SIMICS_2_0_API */

#if defined(SIMICS_1_4_API) || defined(SIMICS_1_6_API) || defined(SIMICS_1_8_API) || defined(SIMICS_2_0_API) || defined(SIMICS_2_2_API)

#define SIM_get_attribute_attributes OLD_get_attribute_attributes
#define SIM_raise_general_exception  OLD_raise_general_exception
#define SIM_check_exception          OLD_check_exception
#define SIM_exception_has_occurred   OLD_exception_has_occurred
#define SIM_c_frontend_exception     OLD_c_frontend_exception
#define VT_get_history_match         OLD_get_history_match

#if defined(SIM_BC_LOG_CONSTRUCTOR)
#define log_constructor(log, obj) SIM_log_constructor(log, obj)
#endif

#if defined(TARGET_X86_64)
typedef uint64 lina_t;
#elif defined(TARGET_X86)
typedef uint32 lina_t;
#endif /* TARGET_X86 */

#if defined(TARGET_ALPHA)
typedef alpha_memory_transaction_t memory_transaction_t;
#endif
#if defined(TARGET_ARM)
typedef arm_memory_transaction_t memory_transaction_t;
#endif
#if defined(TARGET_IA64)
typedef ia64_memory_transaction_t memory_transaction_t;
#endif
#if defined(TARGET_MIPS)
typedef mips_memory_transaction_t memory_transaction_t;
#endif
#if defined(TARGET_PPC)
typedef ppc_memory_transaction_t memory_transaction_t;
#endif
#if defined(TARGET_SPARC_V9)
typedef v9_memory_transaction_t memory_transaction_t;
#endif
#if defined(TARGET_X86)
typedef x86_memory_transaction_t memory_transaction_t;
#endif

typedef uint64 la_t;
typedef uint64 pa_t;
typedef uint64 ga_t;

#ifdef _WIN32
 #define INT64_MOD "I64"
#else
 #define INT64_MOD "ll"
#endif

#define LOGICAL_ADDRESS_STR "0x%016" INT64_MOD "x"
#define PHYSICAL_ADDRESS_STR "0x%016" INT64_MOD "x"
#define GENERIC_ADDRESS_STR "0x%016" INT64_MOD "x"

#define LA_STR LOGICAL_ADDRESS_STR
#define PA_STR PHYSICAL_ADDRESS_STR
#define GA_STR GENERIC_ADDRESS_STR

/* alternate names */
#ifndef LONGLONG_MAX
#define LONGLONG_MAX MAX_INTEGER_T
#endif
#ifndef LONGLONG_MIN
#define LONGLONG_MIN MIN_INTEGER_T
#endif
#ifndef ULONGLONG_MAX
#define ULONGLONG_MAX MAX_UINTEGER_T
#endif
#ifndef ULONGLONG_MIN
#define ULONGLONG_MIN MIN_UINTEGER_T
#endif

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

#if defined(TARGET_VA_BITS) && !defined(TARGET_GA_BITS)
 #if TARGET_PA_BITS > TARGET_VA_BITS
  #define TARGET_GA_BITS TARGET_PA_BITS
 #else
  #define TARGET_GA_BITS TARGET_VA_BITS
 #endif
#endif

/* Win32 does not define caddr_t. */
#if defined(MSVC_WIN32) || defined(INTEL_WIN32) || defined(GCC_WIN32)
typedef char *caddr_t;
#endif

#define Sim_Initiator_CPU_UI   Sim_Initiator_CPU_V9
#define Sim_Initiator_CPU_UV   Sim_Initiator_CPU_V9

#if defined(TARGET_X86)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_X86
#elif defined(TARGET_SPARC_V9)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_V9
#elif defined(TARGET_IA64)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_IA64
#elif defined(TARGET_PPC)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_PPC
#elif defined(TARGET_ARM)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_ARM
#elif defined(TARGET_ALPHA)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_Alpha
#elif defined(TARGET_MIPS_RM7000)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_MIPS_RM7000
#elif defined(TARGET_MIPS_E9000)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_MIPS_E9000
#elif defined(TARGET_MIPS)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU_MIPS
#elif defined(TARGET_CLOCK)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU
#elif defined(TARGET_TMS320C64)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU
#elif defined(TARGET_MSP430)
#define DEFAULT_MEM_OP_INITIATOR Sim_Initiator_CPU
#endif

#define IS_CPU_MEM_OP(type) (((type) & 0xf000) == Sim_Initiator_CPU)
#define IS_DEV_MEM_OP(type) (((type) & 0xf000) == Sim_Initiator_Device)
#define IS_OTH_MEM_OP(type) (((type) & 0xf000) == Sim_Initiator_Other)
#define IS_CPU_ARCH_MEM_OP(type, arch) (((type) & 0xff00) == (arch))

#define Sim_PE_Continue Sim_PE_No_Exception
#define Sim_PE_IO_Break Sim_PE_No_Exception
#define Sim_PE_Error    Sim_PE_No_Exception

#if !defined(WIN32) && !defined(__INTEL_COMPILER)
#define U_TYPES_DEFINED 1
#endif

#ifndef _BSDTYPES_DEFINED
#ifndef U_TYPES_DEFINED

typedef unsigned char u_char;
typedef unsigned short u_short;
typedef unsigned int u_int;
typedef unsigned long u_long;
#ifndef _BSDTYPES_DEFINED
#define _BSDTYPES_DEFINED
#endif
#ifndef U_TYPES_DEFINED
#define U_TYPES_DEFINED
#endif

#endif
#endif /* not _BSDTYPES_DEFINED */

#define TIME_NANO_SECS 1

#define SIM_set_screen_size(w, h)

#endif /* SIMICS_1_4_API || SIMICS_1_6_API || SIMICS_1_8_API || SIMICS_2_0_API || SIMICS_2_2_API */

/* still visible in 3.0 API */
conf_object_t *SIM_proc_no_2_ptr(int proc_no);
int SIM_get_proc_no(const conf_object_t *cpu);
int SIM_get_current_proc_no(void);
void SIM_processor_break(conf_object_t *cpu, integer_t steps);
int SIM_no_windows(void);
void SIM_dump_caches(void);
int SIM_cpu_enabled(conf_object_t *cpu);
int SIM_cpu_privilege_level(conf_object_t *cpu);
object_vector_t SIM_all_objects(void);
class_vector_t SIM_all_classes(void);
void SIM_for_all_processors(void (*func)(conf_object_t *, lang_void *),
                            lang_void *user_data);
void SIM_for_all_hap_types(void (*func)(char *));
void SIM_for_all_modules(void (*func)(char *, char *, char *, char *));
void SIM_for_all_modules_failed(void (*func)(char *, char *, char *,
                                             char *, char *));
int SIM_register_named_interface(conf_class_t *cls, const char *name,
                                 interface_t *iface, const char *portname,
                                 const char *desc);
interface_t *SIM_get_named_interface(const conf_object_t *obj,
                                     const char *name, const char *portname);
interface_t *SIM_get_named_class_interface(const conf_class_t *cls,
                                           const char *name,
                                           const char *portname);
#ifndef GULP
void SIM_describe_interface(const char *NOTNULL name,
                            const char *NOTNULL desc);
#endif

#endif /* _SIMICS_CORE_OBSOLETE_H */
