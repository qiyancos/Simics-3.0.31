/*
 * simics/core/processor.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
*
 */

#ifndef _SIMICS_CORE_PROCESSOR_H
#define _SIMICS_CORE_PROCESSOR_H

#include <simics/core/configuration.h>

/* A class implementing the cpu_group interface should also have
   cpu_list attribute */
#define CPU_GROUP_INTERFACE "cpu_group"
typedef struct {
        int dummy;
} cpu_group_interface_t;

/*
   <add id="simics api types">
   <name index="true">register_type_t</name>
   <doc>
   <doc-item name="NAME">register_type_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="register_type_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   Defines several type of register banks.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="register_type_t def"></add-type> */
typedef enum {
        Sim_Reg_Type_Invalid,
        Sim_Reg_Type_Integer,
        Sim_Reg_Type_Floating,
        Sim_Reg_Type_Control
} register_type_t;

/*
   <add id="simics arch api types">
   <name index="true">register_id_t</name>
   <doc>
   <doc-item name="NAME">register_id_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="register_id_t def"/>
   <insert id="arch_register_id_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   <insert id="arch_register_id_t desc"/>
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="register_id_t def"></add-type> */
typedef uint32 register_id_t;

/*
   <add id="simics api types">
   <name index="true">instruction_error_t</name>
   <doc>
   <doc-item name="NAME">instruction_error_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="instruction_error_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This type is used by the Micro Architecture Interface and documented in the
   Simics Out Of Order Guide.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="instruction_error_t def">
   </add-type> */
typedef enum instruction_error {
        Sim_IE_OK = 0,
        Sim_IE_Unresolved_Dependencies,
        Sim_IE_Speculative,
        Sim_IE_Stalling,
        Sim_IE_Not_Inserted,      /* trying to execute or squash an 
                                     instruction that is inserted. */ 
        Sim_IE_Exception,         /* (SPARC-V9 only) */
        Sim_IE_Fault = Sim_IE_Exception, 
        Sim_IE_Trap,              /* (X86 only) Returned if a trap is 
                                     encountered */
        Sim_IE_Interrupt,         /* (X86 only) Returned if an interrupt is 
                                     waiting and interrupts are enabled */

        Sim_IE_Sync_Instruction,  /* Returned if sync instruction is 
                                     not allowd to execute */
        Sim_IE_No_Exception,      /* Returned by SIM_instruction_
                                     handle_exception */
        Sim_IE_Illegal_Interrupt_Point,
        Sim_IE_Illegal_Exception_Point,
        Sim_IE_Illegal_Address,
        Sim_IE_Illegal_Phase,
        Sim_IE_Interrupts_Disabled,
        Sim_IE_Illegal_Id,
        Sim_IE_Instruction_Tree_Full,
        Sim_IE_Null_Pointer,
        Sim_IE_Illegal_Reg,
        Sim_IE_Invalid,
        Sim_IE_Out_of_Order_Commit, 
        Sim_IE_Retired_Instruction, /* try to squash a retiring instruction */
        Sim_IE_Not_Committed,       /* Returned by SIM_instruction_end */
        Sim_IE_Code_Breakpoint,
        Sim_IE_Mem_Breakpoint,
        Sim_IE_Step_Breakpoint,
        Sim_IE_Hap_Breakpoint
} instruction_error_t;

/*
   <add id="simics api types">
   <name index="true">instruction_phase_t</name>
   <doc>
   <doc-item name="NAME">instruction_phase_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="instruction_phase type"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This type is used by the Micro Architecture Interface and documented in the
   Simics Out Of Order Guide.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="instruction_phase type">
   </add-type> */
typedef enum instruction_phase {
        Sim_Phase_Initiated,
        Sim_Phase_Fetched,
        Sim_Phase_Decoded,
        Sim_Phase_Executed,
        Sim_Phase_Retired,
        Sim_Phase_Committed,
        Sim_Phases
} instruction_phase_t;

/*        Sim_Phase_ITLB_Access, */
/*        Sim_Phase_DTLB_Access, */
/*        Sim_Phase_Mem_Op,      */
/*        Sim_Phase_Write_Back,   */

