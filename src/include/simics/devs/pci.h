/*
 * simics/devs/pci.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.

 *
 */

#ifndef _SIMICS_DEVS_PCI_H
#define _SIMICS_DEVS_PCI_H

/* <add-type id="pci_device_interface_t">
   This interface is implemented by all PCI devices (including bridges).
   </add-type>
 */
typedef struct {
        void (*bus_reset)(conf_object_t *obj);

        /* Interrupt Acknowlege cycle */
        int (*interrupt_acknowledge)(conf_object_t *obj);

        /* Special Cycle */
        void (*special_cycle)(conf_object_t *obj, uint32 value);

        /* System Error */
        void (*system_error)(conf_object_t *obj);

        /* peer-to-peer interrupt mechanism */
        void (*interrupt_raised)(conf_object_t *obj, int pin);
        void (*interrupt_lowered)(conf_object_t *obj, int pin);
} pci_device_interface_t;

#define PCI_DEVICE_INTERFACE "pci-device"
/* ADD INTERFACE pci_device_interface */

/* <add-type id="pci_bus_interface_t">
   No documentation available!
   </add-type>
 */
typedef struct {
        exception_type_t (*memory_access)(conf_object_t *obj,
                                          generic_transaction_t *mem_op);
        void (*raise_interrupt)(conf_object_t *obj, conf_object_t *dev,
                                int pin);
        void (*lower_interrupt)(conf_object_t *obj, conf_object_t *dev,
                                int pin);
        int (*interrupt_acknowledge)(conf_object_t *obj);
        int (*add_map)(conf_object_t *obj, conf_object_t *dev,
                       addr_space_t space, conf_object_t *target,
                       map_info_t info);
        int (*remove_map)(conf_object_t *obj, conf_object_t *dev,
                          addr_space_t space, int function);
	void (*set_bus_number)(conf_object_t *obj, int bus_id);
	void (*set_sub_bus_number)(conf_object_t *obj, int bus_id);
        void (*add_default)(conf_object_t *obj, conf_object_t *dev,
                            addr_space_t space, conf_object_t *target,
                            map_info_t info);
        void (*remove_default)(conf_object_t *obj, addr_space_t space);
        void (*bus_reset)(conf_object_t *obj);
        void (*special_cycle)(conf_object_t *obj, uint32 value);
        void (*system_error)(conf_object_t *obj);

        int (*get_bus_address)(conf_object_t *obj, conf_object_t *dev);

        void (*set_device_timing_model)(conf_object_t *obj,
                                        conf_object_t *dev,
                                        conf_object_t *timing_model);
        // Only available since build 1318
        void (*set_device_status)(conf_object_t *obj, int device, int function,
                                  int enabled);
} pci_bus_interface_t;

#define PCI_BUS_INTERFACE		"pci-bus"
/* ADD INTERFACE pci_bus_interface */

/* <add-type id="pci_bridge_interface_t">
   This interface is implemented by all PCI bridges.
   </add-type>
 */
typedef struct {
        void (*system_error)(conf_object_t *obj);
        void (*raise_interrupt)(conf_object_t *obj, conf_object_t *irq_obj,
                                int device, int pin);
        void (*lower_interrupt)(conf_object_t *obj, conf_object_t *irq_obj,
                                int device, int pin);
} pci_bridge_interface_t;

#define PCI_BRIDGE_INTERFACE		"pci-bridge"
/* ADD INTERFACE pci_bridge_interface */


/* <add-type id="pci_interrupt_interface_t">
   This interface should only be used when a device other than the bridge
   handles PCI interrupts on the PCI bus. The initiating device is specified
   with a PCI device number, and the pin represents PCI interrupt lines
   (A, B, C, or D) as numbers in the range of 0 to 3.
   </add-type>
 */
typedef struct {
        void (*raise_interrupt)(conf_object_t *obj, conf_object_t *irq_obj,
                                int device, int pin);
        void (*lower_interrupt)(conf_object_t *obj, conf_object_t *irq_obj,
                                int device, int pin);
} pci_interrupt_interface_t;

#define PCI_INTERRUPT_INTERFACE		"pci-interrupt"
/* ADD INTERFACE pci_interrupt_interface */

#define DEVICE_CONF_FUNC      0xff
#define DEVICE_PCIE_CONF_FUNC 0xfe

