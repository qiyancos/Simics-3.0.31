/*
  gc-specialize.c - g-cache-ooo implementation

  Copyright 2003-2007 Virtutech AB
  
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

/* busy status macros */
/* if the status is still outstanding */
#define GC_IS_VALID_STATUS(gc, i)                                       \
(((gc)->lines[(i)].busy.start_time + (gc)->lines[(i)].busy.busy_time)   \
 > (gc)->current_cycle)

/* if the status is at least one cycle old */
#define GC_IS_OUTDATED_STATUS(gc, i)                                    \
(((gc)->lines[(i)].busy.start_time + (gc)->lines[(i)].busy.busy_time)   \
 < (gc)->current_cycle)

#define GC_INVALIDATE_STATUS(gc, i)                     \
do {                                                    \
        (gc)->lines[(i)].busy.status = CLT_None;        \
        (gc)->lines[(i)].busy.id = -1;                  \
        (gc)->lines[(i)].busy.ini_ptr = NULL;           \
} while(0);

#define GC_GET_STATUS_TIME(gc, i)                                       \
(((gc)->lines[(i)].busy.start_time + (gc)->lines[(i)].busy.busy_time)   \
 - (gc)->current_cycle)



static int
ot_find_place(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        int i;
        trans_line_t *tr;

        for (i=0; i<gc->config.max_out_trans; i++) {

                tr = &gc->outstanding_trans[i];

                /* first check for time to be sure to override old ids */
                if (tr->start_time + tr->busy_time < gc->current_cycle) {
                        /* just make it empty */
                        tr->id = -1;
                        return 1;
                }
                if (mem_op->id == tr->id && mem_op->ini_ptr == tr->ini_ptr)
                        return 1;
                if (tr->id == -1)
                        return 1;
        }

        SIM_log_info(3, &gc->log, GC_Log_OT,
                     "ot_find_place: no place found in outstanding "
                     "trans. list.");

        return 0;
}

/* find if a transaction has been allocated for this transaction
   without taking over any space */
static int
ot_find_trans(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        int i;
        trans_line_t *tr;

        for (i=0; i<gc->config.max_out_trans; i++) {
                tr = &gc->outstanding_trans[i];
                if (mem_op->id == tr->id
                    && mem_op->ini_ptr == tr->ini_ptr
                    && tr->start_time + tr->busy_time >= gc->current_cycle)
                        return 1;
        }

        SIM_log_info(3, &gc->log, GC_Log_OT,
                     "ot_find_trans: no transaction found in "
                     "outstanding trans. list.");

        return 0;
}

/* find an *outstanding* transaction - that is line != -1 if line == -1, this
   is just a transaction kept for limit purpose or eventually a reissued
   write-through transaction. So the caller must check if the line is valid
   before using it. */
static int 
ot_find_line_trans(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        int i;
        trans_line_t *tr;

        for (i=0; i<gc->config.max_out_trans; i++) {

                tr = &gc->outstanding_trans[i];
                
                if (tr->id == mem_op->id
                    && tr->ini_ptr == mem_op->ini_ptr
                    && tr->start_time + tr->busy_time >= gc->current_cycle) {
                        SIM_log_info(3, &gc->log, GC_Log_OT,
                                     "ot_find_busy_trans: transaction found.");
                        return i;
                }
        }

        return -1;
}

static void
ot_add_trans_all(generic_cache_t *gc, generic_transaction_t *mem_op, int cl,
                 integer_t busy, int wt_reissue, int wt_hit)
{
        int i;
        int j = -1;
        trans_line_t *tr;

        SIM_log_info(4, &gc->log, GC_Log_OT,
                     "ot_add_trans: %d, %lld", cl, busy);
        
        for (i=0; i<gc->config.max_out_trans; i++) {
                
                tr = &gc->outstanding_trans[i];

                /* empty trans */
                if (tr->id == -1 && j == -1)
                        j = i;

                /* found the transaction */
                if (tr->id == mem_op->id &&
                    tr->ini_ptr == mem_op->ini_ptr) {
                        /* update the values */

                        SIM_log_info(3, &gc->log, GC_Log_OT,
                                     "ot_add_trans: found transaction, "
                                     "updating values.");

                        tr->line = cl;
                        tr->start_time = gc->current_cycle;
                        tr->busy_time = busy;
                        tr->wt_reissue = wt_reissue;
                        tr->wt_hit = wt_hit;
                        return;
                }
        }

        /* this should never happen because we check for place first */
        if (j == -1) {
                SIM_log_error(&gc->log, GC_Log_OT,
                              "ot_add_trans: no place left in outstanding "
                              "transaction queue.");
                SIM_break_simulation("");
        }
        else {
                SIM_log_info(3, &gc->log, GC_Log_OT,
                             "ot_add_trans: new transaction, setting "
                             "values.");

                tr = &gc->outstanding_trans[j];

                tr->id         = mem_op->id;
                tr->ini_ptr    = mem_op->ini_ptr;
                tr->line       = cl;
                tr->start_time = gc->current_cycle;
                tr->busy_time  = busy;
                tr->wt_reissue = wt_reissue;
                tr->wt_hit     = wt_hit;
        }
}

