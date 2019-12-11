/*
 * simics/devs/ieee_302_3.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_IEEE_802_3_H
#define _SIMICS_DEVS_IEEE_802_3_H

typedef enum {
        IEEE_no_media,      /* not connected at all */
        IEEE_media_unknown, /* media type is unknown */
        IEEE_10base2,       /* 10 Mb/s CSMA/CD LAN over RG 58 coaxial cable */
        IEEE_10base5,       /* 10 Mb/s CSMA/CD LAN over coaxial cable
                               (i.e., thicknet) */
        IEEE_10baseF,       /* 10 Mb/s CSMA/CD LAN over fiber optic cable */
        IEEE_10baseT,       /* 10 Mb/s CSMA/CD LAN over two pairs of
                               twisted-pair telephone wire */
        IEEE_100baseFX,     /* 100 Mb/s CSMA/CD LAN over two optical fibers */
        IEEE_100baseT,      /* 100 Mb/s CSMA/CD LAN */
        IEEE_100baseT2,     /* 100 Mb/s CSMA/CD LAN over two pairs of cat 3
                               or better balanced cabling */
        IEEE_100baseT4,     /* 100 Mb/s CSMA/CD LAN over four pairs of cat 3,
                               4, and 5 UTP wire */
        IEEE_100baseTX,     /* 100 Mb/s CSMA/CD LAN over two pairs of cat 5
                               UTP or STP wire */
        IEEE_100baseX,      /* 100 Mb/s CSMA/CD LAN with PMD and MDI of
                               ISO/IEC 9314 by ASC X3T12 (FDDI)   */
        IEEE_1000baseX,     /* 1000 Mb/s CSMA/CD LAN derived from
                               ANSI X3.230-1994 (FC-PH) [B20]11         */
        IEEE_1000baseCX,    /* 1000BASE-X over specialty shielded balanced
                               copper jumper cable assemblies  */
        IEEE_1000baseLX,    /* 1000BASE-X using long wavelength laser over
                               multimode and single-mode fiber */
        IEEE_1000baseSX,    /* 1000BASE-X using short wavelength laser over
                               multimode fiber */
        IEEE_1000baseT,     /* 1000 Mb/s CSMA/CD LAN using four pairs of cat 5
                               balanced copper cabling     */
        IEEE_10broad36,     /* 10 Mb/s CSMA/CD LAN over single broadband
                               cable */
        IEEE_1base5         /* 1 Mb/s CSMA/CD LAN over two pairs of
                               twisted-pair telephone wire */
} ieee_802_3_media_t;

typedef enum {
        IEEE_half_duplex,
        IEEE_full_duplex
} ieee_802_3_duplex_mode_t;

typedef enum {
        IEEE_link_unconnected,
        IEEE_link_down,
        IEEE_link_up
} ieee_802_3_link_status_t;

#if 0
/* not sure if we need an interface like this - it should probably be
 * handled through a management channel like MII instead */
typedef struct {
        void (*set_media_type)(conf_object_t *obj, ieee_802_3_media_t type);
        ieee_802_3_media_t (*get_media_type)(conf_object_t *obj);
        void (*set_duplex_mode)(conf_object_t *obj,
                                ieee_802_3_duplex_mode_t duplex);
        ieee_802_3_duplex_mode_t (*get_duplex_mode)(conf_object_t *obj);
        void (*set_link_status)(conf_object_t *obj,
                                ieee_802_3_link_status_t duplex);
        ieee_802_3_link_status_t (*get_link_status)(conf_object_t *obj);
} ieee_802_3_link_interface_t;
#endif /* 0 */

#include <simics/util/dbuffer.h>

