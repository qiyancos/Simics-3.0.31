/*
 * simics/core/hindsight.h
 *
 * This file is part of Virtutech Simics
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_HINDSIGHT_H
#define _SIMICS_CORE_HINDSIGHT_H

void VT_register_revexec(conf_object_t *revexec_obj);
int VT_hindsight_license_check(void);

int VT_is_reversing(void);
int VT_hindsight_active(void);
int VT_hindsight_available(void);

typedef enum {
        Sim_Reverse_Limit      = 0,
        Sim_End_Of_Future      = 1
} revexec_pos_t;


pc_step_t VT_revexec_steps(conf_object_t *cpu, revexec_pos_t where);
cycles_t VT_revexec_cycles(conf_object_t *cpu, revexec_pos_t where);
conf_object_t *VT_revexec_cur_cpu(revexec_pos_t where);

int VT_reverse(pc_step_t count);
int VT_rewind(conf_object_t *cpu, pc_step_t abscount);

int VT_in_the_past(void);
void VT_discard_future(void);

pc_step_t VT_get_rewind_overhead(conf_object_t *cpu, pc_step_t abscount);

typedef enum {
        /* micro checkpoint id */
        Sim_MC_ID_User        = 0,
        Sim_MC_ID_Breakpoint  = 1,
        Sim_MC_ID_Tmp         = 2,
        Sim_MC_ID_N_States    = 3,
        Sim_MC_ID_Last_States = 4,
        Sim_MC_ID_Mask        = 255,

        /* type of micro checkpoint */
        Sim_MC_Persistent    = 256,
        Sim_MC_Automatic     = 512          /* may be deleted automatically */
} micro_checkpoint_flags_t;

void VT_save_micro_checkpoint(const char *name,
                              micro_checkpoint_flags_t flags);

/* <add id="re_state_interface_t">
   Internal. Do not use.

   <insert-until text="// ADD INTERFACE re_state_interface"/>
   </add> */
typedef struct {
        void (*save)(int replace_last, const char *name,
                     micro_checkpoint_flags_t flags);
        void (*restore)(int index);
        void (*remove)(int index);

        int (*num_states)(void);
        pc_step_t (*get_stepcount)(int index, conf_object_t *cpu);
        cycles_t (*get_cyclecount)(int index, conf_object_t *cpu);
        conf_object_t *(*get_cur_cpu)(int index);

        void (*barrier)(void);

        simtime_t (*get_end_of_future)(conf_object_t *cpu, int in_cycles);
        conf_object_t *(*get_end_of_future_cpu)(void);

        int (*get_idx)(const char *name);
} re_state_interface_t;
#define RE_STATE_INTERFACE "_re_state"
// ADD INTERFACE re_state_interface

/* <add id="re_state_interface_t">
   Internal. Do not use.

   <insert-until text="// ADD INTERFACE re_exec_interface"/>
   </add> */
typedef struct {
        int (*reverse)(conf_object_t *cpu, pc_step_t steps);
        int (*rewind)(conf_object_t *cpu, pc_step_t abssteps);
        int (*is_rewinding)(void);
} re_exec_interface_t;
#define RE_EXEC_INTERFACE "_re_exec"
// ADD INTERFACE re_exec_interface


/* <add id="temporal_state_interface_t">
   This interface is used in conjunction with object attributes to
   save an in-memory snapshot of the object state and to restoring this
   state at a later point in time. Note that this interface is only
   used for reverse execution; it is not used for checkpointing to disk.

   All functions in this interface are optional.

   Object state not handled by the attributes can be saved through
   the <fun>save</fun> function. The return value is a pointer
   to state information. It should be noted that the state can be
   represented in an incremental manner as changes since the last
   call to <fun>save</fun>.

   State information is released by the <fun>merge</fun> function. If the
   pointer returned by <fun>save</fun> represents incremental state changes,
   then the data in the <arg>killed</arg> argument should be appended to
   <arg>prev</arg> before the state pointed to be <arg>killed</arg>
   is released.

   The function <fun>prepare_restore</fun> is called when a saved state
   is about to be loaded, before any attributes have been set.

   The <fun>finish_restore</fun> function is invoked when all
   attributes have been set. The <arg>state</arg> argument is the
   pointer previously returned by <fun>save</fun> (or NULL if that function
   is not unused). The passed state information should not be modified
   or released by this function.

   <insert-until text="// ADD INTERFACE temporal_state_interface"/>
   </add> */
typedef struct {
        lang_void *(*save)(conf_object_t *obj);
        void (*merge)(conf_object_t *obj, lang_void *prev, lang_void *killed);
        void (*prepare_restore)(conf_object_t *obj);
        void (*finish_restore)(conf_object_t *obj, lang_void *state);
} temporal_state_interface_t;

#define TEMPORAL_STATE_INTERFACE "temporal_state"
// ADD INTERFACE temporal_state_interface

/* VT_in_time_order() is used to handle events (e.g. breakpoint haps) in strict
   time order. This is particularly useful when simics reverses since there is
   absolutely no guarantee that haps are invoked in reverse time order.

   VT_c_in_time_order() is similar to VT_in_time_order() except the buffer
   pointed to by the data argument is copied and later passed to the callback.
   The callback should not release the data or cache pointers to it since
   the space will be reused automatically.

   The callback may raise an exception, e.g. by calling SIM_break_simulation,
   to signal that the simulation should be stopped.
*/
typedef void (*simple_time_ordered_handler_t)(conf_object_t *obj,
                                              integer_t param1, integer_t param2);


void VT_in_time_order(conf_object_t *obj, simple_time_ordered_handler_t handler,
                      integer_t user_param1, integer_t user_param2);

#ifndef GULP
typedef void (*time_ordered_handler_t)(conf_object_t *obj, 
                                       integer_t param,
                                       void *data);

void VT_c_in_time_order(conf_object_t *obj, time_ordered_handler_t handler,
                        integer_t param, void *data, size_t data_size);
#endif

/* used to prevent reverse execution from touching certain classes/attributes */
void VT_revexec_ignore_class(const char *class_name);
void VT_revexec_ignore_attribute(const char *class_name, const char *attr);
void VT_revexec_ignore_obj(conf_object_t *obj);

/* prevent reversal past this point in time */
void VT_revexec_barrier(void);

/* internal */
int VT_revexec_get_ignored_flag(conf_object_t *obj, const char *attr);
void VT_revexec_divert_output(int divert, int discard);

/* only to be used by the time ordering implementation */
void VT_block_time_ordered_events(int at_step_end);
void VT_time_ordering_reset(void);
int VT_run_time_ordered_events(void);
int VT_time_ordered_stop_point(void);

#endif /* _SIMICS_CORE_HINDSIGHT_H */
