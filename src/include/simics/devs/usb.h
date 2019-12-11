/*
 * simics/devs/usb.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_USB_H
#define _SIMICS_DEVS_USB_H

#include <simics/util/dbuffer.h>

/* <add id="simics api types">
   <name index="true">usb_transfer_t</name>
   <doc>
   <doc-item name="NAME">usb_transfer_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="usb_transfer_t"/></doc-item>
   <doc-item name="DESCRIPTION">
   <insert id="usb_transfer_t description"/>
   </doc-item>
   </doc>
   </add>

   <add id="usb_transfer_t description">

   The <type>usb_transfer_t</type> type is independent of USB host and
   USB device implementations and is used for sending data over USB.

   There are two fields to identify the pipe: <var>function_address</var> is
   the function/device address for the target USB device;
   <var>endpoint_number</var> specifies the endpoint number.

   The type of transfer is defined using the <var>type</var> field. The type is
   either control, bulk, interrupt, or isochronous. The
   <var>u.control_request</var> field is only valid for control transfers. It
   contains the information that would be in the setup packet of a control
   transfer. The <var>u.periodic_time</var> field is only valid for periodic
   transfers, i.e., interrupt and isochronous transfers. It specifies the
   minimum response time for a transfer expected by the USB host. A USB device
   do not need to fulfill the expectation. It is merely a way to tell the USB
   device how to keep the timing specified in the periodic list scheduling.

   The <var>usb_direction</var> field specifies the direction of the data in
   the USB transfer. Only the actual data packet is used to specify the
   direction, even if a real transfer consists of a mix of SETUP/OUT/IN/STATUS
   packets. <const>USB_Direction_None</const> means that the transfer does not
   contain any data, for example, in <type>Set_Address</type> control
   transfers. <var>size</var> is the the number of bytes the USB host can
   receive for IN transfers and the number of bytes sent for OUT
   transfers. <var>buf</var> contains the IN or OUT data. Note that <i>buf</i>
   can contain data for several data packets concatenated together. The
   endpoint descriptors in USB host and USB device define the maximum packet
   size for the pipe, but there is no limitation in Simics.

   The <var>status</var> field contains the status for the transfer. The status
   is typically only set by the USB device. The USB host does not set the
   status field when it has completed an IN transfer.

   </add>

   <add id="usb_transfer_t">
   <name>usb_transfer_t</name>
   <insert-until text="// JDOCU INSERT-UNTIL usb_transfer_t"/>
   </add>
 */
typedef enum {
        USB_Transfer_Completed,
        USB_Transfer_Not_Ready
} usb_transfer_completion_t;

typedef enum {
        USB_Direction_None,
        USB_Direction_In,
        USB_Direction_Out
} usb_direction_t;

typedef enum {
        USB_Status_Undef,
        USB_Status_Ack,
        USB_Status_Nak,
        USB_Status_Stall
} usb_status_t;

typedef enum {
        USB_Type_Control,
        USB_Type_Interrupt,
        USB_Type_Isochronous,
        USB_Type_Bulk
} usb_type_t;

typedef enum {
        USB_Speed_Low,
        USB_Speed_Full,
        USB_Speed_High
} usb_speed_t;

typedef struct {
        uint8  bmRequestType;
        uint8  bRequest;
        uint16 wValue;
        uint16 wIndex;
        uint16 wLength;
} usb_device_request_t;

typedef struct {
        /* Endpoint/function specific information */
        uint8                 function_address;
        uint8                 endpoint_number;
        /* Type specific information */
        usb_type_t            type;
        union {
                usb_device_request_t   control_request;
                nano_secs_t            periodic_time;
        } u;
        /* Data specific */
        usb_direction_t       direction;
        int                   size;
        dbuffer_t             *buf;
        /* Status */
        usb_status_t          status;
} usb_transfer_t;

// JDOCU INSERT-UNTIL usb_transfer_t

