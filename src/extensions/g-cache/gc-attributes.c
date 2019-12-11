/*
  gc-attributes.c - g-cache specific attributes

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

#ifndef HOOK_DEFAULT_REPL_POLICY
#define HOOK_DEFAULT_REPL_POLICY "random"
#endif

/* hap callback for DSTC hit count */
static void
dstc_hit_count_callback(void *data, conf_object_t *cpu, uint64 type, 
                        uint64 va, uint64 pa, uint64 cnt)
{
        generic_cache_t *gc = (generic_cache_t *) data;

        if (type == Sim_RW_Read && gc->config.direct_read_listener) {
                /* first level cache, read */
#ifdef GC_DEBUG
                pr("[%-3s] [0x%016llx, 0x%016llx, %lld] total += %lld\n", 
                   gc->log.obj.name, va, pa, type, cnt);
#endif
                gc->stat.transaction += cnt;
                gc->stat.data_read += cnt;
        }
        else if (type == Sim_RW_Write && gc->config.direct_write_listener) {
                
                /* if the line is in the cache, we're counting hits, otherwise
                   misses (in a NWA cache for example) */
                generic_transaction_t mop;
                int ln;
                mop.logical_address = va;
                mop.physical_address = pa;
                ln = lookup_line(gc, &mop);
                
                /* we're an allocating cache and we match the line */
                if (gc->config.write_allocate && ln != -1) {
                        
                        /* If STC_type is set, it means we set this in
                           the STC, so we should count it as hit 
                           If not, it means we were getting this transaction 
                           through a cache transaction so we don't care about 
                           the DSTC flushing. */
                        if (gc->lines[ln].STC_type) {
#ifdef GC_DEBUG
                                pr("[%-3s] [0x%016llx, 0x%016llx, %lld] "
                                   "total += %lld\n", 
                                   gc->log.obj.name, va, pa, type, cnt);
#endif
                                gc->stat.data_write += cnt;
                                gc->stat.transaction += cnt;
                        }
                }
                /* we're a non-allocating cache */
                else if (!gc->config.write_allocate) {
                        
                        /* we don't have the line in cache, so we count it
                           as a miss */
                        if (ln == -1) {
#ifdef GC_DEBUG
                                pr("[%-3s] [0x%016llx, 0x%016llx, %lld] "
                                   "miss  += %lld\n", 
                                   gc->log.obj.name, va, pa, type, cnt);
#endif
                                gc->stat.data_write_miss += cnt;
                                gc->stat.data_write += cnt;
                                gc->stat.transaction += cnt;

                                /* update profilers too, but not the PC based
                                   profiler since it shouldn't have allowed a
                                   miss to be cached in the STC--it would get
                                   no PC to use when the line is flushed */
                                if (gc->prof[V_DWM].id)
                                        prof_data_add(gc->prof[V_DWM].id,
                                                      va, cnt);

                                if (gc->prof[P_DWM].id)
                                        prof_data_add(gc->prof[P_DWM].id, 
                                                      pa, cnt);
                        }
                        else if (gc->lines[ln].STC_type) {
#ifdef GC_DEBUG
                                pr("[%-3s] [0x%016llx, 0x%016llx, %lld] "
                                   "total += %lld\n", 
                                   gc->log.obj.name, va, pa, type, cnt);
#endif
                                gc->stat.data_write += cnt;
                                gc->stat.transaction += cnt;
                        }
                        /* else we didn't handle this line via DSTC so there's
                           no need to count */
                }
        }
}

/* attribute manipulation functions */
void
update_precomputed_values(generic_cache_t *gc)
{
        int i;

        gc->config.no_STC =
                (gc->penalty.read > 0)
                || (gc->penalty.write > 0)
                || (gc->config.block_STC);
        
        /* remove the STC callbacks */
        SIM_hap_delete_callback(
                "Core_DSTC_Flush_Counter",
                (obj_hap_func_t) dstc_hit_count_callback,
                gc);
        SIM_clear_exception();

        if (!gc->config.no_STC) {
                /* add a callback for each cpu */
                for (i=0; i<gc->cpus_count; i++)
                        SIM_hap_add_callback_obj(
                                "Core_DSTC_Flush_Counter", 
                                gc->cpus[i],
                                0,
                                (obj_hap_func_t) dstc_hit_count_callback,
                                gc);
        }

        gc->config.line_size_ln2 = ln2(gc->config.line_size);
        gc->config.next_assoc = (gc->config.assoc) > 0 
                ? gc->config.line_number / gc->config.assoc : -1;
                
        gc->config.tag_mask = ~(gc->config.line_size - 1);
        gc->config.index_mask = gc->config.next_assoc - 1;

        /* don't call if repl_data is not allocated yet */
        if (gc->config.repl_data)
                gc->config.repl_fun.update_config(gc->config.repl_data, gc);
}

