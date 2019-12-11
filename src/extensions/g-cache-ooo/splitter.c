/*
  splitter.c

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
 * This class implements a out-of-order transaction
 * splitter. Transactions are divided in two if they are unaligned and
 * cross over a cache line. The module supports multiple outstanding
 * transactions.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

#include "gc-common.h"

#define TS_TAG(ts, addr) ((addr) >> (ts)->ncls_ln2)
#define TS_CL_ADDR(ts, addr) ((addr) & ~((ts)->next_cache_line_size - 1))

#define TABLE_SPLITTER_SIZE 0x10000
#define TABLE_SPLITTER_MASK (TABLE_SPLITTER_SIZE - 1)

#define TRANS_POOL_TOTAL 0x1000 /* 4096 transactions */

#undef TRANS_POOL_DEBUG

typedef struct double_trans {
        int used;
        int stall_a, stall_b;
        cache_memory_transaction_t a;
        cache_memory_transaction_t b;
#ifdef TRANS_POOL_DEBUG
        cycles_t arrived;
#endif
} double_trans_t;

typedef struct trans_splitter {

        log_object_t log;

        /* hash table for transactions */
        double_trans_t *table[TABLE_SPLITTER_SIZE]; 

        double_trans_t *pool; /* pool of transactions to use */
        int pool_current;

        /* statistics */
        integer_t split_transactions;
        integer_t transactions;

        generic_cache_t *cache;
        
        conf_object_t *timing_model;
        timing_model_interface_t *tm_ifc;

        int next_cache_line_size;
        int ncls_ln2; /* ln2(next_cache_line_size) */

} trans_splitter_t;


conf_object_t *
ts_new_instance(parse_object_t *pa)
{
        trans_splitter_t *ts = MM_ZALLOC(1, trans_splitter_t);

        SIM_log_constructor(&ts->log, pa);

        ts->pool = MM_ZALLOC(TRANS_POOL_TOTAL, double_trans_t);
        
        return (conf_object_t *) ts;
}


static double_trans_t *
new_trans(trans_splitter_t *ts)
{
        double_trans_t *ret;

        if (ts->pool[ts->pool_current].used) {
                int id;
                for (id = 0; id < TABLE_SPLITTER_SIZE; id++) {
                        if (&ts->pool[ts->pool_current] == ts->table[id])
                                break;
                }
#ifdef TRANS_POOL_DEBUG
                SIM_log_error(&ts->log, 0, "transaction pool overflowed, caused by mem_op with ID: %d arrived: %lld", 
                              id, ts->pool[ts->pool_current].arrived);
#else
                SIM_log_error(&ts->log, 0, "transaction pool overflowed, caused by mem_op with ID: %d.", id);
#endif
                SIM_break_simulation("");
        }

        ret = &ts->pool[ts->pool_current];
        ret->used = 1;
        ts->pool_current = (ts->pool_current + 1)
                & (TRANS_POOL_TOTAL - 1);
#ifdef TRANS_POOL_DEBUG
        ret->arrived = SIM_cycle_count((conf_object_t *)ts);
#endif        
        return ret;
}

