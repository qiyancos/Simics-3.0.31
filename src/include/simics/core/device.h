/*
 * simics/core/device.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 */

#ifndef _SIMICS_CORE_DEVICE_H
#define _SIMICS_CORE_DEVICE_H

/* <add-type id="interrupt_ack_interface_t|interrupt_cpu_interface_t">
   The <tt>interrupt_ack_fn_t</tt> function is called by an interrupt target
   to ack an interrupt. Returns the interrupt vector.
   <ndx>interrupt_ack_fn_t</ndx>
   </add-type> */
typedef int (*interrupt_ack_fn_t)(conf_object_t *NOTNULL);

/* <add id="interrupt_ack_interface_t">
   Interface for acked interrupts. The target is typically a cpu that
   later calls the supplied ack function when the interrupt is
   actually taken.

   <insert-until text="// ADD INTERFACE interrupt_ack_interface"/>
   </add> */
typedef struct interrupt_ack_interface {
        void (*raise_interrupt)(conf_object_t *NOTNULL obj,
                                interrupt_ack_fn_t, 
                                conf_object_t *);
        void (*lower_interrupt)(conf_object_t *NOTNULL obj,
                                interrupt_ack_fn_t);
} interrupt_ack_interface_t;

#define INTERRUPT_ACK_INTERFACE "interrupt_ack"
// ADD INTERFACE interrupt_ack_interface

/* <add id="interrupt_cpu_interface_t">
   Interface that must be implemented by an interrupt source that
   sends interrupts through the interrupt_ack interface. Used to
   reestablish the ack function when loading a checkpoint.

   <insert-until text="// ADD INTERFACE interrupt_cpu_interface"/>
   </add> */
typedef struct interrupt_cpu_interface {
        interrupt_ack_fn_t ack;
} interrupt_cpu_interface_t;

#define INTERRUPT_CPU_INTERFACE "interrupt_cpu"
// ADD INTERFACE interrupt_cpu_interface

/* <add id="port_space_interface_t">
   I/O port interface.
   <insert-until text="// ADD INTERFACE port_space_interface"/>
   </add> */
typedef struct port_space_interface {
        exception_type_t (*port_operation)(conf_object_t *NOTNULL pspace_obj,
                                           generic_transaction_t *NOTNULL mop,
                                           map_info_t map_info);
        /* functions introduced in build 1323 */
        attr_value_t (*read)(conf_object_t *NOTNULL obj,
                             conf_object_t *initiator,
                             physical_address_t addr,
                             int length,
                             int inquiry);
        exception_type_t (*write)(conf_object_t *NOTNULL obj,
                                  conf_object_t *initiator,
                                  physical_address_t addr,
                                  attr_value_t data,
                                  int inquiry);
} port_space_interface_t;

#define PORT_SPACE_INTERFACE "port_space"
// ADD INTERFACE port_space_interface

/* <add-type id="apic_cpu_interface_t">
   Interface to read and write the task priority register. Only used
   on x86-64 where the task priority register is both a cpu register
   (CR8) and a register in the local apic.

   </add-type> */
struct apic_cpu_interface {
        uint64 (*tpr_r)(conf_object_t *NOTNULL obj);
        void (*tpr_w)(conf_object_t *NOTNULL obj, uint64 tpr);
        void (*init)(conf_object_t *NOTNULL obj);
};

/* <add id="pin_interface_t">
   Interface to communicate the value of a pin.

   <note>Obsoleted by the <iface>signal</iface> interface.</note>

   <insert-until text="// ADD INTERFACE pin_interface"/>
   </add> */
struct pin_interface {
        void (*set)(conf_object_t *NOTNULL obj);
        void (*clear)(conf_object_t *NOTNULL obj);
};

#define PIN_INTERFACE "pin"
// ADD INTERFACE pin_interface


/* <add id="signal_interface_t">
   Interface to model a signal, such as a reset or interrupt.

   The signal initiator should call <fun>signal_raise()</fun> to raise the
   signal level to its active level. Signals are always active high in Simics.
   Once raised, the same initiator may not call <fun>signal_raise()</fun> again
   without an intervening call to <fun>signal_lower()</fun>.

   The implementer must increment a level counter on every
   <fun>signal_raise()</fun> call, and decrement it on
   <fun>signal_lower()</fun>. The signal can not be treated as lowered until
   the counter reaches zero again. This allows multiple sources of the signal.

   The signal target should handle the case where a signal is lowered directly
   when after it has been raised and treat it as a valid pulse. The target
   should also allow the signal to remain raised for some time before it is
   lowered.

   An object that does lookup of the <iface>signal</iface> interface in another
   object should have an attribute that can be set in the configuration to the
   target object. This attribute should either be of the
   <tt>Sim_Val_Object</tt> kind, or a list with two entries, one
   <tt>Sim_Val_Object</tt> and one <tt>Sim_Val_String</tt>. If the object only
   format is used in the configuration, the interface should be looked up using
   <fun>SIM_get_interface()</fun>, and if the list format it used the interface
   should be obtained with <fun>SIM_get_port_interface()</fun>.

   A class that wishes to implement several signal inputs should use named
   interfaces.

   <note>The <iface>signal</iface> interface should be used instead of the
   <iface>simple-interrupt</iface>, <iface>pin</iface> and <iface>reset</iface>
   interfaces when writing new classes.</note>

   <insert-until text="// ADD INTERFACE signal_interface"/>
   </add> */
struct signal_interface {
        void (*signal_raise)(conf_object_t *NOTNULL obj);
        void (*signal_lower)(conf_object_t *NOTNULL obj);
};

#define SIGNAL_INTERFACE "signal"
// ADD INTERFACE signal_interface

#endif /* _SIMICS_CORE_DEVICE_H */
