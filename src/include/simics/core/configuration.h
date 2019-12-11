/*
 * simics/core/configuration.h
 *
  Copyright 1991-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_CORE_CONFIGURATION_H
#define _SIMICS_CORE_CONFIGURATION_H

#include <stdarg.h>

/* <add-type id="interface_list_t def"></add-type> */
typedef struct interface_list interface_list_t;
/* <add-type id="conf attr_data_t"></add-type> */
typedef struct attr_data attr_data_t;
/* <add-type id="conf attr_list_t"></add-type> */
typedef struct attr_list attr_list_t;
/* <add-type id="conf attr_dict_pair_t"></add-type> */
typedef struct attr_dict_pair attr_dict_pair_t;

/* <smaller>
   <add-type id="conf attr_kind_t">
   </add-type>
   </smaller>
 */
typedef enum {
        Sim_Val_Invalid  = 0,
        Sim_Val_String   = 1,
        Sim_Val_Integer  = 2,
        Sim_Val_Floating = 3,
        Sim_Val_List     = 4,
        Sim_Val_Data     = 5,
        Sim_Val_Nil      = 6,
        Sim_Val_Object   = 7,
        Sim_Val_Dict     = 8,
        Sim_Val_Boolean  = 9
} attr_kind_t;

/* <add-type id="conf attr_attr_t"><ndx>attr_attr_t</ndx></add-type> */
typedef enum {
        Sim_Attr_Required         = 0,
        Sim_Attr_Optional         = 1,

        Sim_Attr_Session          = 3,
        Sim_Attr_Pseudo           = 4,

        Sim_Attr_Flag_Mask        = 0xff,

        Sim_Init_Phase_Shift      = 8,
        Sim_Init_Phase_0          = 0 << Sim_Init_Phase_Shift,
        Sim_Init_Phase_1          = 1 << Sim_Init_Phase_Shift,
#ifndef DOC
        Sim_Init_Phase_Bits       = 2,
        Sim_Init_Phase_Mask       = (1 << Sim_Init_Phase_Bits) - 1,

        Sim_Init_Phase_Pre1       = (-1 & Sim_Init_Phase_Mask) << Sim_Init_Phase_Shift,
        Sim_Attr_Class            = 0x8000,
        Sim_Attr_Internal         = 0x10000, /* not included in docs */
#endif

        Sim_Attr_Integer_Indexed  = 0x1000,
        Sim_Attr_String_Indexed   = 0x2000,
        Sim_Attr_List_Indexed     = 0x4000,
        
        Sim_Attr_Persistent       = 0x20000,

        /* set by SIM_register_*_attribute() */
        Sim_Attr_Read_Only        = 0x40000,
        Sim_Attr_Write_Only       = 0x80000

} attr_attr_t;

/* <add id="simics api types">
   <name index="true">set_error_t</name>
   <doc>
   <doc-item name="NAME">set_error_t</doc-item>
   <doc-item name="SYNOPSIS"><smaller><insert id="conf set_error_t"/>
   </smaller></doc-item>
   <doc-item name="DESCRIPTION">
   The <fun>SIM_set_attribute()</fun> family of functions and the set functions
   registered with the <fun>SIM_register_typed_attribute()</fun> family of
   functions return a <type>set_error_t</type> value to report success or
   failure.

   <b>Sim_Set_Ok</b><br/>
   The attribute was successfully set.

   <b>Sim_Set_Need_Integer<br/>
      Sim_Set_Need_Floating<br/>
      Sim_Set_Need_String<br/>
      Sim_Set_Need_List<br/>
      Sim_Set_Need_Dict<br/>
      Sim_Set_Need_Boolean<br/>
      Sim_Set_Need_Data<br/>
      Sim_Set_Need_Object</b><br/>
   The value is of an illegal type for the attribute. Deprecated, use
   <const>Sim_Set_Illegal_Type</const> instead.

   <b>Sim_Set_Object_Not_Found</b><br/>
   The string value does not match any object name. Deprecated, use attributes
   of object type instead of string attributes referring to object names.

   <b>Sim_Set_Interface_Not_Found</b><br/>
   The object value does not implement an interface required by the attribute.

   <b>Sim_Set_Illegal_Value</b><br/>
   The value is of a legal type for the attribute, but outside the legal range.

   <b>Sim_Set_Illegal_Type</b><br/>
   The value is of an illegal type for the attribute.

   <b>Sim_Set_Attribute_Not_Found</b><br/>
   The object has no attribute with the specified name. Should only be returned
   by <fun>SIM_set_attribute()</fun> family of functions, not by attribute set
   functions.

   <b>Sim_Set_Not_Writable</b><br/>
   The attribute is read-only.

   <b>Sim_Set_Ignored</b><br/>
   The value was accepted for backwards compatibility reasons, but was ignored.
   Should only be returned by <fun>set_event_info()</fun> functions registered
   with the <iface>event-poster</iface> interface.
   </doc-item>
   </doc>
   </add> */

