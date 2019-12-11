/*
 * simics/util/swabber.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_SWABBER_H
#define _SIMICS_UTIL_SWABBER_H

/*
 * Here we define the following macros:
 *
 * Target-dependent:
 *
 * TARGET_ENDIAN{8,16,32,64}(x)		- convert to/from target byte order
 * LOAD_TARGET{8,16,32,64}(p)		- load using target byte order
 * STORE_TARGET{8,16,32,64}(p, x)	- store using target byte order
 * UNALIGNED_LOAD_TARGET{8,16,32,64}(p)	- unaligned load in target order
 * UNALIGNED_STORE_TARGET{8,16,32,64}(p,x) - unaligned store in target order
 * LOAD_CROSS{8,16,32,64}(p)		- load in anti-target order
 * UNALIGNED_LOAD_CROSS{8,16,32,64}(p)	- unaligned load in anti-target order
 * STORE_CROSS{8,16,32,64}(p)		- store in anti-target order
 *
 * Endian-dependent:
 *
 * CONVERT_{LE,BE}{8,16,32,64}(x)		- convert to/from endianness
 * LOAD_{LE,BE}{8,16,32,64}(p)			- little/big-endian load
 * STORE_{LE,BE}{8,16,32,64}(p, x)		- little/big-endian store
 * UNALIGNED_LOAD_{LE,BE}{8,16,32,64}(p)	- unaligned load
 * UNALIGNED_STORE_{LE,BE}{8,16,32,64}(p, x)	- unaligned store
 *
 * Low-level:
 *
 * SWAB{8,16,32,64}(x)				- byte swapping
 * LOADSWAB{8,16,32,64}(p)			- byte-swapping load
 * STORESWAB{8,16,32,64}(p, x)			- byte-swapping store
 * UNALIGNED_LOAD{8,16,32,64}(p)		- unaligned load
 * UNALIGNED_STORE{8,16,32,64}(p, x)		- unaligned store
 * UNALIGNED_LOADSWAB{8,16,32,64}(p)		- byte-swapping unaligned load
 * UNALIGNED_STORESWAB{8,16,32,64}(p, x)	- byte-swapping unaligned store
 *
 * NOTE: It is generally better to use the load/store versions of the
 * byte-swapping macros rather than the value-converting macros, since the
 * former can be optimised on more platforms
 */

/*
 * Host architecture dependent definitions:
 * Each may define any of the following:
 *
 * SWAB{16,32,64}(x)
 * LOADSWAB{16,32,64}(p)
 * STORESWAB{16,32,64}(p, x)
 * UNALIGNED_LOAD{16,32,64}(p)
 * UNALIGNED_STORE{16,32,64}(p, x)
 * UNALIGNED_LOADSWAB{16,32,64}(p)
 * UNALIGNED_STORESWAB{16,32,64}(p)
 *
 * Any missing defs are filled in with generic implementations.
 */

#if defined(__sparc) || defined(__sparcv8) || defined(__sparcv9)
 #define SWABBER_HOST_SPARC
 #define SWABBER_HOST_BIG_ENDIAN
#elif defined(__i386__) || defined(_M_IX86)
 #define SWABBER_HOST_X86
 #define HOST_ALLOWS_UNALIGNED_ACCESSES 1
#elif defined(__powerpc__)
 #define SWABBER_HOST_PPC
 #define SWABBER_HOST_BIG_ENDIAN
 #define HOST_ALLOWS_UNALIGNED_ACCESSES 1
#elif defined(__x86_64__) || defined(_M_AMD64)
 #define SWABBER_HOST_AMD64
 #define HOST_ALLOWS_UNALIGNED_ACCESSES 1
#endif

#if !defined HOST_ALLOWS_UNALIGNED_ACCESSES
 #define HOST_ALLOWS_UNALIGNED_ACCESSES 0
#endif

#if defined __GNUC__ \
    && (defined SWABBER_HOST_X86 || defined SWABBER_HOST_AMD64)

/* Let gcc handle the 16-bit case - it's likely to do well enough, and will
   schedule better */

FORCE_INLINE uint32
swab32(uint32 x)
{
	__asm__ ("bswapl %0" : "=r" (x) : "0" (x));
	return x;
}

FORCE_INLINE uint64
swab64(uint64 x)
{
#if defined SWABBER_HOST_AMD64
        __asm__ ("bswapq %0" : "=r" (x) : "0" (x));
#else
        __asm__ ("xchg %%edx,%%eax\n"
                 "bswap %%edx\n"
                 "bswap %%eax\n" : "=A" (x) : "0" (x));
#endif
    return x;
}

