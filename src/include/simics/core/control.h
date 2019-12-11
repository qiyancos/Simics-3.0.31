/*
 * simics/core/control.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_CONTROL_H
#define _SIMICS_CORE_CONTROL_H

typedef enum {
        Sim_NM_Read,            /* when ready for reading/accept, or closed */
        Sim_NM_Write            /* when ready for writing/connect */
} notify_mode_t;

#ifdef _WIN32
void SIM_notify_on_object(HANDLE obj, int run_in_thread,
                          void (*callback)(lang_void *data), lang_void *data);
#else
void SIM_notify_on_descriptor(int fd, notify_mode_t mode, int run_in_thread,
                              void (*callback)(lang_void *data),
                              lang_void *data);
#endif
void SIM_notify_on_socket(int sock, notify_mode_t mode, int run_in_thread,
                          void (*callback)(lang_void *data),
                          lang_void *data);
void SIM_thread_safe_callback(void (*NOTNULL f)(lang_void *data),
                              lang_void *data);

void SIM_post_command(void (*NOTNULL f)(lang_void *data), lang_void *data);

integer_t SIM_realtime_event(unsigned delay,
                             void (*NOTNULL callback)(lang_void *data),
                             lang_void *data, int run_in_thread,
                             const char *desc);
int SIM_cancel_realtime_event(integer_t id);

void VT_register_work(void (*NOTNULL f)(lang_void *data), lang_void *data);

int SIM_postponing_continue(void);
pc_step_t SIM_continue(integer_t steps);

int VT_get_pending_sim_continue(void);

const char *VT_get_current_command_file(void);
int VT_get_current_line_number(void);

int SIM_simics_is_running(void);

void SIM_break_simulation(const char *msg);
void SIM_break_message(const char *msg);
void VT_user_interrupt(const char *msg, int break_script);

void VT_clear_break_message(void);
const char *VT_get_break_message(void);

void VT_restart_simics(attr_value_t *argv_list);

#endif /* _SIMICS_CORE_CONTROL_H */
