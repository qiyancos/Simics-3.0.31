# -*- makefile -*-
# Do not edit. This file will be overwritten by the workspace setup script.

ifneq ($(VERBOSE),yes)
MAKEFLAGS += -s
endif

include config.mk

TARGET_DIR=$(SIMICS_WORKSPACE)/$(HOST_TYPE)/lib
MODULES=$(patsubst modules/%/Makefile,%,$(wildcard modules/*/Makefile))

export TARGET_DIR

all: $(MODULES)
.PHONY: $(MODULES)

ifeq ($(ENVCHECK),disable)
ENVCHECK_FLAG=
else
include $(SIMICS_BASE)/config/envcheck.mk
ENVCHECK_FLAG=$(HOST_TYPE)/.environment-check/all
endif

MODULE_CLEAN   := $(foreach MOD,$(MODULES),clean-$(MOD))
MODULE_CLOBBER := $(foreach MOD,$(MODULES),clobber-$(MOD))

$(MODULES): $(ENVCHECK_FLAG)
ifeq (,$(HOST_TYPE))
	echo "Could not determine host-type."
	exit 1
endif
	[ -d "$(TARGET_DIR)" ] || mkdir -p "$(TARGET_DIR)"
	[ -d "$(SIMICS_WORKSPACE)/$(HOST_TYPE)/obj/modules/$@" ] || \
		mkdir -p "$(SIMICS_WORKSPACE)/$(HOST_TYPE)/obj/modules/$@"
	@echo "$(HEAD_COLOR)=== Building module \"$@\" ===$(NO_COLOR)"
	$(MAKE) -C "$(SIMICS_WORKSPACE)/$(HOST_TYPE)/obj/modules/$@" \
		-f "$(SIMICS_WORKSPACE)/modules/$@/Makefile" \
		MOD_MAKEFILE="$(SIMICS_WORKSPACE)/modules/$@/Makefile" \
		HOST_TYPE=$(HOST_TYPE) \
                SRC_BASE="$(SIMICS_WORKSPACE)/modules" \
		MODULE_MAKEFILE="$(SIMICS_BASE)/config/module.mk" \
		TARGET=$@

$(MODULE_CLEAN):
	mod=$(shell echo $@ | sed -e 's/clean-\(.*\)/\1/') ;	\
	echo "Clean of module: $$mod" ;				\
        $(RM) -rf $(HOST_TYPE)/obj/modules/$$mod

$(MODULE_CLOBBER):
	mod=$(shell echo $@ | sed -e 's/clobber-\(.*\)/\1/') ;	\
	echo "Removing module: $$mod" ;				\
        $(RM) -rf $(HOST_TYPE)/obj/modules/$$mod ;		\
	$(RM) -f $(HOST_TYPE)/lib/$$mod.$(SO_SFX) ;		\
	$(RM) -f $(HOST_TYPE)/lib/python/mod_$$mod*

clean:
	echo "Clean of all modules"
	$(RM) -rf $(HOST_TYPE)/obj/*
	$(RM) -rf $(HOST_TYPE)/.environment-check

clobber: clean
	echo "Removing all modules"
	$(RM) -rf $(HOST_TYPE)/lib/*

help:
	@echo Available modules: $(MODULES)
	@echo Show build commands: make VERBOSE=yes