#define SWAB32(x) swab32(x)
#define SWAB64(x) swab64(x)

#define UNALIGNED_LOADSWAB16(p) SWAB16(UNALIGNED_LOAD16(p))
#define UNALIGNED_LOADSWAB32(p) SWAB32(UNALIGNED_LOAD32(p))
#define UNALIGNED_LOADSWAB64(p) SWAB64(UNALIGNED_LOAD64(p))

#define UNALIGNED_STORESWAB16(p, x) UNALIGNED_STORE16(p, SWAB16(x))
#define UNALIGNED_STORESWAB32(p, x) UNALIGNED_STORE32(p, SWAB32(x))
#define UNALIGNED_STORESWAB64(p, x) UNALIGNED_STORE64(p, SWAB64(x))

#endif /* __GNUC__ and (SWABBER_HOST_X86 or SWABBER_HOST_AMD64) */

#if defined SWABBER_HOST_SPARC

#if (defined __SUNPRO_C || defined __SUNPRO_CC) && defined HAVE_SWABBER_IL

uint16 loadswab16(const uint16 *p);
uint32 loadswab32(const uint32 *p);
void storeswab16(uint16 *p, uint16 x);
void storeswab32(uint32 *p, uint32 x);

#ifdef __sparcv9
uint64 loadswab64(const uint64 *p);
void storeswab64(uint64 *p, uint64 x);
#endif /* __sparcv9 */

#elif defined(__GNUC__)

#ifndef ASI_PL
#define ASI_PL 0x88		/* primary little-endian */
#endif

FORCE_INLINE uint16
loadswab16(const uint16 *p)
{
	uint16 ret;
	__asm__ __volatile__("lduha [%1] %2, %0"
			     : "=r" (ret)
			     : "r" (p), "i" (ASI_PL));
	return ret;
}

FORCE_INLINE uint32
loadswab32(const uint32 *p)
{
	uint32 ret;
	__asm__ __volatile__("lduwa [%1] %2, %0"
			     : "=r" (ret)
			     : "r" (p), "i" (ASI_PL));
	return ret;
}

FORCE_INLINE void
storeswab16(uint16 *p, uint16 x)
{
	__asm__ __volatile__("stha %1, [%2] %3"
			     : "=m" (*p)
			     : "r" (x), "r" (p), "i" (ASI_PL));
}

FORCE_INLINE void
storeswab32(uint32 *p, uint32 x)
{
	__asm__ __volatile__("stwa %1, [%2] %3"
			     : "=m" (*p)
			     : "r" (x), "r" (p), "i" (ASI_PL));
}

#ifdef __sparcv9
FORCE_INLINE uint64
loadswab64(const uint64 *p)
{
	uint64 ret;
	__asm__ __volatile__("ldxa [%1] %2, %0"
			     : "=r" (ret)
			     : "r" (p), "i" (ASI_PL));
	return ret;
}

FORCE_INLINE void
storeswab64(uint64 *p, uint64 x)
{
	__asm__ __volatile__("stxa %1, [%2] %3"
			     : "=m" (*p)
			     : "r" (x), "r" (p), "i" (ASI_PL));
}
#endif /* __sparcv9 */

#endif /* __GNUC__ */

#ifndef __sparcv9
FORCE_INLINE uint64
loadswab64(const uint64 *p)
{
        const uint32 *q = (const uint32 *)p;
        return (uint64)loadswab32(q)
               | (uint64)loadswab32(q + 1) << 32;
}

FORCE_INLINE void
storeswab64(uint64 *p, uint64 x)
{
        uint32 *q = (uint32 *)p;
        storeswab32((uint32 *)p, x);
        storeswab32((uint32 *)p + 1, x >> 32);
}
#endif

#define LOADSWAB16(p) loadswab16(p)
#define LOADSWAB32(p) loadswab32(p)
#define LOADSWAB64(p) loadswab64(p)

#define STORESWAB16(p, x) storeswab16(p, x)
#define STORESWAB32(p, x) storeswab32(p, x)
#define STORESWAB64(p, x) storeswab64(p, x)

#endif /* SWABBER_HOST_SPARC */

#if defined(SWABBER_HOST_PPC) && defined(__GNUC__)

/* FIXME: add SWAB16 and SWAB32, using rlwimi */

FORCE_INLINE uint16
loadswab16(const uint16 *p)
{
	uint16 ret;
	__asm__ ("lhbrx %0, 0, %1"
		 : "=r" (ret)
		 : "r" (p), "m" (*p));
	return ret;
}

