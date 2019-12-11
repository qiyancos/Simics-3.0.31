/*
  gc-specialize.c - g-cache implementation

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

/*
  This should be included after defining some constants to control the
  behaviour of the cache.
*/

/* Define defaults for hooks that aren't used. */
#ifndef HOOK_LINE_LOOKUP
#define HOOK_LINE_LOOKUP(gc, index, tag, mem_op)
#endif
#ifndef HOOK_TAG_MATCH

/* 
   When do we get a hit?
   - the line is not invalid
   - the tag match
   - if the index is virtual, the opposite tag must match also

   The reason is that the cache is not emptied when a MMU page is demapped, so
   it must check that its own (phys, virt) translation is still correct. This
   will make the cache behaves properly but it may contain 'invalid' mappings
   that haven't been detected yet.
*/
#define HOOK_TAG_MATCH(gc, line_num, mem_op)                            \
        ((gc)->lines[(line_num)].status != CL_Invalid                   \
         && ((gc)->lines[(line_num)].tag == GC_TAG((gc), (mem_op)))     \
         && (!(gc)->config.virtual_tag                                  \
             || ((gc)->lines[(line_num)].otag                           \
                 == GC_OTAG((gc), (mem_op)))))
             
#endif
#ifndef HOOK_READ_HIT
#define HOOK_READ_HIT(gc, line_num, mem_op)
#endif
#ifndef HOOK_READ_POST
#define HOOK_READ_POST(gc, line_num, mem_op)
#endif
#ifndef HOOK_WRITE_HIT
#define HOOK_WRITE_HIT(gc, line_num, mem_op)
#endif
#ifndef HOOK_WRITE_POST
#define HOOK_WRITE_POST(gc, line_num, mem_op)
#endif
#ifndef HOOK_LINE_FETCH
#define HOOK_LINE_FETCH(gc, line_num, mem_op)
#endif
#ifndef HOOK_LINE_COPYBACK
#define HOOK_LINE_COPYBACK(gc, line_num, mem_op, write_back)
#endif
#ifndef HOOK_SNOOP_HIT_PRE
#define HOOK_SNOOP_HIT_PRE(gc, line_num, mem_op)
#endif
#ifndef HOOK_SNOOP_HIT_POST
#define HOOK_SNOOP_HIT_POST(gc, line_num, mem_op)
#endif
#ifndef HOOK_BLOCK_STC
#define HOOK_BLOCK_STC(gc, line_num, block_stc) block_stc
#endif
#ifndef HOOK_DO_COPYBACK
#define HOOK_DO_COPYBACK(gc, line_num)                  \
        ((gc)->lines[(line_num)].status == CL_Modified)
#endif
#ifndef HOOK_PREFETCH
#define HOOK_PREFETCH(gc, mem_op) 0
#endif
#ifndef HOOK_CONTROL
#define HOOK_CONTROL(gc, mem_op) 0
#endif
#ifndef HOOK_DISABLED
#define HOOK_DISABLED(gc) 0
#endif

/*
  Insure that a cache line is flushed from the STCs
*/
void
flush_STC(generic_cache_t *gc, uint64 tag, uint64 otag, int STC_type, 
          cache_line_status_t status)
{
        int i;

        /* loop over all cpus connected to the cache */
        for (i=0; i<gc->cpus_count; i++) {
                
                if (gc->config.virtual_tag) {
                        if (STC_type & STC_InstSTC)
                                /* SIM_flush_I_STC_logical() is not reliable
                                   when we don't flush pages, so we flush by
                                   physical address instead */
                                SIM_flush_I_STC_physical(
                                        gc->cpus[i],
                                        GC_UNTAG(gc, otag),
                                        gc->config.line_size);
                
                        if (STC_type & STC_DataSTC)
                                SIM_flush_D_STC_logical(
                                        gc->cpus[i],
                                        GC_UNTAG(gc, tag),
                                        gc->config.line_size);
                }
                else {
                        
                        if (STC_type & STC_InstSTC)
                                SIM_flush_I_STC_physical(
                                        gc->cpus[i],
                                        GC_UNTAG(gc, tag),
                                        gc->config.line_size);

                        if (STC_type & STC_DataSTC) {
                                SIM_flush_D_STC_physical(
                                        gc->cpus[i],
                                        GC_UNTAG(gc, tag),
                                        gc->config.line_size,
                                        Sim_RW_Read);
                
                                if (status == CL_Modified
                                    || status == CL_Exclusive) {
                                        SIM_flush_D_STC_physical(
                                                gc->cpus[i],
                                                GC_UNTAG(gc, tag),
                                                gc->config.line_size,
                                                Sim_RW_Write);
                                }
                        }
                }
        }

#ifdef GC_DEBUG
        if (SIM_clear_exception()) {
                SIM_log_error(&gc->log, GC_Log_Cache,
                              "generic-cache::flush_STC: "
                              "got an exception when flushing STC");
        }
#endif
}