/* config_block_STC */
GC_INT_ATTR_UPDATE_SET(config, block_STC)
GC_INT_ATTR_GET(config, block_STC)

/* penalty_read_next */
GC_INT_ATTR_SET(penalty, read_next)
GC_INT_ATTR_GET(penalty, read_next)

/* penalty_write_next */
GC_INT_ATTR_SET(penalty, write_next)
GC_INT_ATTR_GET(penalty, write_next)

/* stat_mesi_exclusive_to_shared */
GC_INT_ATTR_SET(stat, mesi_exclusive_to_shared)
GC_INT_ATTR_GET(stat, mesi_exclusive_to_shared)

/* stat_mesi_modified_to_shared */
GC_INT_ATTR_SET(stat, mesi_modified_to_shared)
GC_INT_ATTR_GET(stat, mesi_modified_to_shared)

/* stat_mesi_invalidate */
GC_INT_ATTR_SET(stat, mesi_invalidate)
GC_INT_ATTR_GET(stat, mesi_invalidate)

/* stat_lost_stall_cycles */
GC_INT_ATTR_SET(stat, lost_stall_cycles)
GC_INT_ATTR_GET(stat, lost_stall_cycles)


/* called from set_lines only */
static set_error_t
set_single_line(generic_cache_t *gc, cache_line_t *cl, attr_value_t *line)
{
        if (line->u.list.vector[0].u.integer < 0 ||
            line->u.list.vector[0].u.integer > 3) {
                SIM_log_error(&gc->log, GC_Log_Attr,
                              "Line %lld status is incorrect",
                              line->u.list.vector[0].u.integer);
                return Sim_Set_Illegal_Value;
        }

        if (line->u.list.vector[3].u.integer < 0 ||
            line->u.list.vector[3].u.integer > 3) {
                SIM_log_error(&gc->log, GC_Log_Attr,
                              "Line %lld STC_type is incorrect",
                              line->u.list.vector[3].u.integer);
                return Sim_Set_Illegal_Value;
        }

        cl->status    = line->u.list.vector[0].u.integer;
        cl->tag       = line->u.list.vector[1].u.integer;
        cl->otag      = line->u.list.vector[2].u.integer;
        cl->STC_type  = line->u.list.vector[3].u.integer;

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
                        line->u.list.size = 4;
                        line->u.list.vector =
                                MM_MALLOC(4, attr_value_t);

                        line->u.list.vector[0].kind = Sim_Val_Integer;
                        line->u.list.vector[0].u.integer = cl->status;

                        line->u.list.vector[1].kind = Sim_Val_Integer;
                        line->u.list.vector[1].u.integer = cl->tag;

                        line->u.list.vector[2].kind = Sim_Val_Integer;
                        line->u.list.vector[2].u.integer = cl->otag;

                        line->u.list.vector[3].kind = Sim_Val_Integer;
                        line->u.list.vector[3].u.integer = cl->STC_type;
                }
        }
        else {
                /* just one element */
                cl = &gc->lines[idx->u.integer];

                ret.kind = Sim_Val_List;
                ret.u.list.size = 4;
                ret.u.list.vector =
                        MM_MALLOC(4, attr_value_t);

                ret.u.list.vector[0].kind = Sim_Val_Integer;
                ret.u.list.vector[0].u.integer = cl->status;

                ret.u.list.vector[1].kind = Sim_Val_Integer;
                ret.u.list.vector[1].u.integer = cl->tag;

                ret.u.list.vector[2].kind = Sim_Val_Integer;
                ret.u.list.vector[2].u.integer = cl->otag;

                ret.u.list.vector[3].kind = Sim_Val_Integer;
                ret.u.list.vector[3].u.integer = cl->STC_type;
        }

        return ret;
}