FORCE_INLINE uint32
loadswab32(const uint32 *p)
{
	uint32 ret;
	__asm__ ("lwbrx %0, 0, %1"
		 : "=r" (ret)
		 : "r" (p), "m" (*p));
	return ret;
}

FORCE_INLINE void
storeswab16(uint16 *p, uint16 x)
{
	__asm__ ("sthbrx %1, 0, %2"
		 : "=m" (*p)
		 : "r" (x), "r" (p));
}

FORCE_INLINE void
storeswab32(uint32 *p, uint32 x)
{
	__asm__ ("stwbrx %1, 0, %2"
		 : "=m" (*p)
		 : "r" (x), "r" (p));
}

FORCE_INLINE uint64
loadswab64(const uint64 *p)
{
        return (uint64)loadswab32((const uint32 *)p)
               | (uint64)loadswab32((const uint32 *)p + 1) << 32;
}

FORCE_INLINE void
storeswab64(uint64 *p, uint64 x)
{
        storeswab32((uint32 *)p, x);
        storeswab32((uint32 *)p + 1, x >> 32);
}

#define LOADSWAB16(p) loadswab16(p)
#define LOADSWAB32(p) loadswab32(p)
#define LOADSWAB64(p) loadswab64(p)

#define STORESWAB16(p, x) storeswab16(p, x)
#define STORESWAB32(p, x) storeswab32(p, x)
#define STORESWAB64(p, x) storeswab64(p, x)

/* PPC supports unaligned access without trapping (usually) */

#define UNALIGNED_LOADSWAB16(p) loadswab16((uint16 *)(p))
#define UNALIGNED_LOADSWAB32(p) loadswab32((uint32 *)(p))
#define UNALIGNED_LOADSWAB64(p) loadswab64((uint64 *)(p))

#define UNALIGNED_STORESWAB16(p, x) storeswab16((uint16 *)(p), x)
#define UNALIGNED_STORESWAB32(p, x) storeswab32((uint32 *)(p), x)
#define UNALIGNED_STORESWAB64(p, x) storeswab64((uint64 *)(p), x)

#endif /* SWABBER_HOST_PPC and __GNUC__ */

/* End of architecture-dependent defs */

FORCE_INLINE uint16
generic_swab16(uint16 x)
{
        return ((x << 8) & 0xff00) | ((x >> 8) & 0xff);
}

FORCE_INLINE uint32
generic_swab32(uint32 x)
{
        return (x & 0xff) << 24 | (x & 0xff00) << 8
               | (x & 0xff0000) >> 8 | (x & 0xff000000) >> 24;
}

FORCE_INLINE uint64
generic_swab64(uint64 x)
{
        return (uint64)generic_swab32(x) << 32 | generic_swab32(x >> 32);
}

#ifndef SWAB16
 #define SWAB16(x) generic_swab16(x)
#endif
#ifndef SWAB32
 #define SWAB32(x) generic_swab32(x)
#endif
#ifndef SWAB64
 #define SWAB64(x) generic_swab64(x)
#endif

FORCE_INLINE uint16 generic_loadswab16(const uint16 *p) { return SWAB16(*p); }
FORCE_INLINE uint32 generic_loadswab32(const uint32 *p) { return SWAB32(*p); }
FORCE_INLINE uint64 generic_loadswab64(const uint64 *p) { return SWAB64(*p); }

FORCE_INLINE void generic_storeswab16(uint16 *p, uint16 x) { *p = SWAB16(x); }
FORCE_INLINE void generic_storeswab32(uint32 *p, uint32 x) { *p = SWAB32(x); }
FORCE_INLINE void generic_storeswab64(uint64 *p, uint64 x) { *p = SWAB64(x); }

FORCE_INLINE uint16 straight_load16(const uint16 *p) { return *p; }
FORCE_INLINE uint32 straight_load32(const uint32 *p) { return *p; }
FORCE_INLINE uint64 straight_load64(const uint64 *p) { return *p; }

FORCE_INLINE void straight_store16(uint16 *p, uint16 x) { *p = x; }
FORCE_INLINE void straight_store32(uint32 *p, uint32 x) { *p = x; }
FORCE_INLINE void straight_store64(uint64 *p, uint64 x) { *p = x; }

FORCE_INLINE uint16 identity16(uint16 x) { return x; }
FORCE_INLINE uint32 identity32(uint32 x) { return x; }
FORCE_INLINE uint64 identity64(uint64 x) { return x; }