/* Performs a copy-back of the specified cache line. */
cycles_t
copy_back(generic_cache_t *gc, int line_num, generic_transaction_t *mem_op,
          conf_object_t *space, map_list_t *map, int write_back)
{
        int penalty = 0;
        cache_line_t *cl = &gc->lines[line_num];

        SIM_log_info(3, &gc->log, 
                     (SIM_mem_op_is_write(mem_op) 
                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                     "copy_back");
        INC_STAT(gc, copy_back);

        HOOK_LINE_COPYBACK(gc, line_num, mem_op, write_back);

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
                mt.s.exception = Sim_PE_No_Exception;
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

                SIM_log_info(4, &gc->log, 
                             (SIM_mem_op_is_write(mem_op)
                              ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                             "copy_back: calling next level");

                penalty += gc->timing_ifc->operate(gc->timing_model, space, 
                                                   map, &mt.s);

                /* Propagate any exceptions. */
                if (mt.s.exception != Sim_PE_No_Exception)
                        mem_op->exception = mt.s.exception;
        }

        return gc->penalty.write_next + penalty;
}

/* 
   Invalidates a cache line, performing a copy-back if the cache line
   is modified. 
*/
cycles_t
empty_line(generic_cache_t *gc, int line_num, generic_transaction_t *mem_op, 
           conf_object_t *space, map_list_t *map)
{
        cache_line_t *cl = &gc->lines[line_num];
        int penalty = 0;

        SIM_log_info(3, &gc->log, 
                     (SIM_mem_op_is_write(mem_op) 
                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                     "empty_line: %d", line_num);

        /* flush the STCs */
        if (!gc->config.no_STC)
                flush_STC(gc, cl->tag, cl->otag, cl->STC_type, cl->status);

        /* write-back */
        if (HOOK_DO_COPYBACK(gc, line_num))
                penalty += copy_back(gc, line_num, mem_op, space, map, 
                                     cl->status == CL_Modified);
        
        cl->STC_type = 0;
        cl->status = CL_Invalid;
        cl->tag = 0;
        cl->otag = 0;

        return penalty;
}

/*
  Fetch a line corresponding to the given mem_op from the previous cache
*/
cycles_t
fetch_line(generic_cache_t *gc, int line_num, generic_transaction_t *mem_op, 
           conf_object_t *space, map_list_t *map)
{
        int penalty = 0;
        cache_line_t *cl = &gc->lines[line_num];

        SIM_log_info(3, &gc->log, 
                     (SIM_mem_op_is_write(mem_op)
                      ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                     "fetch_line: %d", line_num);

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
                mt.s.exception = Sim_PE_No_Exception;
                if (SIM_mem_op_is_data(mem_op))
                        SIM_set_mem_op_type(&mt.s, Sim_Trans_Load);
                else
                        SIM_set_mem_op_type(&mt.s, Sim_Trans_Instr_Fetch);

                /* update the initial_trans field */
                if ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Cache) {
                        cache_memory_transaction_t *ct =
                                (cache_memory_transaction_t *) mem_op;
                        mt.initial_trans = ct->initial_trans;
                }
                else {
                        mt.initial_trans = mem_op;
                }

                SIM_log_info(4, &gc->log, 
                             (SIM_mem_op_is_write(mem_op)
                              ? GC_Log_Write_Miss : GC_Log_Read_Miss),
                             "fetch_line: calling next level");

                penalty += gc->timing_ifc->operate(gc->timing_model, space, 
                                                   map, &mt.s);

                /* Propagate any exceptions. */
                if (mt.s.exception != Sim_PE_No_Exception)
                        mem_op->exception = mt.s.exception;
        }

        /* if the cache is non-write allocate, the write STC may contain a copy
           of this line so we need to flush it to insure correct MESI and line
           status */
        if (!gc->config.write_allocate && gc->config.direct_write_listener)
                flush_STC(gc, GC_TAG(gc, mem_op), GC_OTAG(gc, mem_op), 
                          STC_DataSTC, CL_Modified);
                        
        /* fill the line values */
        cl->status = CL_Shared;
        cl->tag = GC_TAG(gc, mem_op);
        cl->otag = GC_OTAG(gc, mem_op);

        HOOK_LINE_FETCH(gc, line_num, mem_op);

        return gc->penalty.read_next + penalty;
}

/* Look for a cache line matching the address of mem_op. Returns the index of
   the cache line if it is found, or -1 if no matching cache is found. */
int
lookup_line(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        int i;
        int line_num = -1;
        
        int index = GC_INDEX(gc, mem_op);
        int next_assoc = GC_NEXT_ASSOC(gc);

        HOOK_LINE_LOOKUP(gc, index, GC_TAG(gc, mem_op), mem_op);

        /* Always call HOOK_TAG_MATCH for all lines in the set. */
        for (i = index; i < gc->config.line_number; i += next_assoc)
                if (HOOK_TAG_MATCH(gc, i, mem_op))
                        line_num = i;

        return line_num;
}

/* Sends transactions to all coherent caches. */
static cycles_t
mesi_send(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        int i;
        int penalty = 0;

        SIM_log_info(4, &gc->log, GC_Log_MESI, "mesi_send");

        for (i = 0; i < gc->snoopers_size; i++)
                if (gc->snoopers[i] && gc->snoopers_ifc[i])
                        penalty += gc->snoopers_ifc[i]->snoop_transaction(
                                gc->snoopers[i],
                                mem_op);

        return penalty;
}

static cycles_t 
mesi_snoop_read(generic_cache_t *gc, generic_transaction_t *mem_op, 
                int line_num)
{
        int penalty = 0;

        switch (gc->lines[line_num].status) {
        case CL_Shared:
                break;
        case CL_Exclusive:
                SIM_log_info(
                        3, &gc->log, GC_Log_MESI,
                        "mesi_receive: snoop read hit "
                        "on an exclusive line");
                
                /* flush STC to insure that a write hit will change the line
                   status */
                if (!gc->config.no_STC)
                        flush_STC(gc, 
                                  gc->lines[line_num].tag, 
                                  gc->lines[line_num].otag, 
                                  gc->lines[line_num].STC_type,
                                  gc->lines[line_num].status);
                gc->lines[line_num].status = CL_Shared;
                INC_STAT(gc, mesi_exclusive_to_shared);
                break;
        case CL_Modified:
                SIM_log_info(
                        3, &gc->log, GC_Log_MESI,
                        "mesi_receive: snoop read hit "
                        "on a modified line");
                if (!gc->config.no_STC)
                        flush_STC(gc,
                                  gc->lines[line_num].tag, 
                                  gc->lines[line_num].otag, 
                                  gc->lines[line_num].STC_type,
                                  gc->lines[line_num].status);
                penalty += copy_back(
                        gc, line_num, mem_op, 
                        NULL, NULL, 0);
                gc->lines[line_num].status = CL_Shared;
                INC_STAT(gc, mesi_modified_to_shared);
                break;
        default:
                SIM_log_error(
                        &gc->log, GC_Log_MESI,
                        "Cache line in unexpected "
                        "state in snoop read hit.");
        }

        return penalty;
}

/*  Receives transaction from coherent caches. */
cycles_t
mesi_snoop_transaction(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        int penalty = 0;
        int line_num, i;
        int size = 0;
        uint64 orig_pa, orig_la;

        /* first, propagate the snoop to higher level caches */
        for (i = 0; i < gc->hlc_size; i++)
                if (gc->hlc[i] && gc->hlc_ifc[i])
                        penalty += gc->hlc_ifc[i]->snoop_transaction(
                                gc->hlc[i], mem_op);

        /* Look for matching lines. */
        orig_pa = mem_op->physical_address;
        orig_la = mem_op->logical_address;

        for (size = 0; size < mem_op->size; size += gc->config.line_size) {

                mem_op->physical_address = orig_pa + size;
                mem_op->logical_address = orig_la + size;
                line_num = lookup_line(gc, mem_op);
                SIM_log_info(4, &gc->log, GC_Log_MESI, "mesi_receive");

                if (line_num != -1) {
                        
                        HOOK_SNOOP_HIT_PRE(gc, line_num, mem_op);

                        if (SIM_mem_op_is_read(mem_op)) {
                                penalty = mesi_snoop_read(gc, mem_op, line_num);
                        } 
                        else {
                                SIM_log_info(3, &gc->log, GC_Log_MESI,
                                             "mesi_receive: snoop write hit");
                                penalty = empty_line(gc, line_num, mem_op, 
                                                     NULL, NULL);
                                INC_STAT(gc, mesi_invalidate);
                        }

                        HOOK_SNOOP_HIT_POST(gc, line_num, mem_op);
                }
        }

        mem_op->physical_address = orig_pa;
        mem_op->logical_address = orig_la;
                
        return penalty;
}

cycles_t
mesi_snoop_transaction_export(conf_object_t *obj, generic_transaction_t *mem_op)
{
        generic_cache_t *gc = (generic_cache_t *)obj;
        return mesi_snoop_transaction(gc, mem_op);
}

/* Handles read transactions coming to the cache. */
static cycles_t
handle_read(generic_cache_t *gc, generic_transaction_t *mem_op,
            conf_object_t *space, map_list_t *map)
{
        int penalty = 0;
        int line_num;

        /* Update the statistics. */
        if (SIM_mem_op_is_instruction(mem_op))
                INC_STAT(gc, inst_fetch);
        else
                INC_STAT(gc, data_read);

        /* Look for a matching line. */
        line_num = lookup_line(gc, mem_op);
        penalty += gc->penalty.read; /* set a read penalty for everything */

        /* Check if we got a hit. */
        if (line_num != -1) {
                /* Yes, we have a hit. */
                SIM_log_info(3, &gc->log, GC_Log_Read_Hit,
                             "handle_read: transaction is a hit (line %d)", 
                             line_num);

                HOOK_READ_HIT(gc, line_num, mem_op);
        }
        else {
                /* No, we have a miss. */
                SIM_log_info(3, &gc->log, GC_Log_Read_Miss,
                             "handle_read: transaction is a miss");

                /* Broadcast the read to the other caches. */
                if (gc->config.mesi)
                        penalty += mesi_send(gc, mem_op);
                
                /* Update the statistics. */
                if (SIM_mem_op_is_data(mem_op)) {
                        INC_STAT(gc, data_read_miss);
                        
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
                }
                else {
                        INC_STAT(gc, inst_fetch_miss);
                        
                        /* update the profilers */
                        if (gc->prof[V_IFM].id)
                                prof_data_add(gc->prof[V_IFM].id,
                                              GC_VA_ADDRESS(mem_op),
                                              1);
                        if (gc->prof[P_IFM].id)
                                prof_data_add(gc->prof[P_IFM].id,
                                              GC_PA_ADDRESS(mem_op),
                                              1);
                }

                /* Choose a line to use, empty it of any current
                 * content and fetch its new content. */
                line_num = gc->config.repl_fun.get_line(
                        gc->config.repl_data, gc, mem_op);
                penalty += empty_line(gc, line_num, mem_op, space, map);
                penalty += fetch_line(gc, line_num, mem_op, space, map);

                /* The line is now shared. */
                gc->lines[line_num].status = CL_Shared;
        }

        /* Update the replacement state. */
        gc->config.repl_fun.update_repl(gc->config.repl_data, 
                                        gc, mem_op, line_num);

        HOOK_READ_POST(gc, line_num, mem_op);

        /* we shouldn't try to use the STC if we get transactions that are
           created by a higher cache */
        if (HOOK_BLOCK_STC(
                    gc, line_num, 
                    gc->config.no_STC 
                    || ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Cache))) {
                SIM_log_info(4, &gc->log, GC_Log_Cache, 
                             "handle_read: blocking STC");
                mem_op->block_STC = 1;
        }
        else {
                /* The line may be added to one of the STCs. */
                if (SIM_mem_op_is_data(mem_op)) {
                        gc->config.direct_read_listener = 1;
                        gc->lines[line_num].STC_type |= STC_DataSTC;
                }
                else {
                        gc->lines[line_num].STC_type |= STC_InstSTC;
                }
        }

        return penalty;
}

