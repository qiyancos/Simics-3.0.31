/*
 * simics/core/memory.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.

 *
 */

#ifndef _SIMICS_CORE_MEMORY_H
#define _SIMICS_CORE_MEMORY_H

#include <simics/core/configuration.h>

/* Used to uniquely identify the memory transactions initiated by an
   instruction. The explicit number is used to identify which explicit
   transaction a transaction belongs to. The implicit number number is used to
   identify additional implicit transactions, for example hardware tablewalk
   accesses, caused by an explicit transaction. An explicit transaction should
   use implicit number 0, implicit transactions should use numbers from 1 and
   up. */
typedef uint16 stall_id_num_t;
typedef struct stall_id {
        stall_id_num_t explicit_num;
        stall_id_num_t implicit_num;
} stall_id_t;

/* Bits in memory transaction types */
enum {
        Sim_Trn_Instr = 1,
        Sim_Trn_Write = 2,
        Sim_Trn_Control = 4,    /* Ceci n'est pas une mem-trans. Signifies that
                                   this is not an exchange of data between CPU
                                   and memory. */
        Sim_Trn_Prefetch = 8    /* no defined semantics really, may go away */
};

/* <add id="simics api types">
   <name index="true">mem_op_type_t</name>
   <doc>
   <doc-item name="NAME">mem_op_type_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="mem_op_type_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This enum is used to identify the type of a memory operation. The
   function <fun>SIM_get_mem_op_type()</fun> returns the type of a 
   <type>generic_transaction_t</type>, and <fun>SIM_set_mem_op_type()</fun>
   is used to set it.
   </doc-item>
   <doc-item name="SEE ALSO">SIM_get_mem_op_type, SIM_set_mem_op_type,
   generic_transaction_t, SIM_get_mem_op_type_name</doc-item>
   </doc>
   </add>

   <add-type id="mem_op_type_t def"></add-type>
 */
typedef enum {
        Sim_Trans_Load          = 0,
        Sim_Trans_Store         = Sim_Trn_Write,
        Sim_Trans_Instr_Fetch   = Sim_Trn_Instr,
        Sim_Trans_Prefetch      = Sim_Trn_Prefetch | Sim_Trn_Control,
        Sim_Trans_Cache         = Sim_Trn_Control
} mem_op_type_t; 

/*
   <add id="simics api types">
   <name index="true">generic_transaction_t</name>
   <doc>
   <doc-item name="NAME">generic_transaction_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="generic_transaction_t def"/>

   <insert id="arc_type_t def"/>

   <insert id="page_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   Used to communicate information about memory operations. Not all info is
   complete/correct in all uses. For an example of how a memory hierarchy
   can use a memory transaction, see example memory hierarchy.

   The transaction parameters are divided into a generic part shown
   below and an architecture specific part. The generic struct is
   included as the first component of the memory_transaction_t struct,
   where the architecture-specific parameters are declared.

   Normally the logical address and most control flags are set before
   the mmu is called. The host_address is a host pointer to the start
   of the simulated memory the transaction loads from or stores to.

   <i>real_address</i> points to the destination for a load or source of a
   store operation.

   The <i>ini_ptr</i> points to the object initiating the operation, this is
   either a processor or a device depending on the <i>ini_type</i> field.
   <ndx>ini_type_t</ndx>
   <smaller><insert id="ini_type_t"/></smaller>

   The mmu sets the <i>physical_address</i> and possibly set some more control
   flags. The memory hierarchy only reads the memory transaction to
   decide what stall time to return.

   The <i>block_STC</i> bit functions as a "veto" flag for various
   modules. Any code can set this to 1, but it should not be set to
   zero. When set to one, the next access to the same STC line will be
   passed to the memory hierarchy.

   The <i>may_stall</i> bit is set to zero for a few types of references where
   the simulator kernel cannot deal with stalling. A memory hierarchy must
   return stall time zero when the flag is clear. A memory hierarchy
   that wants to stall anyway should accumulate stall time, and
   trigger the total stall time when a stall-capable access comes
   along (which is not guaranteed to happen but most probably
   will). For atomic read/write
   instructions (swap) any access may stall. If an instruction is stalled
   the entire instruction will be executed after the stalltime is up.
   The may_stall bit may be cleared by the mmu.

   The <i>ignore</i> flag can be set to 1 by the MMU. When set no memory
   operation will be performed. This is useful for instructions coded
   as a memory operation but which really only modify mmu internal
   state.

   The <i>inverse_endian</i> flag may be changed by the MMU. If set, the
   data involved in the access will be transferred in the opposite order.
   If not set, the bytes will be transferred in the same order they occur in
   the memory space.
   A memory object should not set this bit to a hard value, only toggle it.
   It may have been set by Simics for implementation reasons.

   The <i>page_cross</i> field is used to indicate when Simics has
   split a memory transaction in two.  It is normally 0, but when a
   transaction crosses an MMU page boundary, it will be converted into
   two separate transactions, one for each accessed page.  The
   addresses and sizes are adjusted to confine them to their
   respective pages.  The first of these transaction will have
   <i>page_cross</i> set to 1, and the second will have it set to 2.

   The <i>atomic</i> is read only. It may be read by any module.
   The atomic flag is set for any data memory transaction caused 
   by an atomic instruction; i.e., an instruction whose memory references
   must be performed without any intervening memory references
   (from other processors). The atomic sequence is a read followed
   by a write.

   The <i>use_page_cache</i> is used internally. Do not change its
   value.

   The <i>user_ptr</i> may be used to pass information between user defined
   modules that use memory transactions. Simics does not use this field.

   The <i>type</i> field should not be used directly; use the
   <fun>SIM_mem_op_is_<em>xxx</em>()</fun>
   predicate functions, where <tt><em>xxx</em></tt> can be
   <tt>instruction</tt>, <tt>data</tt>, <tt>read</tt>, or
   <tt>write</tt>. <fun>SIM_set_mem_op_type()</fun> function is used to set
   the type of a memory operation (see the <type>mem_op_type_t</type> enum
   definition), and <fun>SIM_get_mem_op_type()</fun> is used to read it.

   <i>id</i> is a unique number for all currently outstanding memory
   transactions. In an in-order version of Simics, this field is zero.
   See the <fun>SIM_get_unique_memory_transaction_id()</fun> function.

   When activated, instruction fetches set <i>arc_type</i>
   to indicate if the fetch is the result of sequential 
   execution or a branch. In case of a branch,
   the <i>source_physical_address</i>
   is set to the address where the branch was made from.

   </doc-item>

   <doc-item name="SEE ALSO">mem_op_type_t</doc-item>

   </doc>

   </add>

   <add-type id="generic_transaction_t def"></add-type> */

