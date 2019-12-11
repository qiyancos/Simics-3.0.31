/*
 * simics/devs/central-links.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_CENTRAL_LINKS_H
#define _SIMICS_DEVS_CENTRAL_LINKS_H

#if !defined(GULP)
#include <simics/utils.h>
#endif

/* This structure also documents the network message buffer format */
typedef struct {
        uint32 header_size; /* size of the header, including variable-sized rcpt */
        uint16 type;        /* type of message */
        uint16 link;        /* link number */
        uint16 sender;      /* sending device */
        uint16 flags;       /* return to sender */
        uint32 nrcpt;       /* number of recepients */
        uint64 seq;         /* sender's sequence number */
        uint64 latency;     /* required latency */
        uint64 time;        /* time when sent (from central header) */
        uint16 rcpt[1];     /* variable-sized list of recipients */
} links_msg_header_t;

/* The minimum size of a link message header (excluding rcpt[]) */
#define LINK_HEADER_MIN_SIZE 40

#if !defined(GULP)
#if defined(HOST_32_BIT) 
CASSERT(links_msg_header_t, sizeof(links_msg_header_t) == 44);
#elif defined(HOST_64_BIT)
CASSERT(links_msg_header_t, sizeof(links_msg_header_t) == 48);
#endif
#endif

typedef enum {
        /* link -> central */
        LINK_register_link = 0x8000,
        LINK_register_device,

        /* central -> link */
        LINK_new_device,
        LINK_removed_device
} central_links_msg_type_t;

typedef struct {
        int (*register_device)(conf_object_t *link, conf_object_t *device);
} link_interface_t;

#define LINK_INTERFACE "link"
// ADD INTERFACE link_interface

/* Return to sender */
#define LINK_FLAG_RTS 1

/* Broadcast means that recipients are ignored (nrcpt should be 0) */
#define LINK_FLAG_BROADCAST 2


/* This number should be used for the 'link' header field when talking
   directly to the link central module */
#define META_LINK 0xffff

#endif /* SIMICS_DEVS_CENTRAL_LINKS_H */