/* Handles write transaction coming to the cache. */
static cycles_t
handle_write(generic_cache_t *gc, generic_transaction_t *mem_op,
             conf_object_t *space, map_list_t *map)
{
        int penalty = 0;
        int line_num;
        
        /* Update the statistics. */
        INC_STAT(gc, data_write);

        /* Look for a matching line. */
        line_num = lookup_line(gc, mem_op);
        penalty += gc->penalty.write;

        /* Check if we got a hit. */
        if (line_num != -1) {
                /* Yes, we have a hit. */
                SIM_log_info(3, &gc->log, GC_Log_Write_Hit,
                             "handle_write: transaction is a hit (line %d)", 
                             line_num);
                
                HOOK_WRITE_HIT(gc, line_num, mem_op);

                /* if it's a hit, we must broadcast hit depending on the 
                   line status */
                 if (gc->config.mesi 
                     && gc->lines[line_num].status != CL_Exclusive 
                     && gc->lines[line_num].status != CL_Modified)
                         penalty += mesi_send(gc, mem_op);
        }
        else {
                /* No, we have a miss. */
                SIM_log_info(3, &gc->log, GC_Log_Write_Miss,
                             "handle_write: transaction is a miss");

                /* Update the statistics. */
                INC_STAT(gc, data_write_miss);
                
                /* Update the profilers */
                if (gc->prof[I_DWM].id) {
                        /* we can't have misses placed in the STC by a next
                           cache because we want to have all misses with the
                           right PC. */
                        if (!gc->config.write_allocate)
                                mem_op->block_STC = 1;
                        prof_data_inc_pc(gc->prof[I_DWM].id, GC_CPU(mem_op));
                }

                if (gc->prof[V_DWM].id)
                        prof_data_add(gc->prof[V_DWM].id,
                                      GC_VA_ADDRESS(mem_op),
                                      1);

                if (gc->prof[P_DWM].id)
                        prof_data_add(gc->prof[P_DWM].id, 
                                      GC_PA_ADDRESS(mem_op), 
                                      1);
                
                /* if it's a miss, we should always broadcast it 
                   WT, NWA -> just WT
                   WT,  WA -> just WT + line allocated Exclusive
                   WB, NWA -> just WT
                   WB,  WA -> line allocated Modified
                */
                if (gc->config.mesi) {
                        /* we want to see all misses in there's no
                           allocation done and we're using MESI */
                        if (!gc->config.write_allocate)
                                mem_op->block_STC = 1;
                        penalty += mesi_send(gc, mem_op);
                }

                /* If we have a write-allocate cache we choose a line to use,
                   empty it of any current contents and fetch its new
                   contents. */
                if (gc->config.write_allocate) {
                        line_num = gc->config.repl_fun.get_line(
                                gc->config.repl_data, gc, mem_op);
                        penalty += empty_line(gc, line_num, mem_op, space, map);
                        penalty += fetch_line(gc, line_num, mem_op, space, map);
                }
        }

        /* If we have a write-through cache or we have a miss in a
           non-write-allocate cache we need to send the transaction to
           the next level cache. */
        if (!gc->config.write_back || line_num == -1) {

                /* If the cache is write-back non-write allocate, we're
                   going to end up in a statistics hell if we try to use the
                   STC in the next levels. */
                if (gc->config.write_back)
                        mem_op->block_STC = 1;

                SIM_log_info(3, &gc->log, 
                             ((!gc->config.write_back) 
                              ? GC_Log_Write_Miss | GC_Log_Write_Hit
                              : GC_Log_Write_Miss),
                             "handle_write: writing to next level");
                
                /* count a write-next penalty */
                penalty += gc->penalty.write_next;
                if (gc->timing_model)
                        penalty += gc->timing_ifc->operate(
                                gc->timing_model, space, map, mem_op);
        }

        /* Check if we used a cache line. */
        if (line_num != -1) {
                /* The line is now in modified or exclusive state,
                 * depending on if the cache is write-back. */
                if (gc->config.write_back)
                        gc->lines[line_num].status = CL_Modified;
                else
                        gc->lines[line_num].status = CL_Exclusive;
                
                /* Update the replacement state. */
                gc->config.repl_fun.update_repl(gc->config.repl_data, 
                                                gc, mem_op, line_num);

                HOOK_WRITE_POST(gc, line_num, mem_op);
        }

        /* If we handle a cache transaction, there's no need to care about the
           STCs. */
        if (HOOK_BLOCK_STC(
                    gc, line_num,
                    gc->config.no_STC 
                    || ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Cache))) {
                SIM_log_info(4, &gc->log, GC_Log_Cache,
                             "handle_write: blocking STC");
                mem_op->block_STC = 1;
        }
        else {
                if (mem_op->block_STC == 0) {
                        gc->config.direct_write_listener = 1;
                        if (line_num != -1) {
                                gc->lines[line_num].STC_type |= STC_DataSTC;
                        }
                }
        }
        
        return penalty;
}