/* <add-type id="reg_info type"><ndx>reg_info_t</ndx></add-type> */
struct reg_info {
        register_type_t type;   /* register type */
        register_id_t id;       /* register id */
        unsigned input:1;       /* used as input */
        unsigned output:1;      /* used as output */
};

#define MAX_REG_INFO_REGS 40

/* <add-type id="instr_info_dep type"><ndx>instr_info_dep_t</ndx></add-type> */
struct instr_info_dep {
        int number_of_regs;
        reg_info_t regs[MAX_REG_INFO_REGS];
};

typedef void * instruction_id_t;

/*
   <add id="simics api types">
   <name index="true">instruction_status_t</name>
   <doc>
   <doc-item name="NAME">instruction_status_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="instruction_status type"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This type is used by the Micro Architecture Interface and documented in the
   Simics Out Of Order Guide.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="instruction_status type">
   </add-type> */
typedef enum { 
        Sim_IS_Waiting  = 0x1,           /* Not all inputs are ready */
        Sim_IS_Ready    = 0x2,           /* All inputs are ready */
        Sim_IS_Stalling = 0x4,           /* Waiting for memory to 
                                            finish the operation */
        Sim_IS_Executed = 0x8,           /* Done */
        Sim_IS_Faulting = 0x10,          /* Has raised an exception - 
                                            a fault in x86 case */
        Sim_IS_Branch_Taken = 0x20,      /* The branch is taken for 
                                            branch instructions */
        Sim_IS_Trap     = 0x40,          /* (x86) this instruction
                                            generated a trap */
        Sim_IS_Interrupt = 0x80,         /* (x86) this instruction can not
                                            be executed because the interrupt
                                            must be taken first */
        Sim_IS_Retired = 0x100           /* All stores are retired */
} instruction_status_t;


#define IQ_MAX_BRANCHES 4

/* public part of instruction_t */
typedef struct public_instruction {

        struct instruction *prev;
        struct instruction *branches[IQ_MAX_BRANCHES];
        int no_branches;

        instruction_phase_t current_phase;
        instruction_error_t last_error;

        instr_type_t type;
        int sync;

        void *user_data;
        int allocated;
        conf_object_t *cpu;
        conf_object_t *ram; /* set if this instuction has locked memory in
                               this object */
} public_instruction_t;

/* define this when instruction_t is not fully defined */
#ifndef CPU_INCLUDES_H
typedef public_instruction_t instruction_t;
#endif

#if defined(MAI_FAST_ACCESS_FUNCTIONS)

#define SIM_id_to_public(id) ((public_instruction_t *)(id))
#define SIM_instruction_child(id, n) (SIM_id_to_public(id)->branches[(n)])
#define SIM_instruction_parent(id) (SIM_id_to_public(id)->prev)
#define SIM_instruction_phase(id) (SIM_id_to_public(id)->current_phase)
#define SIM_instruction_is_sync(id) (SIM_id_to_public(id)->sync)
#define SIM_instruction_cpu(id) (SIM_id_to_public(id)->cpu)
#define SIM_instruction_type(id) (SIM_id_to_public(id)->type)

#define SIM_instruction_get_user_data(id) (SIM_id_to_public(id)->user_data)
#define SIM_instruction_set_user_data(id, ud) \
do {                                               \
        SIM_id_to_public(id)->user_data = (ud);    \
} while(0)

#endif


int DBG_instruction_current_allocations(conf_object_t *NOTNULL cpu);


instruction_id_t SIM_instruction_begin(conf_object_t *NOTNULL obj);
instruction_error_t SIM_instruction_end(instruction_id_t ii);
void SIM_instruction_insert(instruction_id_t parent_ii, instruction_id_t ii);

