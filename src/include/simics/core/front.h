/*
 * simics/core/front.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_FRONT_H
#define _SIMICS_CORE_FRONT_H

#include <simics/util/vtprintf.h>
#include <setjmp.h>
#include <simics/core/types.h>

#if !defined(SIM_BC_NO_STDOUT_REDEFINE) && !defined(STANDALONE)

/* <add id="simics compat defines" label="simbcnostdoutredefine">
   <name>SIM_BC_NO_STDOUT_REDEFINE</name><ndx>SIM_BC_NO_STDOUT_REDEFINE</ndx>
   When this macro is defined, Simics will <i>not</i> define the
   following macros to override some standard C library functions:

   <insert id="sim_bc_no_stdout_redefine_def"/>
   </add>
 */

/* <add id="sim_bc_no_stdout_redefine_def">
   <insert-until text="// JDOCU INSERT-UNTIL sim_bc_no_stdout_redefine"/>
   <ndx>printf</ndx><ndx>puts</ndx><ndx>fwrite</ndx><ndx>putchar</ndx>
   <ndx>SIM_printf</ndx><ndx>SIM_write</ndx>
   </add>
 */
#undef printf

#if defined(HAVE_VARARG_MACROS)
#define printf(...) SIM_printf(__VA_ARGS__)
#else
#define printf SIM_printf
#endif

#undef vprintf
#define vprintf(str, ap) SIM_printf_vararg(str, ap)

#undef puts
#define puts(str) SIM_puts(str)

#undef putchar
#define putchar(c) SIM_putchar(c)

#undef fwrite
#define fwrite(ptr, size, nmemb, stream)                \
        ((stream) == stdout                             \
         ? (size_t)SIM_write((ptr), (size) * (nmemb))   \
         : fwrite(ptr, size, nmemb, stream))

#undef fputs
#define fputs(str, stream)                      \
        ((stream) == stdout                     \
         ? SIM_write((str), strlen(str))        \
         : fputs((str), (stream)))

#undef fflush
#define fflush(stream) ((stream) == stdout ? SIM_flush() : fflush(stream))
// JDOCU INSERT-UNTIL sim_bc_no_stdout_redefine

#endif /* not SIM_BC_NO_STDOUT_REDEFINE and not STANDALONE */

int VT_write(const byte_string_t src, int force);
int SIM_flush(void);

#if !defined(GULP)
int SIM_write(const void *src, int length);

int SIM_printf(const char *format, ...)
#if defined(__GNUC__)
   __attribute__ ((format (__printf__, 1, 2)))
#endif
  ;

int SIM_printf_vararg(const char *format, va_list ap);
#endif /* ! GULP */

int SIM_puts(const char *NOTNULL s);
int SIM_putchar(int c);

/* <add-type id="output_handler_t def"><ndx>output_handler_t</ndx></add-type> */
typedef void (*output_handler_t)(lang_void *data,
                                 const char *src, size_t length);

void SIM_add_output_handler(output_handler_t func, lang_void *user_data);
void SIM_remove_output_handler(output_handler_t func, typed_lang_void *user_data);


