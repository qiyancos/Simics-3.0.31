/*
  Copyright 2005-2007 Virtutech AB
 */
#ifndef X86_RESET_BUS_H
#define X86_RESET_BUS_H

typedef struct {
        void (*set_a20_line)(conf_object_t *obj, int value);
        int (*get_a20_line)(conf_object_t *obj);
        void (*reset_all)(conf_object_t *obj);
} x86_reset_bus_interface_t;

#define X86_RESET_BUS_INTERFACE "x86_reset_bus"

#endif /* X86_RESET_BUS_H */
