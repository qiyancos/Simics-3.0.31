/*
  x86_tlb.c

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

#define DEVICE_INFO_STRING \
  "Default X86 TLB class."

#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>
#include <simics/arch/x86.h>

#include "x86_tlb.h"

#define DEVICE_NAME "x86-tlb"

static const char *x86_memory_type_descr[8];

hap_type_t x86_hap_tlb_invalidate[TLB_WAYS];
hap_type_t x86_hap_tlb_replace[TLB_WAYS];
hap_type_t x86_hap_tlb_fill[TLB_WAYS];
hap_type_t x86_hap_tlb_miss[TLB_WAYS];

int
flush_entry(x86_tlb_t *tlb, tlb_entry_t *tlb_entry, int keep_global_entries, int pagesize)
{
        if (!keep_global_entries || !tlb_entry->global_page) {
                SIM_flush_D_STC_logical(tlb->cpu, tlb_entry->linear_page_start, pagesize);
                SIM_c_hap_occurred_always(
                        x86_hap_tlb_invalidate[Sim_DI_Data],
                        &tlb->log.obj,
                        pagesize == 4096 ? 0 : pagesize >> 22 ? 2 : 1,
                        (integer_t)tlb_entry->linear_page_start,
                        (integer_t)tlb_entry->physical_page_start,
                        (integer_t)(pagesize == 4096 ? 0 : pagesize >> 22 ? 2 : 1));

                return 1;
        };
        return 0;
}

int
set_tlb_check_valid(attr_value_t *val, int assoc, int align_mask)
{
        int idx, way;

        for (idx = 0; idx < val->u.list.size; idx++) {
                if (val->u.list.vector[idx].kind != Sim_Val_List ||
                    (assoc && val->u.list.vector[idx].u.list.size != assoc))
                        return 0;
                for (way = 0; way < val->u.list.vector[idx].u.list.size; way++) {
                        attr_value_t *tlb_entry = &val->u.list.vector[idx].u.list.vector[way];
                        if (!valid_tlb_entry(tlb_entry, align_mask))
                                return 0;
                }
        }

        return 1;
}

static void
enter_tlb_mode(x86_tlb_t *tlb, mode_methods_t *new_mode)
{
        if (tlb->methods == new_mode)
                return;

        SIM_log_info(4, &tlb->log, 0, "going from %s to %s.",
                     tlb->methods->name, new_mode->name);

        if (tlb->log.obj.configured)
                SIM_STC_flush_cache(tlb->cpu);

        tlb->methods->leave_mode(tlb);
        tlb->methods = new_mode;
        tlb->methods->enter_mode(tlb);
}

static void
x86_tlb_flush_all(conf_object_t *obj, int keep_global_entries)
{
        x86_tlb_t *tlb = (x86_tlb_t *)obj;

        debug_log(2, &tlb->log, "Flush all (keep global: %d).", keep_global_entries);

        tlb->methods->flush_all(tlb, keep_global_entries);
}

static void
x86_tlb_flush_page(conf_object_t *obj,
                   linear_address_t laddr)
{
        x86_tlb_t *tlb = (x86_tlb_t *)obj;

        SIM_log_info(3, &tlb->log, 0, "Flush page 0x%llx.", laddr);

        tlb->methods->flush_page(tlb, laddr);
}

static tlb_entry_t *
x86_tlb_lookup_common(x86_tlb_t *tlb, processor_mode_t mode,
                      read_or_write_t rw, data_or_instr_t tlb_select,
                      linear_address_t laddr, physical_address_t *out_addr)
{
        linear_address_t offset = 0;
        tlb_entry_t *tlb_entry = NULL;

        tlb_entry = tlb->methods->lookup(tlb, mode, rw, tlb_select, laddr, &offset);

        /* The comparisions below depend those relations */
        CASSERT_STMT(Sim_CPU_Mode_User < Sim_CPU_Mode_Supervisor);
        CASSERT_STMT(Sim_RW_Read < Sim_RW_Write);
        if (tlb_entry && mode >= tlb_entry->mode && rw <= tlb_entry->rw) {
                *out_addr = tlb_entry->physical_page_start + offset;
                return tlb_entry;
        }

        SIM_c_hap_occurred_always(x86_hap_tlb_miss[tlb_select], &tlb->log.obj,
                                  laddr, (integer_t)laddr);
        SIM_clear_exception();
        return NULL;
}