/* <add-type id="conf set_error_t"></add-type> */
typedef enum {
        Sim_Set_Ok,
        Sim_Set_Need_Integer,
        Sim_Set_Need_Floating,
        Sim_Set_Need_String,
        Sim_Set_Need_List,
        Sim_Set_Need_Dict,
        Sim_Set_Need_Boolean,
        Sim_Set_Need_Data,
        Sim_Set_Need_Object,
        Sim_Set_Object_Not_Found,
        Sim_Set_Interface_Not_Found,
        Sim_Set_Illegal_Value,
        Sim_Set_Illegal_Type,
        Sim_Set_Illegal_Index,
        Sim_Set_Attribute_Not_Found,
        Sim_Set_Not_Writable,
        Sim_Set_Ignored
} set_error_t;

/**** structs ****/

/* <add-type id="conf attr_list_t">
   </add-type>
 */
struct attr_list {
        integer_t            size;
        struct attr_value   *vector; /* [size] */
};

/* <add-type id="conf attr_dict_t">
   </add-type>
 */
typedef struct {
        integer_t              size;
        struct attr_dict_pair *vector; /* [size] */
} attr_dict_t;

/* <add-type id="conf attr_data_t">
   </add-type>
 */
struct attr_data {
        integer_t            size;
        uint8               *data; /* [size] */
};

/* <add-type id="conf attr_value_t">
   </add-type>
 */
struct attr_value {
        attr_kind_t          kind;
        union {
                const char    *string;   /* Sim_Val_String   */
                integer_t      integer;  /* Sim_Val_Integer  */
                integer_t      boolean;  /* Sim_Val_Boolean  */
                double         floating; /* Sim_Val_Floating */
                attr_list_t    list;     /* Sim_Val_List     */
                attr_dict_t    dict;     /* Sim_Val_Dict     */
                attr_data_t    data;     /* Sim_Val_Data     */
                conf_object_t *object;   /* Sim_Val_Object   */
        } u;
};

/* <add-type id="conf attr_dict_pair_t">
   </add-type>
 */
struct attr_dict_pair {
        struct attr_value   key;
        struct attr_value   value;
};


/* <add id="simics api types">
   <name>attr_value_t, attr_kind_t, attr_list_t, attr_data_t</name>
   <ndx>attr_kind_t</ndx><ndx>attr_value_t</ndx>
   <ndx>attr_list_t</ndx><ndx>attr_data_t</ndx>
   <doc>
   <doc-item name="NAME">
   attr_value_t, attr_kind_t, attr_list_t, attr_data_t</doc-item>
   <doc-item name="SYNOPSIS">
   <insert id="conf attr_value_t"/>
   <insert id="conf attr_kind_t"/>
   <insert id="conf attr_list_t"/>
   <insert id="conf attr_dict_t"/>
   <insert id="conf attr_dict_pair_t"/>
   <insert id="conf attr_data_t"/>
   </doc-item>
   <doc-item name="DESCRIPTION">
   The <i>attr_value_t</i> is the type used for all values in the
   configuration system. All but the <i>Sim_Val_Data</i> kind are stored
   as text when taking checkpoints.

   The following table shows how the different types of values are to
   be interpreted in C and Python, respectively:

   <center>
   <table border="true" long="false">
   <tr><td><b>Kind</b></td>     <td><b>C</b></td>   <td><b>Python</b></td></tr>
   <tr><td>Sim_Val_Invalid</td> <td>n/a</td>     <td>raises exception</td></tr>
   <tr><td>Sim_Val_String</td>  <td>const char *</td>  <td>String</td></tr>
   <tr><td>Sim_Val_Integer</td> <td>integer_t</td>     <td>Integer</td></tr>
   <tr><td>Sim_Val_Boolean</td> <td>integer_t</td>     <td>Bool</td></tr>
   <tr><td>Sim_Val_Floating</td><td>double</td>        <td>Float</td></tr>
   <tr><td>Sim_Val_List</td>    <td>attr_list_t</td>   <td>List</td></tr>
   <tr><td>Sim_Val_Dict</td>    <td>attr_dict_t</td>   <td>Dictionary</td></tr>
   <tr><td>Sim_Val_Data</td>    <td>attr_data_t</td>   <td>Tuple</td></tr>
   <tr><td>Sim_Val_Nil</td>     <td>n/a</td>           <td>None</td></tr>
   </table>
   </center>

   Use the <fun>SIM_make_attr_<var>XXX</var></fun> functions to create
   these data types.
   </doc-item>

   <doc-item name="SEE ALSO">SIM_make_attr_integer, SIM_make_attr_boolean,
   SIM_make_attr_string, SIM_make_attr_floating, SIM_make_attr_object,
   SIM_make_attr_invalid, SIM_make_attr_nil, SIM_make_attr_list,
   SIM_alloc_attr_list, SIM_alloc_attr_dict</doc-item>
   </doc>
   </add> */

/* <add-type id="conf object_vector_t"><ndx>object_vector_t</ndx></add-type> */
struct object_vector {
        conf_object_t **vec;
        int             size;
};

/* <add-type id="conf class_vector_t"><ndx>class_vector_t</ndx></add-type> */
struct class_vector {
        conf_class_t   **vec;
        int              size;
};

