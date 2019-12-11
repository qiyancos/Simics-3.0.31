/*
  sample-micro-arch.c - example of a micro architectural model

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
#include <simics/arch/sparc.h>

#define NO_VALUE_PREDICTION

#ifndef MAXPATH
#define MAXPATH 1024
#endif

/* 
   This file demonstrates the Micro Architectural Interface. The
   processor modeled can fetch, execute, and commit a configurable
   number of instructions per cycle (by setting some
   attributes). Default is 4, 4, and 4 respectively. It has a simple
   branch-predictor that uses a hash table to lookup the target
   address from the address of the branch instruction. The hash table
   is updated for every successfully committed branch.
   
   Besides speculating on the target address, the architecture also
   speculate fall through for every branch. This way 2 possible
   execution paths are created for every branch.  This makes the
   instruction tree into a binary tree. The number of instructions
   executed and fetch per cycle is actually per branch in the
   instruction tree.

   This demo models no pipeline stages other than those found in
   Simics. Instructions are fetched and decoded at once making the
   fetch staged itself invisible.

   If an exception occurs the tree is drained and all the speculative
   instructions beyond the faulting one are discarded.

   A demo can be run that uses this model by running 
   ./simics -ma -x sarek-1p-tree-ma.simics
   in the simics/home/sarek directoty. Play around with 
   the commands, step-cycle and print-instuction-queue.  */

typedef struct sample_micro_arch_object
{
        log_object_t log;
        int user_drain_queue;
        int drain_queue;
        int interrupt_vector;
        int stalling_reg;
        int fetches_per_cycle;
        int commits_per_cycle;
        int retires_per_cycle;
        int execute_per_cycle;
        int out_of_order_retire;
        int repost;
        logical_address_t branch_table[256];
        logical_address_t stalling_address;
        integer_t break_cycle;
        integer_t value_prediction_table[256];
        integer_t committed_steps;
        integer_t cycles;
        conf_object_t *cpu;
} sample_micro_arch_object_t;

typedef struct user_data {
        logical_address_t address;
        int size;
} user_data_t;

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
        
        vtsprintf(tmp_buf, "<0x%llx> %s", (logical_address_t)pc.u.integer,
                  tuple->string);
        
        return (const char *)tmp_buf;
}

int is_branch(instruction_id_t ii)
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