static int
x86_tlb_lookup(conf_object_t *obj,
               x86_memory_transaction_t *mem_tr)
{
        x86_tlb_t *tlb = (x86_tlb_t *)obj;
        read_or_write_t rw;
        data_or_instr_t tlb_select;
        tlb_entry_t *entry;

        /* 
        ** Perform TLB lookup 
        ** Measurment on booting Linux showed that we hit roughly 75% in the 
        ** 4 meg TLB and 25% in the 4 k TLB (of all TLB hits) 
        */
        rw = (SIM_mem_op_is_write(&mem_tr->s) || mem_tr->fault_as_if_write)
                ? Sim_RW_Write : Sim_RW_Read;
        tlb_select = (SIM_mem_op_is_data(&mem_tr->s)
                      ? Sim_DI_Data
                      : Sim_DI_Instruction);

        entry = x86_tlb_lookup_common(tlb, mem_tr->mode, rw, tlb_select,
                                      mem_tr->linear_address,
                                      &mem_tr->s.physical_address);
        if (entry) {
                mem_tr->mtrr_type = entry->mtrr_type;
                mem_tr->pat_type = entry->pat_type;
        }
        return entry != NULL;
}

static void
x86_tlb_add(conf_object_t *obj,
            processor_mode_t mode,
            read_or_write_t read_or_write,
            data_or_instr_t tlb_select,
            int global_page,
            x86_memory_type_t pat_type,
            x86_memory_type_t mtrr_type,
            linear_address_t laddr,
            physical_address_t paddr,
            int page_code)
{
        tlb_entry_t new_tlb_entry;
        x86_tlb_t *tlb = (x86_tlb_t *)obj;
        linear_address_t pagesize;

        SIM_log_info(4, &tlb->log, 0, "Add %s %s %s l:0x%llx p:0x%llx sz %d.",
                     read_or_write == Sim_RW_Read ? "read" : "write",
                     tlb_select == Sim_DI_Data ? "data" : "instr",
                     global_page ? "global" : "nonglobal",
                     laddr, paddr, page_code);

        new_tlb_entry.mode = mode;
        /* Note: We cannot insert the page in the TLB with writes
           enabled if the current access is a read/fetch. A later write
           will generate a 'false' TLB miss that updates the dirty bit
           correctly. */
        new_tlb_entry.rw = read_or_write;
        new_tlb_entry.global_page = global_page;
	new_tlb_entry.pat_type = pat_type;
	new_tlb_entry.mtrr_type = mtrr_type;

        if (page_code == 2) {
                pagesize = 1 << 22;
        } else if (page_code == 1) {
                pagesize = 1 << 21;
        } else {
                pagesize = 1 << 12;
        }
        new_tlb_entry.linear_page_start = laddr & ~(pagesize - 1);
        new_tlb_entry.physical_page_start = paddr & ~(pagesize - 1);

        ASSERT(tlb->methods);
        ASSERT(tlb->methods->add);
        tlb->methods->add(tlb, tlb_select, &new_tlb_entry, page_code, pagesize);
}

static tagged_physical_address_t
x86_tlb_itlb_lookup(conf_object_t *obj,
                    linear_address_t laddr,
                    processor_mode_t mode)
{
        x86_tlb_t *tlb = (x86_tlb_t *)obj;
        tagged_physical_address_t ret;
        ret.valid = x86_tlb_lookup_common(tlb, mode, Sim_RW_Read,
                                          Sim_DI_Instruction,
                                          laddr, &ret.paddr) != NULL; 
        return ret;
}