cycles_t
ts_operate(conf_object_t *mem_hier, conf_object_t *space, 
           map_list_t *map, generic_transaction_t *mem_op)
{
        trans_splitter_t *ts = (trans_splitter_t *) mem_hier;
        int stall_time, index;
        double_trans_t *dt;
        
        /* uncacheable transactions are not modified */
        if (likely(TS_TAG(ts, mem_op->physical_address) == 
                   (TS_TAG(ts, mem_op->physical_address + mem_op->size - 1))) ||
            (ts->cache && unlikely(is_uncacheable(ts->cache, mem_op, map, &ts->log)))) {
                stall_time = ts->tm_ifc->operate(ts->timing_model, space, 
                                                 map, mem_op);
                if (!stall_time || !mem_op->reissue)
                        ts->transactions++;
                return stall_time;
        }

        /* here we have a cacheable, cache line crossing transaction */
        index = mem_op->id & TABLE_SPLITTER_MASK;
        if ((dt = ts->table[index]) == NULL) {

                int first_size;

                /* first time transaction */
                dt = new_trans(ts);
                ts->table[index] = dt;

                /* setup the two transactions */
                dt->a.s = *mem_op;
                dt->b.s = *mem_op;

                first_size = TS_CL_ADDR(ts, mem_op->physical_address 
                                        + mem_op->size - 1)
                        - mem_op->physical_address;

                dt->a.s.size = first_size;
                dt->a.s.ini_type = Sim_Initiator_Cache;
                dt->a.s.ini_ptr = (conf_object_t *) ts;
                
                dt->b.s.physical_address += first_size;
                dt->b.s.logical_address += first_size;
                dt->b.s.size -= first_size;
                dt->b.s.ini_type = Sim_Initiator_Cache;
                dt->b.s.ini_ptr = (conf_object_t *) ts;
                dt->b.s.id = SIM_get_unique_memory_transaction_id(
                        GC_CPU(mem_op));
                
                dt->stall_a = 0;
                dt->stall_b = 0;
                dt->a.s.reissue = 1;
                dt->b.s.reissue = 1;
        }

        /* update the initial_trans field */
        if ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Cache) {
                cache_memory_transaction_t *ct =
                        (cache_memory_transaction_t *) mem_op;
                dt->a.initial_trans = ct->initial_trans;
                dt->b.initial_trans = ct->initial_trans;
        }
        else {
                dt->a.initial_trans = mem_op;
                dt->b.initial_trans = mem_op;
        }

        if (!dt->stall_a && dt->a.s.reissue) {
                dt->a.s.reissue = 0;
                dt->stall_a = ts->tm_ifc->operate(ts->timing_model, space,
                                                  map, &dt->a.s);
                if (!dt->stall_a)
                        dt->a.s.reissue = 0;
        }

        if (!dt->stall_b && dt->b.s.reissue) {
                dt->b.s.reissue = 0;
                dt->stall_b = ts->tm_ifc->operate(ts->timing_model, space, 
                                                  map, &dt->b.s);
                if (!dt->stall_b)
                        dt->b.s.reissue = 0;
        }

        /* if at least one of the two needs reissue */
        if (dt->a.s.reissue || dt->b.s.reissue) {

                stall_time = MIN((dt->a.s.reissue) ? dt->stall_a : 0x7FFFFFFF, 
                                 (dt->b.s.reissue) ? dt->stall_b : 0x7FFFFFFF);
                dt->stall_a -= stall_time;
                dt->stall_b -= stall_time;
                mem_op->reissue = 1;
        }
        else {
                /* no reissue */
                stall_time = MAX(dt->stall_a, dt->stall_b);
                dt->used = 0;
                ts->table[index] = NULL;
                mem_op->reissue = 0;
                ts->split_transactions++;
                ts->transactions++;
        }

        return stall_time;
}

/* timing model */
static set_error_t
set_timing_model(void *dont_care, conf_object_t *obj,
                 attr_value_t *val, attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        if (val->kind == Sim_Val_Nil) {
                ts->tm_ifc = NULL;
                ts->timing_model = NULL;
        }
        else {
                /* get the timing model interface */
                ts->tm_ifc = SIM_get_interface(val->u.object, 
                                               TIMING_MODEL_INTERFACE);
                if (SIM_clear_exception()) {
                        SIM_log_error(&ts->log, 0,
                                      "set_timing_model: "
                                      "object does not provide the "
                                      "timing model interface.");
                        return Sim_Set_Illegal_Value;
                }

                ts->timing_model = val->u.object;
        }

        return Sim_Set_Ok;
}

static attr_value_t                                             
get_timing_model(void *dont_care, conf_object_t *obj,       
                 attr_value_t *idx)                         
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;          
        attr_value_t ret;                                       

        if (ts->timing_model) {
                ret.kind = Sim_Val_Object;
                ret.u.object = ts->timing_model;
        }
        else {
                ret.kind = Sim_Val_Nil;
        }

        return ret;
}

/* next_cache_line_size */
static set_error_t
set_nc_line_size(void *dont_care, conf_object_t *obj,
                 attr_value_t *val, attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        if ((1 << ln2(val->u.integer)) != val->u.integer) {
                SIM_log_error(&ts->log, 0,
                              "next_cache_line_size: must be a power of 2");
                return Sim_Set_Illegal_Value;
        }
   
        ts->next_cache_line_size = val->u.integer;
        ts->ncls_ln2 = ln2(ts->next_cache_line_size);

        return Sim_Set_Ok;
}