typedef struct pre_conf_object_set_t pre_conf_object_set_t;

/* <add-type id="conf class_data_t">
   </add-type>
 */
typedef enum {
        Sim_Class_Kind_Vanilla, /* object is saved at checkpoints */
        Sim_Class_Kind_Session, /* object is saved as part of a
                                 * session only */
        Sim_Class_Kind_Pseudo   /* object is never saved */
} class_kind_t;

/* This is the top level class. All objects use this base structure
   (but may add elements). */

/* <add id="simics api types">
   <name index="true">conf_object_t</name>
   <doc>
   <doc-item name="NAME">conf_object_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller><insert id="conf conf_object_t"/>
   </smaller></doc-item>
   <doc-item name="DESCRIPTION">
   All classes must inherit the <type>conf_object_t</type> type by
   including it first in the subclass structure. Always initialize the
   <type>conf_object_t</type> part of an object structure using the
   <fun>SIM_object_constructor()</fun> function.
   </doc-item>
   </doc>
   </add> */

/* <add-type id="conf conf_object_t"></add-type> */
struct conf_object {
        conf_class_t *class_data;  /* class data */
        const char *name;          /* instance name */
        struct conf_object *queue; /* queue */
        lang_void *object_data;    /* internal to class implementation */
        int object_id;             /* deprecated, do not use */
        int configured;            /* set when configuration ready */
};

/* <add id="callback_interface_t">
   Internal interface. Do not use.

   <insert-until text="// ADD INTERFACE callback_interface"/>
   </add> */
typedef struct {
        void (*callback)(conf_object_t *);
} callback_interface_t;

#define CALLBACK_INTERFACE "_callback"
// ADD INTERFACE callback_interface

/* <add id="checkpoint_interface_t">
   The <fun>save</fun> function in this interface is called when a checkpoint
   is saved, right before the attributes of an object is read. If defined,
   it should prepare the object for checkpointing, saving any state to
   <param>path</param> that is not directly included in the attributes.
   Errors are signalled through exceptions.

   The <fun>finish</fun> function is called after the checkpoint has been
   saved. If <arg>success</arg> is nonzero, the checkpoint was saved
   successfully; otherwise there was a failure. This permits the object to
   clean up temporary data structures and files in either case.

   The function <fun>has_persistent_data</fun>, if implemented, should return
   0 if the object only has volatile attributes, 1 otherwise. This overrides
   <const>Sim_Attr_Persistent</const> on individual attributes.

   <insert-until text="// ADD INTERFACE checkpoint_interface"/>
   </add> */
typedef struct {
        void (*save)(conf_object_t *obj, const char *path);
        void (*finish)(conf_object_t *obj, int success);
        int (*has_persistent_data)(conf_object_t *obj);
} checkpoint_interface_t;

#define CHECKPOINT_INTERFACE "checkpoint"
// ADD INTERFACE checkpoint_interface

typedef struct parse_object parse_object_t;

/* <add-type id="conf get_attr_t">
   </add-type>
 */
typedef attr_value_t (*get_attr_t)(lang_void *ptr,
                                   conf_object_t *obj,
                                   attr_value_t *idx);

/* <add-type id="conf get_class_attr_t">
   </add-type>
 */
typedef attr_value_t (*get_class_attr_t)(lang_void *ptr,
                                         conf_class_t *c,
                                         attr_value_t *idx);

/* <add-type id="conf set_attr_t">  </add-type> */
typedef set_error_t (*set_attr_t)(lang_void *ptr,
                                  conf_object_t *obj,
                                  attr_value_t *val,
                                  attr_value_t *idx);

/* <add-type id="conf set_class_attr_t">
   </add-type>
 */
typedef set_error_t (*set_class_attr_t)(lang_void *ptr,
                                        conf_class_t *c,
                                        attr_value_t *val,
                                        attr_value_t *idx);

typedef void interface_t;

/* <add id="simics api types">
   <name>class_data_t, class_kind_t</name>
   <ndx>class_data_t</ndx><ndx>class_kind_t</ndx>
   <doc>
   <doc-item name="NAME">class_data_t, class_kind_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="conf class_data_t"/>
   </smaller></doc-item>
   <doc-item name="DESCRIPTION">
   The <type>class_data_t</type> type is used when a new class is
   registered. The only mandatory field is <var>new_instance</var>.
   Make sure that uninitialized fields are set to zero before the
   structure is passed to <fun>SIM_register_class()</fun>. The optional
   <fun>finalize_instance</fun> function is called when all attributes
   have been initialized in an object, and in all other objects
   that are created at the same time.
   </doc-item>
   </doc>
   </add> */
/* <add-type id="conf class_data_t">
   </add-type>
 */
typedef struct class_data {
        conf_object_t *(*new_instance)(parse_object_t *parse_obj);
        int (*delete_instance)(conf_object_t *obj);
        void (*finalize_instance)(conf_object_t *obj);
        attr_value_t (*default_get_attr)(const char *name,
                                         conf_object_t *obj,
                                         attr_value_t *idx);
        set_error_t (*default_set_attr)(const char *name,
                                        conf_object_t *obj,
                                        attr_value_t *val,
                                        attr_value_t *idx);
        conf_class_t         *parent;
        const char           *description;
        class_kind_t          kind;
} class_data_t;