static void
x86_cr4_write(lang_void *_ptr, conf_object_t *cpu_obj, integer_t reg_no, integer_t val)
{
        x86_tlb_t *ptr = (x86_tlb_t *)_ptr;
        /* Check if the hap is from the CPU this TLB is connected to */
        if (cpu_obj == ptr->cpu) {
                mode_methods_t *mode = ptr->methods;
                ASSERT(reg_no == SIM_get_register_number(cpu_obj, "cr4"));
                /* Check the PAE enable bit (bit 5) */
                if (ptr->in_pae_mode && !((val >> 5) & 1)) {
                        debug_log(1, &ptr->log, "Large TLB select: 4 Mb");
                        ptr->in_pae_mode = 0;
                        ptr->large_page_size = 4*1024*1024;
                        ptr->large_shift = 22;
                        if (mode == &hash_mode_methods)
                                mode = &full_table_mode_methods;
                } else if (!ptr->in_pae_mode && ((val >> 5) & 1)) {
                        debug_log(1, &ptr->log, "Large TLB select: 2 Mb");
                        ptr->in_pae_mode = 1;
                        ptr->large_page_size = 2*1024*1024;
                        ptr->large_shift = 21;
                        if (mode == &full_table_mode_methods)
                                mode = &hash_mode_methods;
                }
                enter_tlb_mode(ptr, mode);
        }
}

static conf_object_t *
x86_tlb_new_instance(parse_object_t *parse_obj)
{
        x86_tlb_t *ptr = MM_ZALLOC(1, x86_tlb_t);
        SIM_log_constructor(&ptr->log, parse_obj);

        ptr->methods = &limited_mode_methods;

        ptr->large_page_size = 4*1024*1024;
        ptr->large_shift = 22;

        ptr->methods->enter_mode(ptr);

        return (conf_object_t *)ptr;
}

static x86_tlb_id_t *
x86_tlb_id(data_or_instr_t way, int large)
{
        x86_tlb_id_t *ret = MM_ZALLOC(1, x86_tlb_id_t);
        ret->way = way;
        ret->large = large;
        return ret;
}

static set_error_t
set_cpu(void *_id, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        x86_tlb_t *ptr = (x86_tlb_t *)obj;
        ptr->cpu = val->u.object;
        SIM_hap_add_callback_index("Core_Control_Register_Write",
                                   (obj_hap_func_t)x86_cr4_write, ptr, SIM_get_register_number(ptr->cpu, "cr4"));
        return Sim_Set_Ok;
}

static attr_value_t
get_cpu(void *_id, conf_object_t *obj, attr_value_t *idx)
{
        x86_tlb_t *ptr = (x86_tlb_t *)obj;
        attr_value_t ret;
        if (ptr->cpu) {
                ret.kind = Sim_Val_Object;
                ret.u.object = ptr->cpu;
        } else {
                ret.kind = Sim_Val_Nil;
        }
        return ret;
}

static int
parse_memtype(const char *str)
{
        int i;
        for (i = 0; x86_memory_type_descr[i]; i++)
                if (strcmp(x86_memory_type_descr[i], str) == 0)
                        return i;
        return -1;
}

int
valid_tlb_entry(attr_value_t *tlb_entry, int align_mask)
{
        if (tlb_entry->kind != Sim_Val_List
            || (tlb_entry->u.list.size != 5 && tlb_entry->u.list.size != 7))
                return 0;
        attr_value_t *vector = tlb_entry->u.list.vector;
        if (vector[0].kind != Sim_Val_Integer ||
            vector[1].kind != Sim_Val_Integer ||
            vector[2].kind != Sim_Val_Integer ||
            vector[3].kind != Sim_Val_Integer ||
            vector[4].kind != Sim_Val_Integer)
                return 0;
        if (tlb_entry->u.list.size == 7) {
                if (vector[5].kind != Sim_Val_String ||
                    vector[6].kind != Sim_Val_String)
                        return 0;
                if (parse_memtype(vector[5].u.string) < 0)
                        return 0;
                if (parse_memtype(vector[6].u.string) < 0)
                        return 0;
        }
        if ((vector[0].u.integer & align_mask) ||
            (vector[1].u.integer & align_mask))
                return 0;
        return 1;
}

