/*
 * simics/util/log.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_UTIL_LOG_H
#define _SIMICS_UTIL_LOG_H

#include <simics/core/configuration.h>
#include <simics/util/vtprintf.h>

/* temporary */
#ifndef MIN
#define MIN(a, b)	((a) < (b) ? (a) : (b))
#endif

#ifndef PRINTF_FORMAT_CHECK
 #if defined(__GNUC__)
  #define PRINTF_FORMAT_CHECK(a, b) __attribute__ ((format (__printf__, a, b)))
 #else
  #define PRINTF_FORMAT_CHECK(a, b)
 #endif
#endif

#if !defined(GULP)

#if defined(HAVE_VARARG_MACROS)

#if !defined(STANDALONE)
UNUSED static void
PRINTF_FORMAT_CHECK(5, 6)
__LOG_MESSAGE(int lvl, log_object_t *dev, int grp, log_type_t typ,
              const char *str, ...)
{
        va_list va;
        char buf[1024];
        
        va_start(va, str);
        if (vtvsnprintf(buf, sizeof buf - 1, str, va) < 0)
                buf[sizeof buf - 2] = 0;
        SIM_log_message(&(dev)->obj, lvl, grp, typ, buf);
        va_end(va);
}
#endif

#define SIM_log_error(dev, grp, ...) do {                                    \
	__LOG_MESSAGE(1, dev, grp, Sim_Log_Error, __VA_ARGS__);              \
} while (0)

#define SIM_log_info(lvl, dev, grp, ...) do {                                \
        if ((lvl) <= (dev)->log_level) {                                     \
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Info, __VA_ARGS__);     \
        }                                                                    \
} while (0)

#define SIM_log_undefined(lvl, dev, grp, ...) do {                            \
        if ((lvl) <= (dev)->log_level) {                                      \
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Undefined, __VA_ARGS__); \
        }                                                                     \
} while (0)

#define SIM_log_spec_violation(lvl, dev, grp, ...) do {                            \
        if ((lvl) <= (dev)->log_level) {                                           \
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Spec_Violation, __VA_ARGS__); \
        }                                                                          \
} while (0)

#define SIM_log_target_error(lvl, dev, grp, ...) do {                              \
        if ((lvl) <= (dev)->log_level) {                                           \
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Target_Error, __VA_ARGS__);   \
        }                                                                          \
} while (0)

#define SIM_log_unimplemented(lvl, dev, grp, ...) do {                             \
        if ((lvl) <= (dev)->log_level) {                                           \
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Unimplemented, __VA_ARGS__);  \
        }                                                                          \
} while (0)

/* obsolete */
#define debug_log(lvl, dev, ...) do {                                      \
        /* use lvl + 1 since level 0 isn't allowed anymore */              \
        int __level = MIN((lvl) + 1, MAX_LOG_LEVEL);                       \
        if (__level <= (dev)->log_level) {                                 \
		__LOG_MESSAGE(__level, dev, 0, Sim_Log_Info, __VA_ARGS__); \
        }                                                                  \
} while (0)

/* obsolete */
#define debug_err(dev, ...) do {                                          \
        __LOG_MESSAGE(1, dev, 0, Sim_Log_Error, __VA_ARGS__);             \
} while (0)

#else  /* !HAVE_VARARG_MACROS */

#if !defined(STANDALONE)
UNUSED static void
__LOG_MESSAGE(int lvl, log_object_t *dev, int grp, log_type_t typ,
              const char *str, va_list va)
{
        char buf[1024];
        
        if (vtvsnprintf(buf, sizeof buf - 1, str, va) < 0)
                buf[sizeof buf - 2] = 0;
        SIM_log_message(&(dev)->obj, lvl, grp, typ, buf);
}

UNUSED static void
PRINTF_FORMAT_CHECK(3, 4)
SIM_log_error(log_object_t *dev, int grp, const char *str, ...)
{
        va_list va;

        va_start(va, str);
        __LOG_MESSAGE(1, dev, grp, Sim_Log_Error, str, va);
        va_end(va);
}

UNUSED static void
PRINTF_FORMAT_CHECK(4, 5)
SIM_log_info(int lvl, log_object_t *dev, int grp, const char *str, ...)
{
        va_list va;

        if ((lvl) <= (dev)->log_level) {
                va_start(va, str);
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Info, str, va);
                va_end(va);
        }
}

UNUSED static void
PRINTF_FORMAT_CHECK(4, 5)
SIM_log_undefined(int lvl, log_object_t *dev, int grp, const char *str, ...)
{
        va_list va;

        if ((lvl) <= (dev)->log_level) {
                va_start(va, str);
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Undefined, str, va);
                va_end(va);
        }
}

UNUSED static void
PRINTF_FORMAT_CHECK(4, 5)
SIM_log_spec_violation(int lvl, log_object_t *dev, int grp,
                       const char *str, ...)
{
        va_list va;

        if ((lvl) <= (dev)->log_level) {
                va_start(va, str);
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Spec_Violation, str, va);
                va_end(va);
        }
}

UNUSED static void
PRINTF_FORMAT_CHECK(4, 5)
SIM_log_target_error(int lvl, log_object_t *dev, int grp, const char *str, ...)
{
        va_list va;

        if ((lvl) <= (dev)->log_level) {
                va_start(va, str);
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Target_Error, str, va);
                va_end(va);
        }
}

UNUSED static void
PRINTF_FORMAT_CHECK(4, 5)
SIM_log_unimplemented(int lvl, log_object_t *dev, int grp,
                      const char *str, ...)
{
        va_list va;

        if ((lvl) <= (dev)->log_level) {
                va_start(va, str);
		__LOG_MESSAGE(lvl, dev, grp, Sim_Log_Unimplemented, str, va);
                va_end(va);
        }
}

/* obsolete */
UNUSED static void
PRINTF_FORMAT_CHECK(3, 4)
debug_log(int lvl, log_object_t *dev, const char *str, ...)
{
        va_list va;

        /* use lvl + 1 since level 0 isn't allowed anymore */
        int __level = MIN((lvl) + 1, MAX_LOG_LEVEL);
        if (__level <= (dev)->log_level) {
                va_start(va, str);
		__LOG_MESSAGE(__level, dev, 0, Sim_Log_Info, str, va);
                va_end(va);
        }
}

/* obsolete */
UNUSED static void
PRINTF_FORMAT_CHECK(2, 3)
debug_err(log_object_t *dev, const char *str, ...)
{
        va_list va;

        va_start(va, str);
        __LOG_MESSAGE(1, dev, 0, Sim_Log_Error, str, va);
        va_end(va);
}

#endif /* !STANDALONE */

#endif /* !HAVE_VARARG_MACROS */

#endif /* !GULP */

#endif /* _SIMICS_UTIL_LOG_H */
