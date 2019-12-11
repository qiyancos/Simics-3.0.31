/*
 * simics/core/decoder.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_DECODER_H
#define _SIMICS_CORE_DECODER_H

/* <add id="service routine function">
   <insert-upto text=";"/><ndx>service_routine_t</ndx>
   </add>
*/
typedef exception_type_t (*service_routine_t)(conf_object_t *cpu, 
                                              unsigned int arg, 
                                              lang_void *user_data);

/* <add id="instruction info">
   <insert-upto text="instruction_info_t;"/>
   <ndx>instruction_info_t</ndx>

   <var>ii_ServiceRoutine</var> is a pointer to a service routine to
   be called by Simics every time the instruction is executed. It has
   the following prototype:
   
   <insert id="service routine function"/> 

   <var>ii_Arg</var> is the argument that will be passed on to the
   service routine. It typically contains a bit-field of parameters to
   the instruction such as register numbers or intermediate
   values. It can also be a pointer to a structure if more appropriate.
   
   <var>ii_Type</var> is either <pp>UD_IT_SEQUENTIAL</pp> or
   <pp>UD_IT_CONTROL_FLOW</pp>.  A sequential type means that the
   instruction does not perform any branches and the update of the
   program counter(s) is handled by Simics. In a control flow
   instruction on the other hand it is up to the user to set the
   program counter(s).

   <var>ii_RegInfo</var> should be used if Simics is running in
   out of order mode. An array of <type>reg_info_t</type> should be
   allocated that describes the registers the instruction uses and if
   they are used as input and/or output. The array should be
   terminated with a dummy register (<var>id</var> equal to 0) which
   is neither input nor output (<var>in</var> and <var>out</var> both
   zero).

   <insert id="reg_info type"/>

   The <var>register_id</var> of the PC(s) should not be filled in,
   Simics handles that automatically. If the instruction manipulates a
   register not listed the value <pp>Sim_RI_Sync</pp> should be
   used, this will disallow the instruction to run out of order.

   The array needs to be deallocated when the instruction is
   flushed, see below.

   <var>ii_UserData</var> can be filled in with
   other data.

   The service routine function should return an exception when it is
   finished to signal its status. If no exception occurs
   <const>Sim_PE_No_Exception</const> should be returned.

   See <type>exception_type_t</type> in <file>core/types.h</file> for
   the different exceptions available.

   A special return value, <const>Sim_PE_Default_Semantics</const>, can be
   returned; this signals Simics to run the default semantics for the
   instruction. This is useful if the semantics of an instruction
   should be changed but the user routine does not want to handle it all
   the time.

   </add> */
typedef struct instruction_info {
        service_routine_t  ii_ServiceRoutine;
        unsigned int       ii_Arg;
        unsigned int       ii_Type;
        reg_info_t        *ii_RegInfo;
        lang_void         *ii_UserData;
        logical_address_t  ii_LogicalAddress;
        physical_address_t ii_PhysicalAddress;
} instruction_info_t;

/* <add id="user decoder">
   <insert-upto text="decoder_t;"/>
   <ndx>decoder_t</ndx>

   The <fun>decode</fun> function is called to decode an instruction
   pointed to by <param>code</param>.  The first byte represents the
   lowest address of the instruction in the simulated
   memory. <param>valid_bytes</param> tells how many bytes can be
   read.  The current CPU is given in the <param>cpu</param>
   parameter.  When the decoder has successfully decoded the
   instruction, it fills in the <param>ii</param> structure, and
   returns the number of bytes used in the decoding.  If it does not
   apply to the given instruction, it should return zero.  If the
   decoder needs more data it should return a negative number
   corresponding to the total number of bytes needed. Simics will then
   call the decoder again with more available bytes. This process is
   repeated until the decoder accepts or rejects the instruction.

   Note that in a shared memory multiprocessor, the <param>cpu</param>
   used in decoding may differ from the CPU that executes the
   instruction, since the decoded instructions are cached by Simics.

   The <fun>disassemble</fun> function is called to disassemble an
   instruction.  It uses the same <param>code</param>,
   <param>valid_bytes</param>, and <param>cpu</param> parameters as
   the <fun>decode</fun> function.  In addition, it takes a pointer to
   a string buffer, <param>buffer</param>.  The disassembly should be
   written to this buffer as a null-terminated string with a maximum
   length of 256 characters, including the null terminator.  The
   return value is handled identically to the that of the
   <fun>decode</fun> function.

   The <fun>flush</fun> function is called to free any memory allocated when
   decoding an instruction, including the register info array.  Just like the
   other functions, it should return zero if it doesn't recognize the
   instruction, and non-zero if it has handled it.  Usually, the way to
   recognize if a decoded instruction is the right one is to compare
   <tt>ii->ii_ServiceRoutine</tt> with what is set in the <param>decode</param>
   function. Note that the <param>cpu</param> parameter is the processor that
   caused the flush. It is more or less an arbitrary processor and should be
   ignored.

   In addition to the function pointers, the structure contains a
   <param>user_data</param> pointer that is passed to all the
   functions.  This can be used for passing any data to the decoder
   functions.

   The <type>instruction_info_t</type> is defined like this.

   <insert id="instruction info"/>

   </add> */
