/*
  full_table.c

  Copyright 2002-2007 Virtutech AB
  
  The contents herein are Source Code which are a subset of Licensed
  Software pursuant to the terms of the Virtutech Simics Software
  License Agreement (the "Agreement"), and are being distributed under
  the Agreement.  You should have received a copy of the Agreement with
  this Licensed Software; if not, please contact Virtutech for a copy
  of the Agreement prior to using this Licensed Software.
  
  By using this Source Code, you agree to be bound by all of the terms
  of the Agreement, and use of this Source Code is subject to the terms
  the Agreement.
  
  This Source Code and any derivatives thereof are provided on an "as
  is" basis.  Virtutech makes no warranties with respect to the Source
  Code or any derivatives thereof and disclaims all implied warranties,
  including, without limitation, warranties of merchantability and
  fitness for a particular purpose and non-infringement.

*/

#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>
#include <simics/arch/x86.h>

#include "x86_tlb.h"

/*
 * The tlb entries are kept in a VECT (growable array) and to permit fast
 * lookups, there is a table that maps linear page number to VECT index.
 * The lookup table can contain garbage, so we need to check both against
 * the limit on the VECT and check that the linear address corresponds.
 */

struct x86_tlb_impl {
        /* Unlimited size mode (full table version) */
        uint16                  table_large[1 << 11];
        VECT(tlb_entry_t)       table_large_vect;
        uint32                  table_4k[1 << 20];
        VECT(tlb_entry_t)       table_4k_vect;
};

static void
enter_tlb_mode_table(x86_tlb_t *tlb)
{
        tlb->imp = MM_MALLOC(1, x86_tlb_impl_t);
        VINIT(tlb->imp->table_large_vect);
        VINIT(tlb->imp->table_4k_vect);
}

static void
leave_tlb_mode_table(x86_tlb_t *tlb)
{
        VFREE(tlb->imp->table_large_vect);
        VFREE(tlb->imp->table_4k_vect);
        MM_FREE(tlb->imp);
        tlb->imp = NULL;
}

static void
update_large_pointers(x86_tlb_t *tlb, int i)
{
        tlb_entry_t *entry = &VGET(tlb->imp->table_large_vect, i);
        uint32 key = entry->linear_page_start >> tlb->large_shift;
        ASSERT(key < ALEN(tlb->imp->table_large));
        tlb->imp->table_large[key] = i;
}

static void
table_remove_large_entry(x86_tlb_t *tlb, int i)
{
        VREMOVE(tlb->imp->table_large_vect, i);
        if (i < VLEN(tlb->imp->table_large_vect))
                update_large_pointers(tlb, i);
}

static void
update_4k_pointers(x86_tlb_t *tlb, int i)
{
        tlb_entry_t *entry = &VGET(tlb->imp->table_4k_vect, i);
        uint32 key = entry->linear_page_start >> 12;
        ASSERT(key < ALEN(tlb->imp->table_4k));
        tlb->imp->table_4k[key] = i;
}

static void
table_remove_4k_entry(x86_tlb_t *tlb, int i)
{
        VREMOVE(tlb->imp->table_4k_vect, i);
        if (i < VLEN(tlb->imp->table_4k_vect))
                update_4k_pointers(tlb, i);
}

static int
lookup_large(x86_tlb_t *tlb, linear_address_t laddr)
{
        uint32 key = laddr >> tlb->large_shift;
        ASSERT(key < ALEN(tlb->imp->table_large));
        uint32 possible_index = tlb->imp->table_large[key];
        if (possible_index >= VLEN(tlb->imp->table_large_vect))
                return -1;
        tlb_entry_t *entry = &VGET(tlb->imp->table_large_vect, possible_index);
        if (entry->linear_page_start >> tlb->large_shift != key)
                return -1;
        return possible_index;
}

static int
lookup_4k(x86_tlb_t *tlb, linear_address_t laddr)
{
        uint32 key = laddr >> 12;
        ASSERT(key < ALEN(tlb->imp->table_4k));
        uint32 possible_index = tlb->imp->table_4k[key];
        if (possible_index >= VLEN(tlb->imp->table_4k_vect))
                return -1;
        tlb_entry_t *entry = &VGET(tlb->imp->table_4k_vect, possible_index);
        if (entry->linear_page_start >> 12 != key)
                return -1;
        return possible_index;
}

