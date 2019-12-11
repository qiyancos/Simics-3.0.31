/*
  micro-arch-p4.c

  Copyright 1998-2007 Virtutech AB
  
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

/*
  log:
  0: nothing
  1: cycle count
  2: interrupts
  3: faults and traps
  4: everything
*/

#include <stdlib.h>
#include <assert.h>

/* to get the correct enums */
#define TARGET_X86
#define SIM_FAST_ACCESS_FUNCTIONS

#include <simics/api.h>
#include <simics/utils.h>
#include <simics/arch/x86.h>

/* this performs more checks for error returned */
#undef DEBUG

/* check if an instruction has a REP prefix in which case it branches to
   itself */
#define HAS_REP_PREFIX(sma, ii)                                 \
((SIM_instruction_get_field_value((ii), "prefix")   \
  & (SIM_DI_PREFIX_F2_BIT | SIM_DI_PREFIX_F3_BIT))              \
 && !(SIM_instruction_type(ii) & It_SSE))

typedef enum {
        Sma_Ok,
        Sma_Ok_Leave,
        Sma_Sync_1,
        Sma_Sync_2,
        Sma_Not_Decoded,
        Sma_No_Instruction,
        Sma_Not_Executed,
        Sma_Executed,
        Sma_Interrupt,
        Sma_Fault,
        Sma_Break
} sma_error_t;

typedef struct x86_ma_object {
        log_object_t     log;
        conf_object_t   *cpu;
        
        int interrupt_pending; /* received an interrupt through hap */
        int interrupt_now; /* received an interrupt now in previous cycle */
        int drain_queue; /* no fetch is allowed when queue is drained */
        int user_drain; /* no fetch is allowed by user */

        /* simple from-to branch table */
        struct {
                uinteger_t from;
                uinteger_t to;
        } branch_table[256];

        /* call/ret stack prediction */
        uinteger_t       callret_stack[16];
        int              crs_index;
        
        int              branch_miss; /* current counter */
        int              branch_miss_penalty; /* total penalty when missing a
                                                 branch prediction */

        int              fetches_per_cycle;
        int              execute_per_cycle;
        int              retire_per_cycle;
        int              commits_per_cycle;
        int              max_in_flight;
        int              in_flight; /* current counter */

        instruction_id_t last_in_queue; /* last instruction in the queue */
        instruction_id_t start_execute; /* first non-executed instruction */

        integer_t        commit_steps; /* how many steps have been committed */

        int              step_bp; /* did we get a step break last time? */
        int              step_bp_commit; /* how many instr. were committed? */

        integer_t        stat_decode;
        integer_t        stat_execute;
        integer_t        stat_retire;
        integer_t        stat_commit;
        integer_t        stat_in_flight;
        
        integer_t        stat_exception;
        integer_t        stat_interrupt;
        integer_t        stat_squash;

        integer_t        dbg_counter;

} x86_ma_object_t;

static int
squash_rec(x86_ma_object_t *sma, instruction_id_t ii)
{
        instruction_id_t child;
        int ret = 0;

        if (!ii)
                return 0;

        child = SIM_instruction_child(ii, 0);
        ret |= squash_rec(sma, child);

        if (SIM_instruction_squash(ii) != Sim_IE_OK)
                return 1;

        sma->in_flight -= 1;
        return ret;
}

static int
squash_all_children(x86_ma_object_t *sma, instruction_id_t ii)
{
        instruction_id_t child;

        sma->stat_squash++;

        child = SIM_instruction_child(ii, 0);
        if (squash_rec(sma, child))
                return 1;
        
        /* we squashed all children so the last one is the current 
           instruction */
        sma->last_in_queue = ii;
        return 0;
}

static int
squash_instruction_and_children(x86_ma_object_t *sma, instruction_id_t ii)
{
        if (squash_all_children(sma, ii))
                return 1;
        if (SIM_instruction_squash(ii) != Sim_IE_OK)
                return 1;
        sma->in_flight -= 1;

        /* we don't know what the last in queue is here */
        return 0;
}

/* if last_in_queue is unknown, find it by going through the list */
static instruction_id_t
get_last_in_queue(x86_ma_object_t *sma)
{
        instruction_id_t prev, next;
        
        prev = SIM_instruction_nth_id(sma->cpu, 0);
        if (!prev)
                return 0;

        next = prev;
        do {
                prev = next;
                next = SIM_instruction_child(prev, 0);
        } while (next != 0);
        
        return prev;
}