#if HOST_ALLOWS_UNALIGNED_ACCESSES
FORCE_INLINE uint16 unaligned_load16(const void *p) {
        return *(const uint16 *)p; }
FORCE_INLINE uint32 unaligned_load32(const void *p) {
        return *(const uint32 *)p; }
FORCE_INLINE uint64 unaligned_load64(const void *p) {
        return *(const uint64 *)p; }

FORCE_INLINE void unaligned_store16(void *p, uint16 x) { *(uint16 *)p = x; }
FORCE_INLINE void unaligned_store32(void *p, uint32 x) { *(uint32 *)p = x; }
FORCE_INLINE void unaligned_store64(void *p, uint64 x) { *(uint64 *)p = x; }

#define UNALIGNED_LOAD16(p) unaligned_load16(p)
#define UNALIGNED_LOAD32(p) unaligned_load32(p)
#define UNALIGNED_LOAD64(p) unaligned_load64(p)

#define UNALIGNED_STORE16(p, x) unaligned_store16(p, x)
#define UNALIGNED_STORE32(p, x) unaligned_store32(p, x)
#define UNALIGNED_STORE64(p, x) unaligned_store64(p, x)
#endif

/*
 * FIXME: should the unaligned loads be coded as two consecutive
 * loads followed by shifts/masks? What about stores?
 */

FORCE_INLINE uint16
generic_unaligned_load_le16(const void *p)
{
        const uint8 *q = (const uint8 *)p;
	return q[0] | q[1] << 8;
}

FORCE_INLINE uint16
generic_unaligned_load_be16(const void *p)
{
        const uint8 *q = (const uint8 *)p;
	return q[0] << 8 | q[1];
}

FORCE_INLINE uint32
generic_unaligned_load_le32(const void *p)
{
        const uint8 *q = (const uint8 *)p;
	return q[0] | q[1] << 8 | q[2] << 16 | q[3] << 24;
}

FORCE_INLINE uint32
generic_unaligned_load_be32(const void *p)
{
        const uint8 *q = (const uint8 *)p;
	return q[0] << 24 | q[1] << 16 | q[2] << 8 | q[3];
}

FORCE_INLINE uint64
generic_unaligned_load_le64(const void *p)
{
        const uint8 *q = (const uint8 *)p;
	return (uint64)generic_unaligned_load_le32(q)
               | (uint64)generic_unaligned_load_le32(q + 4) << 32;
}

FORCE_INLINE uint64
generic_unaligned_load_be64(const void *p)
{
        const uint8 *q = (const uint8 *)p;
	return (uint64)generic_unaligned_load_be32(q) << 32
               | (uint64)generic_unaligned_load_be32(q + 4);
}

FORCE_INLINE void
generic_unaligned_store_le16(void *p, uint16 x)
{
        uint8 *q = (uint8 *)p;
        q[0] = x;
        q[1] = x >> 8;
}

FORCE_INLINE void
generic_unaligned_store_be16(void *p, uint16 x)
{
        uint8 *q = (uint8 *)p;
        q[0] = x >> 8;
        q[1] = x;
}

FORCE_INLINE void
generic_unaligned_store_le32(void *p, uint32 x)
{
        uint8 *q = (uint8 *)p;
        q[0] = x;
        q[1] = x >> 8;
        q[2] = x >> 16;
        q[3] = x >> 24;
}

FORCE_INLINE void
generic_unaligned_store_be32(void *p, uint32 x)
{
        uint8 *q = (uint8 *)p;
        q[0] = x >> 24;
        q[1] = x >> 16;
        q[2] = x >> 8;
        q[3] = x;
}

FORCE_INLINE void
generic_unaligned_store_le64(void *p, uint64 x)
{
        uint8 *q = (uint8 *)p;
        generic_unaligned_store_le32(q, x);
        generic_unaligned_store_le32(q + 4, x >> 32);
}

FORCE_INLINE void
generic_unaligned_store_be64(void *p, uint64 x)
{
        uint8 *q = (uint8 *)p;
        generic_unaligned_store_be32(q, x >> 32);
        generic_unaligned_store_be32(q + 4, x);
}

#ifndef LOADSWAB16
 #define LOADSWAB16(p) generic_loadswab16(p)
#endif
#ifndef LOADSWAB32
 #define LOADSWAB32(p) generic_loadswab32(p)
#endif
#ifndef LOADSWAB64
 #define LOADSWAB64(p) generic_loadswab64(p)
#endif

