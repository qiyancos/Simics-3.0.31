/*
 * simics/util/bitcount.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_BITCOUNT_H
#define _SIMICS_UTIL_BITCOUNT_H

/*
 * Following macros are defined here:
 * COUNT_LEADING_ZEROS{32,64}(x)  -- count leading zeros in 32/64-bit word;
 *                                   return 32/64 if value is zero
 * COUNT_TRAILING_ZEROS{32,64}(x) -- count trailing zeros in 32/64-bit word;
 *                                   return 32/64 if value is zero
 * LOG2(x), LOG2_64(x)            -- floor(log2(x)); returns -1 for x=0
 *
 * All the above macros can be used on constants, and will then yield
 * constant expressions.
 */

#undef CONSTANT_P
#if defined(__GNUC__)
 #define CONSTANT_P(x) (__extension__ (__builtin_constant_p(x)))
#else
 #define CONSTANT_P(x) 0
#endif

#undef IS_POWER_OF_2
#define IS_POWER_OF_2(n) ((n) && !((n) & ((n) - 1)))

#if defined __i386__ && defined __GNUC__

FORCE_INLINE unsigned
host_count_leading_zeros32(uint32 x)
{
        unsigned n;
        __asm__ ("bsrl %1, %0\n"
                 "jne 1f\n"
                 "mov $-1, %0\n"
                 "1:"
                 : "=r" (n)
                 : "r" (x)
                 : "cc");
        return 31 - n;
}

FORCE_INLINE unsigned
host_count_leading_zeros64(uint64 x)
{
        unsigned n;
        __asm__ ("bsrl %%edx, %0\n\t"   /* scan the high word */
                 "jne 1f\n\t"           /* if nonzero, use that */
                 "bsrl %%eax, %0\n\t"   /* scan the low word */
                 "jne 2f\n\t"           /* if nonzero, use that */
                 "movl $-1, %0\n\t"     /* default value (both zero) */
                 "2:\n\t"
                 "sub $32, %0\n\t"      /* compensate for low word */
                 "1:"
                 : "=&r" (n)
                 : "A" (x)
                 : "cc");
        return 31 - n;
}

FORCE_INLINE unsigned
host_count_trailing_zeros32(uint32 x)
{
        unsigned n;
        __asm__ ("bsfl %1, %0\n"
                 "jne 1f\n"
                 "mov $32, %0\n"
                 "1:"
                 : "=r" (n)
                 : "r" (x)
                 : "cc");
        return n;

}

FORCE_INLINE unsigned
host_count_trailing_zeros64(uint64 x)
{
        unsigned n;
        __asm__("bsfl %%eax, %0\n\t"    /* scan the low word */
                "jne 1f\n\t"            /* if nonzero, use that */
                "bsfl %%edx, %0\n\t"    /* scan the high word */
                "jne 2f\n\t"            /* if nonzero, use that */
                "movl $32, %0\n\t"      /* default value (both zero) */
                "2:\n\t"
                "add $32, %0\n\t"       /* compensate for low word */
                "1:"
                : "=&r" (n)
                : "A" (x)
                : "cc");
        return n;
}

#define _COUNT_LEADING_ZEROS32(x) host_count_leading_zeros32(x)
#define _COUNT_LEADING_ZEROS64(x) host_count_leading_zeros64(x)
#define _COUNT_TRAILING_ZEROS32(x) host_count_trailing_zeros32(x)
#define _COUNT_TRAILING_ZEROS64(x) host_count_trailing_zeros64(x)

#elif defined __x86_64__ && defined __GNUC__

FORCE_INLINE unsigned
host_count_leading_zeros32(uint32 x)
{
        unsigned n;
        __asm__ ("bsrl %1, %0\n"
                 "jne 1f\n"
                 "mov $-1, %0\n"
                 "1:"
                 : "=r" (n)
                 : "r" (x)
                 : "cc");
        return 31 - n;
}

FORCE_INLINE unsigned
host_count_leading_zeros64(uint64 x)
{
        uint64 n;
        __asm__ ("bsrq %1, %0\n"
                 "jne 1f\n"
                 "mov $-1, %0\n"
                 "1:"
                 : "=r" (n)
                 : "r" (x)
                 : "cc");
        return 63 - n;
}

FORCE_INLINE unsigned
host_count_trailing_zeros32(uint32 x)
{
        unsigned n;
        __asm__ ("bsfl %1, %0\n"
                 "jne 1f\n"
                 "mov $32, %0\n"
                 "1:"
                 : "=r" (n)
                 : "r" (x)
                 : "cc");
        return n;

}

FORCE_INLINE unsigned
host_count_trailing_zeros64(uint64 x)
{
        uint64 n;
        __asm__ ("bsfq %1, %0\n"
                 "jne 1f\n"
                 "mov $64, %0\n"
                 "1:"
                 : "=r" (n)
                 : "r" (x)
                 : "cc");
        return n;

}