/* take care of decoding the last instruction in the tree */
static instruction_error_t
decode_instruction(x86_ma_object_t *sma)
{
        instruction_error_t ie;

        if (!sma->last_in_queue) {
                SIM_log_error(&sma->log, 0,
                              "decode_instruction called with no instruction");
                ASSERT(0);
        }

        sma->stat_decode++;
        switch(ie = SIM_instruction_decode(sma->last_in_queue)) {
        case Sim_IE_OK:
                /* update info */
                if (SIM_instruction_is_sync(sma->last_in_queue) == 2)
                        sma->drain_queue = 1;
                SIM_instruction_opcode(sma->last_in_queue);
                break;
        case Sim_IE_Unresolved_Dependencies:
                break;
        case Sim_IE_Stalling:
                break;
        case Sim_IE_Fault:
                sma->drain_queue = 1;
                break;
        case Sim_IE_Interrupt:
                if (squash_instruction_and_children(
                            sma, SIM_instruction_nth_id(sma->cpu, 0))) {
                        SIM_clear_exception();
                        sma->last_in_queue = get_last_in_queue(sma);
                }
                else {
                        sma->last_in_queue = 0;
                }
                sma->start_execute = 0;
                sma->interrupt_now = 1;
                sma->drain_queue = 1;
                break;
        default:
                ASSERT_MSG(0, "decode_instruction: unknow return value");
        }

        return ie;
}

#define IT_MASK (It_Relbranch | It_Call | It_Return   \
                 |  It_Varbranch | It_Absbranch)

FORCE_INLINE int
is_predicted_branch(conf_object_t *cpu, instruction_id_t ii)
{
        return (SIM_instruction_type(ii) & IT_MASK);
}

static uinteger_t
get_predicted_pc(x86_ma_object_t *sma, instruction_id_t ii) 
{
        uinteger_t index;
        attr_value_t parent_pc;

        parent_pc = SIM_instruction_read_input_reg(ii, X86_Reg_Id_PC);
        
        /* check that we're predicting with the right pc */
        index = (parent_pc.u.integer >> 2) & UINT64_C(0xff);
        if (parent_pc.u.integer == sma->branch_table[index].from)
                return sma->branch_table[index].to;
        else        
                return -1;
}

FORCE_INLINE void
set_predicted_pc(x86_ma_object_t *sma, uinteger_t from, uinteger_t to) 
{
        uinteger_t index;

        index = (from >> 2) & UINT64_C(0xff);
        sma->branch_table[index].from = from;
        sma->branch_table[index].to = to;
}

FORCE_INLINE int
is_call(conf_object_t *cpu, instruction_id_t ii)
{
        return (SIM_instruction_type(ii) & It_Call);
}

FORCE_INLINE int
is_ret(conf_object_t *cpu, instruction_id_t ii)
{
        return (SIM_instruction_type(ii) & It_Return);
}

/* when doing a call, store the final pc for ret */
FORCE_INLINE void
set_predicted_call_pc(x86_ma_object_t *sma, integer_t pc) 
{
        sma->callret_stack[sma->crs_index] = pc;
        sma->crs_index = (sma->crs_index + 1) & 0xF;
}

FORCE_INLINE uinteger_t
get_predicted_ret_pc(x86_ma_object_t *sma) 
{
        uinteger_t ret;

        sma->crs_index = (sma->crs_index - 1) & 0xF;
        ret= sma->callret_stack[sma->crs_index];
        sma->callret_stack[sma->crs_index] = -1;

        return ret;
}

static uinteger_t
speculate_pc_on_fetch(x86_ma_object_t *sma, instruction_id_t parent)
{
        attr_value_t pc;

        /* no parent, no speculation */
        if (!parent)
                return (uinteger_t) -1;

        /* parent executed, no speculation */
        if (SIM_instruction_phase(parent) >= Sim_Phase_Executed)
                return (uinteger_t) -1;

        /* check if the instruction has a rep prefix and is not SSE
           in which case we predict branch to itself */
        if (HAS_REP_PREFIX(sma, parent)) {
                pc = SIM_instruction_read_input_reg(parent, X86_Reg_Id_PC);
                return pc.u.integer;
        }
        else if (is_ret(sma->cpu, parent)) {
                return get_predicted_ret_pc(sma);
        }
        else if (is_predicted_branch(sma->cpu, parent)) {
                return get_predicted_pc(sma, parent);
        }
        else {
                SIM_clear_exception();
                return (uinteger_t) -1;
        }
}

