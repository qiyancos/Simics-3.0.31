/*
  pci-device.h

  Copyright 2000-2007 Virtutech AB
  
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

#ifndef PCI_DEVICE_H
#define PCI_DEVICE_H


// generic registers found in all headers

#define PCI_VENDOR_ID                    0x00
#define PCI_DEVICE_ID                    0x02
#define PCI_COMMAND                      0x04
#define PCI_STATUS                       0x06
#define PCI_REVISION_ID                  0x08
#define PCI_CLASS_CODE                   0x09
#define PCI_CACHE_LINE_SIZE              0x0C
#define PCI_LATENCY_TIMER                0x0D
#define PCI_HEADER_TYPE                  0x0E
#define PCI_BIST                         0x0F
#define PCI_BASE_ADDRESS_0               0x10
#define PCI_BASE_ADDRESS_1               0x14
#define PCI_CAPABILITIES_POINTER         0x34
#define PCI_RESERVED1                    0x35
#define PCI_INTERRUPT_LINE               0x3C
#define PCI_INTERRUPT_PIN                0x3D

// registers unique for type 0 headers

#define PCI_BASE_ADDRESS_2               0x18
#define PCI_BASE_ADDRESS_3               0x1C
#define PCI_BASE_ADDRESS_4               0x20
#define PCI_BASE_ADDRESS_5               0x24
#define PCI_CARDBUS_CIS_PTR              0x28
#define PCI_SUBSYSTEM_VENDOR_ID          0x2C
#define PCI_SUBSYSTEM_ID                 0x2E
#define PCI_EXPANSION_ROM_BASE           0x30
#define PCI_RESERVED2                    0x38
#define PCI_MIN_GNT                      0x3E
#define PCI_MAX_LAT                      0x3F

// registers unique for type 1 headers

#define PCI_PRIMARY_BUS_NUMBER           0x18
#define PCI_SECONDARY_BUS_NUMBER         0x19
#define PCI_SUBORDINATE_BUS_NUMBER       0x1A
#define PCI_SECONDARY_LATENCY_TIMER      0x1B
#define PCI_IO_BASE                      0x1C
#define PCI_IO_LIMIT                     0x1D
#define PCI_SECONDARY_STATUS             0x1E
#define PCI_MEMORY_BASE                  0x20
#define PCI_MEMORY_LIMIT                 0x22
#define PCI_PREFETCHABLE_MEMORY_BASE     0x24
#define PCI_PREFETCHABLE_MEMORY_LIMIT    0x26
#define PCI_PREFETCHABLE_BASE_UPPER_32   0x28
#define PCI_PREFETCHABLE_LIMIT_UPPER_32  0x2C
#define PCI_IO_BASE_UPPER_16             0x30
#define PCI_IO_LIMIT_UPPER_16            0x32
#define PCI_BRIDGE_EXPANSION_ROM_BASE    0x38
#define PCI_BRIDGE_CONTROL               0x3E


#define PCI_TYPE_0_HEADER            0
#define PCI_TYPE_1_HEADER            1
#define PCI_TYPE_2_HEADER            2  // not yet supported


#define IRQ_PIN_A			 0
#define IRQ_PIN_B			 1
#define IRQ_PIN_C			 2
#define IRQ_PIN_D			 3


#if defined(PCI_EXPRESS)
#define CONFIGURATION_SPACE_SIZE    0x1000
#define CONFIGURATION_SPACE_REGS      1024
#else   /* !PCI_EXPRESS */
#define CONFIGURATION_SPACE_SIZE     0x100
#define CONFIGURATION_SPACE_REGS        64
#endif  /* !PCI_EXPRESS */

#define STANDARD_CONFIGURATION_SIZE   0x40

#if !defined(PCI_DEVICE_IN_CC)

#include <simics/devs/pci.h>

#include <simics/utils.h>

typedef struct {
	const char *name;
        int offset;
	int size;
        uint32 mask;
} config_reg_info_t;

