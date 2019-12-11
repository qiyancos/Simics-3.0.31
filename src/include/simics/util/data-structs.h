/*
 * simics/util/data-structs.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_DATA_STRUCTS_H
#define _SIMICS_UTIL_DATA_STRUCTS_H

#if defined(__cplusplus)
extern "C" {
#endif

#include <simics/util/vect.h>

typedef struct range_node { 
        uinteger_t start;
        uinteger_t end;
        void *ptr;
} range_node_t;

struct interval_section {
        uint64 start;           /* start of this section */
        /* section ends right before start of the next section, or
           at 0xffffffffffffffff if it is the last */
        struct interval_bucket *intervals; /* NULL if no intervals here */
};

struct interval_set {
        VECT(struct interval_section) sections;
        unsigned allow_overlap; /* whether overlapping intervals are allowed */
};

#if defined(STANDALONE)
#ifndef HAVE_INTERVAL_SET_T
typedef struct interval_set interval_set_t;
typedef struct interval_set_iter interval_set_iter_t;
#endif
#else
/* Return true iff interval set is empty. */
FORCE_INLINE int
interval_set_empty(interval_set_t *is)
{
        return VLEN(is->sections) == 1
                && VGET(is->sections, 0).intervals == NULL;
}
#endif


void init_interval(interval_set_t *is, int allow_overlap);

struct interval_set_iter {
        interval_set_t *is;
        uint64 start, end;
        unsigned sect;          /* section index */
        unsigned inum;          /* interval index */
};

interval_set_t *new_interval(int allow_overlap);
void insert_interval(interval_set_t *is, uinteger_t start, uinteger_t end,
                     void *ptr);
void *get_interval_ptr(interval_set_t *is, uinteger_t address);
int get_interval_vector(interval_set_t *is, uinteger_t address,
                        range_node_t **res);
void *get_lower_interval_ptr(interval_set_t *is, uinteger_t address);
void *get_higher_interval_ptr(interval_set_t *is, uinteger_t address);

int touch_interval(interval_set_t *is, uinteger_t start, uinteger_t end);

typedef void (*intervals_func_t)(uinteger_t, uinteger_t, void *, void *);

void for_all_intervals(interval_set_t *is, intervals_func_t f, void *data);
void for_some_intervals(interval_set_t *is, uinteger_t start, uinteger_t end,
			intervals_func_t f, void *data);

void remove_interval(interval_set_t *is, uinteger_t start, uinteger_t end,
                     void *ptr);
void free_interval(interval_set_t *is);

void interval_set_new_iter(interval_set_t *is, interval_set_iter_t *it,
                           uint64 start, uint64 end);

range_node_t *interval_set_iter_next(interval_set_iter_t *it);

typedef struct table table_t;

typedef void (*table_func_t)(int slot, void *entry, void *user);

void table_add(table_t *the_table, void *ptr, int slot);
void *table_lookup(table_t *the_table, int slot);
table_t *table_new(void);
void table_free(table_t *the_table);
int table_insert(table_t *the_table, void *ptr);
void for_all_table(table_t *the_table, table_func_t cb, void *user);

typedef struct string_tree string_tree_t;

enum st_lookup_approx_result {
        StApproxLookup_NoEntry,
        StApproxLookup_OK,
        StApproxLookup_Ambiguous
};

typedef void (*st_list_all_func_t)(const char *, void *);
typedef int (*st_do_all_func_t)(const char *, void *);
typedef int (*st_for_all_func_t)(const char *, void *, void *);

const char *st_no2str(string_tree_t *st, int number);
int st_str2no(string_tree_t *st, const char *string);
string_tree_t *st_new(int alloc);
void *st_no2ptr(string_tree_t *st, int number);
void st_free(string_tree_t *st);
int st_do_all(string_tree_t *st, const char *string, st_do_all_func_t f);
const char *st_insert(string_tree_t *st, const char *string, void *ptr);
const char *st_insert_no(string_tree_t *st, int pos, const char *string,
                         void *ptr);
