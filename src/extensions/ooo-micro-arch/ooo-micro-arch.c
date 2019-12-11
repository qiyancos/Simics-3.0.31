/*
  ooo-micro-arch.c - example of a micro architectural model

  Copyright 2002-2007 Virtutech AB
  
  The contents herein are Source Code which are a subset of Licensed
  Software pursuant to the terms of the Virtutech Simics Software
  License Agreement (the "Agreement"), and are being distributed under
  the Agreement.  You should have received a copy of the Agreement with
  this Licensed Software; if not, please contact Virtutech for a copy
  of the Agreement prior to using this Licensed Software.
  
  By using this Source Code, you agree to be bound by all of the terms
  of the Agreement, and use of this Source Code is subject to the terms
  the Agreement.
  
  This Source Code and any derivatives thereof are provided on an "as
  is" basis.  Virtutech makes no warranties with respect to the Source
  Code or any derivatives thereof and disclaims all implied warranties,
  including, without limitation, warranties of merchantability and
  fitness for a particular purpose and non-infringement.

*/   

#include <errno.h>
#include <stdio.h>
#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

/* 
   This file demonstrates the Micro Architectural Interface. The
   processor modeled can fetch, execute, and commit a configurable
   number of intructions per cycle (by setting some
   attributes). Default is 1, 1, and 1 respectively. No speculation is
   performed, thus if an unresolved branch is found the fetches are
   stalled.
   
   If an exception occurs the tree is drained and all the speculative
   instructions beyond the faulting one are discarded.

   A demo can be run that uses this model by running 
   './simics -x sarek-1p-ooo.simics' in the simics/home/sarek
   directoty. Play around with the commands, step-cycle and
   print-instuction-queue. */

typedef struct ooo_micro_arch_object
{
        log_object_t log;
        int drain_queue;
        int interrupt_vector;
        int stalling_reg;
        int fetches_per_cycle;
        int commits_per_cycle;
        int execute_per_cycle;

        logical_address_t branch_table[256];
        logical_address_t stalling_address;
        integer_t break_cycle;
        integer_t value_prediction_table[256];
        conf_object_t *cpu;
} ooo_micro_arch_object_t;

#define fetches_per_cycle(ooo) ((ooo)->fetches_per_cycle)
#define execute_per_cycle(ooo) ((ooo)->execute_per_cycle)
#define commits_per_cycle(ooo) ((ooo)->commits_per_cycle)

static char tmp_buf[256];

const char *asm_s(instruction_id_t ii)
{
        tuple_int_string_t *tuple;
        attr_value_t pc;

        pc = SIM_instruction_read_input_reg(ii, V9_Reg_Id_PC);
        if (pc.kind != Sim_Val_Integer) {
                SIM_clear_exception();                
                return "<unknown pc>";
        }

        SIM_clear_exception();
        tuple = SIM_disassemble(SIM_instruction_cpu(ii), (logical_address_t)pc.u.integer, 1);
        if (SIM_get_pending_exception()) {
                SIM_clear_exception();
                return "<disass error>";
        }
        
        vtsprintf(tmp_buf, "<0x%016llx> %s", (logical_address_t)pc.u.integer, tuple->string);
        
        return (const char *)tmp_buf;
}

int is_branch(ooo_micro_arch_object_t *ooo, conf_object_t *cp, instruction_id_t ii)
{
        attr_value_t val = SIM_instruction_opcode(ii);
        uint32 opc = (uinteger_t)val.u.integer;
        uint32 op = opc >> 30;

        if (op == 0) { /* rel branches */
                uint32 op2 = (opc >> 22) & 0x7;
                return (op2 != 0 && op2 != 4 && op2 != 7);
        } else if (op == 2) { /* jmpl, return */ 
                uint32 op3 = (opc >> 19) & 0x3f;
                return (op3 == 0x38 || op3 == 0x39);
        } else /* call */
                return op == 1;
}

attr_value_t
bpredict(ooo_micro_arch_object_t *ooo, attr_value_t pc)
{
        pc.u.integer = ooo->branch_table[(pc.u.integer >> 2) & 0xff];
        return pc;
}

