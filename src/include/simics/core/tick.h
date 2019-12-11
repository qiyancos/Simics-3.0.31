/*
 * simics/core/tick.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_TICK_H
#define _SIMICS_CORE_TICK_H

typedef enum {
	Tick_Always,
	Tick_When_Running
} tick_active_t;

#if !defined(GULP) /* only for C */

/*
  IMPORTANT compatibility note for Simics 3.0

  The VT_register_tick_handler and VT_unregister_tick_handler can only
  be used in core or in modules part of a base package. They cannot be
  used in anything part of an add-on package.
 */

typedef void (*tick_handler_t)(void *user_data, void *sig_ctx);

void VT_register_tick_handler(tick_handler_t tick, void *user_data, tick_active_t active);
void VT_unregister_tick_handler(tick_handler_t tick, void *user_data);

#endif /* !defined(GULP) */

#endif /* _SIMICS_CORE_TICK_H */
