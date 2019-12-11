/*
  gc.h - g-cache-ooo definitions

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

/* current operation in a cache line */
typedef enum cache_line_trans_status {
        CLT_None     = 0,  /* nothing happening here */
        CLT_Fill     = 1,  /* waiting for data from next cache */
        CLT_CopyBack = 2,  /* waiting for copy back transaction
                              to complete */
} cache_line_trans_status_t;

/* cache line definition */
typedef struct cache_line {
        cache_line_status_t status; 
        integer_t tag;        /* tag of the data contained in the cache line */
        integer_t otag;       /* opposite tag (physical address if tag
                                 is based on the virtual address) */

        /* out-of-order info */
        struct {
                cache_line_trans_status_t status; /* current line status */
                integer_t  next_tag;    /* next tag present when this
                                           transaction is finished */
                uinteger_t start_time;  /* when did the status started */
                uinteger_t busy_time;   /* how long does it last */
                int id;                 /* parent transaction's id */
                conf_object_t *ini_ptr; /* parent transaction's ini_ptr */
                
                int next_id;            /* next transaction id - if -1 then 
                                           no reissue to next level */
        } busy;
} cache_line_t;

/* outstanding transaction 
   - used to get the right line number when reissuing 
   - used to control the total amount of outstanding transactions 
*/
typedef struct trans_line {
        int id;                 /* transaction id */
        conf_object_t *ini_ptr; /* transaction parent */
        int line;               /* cache line if already affected - if line
                                   is -1, then the transaction is already 
                                   processed and stay for limit purposes */
        integer_t start_time;   /* when did the transaction started? */
        integer_t busy_time;    /* how long is it busy? */
        int wt_reissue;         /* this was a wt reissue, so just reissue it */
        int wt_hit;             /* if a wt reissue was a hit or a miss */
} trans_line_t;

/* cache definition */
struct generic_cache {

        log_object_t log;

#if defined(DEBUG_REISSUE)
        struct {
                int flag;
                integer_t cycle;
        } reissue[0x10000];

        struct {
                int flag;
                integer_t cycle;
        } read_counted[0x10000];
#endif

        cache_line_t   *lines;  /* cache lines */
        conf_object_t  **cpus;  /* cpus sending memory transactions */
        int            cpus_count;

        uinteger_t      current_cycle; /* current cycle - update by operate() */

        trans_line_t *outstanding_trans; /* transactions that should be 
                                            reissued */
        
        struct {
                int line_number;/* number of cache lines */
                int line_size;  /* size of a cache line */
                int assoc;      /* associativity */

                int virtual_index;  /* virtual address used for index */
                int virtual_tag;    /* virtual address used for tag */

                int write_allocate; /* allocate on write */
                int write_back;     /* write-through/write-back */
                
                int read_per_cycle;  /* how many read per cycle allowed? */
                int write_per_cycle; /* how many write per cycle allowed? */
                int max_out_trans;   /* how many outstanding transactions 
                                        allowed? */

                /* replacement policy system */
                void *repl_data;    /* data allocated by the replacement
                                       policy */
                repl_interface_t repl_fun; /* copy of the current repl.
                                              policy functions */


                /* precomputed values */
                int line_size_ln2;
                int next_assoc;
                integer_t tag_mask;
                integer_t index_mask;
                int accept_not_stall; /* should the cache accept not-stallable
                                         transactions? */
        } config;

        struct {
                int read;
                int write;
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
        } stat;

        struct {
                conf_object_t *obj;
                prof_data_t *id;
        } prof[GC_Max_Profilers];

        struct {
                integer_t read_cc; /* current cycle for counter */
                int curr_rpc;      /* current counter for read */

                integer_t write_cc; /* current cycle for counter? */
                int curr_wpc;       /* current counter for write */
        } limit;

        conf_object_t *timing_model;
        timing_model_interface_t *timing_ifc;

};


void update_precomputed_values(generic_cache_t *gc);
void gc_register(conf_class_t *class);

void ts_init_local(void);