instruction_error_t
decode_instruction(ooo_micro_arch_object_t *ooo, conf_object_t *cp, instruction_id_t new)
{      
        instruction_error_t ie;
        log_object_t *log = &ooo->log;
                                
        switch(ie = SIM_instruction_decode(new)) {
        case Sim_IE_OK:
                SIM_log_info(4, log, 0, "- load pc (pc = 0x%016llx, npc = 0x%016llx)",
                          SIM_instruction_read_input_reg(new, V9_Reg_Id_PC).u.integer,
                          SIM_instruction_read_input_reg(new, V9_Reg_Id_NPC).u.integer);
                SIM_log_info(3, log, 0, "fetching    - %s", asm_s(new));                
                break;
        case Sim_IE_Unresolved_Dependencies:
                break;
        case Sim_IE_Stalling:
                SIM_log_info(3, log, 0, "stalling    - %s", asm_s(new));                
                break;
        case Sim_IE_Exception: {                        
                /* if we have a code exception on a speculative path we squash it */
                
                if (SIM_instruction_speculative(new)) {
                        SIM_log_info(4, log, 0, "- code access exception on a speculative path  - %s", asm_s(new));
                        if (SIM_instruction_squash(new) != Sim_IE_OK) {
                                pr("SIM_instruction_squash failed\n");
                                return Sim_IE_OK;
                        }
                } else {
                        SIM_log_info(2, log, 0, "- code access exception  - %s", asm_s(new));
                        ooo->drain_queue = 1;
                }
                break;
        }
        default:
                pr("Unexpected return from SIM_instruction_decode()\n");
        }        
        return ie;
}

