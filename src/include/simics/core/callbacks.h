/*
 * simics/core/callbacks.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_CALLBACKS_API_H
#define _SIMICS_CORE_CALLBACKS_API_H

#include <stdarg.h>
#include <simics/core/callbacks-types.h>

/* <add id="simics api types">
   <name index="true">hap_flags_t</name>
   <doc>
   <doc-item name="NAME">hap_flags_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="hap_flags_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   The <type>hap_flags_t</type> is used to specify additional
   information about a hap. <tt>Sim_Hap_Simulation</tt> signals that
   the hap is used to model simulated behavior. All other values
   are currently for Simics internal use only.
   </doc-item>
   <doc-item name="SEE ALSO">SIM_hap_add_callback</doc-item>
   </doc></add>
*/
/* <add-type id="hap_flags_t def"></add-type>
 */
typedef enum {
        Sim_Hap_Simulation  = 1,
        Sim_Hap_Old_Format  = 2,  /* internal use */
        Sim_Hap_Added       = 4,  /* internal use */
        Sim_Hap_Deleted     = 8,  /* internal use */
        Sim_Hap_Attr        = 16  /* internal use */
} hap_flags_t;

attr_value_t SIM_get_all_hap_types(void);

hap_type_t SIM_hap_add_type(const char *NOTNULL hap,
                            const char *NOTNULL params,
                            const char *param_desc,
                            const char *index, const char *desc,
                            int old_had_obj);
void SIM_hap_remove_type(const char *NOTNULL hap);

hap_type_t SIM_hap_get_number(const char *NOTNULL hap);
const char *SIM_hap_get_name(hap_type_t hap);

hap_handle_t SIM_hap_add_callback(const char *NOTNULL hap,
                                  obj_hap_func_t func, typed_lang_void *data);
hap_handle_t SIM_hap_add_callback_index(const char *NOTNULL hap,
                                        obj_hap_func_t func,
                                        typed_lang_void *data,
                                        integer_t index);
hap_handle_t SIM_hap_add_callback_range(const char *NOTNULL hap,
                                        obj_hap_func_t func,
                                        typed_lang_void *data,
                                        integer_t start, integer_t end);
hap_handle_t SIM_hap_add_callback_obj(const char *NOTNULL hap,
                                      conf_object_t *obj, hap_flags_t flags,
                                      obj_hap_func_t func,
                                      typed_lang_void *data);
hap_handle_t SIM_hap_add_callback_obj_index(const char *NOTNULL hap,
                                            conf_object_t *obj,
                                            hap_flags_t flags,
                                            obj_hap_func_t func,
                                            typed_lang_void *data,
                                            integer_t index);
hap_handle_t SIM_hap_add_callback_obj_range(const char *NOTNULL hap,
                                            conf_object_t *obj,
                                            hap_flags_t flags,
                                            obj_hap_func_t func,
                                            typed_lang_void *data,
                                            integer_t start, integer_t end);

void SIM_hap_delete_callback(const char *NOTNULL hap,
                             obj_hap_func_t func, typed_lang_void *data);
void SIM_hap_delete_callback_obj(const char *NOTNULL hap, conf_object_t *obj,
                                 obj_hap_func_t func, typed_lang_void *data);
void SIM_hap_delete_callback_id(const char *NOTNULL hap, hap_handle_t handle);
void SIM_hap_delete_callback_obj_id(const char *NOTNULL hap,
                                    conf_object_t *obj, hap_handle_t handle);

int SIM_hap_callback_exists(const char *NOTNULL id, obj_hap_func_t func,
                            typed_lang_void *data);
int SIM_hap_is_active(hap_type_t hap);

#if !defined(GULP) /* only for C */
int SIM_c_hap_occurred(hap_type_t hap, conf_object_t *obj,
                       integer_t value, ...);
int SIM_c_hap_occurred_vararg(hap_type_t hap, conf_object_t *obj,
                              integer_t value, va_list ap);
int SIM_c_hap_occurred_always(hap_type_t hap, conf_object_t *obj,
                              integer_t value, ...);
int SIM_c_hap_occurred_always_vararg(hap_type_t hap, conf_object_t *obj,
                                     integer_t value, va_list ap);
#endif /* !GULP */

int SIM_hap_occurred(hap_type_t hap, conf_object_t *obj,
                     integer_t value, attr_value_t *NOTNULL list);
int SIM_hap_occurred_always(hap_type_t hap, conf_object_t *obj,
                            integer_t value, attr_value_t *NOTNULL list);

void VT_hap_replace_object_references(conf_object_t *old_ref,
				      conf_object_t *new_ref);

#endif /* _SIMICS_CORE_CALLBACKS_H */