static void
fetch_instructions(x86_ma_object_t *sma)
{
        instruction_id_t ii, parent;
        instruction_error_t ie = Sim_IE_OK;
        attr_value_t next_pc;
        uinteger_t pc;
        int i;

        /* start by checking that the last instruction is at least 
           decoded before fetching more */
        ii = sma->last_in_queue;
        if (unlikely(ii != NULL)) {
                if (SIM_instruction_phase(ii) < Sim_Phase_Decoded)
                        ie = decode_instruction(sma);
        }

        /* should we fetch more? */
        if (unlikely(sma->drain_queue))
                return;

        /* if the user wants to empty the queue ... */
        if (unlikely(sma->user_drain))
                return;

        /* are we paying for a branch miss? */
        if (unlikely(sma->branch_miss)) {
                sma->branch_miss--;
                return;
        }

        for (i=0;
             (i<sma->fetches_per_cycle
              && sma->in_flight < sma->max_in_flight
              && ie == Sim_IE_OK
              && sma->drain_queue == 0);
             i++) {
                
                parent = ii;
                
                ii = SIM_instruction_begin(sma->cpu);
                if (unlikely(!ii)) {

                        attr_value_t ret;

                        ret = SIM_get_attribute(sma->cpu, 
                                                "reorder_buffer_size");
                        if (ret.kind == Sim_Val_Integer &&
                            ret.u.integer < sma->max_in_flight) {
                                SIM_log_error(&sma->log, 0,
                                              "The reorder_buffer_size "
                                              "attribute in the cpu must "
                                              "be at least as big as the "
                                              "maximum number of "
                                              "instruction in flight. "
                                              "Stopping simulation.");
                                SIM_break_cycle(sma->cpu, 0);
                                return;
                        }
                        else {
                                /* this should not happen */
                                ASSERT(0);
                        }
                }

                sma->in_flight += 1;
                SIM_instruction_insert(parent, ii);
                
                sma->last_in_queue = ii;
                pc = speculate_pc_on_fetch(sma, parent);
                
                if (pc != (uinteger_t) -1) {
                        next_pc.kind = Sim_Val_Integer;
                        next_pc.u.integer = pc;
                        SIM_instruction_write_input_reg(
                                ii, X86_Reg_Id_PC, next_pc);
                }

                ie = decode_instruction(sma);
        }
}

static sma_error_t
update_branch_prediction(x86_ma_object_t *sma, instruction_id_t ii)
{
        instruction_id_t ch; /* ii's child */
        attr_value_t parent_pc, child_pc;

        /* check if it was a predicted branch */
        if (is_predicted_branch(sma->cpu, ii) 
            || is_ret(sma->cpu, ii) 
            || HAS_REP_PREFIX(sma, ii)) {
                                
                parent_pc = SIM_instruction_read_input_reg(ii, X86_Reg_Id_PC);
                if (parent_pc.kind != Sim_Val_Integer) {
                        ASSERT_MSG(0, "No parent_pc");
                }

                child_pc = SIM_instruction_read_output_reg(ii, X86_Reg_Id_PC);
                if (child_pc.kind != Sim_Val_Integer) {
                        ASSERT_MSG(0, "No child_pc");
                }
                
                /* update the branch predictor table */
                if (is_predicted_branch(sma->cpu, ii)
                    || is_call(sma->cpu, ii))
                        set_predicted_pc(sma, 
                                         parent_pc.u.integer, 
                                         child_pc.u.integer);
                                
                /* if it's a call, add the ret pc to the stack */
                if (is_call(sma->cpu, ii)) {
                        set_predicted_call_pc(
                                sma,
                                parent_pc.u.integer 
                                + SIM_instruction_length(ii));
                }

                /* check if the next instruction has the right pc */
                ch = SIM_instruction_child(ii, 0);
                if (!ch)
                        return Sma_Ok;

                /* read what the child has as pc input register */
                parent_pc = SIM_instruction_read_input_reg(ch, X86_Reg_Id_PC);

                if (parent_pc.kind != Sim_Val_Integer) {
                        return Sma_Ok;
                }

                /* misspredicted? */
                if (child_pc.u.integer != parent_pc.u.integer) {
                        squash_all_children(sma, ii);
                        sma->branch_miss = sma->branch_miss_penalty;
                        sma->drain_queue = 0;
                }
        }
        
        return Sma_Ok;
}