struct generic_transaction {
        logical_address_t   logical_address;
        physical_address_t  physical_address;
        unsigned int        size;             /* size in bytes */
        mem_op_type_t       type;             /* opaque */
        unsigned int        atomic:1;         /* trans is part of an atomic
                                                 sequence of mem ops */

        unsigned int        inquiry:1;        /* set to 1 to indicate inquiry
                                                 access */
        unsigned int        speculative:1;    /* access is speculative,
                                                 may not be committed */

        unsigned int        ignore:1;         /* set to 1 to signal no-op
                                                 (don't do access) */
        unsigned int        may_stall:1;      /* when set to 0, any stall time
                                                 returned is ignored */
        unsigned int        ma_no_reissue:1;  /* if the transaction's
                                                 instruction is rolled back
                                                 during a stall the memory
                                                 hierarchy should not be called
                                                 again */
        unsigned int        reissue:1;        /* If this is 1, the transaction
                                                 will be reissued if a stall
                                                 greater than 0 is returned */
        unsigned int        block_STC:1;      /* set to 1 iff anybody (MMU,
                                                 memory hierarchy, etc) wants
                                                 to see future accesses of this
                                                 type */
        unsigned int        use_page_cache:1; /* internal - do not change */

        unsigned int        inverse_endian:1; /* data transfer is
                                                 byte-reversed */

        unsigned int        page_cross:2;     /* page crossing
                                                 0 - no crossing
                                                 1 - first access
                                                 2 - second access */

        unsigned int        use_iostc:1;      /* may be added to iostc */
        unsigned int        iostc_blocked:1;  /* was blocked from iostc */

        ini_type_t          ini_type;         /* cpu, device, or other */
        conf_object_t      *ini_ptr;

        int                 id;               /* will be different for
                                                 simultaneously outstanding
                                                 transactions */
        exception_type_t    exception;        /* set if memhier throws
                                                 exception, otherwise
                                                 Sim_PE_No_Exception */
#if !defined(GULP)
        void               *user_ptr;         /* user pointer that Simics never
                                                 touches */
#endif

        char               *real_address;     /* data pointer for the
                                                 initiator */

        int                space_count;       /* internal, # of memory space
                                                 transitions */

        page_t *page;           /* internal: page if RAM access */
        page_t *tag_page;       /* internal: tag page if any */
        unsigned tag_page_ofs;  /* internal: start of page in tag page */

        physical_address_t  source_physical_address; /* if arc_type
							== Arc_Taken_Branch */
        arc_type_t          arc_type;         /* filled for fetches from
						 branch targets */
        int                 allocation_size;  /* The size of the transaction 
                                                 (including local part) only
                                                 valid if > 0 */

        stall_id_t          stall_id;
};

/* <add-type id="map_type_t def"></add-type> */
typedef enum { 
        Sim_Map_Ram,
        Sim_Map_Rom,
        Sim_Map_IO,
        Sim_Map_Port,
        Sim_Map_Translate = 0x100, /* pseudo - do not use */
        Sim_Map_Translate_To_Space,
        Sim_Map_Translate_To_Ram,
        Sim_Map_Translate_To_Rom
} map_type_t;

