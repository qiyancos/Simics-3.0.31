/*
  i2c-device.c - I²C devices

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

#include <simics/api.h>
#include <simics/utils.h>
#include "i2c-device.h"

void
i2c_device_init(log_object_t *log, i2c_device_t *i2c_device)
{
        i2c_device->log = log;
        i2c_device->state = I2C_Pin_Idle;
        i2c_device->data_out = i2c_device->clock_out = 0;
        i2c_device->remote_data = 0;
}

static set_error_t
set_i2c_bus(void *dummy, conf_object_t *obj, attr_value_t *value, attr_value_t *idx)
{
	i2c_device_t *dev = get_i2c_device(obj);
        i2c_bus_interface_t *iface;
        conf_object_t *i2c_bus;

        if (value->kind != Sim_Val_Object)
                return Sim_Set_Need_Object;

        i2c_bus = value->u.object;

        if ((iface = SIM_get_interface(i2c_bus, I2C_BUS_INTERFACE)) == NULL)
                return Sim_Set_Interface_Not_Found;

        dev->i2c_bus = i2c_bus;
        dev->i2c_bus_iface = *iface;

        return Sim_Set_Ok;
}

static attr_value_t
get_i2c_bus(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
	i2c_device_t *dev = get_i2c_device(obj);

        if (dev->i2c_bus)
                return SIM_make_attr_object(dev->i2c_bus);
        
        return SIM_make_attr_invalid();
}

static set_error_t
set_i2c_state(void *dummy, conf_object_t *obj, attr_value_t *value, attr_value_t *idx)
{
	i2c_device_t *dev = get_i2c_device(obj);
        integer_t state, dout, cout, rdata;

        if (!SIM_ascanf(value, "iiii", &state, &dout, &cout, &rdata))
                return Sim_Set_Illegal_Value;

        dev->state = state;
        dev->data_out = dout;
        dev->clock_out = cout;
        dev->remote_data = rdata;

        return Sim_Set_Ok;
}

static attr_value_t
get_i2c_state(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
	i2c_device_t *dev = get_i2c_device(obj);
        
        return SIM_make_attr_list(4,
                                  SIM_make_attr_integer(dev->state),
                                  SIM_make_attr_integer(dev->data_out),
                                  SIM_make_attr_integer(dev->clock_out),
                                  SIM_make_attr_integer(dev->remote_data));
}

void
register_i2c_state_attributes(conf_class_t *i2c_class)
{
        SIM_register_typed_attribute(
                i2c_class, "i2c-device-state",
                get_i2c_state, 0, set_i2c_state, 0,
                Sim_Attr_Optional, "[iiii]", NULL,
                "List representing data state in the device");
}

void
register_i2c_device_attributes(conf_class_t *i2c_class)
{
        SIM_register_attribute(i2c_class, "i2c-bus",
                               get_i2c_bus, 0,
                               set_i2c_bus, 0,
                               Sim_Attr_Required | Sim_Init_Phase_1,
			       "The i2c bus connected this device is connected to");

        register_i2c_state_attributes(i2c_class);
}

static void
i2c_clock_high(i2c_device_t *dev)
{
	switch (dev->state) {
	case I2C_Pin_Address:
                dev->bit++;
		dev->data = (dev->data << 1) | dev->data_out;
		break;
	case I2C_Pin_Write:
                dev->bit++;
		dev->data = (dev->data << 1) | dev->data_out;
		break;
	case I2C_Pin_Read_Ack:
                dev->data = dev->data_out;
                break;
	case I2C_Pin_Write_Ack:
	case I2C_Pin_Address_Ack:
	case I2C_Pin_Read:
	case I2C_Pin_Idle:
		break;
	}
}

static void
i2c_clock_low(i2c_device_t *dev)
{
        dev->remote_data = 1;
	switch (dev->state) {
	case I2C_Pin_Address:
		if (dev->bit == 8) {
                        int status = dev->i2c_bus_iface.start(dev->i2c_bus, dev->data);
                        if (status < 0) {
                                SIM_log_info(2, dev->log, 0,
                                             "No device, cancelling operation.");
                                dev->state = I2C_Pin_Idle;
                                break;
                        }
                        SIM_log_info(3, dev->log, 0, "Address ack state.");
                        dev->state = I2C_Pin_Address_Ack;
                        dev->remote_data = 0;
                }
		break;
	case I2C_Pin_Address_Ack:
		if (dev->data & 1) {
			/* Read operation */
                        SIM_log_info(3, dev->log, 0, "Got address ACK -"
				     " Starting read operation");
                        goto prepare_read;
		} else {
			/* Write operation */
                        SIM_log_info(3, dev->log, 0, "Got address ACK -"
				     " Starting write operation");
                        goto prepare_write;
		}
                break;
        case I2C_Pin_Write:
                if (dev->bit == 8) {
                        SIM_log_info(2, dev->log, 0, "Write operation ready"
                                     " (data = 0x%x)", dev->data);
                        dev->i2c_bus_iface.write_data(dev->i2c_bus, dev->data);
                        dev->state = I2C_Pin_Write_Ack;
                        dev->remote_data = 0;
                }
                break;
	case I2C_Pin_Write_Ack:
          prepare_write:
		dev->state = I2C_Pin_Write;
		dev->bit = 0;
		dev->remote_data = 1;
		break;
	case I2C_Pin_Read_Ack:
                if (dev->data) {
                        SIM_log_info(3, dev->log, 0, "Master nacked read data. Entering idle state.");
                        dev->state = I2C_Pin_Idle;
                        break;
                } else {
                        SIM_log_info(3, dev->log, 0, "Master acked read data. Reading more data.");
                }
          prepare_read:
		dev->state = I2C_Pin_Read;
                dev->data = dev->i2c_bus_iface.read_data(dev->i2c_bus);
		SIM_log_info(3, dev->log, 0, "Starting read operation (data = 0x%x)",
			     dev->data);
		dev->bit = 0;
                /* fall-trough */
	case I2C_Pin_Read:
		if (dev->bit == 8) {
                        dev->state = I2C_Pin_Read_Ack;
                        SIM_log_info(3, dev->log, 0, "Read operation ready");
                        break;
                }
                dev->remote_data = (dev->data >> 7) & 1;
                dev->data <<= 1;
                dev->bit++;
                break;
        case I2C_Pin_Idle:
                break;
	}
}

