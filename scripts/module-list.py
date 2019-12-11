
##  Copyright 2001-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.

import sys, os, string, re, getopt, types, time, operator

"""Module list parsing and formatting"""

def sort(l):
    l.sort()
    return l

MODE_MODULES = 1
MODE_BINARIES = 2

api_defines = {
    'API_1.4': '-DSIMICS_1_4_API',
    'API_1.6': '-DSIMICS_1_6_API',
    'API_1.8': '-DSIMICS_1_8_API',
    'API_1.9': '-DSIMICS_1_9_API',
    'API_2.0': '-DSIMICS_2_0_API',
    'API_2.2': '-DSIMICS_2_2_API',
    'API_3.0': '-DSIMICS_3_0_API',
    'MODULE': ''
    }

current_api = 'MODULE'

variants = ("CURRENT", "API_3.0", "API_2.2", "API_2.0", "API_1.9", "API_1.8",
            "API_1.6", "API_1.4", "SINGLE", "ONE", "ONE2", "ONE3", "BIT",
            "BIT2", "BIT3", "ARCH", "ARCH2", "ARCH3", "MODULE")

moddebug = False

class Group:
    def __init__(self, name, deps, flags):
        self.name = name
        self.deps = deps
        self.flags = flags

        if moddebug:
            print "Added group:", name, deps, flags

class Module:
    def __init__(self, name, variant, src_dir,
                 groups = [], flags = [], make_env = [],
                 deps = [], makefile = "Makefile",
                 api = "MODULE"):

        if type(groups) != types.ListType:
            raise Exception("%s: type error; expected groups = <list>, found groups = %r" % (name, groups))

        if not src_dir:
            raise Exception("%s: no source dir specified" % name)

        self.basename = name
        if variant:
            self.name = name + '-' + variant
        else:
            self.name = name

        self.src_dir = src_dir
        self.variant = variant
        self.groups = sorted(groups)
        self.api = api
        self.flags = flags
        self.deps = deps

        self.make_env = ["%s=yes" % mk for mk in make_env]
        if api.startswith('API_'):
            self.make_env.append("SIMICS_API=%s" % api[4:])

        self.makefile = makefile

        if moddebug:
            print "Added module:", self.name, self.groups


    def __repr__(self):
        return "<module %s>" % self.name

    def __cmp__(self, mod):
        return cmp(self.name, mod.name)


