/*
  hash_based.c

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

struct x86_tlb_impl
{
        /* Unlimited size mode (hash table version) */
        ht_table_t              hash_large;
        ht_table_t              hash_4k;

};

typedef struct {
        x86_tlb_t      *tlb;
        int             pagesize;
        int             keep_global_entries;
} hash_remove_info_t;

static void
enter_tlb_mode_hasht(x86_tlb_t *tlb)
{
        tlb->imp = MM_ZALLOC(1, x86_tlb_impl_t);
        ht_init_table(&tlb->imp->hash_large, 1);
        ht_init_table(&tlb->imp->hash_4k, 1);

}

static void
leave_tlb_mode_hasht(x86_tlb_t *tlb)
{
        ht_delete_table(&tlb->imp->hash_large, 1, 0);
        ht_delete_table(&tlb->imp->hash_4k, 1, 0);
        MM_FREE(tlb->imp);
        tlb->imp = NULL;
}

static int
hash_remove_entry(ht_table_t *table, uint64 key, void *value, void *data)
{
        tlb_entry_t *tlb_entry = (tlb_entry_t *)value;
        hash_remove_info_t *remove_info = (hash_remove_info_t *)data;

        if (flush_entry(remove_info->tlb, tlb_entry,
                        remove_info->keep_global_entries,
                        remove_info->pagesize)) {
                ht_remove_int(table, key, tlb_entry);
                MM_FREE(tlb_entry);
        }

        return 1;
}

static void
x86_tlb_flush_all_hasht(x86_tlb_t *tlb, int keep_global_entries)
{
        hash_remove_info_t remove_info;

        remove_info.tlb = tlb;
        remove_info.keep_global_entries = keep_global_entries;

        remove_info.pagesize = tlb->large_page_size;
        ht_for_each_entry(&tlb->imp->hash_large, hash_remove_entry, &remove_info);
        remove_info.pagesize = 4*1024;
        ht_for_each_entry(&tlb->imp->hash_4k, hash_remove_entry, &remove_info);
}

static void
x86_tlb_flush_page_hasht(x86_tlb_t *tlb, linear_address_t laddr)
{

        tlb_entry_t *tlb_entry;

        if ((tlb_entry = (tlb_entry_t *)ht_lookup_int(&tlb->imp->hash_large, laddr >> tlb->large_shift)) != NULL) {
                SIM_flush_D_STC_logical(tlb->cpu, tlb_entry->linear_page_start, tlb->large_page_size);
                ht_remove_int(&tlb->imp->hash_large, laddr >> tlb->large_shift, tlb_entry);
                MM_FREE(tlb_entry);
        }
        if ((tlb_entry = (tlb_entry_t *)ht_lookup_int(&tlb->imp->hash_4k, laddr >> 12)) != NULL) {
                SIM_flush_D_STC_logical(tlb->cpu, tlb_entry->linear_page_start, 4*1024);
                ht_remove_int(&tlb->imp->hash_4k, laddr >> 12, tlb_entry);
                MM_FREE(tlb_entry);
        }
}

static tlb_entry_t *
x86_tlb_lookup_common_hasht(x86_tlb_t *tlb, processor_mode_t mode,
                            read_or_write_t rw, data_or_instr_t tlb_select,
                            linear_address_t laddr, linear_address_t *offset)
{
        tlb_entry_t *tlb_entry = NULL;

        if ((tlb_entry = ht_lookup_int(&tlb->imp->hash_large, laddr >> tlb->large_shift)) != NULL) {
                *offset = laddr & (tlb->large_page_size - 1);
        } else if ((tlb_entry = ht_lookup_int(&tlb->imp->hash_4k, laddr >> 12)) != NULL) {
                *offset = laddr & (4*1024 - 1);
        }

        return tlb_entry;
}

static void
tlb_add_hash(x86_tlb_t *tlb, ht_table_t *hash, integer_t key,
             tlb_entry_t *new_tlb_entry, uint32 page_size)
{
        tlb_entry_t *tlb_entry = ht_lookup_int(hash, key);

        if (tlb_entry == NULL) {
                tlb_entry = MM_ZALLOC(1, tlb_entry_t);
                ht_insert_int(hash, key, tlb_entry);
        } else {
                if (tlb_entry->linear_page_start
                    == new_tlb_entry->linear_page_start) {
                        /* Remove STC entries for modified TLB entry */
                        SIM_flush_D_STC_logical(tlb->cpu,
                                                tlb_entry->linear_page_start,
                                                page_size);
                }
        }
        *tlb_entry = *new_tlb_entry;
}

