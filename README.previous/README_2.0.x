
Release notes for Simics 2.0
============================

Simics 2.0.27
-------------

 * MAI: Checkpoint restore bug fix for multi-processor configurations.

 * sample-micro-arch: A 'drain_queue' attribute added to help saving checkpoint
   in MAI mode. Wrong CPU test fixed (caused problem when loading checkpoints).

 * g-cache: fix MESI handling for transactions spreading over several cache
   lines

 * g-cache: fix penalty consistency by applying read-next to write-through
   transactions

 * g-cache: print out the total number of stalling cycles lost due to
   non-stallable transactions.


Simics 2.0.26
-------------

 * Solaris host: Support for building modules with the SunONE 9 compiler.

 * Paging bug fix for AMD64 target.


Simics 2.0.25
-------------

 * Simics/Fiesta model included (Sun Blade 1500 workstation).

 * X86 targets only: Fix for assertion error in local-memory.c.

 * Updated 8254 device. (Error message "Both CT or ST selected").

 * UltraSPARC targets: MMU fix, allowing newer SILO versions to run on Simics.

 * Simics MAI: fix locking to prevent timing-model from seeing the same
   transactions twice (this could lead to dead-lock problems).


Simics 2.0.24  (not public)
-------------

 * Several interrupt devices can be connected to the PCI bus.

 * The commands break-cr and trace-cr are now namespace commands of CPUs. This
   fixes problems with multi-cpu machines. The global break-cr/trace-cr
   commands now act on the current processor only.

 * Saving compressed checkpoints now works even when the image memory limit
   is used.

 * SPARC targets only: Hap bug fix in MMU for multiple haps on the same cycle.

 * Flash-memory: Allow 0xf0 reset in AMD unlock-bypass mode.

 * PCI-to-PCI bridges: Upstream mappings are only created if master enable is
   set in the command register.

 * gdb-remote: Support gdb "monitor" command to run Simics commands from GDB.


Simics 2.0.23
-------------

 * Option to create compressed images with the write-configuration and
   save-persistent-state commands. Usage:

       simics> write-configuration -z chkpnt

   Or for save-persistent-state:

       simics> save-persistent-state -z state

   Checkpoint images will still be left uncompressed if the image memory limit
   feature is active.

 * Checkpoint bug fix in the ISP2200 device.

 * x86: multiprocessor stalling problem when using -stall is solved.

 * New hap: Core_Device_Access_Memop lets you access the complete memory
   operation sent to the device. The commands break-io and trace-io use it to
   print out the initiator of each transaction.

 * g-cache: fix splitter to prevent reissue (as in all g-cache based
   hierarchies).


Simics 2.0.22
-------------

 * MAI: bug fix in mai_setup_stalling_instruction: current processor was used
   instead of in->cpu.

 * Removed incorrect assertion in AM79C960 device.


Simics 2.0.21
-------------

 * PowerPC: The altivec instructions lvsl/lvsr are now correctly executed on
   little-endian hosts (such as x86).

 * PowerPC: ppc4xx i2c controllers have been improved to set the STS[PT] and
   STC[SCMP] bits.

Simics 2.0.18
-------------

 * SPARC targets: %ccr bits are correctly labeled by the pregs-all command.

 * MAI: bugfix in the consistency controller: too conservative restrictions
   fixed.

 * MAI: bugfix in the consistency controller: current processor was used
   instead of mem_op->ini_ptr.

 * MAI: bugfix in the ooo-micro-arch module for multi-pro. Cycle handler was
   posted several times on the first CPU. 

 * Simics Central in batch-mode now exits when last Simics disconnects.

 * SPARC targets only: Updated Solaris install scripts to handle Solaris 9
   9/04.

 * MAI: bugfix for magic instructions, the wrong CPU was passed to the handler.

 * Bug fix: '<text-console>.break' now correctly breaks on strings that has an
   'Xterm_Break_String' hap installed.

 * Central: fix EINTR handling that may have cause only partial transfer
   problem with big packets.