int 
execute_instructions(sample_micro_arch_object_t *sma, conf_object_t *cp, instruction_id_t ii, int n)
{
        if (!ii || n == 0) {
                return 1;
        } else {
                int i;
                instruction_id_t child;
                instruction_error_t ie;
                log_object_t *log = &sma->log;

//              SIM_log_info(1, log, 0, "trying     - %s", asm_s(ii));

                if (SIM_instruction_status(ii) & Sim_IS_Faulting) {
                        if (!SIM_instruction_child(ii, 0) && !SIM_instruction_parent(ii)) {
                                switch(SIM_instruction_handle_exception(ii)) {
                                case Sim_IE_OK:
                                        sma->committed_steps++;
                                        SIM_log_info(2, log, 0, "handle exc  - %s", asm_s(ii));
                                        if (SIM_instruction_end(ii) != Sim_IE_OK) {
                                                pr("SIM_instruction_end failed (%lld)\n", SIM_cycle_count(cp));
                                        }
                                        return 1;
                                case Sim_IE_Code_Breakpoint:
                                case Sim_IE_Step_Breakpoint:
                                case Sim_IE_Hap_Breakpoint:
                                        SIM_log_info(1, log, 0, "requested breakpoint - cycle not finished");
                                        SIM_break_cycle(cp, 0);
                                        sma->repost = 1;
                                        return 0;
                                default:
                                        pr("SIM_instruction_handle_exception failed\n");
                                        return 0;
                                }
                        }
                }
                        
                /* execute instruction if it is decoded and ready (first time or after stall in case of mem op) */
                while(SIM_instruction_phase(ii) == Sim_Phase_Decoded) {
                        if (SIM_instruction_status(ii) & Sim_IS_Ready) {
                                
                                if (SIM_instruction_is_sync(ii) == 2) {
                                        if (!SIM_instruction_child(ii, 0) && !SIM_instruction_parent(ii)) {
                                                SIM_log_info(2, log, 0, "sync #2    - %s", asm_s(ii));
                                                sma->drain_queue = 1;                                                
                                        } else {
                                                instruction_id_t child;
                                                /* squash our childen */
                                                while((child = SIM_instruction_child(ii, 0))) {
                                                        if (SIM_instruction_squash(child) != Sim_IE_OK) {
                                                                pr("SIM_instruction_squash failed\n");
                                                                return 0;
                                                        }
                                                }
                                                sma->drain_queue = 1;
                                                return 1;
                                        }
                                }                         

                                switch(ie = SIM_instruction_execute(ii)) {
                                case Sim_IE_OK: {
                                        integer_t pc = SIM_instruction_read_input_reg(ii, V9_Reg_Id_PC).u.integer;
                                        SIM_log_info(2, log, 0, "executing   - %s", asm_s(ii));
                                        if (0 /*(rand() & 0x3) == 0*/) {
                                                ie = SIM_instruction_rewind(ii, Sim_Phase_Decoded);
                                                switch(ie) {
                                                case Sim_IE_OK:
                                                        pr("SIM_instruction_rewind ok - pc = 0x%llx\n", pc);
                                                        break;
                                                case Sim_IE_Sync_Instruction:
                                                        pr("SIM_instruction_rewind on sync - not performed pc = 0x%llx\n",
                                                           pc);
                                                        break;
                                                default:
                                                        pr("*** SIM_instruction_rewind returned "
                                                           "unexpected value (%d) pc = 0x%llx ***\nc", ie, pc);
                                                        break;
                                                }
                                        }
                                        n--;
                                        break;
                                }
                                case Sim_IE_Unresolved_Dependencies:                                        
                                        pr("Instruction unexpected unresolved dependencies\n");
                                        return 0;
                                case Sim_IE_Stalling:
                                        SIM_log_info(2, log, 0, "stalling    - %s", asm_s(ii));
                                        break;
                                case Sim_IE_Exception:
                                        if (SIM_instruction_speculative(ii)) {
                                                SIM_log_info(2, log, 0, 
                                                          "- instruction got speculative exception -> "
                                                          "squash it and later");
                                                /* exception on wrong path -> squash */
                                                if (SIM_instruction_squash(ii) != Sim_IE_OK) {
                                                        pr("SIM_instruction_squash failed\n");
                                                        return 0;
                                                } else {
                                                        return 1;
                                                }      
                                        } else {
                                                instruction_id_t child;
                                                SIM_log_info(2, log, 0, "- instruction got exception -> squash later and drian queue");
                                                /* squash our childen */
                                                while((child = SIM_instruction_child(ii, 0))) {
                                                        if (SIM_instruction_squash(child) != Sim_IE_OK) {
                                                                pr("SIM_instruction_squash failed\n");
                                                                return 0;
                                                        }
                                                }
                                                sma->drain_queue = 1;
                                        }
                                        break;
                                case Sim_IE_Sync_Instruction: {
                                        SIM_log_info(2, log, 0, "- sync instruction");
                                        
                                        if (SIM_instruction_speculative(ii)) {
                                                /* sync on wrong path -> squash */
                                                if (SIM_instruction_squash(ii) != Sim_IE_OK) {
                                                        pr("SIM_instruction_squash failed\n");
                                                        return 0;
                                                }
                                                return 1;
                                        }
                                        break;
                                }
                                default:
                                        pr("Unexpected return from SIM_instruction_execute(): %d\n", ie);
                                        break;
                                }
                        } else {
#ifdef VALUE_PREDICTION
                                generic_transaction_t *mem_op;
                                /* If the instruction is stalling for memory we predict
                                   the out register from a preduction table */

                                if ((mem_op = SIM_instruction_stalling_mem_op(ii))) {
                                        reg_info_t *ri;
                                        for(i = 0; (ri = SIM_instruction_get_reg_info(ii, i)); i++) {
                                                if (ri->out && ri->id < 32) { /* integer out reg */
                                                        attr_value_t reg;
                                                        user_data_t *ud = MM_MALLOC(1, user_data_t);
                                                        SIM_instruction_set_user_data(ii, ud);
                                                        reg.kind = Sim_Val_Integer;
                                                        reg.u.integer = sma->value_prediction_table[
                                                                (mem_op->logical_address >> 2) & 0xff];
                                                        SIM_instruction_write_output_reg(ii, ri->id, reg);
                                                        SIM_log_info(2, log, 0, "- value predict out reg to %lld",
                                                                  reg.u.integer);
                                                        break;
                                                }
                                        }
                                }
#endif
                        }
                        break;
                }
                
                for(i = 0; (child = SIM_instruction_child(ii, i));) {
                        if (!execute_instructions(sma, cp, child, n))
                                return 0;
                        if (child == SIM_instruction_child(ii, i))
                                i++;
                }
                return 1;
        }
}

