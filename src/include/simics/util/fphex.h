/*
 * simics/util/fphex.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_FPHEX_H
#define _SIMICS_UTIL_FPHEX_H

const char *double_hex_str(double _d, int type, int sign);
double fphex_strtod(const char *nptr, char **endptr);

#endif /* _SIMICS_UTIL_FPHEX_H */
