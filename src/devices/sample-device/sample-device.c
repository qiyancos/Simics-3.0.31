/*
  sample-device.c - sample code for a Simics device

  Copyright 1998-2007 Virtutech AB
  
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

#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

#define DEVICE_NAME "sample-device"

#include "sample-device.h"

typedef struct sample_device {
        /* log_object_t must be the first thing in the device struct */
        log_object_t log;

        int value;

        /* fill this structure with device specific data  */

} sample_device_t;

/*
 * This function is registered with the SIM_register_class
 * call (see init_local() below), and is used as a constructor
 * for every instance of the sample-device class.
 */  
static conf_object_t *
sample_new_instance(parse_object_t *parse_obj)
{
        sample_device_t *sample = MM_ZALLOC(1, sample_device_t);
        SIM_log_constructor(&sample->log, parse_obj);
        return &sample->log.obj;
}


/* Dummy function that doesn't really do anything. */
static void
simple_function(conf_object_t *obj)
{
	sample_device_t *dev = (sample_device_t *) obj;

        SIM_log_info(1, &dev->log, 0, "'simple_function' called.");
}


static exception_type_t
sample_operation(conf_object_t *obj, generic_transaction_t *mop,
                 map_info_t info)
{
        sample_device_t *sample = (sample_device_t *)obj;
        int offset = (int)(mop->physical_address + info.start - info.base);

        if (SIM_mem_op_is_read(mop)) {
                SIM_log_info(1, &sample->log, 0,
                             "Read from offset %d.", offset);
                SIM_set_mem_op_value_le(mop, 0);
        } else {
                SIM_log_info(1, &sample->log, 0,
                             "Write to offset %d.", offset);
        }
        return Sim_PE_No_Exception;
}

static set_error_t
set_value_attribute(void *arg, conf_object_t *obj,
                    attr_value_t *val, attr_value_t *idx)
{
        sample_device_t *sample = (sample_device_t *)obj;
        sample->value = val->u.integer;
        return Sim_Set_Ok;
}

static attr_value_t
get_value_attribute(void *arg, conf_object_t *obj, attr_value_t *idx)
{
        sample_device_t *sample = (sample_device_t *)obj;
        return SIM_make_attr_integer(sample->value);
}

static set_error_t
set_add_log_attribute(void *arg, conf_object_t *obj,
                      attr_value_t *val, attr_value_t *idx)
{
        sample_device_t *sample = (sample_device_t *)obj;
        SIM_log_info(1, &sample->log, 0, val->u.string);
        return Sim_Set_Ok;
}

static attr_value_t
get_range_sum_attribute(void *arg, conf_object_t *obj, attr_value_t *idx)
{
        if (idx->kind != Sim_Val_List || idx->u.list.size != 2) {
                SIM_attribute_error("Attribute list-indexed with 2 entries");
                return SIM_make_attr_invalid();
        }

        attr_value_t *index = idx->u.list.vector;
        if (index[0].kind != Sim_Val_Integer
            || index[1].kind != Sim_Val_Integer) {
                SIM_attribute_error("Only integers in index list allowed");
                return SIM_make_attr_invalid();
        }
        
        integer_t start = MIN(index[0].u.integer, index[1].u.integer);
        integer_t end = MAX(index[0].u.integer, index[1].u.integer);
        integer_t sum = 0;
        for (integer_t i = start; i <= end; i++)
                sum += i;

        return SIM_make_attr_integer(sum);
}

#if defined(__cplusplus)
extern "C" {
#endif

/*
 * init_local() is called once when the device module is loaded into Simics.
 */
void
init_local(void)
{
        class_data_t funcs;
        conf_class_t *sample_class;
        sample_interface_t *sample_interface;
        io_memory_interface_t *memory_interface;

        /*
         * Register the sample device class. The 'sample_new_instance'
         * function serve as a constructor, and is called every time
         * a new instance is created.
         */
        memset(&funcs, 0, sizeof(class_data_t));
        funcs.new_instance = sample_new_instance;
        funcs.description =
                "The sample-device device is a dummy device that compiles and "
                "that can be loaded into Simics. Using it as a starting point "
                "when writing own devices for Simics is encouraged. Several "
                "device specific functions are included. The source is "
                "included in <tt>simics/src/devices/sample-device</tt>.";

        sample_class = SIM_register_class(DEVICE_NAME, &funcs);

        /*
         * Register the 'sample-interface', which is an example
         * of a unique, customized interface that we've implemented
         * for this device.
         */
        sample_interface = MM_ZALLOC(1, sample_interface_t);
        sample_interface->simple_function = simple_function;
        SIM_register_interface(sample_class, "sample_interface",
                               sample_interface);

        /*
         * Register the 'io-memory' interface, which is an example
         * of a generic interface that is implemented by a large
         * number of devices.
         */
        memory_interface = MM_ZALLOC(1, io_memory_interface_t);
        memory_interface->operation = sample_operation;
        SIM_register_interface(sample_class, IO_MEMORY_INTERFACE,
                               memory_interface);
        
        /*
         * Register attributes (device specific data) together with
         * functions for getting and setting these attributes.
         * The 'Sim_Attr_Optional' attribute will be saved with a configuration
         */
        SIM_register_typed_attribute(
                sample_class, "value",
                get_value_attribute, NULL,
                set_value_attribute, NULL,
                Sim_Attr_Optional,
                "i", NULL,
                "The <i>value</i> field.");
        
        /* Pseudo attribute, not saved in configuration */
        SIM_register_typed_attribute(
                sample_class, "add_log",
                0, NULL,
                set_add_log_attribute, NULL,
                Sim_Attr_Pseudo,
                "s", NULL,
                "<i>Write-only</i>. Strings written to this "
                "attribute will end up in the device's log file.");

        /* Example of attribute using indexing */
        SIM_register_typed_attribute(
                sample_class, "range_sum",
                get_range_sum_attribute, NULL,
                0, NULL,
                (attr_attr_t)(Sim_Attr_Pseudo | Sim_Attr_List_Indexed),
                "i", "i",
                "<i>Read-only</i>. When read from index <tt>[<i>i0</i>, "
                "<i>i1</i>]</tt>, the sum of the integers between "
                "<tt><i>i0</i></tt> and <tt><i>i1</i></tt> will "
                "be returned.");
}

#if defined(__cplusplus)
}
#endif