class ModuleList:

    def __init__(self, host_str, mode, source_dirs):
        self.source_dirs = source_dirs  # source directories to scan
        self.host_str = host_str        # $(HOST_DIR).$(CC_TYPE)

        self.groups = {}
        self.modules = {}
        self.skip_modules = []
        self.cygpath_map = {}

        self.mode = mode

    def parse(self, module_list_file):
        f = open(module_list_file, "r")
        lines = f.readlines()
        f.close()

        lineno = 0
        for line in lines:
            lineno = lineno + 1

            n = line.find('#')
            if n >= 0:
                line = line[:n]

            # split line into whitespace separated words
            line = [ elem.strip() for elem in line.split() if elem != "|"]

            if len(line) == 0:
                continue

            is_group = 0

            if self.mode == MODE_BINARIES:
                if line[0] == "group:":
                    del line[0]
                    is_group = 1
            else:
                # if the second word is in 'variants', this is a module
                if len(line) > 1 and line[1] in variants:
                    is_group = 0
                else:
                    is_group = 1

            if is_group:
                self.add_group(line, module_list_file)
            else:
                self.add_module(line, module_list_file)


    # Find directories that look like module directories, but aren't listed and
    # warn about them.
    def warn_undefined_modules(self):

        undefined_modules = []

        for d in [ d for d in self.source_dirs if os.path.isdir(d) ]:
            for f in os.listdir(d):
                if os.path.isfile(os.path.join(d, f, "Makefile")):
                    if not f in self.modules.keys() and not f in self.skip_modules:
                        undefined_modules.append([d, f])

        # also add modules that are not in modules.list
        for d, f in undefined_modules:
            if moddebug:
                print "Directory looks like a module dir, but is not listed:",\
                      os.path.join(d, f)

            self.add_module([f, 'MODULE'], "no-file")


    def add_group(self, line, module_list_file):
        name = line[0]

        if self.groups.has_key(name):
            print "Info: group '%s' in file '%s' shadowed." % (name, module_list_file)
            return

        flags = []
        deps = []
        for s in line[1:]:
            if s[0] == "-":
                flags.append(s)
            else:
                deps.append(s)

        self.groups[name] = Group(name, deps, flags)


    # Finds the source directory of a module. Adds module to skip_modules
    # list if the source directory could not be found. Returns a tuple
    # (source_dir, makefile) where 'makefile' is the name of the makefile
    # to use (some modules are co-located in the same directory and suffix
    # their makefiles, e.g. src/cpu/x86-p4/Makefile-stall to build module
    # x86-p4-stall.

    def find_source_directory(self, name):

        # Check if <modname>/Makefile exists in any of the source directories
        for d, f in [(os.path.join(d, name),
                      os.path.join(d, name, "Makefile")) for d in self.source_dirs]:
            if os.path.isfile(f):
                return (d, "Makefile")

        # Search for modules named foo-bar by looking for
        # <source dir>/foo/Makefile-bar

        pos = name.rfind('-')
        if pos >= 0:
            basename = name[:pos]
            suffix = name[pos+1:]

            for d in [ os.path.join(d, basename) for d in self.source_dirs]:
                if not os.path.isdir(d):
                    continue

                for f in os.listdir(d):
                    if f == 'Makefile-' + suffix:
                        if moddebug:
                            print "Mapping module %s to %s" % (name, basename)

                        return (d, f)

        # No source code found, skip module
        self.skip_modules.append(name)
        if moddebug:
            print "Cannot find %s in any source directory - skipping." % name

        return (None, None)

    def cygpath_source_dir(self, d, name):
        if sys.platform != "win32":
            return d

        if self.cygpath_map.has_key(d):
            return self.cygpath_map[d]
        else:
            lines = os.popen("cygpath -u \"%s\"" % (d)).readlines()
            if lines == []:
                print "Cygpath conversion failed for module %s; using original (%s)" % (name, d)
                cygpath_dir = d
            else:
                self.cygpath_map[d] = lines[0].strip()

            return self.cygpath_map[d]

    # Return list of archs which match va and pa bits
    def get_bit_archs(self, va_bit_str, pa_bit_str):

        # return true if flags contains matching defines
        def check_bits(va_str, pa_str, flags):
            va = "-DTARGET_VA_BITS=%s" % va_str
            pa = "-DTARGET_PA_BITS=%s" % pa_str

            return (va in group.flags and pa in group.flags)

        return [ group for group in self.groups
                 if check_bits(va_bit_str, pa_bit_str, group.flags)]



    def add_module(self, line, module_list_file):

        name = line.pop(0)
        if self.mode == MODE_MODULES:
            archvar = line.pop(0)
        else:
            archvar = None

        if self.modules.has_key(name):
            print "Info: module '%s' in file '%s' shadowed." % (name, module_list_file)
            return

        if name.find(" ") != -1:
            print "Module \"%s\" has spaces in it. Ignoring." % name
            return

        makefile = "Makefile"           # default makefile name

        group_list = []
        do_host = []
        no_host = []
        make_env = []
        deps = ''

        for s in line:
            if s[0] == "-":
                no_host.append(s[1:])
            elif s[0] == "+":
                do_host.append(s[1:])
            elif s[0] == "@":
                make_env.append(s[1:])
            elif s[0] == ":":
                deps += s[1:] + ' '
            else:
                group_list.append(s)

        # check if not on this host
        for s in no_host:
            if self.host_str.find(s) != -1:
                self.skip_modules.append(name)
                if moddebug:
                    print "Module '%s' is not available on this host." % name
                return

        if do_host:
            for s in do_host:
                if self.host_str.find(s) != -1:
                    if moddebug:
                        print "Module '%s' is *only* available on this host." % name
                    break
            else:
                if moddebug:
                    print "Module '%s' is not available on this host." % name

                self.skip_modules.append(name)
                return

        source_dir, makefile = self.find_source_directory(name)
        if not source_dir:
            return

        source_dir = self.cygpath_source_dir(source_dir, name)

        if self.mode == MODE_BINARIES:
            self.modules[name] = []

            module = Module(name, None,
                            source_dir,
                            groups = group_list,
                            make_env = make_env,
                            deps = deps,
                            makefile = makefile)

            self.modules[name].append(module)
            return


        if archvar == "CURRENT":
            archvar = current_api

        warn = 1
        # Check for API compatibility
        if archvar == 'MODULE':
            api = archvar
            warn = 0
        elif archvar[:4] == 'API_':
            api = archvar
        elif archvar == 'SINGLE':
            api = 'API_1.9'
        elif archvar in [ 'ARCH3', 'BIT3', 'ONE3' ]:
            api = 'API_1.8'
        elif archvar in [ 'ARCH2', 'BIT2', 'ONE2' ]:
            api = 'API_1.6'
        else:
            api = 'API_1.4'

        if warn:
            print "Warning: Specifying API version in module-list file is obsolete."
            print "Please update module '%s'." % name

        if not api_defines.has_key(api):
            print "Unknown API: %s" % api
        else:
            flags = [api_defines[api]]

        # If this is an old-style arch-specific module, clone it
        if archvar[:4] == "ARCH":
            self.modules[name] = []

            for arch in [ arch for arch in self.groups.keys() if arch in group_list ]:

                module = Module(name, arch, source_dir,
                                groups = [arch],
                                make_env = make_env,
                                flags = flags + self.groups[arch].flags,
                                api = api)

                self.modules[name].append(module)

        elif archvar[:3] == "BIT":
            self.modules[name] = []

            for (vbit, pbit) in [(32, 32), (64, 64), (32, 64)]:
                if vbit == pbit:
                    variant = "%d" % vbit
                else:
                    variant = "v%dp%d" % (vbit, pbit)

                bitflags = ["-DTARGET_VA_BITS=%d" % vbit, "-DTARGET_PA_BITS=%d" % pbit]

                module = Module(name, variant, source_dir,
                                groups = self.get_bit_archs(vbit, pbit),
                                make_env = make_env,
                                flags = flags + bitflags,
                                api = api)

                self.modules[name].append(module)

        elif archvar[:3] == "ONE" or archvar == "SINGLE":
            module = Module(name, None, source_dir,
                            groups = group_list,
                            flags = flags,
                            make_env = make_env,
                            makefile = makefile,
                            api = api)

            self.modules[name] = [module]

        elif archvar in variants:
            module = Module(name, None, source_dir,
                            groups = group_list,
                            flags = flags,
                            make_env = make_env,
                            makefile = makefile,
                            api = api)

            self.modules[name] = [module]

        else:
            print "Unknown variant: %s" % archvar