#if !defined(MAI_FAST_ACCESS_FUNCTIONS)
instruction_id_t     SIM_instruction_child(instruction_id_t ii, int n); 
instruction_id_t     SIM_instruction_parent(instruction_id_t ii);
conf_object_t       *SIM_instruction_cpu(instruction_id_t ii);
instruction_phase_t  SIM_instruction_phase(instruction_id_t ii);
instr_type_t         SIM_instruction_type(instruction_id_t ii);
int                  SIM_instruction_is_sync(instruction_id_t ii);
lang_void           *SIM_instruction_get_user_data(instruction_id_t ii);
void                 SIM_instruction_set_user_data(instruction_id_t ii,
                                                   lang_void *);
#endif

instruction_error_t SIM_instruction_proceed(instruction_id_t ii);
instruction_error_t SIM_instruction_fetch(instruction_id_t ii);
instruction_error_t SIM_instruction_decode(instruction_id_t ii);
instruction_error_t SIM_instruction_execute(instruction_id_t ii);
instruction_error_t SIM_instruction_retire(instruction_id_t ii);
instruction_error_t SIM_instruction_commit(instruction_id_t ii);
instruction_error_t SIM_instruction_squash(instruction_id_t ii);
instruction_error_t SIM_instruction_rewind(instruction_id_t ii,
                                            instruction_phase_t phase);
instruction_error_t SIM_instruction_handle_exception(instruction_id_t ii);
instruction_error_t SIM_instruction_handle_interrupt(conf_object_t *cpu,
                                                     exception_type_t vector);
instruction_id_t SIM_instruction_nth_id(conf_object_t *NOTNULL obj, int n);

void SIM_instruction_set_stop_phase(conf_object_t *NOTNULL obj,
                                    instruction_phase_t phase, int on);

int SIM_instruction_speculative(instruction_id_t ii);
void SIM_instruction_force_correct(instruction_id_t ii);


int SIM_instruction_length(instruction_id_t ii);
instruction_status_t SIM_instruction_status(instruction_id_t ii);

reg_info_t *SIM_instruction_get_reg_info(instruction_id_t ii, int n);
attr_value_t SIM_instruction_read_input_reg(instruction_id_t ii,
                                            register_id_t ri);
attr_value_t SIM_instruction_read_output_reg(instruction_id_t ii,
                                             register_id_t ri);
void SIM_instruction_write_input_reg(instruction_id_t ii, register_id_t ri,
                                     attr_value_t value);
instruction_error_t SIM_instruction_write_output_reg(instruction_id_t ii,
                                                     register_id_t ri,
                                                     attr_value_t val);
 
instruction_id_t SIM_instruction_id_from_mem_op_id(conf_object_t *NOTNULL obj,
                                                   int id);
generic_transaction_t *SIM_instruction_stalling_mem_op(instruction_id_t ii);
generic_transaction_t *SIM_instruction_store_queue_mem_op(instruction_id_t ii,
                                                          int i);
cycles_t SIM_instruction_remaining_stall_time(instruction_id_t ii);

integer_t SIM_instruction_get_field_value(instruction_id_t ii,
                                          const char *NOTNULL field_name);

attr_value_t SIM_instruction_opcode(instruction_id_t ii);

void SIM_release_stall(conf_object_t *NOTNULL obj, int id);
int SIM_get_unique_memory_transaction_id(conf_object_t *NOTNULL obj);

#define PUBLIC_IQ_INTERFACE "public_iq_interface"

typedef struct public_iq_interface {
        public_instruction_t *(*current_instruction)(
                conf_object_t *NOTNULL cpu);
        void                  (*mmu_save_error_info)(
                public_instruction_t *NOTNULL pi,
                lang_void *ei);
} public_iq_interface_t;

enum {
        Step_Type_None = 0,
        Step_Type_Source,
        Step_Type_Step,
        Step_Type_Next,
        Step_Type_Finish,
        Step_Type_Uncall,
        Step_Type_Context
};

enum {
        Step_Flag_Line_Info = (1 << 5), /* command needs line info */
        Step_Flag_Forward = (1 << 6), /* command runs forward */
        Step_Flag_Backward = (1 << 7), /* command runs backward */
        Step_Flag_Success = (1 << 8), /* command succeeded */
        Step_Flag_Not_Symtable = (1 << 9) /* command doesn't need symtable */
};