#define _COUNT_LEADING_ZEROS32(x) host_count_leading_zeros32(x)
#define _COUNT_LEADING_ZEROS64(x) host_count_leading_zeros64(x)
#define _COUNT_TRAILING_ZEROS32(x) host_count_trailing_zeros32(x)
#define _COUNT_TRAILING_ZEROS64(x) host_count_trailing_zeros64(x)

#elif defined __powerpc__ && defined __GNUC__

FORCE_INLINE unsigned
host_count_leading_zeros32(uint32 x)
{
        unsigned n;
        __asm__ ("cntlzw %0, %1"
                 : "=r" (n)
                 : "r" (x));
        return n;
}

FORCE_INLINE unsigned
host_count_leading_zeros64(uint64 x)
{
        uint32 hi = x >> 32;
        return (hi
                ? host_count_leading_zeros32(hi)
                : host_count_leading_zeros32((uint32)x) + 32);
}

FORCE_INLINE unsigned
host_count_trailing_zeros32(uint32 x)
{
        return 32 - host_count_leading_zeros32(~x & (x - 1));
}

FORCE_INLINE unsigned
host_count_trailing_zeros64(uint64 x)
{
        uint32 lo = (uint32)x;
        return (lo
                ? host_count_trailing_zeros32(lo)
                : -32 + host_count_trailing_zeros32(x >> 32));
}

#define _COUNT_LEADING_ZEROS32(x) host_count_leading_zeros32(x)
#define _COUNT_LEADING_ZEROS64(x) host_count_leading_zeros64(x)
#define _COUNT_TRAILING_ZEROS32(x) host_count_trailing_zeros32(x)
#define _COUNT_TRAILING_ZEROS64(x) host_count_trailing_zeros64(x)

#else

/* Generic code for hosts without bitcount instructions */

#if defined(CPU_MODULE) && !defined(STANDALONE)

/* Assuming CPU modules are in the need of speed, we let them use
   table-based routines (requiring tables in src/cpu/common/cpu-module.c) */

#define NEED_BITCOUNT_TABLES
extern uint8 leading_zeros8[];
extern uint8 trailing_zeros8[];

FORCE_INLINE unsigned
table_count_leading_zeros32(uint32 x)
{
        unsigned n, y;
        n = 24;
        y = x >> 16; if (y) { n -= 16; x = y; }
        y = x >>  8; if (y) { n -=  8; x = y; }
        return n + leading_zeros8[x];
}

FORCE_INLINE unsigned
table_count_leading_zeros64(uint64 x)
{
        unsigned start = 0;
        if (x >> 32) x >>= 32; else start  = 32;
        if (x >> 16) x >>= 16; else start += 16;
        if (x >>  8) x >>=  8; else start +=  8;
        return start + leading_zeros8[x];
}

FORCE_INLINE unsigned
table_count_trailing_zeros32(uint32 x)
{
        unsigned n = 24;
        uint32 y;
        y = x << 16; if (y) { n -= 16; x = y; }
        y = x <<  8; if (y) { n -=  8; x = y; }
        return n + trailing_zeros8[x >> 24];
}

FORCE_INLINE unsigned
table_count_trailing_zeros64(uint64 x)
{
        unsigned n = 56;
        uint64 y;
        y = x << 32; if (y) { n -= 32; x = y; }
        y = x << 16; if (y) { n -= 16; x = y; }
        y = x <<  8; if (y) { n -=  8; x = y; }
        return n + trailing_zeros8[x >> 56];
}

#define _COUNT_LEADING_ZEROS32(x) table_count_leading_zeros32(x)
#define _COUNT_LEADING_ZEROS64(x) table_count_leading_zeros64(x)
#define _COUNT_TRAILING_ZEROS32(x) table_count_trailing_zeros32(x)
#define _COUNT_TRAILING_ZEROS64(x) table_count_trailing_zeros64(x)

#else  /* not CPU_MODULE or STANDALONE */

FORCE_INLINE unsigned
generic_count_leading_zeros32(uint32 x)
{
        unsigned n, y;
        n = 32;
        y = x >> 16; if (y) { n -= 16; x = y; }
        y = x >>  8; if (y) { n -=  8; x = y; }
        y = x >>  4; if (y) { n -=  4; x = y; }
        y = x >>  2; if (y) { n -=  2; x = y; }
        y = x >>  1; if (y) return n - 2;
        return n - x;
}

FORCE_INLINE unsigned
generic_count_leading_zeros64(uint64 x)
{
        unsigned n, y;
        n = 64;
        y = x >> 32; if (y) { n -= 32; x = y; }
        y = x >> 16; if (y) { n -= 16; x = y; }
        y = x >>  8; if (y) { n -=  8; x = y; }
        y = x >>  4; if (y) { n -=  4; x = y; }
        y = x >>  2; if (y) { n -=  2; x = y; }
        y = x >>  1; if (y) return n - 2;
        return n - x;
}

