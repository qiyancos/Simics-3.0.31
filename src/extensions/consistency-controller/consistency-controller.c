/*
  store_buffer.c - example of a memory consistency model

  Copyright 2001-2007 Virtutech AB
  
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
   <add id="simics generic module short">
   <name index="true">Consistency Controller</name>
   </add>

*/

/*
   <add id="consistency_controller usage">
   <name>Usage</name>
   
   Use the module by adding an object <tt>consistency_controller0</tt> to the
   configuration file:
   
<pre>
# donut-1p.conf

[...]

OBJECT consistency_controller0 TYPE consistency_controller {
       timing_model: my_mem_hier0
}

OBJECT phys_mem0 TYPE memory-space {
       timing_model: consistency_controller0
       [...]
}

[...]
</pre>
   </add> 

*/

#include <errno.h>
#include <stdio.h>
#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>
#include <simics/arch/sparc.h>

/* struct for the consistency_controller-class */
typedef struct {
        log_object_t obj;
        timing_model_interface_t *timing_interface;
	timing_model_interface_t *next_level_timing_interface;
        conf_object_t *next_level_object;
        int load_load;
        int load_store;
        int store_load;
        int store_store;
        int prefetch;
} consistency_controller_object_t;

timing_model_interface_t *consistency_controller_timing_interface;

conf_object_t *consistency_controller_new_instance(parse_object_t *pa)
{
        consistency_controller_object_t *obj = MM_ZALLOC(1, consistency_controller_object_t);
        SIM_log_constructor((log_object_t *)obj, pa);
        obj->timing_interface = consistency_controller_timing_interface;
        
        obj->load_load = 0;
        obj->load_store = 0;
        obj->store_load = 0;
        obj->store_store = 0;

        return (conf_object_t *)obj;
}

