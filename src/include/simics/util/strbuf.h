/*
 * simics/util/strbuf.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_STRBUF_H
#define _SIMICS_UTIL_STRBUF_H

#include <stdio.h>
#include <stdarg.h>

/* Sys V streams use 'struct strbuf' already */
typedef struct stringbuf {
	char *s;		/* string, always 0-terminated */
	int size;		/* size of allocated buffer */
	int len;		/* current length */
} strbuf_t;

#if !defined(TURBO_SUPPORT) || !defined(STANDALONE)

#ifdef __GNUC__
 #define ATTRIBUTE_PRINTF(n, m) __attribute__ ((__format__ (__printf__, n, m)))
#else
 #define ATTRIBUTE_PRINTF(n, m)
#endif

strbuf_t sb_new(const char *s);
void sb_free(strbuf_t *sb);
char *sb_detach(strbuf_t *sb);
void sb_realloc(strbuf_t *sb, int minlen);
int sb_write(strbuf_t *sb, FILE *f);
void sb_vaddfmt(strbuf_t *sb, const char *format, va_list va);
void sb_addfmt(strbuf_t *sb, const char *format, ...) ATTRIBUTE_PRINTF(2, 3);
void sb_vfmt(strbuf_t *sb, const char *format, va_list va);
void sb_fmt(strbuf_t *sb, const char *format, ...) ATTRIBUTE_PRINTF(2, 3);
void sb_addesc(strbuf_t *sb, char c, char delim);

/* return length of string, excluding nul */
FORCE_INLINE int
sb_len(strbuf_t *sb)
{
	return sb->len;
}

/* return string as C-string, always 0-terminated */
FORCE_INLINE char *
sb_str(strbuf_t *sb)
{
	return sb->s;
}

/* Return the ith character in the string. Count from end of string if
   i is negative. */
FORCE_INLINE char
sb_char(strbuf_t *sb, int i)
{
        if (i >= 0)
                return sb->s[i];
        else 
                return sb->s[sb->len + i];
}


#define SB_INIT {(char *)"", 0, 0}

/* Initialise a string which has not been initialised yet.
   This is equivalent to initialising it with SB_INIT.
   Either sb_init() or initialisation to SB_INIT must be done before a string
   can be used. */
FORCE_INLINE void
sb_init(strbuf_t *sb)
{
	sb->s = (char *)"";
	sb->size = 0;
	sb->len = 0;
}

/* extend storage of sb to hold at least minlen chars, including terminating
   nul */
FORCE_INLINE void
sb_extend(strbuf_t *sb, int minlen)
{
	/* fast path */
	if (minlen > sb->size)
		sb_realloc(sb, minlen);
}

/* set a string to the contents of a C-string */
FORCE_INLINE void
sb_set(strbuf_t *sb, const char *str)
{
	int len = strlen(str);
	sb_extend(sb, len + 1);
	memcpy(sb->s, str, len + 1);
	sb->len = len;
}

/* set a string to the contents of another strbuf */
FORCE_INLINE void
sb_copy(strbuf_t *dst, strbuf_t *src)
{
	sb_extend(dst, src->len + 1);
	memcpy(dst->s, src->s, src->len + 1);
	dst->len = src->len;
}

/* make a string empty */
FORCE_INLINE void
sb_clear(strbuf_t *sb)
{
	sb->len = 0;
        if (sb->size)
                sb->s[0] = '\0';
}

/* append sb2 to sb1 */
FORCE_INLINE void
sb_cat(strbuf_t *sb1, strbuf_t *sb2)
{
	sb_extend(sb1, sb1->len + sb2->len + 1);
	memcpy(sb1->s + sb1->len, sb2->s, sb2->len + 1);
	sb1->len += sb2->len;
}

/* append a C-string to a strbuf */
FORCE_INLINE void
sb_addstr(strbuf_t *sb, const char *str)
{
	int len = strlen(str);
	sb_extend(sb, sb->len + len + 1);
	memcpy(sb->s + sb->len, str, len + 1);
	sb->len += len;
}

/* append a counted string to a strbuf */
FORCE_INLINE void
sb_addmem(strbuf_t *sb, const char *str, int len)
{
	sb_extend(sb, sb->len + len + 1);
	memcpy(sb->s + sb->len, str, len);
	sb->len += len;
        sb->s[sb->len] = '\0';
}

/* add a character to a string */
FORCE_INLINE void
sb_addc(strbuf_t *sb, char c)
{
	sb_extend(sb, sb->len + 2);
	sb->s[sb->len++] = c;
	sb->s[sb->len] = '\0';
}

/* add a character repeated a given number of times to a string */
FORCE_INLINE void
sb_addchars(strbuf_t *sb, int n, char c)
{
	sb_extend(sb, sb->len + n + 1);
	memset(sb->s + sb->len, c, n);
	sb->len += n;
	sb->s[sb->len] = '\0';
}

/* Resize string. If extended, pad with null bytes. */
FORCE_INLINE void
sb_resize(strbuf_t *sb, int size)
{
	if (size > sb->len) {
		sb_extend(sb, size + 1);
		memset(sb->s + sb->len, 0, size - sb->len);
	}
	sb->len = size;
	sb->s[size] = '\0';
}

/* return a copy of a string */
FORCE_INLINE strbuf_t
sb_dup(strbuf_t *sb)
{
	strbuf_t new_sb = SB_INIT;
	sb_cat(&new_sb, sb);
	return new_sb;
}

/* Delete n characters from position start */
FORCE_INLINE void
sb_delete(strbuf_t *sb, int start, int n)
{
        memmove(sb->s + start, sb->s + start + n, sb->len - (start + n) + 1);
        sb->len -= n;
}

#endif /* TURBO_SUPPORT or STANDALONE */

#endif /* _SIMICS_UTIL_STRBUF_H */
