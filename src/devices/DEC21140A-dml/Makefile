#                                                              -*- Makefile -*-
# Copyright (c) Virtutech AB, All Rights Reserved
#
# Simics module makefile
#

MODULE_CLASSES = DEC21140A-dml

SRC_FILES=
DML_FILES= DEC21140A.dml

MODULE_CFLAGS = -I$(SIMICS_BASE)/src/devices/common
DMLC_FLAGS = -m -I$(SIMICS_BASE)/src/devices/microwire-eeprom

# For microwire
EXTRA_VPATH=$(SIMICS_BASE)/src/devices/microwire-eeprom/

include $(MODULE_MAKEFILE)
