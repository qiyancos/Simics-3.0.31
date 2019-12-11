/*
 * simics/devs/i2c.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_I2C_H
#define _SIMICS_DEVS_I2C_H

/*

   Interfaces for the i2c architecture
   -----------------------------------

   The i2c bidirectional 2-wire bus and data transmission protocol was
   developed in the early 1980's by Philips semiconductors. The i2c is
   an acronym for inter-IC (iic), and this name literally explains the
   purpose; to connect integrated circuits to a common bus.

   A device that sends data to the bus is defined as a transmitter,
   and a device receiving data from the bus is defined as a receiver.
   The device that controls the transfer is called a master, and
   devices that are controlled by the master are called slaves. This
   gives us a total of four different modes for device operations:

   - master/transmitter
   - master/receiver
   - slave/transmitter
   - slave/receiver

   Note that not all devices can operate as a bus master.

   The transfer must be initiated by the master, through a start (or
   repeat-start) condition. All data are transfered one byte at a
   time, and the first byte contains the slave address (with the least
   significant bit as a read/write flag).

*/


/* states of the i2c device (well, actually the idle state refers to the i2c
   _bus_). Names used in checkpointing. */
#define FOR_ALL_I2C_DEVICE_STATE(op)                    \
        op(I2C_idle,            "I2C Idle"),            \
        op(I2C_master_transmit, "I2C Master Transmit"), \
        op(I2C_master_receive,  "I2C Master Receive"),  \
        op(I2C_slave_transmit,  "I2C Slave Transmit"),  \
        op(I2C_slave_receive,   "I2C Slave Receive")

#define I2C_FIRST_ELEMENT(a,b) a
typedef enum i2c_device_state {
        FOR_ALL_I2C_DEVICE_STATE(I2C_FIRST_ELEMENT),
        I2C_max_states
} i2c_device_state_t;
#undef I2C_FIRST_ELEMENT

/* <add-type id="i2c_device_flag_t def">
   </add-type> */
typedef enum {
        I2C_flag_exclusive,
        I2C_flag_shared
} i2c_device_flag_t;


/* <add id="i2c_bus_interface_t">
   <insert-until text="// ADD INTERFACE i2c_bus_interface"/>

   The <iface>i2c_bus</iface> interface is implemented by all I2C
   buses. The interface is used by I2C devices to communicate with the
   I2C bus.

   To register an I2C device to an I2C bus, first you call
   <func>register_device</func> with a 7-bit <attr>address</attr> and
   <attr>mask</attr>. The address is actually an address pattern. When
   there is traffic on the I2C bus (as initiated by a call to the bus
   interface <func>start</func> function), the target address is
   matched against each registered device by checking if
   <tt>(target_address ^ device_address) & device_mask == 0</tt>. The
   I2C device sets the type of connection using the <attr>flags</attr>
   attribute. The variants are <i>exclusive</i> or <i>shared</i>. An
   I2C device connected <i>exclusive</i> can not share a transfer with
   another I2C device. An I2C device connected <i>shared</i> supports
   other I2C devices connected <i>shared</i> can handle the same
   transfer.

   Use <func>unregister_device</func> to unregister an I2C device from
   the I2C bus. To completely remove a device use the same
   <attr>address</attr> and <attr>mask</attr> attributes as when the
   device was registered. An I2C device can also remove some part of
   the address match by unregister itself with a different mask.

   An I2C transfer is initiated by a master I2C device. The I2C device
   responding the transfer is called slave. The master starts a
   transfer by calling the <func>start</func> function with
   <attr>address</attr> as argument. The <attr>address</attr> is the
   7-bit address plus a read-write bit (read-write = 0 ->
   slave-receive, read-write = 1 -> slave-transmit). This means that
   all odd values sent to <func>start</func> initiates a transfer
   where the master is requesting data from the slave.

   I2C devices implement the <iface>i2c_device</iface> interface. Both
   the <iface>i2c_device</iface> and the <iface>i2c_bus</iface>
   interface has identical <func>read_data</func> and
   <func>write_data</func> functions to transfer data over the
   bus. The <iface>i2c_device</iface> also has <func>set_state</func>
   function, which is used by the I2C bus to set the I2C device
   state. The states are <i>I2C_idle</i>, <i>I2C_master_transmit</i>,
   <i>I2C_master_receive</i>, <i>I2C_slave_transmit</i>, and
   <i>I2C_slave_receive</i>. The default state is <i>I2C_idle</i>.

   This is how a transfer is made:

   <tt>1.</tt> The I2C master device calls <func>start</func> in the
    I2C bus with 7-bit address and 1-bit read/write flag.

   <tt>2.</tt> The I2C bus calls the <func>set_state</func> in the I2C
   slave device with <i>I2C_slave_transmit</i> or
   <i>I2C_slave_receive</i> as argument depending on the 1-bit
   read/write flag. The I2C slave accepts the state change by
   returning 0.

   <tt>3.</tt> I2C bus returns <tt>0</tt> to the I2C master if the
   start command in <tt>1</tt> was successful. The I2C bus can report
   failure for several reasons, there are another ongoing transfer,
   can not find any device with the address provided, I2C slave did
   not except state change etc.

   <tt>4.</tt> The I2C master calls the I2C buses
   <func>read_data</func> or <func>write_data</func> depending if it
   wants to read or write from the I2C slave. The I2C bus relays the
   call to the I2C slaves <func>read_data</func> or
   <func>write_data</func> function. The I2C have no way to report
   errors, the I2C master expects the I2C slave to be able to handle
   all calls without any problem. The I2C bus can do step <tt>4</tt>
   several times before terminating the transfer.

   <tt>5.</tt> The I2C master calls the <func>stop</func> function
   when it wants to terminate the transfer. This causes the I2C bus to
   call the <func>set_state</function> function in the I2C slave with
   <i>I2C_idle</i> as argument. The transfer is now completed.

   </add>
*/
typedef struct i2c_bus_interface {
        int (*start)(conf_object_t *i2c_bus, uint8 address);
        int (*stop)(conf_object_t *i2c_bus);
        uint8 (*read_data)(conf_object_t *i2c_bus);
        void (*write_data)(conf_object_t *i2c_bus, uint8 value);
        int (*register_device)(conf_object_t *i2c_bus, conf_object_t *device,
                               uint8 address, uint8 mask, i2c_device_flag_t flags);
        void (*unregister_device)(conf_object_t *i2c_bus, conf_object_t *device,
                                  uint8 address, uint8 mask);
} i2c_bus_interface_t;

#define I2C_BUS_INTERFACE "i2c-bus"
// ADD INTERFACE i2c_bus_interface


/* <add id="i2c_device_interface_t">
   <insert-until text="// ADD INTERFACE i2c_device_interface"/>

   </add>
*/
typedef struct i2c_device_interface {
        int (*set_state)(conf_object_t *device, i2c_device_state_t state,
                        uint8 address);
        uint8 (*read_data)(conf_object_t *device);
        void (*write_data)(conf_object_t *device, uint8 value);

} i2c_device_interface_t;

#define I2C_DEVICE_INTERFACE "i2c-device"
// ADD INTERFACE i2c_device_interface

#endif /* _SIMICS_DEVS_I2C_H */
