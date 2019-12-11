/*
  pci-device-cc.cc - Generic PCI device in C++


  THIS FILE IS OBSOLETE. DO NOT USE FOR NEW DEVELOPMENT!


  Copyright (C) 2000-2003 Virtutech AB, All Rights Reserved

  This program is a component ("Component") of Virtutech Simics and is
  being distributed under Section 1(a)(iv) of the Virtutech Simics
  Software License Agreement (the "Agreement").  You should have
  received a copy of the Agreement with this Component; if not, please
  write to Virtutech AB, Norrtullsgatan 15, 1tr, SE-113 27 STOCKHOLM,
  Sweden for a copy of the Agreement prior to using this Component.

  By using this Component, you agree to be bound by all of the terms of
  the Agreement.  If you do not agree to the terms of the Agreement, you
  may not use, copy or otherwise access the Component or any derivatives
  thereof.  You may create and use derivative works of this Component
  pursuant to the terms the Agreement provided that any such derivative
  works may only be used in conjunction with and as a part of Virtutech
  Simics for use by an authorized licensee of Virtutech.

  THIS COMPONENT AND ANY DERIVATIVES THEREOF ARE PROVIDED ON AN "AS IS"
  BASIS.  VIRTUTECH MAKES NO WARRANTIES WITH RESPECT TO THE COMPONENT OR
  ANY DERIVATIVES THEREOF AND DISCLAIMS ALL IMPLIED WARRANTIES,
  INCLUDING, WITHOUT LIMITATION, WARRANTIES OF MERCHANTABILITY AND
  FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.

*/

#include <stdio.h>
#include <string.h>
#ifdef HAVE_SYS_TYPES_H
#include <sys/types.h>
#endif
#ifdef HAVE_SYS_STAT_H
#include <sys/stat.h>
#endif
#ifdef HAVE_FCNTL_H
#include <fcntl.h>
#endif
#ifdef HAVE_UNISTD_H
#include <unistd.h>
#endif

extern "C" {
#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>
}

#define PCI_DEVICE_IN_CC
#include "pci-device.h"
#include <simics/devs/pci.h>

#ifndef DEVICE_NAME
#define DEVICE_NAME "pci-device"
#endif

/* TODO: move to Simics */
#if defined(HOST_BIG_ENDIAN)
static uint16
htols(uint16 in)
{
	return (in << 8) | (in >> 8);
}

static uint32
htoll(uint32 in)
{
	return (htols((uint16)in)  << 16) | htols(in >> 16);
}
#else
#define htoll(x) (x)
#endif

#define ltohl htoll






// constructor
pci_device::pci_device(uint32 a_type)
{
	header_type = a_type;
}

pci_device::~pci_device()
{
}

pci_device *
pci_device::from_conf_obj(conf_object_t *conf) 
{
	return static_cast<pci_device *>((log_object_t *)conf);
}





uint32
pci_device::configuration_read_access(uint32 an_offset, uint32 a_size)
{
	// this means that we default can read almost any register
	return read_config_register(an_offset, a_size);
}


exception_type_t
pci_device::configuration_write_access(uint32 an_offset, uint32 a_size, uint32 a_value)
{
	switch (an_offset) {
	case PCI_COMMAND:
	case PCI_STATUS:
	case PCI_CACHE_LINE_SIZE:
	case PCI_LATENCY_TIMER:
	case PCI_BIST:
	case PCI_INTERRUPT_LINE:
		write_config_register(an_offset, a_value, a_size);
		break;
	}
	return Sim_PE_No_Exception;
}


void
pci_device::map_pci_space(addr_space_t a_space_type, uint64 a_base, uint64 a_length, int a_function)
{
	// this is the case when 0xFFFFFFFF is written to the base register, or the register is cleared
        /* This isn't correct at all, use the c-based device instead!
           Comparing with 4 is to accept the 2-byte offset in pci-ide.cc */
	if(a_base == ~(a_length - 1) || a_base < 4)
		return;

	// remove any previous mapping
	its_pci_bus_interface->remove_map(its_pci_bus, this->conf_obj(), a_space_type, a_function);
	
	// add this new mapping
	map_info_t info;
	memset(&info, 0, sizeof(map_info_t));
	info.base = a_base;
	info.start = 0;
	info.length = a_length;
	info.function = a_function;
	its_pci_bus_interface->add_map(its_pci_bus, this->conf_obj(), a_space_type, 0, info);
	debug_log(1, this, "New %s space mapping (function %d): "
                  "base = 0x%llx, length = 0x%llx",
		  a_space_type == Sim_Addr_Space_IO ? "i/o" : "memory",
                  a_function, a_base, a_length);
	
}