void
set_tlb_entry(tlb_entry_t *entry, attr_value_t *tlb_entry)
{
        entry->linear_page_start = tlb_entry->u.list.vector[0].u.integer;
        entry->physical_page_start = tlb_entry->u.list.vector[1].u.integer;
        entry->mode = tlb_entry->u.list.vector[2].u.integer ?
                Sim_CPU_Mode_Supervisor : Sim_CPU_Mode_User;
        entry->rw = tlb_entry->u.list.vector[3].u.integer ?
                Sim_RW_Read : Sim_RW_Write;
        entry->global_page = tlb_entry->u.list.vector[4].u.integer;
        if (tlb_entry->u.list.size == 7) {
                entry->pat_type = parse_memtype(tlb_entry->u.list.vector[5]
                                                .u.string);
                entry->mtrr_type = parse_memtype(tlb_entry->u.list.vector[6]
                                                 .u.string);
        } else {
                entry->pat_type = X86_None;
                entry->mtrr_type = X86_None;
        }
}

void
get_tlb_entry(attr_value_t *tlb_entry, tlb_entry_t *entry)
{
        *tlb_entry = SIM_make_attr_list(7,
                SIM_make_attr_integer(entry->linear_page_start),
                SIM_make_attr_integer(entry->physical_page_start),
                SIM_make_attr_integer(entry->mode == Sim_CPU_Mode_Supervisor),
                SIM_make_attr_integer(entry->rw == Sim_RW_Read),
                SIM_make_attr_integer(entry->global_page),
                SIM_make_attr_string(x86_memory_type_descr[entry->pat_type]),
                SIM_make_attr_string(x86_memory_type_descr[entry->mtrr_type])
        );
}

static set_error_t
set_x86_tlb(void *_id, conf_object_t *obj, attr_value_t *val, attr_value_t *_unused)
{
        x86_tlb_id_t *id = (x86_tlb_id_t *)_id;
        x86_tlb_t *ptr = (x86_tlb_t *)obj;

        if (val->kind != Sim_Val_List && val->kind != Sim_Val_Nil)
                return Sim_Set_Need_List;

        set_error_t ret = ptr->methods->set(id, ptr, val);

        /* Flush data structures that depend on the address mapping. */
        if (ptr->cpu)
                SIM_STC_flush_cache(ptr->cpu);
        return ret;
}

static attr_value_t
get_x86_tlb(void *_id, conf_object_t *obj, attr_value_t *_unused)
{
        x86_tlb_id_t *id = (x86_tlb_id_t *)_id;
        x86_tlb_t *ptr = (x86_tlb_t *)obj;
        return ptr->methods->get(id, ptr);
}

static set_error_t
set_tlb_select(void *_id, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        x86_tlb_t *ptr = (x86_tlb_t *)obj;
        mode_methods_t *old_mode = ptr->methods;
        mode_methods_t *new_mode = old_mode;
        if (val->kind != Sim_Val_Integer)
                return Sim_Set_Need_Integer;
        if (val->u.integer != 2 && val->u.integer != 4)
                return Sim_Set_Illegal_Value;
        ptr->in_pae_mode = (val->u.integer == 2);
        if (ptr->in_pae_mode) {
                ptr->large_page_size = 2*1024*1024;
                ptr->large_shift = 21;
        } else {
                ptr->large_page_size = 4*1024*1024;
                ptr->large_shift = 22;
        }
        if (old_mode == &full_table_mode_methods && ptr->in_pae_mode)
                new_mode = &hash_mode_methods;
        else if (old_mode == &hash_mode_methods && !ptr->in_pae_mode)
                new_mode = &full_table_mode_methods;
        enter_tlb_mode(ptr, new_mode);
        return Sim_Set_Ok;
}

