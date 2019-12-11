==================================
| RELEASE NOTES FOR SIMICS 3.0.x |
==================================

General
-------

See file RELEASENOTES for new features in Simics 3.0. This file only contains
changes since the first Simics 3.0, build 1311.

Build 1406
==========

 * Core: Add a newline to the output from SIM_puts() (which Simics redefines
   puts() into), so it works like standard puts() (bug 9654).

 * Core: Image saving (when saving a configuration or persistent state)
   should now cope with large files better on x86-linux. (bug 9980)


Build 1404
==========

 * trace-io: Do not crash on transactions larger than 8 bytes (bug
   9232).


Build 1403
==========

 * MIPS-5kc: The 'dadd' and 'dsub' instructions now writes to the correct
             register (bug 9052).
 * x86 PC model: Clock twice as fast on machine cosmo bug fixed (bug 8954).


Build 1402
==========

 * PPC-603e: enabled the 'fsel' instruction (bug 8687).
 * g-cache:  reset-statistics now clears all statistic attributes (bug 8789)


Build 1401
==========

 * PPC: fixed bug where user SPR handlers were allowed to call fetch/stash for
        user defined SPRs. This resulted in a corrupt processor state.
        (bug 8660).

 * Core: memory-spaces now handle correctly ignored splitted transactions. Fix
   a bug where a flash memory device would not receive a complete transaction
   when the access size was greater than the flash bus size.


Build 1400
==========

 * PPC/Altivec:  The <tt>lvsl</tt> instruction did not return the correct
   result for a sixteenth of the possible input values; this has been fixed.
   No other instructions were affected by this defect.

 * PPC: System management interrupt implemented. It can be triggered by
        appending "System_management_interrupt" to the <pending_exceptions>
        attribute on the PPC processor object.


Build 1399
==========

 * Translator mappings with RAM/ROM targets now have a default align-size of
   8K. An align-size of 0 caused accesses across 8K boundaries to either
   silently fail or crash Simics (bug 8593).


Build 1397
==========

 * NS16550: Fix bug where an assertion error occurred when FIFO mode was
   disabled while there still was characters in the FIFO (bug 8513).


Build 1394
==========

 * SPARCv9: Fix skipped magic instruction when running in fast mode (bug 8458).


Build 1393
==========

 * MPC8x4x: Global timers implemented in the PIC.


Build 1392
==========

 * nand-flash: fixed checkpointing (bug 8363).