/* snoopers */
static set_error_t
set_snoopers(void *dont_care, conf_object_t *obj,
             attr_value_t *val, attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;
        attr_value_t *sn;
        int i;

        MM_FREE(gc->snoopers);
        MM_FREE(gc->snoopers_ifc);

        gc->snoopers = MM_MALLOC(val->u.list.size, conf_object_t *);
        gc->snoopers_ifc = MM_MALLOC(val->u.list.size,
                                     mesi_listen_interface_t *);
        gc->snoopers_size = val->u.list.size;

        for (i=0; i<val->u.list.size; i++) {

                sn = &val->u.list.vector[i];

                gc->snoopers_ifc[i] = SIM_get_interface(sn->u.object,
                                                        MESI_LISTEN_INTERFACE);
                if (SIM_clear_exception()) {
                        SIM_log_error(&gc->log, GC_Log_Attr,
                                      "set_snoopers: "
                                      "object %d does not provide the mesi "
                                      "listen interface.", i);
                        gc->snoopers_size = 0;
                        MM_FREE(gc->snoopers);
                        MM_FREE(gc->snoopers_ifc);
                        gc->snoopers = NULL;
                        gc->snoopers_ifc = NULL;
                        return Sim_Set_Interface_Not_Found;
                }

                gc->snoopers[i] = sn->u.object;
        }

        /* enable MESI */
        if (gc->snoopers_size > 0)
                gc->config.mesi = 1;
        else
                gc->config.mesi = 0;

        return Sim_Set_Ok;
}

static attr_value_t
get_snoopers(void *dont_care, conf_object_t *obj,
                 attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;
        attr_value_t ret;
        int i;

        if (gc->snoopers) {

                ret.kind = Sim_Val_List;
                ret.u.list.vector = MM_MALLOC(gc->snoopers_size, attr_value_t);
                ret.u.list.size = gc->snoopers_size;

                for (i=0; i<gc->snoopers_size; i++) {
                        ret.u.list.vector[i].kind = Sim_Val_Object;
                        ret.u.list.vector[i].u.object = gc->snoopers[i];
                }
        }
        else {
                ret.kind = Sim_Val_Nil;
        }

        return ret;
}

/* higher_level_caches */
static set_error_t
set_hlc(void *dont_care, conf_object_t *obj,
        attr_value_t *val, attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;
        attr_value_t *sn;
        int i;

        MM_FREE(gc->hlc);
        MM_FREE(gc->hlc_ifc);

        gc->hlc = MM_MALLOC(val->u.list.size, conf_object_t *);
        gc->hlc_ifc = MM_MALLOC(val->u.list.size,
                                mesi_listen_interface_t *);
        gc->hlc_size = val->u.list.size;

        for (i=0; i<val->u.list.size; i++) {

                sn = &val->u.list.vector[i];

                gc->hlc_ifc[i] = SIM_get_interface(sn->u.object,
                                                   MESI_LISTEN_INTERFACE);
                if (SIM_clear_exception()) {
                        SIM_log_error(&gc->log, GC_Log_Attr,
                                      "set_hlc: "
                                      "object %d does not provide the mesi "
                                      "listen interface.", i);
                        gc->hlc_size = 0;
                        MM_FREE(gc->hlc);
                        MM_FREE(gc->hlc_ifc);
                        gc->hlc = NULL;
                        gc->hlc_ifc = NULL;
                        return Sim_Set_Interface_Not_Found;
                }

                gc->hlc[i] = sn->u.object;
        }

        return Sim_Set_Ok;
}

static attr_value_t
get_hlc(void *dont_care, conf_object_t *obj,
                 attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;
        attr_value_t ret;
        int i;

        if (gc->hlc) {

                ret.kind = Sim_Val_List;
                ret.u.list.vector = MM_MALLOC(gc->hlc_size, attr_value_t);
                ret.u.list.size = gc->hlc_size;

                for (i=0; i<gc->hlc_size; i++) {
                        ret.u.list.vector[i].kind = Sim_Val_Object;
                        ret.u.list.vector[i].u.object = gc->hlc[i];
                }
        }
        else {
                ret.kind = Sim_Val_Nil;
        }

        return ret;
}


