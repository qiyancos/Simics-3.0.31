# Makefile for openif

VPATH = $(SIMICS_BASE)/src/misc/openif

include $(HOST_DIR)/config/host-config

SOURCES=openif.c
OBJECTS=$(SOURCES:.c=.$(OBJEXT))
TARGET=$(TARGET_DIR)/openif$(EXEEXT)

.PHONY: openif

$(TARGET): $(OBJECTS)
	@$(ECHO) "Linking $(FILE_COLOR)$@$(NO_COLOR)"
	$(COLORIZE) $(CC) $(CCLDFLAGS) $(LDFLAGS_LOCAL_FIRST) -o $@	\
		$^ $(LIBSOCKET) $(CCLDFLAGS_LAST)

%.$(OBJEXT): %.c
	@$(ECHO) "Compiling $(FILE_COLOR)$*.c$(NO_COLOR)"
	$(COLORIZE) $(CC) $(CFLAGS) $(CFLAGS_LOCAL) -c -o $@ $<

clean:
	rm -f $(TARGET_DIR)/$(TARGET) $(OBJECTS)

clobber: clean
