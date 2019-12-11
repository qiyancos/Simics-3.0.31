/*
 * simics/magic-instruction.h
 *
 * This file is part of Virtutech Simics
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_MAGIC_INSTRUCTION_H
#define _SIMICS_MAGIC_INSTRUCTION_H

/*
 * This file contains the magic instructions for different target
 * architectures, as understood by different compilers.
 *
 *   arch   instr           limit               compilers
 *   -----------------------------------------------------
 *   ia64   nop 0x1?????    0 <= n < 0x100000   gcc
 *   mips   li $zero,n      0 <= n <= 0xffff    gcc
 *   msp430 bis r0,r0       n == 0              gcc
 *   ppc    mr n,n          0 <= n < 32         gcc
 *   ppc64  fmr n,n         0 <= n < 32         gcc
 *   sparc  sethi n,%g0     0 <  n < (1 << 22)  gcc, WS C[++]
 *   x86    xchg bx,bx      n == 0              gcc
 * 
 */

/*
  <add id="magic instruction figure">
  <figure label="magic_instruction_figure">
  <center>
  <table border="cross">
    <tr>
       <td><b>Target</b></td><td><b>Magic instruction</b></td>
                        <td><b>Conditions on <arg>n</arg></b></td>
    </tr>
    <tr>  
       <td>Alpha</td><td><i>binary:</i> <tt>0x70000000</tt></td>
                     <td><i><math>n = 0</math></i></td>
    </tr>
    <tr>
       <td>ARM</td><td><tt>orreq rn, rn, rn</tt></td>
                   <td><math>0 &lt;= n &lt; 15</math></td>
    </tr>
    <tr>
       <td>IA-64</td><td><tt>nop (0x100000 + n)</tt></td>
                    <td><math>0 &lt;= n &lt; 0x100000</math></td>
    </tr>
    <tr>
       <td>MIPS</td><td><tt>li %zero, n</tt></td>
                    <td><math>0 &lt;= n &lt; 0x10000</math></td>
    </tr>
    <tr>
       <td>MSP430</td><td><tt>bis r0,r0</tt></td>
                      <td><math>n = 0</math></td>
    </tr>
    <tr>
       <td>PowerPC 32-bit</td><td><tt>mr n, n</tt></td>
       <td><math>0 &lt;= n &lt; 32</math></td>
    </tr>
    <tr>
       <td>PowerPC 64-bit</td><td><tt>fmr n, n</tt></td>
       <td><math>0 &lt;= n &lt; 32</math></td>
    </tr>
    <tr>
       <td>SPARC</td><td><tt>sethi n, %g0</tt></td>
               <td><math>1 &lt;= n &lt; 0x400000</math></td>
    </tr>
    <tr>
       <td>x86</td><td><tt>xchg %bx, %bx</tt></td>
                   <td><math>n = 0</math></td>
    </tr>
  </table>
  </center>
  <caption>Magic instructions for different Simics Targets</caption>
  </figure>
  </add>
*/

/* BEGIN EXPORT simics/magic-instruction.h */

#define __MAGIC_CASSERT(p) do {                                 \
        typedef int __check_magic_argument[(p) ? 1 : -1];       \
} while (0)

#if defined(__GNUC__) || defined(__INTEL_COMPILER)

#if defined(__alpha)

#define MAGIC(n) do {                                   \
	__MAGIC_CASSERT(!(n));                          \
        __asm__ __volatile__ (".long 0x70000000");      \
} while (0)

#define MAGIC_BREAKPOINT MAGIC(0)

#elif defined(__sparc) || defined(__sparc__)

#define MAGIC(n) do {                                   \
	__MAGIC_CASSERT((n) > 0 && (n) < (1U << 22));   \
        __asm__ __volatile__ ("sethi " #n ", %g0");     \
} while (0)

#define MAGIC_BREAKPOINT MAGIC(0x40000)