static void
insert_large(x86_tlb_t *tlb, tlb_entry_t *entry)
{
        VADD(tlb->imp->table_large_vect, *entry);
        update_large_pointers(tlb, VLEN(tlb->imp->table_large_vect) - 1);
}

static void
insert_4k(x86_tlb_t *tlb, tlb_entry_t *entry)
{
        VADD(tlb->imp->table_4k_vect, *entry);
        update_4k_pointers(tlb, VLEN(tlb->imp->table_4k_vect) - 1);
}

static void
x86_tlb_flush_all_table(x86_tlb_t *tlb, int keep_global_entries)
{
        int i;

        for (i = 0; i < VLEN(tlb->imp->table_large_vect); i++) {
                if (flush_entry(tlb,
                                &VGET(tlb->imp->table_large_vect, i),
                                keep_global_entries,
                                tlb->large_page_size)) {
                        table_remove_large_entry(tlb, i);
                        i--;
                }
        }
        for (i = 0; i < VLEN(tlb->imp->table_4k_vect); i++) {
                if (flush_entry(tlb,
                                &VGET(tlb->imp->table_4k_vect, i),
                                keep_global_entries,
                                4 * 1024)) {
                        table_remove_4k_entry(tlb, i);
                        i--;
                }
        }
}

static void
x86_tlb_flush_page_table(x86_tlb_t *tlb,
                         linear_address_t laddr)
{
        int i;
        tlb_entry_t *entry;

        i = lookup_large(tlb, laddr);
        if (i >= 0) {
                entry = &VGET(tlb->imp->table_large_vect, i);
                SIM_flush_D_STC_logical(tlb->cpu, entry->linear_page_start,
                                        tlb->large_page_size);
                table_remove_large_entry(tlb, i);
        }
        i = lookup_4k(tlb, laddr);
        if (i >= 0) {
                entry = &VGET(tlb->imp->table_4k_vect, i);
                SIM_flush_D_STC_logical(tlb->cpu, entry->linear_page_start, 4*1024);
                table_remove_4k_entry(tlb, i);
        }
}

static tlb_entry_t *
x86_tlb_lookup_common_table(x86_tlb_t *tlb, processor_mode_t mode,
                            read_or_write_t rw, data_or_instr_t tlb_select,
                            linear_address_t laddr, linear_address_t *offset)
{
        tlb_entry_t *entry = NULL;
        int i;

        *offset = 0;
        
        i = lookup_large(tlb, laddr);
        if (i >= 0) {
                entry = &VGET(tlb->imp->table_large_vect, i);
                *offset = laddr & (tlb->large_page_size - 1);
                return entry;
        }
        i = lookup_4k(tlb, laddr);
        if (i >= 0) {
                entry = &VGET(tlb->imp->table_4k_vect, i);
                *offset = laddr & 4095;
                return entry;
        }
        return NULL;
}

static void
x86_tlb_add_table(x86_tlb_t *tlb, data_or_instr_t tlb_select,
                  tlb_entry_t *new_tlb_entry,
                  int page_code, uint32 pagesize)
{
        int i;
        linear_address_t laddr = new_tlb_entry->linear_page_start;
        if (page_code == 2 || page_code == 1) {
                i = lookup_large(tlb, laddr);
        } else {
                i = lookup_4k(tlb, laddr);
        }
        if (i >= 0) {
                /* Remove STC entries for modified TLB entry */
                SIM_flush_D_STC_logical(tlb->cpu,
                                        new_tlb_entry->linear_page_start,
                                        pagesize);
        }
        if (i >= 0) {
                /* replace entry */
                if (page_code == 2 || page_code == 1)
                        VSET(tlb->imp->table_large_vect, i, *new_tlb_entry);
                else
                        VSET(tlb->imp->table_4k_vect, i, *new_tlb_entry);
        } else {
                /* insert entry */
                if (page_code == 2 || page_code == 1)
                        insert_large(tlb, new_tlb_entry);
                else
                        insert_4k(tlb, new_tlb_entry);
        }
        SIM_c_hap_occurred_always(x86_hap_tlb_fill[tlb_select],
                                  &tlb->log.obj, page_code,
                                  (integer_t)new_tlb_entry->linear_page_start,
                                  (integer_t)new_tlb_entry->physical_page_start,
                                  (integer_t)page_code);
}

