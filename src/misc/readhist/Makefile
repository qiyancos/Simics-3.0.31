# Makefile for readhist

VPATH = $(SIMICS_BASE)/src/misc/readhist

include $(HOST_DIR)/config/host-config

INCPATHS = -I$(SIMICS_BASE)/src/include
DEFS=-DSTANDALONE="" -DFORCE_INLINE="static inline"
CFLAGS += $(INCPATHS) $(patsubst %,-I%,$(subst :, ,$(VPATH))) $(DEFS)

SOURCES=readhist.c
OBJECTS=$(SOURCES:.c=.$(OBJEXT))
TARGET=$(TARGET_DIR)/readhist

LIBPATH_FLAGS = $(patsubst %, -L%, $(subst :, ,$(LIBPATH)))

.PHONY: readhist

$(TARGET): $(OBJECTS)
	@$(ECHO) "Linking $(FILE_COLOR)$@$(NO_COLOR) "
	$(COLORIZE) $(CC) $(CCLDFLAGS) $(LDFLAGS_LOCAL_FIRST) -o $@	\
		$^ $(LIBPATH_FLAGS) $(LIBS) $(LIBREADLINE) $(CCLDFLAGS_LAST)

%.$(OBJEXT): %.c
	@$(ECHO) "Compiling $(FILE_COLOR)$*.c$(NO_COLOR) "
	$(COLORIZE) $(CC) $(CFLAGS) $(CFLAGS_LOCAL) -c -o $@ $<

clean:
	rm -f $(TARGET_DIR)/$(TARGET) $(OBJECTS)

clobber: clean