#ifndef STORESWAB16
 #define STORESWAB16(p, x) generic_storeswab16(p, x)
#endif
#ifndef STORESWAB32
 #define STORESWAB32(p, x) generic_storeswab32(p, x)
#endif
#ifndef STORESWAB64
 #define STORESWAB64(p, x) generic_storeswab64(p, x)
#endif

#if defined(SWABBER_HOST_BIG_ENDIAN)
 #ifndef UNALIGNED_LOAD16
  #define UNALIGNED_LOAD16(p) generic_unaligned_load_be16(p)
 #endif
 #ifndef UNALIGNED_LOAD32
  #define UNALIGNED_LOAD32(p) generic_unaligned_load_be32(p)
 #endif
 #ifndef UNALIGNED_LOAD64
  #define UNALIGNED_LOAD64(p) generic_unaligned_load_be64(p)
 #endif

 #ifndef UNALIGNED_STORE16
  #define UNALIGNED_STORE16(p, x) generic_unaligned_store_be16(p, x)
 #endif
 #ifndef UNALIGNED_STORE32
  #define UNALIGNED_STORE32(p, x) generic_unaligned_store_be32(p, x)
 #endif
 #ifndef UNALIGNED_STORE64
  #define UNALIGNED_STORE64(p, x) generic_unaligned_store_be64(p, x)
 #endif

 #ifndef UNALIGNED_LOADSWAB16
  #define UNALIGNED_LOADSWAB16(p) generic_unaligned_load_le16(p)
 #endif
 #ifndef UNALIGNED_LOADSWAB32
  #define UNALIGNED_LOADSWAB32(p) generic_unaligned_load_le32(p)
 #endif
 #ifndef UNALIGNED_LOADSWAB64
  #define UNALIGNED_LOADSWAB64(p) generic_unaligned_load_le64(p)
 #endif

 #ifndef UNALIGNED_STORESWAB16
  #define UNALIGNED_STORESWAB16(p, x) generic_unaligned_store_le16(p, x)
 #endif
 #ifndef UNALIGNED_STORESWAB32
  #define UNALIGNED_STORESWAB32(p, x) generic_unaligned_store_le32(p, x)
 #endif
 #ifndef UNALIGNED_STORESWAB64
  #define UNALIGNED_STORESWAB64(p, x) generic_unaligned_store_le64(p, x)
 #endif

 #define LOAD_BE16(p) straight_load16(p)
 #define LOAD_LE16(p) LOADSWAB16(p)
 #define LOAD_BE32(p) straight_load32(p)
 #define LOAD_LE32(p) LOADSWAB32(p)
 #define LOAD_BE64(p) straight_load64(p)
 #define LOAD_LE64(p) LOADSWAB64(p)

 #define STORE_BE16(p, x) straight_store16(p, x)
 #define STORE_LE16(p, x) STORESWAB16(p, x)
 #define STORE_BE32(p, x) straight_store32(p, x)
 #define STORE_LE32(p, x) STORESWAB32(p, x)
 #define STORE_BE64(p, x) straight_store64(p, x)
 #define STORE_LE64(p, x) STORESWAB64(p, x)

 #define UNALIGNED_LOAD_BE16(p) UNALIGNED_LOAD16(p)
 #define UNALIGNED_LOAD_LE16(p) UNALIGNED_LOADSWAB16(p)
 #define UNALIGNED_LOAD_BE32(p) UNALIGNED_LOAD32(p)
 #define UNALIGNED_LOAD_LE32(p) UNALIGNED_LOADSWAB32(p)
 #define UNALIGNED_LOAD_BE64(p) UNALIGNED_LOAD64(p)
 #define UNALIGNED_LOAD_LE64(p) UNALIGNED_LOADSWAB64(p)

 #define UNALIGNED_STORE_BE16(p, x) UNALIGNED_STORE16(p, x)
 #define UNALIGNED_STORE_LE16(p, x) UNALIGNED_STORESWAB16(p, x)
 #define UNALIGNED_STORE_BE32(p, x) UNALIGNED_STORE32(p, x)
 #define UNALIGNED_STORE_LE32(p, x) UNALIGNED_STORESWAB32(p, x)
 #define UNALIGNED_STORE_BE64(p, x) UNALIGNED_STORE64(p, x)
 #define UNALIGNED_STORE_LE64(p, x) UNALIGNED_STORESWAB64(p, x)

 #define CONVERT_BE16(x) identity16(x)
 #define CONVERT_BE32(x) identity32(x)
 #define CONVERT_BE64(x) identity64(x)

 #define CONVERT_LE16(x) SWAB16(x)
 #define CONVERT_LE32(x) SWAB32(x)
 #define CONVERT_LE64(x) SWAB64(x)
