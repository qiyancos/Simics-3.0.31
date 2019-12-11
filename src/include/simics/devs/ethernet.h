/*
 * simics/devs/ethernet.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_ETHERNET_H
#define _SIMICS_DEVS_ETHERNET_H

#include <simics/util/dbuffer.h>

#if !defined(ETHER_CRC_LEN)
 #define ETHER_CRC_LEN 4
#endif
#if !defined(ETHER_MIN_LEN)
 #define ETHER_MIN_LEN 64
#endif
#if !defined(ETHER_MAX_LEN)
 #define ETHER_MAX_LEN 1518
#endif
#if !defined(ETH_ALEN)
 #define ETH_ALEN 6
#endif
#if !defined(ETHERTYPE_PUP)
 #define ETHERTYPE_PUP 0x0200      /* Xerox PUP */
#endif
#if !defined(ETHERTYPE_IP)
 #define ETHERTYPE_IP 0x0800       /* IP */
#endif
#if !defined(ETHERTYPE_ARP)
 #define ETHERTYPE_ARP 0x0806      /* Address resolution */
#endif
#if !defined(ETHERTYPE_REVARP)
 #define ETHERTYPE_REVARP 0x8035   /* Reverse ARP */
#endif

typedef struct {
        uint8  ether_dhost[ETH_ALEN];
        uint8  ether_shost[ETH_ALEN];
        uint16 ether_type;
} ether_header_t;

typedef struct {
#if defined(HOST_LITTLE_ENDIAN)
        uint8  ip_hl:4;                 /* header length */
        uint8  ip_v:4;                  /* version */
#else
        uint8  ip_v:4;                  /* version */
        uint8  ip_hl:4;                 /* header length */
#endif
        uint8  ip_tos;                  /* type of service */
        uint16 ip_len;                  /* total length */
        uint16 ip_id;                   /* identification */
        uint16 ip_off;                  /* fragment offset field */
        uint8  ip_ttl;                  /* time to live */
        uint8  ip_p;                    /* protocol */
        uint16 ip_sum;                  /* checksum */
        uint32 ip_src, ip_dst;          /* source and dest address */
} ip_header_t;

/* This follows the priority list in the autonegotiation protocol.
   See .e.g the book "Ethernet; The Definitive Guide" p. 90, or
   "28B.3 Priority resolution" in the IEEE 802.3 Standard */
typedef enum {
        Phy_Speed_10BASE_T      = 0x001,
        Phy_Speed_10BASE_T_FD   = 0x002,
        Phy_Speed_100BASE_TX    = 0x004,
        Phy_Speed_100BASE_T4    = 0x008,
        Phy_Speed_100BASE_T2    = 0x010,
        Phy_Speed_100BASE_TX_FD = 0x020,
        Phy_Speed_100BASE_T2_FD = 0x040,
        Phy_Speed_1000BASE_T    = 0x080,
        Phy_Speed_1000BASE_T_FD = 0x100
} phy_speed_t;

/* <add id="ethernet_link_interface_t">
   <insert-until text="// ADD INTERFACE ethernet_link_interface"/>

   This interface is implemented by Ethernet link objects that provide
   a data link layer interface for Ethernet frame delivery.

   An Ethernet device calls the <fun>connect_device</fun> device
   function to attach itself to the link, and
   <fun>disconnect_device</fun> to detach itself.  The device must
   implement the <iface>ethernet_device</iface> interface.

   The <fun>connect_device</fun> function attaches an Ethernet
   device to the link.  The device must implement the
   <iface>ethernet_device</iface> interface.  The return value is an
   identification number that should be used in subsequent calls to
   the link to identify the device.

   The <fun>disconnect_device</fun> function detaches an Ethernet
   device from the link.  It will not receive any more frames from the
   link and may not call any functions in the interface, except
   <fun>connect_device</fun>.

   The <fun>send_frame</fun> function is used by a device to send an
   Ethernet frame onto the link to be delivered to the other devices
   connected to the same link.  The frame should be a
   <type><idx>dbuffer_t</idx></type> containing a complete Ethernet frame,
   excluding the preamble and SFD, but including the CRC.  The
   <para>crc_calculated</para> flag indicates whether the CRC is
   actually calculated.  In many cases, the CRC will not be checked by
   the receiver, which makes it more efficient to skip the CRC
   calculation an set this flag to 0.  If needed, Simics will
   calculate a valid CRC for the frame.  The <para>delay</para> makes
   it possible to add a small delay to the frame.  This can be used
   when a device wants to send multiple frames at once, but want them
   to be delivered in a specific sequence.  Instead of using an event
   handler to send each frame, they can be sent at once, with an
   increasing delay for each frame. The delay is given in nanoseconds.

   The <fun>auto_negotiate</fun> is used to do auto-negotiation of
   speed.  An Ethernet device should call this function with the
   <para>speed</para> argument set to a value where all the bits that
   corresponds to speeds that the device can handle set.  The device
   should call this function after it connects to the link the very
   first time (i.e. not after restarting from a checkpoint), or
   whenever the <fun>auto_neg_request</fun> function in its
   <iface>ethernet_device</iface> is called.

   The <fun>add_mac</fun> function registers a MAC address that the
   device will accept frames for.  By default, the device will receive
   no frames at all, but by calling this function, the device can inform
   the link that it will receive frames that match any of the MAC
   addresses it has registered.
   The device is not guaranteed to receive any frames not
   addressed to one of the registered addresses. The address is given as
   a string of six bytes in a <type>byte_string_t</type> structure.

   The <fun>add_mac_mask</fun> is similar to <fun>add_mac</fun>,
   but in addition to the MAC address, a six byte bit mask is also be
   provided.  This mask will be used to mask addresses when checking
   if they should be delivered to the device.  Only bits in the
   address that has the corresponding bit in the mask set to 1 will be
   considered a match.  If the bit mask is zero bytes, it will be
   handled as if it had been all ones, only an exact match will be
   accepted.

   Most network cards listen to the broadcast address (ff:ff:ff:ff:ff:ff)
   or multicast addresses (01:00:00:00:00:00/01:00:00:00:00:00) in
   addition to the configured MAC address. Such models need to call
   <fun>add_mac_mask</fun> with appropriate arguments after being
   connected to a link.

   The <fun>delete_mac</fun> and <fun>delete_mac_mask</fun> functions
   unregisters a MAC address previously registered with
   <fun>add_mac</fun> or <fun>add_mac_mask</fun>.

   The <fun>clear_macs</fun> unregisters all previously registered
   MAC addresses.

   The <fun>promiscuous_mode</fun> function sets the promiscuous
   flag that indicates that the device is listening to all MAC
   addresses.  Setting this to true (non-zero) has a similar effect as
   <fun>clear_macs</fun> in that the link will start sending all
   frames to the device, but when the flag is set to false (zero) the
   MAC addresses filtering will resume with the previously registered
   MAC addresses.

   The functions <fun>auto_negotiate</fun>, <fun>add_mac</fun>,
   <fun>add_mac_mask</fun>, <fun>delete_mac</fun>,
   <fun>clear_macs</fun>, and <fun>promiscuous</fun> behave
   slightly differently when called during initialization and during
   simulation.  When loading a configuration, the devices may call
   these functions to set the initial configuration, but after the
   configuration has been set, the effect of these calls will be
   delayed by at least the latency of the link, since it is a change
   in the simulated state that needs to be propagated in a
   deterministic way.
   </add>
 */
