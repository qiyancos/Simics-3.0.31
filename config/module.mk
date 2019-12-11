# -*- makefile -*-
#
# Makefile for user workspaces.
#

ifdef MODULE_DIR
MODULE_DIR:=$(firstword $(wildcard $(SIMICS_WORKSPACE)/modules/$(MODULE_DIR)) \
			$(wildcard $(SIMICS_BASE)/src/devices/$(MODULE_DIR))  \
			$(wildcard $(SIMICS_BASE)/src/extensions/$(MODULE_DIR)))
else
MODULE_DIR:=$(SIMICS_WORKSPACE)/modules/$(TARGET)
endif

override VPATH := $(EXTRA_VPATH):$(MODULE_DIR):$(VPATH)

CFLAGS += $(MODULE_CFLAGS) -DUSE_MODULE_HOST_CONFIG
CFLAGS += $(patsubst %, -I%,$(subst :, ,$(VPATH)))

CXXFLAGS += $(MODULE_CFLAGS) -DUSE_MODULE_HOST_CONFIG
CXXFLAGS += $(patsubst %, -I%,$(subst :, ,$(VPATH)))

LDFLAGS += $(MODULE_LDFLAGS)

ifdef SIMICS_API
CFLAGS += $(shell echo \"-DSIMICS_$(SIMICS_API)_API\" | sed "s/\./_/g")
CXXFLAGS += $(shell echo \"-DSIMICS_$(SIMICS_API)_API\" | sed "s/\./_/g")
API_WARN:=api_warning
endif

DDL_FILES:=$(strip $(DDL_FILES))
DML_FILES:=$(strip $(DML_FILES))

MODULE_OBJS=						\
	$(patsubst %.S,%.$(OBJEXT),$(filter %.S,$(SRC_FILES)))	 \
	$(patsubst %.s,%.$(OBJEXT),$(filter %.s,$(SRC_FILES)))	 \
	$(patsubst %.cc,%.$(OBJEXT),$(filter %.cc,$(SRC_FILES))) \
	$(patsubst %.cpp,%.$(OBJEXT),$(filter %.cpp,$(SRC_FILES))) \
	$(patsubst %.c,%.$(OBJEXT),$(filter %.c,$(SRC_FILES)))	 \
	$(patsubst %.ddl,%-ddl.$(OBJEXT),$(DDL_FILES))  \
	$(patsubst %.dml,%-dml.$(OBJEXT),$(DML_FILES))  \
	$(EXTRA_OBJ_FILES)

# module name used for python command files
MODULE_PYNAME= $(subst -,_,$(TARGET))

TARGET_DIR= $(SIMICS_WORKSPACE)/$(HOST_TYPE)/lib

# shared object file for the module
MODULE_SHLIB= $(TARGET_DIR)/$(TARGET).$(SO_SFX)

# small object file containing module metadata
MODULE_ID= module_id.$(OBJEXT)

CMD_SRC=$(wildcard $(SIMICS_WORKSPACE)/modules/$(TARGET)/commands.py)
GCMD_SRC=$(wildcard $(SIMICS_WORKSPACE)/modules/$(TARGET)/gcommands.py)

ifneq ($(CMD_SRC),)
CMD_TGT= $(TARGET_DIR)/python/mod_$(MODULE_PYNAME)_commands.py
endif
ifneq ($(GCMD_SRC),)
GCMD_TGT= $(TARGET_DIR)/python/mod_$(MODULE_PYNAME)_gcommands.py
endif

.PHONY: all
ifeq ($(findstring .py,$(SRC_FILES)),.py)
all: $(addprefix $(TARGET_DIR)/,$(notdir $(SRC_FILES))) $(CMD_TGT) $(GCMD_TGT)

$(TARGET_DIR)/%.py: $(SIMICS_WORKSPACE)/modules/$(TARGET)/%.py $(MOD_MAKEFILE)
	@echo "        $(FILE_COLOR)$(@F)$(NO_COLOR)"
	@cp $< $@
else
all: $(API_WARN) $(MODULE_SHLIB) $(CMD_TGT) $(GCMD_TGT)

api_warning:
	@printf "$(WARN_COLOR)Using the Simics $(SIMICS_API) API "
	@printf "for $(TARGET) module$(NO_COLOR)\n"

ifeq ($(findstring win32,$(HOST_TYPE)),win32)
SIMICS_START_SCRIPT:=simics.bat
else
SIMICS_START_SCRIPT:=simics
endif

.DELETE_ON_ERROR: $(MODULE_SHLIB)

$(MODULE_SHLIB): $(MODULE_OBJS) $(MODULE_ID)
	@echo "CCLD    $(FILE_COLOR)$(@F)$(NO_COLOR)"
	$(CCLD) $(CCLDFLAGS_DYN) $^ -o $@ $(LDFLAGS) $(LIBS)
	$(SIMICS_WORKSPACE)/$(SIMICS_START_SCRIPT) -batch-mode	\
		-quiet -no-copyright -no-module-cache		\
		-P modelbuilder -sign-module $@
endif

-include $(MODULE_OBJS:.$(OBJEXT)=.d) $(DDL_FILES:.ddl=.ddldep) $(DML_FILES:.dml=.dmldep)

cls=$(subst ; ,;,$(patsubst %,CLS:%;,$(MODULE_CLASSES)))
mod=$(addprefix MOD:,$(TARGET))

module_id.$(OBJEXT): module_id.c $(MOD_MAKEFILE)
# do not use += on the next line, since it triggers a gmake 3.79.1 crash
module_id.$(OBJEXT): CFLAGS:=$(CFLAGS) -DMODNAME='"$(mod)"' -DCLASSES='"$(cls)"'

module_id.c:
	@echo "        $(FILE_COLOR)$@$(NO_COLOR)"
	cat $(SIMICS_BASE)/src/include/module-id.template \
		| sed "s|__MODULE_DATE__|`date`|" > $@

ifneq ($(findstring .py,$(SRC_FILES)),.py)
-include module_id.d
endif

# --- compilation rules ---

%.$(OBJEXT): %.c $(MOD_MAKEFILE)
	@echo "CC      $(FILE_COLOR)$@$(NO_COLOR)"
	$(CC) $(CFLAGS) $(BLD_CFLAGS) -c $< -o $@

%.$(OBJEXT): %.cc $(MOD_MAKEFILE)
	@echo "CXX     $(FILE_COLOR)$@$(NO_COLOR)"
	$(CXX) $(CXXFLAGS) $(BLD_CXXFLAGS) -c $< -o $@

%.$(OBJEXT): %.cpp $(MOD_MAKEFILE)
	@echo "CXX     $(FILE_COLOR)$@$(NO_COLOR)"
	$(CXX) $(CXXFLAGS) $(BLD_CXXFLAGS) -c $< -o $@

# --- dependency rules ---

ifeq ($(OBJEXT),o)
DEP_PP_FILTER= | sed -e 's,$*\.o,& $@,g'
else
DEP_PP_FILTER= | sed -e 's,$*\.$(OBJEXT),& $@,g' -e 's/\.o\b/\.$(OBJEXT)/g'
endif

%.d: %.c
	@echo "DEP     $(FILE_COLOR)$@$(NO_COLOR)"
	$(DEP_CC) $< $(DEP_CFLAGS) $(CFLAGS) $(DEP_PP_FILTER) > $@

%.d: %.cc
	@echo "DEP     $(FILE_COLOR)$@$(NO_COLOR)"
	$(DEP_CXX) $< $(DEP_CXXFLAGS) $(CXXFLAGS) $(DEP_PP_FILTER) > $@

%.d: %.cpp
	@echo "DEP     $(FILE_COLOR)$@$(NO_COLOR)"
	$(DEP_CXX) $< $(DEP_CXXFLAGS) $(CXXFLAGS) $(DEP_PP_FILTER) > $@

%.d: %.S
	touch $@

%.ddldep : %.ddl
	@echo "DDL-DEP $(FILE_COLOR)$@$(NO_COLOR)"
	$(DMLC) $(DMLC_FLAGS) -M $< $*-ddl > $@

%.dmldep : %.dml
	@echo "DML-DEP $(FILE_COLOR)$@$(NO_COLOR)"
	$(DMLC) $(DMLC_FLAGS) -M $< $*-dml > $@

# --- python command rules ---

$(TARGET_DIR)/python/mod%_commands.py: $(CMD_SRC) $(MOD_MAKEFILE)
	@echo "        $(FILE_COLOR)$(@F)$(NO_COLOR)"
	mkdir $(TARGET_DIR)/python 2>/dev/null;			\
	cp -f $< $@

$(TARGET_DIR)/python/mod%_gcommands.py: $(GCMD_SRC) $(MOD_MAKEFILE)
	@echo "        $(FILE_COLOR)$(@F)$(NO_COLOR)"
	mkdir $(TARGET_DIR)/python 2>/dev/null;			\
	cp -f $< $@

######## DML

DMLC = $(SIMICS_BASE)/bin/dmlc
DMLC_FLAGS +=	-I$(SIMICS_BASE)/$(HOST_TYPE)/lib/dml -I.	\
		-I$(SIMICS_BASE)/src/devices/common 		\
		$(DEVGEN_FLAGS) $(DMLC_FLAGS_USER)

.PRECIOUS: %-ddl.c %-ddl.h %-ddl-struct.h %-ddl-protos.c
.PRECIOUS: %-dml.c %-dml.h %-dml-struct.h %-dml-protos.c

%-ddl.c: %.ddl $(DMLC)
	@echo "DMLC    $(FILE_COLOR)$@$(NO_COLOR)"
	$(DMLC) $(DMLC_FLAGS) $< $*-ddl

%-dml.c: %.dml $(DMLC)
	@echo "DMLC    $(FILE_COLOR)$@$(NO_COLOR)"
	$(DMLC) $(DMLC_FLAGS) $< $*-dml

########

-include $(SIMICS_WORKSPACE)/module-user.mk