// access to configuration space
exception_type_t
pci_device::configuration_access(generic_transaction_t *a_transaction)
{
	// bus, device, function, and register are encoded in the physical address
#if 0
	uint8 bus      = a_transaction->physical_address >> 16 & 0xFF;
	uint8 device   = a_transaction->physical_address >> 11 & 0x1F;
	uint8 function = a_transaction->physical_address >>  8 & 0x07;
#endif
	uint8 reg = a_transaction->physical_address & 0xFF;

	int size = a_transaction->size;
        unsigned int offset = reg;
	
#if 0
	pr("configuration_access: bus %d, dev %d, fnc %d, reg %d\n",
           (int)bus, (int)device, (int)function, (int)reg);
#endif

	if (SIM_mem_op_is_read(a_transaction)) {
		uint64 value = 0;
		unsigned int i = 0;
		while(size > 0) {
			int s;
			if(valid_config_register(offset))
				s = config_register_size(offset);
			else
				s = size;
			/*ASSERT(size >= s);*/
			value |= uint64(configuration_read_access(offset, s)) << i;

			debug_log(1, this, "read config register: offset 0x%x, size 0x%x, value 0x%x",
				  (int)offset, (int)a_transaction->size, (int)value);

			offset += s;
			size -= s;
			i += s << 3;
		}
		SIM_set_mem_op_value_le(a_transaction, value);
	} else {
		uint64 value = SIM_get_mem_op_value_le(a_transaction);
		while(size > 0) {
                        uint64 val_part;
			int s, bits;
			if(valid_config_register(offset))
				s = config_register_size(offset);
			else
				s = size;
			/*ASSERT(size >= s);*/
                        bits = s << 3;
                        val_part = value & ((UINT64_C(1) << bits) - 1);
			value >>= bits;

                        debug_log(1, this, "write config register: offset 0x%x, size 0x%x, value 0x%x",
                                  (int)offset, (int)s, (int)val_part);

		        configuration_write_access(offset, s, val_part);
			offset += s;
			size -= s;
		}
        }
	return Sim_PE_No_Exception;

}

// callback from an interrupt acknowledgement cycle on the pci bus
extern "C" {

static int
pci_device_interrupt_acknowledge_callback(conf_object_t *an_object)
{
	pci_device *the_device = pci_device::from_conf_obj(an_object);

	// call virtual function in device instance
	return the_device->interrupt_acknowledge();
}

}

// return interrupt vector in response to an acknowledgement bus cycle
int
pci_device::interrupt_acknowledge(void)
{
	// return -1 (none) by default (subclass can override this)
	return -1;
} 

// raise interrupt on the pci bus
void
pci_device::raise_pci_interrupt(unsigned int a_pin)
{
	(its_pci_bus_interface->raise_interrupt)(its_pci_bus, this->conf_obj(), a_pin);
}

// lower interrupt on the pci bus
void
pci_device::lower_pci_interrupt(unsigned int a_pin)
{
	(its_pci_bus_interface->lower_interrupt)(its_pci_bus, this->conf_obj(), a_pin);
}

// map method
extern "C" {
static int
pci_device_map(conf_object_t *dev, addr_space_t space, map_info_t info)
{
        return 0;
}

// i/o and memory operation (configuration is handled in a separate callback)
static exception_type_t
pci_device_operation_callback(conf_object_t *an_object, generic_transaction_t *a_transaction, map_info_t a_mapping)
{
        pci_device *the_device = pci_device::from_conf_obj(an_object);

        if (a_mapping.function == 0xff)
                return the_device->configuration_access(a_transaction);
        else
                return the_device->operation(a_transaction, a_mapping);
}
} // extern "C"