static sma_error_t
execute_single_instruction(x86_ma_object_t *sma, instruction_id_t ii,
                           int all_executed)
{
        instruction_error_t ie;
        instruction_phase_t phase;
        instruction_status_t status;
        int sync;

        if (!ii)
                return Sma_No_Instruction;

        phase = SIM_instruction_phase(ii);
        if (phase >= Sim_Phase_Executed)
                return Sma_Executed;

        status = SIM_instruction_status(ii);
        if (status == Sim_IS_Interrupt) {
                ASSERT_MSG(0, "Interrupt should have been handled before.");
        }

        /* stalling? */
        if ((status & (Sim_IS_Stalling | Sim_IS_Ready)) == Sim_IS_Stalling) {
                return Sma_Not_Executed;
        }

        /* unresolved dependencies? */
        if (status == Sim_IS_Waiting) {
                return Sma_Not_Executed;
        }
        
        /* check if a fault is waiting */
        if (status == Sim_IS_Faulting || status == Sim_IS_Trap) {
                /* is it the first in the queue? */
                if (!(SIM_instruction_nth_id(sma->cpu, 0) == ii))
                        return Sma_Fault;
        }
        else {
                if (phase < Sim_Phase_Decoded)
                        return Sma_Not_Decoded;

                sync = SIM_instruction_is_sync(ii);
                if (sync == 2) {
                        /* is it the first in the queue? */
                        if (!(SIM_instruction_nth_id(sma->cpu, 0) == ii))
                                return Sma_Sync_2;
                }

                if (sync == 1) {
                        /* if not all previous instructions have been executed,
                           we can not execute that one */
                        if (!all_executed)
                                return Sma_Sync_1;
                }
        }

        /* now handle the execution */
        if (status == Sim_IS_Faulting || status == Sim_IS_Trap) {

                if (status == Sim_IS_Faulting)
                        SIM_log_info(4, &sma->log, 0, "handle fault/trap "
                                     "(cycle %lld, steps = %lld)",
                                     SIM_cycle_count(sma->cpu),
                                     SIM_step_count(sma->cpu));

                sma->stat_exception++;
                ie = SIM_instruction_handle_exception(ii);
                if (ie != Sim_IE_OK) {
                        ASSERT_MSG(0, "handling exception here should "
                                   "not fail.");
                }
                sma->drain_queue = 0;
                sma->last_in_queue = 0;
                sma->start_execute = 0;
                sma->in_flight--;
                if (SIM_instruction_end(ii) != Sim_IE_OK) {
                        ASSERT_MSG(0, "SIM_instruction_end failed\n");
                }

                sma->commit_steps++;

                /* we need to go out because 'ii' is not a valid instruction
                   anymore */
                return Sma_Ok_Leave;
        }
        else {
                sma->stat_execute++;
                ie = SIM_instruction_execute(ii);

                switch(ie) {
                case Sim_IE_OK:
                        return update_branch_prediction(sma, ii);
                case Sim_IE_Unresolved_Dependencies:
                        /* should not happen since we tested that above */
                case Sim_IE_Stalling:
                        return Sma_Not_Executed;
                case Sim_IE_Trap:
                case Sim_IE_Fault:
                        squash_all_children(sma, ii);
                        sma->drain_queue = 1;
                        return Sma_Fault;
                case Sim_IE_Interrupt:
                        /* interrupt now */
                        if (squash_instruction_and_children(
                                    sma, SIM_instruction_nth_id(sma->cpu, 0))) {
                                SIM_clear_exception();
                                sma->last_in_queue = get_last_in_queue(sma);
                        }
                        else
                                sma->last_in_queue = 0;
                        sma->start_execute = 0;
                        sma->interrupt_now = 1;
                        sma->drain_queue = 1;
                        return Sma_Interrupt;
                default:
                        ASSERT_MSG(0, "execute_instruction: unknow return "
                                   "value");
                }
        }
        
        /* never reached */
        return Sma_Ok;
}

static void
execute_instructions(x86_ma_object_t *sma)
{
        instruction_id_t ii;
        sma_error_t se;
        int i;
        int go_on  = 1;
        int all_executed  = 1;

        /* start from where we remember */
        if (!sma->start_execute) {
                ii = SIM_instruction_nth_id(sma->cpu, 0);
        }
        else {
                ii = sma->start_execute;
                sma->start_execute = 0;
        }
        i = 0;

        while (i<sma->execute_per_cycle && ii != 0 && go_on) {

                se = execute_single_instruction(sma, ii, all_executed);

                switch(se) {
                case Sma_Break:
                        /* we got a commited step breakpoint when executing */
                        /* FALLTHROUGH */
                case Sma_Fault:
                        /* we got a fault when executing */
                        /* FALLTHROUGH */
                case Sma_Sync_2:
                        /* we need to wait for this one to commit */
                        sma->start_execute = 0;
                        go_on = 0;
                        break;

                case Sma_Not_Decoded:
                        /* this instruction is not decoded yet */
                        if (!sma->start_execute)
                                sma->start_execute = ii;
                        go_on = 0;
                        break;

                case Sma_Interrupt:
                        /* we got an interrupt now - we return
                           directly to avoid running
                           SIM_instruction_child */
                        sma->start_execute = 0;
                        return;
                        
                case Sma_No_Instruction:
                        ASSERT_MSG(0, "No instruction to execute, this should "
                                   "be caught before.");
                        break;

                case Sma_Not_Executed:
                        /* this instruction couldn't be executed completely */
                        all_executed = 0;
                        if (!sma->start_execute)
                                sma->start_execute = ii;
                        i++;
                        break;

                case Sma_Sync_1:
                        /* not all previous instruction are executed */
                        all_executed = 0;
                        break;

                case Sma_Executed:
                        /* instruction already executed */
                        break;

                case Sma_Ok:
                        /* instruction executed ok */
                        i++;
                        break;

                case Sma_Ok_Leave:
                        /* instruction executed ok but no more instruction
                           should be executed */
                        sma->start_execute = 0;
                        return;
                }

                ii = SIM_instruction_child(ii, 0);
        }
}