static cycles_t
gc_operate(conf_object_t *mem_hier, conf_object_t *space,
           map_list_t *map, generic_transaction_t *mem_op)
{
        generic_cache_t *gc = (generic_cache_t *) mem_hier;
        cycles_t stall_time;

        SIM_log_info(4, &gc->log, GC_Log_Cache,
                     "operate: *** new transaction ***");

        /* Set reissue to 0 so we won't see the transaction again. */
        mem_op->reissue = 0;

        /* Run HOOK_PREFETCH for prefetch transactions. */
        if (SIM_mem_op_is_prefetch(mem_op)) {
                if (HOOK_PREFETCH(gc, mem_op))
                        return 0;

                if (gc->timing_model) {
                        SIM_log_info(4, &gc->log, GC_Log_Cache,
                                     "operate: passing prefetch transaction "
                                     "to next level");
                        stall_time = gc->timing_ifc->operate(
                                gc->timing_model, space, map, mem_op);
                }
                else
                        stall_time = 0;
        }
        else if (SIM_mem_op_is_control(mem_op)) {
                if (HOOK_CONTROL(gc, mem_op))
                        return 0;

                if (gc->timing_model) {
                        SIM_log_info(4, &gc->log, GC_Log_Cache,
                                     "operate: passing control transaction "
                                     "to next level");
                        stall_time = gc->timing_ifc->operate(
                                gc->timing_model, space, map, mem_op);
                }
                else
                        stall_time = 0;
        }
        else {

                /* Update the statistics. */
                INC_STAT(gc, transaction);

                if (is_uncacheable(gc, mem_op, map, &gc->log) 
                    || HOOK_DISABLED(gc)) {                                 

                        /* Handle uncacheable transactions. */
                        SIM_log_info(3, &gc->log, GC_Log_Cache,
                                     "operate: transaction is uncacheable");

                        /* Check if it's a device transaction to count
                           it apart from cpu transactions */
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
                                else
                                        INC_STAT(gc, uc_data_write);
                        }

                        if (gc->timing_model) {
                                SIM_log_info(3, &gc->log, GC_Log_Cache,
                                             "operate: passing transaction "
                                             "to next level");
                                stall_time = gc->timing_ifc->operate(
                                        gc->timing_model, space, map, mem_op);
                        }
                        else
                                stall_time = 0;
                        
                        /* if the transaction is uncacheable, block STC so that
                           we won't get STC hit reported for uncacheable values
                           - just in case the STC thinks it could cache them */
                        mem_op->block_STC = 1;
                }
                else {

                        /* Handle cacheable transactions. */
#ifdef GC_DEBUG
                        const char *trans_type;

                        if (SIM_mem_op_is_read(mem_op)) {
                                if (SIM_mem_op_is_instruction(mem_op))
                                        trans_type = "inst. fetch";
                                else
                                        trans_type = "data read";
                        }
                        else
                                trans_type = "data write ";

                        SIM_log_info(1, &gc->log, GC_Log_Cache,
                                     "operate: %s (phys = 0x%llx, "
                                     "log = 0x%llx, tag = 0x%llx, size = %d)",
                                     trans_type,
                                     mem_op->physical_address,
                                     mem_op->logical_address,
                                     GC_UNTAG(gc, GC_TAG(gc, mem_op)),
                                     mem_op->size);
#endif

                        if (SIM_mem_op_is_read(mem_op))
                                stall_time = handle_read(gc, mem_op, 
                                                         space, map);
                        else
                                stall_time = handle_write(gc, mem_op, 
                                                          space, map);
                }
        }

        if (mem_op->may_stall) {
                SIM_log_info(4, &gc->log, GC_Log_Cache,
                             "operate: returning %lld cycles penalty",
                             stall_time);
                return stall_time;
        }
        else {
                gc->stat.lost_stall_cycles += stall_time;
                SIM_log_info(4, &gc->log, GC_Log_Cache,
                             "operate: missing %lld cycles penalty",
                             stall_time);
                return 0;
        }
}

