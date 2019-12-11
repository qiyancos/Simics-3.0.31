/*
 * simics/core/profiling.h
 *
 * This file is part of Virtutech Simics
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_PROFILING_H
#define _SIMICS_CORE_PROFILING_H

#define FOR_ALL_ADDRESS_TYPES(op)               \
        op(Invalid),                            \
        op(Physical),                           \
        op(Virtual)
#define ADDRESS_TYPE_ENUM_OP(s) Addr_Type_ ## s
typedef enum {
        FOR_ALL_ADDRESS_TYPES(ADDRESS_TYPE_ENUM_OP)
} addr_type_t;


/* <add id="simics api types">
   <name index="true">addr_prof_iter_t</name>
   <doc>
   <doc-item name="NAME">addr_prof_iter_t</doc-item>
   <doc-item name="DESCRIPTION">

   An address profile iterator will iterate over a specified portion of the
   address space in some unspecified order, and return every nonzero counter
   value exactly once. When done, it will return 0.

   </doc-item>
   </doc>
   </add>
*/
typedef struct addr_prof_iter {
        uint64 (*next)(struct addr_prof_iter *i);
        void (*destroy)(struct addr_prof_iter *i);
        generic_address_t addr;
} addr_prof_iter_t;

/* A branch arc iterator will iterate over a specified portion of the to or
   from branch address space in order (direction address, then other address,
   then type), and return every branch arc with a given type exactly once. When
   done, it will return 0. */

/*
  <add-type id="branch_arc_type_t def"></add-type> 
*/
typedef enum {
        Branch_Arc_Branch,
        Branch_Arc_Exception,
        Branch_Arc_Exception_Return,
        Branch_Arc_Max
} branch_arc_type_t;

/*
  <add-type id="branch_recorder_direction_t def"></add-type> 
*/
typedef enum {
        BR_Direction_From,
        BR_Direction_To
} branch_recorder_direction_t;

#if !defined(GULP) /* only for C */

/* <add id="experimental">

   <b>EXPERIMENTAL.</b> While this functionality is expected to be retained in
   future releases, the interface is likely to change.

   </add>
*/

/* <add-fun id="simics api profiling">

   <insert id="experimental"/>

   <short>Iterate over address profile counters</short>

   An address profile iterator visits some of the counters of an address
   profiler in some order. It is obtained from the <fun>iter</fun> function of
   the <iface>address_profiler</iface> interface.

   <fun>SIM_iter_next</fun> advances the address profile iterator
   <param>iter</param> to the next nonzero counter and returns the count. It
   will return 0 when there are no more counters to visit. Note that the order
   in which the counters are visited is unspecified.

   <fun>SIM_iter_addr</fun> returns the address of the counter returned by the
   most recent call to <fun>iter_next</fun>.

   When you are done with the iterator, deallocate it with
   <fun>SIM_iter_free</fun>.

   </add-fun>
*/
FORCE_INLINE uint64
SIM_iter_next(addr_prof_iter_t *iter)
{
        return iter->next(iter);
}

/* <append-fun id="SIM_iter_next"/> */
FORCE_INLINE generic_address_t
SIM_iter_addr(addr_prof_iter_t *iter)
{
        return iter->addr;
}

/* <append-fun id="SIM_iter_next"/> */
FORCE_INLINE void
SIM_iter_free(addr_prof_iter_t *iter)
{
        iter->destroy(iter);
}

#endif /* !GULP */


/* <add id="data_profiler_interface_t">

   This interface allows manipulation of the profiling data stored in an
   object. (Note that not all objects that store profiling data implement this
   interface.)

   <fun>save</fun> writes the profiling data to a file. <fun>load</fun> reads
   profiling data from a file, and adds it to whatever data was already present
   in the profiler. <fun>clear</fun> resets all counters in the profiler to
   zero. (So, to replace the current data with data stored in a file, you can
   call first <fun>clear</fun>, then <fun>load</fun>.)

   <fun>accum_in_range</fun> computes the sum of all counters in an address
   range, from <param>start</param> to <param>end</param>, inclusive. This
   function is deprecated; you should use the functions of the
   <iface>address_profiler</iface> interface instead.

   <insert-until text="// ADD INTERFACE data_profiler_interface"/>
   </add>
*/
typedef struct {
        uint64 (*accum_in_range)(conf_object_t *profiler,
                                 uint64 start, uint64 end);
        void (*save)(conf_object_t *profiler, const char *file);
        void (*load)(conf_object_t *profiler, const char *file);
        void (*clear)(conf_object_t *profiler);
#if !defined(GULP) && !defined(DOC)
        /* actually returns a prof_data_t* */
        void *(*get_prof_data)(conf_object_t *profiler);
#endif
} data_profiler_interface_t;

#define DATA_PROFILER_INTERFACE "_data_profiler"
// ADD INTERFACE data_profiler_interface

#if !defined(GULP)
typedef void (*data_profiler_flush_t)(conf_object_t *profiler, void *param);
void VT_profiler_add_flush(
        conf_object_t *dp, data_profiler_flush_t flush_fun,
        void *flush_param);
void VT_profiler_remove_flush(
        conf_object_t *dp, data_profiler_flush_t flush_fun,
        void *flush_param);