/* <add id="simics api types">
   <name index="true">map_info_t</name>
   <doc>
   <doc-item name="NAME">map_info_t</doc-item>
   <doc-item name="SYNOPSIS">
   <ndx>map_type_t</ndx>
   <smaller>
   <insert id="map_info_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   The <tt>map_info_t</tt> structure members have the following meaning:
   <ul>
   <li>
   <tt>base</tt>: The base address of the device mapping in the memory space.
   </li>
   <li>
   <tt>start</tt>: The address inside the device memory space where the mapping
   starts.</li>
   <li><tt>length</tt>: The length of the mapped memory, in bytes.</li>
   <li><tt>function</tt>: Used to mapped the same object several times
       with different functionality. Corresponds to the function argument used
       when mapping devices into a memory space.</li>
   <li>If the map target does not support large accesses, then
       <tt>align-size</tt> can be set to the maximum allowed size.
        Accesses spanning align boundaries will be split info several
        smaller transactions. By default, the align size is set to 4
        for port space devices, 8 for other devices and 8192 for memory.</li>
   <li>Mappings with an align size of 2, 4 and 8 may set the
       <tt>reverse_endian</tt> field to a non zero value. This can be used to
       model bridges that perform byte swapping on a specific bus width.</li>
   </ul>
   </doc-item>
   </doc>
   </add>

   <add-type id="map_info_t def"></add-type> */
typedef struct map_info {
        physical_address_t  base;
        physical_address_t  start;
        physical_address_t  length;
        int                 function;
        uint8               priority;
        int                 align_size;
        swap_mode_t         reverse_endian;
} map_info_t;

/* <add id="simics api types">
   <name index="true">map_list_t</name>
   <doc>
   <doc-item name="NAME">map_list_t</doc-item>
   <doc-item name="SYNOPSIS">
   <ndx>map_type_t</ndx><ndx>map_info_t</ndx>
   <smaller>
   <insert id="map_type_t def"/>
   <insert id="struct map_list def"/>
   <insert id="map_list_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This data structure is used to pass information about the set of
   mappings a particular address in an address space contains.  
   </doc-item>
   </doc>
   </add>
   <add-type id="struct map_list def"></add-type> 
*/
struct map_list {
        map_type_t       map_type;
        conf_object_t   *object;
#if !defined(GULP)
        void            *interface_ptr;
        void            *target_interface;
        void            *breakpoint_interface;
        void            *bridge_interface;
#endif
        conf_object_t   *target_object;
        conf_object_t   *bridge;
        map_info_t       map_info;

        physical_address_t map_size; /* not constant, use with caution */

        int              deleted;  /* internal flag - should always be 0 ! */
};

/* image interface and vdisk types */

/* <add-type id="image_spage_t def"></add-type> */
typedef struct image_spage image_spage_t;

struct image_spage {
        void *data;
        void *meta_data;
        char dirty;
        char zero_backed;       /* true if page backed by zeros */
        char all_zeros;         /* iff page is all zeros (only when writing) */
        int mmapped_fd;         /* fd if data is mapped with mmap() */

        unsigned int gen_count; /* priv. to rev-execution; used to detect
                                   the first write to a new micro checkpoint */
        uint64 offs;            /* byte offset in image */
        conf_object_t *img_obj; /* image to which this page belongs */
};

/* <add id="image_interface_t">
   This interface is used for handling big data images.
   <fun>read()</fun> and <fun>write</fun> access a block of data at a time.
   Iteration over all pages can be done with <fun>for_all_spages()</fun>.
   The iteration stops when <fun>f()</fun> returns non-zero,
   and the return value from <fun>for_all_spages()</fun> is the last return
   value from the callback function.
   </add> */
/* <add-type id="image_interface_t"><ndx>vdisk_addr_t</ndx></add-type> */
typedef uint64 vdisk_addr_t;

/* <add-type id="image_interface_t"></add-type> */
typedef struct image_interface {
#if !defined(GULP)
        void (*read)(conf_object_t *img, void *to_buf, vdisk_addr_t start,
                     size_t length);
        void (*write)(conf_object_t *img, void *from_buf, vdisk_addr_t start,
                      size_t length);
        int (*for_all_spages)(conf_object_t *img,
                              int (*f)(image_spage_t *, vdisk_addr_t, void *),
                              void *arg);
#endif /* not GULP */
        void (*set_persistent)(conf_object_t *obj);
        void (*save_to_file)(conf_object_t *NOTNULL obj,
                             const char *NOTNULL file,
                             uint64 start, uint64 length);
        void (*save_diff)(conf_object_t *NOTNULL obj,
                          const char *NOTNULL file);
        void (*clear_range)(conf_object_t *NOTNULL obj,
                            uint64 start, uint64 length);
} image_interface_t;

#define IMAGE_INTERFACE "image"
/* ADD INTERFACE image_interface */

typedef struct {
#if !defined(GULP)
        char *(*get_base)(conf_object_t *obj, size_t *retsize);
#endif /* not GULP */
        void (*prepare_range)(conf_object_t *NOTNULL obj,
                              access_t type, size_t offs, size_t size);
} linear_image_interface_t;
#define LINEAR_IMAGE_INTERFACE "linear_image"
/* ADD INTERFACE linear_image_interface */

void VT_image_swapout_dirty(void);           /* unofficial */

/* DEPENDENCY <simics/core/configuration.h> */
uinteger_t SIM_read_phys_memory(conf_object_t *NOTNULL cpu,
                                physical_address_t paddr,
                                int length);

void SIM_write_phys_memory(conf_object_t *NOTNULL cpu,
                           physical_address_t paddr,
                           uinteger_t value, int length);

uint8 SIM_read_byte(conf_object_t *NOTNULL obj, generic_address_t paddr);

void SIM_write_byte(conf_object_t *NOTNULL obj, generic_address_t paddr,
                    uint8 value);