/* Call fun once for each cache line that the memop touches, and return the max
   of their stall times. */
static cycles_t
cc_each_line(conf_object_t *cache, generic_transaction_t *mem_op,
             cycles_t (*fun)(generic_cache_t *, generic_transaction_t *))
{
        generic_cache_t *gc = (generic_cache_t *)cache;
        cache_memory_transaction_t trans;
        cycles_t penalty = 0;
        physical_address_t start, end, offs;

        /* If the memop doesn't straddle cache lines, just pass it through. */
        if (((mem_op->physical_address
              ^ (mem_op->physical_address + mem_op->size - 1))
             >> gc->config.line_size_ln2) == 0)
                return fun(gc, mem_op);

        /* Create a wrapper memop. */
        trans.s = *mem_op;
        trans.s.ini_type = Sim_Initiator_Cache;
        trans.s.ini_ptr = cache;
        trans.s.id = 0;
        if ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Cache) {
                cache_memory_transaction_t *ct =
                        (cache_memory_transaction_t *) mem_op;
                trans.initial_trans = ct->initial_trans;
        } else {
                trans.initial_trans = mem_op;
        }

        /* Loop over all cache lines that the original memop intersects. */
        offs = 0;
        while (offs < mem_op->size) {
                trans.s.physical_address = mem_op->physical_address + offs;
                trans.s.logical_address = mem_op->logical_address + offs;
                start = trans.s.physical_address;
                end = MIN(start | (gc->config.line_size - 1),
                          mem_op->size - offs);
                trans.s.size = end - start + 1;
                penalty = MAX(penalty, fun(gc, &trans.s));
                offs = (offs | (gc->config.line_size - 1)) + 1;
        }
        return penalty;
}

