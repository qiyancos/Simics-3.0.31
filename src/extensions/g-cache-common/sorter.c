/*
  sorter.c

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

#include <errno.h>
#include <stdio.h>
#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

#include "gc-common.h"
#include "gc.h"

typedef enum {
        Trans_Cache_Mem   = 0,
        Trans_Cache_Dev   = 1,
        Trans_Uncache_Mem = 2,
        Trans_Uncache_Dev = 3,
        Trans_Max
} trans_sort_t;

typedef struct trans_sorter {

        log_object_t log;

        conf_object_t            *tm[Trans_Max];
        timing_model_interface_t *ifc[Trans_Max];
        int                       transactions[Trans_Max];

        generic_cache_t          *cache;
} trans_sorter_t;

static conf_object_t *
ts_new_instance(parse_object_t *pa)
{
        trans_sorter_t *obj = MM_ZALLOC(1, trans_sorter_t);
        SIM_log_constructor(&obj->log, pa);
        
        return (conf_object_t *)obj;
}

static cycles_t
ts_operate(conf_object_t *obj, conf_object_t *space, map_list_t *map, 
           generic_transaction_t *mem_op)
{
        trans_sorter_t *ts = (trans_sorter_t *) obj;
        int stall_time;
        int index = 0;

        if (is_uncacheable(ts->cache, mem_op, map, &ts->log))
                index = 2;

        if ((mem_op->ini_type & 0xFF00) == Sim_Initiator_Device)
                index++;

        if (ts->ifc[index])
                stall_time = ts->ifc[index]->operate(ts->tm[index], space, 
                                                     map, mem_op);
        else 
                stall_time = 0;

        if (!stall_time || !mem_op->reissue)
                ts->transactions[index]++;

        return stall_time;
}

static set_error_t
set_cache(void *dont_care, conf_object_t *obj,
          attr_value_t *val, attr_value_t *idx)
{
        trans_sorter_t *ts = (trans_sorter_t *) obj;

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
        trans_sorter_t *ts = (trans_sorter_t *) obj;
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


static set_error_t
set_tm(trans_sorter_t *ts, attr_value_t *val, int t)
{
        if (val->kind == Sim_Val_Nil) {
                ts->ifc[t] = NULL;
                ts->tm[t] = NULL;
        }
        else {
                ts->ifc[t] = SIM_get_interface(val->u.object, 
                                       TIMING_MODEL_INTERFACE);
                if (SIM_clear_exception()) {
                        SIM_log_error(&ts->log, 0,
                                      "set_tm: "
                                      "object does not provide the "
                                      "timing model interface.");
                        return Sim_Set_Illegal_Value;
                }
        
                ts->tm[t] = val->u.object;
        }
        
        return Sim_Set_Ok;
}

static set_error_t
set_c_mem_tm(void *dont_care, conf_object_t *obj,
             attr_value_t *val, attr_value_t *idx)
{
        return set_tm((trans_sorter_t *) obj, val, Trans_Cache_Mem);
}

static set_error_t
set_c_dev_tm(void *dont_care, conf_object_t *obj,
             attr_value_t *val, attr_value_t *idx)
{
        return set_tm((trans_sorter_t *) obj, val, Trans_Cache_Dev);
}

static set_error_t
set_u_mem_tm(void *dont_care, conf_object_t *obj,
             attr_value_t *val, attr_value_t *idx)
{
        return set_tm((trans_sorter_t *) obj, val, Trans_Uncache_Mem);
}

static set_error_t
set_u_dev_tm(void *dont_care, conf_object_t *obj,
            attr_value_t *val, attr_value_t *idx)
{
        return set_tm((trans_sorter_t *) obj, val, Trans_Uncache_Dev);
}

static attr_value_t                                             
get_tm(trans_sorter_t *ts, trans_sort_t t)
{                                                               
        attr_value_t ret;                                     

        if (ts->tm[t]) {
                ret.kind = Sim_Val_Object;
                ret.u.object = ts->tm[t];
        }
        else {
                ret.kind = Sim_Val_Nil;
        }

        return ret;        
}

static attr_value_t                                             
get_c_mem_tm(void *dont_care, conf_object_t *obj,       
             attr_value_t *idx)                         
{
        return get_tm((trans_sorter_t *) obj, Trans_Cache_Mem);
}

static attr_value_t                                             
get_c_dev_tm(void *dont_care, conf_object_t *obj,       
           attr_value_t *idx)                         
{
        return get_tm((trans_sorter_t *) obj, Trans_Cache_Dev);
}

static attr_value_t                                             
get_u_mem_tm(void *dont_care, conf_object_t *obj,       
             attr_value_t *idx)                         
{
        return get_tm((trans_sorter_t *) obj, Trans_Uncache_Mem);
}

static attr_value_t                                             
get_u_dev_tm(void *dont_care, conf_object_t *obj,       
            attr_value_t *idx)                         
{
        return get_tm((trans_sorter_t *) obj, Trans_Uncache_Dev);
}



static set_error_t
set_stat(trans_sorter_t *ts, attr_value_t *val, int t)
{
        ts->transactions[t] = val->u.integer;

        return Sim_Set_Ok;
}

static set_error_t
set_c_mem_stat(void *dont_care, conf_object_t *obj,
               attr_value_t *val, attr_value_t *idx)
{
        return set_stat((trans_sorter_t *) obj, val, Trans_Cache_Mem);
}

static set_error_t
set_c_dev_stat(void *dont_care, conf_object_t *obj,
               attr_value_t *val, attr_value_t *idx)
{
        return set_stat((trans_sorter_t *) obj, val, Trans_Cache_Dev);
}

static set_error_t
set_u_mem_stat(void *dont_care, conf_object_t *obj,
               attr_value_t *val, attr_value_t *idx)
{
        return set_stat((trans_sorter_t *) obj, val, Trans_Uncache_Mem);
}

static set_error_t
set_u_dev_stat(void *dont_care, conf_object_t *obj,
               attr_value_t *val, attr_value_t *idx)
{
        return set_stat((trans_sorter_t *) obj, val, Trans_Uncache_Dev);
}




static attr_value_t                                             
get_stat(trans_sorter_t *ts, trans_sort_t t)
{                                                               
        attr_value_t ret;                                     

        ret.kind = Sim_Val_Integer;
        ret.u.integer = ts->transactions[t];
        return ret;        
}

static attr_value_t                                             
get_c_mem_stat(void *dont_care, conf_object_t *obj,       
               attr_value_t *idx)                         
{
        return get_stat((trans_sorter_t *) obj, Trans_Cache_Mem);
}

static attr_value_t                                             
get_c_dev_stat(void *dont_care, conf_object_t *obj,       
               attr_value_t *idx)                         
{
        return get_stat((trans_sorter_t *) obj, Trans_Cache_Dev);
}

static attr_value_t                                             
get_u_mem_stat(void *dont_care, conf_object_t *obj,       
               attr_value_t *idx)                         
{
        return get_stat((trans_sorter_t *) obj, Trans_Uncache_Mem);
}

static attr_value_t                                             
get_u_dev_stat(void *dont_care, conf_object_t *obj,       
               attr_value_t *idx)                         
{
        return get_stat((trans_sorter_t *) obj, Trans_Uncache_Dev);
}

static conf_class_t *ts_class;
static class_data_t ts_data;
static timing_model_interface_t ts_ifc;

void
sort_init_local(void)
{
        ts_data.new_instance = ts_new_instance;
        ts_data.description = 
                "A trans-sorter object divides the transactions in "
                "4 transaction flows according to two criteria: are they "
                "cacheable or not? Are they generated by the cpu or by a "
                "device? They are forwarded to the four timing models "
                "attributes corresponding to the four possibilities. "
                "This can be useful to ignore some types of transactions when "
                "tracing or connecting a memory hierarchy.";
        
        if (!(ts_class = SIM_register_class("trans-sorter", &ts_data))) {
                pr_err("Could not create g-cache class\n");
        } else {

                /* initialize and register the timing-model interface */
                ts_ifc.operate = ts_operate;
                SIM_register_interface(ts_class, "timing-model", &ts_ifc);

                /* initialize attributes */
                SIM_register_typed_attribute(
                        ts_class, "cache", 
                        get_cache, NULL, 
                        set_cache, NULL, 
                        Sim_Attr_Required,
                        "o|n", NULL,
                        "Cache to which the sorter is connected.");

                SIM_register_typed_attribute(
                        ts_class, "cacheable-mem-timing_model", 
                        get_c_mem_tm, NULL, 
                        set_c_mem_tm, NULL, 
                        Sim_Attr_Optional,
                        "o|n", NULL,
                        "Timing model which will receive cacheable "
                        "memory transactions.");
        
                SIM_register_typed_attribute(
                        ts_class, "cacheable-dev-timing_model", 
                        get_c_dev_tm, NULL, 
                        set_c_dev_tm, NULL, 
                        Sim_Attr_Optional,
                        "o|n", NULL,
                        "Timing model which will receive cacheable "
                        "device transactions.");

                SIM_register_typed_attribute(
                        ts_class, "uncacheable-mem-timing_model", 
                        get_u_mem_tm, NULL, 
                        set_u_mem_tm, NULL, 
                        Sim_Attr_Optional,
                        "o|n", NULL,
                        "Timing model which will receive uncacheable "
                        "memory transactions.");
        
                SIM_register_typed_attribute(
                        ts_class, "uncacheable-dev-timing_model", 
                        get_u_dev_tm, NULL, 
                        set_u_dev_tm, NULL, 
                        Sim_Attr_Optional,
                        "o|n", NULL,
                        "Timing model which will receive uncacheable "
                        "device transactions."); 

                SIM_register_typed_attribute(
                        ts_class, "cacheable-mem-transactions", 
                        get_c_mem_stat, NULL, 
                        set_c_mem_stat, NULL, 
                        Sim_Attr_Optional,
                        "i", NULL,
                        "Number of cacheable memory transactions.");
        
                SIM_register_typed_attribute(
                        ts_class, "cacheable-dev-transactions", 
                        get_c_dev_stat, NULL, 
                        set_c_dev_stat, NULL, 
                        Sim_Attr_Optional,
                        "i", NULL,
                        "Number of cacheable device transactions.");

                SIM_register_typed_attribute(
                        ts_class, "uncacheable-mem-transactions", 
                        get_u_mem_stat, NULL, 
                        set_u_mem_stat, NULL, 
                        Sim_Attr_Optional,
                        "i", NULL,
                        "Number of uncacheable memory transactions.");
        
                SIM_register_typed_attribute(
                        ts_class, "uncacheable-dev-transactions", 
                        get_u_dev_stat, NULL, 
                        set_u_dev_stat, NULL, 
                        Sim_Attr_Optional,
                        "i", NULL,
                        "Number of uncacheable device transactions."); 
        }
}

