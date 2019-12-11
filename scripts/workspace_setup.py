# -*- python -*-

##  Copyright 2005-2007 Virtutech AB
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


import sys
import os
import shutil
import re
import glob
import stat
from subprocess import *

Create  = 1
Upgrade = 2

module_building_enabled = True
cygwin_installed = False

try:
    conf.sim
except:
    sys.exit("This script is intended to be invoked from fake-python.")

from os.path import join, basename, dirname, isfile, isdir, abspath, normpath, exists
from optparse import OptionParser, OptionValueError
from errno import *

def get_simics_root():
    return conf.sim.simics_base

scriptdir = join(get_simics_root(), "scripts")
sys.path.append(scriptdir)

# Subdirectory to store workspace metadata stuff (such as workspace-version).
# wxSimics also store data in here.
workspace_properties = ".workspace-properties"

assert sys.platform != "cygwin"

if sys.platform == "win32":
    cygwin_path_ok = False

    # try to locate Cygwin
    for p in os.environ['PATH'].split(";"):
        if isfile(join(p, "cygpath.exe")):
            cygwin_path_ok = True

    if not cygwin_path_ok:
        guess_cygroot = "c:\\cygwin"
        if isfile(join(guess_cygroot, "bin", "cygpath.exe")):
            print "Cygwin not in path; but is installed at", guess_cygroot
            print "Adding %s to PATH." % join(guess_cygroot, "bin")
            os.environ['PATH'] = join(guess_cygroot, "bin") + ";" + os.environ['PATH']
        
    # On windows, we need Cygwin in case the user wants to build modules. To
    # just run Simics, we can do without Cygwin.
    root = os.popen("cygpath --mixed /").readline().strip()
    if len(root) == 0:
        cygwin_installed = False
        module_building_enabled = False
        if "--quiet" not in sys.argv:
            print
            print "*" * 75
            print "Warning: Cygwin does not seem to be installed. You will not be able"
            print "         to build Simics modules. Script options related to building"
            print "         modules have been disabled."
            print
            print "If cygwin is installed, you may need to add Cygwin to your PATH:"
            print
            print "c:\> set PATH=c:\\cygwin\\bin;%PATH%"
            print "*" * 75
            print
    else:
        cygwin_installed = True

def cygwin_platform():
    return sys.platform == "win32" and cygwin_installed

def need_short_form(s):
    for c in [ " ", "(", ")" ]:
        if c in s:
            return True
    return False

def run_command(args):
    return Popen(args, stdout=PIPE).communicate()[0]

def is_valid_class_name(module):
    import re
    return bool(re.match("[A-Za-z][A-Za-z0-9_-]*$", module))

def dos_format_error(s):
    print "Internal error: DOS format conversion requires an existing file or directory:", s
    sys.exit(1)

def run_cygpath(path, style):
    s = run_command(["cygpath", style, path]).strip()
    if not s:
        # Stupid CygWin bug.  Try again
        s = run_cygpath(path, style)
    return s

# convert a native path to valid path for the build system
def buildpath(native_path):
    if cygwin_platform():
        if need_short_form(native_path):
            if not exists(native_path):
                dos_format_error(native_path)
            else:
                native_path = run_cygpath(native_path, "--dos")
        return run_cygpath(native_path, "--unix")
    else:
        return native_path

def unixpath(native_path):
    if cygwin_platform():
        return run_cygpath(native_path, "--unix")
    elif sys.platform == "win32":
        raise "Unix path requested on pure win32 platform"
    else:
        return native_path

# convert any kind of path to a native path
def nativepath(any_path):
    if cygwin_platform():
        return run_cygpath(any_path, "--windows")
    else:
        return any_path
    
def build_cygwrap(workspace, options):
    if not cygwin_installed:
        return
        
    if options.verbose:
        print "Compiling 'cygwrap' wrapper"

    cmd = '%s -Wall -O2 "%s" -o "%s"' % \
          (nativepath("/bin/gcc"),
           unixpath(join(get_simics_root(), "src", "misc", "cygwrap",
                          "cygwrap.c")),
           unixpath(join(workspace, "cygwrap.exe")))
        
    if cmd and not options.dry_run:
        print cmd
        status = os.system(cmd)
        if status != 0:
            sys.exit(1)
    