uint64 SIM_read_phys_memory_tags(conf_object_t *mem_space,
                                 physical_address_t paddr, unsigned ntags);
void SIM_write_phys_memory_tags(conf_object_t *mem_space,
                                physical_address_t paddr, uint64 tag_bits,
                                unsigned ntags);
uint64 VT_read_phys_memory_tags_mask(conf_object_t *mem_space,
                                     physical_address_t paddr, unsigned ntags);

physical_address_t SIM_logical_to_physical(conf_object_t *NOTNULL cpu,
                                           data_or_instr_t data_or_instr,
                                           logical_address_t vaddr);

void SIM_flush_I_STC_logical(conf_object_t *NOTNULL cpu,
                             logical_address_t vaddr,
                             logical_address_t length);
void SIM_flush_D_STC_logical(conf_object_t *NOTNULL cpu,
                             logical_address_t vaddr,
                             logical_address_t length);
void SIM_flush_I_STC_physical(conf_object_t *NOTNULL cpu,
                              physical_address_t paddr,
                              physical_address_t length);
void SIM_flush_D_STC_physical(conf_object_t *NOTNULL cpu,
                              physical_address_t paddr,
                              physical_address_t length,
                              read_or_write_t read_or_write);
void SIM_STC_flush_cache(conf_object_t *NOTNULL cpu);
void SIM_for_all_memory_pages(void (*f)(integer_t), int d_or_i);

#if !defined(GULP)
void SIM_c_get_mem_op_value_buf(generic_transaction_t *mop, char *dst);
void SIM_c_set_mem_op_value_buf(generic_transaction_t *mop, char *src);
#endif

attr_value_t SIM_get_mem_op_value_buf(generic_transaction_t *NOTNULL mop);
void SIM_set_mem_op_value_buf(generic_transaction_t *NOTNULL mop,
                              attr_value_t value);

/*
  <add-fun id="simics api memtrans">
  <short>transaction data/instruction predicates</short>
  These functions check whether <tt>mem_op</tt> is a data or an instruction
  transaction. Currently, the only transactions that are instruction
  transactions are instruction fetches.
  </add-fun>
*/
FORCE_INLINE int
SIM_mem_op_is_data(const generic_transaction_t *NOTNULL mop)
{
        return !(mop->type & Sim_Trn_Instr);
}

/* <append-fun id="SIM_mem_op_is_data"/> */
FORCE_INLINE int
SIM_mem_op_is_instruction(const generic_transaction_t *NOTNULL mop)
{
        return mop->type & Sim_Trn_Instr;
}

/*
  <add-fun id="simics api memtrans">
  <short>transaction read/write predicates</short>
  These functions check whether <tt>mem_op</tt> is a read or a write
  transaction.
  </add-fun>
*/
FORCE_INLINE int
SIM_mem_op_is_read(const generic_transaction_t *NOTNULL mop)
{
        return !(mop->type & Sim_Trn_Write);
}

/* <append-fun id="SIM_mem_op_is_read"/> */
FORCE_INLINE int
SIM_mem_op_is_write(const generic_transaction_t *NOTNULL mop)
{
        return mop->type & Sim_Trn_Write;
}

/*
  <add-fun id="simics api memtrans">
  <short>transaction control predicates</short>
  Checks whether <tt>mem_op</tt> is control transaction.
  </add-fun>
*/
FORCE_INLINE int
SIM_mem_op_is_control(const generic_transaction_t *NOTNULL mop)
{
        return mop->type & Sim_Trn_Control;
}

/*
  <add-fun id="simics api memtrans">
  <short>transaction control predicates</short>
  Checks whether <tt>mem_op</tt> is prefetch transaction.
  </add-fun>
*/
FORCE_INLINE int
SIM_mem_op_is_prefetch(const generic_transaction_t *NOTNULL mop)
{
        return mop->type & Sim_Trn_Prefetch;
}

/*
  <add-fun id="simics api memtrans">
  <short>CPU initiated transaction</short>
  Checks whether <tt>mem_op</tt> is sent from a processor.
  </add-fun>
*/
FORCE_INLINE int
SIM_mem_op_is_from_cpu(const generic_transaction_t *NOTNULL mop)
{
        return (mop->ini_type & 0xf000) == Sim_Initiator_CPU;
}

/*
  <add-fun id="simics api memtrans">
  <short>CPU initiated transaction</short>
  Checks whether <tt>mem_op</tt> is sent from a processor
  of a specific architecture.
  </add-fun>
*/
FORCE_INLINE int
SIM_mem_op_is_from_cpu_arch(const generic_transaction_t *NOTNULL mop,
                            ini_type_t arch)
{
        return (mop->ini_type & 0xff00) == arch;
}

/*
  <add-fun id="simics api memtrans">
  <short>Device initiated transaction</short>
  Checks whether <tt>mem_op</tt> is sent from a device.
  </add-fun>
*/
FORCE_INLINE int
SIM_mem_op_is_from_device(const generic_transaction_t *NOTNULL mop)
{
        return (mop->ini_type & 0xf000) == Sim_Initiator_Device;
}

