/*
 * simics/util/alloc.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_ALLOC_H
#define _SIMICS_UTIL_ALLOC_H

#if defined(__cplusplus)
extern "C" {
#endif

#ifdef STANDALONE
#include <stdlib.h>

#define MM_MALLOC(nelems, type) ((type *)malloc((nelems) * sizeof(type)))
#define MM_MALLOC_SZ(size, type) ((type *)malloc(size))
#define MM_ZALLOC(nelems, type) ((type *)calloc(nelems, sizeof(type)))
#define MM_ZALLOC_SZ(size, type) ((type *)calloc(size, 1))
#define MM_REALLOC(p, nelems, type) ((type *)                             \
                                     realloc(p, (nelems) * sizeof(type)))
#define MM_REALLOC_SZ(p, size, type) ((type *) realloc(p, size))

/* We can't define ZREALLOC since we don't know how large the original
   allocation was */
#define MM_ZREALLOC(p, nelems, type) sorry_no_zrealloc_available
#define MM_ZREALLOC_SZ(p, nelems, type) sorry_no_zrealloc_available

/* MM_MALIGN isn't available in the general case, but at least it works
   under Unix: */
#define MM_MALIGN(align, nelems, type) ((type *)                          \
                                        memalign(align,                   \
                                                 (nelems) * sizeof(type)))
/* MM_ZALIGN would require an inline function; can't be bothered */
#define MM_ZALIGN(align, nelems, type) sorry_no_zalign_available

#define MM_STRDUP(s) strdup(s)
#define MM_FREE(p) free(p)

#else

/* The gcc 'malloc' attribute just tells the compiler that a function
   returns an alias-free pointer. Note that this is true even for realloc. */
#ifndef ATTRIBUTE_MALLOC
 #if defined __GNUC__ && __GNUC__ >= 3
  #define ATTRIBUTE_MALLOC __attribute__ ((__malloc__))
 #else
  #define ATTRIBUTE_MALLOC
 #endif
#endif

void VT_init_vtmem(void);

void mm_free(void *ptr, const char *file, int line);
void *mm_malloc(size_t size, size_t typesize, const char *type,
		const char *file, int line) ATTRIBUTE_MALLOC;
void *mm_malloc_low(size_t size, size_t typesize, const char *type,
                    const char *file, int line) ATTRIBUTE_MALLOC;
void *mm_zalloc(size_t size, size_t typesize, const char *type,
		const char *file, int line) ATTRIBUTE_MALLOC;
void *mm_realloc(void *ptr, size_t size, size_t typesize, const char *type,
		 const char *file, int line) ATTRIBUTE_MALLOC;
void *mm_zrealloc(void *ptr, size_t size, size_t typesize, const char *type,
		  const char *file, int line) ATTRIBUTE_MALLOC;
void *mm_malign(size_t align, size_t size, size_t typesize, const char *type,
		const char *file, int line) ATTRIBUTE_MALLOC;
void *mm_zalign(size_t align, size_t size, size_t typesize, const char *type,
		const char *file, int line) ATTRIBUTE_MALLOC;
char *mm_strdup(const char *str, const char *file, int line)
     ATTRIBUTE_MALLOC;

void mm_verify_alloc(void *ptr, const char *type, size_t size);

#if defined(__SUNPRO_C)
#pragma returns_new_memory(mm_malloc, mm_zalloc, mm_realloc, mm_zrealloc, \
			   mm_malign, mm_zalign, mm_strdup)
#endif

/*
  <add-macro id="vtmem macros">
  <short>free vtmem object</short>
  <fun>MM_FREE</fun> frees a vtmem object. It is legal to pass a null
  pointer, in which case it does nothing.
  </add-macro>
*/
#define MM_FREE(p)							\
    mm_free(p, __FILE__, __LINE__)

/*
  <add-macro id="vtmem macros">
  <short>allocate memory object</short>
  <fun>MM_MALLOC</fun> allocates <arg>nelems</arg> objects of
  <arg>type</arg>.

  <fun>MM_MALLOC_SZ</fun> specifies the allocation in bytes, which can be
  occasionally useful.

  <fun>MM_ZALLOC</fun> and <fun>MM_ZALLOC_SZ</fun> do the same thing as their
  Z-less counterparts but in addition zero out the allocated memory.

  If <arg>nelems</arg> or <arg>size</arg> are zero, a null pointer is returned.

  <doc-item name="RETURN VALUE">Pointer to the allocated object.</doc-item>  
  </add-macro>
*/
#define MM_MALLOC(nelems, type)						\
    (type *)mm_malloc(sizeof(type) * (nelems), sizeof(type), #type,	\
		      __FILE__, __LINE__)
/* <append-macro id="MM_MALLOC"/> */
#define MM_MALLOC_SZ(size, type)					\
    (type *)mm_malloc(size, sizeof(type), #type,			\
    		      __FILE__, __LINE__)