static void
retire_stores(x86_ma_object_t *sma)
{
        instruction_id_t ii;
        instruction_phase_t phase;
        int go_on  = 1;
        instruction_error_t ie;
        int i = 0;
        
        ii = SIM_instruction_nth_id(sma->cpu, 0);
        
        while (i<sma->retire_per_cycle && ii != 0 && go_on) {
                
                phase = SIM_instruction_phase(ii);
                if (phase == Sim_Phase_Executed) {
                        
                        sma->stat_retire++;
                        ie = SIM_instruction_retire(ii);
                        
                        switch(ie) {
                        case Sim_IE_OK:
                        case Sim_IE_Stalling:
                                i++;
                                break;
                        case Sim_IE_Speculative:
                                /* no need to continue afterwards */
                                go_on = 0;
                                if (ii == SIM_instruction_nth_id(sma->cpu, 0)) {
                                        SIM_log_error(
                                                &sma->log, 0,
                                                "Root instruction is "
                                                "speculative!");
                                        SIM_break_cycle(sma->cpu, 0);
                                }
                                break;
                        case Sim_IE_Unresolved_Dependencies:
                        case Sim_IE_Trap:
                        case Sim_IE_Fault:
                        case Sim_IE_Interrupt:
                        default:
                                ASSERT_MSG(0, "retire_instruction: unknow "
                                           "return value");
                        }
                }
                        
                ii = SIM_instruction_child(ii, 0);
        }
}