// i/o or memory operation
exception_type_t
pci_device::operation(generic_transaction_t *a_transaction, map_info_t a_mapping)
{
        debug_err(this, "pci_device::operation called");
        return Sim_PE_No_Exception;
}

exception_type_t
pci_device::read_from_memory(void *a_buffer, uint64 an_address, uint64 a_size)
{
	generic_transaction_t transaction;
	memset(&transaction, 0, sizeof(generic_transaction_t));

	transaction.physical_address = an_address;
        SIM_set_mem_op_type(&transaction, Sim_Trans_Load);
	transaction.size = a_size;
	transaction.block_STC = 1;
	transaction.may_stall = 0;

        transaction.ini_type = Sim_Initiator_Device;
        transaction.ini_ptr = &obj;
        transaction.real_address = (char *)a_buffer;

	map_info_t mapinfo;
	memset(&mapinfo, 0, sizeof(map_info_t));
	mapinfo.function = 2; // memory space
	return its_pci_bus_mem_interface->operation(its_pci_bus, &transaction, mapinfo);
}

exception_type_t
pci_device::write_to_memory(void *a_buffer, uint64 an_address, uint64 a_size)
{
	generic_transaction_t transaction;
	memset(&transaction, 0, sizeof(generic_transaction_t));

	transaction.physical_address = an_address;
        SIM_set_mem_op_type(&transaction, Sim_Trans_Store);
	transaction.size = a_size;
	transaction.block_STC = 1;
	transaction.may_stall = 0;

	map_info_t mapinfo;
	memset(&mapinfo, 0, sizeof(map_info_t));
	mapinfo.function = 2; // memory space

        transaction.ini_type = Sim_Initiator_Device;
        transaction.ini_ptr = &obj;
        transaction.real_address = (char *)a_buffer;        

	return its_pci_bus_mem_interface->operation(its_pci_bus, &transaction, mapinfo);
}

// set the pci bus attribute
set_error_t
pci_device::set_pci_bus(void *dont_care, conf_object_t *an_object, attr_value_t *a_value, attr_value_t *idx)
{
	pci_device *the_pci_device = pci_device::from_conf_obj(an_object);

	if (a_value->kind != Sim_Val_Object)
                return Sim_Set_Need_Object;
	
	conf_object_t *the_object = a_value->u.object;
	pci_bus_interface_t *the_interface =
		(pci_bus_interface_t *)SIM_get_interface(the_object,
							 "pci-bus");
	if(!the_interface)
		return Sim_Set_Interface_Not_Found;
	
	the_pci_device->its_pci_bus = the_object;
	the_pci_device->its_pci_bus_interface = the_interface;

	io_memory_interface_t *the_memory_interface =
		(io_memory_interface_t *)SIM_get_interface(the_object,
							   "io-memory");
	if (!the_memory_interface)
		return Sim_Set_Interface_Not_Found;
	the_pci_device->its_pci_bus_mem_interface = the_memory_interface;

	return Sim_Set_Ok;
}

// get the pci bus attribute
attr_value_t
pci_device::get_pci_bus(void *dont_care, conf_object_t *the_object, attr_value_t *idx)
{
        attr_value_t the_value;
        pci_device *the_pci_device = pci_device::from_conf_obj(the_object);

        if (the_pci_device->its_pci_bus) {
                the_value.kind = Sim_Val_Object;
                the_value.u.object = the_pci_device->its_pci_bus;
        }
	else
                the_value.kind = Sim_Val_Invalid;
     
        return the_value;
}