static set_error_t
set_x86_tlb_table(x86_tlb_id_t *id, x86_tlb_t *ptr, attr_value_t *val)
{
        int idx, way;

        if (val->kind == Sim_Val_List) {
                if (id->large) {
                        if (id->way != Sim_DI_Data)
                                return Sim_Set_Illegal_Value;
                        if (val->u.list.size != 1)
                                return Sim_Set_Illegal_Value;
                        if (!set_tlb_check_valid(val, 0, ptr->large_page_size - 1))
                                return Sim_Set_Illegal_Value;
                } else { /* 4k */
                        if (id->way != Sim_DI_Data)
                                return Sim_Set_Illegal_Value;
                        if (val->u.list.size != 1)
                                return Sim_Set_Illegal_Value;
                        if (!set_tlb_check_valid(val, 0, 0xfff))
                                return Sim_Set_Illegal_Value;
                }
        }

        if (id->large) {
                VCLEAR(ptr->imp->table_large_vect);
        } else { /* 4k */
                VCLEAR(ptr->imp->table_4k_vect);
        }

        if (val->kind == Sim_Val_List) {
                if (id->large) {
                        for (idx = 0; idx < val->u.list.size; idx++) {
                                for (way = 0; way < val->u.list.vector[idx].u.list.size; way++) {
                                        attr_value_t *tlb_entry = &val->u.list.vector[idx].u.list.vector[way];
                                        tlb_entry_t entry;
                                        set_tlb_entry(&entry, tlb_entry);
                                        insert_large(ptr, &entry);
                                }
                        }
                } else { /* 4k */
                        for (idx = 0; idx < val->u.list.size; idx++) {
                                for (way = 0; way < val->u.list.vector[idx].u.list.size; way++) {
                                        attr_value_t *tlb_entry = &val->u.list.vector[idx].u.list.vector[way];
                                        tlb_entry_t entry;
                                        set_tlb_entry(&entry, tlb_entry);
                                        insert_4k(ptr, &entry);
                                }
                        }
                }
        }

        return Sim_Set_Ok;
}

static attr_value_t
get_x86_tlb_table(x86_tlb_id_t *id, x86_tlb_t *ptr)
{
        attr_value_t ret;
        ret.kind = Sim_Val_List;
        if (id->large) {
                if (id->way != Sim_DI_Data)
                        return SIM_make_attr_nil();
                ret = SIM_alloc_attr_list(1);
                int len = VLEN(ptr->imp->table_large_vect);
                ret.u.list.vector[0] = SIM_alloc_attr_list(len);
                int i;
                for (i = 0; i < len; i++)
                        get_tlb_entry(&ret.u.list.vector[0].u.list.vector[i],
                                      &VGET(ptr->imp->table_large_vect, i));
        } else { /* 4k */
                if (id->way != Sim_DI_Data)
                        return SIM_make_attr_nil();
                ret = SIM_alloc_attr_list(1);
                int len = VLEN(ptr->imp->table_4k_vect);
                ret.u.list.vector[0] = SIM_alloc_attr_list(len);
                int i;
                for (i = 0; i < len; i++)
                        get_tlb_entry(&ret.u.list.vector[0].u.list.vector[i],
                                      &VGET(ptr->imp->table_4k_vect, i));
        }
        return ret;
}

mode_methods_t full_table_mode_methods = {
        .name = "Full table mode",
        .enter_mode = enter_tlb_mode_table,
        .leave_mode = leave_tlb_mode_table,
        .flush_all = x86_tlb_flush_all_table,
        .flush_page = x86_tlb_flush_page_table,
        .lookup = x86_tlb_lookup_common_table,
        .add = x86_tlb_add_table,
        .set = set_x86_tlb_table,
        .get = get_x86_tlb_table,
};