/*
  <add-fun id="simics api memtrans">
  <short>Cache initiated transaction</short>
  Checks whether <tt>mem_op</tt> is sent from a cache timing model.
  </add-fun>
*/
FORCE_INLINE int
SIM_mem_op_is_from_cache(const generic_transaction_t *NOTNULL mop)
{
        return (mop->ini_type & 0xf000) == Sim_Initiator_Cache;
}

/*
  <add-fun id="simics api memtrans">
  <short>get type of transaction</short>
  This function returns the type of the memory transaction.
  </add-fun>
*/
FORCE_INLINE mem_op_type_t
SIM_get_mem_op_type(const generic_transaction_t *NOTNULL mop)
{
        return mop->type;
}

/*
  <add-fun id="simics api memtrans">
  <short>set type of transaction</short>
  </add-fun>
*/
FORCE_INLINE void
SIM_set_mem_op_type(generic_transaction_t *NOTNULL mop, mem_op_type_t type)
{
        mop->type = type;
}

const char *SIM_get_mem_op_type_name(mem_op_type_t type);

uinteger_t SIM_get_mem_op_value_le(generic_transaction_t *NOTNULL mop);
uinteger_t SIM_get_mem_op_value_be(generic_transaction_t *NOTNULL mop);
uinteger_t SIM_get_mem_op_value_cpu(generic_transaction_t *NOTNULL mop);

void SIM_set_mem_op_value_le(generic_transaction_t *NOTNULL mop,
                             uinteger_t value);
void SIM_set_mem_op_value_be(generic_transaction_t *NOTNULL mop,
                             uinteger_t value);
void SIM_set_mem_op_value_cpu(generic_transaction_t *NOTNULL mop,
                              uinteger_t value);

#if defined(DEVICE_IS_BIG_ENDIAN)
#if defined(DEVICE_IS_LITTLE_ENDIAN)
#error "Device cannot be both BIG and LITTLE endian!"
#endif
#define SIM_get_mem_op_value(mop)    SIM_get_mem_op_value_be(mop)
#define SIM_set_mem_op_value(mop, v) SIM_set_mem_op_value_be(mop, v)
#elif defined(DEVICE_IS_LITTLE_ENDIAN)
#define SIM_get_mem_op_value(mop)    SIM_get_mem_op_value_le(mop)
#define SIM_set_mem_op_value(mop, v) SIM_set_mem_op_value_le(mop, v)
#else     /* !DEVICE_IS_LITTLE_ENDIAN */
#define SIM_get_mem_op_value(mop)  UNDEFINED_ENDIAN
#define SIM_set_mop_value(mop, v)  UNDEFINED_ENDIAN
#endif    /* !DEVICE_IS_LITTLE_ENDIAN */

/* <add id="snoop_memory interface">
   This interface is described with the <iface>timing-model</iface>
   interface.
   </add>
*/

/* <add id="timing_model_interface_t">
   <ndx>operate_func_t</ndx>
   The <iface>timing-model</iface> interface is used to communicate
   stall times for memory accesses. It is typically exported by cache
   models. The <fun>operate()</fun> function is then called on every
   memory access that misses in the STC, and the return value from the
   call is the number of cycles to stall.

   The <iface>snoop-memory</iface> interface has the exact same layout
   as the <iface>timing-model</iface> interface, but its
   <fun>operate()</fun> function is called after the memory access has
   been performed. The return value from the <fun>operate()</fun>
   function of a <iface>snoop-memory</iface> interface is ignored.
   
   See the Creating a Timing Model chapter in the <i>Simics User
   Guide</i> for more information on how to use these interfaces.
  
   <insert-until text="// ADD INTERFACE timing_model_interface"/>
   </add>
*/
typedef cycles_t (*operate_func_t)(conf_object_t *NOTNULL mem_hier,
                                   conf_object_t *NOTNULL space,
                                   map_list_t *NOTNULL map_list,
                                   generic_transaction_t *NOTNULL mem_op);

typedef struct timing_model_interface {
        operate_func_t operate;
} timing_model_interface_t;

typedef struct snoop_memory_interface {
        operate_func_t operate;
} snoop_memory_interface_t;

#define TIMING_MODEL_INTERFACE "timing_model"
#define SNOOP_MEMORY_INTERFACE "snoop_memory"
// ADD INTERFACE timing_model_interface
// ADD INTERFACE snoop_memory_interface

/*
  <add id="cache_control_interface_t">

  Interface for controlling a cache. Returns the number of cycles until the
  operation is complete.

  <insert-until text="// ADD INTERFACE cache_control_interface"/>
  </add>
*/
typedef struct {
        cycles_t (*cache_control)(conf_object_t *cache,
                                  cache_control_operation_t op,
                                  generic_transaction_t *mem_op);
} cache_control_interface_t;
#define CACHE_CONTROL_INTERFACE "_cache_control"
// ADD INTERFACE cache_control_interface

typedef struct {
        conf_object_t *obj;
        cache_control_interface_t *ifc;
} controllable_cache_t;

/* ADD INTERFACE a20_interface */

/* <add-type id="a20_interface_t">
   This interface is used between the A20 line handling device
   (typically the keyboard controller) and the x86 processor.
   </add-type> */
typedef struct {
        void (*set_a20_line)(conf_object_t *NOTNULL, int);
        int (*get_a20_line)(conf_object_t *NOTNULL);
} a20_interface_t;