typedef struct pci_device {

        log_object_t *log;
        int log_group;

        int bus_address;

        void (*pci_bus_reset)(conf_object_t *obj);
        uint32 (*conf_read_func)(conf_object_t *obj, uint32, uint32);
        void (*conf_write_func)(conf_object_t *obj, uint32, uint32, uint32);
        exception_type_t (*pci_operation)(conf_object_t *, generic_transaction_t *, map_info_t);

        // the configuration header is 64 double words (a 32 bit)
        uint8 config_registers[CONFIGURATION_SPACE_SIZE];

        conf_object_t *rom;
        uint32 rom_size;
        uint32 rom_func;

        int interrupt_pin[4];

        ht_table_t *map_table;
        ht_table_t *user_reg_table;

        conf_object_t         *pci_bus;
        pci_bus_interface_t   pci_bus_interface;
        io_memory_interface_t pci_bus_mem_interface;

#if defined(PCI_EXPRESS)
        int pci_express_on;
        pci_express_interface_t pcie_bus_interface;
#endif   /* PCI_EXPRESS */

        int may_stall;

        /* below are bridge specific only (TYPE1) */
        void (*system_error)(conf_object_t *obj);
        exception_type_t (*access_not_taken)(conf_object_t *obj,
                                             conf_object_t *src_space,
                                             conf_object_t *dst_space,
                                             exception_type_t ex,
                                             generic_transaction_t *mem_op,
                                             map_info_t mapinfo);
        void (*interrupt_raised)(conf_object_t *obj, conf_object_t *dev_obj,
                                 int device, int pin);
        void (*interrupt_lowered)(conf_object_t *obj, conf_object_t *dev_obj,
                                  int device, int pin);

        int forward_io;
        int forward_io32;
        int forward_mem;
        int forward_prefetchable;
        int forward_prefetchable64;

        conf_object_t         *secondary_bus;
        pci_bus_interface_t   secondary_bus_interface;
        io_memory_interface_t secondary_bus_io_memory;

        conf_object_t         *pci_bus_cfg_space;
        conf_object_t         *pci_bus_mem_space;
        conf_object_t         *pci_bus_io_space;

        conf_object_t         *secondary_bus_cfg_space;
        conf_object_t         *secondary_bus_mem_space;
        conf_object_t         *secondary_bus_io_space;

        int io_down_priority;
        int io_down_align_size;
        int io_down_endian;
        int mem_down_priority;
        int mem_down_align_size;
        int mem_down_endian;
        int pref_down_priority;
        int pref_down_align_size;
        int pref_down_endian;
        int io_up_priority;
        int io_up_align_size;
        int io_up_endian;
        int mem_up_priority;
        int mem_up_align_size;
        int mem_up_endian;

        /* created, no checkpointing */
        config_reg_info_t config_reg_info[2][0x40];
} pci_device_t;
#endif   /* !PCI_DEVICE_IN_CC */


#if defined(PCI_DEVICE_IN_C) || defined(PCI_DEVICE_IN_CC)

#include "pci-device-old.h"

#endif /* PCI_DEVICE_IN_C  || PCI_DEVICE_IN_C */


#if !defined(PCI_DEVICE_IN_CC)

uint32 PCI_default_configuration_read_access(conf_object_t *obj, uint32 offset, uint32 size);
void PCI_default_configuration_write_access(conf_object_t *obj, uint32 offset, uint32 size, uint32 value);

void
PCI_device_init(log_object_t *log, int log_group,
                pci_device_t *pci_dev,
                pci_device_t *(*unused)(conf_object_t *), /* call with NULL */
                void (*pci_bus_reset)(conf_object_t *obj),
                uint32 (*conf_read_func)(conf_object_t *obj, uint32 offset, uint32 size),
                void (*conf_write_func)(conf_object_t *obj, uint32 offset, uint32 size, uint32 value),
                exception_type_t (*pci_operation)(conf_object_t *obj, generic_transaction_t *mem_op, map_info_t map_info));

void PCI_add_config_register(pci_device_t *pci, uint32 offset,
                             const char *name, int size, uint32 mask,
                             uint32 initial_value);
void PCI_set_config_register_mask(pci_device_t *pci, uint32 offset, uint32 mask);
uint32 PCI_get_config_register_mask(pci_device_t *pci, uint32 offset);
const char *PCI_config_register_name(pci_device_t *pci, uint32 offset);
uint32 PCI_config_register_size(pci_device_t *pci, uint32 offset);
uint32 PCI_read_sized_config_register(pci_device_t *pci, uint32 offset, uint32 size);
uint32 PCI_read_config_register(pci_device_t *pci, uint32 offset);
void PCI_write_sized_config_register(pci_device_t *pci, uint32 offset, uint32 value, uint32 size);
void PCI_write_config_register(pci_device_t *pci, uint32 offset, uint32 value);

exception_type_t PCI_configuration_access(pci_device_t *pci, generic_transaction_t *trans);

int PCI_get_bus_address(pci_device_t *pci);

void PCI_handle_mapping32(pci_device_t *pci_ptr, int reg, addr_space_t space,
                          uint32 size, int function, int priority,
                          uint64 target_offset,
                          conf_object_t *target,
                          int align_size, int inverse_endian);
void PCI_handle_mapping64(pci_device_t *pci_ptr, int reg,
                          uint64 size, int function, int priority,
                          uint64 target_offset,
                          conf_object_t *target,
                          int align_size, int inverse_endian);

