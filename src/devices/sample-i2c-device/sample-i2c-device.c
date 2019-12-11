/*
  sample-i2c-device.c - sample code for a Simics I2C device

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

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

#include "../i2c-device/i2c-device.h"

typedef struct sample_i2c_device {

        log_object_t log;

        i2c_device_t i2c;

        uint8 address;
        uint8 read_value;
        int written_value;

} sample_i2c_device_t;

i2c_device_t *
get_i2c_device(conf_object_t *obj)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;
        return &dev->i2c;
}

static int
set_state(conf_object_t *obj, i2c_device_state_t state, uint8 address)
{
        return 0;
}

static uint8
read_data(conf_object_t *obj)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;
        uint8 value = dev->read_value;

        /* handle read operations */
        
        SIM_log_info(1, &dev->log, 0, "reading 0x%x", (int)value);
        
        return value;
}

static void
write_data(conf_object_t *obj, uint8 value)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;

        SIM_log_info(1, &dev->log, 0, "writing 0x%x", (int)value);
        dev->written_value = value;
}

static void
finalize_instance(conf_object_t *obj)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;

        dev->i2c.i2c_bus_iface.register_device(dev->i2c.i2c_bus,
                                               &dev->log.obj,
                                               dev->address,
                                               0xff,
                                               I2C_flag_exclusive);
}

static conf_object_t *
new_instance(parse_object_t *parse_obj)
{
        sample_i2c_device_t *dev = MM_ZALLOC(1, sample_i2c_device_t);        
        
        SIM_log_constructor(&dev->log, parse_obj);
        
        i2c_device_init(&dev->log, &dev->i2c);
        
        return &dev->log.obj;
}

static set_error_t
set_address(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;

        dev->address = val->u.integer;

        return Sim_Set_Ok;
}

static attr_value_t
get_address(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;

        return SIM_make_attr_integer(dev->address);
}

static set_error_t
set_read_value(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;

        dev->read_value = val->u.integer;

        return Sim_Set_Ok;
}

static attr_value_t
get_read_value(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;

        return SIM_make_attr_integer(dev->read_value);
}

static set_error_t
set_written_value(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;

        dev->written_value = val->u.integer;

        return Sim_Set_Ok;
}

static attr_value_t
get_written_value(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        sample_i2c_device_t *dev = (sample_i2c_device_t *)obj;

        return SIM_make_attr_integer(dev->written_value);
}

void
init_local(void)
{
        class_data_t            funcs;
        conf_class_t           *class;
        i2c_device_interface_t *iface;

        memset(&funcs, 0, sizeof(class_data_t));
        funcs.new_instance = new_instance;
        funcs.finalize_instance = finalize_instance;
        funcs.description =
                "The is the sample-i2c-device class which is an example of "
                "how i2c devices can be written in Simics.";
        
        class = SIM_register_class("sample-i2c-device", &funcs);

        iface = MM_ZALLOC(1, i2c_device_interface_t);
        iface->set_state = set_state;
        iface->read_data = read_data;
        iface->write_data = write_data;
        SIM_register_interface(class, I2C_DEVICE_INTERFACE, iface);

        register_i2c_device_attributes(class);

        SIM_register_typed_attribute(class, "address",
                                     get_address, NULL,
                                     set_address, NULL,
                                     Sim_Attr_Required,
                                     "i", NULL,
                                     "Address on the i2c bus.");

        SIM_register_typed_attribute(class, "read_value",
                                     get_read_value, NULL,
                                     set_read_value, NULL,
                                     Sim_Attr_Optional,
                                     "i", NULL,
                                     "Value to return on reads.");

        SIM_register_typed_attribute(class, "written_value",
                                     get_written_value, NULL,
                                     set_written_value, NULL,
                                     Sim_Attr_Optional,
                                     "i", NULL,
                                     "Last byte written to this device.");
}
