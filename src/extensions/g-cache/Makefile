#                                                              -*- Makefile -*-
# Copyright (c) Virtutech AB, All Rights Reserved
#
# Simics module makefile
#

MODULE_CLASSES = g-cache trans-splitter trans-sorter

SRC_FILES = gc-common.c gc-common-attributes.c			\
	    gc-random-repl.c gc-lru-repl.c gc-cyclic-repl.c	\
	    gc-attributes.c gc-interface.c gc.c			\
	    splitter.c sorter.c

MODULE_CFLAGS = -DGC_USE_STC # -DGC_DEBUG

EXTRA_VPATH=$(SIMICS_BASE)/src/extensions/g-cache-common

include $(MODULE_MAKEFILE)