cycles_t
consistency_controller_operate(conf_object_t *obj, conf_object_t *space, map_list_t *map,
                               generic_transaction_t *mem_op)
{
        instruction_id_t current, ii;
        instr_type_t type;
        log_object_t *log = (log_object_t *)obj;
        conf_object_t *cpu = mem_op->ini_ptr;
        instruction_phase_t phase;
        consistency_controller_object_t *cc = (consistency_controller_object_t *)obj;
        
        if (!SIM_mem_op_is_from_cpu(mem_op) || SIM_mem_op_is_instruction(mem_op)) {
                if (cc->next_level_timing_interface) {
                        return cc->next_level_timing_interface->operate(cc->next_level_object, space, map, mem_op);
                } else {
                        return 0;
                }
        }

        if (SIM_instruction_nth_id(cpu, 0)) {
                if (!(current = SIM_instruction_id_from_mem_op_id(cpu, mem_op->id))) {
                        /* No entry -> dangling transaction - pass on */
                        SIM_log_info(3, log, 0, "Passing dangling transaction on (id = %d)", 
                                     mem_op->id);
                        return cc->next_level_timing_interface->operate(cc->next_level_object, 
                                                                        space, map, mem_op);                        
                }
                    
                if (SIM_instruction_type(current) & It_Load) {
                        for(ii = SIM_instruction_parent(current); ii; ii = SIM_instruction_parent(ii)) {
                                type = SIM_instruction_type(ii);
                                phase = SIM_instruction_phase(ii);
                                
                                /* if the instruction is retired, skip */
                                if (phase >= Sim_Phase_Retired)
                                        continue;
                                
                                if (((type & It_Store) && cc->store_load && phase < Sim_Phase_Retired) ||
                                    ((type & It_Load)  && cc->load_load  && phase < Sim_Phase_Executed)) {
                                        
                                        if (!mem_op->may_stall)
                                                ASSERT_MSG(0,"Must stall but can not.");

                                        SIM_log_info(2, log, 0, 
                                                     "Obeying %s#load consistency @ %lld for %s",
                                                     (type & It_Store) ? "store":"load",
                                                     SIM_cycle_count(cpu), cpu->name);
                                        goto stall;
                                }
                        }
                } 

                if (SIM_instruction_type(current) & It_Store) {
                        for(ii = SIM_instruction_parent(current); ii; ii = SIM_instruction_parent(ii)) {
                                type = SIM_instruction_type(ii);
                                phase = SIM_instruction_phase(ii);
                                
                                /* if the instruction is executed, skip */
                                if (phase >= Sim_Phase_Retired)
                                        continue;
                                
                                if (((type & It_Load)  && cc->load_store  && phase < Sim_Phase_Executed) ||
                                    ((type & It_Store) && cc->store_store && phase < Sim_Phase_Retired)) {
                                        
                                        if (!mem_op->may_stall)
                                                ASSERT_MSG(0,"Must stall but can not.");

                                        SIM_log_info(2, log, 0, 
                                                     "Obeying %s#store consistency @ %lld for %s",
                                                     (type & It_Store) ? "store":"load",
                                                     SIM_cycle_count(cpu), cpu->name);
                                        goto stall;
                                }
                                
                        }
                }

                if (SIM_get_pending_exception())
                        SIM_log_error(log, 0, "*** Exception in consistency_controller_operate *** %lld", 
                                      SIM_cycle_count(cpu));
        }
        
        mem_op->ma_no_reissue = 0;
        if (cc->next_level_timing_interface) {
                return cc->next_level_timing_interface->operate(cc->next_level_object, space, map, mem_op);
        } else {
                return 0;
        }

stall:
        /* if ma_no_reissue is 0 it is the first time we CC-stall 
           this op, we will only prefetch once */
        if (cc->prefetch && !mem_op->ma_no_reissue && cc->next_level_timing_interface) {
                mem_op_type_t type;
                cycles_t time;
                int may_stall;
                v9_memory_transaction_t *v9_mem_op = 0;
                uint16 p_fcn = 0;

                if (SIM_mem_op_is_from_cpu_arch(mem_op, Sim_Initiator_CPU_V9)) {
                        v9_mem_op = (v9_memory_transaction_t *)mem_op;
                        p_fcn = v9_mem_op->prefetch_fcn;
                        v9_mem_op->prefetch_fcn = SIM_mem_op_is_write(mem_op) ? 3 : 1;
                }

                type = mem_op->type;
                mem_op->type = Sim_Trans_Prefetch;

                may_stall = mem_op->may_stall;
                mem_op->may_stall = 0; /* Prefetches may not stall */

                SIM_log_info(2, log, 0, "Sending prefetch for id %d", (int)mem_op->id);

                time = cc->next_level_timing_interface->operate(cc->next_level_object, space, map, mem_op);
                
                if (v9_mem_op)
                        v9_mem_op->prefetch_fcn = p_fcn;

                mem_op->type = type;
                mem_op->may_stall = may_stall;
        }

        /* do not reissue if squashed */
        mem_op->ma_no_reissue = 1;
        return 1;
}

static set_error_t
set_timing_model_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        consistency_controller_object_t *cc = (consistency_controller_object_t *)obj;
        conf_object_t *next;

        /* accept nil as input to cancel the next timing model */
        if (val->kind == Sim_Val_Nil) {
                cc->next_level_object = NULL;
                cc->next_level_timing_interface = NULL;
        }
        else {
                if (val->kind != Sim_Val_Object)
                        return Sim_Set_Need_Object;

                next = val->u.object;
                if (SIM_get_pending_exception()) {
                        return Sim_Set_Illegal_Value;
                }

                cc->next_level_timing_interface = 
                        SIM_get_interface(next, "timing-model");

                if (SIM_get_pending_exception()) {
                        return Sim_Set_Illegal_Value;
                }
 
                cc->next_level_object = next;
        }

        return Sim_Set_Ok;
}

static attr_value_t
get_timing_model_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        consistency_controller_object_t *cc = (consistency_controller_object_t *)obj;

        if (cc->next_level_object)
                return SIM_make_attr_object(cc->next_level_object);

        return SIM_make_attr_nil();
}

