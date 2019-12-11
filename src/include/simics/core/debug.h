/*
 * simics/core/debug.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_DEBUG_H
#define _SIMICS_CORE_DEBUG_H

attr_value_t DBG_get_branch_arcs(conf_object_t *br_obj,
                                 generic_address_t start,
                                 generic_address_t stop);
void DBG_realtime_events(void);
void DBG_license_files(void);
int  DBG_uncatch_signal(int sig);
void DBG_infinite_loop(void);
void DBG_control_c_handler(void);
void DBG_reinstall_control_c_handler(void);
void DBG_image_stats(void);

void VT_post_event_in_assert_slot(struct conf_object *obj, uint64 delta, 
                                  event_handler_t fp, lang_void *arg);

int DBG_check_icode(void);
void DBG_dump_dstc(conf_object_t *cpu);
void DBG_check_dstc(conf_object_t *cpu);
void DBG_dump_turbo_page_mappings(conf_object_t *cpu);

void DBG_mm_list_types(int max);
attr_value_t DBG_mm_list_sites(const char *file_pat, int maxsites,
                               int return_val);
void DBG_mm_snoop_type(const char *type, int enable);
void DBG_mm_vtmem_inform(int enable);
void DBG_mm_hash_stat(void);

#if defined(HOST_X86) && defined(__GNUC__)
#define HAVE_VTMEM_INFORM
#endif
#if defined(HOST_ULTRASPARC) && defined(HOST_64_BIT)
#define HAVE_VTMEM_INFORM
#endif

#define VTMEM_INFORM_STR_WORDS 6
#define MODULE_LOAD_2_STR_WORDS 16
#define MAX_PACKET_SIZE 20

typedef enum {
        Vtmem_Allocate_Object = 1,
        Vtmem_Free_Object = 2,
        Vtmem_New_Site = 3,
        Vtmem_Module_Load = 4,
        Vtmem_Early_Stack_Pointer = 5,
        Vtmem_Unload_All_Modules = 6,
        Vtmem_Start_Run = 7,
        Vtmem_Module_Load_2 = 8
} vtmem_inform_opcode_t;

#endif /* _SIMICS_CORE_DEBUG_H */