static attr_value_t                                             
get_nc_line_size(void *dont_care, conf_object_t *obj,       
                 attr_value_t *idx)                         
{                                                               
        trans_splitter_t *ts = (trans_splitter_t *) obj;          
        attr_value_t ret;                                       

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ts->next_cache_line_size;
        return ret;
}

/* transactions */
static set_error_t
set_transactions(void *dont_care, conf_object_t *obj,
                 attr_value_t *val, attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        ts->transactions = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t                                             
get_transactions(void *dont_care, conf_object_t *obj,       
                    attr_value_t *idx)                         
{                                                               
        trans_splitter_t *ts = (trans_splitter_t *) obj;          
        attr_value_t ret;                                       

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ts->transactions;
        return ret;
}

/* split_transactions */
static set_error_t
set_split_transactions(void *dont_care, conf_object_t *obj,
                 attr_value_t *val, attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        ts->split_transactions = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t                                             
get_split_transactions(void *dont_care, conf_object_t *obj,       
                    attr_value_t *idx)                         
{                                                               
        trans_splitter_t *ts = (trans_splitter_t *) obj;          
        attr_value_t ret;                                       

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ts->split_transactions;
        return ret;
}

static set_error_t
set_cache(void *dont_care, conf_object_t *obj,
          attr_value_t *val, attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        if (val->kind == Sim_Val_Nil)
                ts->cache = NULL;
        else
                ts->cache = (generic_cache_t *) val->u.object;
        
        return Sim_Set_Ok;
}

static attr_value_t                                             
get_cache(void *dont_care, conf_object_t *obj,       
          attr_value_t *idx)                         
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;
        attr_value_t ret;                                     

        if (ts->cache) {
                ret.kind = Sim_Val_Object;
                ret.u.object = (conf_object_t *) ts->cache;
        }
        else {
                ret.kind = Sim_Val_Nil;
        }

        return ret;        
}

static void
ts_register(conf_class_t *ts_class)
{
        SIM_register_typed_attribute(
                ts_class, "next-cache-line-size",
                get_nc_line_size, 0,
                set_nc_line_size, 0,
                Sim_Attr_Required,
                "i", NULL,
                "Cache line size used for splitting "
                "transactions.");

        SIM_register_typed_attribute(
                ts_class, "cache",
                get_cache, 0,
                set_cache, 0,
                Sim_Attr_Required,
                "o|n", NULL,
                "Cache to which the splitter is connected");

        SIM_register_typed_attribute(
                ts_class, "transactions",
                get_transactions, 0,
                set_transactions, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Total number of transactions processed.");

        SIM_register_typed_attribute(
                ts_class, "split-transactions",
                get_split_transactions, 0,
                set_split_transactions, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Number of transactions split.");

        SIM_register_typed_attribute(
                ts_class, "timing-model",
                get_timing_model, 0,
                set_timing_model, 0,
                Sim_Attr_Required,
                "o|n", NULL,
                "Object listening on transactions coming from "
                "the splitter.");
}

/*
  Information for class registering
*/
static conf_class_t *ts_class;
static class_data_t ts_data;
static timing_model_interface_t ts_ifc;

void
ts_init_local(void)
{
        ts_data.new_instance = ts_new_instance;
        ts_data.description =
                "A trans-splitter-ooo object can split a transaction that "
                "crosses a cache line in two non-crossing transactions.\n\n"
                
                "A trans-splitter-ooo can be inserted between the cpu and "
                "the caches if the cpu can issue cache-line crossing "
                "transactions (x86 being a good example). It can also be "
                "used between two caches to split transactions.\n\n"
                
                "A trans-splitter-ooo object supports multiple outstanding "
                "transactions. Note that it does not support splitting a "
                "transaction more than once, so transactions that crosses "
                "two cache lines or more will be split incorrectly.";
                
        if (!(ts_class = SIM_register_class("trans-splitter-ooo", 
                                            &ts_data))) {
                pr_err("Could not create trans-splitter-ooo class\n");
        } else {
                /* register the attributes */
                ts_register(ts_class);

                /* register the timing model interface */
                ts_ifc.operate = ts_operate;
                SIM_register_interface(ts_class, "timing-model", 
                                       (void *) &ts_ifc);
        }
}