#else
 #ifndef UNALIGNED_LOAD16
  #define UNALIGNED_LOAD16(p) generic_unaligned_load_le16(p)
 #endif
 #ifndef UNALIGNED_LOAD32
  #define UNALIGNED_LOAD32(p) generic_unaligned_load_le32(p)
 #endif
 #ifndef UNALIGNED_LOAD64
  #define UNALIGNED_LOAD64(p) generic_unaligned_load_le64(p)
 #endif

 #ifndef UNALIGNED_STORE16
  #define UNALIGNED_STORE16(p, x) generic_unaligned_store_le16(p, x)
 #endif
 #ifndef UNALIGNED_STORE32
  #define UNALIGNED_STORE32(p, x) generic_unaligned_store_le32(p, x)
 #endif
 #ifndef UNALIGNED_STORE64
  #define UNALIGNED_STORE64(p, x) generic_unaligned_store_le64(p, x)
 #endif

 #ifndef UNALIGNED_LOADSWAB16
  #define UNALIGNED_LOADSWAB16(p) generic_unaligned_load_be16(p)
 #endif
 #ifndef UNALIGNED_LOADSWAB32
  #define UNALIGNED_LOADSWAB32(p) generic_unaligned_load_be32(p)
 #endif
 #ifndef UNALIGNED_LOADSWAB64
  #define UNALIGNED_LOADSWAB64(p) generic_unaligned_load_be64(p)
 #endif

 #ifndef UNALIGNED_STORESWAB16
  #define UNALIGNED_STORESWAB16(p, x) generic_unaligned_store_be16(p, x)
 #endif
 #ifndef UNALIGNED_STORESWAB32
  #define UNALIGNED_STORESWAB32(p, x) generic_unaligned_store_be32(p, x)
 #endif
 #ifndef UNALIGNED_STORESWAB64
  #define UNALIGNED_STORESWAB64(p, x) generic_unaligned_store_be64(p, x)
 #endif

 #define LOAD_LE16(p) straight_load16(p)
 #define LOAD_BE16(p) LOADSWAB16(p)
 #define LOAD_LE32(p) straight_load32(p)
 #define LOAD_BE32(p) LOADSWAB32(p)
 #define LOAD_LE64(p) straight_load64(p)
 #define LOAD_BE64(p) LOADSWAB64(p)

 #define STORE_LE16(p, x) straight_store16(p, x)
 #define STORE_BE16(p, x) STORESWAB16(p, x)
 #define STORE_LE32(p, x) straight_store32(p, x)
 #define STORE_BE32(p, x) STORESWAB32(p, x)
 #define STORE_LE64(p, x) straight_store64(p, x)
 #define STORE_BE64(p, x) STORESWAB64(p, x)

 #define UNALIGNED_LOAD_LE16(p) UNALIGNED_LOAD16(p)
 #define UNALIGNED_LOAD_BE16(p) UNALIGNED_LOADSWAB16(p)
 #define UNALIGNED_LOAD_LE32(p) UNALIGNED_LOAD32(p)
 #define UNALIGNED_LOAD_BE32(p) UNALIGNED_LOADSWAB32(p)
 #define UNALIGNED_LOAD_LE64(p) UNALIGNED_LOAD64(p)
 #define UNALIGNED_LOAD_BE64(p) UNALIGNED_LOADSWAB64(p)

 #define UNALIGNED_STORE_LE16(p, x) UNALIGNED_STORE16(p, x)
 #define UNALIGNED_STORE_BE16(p, x) UNALIGNED_STORESWAB16(p, x)
 #define UNALIGNED_STORE_LE32(p, x) UNALIGNED_STORE32(p, x)
 #define UNALIGNED_STORE_BE32(p, x) UNALIGNED_STORESWAB32(p, x)
 #define UNALIGNED_STORE_LE64(p, x) UNALIGNED_STORE64(p, x)
 #define UNALIGNED_STORE_BE64(p, x) UNALIGNED_STORESWAB64(p, x)

 #define CONVERT_LE16(x) identity16(x)
 #define CONVERT_LE32(x) identity32(x)
 #define CONVERT_LE64(x) identity64(x)

 #define CONVERT_BE16(x) SWAB16(x)
 #define CONVERT_BE32(x) SWAB32(x)
 #define CONVERT_BE64(x) SWAB64(x)
