/*
  x86_tlb.h

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

#include <simics/api.h>
#include <simics/arch/x86.h>

#define TLB_WAYS 2 /* instruction or data */

extern hap_type_t x86_hap_tlb_invalidate[TLB_WAYS];
extern hap_type_t x86_hap_tlb_replace[TLB_WAYS];
extern hap_type_t x86_hap_tlb_fill[TLB_WAYS];
extern hap_type_t x86_hap_tlb_miss[TLB_WAYS];

typedef struct {
        data_or_instr_t  way;
        int              large;
} x86_tlb_id_t;

typedef struct tlb_entry {
        linear_address_t        linear_page_start;
        physical_address_t      physical_page_start;
        processor_mode_t        mode:2;
        read_or_write_t         rw:1;
        unsigned                global_page:1;
        x86_memory_type_t       pat_type;
        x86_memory_type_t       mtrr_type;
} tlb_entry_t;

typedef struct mode_methods mode_methods_t;
typedef struct x86_tlb_impl x86_tlb_impl_t;

typedef struct x86_tlb
{
        log_object_t            log;
        conf_object_t          *cpu;

        mode_methods_t         *methods;
        int                     in_pae_mode;

        linear_address_t        large_page_size;
        int                     large_shift;

        x86_tlb_impl_t         *imp;

} x86_tlb_t;

struct mode_methods {
        const char *name;
        void (*enter_mode)(x86_tlb_t *tlb);
        void (*leave_mode)(x86_tlb_t *tlb);
        void (*flush_all)(x86_tlb_t *tlb, int keep_global_entries);
        void (*flush_page)(x86_tlb_t *tlb, linear_address_t laddr);
        tlb_entry_t *(*lookup)(x86_tlb_t *tlb, processor_mode_t mode,
                               read_or_write_t rw, data_or_instr_t tlb_select,
                               linear_address_t laddr, linear_address_t *offset);
        void (*add)(x86_tlb_t *tlb, data_or_instr_t tlb_select,
                    tlb_entry_t *new_tlb_entry, int page_code, uint32 pagesize);
        set_error_t (*set)(x86_tlb_id_t *id, x86_tlb_t *ptr, attr_value_t *val);
        attr_value_t (*get)(x86_tlb_id_t *id, x86_tlb_t *ptr);
};

int valid_tlb_entry(attr_value_t *tlb_entry, int align_mask);
void set_tlb_entry(tlb_entry_t *entry, attr_value_t *tlb_entry);
void get_tlb_entry(attr_value_t *tlb_entry, tlb_entry_t *entry);
int flush_entry(x86_tlb_t *tlb, tlb_entry_t *tlb_entry, int keep_global_entries, int pagesize);
int set_tlb_check_valid(attr_value_t *val, int assoc, int align_mask);

extern mode_methods_t limited_mode_methods;
extern mode_methods_t hash_mode_methods;
extern mode_methods_t full_table_mode_methods;