FORCE_INLINE unsigned
generic_count_trailing_zeros32(uint32 x)
{
        unsigned n;
        if (x == 0)
                return 32;
        n = 1;
        if (!(x & 0x0000ffff)) { n += 16; x >>= 16; }
        if (!(x & 0x000000ff)) { n +=  8; x >>=  8; }
        if (!(x & 0x0000000f)) { n +=  4; x >>=  4; }
        if (!(x & 0x00000003)) { n +=  2; x >>=  2; }
        return n - (x & 1);
}

FORCE_INLINE unsigned
generic_count_trailing_zeros64(uint64 x)
{
        unsigned n;
        if (x == 0)
                return 64;
        n = 1;
        if (!(x & 0x00000000ffffffff)) { n += 32; x >>= 32; }
        if (!(x & 0x000000000000ffff)) { n += 16; x >>= 16; }
        if (!(x & 0x00000000000000ff)) { n +=  8; x >>=  8; }
        if (!(x & 0x000000000000000f)) { n +=  4; x >>=  4; }
        if (!(x & 0x0000000000000003)) { n +=  2; x >>=  2; }
        return n - (x & 1);
}

#define _COUNT_LEADING_ZEROS32(x) generic_count_leading_zeros32(x)
#define _COUNT_LEADING_ZEROS64(x) generic_count_leading_zeros64(x)
#define _COUNT_TRAILING_ZEROS32(x) generic_count_trailing_zeros32(x)
#define _COUNT_TRAILING_ZEROS64(x) generic_count_trailing_zeros64(x)

#endif /* not CPU_MODULE or STANDALONE */

#endif /* generic code */

/* macro for constant expressions */
#define COUNT_LEADING_ZEROS16_CONST(x)          \
    ((x) >= 1u << 8                             \
     ? ((x) >= 1u << 12                         \
        ? ((x) >= 1u << 14                      \
           ? ((x) >= 1u << 15                   \
              ? 0                               \
              : 1)                              \
           : ((x) >= 1u << 13                   \
              ? 2                               \
              : 3))                             \
        : ((x) >= 1u << 10                      \
           ? ((x) >= 1u << 11                   \
              ? 4                               \
              : 5)                              \
           : ((x) >= 1u << 9                    \
              ? 6                               \
              : 7)))                            \
     : ((x) >= 1u << 4                          \
        ? ((x) >= 1u << 6                       \
           ? ((x) >= 1u << 7                    \
              ? 8                               \
              : 9)                              \
           : ((x) >= 1u << 5                    \
              ? 10                              \
              : 11))                            \
        : ((x) >= 1u << 2                       \
           ? ((x) >= 1u << 3                    \
              ? 12                              \
              : 13)                             \
           : ((x) >= 1u << 1                    \
              ? 14                              \
              : ((x) >= 1u << 0                 \
                 ? 15                           \
                 : 16)))))

#define COUNT_LEADING_ZEROS32_CONST(x)                  \
    ((uint32)(x) >= 1u << 16                            \
     ? COUNT_LEADING_ZEROS16_CONST((uint32)(x) >> 16)   \
     : COUNT_LEADING_ZEROS16_CONST((uint16)(x)) + 16)

#define COUNT_LEADING_ZEROS64_CONST(x)                  \
    ((uint64)(x) >= (uint64)1 << 32                     \
     ? COUNT_LEADING_ZEROS32_CONST((uint64)(x) >> 32)   \
     : COUNT_LEADING_ZEROS32_CONST((uint32)(x)) + 32)

#define COUNT_TRAILING_ZEROS32_CONST(x)                                  \
    (32 - COUNT_LEADING_ZEROS32_CONST(~(uint32)(x) & ((uint32)(x) - 1)))

#define COUNT_TRAILING_ZEROS64_CONST(x)                                 \
    (64 - COUNT_LEADING_ZEROS64(~(uint64)(x) & ((uint64)(x) - 1)))

#define COUNT_LEADING_ZEROS32(x)                \
    (CONSTANT_P(x)                              \
     ? COUNT_LEADING_ZEROS32_CONST(x)           \
     : _COUNT_LEADING_ZEROS32(x))
#define COUNT_LEADING_ZEROS64(x)                \
    (CONSTANT_P(x)                              \
     ? COUNT_LEADING_ZEROS64_CONST(x)           \
     : _COUNT_LEADING_ZEROS64(x))
#define COUNT_TRAILING_ZEROS32(x)               \
    (CONSTANT_P(x)                              \
     ? COUNT_TRAILING_ZEROS32_CONST(x)          \
     : _COUNT_TRAILING_ZEROS32(x))
#define COUNT_TRAILING_ZEROS64(x)               \
    (CONSTANT_P(x)                              \
     ? COUNT_TRAILING_ZEROS64_CONST(x)          \
     : _COUNT_TRAILING_ZEROS64(x))

#define LOG2(x) (31 - COUNT_LEADING_ZEROS32(x))
#define LOG2_64(x) (63 - COUNT_LEADING_ZEROS64(x))

#endif /* _SIMICS_UTIL_BITCOUNT_H */