class ModuleListWriter:

    def __init__(self, modules, groups, mode):

        self.modules = modules
        self.groups = groups
        self.mode = mode

        self.module_names = sorted(self.modules.keys())
        self.group_names = sorted(self.groups.keys())

        # Flat list of modules
        self.module_list = sorted(reduce(operator.add, self.modules.values()))

    def generate_group_to_group_dependencies(self, f):
        f.write("#\n")
        f.write("# group -> group dependencies\n")
        f.write("#\n\n")

        for g in self.group_names:
            dep_str = ""
            cln_str = ""

            for d in sort(self.groups[g].deps):
                dep_str = dep_str + " " + d
                cln_str = cln_str + " clean-" + d

            f.write("%s:%s\n\n" % (g, dep_str))
            f.write("clean-%s:%s\n\n" % (g, cln_str))

    def generate_module_to_module_variant_dependencies(self, f):
        f.write("#\n")
        f.write("# module -> module-variant dependencies\n")
        f.write("#\n\n")

        for m in self.module_names:

            dep_str = ""
            clean_str = ""

            if len(self.modules[m]) == 1 and self.modules[m][0].name == m:
                # This is a ONE module.  No variants.
                continue

            for mod in sort(self.modules[m]):
                dep_str = dep_str + " " + mod.name
                clean_str = clean_str + " clean-" + mod.name

	    f.write("%s: %s\n\n" % (m, dep_str))
            f.write("clean-%s: %s\n\n" % (m, clean_str))

    # Generate group -> module variant dependencies (MODE_BINARIES)
    def generate_binaries_group_to_module_variant_dependencies(self, f):
        f.write("#\n")
        f.write("# group -> module-variant dependencies\n")
        f.write("#\n\n")

        for g in self.group_names:
            dep_str = ""

            f.write("\n\n# group -> module-variants for group \"%s\"\n" % g)

            group_mods = [ m for m in self.module_list if g in m.groups ]
            mods = [ m.name for m in group_mods ]
            ug = g.upper()

            fmtdict = { 'GROUP': ug,
                        'mods_str': " ".join(mods),
                        'group': g }

            f.write("""
%(GROUP)s_BINARIES := %(mods_str)s

%(group)s: $(%(GROUP)s_BINARIES)

list-%(group)s:
	@if [ -z "$(%(GROUP)s_BINARIES)" ]; then			\\
	    echo 'There are no targets in the "%(group)s" group.';	\\
	else								\\
	    echo 'The following targets are in the "%(group)s" group:';	\\
	    echo;							\\
	    echo $(%(GROUP)s_BINARIES) | tr ' ' '\\012' | $(COLUMN);	\\
	fi

clean-%(group)s: $(patsubst %%, clean-%%, $(%(GROUP)s_BINARIES))
""" % fmtdict)

    # Generate group -> module variant dependencies (MODE_MODULES)
    def generate_module_group_to_module_variant_dependencies(self, f):
        f.write("#\n")
        f.write("# group -> module-variant dependencies\n")
        f.write("#\n\n")

        for g in self.group_names:
            dep_str = ""

            f.write("\n\n# group -> module-variants for group \"%s\"\n" % g)

            group_mods = [ m for m in self.module_list if g in m.groups ]

            if not group_mods:
                f.write("# no modules in this group\n\n")
                continue

            ug = g.upper()

            mods = [ m.name for m in group_mods if m.src_dir.find("/cpu/") < 0 ]

            f.write("%s_MODULES := %s\n" % (ug, " ".join(mods)))

            mods = [ m.name for m in group_mods if m.src_dir.find("/cpu/") >= 0 ]

            fmtdict = { 'GROUP': ug,
                        'mods_str': " ".join(mods),
                        'group': g }

            f.write("""
%(GROUP)s_CPU_MODULES := %(mods_str)s

list-%(group)s:
	@if [ -z "$(strip $(%(GROUP)s_MODULES) $(%(GROUP)s_CPU_MODULES))" ]; then \\
	    echo 'There are no targets in the "%(group)s" group.';	\\
	else								\\
	    echo 'The following targets are in the "%(group)s" group:';	\\
	    echo;							\\
	    echo $(%(GROUP)s_MODULES) $(%(GROUP)s_CPU_MODULES)		\\
		|  tr ' ' '\\012' | $(COLUMN);				\\
	fi

clean-%(group)s: $(patsubst %%, clean-%%, $(%(GROUP)s_MODULES) $(%(GROUP)s_CPU_MODULES))

%(group)s: $(%(GROUP)s_MODULES) $(%(GROUP)s_CPU_MODULES)

""" % fmtdict)

    def generate_module_rules(self, f):

        f.write("""

# ------------------------------------------------------------
# MODULE RULES
# ------------------------------------------------------------
""")

        for m in self.module_list:

            if m.api not in (current_api, 'MODULE'):
                api_str = "using the %s API " % m.api[4:]
            else:
                api_str = ""

            fmtdict = { 'mod_flags': " ".join(m.flags),
                        'make_env': " ".join(m.make_env),
                        'name': m.name,
                        'api_str': api_str,
                        'makefile': m.makefile,
                        'src_dir': m.src_dir,
                        'src_base': os.path.dirname(m.src_dir),
                        'makefile_dir': os.path.basename(m.src_dir),
                        'mod_base': m.basename}

            # ------------------------------------------------------------
            # NOTE: do not remove the tabs in the rules below!
            # ------------------------------------------------------------

            f.write("""\

.PHONY: %(name)s

%(name)s: $(BUILD_DIR)/obj/modules/%(name)s
ifeq ($(OUTPUT_TIMESTAMP),yes)
	$(PERL) -le 'print \"module:%(name)s \", time'
endif
ifneq ($(SILENT),yes)
	@echo \"$(HEAD_COLOR)=== Building module \\\"%(name)s\\\" %(api_str)s===$(NO_COLOR)\"
endif
	@$(RM) modcap.buf
	@SIMICS_BASE=$(SIMICS_BASE) \\
        BUILD_DIR=$(BUILD_DIR) \\
        $(MAKE) -C $(BUILD_DIR)/obj/modules/%(name)s \\
		-f %(src_dir)s/%(makefile)s \\
                -r $(FLG) $(MAKE_OPTIONS) \\
		SRC_BASE=%(src_base)s \\
		MODULE_MAKEFILE=$(SIMICS_BASE)/src/devices/common/device-makefile \\
		MAKEFILE_DIR=%(makefile_dir)s \\
		TARGET=%(mod_base)s \\
		%(make_env)s \\
		MOD_CFLAGS=\"%(mod_flags)s\" \\
		FILE_NAME=%(name)s \\
		$(TGT);

.PHONY: clean-%(name)s

clean-%(name)s:
	@if [ -d $(BUILD_DIR)/obj/modules/%(name)s ]; then \\
		echo \"Deleting %(name)s...\"; \\
		rm -rf $(BUILD_DIR)/obj/modules/%(name)s; \\
	fi

""" % fmtdict)

    def generate_binaries_rules(self, f):
        f.write("""

# ------------------------------------------------------------
# BINARIES RULES
# ------------------------------------------------------------
""")

        for m in self.module_list:

            if not m.name.startswith('simics-common'):
                simicsdep = 'simics-common'
            else:
                simicsdep = ''

            fmtdict = { 'name': m.name,
                        'src_dir': m.src_dir,
                        'makefile': m.makefile,
                        'simicsdep' : m.deps,
                        'make_env':  " ".join(m.make_env) }

            f.write("""\

.PHONY: %(name)s

%(name)s: acdeps $(BUILD_DIR)/obj/binaries/%(name)s %(simicsdep)s
ifeq ($(OUTPUT_TIMESTAMP),yes)
	$(PERL) -le 'print \"binary:%(name)s \", time'
endif
ifneq ($(SILENT),yes)
	@echo \"$(HEAD_COLOR)=== Building binary \\\"%(name)s\\\" ===$(NO_COLOR)\"
endif
	@SIMICS_BASE=\"$(SIMICS_BASE)\" \\
	BUILD_DIR=\"$(BUILD_DIR)\" \\
	$(MAKE) -C $(BUILD_DIR)/obj/binaries/%(name)s \\
		-f %(src_dir)s/%(makefile)s \\
		$(FAST_MAKE) $(SILENT_MODE) $(FLG) $(MAKE_OPTIONS) \\
                HOST_DIR=$(BUILD_DIR) %(make_env)s $(TGT)

.PHONY: clean-%(name)s

clean-%(name)s:
	@if [ -d $(BUILD_DIR)/obj/binaries/%(name)s ]; then \\
		echo \"Deleting %(name)s...\"; \\
		rm -rf $(BUILD_DIR)/obj/binaries/%(name)s;  \\
	fi

""" % fmtdict)

    def generate_modules_cache(self, output_filename):
        if self.mode == MODE_MODULES:
            subdir = "modules"
        else:
            subdir = "binaries"

        f =  open(output_filename, "w")

        # ------------------------------------------------------------
        # NOTE: do not remove the tabs in the rules below!
        # ------------------------------------------------------------

        fmtdict =  { 'subdir': subdir,
                     'group_names': " ".join(self.group_names),
                     'module_names': " ".join(self.module_names) }

        f.write("""\
# -*- Makefile -*-
# automatically generated; all edits will be lost

# All groups
ALL_GROUPS:= %(group_names)s

# All modules
ALL_MODULES:= %(module_names)s
""" % fmtdict)

        if self.mode == MODE_MODULES:
            f.write("LIB_GROUPS := $(ALL_GROUPS)\n")
            f.write("LIB_MODULES := $(ALL_MODULES)\n")
        else:
            f.write("BIN_GROUPS := $(ALL_GROUPS)\n")
            f.write("BIN_MODULES := $(ALL_MODULES)\n")

        if self.mode == MODE_MODULES:
            f.write("ifeq ($(IN_HOST_DIR),)\n")

        f.write("""\

all: $(ALL_MODULES)

$(BUILD_DIR)/obj/%(subdir)s/%%:
	@mkdir -p $@ 2>/dev/null

""" % fmtdict)


        self.generate_group_to_group_dependencies(f)

        if self.mode == MODE_MODULES:
            self.generate_module_to_module_variant_dependencies(f)
            self.generate_module_group_to_module_variant_dependencies(f)
            self.generate_module_rules(f)
        else:
            self.generate_binaries_group_to_module_variant_dependencies(f)
            self.generate_binaries_rules(f)


        if self.mode == MODE_MODULES:
            f.write("endif	# not IN_HOST_DIR\n")

        f.close()