#endif /* !GULP */


const char *VT_addr_type_to_str(addr_type_t type);
addr_type_t VT_addr_type_from_str(const char *type);

/* <add id="address_profiler_interface_t">

   Interface for getting statistics out of profilers. The target is some kind
   of profiler whose data can be meaningfully viewed as counts per address.

   The function <fun>num_views</fun> returns the number <math>k</math> of
   different ways you can view the data of this object. The view selection
   parameter <param>view</param> to all other functions in the interface
   accepts values between 0 and <math>k - 1</math>.

   <fun>description</fun> returns a short string that explains what the data
   means. <fun>physical_addresses</fun> returns true if the profiler works with
   physical addresses, or false if it uses virtual addresses.
   <fun>address_bits</fun> returns the number of bits in an address.

   <fun>granularity_log2</fun> returns the base 2 logarithm of the size, in
   bytes, of the address intervals that the counters are associated to. For
   example, if the data is instruction execution count and each instruction is
   4 bytes long, one would expect the granularity to be at least 4 bytes since
   that is the smallest interval containing a whole instruction (but it might
   be more, if the profiler is less fine-grained for some reason). And for a
   4-byte granularity, <fun>granularity_log2</fun> would return 2.

   <fun>sum</fun> returns the sum of all counters between <param>start</param>
   and <param>stop</param>, inclusive. <fun>max</fun> returns the maximum value
   of any counter in the range.

   <fun>iter</fun> returns an address profile iterator that will visit all
   nonzero counters in the range precisely once, in some order. In C, you can
   use the functions <fun>SIM_iter_next</fun>, <fun>SIM_iter_addr</fun> and
   <fun>SIM_iter_free</fun> to operate the iterator. In Python, it works just
   like any other iterator, and returns (count, address) pairs. Note that you
   may not continue to use the iterator after the underlying address profiler
   has been modified.

   <insert-until text="// ADD INTERFACE address_profiler_interface"/>
   </add>
*/
typedef struct address_profiler_interface {
        addr_prof_iter_t *(*iter)(conf_object_t *prof_obj, unsigned view,
                                  generic_address_t start,
                                  generic_address_t stop);
        uint64 (*sum)(conf_object_t *prof_obj, unsigned view,
                      generic_address_t start, generic_address_t end);
        uint64 (*max)(conf_object_t *prof_obj, unsigned view,
                      generic_address_t start, generic_address_t end);
        unsigned (*granularity_log2)(conf_object_t *prof_obj, unsigned view);
        int (*address_bits)(conf_object_t *prof_obj, unsigned view);
        int (*physical_addresses)(conf_object_t *prof_obj, unsigned view);
        const char *(*description)(conf_object_t *prof_obj, unsigned view);
        unsigned (*num_views)(conf_object_t *prof_obj);
} address_profiler_interface_t;

#define ADDRESS_PROFILER_INTERFACE "address_profiler"
// ADD INTERFACE address_profiler_interface

/* <add id="branch_arc_interface_t">
   <ndx>branch_arc_iter_t</ndx>
   <ndx>branch_arc_t</ndx>
   <ndx>branch_arc_type_t</ndx>
   <ndx>branch_recorder_direction_t</ndx>

   Interface for getting branch arcs out profilers. The target is some kind of
   profiler whose data can be meaningfully viewed as branch arcs (usually a
   branch profiler).

   <fun>iter</fun> returns a branch arc iterator that will visit all branch
   arcs in the range precisely once, in order of selected address (to or from,
   selected with <param>dir</param>), other address and type. In Python, it
   works just like any other iterator, and returns (from, to, counter, type)
   tuples. Note that you may not continue to use the iterator after the
   underlying profiler has been modified.

  <type>branch_arc_type_t</type> defines the branch types returned by a branch
  arc iterator.

  <dl>
  <dt><tt>Branch_Arc_Branch</tt></dt> <dd>Normal branch operation</dd> 
  <dt><tt>Branch_Arc_Exception</tt></dt> <dd>Branch because an exception 
  was encountered</dd>
  <dt><tt>Branch_Arc_Exception_Return</tt></dt> <dd>Branch to finish an 
  exception handler</dd>
  </dl>

   <insert id="branch_arc_type_t def"/>
   <insert id="branch_recorder_direction_t def"/>
   <insert-until text="// ADD INTERFACE branch_arc_interface"/>

   </add>
*/
typedef struct {
        uinteger_t addr_from;
        uinteger_t addr_to;
        integer_t count;
        branch_arc_type_t type;
} branch_arc_t;

typedef struct branch_arc_iter {
        branch_arc_t *(*next)(struct branch_arc_iter *i);
        void (*destroy)(struct branch_arc_iter *i);
} branch_arc_iter_t; 

typedef struct branch_arc_interface {
        branch_arc_iter_t *(*iter)(conf_object_t *prof_obj,
                                   generic_address_t start,
                                   generic_address_t stop,
                                   branch_recorder_direction_t dir);
} branch_arc_interface_t;

#define BRANCH_ARC_INTERFACE "branch_arc"
// ADD INTERFACE branch_arc_interface

#endif /* _SIMICS_CORE_PROFILING_H */
