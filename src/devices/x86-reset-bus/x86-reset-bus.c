/*
  x86-reset-bus.c

  Copyright 2002-2007 Virtutech AB
  
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
#include <simics/arch/x86.h>

#include "x86-reset-bus.h"

#define DEVICE_NAME "x86-reset-bus"

typedef struct irq_device {
        log_object_t log;
        int num_reset_tgts;
        conf_object_t **reset_tgts;
        x86_interface_t **x86_iface;
        a20_interface_t *a20_iface;
} irq_device_t;

static conf_object_t *
new_instance(parse_object_t *parse_obj)
{
        irq_device_t *irq = MM_ZALLOC(1, irq_device_t);        
        SIM_log_constructor(&irq->log, parse_obj);
        return &irq->log.obj;
}

static void
set_a20_line(conf_object_t *obj, int value)
{
	irq_device_t *irq = (irq_device_t *)obj;

        if (irq->num_reset_tgts)
                irq->a20_iface->set_a20_line(irq->reset_tgts[0], value);
}

static int
get_a20_line(conf_object_t *obj)
{
	irq_device_t *irq = (irq_device_t *)obj;

        if (irq->num_reset_tgts)
                return irq->a20_iface->get_a20_line(irq->reset_tgts[0]);
        return 0;
}

static void
reset_all(conf_object_t *obj)
{
        irq_device_t *irq = (irq_device_t *)obj;
        int i;

        for (i = 0; i < irq->num_reset_tgts; i++)
                irq->x86_iface[i]->set_pin_status(irq->reset_tgts[i], Pin_Init, 1);
}

static set_error_t
set_reset_tgts(void *arg, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
	irq_device_t *irq = (irq_device_t *)obj;
        int i;

        for (i = 0; i < val->u.list.size; i++) {
                if (!SIM_get_interface(val->u.list.vector[i].u.object,
                                       X86_INTERFACE)) {
                        SIM_clear_exception();
                        return Sim_Set_Interface_Not_Found;
                }
                if (i == 0) {
                        if (!SIM_get_interface(val->u.list.vector[i].u.object,
                                               A20_INTERFACE)) {
                                SIM_clear_exception();
                                return Sim_Set_Interface_Not_Found;
                        }
                }
        }

        if (irq->num_reset_tgts) {
                MM_FREE(irq->reset_tgts);
                MM_FREE(irq->x86_iface);
        }

        irq->num_reset_tgts = val->u.list.size;
        irq->reset_tgts = MM_ZALLOC(irq->num_reset_tgts, conf_object_t *);
        irq->x86_iface = MM_ZALLOC(irq->num_reset_tgts, x86_interface_t *);
        for (i = 0; i < irq->num_reset_tgts; i++) {
                irq->reset_tgts[i] = val->u.list.vector[i].u.object;
                irq->x86_iface[i] = SIM_get_interface(irq->reset_tgts[i],
                                                      X86_INTERFACE);
        }
        irq->a20_iface = SIM_get_interface(irq->reset_tgts[0], A20_INTERFACE);
        return Sim_Set_Ok;
}

static attr_value_t
get_reset_tgts(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
	irq_device_t *irq = (irq_device_t *)obj;
        attr_value_t ret;
        int i;

        ret = SIM_alloc_attr_list(irq->num_reset_tgts);
        for (i = 0; i < irq->num_reset_tgts; i++)
                ret.u.list.vector[i] = SIM_make_attr_object(irq->reset_tgts[i]);
        return ret;
}

DLL_EXPORT void
init_local(void)
{
        class_data_t funcs;
        conf_class_t *class;
        x86_reset_bus_interface_t *irq_iface;
        cpu_group_interface_t *grp_iface;
        
        memset(&funcs, 0, sizeof(class_data_t));
        funcs.new_instance = new_instance;
	funcs.description =
		"The " DEVICE_NAME " device forwards resets to connected "
                "x86 processors.";
        class = SIM_register_class(DEVICE_NAME, &funcs);
        
        irq_iface = MM_ZALLOC(1, x86_reset_bus_interface_t);
        irq_iface->set_a20_line = set_a20_line;
        irq_iface->get_a20_line = get_a20_line;
        irq_iface->reset_all = reset_all;
        SIM_register_interface(class, X86_RESET_BUS_INTERFACE, irq_iface);

        grp_iface = MM_ZALLOC(1, cpu_group_interface_t);
        SIM_register_interface(class, CPU_GROUP_INTERFACE, grp_iface);

        SIM_register_typed_attribute(
                class, "reset_targets",
                get_reset_tgts, NULL,
                set_reset_tgts, NULL,
                Sim_Attr_Optional, "[o*]", NULL,
                "A list of objects implementing the <tt>" X86_INTERFACE
                "</tt> and <tt>" A20_INTERFACE "</tt> interfaces.");

        SIM_register_typed_attribute(
                class, "cpu_list",
                get_reset_tgts, NULL,
                NULL, NULL,
                Sim_Attr_Pseudo, "[o*]", NULL,
                "List of all connected processors. This attribute is "
                "available in all classes implementing the \""
                CPU_GROUP_INTERFACE "\" interface.");
}