static attr_value_t
get_tlb_select(void *_id, conf_object_t *obj, attr_value_t *idx)
{
        x86_tlb_t *ptr = (x86_tlb_t *)obj;
        return SIM_make_attr_integer(ptr->in_pae_mode ? 2 : 4);
}

static set_error_t
set_tlb_type(void *_id, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        x86_tlb_t *ptr = (x86_tlb_t *)obj;
        if (strcmp(val->u.string, "normal") == 0) {
                enter_tlb_mode(ptr, &limited_mode_methods);
                return Sim_Set_Ok;
        } else if (strcmp(val->u.string, "unlimited") == 0) {
                mode_methods_t *new_mode;
                if (ptr->in_pae_mode)
                        new_mode = &hash_mode_methods;
                else
                        new_mode = &full_table_mode_methods;
                enter_tlb_mode(ptr, new_mode);
                return Sim_Set_Ok;
        } else {
                return Sim_Set_Illegal_Value;
        }
}

static attr_value_t
get_tlb_type(void *_id, conf_object_t *obj, attr_value_t *idx)
{
        x86_tlb_t *ptr = (x86_tlb_t *)obj;
        if (ptr->methods == &limited_mode_methods)
                return SIM_make_attr_string("normal");
        else
                return SIM_make_attr_string("unlimited");
}

#define TLB_FORMAT_STRING \
   "(((la, pa, mode, rw, g, pat_type, mtrr_type){associativity}){way-size}). "