/* This is only a small part of the real conf_class_t structure, left here for
   backward compability. */
#if !defined(SIMICS_CORE)
struct conf_class {
        const char *name;
};
#endif

/**** functions ****/

void SIM_read_configuration(const char *NOTNULL file);

void SIM_set_configuration(attr_value_t conf);

pre_conf_object_set_t *VT_get_configuration(const char *NOTNULL file);

void SIM_add_configuration(pre_conf_object_set_t *NOTNULL object_list,
                           const char *file);

void SIM_flush_all_caches(void);

int SIM_initial_configuration_ok(void);

void VT_finalize_object(conf_object_t *NOTNULL obj);

const char *SIM_get_class_name(const conf_class_t *NOTNULL class_data);

/* Write configuration to file. Returns error code on failure (0 == ok). */
int SIM_write_configuration_to_file(const char *NOTNULL file);

int VT_write_configuration_persistent(const char *NOTNULL file);
int VT_write_configuration_objects(const char *NOTNULL file,
                                   attr_value_t obj_list);

/* will return 1 while getting persistent attributes only */
int VT_is_saving_persistent_data(void);

void VT_save_preferences(void);

/* Register new class. Returns NULL on failure. */
conf_class_t *SIM_register_class(const char *NOTNULL name,
                                 class_data_t *NOTNULL class_data);
void SIM_register_class_alias(const char *NOTNULL alias,
                              const char *NOTNULL name);

/* Return error code on failure (0 == ok). */

int SIM_register_interface(conf_class_t *NOTNULL cls,
                           const char *NOTNULL name,
                           interface_t *NOTNULL iface);

int SIM_register_port_interface(conf_class_t *NOTNULL cls,
                                const char *NOTNULL name,
                                interface_t *NOTNULL iface,
                                const char *NOTNULL instance_name,
                                const char *desc);

void VT_describe_interface(const char *NOTNULL name,
                           const char *NOTNULL desc);

/* Register attribute. Returns non-zero on failure. */
int SIM_register_attribute(conf_class_t *NOTNULL cls, const char *NOTNULL name,
                           get_attr_t get_attr, lang_void *user_data_get,
                           set_attr_t set_attr, lang_void *user_data_set,
                           attr_attr_t attr,
                           const char *desc);

/* Register a typed attribute (with an eventual typed index). */
int SIM_register_typed_attribute(
        conf_class_t *NOTNULL cls, const char *NOTNULL name,
        get_attr_t get_attr, lang_void *user_data_get,
        set_attr_t set_attr, lang_void *user_data_set,
        attr_attr_t attr, const char *type, const char *idx_type,
        const char *desc);

/* Register attribute. Returns non-zero on failure. */
int SIM_register_class_attribute(
        conf_class_t *NOTNULL cls, const char *NOTNULL name,
        get_class_attr_t get_attr, lang_void *user_data_get,
        set_class_attr_t set_attr, lang_void *user_data_set,
        attr_attr_t attr,
        const char *desc);

int SIM_register_typed_class_attribute(
        conf_class_t *NOTNULL cls, const char *NOTNULL name,
        get_class_attr_t get_attr, lang_void *user_data_get,
        set_class_attr_t set_attr, lang_void *user_data_set,
        attr_attr_t attr, const char *type, const char *idx_type,
        const char *desc);

void SIM_ensure_partial_attr_order(conf_class_t *cls, const char *attr1,
                                   const char *attr2);

void SIM_attribute_error(const char *NOTNULL msg);

/* Get attribute attribute. */
attr_attr_t SIM_get_attribute_attributes(conf_class_t *NOTNULL cls,
                                         const char *NOTNULL attr);

/* Change attribute of attribute. */
int SIM_change_attribute_attribute(conf_class_t *NOTNULL cls,
                                   const char *NOTNULL name, attr_attr_t attr);

/* return 1 if the class has an attribute with name attr */
int SIM_class_has_attribute(conf_class_t *NOTNULL cls,
                            const char *NOTNULL attr);

/* Objects that store configuration data in files need to get a
   filename prefix with this function */
const char *SIM_get_configuration_file_prefix(void);

/* Get registered class (returns NULL if class not found). */
conf_class_t *SIM_get_class(const char *NOTNULL name);
const char *VT_get_class_description(conf_class_t *NOTNULL cls);

attr_value_t VT_get_all_known_classes(void);

/* Get object (returns NULL if object not found). */
conf_object_t *SIM_get_object(const char *NOTNULL name);

/* Get interface from object (returns NULL if interface not
   implemented by object). */
interface_t *SIM_get_interface(const conf_object_t *NOTNULL obj,
                               const char *NOTNULL name);
interface_t *SIM_get_class_interface(const conf_class_t *NOTNULL cls,
				     const char *NOTNULL name);

interface_t *SIM_get_port_interface(const conf_object_t *NOTNULL obj,
                                    const char *NOTNULL name,
                                    const char *instance_name);