Simics 2.0.17
-------------

 * x86: Helper script used to boot from simulated cdrom left a file descriptor
   opened which, if host-cdrom was used, prevented a user from opening the real
   cdrom tray until Simics was stopped. The file descriptor is now closed
   properly.

 * x86 MAI: Fix for HLT instruction which prevents the processor from halting
   forever.

 * PowerPC: Floating-point registers are now called fN (ie f13) instead of frN,
   for consistency with general PPC convention. The names frN are retained as
   aliases (so %fr13 still works) for some time, but are now deprecated and
   might go away in a future release.


Simics 2.0.16
-------------

 * PowerPC: Single-precision loads and stores (lfs, stfs etc) now convert the
   value correctly according to the architecture (and in undefined cases behave
   as a PPC750).


Simics 2.0.15 (not public)
-------------------------

 * Windows host only: The GUI console can now accept Emacs keyboard shortcuts.
   By selecting "Keyboard shortcuts: Emacs compatibility" in the preferences
   dialog, the following key-combinations can be used at the console prompt:
     control-a: go to the beginning of the input prompt
     control-e: go to the end of the input prompt
     control-k: cut out the text on the right of the cursor
     control-y: paste the contents of the cliboard at the cursor
     control-f: move the cursor forward one character
     control-b: move the cursor back one character
     control-n: recall the next history entry
     control-p: recall the previous history entry
     control-t: switch the order of the two characters on each side
                of the cursor
     control-w: delete a word to the left of the cursor
     control-d: delete a character to the right of the cursor
     control-x control-f: open new machine dialog
     control-x control-c: exit Simics

 * Windows host only: The default scrolling behaviour of the GUI console has
   been changed so that when new output is added, it will only scroll to the
   end if it was previously positioned at the end. The old behaviour can be
   obtained by selecting "Auto-scroll console: Always" in the preferences
   dialog.

 * The GUI versions of Simics (gsimics on UNIX, simics.exe on Windows) now
   support the same command line arguments as the CLI version of Simics.

 * Windows host only: A "New Session" toolbar button now exists.


Simics 2.0.14 (not public)
-------------------------

 * New '-bcd' and '-binary' flags to the <DS12887>.set-date-time and
   <M5823>.set-date-time commands.

 * The 'boot_sol8' variable for Serengeti and SunFire setups was replaced by
   the 'solaris_version' variable. Allowed values are currently 8 and 9.

 * X86 target only: Fix for selecting hyper-threading from the GUI.

 * Bug fix: hostfs checkpointing did not work properly when the host_root
   attribute had been changed.

 * Windows host only: Python path conversion problem with cygwin fixed.

 * Updated documentation for the 'Core_Instruction_Squashed' hap.

 * Updated documentation for the 'map_info_t' type.

 * SPARC targets: The mnemonics for LDUW, LDUWA, STW and STWA have been
   changed to lduw, lduwa, stw and stwa, following the recommendations in
   the architecture.

 * Minor bug fixes and improvements to the symtable module, mostly related
   to debug info produced by Sun's Forte compilers. Source line numbers may
   now exceed 65535 (using N_XLINE stabs), and file-scoped static variables
   are now handled somewhat better.


Simics 2.0.13 (not public)
--------------------------

 * SPARC targets only: %stick and %stick_cmpr included in pregs output.

 * Bug fix: The use of SIM_stall_cycle() in a multi-pro machine could cause
   one processors to advance the time without switching to the next cpu.

 * Bug fix: Removal of machine synching events didn't always work.


Simics 2.0.12
-------------

 * Some fixes were made in the Python/C function handling (i.e., when functions
   are passed through the Python API). This makes it possible to implement
   parts of the event poster interface in Python. There is a limitation, which
   is that the data pointers are now always passed to Python as None.

 * SPARC targets only: Improved performance for first part of Solaris boot, in
   particular when running with a large simulated memory.