static mesi_listen_interface_t mesi_ifc;

/* registering attributes */
void
gc_register(conf_class_t *gc_class)
{
        mesi_ifc.snoop_transaction = mesi_snoop_transaction_export;
        SIM_register_interface(gc_class, MESI_LISTEN_INTERFACE,
                               (void *) &mesi_ifc);

        SIM_register_typed_attribute(
                gc_class, "config_block_STC",
                get_config_block_STC, 0,
                set_config_block_STC, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Prevent the cache from using the STCs. Read the "
                "'Cache Simulation' chapter in Simics User Guide for more "
                "information"
                "(0: STC usage allowed, 1: STC usage blocked; default is 0).");

        SIM_register_typed_attribute(
                gc_class, "penalty_read_next",
                get_penalty_read_next, 0,
                set_penalty_read_next, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Stall penalty (in cycles) for a read transaction issued by "
                "the cache to "
                "the next level cache. A cache miss on read will have "
                "a penalty for 'read' (incoming transaction) + 'read-next' "
                "(line fetch transaction) + any penalty set by the next "
                "caches. (default is 0)");

        SIM_register_typed_attribute(
                gc_class, "penalty_write_next",
                get_penalty_write_next, 0,
                set_penalty_write_next, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Stall penalty (in cycles) for a write transactions issued by"
                " the cache to the next level cache. In a write-back cache, a "
                "cache miss on read "
                "triggering a copy-back transaction will have a penalty for "
                "'read', 'write-next' (copy-back transaction) and 'read-next' "
                "(line fetch transaction). In write-through cache, a "
                "write transaction will always have at least a penalty for "
                "'write' and 'write-next' (write-through transaction). "
                "(default is 0).");

        SIM_register_typed_attribute(
                gc_class, "lines",
                get_lines, 0,
                set_lines, 0,
                Sim_Attr_Optional | Sim_Init_Phase_1 | Sim_Attr_Integer_Indexed,
                "[[iiii]*]", "[iiii]",
                "Content of the cache lines");

        SIM_register_typed_attribute(
                gc_class, "snoopers",
                get_snoopers, 0,
                set_snoopers, 0,
                Sim_Attr_Optional,
                "[o*]", NULL,
                "Caches listening on the bus (MESI protocol).");

        SIM_register_typed_attribute(
                gc_class, "higher_level_caches",
                get_hlc, 0,
                set_hlc, 0,
                Sim_Attr_Optional,
                "[o*]", NULL,
                "Higher level caches that need to receive invalidates during "
                "MESI snooping (MESI protocol).");

        SIM_register_typed_attribute(
                gc_class, "stat_mesi_exclusive_to_shared",
                get_stat_mesi_exclusive_to_shared, 0,
                set_stat_mesi_exclusive_to_shared, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Number of Exclusive to Shared transitions in MESI protocol.");

        SIM_register_typed_attribute(
                gc_class, "stat_mesi_modified_to_shared",
                get_stat_mesi_modified_to_shared, 0,
                set_stat_mesi_modified_to_shared, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Number of Modified to Shared transitions in MESI protocol.");

        SIM_register_typed_attribute(
                gc_class, "stat_mesi_invalidate",
                get_stat_mesi_invalidate, 0,
                set_stat_mesi_invalidate, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Number of lines invalidated in MESI protocol.");

        SIM_register_typed_attribute(
                gc_class, "stat_lost_stall_cycles",
                get_stat_lost_stall_cycles, 0,
                set_stat_lost_stall_cycles, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Stall cycles lost due to non-stallable transactions.");
}

void
gc_init_cache(generic_cache_t *gc)
{
        /* Set block_STC to 0 since the cache will behave properly in most
           cases. */
        gc->config.block_STC = 0;

        gc->config.line_size = 32;
        gc->config.assoc = 4;
        
        gc_set_config_repl(gc, HOOK_DEFAULT_REPL_POLICY);
        gc_set_config_line_number(gc, 128);
}
