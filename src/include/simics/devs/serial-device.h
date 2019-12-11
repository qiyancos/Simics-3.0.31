/*
 * simics/devs/serial-device.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_SERIAL_DEVICE_H
#define _SIMICS_DEVS_SERIAL_DEVICE_H

typedef struct {
        int  (*connect_device)(conf_object_t *obj, conf_object_t *dev);
        void (*disconnect_device)(conf_object_t *obj, conf_object_t *dev);
        int (*send_char)(conf_object_t *obj, int id, int ch);
        void (*receive_ready)(conf_object_t *obj, int id);
} serial_link_interface_t;

#define SERIAL_LINK_INTERFACE "serial_link"
// ADD INTERFACE serial_link_interface


/* <add id="serial_device_interface_t">
   Interface used to connect serial devices together. It is typically
   implemented by both devices and text consoles. A character (byte) is
   sent with the <fun>write()</fun> function where <arg>obj</arg> is the
   destination device and the <arg>value</arg> argument is either a data
   byte, or the out-of-band value <tt>TTY_ABORT</tt>.

   The called device will return the number of characters accepted; i.e.
   1 on success and 0 if it could not handle the new byte. If the receiver
   returns 0, it must later call <fun>receive_ready()</fun> in the sender's
   interface to signal that new bytes can be accepted. A serial device should
   handle the case where the <fun>receive_ready()</fun> function is called
   although it has no more bytes to send.

   <insert-until text="// ADD INTERFACE serial_device_interface"/>
   </add>
*/

#define TTY_ABORT   0x100

typedef struct {
        int (*write)(conf_object_t *obj, int value);
        void (*receive_ready)(conf_object_t *obj);
} serial_device_interface_t;

#define SERIAL_DEVICE_INTERFACE "serial-device"
// ADD INTERFACE serial_device_interface

/* <add id="extended_serial_interface_t">
   This interface extends the <tt>SERIAL_DEVICE_INTERFACE</tt> with
   a <fun>write_at()</fun> function. It is similar to the <fun>write()</fun>
   function of the mentioned interface, but accepts an on-screen character
   position. This interface is implemented by text consoles allowing them
   to be connected to text oriented frame buffers, such as VGA in text mode.

   <insert-until text="// ADD INTERFACE extended_serial_interface"/>
   </add>
*/
typedef struct {
        void (*write_at)(conf_object_t *obj,
                         int value, int x, int y, int fg, int bg);
        void (*graphics_mode)(conf_object_t *obj, int in_graphics_mode);
} extended_serial_interface_t;

#define EXTENDED_SERIAL_INTERFACE "extended-serial"
// ADD INTERFACE extended_serial_interface


/* <add id="rs232_device_interface_t">
   Currently Simics internal.

   <insert-until text="// ADD INTERFACE rs232_device_interface"/>
   </add>
*/
typedef struct {
        /* Flow control lines */
        void (*cts)(conf_object_t *obj, int status);
        void (*dsr)(conf_object_t *obj, int status);

        /* Ring indicator */
        void (*ring)(conf_object_t *obj, int status);

        /* Carrier detect */
        void (*carrier)(conf_object_t *obj, int status);

        /* Break */
        void (*got_break)(conf_object_t *obj);

        /* Frame error */
        void (*got_frame_error)(conf_object_t *obj);
} rs232_device_interface_t;

#define RS232_DEVICE_INTERFACE "rs232-device"
// ADD INTERFACE rs232_device_interface

/* <add id="rs232_console_interface_t">
   Currently Simics internal.

   <insert-until text="// ADD INTERFACE rs232_console_interface"/>
   </add>
*/

typedef enum {
        Stop_Bits_1,
        Stop_Bits_1p5,
        Stop_Bits_2
} stop_bits_t;

typedef enum {
        Parity_None,
        Parity_Even,
        Parity_Odd
} parity_mode_t;


typedef struct {
        /* Set line parameters */
        void (*set_baudrate)(conf_object_t *obj, int rate, int commit);
        void (*set_data_bits)(conf_object_t *obj, int bits, int commit);
        void (*set_stop_bits)(conf_object_t *obj, stop_bits_t stop_bits,
                              int commit);
        void (*set_parity_mode)(conf_object_t *obj, parity_mode_t parity_mode,
                                int commit);

        /* Flow control lines */
        void (*set_dtr)(conf_object_t *obj, int status);
        void (*set_rts)(conf_object_t *obj, int status);

        /* Break */
        void (*set_break)(conf_object_t *obj, int status);
} rs232_console_interface_t;

#define RS232_CONSOLE_INTERFACE "rs232-console"
// ADD INTERFACE rs232_console_interface

/* obsolete out-out-band characters */
#define TTY_NO_CHAR 0x101

#endif /* _SIMICS_DEVS_SERIAL_DEVICE_H */