void run_cycle(ooo_micro_arch_object_t *ooo)
{
        instruction_id_t ii, parent, new;
        instruction_error_t ie;
        log_object_t *log = &ooo->log;
        int i, executed = 0;
        
        conf_object_t *cp = ooo->cpu;

        if (ooo->drain_queue && SIM_instruction_nth_id(cp, 0) == 0)
                ooo->drain_queue = 0;

        /* check for interrupts */
        if (ooo->interrupt_vector != Sim_PE_No_Exception) {
                switch(SIM_instruction_handle_interrupt(cp, ooo->interrupt_vector)) {
                case Sim_IE_OK:
                        SIM_log_info(2, &ooo->log, 0, "- handle interrupt @ %lld (vector=%x)", 
                                  SIM_cycle_count(cp), 
                                  ooo->interrupt_vector);
                        ooo->interrupt_vector = Sim_PE_No_Exception;
                        ooo->drain_queue = 0;
                        break;
                case Sim_IE_Interrupts_Disabled:
                        /* OK try later */
                        break;
                case Sim_IE_Illegal_Interrupt_Point:
                        /* queue is not-empty */
                        ooo->drain_queue = 1;
                        break;
                default:
                        pr("SIM_instruction_handle_interrupt() failed\n");
                }
        }

        /* If first instruction on a speculative path squash queue */
        if ((ii = SIM_instruction_nth_id(cp, 0)) && SIM_instruction_speculative(ii)) {
                SIM_log_info(4, log, 0, "a speculative path  - %s", asm_s(ii));
                if (SIM_instruction_squash(ii) != Sim_IE_OK) {
                        pr("SIM_instruction_squash failed\n");
                        return;
                }
                return;
        }

        /* commit instructions */
        for(i = 0; i < commits_per_cycle(ooo); i++) {                
                if (!(ii = SIM_instruction_nth_id(cp, 0)))
                        break;

                if (SIM_instruction_phase(ii) >= Sim_Phase_Executed) {
                        if (SIM_instruction_speculative(ii)) {
                                SIM_log_info(4, log, 0, "a speculative path  - %s", asm_s(ii));
                                if (SIM_instruction_squash(ii) != Sim_IE_OK) {
                                        pr("SIM_instruction_squash failed\n");
                                        return;
                                }
                                return;
                        } else if (SIM_instruction_is_sync(ii) == 2 && SIM_instruction_child(ii, 0)) {
                                /* Need to commit sync 2 instruction alone in tree */
                                if (SIM_instruction_squash(SIM_instruction_child(ii, 0)) != Sim_IE_OK) {
                                        pr("SIM_instruction_squash failed\n");
                                        return;
                                }
                        }

                        switch(ie = SIM_instruction_commit(ii)) {
                        case Sim_IE_OK:
                                SIM_log_info(3, log, 0, "committing  - %s", asm_s(ii));                       
                                break;
                        case Sim_IE_Code_Breakpoint:
                        case Sim_IE_Step_Breakpoint:
                        case Sim_IE_Hap_Breakpoint:
                                SIM_break_cycle(cp, 0);
                                return;
                        case Sim_IE_Exception: {
                                /* store retire face returned exception, probably a 
                                   memory checksum fault */
                                instruction_id_t child = SIM_instruction_child(ii, 0);
                                        
                                if (child && SIM_instruction_squash(child) != Sim_IE_OK) {
                                        pr("SIM_instruction_squash failed\n");
                                        executed = execute_per_cycle(ooo);
                                }
                                /* exit the loop */
                                i = commits_per_cycle(ooo);
                                continue;
                        }
                        case Sim_IE_Stalling:
                                SIM_log_info(3, log, 0, "stalling    - %s", asm_s(ii));
                                /* exit the loop */
                                i = commits_per_cycle(ooo);
                                continue;
                        default: 
                                pr("SIM_instruction_commit failed %d\n", ie); 
                                return;
                        }

                        switch(ie = SIM_instruction_end(ii)) {
                        case Sim_IE_OK: 
                                break;
                        default: 
                                pr("SIM_instruction_end failed (%lld)\n", SIM_cycle_count(cp));
                                return;
                        }
                }
        }

        /* execute instructions */
        for(ii = SIM_instruction_nth_id(cp, 0); ii; ii = SIM_instruction_child(ii, 0)) {

                /* check for exceptions */
                if (SIM_instruction_status(ii) & Sim_IS_Faulting) {
                        if (!SIM_instruction_child(ii, 0) && !SIM_instruction_parent(ii)) {
                                if (SIM_instruction_handle_exception(ii) != Sim_IE_OK)
                                        pr("SIM_instruction_handle_exception failed\n");
                                SIM_log_info(2, log, 0, "handle exc  - %s", asm_s(ii));
                                if (SIM_instruction_end(ii) != Sim_IE_OK) {
                                        pr("SIM_instruction_end failed (%lld)\n", SIM_cycle_count(cp));
                                }
                                break;
                        }
                }
                        
                /* execute instruction if it is decoded and ready 
                   (first time or after stall in case of mem op) */
                if (SIM_instruction_phase(ii) == Sim_Phase_Decoded && 
                    (SIM_instruction_status(ii) & Sim_IS_Ready)) {
                        
                        if (SIM_instruction_is_sync(ii) == 2) {
                                if (!SIM_instruction_child(ii, 0) && !SIM_instruction_parent(ii)) {
                                        SIM_log_info(4, log, 0, "sync #2     - %s", asm_s(ii));
                                } else {
                                        /* squash our children */
                                        instruction_id_t child = SIM_instruction_child(ii, 0);
                                        
                                        if (child && SIM_instruction_squash(child) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                        }
                                }
                                ooo->drain_queue = 1;
                        }
                                
                        switch(ie = SIM_instruction_execute(ii)) {
                        case Sim_IE_OK:
                                SIM_log_info(3, log, 0, "executing   - %s", asm_s(ii));
                                executed++;
                                break;
                        case Sim_IE_Unresolved_Dependencies:                  
                                pr("Instruction unexpected unresolved dependencies\n");                                
                                return;
                        case Sim_IE_Stalling:
                                SIM_log_info(3, log, 0, "stalling    - %s", asm_s(ii));
                                break;
                        case Sim_IE_Exception:
                                if (SIM_instruction_speculative(ii)) {
                                        SIM_log_info(4, log, 0, 
                                                  "- instruction got exception on a speculative path -> squash it and later\n");
                                        /* exception on a speculative path -> squash */
                                        if (SIM_instruction_squash(ii) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                        }
                                        executed = execute_per_cycle(ooo);
                                        break;
                                } else {
                                        /* squash our childen */
                                        instruction_id_t child = SIM_instruction_child(ii, 0);
                                        
                                        if (child && SIM_instruction_squash(child) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                                executed = execute_per_cycle(ooo);
                                                break;
                                        }
                                }
                                ooo->drain_queue = 1;
                                break;
                        case Sim_IE_Sync_Instruction:
                                SIM_log_info(4, log, 0, "- sync instruction");
                                        
                                if (SIM_instruction_speculative(ii)) {
                                        /* sync on a speculative path -> squash */
                                        if (SIM_instruction_squash(ii) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                        }
                                        executed = execute_per_cycle(ooo);
                                }
                                break;
                        default:
                                pr("Unexpected return from SIM_instruction_execute(): %d\n", ie);
                                break;
                        }
                        
                        if (executed == execute_per_cycle(ooo))
                                break;
                }
        }


        parent = 0;

        /* Get the last instruction in the queue */ 
        for(ii = SIM_instruction_nth_id(cp, 0); ii; ii = SIM_instruction_child(ii, 0)) {
                if (!SIM_instruction_child(ii, 0))
                        parent = ii;
        }

        /* Check to see if last fetch still stalling */
        if (parent &&
            SIM_instruction_phase(parent) < Sim_Phase_Decoded && 
            SIM_instruction_remaining_stall_time(parent) > 0) {
                SIM_log_info(1, log, 3, "- still stalling on instruction fetch");
                return;
        }
 
        for(i = 0; i < fetches_per_cycle(ooo); i++, parent = new) {
                        
                /* Only create new instruction if we have no parent or parent has been decoded succesfully */
                if (!parent || SIM_instruction_phase(parent) >= Sim_Phase_Decoded) {
                        
                        /* if we should drain the queue we should not fetch a new instructions */
                        if (ooo->drain_queue)
                                return;
                        
                        if (parent && SIM_instruction_phase(parent) < Sim_Phase_Executed &&
                            is_branch(ooo, cp, parent)) {
                                SIM_log_info(4, log, 0, "- control dependency: cannot fetch more");
                                return;
                        }

                        if (!(new = SIM_instruction_begin(cp))) {
                                SIM_log_info(4, log, 0, "- reorder buffer queue full");
                                return;
                        }
                        
                        SIM_instruction_insert(parent, new);
                } else {
                        /* we try to redecode the parent */
                        new = parent;
                }
                
                ie = decode_instruction(ooo, cp, new);

                if (ie == Sim_IE_OK)
                        continue;
                else if (ie == Sim_IE_Unresolved_Dependencies) {
                        attr_value_t parent_pc, parent_npc;
                
                        SIM_log_info(4, log, 0, "- PC not ready - speculate");
                        
                        ASSERT(parent);

                        parent_pc  = SIM_instruction_read_input_reg(parent, V9_Reg_Id_PC);
                        parent_npc = SIM_instruction_read_input_reg(parent, V9_Reg_Id_NPC);

                        ASSERT(parent_pc.kind == Sim_Val_Integer && parent_npc.kind == Sim_Val_Integer);

                        parent_pc.u.integer = parent_npc.u.integer;
                        parent_npc.u.integer = parent_npc.u.integer + 4;
                                
                        SIM_instruction_write_input_reg(new, V9_Reg_Id_PC, parent_pc);
                        SIM_instruction_write_input_reg(new, V9_Reg_Id_NPC, parent_npc);

                        if (Sim_IE_OK != decode_instruction(ooo, cp, new)) {
                                return;
                        }
                } else {
                        /* code exception or stalling fetches */
                        return;
                }
        }
}

