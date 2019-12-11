/*
 * simics/devs/reset.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_RESET_H
#define _SIMICS_DEVS_RESET_H

/* <add id="reset_interface_t">
   The <i>reset</i> functions gets invoked whenever a caller decides
   that the device should reset itself. The argument <i>hard</i> is
   nonzero if the device should perform a hard reset.  Otherwise a
   soft reset should be done.  

   <insert-until text="// ADD INTERFACE reset_interface"/>
   </add>
*/
typedef struct {
        void (*reset)(conf_object_t *, int hard);
} reset_interface_t;

#define RESET_INTERFACE "reset"
// ADD INTERFACE reset_interface

#endif /* _SIMICS_DEVS_RESET_H */
