/*
  assoc.c

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

/* Define here the size and associativity */
#define X86_4K_TLB_SIZE 16
#define X86_4K_TLB_ASSOC 4
#define X86_LARGE_TLB_SIZE 16
#define X86_LARGE_TLB_ASSOC 4

struct x86_tlb_impl
{
        /* Limited size mode */
        tlb_entry_t             pc_tlb_4k[TLB_WAYS][X86_4K_TLB_SIZE][X86_4K_TLB_ASSOC];
        tlb_entry_t             pc_tlb_large[TLB_WAYS][X86_LARGE_TLB_SIZE][X86_LARGE_TLB_ASSOC];
};

#define INVALIDATE(entry) (entry).linear_page_start = 1
#define ISVALID(entry)    ((entry).linear_page_start != 1)

static void
enter_tlb_mode_limited(x86_tlb_t *tlb)
{
        int i, j, k;

        tlb->imp = MM_ZALLOC(1, x86_tlb_impl_t);
        for (i = 0; i < TLB_WAYS; i++)
                for (j = 0; j < X86_4K_TLB_SIZE; j++)
                        for (k = 0; k < X86_4K_TLB_ASSOC; k++)
                                INVALIDATE(tlb->imp->pc_tlb_4k[i][j][k]);
        for (i = 0; i < TLB_WAYS; i++)
                for (j = 0; j < X86_LARGE_TLB_SIZE; j++)
                        for (k = 0; k < X86_LARGE_TLB_ASSOC; k++)
                                INVALIDATE(tlb->imp->pc_tlb_large[i][j][k]);
}

static void
leave_tlb_mode_limited(x86_tlb_t *tlb)
{
        MM_FREE(tlb->imp);
        tlb->imp = NULL;
}

enum cond { Cond_Always, Cond_Nonglobal, Cond_Matching };

static void
flush_tlb_assoc_one(x86_tlb_t *tlb, int large, int select,
                    enum cond when, linear_address_t la, data_or_instr_t way)
{
        int k, prev_size;
        int entries_flushed = 0;
        tlb_entry_t *table = large ? tlb->imp->pc_tlb_large[way][select]
                                   : tlb->imp->pc_tlb_4k[way][select];
        int assoc_size = large ? X86_LARGE_TLB_ASSOC : X86_4K_TLB_ASSOC;
        int page_code = large ? (tlb->in_pae_mode ? 1 : 2) : 0;

        for (k = 0; k < assoc_size; k++) {
                if (!ISVALID(table[k]))
                        break;
                if (when == Cond_Nonglobal) {
                        if (table[k].global_page) continue;
                } else if (when == Cond_Matching) {
                        if (la != table[k].linear_page_start) continue;
                }
                /* flush this entry */
                entries_flushed++;
                SIM_c_hap_occurred_always(
                        x86_hap_tlb_invalidate[way],
                        &tlb->log.obj,
                        page_code,
                        (integer_t)table[k].linear_page_start,
                        (integer_t)table[k].physical_page_start,
                        (integer_t)page_code);
                SIM_clear_exception();
                if (when != Cond_Always)
                        SIM_flush_D_STC_logical(tlb->cpu,
                                table[k].linear_page_start,
                                large ? tlb->large_page_size : 4096);
                INVALIDATE(table[k]);
        }
        prev_size = k;

        /* Pack the entries if holes appeared */
        if (entries_flushed == 0 || entries_flushed == prev_size)
                return;
        int next_slot = 0;
        for (k = 0; k < prev_size; k++) {
                if (ISVALID(table[k]))
                        table[next_slot++] = table[k];
        }
        for (; next_slot < prev_size; next_slot++)
                INVALIDATE(table[next_slot]);
}

static void
flush_tlb_assoc(x86_tlb_t *tlb, int large, int select,
                enum cond when, linear_address_t la)
{
        flush_tlb_assoc_one(tlb, large, select, when, la, Sim_DI_Data);
        flush_tlb_assoc_one(tlb, large, select, when, la, Sim_DI_Instruction);
}

static void
x86_tlb_flush_all_limited(x86_tlb_t *tlb, int keep_global_entries)
{
        int i;
        if (keep_global_entries) {
                for (i = 0; i < X86_LARGE_TLB_SIZE; i++)
                        flush_tlb_assoc(tlb, 1, i, Cond_Nonglobal, 0);
                for (i = 0; i < X86_4K_TLB_SIZE; i++)
                        flush_tlb_assoc(tlb, 0, i, Cond_Nonglobal, 0);
        } else {
                /* Flush all TLB entries, PGE not supported or everything
                   should be flushed */
                for (i = 0; i < X86_LARGE_TLB_SIZE; i++)
                        flush_tlb_assoc(tlb, 1, i, Cond_Always, 0);
                for (i = 0; i < X86_4K_TLB_SIZE; i++)
                        flush_tlb_assoc(tlb, 0, i, Cond_Always, 0);
                SIM_STC_flush_cache(tlb->cpu);
        }
}