static void 
my_cycle_handler(conf_object_t *cpu, ooo_micro_arch_object_t *ooo)
{
        run_cycle(ooo);
        if (SIM_get_pending_exception()) {
                pr("*** Exception (%s) in run_cycle @ %lld cycles ***\n", SIM_last_error(), SIM_cycle_count(cpu));
                SIM_break_cycle(cpu, 0);
        }
        SIM_time_post_cycle(cpu,1,0,(event_handler_t)my_cycle_handler, ooo);
}

static void 
my_interrupt_handler(void *_ooo, void *_cpu, integer_t vector)
{
        ooo_micro_arch_object_t *ooo = _ooo;
        
        if ((conf_object_t *)_cpu == ooo->cpu)
                ooo->interrupt_vector = (int)vector;
}

static set_error_t
set_fetches_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)obj;

        if (val->kind != Sim_Val_Integer) {
                return Sim_Set_Need_Integer;
        }

        ooo->fetches_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_fetches_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)obj;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ooo->fetches_per_cycle;
        return ret;
}

static set_error_t
set_execute_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)obj;

        if (val->kind != Sim_Val_Integer) {
                return Sim_Set_Need_Integer;
        }

        ooo->execute_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_execute_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)obj;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ooo->execute_per_cycle;
        return ret;
}