typedef enum {
        Step_State_Command_None = Step_Type_None,
        Step_State_Command_Goto_Source = (Step_Type_Source
                                          | Step_Flag_Line_Info
                                          | Step_Flag_Forward
                                          | Step_Flag_Backward),
        Step_State_Command_Step = (Step_Type_Step
                                   | Step_Flag_Line_Info
                                   | Step_Flag_Forward),
        Step_State_Command_Unstep = (Step_Type_Step
                                     | Step_Flag_Line_Info
                                     | Step_Flag_Backward),
        Step_State_Command_Next = (Step_Type_Next
                                   | Step_Flag_Line_Info
                                   | Step_Flag_Forward),
        Step_State_Command_Nexti = (Step_Type_Next
                                    | Step_Flag_Forward),
        Step_State_Command_Prev = (Step_Type_Next
                                   | Step_Flag_Line_Info
                                   | Step_Flag_Backward),
        Step_State_Command_Previ = (Step_Type_Next
                                    | Step_Flag_Backward),
        Step_State_Command_Finish = (Step_Type_Finish
                                     | Step_Flag_Forward),
        Step_State_Command_Uncall = (Step_Type_Uncall
                                     | Step_Flag_Backward),
        Step_State_Command_Goto_Context = (Step_Type_Context
                                           | Step_Flag_Not_Symtable
                                           | Step_Flag_Forward
                                           | Step_Flag_Backward),
        Step_State_Command_Stepi = (Step_Type_Step
                                    | Step_Flag_Not_Symtable
                                    | Step_Flag_Forward),
        Step_State_Command_Unstepi = (Step_Type_Step
                                      | Step_Flag_Not_Symtable
                                      | Step_Flag_Backward)
} step_state_command_t;

typedef enum {
        /* Stepping failed. */
        Step_Result_Failure = 0,

        /* Stepping succeeded, and is done. */
        Step_Result_Success = Step_Flag_Success,

        /* Stepping succeeded so far, but is not finished yet. Need to run
           forward, or backward, or in either direction. */
        Step_Result_Run_Forward = Step_Flag_Success | Step_Flag_Forward,
        Step_Result_Run_Backward = Step_Flag_Success | Step_Flag_Backward,
        Step_Result_Run = (Step_Flag_Success | Step_Flag_Forward
                           | Step_Flag_Backward)
} source_step_result_t;

/* <add id="source_step_interface_t">

   Interface with source-line stepping functions.

   <insert-until text="// ADD INTERFACE source_step_interface"/>
   </add>
*/
typedef struct {
        source_step_result_t (*source_step)(conf_object_t *NOTNULL ctx_obj,
                                            step_state_command_t command);
} source_step_interface_t;

#define SOURCE_STEP_INTERFACE "_source_step"
// ADD INTERFACE source_step_interface

/* <add-type id="struct symtable def"></add-type> */
struct symtable;
/* <add-type id="struct simcontext def"></add-type> */
struct simcontext;
struct symtable *VT_context_get_symtable(struct simcontext *NOTNULL ctx);
conf_object_t *VT_get_primary_context(void);

struct icode_mode_group *init_icode_mode_group(struct icode_mode_group *group);
void update_icode_mode_group_prof(processor_t *proc);
void update_icode_mode_group_ctx(processor_t *proc);

typedef void (*instruction_trace_callback_t)(lang_void *tracer_data,
                                             conf_object_t *cpu,
                                             linear_address_t la,
                                             logical_address_t va,
                                             physical_address_t pa,
                                             byte_string_t opcode);

void VT_register_exec_tracer(conf_object_t *NOTNULL cpu_obj,
                             instruction_trace_callback_t tracer,
                             lang_void *tracer_data);
void VT_unregister_exec_tracer(conf_object_t *NOTNULL cpu_obj,
                               instruction_trace_callback_t tracer,
                               typed_lang_void *tracer_data);

/* Iterates over all objects that owns an event queue in simulator,
   returns next object on machine. If null is entered returns first
   object in list. Currently each processor object owns event queues.
  */