interface_t *SIM_get_class_port_interface(const conf_class_t *NOTNULL cls,
                                          const char *NOTNULL name,
                                          const char *instance_name);

attr_value_t VT_get_attributes(conf_class_t *NOTNULL cls);
attr_value_t VT_get_interfaces(conf_class_t *NOTNULL cls);
attr_value_t VT_get_port_interfaces(conf_class_t *NOTNULL cls);

/* Return vector with all objects. */
attr_value_t SIM_get_all_objects(void);
attr_value_t SIM_get_all_classes(void);
attr_value_t VT_get_all_instances(conf_class_t *NOTNULL cls);

/* deprecated, do not use */
conf_object_t *SIM_new_object(conf_class_t *NOTNULL cls,
                              const char *NOTNULL name);

conf_object_t *SIM_create_object(conf_class_t *NOTNULL cls,
                                 const char *NOTNULL name,
                                 attr_value_t attrs);
void VT_rename_object(conf_object_t *NOTNULL obj, const char *NOTNULL newname);

conf_object_t *SIM_alloc_conf_object(parse_object_t *NOTNULL pa);
conf_object_t *VT_alloc_log_object(parse_object_t *NOTNULL pa);

/* Delete object. */
int SIM_delete_object(conf_object_t *NOTNULL obj);

/* internal test function, do not use */
void DBG_delete_configuration(void);

/* Get attribute from object. */
attr_value_t SIM_get_attribute(conf_object_t *NOTNULL obj,
                               const char *NOTNULL name);
attr_value_t SIM_get_attribute_idx(conf_object_t *NOTNULL obj,
                                   const char *NOTNULL name,
                                   attr_value_t *NOTNULL index);

/* Get attribute from class. */
attr_value_t SIM_get_class_attribute(conf_class_t *NOTNULL cls,
                                     const char *NOTNULL name);
attr_value_t SIM_get_class_attribute_idx(conf_class_t *NOTNULL cls,
                                         const char *NOTNULL name,
                                         attr_value_t *NOTNULL index);

/* Set attribute in object. Returns error code on failure (0 == ok). */
set_error_t SIM_set_attribute(conf_object_t *NOTNULL obj,
                              const char *NOTNULL name,
                              attr_value_t *NOTNULL value);

set_error_t SIM_set_attribute_idx(conf_object_t *NOTNULL obj,
                                  const char *NOTNULL name,
                                  attr_value_t *NOTNULL index,
                                  attr_value_t *NOTNULL value);

/* Set attribute in class. Returns error code on failure (0 == ok). */
set_error_t SIM_set_class_attribute(conf_class_t *NOTNULL cls,
                                    const char *NOTNULL name,
                                    attr_value_t *NOTNULL value);

set_error_t SIM_set_class_attribute_idx(conf_class_t *NOTNULL cls,
                                        const char *NOTNULL name,
                                        attr_value_t *NOTNULL index,
                                        attr_value_t *NOTNULL value);

/* Free all linked objects (in lists) */
#if !defined(GULP)
void SIM_free_attribute(attr_value_t value);
#endif

/* Constructor for the root class */
void SIM_object_constructor(conf_object_t *NOTNULL obj,
                            parse_object_t *NOTNULL pobj);

int SIM_object_is_processor(conf_object_t *NOTNULL obj);

int DBG_check_typing_system(const char *type, attr_value_t *NOTNULL val);

/* documentation stuff */

attr_value_t VT_get_class_info(char *NOTNULL, int, int);
attr_value_t VT_get_interface_info(char *NOTNULL, int, int);
attr_value_t VT_get_all_attributes(char *NOTNULL, int, int);

/* attr_value_t constructors */

#if !defined(GULP)

FORCE_INLINE attr_value_t
SIM_make_attr_integer(integer_t i)
{
        attr_value_t ret;
        ret.kind = Sim_Val_Integer;
        ret.u.integer = i;
        return ret;
}

FORCE_INLINE attr_value_t
SIM_make_attr_boolean(integer_t i)
{
        attr_value_t ret;
        ret.kind = Sim_Val_Boolean;
        ret.u.boolean = i ? 1 : 0;
        return ret;
}

FORCE_INLINE attr_value_t
SIM_make_attr_string(const char *str)
{
        attr_value_t ret;
        ret.kind = str ? Sim_Val_String : Sim_Val_Nil;
        ret.u.string = str;
        return ret;
}

FORCE_INLINE attr_value_t
SIM_make_attr_floating(double d)
{
        attr_value_t ret;
        ret.kind = Sim_Val_Floating;
        ret.u.floating = d;
        return ret;
}

FORCE_INLINE attr_value_t
SIM_make_attr_object(conf_object_t *obj)
{
        attr_value_t ret;
        ret.kind = obj ? Sim_Val_Object : Sim_Val_Nil;
        ret.u.object = obj;
        return ret;
}

FORCE_INLINE attr_value_t
SIM_make_attr_invalid(void)
{
        attr_value_t ret;
        ret.kind = Sim_Val_Invalid;
        return ret;
}