static set_error_t
set_commits_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)obj;

        if (val->kind != Sim_Val_Integer) {
                return Sim_Set_Need_Integer;
        }

        ooo->commits_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_commits_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)obj;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ooo->commits_per_cycle;
        return ret;
}

static void
initial_config_hap(void *data)
{
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)data;
        attr_value_t mode;

        mode = SIM_get_attribute(ooo->cpu, "ooo-mode");

        if (strcmp(mode.u.string, "micro-architecture") != 0) {
                SIM_log_error(&ooo->log, 0,
                              "%s is not an MAI compatible processor, "
                              "make sure Simics is started with the -ma flag",
                              ooo->cpu->name);
                return;
        }

        pr("[%s] added cycle handler on %s\n",
           ooo->log.obj.name, ooo->cpu->name);

        SIM_time_post_cycle(ooo->cpu, 0, 0,
			    (event_handler_t)my_cycle_handler, data);
	
        SIM_hap_add_callback("Core_Asynchronous_Trap", 
                             (obj_hap_func_t)my_interrupt_handler, data);

}


static set_error_t
set_cpu(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)obj;

        if (val->kind != Sim_Val_Object)
                return Sim_Set_Need_Object;
	
        ooo->cpu = val->u.object;

        if (SIM_initial_configuration_ok()) {
                initial_config_hap(obj);
        } else {
		SIM_hap_register_callback("Core_Initial_Configuration",
					  initial_config_hap, obj);
        }
        
        return Sim_Set_Ok;
}

static attr_value_t
get_cpu(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        ooo_micro_arch_object_t *ooo = (ooo_micro_arch_object_t *)obj;

        if (ooo->cpu) {
                ret.kind = Sim_Val_Object;
                ret.u.object = ooo->cpu;
        } else {
                ret.kind = Sim_Val_Nil;
        }
        return ret;
}

static conf_object_t *
new_instance(parse_object_t *pa)
{
        ooo_micro_arch_object_t *obj = MM_ZALLOC(1, ooo_micro_arch_object_t);
        SIM_log_constructor(&obj->log, pa);

        obj->interrupt_vector = Sim_PE_No_Exception;

        obj->fetches_per_cycle = 1;
        obj->execute_per_cycle = 1;
        obj->commits_per_cycle = 1;

        return &obj->log.obj;
}

static int
delete_instance(conf_object_t *obj)
{
        SIM_time_clean(SIM_current_processor(), Sim_Sync_Processor, (event_handler_t)my_cycle_handler, (void *)obj);
        MM_FREE(obj);
        return 0;
}

static class_data_t class_data;
static conf_class_t *conf_class;

DLL_EXPORT void
init_local(void)
{
        /* initialize and register the class "ooo-memhier-class" */
        memset(&class_data, 0, sizeof(class_data_t));
        class_data.new_instance = new_instance;
        class_data.delete_instance = delete_instance;
        class_data.description = 
                "This class models a simple out of order processor which "
                "can fetch, execute, and commit a configurable "
                "number of instructions per cycle (by setting some "
                "attributes). ";

        //class_data.kind = Sim_Class_Kind_Pseudo;

        conf_class = SIM_register_class("ooo_micro_arch", &class_data);

        /* initialize attributes */
        SIM_register_attribute(conf_class, "cpu", get_cpu,
                               0, set_cpu, 0, Sim_Attr_Optional,
                               "The CPU of the micro architecture model");

        SIM_register_attribute(conf_class, "fetches_per_cycle", get_fetches_per_cycle,
                               0, set_fetches_per_cycle, 0, Sim_Attr_Optional,
                               "Number of instructions to fetch each cycle.");

        SIM_register_attribute(conf_class, "execute_per_cycle", get_execute_per_cycle,
                               0, set_execute_per_cycle, 0, Sim_Attr_Optional,
                               "Number of instructions to execute each cycle per instruction tree branch.");
        
        SIM_register_attribute(conf_class, "commits_per_cycle", get_commits_per_cycle,
                               0, set_commits_per_cycle, 0, Sim_Attr_Optional,
                               "Number of instructions to commit each cycle.");
}