#endif

#ifdef CROSS_ENDIAN

 #define TARGET_ENDIAN16(x) SWAB16(x)
 #define TARGET_ENDIAN32(x) SWAB32(x)
 #define TARGET_ENDIAN64(x) SWAB64(x)

 #define LOAD_TARGET16(p) LOADSWAB16(p)
 #define LOAD_TARGET32(p) LOADSWAB32(p)
 #define LOAD_TARGET64(p) LOADSWAB64(p)

 #define STORE_TARGET16(p, x) STORESWAB16(p, x)
 #define STORE_TARGET32(p, x) STORESWAB32(p, x)
 #define STORE_TARGET64(p, x) STORESWAB64(p, x)

 #define UNALIGNED_LOAD_TARGET16(p) UNALIGNED_LOADSWAB16(p)
 #define UNALIGNED_LOAD_TARGET32(p) UNALIGNED_LOADSWAB32(p)
 #define UNALIGNED_LOAD_TARGET64(p) UNALIGNED_LOADSWAB64(p)

 #define UNALIGNED_STORE_TARGET16(p, x) UNALIGNED_STORESWAB16(p, x)
 #define UNALIGNED_STORE_TARGET32(p, x) UNALIGNED_STORESWAB32(p, x)
 #define UNALIGNED_STORE_TARGET64(p, x) UNALIGNED_STORESWAB64(p, x)

 /* cross-endian loads */
 #define LOAD_CROSS16(p) straight_load16(p)
 #define LOAD_CROSS32(p) straight_load32(p)
 #define LOAD_CROSS64(p) straight_load64(p)

 #define STORE_CROSS16(p, x) straight_store16(p, x)
 #define STORE_CROSS32(p, x) straight_store32(p, x)
 #define STORE_CROSS64(p, x) straight_store64(p, x)

 #define UNALIGNED_LOAD_CROSS16(p) UNALIGNED_LOAD16(p)
 #define UNALIGNED_LOAD_CROSS32(p) UNALIGNED_LOAD32(p)
 #define UNALIGNED_LOAD_CROSS64(p) UNALIGNED_LOAD64(p)

#else  /* not CROSS_ENDIAN */

 #define TARGET_ENDIAN16(x) identity16(x)
 #define TARGET_ENDIAN32(x) identity32(x)
 #define TARGET_ENDIAN64(x) identity64(x)

 #define LOAD_TARGET16(p) straight_load16(p)
 #define LOAD_TARGET32(p) straight_load32(p)
 #define LOAD_TARGET64(p) straight_load64(p)

 #define STORE_TARGET16(p, x) straight_store16(p, x)
 #define STORE_TARGET32(p, x) straight_store32(p, x)
 #define STORE_TARGET64(p, x) straight_store64(p, x)

 #define UNALIGNED_LOAD_TARGET16(p) UNALIGNED_LOAD16(p)
 #define UNALIGNED_LOAD_TARGET32(p) UNALIGNED_LOAD32(p)
 #define UNALIGNED_LOAD_TARGET64(p) UNALIGNED_LOAD64(p)

 #define UNALIGNED_STORE_TARGET16(p, x) UNALIGNED_STORE16(p, x)
 #define UNALIGNED_STORE_TARGET32(p, x) UNALIGNED_STORE32(p, x)
 #define UNALIGNED_STORE_TARGET64(p, x) UNALIGNED_STORE64(p, x)

 /* cross-endian loads */
 #define LOAD_CROSS16(p) LOADSWAB16(p)
 #define LOAD_CROSS32(p) LOADSWAB32(p)
 #define LOAD_CROSS64(p) LOADSWAB64(p)

 #define STORE_CROSS16(p, x) STORESWAB16(p, x)
 #define STORE_CROSS32(p, x) STORESWAB32(p, x)
 #define STORE_CROSS64(p, x) STORESWAB64(p, x)

 #define UNALIGNED_LOAD_CROSS16(p) UNALIGNED_LOADSWAB16(p)
 #define UNALIGNED_LOAD_CROSS32(p) UNALIGNED_LOADSWAB32(p)
 #define UNALIGNED_LOAD_CROSS64(p) UNALIGNED_LOADSWAB64(p)

#endif /* not CROSS_ENDIAN */

/* eight-bit versions for completeness */

