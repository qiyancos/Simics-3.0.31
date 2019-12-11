/*
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
 * This class implements a simple staller. If a transactions is
 * stallable, it will return a fixed stall time. It can be used for a
 * simple memory simulation at the end of a cache hierarchy.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

typedef struct simple_staller {
        log_object_t log;
        int stall_time;
} simple_staller_t;

conf_object_t *
st_new_instance(parse_object_t *pa)
{
        simple_staller_t *st = MM_ZALLOC(1, simple_staller_t);
        SIM_log_constructor(&st->log, pa);
        return (conf_object_t *) st;
}


cycles_t
st_operate(conf_object_t *mem_hier, conf_object_t *space, 
           map_list_t *map, generic_transaction_t *mem_op)
{
        simple_staller_t *st = (simple_staller_t *) mem_hier;
        
        mem_op->reissue = 0;
        mem_op->block_STC = 1;
        if (mem_op->may_stall) {
//                printf("Stalling\n");
                return st->stall_time;
        } else
                return 0;
}

/* cpu  */
static set_error_t
set_stall_time(void *dont_care, conf_object_t *obj,
               attr_value_t *val, attr_value_t *idx)
{
        simple_staller_t *st = (simple_staller_t *) obj;
        
        st->stall_time = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t                                             
get_stall_time(void *dont_care, conf_object_t *obj,       
               attr_value_t *idx)                         
{                                                               
        simple_staller_t *st = (simple_staller_t *) obj;          
        attr_value_t ret;                                       

        ret.kind = Sim_Val_Integer;
        ret.u.integer = st->stall_time;

        return ret;
}

static void
st_register(conf_class_t *st_class)
{
        SIM_register_typed_attribute(
                st_class, "stall_time",
                get_stall_time, 0,
                set_stall_time, 0,
                Sim_Attr_Optional,
                "i", NULL,
                "Stall time returned when accessed");
}

/*
  Information for class registering
*/
static conf_class_t *st_class;
static class_data_t st_data;
static timing_model_interface_t st_ifc;

DLL_EXPORT void
init_local(void)
{
        st_data.new_instance = st_new_instance;
        st_data.parent = SIM_get_class("log-object");
        st_data.description =
                "This class implements a simple transaction staller. If a"
                " transactions is stallable, it will return a fixed stall"
                " time. It can be used for a simple memory simulation at the"
                " end of a cache hierarchy.";
                
        if (!(st_class = SIM_register_class("trans-staller",
                                            &st_data))) {
                pr_err("Could not create trans-staller class\n");
                return;
        }

        /* register the attributes */
        st_register(st_class);

        /* register the timing model interface */
        st_ifc.operate = st_operate;
        SIM_register_interface(st_class, "timing-model",
                               (void *) &st_ifc);
}