static cycles_t
cc_fetch_one_line(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        cycles_t penalty = 0;
        int line;

        if (lookup_line(gc, mem_op) == -1) {
                /* Choose a line to use, empty it of any current content and
                   fetch its new content. */
                line = gc->config.repl_fun.get_line(
                        gc->config.repl_data, gc, mem_op);
                penalty += empty_line(gc, line, mem_op, NULL, NULL);
                penalty += fetch_line(gc, line, mem_op, NULL, NULL);

                /* The line is now shared. */
                gc->lines[line].status = CL_Shared;
        }
        return penalty;
}

static cycles_t
cc_invalidate_one_line(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        /* Empty line if it is in the cache. */
        int line = lookup_line(gc, mem_op);
        if (line != -1)
                return empty_line(gc, line, mem_op, NULL, NULL);
        else
                return 0;
}

static cycles_t
cc_copyback_one_line(generic_cache_t *gc, generic_transaction_t *mem_op)
{
        cache_line_t *cl;
        cycles_t penalty = 0;
        int line;

        line = lookup_line(gc, mem_op);
        if (line != -1) {
                /* Line is cached. */
                cl = &gc->lines[line];
                if (cl->status == CL_Modified) {
                        /* Line is modified, so we have to copy it back. */
                        penalty += copy_back(gc, line, mem_op, NULL, NULL, 1);
                        cl->status = CL_Exclusive;
                }
        }
        return penalty;
}

