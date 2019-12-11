/*
 * simics/devs/recorder.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_RECORDER_H
#define _SIMICS_DEVS_RECORDER_H

#define RECORDER_INTERFACE "recorder"

typedef struct recorder recorder_t;

/*
 * dbuffer ownership is _not_ transfered. The callback must not modify the
 * dbuffer without cloning it first.
 */

typedef void (*recorder_input_handler_t)(conf_object_t *obj, dbuffer_t *data,
                                         uint32 uint_data);

typedef struct recorder_interface {
        recorder_t *(*attach)(conf_object_t *rec, conf_object_t *obj,
                              recorder_input_handler_t input_from_recorder);
        void (*detach)(recorder_t *r);
        void (*input)(recorder_t *r, dbuffer_t *data, uint32 uint_data);
} recorder_interface_t;

#endif /* _SIMICS_DEVS_RECORDER_H */
