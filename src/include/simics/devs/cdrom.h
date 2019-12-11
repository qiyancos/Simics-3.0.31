/*
 * simics/devs/cdrom.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_CDROM_H
#define _SIMICS_DEVS_CDROM_H

#define CDROM_MEDIA_INTERFACE "cdrom-media"

typedef struct {
        int (*read_toc)(conf_object_t *media, char *buf, int msf, int start_track);
        uint32 (*capacity)(conf_object_t *media);
        int (*read_block)(conf_object_t *media, char *buf, int lba);
        int (*read_raw_block)(conf_object_t *media, char *buf, int lba);
	int (*insert)(conf_object_t *media);
	void (*eject)(conf_object_t *media);	
} cdrom_media_interface_t;

// ADD INTERFACE cdrom_media_interface

#endif /* _SIMICS_DEVS_CDROM_H */