static void
x86_tlb_flush_page_limited(x86_tlb_t *tlb, linear_address_t laddr)
{
        int tlb_index;
        linear_address_t linear_page_start;

        /* Check the 4M/2M TLB entries, clear the page entry if found */
        linear_page_start = laddr & ~(tlb->large_page_size - 1);
        tlb_index = (laddr >> tlb->large_shift) & (X86_LARGE_TLB_SIZE-1);
        flush_tlb_assoc(tlb, 1, tlb_index,
                        Cond_Matching, linear_page_start);
        
        /* Check the 4K TLB entries, clear the page entry if found */
        linear_page_start = laddr & ~0xfff;
        tlb_index = (laddr >> 12) & (X86_4K_TLB_SIZE-1);
        flush_tlb_assoc(tlb, 0, tlb_index,
                        Cond_Matching, linear_page_start);
}

static tlb_entry_t *
x86_tlb_lookup_limited(x86_tlb_t *tlb, processor_mode_t mode,
                       read_or_write_t rw, data_or_instr_t tlb_select,
                       linear_address_t laddr, linear_address_t *offset)
{
        linear_address_t linear_page_start;
	int k;
        int tlb_index;
        tlb_entry_t *tlb_entry = NULL;

        /* First look in the 2M/4M TLB */
        linear_page_start = laddr & ~(tlb->large_page_size - 1);
        tlb_index = (laddr >> tlb->large_shift) & (X86_LARGE_TLB_SIZE-1);
        *offset = laddr & (tlb->large_page_size - 1);
        for (k = 0; k < X86_LARGE_TLB_ASSOC; k++) {
                if (linear_page_start == tlb->imp->pc_tlb_large[tlb_select][tlb_index][k].linear_page_start) {
                        tlb_entry = &tlb->imp->pc_tlb_large[tlb_select][tlb_index][k];
                        break;
                }
        }

        if (!tlb_entry) {
                /* Now check the 4K TLB */
                linear_page_start = laddr & ~0xfff;
                tlb_index = (laddr >> 12) & (X86_4K_TLB_SIZE-1);
                *offset = laddr & 0xfff;
                for (k = 0; k < X86_4K_TLB_ASSOC; k++) {
                        if (linear_page_start == tlb->imp->pc_tlb_4k[tlb_select][tlb_index][k].linear_page_start) {
                                tlb_entry = &tlb->imp->pc_tlb_4k[tlb_select][tlb_index][k];
                                break;
                        }
                }
        }
        return tlb_entry;
}

static void
tlb_add_assoc(x86_tlb_t *tlb, data_or_instr_t tlb_select,
              tlb_entry_t *table, int assoc_size, tlb_entry_t *new_entry,
              linear_address_t page_size, int page_code)
{
        int k;
        int first_free = -1;

        for (k = 0; k < assoc_size; k++) {
                if (table[k].linear_page_start
                    == new_entry->linear_page_start) {
                        /* Remove STC entries for modified TLB entry */
                        SIM_flush_D_STC_logical(tlb->cpu,
                                                table[k].linear_page_start,
                                                page_size);
                        break;
                }
                else if (!ISVALID(table[k]) && first_free == -1)
                        first_free = k;
        }
        if (k == assoc_size && first_free >= 0)
                k = first_free;
        if (k == assoc_size) {
                /* Move entries up through FIFO, evict entry 0, fill entry
                   ASSOC-1 */
                k = assoc_size - 1;
                SIM_c_hap_occurred_always(x86_hap_tlb_replace[tlb_select],
                                  &tlb->log.obj, page_code,
                                  (integer_t)table[0].linear_page_start,
                                  (integer_t)table[0].physical_page_start,
                                  (integer_t)page_code);
                SIM_clear_exception();
                /* Remove STC entries for overwritten TLB entry */
                SIM_flush_D_STC_logical(tlb->cpu, table[0].linear_page_start,
                                        page_size);
                int move;
                for (move = 0; move < assoc_size-1; move++)
                        table[move] = table[move+1];
        }
        SIM_c_hap_occurred_always(x86_hap_tlb_fill[tlb_select],
                                  &tlb->log.obj, page_code,
                                  (integer_t)new_entry->linear_page_start,
                                  (integer_t)new_entry->physical_page_start,
                                  (integer_t)page_code);
        SIM_clear_exception();
        table[k] = *new_entry;
}

static void
x86_tlb_add_limited(x86_tlb_t *tlb,
                    data_or_instr_t tlb_select,
                    tlb_entry_t *new_tlb_entry,
                    int page_code,
                    uint32 pagesize)
{
        int tlb_index;
        linear_address_t laddr = new_tlb_entry->linear_page_start;
        if (page_code > 0) {
                /* The page table entry represented a large page */
                tlb_index = (laddr >> tlb->large_shift) & (X86_LARGE_TLB_SIZE-1);
                tlb_add_assoc(tlb, tlb_select,
                              tlb->imp->pc_tlb_large[tlb_select][tlb_index],
                              X86_LARGE_TLB_ASSOC,
                              new_tlb_entry,
                              pagesize,
                              page_code);
        } else {
                /* The page table entry represented a 4K page */
                tlb_index = (laddr >> 12) & (X86_4K_TLB_SIZE-1);
                tlb_add_assoc(tlb, tlb_select,
                              tlb->imp->pc_tlb_4k[tlb_select][tlb_index],
                              X86_4K_TLB_ASSOC,
                              new_tlb_entry,
                              pagesize,
                              page_code);
        }
}