attr_value_t 
bpredict(sample_micro_arch_object_t *sma, attr_value_t pc)
{
        pc.u.integer = sma->branch_table[(pc.u.integer >> 2) & 0xff];
        return pc;
}



instruction_error_t
decode_instruction(sample_micro_arch_object_t *sma, conf_object_t *cp, instruction_id_t new)
{      
        instruction_error_t ie;
        log_object_t *log = &sma->log;
                                
        switch(ie = SIM_instruction_decode(new)) {
        case Sim_IE_OK:
                SIM_log_info(3, log, 0, "- load pc (pc = 0x%llx, npc = 0x%llx)",
                          (logical_address_t)SIM_instruction_read_input_reg(new, V9_Reg_Id_PC).u.integer,
                          (logical_address_t)SIM_instruction_read_input_reg(new, V9_Reg_Id_NPC).u.integer);
                SIM_log_info(2, log, 0, "fetching    - %s", asm_s(new));
                break;
        case Sim_IE_Unresolved_Dependencies:
                break;
        case Sim_IE_Stalling:
                SIM_log_info(2, log, 0, "stalling    - %s", asm_s(new));                
                break;
        case Sim_IE_Exception: {                        
                /* if we have a code exception on wrong path we squash it */
                
                if (SIM_instruction_speculative(new)) {
                        SIM_log_info(2, log, 0, "- code access exception on wrong path  - %s", asm_s(new));
                        if (SIM_instruction_squash(new) != Sim_IE_OK) {
                                pr("SIM_instruction_squash failed\n");
                                return Sim_IE_OK;
                        }
                } else {
                        SIM_log_info(2, log, 0, "- code access exception  - %s", asm_s(new));
                        sma->drain_queue = 1;
                }
                break;
        }
        default:
                pr("Unexpected return from SIM_instruction_decode()\n");
        }        
        return ie;
}

void fetch_decode_instructions(sample_micro_arch_object_t *sma, conf_object_t *cp, instruction_id_t ii)
{
        /* fetching & decoding */
        if (ii && SIM_instruction_child(ii, 0)) {
                int i;
                instruction_id_t child;
                for(i = 0; (child = SIM_instruction_child(ii, i)); i++) {
                        fetch_decode_instructions(sma, cp, child);
                }
        } else {
                /* leaf instruction */
                instruction_id_t new, parent = ii;
                instruction_error_t ie;
                log_object_t *log = &sma->log;
                int i;

                /* Check to see if last fetch still stalling */
                if (parent &&
                    SIM_instruction_phase(parent) < Sim_Phase_Decoded && 
                    SIM_instruction_remaining_stall_time(parent) > 0) {
                        SIM_log_info(2, log, 0, "- still stalling on instruction fetch");
                        return;
                }
 
                for(i = 0; i < sma->fetches_per_cycle; i++, parent = new) {
                        
                        /* Only create new instruction if we have no parent or parent has been decoded succesfully */
                        if (!parent || SIM_instruction_phase(parent) >= Sim_Phase_Decoded) {

                                /* if we should drain the queue we should not fetch a new instructions */
                                if (sma->drain_queue || sma->user_drain_queue)
                                        return;

                                if (!(new = SIM_instruction_begin(cp))) {
                                        SIM_log_info(2, log, 0, "- reorder buffer queue full");
                                        return;
                                }

                                SIM_instruction_insert(parent, new); 
                        } else {
                                new = parent;
                        }

                        ie = decode_instruction(sma, cp, new);

                        if (ie == Sim_IE_OK)
                                continue;
                        else if (ie == Sim_IE_Unresolved_Dependencies) {
                                attr_value_t parent_pc, parent_npc;
                
                                SIM_log_info(3, log, 0, "- PC not ready - speculate");

                                ASSERT(parent);

                                parent_pc  = SIM_instruction_read_input_reg(parent, V9_Reg_Id_PC);
                                parent_npc = SIM_instruction_read_input_reg(parent, V9_Reg_Id_NPC);

                                ASSERT(parent_pc.kind == Sim_Val_Integer && parent_npc.kind == Sim_Val_Integer);

                                parent_pc.u.integer = parent_npc.u.integer;
                                parent_npc.u.integer = parent_npc.u.integer + 4;
                                
                                SIM_instruction_write_input_reg(new, V9_Reg_Id_PC, parent_pc);
                                SIM_instruction_write_input_reg(new, V9_Reg_Id_NPC, parent_npc);

                                if (Sim_IE_OK != decode_instruction(sma, cp, new)) {
                                        return;
                                }

                                if (is_branch(parent)) {
                                        /* branch instruction - add speculative path */
                                        
                                        attr_value_t target = bpredict(sma, parent_pc);

                                        /* only add new spec path if we predict other than fall through */
                                        if (target.u.integer != parent_npc.u.integer) { 
                                                instruction_id_t branch = SIM_instruction_begin(cp);
                                                if (!branch) {
                                                        SIM_log_info(2, log, 0, "- reorder buffer queue full");
                                                        return;
                                                }
                                                SIM_log_info(2, log, 0, "- branch instruction - add speculative path");
                                        
                                                SIM_instruction_write_input_reg(branch, V9_Reg_Id_PC, parent_pc);
                                                SIM_instruction_write_input_reg(branch, V9_Reg_Id_NPC, target);
                                        
                                                SIM_instruction_insert(parent, branch);
                                                if (Sim_IE_OK != decode_instruction(sma, cp, branch)) {
                                                        return;
                                                }
                                        }
                                }                                
                        } else {
                                /* code exception or stalling fetches */
                                return;
                        }
                }
        }
}