FORCE_INLINE attr_value_t
SIM_make_attr_nil(void)
{
        attr_value_t ret;
        ret.kind = Sim_Val_Nil;
        return ret;
}

attr_value_t SIM_make_attr_list_vararg(int length, va_list va);
attr_value_t SIM_make_attr_list(int length, ...);
attr_value_t SIM_alloc_attr_list(int length);
attr_value_t SIM_make_attr_data(integer_t size, void *data);
attr_value_t SIM_alloc_attr_dict(int length);

int SIM_ascanf(attr_value_t *NOTNULL list, const char *NOTNULL fmt, ...);

#endif /* !GULP */

/* <add id="symtable_interface_t">
This is a collection of API calls for the symtable module, providing
symbolic debugging support of the target machine.
<pre>
typedef struct symtable_interface {
        attr_value_t (*eval_sym)(processor_t *cpu,
                                 const char *expr,
                                 attr_value_t *frame,
                                 const char *format);
</pre>
Evaluates the symbolic expression <i>expr</i> in the given stack frame on the
specified cpu. The result is the list (<i>value</i>, <i>type</i>) where
<i>value</i> depends on the format, and <i>type</i> is a string describing
the type of the result. If <i>format</i> is "v", then <i>value</i> is the
value of the result as a string or integer; otherwise it is a human-readable
string representation of the result. The only operators allowed in <i>expr</i>
are casts, indirection and member selection (no arithmetic).
<pre>
        attr_value_t (*stack_trace)(processor_t *cpu,
                                    int maxframes);
</pre>
Does a stack trace in the current context of the specified cpu, and returns
a list of stack frames (at most <i>maxframes</i>). Each stack frame is
in turn a list of state variables, suitable for passing to <tt>eval_sym</tt>
above, but has no defined structure other than that the first element
is the program counter. This program counter points to the next
instruction to be executed in respective frame.
<pre>
        attr_value_t (*fun_args)(processor_t *cpu,
                                 attr_value_t *frame);
</pre>
Given a stack frame, returns a list of the formal and actual parameters
to the function where that frame is currently executing. Each element of
the returned list is a list on the form (<i>name</i>, <i>value</i>).
<pre>
        attr_value_t (*source_profile)(conf_object_t *symtable,
                                       conf_object_t *profile);
</pre>
Find the corresponding source lines for profile values and return a list
on the form ((<i>source-file</i>, (<i>line</i>, <i>value</i>) ...) ...).
<pre>
} symtable_interface_t;
</pre>
</add>
*/

/* ADD INTERFACE symtable_interface */
/* Note: This struct must be kept in sync with the documentation above
   manually */
typedef struct symtable_interface {
        attr_value_t (*eval_sym)(conf_object_t *NOTNULL cpu,
                                 const char *NOTNULL expr,
                                 attr_value_t *NOTNULL frame,
                                 const char *format);
        attr_value_t (*stack_trace)(conf_object_t *NOTNULL cpu, int maxframes);
        attr_value_t (*fun_args)(conf_object_t *NOTNULL cpu,
                                 attr_value_t *NOTNULL frame);
        attr_value_t (*source_profile)(conf_object_t *NOTNULL symtable,
                                       conf_object_t *NOTNULL profile);
} symtable_interface_t;

#define SYMTABLE_INTERFACE "symtable"

/* The frontend server interface is implemented in the frontend-server module */
typedef struct frontend_server_interface {
        void (*init_control_pipes)(const char *NOTNULL s);
        int (*have_mi_frontend)(void);
        void (*notify_break_on_breakpoint)(integer_t break_id);
        void (*send_control_message)(attr_value_t *NOTNULL val);
        void (*send_checkpoint_progress_message)(const char *NOTNULL msg,
                                                 conf_object_t *obj);
} frontend_server_interface_t;

#define FRONTEND_SERVER_INTERFACE "_frontend_server"

#if !defined(GULP)
typedef struct {
        const char *file;
        const char *fun;
        int line;
} source_line_t;

struct simcontext;

/* Instruction masks of the form expected by the global breakpoint attribute.
   Unused parts are NULL. */
typedef struct {
        const char *mask;
        const char *pattern;
        const char *prefix;
} instr_mask_t;