#define A20_INTERFACE "a20"

physical_address_t SIM_load_binary(conf_object_t *NOTNULL obj,
                                   const char *NOTNULL file,
                                   physical_address_t offset,
                                   int use_pa, int verbose);

void SIM_load_file(conf_object_t *NOTNULL obj, const char *NOTNULL file,
                   physical_address_t paddr, int verbose);

void VT_remove_all_icode(void);
void VT_page_cache_clean(void);
unsigned VT_get_storage_page_size(void);
void VT_set_storage_page_size(int new_size_log2);
void VT_page_flush_icode(page_t *page);

void VT_do_mem_op(generic_transaction_t *RESTRICT mop,
                  char *RESTRICT src, char *RESTRICT dst);

void VT_page_invalidate_code(page_t *page,
                             physical_address_t paddr,
                             physical_address_t length,
                             int adding_to_stc);

void VT_page_access(page_t *page,
                    physical_address_t paddr,
                    generic_transaction_t *mop);

/* <add-type id="space_lookup_t">
   </add-type>
*/
typedef map_list_t *(*space_lookup_t)(conf_object_t *,
                                      generic_transaction_t *,
                                      map_info_t);


/* <add id="memory_space interface">
   <ndx>memory_space_interface_t</ndx>
   This interface is implemented by classes that provide linear address
   spaces. Other objects may perform accesses in the address space using
   the <fun>access()</fun> function or one of the simplified access functions,
   or may ask for mapped objects using <fun>space_lookup()</fun>. Typical usage
   of this interface would be memory accesses from devices or processors.

   The <fun>access_simple()</fun> function is similar to <fun>access()</fun>
   but takes some additional arguments instead of a complete
   <type>generic_transaction_t</type> structure. An inquiry version of this
   function is available as <fun>access_simple_inq()</fun>. Both these
   functions can perform endian conversion if the buffer pointed to by
   <arg>buf</arg> contains a value in host endian byte-order. To avoid endian
   conversion, <tt>Sim_Endian_Target</tt> should be specified as
   <arg>endian</arg>.
   These two functions are not available from Python.

   The functions <fun>read()</fun> and <fun>write()</fun> operate on data in
   an <type>attr_value_t</type> format. This is useful for accesses from
   Python, but they can also be used from C/C++. The value returned by
   <fun>read()</fun> is statically allocated and should be copied to a
   destination buffer directly after the call. The largest amount of data that
   can be transferred in a single <fun>read()</fun> call is 1024 bytes. If the
   <fun>write()</fun> function fails, the pseudo exception is returned as an
   integer.

   <insert id="memory_space_interface_t"/>
   </add>
*/

/* <add-type id="memory_space_interface_t">
   </add-type>
*/
#define MEMORY_SPACE_INTERFACE "memory_space"
struct memory_space_interface {
        map_list_t *(*space_lookup)(conf_object_t *NOTNULL obj,
                                    generic_transaction_t *NOTNULL mop,
                                    map_info_t mapinfo);
        exception_type_t (*access)(conf_object_t *NOTNULL obj,
                                   generic_transaction_t *NOTNULL mop);
#if !defined(GULP)
        exception_type_t (*access_simple)(conf_object_t *obj,
                                          conf_object_t *initiator,
                                          physical_address_t addr,
                                          char *buf,
                                          physical_address_t len,
                                          read_or_write_t type,
                                          endianness_t endian);
        exception_type_t (*access_simple_inq)(conf_object_t *obj,
                                              conf_object_t *initiator,
                                              physical_address_t addr,
                                              char *buf,
                                              physical_address_t len,
                                              read_or_write_t type,
                                              endianness_t endian);
#endif /* !GULP */
        attr_value_t (*read)(conf_object_t *NOTNULL obj,
                             conf_object_t *initiator,
                             physical_address_t addr,
                             int length,
                             int inquiry);
        exception_type_t (*write)(conf_object_t *NOTNULL obj,
                                  conf_object_t *initiator,
                                  physical_address_t addr,
                                  attr_value_t data,
                                  int inquiry);
        cycles_t (*timing_model_operate)(conf_object_t *NOTNULL space,
                                         generic_transaction_t *NOTNULL mop);
};
// ADD INTERFACE memory_space_interface

/* <add-type id="ram_interface_t">
   The <iface>ram</iface> interface is implemented by classes that provide
   random access read/write memory. The <iface>rom</iface> interface is
   identical to <iface>ram</iface> but provides read only memory (writes are
   dropped by the memory system).

   Both the ram and rom interfaces are Simics internal, and should not be used
   by user-defined classes.

   The <fun>phys_to_real_p</fun> function returns the page
   associated with the given address. <fun>get_page</fun> does the same thing
   but also returns the corresponding tag page in <arg>tags_ret</arg>.
   </add-type> */
typedef struct ram_interface {
        page_t *(*phys_to_real_p)(conf_object_t *obj, physical_address_t addr);
        page_t *(*get_page)(conf_object_t *obj, physical_address_t addr,
                            page_t **tags_ret, unsigned *tag_ofs_ret);
} ram_interface_t;

typedef ram_interface_t rom_interface_t;

/* <add id="ram_interface define">
   <insert-next/>
   </add> */