static set_error_t
set_x86_tlb_limited(x86_tlb_id_t *id, x86_tlb_t *ptr, attr_value_t *val)
{
        int idx, way;

        if (val->kind != Sim_Val_List && val->kind != Sim_Val_Nil)
                return Sim_Set_Need_List;

        if (val->kind == Sim_Val_List) {
                if (id->large) {
                        /* we can handle the case where the tlb is larger than in the checkpoint */
                        if (val->u.list.size > X86_LARGE_TLB_SIZE)
                                return Sim_Set_Illegal_Value;
                        if (!set_tlb_check_valid(val, X86_LARGE_TLB_ASSOC, (ptr->large_page_size - 1) & ~(linear_address_t)1))
                                return Sim_Set_Illegal_Value;
                } else { /* 4k */
                        /* we can handle the case where the tlb is larger than in the checkpoint */
                        if (val->u.list.size > X86_4K_TLB_SIZE)
                                return Sim_Set_Illegal_Value;
                        if (!set_tlb_check_valid(val, X86_4K_TLB_ASSOC, 0xffe))
                                return Sim_Set_Illegal_Value;
                }
        }

        if (id->large) {
                for (idx = 0; idx < X86_LARGE_TLB_SIZE; idx++) {
                        for (way = 0; way < X86_LARGE_TLB_ASSOC; way++) {
                                INVALIDATE(ptr->imp->pc_tlb_large[id->way][idx][way]);
                        }
                }
        } else { /* 4k */
                for (idx = 0; idx < X86_4K_TLB_SIZE; idx++) {
                        for (way = 0; way < X86_4K_TLB_ASSOC; way++) {
                                INVALIDATE(ptr->imp->pc_tlb_4k[id->way][idx][way]);
                        }
                }
        }

        if (val->kind == Sim_Val_List) {
                if (id->large) {
                        for (idx = 0; idx < val->u.list.size; idx++) {
                                for (way = 0; way < X86_LARGE_TLB_ASSOC; way++) {
                                        attr_value_t *tlb_entry = &val->u.list.vector[idx].u.list.vector[way];
                                        tlb_entry_t *entry = &ptr->imp->pc_tlb_large[id->way][idx][way];
                                        set_tlb_entry(entry, tlb_entry);
                                }
                        }
                } else { /* 4k */
                        for (idx = 0; idx < val->u.list.size; idx++) {
                                for (way = 0; way < X86_4K_TLB_ASSOC; way++) {
                                        attr_value_t *tlb_entry = &val->u.list.vector[idx].u.list.vector[way];
                                        tlb_entry_t *entry = &ptr->imp->pc_tlb_4k[id->way][idx][way];
                                        set_tlb_entry(entry, tlb_entry);
                                }
                        }
                }
        }

        return Sim_Set_Ok;
}

static attr_value_t
get_x86_tlb_limited(x86_tlb_id_t *id, x86_tlb_t *ptr)
{
        int idx, way;
        attr_value_t ret;
        if (id->large) {
                ret = SIM_alloc_attr_list(X86_LARGE_TLB_SIZE);
                for (idx = 0; idx < X86_LARGE_TLB_SIZE; idx++) {
                        ret.u.list.vector[idx] = SIM_alloc_attr_list(X86_LARGE_TLB_ASSOC);
                        for (way = 0; way < X86_LARGE_TLB_ASSOC; way++) {
                                attr_value_t *tlb_entry = &ret.u.list.vector[idx].u.list.vector[way];
                                tlb_entry_t *entry = &ptr->imp->pc_tlb_large[id->way][idx][way];
                                get_tlb_entry(tlb_entry, entry);
                        }
                }
        } else { /* 4k */
                ret = SIM_alloc_attr_list(X86_4K_TLB_SIZE);
                for (idx = 0; idx < X86_4K_TLB_SIZE; idx++) {
                        ret.u.list.vector[idx] = SIM_alloc_attr_list(X86_4K_TLB_ASSOC);
                        for (way = 0; way < X86_4K_TLB_ASSOC; way++) {
                                attr_value_t *tlb_entry = &ret.u.list.vector[idx].u.list.vector[way];
                                tlb_entry_t *entry = &ptr->imp->pc_tlb_4k[id->way][idx][way];
                                get_tlb_entry(tlb_entry, entry);
                        }
                }
        }
        return ret;
}

mode_methods_t limited_mode_methods = {
        .name = "Limited mode",
        .enter_mode = enter_tlb_mode_limited,
        .leave_mode = leave_tlb_mode_limited,
        .flush_all = x86_tlb_flush_all_limited,
        .flush_page = x86_tlb_flush_page_limited,
        .lookup = x86_tlb_lookup_limited,
        .add = x86_tlb_add_limited,
        .set = set_x86_tlb_limited,
        .get = get_x86_tlb_limited,
};