static void
run_cycle(x86_ma_object_t *sma)
{
        instruction_id_t ii, tmp;
        instruction_error_t ie;
        int i;
        int go_on;

        if (sma->user_drain && sma->in_flight == 0) {
                SIM_log_info(1, &sma->log, 0, "The queue is empty.");
                SIM_break_cycle(sma->cpu, 0);
                return;
        }

        if (sma->drain_queue && SIM_instruction_nth_id(sma->cpu, 0) == 0)
                sma->drain_queue = 0;

        /* interrupt_now; squash all not committed instructions,
           handle the interrupt and continue to execute */
        if (sma->interrupt_now) {
                /* handle the interrupt */
                ie = SIM_instruction_handle_interrupt(sma->cpu, 0);
                switch (ie) {
                case Sim_IE_OK:
                        sma->stat_interrupt++;
                        SIM_log_info(3, &sma->log, 0, "handle_interrupt (now)"
                                     " (cycle %lld, steps = %lld)",
                                     SIM_cycle_count(sma->cpu),
                                     SIM_step_count(sma->cpu));
                        sma->drain_queue = 0;
                        sma->interrupt_now = 0;
                        sma->commit_steps++;
                        break;
                case Sim_IE_Illegal_Interrupt_Point:
                        /* squash everything now - this could fail if we have
                           a executed sync instruction */
                        if (squash_instruction_and_children(
                                    sma, SIM_instruction_nth_id(sma->cpu, 0))) {
                                /* find which is last now */
                                SIM_clear_exception();
                                sma->last_in_queue = get_last_in_queue(sma);
                                sma->start_execute = 0;
                                sma->drain_queue = 1; /* prevent more instr. to
                                                         come in */
                        }
                        else {
                                sma->last_in_queue = 0;
                                sma->start_execute = 0;
                                /* next cycle we handle the interrupt */
                                return;
                        }
                        break;
                case Sim_IE_No_Exception:
                        ASSERT_MSG(0, "interrupt_now; SIM_instruction_handle_i"
                                   "nterrupt: Sim_IE_No_Exception");
                case Sim_IE_Interrupts_Disabled:
                        ASSERT_MSG(0, "interrupt_now; SIM_instruction_handle_i"
                                   "nterrupt: Sim_IE_Interrupts_Disabled");
                case Sim_IE_Null_Pointer:
                        ASSERT_MSG(0, "interrupt_now; SIM_instruction_handle_i"
                                   "nterrupt: Sim_IE_Null_Pointer");
                default:
                        ASSERT_MSG(0, "interrupt_now; SIM_instruction_handle_i"
                                   "nterrupt: unknow error.");
                }
        }

        /* interrupt pending */
        if (sma->interrupt_pending) {
                printf("Handling interrupt\n");
                ie = SIM_instruction_handle_interrupt(sma->cpu, 0);
                switch (ie) {
                case Sim_IE_OK:
                        sma->stat_interrupt++;
                        SIM_log_info(3, &sma->log, 0, "handle_interrupt (done)"
                                     " (cycle %lld, steps = %lld)",
                                     SIM_cycle_count(sma->cpu),
                                     SIM_step_count(sma->cpu));
                        sma->interrupt_pending = 0;
                        sma->commit_steps++;
                        break;

                case Sim_IE_Interrupts_Disabled:
                        /* we can't do anything right now */
                        break;
                        
                case Sim_IE_Illegal_Interrupt_Point:
                        /* squash everything now - this could fail if we have
                           a executed sync instruction */
                        if (squash_instruction_and_children(
                                    sma, SIM_instruction_nth_id(sma->cpu, 0))) {
                                /* find which is last now */
                                SIM_clear_exception();
                                sma->last_in_queue = get_last_in_queue(sma);
                                sma->start_execute = 0;
                                sma->drain_queue = 1; /* prevent more instr. to
                                                         come in */
                        }
                        else {
                                sma->last_in_queue = 0;
                                sma->start_execute = 0;
                                /* next cycle we handle the interrupt */
                                return;
                        }
                        break;

                case Sim_IE_No_Exception:
                        ASSERT_MSG(0, "interrupt_pending; SIM_instruction_"
                                   "handle_interrupt: Sim_IE_No_Exception");
                case Sim_IE_Null_Pointer:
                        ASSERT_MSG(0, "interrupt_pending; SIM_instruction_"
                                   "handle_interrupt: Sim_IE_Null_Pointer");
                default:
                        ASSERT_MSG(0, "interrupt_pending; SIM_instruction_"
                                   "handle_interrupt: default");
                }
        }

        /* commit instructions */
        go_on = 1;
        tmp = 0;
        ii = SIM_instruction_nth_id(sma->cpu, 0);

        if (sma->step_bp) {
                i = sma->step_bp_commit;
                sma->step_bp = 0;
        }
        else {
                i = 0;
        }

        for (; i<sma->commits_per_cycle && go_on && ii != 0; i++) {
                
                if (SIM_instruction_phase(ii) == Sim_Phase_Retired) {
                        
                        /* get the eventual child before commit, 
                           because it won't be possible after */
                        tmp = SIM_instruction_child(ii, 0);
                        sma->stat_commit++;
                        ie = SIM_instruction_commit(ii);
                        switch (ie) {
                        case Sim_IE_OK:
                                sma->commit_steps++;
                                
                                if (SIM_instruction_is_sync(ii) == 2)
                                        sma->drain_queue = 0;

                                if (!tmp) {
                                        sma->start_execute = 0;
                                        sma->last_in_queue = 0;
                                }
                                sma->in_flight -= 1;
                                break;
                        case Sim_IE_Mem_Breakpoint:
                        case Sim_IE_Step_Breakpoint:
                        case Sim_IE_Hap_Breakpoint:
                        case Sim_IE_Code_Breakpoint:
                                sma->step_bp = 1;
                                sma->step_bp_commit = i;
                                SIM_break_cycle(sma->cpu, 0);
                                return;
                        default:
                                ASSERT_MSG(0, "SIM_instruction_commit failed");
                        }

                        if (SIM_instruction_end(ii) != Sim_IE_OK) {
                                fprintf(stderr, "SIM_instruction_end failed\n");
                                return;
                        }

                        ii = SIM_instruction_nth_id(sma->cpu, 0);
                }
                else 
                        go_on = 0;
        }

#ifdef DEBUG
        if (SIM_clear_exception()) {
                SIM_log_error(&sma->log, 0, "exception after commit\n");
                SIM_break_cycle(sma->cpu, 0);
        }
#endif

        retire_stores(sma);

#ifdef DEBUG
        if (SIM_clear_exception()) {
                SIM_log_error(&sma->log, 0, "exception after retire\n");
                SIM_break_cycle(sma->cpu, 0);
        }
#endif

        execute_instructions(sma);

#ifdef DEBUG
        if (SIM_clear_exception()) {
                SIM_log_error(&sma->log, 0, "exception after execute\n");

                /* this is the most probable cause of problem, set it to 0
                   to allow to continue */
                sma->start_execute = 0;
                SIM_break_cycle(sma->cpu, 0);
        }
#endif

        fetch_instructions(sma);

#ifdef DEBUG
        if (SIM_clear_exception()) {
                SIM_log_error(&sma->log, 0, "exception after fetch\n");
                SIM_break_cycle(sma->cpu, 0);
        }
#endif

        sma->stat_in_flight += sma->in_flight;
}

