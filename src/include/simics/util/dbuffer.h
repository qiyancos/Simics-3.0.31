/*
 * simics/util/dbuffer.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_DBUFFER_H
#define _SIMICS_UTIL_DBUFFER_H

/*
   <add id="simics api types">
   <name index="true">dbuffer_t</name>
   <doc>
   <doc-item name="NAME">dbuffer_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="dbuffer_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This type is used to store blocks of binary data.  It is optimized
   for fast adding and removing of data, and does fast copying between
   buffers using copy-on-write semantics.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="dbuffer_t def"></add-type> */
typedef struct dbuffer dbuffer_t;

#ifndef GULP

/* Get a new buffer */
dbuffer_t *new_dbuffer(void);

/* Release a buffer.  The buffer should not be freed in any other
   way.  */
void dbuffer_free(dbuffer_t *dbuffer);

/* Get the length */
size_t dbuffer_len(dbuffer_t *dbuffer);

/*
 * Add static data.  This will make the buffer reference the data
 * pointed to directly, without making a copy.
 *
 * If the 'adopt' flag is true, the control of the data block is
 * transferred to the dbuffer.  It is assumed to be a MM_MALLOCed
 * block that will be MM_FREEd when the dbuffer is freed.
 *
 * If the 'adopt' flag is false, the dbuffer will not free the
 * memory. Instead it is up to the caller to free the memory, but it
 * must not do so before the dbuffer is freed.  Actually, this
 * reference could be copied to other dbuffers, so great care has to
 * be taken.  This shoud only be used for buffers that will only be
 * read, since it hard to know if a write operation will actually
 * write to the buffer or to a copy.
*/
uint8 *dbuffer_append_external_data(dbuffer_t *dbuffer, void *data, size_t len, int adopt);
uint8 *dbuffer_prepend_external_data(dbuffer_t *dbuffer, void *data, size_t len, int adopt);

/* Copy from one buffer to another. */
void dbuffer_copy_append(dbuffer_t *dst, dbuffer_t *src, size_t offset, size_t len);
void dbuffer_copy_prepend(dbuffer_t *dst, dbuffer_t *src, size_t offset, size_t len);

/* Add a repeating byte value */
uint8 *dbuffer_append_value(dbuffer_t *dbuffer, int value, size_t len);
uint8 *dbuffer_prepend_value(dbuffer_t *dbuffer, int value, size_t len);

/* Add uninitialized memory */
uint8 *dbuffer_append(dbuffer_t *dbuffer, size_t len);
uint8 *dbuffer_prepend(dbuffer_t *dbuffer, size_t len);
uint8 *dbuffer_insert(dbuffer_t *dbuffer, size_t offset, size_t len);

/* Make the buffer smaller */
void dbuffer_remove(dbuffer_t *dbuffer, size_t offset, size_t remove_len);
void dbuffer_remove_head(dbuffer_t *dbuffer, size_t remove_len);
void dbuffer_remove_tail(dbuffer_t *dbuffer, size_t remove_len);


/*
 * Extract data for reading or writing.  The 'offset' and 'len'
 * parameter specify a region of the buffer to read from or write to.
 * The returned pointer is guaranteed to point to a contiguous block
 * of memory.
 *
 * The returned pointer is only valid until the next operation on the
 * dbuffer.  The only operation that is guaranteed not to invalidate
 * the pointer is the dbuffer_len() function.
 *
 * The *_some versions of these functions take an 'actual_len'
 * parameter, and may return a smaller buffer than requested.  The
 * actual number of valid bytes in the returned buffer is then written
 * to *actual_len, and is smaller if it would have had to copy data to
 * return a pointer to the whole region.  If NULL is passed for
 * 'actual_len', it will force the functions to return the full
 * region.
 *
 * The other functions always create a complete region, equivalent to
 * passing NULL in the 'actual_len' parameter.
 *
 * The *_all versions of these functions assume 0 for 'offset', and
 * buffer_len(dbuffer) for 'len'.
 */

/* The pointer returned by dbuffer_read() may point to memory shared
   with other buffers, and should not be written to. */
uint8 *dbuffer_read(dbuffer_t *dbuffer, size_t offset, size_t len);
uint8 *dbuffer_read_some(dbuffer_t *dbuffer, size_t offset,
                         size_t len, size_t *actual_len);
uint8 *dbuffer_read_all(dbuffer_t *dbuffer);

/* A buffer returned by dbuffer_update() is not used by any other
   dbuffer_t and can be freely read from or written to. */
uint8 *dbuffer_update(dbuffer_t *dbuffer, size_t offset,
                      size_t len);
uint8 *dbuffer_update_some(dbuffer_t *dbuffer, size_t offset,
                           size_t len, size_t *actual_len);
uint8 *dbuffer_update_all(dbuffer_t *dbuffer);

/* A buffer returned by dbuffer_replace() is not used by any other
   dbuffer_t and may contain junk.  This function should only be used
   when the whole buffer section will be overwritten with new data. */
uint8 *dbuffer_replace(dbuffer_t *dbuffer, size_t offset, size_t len);
uint8 *dbuffer_replace_some(dbuffer_t *dbuffer, size_t offset,
                            size_t len, size_t *actual_len);
uint8 *dbuffer_replace_all(dbuffer_t *dbuffer);

/* Make a full copy of another buffer */
dbuffer_t * dbuffer_clone(dbuffer_t *dbuffer);

/* Split a buffer in two.  The data after 'offset' is left in the old
   dbuffer, and the data before 'offset' is returned in a newly
   allocated dbuffer. */
dbuffer_t * dbuffer_split(dbuffer_t *dbuffer, size_t offset);


/* Derived functions */

#ifndef STANDALONE
/* Make the buffer empty. */
static inline void
dbuffer_clear(dbuffer_t *dbuffer) {
        dbuffer_remove_tail(dbuffer, dbuffer_len(dbuffer));
}

/* Make the buffer contain a repeating byte value.  Any previous
   contents are removed. */
static inline void
dbuffer_set(dbuffer_t *dbuffer, int val, size_t len) {
        dbuffer_clear(dbuffer);
        dbuffer_append_value(dbuffer, val, len);
}
#endif /* STANDALONE */

#endif /* !GULP */

#endif /* _SIMICS_UTIL_DBUFFER_H */