static attr_value_t
get_load_load(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;
        attr_value_t ret;
        ret.kind = Sim_Val_Integer;
        ret.u.integer = o->load_load;        
        return ret;
}

static set_error_t
set_load_load(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;
        
        o->load_load = !!val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_load_store(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;
        attr_value_t ret;
        ret.kind = Sim_Val_Integer;
        ret.u.integer = o->load_store;        
        return ret;
}

static set_error_t
set_load_store(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;
        
        o->load_store = !!val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_store_load(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;
        attr_value_t ret;
        ret.kind = Sim_Val_Integer;
        ret.u.integer = o->store_load;        
        return ret;
}

static set_error_t
set_store_load(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;
        
        o->store_load = !!val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_store_store(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;
        attr_value_t ret;
        ret.kind = Sim_Val_Integer;
        ret.u.integer = o->store_store;        
        return ret;
}

static set_error_t
set_store_store(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;
        
        o->store_store = !!val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_prefetch(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;
        attr_value_t ret;
        ret.kind = Sim_Val_Integer;
        ret.u.integer = o->prefetch;
        return ret;
}

static set_error_t
set_prefetch(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        consistency_controller_object_t *o = (consistency_controller_object_t *)obj;

        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;
        
        o->prefetch = !!val->u.integer;
        return Sim_Set_Ok;
}

class_data_t class_data;

void
init_local(void)
{
        conf_class_t *conf_class;

        /* Initialize and register the class "consistency_controller". */
        memset(&class_data, 0, sizeof(class_data_t));
        class_data.new_instance = consistency_controller_new_instance;
        class_data.description = 
                "The consistency controller class implements a "
                "memory hierarchy that communicates with the instruction tree "
                "(in an out of order Simics) to enforce the architecturally "
                "defined consistency model. This is done by stalling loads and stores "
                "that would violate the consistency model but are otherwise ready to "
                "issue to the memory system. The reason for not integrating the "
                "consistency controller into the Simics core is to allow the user to "
                "experiment with relaxed consistency model implementations. The user "
                "can replace the consistency controller or modify the default one to "
                "meet their needs (the source code is available in the distribution). "
                "\n\n"
                "The default consistency controller can be constrained through "
                "attributes";

        conf_class = SIM_register_class("consistency-controller", &class_data);

        /* Initialize and register the timing-model interface */
        consistency_controller_timing_interface = MM_ZALLOC(1, timing_model_interface_t);
        consistency_controller_timing_interface->operate = consistency_controller_operate;
        SIM_register_interface(conf_class, "timing-model", consistency_controller_timing_interface);

        /* Initialize attributes */

        SIM_register_attribute(conf_class, "timing_model", 
                               get_timing_model_attribute, 0, 
                               set_timing_model_attribute, 0, Sim_Attr_Optional,
                               "The next memory hierarchy object");

        SIM_register_attribute(conf_class, "load-load",
                               get_load_load, 0, 
                               set_load_load, 0, Sim_Attr_Optional,
                               "If set to non-zero load-load memory consistency will be enforced.");

        SIM_register_attribute(conf_class, "load-store",
                               get_load_store, 0, 
                               set_load_store, 0, Sim_Attr_Optional,
                               "If set to non-zero load-store memory consistency will be enforced.");

        SIM_register_attribute(conf_class, "store-load",
                               get_store_load, 0, 
                               set_store_load, 0, Sim_Attr_Optional,
                               "If set to non-zero store-load memory consistency will be enforced. This is the default");

        SIM_register_attribute(conf_class, "store-store",
                               get_store_store, 0, 
                               set_store_store, 0, Sim_Attr_Optional,
                               "If set to non-zero store-store memory consistency will be enforced. This is the default.");

        SIM_register_attribute(conf_class, "prefetch",
                               get_prefetch, 0, 
                               set_prefetch, 0, Sim_Attr_Optional,
                               "If set to non-zero prefetch memory transaction will be sent to the rest "
                               "of the memory hierarchy for transactions that breaks the memory consistency. "
                               "Zero is default.");
}
