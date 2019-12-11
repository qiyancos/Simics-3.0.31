/*
 * simics/core/breakpoints.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_BREAKPOINTS_H
#define _SIMICS_CORE_BREAKPOINTS_H

/* <add-type id="breakpoint_vector_t"><ndx>breakpoint_vector_t</ndx>
   </add-type> */
typedef struct {
        int             size;
        breakpoint_t  **vector;
} breakpoint_vector_t;


/* <add-type id="enum breakpoint_flag"></add-type> */
enum breakpoint_flag {
        Sim_Breakpoint_Temporary = 1,
        Sim_Breakpoint_Simulation = 2,
        Sim_Breakpoint_Private = 4
};

breakpoint_id_t SIM_breakpoint(conf_object_t *obj,
                               breakpoint_kind_t type,
                               access_t access,
                               uint64 address,
                               uint64 length,
                               unsigned flags);
void SIM_delete_breakpoint(breakpoint_id_t id);

void SIM_breakpoint_remove(int id, access_t access,
                           generic_address_t address,
			   generic_address_t length);

/* <add-type id="struct breakpoint_range"></add-type> */
struct breakpoint_range {
        generic_address_t          lower;
        generic_address_t          upper;
        struct breakpoint_range   *next;
};

/* <add id="breakpoint_interface_t">

   <ndx>insert_bp_func_t</ndx>
   <ndx>remove_bp_func_t</ndx>
   <ndx>remove_bp_range_func_t</ndx>
   <ndx>get_bp_ranges_func_t</ndx>
   <ndx>get_bp_func_t</ndx>

   The breakpoint interface are implemented by any object who supports
   breaking on an address range.

   <insert-until text="// ADD INTERFACE breakpoint_interface"/>

   Most functions in the interface get the <i>object</i> and the
   <i>bp</i> arguments as in-parameters. Object is the object
   implementing this interface and bp is a structure that is used to
   identify the breakpoint. bp is of type <b>breakpoint_t</b> and is
   declared like this:

   <name index="true">breakpoint_t</name>
   <smaller>
   <insert id="breakpoint_t def"/>
   <insert id="struct breakpoint"/>
   </smaller>

   <b>insert_breakpoint</b> are called when a breakpoint is added on
   the object. This can be done with the break command or with
   the SIM_breakpoint API function.
   
   <b>remove_breakpoint</b> should remove the breakpoint and further
   accesses to the address range should not stop the simulation.

   <b>remove_breakpoint_range</b> is called when a range should be
   removed from a breakpoint. It is thus possible to create holes in
   the range. See SIM_breakpoint_remove. <i>access</i> is what kind of
   accesses should be removed. See SIM_breakpoint for a description of
   the access parameter.

   <b>get_breakpoint_ranges</b> should return a list of ranges
   currently set.  <type><idx>breakpoint_range_t</idx></type> is
   declared like this:
   
   <insert id="breakpoint_range_t def"/>
   <insert id="struct breakpoint_range"/>

   <b>get_breakpoints</b> should return a vector of breakpoints set on
   the object matching <i>access</i> and <i>type</i>. See
   SIM_breakpoint for a description of access and type.
   <b>breakpoint_vector_t</b> is declared like this:

   <insert id="breakpoint_vector_t"/>

   </add> */
typedef void (*insert_bp_func_t)
        (conf_object_t *object, breakpoint_t *bp, 
         generic_address_t start, generic_address_t end);
typedef void (*remove_bp_func_t)
        (conf_object_t *object, breakpoint_t *bp);
typedef void (*remove_bp_range_func_t)
        (conf_object_t *object, breakpoint_id_t bp_id,
         access_t access, 
         generic_address_t start, generic_address_t end);
typedef breakpoint_range_t *(*get_bp_ranges_func_t)
        (conf_object_t *object, 
         breakpoint_t *bp);
typedef breakpoint_vector_t (*get_bp_func_t)
        (conf_object_t *object, 
         access_t access, 
         breakpoint_kind_t type, 
         generic_address_t start, 
         generic_address_t end);

struct breakpoint_interface {
        insert_bp_func_t       insert_breakpoint;
        remove_bp_func_t       remove_breakpoint;
        remove_bp_range_func_t remove_breakpoint_range;
        get_bp_ranges_func_t   get_breakpoint_ranges;
        get_bp_func_t          get_breakpoints;
};

#define BREAKPOINT_INTERFACE "breakpoint"
// ADD INTERFACE breakpoint_interface

int VT_magic_break_query(void);
int VT_magic_break_enable(int enable);

#endif /* _SIMICS_CORE_BREAKPOINTS_H */
