/*
 * simics/devs/mii.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_MII_H
#define _SIMICS_DEVS_MII_H

#define MII_INTERFACE "mii"

typedef struct {
        int    (*serial_access)(conf_object_t *obj, int data_in, int clock);
        uint16 (*read_register)(conf_object_t *obj, int index);
        void   (*write_register)(conf_object_t *obj, int index, uint16 value);
} mii_interface_t;

typedef void (*mii_register_watch_callback_t)(void *parameter,
                                              uint16 old_value,
                                              uint16 new_value);

/* interface exported by the physical layer device */
#define MII_MANAGEMENT_INTERFACE "mii-management"
typedef struct {
        int    (*serial_access)(conf_object_t *obj, int data_in, int clock);
        uint16 (*read_register)(conf_object_t *obj, int phy, int reg);
        void   (*write_register)(conf_object_t *obj, int phy, int reg,
                                 uint16 value);
#if !defined(GULP)
        void   (*watch_register)(conf_object_t *obj, int phy, int reg,
                                 mii_register_watch_callback_t callback,
                                 void *parameter);
#endif
} mii_management_interface_t;

#endif /* _SIMICS_DEVS_MII_H */