static int
is_listening(i2c_device_t *dev)
{
        /* I2C_Pin_Read should be included here too, but some devices
           only send one byte and goes into idle state after that. In
           Simics there is currently no way for a device to say if it
           is sending more data. */
	return (dev->state != I2C_Pin_Address_Ack
                && dev->state != I2C_Pin_Write_Ack);
}

static void
i2c_data_high(i2c_device_t *dev)
{
	if (dev->clock_out && is_listening(dev)) {
		/* Stop condition */
                SIM_log_info(3, dev->log, 0, "STOP");

                dev->i2c_bus_iface.stop(dev->i2c_bus);
	}
}

static void
i2c_data_low(i2c_device_t *dev)
{
        /* Check that we are not driving the bus ourselves */
	if (dev->clock_out && is_listening(dev)) {
		/* Start condition */
                
		SIM_log_info(3, dev->log, 0, "START");
                
		dev->state = I2C_Pin_Address;
		dev->data = 0;
		dev->bit = 0;
	}
}

int
i2c_read_clock(i2c_device_t *dev)
{
        return dev->clock_out;
}

int
i2c_read_data(i2c_device_t *dev)
{
        return dev->data_out && dev->remote_data;
}

void
i2c_write_clock(i2c_device_t *dev, int state)
{
        state = !!state;
        if (dev->clock_out == state)
                return;

        SIM_log_info(4, dev->log, 0, "Clock %s [data field = 0x%x]",
		     state ? "HIGH" : "LOW", dev->data);

        dev->clock_out = state;
        (state ? i2c_clock_high : i2c_clock_low)(dev);
}

void
i2c_write_data(i2c_device_t *dev, int state)
{
        state = !!state;
        if (dev->data_out == state)
                return;

        SIM_log_info(4, dev->log, 0, "Data %s", state ? "HIGH" : "LOW");
        
        dev->data_out = state;
        (state ? i2c_data_high : i2c_data_low)(dev);
}
