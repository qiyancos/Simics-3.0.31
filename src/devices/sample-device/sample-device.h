/*
  sample-device.h - sample code for a Simics device

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

#ifndef SAMPLE_DEVICE_H
#define SAMPLE_DEVICE_H

/* Other modules can find our exported interface
 * using the SIM_get_interface function.
 */

typedef struct {
        
        void (*simple_function)(conf_object_t *obj);

} sample_interface_t;

#endif /* SAMPLE_DEVICE_H */