/* <add id="ieee_802_3_phy_interface_t">
   <insert-until text="// ADD INTERFACE ieee_802_3_phy_interface"/>

   Interface that should be implemented by 802.3 physical layers.

   The <fun>send_frame</fun> function is used by a device to send an
   Ethernet frame. The frame should be a
   <type><idx>dbuffer_t</idx></type> containing a complete Ethernet frame.
   excluding the preamble and SFD, but including the CRC.  The
   <para>replace_crc</para> flag indicates whether the CRC is
   not actually calculated yet. The passed <para>buf</para> should
   not be modified by the called function.
   If the function return 0, the frame was sent to the link; In case
   -1 is returned, there was not enough bandwidth available right now,
   and the frame could not be sent. The PHY should call the
   <fun>tx_bandwidth_available</fun> in the <iface>ieee_802_3_mac</iface>
   interface at the MAC, when the frame can be sent.

   The <fun>check_tx_bandwidth</fun> can also be used to check that there
   is bandwidth available, without sending a frame. It returns 0 if there
   is no bandwidth available, and a positive value if the frame can be
   sent right away.

   </add>
*/
#define IEEE_802_3_PHY_INTERFACE "ieee_802_3_phy"
typedef struct {
        
        int (*send_frame)(conf_object_t *obj, dbuffer_t *buf, int replace_crc);
        int (*check_tx_bandwidth)(conf_object_t *obj);
        
} ieee_802_3_phy_interface_t;
// ADD INTERFACE ieee_802_3_phy_interface

/* This interface should be merged into the ieee_802_3_phy_interface_t when
   we can change the ABI. This have the same functionality as the same
   functions in <iface>ethernet-link</iface> interface. */
#define IEEE_802_3_EXTRA_PHY_INTERFACE "ieee_802_3_extra_phy"
typedef struct {
        void (*add_mac)(conf_object_t *obj, uint8 *mac);
        void (*del_mac)(conf_object_t *obj, uint8 *mac);
        void (*set_promiscous_mode)(conf_object_t *obj, int enable);
} ieee_802_3_extra_phy_interface_t;

/* <add id="ieee_802_3_mac_interface_t">
   <insert-until text="// ADD INTERFACE ieee_802_3_mac_interface"/>

   Interface that should be implemented by 802.3 media access control layers.

   The <fun>receive_frame</fun> function is called when a frame has
   been received by the phy.  The frame is passed as a
   <type><idx>dbuffer_t</idx></type> that may not be modified without
   cloning it first. The return value have no meaning, callers should
   ignore it, and new implementations should return 0.

   The <fun>tx_bandwith_available</fun> is called by the PHY when a
   previous call to <fun>send_frame</fun> or <fun>check_tx_bandwidth</fun>
   in the <iface>ieee_802_3_phy</iface> have returned no bandwidth available.

   <fun>link_status_changed</fun> is called when the phy detects a change
   of the link status.

   The <para>phy</para> parameter is a number that identifies this particular
   PHY, in configurations with several PHYs connected to the same MAC.

   </add>
*/
#define IEEE_802_3_MAC_INTERFACE "ieee_802_3_mac"
typedef struct {
        int (*receive_frame)(conf_object_t *obj, int phy,
                             dbuffer_t *buf, int crc_ok);
        void (*tx_bandwidth_available)(conf_object_t *obj, int phy);
        void (*link_status_changed)(conf_object_t *obj, int phy,
                                    ieee_802_3_link_status_t status);
} ieee_802_3_mac_interface_t;
// ADD INTERFACE ieee_802_3_mac_interface

/* <add id="link_status_interface_t">
   <insert-until text="// ADD INTERFACE link_status_interface"/>

   Interface that can be implemented by ethernet-devices.

   The <fun>changed</fun> function is called when a real-network connection
   detects a link status change on the host interface. <para>status</para>
   is the new link status.

   </add>
*/
#define LINK_STATUS_INTERFACE "link_status"
typedef struct {
        void (*changed)(conf_object_t *obj, ieee_802_3_link_status_t status);
} link_status_interface_t;
// ADD INTERFACE link_status_interface

#endif /* _SIMICS_DEVS_IEEE_802_3_H */