typedef struct {
        void *user_data;
        int (*NOTNULL decode)(unsigned char *code,
                              int valid_bytes,
                              conf_object_t *cpu,
                              instruction_info_t *ii,
                              void *user_data);
        int (*NOTNULL disassemble)(unsigned char *code,
                                   int valid_bytes,
                                   conf_object_t *cpu,
                                   char *buffer,
                                   void *user_data);
        int (*NOTNULL flush)(conf_object_t *cpu,
                             instruction_info_t *ii,
                             void *user_data);
} decoder_t;

/* <add id="compatibility user decoder">
   <insert-upto text=";"/>
   <ndx>user_decoder_t</ndx>

   <tt>code</tt> is a pointer to the instruction to decode.  The first
   byte represents the lowest address of the instruction in the
   simulated memory. <tt>valid_bytes</tt> tells how many bytes
   can be read.  If the decoder needs more data it should return a
   negative number corresponding to the total number of bytes
   needed. Simics will then call the decoder again with more available
   bytes. This process is repeated until the decoder accepts or
   rejects the instruction. If the instruction is accepted its length
   in bytes should be returned, otherwise zero.

   <tt>cpu</tt> is the cpu decoding the instruction. Note that in
   a shared memory multiprocessor, this may differ from the one executing
   the instruction since decoded instructions are cached. 

   <tt>action</tt> is whether Simics wants to decode, disassemble or
   flush a previously decoded instruction. For decoding, the value is
   <tt>UD_ACTION_DECODE</tt> and the instruction_info_t structure
   <tt>ii</tt> should be filled in. The structure has the following
   fields:

   <insert id="instruction info"/>

   If Simics wants to disassemble the instruction the <tt>action</tt>
   value will be <tt>UD_ACTION_DISASS</tt> and the <tt>string_buffer</tt>
   should be filled with the disassembled instruction (max length is
   256 characters). The <tt>ii</tt> structure should be ignored.

   A value of UD_ACTION_FLUSH (code and string_buffer will be null,
   valid_bytes zero) means that Simics wants to flush a cached decoded
   instruction. The instruction_info_t structure <tt>ii</tt> will then
   hold the values previously stored there. If the user-decoder
   recognizes the <tt>ii->ii_ServiceRoutine</tt> function as its own
   it should now free all allocated user data including the register
   info array, if allocated, and return a non-zero value to indicate
   success. Otherwise zero should be returned letting other
   user-decoders have a shot.

   </add> */
typedef int (*NOTNULL user_decoder_t)(unsigned char *code,
                                      int valid_bytes,
                                      conf_object_t *cpu,
                                      instruction_info_t *ii,
                                      int action,
                                      char *string_buffer);

/* Instruction type */

#define UD_IT_SEQUENTIAL   1
#define UD_IT_CONTROL_FLOW 2

/* Decode action */

#define UD_ACTION_DECODE 1
#define UD_ACTION_DISASS 2
#define UD_ACTION_FLUSH  3

/* Protos */

#if !defined(GULP)
void SIM_register_arch_decoder(decoder_t *NOTNULL decoder,
                               const char *arch, int arch_mode);
void SIM_unregister_arch_decoder(decoder_t *NOTNULL decoder,
                                 const char *arch, int arch_mode);

void SIM_register_decoder(user_decoder_t decoder);
void SIM_unregister_decoder(user_decoder_t decoder);
#endif /* !GULP */

#endif /* _SIMICS_CORE_DECODER_H */