def get_simics_version():
    d = os.getcwd()
    try:
        os.chdir(join(get_simics_root(), "bin"))
        if sys.platform == "win32":
            cmd = "simics.bat -version"
        else:
            cmd = "./simics -version"
            
        return os.popen(cmd).readline().strip()
    finally:
        os.chdir(d)

def get_workspace_version(workspace):
    workspace_version_file = join(workspace, workspace_properties,
                                  "workspace-version")
    if isfile(workspace_version_file):
        return open(workspace_version_file, "r").readline().strip()
    else:
        return None

def is_workspace(workspace):
    return get_workspace_version(workspace) != None

def get_mtime(f):
    if not isfile(f):
        return 0
    
    try:
        return os.stat(f)[stat.ST_MTIME]
    except Exception, msg:
        print "Warning: failed to get mtime for", f, msg
        return 0
    
# Return the time when the workspace was last created/upgraded
def get_workspace_mtime(workspace):
    return get_mtime(join(workspace, workspace_properties,
                          "workspace-version"))

def get_backup_filename(f):
    n = 1
    while True:
        if sys.platform == "win32":
            bf = f + "~%d~.backup" % n
        else:
            bf = f + ".~%d~" % n
        
        if not isfile(bf):
            return bf
        else:
            n += 1

num_backed_up_files = 0

def backup_file_if_modified(workspace, f):
    global num_backed_up_files

    if not isfile(f):
        return

    f_mtime = get_mtime(f)
    w_mtime = get_workspace_mtime(workspace)

    if f_mtime > w_mtime or f_mtime == 0 or w_mtime == 0:
        bf = get_backup_filename(f)
        try:
            num_backed_up_files += 1
            shutil.copy(f, bf)
        except IOError, msg:
            print "Failed to backup modified file %s: %s" % (f, msg)
            print "Exiting."
            sys.exit(1)

def create_version_file(workspace, options):
    workspace_version_file = join(workspace, workspace_properties,
                                  "workspace-version")

    if options.dry_run:
        return
    
    out = open(workspace_version_file, "w")
    out.write(get_simics_version() + "\n")
    out.close()
        
def makedir(options, path):
    if isdir(path):
        if options.verbose:
            print "Directory already exists: %s" % path
    else:
        if not options.dry_run:
            os.makedirs(path)
            
        if options.verbose:
            print "Created directory: %s" % path

def create_directories(workspace, options):
    makedir(options, workspace)
    makedir(options, join(workspace, workspace_properties))
    makedir(options, join(workspace, "modules"))
    
def create_start_script_sh(workspace, options, suffix, args = ""):
    path = join(workspace, "simics" + suffix)

    if not options.dry_run:
        backup_file_if_modified(workspace, path)
        
        f = open(path, "w+")
        f.write("#!/bin/sh\n")
        f.write(("# this file will be overwritten by the "
                 "workspace setup script\n"))
        f.write("SIMICS_WORKSPACE=\"%s\"; export SIMICS_WORKSPACE\n" %
                workspace)
        f.write("exec \"%s/simics%s\" %s ${1+\"$@\"}\n" % \
                (join(get_simics_root(), "bin"), suffix, args))
        f.close()
        os.chmod(path, 0755)

    if options.verbose:
        print "Wrote:", path

def create_start_script_bat(workspace, options):
    path = join(workspace, "simics.bat")

    if not options.dry_run:
        backup_file_if_modified(workspace, path)
        
        f = open(path, "w+")
        f.write("@echo off\n")
        f.write(("rem this file will be overwritten by the "
                 "workspace setup script\n"))
        f.write("set SIMICS_HOST=x86-win32\n")
        f.write("set SIMICS_WORKSPACE=%s\n" % workspace)
        f.write("set SIMICS_EXTRA_LIB=%s\n" % \
                join(workspace, "x86-win32", "lib"))
        f.write("set PATH=%s\\%%SIMICS_HOST%%\\bin;%%PATH%%\n" % \
                get_simics_root())
        f.write("call simics-common %*\n")
        f.close()

    if options.verbose:
        print "Wrote:", path

