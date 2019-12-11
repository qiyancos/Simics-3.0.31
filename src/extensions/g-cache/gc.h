/*
  gc.h - g-cache definitions

  Copyright 2003-2007 Virtutech AB
  
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

#ifdef HOOK_HEADER
#  include "gc-hook.h"
#else
#  define HOOK_EXTRA_DATA
#  define HOOK_EXTRA_LINE_DATA
#endif

/* cache line definition */
typedef struct cache_line {
        cache_line_status_t status;
        integer_t tag;        /* tag of the data contained in the cache line */
        integer_t otag;       /* opposite tag (virtual if tag is physical) */

        /* in-order specific info */
        int STC_type;         /* STC that may contain the cache line data */

        HOOK_EXTRA_LINE_DATA  /* hook, see above */
} cache_line_t;

/* generic cache object structure */
struct generic_cache {
        
        log_object_t log;

        cache_line_t   *lines;  /* cache lines */

        conf_object_t  **cpus;  /* cpus sending memory transactions */
        int            cpus_count;

        struct {
                int line_number;    /* number of cache lines */
                int line_size;      /* size of a cache line */
                int assoc;          /* associativity */

                int virtual_index;  /* virtual address used for index */
                int virtual_tag;    /* virtual address used for tag */

                int write_allocate; /* allocate on write */
                int write_back;     /* write-through/write-back */

                int block_STC;      /* prevent usage of the STC so the cache
                                       sees all the transactions */

                /* replacement policy system */
                void *repl_data;    /* data allocated by the replacement
                                       policy */
                repl_interface_t repl_fun; /* copy of the current repl.
                                              policy functions */
                
                /* precomputed values */
                int mesi;       /* activate the coherence protocol */
                int no_STC;     /* tell the cache whether it should allow STC
                                   usage */

                int line_size_ln2;
                int next_assoc;
                integer_t tag_mask;
                integer_t index_mask;

                /* These two variables check if this cache is receiving direct
                   read/writes from the processor. If 1, the cache should
                   handle the corresponding DSTC counts as hits, otherwise
                   ignore them. */
                int direct_read_listener;
                int direct_write_listener;
        } config;

        struct {
                int read;
                int read_next;
                int write;
                int write_next;
        } penalty;

        struct {
                integer_t transaction;

                /* device transactions (DMA) */
                integer_t dev_data_read;
                integer_t dev_data_write;

                /* uncacheable transactions */
                integer_t uc_data_read;
                integer_t uc_data_write;
                integer_t uc_inst_fetch;

                /* usual transactions */
                integer_t data_read;
                integer_t data_read_miss;
                integer_t data_write;
                integer_t data_write_miss;
                integer_t inst_fetch;
                integer_t inst_fetch_miss;

                integer_t copy_back;

                integer_t mesi_exclusive_to_shared;
                integer_t mesi_modified_to_shared;
                integer_t mesi_invalidate;

                integer_t lost_stall_cycles;
        } stat;

        struct {
                conf_object_t *obj;
                prof_data_t *id;
        } prof[GC_Max_Profilers];

        conf_object_t *timing_model;
        timing_model_interface_t *timing_ifc;

        /* caches listening on the bus - for mesi protocol */
        conf_object_t **snoopers;
        mesi_listen_interface_t **snoopers_ifc;
        int snoopers_size;

        /* higher level caches - for mesi protocol */
        conf_object_t **hlc;
        mesi_listen_interface_t **hlc_ifc;
        int hlc_size;

        HOOK_EXTRA_DATA /* hook, see above */
};

int lookup_line(generic_cache_t *gc, generic_transaction_t *mem_op);
cycles_t copy_back(generic_cache_t *gc, int line_num, 
                   generic_transaction_t *mem_op, conf_object_t *space, 
                   map_list_t *map, int write_back);
cycles_t empty_line(generic_cache_t *gc, int line_num, 
                    generic_transaction_t *mem_op, conf_object_t *space, 
                    map_list_t *map);
cycles_t fetch_line(generic_cache_t *gc, int line_num, 
                    generic_transaction_t *mem_op, conf_object_t *space, 
                    map_list_t *map);
cycles_t mesi_snoop_transaction(generic_cache_t *gc, 
                                generic_transaction_t *mem_op);
cycles_t mesi_snoop_transaction_export(conf_object_t *obj,
                                       generic_transaction_t *mem_op);
void flush_STC(generic_cache_t *gc, uint64 tag, uint64 otag, int STC_type, 
               cache_line_status_t status);

void gc_register(conf_class_t *gc_class);
void ts_init_local(void);
void update_precomputed_values(generic_cache_t *gc);