typedef struct {
#ifndef GULP
        int  (*connect_device)(conf_object_t *_obj, conf_object_t *dev,
                               int *new_connection);
        void (*disconnect_device)(conf_object_t *_obj,
                                  conf_object_t *dev);
#endif
        void (*send_frame)(conf_object_t *_obj, int id,
                           dbuffer_t *frame,
                           int crc_calculated, nano_secs_t delay);
        void (*auto_negotiate)(conf_object_t *_obj, int id,
                               phy_speed_t speed);
        void (*add_mac)(conf_object_t *_obj, int id,
                        byte_string_t addr);
        void (*add_mac_mask)(conf_object_t *_obj, int id,
                             byte_string_t addr, byte_string_t mask);
        void (*delete_mac)(conf_object_t *_obj, int id,
                           byte_string_t addr);
        void (*delete_mac_mask)(conf_object_t *_obj, int id,
                                byte_string_t addr, byte_string_t mask);
        void (*clear_macs)(conf_object_t *_obj, int id);
        void (*promiscuous_mode)(conf_object_t *_obj, int id, int enable);
} ethernet_link_interface_t;
#define ETHERNET_LINK_INTERFACE "ethernet_link"
// ADD INTERFACE ethernet_link_interface


/* <add id="ethernet_device_interface_t">
   <insert-until text="// ADD INTERFACE ethernet_device_interface"/>

   This interface is implemented by Ethernet device objects that
   connect to <class>ethernet-link</class> objects.  It is used by the
   link object to send messages to the device object.

   The <fun>receive_frame</fun> function is called when a frame has
   been sent by another device on the link.  The frame is passed as a
   <type><idx>dbuffer_t</idx></type> pointer that may not be modified without
   cloning it first.

   The frame may be addressed to another device, which means that the
   device must be prepared to drop frames addressed to other devices,
   even if it has registered a MAC address.  Also, the frame must not
   assume that it will receive all frames on the link if it has
   registered a MAC address, unless it tells the link it is running in
   promiscuous mode.

   The <fun>auto_neg_request</fun> might be called when another device
   has requested auto-negotiation.  The <para>speed</para> parameter
   contains the connection speeds that the other device supports.  The
   return value should result of clearing the bits in
   <para>speed</para> that the device doesn't support.

   The <fun>auto_neg_reply</fun> is called to return the result of a
   previous call to <fun>auto_negotiate</fun> in the
   <iface>ethernet_link</iface> interface.
   </add>
*/
typedef struct {
        void (*receive_frame)(conf_object_t *dev,
                              conf_object_t *link,
                              dbuffer_t *frame);
        phy_speed_t (*auto_neg_request)(conf_object_t *dev,
                                        phy_speed_t speed);
        void (*auto_neg_reply)(conf_object_t *dev,
                               phy_speed_t speed);
} ethernet_device_interface_t;
#define ETHERNET_DEVICE_INTERFACE "ethernet_device"
// ADD INTERFACE ethernet_device_interface

#endif /* _SIMICS_DEVS_ETHERNET_H */