DLL_EXPORT void
init_local(void)
{
        class_data_t           class_data;
        conf_class_t          *conf_class;
        x86_tlb_interface_t   *tlb_iface;
        x86_tlb_id_t          *tlb_id;

        memset(&class_data, 0, sizeof(class_data_t));
        class_data.new_instance = x86_tlb_new_instance;
        class_data.description = DEVICE_INFO_STRING;
        conf_class = SIM_register_class(DEVICE_NAME, &class_data);

        tlb_iface = MM_ZALLOC(1, x86_tlb_interface_t);
        tlb_iface->flush_all = x86_tlb_flush_all;
        tlb_iface->flush_page = x86_tlb_flush_page;
        tlb_iface->lookup = x86_tlb_lookup;
        tlb_iface->add = x86_tlb_add;
        tlb_iface->itlb_lookup = x86_tlb_itlb_lookup;
        SIM_register_interface(conf_class, X86_TLB_INTERFACE, tlb_iface);

        SIM_register_typed_attribute(conf_class, "cpu", get_cpu, 0,
                set_cpu, 0, Sim_Attr_Required, "o", NULL,
                "CPU object to which TLB object is bound.");
        SIM_register_typed_attribute(conf_class, "type", get_tlb_type, 0,
                set_tlb_type, 0, Sim_Attr_Optional, "s", NULL,
                "Type of TLB. Can be either normal for a set associative TLB,"
                " or unlimited for a very large TLB.");
        SIM_register_attribute(conf_class, "large_tlb_select", get_tlb_select,
                0, set_tlb_select, 0, Sim_Attr_Optional,
                "Determines the size for pages mapped in the large page TLBs."
                " 2 for 2Mb and 4 for 4Mb.");
        tlb_id = x86_tlb_id(Sim_DI_Instruction, 1);
        SIM_register_attribute(conf_class, "itlb_large", get_x86_tlb,
                tlb_id, set_x86_tlb, tlb_id, Sim_Attr_Optional,
                TLB_FORMAT_STRING "Instruction TLB for 2Mb and 4Mb pages.");
        tlb_id = x86_tlb_id(Sim_DI_Data, 1);
        SIM_register_attribute(conf_class, "dtlb_large", get_x86_tlb,
                tlb_id, set_x86_tlb, tlb_id, Sim_Attr_Optional,
                TLB_FORMAT_STRING "Data TLB for 2Mb and 4Mb pages.");
        tlb_id = x86_tlb_id(Sim_DI_Instruction, 0);
        SIM_register_attribute(conf_class, "itlb_4k", get_x86_tlb,
                tlb_id, set_x86_tlb, tlb_id, Sim_Attr_Optional,
                TLB_FORMAT_STRING "Instruction TLB for 4kb pages.");
        tlb_id = x86_tlb_id(Sim_DI_Data, 0);
        SIM_register_attribute(conf_class, "dtlb_4k", get_x86_tlb,
                tlb_id, set_x86_tlb, tlb_id, Sim_Attr_Optional,
                TLB_FORMAT_STRING "Data TLB for 4kb pages.");

	x86_memory_type_descr[X86_None] = "none";
        x86_memory_type_descr[X86_Strong_Uncacheable] = "UC";
	x86_memory_type_descr[X86_Uncacheable] = "UC-";
	x86_memory_type_descr[X86_Write_Combining] = "WC";
	x86_memory_type_descr[X86_Write_Through] = "WT";
	x86_memory_type_descr[X86_Write_Back] = "WB";
	x86_memory_type_descr[X86_Write_Protected] = "WP";

        x86_hap_tlb_fill[Sim_DI_Instruction] =
                SIM_hap_add_type("TLB_Fill_Instruction",
                                 "III", "linear physical page_size",
                                 "page_size",
                                 "Triggered when a TLB entry is filled after a table walk. "
                                 "Page size encoding: 0==4k, 1==2M, 2==4M.", 0);
        x86_hap_tlb_fill[Sim_DI_Data] =
                SIM_hap_add_type("TLB_Fill_Data",
                                 "III", "linear physical page_size",
                                 "page_size",
                                 "Triggered when a TLB entry is filled after a table walk. "
                                 "Page size encoding: 0==4k, 1==2M, 2==4M.", 0);
        x86_hap_tlb_replace[Sim_DI_Instruction] =
                SIM_hap_add_type("TLB_Replace_Instruction",
                                 "III", "linear physical page_size",
                                 "page_size",
                                 "This hap is triggered when a TLB entry is replaced by "
                                 "another. The parameters relate to the old entry, and the "
                                 "insertion of the new entry will trigger a fill hap. "
                                 "Page size encoding: 0==4k, 1==2M, 2==4M.", 0);
        x86_hap_tlb_replace[Sim_DI_Data] =
                SIM_hap_add_type("TLB_Replace_Data",
                                 "III", "linear physical page_size",
                                 "page_size",
                                 "This hap is triggered when a TLB entry is replaced by "
                                 "another. The parameters relate to the old entry, and the "
                                 "insertion of the new entry will trigger a fill hap. "
                                 "Page size encoding: 0==4k, 1==2M, 2==4M.", 0);
        x86_hap_tlb_invalidate[Sim_DI_Instruction] =
                SIM_hap_add_type("TLB_Invalidate_Instruction",
                                 "III", "linear physical page_size",
                                 "page_size",
                                 "Triggered when a TLB entry is invalidated. The invalidation "
                                 "can be caused by an INVLPG instruction, a write to CR3, "
                                 "or by changes to paging bits in CR0 and CR4. "
                                 "Page size encoding: 0==4k, 1==2M, 2==4M.", 0);
        x86_hap_tlb_invalidate[Sim_DI_Data] =
                SIM_hap_add_type("TLB_Invalidate_Data",
                                 "III", "linear physical page_size",
                                 "page_size",
                                 "Triggered when a TLB entry is invalidated. The invalidation "
                                 "can be caused by an INVLPG instruction, a write to CR3, "
                                 "or by changes to paging bits in CR0 and CR4. "
                                 "Page size encoding: 0==4k, 1==2M, 2==4M.", 0);
        x86_hap_tlb_miss[Sim_DI_Instruction] =
                SIM_hap_add_type("TLB_Miss_Instruction",
                                 "I", "linear_address",
                                 "linear_address",
                                 "Triggered when an ITLB miss occurs.", 0);
        x86_hap_tlb_miss[Sim_DI_Data] =
                SIM_hap_add_type("TLB_Miss_Data",
                                 "I", "linear_address",
                                 "linear_address",
                                 "Triggered when a DTLB miss occurs.", 0);
}
