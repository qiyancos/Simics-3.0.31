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

#ifndef PCI_DEVICE_OLD_H
#define PCI_DEVICE_OLD_H

#ifdef __cplusplus
extern "C" {
#endif
#include <simics/devs/pci.h>
#ifdef __cplusplus
};
#endif

#define NUMBER_OF_CONFIG_REGISTERS 44

#if defined(PCI_DEVICE_IN_C)

typedef uint32 (*conf_read_func_t)(conf_object_t *obj, uint32 offset, uint32 size);
typedef exception_type_t (*conf_write_func_t)(conf_object_t *obj, uint32 offset, uint32 size, uint32 value);
typedef int (*pci_irq_ack_t)(conf_object_t *obj);
typedef exception_type_t (*pci_operation_t)(conf_object_t *, generic_transaction_t *, map_info_t);

uint32 default_configuration_read_access(conf_object_t *obj, uint32 offset, uint32 size);
exception_type_t default_configuration_write_access(conf_object_t *obj, uint32 offset, uint32 size, uint32 value);

/* Functions implemented by pci_device, should be called from sub class */
void pci_device_init(log_object_t *log,
                     pci_device_t *pci_ptr,
                     uint32 header_type,
                     conf_read_func_t conf_read_func,   /* may be NULL */
                     conf_write_func_t conf_write_func, /* may be NULL */
                     pci_irq_ack_t pci_irq_ack,         /* may be NULL */
                     pci_operation_t pci_operation);    /* may NOT be NULL */

void map_pci_space(pci_device_t *pci_dev, addr_space_t space_type, uint32 base, uint32 length, int function);
void raise_pci_interrupt(pci_device_t *pci_dev, int pin);
void lower_pci_interrupt(pci_device_t *pci_dev, int pin);

void write_sized_config_register(pci_device_t *pci_dev, uint32 offset, uint32 value, uint32 size);
void write_config_register(pci_device_t *pci_dev, uint32 offset, uint32 value);
uint32 read_config_register(pci_device_t *pci_dev, uint32 offset);
uint32 read_sized_config_register(pci_device_t *pci_dev, uint32 offset, uint32 size);

exception_type_t read_from_memory(pci_device_t *pci_dev, void *buffer, uint64 address, uint64 size);
exception_type_t write_to_memory(pci_device_t *pci_dev, void *buffer, uint64 address, uint64 size);

void register_pci_device_attributes(conf_class_t *pci_class);

void handle_pci_mapping(pci_device_t *pci_ptr, int reg, addr_space_t space, uint32 size, int function);
void handle_pci_mapping64(pci_device_t *pci_ptr, int reg, uint64 size, int function);

/* Function implemented in sub-class, is called from pci_device */
pci_device_t *get_pci_device_ptr(conf_object_t *obj);

#if defined(PCI_EXPRESS)
exception_type_t configuration_access(pci_device_t *pci_dev, generic_transaction_t *trans, int pcie_conf);
#else   /* !PCI_EXPRESS */
exception_type_t configuration_access(pci_device_t *pci_dev, generic_transaction_t *trans);
#endif  /* !PCI_EXPRESS */

#else /* !defined(PCI_DEVICE_IN_C) */

#ifndef __cplusplus
#error "Needs to be compiled with C++"
#endif

class pci_device : public log_object_t {

 protected:

        // the configuration space is 64 double words (a 32 bit)
        uint8 config_registers[CONFIGURATION_SPACE_SIZE];
        
        uint32 header_type;

 public:
        
        uint32      read_config_register (uint32 an_offset, uint32 a_size);
        uint32      read_config_register (uint32 an_offset);
        void        write_config_register(uint32 an_offset, uint32 a_value, uint32 a_size);
        void        write_config_register(uint32 an_offset, uint32 a_value);
        bool        valid_config_register(uint32 an_offset);
        const char* config_register_name (uint32 an_offset);
        uint32      config_register_size (uint32 an_offset);


        virtual uint32 configuration_read_access(uint32 an_offset, uint32 a_size);
        virtual exception_type_t configuration_write_access(uint32 an_offset, uint32 a_size,  uint32 a_value);


  
        void map_pci_space(addr_space_t a_space_type, uint64 a_base, uint64 a_length, int a_function); 


        conf_object_t         *its_pci_bus;
        pci_bus_interface_t   *its_pci_bus_interface;
        io_memory_interface_t *its_pci_bus_mem_interface;

 public:

        pci_device(uint32 a_type);
        virtual ~pci_device();

        // configuration
        virtual exception_type_t configuration_access(generic_transaction_t *);
        uint32 get_config_dword(int reg);

        // i/o and memory operations
        virtual exception_type_t operation(generic_transaction_t *, map_info_t);

        // interrupt acknowledgement
        virtual int interrupt_acknowledge(void);

        // interrupt requests
        virtual void raise_pci_interrupt(unsigned int a_pin);
        virtual void lower_pci_interrupt(unsigned int a_pin);
        
        // set and get the pci bus attribute
        static set_error_t set_pci_bus(void *dont_care, conf_object_t *an_object, attr_value_t *a_value, attr_value_t *idx);
        static attr_value_t get_pci_bus(void *dont_care, conf_object_t *the_object, attr_value_t *idx);

        static set_error_t set_config_registers(void *, conf_object_t *, attr_value_t *, attr_value_t *idx);
        static attr_value_t get_config_registers(void *, conf_object_t *, attr_value_t *idx);

        exception_type_t read_from_memory(void *a_buffer, uint64 an_address, uint64 a_size);
        exception_type_t write_to_memory(void *a_buffer, uint64 an_address, uint64 a_size);

        // init the pci class
        static void  init_class(conf_class_t *a_class);
      
        // overloading the new operator in order to use vtmem
        void *operator new(size_t);

        conf_object_t *conf_obj(void) { return &obj; };

        static pci_device *from_conf_obj(conf_object_t *conf);
};

#endif /* !defined(PCI_DEVICE_IN_C) */

#endif // PCI_DEVICE_OLD_H