#define RAM_INTERFACE "ram"

/* <add id="rom_interface define">
   <insert-next/>
   </add> */
#define ROM_INTERFACE "rom"

/* <add id="io_memory_interface_t">
   <ndx>map_func_t</ndx>
   <ndx>operation_func_t</ndx>

   This interface is implemented by devices that can be mapped into
   address spaces (including port spaces). The <fun>map()</fun>
   function is called for an object when it initially is mapped into
   the address space, and <fun>operation()</fun> is called when the object
   is accessed through an address space.

   The <arg>obj</arg> argument is a pointer to the mapped object and
   <arg>map_info</arg> contains information about how and where
   the device is mapped into memory. The <arg>memory_or_io</arg>
   argument to <fun>map()</fun> identifies the type of the address
   space where the device is mapped. The <arg>mem_op</arg> argument
   to <fun>operate()</fun> contains information about the access.

   The offset into the device mapping for the access is typically
   calculated in the following way:

   <small>
   <tt>offset = mem_op->physical_address - map_info.base + map_info.start</tt>
   </small>

   The return value from <fun>map()</fun> is currently not used
   and should be always be 0.

   The <type>exception_type_t</type> type, that is the same as
   <type>pseudo_exception_t</type>, returned by the
   <fun>operation()</fun> function may be used to signal errors to
   Simics, but should in most cases be <tt>Sim_PE_No_Exception</tt>.
   If the device does not support inquiry accesses, it should return
   <tt>Sim_PE_Inquiry_Unhandled</tt> if <tt>mem_op->inqury</tt> is 1.

   <insert id="addr_space_t def"/>
   <insert-until text="// ADD INTERFACE io_memory_interface"/>
   </add>
*/
typedef int (*map_func_t)(conf_object_t *NOTNULL obj,
                          addr_space_t memory_or_io,
                          map_info_t map_info);
typedef exception_type_t (*operation_func_t)(
        conf_object_t *NOTNULL obj,
        generic_transaction_t *NOTNULL mem_op,
        map_info_t map_info);

typedef struct io_memory_interface {
        map_func_t map;
        operation_func_t operation;
} io_memory_interface_t;

#define IO_MEMORY_INTERFACE "io_memory"
// ADD INTERFACE io_memory_interface

/* <add id="translate_interface_t">
   The <iface>translate</iface> interface is implemented by objects
   that bridge between memory spaces. <fun>translate()</fun> can
   change fields like <var>size</var> and <var>physical_address</var>
   in the <arg>mem_op</arg>. The return value from
   <fun>translate()</fun> can be a target memory space or
   <const>NULL</const> in which case the space provided in the
   configuration is used.

   <insert-until text="// ADD INTERFACE translate_interface"/>
   </add> */
typedef struct {
        conf_object_t *(*translate)(conf_object_t *NOTNULL obj,
                                    generic_transaction_t *NOTNULL mem_op,
                                    map_info_t mapinfo);
} translate_interface_t;

#define TRANSLATE_INTERFACE "translate"
// ADD INTERFACE translate_interface

/* <add id="bridge_interface_t">
   The <iface>bridge</iface> interface is implemented by objects
   that bridge between memory spaces. The <fun>not_taken</fun> function
   is called if the access is not claimed by any device in the
   destination memory-space. If a memory transaction reaches a mapping
   that has the same bridge object as the previous mapping, the access
   is considered as not taken, and the <fun>not_taken</fun> function
   for the first bridge mapping is called.
   <insert-until text="// ADD INTERFACE bridge_interface"/>
   </add> */
typedef struct {
        exception_type_t (*not_taken)(conf_object_t *NOTNULL obj,
                                      conf_object_t *NOTNULL src_space,
                                      conf_object_t *NOTNULL dst_space,
                                      exception_type_t ex,
                                      generic_transaction_t *NOTNULL mem_op,
                                      map_info_t mapinfo);
} bridge_interface_t;

#define BRIDGE_INTERFACE "bridge"
// ADD INTERFACE bridge_interface

/* <add id="map_demap_interface_t">
   Interface used to dynamically add and remove mappings in a memory space.
   The first argument to all functions, <param>space</param> is the memory
   space to map an object in. The <param>dev</param> argument is the object to
   map or unmap. This object must implement one of the following interfaces:
   <iface>io_memory</iface>, <iface>_ram</iface>, <iface>_rom</iface>,
   <iface>port_space</iface>, <iface>translate</iface>, <iface>bridge</iface>
   and <iface>memory_space</iface>. If the object implements one of the last
   two interfaces, the <param>target</param> argument must be supplied with an
   object of the class that the translator/bridge maps to.
   
   The <param>function</param> argument to <fun>remove_map</fun> is the
   identification number of a specific mapping, specified in the
   <param>map_info</param> structure when the mapping was created by
   <fun>add_map</fun>.

   An object implementing the <iface>translate</iface> may have a target
   object that implements one of <iface>memory_space</iface>,
   <iface>_ram</iface> and <iface>_rom</iface>. This means that a translator
   object can translate an address into a new memory space, or a RAM/ROM
   object. The <param>target</param> argument may be set to NULL. Then the
   target has to be provided by the translator on each access, and it is
   assumed to be of the default memory space class.

   An object implementing the <iface>bridge</iface> must have a target object
   that implements the <iface>memory_space</iface>.

   The <fun>add_default</fun> function adds a mapping that is used for accesses
   to addresses without any other mapping. Default mappings can not map to
   objects that implement the <iface>_ram</iface> or <iface>_rom</iface>.

   All functions in the <iface>map_demap</iface> return 1 on success and 0 on
   failure.

   More information about the different kinds of memory space mappings is
   available in the Simics User Guide.

   <insert-until text="// ADD INTERFACE map_demap_interface"/>
   </add>
*/
typedef struct {
        int (*add_map)(conf_object_t *NOTNULL space,
                       conf_object_t *NOTNULL dev,
                       conf_object_t *target,
                       map_info_t map_info);
        int (*remove_map)(conf_object_t *NOTNULL space,
                          conf_object_t *NOTNULL dev,
                          int function);
        int (*add_default)(conf_object_t *NOTNULL space,
                           conf_object_t *NOTNULL dev,
                           conf_object_t *target,
                           map_info_t map_info);
        void (*remove_default)(conf_object_t *NOTNULL space);
} map_demap_interface_t;