/*
   <add id="usb_device_interface_t">
   <name>usb_device_interface_t</name>

   The <iface>usb_device_interface_t</iface> interface is implemented
   by all USB devices. It is used by the USB host to communicate with
   the USB devices.

   <pre/>
   <insert id="usb_device_interface_t def"/>
   <pre/>

   The <fun>submit_transfer()</fun> function is used by the USB host controller
   to send a new transfer to a USB device. Transfers are the basic means of
   communication between the USB host controller and the USB devices. A
   transfer contains all information needed to handle control, bulk, interrupt,
   and isochronous transfers. A transfer to a USB device simply moves the
   control from the the USB host to the USB device. The USB device can then
   decide when to send back any useful data to the USB host.  The USB device
   receives a pointer to the transfer to handle. It can either handle the
   transfer immediately or send the transfer back later using the
   <fun>complete_transfer()</fun> function in the
   <iface>usb_interface_t</iface> interface, which is implemented by the USB
   host.

   The USB device must return <const>USB_Transfer_Completed</const> when it
   handles the transfer immediately, i.e., it has filled the required fields in
   the transfer structure. The USB device must return
   <const>USB_Transfer_Not_Ready</const> for unfinished transfers, i.e., the
   USB device does not have any interesting data to deliver at this point. The
   isochronous and interrupt transfers contain a field indicating how long time
   the USB host expects the USB device to wait before returning the
   transfer. Note that it is just an indication on how often this transfer is
   scheduled in the periodic list and USB devices can complete the transfers at
   any time. A value of <tt>0</tt> means that the USB host does have any
   expectations about the return time.

   The <fun>abort_transfer()</fun> function tells the USB device to abort a
   transfer previously issued by the USB host. The USB device should not call
   the <fun>complete_transfer()</fun> function for a request that has been
   aborted.

   The <fun>reset()</fun> function is used by the USB host to reset the USB
   device.

   The USB host expects the device to return the same transfer pointer it
   received when completing, i.e., the transfer pointer is used to identify
   uniquely a transfer.

   </add>

   <add-type id="usb_device_interface_t def">
   </add-type>
 */
typedef struct {
        usb_transfer_completion_t (*submit_transfer)(conf_object_t *dev_obj,
                                                     usb_transfer_t *transfer);
        void (*abort_transfer)(conf_object_t *dev_obj,
                               usb_transfer_t *transfer);
        void (*reset)(conf_object_t *dev_obj);
} usb_device_interface_t;

#define USB_DEVICE_INTERFACE "usb_device"


/*
   <add id="usb_interface_t">
   <name>usb_interface_t</name>

   The <iface>usb_interface_t</iface> interface is implemented by all
   USB hosts. USB devices use the interface to communicate with the
   USB host.

   <pre/>
   <insert id="usb_interface_t def"/>
   <pre/>

   The <fun>connect_device()</fun> function is called by the USB device to
   connect to the USB. The host returns the physical port to which the device
   is connected, or <tt>-1</tt> on connection error (for example, if all ports
   are occupied). Parameter to <fun>connect_device()</fun> is the maximum
   data speed for the USB device.

   The <fun>disconnect_device()</fun> function is called by the USB device when
   it wants to disconnect from the USB. The host returns <tt>0</tt> on success.

   The <fun>complete_transfer()</fun> function is called by a USB device when
   it has completed a transfer. Refer to the <iface>usb_device_t</iface>
   interface documentation to know more about how a transfer is sent to the USB
   device.

   </add>

   <add-type id="usb_interface_t def">
   </add-type>
 */

typedef struct {
        int (*connect_device)(conf_object_t *bus_obj,
                              conf_object_t *dev_obj,
                              usb_speed_t speed);
        int (*disconnect_device)(conf_object_t *bus_obj,
                                 conf_object_t *dev_obj);
        void (*complete_transfer)(conf_object_t *bus_obj,
                                  conf_object_t *dev_obj,
                                  usb_transfer_t *transfer);
} usb_interface_t;

#define USB_INTERFACE "usb"


#endif /* _SIMICS_DEVS_USB_H */