void *st_lookup(string_tree_t *st, const char *string);
void st_list_all(string_tree_t *st, st_list_all_func_t f);
int st_for_all(string_tree_t *st, st_for_all_func_t f, void *data);

enum st_lookup_approx_result st_lookup_approx(string_tree_t *string_tree,
                                              const char *string,
                                              void **result);
void st_init(string_tree_t *st, int alloc);
int st_num_strings(string_tree_t *st);

/* The assoc_table functions are strongly DEPRECATED and kept for binary
   compatibility until 3.2. Do _not_ use! (bug 5063) */
typedef struct assoc_table {
        void *entry;
        int handle_free;
} assoc_table_t;

void *assoc_table_lookup(assoc_table_t *table, integer_t value);
void assoc_table_add(assoc_table_t *table, integer_t value, void *ptr);
assoc_table_t *assoc_table_new(int handle_free);
void assoc_table_free(assoc_table_t *table);

typedef void (*for_all_assoc_table_func_t)(integer_t, void *, void *);

void for_all_assoc_table(assoc_table_t *table, for_all_assoc_table_func_t f,
                         void *data);

typedef struct ht_entry {
	uint64 key;
	const void *value;
	unsigned hash;		/* raw hash value */
	struct ht_entry *next;
} ht_entry_t;

typedef struct ht_table {
        unsigned bits;          /* size in bits */
	int num_entries;
	ht_entry_t **entries;
	int int_keys;		/* 1 if keys are integers, 0 if strings */
} ht_table_t;

typedef struct {
        ht_table_t *table;
        int index;
        ht_entry_t *next;
} ht_iter_t;

FORCE_INLINE const char *
ht_str_key(ht_entry_t *e)
{
        return (char *)(uintptr_t)e->key;
}

FORCE_INLINE uint64
ht_int_key(ht_entry_t *e)
{
        return e->key;
}

FORCE_INLINE void *
ht_value(ht_entry_t *e)
{
        return (void *)e->value;
}

/* Change key of an entry: can only be used for string keys, and only if the
   new key is identical to the old */
FORCE_INLINE void
ht_set_key(ht_entry_t *e, const char *key)
{
        e->key = (uintptr_t)key;
}

FORCE_INLINE void
ht_set_value(ht_entry_t *e, const void *value)
{
        e->value = value;
}

FORCE_INLINE unsigned
ht_num_entries(ht_table_t *ht)
{
        return ht->num_entries;
}

FORCE_INLINE int
ht_is_inited(ht_table_t *ht)
{
        return !!ht->entries;
}

void ht_init_table(ht_table_t *ht, int integer_keys);
void ht_clear_table(ht_table_t *ht, int free_values, int free_keys);
void ht_delete_table(ht_table_t *ht, int free_values, int free_keys);
void ht_insert_int(ht_table_t *ht, uint64 key, const void *value);
void ht_insert_str(ht_table_t *ht, const char *key, const void *value);
void *ht_update_int(ht_table_t *ht, uint64 key, const void *value);
void *ht_update_str(ht_table_t *ht, const char *key, const void *value);
ht_entry_t *ht_insert_unique_int(ht_table_t *ht, uint64 key,
                                 const void *value);
ht_entry_t *ht_insert_unique_str(ht_table_t *ht, const char *key,
                                 const void *value);
int ht_remove_int(ht_table_t *ht, uint64 key, const void *value);
int ht_remove_str(ht_table_t *ht, const char *key, const void *value);
ht_entry_t *ht_entry_lookup_int(ht_table_t *ht, uint64 key);
ht_entry_t *ht_entry_lookup_str(ht_table_t *ht, const char *key);
void *ht_lookup_int(ht_table_t *ht, uint64 key);
void *ht_lookup_str(ht_table_t *ht, const char *key);
ht_entry_t *ht_next_entry(ht_table_t *ht, ht_entry_t *prev);
void ht_new_iter(ht_table_t *ht, ht_iter_t *it);
ht_entry_t *ht_iter_next(ht_iter_t *it);