FORCE_INLINE void
ot_add_trans(generic_cache_t *gc, generic_transaction_t *mem_op, int cl,
             integer_t busy)
{
        ot_add_trans_all(gc, mem_op, cl, busy, 0, 0);
}


static int
limit_check_per_cycle(generic_cache_t *gc, generic_transaction_t *mem_op)
{

        SIM_log_info(4, &gc->log, GC_Log_Cache,
                     "limit_check_per_cycle.");

        /* update the counters */
        if (gc->limit.read_cc != gc->current_cycle) {
                gc->limit.read_cc = gc->current_cycle;
                gc->limit.curr_rpc = 0;
        }
        if (gc->limit.write_cc != gc->current_cycle) {
                gc->limit.write_cc = gc->current_cycle;
                gc->limit.curr_wpc = 0;
        }

        if (SIM_mem_op_is_read(mem_op)) {
                if (gc->limit.curr_rpc < gc->config.read_per_cycle) {
                        gc->limit.curr_rpc++;
                        return 1;
                }
        }
        else {
                if (gc->limit.curr_wpc < gc->config.write_per_cycle) {
                        gc->limit.curr_wpc++;
                        return 1;
                }
        }

        SIM_log_info(3, &gc->log, GC_Log_Cache,
                     "limit_check_per_cycle: "
                     "limit per cycle reached, transaction refused.");

        return 0;
}

/*
  pick up a new line for a transaction.
*/
static int
get_line(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        int line; 

        /* first check in the outstanding transaction list 
           line is *not* the line number here, but the index in the
           outstanding transaction array */
        line = ot_find_line_trans(gc, mem_op);
        if (line != -1 && gc->outstanding_trans[line].line != -1)
                return gc->outstanding_trans[line].line;

        return gc->config.repl_fun.get_line(gc->config.repl_data, gc, mem_op);
}

static cycles_t 
copy_back(generic_cache_t *gc, int i, generic_transaction_t *mem_op,
          conf_object_t *space, map_list_t *map, int id)
{
        int penalty = 0;
        cache_line_t *cl = &gc->lines[i];

        SIM_log_info(3, &gc->log,
                     (SIM_mem_op_is_write(mem_op) 
                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                     "copy_back");

        /* don't do anything if we don't have a
           timing model behind us */
        if (gc->timing_model) {
                cache_memory_transaction_t mt;

                /* setup a copy back transaction for the line */
                memset(&mt, 0, sizeof mt);
                if (gc->config.virtual_tag) {
                        mt.s.logical_address =
                                GC_UNTAG(gc, cl->tag);
                        mt.s.physical_address =
                                GC_UNTAG(gc, cl->otag);
                }
                else {
                        mt.s.physical_address =
                                GC_UNTAG(gc, cl->tag);
                        mt.s.logical_address =
                                GC_UNTAG(gc, cl->otag);
                }

                mt.s.size = gc->config.line_size;
                mt.s.may_stall = 1;
                mt.s.ini_type = Sim_Initiator_Cache;
                mt.s.ini_ptr = (conf_object_t *) gc;
                if (id == -1)
                        mt.s.id = SIM_get_unique_memory_transaction_id(
                                gc->cpus[0]);
                else
                        mt.s.id = id;
                SIM_set_mem_op_type(&mt.s, Sim_Trans_Store);

                /* update the initial_trans field */
                if ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Cache) {
                        cache_memory_transaction_t *ct =
                                (cache_memory_transaction_t *) mem_op;
                        mt.initial_trans = ct->initial_trans;
                }
                else {
                        mt.initial_trans = mem_op;
                }

                penalty += gc->timing_ifc->operate(gc->timing_model, 
                                                   space,
                                                   map, &mt.s);

                /* now setup properly the busy information */
                if (penalty > 0) {
                        cl->busy.status = CLT_CopyBack;
                        cl->busy.start_time = gc->current_cycle;
                        cl->busy.busy_time = penalty;
                        cl->busy.next_tag = GC_TAG(gc, mem_op);
                        if (mt.s.reissue == 1) {
                                cl->busy.next_id = mt.s.id;
                                cl->busy.id = mem_op->id;
                                cl->busy.ini_ptr = mem_op->ini_ptr;
                        }
                        else {
                                cl->busy.next_id = -1;
                                cl->busy.id = mem_op->id;
                                cl->busy.ini_ptr = mem_op->ini_ptr;
                        }
                        /* ask for memory transaction reissue */
                        mem_op->reissue |= 1;
                }
        }

        return penalty;
}