def create_start_script(workspace, options):
    if sys.platform == "win32":
        create_start_script_bat(workspace, options)
    else:
        create_start_script_sh(workspace, options, '')
        create_start_script_sh(workspace, options,
                               '-eclipse', '-data "%s"' % workspace)

def create_compiler_makefile(workspace, options):
    if options.dry_run:
        return

    compiler_mk = join(workspace, "compiler.mk")
    if exists(compiler_mk):
        # do not overwrite old one
        return

    f = open(compiler_mk, "w")
    f.write("""\
# -*- makefile -*-
# Select compiler by changing CC for your host type.

ifeq (default,$(origin CC))
  ifeq (x86-linux,$(HOST_TYPE))
    CC=gcc
  endif

  ifeq (v9-sol8-64,$(HOST_TYPE))
    CC=gcc
  endif

  ifeq (amd64-linux,$(HOST_TYPE))
    CC=gcc
  endif

  ifeq (x86-win32,$(HOST_TYPE))
    CC=/cygdrive/c/MinGW/bin/gcc
  endif
endif
""")
    f.close()

    if options.verbose:
        print "Wrote:", compiler_mk

def create_config_makefile(workspace, options):
    if options.dry_run:
        return
    
    config_mk = join(workspace, "config.mk")
    backup_file_if_modified(workspace, config_mk)

    f = open(config_mk, "w")
    f.write("""\
# -*- makefile -*-
# Do not edit this file.
# This file will be overwritten by the workspace setup script.

SIMICS_BASE=%s
SIMICS_WORKSPACE=%s

# allow user to override HOST_TYPE
ifeq (,$(HOST_TYPE))
HOST_TYPE=$(shell $(SIMICS_BASE)/scripts/host-type.sh)
endif

ifeq (x86-win32,$(HOST_TYPE))
CYGWRAP=%s
endif

include compiler.mk

include $(SIMICS_BASE)/config/config.mk

# Put user definitions in config-user.mk
-include config-user.mk

# Deprecated
-include Config-user.mk
""" % (buildpath(get_simics_root()),
       buildpath(workspace),
       buildpath(join(workspace, 'cygwrap.exe'))))

    f.close()

    if options.verbose:
        print "Wrote:", config_mk

def create_workspace_makefile(workspace, options):
    workspace_mk_src = join(get_simics_root(), "config",
                            "masters",
                            "Makefile.workspace")
    workspace_mk = join(workspace, "GNUmakefile")
    
    if not options.dry_run:
        backup_file_if_modified(workspace, workspace_mk)
        shutil.copy(workspace_mk_src, workspace_mk)
        
    if options.verbose:
        print "Wrote:", workspace_mk

def shallow_copy(workspace, options, source_dir, module,
                 translate=lambda s:s):
    target_dir = join(workspace, "modules", module)
    if isdir(target_dir):
        if options.verbose:
            print ("Ignoring module %s, directory "
                   "%s already exists." ) % (module, target_dir)
        return
 
    if options.dry_run:
        return
    
    if options.verbose:
        print "Creating module directory: %s" % target_dir

    os.makedirs(target_dir)
    for source_file in os.listdir(source_dir):
        if not isfile(join(source_dir, source_file)):
            continue
        content = open(join(source_dir, source_file)).read()
        content = translate(content)
        dest_file = translate(source_file)
        open(join(target_dir, dest_file), "w").write(content)
        if options.verbose:
            print "Wrote", dest_file

def copy_module(workspace, options, module, source_module):
    if not is_valid_class_name(module):
        print ("Invalid device name '%s'. Device names must consist of"
               " letters, digits, underscores or dashes, and not start"
               " with a digit."%module)
        return

    idbase = re.sub("[^\w]", "_", module)
    idbase_source = re.sub("[^\w]", "_", source_module)

    if options.verbose:
        print ("Creating module skeleton for module '%s', "
               "C identifier base = '%s'" % (module, idbase))

    source_dir = join(get_simics_root(), "src", "devices", source_module)
    
    convert = lambda s: (s.replace(source_module, module)
                          .replace(idbase_source, idbase))
        
    shallow_copy(workspace, options, source_dir, module, convert)