static cycles_t
cc_invalidate_cache(generic_cache_t *gc)
{
        /* Clear STCs from all entries  */
        for (int l = 0; l < gc->config.line_number; l++) {
                cache_line_t *cl = &gc->lines[l];
                if (cl->status != CL_Invalid)
                        flush_STC(gc, cl->tag, cl->otag, 
                                  cl->STC_type, cl->status);
        }
        CASSERT_STMT(CL_Invalid == 0); 
        memset(gc->lines, 0, sizeof(cache_line_t) * gc->config.line_number);
        return 0;
}


static UNUSED cycles_t
cache_control(conf_object_t *cache, cache_control_operation_t op,
              generic_transaction_t *mem_op)
{
        generic_cache_t *gc = (generic_cache_t *) cache;
        SIM_log_info(2, &gc->log, 0,
                     "cache control %d", op);

        switch (op) {
        case Cache_Control_Fetch_Line:
                return cc_each_line(cache, mem_op, cc_fetch_one_line);
        case Cache_Control_Invalidate_Line:
                return cc_each_line(cache, mem_op, cc_invalidate_one_line);
        case Cache_Control_Copyback_Line:
                return cc_each_line(cache, mem_op, cc_copyback_one_line);
        case Cache_Control_Invalidate_Cache:
                return cc_invalidate_cache(gc);
        default:
                ASSERT(0);
                break;
        }
}
