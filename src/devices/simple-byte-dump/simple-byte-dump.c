/*
  simple-byte-dump.c

  Copyright 1998-2007 Virtutech AB
  
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

#include <stdio.h>
#include <fcntl.h>
#include <ctype.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

#define DEVICE_NAME "simple-byte-dump"

typedef struct simple_byte_dump_device {
        log_object_t log;
	const char *filename;
	int fd;
} byte_dump_device_t;


static conf_object_t *
new_instance(parse_object_t *parse_obj)
{
        byte_dump_device_t *bdd = MM_ZALLOC(1, byte_dump_device_t);
        SIM_log_constructor(&bdd->log, parse_obj);
	bdd->fd = -1;
        return &bdd->log.obj;
}

static exception_type_t
operation(conf_object_t *obj, generic_transaction_t *mop, map_info_t info)
{
        byte_dump_device_t *bdd = (byte_dump_device_t *)obj;
        int offset = mop->physical_address + info.start - info.base;

        if (SIM_mem_op_is_read(mop)) {

                if (mop->inquiry)
                        return Sim_PE_Inquiry_Unhandled;

                SIM_log_error(&bdd->log, 0,"Only write accesses allowed.");
                SIM_set_mem_op_value_le(mop, 0);
        } else {
		uint8 value = SIM_get_mem_op_value_le(mop);

                if (mop->size != 1) {
                        SIM_log_error(&bdd->log, 0,
                                      "Only byte accesses allowed.");
                }

		SIM_log_info(2, &bdd->log, 0,
			     "Write to offset %d, value 0x%x: '%c'",
                             offset, value,
                             isprint(value) ? value : ' ');

		if (bdd->fd >= 0)
			write(bdd->fd, &value, 1);
        }
        return Sim_PE_No_Exception;
}

static set_error_t
set_filename(void *arg, conf_object_t *obj,
             attr_value_t *val, attr_value_t *idx)
{
        byte_dump_device_t *bdd = (byte_dump_device_t *)obj;
	int fd = open(val->u.string, O_CREAT | O_RDWR | O_BINARY, 0666);

        if (fd < 0) {
                SIM_frontend_exception(SimExc_General, "Failed opening file");
		return Sim_Set_Illegal_Value;
        }

        if (bdd->filename) {
                close(bdd->fd);
                MM_FREE((char *)bdd->filename);
        }

	bdd->fd = fd;
	bdd->filename = MM_STRDUP(val->u.string);
        return Sim_Set_Ok;
}

static attr_value_t
get_filename(void *arg, conf_object_t *obj, attr_value_t *idx)
{
        byte_dump_device_t *bdd = (byte_dump_device_t *)obj;
        return SIM_make_attr_string(bdd->filename);
}

DLL_EXPORT void
init_local(void)
{
        class_data_t funcs;
        conf_class_t *class;
        io_memory_interface_t *memory_interface;

        memset(&funcs, 0, sizeof(class_data_t));
        funcs.new_instance = new_instance;
        funcs.description =
                DEVICE_NAME " is a simple device that dumps all "
		"bytes written to a particular location in memory to "
		"a file specified by the \"filename\" attribute.";
        class = SIM_register_class(DEVICE_NAME, &funcs);

        memory_interface = MM_ZALLOC(1, io_memory_interface_t);
        memory_interface->operation = operation;
        SIM_register_interface(class, IO_MEMORY_INTERFACE, memory_interface);

        SIM_register_typed_attribute(class, "filename",
                                     get_filename, NULL,
                                     set_filename, NULL,
                                     Sim_Attr_Optional,
                                     "s", NULL,
                                     "Filename to write bytes to. If not set, "
				     "bytes are only added to the device log.");
}
