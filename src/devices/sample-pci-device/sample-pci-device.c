/*
  sample-pci-device.c - sample code for a Simics PCI device

  Copyright 2001-2007 Virtutech AB
  
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

#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <assert.h>
#include <stdlib.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

#include <simics/devs/interrupt.h>

/* pci-device is the superclass of the sample-pci-device class */
#include "pci-device.h"

#define IO_SPACE_SIZE 256UL
#define MEMORY_SPACE_SIZE 65536UL

#define IO_SPACE_MAPPING     1
#define MEMORY_SPACE_MAPPING 2


typedef struct sample_device {

        log_object_t log;
        pci_device_t pci;

	int dummy_attribute;

} sample_device_t;


static exception_type_t
sample_operation(conf_object_t *obj, generic_transaction_t *mem_op, map_info_t info)
{
        sample_device_t *sample = (sample_device_t *)obj;
        int offset = mem_op->physical_address - info.base + info.start;
        
	switch(info.function) {
		
	case IO_SPACE_MAPPING:
                /* handle access to io space here */
                
                /* Some dummy code demonstrating the use of interrupts */
                if (SIM_mem_op_is_write(mem_op)) {
                        if (offset == 4)
                                PCI_raise_interrupt(&sample->pci);
                        else if (offset == 8)
                                PCI_lower_interrupt(&sample->pci);
                }
                break;
                
	case MEMORY_SPACE_MAPPING:
                /* handle access to memory space here */
		break;
                
	default:
		SIM_log_error(&sample->log, 0, "access to unknown pci space");
	}
        
	return Sim_PE_No_Exception;
}


static conf_object_t *
new_instance(parse_object_t *parse_obj)
{
	/* create a new instance of this sample device */
        sample_device_t *sample = MM_ZALLOC(1, sample_device_t);

	/* initialize the log_object part of this instance */
	SIM_log_constructor(&sample->log, parse_obj);

	/* initialize the pci-device part of this instance */
        PCI_device_init(&sample->log, 0,
                        &sample->pci,
                        NULL,
                        NULL, /* pci bus reset */
                        NULL, /* configuration_read_access - use default */
                        NULL, /* configuration_write_access - use default */
                        sample_operation);

        /* initialize pci registers to some default values */
	PCI_write_config_register(&sample->pci, PCI_DEVICE_ID,       0x1234);
	PCI_write_config_register(&sample->pci, PCI_VENDOR_ID,       0x5678);
	PCI_write_config_register(&sample->pci, PCI_STATUS,          0x0000);
	PCI_write_config_register(&sample->pci, PCI_COMMAND,         0x0000);
	PCI_write_config_register(&sample->pci, PCI_CLASS_CODE,      0x000000);
	PCI_write_config_register(&sample->pci, PCI_REVISION_ID,     0x00);
	PCI_write_config_register(&sample->pci, PCI_HEADER_TYPE,     0x00);
	PCI_write_config_register(&sample->pci, PCI_INTERRUPT_PIN,   0x01 + IRQ_PIN_A);
	PCI_write_config_register(&sample->pci, PCI_BASE_ADDRESS_0,  0x00000001);
	PCI_write_config_register(&sample->pci, PCI_BASE_ADDRESS_1,  0x00000000);

        PCI_handle_mapping32(&sample->pci,
                             PCI_BASE_ADDRESS_0, Sim_Addr_Space_IO,
                             IO_SPACE_SIZE, IO_SPACE_MAPPING, 0,
                             0x0, NULL, 0, 0);

        PCI_handle_mapping32(&sample->pci,
                             PCI_BASE_ADDRESS_1, Sim_Addr_Space_Memory,
                             MEMORY_SPACE_SIZE, MEMORY_SPACE_MAPPING, 0,
                             0x0, NULL, 0, 0);

	/* initialize the dummy attribute of this instance */
	sample->dummy_attribute = 0x123456;

	return &sample->log.obj;
}


static set_error_t
set_dummy_attribute(void *dont_care, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        sample_device_t *sample = (sample_device_t *)obj;

	/* update the attribute of the given device */
	sample->dummy_attribute = val->u.integer;

	/* everything went just great */
        return Sim_Set_Ok;
}


static attr_value_t
get_dummy_attribute(void *dont_care, conf_object_t *obj, attr_value_t *idx)
{
        sample_device_t *sample = (sample_device_t *)obj;
	return SIM_make_attr_integer(sample->dummy_attribute);
}


void
init_local(void)
{
	class_data_t funcs;
	conf_class_t *sample_class;
        
	/* 
         * fill out the class_data_t structure - we must supply a
         * callback for creation of new instances of this device.
         */
        memset(&funcs, 0, sizeof funcs);
	funcs.new_instance = new_instance;
        funcs.description =
                "This is the sample-pci-device class which is an example of "
                "how to write PCI devices in Simics.";

	/* Register the class of this device. */
	sample_class = SIM_register_class(DEVICE_NAME, &funcs);

	/* init the pci_device superclass */
        PCI_register_device_attributes(sample_class, NULL, NULL, NULL, NULL, NULL);

	SIM_register_typed_attribute(sample_class, "dummy-attribute",
                                     get_dummy_attribute, 0,
                                     set_dummy_attribute, 0,
                                     Sim_Attr_Required,
                                     "i", NULL,
                                     "this attribute represents...");
}
