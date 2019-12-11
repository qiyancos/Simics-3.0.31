/*
  gc-attributes.c - g-cache-ooo specific attributes

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

/* attribute manipulation functions */
void
update_precomputed_values(generic_cache_t *gc)
{
        gc->config.line_size_ln2 = ln2(gc->config.line_size);
        if (gc->config.assoc) {
                gc->config.next_assoc = 
                        gc->config.line_number / gc->config.assoc;
                gc->config.index_mask = 
                        (gc->config.line_number / gc->config.assoc) - 1;
        }
        gc->config.tag_mask = ~(gc->config.line_size - 1);
}

/* config_read_per_cycle */
GC_INT_ATTR_SET(config, read_per_cycle)
GC_INT_ATTR_GET(config, read_per_cycle)

/* config_write_per_cycle */
GC_INT_ATTR_SET(config, write_per_cycle)
GC_INT_ATTR_GET(config, write_per_cycle)

/* config_max_out_trans */
static set_error_t
set_config_max_out_trans(void *dont_care, conf_object_t *obj,
                         attr_value_t *val, attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;
        int i;

        gc->config.max_out_trans = val->u.integer;

        /* re-allocate the lines */
        if (gc->outstanding_trans)
                MM_FREE(gc->outstanding_trans);
        gc->outstanding_trans = MM_ZALLOC(gc->config.max_out_trans, 
                                          trans_line_t);

        for (i=0; i<gc->config.max_out_trans; i++) {
                gc->outstanding_trans[i].id = -1;
                gc->outstanding_trans[i].line = -1;
        }

        return Sim_Set_Ok;
}

GC_INT_ATTR_GET(config, max_out_trans)

/* config_accept_not_stall */
GC_INT_ATTR_SET(config, accept_not_stall)
GC_INT_ATTR_GET(config, accept_not_stall)

/* called from set_lines only */
static set_error_t
set_single_line(generic_cache_t *gc, cache_line_t *cl, attr_value_t *line)
{
        if (line->u.list.vector[0].u.integer < 0 ||
            line->u.list.vector[0].u.integer > 3) {
                SIM_log_error(&gc->log, GC_Log_Attr,
                              "Line status is incorrect");
                return Sim_Set_Illegal_Value;
        }

        if (line->u.list.vector[3].u.integer < 0 ||
            line->u.list.vector[3].u.integer > 3) {
                SIM_log_error(&gc->log, GC_Log_Attr,
                              "Line busy.status is incorrect");
                return Sim_Set_Illegal_Value;
        }
                     
        cl->status          = line->u.list.vector[0].u.integer;
        cl->tag             = line->u.list.vector[1].u.integer;
        cl->otag            = line->u.list.vector[2].u.integer;
        cl->busy.status     = line->u.list.vector[3].u.integer;
        cl->busy.start_time = line->u.list.vector[4].u.integer;
        cl->busy.busy_time  = line->u.list.vector[5].u.integer;
        cl->busy.id         = line->u.list.vector[6].u.integer;
        cl->busy.next_id    = line->u.list.vector[7].u.integer;
        
        return Sim_Set_Ok;
}

/* lines */
static set_error_t
set_lines(void *dont_care, conf_object_t *obj,
          attr_value_t *val, attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;
        set_error_t diag;
        int i;

        if (!gc->lines) {
                SIM_log_error(&gc->log, GC_Log_Attr,
                              "generic-cache::set_lines: "
                              "lines is a NULL pointer");
                return Sim_Set_Illegal_Value;
        }

        if (!idx || idx->kind != Sim_Val_Integer) {

                if (val->u.list.size != gc->config.line_number) {
                        SIM_log_error(&gc->log, GC_Log_Attr,
                                      "generic-cache::set_lines: "
                                      "this has cache doesn't have the right "
                                      "number of lines for loading the lines.");
                        return Sim_Set_Illegal_Value;
                }
                
                for (i=0; i<gc->config.line_number; i++) {
                        
                        diag = set_single_line(gc,
                                               &gc->lines[i], 
                                               &val->u.list.vector[i]);
                        if (diag != Sim_Set_Ok)
                                return diag;
                }
        }
        else {
                return set_single_line(gc, &gc->lines[idx->u.integer], val);
        }
        
        return Sim_Set_Ok;
}