#elif defined(__i386) || defined(__x86_64__) || defined(__INTEL_COMPILER)

#define MAGIC(n) do {                           \
	__MAGIC_CASSERT(!(n));                  \
        __asm__ __volatile__ ("xchg %bx,%bx");  \
} while (0)

#define MAGIC_BREAKPOINT MAGIC(0)

#elif defined(__ia64)

#define MAGIC(n) do {                                           \
	__MAGIC_CASSERT((n) >= 0 && (n) < 0x100000);            \
        __asm__ __volatile__ ("nop (0x100000 + " #n ");;");     \
} while (0)

#define MAGIC_BREAKPOINT MAGIC(0x40000)

#elif defined(__powerpc__)

/* or rN,rN,rN can't be used as a magic instruction on 64-bit PowerPC
   since it is used for thread control on HMT/SMT hardware.
   Conversely, fmr fN,fN can't be used on PowerPC implementations without
   fp registers. */
#if defined(__powerpc64__)

#define MAGIC(n) do {                                   \
	__MAGIC_CASSERT((n) >= 0 && (n) < 32);           \
        __asm__ __volatile__ ("fmr " #n ", " #n);        \
} while (0)

#else  /* not __powerpc64__ */

#define MAGIC(n) do {                                   \
	__MAGIC_CASSERT((n) >= 0 && (n) < 32);          \
        __asm__ __volatile__ ("mr " #n ", " #n);        \
} while (0)

#endif /* not __powerpc64__ */

#define MAGIC_BREAKPOINT MAGIC(0)

#elif defined(__arm__)

#define MAGIC(n) do {                                   \
        __MAGIC_CASSERT((n) == 0);                      \
        __asm__ __volatile__ ("orreq r0, r0, r0");      \
} while (0)

#define MAGIC_BREAKPOINT MAGIC(0)

#elif defined(__mips__)

#define MAGIC(n) do {                                   \
	__MAGIC_CASSERT((n) >= 0 && (n) <= 0xffff);     \
        /* GAS refuses to do 'li $zero,n' */            \
        __asm__ __volatile__ (".word 0x24000000+" #n);	\
} while (0)

#define MAGIC_BREAKPOINT MAGIC(0)

#elif defined __MSP430__

#define MAGIC(n) do {                           \
	__MAGIC_CASSERT(!(n));                  \
        __asm__ __volatile__ ("bis %pc,%pc");  \
} while (0)

#define MAGIC_BREAKPOINT MAGIC(0)

#else  /* !__sparc && !__i386 && !__powerpc__ */
#error "Unsupported architecture"
#endif /* !__sparc && !__i386 && !__powerpc__ */

#elif defined(__SUNPRO_C) || defined(__SUNPRO_CC)

#if defined(__sparc)

#define MAGIC(n) do {                                   \
	__MAGIC_CASSERT((n) > 0 && (n) < (1U << 22));   \
        asm ("sethi " #n ", %g0");                      \
} while (0)

#define MAGIC_BREAKPOINT MAGIC(0x40000)

#else  /* !__sparc */
#error "Unsupported architecture"
#endif /* !__sparc */

#elif defined(__DECC)

#if defined(__alpha)

#define MAGIC(n) do {                           \
	__MAGIC_CASSERT(!(n));                  \
        asm (".long 0x70000000");               \
} while (0)

#else  /* !__alpha */
#error "Unsupported architecture"
#endif /* !__alpha */

#else  /* !__GNUC__ && !__SUNPRO_C && !__SUNPRO_CC && !__DECC */

#ifdef _MSC_VER
#define MAGIC(n)
#define MAGIC_BREAKPOINT
#pragma message("MAGIC() macro needs attention!")
#else
#error "Unsupported compiler"
#endif

#endif /* !__GNUC__ && !__SUNPRO_C && !__SUNPRO_CC && !__DECC  */

#endif /* _SIMICS_MAGIC_INSTRUCTION_H */