def create_module_skeletons(workspace, options):
    for lang, skel, modules in \
            [ ( "DML", "empty-dml-device", options.dml_modules ),
              ( "C", "empty-device", options.c_modules ),
              ( "Python", "empty-python-device", options.py_modules ) ]:
        
        for mod in modules:
            copy_module(workspace, options, mod, skel)

def create_copied_modules(workspace, options):
    failed = []
    for mod in options.copied_modules:
        # find the source directory
        for subdir in ("devices", "extensions"):
            source_dir = join(get_simics_root(), "src", subdir, mod)
            if isdir(source_dir): break
        else:
            failed.append(mod)
            continue
        shallow_copy(workspace, options, source_dir, mod)

    if failed:
        print "Failed to find the source of modules:", ' '.join(failed)
        possible = []
        for subdir in ("devices", "extensions"):
            source_dir = join(get_simics_root(), "src", subdir)
            try:
                possible.extend(os.listdir(source_dir));
            except EnvironmentError:
                pass
        if possible:
            possible.sort()
            print "Source is available for:", ' '.join(possible)
        else:
            print "Source is not available for any module"

def create_machine_scripts(workspace, options):
    if options.dry_run:
        return
    
    if options.verbose:
        print "Creating target start scripts"

    for f in glob.glob(join(get_simics_root(), "targets", "*", "*.simics")):

        script = basename(f)
        target = basename(dirname(f))

        target_ws_dir = join(workspace, "targets", target)
        if not isdir(target_ws_dir):
            try:
                os.makedirs(target_ws_dir)
            except OSError, msg:
                print ("Failed to create directory for target %s: %s"
                       % (target, msg))
                continue

        script_path = join(target_ws_dir, script)
        backup_file_if_modified(workspace, script_path)
        
        f = open(script_path, "w")
        f.write("add-directory \"%script%\"\n")
        f.write("run-command-file \"%%simics%%/targets/%s/%s\"\n"
                % (target, script))
        f.close()

def print_version(*args, **kwargs):
    print
    print "Simics version:  ", get_simics_version()
    print "Installed at:    ", get_simics_root()
    print
    
    sys.exit(0)