Build 1391
==========

 * Real Network: Real network through the bridge method with mac address
   translation now allows multicast packets into the simulated network
   (bug #8351).


Build 1390
==========

 * x86: raise SMP limit from 15 to 255 processors. Using more than 15
   processors requires an ACPI-aware OS (such as Linux 2.6) for SMP to work.


Build 1389
==========

 * MPC8x4x: Don't crash when TSEC/PHY is disconnected from ethernet link.

 * The 'ethereal' command will start wireshark instead, if it is available.

 * win32-text-console correctly detects the size of the window.

Build 1388
==========

 * i82546: Better reset support and receive interrupt coalescing (bug 1125).


Build 1387
==========

 * Classic PPC processors: Optimized segment register updates. (bug 1715)

 * PPC-4xx: Corrected a bug in the EMAC controller that made it unable to
   handle ehternet multicast. (bug 8211)


Build 1386
==========

 * Fixed a bug where swap files were not removed after saving a configuration
   in some cases; this was a regression from build 1382. (bug 8132)

 * Fix Cygwin and Windows path handling in workspace-setup.

 * MPC8x4x: PCIe controller now handles 32-bit I/O and 64-bit memory windows


Build 1385
==========

 * PowerPC: Fixed a bug where the fmadd, fmsub, fnmadd and fnmsub instructions
   gave inaccurate results in rare cases. (bug 8147)


Build 1383
==========

 * service-node: The DHCP service no longer crashes Simics if the host table is
   updated while handing out DHCP leases. (bug 8047)

 * A memory leak when reading the <memory-space>.memory attribute was plugged.
   (bug 8048)

 * Marvell, Discovery controllers: MPSC interrupts delay are based on
   the baud rate (bug 8061).


Build 1382
==========

 * symtable: Function symbols without size information are now recomputed
   each time new symbols are added so that they extend to the start of
   the next symbol (bug 7974)

 * Fixed a crash occurring sometimes when re-trying write-configuration
   after failing because of insufficient disk space (bug 7955)

 * ELF symbols can now be read for the MSP430 architecture (bug 7993)

 * Niagara: Update to boot with latest firmware files from OpenSPARC.

 * MSP430: There is no longer an extra instruction step taken in certain
   cases when the CPU is turned off (sleep mode) (bug 7756)

 * Marvell, Dicovery controllers: mpsc, sdma, ethernet, idma,
   timer/counter units now supports level triggered interrupts (bug 8021).

 * Improved error handling for component connect methods.

 * If an image uses a file in read-write mode, this file must be no smaller
   than the image. Violation of this condition is now an error. (bug 8033)


Build 1380
==========

 * image / craff utility: Corrupt craff files are now detected better with
   an improved error message. (bug 7873)

 * craff utility: new --verify option for testing file integrity. (bug 7874)


Build 1379
==========

 * Fix crash occurring on device access on long runs with over 64 000 memory
   remappings.


Build 1378
==========

 * PPC-4xx: Corrected a bug in the i2c controller causing the STC[SCMP] to be
   set when in chain mode. (bug 7746)

 * MPC8x4x: UPM mode of the LBC memory banks is now supported.


Build 1377
==========

 * An ABI compatibility issue has been fixed. The problem was identified when
   when running with a newer add-on package (containing processor models) on
   top of an older Simics base package (and the core hap list had changed).
   (bug 6595)

 * Fixed a Simics Central crash caused by an assertion failure. (bug 7240)


Build 1376
==========

 * MPC8x4x: PCI Express host controller now returns 0xff when trying to read
            a non-existing device's PCI configuration space.


Build 1375
==========

 * Fixed race in branch creation.


Build 1373
==========

 * A memory leak in SIM_load_binary was fixed. (bug 7424)

 * MPC8x4x models: the TSECs now polls Tx descriptors if DMACTRL.WOP is set.

 * MPC8x4x models: the TSECs now handles bandwidth limitations. This fixes
   problems such as fragmented frames not being transmitted. (bug 7433)

 * ppce500: add missing rfci instruction. (bug 7505)

 * A problem caused by an issue with one of the speed enhancements in Simics 
   was fixed (bug 7404).

 * PPC: the timebase was calculated incorrectly in rare cases, caused by an
        overflow. Syptoms were strange jumps in timebase values, usually
        backwards. (bug 7523)


Build 1371
==========

 * PPC64: branch instructions now compare only the low 32 bits of CTR when
          MSR[SF] is 0. (bug 7350)

 * PPC: bdnz 0, when CTR=0 will loop for the correct number of iterations
        instead of zero. (bug 7370)

 * wait-for-hap "Core_Continuation" in a script branch no longer crashes
   with an assertion failure. (bug 7382)


Build 1370
==========

 * MV64460: new register, CPU_Ordering_and_Dead_Lock_Control @ 0x2D0


Build 1369
==========

 * x86 targets: Bug causing program counter corruption fixed. (bug 7184)

 * The checkpoint-merge script does not fail on source checkpoints with a
   .raw file. (bug 7517)


Build 1368
==========

 * Bug fix: <text-console>.record-stop would in some cases return garbage
   characters.

 * The server-console class now implements the record-start/stop and
   capture-start/stop commands. (bug 7111, 7117)

 * x86 targets: properly handle pending interrupts during reset. (bug 5153)

 * Bug fix in the 'new-std-server-console' command.

 * 440gp/gx-devices: DMA scatter/gather fix. (bug 5775)


Build 1367
==========

 * A rare bug when machine-synchronised events were posted from object
   initialisation code and processors were reordered later (leading to
   an assertion failure), was fixed. (bug 7030)

 * Marvell controllers: IDMA_Interrupt_Cause and IDMA_Interrupt_Mask
   now support partial accesses. PCI access control fix when using old
   setups.


Build 1366
==========

 * Symtable: Stab types 0x2e and 0x4e are now recognised (but ignored),
   eliminating warnings. (bug 7028)

 * MV64460
  - removed registers
      SRAM_Test_Mode                                  @ 0x03F4
      SRAM_Error_Parity                               @ 0x03A8
      SDRAM_ECC_Counter                               @ 0x1458
      DFCDL_Indications                               @ 0x149C
      DFCDL_Probe                                     @ 0x14A0

  - added registers (functionality unimplemented)
      CPU_Control_CPU_Interface_Sync_Barrier_Control  @ 0x01C0
      SRAM_Error_Mask                                 @ 0x02D8
      SRAM_Error_ECC                                  @ 0x03A8
      SRAM_Calculated_ECC                             @ 0x0308
      SRAM_Single_Bit_Error_Counter                   @ 0x02E0
      RAM_Double_Bit_Error_Counter                    @ 0x02E8
      Dunit_Interrupt_Cause                           @ 0x14D0
      Dunit_Interrupt_Mask                            @ 0x14D4
      SDRAM_CS0_Single_Bit_Error_Counter              @ 0x1458
      SDRAM_CS0_Double_Bit_Error_Counter              @ 0x145C
      SDRAM_CS1_Single_Bit_Error_Counter              @ 0x1460
      SDRAM_CS1_Double_Bit_Error_Counter              @ 0x1464
      SDRAM_CS2_Single_Bit_Error_Counter              @ 0x1468
      SDRAM_CS2_Double_Bit_Error_Counter              @ 0x146C
      SDRAM_CS3_Single_Bit_Error_Counter              @ 0x1470
      SDRAM_CS3_Double_Bit_Error_Counter              @ 0x1474
      DunitMMask                                      @ 0x14B0
      EUPCR0                                          @ 0x20A0
      EUPCR1                                          @ 0x20A4
      EUPCR2                                          @ 0x20A8
      EUC                                             @ 0x20B0
      GBE_DFCDL_Configuration0                        @ GBE_OFFSET + 0x2100;
      GBE_DFCDL_Configuration1                        @ GBE_OFFSET + 0x2104;
      GBE_DFCDL_Status                                @ GBE_OFFSET + 0x210C;
      GBE_SRAM_Address                                @ GBE_OFFSET + 0x2110;
      GBE_SRAM_Data0                                  @ GBE_OFFSET + 0x2114;
      GBE_SRAM_Data1                                  @ GBE_OFFSET + 0x2118;
      GBE_DFCDL_Probe_Ctrl                            @ GBE_OFFSET + 0x2120;


Build 1365
==========

 * x86 targets: Multibyte mappings in port-space only match if the access is
   towards the mapped base address. (bug 6994)

 * service-node: Handle acknowledgment of a previous data packet in a correct
   way. (bug 6970)


Build 1364
==========

 * All processors in fast mode: Reversing after break-exception now works
   reliably. (bug 6960)

 * Raise exception when more than one processor with the same processor number
   is created (bug 6464).


Build 1363
==========

 * MV64360: MSwapEn, SSwapEn support. Better PCISwap support. New
   discovery-pci-bus.


Build 1362
==========

 * Symtable bug fix: Arrays are now printed correctly (bug 6899)

 * Real-network: close socket when connection to real host fails (bug 6886).

 * I82546: The second controller now uses INTB pin for interrupts. (bug 6906)


Build 1361
==========

 * Support for ABS symbols (constants) in ELF files added to symtable
   (bug 6880).

 * The TFTP server now closes the connection correctly after a session has
   ended. As a result, Simics no longer crashes if more packets are sent to
   closed session's port number (bug 6856).

 * Bug fix: Objects created by components could in some cases have identical
   names with no error reported. (bug 5416).

 * The checkpoint-merge script does not fail on source checkpoints without any
   .raw file. (bug 6579)

 * In the Windows GUI, selecting File->Exit or closing the main window to shut
   down Simics will now wait for the simics backend process to exit correctly
   instead of just terminating it. (bug 6513)

 * Windows host: Cygwin GNU make 3.80 included with Simics since more recent
   versions do not support DOS file names.


Build 1360
==========

 * Added support for floating point values in symtable (bug 63).

 * Windows host: Fixed module build problem found on some hosts. (bug 5491,
   undefined reference to __EH_FRAME_BEGIN__.)


Build 1359
==========

 * A rare memory corruption in conjunction with data breakpoints was fixed
   (bug 6777).

 * MPC8548: default kernel now supports both PCI Express and RapidI/O.


Build 1358
==========

 * MV64xxx: wde/wdnmi signal is only raised/lowered once.

 * MV64xxx: GoodFramesReceived and GoodFramesSent counters implemented.

 * Symtable: Eliminated a crash when a function appeared in stabs without
   information about what file it belongs to (bug 6746).


Build 1357
==========

 * MPC8x4x: tsec transmission bug fixed (bug 6552).

 * Fiesta target: Corrected physical memory mappings.

 * New hap: Core_Conf_Object_Pre_Delete. The hap is called before an object is
   deleted, allowing the hap handler to access the object.

 * PPC-403/405/440: the dcr-space attribute is now 'required'. If your
   configuration for some reason does not need a DCR space, you can use an
   empty memory-space (bug 6380).

 * The 'pty-console' class was renamed to 'host-serial-console'. The old name
   is still available as a class alias.

 * The <symtable>.pos command now splits its argument at the last colon
   instead of the first, to allow Windows drive letters in the file name
   (bug 6702).


Build 1356
==========

 * MSP430: There is now a magic instruction for this architecture,
   "bis r0,r0" (0xd000).

 * MSP430: Instruction tracing is now implemented.

 * Two new argument types available for building CLI commands:
   string_set_t and bool_t. See the Programming Guide for details.

 * The 'hex' commands returns a string instead of printing the converted value.


Build 1355
==========

 * PPC-e500: correct l1cfg0 and l1cfg1 initial values (bug 6574).


Build 1354
==========

 * The cpus_may_share_memory attribute in the sim object has changed from a
   "session" to an "optional" attribute. Consequently the attribute will be
   saved in checkpoints. (bug 6041)

 * Fiesta Serengeti, Sunfire targets: Solaris 10 installation scripts updated
   for the most recent Solaris 10 version (6/06 aka update 2).

 * Non-module directories allowed in the [workspace]/modules/ (bug 6506).

 * New version of the SimicsFS kernel module for Linux available for download
   at https://www.simics.net/pub/. (SimicsFS version 1.6).

 * Hardware IP checksum bug fix in the BCM570xC devices.

 * Fix of I2C device bug that caused problems on Fiesta target systems.


Build 1353
==========

 * x86-440bx target: report a correct APIC ID for each processor in the BIOS
   ACPI tables. This fixes problems where the Linux kernel on tango would only
   activate some of the processors in a multi-processor system.

 * Initiating signal-bus from checkpoints now do not cause errors for connected
   unnamed ports.

 * ARM targets: A bug in the ARM MMU that caused invalid virtual to physical
   address translations has been fixed (bug 6467).


Build 1352
==========

 * A new command, break-log, is now available to break on log messages.

 * The etg can now be restarted properly (bug 6411)

 * SIM_get_object now reports the name of the requested object when it does
   not exist.

 * Simics Hindsight license is not checked out until using a hindsight command
   or loading the rev-execution module.


Build 1351
==========

 * ARM targets: The bx instruction has been implemented for jumps to ARM mode
   (bug 6406).


Build 1350
==========

 * x86 MAI: make HLT Sync#2 to conform the the new internal
   implementation. This probably fix most of the HTL bugs reported with x86
   MAI.


Build 1349
==========

 * A bug causing output to the command-line console to deadlock under certain
   circumstances involving Python threads was fixed. (bug 5949).

 * PPC-targets: the mftb instruction will now be disassembled with a warning
   about invalid TB register if the encoded tbr is not 268/269:

     mftb r6,284  # invalid TBR

   mfspr where spr is one of the TB registers (268/269/284/285) is now
   disassembled as:

     mfspr r6,268  # utbl

   to avoid confusion with the mftb instruction. (bug 6225).

 * A bug causing port forwarding to randomly fail on Solaris host was fixed.
   (bug 6286)


Build 1348
==========

 * It is now possible to call SIM_instruction_read/write_input/output_reg()
   for the Y register on sparc v9 target (bug 5946).

 * Output handlers written in Python will no longer be passed a string with
   garbage at the end (bug 5235).

 * Configurations saved while a cpu was stalling are now loaded correctly.
   (bug 6128)

 * PPC-targets: warn when reading from TBL/TBU (spr #284/285),  since these
   are for writing only. SPRs #268/269 should be used for reading.


Build 1347
==========

 * Real-network: loading a checkpoint no longer results in:
   "[error] setting attribute link_status_enabled in..." 
   (bug 6154)

 * Symtable: Stack tracing for PowerPC (32 and 64-bit) improved (bug 6136);
   the return address of the current function is now more reliably retrieved.


Build 1346
==========

 * UltraSPARC targets: Solaris 10 installation scripts updated for Solaris 1/06
   (Solaris 10 Update 1).


Build 1345
==========

 * Fixed an assertion error in ethernet-link that failed under heavy load.
   (bug 5053)

 * X86-64 targets: Bug that caused the cosmo dump to fail during boot on 32-bit
   x86 hosts fixed (bug 5982).


Build 1344
==========

 * PPC-970fx: decrementer exception is now level sensitive (bug 5995).

 * MAI: fix broken SIM_instruction_read_input/output_reg functions.


Build 1343
==========

 * LEON2 based machine 'leon2-simple' included in the public Simics package.

 * Simulated machines can now communicate with hosts behind a real router in
   the "bridge" real-network case with MAC address translation enabled. The
   'gateway_ip' attribute has to be set manually in the real-network object for
   this to work.

 * Bug fix for discovery system controllers map/demap functionality.


Build 1342
==========

 * If an object is initialized with a class attribute, a warning is emitted,
   as this is almost always a mistake (bug 5889).
   This warning will become a hard error in a future release, so initializing
   an object with class attributes should be considered deprecated.

 * Performance of SIM_continue() for short simulation runs when no console
   windows are used has been improved. (bug 5891)

 * <memory-space>.del-map can now remove mappings from a specific base address.
   (bug 5895)

 * Fix truncated Python traceback when SIM_add_configuration fails because
   of an invalid configuration class name (bug 5894).

 * Syntax bug fix in Solaris 10 installation scripts for UltraSPARC targets.

 * 64-bit PPC: Raise log level for informational message when executing
   an enabled ATTN instruction, and don't print anything at all if a hap
   function has been registered to handle it.

 * Symtable no longer crashes when reading binaries with Stabs debug info
   of very long source files (>65535 lines). (bug 5918)


Build 1341
==========

 * Symtable is now slightly less chatty with respect to messages that do
   not necessarily indicate an error. Raise the log-level of the symtable
   object to get more of them.

 * PPC-e500: an SPE unavailable exception no longer triggers an assertion.


Build 1340
==========

 * Simics no longer crashes when a too small (less than 4 bytes) Ethernet
   frame is injected (using the attribute inject_packet). Bug 5832.

 * CLI and Python output (echo/print) from script branches would sometimes get
   lost or be delayed (bug 5805); this is no longer the case.

 * SIM_describe_interface is obsolete; it was only used internally for
   generating documentation. (bug 5854)

 * Simics will now warn on attempts to register a class attributes not marked
   as Pseudo or Session, as such attributes cannot be saved in configurations
   (bug 5858).


Build 1339
==========

 * X86 target: New Fedora Core 5 disk image available. See the Garget Guide and
   the 'tango' scripts in the targets/x86-440bx directory for more information.

 * X86-64 target: New Fedora Core 5 disk image available. See the 'cosmo'
   scripts in the targets/x86-440bx directory for more information.

 * SunFire target: New Aurora 2.0 (Fedora Core 3) disk image available. See the
   Target Guide and the 'cashew' scripts in the targets/sunfire directory for
   more information.

 * X86 targets: problems with checkpoint of CR3 and TSC were fixed. These
   problems probably caused the soft-lockup error report from recent Linux
   kernels.

 * X86 targets: a problem that caused a 1030 pseudo-exception to interrupt the
   simulation was fixed.


Build 1338
==========

 * The functions SIM_register_named_interface, SIM_get_named_interface, and
   SIM_get_named_class_interface were added as synonyms to their port interface
   equivalents for backward compatibility. They should not be used in new code.
   (bug 5796)


Build 1337
==========

 * Uncaught frontend exceptions that occur in callbacks written in Python will
   now cause a stack trace to be printed, as it is a most likely sign of a
   programming error. The new API call SIM_attribute_error() should be used
   inside attribute getter/setter methods to give extended error information,
   in preference to SIM_frontend_exception. (bug 5720)

 * Reading debug info in stabs format is now much faster when it contains
   many function names missing from the symbol table of the same file.
   (bug 5755)


Build 1336
==========

 * UltraSPARC T1 model added. For more information see the Target Guide for the
   "Niagara Simple" system.

 * UltraSPARC IV+ model included in packages with the Serengeti architecture.

 * The "named interface" API has been changed to "interface ports". The new API
   functions are named SIM_register_port_interface, SIM_get_port_interface, and
   SIM_get_class_port_interface.

 * New version of the SimicsFS kernel module for Linux available for download
   at https://www.simics.net/pub/.

 * Minor bug fix in the ISP2200 device, making it work with Solaris 10.


Build 1335
==========

 * PPC-targets: User-mode register aliases (e.g. utbl) can now be used with
   Core_Control_Register_Read and Core_Control_Register_Write. (bug 5668)

 * Fix for a bug in the floppy controller that could trigger the following
   assertion: src/devices/82077/82077.c:750

 * X86 targets: Processors implementing the DAZ bit in the mxcsr register do
   not incorrectly generate GP fault when this bit is written. (bug #5680)

 * X86 targets: Minor PCI device related bug fixes in the BIOS.

 * X86 targets: The local APIC timer now posts interrupts on the time queue,
   which makes it works properly even when the CPI rate is different from 1.

 * Building user modules on Windows 2000 hosts should work again.

 * The sim object will print a message as each object being saved at log
   level 3. At level 4, there will be additional messages as each attribute is
   read or written as part of a configuration load/save. (bug 5524)

 * X86 targets: Fix to prevent BSP processor from being disabled on reboot.

 * Voodoo3: Missing external VGA registers are now saved in checkpoints.


Build 1334
==========

 * Fix memory leak when invoking hap callbacks written in Python. (bug 5631)


Build 1333
==========

 * PowerPC 440/405 UIC: When a device lowers an interrupt towards the UIC the 
   interrupt is kept unchanged in the status register and needs to be
   explicitly cleared by software. Previously the status register bit was
   cleared when the device lowered the interrupt. (bug 5569)

 * X86 targets: New MSR implementation (many bug fixes and performance
   improvements). MSRs are not printed by 'pregs -all' anymore, use <cpu>.msrs
   instead.

 * The Simics main binary is not linked with libstdc++ anymore. Any user
   modules written in C++ should be linked agains libstdc++ themselves. (This
   is done automatically when calling the C++ compiler to link the module).


Build 1332
==========

 * PPC32 classic targets: the MMU now correctly considers the 'G' bit when
   checking that instructions are not fetched from guarded memory. Previously
   it incorrectly looked at the 'W' bit instead.

 * There are no longer any restrictions regarding what type signatures are
   allowed when registering a new hap type (SIM_hap_add_type) as long as they
   only used the permitted types. (bug 5534)

 * The cb_func_*_t function pointer typedefs are now deprecated and will be
   removed in a future release. They are no longer used by any part of the
   Simics API.


Build 1331
==========

 * TRUE and FALSE added to CLI as aliases for 1 and 0.

 * PPC-targets: enabling floating-point exceptions (MSR[FE0 FE1]) when there
   exist enabled exceptions in FPSCR will now trigger an FP enabled exception.
   (bug 5511)

 * PPC-targets: cache management instructions that cannot be translated by the
   MMU are no longer sent to the caches (bug 5531).

 * PPC-targets: a bug that caused a processors reservation (for conditional
   stores) to not be invalidated in fast mode has been fixed (bug 5533).


Build 1330
==========

 * The help command now understands the object->attribute syntax.

 * The 'list-hap-callbacks' output was extended with hap callback index/range.


Build 1329
==========

 * Processors that were disabled when a checkpoint was saved will now be
   disabled properly when it is loaded. Previously, this was not always the
   case. (bug 5463)

 * The CPU switch time is now calculated with respect to the correct processor
   (number 0) after reading a checkpoint where multiple processor frequencies
   were used. This was previously not always the case, but depended on hash
   table ordering. (bug 5463)

 * The swap directory can now be changed even after swapping has started. This
   makes it easier to save a checkpoint when there is a shortage of disk space
   where the swap files are written. (bug 2344)


Build 1328
==========

 * The new command 'new-gdb-remote' should be used instead of 'gdb-remote' 
   to create gdb debugging connections (bug 5322)

 * PPC targets: improvements to floating-point instructions:
       - Correct setting of FPSCR status and exception bits.
       - Correct handling of floating-point exceptions (returning the correct
         result and setting FPSCR accordingly).
       - NaN propagation.
       - Bit correct single-precision and fused multiply-add instructions (not
         including estimate instructions).

   (The estimate instructions fre/fres/frsqrte/frsqrtes will not always produce
    the same results as real hardware would.)

   The vector floating multiply-add instructions (vmaddfp/vnmsubfp) should now
   be bit-correct as well (bug 4346).


Build 1327
==========

 * Unix installer: Selecting a single add-on package does not install all
   available add-on packages. (bug #5355)

 * New Python functions for running a CLI command and returning the value:
   'run_command' and 'quiet_run_command'.

 * X86 targets: A bug causing incorrect compare results for some instructions
   in fast mode has been fixed. (bug #5402)


Build 1326
==========

 * The Linux process tracker now supports the UltraSPARC target. Tested with
   Linux kernel versions 2.4.14 and 2.6.13.

 * X86 targets: The state-assertion file format have changed and is now
   portable among hosts.

 * Unix installer: The support for installing all add-on packages is back.


Build 1325
==========

 * The 'set_persistent()' method in the image interface is available in Python.

 * X86 targets: A bug that caused incorrect behaviour when running in fast
   mode has been fixed. (bug #5348)

 * Bug fix for building modules with several classes in workspaces. (bug #5368)


Build 1324
==========

 * Calling stack_trace() in the symtable interface without a symtable set
   on the specified cpu will no longer crash Simics.

 * SIL680A: Correct attribute types of several attributes. (The incorrect
   type made it impossible to load checkpoints) (bug 5309).


Build 1323
==========

 * Port-space: two new Python-friendly functions were added to the port-space
   interface: read() and write().

 * Documentation for the Sim_Attr_Persistent and Sim_Attr_Internal flags was
   added to the Programming Guide.


Build 1322
==========

 * Linux hosts: Simics uses the NPTL thread library if available.

 * Simics will look for the user specific 'startup-commands' file in the
   workspace if one exists and not in the current directory.


Build 1321
==========

 * Some issues with the Rage XL device and simulated Windows fixed. (bug #5040)

 * PPC targets: Correct register number is now passed to
   Core_Control_Register_Read and Core_Control_Register_Write haps.

 * PPC64 targets: Execution of 'mtmsrd' instruction will now trigger a
   Core_Control_Register_Write hap.

 * The new-symtable and <symtable>.load-symbols commands now use the Simics
   search path to locate the specified file, for consistency with load-binary
   (bug 5187).

 * The connect_device() method of ethernet-link does not automatically register
   the device to listen on broadcast frames any longer. (bug 5169)

 * A class may now implement the same interface multiple times by using the new
   SIM_register_named_interface()/SIM_get_named_interface() functions.
   Interface instance names has to be capitalized, while interface type names
   may not start with an upper-case letter.

 * The parse_object_t struct is now an opaque data type, and direct access to
   its members from user modules is not possible. This is no actual restriction
   since it was never intended to be used directly anyway.


Build 1320
==========

 * New commands '<memory-space>.add-map' and '<memory-space>.del-map', and
   corresponding ones for <port-space>.

 * The .cpp file extension is treated as C++ in the module build environment.

 * Fixed problem with reverse DNS lookups of external IP addresses. (bug #5151)

 * Distributed checkpoints could sometimes not be restored.  This has been
   fixed. (bug #5117)

 * Fixed problem with multi-line inputs that were executed twice. (bug #5131)

 * The cause of the message "*** Checkpoint path '1' used by file, but no such
   entry found in the sim.checkpoint_path attribute" was fixed. (bug #4996)

 * Ethernet-link now forwards all multicast MAC addresses and not only the
   broadcast address.

 * X86 targets: Fix for configuration bug that sometimes caused the boot to get
   stuck for multi-processor machines.

 * X86 targets: Some object names used when building x86 configuration have
   been changed: a multithread cpu will now have threads called cpu0_0, cpu0_1,
   ... The corresponding apic and TLB will be cpu0_0_apic, cpu0_0_tlb, ... For
   single-threaded processors, the names would be cpu0, cpu0_apic and cpu0_tlb.

 * DML PCI support code: fix config_registers attribute which caused checkpoint
   problems for PCI-based DML devices.

 * PPC targets: user-mode read-only register aliases (e.g. utbl/utbu) are no
   longer exposed through attributes and the int_register interface. As a
   consequence, some register numbers will have changed.


Build 1319
==========

 * New make targets in user workspaces: clobber-<module> and clobber.

 * New optional workspace makefile 'module-user.mk'.

 * New 'set_processors()' function in component class. See the Programming
   Guide for more information.

 * New function 'clear_range' in the image interface, permitting a range of
   addresses to be cleared efficiently. (bug #5082)

 * New command 'save-component-template'.

 * "else if" now works in CLI.

 * New -c and -s flags to the 'ptime' (print-time) command for returning the
   cycle and step count.

 * It is now possible to run the Unix installer without installing any base
   package, to install new add-on packages only.

 * The installation directory is cached by the Unix installer between runs.

 * The Unix installer installs add-on packages for mutiple hosts
   simultaneously.

 * X86 targets: The 'connect-real-network' command works properly again when
   starting from a saved checkpoint. (bug #5097)

 * SDRAM/DDR/DDR2-memory-module 'registered' attribute removed. New attribute
   'module_type' added. Fixed warning for 'registered' attribute when loading
   old 3.0.x checkpoints.

 * Bug fix: Information about added connectors in the 'std-service-node'
   component is properly saved in checkpoints.

 * Bug fix: The 'connect-real-network' command now works in non-component
   based configurations with an already existing ethernet-link, but with no
   service-node.


Build 1318
==========

 * Support for building modules with Sun Studio 11 on Solaris/SPARC added.

 * The full path to the module files are included in the 'list-modules' and
   'list-failed-modules' commands when used with -v. (bug #4927).

 * PPC-64 targets: LR would in some rare cases be set to an incorrect value
   when a branch instruction was executed in 32-bit mode.


Build 1317
==========

 * The 'connect-real-network' command enables FTP ALG again as in Simics 2.2.

 * New section in the Programming Guide describing attribute data ownership.

 * New command 'defined' that checks if a CLI variable exists or not.

 * New command 'interrupt-script-branch' that may be used to cancel a
   suspended script branch.

 * Updated SimicsFS sources with support for Linux 2.6 kernels available for
   download from https://www.simics.net/pub/.

 * GDB 6.3 sources with hindsight support for use as gdb-remote available for
   download from https://www.simics.net/pub/.

 * A bug causing SIM_break_simulation() to be ignored in some cases was fixed.
   (bug #5032)

 * Improved support for system reset without any umount in the SimicsFS
   (hostfs) Simics module. (bug #5054).

 * Simics will now automatically raise the soft file descriptor limit to its
   hard maximum before opening any configuration (bug #5028).

 * The 'script-branch' command now returns a script branch ID.

 * The script branch ID was added to the output of 'list-script-branches'.

 * The SIM_hap_occurred() family of functions did not always return the
   SimExc_Break exception when a callback had requested a break. Now these
   functions always return SimExc_Break on a user callback break. (bug #5032)
   Note that this exception will be removed in future versions of Simics and
   new code should not rely on it, only clear it.

 * Function 1 of the '440gp-pci' and '440gx-pci' devices may be mapped at any
   address.

 * Serial connector in Serengeti system correctly marked as hotplug capable.

 * Multi-processor machines can now be created after the initial configuration
   has been loaded. (bug #5057)

 * UltraSPARC I/II (Solaris) hosts: A hardware bug (Spitfire erratum #57)
   has been worked around and no longer prevents Simics from running in
   fast mode. This was previous a problem with mmap in low memory. (bug 4923)

 * X86 targets: A bug that caused incorrect behaviour in multi-machine setups
   running in fast mode has been fixed. (bug #4998)

 * PowerPC targets: A Trace exception is now generated even after an
   mtmsr/mtmsrd that clears MSR[SE].

 * PowerPC targets: Data Address Breakpoints (DABR) were sometimes not
   triggered correctly when the DSTC was enabled.

 * PowerPC targets: Data Address Breakpoints (DABR) were sometimes not
   triggered correctly for accesses larger than 8 bytes (e.g. AltiVec
   loads/stores)

 * PowerPC-64 targets: CLI command print-slb no longer fails with:
   "TypeError: len() of unsized object"

 * PowerPC 4xx targets: Save DBSR[MRR] and TSR[WRS] with reset information when
   doing software resets. (bug #5009)


Build 1316
==========

 * The x86-hammer target now reports a 64 byte clflush line size. This allows
   Linux kernels depending on a non-zero clflush size to work. The default
   kernel in the 32-bit version of Suse Linux 10.0 is an example of such a
   kernel.

 * The ppc32-linux, ppc64-linux, and x86-linux process trackers have been
   replaced with a single Linux process tracker, which is able to auto-detect
   all kernel-version-dependent parameters necessary for its operation.

 * UltraSPARC IV model included in packages with the Serengeti architecture.

 * Memory-leak when loading checkpoints fixed.

 * New section in the Simics Programming Guide about writing components.

 * X86 targets: A bug that caused breakpoints to be ignored in fast mode have
   been fixed. (bug #4988)


Build 1315
==========

 * Improved support for selecting different compilers in a workspace. See the
   Programming Guide for updated information on the compiler.mk and
   user-config.mk files.

 * X86 targets: Fixed multi-processor configuration bug that caused Linux to
   hang early in the boot.

 * Added SimicsFS kernel module for Solaris 10 (UltraSPARC targets).

 * The SimicsFS kernel module for Solaris was renamed to simicsfs from hostfs.

 * The Solaris 10 installation scripts for UltraSPARC targets now install
   software from all four Solaris CD-ROMs.

 * New: Variants of step-instruction and reverse-step-instruction that follow
   a context.

 * Workspace changes: The WorkspaceEnvCheck.mk, Workspace.mk, and Config.mk
   files are not used anymore and can be removed.

 * flash-memory: fix an uninitialized value used when padding accesses to the
   flash bus.


Build 1314
==========

 * Better handling of watchpoints in gdb-remote when running in reverse.
   (bug #4065)

 * New -f flag in <component>.connect for selecting any matching connector.

 * The 'connect-real-network' command will create and connect components if
   a link and service-node are created.

 * The <console>.switch-to-* commands will also create and connect components.

 * Fix for 'bin/fake-python' and 'bin/workspace-setup' on Solaris hosts that
   have the LD_LIBRARY_PATH_64 environment variable set.

 * PowerPC targets: Correct disassembly of 'mcrfs' instruction, previously 
   incorrectly disassembled as a 'mcrf' instruction. (bug #4904)

 * PowerPC targets: Correct disassembly of 'nor[.]' and not[.] instructions,
   previously incorrectly disassembled wrong registers. (bug #4925)

 * Name-space version of the 'list-attributes' command added.

 * Fixed tab-completion of name-space command attributes (bug in build 1313).

 * New script 'targets/x86-440bx/dredd-floppy-install.simics' for booting from
   a floppy image.

 * The server-console module is now also supported on Windows host.


Build 1313
==========

 * BCM5703C correctly sends frames splitted on many descriptors. (bug #4762)

 * It is now configurable whether reboot of x86 machines should break the
   simulation. An attribute in the system component controls this.

 * Individual modules can now be "cleaned" in workspaces, using the
   "clean-<modulename>" target. (bug #4500)

 * The 'last_frame' in <ethernet-link> has been fixed so that it is possible to
   change the frame data, and not only drop the frame. The format of the
   attribute was also changed so that any scrips reading this attribute needs
   updating.

 * Make it easier for a GDB session to follow a context, by using the new
   <gdb-session>.follow-context command. (bug #4889)

 * The -> command will print the value of attributes that cannot be returned in
   CLI, instead of giving an error message.

 * Tab-completion in CLI on strings with spaces, and quoted strings now works
   properly on Unix hosts.

 * The running/stopped status in the title of the text consoles is now correct
   even if Simics is not controlled from the command line. (bug #4822)

 * Telnet signaling messages in the server-console-c module are now at log
   level 2.

 * generic-flash-memory: AMD command/autoselect addresses for 16-bit flash
   chips are now correctly decoded.

 * generic-flash-memory: write buffer size is now configurable via the
   write_buffer_size attribute.

 * generic-flash-memory: CFI query structure is no longer limited to 256 bytes.

 * Attributes can be changed in text-console components before instantiation.
   Also fixed problem with setting the console font in components.

 * The 'list-objects' command separates component objects from other objects.

 * A default port-forwarding IP address is configured for Ebony machines.


Build 1312
==========

 * The std-text-console component does not override geometry and color settings
   in the text-console object when a checkpoint is loaded. (bug #4786)

 * The console font can be set in the std-text-console component. (bug #4480)

 * The data associated with a hap is now available to the 'wait-for-hap'
   command in CLI. (bug #4794)

 * BOOTP support in the service-node works again. (bug #4001)

 * Support for building DML modules in user-install directories. (bug #4805)

 * New CLI commands 'signed' and 'signed<bit-width>' for integer conversion.

 * Support for changing port forwarding setup without a restart. (bug #2608)

 * Denormal-as-zero feature now supported on selected x86 targets. (bug #3136)

 * The external interrupt enable logic in the NS16[45]50 devices is now off by
   default. (bug #3801)

 * Experimental host accelerated floating point code documented. (bug #3855)

 * X86 targets no longer write reserved areas with FXSAVE. (bug #3872)

 * Unnecessary REX prefixes removed from dynamically generated code (bug #3935)

 * SCSI disk info command changed to show sectors instead of C/H/S. (bug #3992)

 * Fix for bug in the RageXL device that made it unable to switch from graphics
   to text mode in certain situations. (bug #4004)

 * Removal of some debug messages in the PIIX4 device. (bug #4022)

 * Host cpu profiling added to the system perfmeter module. (bug #4039)

 * Warnings when loading Simics 2.2.1 checkpoints were removed. (bug #4076)

 * Bugfix in the handling of the non-execute page table bit for x86 targets.
   (bug #4214)

 * Fix for problem with cop2 instruction decoding for MIPS targets. (bug #4228)

 * Better handling of unaligned accesses in the RageXL device. (bug #4401)

 * The instr_type_t It_* constants are now accessible from python. (bug #4569)

 * Commands that take an address as argument will truncate large integers.
   (bug #4807)

 * Added support for floating point values in the -> command. (bug #4806)

 * The craff utility can now accept a Unix block device directly as input.
   (bug 4731)

 * Error messages from Simics when signing modules are printed correctly.

 * Tab-completion fix for floats and for strings similar to floats. (bug #4811)

 * %simics% is saved non-expanded again (as in Simics 2.2) in the simics_path
   attribute in checkpoints.

 * New process tracker: Linux on x86 target. (bug #3770)

 * Setting the align-size in the memory-space map attribute now works even if
   no processor module is loaded. (bug #4824)

 * Generic flash memory: memory transactions that caused a flash error are now
   correctly ignored and not passed to the underlying memory as before.