typedef int (*ht_for_each_entry_func_t)(ht_table_t *table, uint64 key,
					void *value, void *data);

int ht_for_each_entry(ht_table_t *table, ht_for_each_entry_func_t func,
                      void *data);

void ht_statistics(ht_table_t *table);

typedef int (*ht_sorted_entries_func_t)(ht_entry_t *a, ht_entry_t *b,
					void *data);

ht_entry_t **ht_sorted_entries(ht_table_t *table,
                               ht_sorted_entries_func_t compare,
			       void *data);


typedef void *binary_heap_entry_t;

/* return 1 if x > y - always 0 if x = NULL */
typedef int (*binary_heap_compare_func_t)(binary_heap_entry_t x,
                                          binary_heap_entry_t y);

typedef struct binary_heap {
        
        int                         size;
        int                         max_size;
        binary_heap_entry_t        *entries;
        binary_heap_compare_func_t  compare;
        
} binary_heap_t;

void binary_heap_setup(binary_heap_t *heap, int size,
                       binary_heap_compare_func_t compare);

int binary_heap_insert(binary_heap_t *heap, void *entry);

void *binary_heap_min(binary_heap_t *heap);

void *binary_heap_delete_min(binary_heap_t *heap);

typedef struct prof_data prof_data_t;

#ifndef STANDALONE

typedef uint64 prof_data_address_t;
typedef uint64 prof_data_counter_t;

typedef prof_data_counter_t  ***radix_top_t;
typedef prof_data_counter_t   **radix_middle_t;
typedef prof_data_counter_t    *radix_bottom_t;

typedef struct {
        prof_data_t *pd;
        uint64 start, end;
        uint64 addr;
        ht_iter_t hit;
        uint64 top_key;
        unsigned l_index, m_index, h_index; /* radix tree indices */
        unsigned l_reset, m_reset, h_reset;
        radix_bottom_t ltab;
        radix_middle_t mtab;
        radix_top_t htab;
} prof_data_iter_t;

prof_data_t *prof_data_create(unsigned granularity);
void prof_data_delete(prof_data_t *pd);
void prof_data_clear(prof_data_t *pd);
int prof_data_granularity_log2(prof_data_t *pd);
void prof_data_set(prof_data_t *pd, prof_data_address_t address,
                   prof_data_counter_t value);
void prof_data_add(prof_data_t *pd, prof_data_address_t address,
                   prof_data_counter_t value);

void prof_data_inc_pc(prof_data_t *prof, conf_object_t *cpu);
prof_data_counter_t prof_data_get(prof_data_t *pd,
                                  prof_data_address_t address);

void prof_data_new_iter(prof_data_t *pd, prof_data_iter_t *it,
                        prof_data_address_t start, prof_data_address_t end);
prof_data_counter_t prof_data_iter_next(prof_data_iter_t *it);
prof_data_address_t prof_data_iter_addr(prof_data_iter_t *it);

typedef void (*prof_data_func_t)(prof_data_address_t address,
                                 prof_data_counter_t counter,
                                 void *data);
void prof_data_for_counters_in_range(prof_data_t *pd,
                                     prof_data_func_t f, void *data,
                                     prof_data_address_t start,
                                     prof_data_address_t end);
void prof_data_for_all_counters(prof_data_t *pd, prof_data_func_t f,
                                void *data);
int prof_data_save(prof_data_t *pd, FILE *f);
int prof_data_load(prof_data_t *pd, FILE *f);

#endif /* !STANDALONE */

#if defined(__cplusplus)
}
#endif

#endif /* _SIMICS_UTIL_DATA_STRUCTS_H */