/* <add id="symtable_step_interface_t">

   Symtable support for source-line stepping functions.

   <insert-until text="// ADD INTERFACE symtable_step_interface"/>
   </add>
*/
typedef struct {
        int (*get_return_address)(struct simcontext *ctx,
                                  conf_object_t *cpu_obj,
                                  logical_address_t *ret_addr);
        logical_address_t (*get_stack_pointer)(struct simcontext *ctx,
                                               conf_object_t *cpu_obj);
        int (*get_source_line)(struct simcontext *ctx,
                               logical_address_t addr,
                               source_line_t *s);
        int (*get_address_of_line)(struct simcontext *ctx,
                                   conf_object_t *cpu_obj, source_line_t s,
                                   void (*f)(void *user_data,
                                             logical_address_t start,
                                             logical_address_t end),
                                   void *user_data);
        int (*instr_is_call)(struct simcontext *ctx,
                             conf_object_t *cpu_obj,
                             logical_address_t addr,
                             logical_address_t *ret_addr);
        instr_mask_t **(*call_instr_masks)(struct simcontext *ctx);
        int (*instr_is_return)(struct simcontext *ctx,
                               conf_object_t *cpu_obj,
                               logical_address_t addr,
                               logical_address_t *ret_addr);
        instr_mask_t **(*return_instr_masks)(struct simcontext *ctx);
        int (*last_instr_before_call)(struct simcontext *ctx,
                                      conf_object_t *cpu_obj,
                                      logical_address_t *ret_addr);
        int (*last_instr_before_return)(struct simcontext *ctx,
                                        conf_object_t *cpu_obj,
                                        logical_address_t *ret_addr);
        void (*for_all_lineinfo)(struct simcontext *ctx,
                                 conf_object_t *cpu_obj,
                                 void (*f)(void *user_data,
                                           logical_address_t start,
                                           logical_address_t end),
                                 void *user_data);
        logical_address_t (*call_addr_from_ret_addr)(
                struct simcontext *ctx, logical_address_t ret_addr);
        int (*call_has_delay_slot)(struct simcontext *ctx,
                                   logical_address_t call_addr,
                                   logical_address_t *delay_slot);
        int (*has_delayed_return)(struct simcontext *ctx);
} symtable_step_interface_t;
#define SYMTABLE_STEP_INTERFACE "_symtable_step"
// ADD INTERFACE symtable_step_interface

#endif /* !GULP */

/* <add id="tracker_interface_t">

   <note>This interface is not supported, and may change in the future.</note>

   Interface for trackers. This is a generic interface implemented by all
   trackers, regardless of what it is that they track.

   Typically, the things being tracked (the <i>trackees</i>) are processes. The
   tracker keeps track of what trackee is active on what processor; this is
   useful when one wants to observe one specific trackee and disregard the
   others. Trackees are identified by a unique integer called a <i>tid</i>
   (Trackee ID).

   <insert-until text="// ADD INTERFACE tracker_interface"/>

   <fun>active_trackee</fun> returns the tid of the trackee that is currently
   active on the given processor. <fun>describe_trackee</fun> returns a short
   string that describes the trackee with the given tid.

   <fun>processor_list</fun> returns the set of processors being watched by the
   tracker. <fun>add_processor</fun> and <fun>remove_processor</fun> add and
   remove a processor from this set, respectively.

   <fun>supports_processor</fun> returns true if trackers of this type support
   processors of the given class, and false otherwise.

   Before using the tracker, call <fun>activate</fun>. When you are done with
   it, call <fun>deactivate</fun>.

   In addition to these interface functions, the tracker should trigger the
   <fun>Core_Trackee_Active</fun> hap when the active trackee changes for a
   processor.

   </add>
*/
typedef struct {
        integer_t (*active_trackee)(conf_object_t *NOTNULL tracker,
                                    conf_object_t *NOTNULL cpu);
        const char *(*describe_trackee)(conf_object_t *NOTNULL tracker,
                                        integer_t tid);
        attr_value_t (*processor_list)(conf_object_t *NOTNULL tracker);
        void (*add_processor)(conf_object_t *NOTNULL tracker,
                              conf_object_t *NOTNULL cpu);
        void (*remove_processor)(conf_object_t *NOTNULL tracker,
                                 conf_object_t *NOTNULL cpu);
        int (*supports_processor)(const char *NOTNULL classname);
        int (*activate)(conf_object_t *NOTNULL tracker);
        int (*deactivate)(conf_object_t *NOTNULL tracker);
} tracker_interface_t;
#define TRACKER_INTERFACE "tracker"
// ADD INTERFACE tracker_interface

/* <add id="tracker_settings_interface_t">

   <note>This interface is not supported, and may change in the future.</note>

   This interface is a way of giving names to sets of attribute values for
   process trackers. For example, a Linux process tracker might have a few
   integer attributes that store memory offsets that differ between different
   versions of the operating system. Rather than forcing the user to look up
   the values appropriate to her version and setting the attributes manually,
   the settings for the different supported versions can be given names.

   <insert-until text="// ADD INTERFACE tracker_settings_interface"/>

   <fun>settings_id_list</fun> returns a list of strings. Each string is the ID
   of a set of attributes (for example "linux-4.7.11").

   <fun>describe_settings</fun> returns a human-readable description of a
   settings ID (for example, "linux-4.7.11" might give "Linux 4.7.11").

   <fun>use_settings</fun> sets the attributes to the values in the named set.
   It returns true on success, false on error (the typical error would be an
   invalid settings ID name).

   </add>
*/
typedef struct {
        attr_value_t (*settings_id_list)(void);
        const char *(*describe_settings)(const char *NOTNULL settings_id);
        int (*use_settings)(conf_object_t *NOTNULL tracker,
                            const char *NOTNULL settings_id);
} tracker_settings_interface_t;
#define TRACKER_SETTINGS_INTERFACE "tracker_settings"
// ADD INTERFACE tracker_settings_interface

