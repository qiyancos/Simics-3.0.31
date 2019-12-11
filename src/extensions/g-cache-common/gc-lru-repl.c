/*
  gc-lru-repl.c - perfect LRU replacement implementation for all caches

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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

/* cache includes */
#include "gc-common.h"
#include "gc.h"

typedef struct lru_data {
        integer_t *last_used;
} lru_data_t;

static const char *
lru_get_name(void)
{
        return "lru";
}

static void
lru_update_repl(void *data, generic_cache_t *gc, generic_transaction_t *gt, 
                 int line_num)
{
        lru_data_t *d = (lru_data_t *) data;

#ifdef GC_USE_STC
        /* empty other lines from STC if we are using the STC from this cache */
        if (!gc->config.no_STC 
            && (gc->config.direct_read_listener
                || gc->config.direct_write_listener)) {
                /* Remove the previously most recent line from the STC */
                int k,j;
                uinteger_t newest = (uinteger_t) -1;

                for (k=j=GC_INDEX(gc, gt);
                     k<gc->config.line_number;
                     k+= GC_NEXT_ASSOC(gc)) {

                        if (newest < d->last_used[k]) {
                                newest = d->last_used[k];
                                j = k;
                        }
                }

                /* flush STC only if the line is there */
                if (gc->lines[j].STC_type)
                        flush_STC(gc, gc->lines[j].tag, gc->lines[j].otag,
                                  gc->lines[j].STC_type, gc->lines[j].status);
        }
#endif

         
        d->last_used[line_num] = SIM_cycle_count(GC_CPU(gt));

#ifdef GC_DEBUG
        if (SIM_clear_exception()) {
                SIM_log_error(&gc->log, GC_Log_Repl, "generic-cache::"
                              "lru_update_replacement: "
                              "got an exception in SIM_cycle_count()");
        }
#endif
}

static int
lru_get_line(void *data, generic_cache_t *gc, generic_transaction_t *gt)
{
        lru_data_t *d = (lru_data_t *) data;
        int i;
        int lru_line = GC_INDEX(gc, gt);
        uinteger_t lru_time = (uinteger_t)-1;

        for (i = lru_line; 
             i < gc->config.line_number; i += GC_NEXT_ASSOC(gc))
                if (d->last_used[i] <= lru_time) {
                        lru_line = i;
                        lru_time = d->last_used[i];
                }
        
        SIM_log_info(3, &gc->log, GC_Log_Repl,
                     "get_line::lru: got line %d", lru_line);
        return lru_line;
}

static void *
lru_new_instance(generic_cache_t *gc)
{
        lru_data_t *d;

        d = MM_ZALLOC(1, lru_data_t);
        d->last_used = MM_ZALLOC(gc->config.line_number, integer_t);
        return d;
}

static void
lru_update_config(void *data, generic_cache_t *gc)
{
        lru_data_t *d = (lru_data_t *) data;

        MM_FREE(d->last_used);
        d->last_used = MM_ZALLOC(gc->config.line_number, integer_t);
}

static void
lru_set_timestamp(void *data, generic_cache_t *gc,
                  int line_num, integer_t timestamp)
{
        lru_data_t *d = (lru_data_t *) data;
        d->last_used[line_num] = timestamp;
}

static integer_t
lru_get_timestamp(void *data, generic_cache_t *gc,
                  int line_num)
{
        lru_data_t *d = (lru_data_t *) data;
        return d->last_used[line_num];
}


static set_error_t                                              
set_lines_last_used(void *dont_care, conf_object_t *obj,       
                    attr_value_t *val, attr_value_t *idx)      
{                                                               
        generic_cache_t *gc = (generic_cache_t *) obj;          

        if (strcmp(gc->config.repl_fun.get_name(), lru_get_name()) == 0) {
                lru_data_t *d = (lru_data_t *) gc->config.repl_data;
                int i;

                if (!idx || idx->kind != Sim_Val_Integer) {

                        if (val->u.list.size != gc->config.line_number) {
                                SIM_log_error(
                                        &gc->log, GC_Log_Attr,
                                        "generic-cache::set_lines: "
                                        "this has cache doesn't have the "
                                        "right number of lines for loading "
                                        "the lines.");
                                return Sim_Set_Illegal_Value;
                        }

                        for (i=0; i<gc->config.line_number; i++)
                                d->last_used[i] = 
                                        val->u.list.vector[i].u.integer;
                }
                else {
                        d->last_used[idx->u.integer] = 
                                val->u.list.vector[idx->u.integer].u.integer;
                }

                return Sim_Set_Ok;                   
        }
        else {
                SIM_log_info(4, &gc->log, GC_Log_Repl,
                             "LRU replacement policy is not in use.");
                return Sim_Set_Illegal_Value;
        }
}

static attr_value_t                                         
get_lines_last_used(void *dont_care, conf_object_t *obj,       
                    attr_value_t *idx)                    
{                                                          
        generic_cache_t *gc = (generic_cache_t *) obj;     
        attr_value_t ret;                                  

        if (strcmp(gc->config.repl_fun.get_name(), lru_get_name()) == 0) {
                lru_data_t *d = (lru_data_t *) gc->config.repl_data;
                int i;

                if (!idx || idx->kind != Sim_Val_Integer) {

                        ret.kind = Sim_Val_List;
                        ret.u.list.size = gc->config.line_number;
                        ret.u.list.vector = MM_MALLOC(gc->config.line_number,
                                                      attr_value_t);

                        for (i=0; i<gc->config.line_number; i++) {

                                ret.u.list.vector[i].kind = Sim_Val_Integer;
                                ret.u.list.vector[i].u.integer = 
                                        d->last_used[i];
                        }
                }
                else {
                        /* just one element */
                        ret.kind = Sim_Val_Integer;
                        ret.u.integer = d->last_used[idx->u.integer];
                }
        }
        else {
                SIM_log_info(4, &gc->log, GC_Log_Repl,
                             "LRU replacement policy is not in use.");
                ret.kind = Sim_Val_Invalid;
        }

        return ret;                             
}



repl_interface_t *
init_lru_repl(conf_class_t *gc_class)
{
        repl_interface_t *lru_i;

        lru_i = MM_ZALLOC(1, repl_interface_t);

        /* config_seed */
        SIM_register_typed_attribute(
                gc_class, "lines_last_used",
                get_lines_last_used, 0,
                set_lines_last_used, 0,
                Sim_Attr_Optional | Sim_Attr_Integer_Indexed | Sim_Init_Phase_1,
                "[i*]", "i",
                "Last used timestamp for the cache lines");
        
        lru_i->new_instance = lru_new_instance;
        lru_i->update_config = lru_update_config;
        lru_i->get_name = lru_get_name;
        lru_i->update_repl = lru_update_repl;
        lru_i->get_line = lru_get_line;
        lru_i->set_timestamp = lru_set_timestamp;
        lru_i->get_timestamp = lru_get_timestamp;
        
        return lru_i;
}