conf_object_t *SIM_next_queue(conf_object_t *obj);

char *branch_arc_type2str(int type, char *buf);

int VT_attach_branch_recorder_to_processor(conf_object_t *NOTNULL cpu_obj,
                                           conf_object_t *NOTNULL brec_obj);
int VT_detach_branch_recorder_from_processor(conf_object_t *NOTNULL cpu_obj,
                                             conf_object_t *NOTNULL brec_obj);
int VT_eec_interrupt_instruction(conf_object_t *NOTNULL cpu, int extype);

int SIM_number_processors(void);

void SIM_enable_processor(conf_object_t *NOTNULL cpu);
void SIM_disable_processor(conf_object_t *NOTNULL cpu);

void SIM_reset_processor(conf_object_t *NOTNULL cpu, int hard_reset); 

void VT_for_all_processors(void (*func)(conf_object_t *, lang_void *),
                           lang_void *user_data);

attr_value_t SIM_get_all_processors(void);
conf_object_t *SIM_get_processor(int proc_no);
int SIM_get_processor_number(const conf_object_t *NOTNULL cpu);
conf_object_t *SIM_current_processor(void);
int SIM_processor_enabled(conf_object_t *NOTNULL cpu);
int SIM_processor_privilege_level(conf_object_t *NOTNULL cpu);

int SIM_get_register_number(conf_object_t *NOTNULL cpu, const char *name);
const char *SIM_get_register_name(conf_object_t *NOTNULL cpu, int reg);
uinteger_t SIM_read_register(conf_object_t *NOTNULL cpu, int indx);
void SIM_write_register(conf_object_t *NOTNULL cpu, int reg, uinteger_t value);
attr_value_t SIM_get_all_registers(conf_object_t *NOTNULL cpu);

const char *SIM_get_exception_name(conf_object_t *NOTNULL cpu, int exc);
int SIM_get_exception_number(conf_object_t *NOTNULL cpu,
                             const char *NOTNULL name);
attr_value_t SIM_get_all_exceptions(conf_object_t *NOTNULL cpu);

logical_address_t SIM_get_program_counter(conf_object_t *NOTNULL cpu);

void SIM_set_program_counter(conf_object_t *NOTNULL cpu, logical_address_t pc);

tuple_int_string_t *SIM_disassemble(conf_object_t *NOTNULL cpu,
                                    generic_address_t addr, int type);

instr_info_t *SIM_instruction_info(conf_object_t *NOTNULL cpu,
                                   logical_address_t vaddr);

typedef enum {
        DA_Physical = 1,        /* include physical address */
        DA_Opcode = 2           /* include opcode */
} disass_flags_t;

/* <add id="processor_interface_t">
   Interface for accessing processor functionality.

   <insert-until text="// ADD INTERFACE processor_interface"/>

   The functions correspond to the API functions
   <fun>SIM_get_program_counter</fun>,
   <fun>SIM_set_program_counter</fun>,
   <fun>SIM_processor_privilege_level</fun>, and
   <fun>SIM_disassemble</fun>.  See the documentation for
   those functions for more complete documentation.

   The function <fun>instruction_info</fun> can take either a physical address
   (type = 0) or a logical address (type = 1). It returns a filled
   <type>instr_info_t</type> structure. Only the SPARCv9 and the x86
   architectures provides
   a list of register dependencies as an array of <type>reg_info_t</type>.

   <insert id="instr_info type"/>
   <insert id="instr_info_dep type"/>
   <insert id="reg_info type"/>

   <doc-item name="SEE ALSO">SIM_get_program_counter,
   SIM_processor_privilege_level</doc-item>
   </add> */