static void 
my_cycle_handler(conf_object_t *obj, void *nothing)
{
        x86_ma_object_t *sma = (x86_ma_object_t *)obj;

        run_cycle(sma);

        sma->dbg_counter += 1;
        if ((sma->dbg_counter & 0xFFFF) == 0)
                SIM_log_info(2, &sma->log, 0, "cycle: %lld, steps: %lld", 
                             SIM_cycle_count(sma->cpu), 
                             SIM_step_count(sma->cpu));
        
        if (SIM_get_pending_exception()) {
                SIM_log_error(
                        &sma->log, 0,
                        "*** Exception (%s) in run_cycle @ %lld cycles ***\n",
                        SIM_last_error(), 
                        SIM_cycle_count(sma->cpu));
                SIM_break_cycle(sma->cpu, 0);
        }

        if (sma->step_bp) {
                /* post ourselves in the same cycle to go on */
                SIM_time_post_cycle(obj, 0, 0,
                                    (event_handler_t) my_cycle_handler,
                                    NULL);
        }
        else {
                /* post ourselves next cycle */
                SIM_time_post_cycle(obj, 1, 0,
                                    (event_handler_t) my_cycle_handler,
                                    NULL);
        }
}

static const char *
my_cycle_handler_describe_event(conf_object_t *obj, event_handler_t func, 
                                void *info)
{
        if (func == (event_handler_t)my_cycle_handler)
                return "p4-model cycle handler event";

        return NULL;
}

static void 
my_interrupt_handler(void *obj, void *cpu, integer_t vector)
{
        printf("got interrupt %x\n", (int)vector);
        x86_ma_object_t *sma = obj;
        sma->interrupt_pending = 1;
}

static void
x86_ma_finalize_instance(conf_object_t *data)
{
        x86_ma_object_t *sma;
        attr_value_t ret;
        conf_object_t *cpu_obj;
        
        sma = (x86_ma_object_t *) data;
        cpu_obj = (conf_object_t *) sma->cpu;

        /* check if the processor is x86/amd64 */
        SIM_get_interface(cpu_obj, X86_INTERFACE);
        if (SIM_clear_exception()) {
                SIM_log_info(1, &sma->log, 0,
                             "'%s' is not an x86 processor, disabling "
                             "processor timing model", cpu_obj->name);
                return;
        }

        /* check if the processor is MAI */
        ret = SIM_get_attribute(cpu_obj, "ooo-mode");
        if (ret.kind != Sim_Val_String 
            || strcmp(ret.u.string, "micro-architecture") != 0) {
                SIM_log_info(1, &sma->log, 0,
                             "'%s' is not an MAI processor, disabling "
                             "processor timing model", cpu_obj->name);
        }
        else {
                /* patch the queue if no set yet */
                ret = SIM_get_attribute(&sma->log.obj, "queue");
                if (ret.kind != Sim_Val_Object) {
                        ret.kind = Sim_Val_Object;
                        ret.u.object = sma->cpu;
                        SIM_set_attribute(&sma->log.obj, "queue", &ret);
                }
                
                SIM_time_post_cycle(&sma->log.obj, 0, 0,
                                    (event_handler_t)my_cycle_handler, NULL);
                SIM_hap_add_callback_obj(
                        "Core_Asynchronous_Trap", 
                        cpu_obj,
                        0,
                        (obj_hap_func_t) my_interrupt_handler,
                        data);
        }
}

static conf_object_t *
x86_ma_new_instance(parse_object_t *pa)
{
        x86_ma_object_t *sma;
        int i;
        
        sma = MM_ZALLOC(1, x86_ma_object_t);
        SIM_log_constructor(&sma->log, pa);

        sma->branch_miss_penalty = 16;

        sma->fetches_per_cycle = 2;
        sma->execute_per_cycle = 16;
        sma->retire_per_cycle = 4;
        sma->commits_per_cycle = 2;
        sma->max_in_flight = 32;

        for (i=0; i<256; i++)
                sma->branch_table[i].from = -1;

        return (conf_object_t *)sma;
}

static int
x86_ma_delete_instance(conf_object_t *obj)
{
        MM_FREE(obj);
        return 0;
}

static set_error_t
set_fpc_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->fetches_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_fpc_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->fetches_per_cycle;

        return ret;
}