#define FOR_ALL_EXCEPTIONS(op)                                          \
        op( SimExc_No_Exception,		SimExc_No_Exception ),  \
        op( SimExc_General,			SimExc_General ),       \
        op( SimExc_Arithmetic,			SimExc_General ),       \
        op( SimExc_Lookup,			SimExc_General ),       \
        op( SimExc_Attribute,			SimExc_General ),       \
        op( SimExc_IOError,			SimExc_General ),       \
        op( SimExc_Index,			SimExc_General ),       \
        op( SimExc_Memory,			SimExc_General ),       \
	op( SimExc_Inquiry,			SimExc_Memory ),        \
	op( SimExc_InquiryOutsideMemory,	SimExc_Inquiry ),       \
	op( SimExc_InquiryUnhandled,		SimExc_Inquiry ),       \
        op( SimExc_Overflow,			SimExc_General ),       \
        op( SimExc_Syntax,			SimExc_General ),       \
        op( SimExc_Type,			SimExc_General ),       \
        op( SimExc_ZeroDivision,		SimExc_Arithmetic ),    \
	op( SimExc_RuntimeError,		SimExc_General ),       \
	op( SimExc_Break,			SimExc_General ),       \
	op( SimExc_PythonTranslation,		SimExc_General ),       \
        op( SimExc_IllegalValue,                SimExc_Attribute ),     \
        op( SimExc_ObjectNotFound,              SimExc_Lookup ),        \
        op( SimExc_InterfacedNotFound,          SimExc_Lookup ),        \
        op( SimExc_AttrNotFound,                SimExc_Lookup ),        \
        op( SimExc_AttrNotReadable,             SimExc_Attribute ),     \
        op( SimExc_AttrNotWritable,             SimExc_Attribute ),     \
        op( SimExc_NeedInteger,                 SimExc_Type ),          \
        op( SimExc_NeedFloating,                SimExc_Type ),          \
        op( SimExc_NeedBoolean,                 SimExc_Type ),          \
        op( SimExc_NeedString,                  SimExc_Type ),          \
        op( SimExc_NeedList,                    SimExc_Type ),          \
        op( SimExc_NeedDict,                    SimExc_Type ),          \
        op( SimExc_NeedData,                    SimExc_Type ),          \
        op( SimExc_NeedObject,                  SimExc_Type ),          \
        op( SimExc_InternalRevexecBreak,        SimExc_General )

#define ENUM_DEF(this, parent) this

typedef enum sim_exception {
        FOR_ALL_EXCEPTIONS(ENUM_DEF),
        Sim_Exceptions
} sim_exception_t;

#undef ENUM_DEF

#if !defined(_MSC_VER) && !defined(__SUNPRO_C)
enum sim_exception;
#endif

#if !defined(__LEAVE_EXCEPTION_DEFS)
#undef FOR_ALL_EXCEPTIONS
#endif

#ifndef SIM_NATIVE_PATH_DEFINED
#define SIM_NATIVE_PATH_DEFINED
char *SIM_native_path(const char *NOTNULL path);
#endif

void VT_try_module(const char *NOTNULL filename);
void VT_sign_module(const char *NOTNULL filename);
void VT_push_current_loading_module(const char *NOTNULL m);
void VT_pop_current_loading_module(void);
char *VT_get_current_loading_module(void);
char *VT_get_last_loaded_module(void);
attr_value_t VT_get_implemented_haps(const char *NOTNULL m);
int VT_module_has_commands(const char *NOTNULL module, int global);
void VT_add_module_dir(const char *NOTNULL path);

attr_value_t SIM_get_all_modules(void);
attr_value_t SIM_get_all_failed_modules(void);

void SIM_module_list_refresh(void);

int get_compile_info(int idx, int id, char *info_out);

#if !defined(GULP)
void pr_err(const char *str, ...);
void pr_err_vararg(const char *str, va_list ap);

#define BATCH_MODE_MAX_ERROR_MSGS 100000
extern uinteger_t max_error_msgs;
void increase_and_check_error_count(void);

void VT_set_frontend_context(void *context);
#endif /* !GULP */

int VT_set_frontend_server(const char *class_name);

void VT_reinstall_interrupt_key_handler(void);

void VT_do_command(const char *command_string);

NORETURN void VT_return_to_front(void);
#if defined(__SUNPRO_C)
#pragma does_not_return(VT_return_to_front)
#endif

void SIM_frontend_exception(sim_exception_t exc_type, const char *NOTNULL str);

#if !defined(GULP)
void VT_frontend_exception(const char *filename, int line,
                           sim_exception_t exc_type, const char *str, ...);
#endif

#ifndef SIM_frontend_exception
#  define SIM_frontend_exception(exc_type, str)                           \
        VT_frontend_exception(__FILE__, __LINE__, exc_type, "%s", str)