typedef struct {
        logical_address_t (*get_program_counter)(conf_object_t *NOTNULL cpu);
        void (*set_program_counter)(conf_object_t *NOTNULL cpu,
                                    logical_address_t pc);
        int (*get_privilege_level)(conf_object_t *NOTNULL cpu);
        tuple_int_string_t *(*disassemble)(conf_object_t *NOTNULL cpu,
                                           generic_address_t address,
                                           int type);
        tuple_int_string_t (*disassemble_buf)(
                conf_object_t *NOTNULL cpu, generic_address_t address,
                byte_string_t opcode);
        struct instr_info *(*instruction_info)(conf_object_t *NOTNULL cpu,
                                               generic_address_t address,
                                               int type);
        void (*reset)(conf_object_t *NOTNULL cpu, int hard_reset);
        processor_t *(*simcore)(processor_t *NOTNULL);
        void (*pre_simcore)(processor_t *NOTNULL);
        void (*post_simcore)(processor_t *NOTNULL);
        processor_t *(*in_order_simcore)(processor_t *NOTNULL);
        processor_t *(*step_queue_simcore)(processor_t *NOTNULL);
        processor_t *(*mai_simcore)(processor_t *NOTNULL);
        int (*dump_sr_stat)(const char *NOTNULL filename);
        void (*print_instruction_queue)(conf_object_t *NOTNULL cpu,
                                        int verbose);
        void (*dbg_print_pistc)(conf_object_t *NOTNULL cpu, int table);
#if !defined(GULP)
        int (*stc_load)(conf_object_t *cpu, logical_address_t laddr,
                        uint8 *value, int size);
        int (*stc_store)(conf_object_t *cpu, logical_address_t laddr,
                         uint8 *value, int size);
#endif /* !GULP */
        attr_value_t (*disassemble_range)(processor_t *NOTNULL cpu,
                                          logical_address_t start,
                                          int nlines, int back,
                                          disass_flags_t flags);
} processor_interface_t;

#define PROCESSOR_INTERFACE "processor"
// ADD INTERFACE processor_interface

/*
   <add id="int_register_interface_t"> The <iface>int-register</iface>
   interface is used for fast access to registers in a processor.  It
   can be used to access any kind of integer register, not only the
   "normal" registers.  This includes all kinds of control registers,
   hidden registers and anything else that might be useful to access as
   a register.  The only limitation is that the register value should
   be representable as an <type>uinteger_t</type>.
 
   This interface can be implemented by other classes than processors,
   but it is likely to be found mostly in processors.
 
   Registers are identified by a number, and there are two functions
   to translate from register names to register numbers and back.  The
   translation need not be one-to-one, which means that one register
   can have several names.  A register name can, however, only
   translate to a single register number.

   Often, registers are grouped in <i>register banks</i>, where
   registers in the bank are numbered from 0 up. Registers in a bank
   should have consecutive numbers (unless their numbering is very sparse).
   This allows a user to deduce register numbers by calling
   <fun>get_number</fun> for the first register only.
   The first register numbers should be used for the general-purpose integer 
   registers, if possible (so that integer register <b>r</b>N has number N).

   Using this interface to read or write registers does not cause any
   side effects, such as triggering interrupts or signalling haps.

   <b>get_number</b> translates a register name to its number.
   
   <b>get_name</b> translates a register number to its canonical name.

   <b>read</b> reads a register value.

   <b>write</b> writes a new register value.

   <b>all_registers</b> returns a list of all register numbers that can
   be used for this object.

   <b>register_info</b> returns information about a single register.
   The information return depends on the <param>info</param> parameter.

   <dl>
   
   <dt>Sim_RegInfo_Catchable</dt><dd>Return 1 if
   <const>Core_Control_Register_Write</const> and
   <const>Core_Control_Register_Read</const> are triggered when this
   register is written or read.</dd>  Return 0 otherwise.

   </dl>

   <small>
   <insert id="ireg_info_t"/>

   <insert-until text="// ADD INTERFACE int_register_interface"/>
   </small>
   </add>
*/
typedef struct {
        int (*get_number)(conf_object_t *NOTNULL obj,
                          const char *NOTNULL name);
        const char *(*get_name)(conf_object_t *NOTNULL obj, int reg);
        uinteger_t (*read)(conf_object_t *NOTNULL obj, int reg);
        void (*write)(conf_object_t *NOTNULL obj, int reg, uinteger_t val);
        attr_value_t (*all_registers)(conf_object_t *NOTNULL obj);
        int (*register_info)(conf_object_t *NOTNULL obj, int reg,
                             ireg_info_t info);
} int_register_interface_t;