set_error_t
pci_device::set_config_registers(void *dont_care, conf_object_t *an_object, attr_value_t *a_value, attr_value_t *idx)
{
	pci_device *the_pci_device = pci_device::from_conf_obj(an_object);

	uint32 *the_config_registers = (uint32*)the_pci_device->config_registers;

        if (idx->kind == Sim_Val_Nil) {
                if(a_value->kind != Sim_Val_List)
                        return Sim_Set_Need_List;

                if(a_value->u.list.size != CONFIGURATION_SPACE_SIZE / 4)
                        return Sim_Set_Illegal_Value;

                for(int i = 0; i < CONFIGURATION_SPACE_SIZE / 4; i++) {

                        if(a_value->u.list.vector[i].kind != Sim_Val_Integer)
                                return Sim_Set_Illegal_Value;

                        the_config_registers[i] = htoll(a_value->u.list.vector[i].u.integer);
                }
        } else if (idx->kind == Sim_Val_Integer
                   && idx->u.integer >= 0
                   && idx->u.integer < CONFIGURATION_SPACE_SIZE/4) {
                the_config_registers[idx->u.integer] = htoll(a_value->u.integer);
        } else {
                return Sim_Set_Illegal_Value;
        }

        return Sim_Set_Ok;
}

// get the pci bus attribute
attr_value_t
pci_device::get_config_registers(void *dont_care, conf_object_t *the_object, attr_value_t *idx)
{
        attr_value_t the_value;
        pci_device *the_pci_device = pci_device::from_conf_obj(the_object);
	uint32 *the_config_registers = (uint32*)the_pci_device->config_registers;

        if (idx->kind == Sim_Val_Nil) {
                the_value.kind = Sim_Val_List;
                the_value.u.list.size = CONFIGURATION_SPACE_SIZE / 4;
                the_value.u.list.vector = MM_ZALLOC(CONFIGURATION_SPACE_SIZE / 4, attr_value_t);
        
                for(int i = 0; i < CONFIGURATION_SPACE_SIZE / 4; i++) {

                        the_value.u.list.vector[i].kind = Sim_Val_Integer;
                        the_value.u.list.vector[i].u.integer = ltohl(the_config_registers[i]);
                }
        } else if (idx->kind == Sim_Val_Integer
                   && idx->u.integer >= 0
                   && idx->u.integer < CONFIGURATION_SPACE_SIZE/4) {
                the_value.kind = Sim_Val_Integer;
                the_value.u.integer = ltohl(the_config_registers[idx->u.integer]);
        } else {
                the_value.kind = Sim_Val_Invalid;
        }
        return the_value;
}



extern "C" {


static set_error_t
pci_device_set_pci_bus(void *dont_care, conf_object_t *an_object, attr_value_t *a_value, attr_value_t *idx)
{
        return pci_device::set_pci_bus(dont_care, an_object, a_value, idx);
}

static attr_value_t
pci_device_get_pci_bus(void *dont_care, conf_object_t *the_object, attr_value_t *idx)
{
        return pci_device::get_pci_bus(dont_care, the_object, idx);
}

static attr_value_t
pci_device_get_config_registers(void *dont_care, conf_object_t *the_object, attr_value_t *idx)
{
        return pci_device::get_config_registers(dont_care, the_object, idx);
}

static set_error_t
pci_device_set_config_registers(void *dont_care, conf_object_t *an_object, attr_value_t *a_value, attr_value_t *idx)
{
        return pci_device::set_config_registers(dont_care, an_object, a_value, idx);
}

} // extern "C"


// generic initialization of all pci-device classes
void
pci_device::init_class(conf_class_t *a_class)
{
	pci_device_interface_t *the_interface = MM_ZALLOC(1, pci_device_interface_t);
	the_interface->interrupt_acknowledge = pci_device_interrupt_acknowledge_callback;
	SIM_register_interface(a_class, "pci-device", the_interface);

	// register the io memory interface
	io_memory_interface_t *the_io_memory_interface = MM_ZALLOC(1, io_memory_interface_t);
	the_io_memory_interface->map = pci_device_map;
        the_io_memory_interface->operation = pci_device_operation_callback;
	SIM_register_interface(a_class, "io-memory", the_io_memory_interface);

        // attributes
	SIM_register_attribute(a_class, "pci_bus",
			       pci_device_get_pci_bus, 0,
			       pci_device_set_pci_bus, 0, Sim_Attr_Required,
			       "The PCI bus this device is connected to,"
			       " implementing the <tt>pci-bus</tt>"
			       " interface.");
	SIM_register_attribute(a_class, "config-registers",
			       pci_device_get_config_registers, 0,
			       pci_device_set_config_registers, 0, (attr_attr_t)(Sim_Attr_Optional | Sim_Attr_Integer_Indexed),
			       "The 64 PCI configuration registers, each"
			       " 32 bits in size, in the byte order of the"
			       " target machine.");

}

