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
 * This class implements a transaction splitter. Transactions are split if they
 * are cacheable and span multiple cache lines in the next level cache. The
 * module does not support multiple outstanding transactions.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

#include "gc-common.h"
#include "gc.h"

#define TS_CL_TAG(ts, addr) ((addr) >> (ts)->next_cache_line_size_ln2)
#define TS_CL_ADDR(ts, addr) ((addr) & ~((ts)->next_cache_line_size_ln2 - 1))

typedef struct trans_splitter {
        log_object_t log;

        /* statistics */
        integer_t transactions;
        integer_t split_transactions;

        conf_object_t *timing_model;
        timing_model_interface_t *tm_ifc;

        int next_cache_line_size;
        int next_cache_line_size_ln2;
        generic_cache_t *cache;
} trans_splitter_t;

static conf_object_t *
ts_new_instance(parse_object_t *pa)
{
        trans_splitter_t *ts = MM_ZALLOC(1, trans_splitter_t);

        SIM_log_constructor(&ts->log, pa);

        return (conf_object_t *) ts;
}

static cycles_t
ts_operate(conf_object_t *mem_hier, conf_object_t *space, 
           map_list_t *map, generic_transaction_t *mem_op)
{
        trans_splitter_t *ts = (trans_splitter_t *) mem_hier;
        int total_stall_time;
        cache_memory_transaction_t trans;
        generic_address_t offset;

        ts->transactions++;

        /* Transactions that don't span multiple cache lines or are
         * uncacheable are not modified */
        if (likely(TS_CL_TAG(ts, mem_op->physical_address) 
                   == (TS_CL_TAG(ts, mem_op->physical_address+mem_op->size-1))) 
            || unlikely(is_uncacheable(ts->cache, mem_op, map, &ts->log)))
                return ts->tm_ifc->operate(ts->timing_model, space, 
                                           map, mem_op);

        /* Here we have a cacheable cache line crossing transaction */
        ts->split_transactions++;

        total_stall_time = 0;
        trans.s = *mem_op;
        trans.s.ini_type = Sim_Initiator_Cache;
        trans.s.ini_ptr = (conf_object_t *) ts;
        
        /* we won't need reissue */
        mem_op->reissue = 0;

        /* update the initial_trans field */
        if ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Cache) {
                cache_memory_transaction_t *ct =
                        (cache_memory_transaction_t *) mem_op;
                trans.initial_trans = ct->initial_trans;
        }
        else {
                trans.initial_trans = mem_op;
        }

        offset = 0;
        while (offset < mem_op->size) {
                int stall_time;
                trans.s.physical_address = mem_op->physical_address + offset;
                trans.s.logical_address = mem_op->logical_address + offset;
                trans.s.size = MIN(mem_op->size - offset, 
                                 TS_CL_ADDR(ts, trans.s.physical_address 
                                            + ts->next_cache_line_size) 
                                 - trans.s.physical_address);
                trans.s.id = 0;
                stall_time = ts->tm_ifc->operate(ts->timing_model, space, map, 
                                                 &trans.s);
                total_stall_time = MAX(total_stall_time, stall_time);
                if (trans.s.exception != Sim_PE_No_Exception)
                        mem_op->exception = trans.s.exception;
                offset += trans.s.size;
        }

        return total_stall_time;
}

/* timing model */
static set_error_t
set_timing_model(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                 attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        if (val->kind == Sim_Val_Nil) {
                ts->tm_ifc = NULL;
                ts->timing_model = NULL;
        }
        else {
        
                ts->tm_ifc = SIM_get_interface(val->u.object, 
                                               TIMING_MODEL_INTERFACE);
                if (SIM_clear_exception()) {
                        SIM_log_error(&ts->log, 0,
                                      "set_timing_model: object does not "
                                      "provide the timing model interface.");
                        return Sim_Set_Illegal_Value;
                }

                ts->timing_model = val->u.object;
        }

        return Sim_Set_Ok;
}

static attr_value_t
get_timing_model(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;
        attr_value_t ret;

        if (ts->timing_model) {
                ret.kind = Sim_Val_Object;
                ret.u.object = ts->timing_model;
        }
        else
                ret.kind = Sim_Val_Nil;

        return ret;
}

/* next_cache_line_size */
static set_error_t
set_nc_line_size(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                 attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        if ((1 << ln2(val->u.integer)) != val->u.integer) {
                SIM_log_error(&ts->log, 0,
                              "next_cache_line_size: must be a power of 2");
                return Sim_Set_Illegal_Value;
        }

        ts->next_cache_line_size = val->u.integer;
        ts->next_cache_line_size_ln2 = ln2(ts->next_cache_line_size);

        return Sim_Set_Ok;
}

static attr_value_t
get_nc_line_size(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ts->next_cache_line_size;
        return ret;
}

/* transactions */
static set_error_t
set_transactions(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                 attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        ts->transactions = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_transactions(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;
        attr_value_t ret;

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ts->transactions;
        return ret;
}

/* split_transactions */
static set_error_t
set_split_transactions(void *dont_care, conf_object_t *obj, attr_value_t *val, 
                       attr_value_t *idx)
{
        trans_splitter_t *ts = (trans_splitter_t *) obj;

        ts->split_transactions = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_split_transactions(void *dont_care, conf_object_t *obj, attr_value_t *idx)
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
                ts_class, "cache",
                get_cache, 0,
                set_cache, 0,
                Sim_Attr_Required,
                "o", NULL,
                "Cache to which the splitter is connected.");

        SIM_register_typed_attribute(
                ts_class, "next-cache-line-size",
                get_nc_line_size, 0,
                set_nc_line_size, 0,
                Sim_Attr_Required,
                "i", NULL,
                "Cache line size used for splitting transactions.");

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
                "Number of split transactions.");

        SIM_register_typed_attribute(
                ts_class, "timing-model",
                get_timing_model, 0,
                set_timing_model, 0,
                Sim_Attr_Required,
                "o", NULL,
                "Object listening on transactions coming "
                "from the splitter.");
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
                "A trans-splitter object should be inserted between two caches if the higher-level "
                "cache has a larger cache line size than the lower-level cache, or between the "
                "processor and the id-splitter object if you have a processor that can do "
                "unaligned accesses or accesses larger than one cache line. It splits cacheable "
                "transactions that span more than one naturally aligned next-cache-line-size bytes "
                "big lines into multiple transactions that each fit within one line.";

        if (!(ts_class = SIM_register_class("trans-splitter", &ts_data))) {
                fputs("Could not create trans-splitter class\n", stderr);
        } else {
                /* register the attributes */
                ts_register(ts_class);

                /* register the timing model interface */
                ts_ifc.operate = ts_operate;
                SIM_register_interface(ts_class, "timing-model", &ts_ifc);
        }
}
