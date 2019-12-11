/*
 * simics/core/event.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_EVENT_H
#define _SIMICS_CORE_EVENT_H

/* which cpus will be synced before performing event */
/* much to do here to set the enum values, perhaps they should not be
   absolute */
/* <add-type id="sync_t"></add-type> */
typedef enum {
        Sim_Sync_Processor = 0,
        /* Sim_Sync_Node = 1,		 not supported yet */
        Sim_Sync_Machine = 2
} sync_t;

/* <add id="simics api types">
   <name index="true">event_handler_t</name>
   <doc>
   <doc-item name="NAME">event_handler_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="event_handler_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   The <type>event_handler_t</type> data type is used for event
   handler functions. <type><idx>event_function_t</idx></type> is a
   deprecated data type used for the same purpose.
   </doc-item>
   <doc-item name="SEE ALSO">
   SIM_step_clean, SIM_step_post, SIM_time_clean, SIM_time_clean
   </doc-item>
   </doc></add>

   <add id="event_handler_t def">
   <insert-upto id="event_handler_t def" text="event_function_t;"/>
   </add>
*/
typedef void (*event_handler_t)(conf_object_t *obj,
                                lang_void *parameter);
typedef event_handler_t event_function_t;

#ifdef SIMICS_API_TRACE
event_handler_t api_wrap_event_handler(event_handler_t f);
event_handler_t api_unwrap_event_handler(event_handler_t f);
#endif

/* <add-type id="event_queue_type_t def"></add-type> */
typedef enum event_queue_type {
        Sim_Queue_Step,
        Sim_Queue_Time
} event_queue_type_t;

void SIM_time_post(conf_object_t *NOTNULL obj, double seconds, sync_t sync,
                   void (*NOTNULL func)(conf_object_t *obj, lang_void *param),
                   lang_void *user_data);
void SIM_time_post_cycle(conf_object_t *NOTNULL obj, cycles_t cycles,
                         sync_t sync,
                         void (*NOTNULL func)(conf_object_t *obj,
                                              lang_void *param),
                         lang_void *user_data);
cycles_t SIM_time_next_occurrence(conf_object_t *NOTNULL obj,
                                  void (*NOTNULL func)(conf_object_t *obj,
                                                       lang_void *param),
                                  typed_lang_void *user_data);
void SIM_step_post(conf_object_t *NOTNULL obj, pc_step_t steps,
                   void (*NOTNULL func)(conf_object_t *obj, lang_void *param),
                   lang_void *user_data);
void VT_step_post(processor_t *NOTNULL cpu, conf_object_t *NOTNULL poster,
                  pc_step_t steps,
                  void (*NOTNULL func)(conf_object_t *obj, lang_void *param),
                  lang_void *user_data);
void VT_step_clean(processor_t *NOTNULL cpu, conf_object_t *NOTNULL poster,
                   void (*NOTNULL func)(conf_object_t *obj, lang_void *param),
                   typed_lang_void *user_data);
void VT_time_post(processor_t *NOTNULL cpu, conf_object_t *NOTNULL poster,
                  double seconds, sync_t sync,
                  void (*NOTNULL func)(conf_object_t *obj, lang_void *param),
                  lang_void *user_data);
void VT_time_post_cycle(processor_t *NOTNULL cpu,
                        conf_object_t *NOTNULL poster,
                        cycles_t delta, sync_t sync,
                        void (*NOTNULL func)(conf_object_t *obj,
                                             lang_void *param),
                        lang_void *arg);
void VT_time_clean(processor_t *NOTNULL cpu, conf_object_t *NOTNULL poster,
                   sync_t sync,
                   void (*NOTNULL func)(conf_object_t *obj, lang_void *param),
                   typed_lang_void *user_data);
pc_step_t SIM_step_next_occurrence(conf_object_t *NOTNULL obj,
                                   void (*NOTNULL func)(conf_object_t *obj,
                                                        lang_void *param),
                                   typed_lang_void *user_data);
void SIM_step_clean(conf_object_t *NOTNULL obj,
                    void (*NOTNULL func)(conf_object_t *obj, lang_void *param),
                    typed_lang_void *user_data);
void SIM_time_clean(conf_object_t *NOTNULL obj, sync_t sync,
                    void (*NOTNULL func)(conf_object_t *obj, lang_void *param),
                    typed_lang_void *user_data);

cycles_t SIM_cycle_count(conf_object_t *NOTNULL obj);
pc_step_t SIM_step_count(conf_object_t *NOTNULL obj);
cycles_t VT_cycles_to_quantum_end(processor_t *NOTNULL cpu);
double SIM_time(conf_object_t *NOTNULL obj);

void SIM_stall_cycle(conf_object_t *NOTNULL obj, cycles_t cycles);
void SIM_stall(conf_object_t *NOTNULL obj, double seconds);
cycles_t SIM_stalled_until(conf_object_t *NOTNULL obj);
cycles_t SIM_stall_count(conf_object_t *NOTNULL obj);

void VT_stall_cycle_counter(conf_object_t *NOTNULL cpu, pc_step_t steps);
void VT_stop_cycle_counter(conf_object_t *NOTNULL cpu);
void VT_unstall_cycle_counter(conf_object_t *NOTNULL cpu);

void SIM_break_cycle(conf_object_t *NOTNULL obj, integer_t cycles);
void SIM_break_step(conf_object_t *NOTNULL obj, integer_t steps);

