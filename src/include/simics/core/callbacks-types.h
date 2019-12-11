/*
 * simics/core/callbacks-types.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

/* THIS FILE IS OBSOLETE; please do not use any of the types defined herein.
   It should be removed (or at least replaced with a dummy file) as soon as
   we can get rid of the callback_arguments_t and cb_func_*_t types. */

#ifndef _SIMICS_CORE_CALLBACK_TYPES_H
#define _SIMICS_CORE_CALLBACK_TYPES_H

#include <simics/core/types.h>

typedef int callback_arguments_t;

#if !defined(TURBO_SIMICS)
typedef integer_t (*cb_func_Io_t)(lang_void *);
typedef integer_t (*cb_func_IoI_t)(lang_void *, integer_t);
typedef integer_t (*cb_func_IoII_t)(lang_void *, integer_t, integer_t);
typedef integer_t (*cb_func_IoIII_t)(lang_void *,
                                     integer_t, integer_t, integer_t);
typedef integer_t (*cb_func_IooII_t)(lang_void *,
                                     lang_void *, integer_t, integer_t);
typedef integer_t (*cb_func_Ios_t)(lang_void *, char *);
typedef integer_t (*cb_func_IossII_t)(lang_void *,
                                      char *, char *, integer_t, integer_t);
typedef integer_t (*cb_func_IssII_t)(char *, char *, integer_t, integer_t);
typedef exception_type_t (*cb_func_em_t)(generic_transaction_t *);
typedef exception_type_t (*cb_func_ecm_t)(conf_object_t *,
                                          generic_transaction_t *);
typedef void (*cb_func_nI_t)(integer_t);
typedef void (*cb_func_nIco_t)(integer_t, conf_object_t *, lang_void *);
typedef void (*cb_func_nIss_t)(integer_t, char *, char *);
typedef void (*cb_func_nc_t)(conf_object_t *);
typedef void (*cb_func_nco_t)(conf_object_t *, lang_void *);
typedef void (*cb_func_ncoi_t)(conf_object_t *, lang_void *, int);
typedef void (*cb_func_ncsII_t)(conf_object_t *, char *, integer_t, integer_t);
typedef void (*cb_func_ncsIII_t)(conf_object_t *,
                                 char *, integer_t, integer_t, integer_t);
typedef void (*cb_func_ns_t)(char *);
typedef void (*cb_func_nsI_t)(char *, integer_t);
typedef void (*cb_func_nss_t)(char *, char *);
typedef void (*cb_func_nsss_t)(char *, char *, char *);
typedef void (*cb_func_nssss_t)(char *, char *, char *, char *);
typedef void (*cb_func_nsssss_t)(char *, char *, char *, char *, char *);
typedef void (*cb_func_nvo_t)(void *, lang_void *);
typedef void (*cb_func_nzo_t)(ignored_pointer_t, lang_void *);
typedef char *(*cb_func_so_t)(lang_void *);
typedef void (*cb_func_nci_t)(conf_object_t *, int);
typedef void (*cb_func_no_t)(lang_void *);
typedef void (*cb_func_noisssI_t)(lang_void *,
                                  int, char *, char *, char *, integer_t);
typedef void (*cb_func_noI_t)(lang_void *, integer_t);
typedef void (*cb_func_noII_t)(lang_void *, integer_t, integer_t);
typedef void (*cb_func_noIII_t)(lang_void *, integer_t, integer_t, integer_t);
typedef void (*cb_func_noIIII_t)(lang_void *,
                                 integer_t, integer_t, integer_t, integer_t);
typedef void (*cb_func_noIIvI_t)(lang_void *,
                                 integer_t, integer_t, void *, integer_t);
typedef void (*cb_func_noIIzI_t)(lang_void *,
                                 integer_t, integer_t, ignored_pointer_t,
                                 integer_t);
typedef void (*cb_func_nois_t)(lang_void *, int, char *);
typedef void (*cb_func_noIs_t)(lang_void *, integer_t, char *);
typedef void (*cb_func_noc_t)(lang_void *, conf_object_t *);
typedef void (*cb_func_noci_t)(lang_void *, conf_object_t *, int);
typedef void (*cb_func_nocii_t)(lang_void *, conf_object_t *, int, int);
typedef void (*cb_func_nocI_t)(lang_void *, conf_object_t *, integer_t);
typedef void (*cb_func_nocII_t)(lang_void *, conf_object_t *,
                                integer_t, integer_t);
typedef void (*cb_func_nocIII_t)(lang_void *, conf_object_t *,
                                 integer_t, integer_t, integer_t);
