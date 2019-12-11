/*
 * simics/devs/interrupt.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_INTERRUPT_H
#define _SIMICS_DEVS_INTERRUPT_H


/* trigger interface
   Useful to acknowledge interrupts in some architectures.
   <note>Obsoleted by the <iface>signal</iface> interface.</note>
 */
typedef void (*trigger_t)(conf_object_t *, int param);

typedef struct {
        trigger_t trigger;
} trigger_interface_t;

#define TRIGGER_INTERFACE "trigger"

/* <add id="simple_interrupt_interface_t">

   A device calls <fun>interrupt()</fun> to logically raise an interrupt and
   <fun>interrupt_clear()</fun> to lower an interrupt.

   The first argument is the object to interrupt, usually a cpu. The
   integer argument to both functions may indicate an interrupt level
   or interrupt pin depending on the receiving device.

   On ARM the integer argument indicates whether the interrupt is normal or
   fast, by being either ARM_INT_IRQ or ARM_INT_FIQ defined by the ARM API
   (by including <file>&lt;simics/arch/arm.h&gt;</file>).

   <note>Obsoleted by the <iface>signal</iface> interface.</note>

   <insert-until text="// ADD INTERFACE simple_interrupt_interface"/>
   </add>
*/
typedef void (*device_interrupt_t)(conf_object_t *, int);
typedef void (*device_interrupt_clear_t)
        (conf_object_t *, int);

typedef struct {
        device_interrupt_t interrupt;
        device_interrupt_clear_t interrupt_clear;
} simple_interrupt_interface_t;

#define SIMPLE_INTERRUPT_INTERFACE "simple-interrupt"
// ADD INTERFACE simple_interrupt_interface

#define INTERRUPT_QUERY_INTERFACE "interrupt-query"

typedef void (*interrupt_changed_state_callback_t)
        (conf_object_t *interrupt_controller,
         conf_object_t *device,
         int irq_level,
         int enabled,
         void *data);
typedef void (*interrupt_query_register_t)
        (conf_object_t *interrupt_controller,
         conf_object_t *device,
         int irq_level,
         interrupt_changed_state_callback_t cb,
         void *cb_data);
typedef int (*interrupt_query_enabled_t)
        (conf_object_t *interrupt_controller,
         int irq_level);

/* <add-type id="interrupt_query_interface_t">
   This interface is used by devices connected to interrupt controllers to
   query whether their irq level is enabled in the interrupt controller or
   not. This is done by the <tt>is_enabled()</tt> function.

   It can also be used to register a callback function to be called when the
   irq is enabled or disabled through the <tt>register_callback</tt> function.
   </add-type>
 */
typedef struct {
        interrupt_query_enabled_t  is_enabled;
        interrupt_query_register_t register_callback;
} interrupt_query_interface_t;

#endif /* _SIMICS_DEVS_INTERRUPT_H */