#endif

/* print out the list of the last exceptions */
void DBG_print_exception_list(void);

void VT_logit(const char *NOTNULL str);

int VT_remote_control(void);
void VT_send_control_msg(attr_value_t *NOTNULL val);
#ifndef GULP
void VT_send_str_msg(const char *req, integer_t id, const char *arg);
#endif

void SIM_set_prompt(const char *NOTNULL prompt);

void SIM_source_python(const char *NOTNULL file);
void SIM_source_python_in_module(const char *NOTNULL file,
                                 const char *NOTNULL module);
void SIM_run_command_file(const char *NOTNULL file);
int  SIM_is_interactive(void);

void SIM_command_has_problem(void);
void SIM_command_clear_problem(void);
int  SIM_command_problem_status(void);

#if !defined(GULP)
void VT_source_python_with_args(const char *file, char **args, int argc);
#endif
sim_exception_t SIM_clear_exception(void);
sim_exception_t SIM_get_pending_exception(void);
const char *SIM_last_error(void);

void SIM_quit(int exit_code);

void SIM_set_quiet(int mode);
int SIM_get_quiet(void);
void SIM_set_verbose(int mode);
int SIM_get_verbose(void);
void SIM_load_module(const char *NOTNULL module);
void SIM_unload_module(const char *NOTNULL module);

void VT_load_module_file(const char *NOTNULL file);

int SIM_get_batch_mode(void);

void VT_add_completion(const char *NOTNULL str);
void VT_filename_completion(void);

const char *SIM_version(void);
const char *SIM_version_sub(void);
void SIM_copyright(void);
void SIM_register_copyright(const char *NOTNULL str);
const char *SIM_readme(void);
void SIM_license(void);
const char *SIM_snapshot_date(void);

const char *SIM_lookup_file(const char *file);

void SIM_add_directory(const char *NOTNULL directory, int prepend);
void SIM_clear_directories(void);
attr_value_t SIM_get_directories(void);

const char *SIM_get_simics_home(void);

void VT_disable_command_line(void);
void VT_enable_command_line(void);

/* this is ugly and full of special cases since we don't always want
 * to include Python.h, but we cannot define PyObject twice */
#if defined(GULP_API_HELP)
typedef struct _object PyObject;
#endif
#if defined(GULP_API_HELP) || defined(GULP_PYTHON)
#define _PYOBJECT PyObject
#else  /* ! GULP_xxx */
#define _PYOBJECT struct _object
#endif /* ! GULP_xxx */

/* One argument word of host register size (internal use only) */
typedef unsigned long argword_t;

typedef struct python_interface {
        _PYOBJECT *(*eval_python)(const char *NOTNULL str);
        _PYOBJECT *(*call_python_with_attr)(_PYOBJECT *code,
                                            attr_value_t *value);
        void (*exec_python)(const char *str);
        void (*add_module_dir)(const char *dirname);
        void (*import_module)(const char *modfile, const char *pymod);
        int (*create_branch)(_PYOBJECT *branch);
        int (*interrupt_branch)(int id);
        uintptr_t (*get_cobject_addr)(_PYOBJECT *obj);
        int (*in_main_branch)(void);
        int (*pyobject_to_attr)(_PYOBJECT *pyobject, attr_value_t *attr);
        void (*send_sigint)(void);
        int (*force_release_python_lock)(void);
        void (*force_obtain_python_lock)(int lock_count);
        void (*reset_python_state)(void);
#ifndef GULP
        void (*apply_hap)(const char *signature, _PYOBJECT *f, lang_void *data,
                          conf_object_t *obj, int nwords, argword_t *args,
                          int call_with_obj);
#endif
} python_interface_t;

#define PYTHON_INTERFACE "python"
/* ADD INTERFACE python_interface */

#undef _PYOBJECT

#endif /* _SIMICS_CORE_FRONT_H */
