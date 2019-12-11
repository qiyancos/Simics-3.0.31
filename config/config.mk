# -*- makefile -*-

compiler:=$(shell $(SIMICS_BASE)/scripts/cctype.sh $(CC))

ifeq (default,$(origin CXX))
CXX=
endif

ifeq (win32,$(findstring win32,$(HOST_TYPE)))
OBJEXT=obj
SO_SFX=dll
else
OBJEXT=o
SO_SFX=so
endif

PYTHON=$(SIMICS_BASE)/bin/fake-python
VPATH=.:$(SIMICS_BASE)/src/include

LDFLAGS+=-L$(SIMICS_BASE)/$(HOST_TYPE)/bin
LIBS=-lsimics-common

DEP_CC=$(CC)
DEP_CXX=$(DEP_CC)

system:=$(HOST_TYPE)-$(compiler)

ifneq (,$(filter $(compiler),gcc3 gcc4))
	CCLDFLAGS_DYN=-shared
	BLD_CFLAGS=-g -O2 -Wall -std=gnu99
	BLD_CXXFLAGS=-g -O2 -Wall
	CXX_NAME=g++
	ifneq (win32,$(findstring win32,$(HOST_TYPE)))
		BLD_CFLAGS+=-fPIC
		BLD_CXXFLAGS+=-fPIC
	endif
	ifeq (v9-sol8-64,$(HOST_TYPE))
		CCLDFLAGS_DYN+=-m64
		BLD_CFLAGS+=-m64
		BLD_CXXFLAGS+=-m64
	endif
endif

ifneq (,$(filter $(system),v9-sol8-64-ws5 v9-sol8-64-ws6 v9-sol8-64-ws7))
	CCLDFLAGS_DYN=-G -xarch=v9a
	BLD_CFLAGS=-v -fast -xarch=v9a -xO4
	BLD_CXXFLAGS=-fast -xarch=v9a -xO4
	DEP_CC=gcc
	CXX_NAME=CC
endif

ifneq (,$(filter $(system),v9-sol8-64-sone8 v9-sol8-64-sone9 v9-sol8-64-sun10 v9-sol8-64-sun11))
	CCLDFLAGS_DYN=-G -xarch=v9a
	BLD_CFLAGS=-v -fast -fns=no -xarch=v9a -xO4 -xF -xalias_level=std
	BLD_CXXFLAGS=-fast -fns=no -xarch=v9a -xO4 -xF
	DEP_CC=gcc
	CXX_NAME=CC
endif

ifeq (,$(CXX))
  ifeq (,$(CXX_NAME))
    CXX=g++
  else
    CXX=$(shell dirname "`which $(CC)`")/$(CXX_NAME)
  endif
endif

DEP_CFLAGS=-M -MG
DEP_CXXFLAGS=$(DEP_CFLAGS)

ifeq (win32,$(findstring win32,$(HOST_TYPE)))
DEP_CFLAGS+=-mno-cygwin
CC:=$(CYGWRAP) $(CC)
CXX:=$(CYGWRAP) $(CXX)
# make sure to use supplied gmake 3.80 and not the new "broken" 3.81
MAKE:=$(SIMICS_BASE)/$(HOST_TYPE)/bin/make
endif

CCLD=$(CXX)

# If using a 32-bit Simics on x86_64 hardware, check if $(CC)/$(CXX)
# needs a flag to generate 32-bit code.
ifeq ($(shell uname -m),x86_64) # Host is x86_64
  ifeq ($(HOST_TYPE),x86-linux) # Simics is 32-bit
    BITFLAG=-m32
    ifeq ($(findstring 64,$(shell $(CC) -dumpmachine)),64)
      BLD_CFLAGS += $(BITFLAG)
      CCLDFLAGS_DYN += $(BITFLAG)
      DEP_CFLAGS += $(BITFLAG)
    endif
    ifeq ($(findstring 64,$(shell $(CXX) -dumpmachine)),64)
      BLD_CXXFLAGS += $(BITFLAG)
      DEP_CXXFLAGS += $(BITFLAG)
    endif
  endif
endif

ifneq (no,$(COLORIZED_MAKE))
ifndef EMACS
  export FILE_COLOR=[1;34m
  export ERR_COLOR=[1;31m
  export WARN_COLOR=[1;35m
  export HEAD_COLOR=[7;34m
  export NO_COLOR=[0m
endif

# The 'cygwin' terminal does not know what the default color is, so ^[[0m
# as NO_COLOR doesn't work. We have to explicitly set the default color to
# something. Currently set to 'light gray', which matches the default
# foreground color for cmd.exe.
ifeq ($(TERM),cygwin)
  export NO_COLOR=[0;37m
endif
endif # COLORIZED_MAKE

export SO_SFX
export DEP_CXXFLAGS
export SIMICS_BASE
export BLD_CFLAGS
export DEP_CXX
export LDFLAGS
export PYTHON
export CXX
export OBJEXT
export DEP_CFLAGS
export DEP_CC
export BLD_CXXFLAGS
export CC
export SIMICS_WORKSPACE
export CCLD
export LIBS
export CCLDFLAGS_DYN
export VPATH