void PCI_set_map_base(pci_device_t *pci, int reg, uint64 base);
void PCI_set_map_size(pci_device_t *pci, int reg, uint64 size);
void PCI_set_map_offset(pci_device_t *pci, int reg, uint64 target_offset);
void PCI_set_map_enable(pci_device_t *pci, int reg, int enable);
void PCI_set_map_ignore_command(pci_device_t *pci, int reg, int map_ignore_command);
void PCI_set_map_always_on(pci_device_t *pci, int reg, int always_on);

uint64 PCI_get_map_base(pci_device_t *pci, int reg);
uint64 PCI_get_map_size(pci_device_t *pci, int reg);
uint64 PCI_get_map_offset(pci_device_t *pci, int reg);
int    PCI_get_map_enable(pci_device_t *pci, int reg);
int    PCI_get_map_ignore_command(pci_device_t *pci, int reg);
int    PCI_get_map_always_on(pci_device_t *pci, int reg);

void PCI_set_may_stall(pci_device_t *pci, int may_stall);
int PCI_get_may_stall(pci_device_t *pci);

void PCI_raise_interrupt(pci_device_t *pci);
void PCI_lower_interrupt(pci_device_t *pci);
void PCI_raise_interrupt_pin(pci_device_t *pci, int pin);
void PCI_lower_interrupt_pin(pci_device_t *pci, int pin);

#if defined(PCI_EXPRESS)
void PCIE_send_message(pci_device_t *pci, pcie_message_type_t type, byte_string_t payload);
#endif

exception_type_t PCI_data_from_memory(pci_device_t *pci, addr_space_t space,
                                      uint8 *buffer, uint64 address, uint64 size);

exception_type_t PCI_data_to_memory(pci_device_t *pci, addr_space_t space,
                                    uint8 *buffer, uint64 address, uint64 size);

uint64 PCI_value_from_memory(pci_device_t *pci, addr_space_t space,
                             exception_type_t *ex,
                             uint64 address, uint32 size);

exception_type_t PCI_value_to_memory(pci_device_t *pci, addr_space_t space,
                                     uint64 value,
                                     uint64 address, uint32 size);

void PCI_system_error(pci_device_t *pci);

void PCI_default_device_reset(conf_object_t *obj);

void PCI_register_device_attributes(conf_class_t *pci_class,
                                    int (*interrupt_ack)(conf_object_t *obj),
                                    void (*special_cycle)(conf_object_t *obj, uint32 value),
                                    void (*system_error)(conf_object_t *obj),
                                    void (*interrupt_raised)(conf_object_t *obj, int pin),
                                    void (*interrupt_lowered)(conf_object_t *obj, int pin));

void PCI_bridge_default_system_error(conf_object_t *obj);

exception_type_t PCI_bridge_default_access_not_taken(conf_object_t *obj,
                                                     conf_object_t *src_space,
                                                     conf_object_t *dst_space,
                                                     exception_type_t ex,
                                                     generic_transaction_t *mem_op,
                                                     map_info_t mapinfo);

void PCI_bridge_init(pci_device_t *pci,
                     void (*system_error)(conf_object_t *obj),
                     exception_type_t (*access_not_taken)(conf_object_t *obj,
                                                          conf_object_t *src_space,
                                                          conf_object_t *dst_space,
                                                          exception_type_t ex,
                                                          generic_transaction_t *mem_op,
                                                          map_info_t mapinfo),
                void (*interrupt_raised)(conf_object_t *obj, conf_object_t *dev_obj,
                                         int device, int pin),
                void (*interrupt_lowered)(conf_object_t *obj, conf_object_t *dev_obj,
                                          int device, int pin),
                     int forward_io, int forward_io32,
                     int forward_mem,
                     int forward_prefetchable, int forward_prefetchable64);

void PCI_bridge_map_setup(pci_device_t *pci,
                          int io_down_priority, int io_down_align_size, int io_down_endian,
                          int mem_down_priority, int mem_down_align_size, int mem_down_endian,
                          int pref_down_priority, int pref_down_align_size, int pref_down_endian,
                          int io_up_priority, int io_up_align_size, int io_up_endian,
                          int mem_up_priority, int mem_up_align_size, int mem_up_endian);

void PCI_register_bridge_attributes(conf_class_t *pci_class);

#endif   /* !PCI_DEVICE_IN_CC */


#if defined(PCI_DEVICE_PRIVATE)
void common_configuration_register_write(pci_device_t *pci, uint32 offset, uint32 size, uint32 value);
void base_address_write(pci_device_t *pci, uint32 offset, uint32 value);

void (*type1_configuration_register_write)(pci_device_t *pci,
                                           uint32 offset, uint32 size,
                                           uint32 value);
void (*type1_reset)(pci_device_t *pci);
void (*get_bridge_bus_info)(pci_device_t *pci);

#endif   /* PCI_DEVICE_PRIVATE */

#endif // PCI_DEVICE_H