void *
pci_device::operator new(size_t a_size)
{
        /* virtual base class shouldn't be allocated */
        ASSERT(0);
        exit(1);
        return (void *)0xdeadbeef;
}




static struct {

	char          name[30];           // register name
	unsigned int  offset;             // register offset
	unsigned int  size;               // register size
	unsigned int  its_default_value;  // default value
	unsigned int  header_type;

} config_register_info[NUMBER_OF_CONFIG_REGISTERS] = {
	
	// generic registers found in all headers

	{ "vendor_id",                   0x00, 2, 0x0000,     (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "device_id",                   0x02, 2, 0x0000,     (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "command",                     0x04, 2, 0x0000,     (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "status",                      0x06, 2, 0x0000,     (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "revision_id",                 0x08, 1, 0x00,       (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "class_code",                  0x09, 3, 0x000000,   (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "cache_line_size",             0x0C, 1, 0x00,       (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "latency_timer",               0x0D, 1, 0x00,       (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "header_type",                 0x0E, 1, 0x00,       (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "bist",                        0x0F, 1, 0x00,       (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "base_address_0",              0x10, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "base_address_1",              0x14, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "capabilities_ptr",            0x34, 1, 0x00,       (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "reserved",                    0x35, 3, 0x000000,   (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "interrupt_line",              0x3C, 1, 0x00,       (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },
	{ "interrupt_pin",               0x3D, 1, 0x00,       (1 << PCI_TYPE_0_HEADER) | (1 << PCI_TYPE_1_HEADER) },

	// registers unique for type 0 headers

	{ "base_address_2",              0x18, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER)                     },
	{ "base_address_3",              0x1C, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER)                     },
	{ "base_address_4",              0x20, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER)                     },
	{ "base_address_5",              0x24, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER)                     },
	{ "cardbus_cis_ptr",             0x28, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER)                     },
	{ "subsystem_vendor_id",         0x2C, 2, 0x0000,     (1 << PCI_TYPE_0_HEADER)                     },
	{ "subsystem_id",                0x2E, 2, 0x0000,     (1 << PCI_TYPE_0_HEADER)                     },
	{ "expansion_rom_base",          0x30, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER)                     },
	{ "reserved",                    0x38, 4, 0x00000000, (1 << PCI_TYPE_0_HEADER)                     },
	{ "min_gnt",                     0x3E, 1, 0x00,       (1 << PCI_TYPE_0_HEADER)                     },
	{ "max_lat",                     0x3F, 1, 0x00,       (1 << PCI_TYPE_0_HEADER)                     },

	// registers unique for type 1 headers

	{ "primary_bus_number",          0x18, 1, 0x00,       (1 << PCI_TYPE_1_HEADER)                     },
	{ "secondary_bus_number",        0x19, 1, 0x00,       (1 << PCI_TYPE_1_HEADER)                     },
	{ "subordinate_bus_number",      0x1A, 1, 0x00,       (1 << PCI_TYPE_1_HEADER)                     },
	{ "secondary_latency_timer",     0x1B, 1, 0x00,       (1 << PCI_TYPE_1_HEADER)                     },
	{ "io_base",                     0x1C, 1, 0x00,       (1 << PCI_TYPE_1_HEADER)                     },
	{ "io_limit",                    0x1D, 1, 0x00,       (1 << PCI_TYPE_1_HEADER)                     },
	{ "secondary_status",            0x1E, 2, 0x0000,     (1 << PCI_TYPE_1_HEADER)                     },
	{ "memory_base",                 0x20, 2, 0x0000,     (1 << PCI_TYPE_1_HEADER)                     },
	{ "memory_limit",                0x22, 2, 0x0000,     (1 << PCI_TYPE_1_HEADER)                     },
	{ "prefetchable_memory_base",    0x24, 2, 0x0000,     (1 << PCI_TYPE_1_HEADER)                     },
	{ "prefetchable_memory_limit",   0x26, 2, 0x0000,     (1 << PCI_TYPE_1_HEADER)                     },
	{ "prefetchable_base_upper_32",  0x28, 4, 0x00000000, (1 << PCI_TYPE_1_HEADER)                     },
	{ "prefetchable_limit_upper_32", 0x2C, 4, 0x00000000, (1 << PCI_TYPE_1_HEADER)                     },
	{ "io_base_upper_16",            0x30, 2, 0x0000,     (1 << PCI_TYPE_1_HEADER)                     },
	{ "io_limit_upper_16",           0x32, 2, 0x0000,     (1 << PCI_TYPE_1_HEADER)                     },
	{ "expansion_rom_base",          0x38, 4, 0x00000000, (1 << PCI_TYPE_1_HEADER)                     },
	{ "bridge_control",              0x3E, 2, 0x0000,     (1 << PCI_TYPE_1_HEADER)                     }

};



uint32
pci_device::read_config_register(uint32 an_offset)
{
	uint32 a_size;

	ASSERT(an_offset < CONFIGURATION_SPACE_SIZE);

	ASSERT(valid_config_register(an_offset));
	
	a_size = config_register_size(an_offset);

	return read_config_register(an_offset, a_size);
}


uint32
pci_device::read_config_register(uint32 an_offset, uint32 a_size)
{
	uint32 a_value = 0;
	
	ASSERT(an_offset < CONFIGURATION_SPACE_SIZE);

	switch(a_size) {
	case 1:
		return config_registers[an_offset];
	case 2:
		memcpy((char *)&a_value, &config_registers[an_offset], 2);
		return ltohl(a_value);
	case 3:
		memcpy((char *)&a_value, &config_registers[an_offset], 3);
		return ltohl(a_value);
	case 4:
		memcpy((char *)&a_value, &config_registers[an_offset], 4);
		return ltohl(a_value);
	}	       
	
	// should never return
	ASSERT(0);

	// will get a warning otherwise
	return 0;
}




void
pci_device::write_config_register(uint32 an_offset, uint32 a_value)
{
	uint32 a_size;
	ASSERT(an_offset < CONFIGURATION_SPACE_SIZE);
	ASSERT(valid_config_register(an_offset));
	a_size = config_register_size(an_offset);
	
	write_config_register(an_offset, a_value, a_size);
}

void
pci_device::write_config_register(uint32 an_offset, uint32 a_value, uint32 a_size)
{
	ASSERT(an_offset < CONFIGURATION_SPACE_SIZE);

	switch(a_size) {
	case 1:
		config_registers[an_offset] = a_value;
		break;
	case 2:
		a_value = htoll(a_value);
		memcpy(&config_registers[an_offset], (char *)&a_value, 2);
		break;
	case 3:
		a_value = htoll(a_value);
		memcpy(&config_registers[an_offset], (char *)&a_value, 3);
		break;
	case 4:
		a_value = htoll(a_value);
		memcpy(&config_registers[an_offset], (char *)&a_value, 4);
		break;
	default:
		ASSERT(0);
	}	       

}


bool
pci_device::valid_config_register(uint32 an_offset)
{
	ASSERT(an_offset < CONFIGURATION_SPACE_SIZE);

	for(unsigned int i = 0; i < NUMBER_OF_CONFIG_REGISTERS; i++)
		if((config_register_info[i].offset == an_offset) &&
		   (config_register_info[i].header_type & (1 << header_type)))
			return true;
	return false;
}

const char*
pci_device::config_register_name(uint32 an_offset)
{
	for(unsigned int i = 0; i < NUMBER_OF_CONFIG_REGISTERS; i++)
		if((config_register_info[i].offset == an_offset) &&
		   (config_register_info[i].header_type & (1 << header_type)))
			return config_register_info[i].name;

	return 0;
}

uint32
pci_device::config_register_size(uint32 an_offset)
{
	for(unsigned int i = 0; i < NUMBER_OF_CONFIG_REGISTERS; i++)
		if((config_register_info[i].offset == an_offset) &&
		   (config_register_info[i].header_type & (1 << header_type)))
			return config_register_info[i].size;

	return 0;
}
