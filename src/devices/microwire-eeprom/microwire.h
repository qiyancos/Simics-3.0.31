/*
  Copyright 2003-2007 Virtutech AB
 */
/* <add id="microwire_interface_t">
   <insert-until text="// END INTERFACE microwire"/>
   </add> */

#define MICROWIRE_INTERFACE "microwire"

typedef struct {
        void (*set_cs)(conf_object_t *obj, int cs);
        void (*set_sk)(conf_object_t *obj, int sk);
        void (*set_di)(conf_object_t *obj, int di);
        int  (*get_do)(conf_object_t *obj);
} microwire_interface_t;

// END INTERFACE microwire