static attr_value_t
get_lines(void *dont_care, conf_object_t *obj,       
          attr_value_t *idx)                         
{                                                               
        generic_cache_t *gc = (generic_cache_t *) obj;          
        attr_value_t ret;
        attr_value_t *line;
        cache_line_t *cl;
        int i;

        if (!gc->lines) {
                SIM_log_error(&gc->log, GC_Log_Attr,
                              "generic-cache::get_lines: "
                              "lines is a NULL pointer");
                ret.kind = Sim_Val_Invalid;
                return ret;
        }

        if (!idx || idx->kind != Sim_Val_Integer) {

                ret.kind = Sim_Val_List;
                ret.u.list.size = gc->config.line_number;
                ret.u.list.vector = MM_MALLOC(gc->config.line_number, 
                                              attr_value_t);

                for (i=0; i<gc->config.line_number; i++) {

                        line = &ret.u.list.vector[i];
                        cl = &gc->lines[i];
                        
                        line->kind = Sim_Val_List;
                        line->u.list.size = 8;
                        line->u.list.vector = 
                                MM_MALLOC(line->u.list.size, attr_value_t);

                        line->u.list.vector[0].kind = Sim_Val_Integer;
                        line->u.list.vector[0].u.integer = cl->status;
                        
                        line->u.list.vector[1].kind = Sim_Val_Integer;
                        line->u.list.vector[1].u.integer = cl->tag;

                        line->u.list.vector[2].kind = Sim_Val_Integer;
                        line->u.list.vector[2].u.integer = cl->otag;

                        line->u.list.vector[3].kind = Sim_Val_Integer;
                        line->u.list.vector[3].u.integer = cl->busy.status;

                        line->u.list.vector[4].kind = Sim_Val_Integer;
                        line->u.list.vector[4].u.integer = cl->busy.start_time;

                        line->u.list.vector[5].kind = Sim_Val_Integer;
                        line->u.list.vector[5].u.integer = cl->busy.busy_time;

                        line->u.list.vector[6].kind = Sim_Val_Integer;
                        line->u.list.vector[6].u.integer = cl->busy.id;

                        line->u.list.vector[7].kind = Sim_Val_Integer;
                        line->u.list.vector[7].u.integer = cl->busy.next_id;
                }
        }
        else {
                /* just one element */
                cl = &gc->lines[idx->u.integer];
                        
                ret.kind = Sim_Val_List;
                ret.u.list.size = 8;
                ret.u.list.vector = 
                        MM_MALLOC(ret.u.list.size, attr_value_t);

                ret.u.list.vector[0].kind = Sim_Val_Integer;
                ret.u.list.vector[0].u.integer = cl->status;
                        
                ret.u.list.vector[1].kind = Sim_Val_Integer;
                ret.u.list.vector[1].u.integer = cl->tag;

                ret.u.list.vector[2].kind = Sim_Val_Integer;
                ret.u.list.vector[2].u.integer = cl->otag;

                ret.u.list.vector[3].kind = Sim_Val_Integer;
                ret.u.list.vector[3].u.integer = cl->busy.status;

                ret.u.list.vector[4].kind = Sim_Val_Integer;
                ret.u.list.vector[4].u.integer = cl->busy.start_time;
                
                ret.u.list.vector[5].kind = Sim_Val_Integer;
                ret.u.list.vector[5].u.integer = cl->busy.busy_time;

                ret.u.list.vector[6].kind = Sim_Val_Integer;
                ret.u.list.vector[6].u.integer = cl->busy.id;

                ret.u.list.vector[7].kind = Sim_Val_Integer;
                ret.u.list.vector[7].u.integer = cl->busy.next_id;
        }
        
        return ret;
}