void retire_instructions(sample_micro_arch_object_t *sma, conf_object_t *cp, instruction_id_t ii, int n)
{
        if (!ii || n == 0) {
                return;
        } else {
                int i;
                instruction_id_t child;
                instruction_error_t ie;
                log_object_t *log = &sma->log;

//              SIM_log_info(2, log, 0, "trying     - %s", asm_s(ii));

                if ((SIM_instruction_phase(ii) == Sim_Phase_Executed) && 
                    (SIM_instruction_speculative(ii) == 0) &&
                    (SIM_instruction_status(ii) & Sim_IS_Ready)) {
                        if (SIM_instruction_is_sync(ii) == 2 && SIM_instruction_child(ii, 0)) {
                                /* Need to retire sync 2 instruction alone in tree*/
                                instruction_id_t child;
                                while((child = SIM_instruction_child(ii, 0))) {
                                        if (SIM_instruction_squash(child) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                                return;
                                        }
                                }
                        } else if (SIM_instruction_child(ii, 1)) {
                                instruction_id_t 
                                        child0 = SIM_instruction_child(ii, 0),
                                        child1;
                                
                                SIM_log_info(2, log, 0, "- more than one child - %s", asm_s(ii));
                                
                                if (SIM_instruction_speculative(child0)) {
                                        SIM_log_info(2, log, 0, "- squashing %s", asm_s(child0));
                                        if (SIM_instruction_squash(child0) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                                return;
                                        }
                                        child1 = SIM_instruction_child(ii, 0);
                                } else {
                                        child1 = SIM_instruction_child(ii, 1);
                                }

                                if (SIM_instruction_speculative(child1)) {
                                        SIM_log_info(2, log, 0, "- squashing %s", asm_s(child1));
                                        if (SIM_instruction_squash(child1) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                                return;
                                        }
                                }
                        }

                        switch(ie = SIM_instruction_retire(ii)) {
                        case Sim_IE_OK:
                                SIM_log_info(2, log, 0, "retiring   - %s", asm_s(ii));
                                n--;
                                break;
                        case Sim_IE_Stalling:
                                SIM_log_info(2, log, 0, "stalling    - %s", asm_s(ii));
                                break;
                        case Sim_IE_Exception: {
                                instruction_id_t child;
                                SIM_log_info(2, log, 0, "- instruction got exception -> squash later and drian queue");
                                /* squash our childen */
                                while((child = SIM_instruction_child(ii, 0))) {
                                        if (SIM_instruction_squash(child) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                                return;
                                        }
                                }
                                sma->drain_queue = 1;
                                break;
                        }
                        case Sim_IE_Sync_Instruction: {
                                SIM_log_info(2, log, 0, "- sync instruction");
                                
                                if (SIM_instruction_speculative(ii)) {
                                        /* sync on wrong path -> squash */
                                        if (SIM_instruction_squash(ii) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                                return;
                                        }
                                        return;
                                }
                        }
                        default:
                                pr("Unexpected return from SIM_instruction_retire()\n");
                                return;
                        }
                }
                
                if (sma->out_of_order_retire || SIM_instruction_phase(ii) == Sim_Phase_Retired) {
                        for(i = 0; (child = SIM_instruction_child(ii, i));) {
                                retire_instructions(sma, cp, child, n);
                                if (child == SIM_instruction_child(ii, i))
                                        i++;
                        }
                }
        }
}

