/*
 * simics/devs/kbd-interface.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_KBD_INTERFACE_H
#define _SIMICS_DEVS_KBD_INTERFACE_H

/* <add id="kbd_interface_t">

   Interface implemented by keyboard controllers. Used by consoles to send
   keyboard events to the controller.

   The function <fun>keyboard_event()</fun> takes the keyboard controller as
   its first argument <arg>obj</arg>. The <arg>key_up</arg> argument specifies
   whether the event is a key release (1) or a key press (0). The
   <arg>key</arg> argument is the Simics internal keycode, as defined in
   <file>src/extension/common/keycodes.h</file>.

   If the return value is 1 the keyboard controller accepted the event. If
   return value is 0 the keyboard controller did not accept the event, and the
   console should buffer the event until it gets a <fun>keyboard_ready()</fun>
   call from the keyboard controller.

   <insert-until text="// ADD INTERFACE kbd_interface"/>
   </add>
*/

typedef struct {
        int (*keyboard_event)(conf_object_t *obj, int key_up, uint8 key);
} kbd_interface_t;

#define KEYBOARD_INTERFACE "keyboard"
// ADD INTERFACE kbd_interface

/* <add id="kbd_console_interface_t">

   Interface implemented by consoles, to receive notifications from keyboard
   controllers.

   The function <fun>keyboard_ready()</fun>, which takes the console as its
   first argument <arg>obj</arg>, must be called by the keyboard controller
   when it is ready to receive keyboard events again after having rejected a
   keyboard event. Note that this function may be called even though no
   keyboard event has been rejected, and that the console must not assume that
   keyboard controller will accept an event just because the
   <fun>keyboard_ready()</fun> function has been called.

   <fun>keyboard_ready</fun> must not be called while the keyboard controller
   is handling a <fun>keyboard_event()</fun> call.

   <insert-until text="// ADD INTERFACE kbd_console_interface"/>
   </add>
*/

typedef struct {
        void (*keyboard_ready)(conf_object_t *obj);
} kbd_console_interface_t;

#define KEYBOARD_CONSOLE_INTERFACE "keyboard-console"
// ADD INTERFACE kbd_console_interface

/* <add id="mouse_interface_t">
   Interface used to send mouse events to a mouse device. The function
   <fun>mouse_event()</fun> takes the destination device as first argument
   in <arg>obj</arg>. The <arg>xmicro</arg> and <arg>ymicro</arg> arguments
   specified the relative mouse movement in micro-meters. If the mouse
   supports a wheel, the wheel movement is supplied in <arg>z</arg>, as
   number of steps up or down. The last argument <arg>buttons</arg> is a
   bit-mask with the state of the mouse buttons. The mapping of mouse
   buttons to bits is defined in the file
   <file>src/extension/common/keycodes.h</file>.
   <insert-until text="// ADD INTERFACE mouse_interface"/>
   </add>
*/

typedef struct {
        void (*mouse_event)(conf_object_t *obj, int xmicro, int ymicro, int z, int buttons);
} mouse_interface_t;

#define MOUSE_INTERFACE "mouse"
// ADD INTERFACE mouse_interface

#endif /* _SIMICS_DEVS_KBD_INTERFACE_H */