#define INT_REGISTER_INTERFACE "int_register"
// ADD INTERFACE int_register_interface

/*
 * The exception interface is used to translate exception numbers, as
 * received by the Core_Exception hap, to names, and vice versa.
 */

/* <add id="exception_interface_t">
   Interface for identifying exceptions.

   <insert-until text="// ADD INTERFACE exception_interface"/>
   
   </add> */
typedef struct {
        int (*get_number)(conf_object_t *NOTNULL obj,
                          const char *NOTNULL name);
        const char *(*get_name)(conf_object_t *NOTNULL obj, int exc);
        int (*get_source)(conf_object_t *NOTNULL obj, int exc);
        attr_value_t (*all_exceptions)(conf_object_t *NOTNULL obj);
} exception_interface_t;

#define EXCEPTION_INTERFACE "exception"
// ADD INTERFACE exception_interface

/* <add-type id="state_save_kind_t def"></add-type> */
typedef enum {
	Sim_State_IA64_Default	= 1,
	Sim_State_IA64_System 	= 1,
	Sim_State_IA64_User 	= 2, /* no CRs */

	Sim_State_X86_Default	= 1,
	Sim_State_X86_System 	= 1,
        Sim_State_X86_MM        = 2, /* XMM and MMX */
        Sim_State_X86_OOO       = 3, /* MM + patching of EAX when needed */

	Sim_State_Sparc_Default	= 1,
	Sim_State_Sparc_System 	= 1,
        Sim_State_Sparc_Visible = 2, /* only visible window */
        Sim_State_Sparc_System_OOO = 3, /* no TICK, STICK */

	Sim_State_Alpha_Default	= 1,
	Sim_State_Alpha_System 	= 1,

	Sim_State_PPC_Default	= 1,
	Sim_State_PPC_System 	= 1,

        Sim_State_ARM_Default   = 1,
        Sim_State_ARM_System    = 1,

        Sim_State_MIPS_Default  = 1,
        Sim_State_MIPS_System   = 1
} state_save_kind_t;

/*
  Save state interface for saving/loading state fast

  <add id="save_state_interface">
  Internal, do not use.
   </add>

 */
typedef struct save_state_interface {

        /* return the CVS version of the object */
        int (*get_version)(struct conf_object *obj);
        /* return the size needed for the current state */
        int (*get_size)(struct conf_object *obj, state_save_kind_t stype);
        /* return the alignment needed for the structure */
        int (*get_align)(struct conf_object *obj, state_save_kind_t stype);


        /* network-endian functions */

        /* save the state in dest. dest must contains enough space
           (get_size with the same parameter should return the size needed) */
        int (*save_state)(struct conf_object *obj, state_save_kind_t stype,
                          void *dest);
        /* load the state from src */
        int (*load_state)(struct conf_object *obj, state_save_kind_t stype,
                          void *src);
        /* compare the state and return 0 if the same */
        int (*compare_state)(struct conf_object *obj, state_save_kind_t stype,
                             void *src);
        /* compare the state and return 0 if the same. print out
           all/the difference according to flags */
        int (*print_state)(struct conf_object *obj, state_save_kind_t stype,
                           void *src, int symnames, int diff);

        /* host-endian functions (eventually faster, not mandatory) */
        int (*save_state_he)(struct conf_object *obj, state_save_kind_t stype,
                             void *dest);
        int (*load_state_he)(struct conf_object *obj, state_save_kind_t stype,
                             void *src);
        int (*compare_state_he)(struct conf_object *obj,
                                state_save_kind_t stype, void *src);
        int (*print_state_he)(struct conf_object *obj, 
                              state_save_kind_t stype,
                              void *src, int symnames, int diff);
} save_state_interface_t;

#define SAVE_STATE_INTERFACE "_save_state"

#endif /* _SIMICS_CORE_PROCESSOR_H */