void run_cycle(conf_object_t *cp, sample_micro_arch_object_t *sma)
{
        instruction_id_t ii;
        instruction_error_t ie;
        log_object_t *log = &sma->log;
        int i;

        if (sma->log.log_level >= 4) {
                int i;
                for(i = 0; i < 256; i++) {
                        pr( "0x%llx ", sma->branch_table[i]);
                        if ((i & 0xf) == 0xf)
                                pr("\n");
                }
        }

#ifdef VALUE_PREDICTION
        if (sma->log.log_level >= 4) {
                int i;
                pr("\n");
                for(i = 0; i < 256; i++) {
                        pr( "0x%llx ", sma->value_prediction_table[i]);
                        if ((i & 0xf) == 0xf)
                                pr("\n");
                }
                pr("\n");
        }
#endif

        if (sma->user_drain_queue && SIM_instruction_nth_id(cp, 0) == 0) {
                SIM_log_info(1, &sma->log, 0,
                             "The queue is empty.");
                SIM_break_cycle(sma->cpu, 0);
                return;
        }

        if (sma->drain_queue && SIM_instruction_nth_id(cp, 0) == 0)
                sma->drain_queue = 0;

        /* check for interrupts */
        if (sma->interrupt_vector != Sim_PE_No_Exception) {
                switch(SIM_instruction_handle_interrupt(cp, sma->interrupt_vector)) {
                case Sim_IE_OK:
                        sma->committed_steps++;
                        SIM_log_info(2, &sma->log, 0, "- handle interrupt @ %lld (vector=%x)", 
                                  SIM_cycle_count(cp), 
                                  sma->interrupt_vector);
                        sma->interrupt_vector = Sim_PE_No_Exception;
                        sma->drain_queue = 0;
                        break;
                case Sim_IE_Interrupts_Disabled:
                        /* OK try later */
                        break;
                case Sim_IE_Illegal_Interrupt_Point: {
                        /* queue is not-empty */
                        instruction_id_t first = SIM_instruction_nth_id(cp, 0);
                        if (first && SIM_instruction_squash(first) != Sim_IE_OK) {
                                SIM_log_info(3, &sma->log, 0, 
                                             "cannot squach queue for interrupt - try next cycle");
                        }
                        sma->drain_queue = 1;
                        break;
                }
                case Sim_IE_Step_Breakpoint:
                        SIM_log_info(1, log, 0, "requested breakpoint - cycle not finished");
                        SIM_break_cycle(cp, 0);
                        sma->repost = 1;
                        return;
                        
                default:
                        pr("SIM_instruction_handle_interrupt() failed\n");
                }
        }

        /* If first instruction on wrong path squash queue */
        if ((ii = SIM_instruction_nth_id(cp, 0)) && SIM_instruction_speculative(ii)) {
                SIM_log_info(2, log, 0, "wrong path  - %s", asm_s(ii));
                if (SIM_instruction_squash(ii) != Sim_IE_OK) {
                        pr("SIM_instruction_squash failed @ %lld\n", SIM_cycle_count(cp));
                        return;
                }
                return;
        }

        /* commit instructions */
        for(i = 0; i < sma->commits_per_cycle; i++) {                
                if (!(ii = SIM_instruction_nth_id(cp, 0)))
                        break;

                if (SIM_instruction_phase(ii) == Sim_Phase_Retired) {
                        if (SIM_instruction_speculative(ii)) {
                                ASSERT_MSG(0, "retired on wrong path");
                                return;
                        } else if (SIM_instruction_child(ii, 1)) {
                                instruction_id_t 
                                        child0 = SIM_instruction_child(ii, 0),
                                        child1;

                                SIM_log_info(2, log, 0, "- more than one child - %s", asm_s(ii));
                                
                                if (SIM_instruction_speculative(child0)) {
                                        SIM_log_info(2, log, 0, "- squashing %s", asm_s(child0));
                                        if (SIM_instruction_squash(child0) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                                return;
                                        }
                                        child1 = SIM_instruction_child(ii, 0);
                                } else {
                                        child1 = SIM_instruction_child(ii, 1);
                                }

                                if (SIM_instruction_speculative(child1)) {
                                        SIM_log_info(2, log, 0, "- squashing %s", asm_s(child1));
                                        if (SIM_instruction_squash(child1) != Sim_IE_OK) {
                                                pr("SIM_instruction_squash failed\n");
                                                return;
                                        }
                                }
                        } else if (SIM_instruction_is_sync(ii) == 2 && SIM_instruction_child(ii, 0)) {
                                /* Need to commit sync 2 instruction alone in tree*/
                                if (SIM_instruction_squash(SIM_instruction_child(ii, 0)) != Sim_IE_OK) {
                                        pr("SIM_instruction_squash failed\n");
                                        return;
                                }
                        }

                        switch(ie = SIM_instruction_commit(ii)) {
                        case Sim_IE_OK:
                                sma->committed_steps++;
                                if (is_branch(ii)) {
                                        /* committed branch */
                                        attr_value_t pc = SIM_instruction_read_output_reg(ii, V9_Reg_Id_PC);
                                        attr_value_t npc = SIM_instruction_read_output_reg(ii, V9_Reg_Id_NPC);
                                        
                                        SIM_log_info(2, log, 0, "- updating "
                                                     "branch prediction "
                                                     "table[0x%02x] = 0x%llx", 
                                                  (int)((pc.u.integer >> 2) & 0xff),
                                                  (logical_address_t)npc.u.integer);
                                        sma->branch_table[(pc.u.integer >> 2) & 0xff] = npc.u.integer;
                                }
#ifdef VALUE_PREDICTION 
                                else if (SIM_instruction_type(ii) & It_Load) {
                                        reg_info_t *ri;
                                        int i;
                                        user_data_t *ud = SIM_instruction_get_user_data(ii);

                                        /* we update the value prediction table with the last loaded value */
                                        if (ud) {
                                                for(i = 0; (ri = SIM_instruction_get_reg_info(ii, i)); i++) {
                                                        if (ri->out && ri->id < 32) { /* integer out reg */
                                                                attr_value_t reg;
                                                                logical_address_t la = ud->address;
                                                                
                                                                reg = SIM_instruction_read_output_reg(ii, ri->id);
                                                                ASSERT(reg.kind == Sim_Val_Integer);
                                                                
                                                                sma->value_prediction_table[(la >> 2) & 0xff] =
                                                                        reg.u.integer;
                                                                
                                                                SIM_log_info(2, log, 0, 
                                                                          "- updating value prediction "
                                                                          "table[0x%02x] = 0x%llx",
                                                                          (int)((la >> 2) & 0xff), reg.u.integer);
                                                                break;
                                                        }
                                                }
                                                MM_FREE(ud);
                                        }
                                }
#endif 
                                SIM_log_info(2, log, 0, "committing  - %s", asm_s(ii));                       
                                break;
                        case Sim_IE_Code_Breakpoint:
                        case Sim_IE_Step_Breakpoint:
                        case Sim_IE_Hap_Breakpoint:
                                SIM_log_info(1, log, 0, "requested breakpoint - cycle not finished");
                                SIM_break_cycle(cp, 0);
                                sma->repost = 1;
                                return;
                        default: 
                                pr("SIM_instruction_commit failed %d\n", ie); return;
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

        /* retire instructions */
        retire_instructions(sma, cp, SIM_instruction_nth_id(cp, 0), sma->retires_per_cycle);

        /* execute max 4 instructions in each branch */
        if (!execute_instructions(sma, cp, SIM_instruction_nth_id(cp, 0), sma->execute_per_cycle))
                return;

        fetch_decode_instructions(sma, cp, SIM_instruction_nth_id(cp, 0));
}
static void 
my_cycle_handler(conf_object_t *cpu, sample_micro_arch_object_t *sma)
{
        SIM_log_info(4, (log_object_t *)cpu, 0, "*** cycle begin ***");

        if ((sma->cycles % 1000000) == 0)
                SIM_log_info(1, &sma->log, 0, "cycle: %08lld - steps: %08lld", 
                          sma->cycles, sma->committed_steps);

        run_cycle(cpu, sma);

        if (SIM_get_pending_exception()) {
                pr("*** Exception (%s) in run_cycle @ %lld cycles ***\n", SIM_last_error(), SIM_cycle_count(cpu));
                SIM_break_cycle(cpu, 0);
        }
        if (sma->repost) {
                SIM_time_post_cycle(cpu, 0, 0, (event_handler_t)my_cycle_handler, sma);
                sma->repost = 0;
        } else {
                SIM_time_post_cycle(cpu, 1, 0, (event_handler_t)my_cycle_handler, sma);
                sma->cycles++;
        }
        SIM_log_info(4, (log_object_t *)cpu, 0, "*** cycle end ***");
}

static void 
my_interrupt_handler(void *_sma, conf_object_t *cpu, integer_t vector)
{
        sample_micro_arch_object_t *sma = _sma;
        
        if (sma->cpu == cpu)
                sma->interrupt_vector = (int)vector;
}

static void 
instruction_squashed_handler(void *_sma, conf_object_t *cpu, void *instruction)
{
        instruction_id_t id = instruction;
        user_data_t *ud = SIM_instruction_get_user_data(id);
        sample_micro_arch_object_t *sma = _sma;
 
        SIM_log_info(3, &sma->log, 0,
                     "Instruction @ 0x%llx squashed!",
                     SIM_instruction_read_input_reg(id, V9_Reg_Id_PC).u.integer);
        if (ud) {
                MM_FREE(ud);
        }
}

static void
initial_config_hap(void *data, conf_object_t *dontcare)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)data;
        attr_value_t mode;

        mode = SIM_get_attribute(sma->cpu, "ooo-mode");

        if (strcmp(mode.u.string, "micro-architecture") != 0) {
                SIM_log_error(&sma->log, 0, 
                              "%s is not an MAI compatible processor, "
                              "make sure Simics is started with the -ma flag.",
                              sma->cpu->name);
                return;
        }

        SIM_time_post_cycle(sma->cpu, 0, 0,
			    (event_handler_t)my_cycle_handler, data);
	
        SIM_hap_add_callback("Core_Asynchronous_Trap", 
                             (obj_hap_func_t)my_interrupt_handler, data);

        SIM_hap_add_callback("Core_Instruction_Squashed",
                             (obj_hap_func_t)instruction_squashed_handler,
                             data);

        SIM_log_info(1, &sma->log, 0, "added cycle handler on %s", 
                     sma->cpu->name);
}

static set_error_t
set_cpu(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        sma->cpu = val->u.object;

        if (SIM_initial_configuration_ok()) {
                initial_config_hap(obj, NULL);
        } else {
		SIM_hap_add_callback("Core_Initial_Configuration",
                                     (obj_hap_func_t) initial_config_hap, 
                                     obj);
        }
        
        return Sim_Set_Ok;
}

static attr_value_t
get_cpu(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        if (sma->cpu) {
                ret.kind = Sim_Val_Object;
                ret.u.object = sma->cpu;
        } else {
                ret.kind = Sim_Val_Nil;
        }
        return ret;
}


static set_error_t
set_fetches_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        sma->fetches_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_fetches_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->fetches_per_cycle;
        return ret;
}