static void
x86_tlb_add_hasht(x86_tlb_t *tlb, data_or_instr_t tlb_select,
                  tlb_entry_t *new_tlb_entry,
                  int page_code, uint32 pagesize)
{
        if (page_code == 2) {
                tlb_add_hash(tlb, &tlb->imp->hash_large,
                             new_tlb_entry->linear_page_start >> 22,
                             new_tlb_entry, pagesize);
        } else if (page_code == 1) {
                tlb_add_hash(tlb, &tlb->imp->hash_large,
                             new_tlb_entry->linear_page_start >> 21,
                             new_tlb_entry, pagesize);
        } else {
                tlb_add_hash(tlb, &tlb->imp->hash_4k,
                             new_tlb_entry->linear_page_start >> 12,
                             new_tlb_entry, pagesize);
        }
        SIM_c_hap_occurred_always(x86_hap_tlb_fill[tlb_select],
                                  &tlb->log.obj, page_code,
                                  (integer_t)new_tlb_entry->linear_page_start,
                                  (integer_t)new_tlb_entry->physical_page_start,
                                  (integer_t)page_code);
}

static set_error_t
set_x86_tlb_hasht(x86_tlb_id_t *id, x86_tlb_t *ptr, attr_value_t *val)
{
        int idx, way;

        if (val->kind != Sim_Val_List && val->kind != Sim_Val_Nil)
                return Sim_Set_Need_List;

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
                ht_clear_table(&ptr->imp->hash_large, 1, 0);
        } else { /* 4k */
                ht_clear_table(&ptr->imp->hash_4k, 1, 0);
        }

        if (val->kind == Sim_Val_List) {
                if (id->large) {
                        for (idx = 0; idx < val->u.list.size; idx++) {
                                for (way = 0; way < val->u.list.vector[idx].u.list.size; way++) {
                                        attr_value_t *tlb_entry = &val->u.list.vector[idx].u.list.vector[way];
                                        tlb_entry_t *entry = MM_ZALLOC(1, tlb_entry_t);
                                        set_tlb_entry(entry, tlb_entry);
                                        ht_insert_int(&ptr->imp->hash_large, entry->linear_page_start >> ptr->large_shift, entry);
                                }
                        }
                } else { /* 4k */
                        for (idx = 0; idx < val->u.list.size; idx++) {
                                for (way = 0; way < val->u.list.vector[idx].u.list.size; way++) {
                                        attr_value_t *tlb_entry = &val->u.list.vector[idx].u.list.vector[way];
                                        tlb_entry_t *entry = MM_ZALLOC(1, tlb_entry_t);
                                        set_tlb_entry(entry, tlb_entry);
                                        ht_insert_int(&ptr->imp->hash_4k, entry->linear_page_start >> 12, entry);
                                }
                        }
                }
        }

        return Sim_Set_Ok;
}

typedef struct {
        attr_value_t *attr;
        int i;
} hash_iter_t;

static int
get_hash_entry(ht_table_t *table, uint64 key, void *value, void *data)
{
        tlb_entry_t *entry = (tlb_entry_t *)value;
        hash_iter_t *iter = (hash_iter_t *)data;
        get_tlb_entry(&iter->attr->u.list.vector[iter->i], entry);
        iter->i++;
        return 1;
}

static attr_value_t
get_x86_tlb_hasht(x86_tlb_id_t *id, x86_tlb_t *ptr)
{
        attr_value_t ret;
        hash_iter_t hash_iter;
        if (id->large) {
                if (id->way != Sim_DI_Data)
                        return SIM_make_attr_nil();
                ret = SIM_alloc_attr_list(1);
                ret.u.list.vector[0] = SIM_alloc_attr_list(ht_num_entries(&ptr->imp->hash_large));
                hash_iter.attr = &ret.u.list.vector[0];
                hash_iter.i = 0;
                ht_for_each_entry(&ptr->imp->hash_large, get_hash_entry, &hash_iter);
                ASSERT(hash_iter.i == ret.u.list.vector[0].u.list.size);
        } else { /* 4k */
                if (id->way != Sim_DI_Data)
                        return SIM_make_attr_nil();
                ret = SIM_alloc_attr_list(1);
                ret.u.list.vector[0] = SIM_alloc_attr_list(ht_num_entries(&ptr->imp->hash_4k));
                hash_iter.attr = &ret.u.list.vector[0];
                hash_iter.i = 0;
                ht_for_each_entry(&ptr->imp->hash_4k, get_hash_entry, &hash_iter);
                ASSERT(hash_iter.i == ret.u.list.vector[0].u.list.size);
        }
        return ret;
}

mode_methods_t hash_mode_methods = {
        .name = "Hash table",
        .enter_mode = enter_tlb_mode_hasht,
        .leave_mode = leave_tlb_mode_hasht,
        .flush_all = x86_tlb_flush_all_hasht,
        .flush_page = x86_tlb_flush_page_hasht,
        .lookup = x86_tlb_lookup_common_hasht,
        .add = x86_tlb_add_hasht,
        .set = set_x86_tlb_hasht,
        .get = get_x86_tlb_hasht,
};
