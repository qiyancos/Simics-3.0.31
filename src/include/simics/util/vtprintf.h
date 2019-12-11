/*
 * simics/util/vtprintf.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_VTPRINTF_H
#define _SIMICS_UTIL_VTPRINTF_H

#if defined(__cplusplus)
extern "C" {
#endif

#include <stdarg.h>
#include <stdio.h>

#if !defined(GULP) && !defined(GULP_API_WRAP)

#if defined(__GNUC__)
 #define PRINTF_FORMAT(a, b) __attribute__ ((format (__printf__, a, b)))
#else
 #define PRINTF_FORMAT(a, b)
#endif

int vtvfprintf(FILE *stream, const char *format, va_list va);
int vtfprintf(FILE *stream, const char *format, ...) PRINTF_FORMAT(2, 3);
int vtvprintf(const char *format, va_list va);
int vtprintf(const char *format, ...) PRINTF_FORMAT(1, 2);
int vtvsprintf(char *str, const char *format, va_list va);
int vtsprintf(char *str, const char *format, ...) PRINTF_FORMAT(2, 3);
int vtvsnprintf(char *str, size_t n, const char *format, va_list va);
int vtsnprintf(char *str, size_t n, const char *format, ...)
             PRINTF_FORMAT(3, 4);

/* pr is just an alias for vtprintf */
int pr(const char *format, ...) PRINTF_FORMAT(1, 2);

#endif /* !GULP && !GULP_API_WRAP */

#if defined(__cplusplus)
}
#endif

#endif /* _SIMICS_UTIL_VTPRINTF_H */