class Timer:
    def start(self):
        self.t0 = time.clock()

    def stop(self):
        self.duration = time.clock() - self.t0

    def __str__(self):
        return "%.02f secs" % self.duration

if __name__ == "__main__":
    timer = Timer()
    timer.start()

    mode = 0
    output_filename = None
    module_list_files = []
    host_str = None

    optlist, tail = getopt.getopt(sys.argv[1:], "h:mbl:d",
                                  ["host=",
                                   "modules",
                                   "binaries",
                                   "debug",
                                   "module-list="])

    for opt, val in optlist:
        if opt == "--host" or opt == "-h":
            host_str = val

        elif opt == "--module-list" or opt == "-l":
            # currently, we only use one module-list file, but allow
            # for a comma-separated list
            module_list_files = val.split(",")

        elif opt == "--modules" or opt == "-m":
            mode = MODE_MODULES
            output_filename = "modules.cache"
            # print "Mode: modules"

        elif opt == "--binaries" or opt == "-b":
            mode = MODE_BINARIES
            output_filename = "binaries.cache"
            # print "Mode: binaries"

        elif opt == "--debug" or opt == "-d":
            moddebug = True

    if not module_list_files or not host_str:
        raise Exception("--host and --module-list must be specified")

    if mode == 0:
        raise Exception("--modules or --binaries must be specified")

    source_dirs = tail

    p = ModuleList(host_str, mode, source_dirs)
    for module_list_file in module_list_files:
        p.parse(module_list_file)
    p.warn_undefined_modules()

    timer.stop()
    # print "parse:", timer

    timer.start()
    writer = ModuleListWriter(p.modules, p.groups, mode)
    writer.generate_modules_cache(output_filename)
    timer.stop()
    # print "modcache:", timer