static set_error_t
set_execute_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        sma->execute_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_execute_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->execute_per_cycle;
        return ret;
}

static set_error_t
set_retires_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                     attr_value_t *idx)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        sma->retires_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_retires_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->retires_per_cycle;
        return ret;
}

static set_error_t
set_commits_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        sma->commits_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_commits_per_cycle(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->commits_per_cycle;
        return ret;
}

static set_error_t
set_out_of_order_retire(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                     attr_value_t *idx)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        sma->out_of_order_retire = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_out_of_order_retire(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->out_of_order_retire;
        return ret;
}

static conf_object_t *
sample_micro_arch_new_instance(parse_object_t *pa)
{
        sample_micro_arch_object_t *obj = MM_ZALLOC(1, sample_micro_arch_object_t);
        SIM_log_constructor(&obj->log, pa);

        obj->interrupt_vector = Sim_PE_No_Exception;

        obj->fetches_per_cycle = 4;
        obj->execute_per_cycle = 4;
        obj->retires_per_cycle = 4;
        obj->commits_per_cycle = 4;
        obj->out_of_order_retire = 0;

        return (conf_object_t *)obj;
}

static int
sample_micro_arch_delete_instance(conf_object_t *obj)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *)obj;

        SIM_time_clean(sma->cpu, Sim_Sync_Processor, (event_handler_t)my_cycle_handler, obj);
        
        SIM_hap_delete_callback("Core_Asynchronous_Trap", 
                                (obj_hap_func_t)my_interrupt_handler, 
                                obj);

        SIM_hap_delete_callback("Core_Instruction_Squashed",
                                (obj_hap_func_t)instruction_squashed_handler,
                                obj);

        MM_FREE(obj);
        return 0;
}