typedef void (*cb_func_nocIvvv_t)(lang_void *, conf_object_t *,
                                  integer_t, void *, void *, void *);
typedef void (*cb_func_nocIzzz_t)(lang_void *, conf_object_t *,
                                  integer_t, ignored_pointer_t,
                                  ignored_pointer_t, ignored_pointer_t);
typedef void (*cb_func_nocc_t)(lang_void *, conf_object_t *, conf_object_t *);
typedef void (*cb_func_noccc_t)(lang_void *, conf_object_t *,
                                conf_object_t *, conf_object_t *);
typedef void (*cb_func_nocs_t)(lang_void *, conf_object_t *, char *);
typedef void (*cb_func_noi_t)(lang_void *, int);
typedef void (*cb_func_noii_t)(lang_void *, int, int);
typedef void (*cb_func_noiiI_t)(lang_void *, int, int, integer_t);
typedef void (*cb_func_nooII_t)(lang_void *, lang_void *,
                                integer_t, integer_t);
typedef void (*cb_func_nooIII_t)(lang_void *, lang_void *,
                                 integer_t, integer_t, integer_t);
typedef void (*cb_func_nos_t)(lang_void *, char *);
typedef void (*cb_func_nosI_t)(lang_void *, char *, integer_t);
typedef void (*cb_func_nosII_t)(lang_void *, char *, integer_t, integer_t);
typedef void (*cb_func_nossII_t)(lang_void *, char *, char *,
                                 integer_t, integer_t);
typedef void (*cb_func_nov_t)(lang_void *, void *);
typedef void (*cb_func_noz_t)(lang_void *, ignored_pointer_t);
typedef void (*cb_func_noIm_t)(lang_void *, integer_t, 
                               generic_transaction_t *);
typedef void (*cb_func_nom_t)(lang_void *, generic_transaction_t *);
typedef void (*cb_func_nocisssI_t)(lang_void *, conf_object_t *,
                                   int, char *, char *, char *, integer_t);
typedef void (*cb_func_nocIIvI_t)(lang_void *, conf_object_t *,
                                  integer_t, integer_t, void *, integer_t);
typedef void (*cb_func_nocIIzI_t)(lang_void *, conf_object_t *,
                                  integer_t, integer_t, ignored_pointer_t,
                                  integer_t);
typedef void (*cb_func_nocis_t)(lang_void *, conf_object_t *, int, char *);
typedef void (*cb_func_nociiI_t)(lang_void *, conf_object_t *,
                                 int, int, integer_t);
typedef void (*cb_func_nocIs_t)(lang_void *, conf_object_t *,
                                integer_t, char *);
typedef void (*cb_func_nocoII_t)(lang_void *, conf_object_t *,
                                 lang_void *, integer_t, integer_t);
typedef void (*cb_func_nocoIII_t)(lang_void *, conf_object_t *,
                                  lang_void *, integer_t, integer_t,
                                  integer_t);
typedef void (*cb_func_nocsI_t)(lang_void *, conf_object_t *,
                                char *, integer_t);
typedef void (*cb_func_nocsII_t)(lang_void *, conf_object_t *,
                                 char *, integer_t, integer_t);
typedef void (*cb_func_nocssII_t)(lang_void *, conf_object_t *,
                                  char *, char *, integer_t, integer_t);
typedef void (*cb_func_nocv_t)(lang_void *, conf_object_t *, void *);
typedef void (*cb_func_nocz_t)(lang_void *, conf_object_t *,
                               ignored_pointer_t);
typedef void (*cb_func_nocIIII_t)(lang_void *, conf_object_t *,
                                  integer_t, integer_t, integer_t, integer_t);
typedef void (*cb_func_nocIm_t)(lang_void *, conf_object_t *,
                                integer_t, generic_transaction_t *);
typedef void (*cb_func_nocm_t)(lang_void *, conf_object_t *,
                               generic_transaction_t *);
typedef void (*cb_func_noIci_t)(lang_void *, integer_t, conf_object_t *, int);
typedef void (*cb_func_nocIci_t)(lang_void *, conf_object_t *,
                                 integer_t, conf_object_t *, int);
typedef void (*cb_func_noIcs_t)(lang_void *,
                                integer_t, conf_object_t *, char *);
typedef void (*cb_func_nocIcs_t)(lang_void *, conf_object_t *,
                                 integer_t, conf_object_t *, char *);

#endif /* TURBO_SIMICS */

#endif /* _SIMICS_CORE_CALLBACK_TYPES_H */
