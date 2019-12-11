/*
  i2c-device.h

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

#ifndef I2C_DEVICE_H
#define I2C_DEVICE_H

#include <simics/devs/i2c.h>

enum i2c_pin_state {
        I2C_Pin_Idle,
        I2C_Pin_Address,
        I2C_Pin_Address_Ack,
        I2C_Pin_Read,
        I2C_Pin_Read_Ack,
        I2C_Pin_Write,
        I2C_Pin_Write_Ack
};

typedef struct i2c_device {
        log_object_t *log;

        enum i2c_pin_state state;

        unsigned clock_out : 1, data_out : 1, remote_data:1;
        uint8 data;
        int bit;

        conf_object_t *i2c_bus;
        i2c_bus_interface_t i2c_bus_iface;
} i2c_device_t;

void i2c_device_init(log_object_t *log, i2c_device_t *i2c_device);
void register_i2c_device_attributes(conf_class_t *i2c_class);
/* This function only registers the state attribute. */
void register_i2c_state_attributes(conf_class_t *i2c_class);

void i2c_write_clock(i2c_device_t *dev, int state);
void i2c_write_data(i2c_device_t *dev, int state);

int i2c_read_data(i2c_device_t *dev);
int i2c_read_clock(i2c_device_t *dev);

/* implemented by the user */
i2c_device_t *get_i2c_device(conf_object_t *obj);

#endif /* I2C_DEVICE_H */