/* <add-type id="trackee_unix_type_t def">
   </add-type>
 */
typedef enum {
        Sim_Trackee_Invalid = 0,
        Sim_Trackee_Kernel,
        Sim_Trackee_Process
} trackee_unix_type_t;

/* <add id="tracker_unix_interface_t">

   <note>This interface is not supported, and may change in the future.</note>

   Interface for trackers. This is an interface implemented by process trackers
   for UNIX-like operating systems. Such trackers should also implement the
   basic tracker interface.

   <insert-until text="// ADD INTERFACE tracker_unix_interface"/>

   <fun>trackee_type</fun> returns the type of the trackee that has the given
   tid. The types are defined by the following <tt>enum</tt>:

   <insert id="trackee_unix_type_t def"/>

   <fun>tid_to_pid</fun> and <fun>pid_to_tid</fun> map tids to pids and pids to
   tids.

   In addition to these interface functions, the tracker should trigger the
   <fun>Core_Trackee_Exec</fun> hap when a process calls the <tt>exec</tt>
   syscall.

   </add>
*/
typedef struct {
        trackee_unix_type_t (*trackee_type)(conf_object_t *NOTNULL tracker,
                                            integer_t tid);
        integer_t (*tid_to_pid)(conf_object_t *NOTNULL tracker, integer_t tid);
        integer_t (*pid_to_tid)(conf_object_t *NOTNULL tracker, integer_t pid);
} tracker_unix_interface_t;
#define TRACKER_UNIX_INTERFACE "tracker_unix"
// ADD INTERFACE tracker_unix_interface

/*
   <add id="simics api types">
   <name index="true">log_type_t</name>
   <doc>
   <doc-item name="NAME">log_type_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="log_type_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">
   This type defines different log types that are used by the logging
   facility to categorise messages.
   </doc-item>
   </doc>
   </add>
*/

/* <add-type id="log_type_t def">
   </add-type>
 */
typedef enum {
        Sim_Log_Info,           // Normal informational message
        Sim_Log_Error,          // Simics error
        Sim_Log_Undefined,      // use of undefined target behavior
        Sim_Log_Spec_Violation, // target program violates the specification
        Sim_Log_Target_Error,   // error state in target (not in Simics)
        Sim_Log_Unimplemented,  // not implemented in Simics
        Sim_Log_Num_Types       // Do not use
} log_type_t;

#define MIN_LOG_LEVEL 1
#define MAX_LOG_LEVEL 4

/* <add-type id="io_trace_t def"></add-type> */
typedef struct io_trace io_trace_t;
/* <add-type id="io_trace_log_t def"></add-type> */
typedef struct io_trace_log io_trace_log_t;

/* <add id="simics api types">
   <name index="true">log_object_t</name>
   <doc>
   <doc-item name="NAME">log_object_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller><insert id="conf log_object_t"/>
   </smaller></doc-item>
   <doc-item name="DESCRIPTION">
   The <type>log_object_t</type> structure directly inherits
   <type>conf_object_t</type>, and it extends that class with logging
   functionality. Use <fun>SIM_log_constructor()</fun> to initialize
   new instances. The constructor automatically adds attributes to
   save and restore the members in the <type>log_object_t</type>
   structure.

   Since the internal representation of this structure may change
   between releases, classes using the structure should not inspect
   the members directly (except for obj), but rather use the attributes.
   New entries should be added with the <fun>SIM_log_message()</fun> function.
   From C/C++ the <fun>SIM_log_...</fun> helper functions are recommended.
   </doc-item>
   <doc-item name="SEE ALSO">SIM_log_constructor, SIM_log_message</doc-item>
   </doc>
   </add> */

/* <add-type id="conf log_object_t"></add-type> */
struct log_object {
        conf_object_t   obj;

        uint32          access_cnt;    /* number of IO transactions
                                        * performed  */
        int             access_active; /* set while an access is in
                                        * progress  */

        io_trace_log_t *active_trace;  /* temporary log list during
                                        * the access  */

        io_trace_t     *trace_buffer;
        int             trace_next;
        int             trace_wrap;
        int             trace_size;

        int             log_level;
        int             group_mask;
        int             type_mask;
};

#define LOG_OBJECT_INTERFACE "log_object"
// ADD INTERFACE log_object_interface

/* <add id="log_object_interface_t">
   <ndx>log_object</ndx>
   </add> */
typedef struct log_object_interface {
        int dummy;
} log_object_interface_t;

struct parse_object;

void SIM_log_constructor(log_object_t *NOTNULL log,
                         struct parse_object *NOTNULL obj);
void SIM_log_register_groups(conf_class_t *NOTNULL cls,
                             const char **NOTNULL names);
void SIM_log_message(conf_object_t *NOTNULL obj,
                     int level,
                     int group_ids,
                     log_type_t log_type,
                     const char *NOTNULL message);

/* <add id="component_interface_t">
   Internal interface. Do not use.
   </add>
*/
typedef struct component_interface {
        int dummy;
} component_interface_t;
#define COMPONENT_INTERFACE "component"

#endif /* _SIMICS_CORE_CONFIGURATION_H */