void SIM_stacked_post(conf_object_t *NOTNULL obj,
                      void (*NOTNULL func)(conf_object_t *obj,
                                           lang_void *param),
                      lang_void *user_data);
void VT_run_outside_instruction(conf_object_t *NOTNULL obj,
                                void (*NOTNULL func)(conf_object_t *obj,
                                                     lang_void *param),
                                lang_void *user_data);
void VT_post_first_in_step_queue(conf_object_t *NOTNULL obj,
                                 void (*NOTNULL func)(conf_object_t *obj,
                                                      lang_void *param),
                                 lang_void *user_data);
int VT_inside_instruction(void);

typedef struct {
        /* Information */
        simtime_t (*read)(conf_object_t *clockobj);
        uint64 (*get_frequency)(conf_object_t *clockobj); /* Hz */

        /* Events */
        void (*post)(conf_object_t *clockobj,
                     conf_object_t *poster,
                     cycles_t cycles,
                     sync_t sync,
                     void (*NOTNULL func)(conf_object_t *obj,
                                          lang_void *param),
                     lang_void *user_data);
} clock_interface_t;
#define CLOCK_INTERFACE "clock"

int VT_signal_safe_callback(void (*func)(lang_void *), lang_void *user_data);

/* <add id="event_poster_interface_t">

   This interface is intended for objects that post events. Each events has a
   pointer to a call-back function and a data pointer associated with it. These
   pointers need to be converted to values that can be represented in a file
   when a configuration is written (a checkpoint is taken), and converted back
   to pointers when a configuration is read (a checkpoint is opened). Simics
   also needs some way to get a text description of an event that can be
   presented to the user. These functions should be implemented through the
   <iface>event-poster</iface> interface by all objects posting event.

   <insert-until text="// ADD INTERFACE event_poster_interface"/>

   <fun><idx>get_event_info_val</idx>()</fun> is called for each event posted
   by the object <param>obj</param> present in the event queues when writing a
   configuration. Using the <param>func</param> and the <param>info</param>
   parameters <fun>get_event_info_val()</fun> should return a checkpoint value
   so that <fun>set_event_info()</fun> can restore both <param>func</param> and
   <param>info</param> when the configuration is later read. If the event
   should not be saved, <fun>get_event_info_val()</fun> should return
   <pp>Sim_Val_Nil</pp>.

   <fun><idx>get_event_info</idx>()</fun> is an alternative interface
   kept for compatibility. It modifies the <param>checkpoint_value</param>
   parameter instead of returning a value. It is only used if
   <fun>get_event_info_val()</fun> is not present.

   <fun><idx>set_event_info</idx>()</fun> is called for each event associated
   with <param>obj</param> found when restoring events from a saved
   configuration. Using the <param>checkpoint_value</param>
   <fun>set_event_info()</fun> should fill in <param>out_func</param> and
   <param>out_info</param> with the associated
   values. <fun>set_event_info()</fun> should return one of
   <pp>Sim_Set_Ok</pp>, <pp>Sim_Set_Ignored</pp> and
   <pp>Sim_Set_Illegal_Value</pp>.
   <pp>Sim_Set_Ok</pp> should be returned if the event was recognised and
   should be posted, <pp>Sim_Set_Ignored</pp> if the event was recognised for
   backwards compatibility but should not be posted, and
   <pp>Sim_Set_Illegal_Value</pp> if the event was not recognised.

   <fun><idx>describe_event</idx>()</fun> should return a string describing the
   event using the <param>func</param> and <param>user_data</param>
   parameters. The string is for example used when the event queue is printed.

   </add> */

struct event_poster_interface {
#if defined(GULP)
        attr_value_t (*get_event_info_val)(conf_object_t *NOTNULL obj, 
                                           void (*NOTNULL func)(
                                                           conf_object_t *obj,
                                                           lang_void *param),
                                           ignored_pointer_t user_data);
        const char *(*describe_event)(conf_object_t *NOTNULL obj, 
                                      void (*NOTNULL func)(conf_object_t *obj,
                                                           lang_void *param),
                                      ignored_pointer_t user_data);
#else  /* ! GULP */
        attr_value_t (*get_event_info_val)(conf_object_t *NOTNULL obj,
                                           void (*NOTNULL func)(
                                                            conf_object_t *obj,
                                                            lang_void *param),
                                           void *user_data);
        const char *(*describe_event)(conf_object_t *NOTNULL obj,
                                      void (*NOTNULL func)(conf_object_t *obj,
                                                           lang_void *param),
                                      void *user_data);
        void (*get_event_info)(attr_value_t *NOTNULL checkpoint_value,
                               conf_object_t *NOTNULL obj,
                               void (*NOTNULL func)(conf_object_t *obj,
                                                    lang_void *param),
                               void *user_data);
        int (*set_event_info)(conf_object_t *NOTNULL obj,
                              attr_value_t *NOTNULL checkpoint_value,
                              void (**NOTNULL out_func)(conf_object_t *obj,
                                                        lang_void *param),
                              void **NOTNULL out_info);
#endif /* ! GULP */
};

#define EVENT_POSTER_INTERFACE "event_poster"
// ADD INTERFACE event_poster_interface

#endif /* _SIMICS_CORE_EVENT_H */
