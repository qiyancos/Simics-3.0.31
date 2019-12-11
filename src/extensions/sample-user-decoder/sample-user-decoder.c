/*
  sample-user-decoder.c - decoder extension module for adding a user decoder

  Copyright 1998-2007 Virtutech AB
  
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include <simics/api.h>
#include <simics/alloc.h>

/* Define OOO_MODE if Simics is running in out of order mode.
   It makes my nop dependent of %o1 */

/*#define OOO_MODE*/

/*
 * This module works with several CPU architectures, and uses
 * different encodings for different architectures.
 */
static uint8 alpha_nop[]      = { 0x1f, 0x04, 0xff, 0x47 };
static uint8 arm_nop[]        = { 0, 0, 0xa0, 0xe1 };
static uint8 mips32_nop[]     = { 0, 0, 0, 0 };
static uint8 ppc32_nop[]      = { 0x60, 0, 0, 0 };
static uint8 v9_nop[]         = { 0x01, 0, 0, 0 };
static uint8 ia64_nop[]       = { 0x40, 4, 0, 8, 0, 0x14, 0, 0 }; /* nop.i 17;; */
static uint8 x86_nop[]        = { 0x90 };

static decoder_t my_decoder;
static conf_object_t *last_cpu = NULL;
static uint8 *nop_code = NULL;
static int instr_size = 0;

static exception_type_t
my_nop(conf_object_t *cpu, unsigned int arg, void *user_data)
{
        printf("- Executing my nop (arg = %d) -\n", arg);
        
        return Sim_PE_No_Exception;
}

/* This function is called when we are called from a new CPU. */
static void
update_cpu(conf_object_t *cpu)
{
        attr_value_t attr = SIM_get_attribute(cpu, "architecture");
        const char *arch = attr.u.string;
        assert(attr.kind == Sim_Val_String);
        if (strcmp(arch, "ppc32") == 0 || strcmp(arch, "ppc64") == 0) {
                nop_code = ppc32_nop;
                instr_size = 4;
        } else if (strcmp(arch, "sparc-v9") == 0) {
                nop_code = v9_nop;
                instr_size = 4;
        } else if (strcmp(arch, "ia64") == 0) {
                nop_code = ia64_nop;
                instr_size = 8;
        } else if (strcmp(arch, "alpha") == 0) {
                nop_code = alpha_nop;
                instr_size = 4;
        } else if (strcmp(arch, "arm") == 0) {
                nop_code = arm_nop;
                instr_size = 4;
        } else if (strcmp(arch, "mips32") == 0) {
                nop_code = mips32_nop;
                instr_size = 4;
        } else if (strcmp(arch, "x86") == 0) {
                nop_code = x86_nop;
                instr_size = 1;
        } else if (strcmp(arch, "x86-64") == 0) {
                nop_code = x86_nop;
                instr_size = 1;
        } else {
                printf("sample-user-decoder:"
                       " Unknown CPU architecture: %s\n",
                       arch);
        }
        last_cpu = cpu;
}

static int
my_decode(uint8 *code, int valid_bytes, conf_object_t *cpu,
          instruction_info_t *ii, void *data)
{
        if (cpu != last_cpu)
                update_cpu(cpu);

        if (instr_size > valid_bytes)
                return -instr_size;

        if (memcmp(code, nop_code, instr_size) == 0) {
                printf("- Decoding my nop -\n");
                ii->ii_Type           = UD_IT_SEQUENTIAL;
                ii->ii_ServiceRoutine = my_nop;
                ii->ii_Arg            = 13;
                ii->ii_UserData       = 0;
#ifdef OOO_MODE
                ii->ii_RegInfo        = MM_ZALLOC(2, reg_info_t);
                ii->ii_RegInfo[0].id  = SIM_REG_ID_RN(9);
                ii->ii_RegInfo[0].in  = 1;
                ii->ii_RegInfo[0].out = 1;
#endif
                return instr_size;
        } else
                return 0;
}

static int
my_disassemble(uint8 *code, int valid_bytes, conf_object_t *cpu,
               char *string_buffer, void *data)
{
        if (cpu != last_cpu)
                update_cpu(cpu);

        if (instr_size > valid_bytes)
                return -instr_size;

        if (memcmp(code, nop_code, instr_size) == 0) {
                strcpy(string_buffer, "my nop");
                return instr_size;
        } else
                return 0;
}

static int
my_flush(conf_object_t *cpu, instruction_info_t *ii, void *data)
{
        if (ii->ii_ServiceRoutine == my_nop) {
                /* This is the time to dealloc ii->ii_UserData */
                printf("# Flushing my nop #\n");
#ifdef OOO_MODE
                MM_FREE(ii->ii_RegInfo);
#endif
                return 1;
        } else {
                /* Not mine */
                return 0;
        }
}

DLL_EXPORT void
init_local(void)
{
        my_decoder.decode = my_decode;
        my_decoder.disassemble = my_disassemble;
        my_decoder.flush = my_flush;

        SIM_register_arch_decoder(&my_decoder, "ppc32", 0);
        SIM_register_arch_decoder(&my_decoder, "ppc64", 1);
        SIM_register_arch_decoder(&my_decoder, "ppc64 TA", 2);
        SIM_register_arch_decoder(&my_decoder, "sparc-v9", 0);
        SIM_register_arch_decoder(&my_decoder, "ia64", 0);
        SIM_register_arch_decoder(&my_decoder, "alpha", 0);
        SIM_register_arch_decoder(&my_decoder, "arm", 0);
        SIM_register_arch_decoder(&my_decoder, "mips32", 0);
        SIM_register_arch_decoder(&my_decoder, "x86", 0); /* 16-bit mode */
        SIM_register_arch_decoder(&my_decoder, "x86", 1); /* 32-bit mode */
        SIM_register_arch_decoder(&my_decoder, "x86", 2); /* 64-bit mode */
}