FORCE_INLINE uint8 straight_load8(const uint8 *p) { return *p; }
FORCE_INLINE uint8 unaligned_load8(const void *p) { return *(const uint8 *)p; }
FORCE_INLINE void straight_store8(uint8 *p, uint8 x) { *p = x; }
FORCE_INLINE void unaligned_store8(void *p, uint8 x) { *(uint8 *)p = x; }
FORCE_INLINE uint8 identity8(uint8 x) { return x; }

#define TARGET_ENDIAN8(x) identity8(x)
#define LOAD_TARGET8(p)	straight_load8(p)
#define STORE_TARGET8(p, x) straight_store8(p, x)
#define UNALIGNED_LOAD_TARGET8(p) unaligned_load8(p)
#define UNALIGNED_STORE_TARGET8(p, x) unaligned_store8(p, x)
#define LOAD_CROSS8(p) straight_load8(p)
#define UNALIGNED_LOAD_CROSS8(p) unaligned_load8(p)
#define STORE_CROSS8(p, x) straight_store8(p, x)

#define CONVERT_LE8(x) identity8(x)
#define CONVERT_BE8(x) identity8(x)
#define LOAD_LE8(p) straight_load8(p)
#define LOAD_BE8(p) straight_load8(p)
#define STORE_LE8(p, x) straight_store8(p, x)
#define STORE_BE8(p, x) straight_store8(p, x)
#define UNALIGNED_LOAD_LE8(p) unaligned_load8(p)
#define UNALIGNED_LOAD_BE8(p) unaligned_load8(p)
#define UNALIGNED_STORE_LE8(p, x) unaligned_store8(p, x)
#define UNALIGNED_STORE_BE8(p, x) unaligned_store8(p, x)

#define SWAB8(x) identity8(x)
#define LOADSWAB8(p) straight_load8(p)
#define STORESWAB8(p, x) straight_store8(p, x)
#define UNALIGNED_LOAD8(p) unaligned_load8(p)
#define UNALIGNED_STORE8(p, x) unaligned_store8(p, x)
#define UNALIGNED_LOADSWAB8(p) unaligned_load8(p)
#define UNALIGNED_STORESWAB8(p, x) unaligned_store8(p, x)

/* Reverse the bits in an uint8. */
FORCE_INLINE uint8
reverse_bits8(uint8 x)
{
        x = (x << 4) | (x >> 4);
        x = ((x & 0x33) << 2) | ((x & 0xcc) >> 2);
        x = ((x & 0x55) << 1) | ((x & 0xaa) >> 1);
        return x;
}

/* Reverse the bits in an uint16. */
FORCE_INLINE uint16
reverse_bits16(uint16 x)
{
        x = (x << 8) | (x >> 8);
        x = ((x & 0x0f0f) << 4) | ((x & 0xf0f0) >> 4);
        x = ((x & 0x3333) << 2) | ((x & 0xcccc) >> 2);
        x = ((x & 0x5555) << 1) | ((x & 0xaaaa) >> 1);
        return x;
}

/* Reverse the bits in an uint32. */
FORCE_INLINE uint32
reverse_bits32(uint32 x)
{
        x = (x << 16) | (x >> 16);
        x = ((x & 0x00ff00ff) << 8)  | ((x & 0xff00ff00) >> 8);
        x = ((x & 0x0f0f0f0f) << 4)  | ((x & 0xf0f0f0f0) >> 4);
        x = ((x & 0x33333333) << 2)  | ((x & 0xcccccccc) >> 2);
        x = ((x & 0x55555555) << 1)  | ((x & 0xaaaaaaaa) >> 1);
        return x;
}

#ifdef UINT64_C
/* Reverse the bits in an uint64. */
FORCE_INLINE uint64
reverse_bits64(uint64 x)
{
        x = (x << 32) | (x >> 32);
        x = (x & UINT64_C(0x0000ffff0000ffff)) << 16
            | (x & UINT64_C(0xffff0000ffff0000)) >> 16;
        x = (x & UINT64_C(0x00ff00ff00ff00ff)) << 8
            | (x & UINT64_C(0xff00ff00ff00ff00)) >> 8;
        x = (x & UINT64_C(0x0f0f0f0f0f0f0f0f)) << 4
            | (x & UINT64_C(0xf0f0f0f0f0f0f0f0)) >> 4;
        x = (x & UINT64_C(0x3333333333333333)) << 2
            | (x & UINT64_C(0xcccccccccccccccc)) >> 2;
        x = (x & UINT64_C(0x5555555555555555)) << 1
            | (x & UINT64_C(0xaaaaaaaaaaaaaaaa)) >> 1;
        return x;
}
#endif

#endif /* _SIMICS_UTIL_SWABBER_H */
