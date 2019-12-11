/*
  gc-lru2-repl.c

  Copyright 1993-2007 Virtutech AB
  
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

#include "gc-lru2-repl.h"

static const char *
lru2_get_name(void)
{
        return "lru2";
}

static void
lru2_update_repl(void *data, generic_cache_t *gc, generic_transaction_t *gt, int line_num)
{
        int i;
        lru2_data_t *d = (lru2_data_t *)data;
        int index = GC_INDEX(gc, gt);
        uinteger_t *state_transitions = 
                &d->state_transitions[d->states[line_num] * gc->config.assoc];

        for (i = 0; i < gc->config.assoc; i++) {
                uinteger_t *states = 
                        &d->states[index + i * gc->config.next_assoc];
                if (*states >= gc->config.assoc) {
                        SIM_log_error(&gc->log, GC_Log_Repl,
                                      "Illegal line LRU2 state, setting it "
                                      "to least recently used.");
                        *states = gc->config.assoc - 1;
                }
                else {
                        if (*states == 0)
                                flush_STC(gc, 
                                          gc->lines[i].tag, 
                                          gc->lines[i].otag,
                                          gc->lines[i].STC_type, 
                                          gc->lines[i].status);
                        *states = state_transitions[*states];
                }
        }
        d->states[line_num] = 0;
}

static int
lru2_get_line(void *data, generic_cache_t *gc, generic_transaction_t *gt)
{
        int i;
        lru2_data_t *d = (lru2_data_t *)data;
        int line_num = GC_INDEX(gc, gt);
        uinteger_t lru_state = 0;

        for (i = GC_INDEX(gc, gt); i < gc->config.line_number; i += GC_NEXT_ASSOC(gc))
                if (d->states[i] >= lru_state) {
                        line_num = i;
                        lru_state = d->states[i];
                }

        SIM_log_info(3, &gc->log, GC_Log_Repl,
                     "get_line::lru2: got line %d", line_num);
        return line_num;
}

static void lru2_update_config(void *data, generic_cache_t *gc);

static void *
lru2_new_instance(generic_cache_t *gc)
{
        lru2_data_t *d;

        d = MM_MALLOC(1, lru2_data_t);
        d->states = NULL;
        d->state_transitions = NULL;
        lru2_update_config(d, gc);
        return d;
}

static void
lru2_update_config(void *data, generic_cache_t *gc)
{
        int i;
        lru2_data_t *d = (lru2_data_t *) data;

        /* Initialize the LRU states. */
        d->states = MM_REALLOC(d->states, gc->config.line_number, uinteger_t);

        for (i = 0; i < gc->config.assoc; i++) {
                int j;
                for (j = i * gc->config.next_assoc; j < (i + 1) * gc->config.next_assoc; j++)
                        d->states[j] = i;
        }

        /* Initialize the state transition table. */
        d->state_transitions = MM_REALLOC(d->state_transitions, gc->config.assoc * gc->config.assoc, uinteger_t);

        for (i = 0; i < gc->config.assoc; i++) {
                int j;
                for (j = 0; j < gc->config.assoc; j++)
                        d->state_transitions[i * gc->config.assoc + j] = j < i ? j + 1 : j;
        }
}

static set_error_t
set_lines_states(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;

        if (strcmp(gc->config.repl_fun.get_name(), lru2_get_name()) == 0) {
                lru2_data_t *d = (lru2_data_t *) gc->config.repl_data;

                if (!idx || idx->kind != Sim_Val_Integer) {
                        int i;

                        if (val->u.list.size != gc->config.line_number) {
                                SIM_log_error(&gc->log, GC_Log_Repl, 
                                              "Cache line number mismatch "
                                              "when setting LRU states.");
                                return Sim_Set_Illegal_Value;
                        }

                        for (i = 0; i < gc->config.line_number; i++)
                                d->states[i] = val->u.list.vector[i].u.integer;
                }
                else
                        d->states[idx->u.integer] = val->u.list.vector[idx->u.integer].u.integer;

                return Sim_Set_Ok;
        }
        else {
                SIM_log_info(4, &gc->log, GC_Log_Repl,
                             "LRU2 replacement policy is not in use.");
                return Sim_Set_Illegal_Value;
        }
}

static attr_value_t
get_lines_states(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        generic_cache_t *gc = (generic_cache_t *) obj;
        attr_value_t ret;

        if (strcmp(gc->config.repl_fun.get_name(), lru2_get_name()) == 0) {
                lru2_data_t *d = (lru2_data_t *) gc->config.repl_data;

                if (!idx || idx->kind != Sim_Val_Integer) {
                        int i;

                        ret.kind = Sim_Val_List;
                        ret.u.list.size = gc->config.line_number;
                        ret.u.list.vector = MM_MALLOC(gc->config.line_number, attr_value_t);

                        for (i = 0; i < gc->config.line_number; i++) {
                                ret.u.list.vector[i].kind = Sim_Val_Integer;
                                ret.u.list.vector[i].u.integer = d->states[i];
                        }
                }
                else {
                        ret.kind = Sim_Val_Integer;
                        ret.u.integer = d->states[idx->u.integer];
                }
        }
        else {
                SIM_log_info(4, &gc->log, GC_Log_Repl,
                             "LRU2 replacement policy is not in use.");
                ret.kind = Sim_Val_Invalid;
        }

        return ret;
}



repl_interface_t *
init_lru2_repl(conf_class_t *gc_class)
{
        repl_interface_t *lru2_i = MM_ZALLOC(1, repl_interface_t);

        SIM_register_typed_attribute(
                gc_class, "lines_states",
                get_lines_states, 0,
                set_lines_states, 0,
                Sim_Attr_Optional | Sim_Attr_Integer_Indexed | Sim_Init_Phase_1,
                "[i*]", "i",
                "LRU states of the cache lines.");

        lru2_i->new_instance = lru2_new_instance;
        lru2_i->update_config = lru2_update_config;
        lru2_i->get_name = lru2_get_name;
        lru2_i->update_repl = lru2_update_repl;
        lru2_i->get_line = lru2_get_line;

        return lru2_i;
}
