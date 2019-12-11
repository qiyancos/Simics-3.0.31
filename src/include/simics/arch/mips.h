/*
 * simics/arch/mips.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_ARCH_MIPS_H
#define _SIMICS_ARCH_MIPS_H

/* <add id="simics arch api types">
   <name index="true">mips_memory_transaction_t</name>
   <doc>
   <doc-item name="NAME">mips_memory_transaction_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="mips_memory_transaction_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">

   This is the MIPS specific memory transaction data structure.
   The generic data is stored in the <var>s</var> field.

   The <var>cache_coherency</var> field specifies the cache coherency attribute
   of the memory transaction, as defined by the C field of the EntryLo0 and
   EntryLo1 coprocessor 0 registers.

   </doc-item>
   </doc>

   </add>
*/

/* <add-type id="mips_memory_transaction_t def">
   </add-type> 
*/
typedef struct mips_memory_transaction {

        /* generic transaction */
        generic_transaction_t s;

        /* Cache coherency, values as the C field in EntryLo0 and EntryLo1. */
        unsigned int cache_coherency:3;

        /* if non-zero, the id needed to calculate the program counter */
        intptr_t turbo_miss_id;
} mips_memory_transaction_t;


/* <add id="mips_interface_t">
   This interface is implemented by MIPS processors to provide various
   functionality that is specific for this class of processors.

   There are currently no MIPS-specific functions.

   <insert-until text="// ADD INTERFACE mips_interface"/>
   </add> */

typedef struct mips_interface {
        int dummy;
} mips_interface_t;

#define MIPS_INTERFACE "mips"
// ADD INTERFACE mips_interface

#endif /* _SIMICS_ARCH_MIPS_H */