/* called from set_out_trans only */
static set_error_t
set_single_out_trans(generic_cache_t *gc, trans_line_t *cl, attr_value_t *trans)
{
        conf_object_t *ini_ptr;

        if (trans->u.list.vector[0].u.integer < -1 ||
            trans->u.list.vector[0].u.integer > 0xFFFF) {
                SIM_log_error(&gc->log, GC_Log_Attr,
                              "Transaction %lld id is incorrect",
                              trans->u.list.vector[0].u.integer);
                return Sim_Set_Illegal_Value;
        }

        if (strcmp(trans->u.list.vector[1].u.string, "") != 0) {
                ini_ptr = SIM_get_object(trans->u.list.vector[1].u.string);
                if (SIM_clear_exception()) {
                        SIM_log_error(&gc->log, GC_Log_Attr,
                                      "Transaction ini_ptr does not refer "
                                      "to an existing object");
                        return Sim_Set_Illegal_Value;
                }
        }
        else
                ini_ptr = NULL;
        
        cl->id         = trans->u.list.vector[0].u.integer;
        cl->ini_ptr    = ini_ptr;
        cl->line       = trans->u.list.vector[2].u.integer;
        cl->start_time = trans->u.list.vector[3].u.integer;
        cl->busy_time  = trans->u.list.vector[4].u.integer;
        
        return Sim_Set_Ok;
}

/* lines */
static set_error_t
set_out_trans(void *dont_care, conf_object_t *obj,
              attr_value_t *val, attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;
        set_error_t diag;
        int i;

        if (!idx || idx->kind != Sim_Val_Integer) {

                if (val->u.list.size != gc->config.max_out_trans) {
                        SIM_log_error(&gc->log, GC_Log_Attr,
                                  "generic-cache::set_out_trans: "
                                  "the outstanding transaction list does "
                                  "not have the same size in the cache.");
                        return Sim_Set_Illegal_Value;
                }
                
                for (i=0; i<gc->config.max_out_trans; i++) {
                        
                        diag = set_single_out_trans(gc,
                                                    &gc->outstanding_trans[i], 
                                                    &val->u.list.vector[i]);
                        if (diag != Sim_Set_Ok)
                                return diag;
                }
        }
        else {
                return set_single_out_trans(
                        gc, 
                        &gc->outstanding_trans[idx->u.integer], 
                        val);
        }
        
        return Sim_Set_Ok;
}

static attr_value_t
get_out_trans(void *dont_care, conf_object_t *obj,       
          attr_value_t *idx)                         
{                                                               
        generic_cache_t *gc = (generic_cache_t *) obj;          
        attr_value_t ret;
        attr_value_t *trans;
        trans_line_t *tl;
        int i;

        if (!idx || idx->kind != Sim_Val_Integer) {

                ret.kind = Sim_Val_List;
                ret.u.list.size = gc->config.max_out_trans;
                ret.u.list.vector = MM_MALLOC(gc->config.max_out_trans, 
                                              attr_value_t);

                for (i=0; i<gc->config.max_out_trans; i++) {

                        trans = &ret.u.list.vector[i];
                        tl = &gc->outstanding_trans[i];
                        
                        trans->kind = Sim_Val_List;
                        trans->u.list.size = 5;
                        trans->u.list.vector = 
                                MM_MALLOC(5, attr_value_t);

                        trans->u.list.vector[0].kind = Sim_Val_Integer;
                        trans->u.list.vector[0].u.integer = tl->id;
                        
                        trans->u.list.vector[1].kind = Sim_Val_String;
                        if (tl->ini_ptr)
                                trans->u.list.vector[1].u.string = 
                                        tl->ini_ptr->name;
                        else 
                                trans->u.list.vector[1].u.string = "";
                        
                        trans->u.list.vector[2].kind = Sim_Val_Integer;
                        trans->u.list.vector[2].u.integer = tl->line;

                        trans->u.list.vector[3].kind = Sim_Val_Integer;
                        trans->u.list.vector[3].u.integer = tl->start_time;

                        trans->u.list.vector[4].kind = Sim_Val_Integer;
                        trans->u.list.vector[4].u.integer = tl->busy_time;
                }
        }
        else {
                if (idx->u.integer < 0 || 
                    idx->u.integer >= gc->config.max_out_trans) {
                        ret.kind = Sim_Val_Invalid;
                        return ret;
                }

                /* just one element */
                tl = &gc->outstanding_trans[idx->u.integer];
                        
                ret.kind = Sim_Val_List;
                ret.u.list.size = 5;
                ret.u.list.vector = 
                        MM_MALLOC(5, attr_value_t);

                ret.u.list.vector[0].kind = Sim_Val_Integer;
                ret.u.list.vector[0].u.integer = tl->id;
                        
                ret.u.list.vector[1].kind = Sim_Val_String;
                if (tl->ini_ptr)
                        ret.u.list.vector[1].u.string = tl->ini_ptr->name;
                else
                        ret.u.list.vector[1].u.string = "";

                ret.u.list.vector[2].kind = Sim_Val_Integer;
                ret.u.list.vector[2].u.integer = tl->line;

                ret.u.list.vector[3].kind = Sim_Val_Integer;
                ret.u.list.vector[3].u.integer = tl->start_time;

                ret.u.list.vector[4].kind = Sim_Val_Integer;
                ret.u.list.vector[4].u.integer = tl->busy_time;
        }
        
        return ret;
}