static set_error_t
set_dq_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->user_drain_queue = val->u.integer;

        if (sma->user_drain_queue)
                SIM_log_info(1, &sma->log, 0, "Emptying the instruction queue. "
                             "When the queue is empty, Simics will "
                             "automatically stop the simulation.");

        return Sim_Set_Ok;
}

static attr_value_t
get_dq_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        sample_micro_arch_object_t *sma = (sample_micro_arch_object_t *) obj;
        return SIM_make_attr_integer(sma->user_drain_queue);
}

DLL_EXPORT void
init_local(void)
{
        class_data_t class_data;
        conf_class_t *conf_class;

        /* initialize and register the class "sample-memhier-class" */
        memset(&class_data, 0, sizeof(class_data_t));
        class_data.new_instance = sample_micro_arch_new_instance;
        class_data.delete_instance = sample_micro_arch_delete_instance;
        class_data.description = 
                "This class demonstrates the Micro Architectural Interface. The "
                "processor modeled can fetch, execute, and commit a configurable "
                "number of instructions per cycle (by setting some "
                "attributes). Default is 4, 4, and 4 respectively. It has a simple "
                "branch-predictor that uses a hash table to lookup the target address "
                "from the address of the branch instruction. The hash table is "
                "updated for every successfully committed branch."
                "\n\n"
                "Besides speculating on the target address, the architecture also "
                "speculate fall through for every branch. This way 2 possible "
                "execution paths are created for every branch.  This makes the "
                "instruction tree into a binary tree. The number of instructions "
                "executed and fetch per cycle is actually also per branch in the "
                "instruction tree. "
                "\n\n"
                "This demo models no pipeline stages other than those found in "
                "Simics. Instructions are fetched and decoded at once making the "
                "fetch staged itself invisible. "
                "\n\n"
                "If an exception occurs the tree is drained and all the speculative "
                "instructions beyond the faulting one are discarded.";

        conf_class = SIM_register_class("sample_micro_arch", &class_data);

        /* initialize attributes */
        
        SIM_register_typed_attribute(conf_class, "cpu",
                                     get_cpu, 0, 
                                     set_cpu, 0, 
                                     Sim_Attr_Required, "o", NULL,
                                     "The CPU of the micro architecture model");

        SIM_register_typed_attribute(conf_class, "fetches_per_cycle", 
                                     get_fetches_per_cycle, 0, 
                                     set_fetches_per_cycle, 0, 
                                     Sim_Attr_Optional, "i", NULL,
                                     "Number of instructions to fetch each cycle.");
        
        SIM_register_typed_attribute(conf_class, "execute_per_cycle", 
                                     get_execute_per_cycle, 0, 
                                     set_execute_per_cycle, 0, 
                                     Sim_Attr_Optional, "i", NULL,
                                     "Number of instructions to execute each cycle per instruction tree branch.");
        
        SIM_register_typed_attribute(conf_class, "retires_per_cycle", 
                                     get_retires_per_cycle, 0, 
                                     set_retires_per_cycle, 0, 
                                     Sim_Attr_Optional, "i", NULL,
                                     "Number of instructions to retire each cycle per instruction tree branch.");
        
        SIM_register_typed_attribute(conf_class, "out_of_order_retire", 
                                     get_out_of_order_retire, 0,
                                     set_out_of_order_retire, 0, 
                                     Sim_Attr_Optional, "i", NULL,
                                     "Number of instructions to retire each cycle per instruction tree branch.");

        SIM_register_typed_attribute(conf_class, "commits_per_cycle",
                                     get_commits_per_cycle, 0, 
                                     set_commits_per_cycle, 0, 
                                     Sim_Attr_Optional, "i", NULL,
                                     "Number of instructions to commit each cycle.");

        SIM_register_typed_attribute(conf_class, "drain-queue", 
                                     get_dq_attribute,0, 
                                     set_dq_attribute, 0, 
                                     Sim_Attr_Session, "i", NULL,
                                     "Tell the model to stop fetching so that the "
                                     "instruction queue will empty itself. Useful "
                                     "to save a checkpoint.");

        
}