static set_error_t
set_epc_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->execute_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_epc_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->execute_per_cycle;

        return ret;
}

static set_error_t
set_rpc_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->retire_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_rpc_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->retire_per_cycle;

        return ret;
}

static set_error_t
set_cpc_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->commits_per_cycle = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_cpc_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->commits_per_cycle;

        return ret;
}

static set_error_t
set_mif_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->max_in_flight = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_mif_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->max_in_flight;

        return ret;
}

static set_error_t
set_bmp_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->branch_miss_penalty = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_bmp_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->branch_miss_penalty;

        return ret;
}

static set_error_t
set_cs_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->commit_steps = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_cs_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->commit_steps;

        return ret;
}

static set_error_t
set_dq_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;

        sma->user_drain = val->u.integer;

        if (sma->user_drain)
                SIM_log_info(1, &sma->log, 0, "Emptying the instruction queue. "
                             "When the queue is empty, Simics will "
                             "automatically stop the simulation.");

        return Sim_Set_Ok;
}

static attr_value_t
get_dq_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = sma->user_drain;

        return ret;
}

static set_error_t
set_cpu_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val,
                  attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;

        sma->cpu = val->u.object;
        return Sim_Set_Ok;
}

static attr_value_t
get_cpu_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        x86_ma_object_t *sma = (x86_ma_object_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Object;
        ret.u.object = sma->cpu;

        return ret;
}

DLL_EXPORT void
init_local(void)
{
        class_data_t class_data;
        conf_class_t *conf_class;
        event_poster_interface_t *event_poster_interface;

        memset(&class_data, 0, sizeof class_data);
        class_data.new_instance = x86_ma_new_instance;
        class_data.finalize_instance = x86_ma_finalize_instance;
        class_data.delete_instance = x86_ma_delete_instance;
        class_data.description = 
                "sample-micro-arch-x86 is a sample processor timing model "
                "for x86 MAI. It drives an x86 out-of-order processor with "
                "a simple pipeline and branch prediction.";

        conf_class = SIM_register_class("sample_micro_arch_x86", &class_data);

        event_poster_interface = MM_ZALLOC(1, event_poster_interface_t);
        event_poster_interface->describe_event = 
                my_cycle_handler_describe_event;
        SIM_register_interface(conf_class, EVENT_POSTER_INTERFACE, 
                               event_poster_interface);

        /* initialize attributes */
        SIM_register_attribute(conf_class, "fetches-per-cycle", 
                               get_fpc_attribute,0, 
                               set_fpc_attribute, 0, 
                               Sim_Attr_Optional,
                               "Number of fetches allowed per cycle.");

        SIM_register_attribute(conf_class, "executes-per-cycle", 
                               get_epc_attribute,0, 
                               set_epc_attribute, 0, 
                               Sim_Attr_Optional,
                               "Number of execution phases allowed per cycle.");

        SIM_register_attribute(conf_class, "retires-per-cycle", 
                               get_rpc_attribute,0, 
                               set_rpc_attribute, 0, 
                               Sim_Attr_Optional,
                               "Number of store retiring allowed per cycle.");

        SIM_register_attribute(conf_class, "commits-per-cycle", 
                               get_cpc_attribute,0, 
                               set_cpc_attribute, 0, 
                               Sim_Attr_Optional,
                               "Number of commits allowed per cycle.");

        SIM_register_attribute(conf_class, "max-in-flight", 
                               get_mif_attribute,0, 
                               set_mif_attribute, 0, 
                               Sim_Attr_Optional,
                               "Maximum number of instructions in-flight.");

        SIM_register_attribute(conf_class, "branch-miss-penalty", 
                               get_bmp_attribute,0, 
                               set_bmp_attribute, 0, 
                               Sim_Attr_Optional,
                               "Penalty taken when mispredicting a branch "
                               "(no fetch is performed during this penalty "
                               "time).");

        SIM_register_attribute(conf_class, "committed-steps", 
                               get_cs_attribute,0, 
                               set_cs_attribute, 0, 
                               Sim_Attr_Session,
                               "Committed steps since the model started.");

        SIM_register_attribute(conf_class, "drain-queue", 
                               get_dq_attribute,0, 
                               set_dq_attribute, 0, 
                               Sim_Attr_Session,
                               "Tell the model to stop fetching so that the "
                               "instruction queue will empty itself. Useful "
                               "to save a checkpoint.");

        SIM_register_typed_attribute(
                conf_class, "cpu", 
                get_cpu_attribute,0, 
                set_cpu_attribute, 0, 
                Sim_Attr_Required,
                "o", NULL,
                "CPU to connect the model to.");
}
