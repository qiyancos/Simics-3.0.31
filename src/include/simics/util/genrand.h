/*
 * simics/util/genrand.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 *
 * MT19937 random number generation.
 *
 */

#ifndef _SIMICS_UTIL_GENRAND_H
#define _SIMICS_UTIL_GENRAND_H

typedef struct rand_state rand_state_t;

rand_state_t *genrand_init(uint32 s);
rand_state_t *genrand_init_array(uint32 init_key[], unsigned key_length);
rand_state_t *genrand_init_attr(attr_value_t *val);
attr_value_t genrand_state_to_attr(rand_state_t *rs);

uint32 genrand_uint32(rand_state_t *rs);
uint64 genrand_uint64(rand_state_t *rs);
double genrand_double(rand_state_t *rs);

#endif /* _SIMICS_UTIL_GENRAND_H */
