# -*- makefile -*-
#
# User workspace environment checks.
#

CCTYPE=$(SIMICS_BASE)/scripts/cctype.sh
CCVERSION=$(SIMICS_BASE)/scripts/ccversion.sh

ifeq ($(findstring cygwrap, $(word 1, $(CC))),cygwrap)
REALCC=$(word 2, $(CC))
else
REALCC=$(CC)
endif

cctype=$(shell $(CCTYPE) $(REALCC))
ccversion=$(shell $(CCVERSION) $(REALCC))
makeversion=$(shell $(MAKE) --version |\
		 sed -ne 's/.*\([0-9]\.[0-9]*\).*/\1/p')

define touch-flagfile
([ -d `dirname "$@"` ] || mkdir -p `dirname $@`) && touch $@
endef

define inform-user
echo "Pass \"ENVCHECK=disable\" to \"make\" to disable this check."
endef

.PHONY: $(HOST_TYPE)/.environment-check/all
.NOTPARALLEL: $(HOST_TYPE)/.environment-check/all

$(HOST_TYPE)/.environment-check/all:		\
	$(HOST_TYPE)/.environment-check/info	\
	$(HOST_TYPE)/.environment-check/python	\
	$(HOST_TYPE)/.environment-check/cctype 	\
	$(HOST_TYPE)/.environment-check/gnumake

ENV_DEPS:=$(SIMICS_BASE)/config/envcheck.mk $(SIMICS_BASE)/config/config.mk config.mk compiler.mk GNUmakefile
ENV_DEPS+=$(wildcard config-user.mk) $(wildcard Config-user.mk)

$(HOST_TYPE)/.environment-check/info: $(ENV_DEPS)
	@echo "$(HEAD_COLOR)=== Environment Check ===$(NO_COLOR)"
	$(touch-flagfile)

$(HOST_TYPE)/.environment-check/python: $(ENV_DEPS)
	printf "Checking Python version... "
	$(PYTHON) -c "import sys; sys.exit(sys.hexversion >= 0x02040000)"; \
	if [ $$? = 0 ]; then						\
		echo ; 							\
		echo "$(PYTHON) is too old. You need Python >= 2.4." ;	\
		$(inform-user) ;					\
		false ;							\
	else								\
		$(PYTHON) -c 'import sys; print "%d.%d.%d" % sys.version_info[:3];' ; \
		$(touch-flagfile) ;					\
	fi

$(HOST_TYPE)/.environment-check/cctype: $(ENV_DEPS)
	printf "Checking compiler... "
	if [ $(cctype) = unknown -o $(cctype) = unsupported ] ; then	\
		echo ;							\
		echo "Unknown or unsupported compiler." ;		\
		echo "$(CC)" ;						\
		echo "$(ccversion)" ;					\
		$(inform-user) ;					\
		false ;							\
	else								\
		echo "$(ccversion)" ; 					\
		$(touch-flagfile);					\
	fi

ifeq (win32,$(findstring win32,$(HOST_TYPE)))
$(HOST_TYPE)/.environment-check/gnumake: $(ENV_DEPS)
	printf "Checking GNU make... "
	case $(makeversion) in						\
		3.7[7-9] | 3.80 )					\
			echo "$(makeversion)" ;				\
			$(touch-flagfile) ;				\
			;;						\
		3.81 )							\
			echo "Make v. 3.81 doesn't work with Simics, please use v. 3.80" ; \
			$(inform-user) ;				\
			false ;						\
			;;						\
		3.8* )							\
			echo "WARNING: Make v. 3.81 was incompatible with Simics" ; \
			echo "and $(makeversion) is not yet verified to work properly with Simics" ; \
			;;						\
		*)							\
			echo "Unsupported GNU Make version: $(makeversion)"; \
			$(inform-user) ;				\
			false ;						\
			;;						\
	esac
else
$(HOST_TYPE)/.environment-check/gnumake: $(ENV_DEPS)
	printf "Checking GNU make... "
	case $(makeversion) in						\
		3.7[7-9] | 3.8* | 4.* )					\
			echo "$(makeversion)" ;				\
			$(touch-flagfile) ;				\
			;;						\
		*)							\
			echo "Unsupported GNU Make version: $(makeversion)"; \
			$(inform-user) ;				\
			false ;						\
			;;						\
	esac
endif