Simics 2.0.11 (not public)
--------------------------

 * X86 target only: All Python based configuration script functions were moved
   to the x86_conf namespace. For example: Instead of using add_pci_dec21143()
   directly, the x86_conf.add_pci_dec21143() should be used.

 * Bug fix: Data could in some cases be corrupted in images larger than 8GB.

 * Bug fix: Saving checkpoint directly after saving persistent data now works
   correctly.

 * Fix of seg fault in ISP2200 module.

 * The readhist module is now a stand alone binary.


Simics 2.0.10 (not public)
--------------------------

 * The Simics Central protocol was modified slightly to handle some issues when
   continuing from a checkpoint. As a result, Simics and Simics Central in
   2.0.11 can not be connected to older Simics versions.

 * Several minor Simics Central problems fixed.


Simics 2.0.9 (not public)
-------------------------

 * Fixed memory leak in standalone Simics Central.

 * Fixes in some x86 target machine scripts.

 * MAI only: The LSQ is enabled by default when starting from an in-order
   checkpoint.

 * SYM53Cxx: Improved support for multiple controllers on a single SCSI bus.

 * SPARC on SPARC fix when running with -fast.


Simics 2.0.8
------------

 * SPARC targets only: New functions in the sparc_v9 interface for installing
   ASI handlers, allowing several SPARC cpu classes to be used simultaneously

 * Checkpoint bugfix in the DEC21xxx network devices.

 * MAI only: added attribute lsq_enabled to each CPU object. This makes it 
   possible to the disable the internal load/store queue.

 * Improved support for low min-latency values in Central communication.

 * Added support for injecting and modifying sent/received ethernet packets
   for each network device. (attributes 'current_packet', 'inject_packet').

 * New console handling commands:
     <text-console>.switch-to-server-console
     <server-console>.switch-to-text-console

 * You can now specify the cpu you want to debug in the gdb-remote command. If
   you do not specify a cpu it now uses the currently selected cpu by default,
   instead of cpu number 0 as it did before.

Simics 2.0.7
------------

 * Minor update of generic PCI Express code.

 * Bug fix in <cheetah-mmu>.d-probe, <cheetah-mmu>.i-probe commands.

 * Stall bug fix in x86/x86-64 MAI.

 * The path specified with the 'add-directory' command can start with %simics%
   to reference the current Simics base directory.

 * Image files found using the "Simics path" are now saved without the full
   path prepended in checkpoints. This, together with the '%simics%' addition,
   makes it easier to move checkpoints to new Simics versions.

 * Bug fixes in the DEC21x4x network devices.

 * Programming bug fix in AMD compatible flash memory.

 * Added aliases for Simics 1.6 classes 'x86-p4-stall' and 'x86-p2-stall'.

 * X86 target: Fixed boot performance problem.


Simics 2.0.6 (not public)
-------------------------

 * Customer specific release.


Simics 2.0.5
------------

 * X86 targets: Support for up to four serial ports.

 * X86 targets: BIOS fix for processor frequencies >= 5GHz.

 * Improved disassembly output. New command 'disassemble-settings'.

 * Serengeti and SunFire targets: PCI DMA accesses are not split into 8 byte
   chunks by the upstream DVMA mappings anymore. (Now split on 8K boundaries).

 * Support for more mailbox commands in ISP2200.

 * Fix for crash when running Simics Central standalone.


Simics 2.0.4
------------

 * Updated OBP for Serengeti, required by Solaris 9 (12/03) and Solaris 10.

 * Updates to the ISP1040 and ISP2200 devices.

 * Build environment fixes for modules using the Simics 1.4/1.6/1.8 API.


Simics 2.0.3
------------

 * Graphics console updated correctly when loading checkpoint from the GUI.

 * PPC targets only: gdb now works in the simulated system.


Simics 2.0.2
------------

 * Bug fix in '<memory-space>.map' command.

 * Bug fix for memory mappings with different priorities.


Simics 2.0.1
------------

 * First public release of Simics 2.0.


Simics 2.0.0 (not public)
-------------------------

 * Virtutech internal release.