#define MAP_DEMAP_INTERFACE "map_demap"
// ADD INTERFACE map_demap_interface

/* ADD INTERFACE cache_miss_interface */

/* <add-type id="cache_miss_interface_t">
   This interface can be used to gather cache miss traces. Classes
   that model caches typically provide an attribute through which
   on object implementing the cache miss interface can be connected.
   </add-type> */
typedef struct {
        void (*cache_miss)(conf_object_t *NOTNULL obj,
                           data_or_instr_t data_or_instr,
                           read_or_write_t read_or_write,
                           logical_address_t logical_address,
                           physical_address_t physical_address);
} cache_miss_interface_t;

#define CACHE_MISS_INTERFACE "cache_miss"

/* <add id="simics api types">
   <name index="true">pci_memory_transaction_t</name>
   <doc>
   <doc-item name="NAME">pci_memory_transaction_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="pci_memory_transaction_t def"/>
   </doc-item>
   <doc-item name="DESCRIPTION">
   The <type>pci_memory_transaction_t</type> is used for memory
   accesses initiated by PCI devices. It is based on a generic
   memory transaction struct, followed by two PCI specific fields.
   The first, <var>original_size</var>, should not be accessed if
   possible since it may be changed in future Simics versions. It
   specifies the size of the original memory access before possible
   split up. The <var>bus_address</var> field is the address of the
   initiating PCI device in a PCI Type 1 address format, i.e.
   <tt>bus &lt;&lt; 16 | device &lt;&lt; 11 | function &lt;&lt; 8</tt>.
   A <type>generic_transaction_t</type> can be converted to a
   <type>pci_memory_transaction_t</type> if the <var>ini_type</var>
   field has the value <tt>Sim_Initiator_PCI_Device</tt>.
   </doc-item>
   <doc-item name="SEE ALSO">generic_transaction_t,
   PCI_data_from_memory</doc-item>
   </doc></add>

   <add-type id="pci_memory_transaction_t def"></add-type>
*/
typedef struct pci_memory_transaction {
        generic_transaction_t s;
        /* The original_size field will probably be moved to the
           generic_transaction_t structure in the future */
        uint32 original_size;
        int bus_address;
} pci_memory_transaction_t;

struct alpha_memory_transaction;
struct arm_memory_transaction;
struct ia64_memory_transaction;
struct mips_memory_transaction;
struct ppc_memory_transaction;
struct v9_memory_transaction;
struct x86_memory_transaction;
struct alpha_memory_transaction *SIM_alpha_mem_trans_from_generic(
        generic_transaction_t *NOTNULL mop);
struct arm_memory_transaction *SIM_arm_mem_trans_from_generic(
        generic_transaction_t *NOTNULL mop);
struct ia64_memory_transaction *SIM_ia64_mem_trans_from_generic(
        generic_transaction_t *NOTNULL mop);
struct mips_memory_transaction *SIM_mips_mem_trans_from_generic(
        generic_transaction_t *NOTNULL mop);
struct ppc_memory_transaction *SIM_ppc_mem_trans_from_generic(
        generic_transaction_t *NOTNULL mop);
struct v9_memory_transaction *SIM_v9_mem_trans_from_generic(
        generic_transaction_t *NOTNULL mop);
struct x86_memory_transaction *SIM_x86_mem_trans_from_generic(
        generic_transaction_t *NOTNULL mop);
struct pci_memory_transaction *SIM_pci_mem_trans_from_generic(
        generic_transaction_t *NOTNULL mop);

cycles_t VT_last_device_stall_time(void);

struct dmacache;
exception_type_t VT_dmacache_access(struct dmacache *dc,
                                    generic_transaction_t *mop);
exception_type_t VT_dmacache_write(struct dmacache *dc,
                                   conf_object_t *initiator,
                                   physical_address_t addr, attr_value_t data);
struct dmacache *VT_dmacache_alloc(conf_object_t *memory_space);
void VT_dmacache_free(struct dmacache *dc);

void VT_no_side_effects_IO(generic_transaction_t *mop, lang_void *regptr);

#endif /* _SIMICS_CORE_MEMORY_H */