if __name__ == "__main__":
    descr = """\
Creates or updates a Simics workspace for user scripts and modules.
If workspace directory is omitted, the current working directory is used.
"""

    # Do not forget to update the programming-guide when adding new switches
    parser = OptionParser(usage = ("workspace-setup [options] [workspace]"),
                          description = descr)

    parser.add_option("-v", "--version",
                      action = "callback",
                      callback = print_version,
                      help = ("Prints information about Simics "
                              "(version, installation directory)."))

    parser.add_option("-n", "--dry-run",
                      action = "store_true",
                      dest = "dry_run",
                      help = ("Execute normally, "
                              "but do change or create any files."))

    parser.add_option("-q", "--quiet",
                      dest = "verbose",
                      action = "store_false",
                      default = True,
                      help = ("Do not print any info about the "
                              "actions taken by the script."))
    
    parser.add_option("--force",
                      dest = "force",
                      action = "store_true",
                      help = ("Force using a non-empty directory as "
                              "workspace. Note: even with this option, "
                              "modules in the module sub-directory will "
                              "*not* be overwritten. Modules must be "
                              "removed manually before they can be "
                              "overwritten."))

    parser.add_option("--check-workspace-version",
                      dest = "check_version",
                      action = "store_true",
                      help = ("Check the version of the workspace, and "
                              "return 1 if it needs creating/upgrading, "
                              "0 otherwise."))

    if module_building_enabled:
        parser.add_option("--device", "--dml-device",
                          action = "append",
                          metavar = "DEVICE_NAME",
                          dest = "dml_modules",
                          default = [],
                          help = ("Generate skeleton code for a device, "
                                  "suitable to use as a starting point for "
                                  "implementing your own device. The default "
                                  "implementation language is DML. See the "
                                  "--c-device and --py-device options for "
                                  "creating devices using other languages. "
                                  "If the device already exists, this option "
                                  "is ignored. To recreate the skeleton, remove "
                                  "the device directory."))
                              
        parser.add_option("--c-device",
                          action = "append",
                          metavar = "DEVICE_NAME",
                          dest = "c_modules",
                          default = [],
                          help = ("Similar to --device, but creates a device "
                                  "using C instead of DML."))
        
        parser.add_option("--py-device",
                          action = "append",
                          metavar = "DEVICE_NAME",
                          dest = "py_modules",
                          default = [],
                          help = ("Similar to --device, but creates a device "
                                  "using Python instead of DML."))
        
        parser.add_option("--copy-device",
                          action = "append",
                          metavar = "MODULE_NAME",
                          dest = "copied_modules",
                          default = [],
                          help = ("Copies the source for a sample device/module "
                                  "into the workspace. The files will be "
                                  "copied from the Simics installation. "
                                  "If the device already exist in your "
                                  "workspace, you must manually delete it "
                                  "first."))

    (options, args) = parser.parse_args()

    if len(args) == 0:
        workspace_raw = os.getcwd()
        workspace = workspace_raw
        explicit_workspace = False
    elif len(args) == 1:
        # make sure that the workspace passed as argument is a native path
        workspace_raw = args[0]
        workspace = abspath(nativepath(workspace_raw))
        explicit_workspace = True
    else:
        parser.error("incorrect number of arguments")

    if options.check_version:
        if is_workspace(workspace):
            if get_workspace_version(workspace) != get_simics_version():
                print "Workspace needs upgrading:", workspace_raw
                sys.exit(1)
            else:
                print "Workspace is up-to-date:", workspace_raw
                sys.exit(0)
        else:
            print "Workspace does not exist:", workspace_raw
            sys.exit(1)

    if isdir(workspace) and not is_workspace(workspace) and \
       not options.force and len(os.listdir(workspace)) > 0:
        print "The workspace directory:"
        print "\n\t%s\n" % workspace_raw
        print "already exists and is non-empty. Select another directory,"
        print "or use the --force flag."
        sys.exit(1)

    if module_building_enabled:
        if options.dml_modules and not isdir(join(get_simics_root(), "src",
                                                  "devices", "empty-dml-device")):
            print "The DML toolkit is required to create DML devices."
            options.dml_modules = []

    if options.verbose:
        print "Setting up Simics workspace directory:",
        print workspace_raw

    create_directories(workspace, options)

    # this needs to be done before the build makefiles are written
    # to make sure that cygwrap.exe exists
    if cygwin_platform() and not isfile(join(workspace, "cygwrap.exe")):
        build_cygwrap(workspace, options)

    # start-scripts
    create_start_script(workspace, options)

    # makefiles
    create_compiler_makefile(workspace, options)
    create_config_makefile(workspace, options)
    create_workspace_makefile(workspace, options)

    # modules
    if module_building_enabled:
        create_module_skeletons(workspace, options)
        create_copied_modules(workspace, options)

    # machine-scripts
    create_machine_scripts(workspace, options)

    if num_backed_up_files > 0:
        print "Backed up %d files during workspace upgrade." % num_backed_up_files

    # should be last, so the workspace-version file has mtime larger
    # than all other created files
    create_version_file(workspace, options)

    if not options.verbose:
        sys.exit(0)

    # NOTE: only informative printouts below
    print
        
    if module_building_enabled:
        print "Finished. To build devices:"
        print
        if explicit_workspace:
            print "\t$ cd %s" % workspace_raw

        print "\t$ make"
        print

    print "To start Simics, use the scripts under targets/<arch>/. "
    print "For example:"
    print
    if explicit_workspace and not module_building_enabled:
        print "\t$ cd %s" % workspace_raw

    if sys.platform == "win32":
        print "\t$ ./simics.bat targets/ebony/ebony-linux-firststeps.simics"
    else:
        print "\t$ ./simics targets/ebony/ebony-linux-firststeps.simics"

    print
