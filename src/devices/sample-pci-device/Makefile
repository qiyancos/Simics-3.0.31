#                                                              -*- Makefile -*-
# Copyright (c) Virtutech AB, All Rights Reserved
#
# Simics module makefile
#

MODULE_CLASSES = sample-pci-device

SRC_FILES = sample-pci-device.c pci-device.c

MODULE_CFLAGS = -DDEVICE_NAME=\"sample-pci-device\"

EXTRA_VPATH=$(SIMICS_BASE)/src/devices/pci-device/

include $(MODULE_MAKEFILE)
