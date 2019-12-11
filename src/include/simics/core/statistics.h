/*
 * simics/core/statistics.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_STATISTICS_H
#define _SIMICS_CORE_STATISTICS_H

int SIM_add_mode_counter(conf_object_t *cpu, const char *desc);
integer_t SIM_get_mode_counter(conf_object_t *cpu, processor_mode_t mode,
                               int counter);
void SIM_set_mode_counter(conf_object_t *cpu, processor_mode_t mode,
                          int counter, integer_t value);
void SIM_inc_mode_counter(conf_object_t *cpu, processor_mode_t mode,
                          int counter);
void SIM_inc_cur_mode_counter(conf_object_t *cpu, int counter);

#endif /* _SIMICS_CORE_STATISTICS_H */