/* <append-macro id="MM_MALLOC"/> */
#define MM_ZALLOC(nelems, type)						\
    (type *)mm_zalloc(sizeof(type) * (nelems), sizeof(type), #type,	\
                      __FILE__, __LINE__)
/* <append-macro id="MM_MALLOC"/> */
#define MM_ZALLOC_SZ(size, type)					\
    (type *)mm_zalloc(size, sizeof(type), #type,			\
                      __FILE__, __LINE__)

#define MM_MALLOC_LOW(nelems, type)                                     \
    (type *)mm_malloc_low(sizeof(type) * (nelems), sizeof(type), #type, \
                          __FILE__, __LINE__)

/*
  <add-macro id="vtmem macros">
  <short>reallocate memory</short>
  <fun>MM_REALLOC</fun> changes the size of an allocated memory block to
  <arg>nelems</arg> elements.

  <fun>MM_REALLOC_SZ</fun> specifies the new size in bytes.

  <fun>MM_ZREALLOC</fun> and <fun>MM_ZREALLOC_SZ</fun> do the same
  thing as their Z-less counterparts, but in addition zero out the
  extended part of the allocation.

  If the passed pointer is <const>NULL</const>, then these macros are
  equivalent to an allocation of the desired amount. If
  <arg>nelems</arg> or <arg>size</arg> are zero, a null pointer is
  returned and the original allocation is freed.

  <doc-item name="RETURN VALUE">Pointer to the reallocated
  object.</doc-item>
  </add>
*/
#define MM_REALLOC(p, nelems, type)					\
    (type *)mm_realloc(p, sizeof(type) * (nelems), sizeof(type), #type,	\
	               __FILE__, __LINE__)
/* <append-macro id="MM_REALLOC"/> */
#define MM_REALLOC_SZ(p, size, type)					\
    (type *)mm_realloc(p, size, sizeof(type), #type,			\
	               __FILE__, __LINE__)
/* <append-macro id="MM_REALLOC"/> */
#define MM_ZREALLOC(p, nelems, type)					\
    (type *)mm_zrealloc(p, sizeof(type) * (nelems), sizeof(type),	\
                        #type, __FILE__, __LINE__)
/* <append-macro id="MM_REALLOC"/> */
#define MM_ZREALLOC_SZ(p, size, type)					\
    (type *)mm_zrealloc(p, size, sizeof(type), #type,			\
		        __FILE__, __LINE__)

/*
  <add-macro id="vtmem macros">
  <short>allocate aligned memory</short>  

  <fun>MM_MALIGN</fun> allocates memory aligned to the nearest
  <arg>align</arg>-byte boundary. The <arg>align</arg> parameter must
  be an even power of 2.

  <fun>MM_ZALIGN</fun> does the same thing but in addition zeroes out
  the allocated memory.

  Allocated aligned memory imposes a slightly higher space overhead
  than ordinary memory as handed out by <fun>MM_MALLOC</fun>. The
  overhead is of the order of <arg>align</arg> bytes per allocation.

  <doc-item name="RETURN VALUE">Pointer to the allocated object.</doc-item>  
  </add-macro>
*/
#define MM_MALIGN(align, nelems, type)					\
    (type *)mm_malign(align, sizeof(type) * (nelems), sizeof(type),	\
		      #type, __FILE__, __LINE__)
/* <append-macro id="MM_MALIGN"/> */
#define MM_ZALIGN(align, nelems, type)					\
    (type *)mm_zalign(align, sizeof(type) * (nelems), sizeof(type),	\
		      #type, __FILE__, __LINE__)

/*
  <add-macro id="vtmem macros">
  <short>duplicate a string</short>

  Corresponds to the traditional <fun>strdup()</fun> function, but
  uses the instrumentation of the Simics memory allocator.

  <doc-item name="RETURN VALUE">Pointer to the newly allocated
  string.</doc-item>

  </add-macro>
*/
#define MM_STRDUP(str)							\
    mm_strdup(str, __FILE__, __LINE__)

/* take over any stray use of normal malloc()s */
#if !defined(IGNORE_VTMEM)

#undef malloc
#undef calloc
#undef realloc
#undef free
#undef strdup

#define malloc(size) mm_malloc(size, 1, "char", __FILE__, __LINE__)
#define calloc(size, n) mm_zalloc((size) * (n), 1, "char",	\
				  __FILE__, __LINE__)
#define realloc(p, size) mm_realloc(p, size, 1, "char", __FILE__, __LINE__)
#define free(p) mm_free(p, __FILE__, __LINE__)
#define strdup(s) mm_strdup(s, __FILE__, __LINE__)

#endif /* not IGNORE_VTMEM */

/* interface to libc's own allocator */
void *native_calloc(size_t nmemb, size_t size);
void *native_malloc(size_t size);
void native_free(void *ptr);
void *native_realloc(void *ptr, size_t size);
char *native_strdup(const char *s);

/* dummy implementation of obsolete function */
#define mm_new_group(desc) 0

#endif /* STANDALONE */

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* _SIMICS_UTIL_ALLOC_H */