/*
  Empty a cache line, with eventual copy back transaction
*/
static cycles_t
empty_line(generic_cache_t *gc, int i, generic_transaction_t *mem_op,
           conf_object_t *space, map_list_t *map)
{
        cache_line_t *cl = &gc->lines[i];
        int penalty = 0;
        int do_copy_back = 0;
        
        SIM_log_info(4, &gc->log,
                     (SIM_mem_op_is_write(mem_op) 
                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                     "empty_line: %d", i);

        /* check the line status */
        if (cl->busy.status == CLT_CopyBack) {

                /* there is a copy-back transaction going on */
                do_copy_back = 1;
                
                /* if the status is valid, the transaction has nothing to do
                   with the line, so wait */
                if (GC_IS_VALID_STATUS(gc, i)) {
                        
                        SIM_log_info(3, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "empty_line: transaction will wait "
                                     "because the line is busy");

                        mem_op->reissue |= 1;
                        return GC_GET_STATUS_TIME(gc, i);
                }
                /* we're waiting for re-issue */
                else if (cl->busy.next_id != -1) {
                        
                        if (cl->busy.id == mem_op->id
                            && cl->busy.ini_ptr == mem_op->ini_ptr) {
                                /* reissue the transaction */
                                SIM_log_info(4, &gc->log,
                                             (SIM_mem_op_is_write(mem_op) 
                                              ? GC_Log_Write_Miss 
                                              : GC_Log_Read_Miss),
                                             "empty_line: reissuing "
                                             "copy-back transaction");

                                penalty += copy_back(gc, i, mem_op,
                                                     space, map, 
                                                     cl->busy.next_id);
                        }
                        else {
                                /* reissue in 1 cycle, it's not the right
                                   transaction */
                                SIM_log_info(2, &gc->log,
                                             (SIM_mem_op_is_write(mem_op) 
                                              ? GC_Log_Write_Miss 
                                              : GC_Log_Read_Miss),
                                             "empty_line: wrong transaction "
                                             "for triggering reissue");

                                mem_op->reissue |= 1;
                                return 1;
                        }
                }
                else if (GC_IS_OUTDATED_STATUS(gc, i)) {

                        if (cl->busy.id != mem_op->id 
                            || cl->busy.ini_ptr != mem_op->ini_ptr) {
                                /* make the line not busy */

                                SIM_log_info(2, &gc->log,
                                             (SIM_mem_op_is_write(mem_op) 
                                              ? GC_Log_Write_Miss 
                                              : GC_Log_Read_Miss),
                                             "empty_line: taking over old "
                                             "busy line.");
                        
                                GC_INVALIDATE_STATUS(gc, i);
                        }
                }
        }
        /* if it's busy doing something else */
        else if (cl->busy.status != CLT_None && 
                 (cl->busy.id != mem_op->id 
                  || cl->busy.ini_ptr != mem_op->ini_ptr)) {
                if (GC_IS_VALID_STATUS(gc, i)) {

                        SIM_log_info(2, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "empty_line: wrong status - reissue "
                                     "transaction when status is cleared.");

                        mem_op->reissue |= 1;
                        return GC_GET_STATUS_TIME(gc, i);
                }
                else if (cl->busy.next_id != -1) {
                        /* reissue in 1 cycle, it's not the right
                           transaction */

                        SIM_log_info(2, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "empty_line: wrong status - transaction "
                                     "is waiting for reissue to next level.");

                        mem_op->reissue |= 1;
                        return 1;
                } 
                else if (GC_IS_OUTDATED_STATUS(gc, i)) {
                        /* make the line not busy */

                        SIM_log_info(2, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "empty_line: taking over old busy line.");

                        GC_INVALIDATE_STATUS(gc, i);
                }
        }

        /* do the empty line if the line does nothing */
        if (cl->busy.status == CLT_None) {
                /* write-back */
                if (cl->status == CL_Modified) {

                        SIM_log_info(3, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "empty_line: starting a new copy-back.");

                        penalty += copy_back(gc, i, mem_op,
                                             space, map, -1);
                        do_copy_back = 1;
                }
        }

        /* now update the status only if reissue is not set */
        if (!mem_op->reissue) {
                /* cancel copy back if it was going on */
                if (cl->busy.status == CLT_CopyBack)
                        cl->busy.status = CLT_None;
                cl->status = CL_Invalid;
                if (do_copy_back)
                        INC_STAT(gc, copy_back);
        }

        return penalty;
}

static cycles_t
fetch_line_trans(generic_cache_t *gc, int i, generic_transaction_t *mem_op,
                 conf_object_t *space, map_list_t *map, int id) 
{
        int penalty = 0;
        cache_line_t *cl = &gc->lines[i];
        
        SIM_log_info(4, &gc->log,
                     (SIM_mem_op_is_write(mem_op) 
                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                     "fetch_line_trans");

        /* propagate to next level */
        if (gc->timing_model) {
                cache_memory_transaction_t mt;

                /* fetch the line */
                memset(&mt, 0, sizeof mt);
                if (gc->config.virtual_tag) {
                        mt.s.logical_address =
                                GC_TAG_ADDRESS(gc, mem_op) & GC_TAG_MASK(gc);
                        mt.s.physical_address =
                                GC_OTAG_ADDRESS(gc, mem_op) & GC_TAG_MASK(gc);
                }
                else {
                        mt.s.physical_address =
                                GC_TAG_ADDRESS(gc, mem_op) & GC_TAG_MASK(gc);
                        mt.s.logical_address =
                                GC_OTAG_ADDRESS(gc, mem_op) & GC_TAG_MASK(gc);
                }

                mt.s.size = gc->config.line_size;
                mt.s.may_stall = 1;
                mt.s.ini_type = Sim_Initiator_Cache;
                mt.s.ini_ptr = (conf_object_t *) gc;

                /* set the transaction according to the initiating mem_op */
                if (SIM_mem_op_is_data(mem_op))
                        SIM_set_mem_op_type(&mt.s, Sim_Trans_Load);
                else
                        SIM_set_mem_op_type(&mt.s, Sim_Trans_Instr_Fetch);

                if (id == -1)
                        mt.s.id = SIM_get_unique_memory_transaction_id(
                                gc->cpus[0]);
                else 
                        mt.s.id = id;

                /* update the initial_trans field */
                if ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Cache) {
                        cache_memory_transaction_t *ct =
                                (cache_memory_transaction_t *) mem_op;
                        mt.initial_trans = ct->initial_trans;
                }
                else {
                        mt.initial_trans = mem_op;
                }

                penalty += gc->timing_ifc->operate(gc->timing_model, 
                                                   space,
                                                   map, &mt.s);

#if defined(DEBUG_REISSUE)
                /* this is a miss */
                if (gc->read_counted[mem_op->id].flag) {
                        SIM_log_error(&gc->log, 0,
                                      "missed transaction %d not counted "
                                      "cycle (%lld)",
                                      mem_op->id,
                                      gc->read_counted[mem_op->id].cycle);
                }
                if (!mt.s.reissue) {
                        gc->read_counted[mem_op->id].flag = 1;
                        gc->read_counted[mem_op->id].cycle = gc->current_cycle;
                }
#endif

                /* now setup properly the busy information */
                if (penalty > 0) {
                        cl->busy.status = CLT_Fill;
                        cl->busy.start_time = gc->current_cycle;
                        cl->busy.busy_time = penalty;
                        cl->busy.next_tag = GC_TAG(gc, mem_op);
                        if (mt.s.reissue) {
                                cl->busy.next_id = mt.s.id;
                                cl->busy.id = mem_op->id;
                                cl->busy.ini_ptr = mem_op->ini_ptr;
                        }
                        else {
                                cl->busy.next_id = -1;
                                cl->busy.id = mem_op->id;
                                cl->busy.ini_ptr = mem_op->ini_ptr;
                        }
                        /* ask for memory transaction reissue */
                        mem_op->reissue |= 1;
                }
        }
        else {
#if defined(DEBUG_REISSUE)
                /* this is a miss */
                if (gc->read_counted[mem_op->id].flag) {
                        SIM_log_error(&gc->log, 0,
                                      "missed transaction %d not counted "
                                      "(%lld)", mem_op->id,
                                      gc->read_counted[mem_op->id].cycle);
                }
                gc->read_counted[mem_op->id].flag = 1;
                gc->read_counted[mem_op->id].cycle = gc->current_cycle;
#endif
        }

        return penalty;
}
        


/*
  Fetch a line corresponding to the given mem_op from the previous cache 
*/
static cycles_t
fetch_line(generic_cache_t *gc, int i, generic_transaction_t *mem_op,
           conf_object_t *space, map_list_t *map)
{
        int penalty = 0;
        cache_line_t *cl = &gc->lines[i];

        SIM_log_info(4, &gc->log,
                     (SIM_mem_op_is_write(mem_op) 
                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                     "fetch_line: %d", i);

        /* check the line status */
        if (cl->busy.status == CLT_Fill) {
                
                /* if the status is valid, the transaction has nothing to do
                   with the line, so wait */
                if (GC_IS_VALID_STATUS(gc, i)) {

                        SIM_log_info(3, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "fetch_line: transaction will wait "
                                     "because the line is busy");

                        mem_op->reissue |= 1;
                        return GC_GET_STATUS_TIME(gc, i);
                }
                /* we're waiting for re-issue */
                else if (cl->busy.next_id != -1) { 
                        
                        if (cl->busy.id == mem_op->id
                            && cl->busy.ini_ptr == mem_op->ini_ptr) {
                                /* reissue the transaction */
                                SIM_log_info(4, &gc->log,
                                             (SIM_mem_op_is_write(mem_op) 
                                              ? GC_Log_Write_Miss 
                                              : GC_Log_Read_Miss),
                                             "fetch_line: reissuing "
                                             "fetch transaction");

                                penalty += fetch_line_trans(gc, i, mem_op,
                                                            space, map,
                                                            cl->busy.next_id);
                        }
                        else {
                                /* reissue in 1 cycle, it's not the right
                                   transaction */
                                SIM_log_info(2, &gc->log,
                                             (SIM_mem_op_is_write(mem_op) 
                                              ? GC_Log_Write_Miss 
                                              : GC_Log_Read_Miss),
                                             "fetch_line: wrong transaction "
                                             "for triggering reissue");

                                mem_op->reissue |= 1;
                                return 1;
                        }
                }
                /* if the status is one cycle too old, clear it */
                else if (GC_IS_OUTDATED_STATUS(gc, i)
                         && (cl->busy.id != mem_op->id
                             || cl->busy.ini_ptr != mem_op->ini_ptr)) {
                        /* make the line not busy */

                        SIM_log_info(2, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "fetch_line: taking over old busy line.");
                        
                        GC_INVALIDATE_STATUS(gc, i);
                }
        }
        /* if it's busy doing something else */
        else if (cl->busy.status != CLT_None 
                 && (cl->busy.id != mem_op->id
                     || cl->busy.ini_ptr != mem_op->ini_ptr)) {
                if (GC_IS_VALID_STATUS(gc, i)) {

                        SIM_log_info(2, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "fetch_line: wrong status - reissue "
                                     "transaction when status is cleared.");

                        mem_op->reissue |= 1;
                        return GC_GET_STATUS_TIME(gc, i);
                }
                else if (cl->busy.next_id != -1) {

                        SIM_log_info(2, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "fetch_line: wrong status - transaction "
                                     "is waiting for reissue to next level.");

                        mem_op->reissue |= 1;
                        return 1;
                }
                else if (GC_IS_OUTDATED_STATUS(gc, i)) {
                        /* make the line not busy */

                        SIM_log_info(2, &gc->log,
                                     (SIM_mem_op_is_write(mem_op) 
                                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                                     "fetch_line: taking over old busy line.");

                        GC_INVALIDATE_STATUS(gc, i);
                }
        }

        /* do the fetch line if the line does nothing */
        if (cl->busy.status == CLT_None) {
                /* fill the line values */
                SIM_log_info(4, &gc->log,
                             (SIM_mem_op_is_write(mem_op) 
                              ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                             "fetch_line: setting a new fetch line.");

                penalty += fetch_line_trans(gc, i, mem_op, space, map, -1);
        }

        /* update the status only if no reissue is asked for */
        if (!mem_op->reissue) {

                SIM_log_info(4, &gc->log,
                             (SIM_mem_op_is_write(mem_op) 
                              ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                             "fetch_line: fetching done, update line info.");
                
                cl->status = CL_Shared;
                cl->tag = GC_TAG(gc, mem_op);
                cl->otag = GC_OTAG(gc, mem_op);
        }
        
        return penalty;
}

/*
  Handle a data read / instr. fetch transaction coming to the cache
*/
static cycles_t
handle_read(generic_cache_t *gc, generic_transaction_t *mem_op,
            conf_object_t *space, map_list_t *map)
{
        int i;
        int hit = 0;
        int penalty = 0;

        /* precompute tag and index */
        integer_t tag = GC_TAG(gc, mem_op);
        int index = GC_INDEX(gc, mem_op);

        /* look for a matching line */
        for (i=index; 
             i<gc->config.line_number;
             i+= GC_NEXT_ASSOC(gc)) {
                
                /* real hit */
                if ((gc->lines[i].status != CL_Invalid)
                    && (gc->lines[i].busy.status == CLT_None)
                    && (gc->lines[i].tag == tag)) {
                        /* it's a hit */
                        SIM_log_info(3, &gc->log, GC_Log_Read_Hit,
                                     "handle_read: "
                                     "transaction is a real hit (line %d)", i);
                        hit = 1;
                        break; /* get out with i unmodified */
                }
                /* potential hit - it must be a different transaction */
                else if ((gc->lines[i].busy.status != CLT_None)
                         && (gc->lines[i].busy.next_tag == tag)
                         && (gc->lines[i].busy.id != mem_op->id
                             || gc->lines[i].busy.ini_ptr != mem_op->ini_ptr)) {
                        
                        /* it's a future hit */
                        SIM_log_info(3, &gc->log, GC_Log_Read_Hit,
                                     "handle_read: "
                                     "transaction is a future hit (line %d)", 
                                     i);
                        hit = 1;
                        break; /* get out with i unmodified */
                }
        }

        /* we've got a hit in the cache */
        if (hit) {
                
                /* are we waiting for a copyback? */
                if (gc->lines[i].busy.status == CLT_CopyBack) {
                        if (GC_IS_VALID_STATUS(gc, i))
                                penalty += GC_GET_STATUS_TIME(gc, i);
                        else {
                                if (GC_IS_OUTDATED_STATUS(gc, i)) {
                                        SIM_log_info(2, &gc->log,
                                                     GC_Log_Read_Hit,
                                                     "Found an invalid "
                                                     "copy-back status");
                                        GC_INVALIDATE_STATUS(gc, i);
                                }
                                penalty += 1;
                        }
                }
                else if (gc->lines[i].busy.status == CLT_Fill) {
                        if (GC_IS_VALID_STATUS(gc, i))
                                penalty += GC_GET_STATUS_TIME(gc, i);
                        else {
                                if (GC_IS_OUTDATED_STATUS(gc, i)) {
                                        SIM_log_info(2, &gc->log,
                                                     GC_Log_Read_Hit,
                                                     "Found an invalid fill "
                                                     "status");
                                        GC_INVALIDATE_STATUS(gc, i);
                                }
                                penalty += 1;
                        }
                }

                /* after this point, the transaction won't be reissued 
                   so we can update the stats. */
                if (SIM_mem_op_is_data(mem_op))
                        INC_STAT(gc, data_read);
                else
                        INC_STAT(gc, inst_fetch);
                INC_STAT(gc, transaction);

                /* update the limits */
                ot_add_trans(gc, mem_op, -1, 
                             penalty + gc->penalty.read);

                gc->config.repl_fun.update_repl(
                        gc->config.repl_data, gc, mem_op, i);
                return penalty + gc->penalty.read;
        }
        else {
                SIM_log_info(3, &gc->log, GC_Log_Read_Miss,
                             "handle_read: transaction is a miss");
                
                i = get_line(gc, mem_op);

                /* empty the line if needed */
                penalty += empty_line(gc, i, mem_op, space, map);
                if (mem_op->reissue) {
                        ot_add_trans(gc, mem_op, i, penalty);
                        gc->config.repl_fun.update_repl(
                                gc->config.repl_data, gc, mem_op, i);
                        return penalty;
                }
                
                /* the line is empty, now fetch the data */
                penalty += fetch_line(gc, i, mem_op, space, map);
                if (mem_op->reissue) {
                        ot_add_trans(gc, mem_op, i, penalty);
                        gc->config.repl_fun.update_repl(
                                gc->config.repl_data, gc, mem_op, i);
                        return penalty;
                }

                /* invalidate status *now*, because no reissue will be
                   needed */
                GC_INVALIDATE_STATUS(gc, i);
                
                /* after this point, the transaction won't be reissued 
                   so we can update the stats. */
                if (SIM_mem_op_is_data(mem_op)) {
                        INC_STAT(gc, data_read);
                        INC_STAT(gc, data_read_miss);
                        INC_STAT(gc, transaction);

                        /* update the profilers */
                        if (gc->prof[I_DRM].id)
                                prof_data_inc_pc(gc->prof[I_DRM].id,
                                                 GC_CPU(mem_op));

                        if (gc->prof[V_DRM].id)
                                prof_data_add(gc->prof[V_DRM].id,
                                              GC_VA_ADDRESS(mem_op),
                                              1);

                        if (gc->prof[P_DRM].id)
                                prof_data_add(gc->prof[P_DRM].id,
                                              GC_PA_ADDRESS(mem_op),
                                              1);
                        
#if defined(DEBUG_REISSUE)
                        if (!gc->read_counted[mem_op->id].flag) {
                                SIM_log_error(&gc->log, 0,
                                              "no miss transaction (%lld)",
                                              mem_op->id,
                                              gc->current_cycle);
                        }
                        gc->read_counted[mem_op->id].flag = 0;
#endif

                }
                else {
                        INC_STAT(gc, inst_fetch);
                        INC_STAT(gc, inst_fetch_miss);
                        INC_STAT(gc, transaction);
                        
                        /* update the profilers */
                        if (gc->prof[V_IFM].id)
                                prof_data_add(gc->prof[V_IFM].id,
                                              GC_VA_ADDRESS(mem_op),
                                              1);
                        if (gc->prof[P_IFM].id)
                                prof_data_add(gc->prof[P_IFM].id,
                                              GC_PA_ADDRESS(mem_op),
                                              1);
                        
#if defined(DEBUG_REISSUE)
                        if (!gc->read_counted[mem_op->id].flag) {
                                SIM_log_error(&gc->log, 0,
                                              "no miss transaction (%lld)",
                                              mem_op->id,
                                              gc->current_cycle);
                        }
                        gc->read_counted[mem_op->id].flag = 0;
#endif
                }
                
                ot_add_trans(gc, mem_op, -1,
                             penalty + gc->penalty.read);
                gc->config.repl_fun.update_repl(
                        gc->config.repl_data, gc, mem_op, i);

                return penalty + gc->penalty.read;
        }
}

/*
  Handle a write transaction in the cache
*/
static cycles_t
handle_write(generic_cache_t *gc, generic_transaction_t *mem_op,
             conf_object_t *space, map_list_t *map)
{
        int penalty = 0;
        int hit = 0;
        int i = 0;
        int t, wt_r;

        /* precompute some values */
        integer_t tag = GC_TAG(gc, mem_op);
        integer_t index = GC_INDEX(gc, mem_op);

        t = ot_find_line_trans(gc, mem_op);
        if (t != -1 && gc->outstanding_trans[t].wt_reissue) {
                wt_r = 1;
                hit = gc->outstanding_trans[t].wt_hit;
        }
        else 
                wt_r = 0;

        /* in both cases, we need to know if the transaction
           is a hit -- skip if reissuing write-through*/
        if (!wt_r) {

                /* look for a matching line */
                for (i=index; 
                     i<gc->config.line_number;
                     i+= GC_NEXT_ASSOC(gc)) {

                        if ((gc->lines[i].status != CL_Invalid) 
                            && (gc->lines[i].busy.status == CLT_None)
                            && (gc->lines[i].tag == tag)) {
                                /* it's a hit */
                                SIM_log_info(3, &gc->log, GC_Log_Write_Hit,
                                             "handle_write: "
                                             "transaction is a real hit");
                                hit = 1;
                                break; /* get out without changing i */
                        }
                        else if ((gc->lines[i].busy.status != CLT_None)
                                 && (gc->lines[i].busy.next_tag == tag)
                                 && (gc->lines[i].busy.id != mem_op->id
                                     || gc->lines[i].busy.ini_ptr != 
                                     mem_op->ini_ptr)) {
                                /* it's a hit */
                                SIM_log_info(3, &gc->log, GC_Log_Write_Hit,
                                             "handle_write: "
                                             "transaction is a future hit");
                                hit = 1;
                                break; /* get out without changing i */
                        }
                }

                /* check if it's a future hit */
                if (hit && gc->lines[i].busy.status != CLT_None) {
                        if (GC_IS_VALID_STATUS(gc, i))
                                penalty += GC_GET_STATUS_TIME(gc, i);
                        else {
                                if (GC_IS_OUTDATED_STATUS(gc, i)) {
                                        SIM_log_info(2, &gc->log,
                                                     GC_Log_Write_Hit,
                                                     "Found an invalid busy "
                                                     "status");
                                        GC_INVALIDATE_STATUS(gc, i);
                                }
                                penalty += 1;
                        }
                }
        }

        /* if we don't hit and we won't allocate any line, then
           set i to to an invalid value */
        if (!hit && !gc->config.write_allocate)
                i = -1;

        /* if we need to allocate, get a line - skip if reissuing wt */
        if (gc->config.write_allocate && !hit && !wt_r) {
                i = get_line(gc, mem_op);

                penalty += empty_line(gc, i, mem_op, space, map);
                if (mem_op->reissue) {
                        ot_add_trans(gc, mem_op, i, penalty);
                        gc->config.repl_fun.update_repl(
                                gc->config.repl_data, gc, mem_op, i);
                        return penalty;
                }

                penalty += fetch_line(gc, i, mem_op, space, map);
                if (mem_op->reissue) {
                        ot_add_trans(gc, mem_op, i, penalty);
                        gc->config.repl_fun.update_repl(
                                gc->config.repl_data, gc, mem_op, i);
                        return penalty;
                }

                GC_INVALIDATE_STATUS(gc, i);
        }

        /* write to next level, unless the cache is write-back write-allocate
           or write-back, non-write-allocate and hit 
           go in if reissuing wt. */
        if (!gc->config.write_back || 
            (!gc->config.write_allocate && !hit) || wt_r) {

                SIM_log_info(4, &gc->log, GC_Log_Write_Miss | GC_Log_Write_Hit,
                             "handle_write: writing to next level");
                
                /* propagate the transaction 'as is' to next level */
                if (gc->timing_model) {
                        penalty += gc->timing_ifc->operate(gc->timing_model, 
                                                           space,
                                                           map, mem_op);
                        if (mem_op->reissue) {
                                ot_add_trans_all(gc, mem_op, i, 
                                                 penalty, 1, hit);
                                return penalty;
                        }
                }
        }

        /* add the generic write penalty */
        penalty += gc->penalty.write;

        /* the transaction coming here won't be reissued */
        INC_STAT(gc, data_write);
        INC_STAT(gc, transaction);

        /* check if it was a miss---what happens is that if the transaction 
           needed to be stored then it was a miss. */
        if ((t != -1 && !wt_r) || !hit) {

#if defined(DEBUG_REISSUE)
                /* just cancel an eventual value set to 1 */
                gc->read_counted[mem_op->id].flag = 0;
#endif
                INC_STAT(gc, data_write_miss);
                
                /* Update the profilers */
                if (gc->prof[I_DWM].id)
                        prof_data_inc_pc(gc->prof[I_DWM].id,
                                         GC_CPU(mem_op));
                
                if (gc->prof[V_DWM].id)
                        prof_data_add(gc->prof[V_DWM].id, 
                                      GC_VA_ADDRESS(mem_op), 
                                      1);

                if (gc->prof[P_DWM].id)
                        prof_data_add(gc->prof[P_DWM].id, 
                                      GC_PA_ADDRESS(mem_op), 
                                      1);
        }

        if (i != -1) {
                if (gc->config.write_back)
                        gc->lines[i].status = CL_Modified;
                else
                        /* wt, we have written the value */
                        gc->lines[i].status = CL_Shared;

                /* update i only if a line was touched */
                gc->config.repl_fun.update_repl(
                        gc->config.repl_data, gc, mem_op, i);
        }

        ot_add_trans(gc, mem_op, -1, penalty);
        return penalty;
}

cycles_t
gc_operate(conf_object_t *mem_hier, conf_object_t *space, 
                   map_list_t *map, generic_transaction_t *mem_op)
{
        generic_cache_t *gc = (generic_cache_t *) mem_hier;
        cycles_t stall_time;

        SIM_log_info(4, &gc->log, GC_Log_Cache,
                     "operate: *** new transaction ***");

        /* update the current cycle count */
        gc->current_cycle = SIM_cycle_count(GC_CPU(mem_op));
        mem_op->reissue = 0; /* cancel reissue by default */

#ifdef GC_DEBUG
        if (SIM_clear_exception()) {
                SIM_log_error(&gc->log, 0,
                              "operate: (cycle %lld) "
                              "got an exception in SIM_cycle_count()",
                              gc->current_cycle);
                SIM_break_simulation("");
        }
#endif

        /* handle uncacheable transaction */
        if (is_uncacheable(gc, mem_op, map, &gc->log)) {
                
                SIM_log_info(4, &gc->log, GC_Log_Cache,
                             "operate: transaction is uncacheable");

                if (gc->timing_model) {
                        SIM_log_info(4, &gc->log, GC_Log_Cache,
                                  "operate: passing transaction to next level");
                        stall_time = gc->timing_ifc->operate(gc->timing_model,
                                                             space,
                                                             map,
                                                             mem_op);
                        SIM_log_info(4, &gc->log, GC_Log_Cache,
                                     "operate: return stall time %lld", 
                                     stall_time);
                }
                else {
                        stall_time = 0;
                        SIM_log_info(4, &gc->log, GC_Log_Cache,
                                     "operate: return stall time 0");
                }

                /* count only if no reissue */
                if (stall_time == 0 || !mem_op->reissue) {

                        INC_STAT(gc, transaction);

                        if ((mem_op->ini_type & 0xFF00)
                            == Sim_Initiator_Device) {
                                if (SIM_mem_op_is_read(mem_op))
                                        INC_STAT(gc, dev_data_read);
                                else
                                        INC_STAT(gc, dev_data_write);
                        }
                        else {
                                if (SIM_mem_op_is_read(mem_op)) {
                                        if (SIM_mem_op_is_instruction(mem_op))
                                                INC_STAT(gc, uc_inst_fetch);
                                        else
                                                INC_STAT(gc, uc_data_read);
                                }
                                else {
                                        INC_STAT(gc, uc_data_write);
                                }
                        }

                        /* if stallable, use penalty anyway */
                        if (mem_op->may_stall) {
                                if (SIM_mem_op_is_read(mem_op))
                                        stall_time += gc->penalty.read;
                                else
                                        stall_time += gc->penalty.write;
                        }
                }

#if defined(DEBUG_REISSUE)
        if (gc->reissue[mem_op->id].flag == 0) {
                /* check if the cycle is big enough */
                if ((gc->reissue[mem_op->id].cycle != -1) 
                    && (gc->current_cycle - 
                        gc->reissue[mem_op->id].cycle) < 256) {
                        SIM_log_error(&gc->log, 0,
                                      "transaction %d should not have "
                                      "been reissued (was cycle %lld)",
                                      mem_op->id,
                                      gc->reissue[mem_op->id].cycle);
                        SIM_break_simulation("");
                }
        }
        else {
                /* check if too much time has been spent */
                if ((gc->reissue[mem_op->id].cycle != -1)
                    && (gc->current_cycle - 
                        gc->reissue[mem_op->id].cycle) > 256) {
                        SIM_log_error(&gc->log, 0,
                                      "transaction %d should have "
                                      "been reissued (was cycle %lld)",
                                      mem_op->id,
                                      gc->reissue[mem_op->id].cycle);
                        SIM_break_simulation("");
                }
        }
                
        /* remove these values because the processor may re-use uncacheable
           ids, in table-walk */
        gc->reissue[mem_op->id].flag = 0;
        gc->reissue[mem_op->id].cycle = -1;
#endif
        
                return stall_time;
        }

#ifdef GC_DEBUG
        /* print out info about the transaction */
        {
                const char *trans_type;
                
                if (SIM_mem_op_is_read(mem_op)) {
                        if (SIM_mem_op_is_instruction(mem_op))
                                trans_type = "inst. fetch";
                        else
                                trans_type = "data read  ";
                }
                else
                        trans_type = "data write ";
                
                SIM_log_info(4, &gc->log, GC_Log_Cache,
                             "operate: %s "
                             "(phys = %llx, log = %llx, size = %d)",
                             trans_type,
                             mem_op->physical_address,
                             mem_op->logical_address,
                             mem_op->size);
        }
#endif

        /* check if the transaction has been here,
           if not check for limits, then check for space in the outstanding
           queue */
        if (!ot_find_trans(gc, mem_op)
            && (!limit_check_per_cycle(gc, mem_op) 
                || !ot_find_place(gc, mem_op))) {
                /* ask for reissue in 1 cycle */
                SIM_log_info(3, &gc->log, GC_Log_Cache,
                             "operate: limits blocks "
                             "operation for 1 cycle");
                
                mem_op->reissue = 1;
                stall_time = 1;
        }
        else if (SIM_mem_op_is_read(mem_op)) {
                stall_time = handle_read(gc, mem_op, space, map);
                SIM_log_info(4, &gc->log, GC_Log_Cache,
                             "operate: return stall time %lld", stall_time);
        }
        else {
                stall_time = handle_write(gc, mem_op, space, map);
                SIM_log_info(4, &gc->log, GC_Log_Cache,
                             "operate: return stall time %lld", stall_time);
        }

#if defined(DEBUG_REISSUE)
        if (gc->reissue[mem_op->id].flag == 0) {
                /* check if the cycle is big enough */
                if ((gc->reissue[mem_op->id].cycle != -1) 
                    && (gc->current_cycle - 
                        gc->reissue[mem_op->id].cycle) < 256) {
                        SIM_log_error(&gc->log, 0,
                                      "transaction %d should not have "
                                      "been reissued (was cycle %lld)",
                                      mem_op->id,
                                      gc->reissue[mem_op->id].cycle);
                        SIM_break_simulation("");
                }
        }
        else {
                /* check if too much time has been spent */
                if ((gc->reissue[mem_op->id].cycle != -1) 
                    && (gc->current_cycle - 
                        gc->reissue[mem_op->id].cycle) > 256) {
                        SIM_log_error(&gc->log, 0,
                                      "transaction %d should have "
                                      "been reissued (was cycle %lld)",
                                      mem_op->id,
                                      gc->reissue[mem_op->id].cycle);
                        SIM_break_simulation("");
                }
        }
                
        gc->reissue[mem_op->id].flag = stall_time ? mem_op->reissue : 0;
        gc->reissue[mem_op->id].cycle = gc->current_cycle;
#endif        
        
        return stall_time;
}