/*
   <add-type id="pcie_message_type_t def">
   </add-type>
*/
typedef enum {
        /* INTx emulation */
        PCIE_Msg_Assert_INTA       = 0x20,
        PCIE_Msg_Assert_INTB       = 0x21,
        PCIE_Msg_Assert_INTC       = 0x22,
        PCIE_Msg_Assert_INTD       = 0x23,
        PCIE_Msg_Deassert_INTA     = 0x24,
        PCIE_Msg_Deassert_INTB     = 0x25,
        PCIE_Msg_Deassert_INTC     = 0x26,
        PCIE_Msg_Deassert_INTD     = 0x27,

        /* Power Management */
        PCIE_PM_Active_State_Nak   = 0x14,
        PCIE_PM_PME                = 0x18,
        PCIE_PM_Turn_Off           = 0x19,
        PCIE_PM_PME_TO_Ack         = 0x1B,

        /* Error Messages */
        PCIE_ERR_COR               = 0x30,
        PCIE_ERR_NONFATAL          = 0x31,
        PCIE_ERR_FATAL             = 0x33,

        /* Locked Transaction */
        PCIE_Locked_Transaction    = 0x00,

        /* Slot Power Limit */
        PCIE_Set_Slot_Power_Limit  = 0x90,

        /* Hot Plug Messages */
        PCIE_HP_Power_Indicator_On        = 0x45,
        PCIE_HP_Power_Indicator_Blink     = 0x47,
        PCIE_HP_Power_Indicator_Off       = 0x44,
        PCIE_HP_Attention_Button_Pressed  = 0x48,
        PCIE_HP_Attention_Indicator_On    = 0x41,
        PCIE_HP_Attention_Indicator_Blink = 0x43,
        PCIE_HP_Attention_Indicator_Off   = 0x40
} pcie_message_type_t;

/* <add-type id="pci_express_interface_t">
   This interface can be implemented by any PCI Express device, switch or
   endpoint. It is also implemented by the pci-bus, which will pass it on
   to the other end; e.g. if the endpoint sends a message, the pci-bus will
   pass it on to the bridge (downport), and if the downport sends it, it will
   be broadcasted to all devices on the bus.

   <param>src</param> is the object sending the object. <param>type</param> is
   one of:

   <insert id="pcie_message_type_t def"/>

   The contents of <param>payload</param> depends on <param>type</param>.
   </add-type>
 */
typedef struct {
        int (*send_message)(conf_object_t *dst, conf_object_t *src,
                            pcie_message_type_t type, byte_string_t payload);
} pci_express_interface_t;
#define PCI_EXPRESS_INTERFACE "pci-express"
/* ADD INTERFACE pci_express_interface */

/* <add-type id="pci_express_hotplug_interface_t">
   This interface is intended for PCI Express switches that need to monitor
   the status of their downports.

   <fun>presence_change</fun> is called from the pci-bus when an device is
   added or removed from the bus. <param>is_present</param> is set to 1 when
   the device is added, and 0 when it is removed.

   <fun>inject_power_fault</fun> can be used to simulate a power fault on
   the downport. It is never called automatically.

   <fun>press_attention_button</fun> can be called to simulate the attention
   button being pressed. The switch can respond to this by e.g. raising
   an interrupt and setting appropriate status bits. It is never called
   automatically.

   <fun>set_mrl_state</fun> is similar to <fun>attention_button_press</fun>
   but controls the Manually operated Retention Latch. Set
   <param>locked</param> to 1 to simulate it being locked/closed, and 0 to
   simulate it being unlocked/opened.

   Finally, <fun>get_mrl_state</fun> returns the state of the Manually
   operated Retention Latch.
   </add-type>
 */
typedef struct {
        /* This is sent when a device is added or removed from the bus. */
        void (*presence_change)(conf_object_t *dst, conf_object_t *src,
                                int is_present);
        void (*inject_power_fault)(conf_object_t *obj);
        void (*press_attention_button)(conf_object_t *obj);
        void (*set_mrl_state)(conf_object_t *obj, int locked);
        int  (*get_mrl_state)(conf_object_t *obj);
} pci_express_hotplug_interface_t;
#define PCI_EXPRESS_HOTPLUG_INTERFACE "pci-express-hotplug"
/* ADD INTERFACE pci_express_hotplug_interface */

#endif /* _SIMICS_DEVS_PCI_H */