/* registering attributes */
void
gc_register(conf_class_t *gc_class)
{
        SIM_register_typed_attribute(
                gc_class, "config_read_per_cycle",
                get_config_read_per_cycle, 0,
                set_config_read_per_cycle, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Number of read transactions allowed per cycle "
                "(default is 4).");

        SIM_register_typed_attribute(
                gc_class, "config_write_per_cycle",
                get_config_write_per_cycle, 0,
                set_config_write_per_cycle, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Number of write transactions allowed per cycle "
                "(default is 4).");

        SIM_register_typed_attribute(
                gc_class, "config_max_out_trans",
                get_config_max_out_trans, 0,
                set_config_max_out_trans, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Maximum number of outstanding transactions "
                "handled simultaneously by the cache "
                "(default is 16).");

        SIM_register_typed_attribute(
                gc_class, "config_accept_not_stall",
                get_config_accept_not_stall, 0,
                set_config_accept_not_stall, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "By default, the cache considers all non-stallable memory transactions as uncacheable. If this is set to 1, the cache will accept non-stallable cpu memory transactions as cacheable. This is useful to run a g-cache-ooo memory hierarchy with in-order Simics binaries. Note that *all* the memory hierarchy elements below the cache MUST have all stall penalties to zero for this to work properly (0: non-stallable transactions are uncacheable, 1: non-stallable transactions may be cached, default is 0).");

        SIM_register_typed_attribute(
                gc_class, "lines",
                get_lines, 0,
                set_lines, 0,
                Sim_Attr_Optional | Sim_Init_Phase_1 |
                Sim_Attr_Integer_Indexed,
                "[[i{8}]*]", "[i{8}]",
                "Content of the cache lines.");

        SIM_register_typed_attribute(
                gc_class, "outstanding_transactions",
                get_out_trans, 0,
                set_out_trans, 0,
                Sim_Attr_Optional | Sim_Init_Phase_1 |
                Sim_Attr_Integer_Indexed,
                "[[isiii]*]", "[isiii]",
                "Outstanding transactions information.");
}

void
gc_init_cache(generic_cache_t *gc)
{
        attr_value_t attr;

        /* set default values in the cache */
        gc->config.line_size = 32;
        gc->config.assoc = 4;

        attr.kind = Sim_Val_String;
        attr.u.string = "random";
        SIM_set_attribute((conf_object_t *) gc, "config-replacement-policy", 
                          &attr);

        gc->penalty.read = 2;
        gc->penalty.write = 2;
        
        attr.kind = Sim_Val_Integer;
        attr.u.integer = 128;
        SIM_set_attribute((conf_object_t *) gc, "config-line-number", &attr);

        gc->config.read_per_cycle = 4;
        gc->config.write_per_cycle = 4;

        attr.kind = Sim_Val_Integer;
        attr.u.integer = 16;
        SIM_set_attribute((conf_object_t *) gc, "config-max-out-trans", &attr);

#if defined(DEBUG_REISSUE)
        {
                int i;

                for (i=0; i<0x10000; i++) {
                        gc->reissue[i].flag = 1;
                        gc->reissue[i].cycle = -1;
                }

                for (i=0; i<0x10000; i++) {
                        gc->read_counted[i].flag = 0;
                        gc->read_counted[i].cycle = -1;
                }
        }
#endif

        update_precomputed_values(gc);
}
