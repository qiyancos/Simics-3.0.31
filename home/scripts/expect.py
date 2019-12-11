
##  Copyright 2000-2007 Virtutech AB
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

import string
import sys

from gfx_console_common import *

# should only be called from branch
def wait_num_cycles(cycles):
	start_cycles = SIM_cycle_count(SIM_current_processor())
	wait_for_hap_idx("Core_Cycle_Count", start_cycles + cycles)

def wait_for_string(expect_string, timeout_cycles, sample_interval, vga_name = "vga0"):
	cycles_so_far = 0L
	if timeout_cycles == 0:
		cycles_so_far = "n/a"
	while timeout_cycles == 0 or cycles_so_far < timeout_cycles:
		SIM_continue(sample_interval)
		if timeout_cycles != 0:
			cycles_so_far = cycles_so_far + sample_interval
		try:
			text = SIM_get_object(vga_name).text_page
		except:
			text = []
		for line in text:
			if string.find(line, expect_string) != -1:
				print "Found '%s' within %s cycles" % (expect_string, cycles_so_far)
				return
	raise Exception("Timed out waiting for '%s'" % (expect_string))

graphics_break_reached = 0

def graphics_hap_handler(obj, con, id):
	global graphics_break_reached
	graphics_break_reached = 1
        raise SimExc_Break, "graphics break"

def wait_for_graphics(filename, timeout_cycles):
	global graphics_break_reached
	graphics_break_reached = 0
	eval_cli_line("con0.break %s" % filename)
	SIM_hap_register_callback("Gfx_Break_String", graphics_hap_handler, 0)
	SIM_continue(timeout_cycles)
	if not graphics_break_reached:
		raise Exception("Times out waiting for graphics '%s'" % filename)
	graphics_break_reached = 0

# should only be called from a script branch
def branch_wait_for_string(expect_string, timeout_cycles, sample_interval, vga_object = ""):
	if vga_object == "":
		vga_object = conf.vga0
        start_cycles = SIM_cycle_count(SIM_current_processor())
	cycles_so_far = 0
	if timeout_cycles == 0:
		cycles_so_far = "n/a"
	while timeout_cycles == 0 or cycles_so_far < timeout_cycles:
		wait_num_cycles(sample_interval)
		if timeout_cycles != 0:
			cycles_so_far = cycles_so_far + sample_interval
		try:
			text = vga_object.text_page
		except:
			text = []
		for line in text:
			if string.find(line, expect_string) != -1:
				print "Found '%s' within %s cycles" % (expect_string, cycles_so_far)
				return
	raise Exception("Timed out waiting for '%s'" % (expect_string))

def fkey_to_keystrokes(num):
	ret = []
	if num < 13:
		ret.append([0, num+1])
		ret.append([1, num+1])
	else:
		try:
			ret = char_to_keystrokes(num)
		except KeyError:
			raise Exception("fkey '%n' not supported." % (num))
	return ret

def string_to_keystrokes(str):
	ret = []
	for ch in str:
		c = ch
		for stroke in char_to_keystrokes(ch):
			ret.append((c, stroke))
			c = None
	return ret

def enter_string(obj, str):
	cli.pr("Typing: %s\n" % string.replace(str, "\n", "\\n"))
	for ch, stroke in string_to_keystrokes(str):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		SIM_continue(steps_per_keystroke())

def enter_fkey(obj, num):
	sys.stdout.write("Typing: F")
	sys.stdout.write(`num`)
	sys.stdout.write("\n")
	for stroke in fkey_to_keystrokes(num):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		SIM_continue(steps_per_keystroke())

def enter_backspace(obj):
	sys.stdout.write("Typing: Backspace\n")
	for stroke in specialchar_to_keystrokes('b'):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		SIM_continue(steps_per_keystroke())

def enter_escape(obj):
	sys.stdout.write("Typing: Escape\n")
	for stroke in specialchar_to_keystrokes('e'):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		SIM_continue(steps_per_keystroke())

def enter_winkey(obj):
	sys.stdout.write("Typing: Winkey\n")
	for stroke in specialchar_to_keystrokes('w'):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		SIM_continue(steps_per_keystroke())

def enter_alt(obj):
	sys.stdout.write("Typing: alt\n")
	for stroke in specialchar_to_keystrokes('a'):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		SIM_continue(steps_per_keystroke())

def enter_special(obj, char):
	sys.stdout.write("Typing special key: ")
	sys.stdout.write(`char`)
	sys.stdout.write("\n")
	for stroke in specialchar_to_keystrokes(char):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		SIM_continue(steps_per_keystroke())

def branch_enter_string(obj, str):
	cli.pr("Typing: %s\n" % string.replace(str, "\n", "\\n"))
	sys.stdout.flush()
	for ch, stroke in string_to_keystrokes(str):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		wait_num_cycles(cycles_per_keystroke())

def branch_enter_fkey(obj, num):
	sys.stdout.write("Typing: F")
	sys.stdout.write(`num`)
	sys.stdout.write("\n")
	for stroke in fkey_to_keystrokes(num):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		wait_num_cycles(cycles_per_keystroke())

def branch_enter_escape(obj):
	sys.stdout.write("Typing: Escape\n")
	for stroke in specialchar_to_keystrokes('e'):
		SIM_set_attribute_idx(obj, "key-event", stroke[1], stroke[0])
		wait_num_cycles(cycles_per_keystroke())


# use the python-wrapped attributes
def ctrl_alt_del(obj = None):
    if not obj:
        obj = conf.kbd0
    print "Sending Ctrl-Alt-Del to %s" % obj.name
    obj.key_event[69] = 0  # SK_CTRL_L down
    obj.key_event[73] = 0  # SK_ALT_L down
    obj.key_event[83] = 0  # SK_GR_DELETE down
    obj.key_event[69] = 1  # SK_CTRL_L up
    obj.key_event[73] = 1  # SK_ALT_L up
    obj.key_event[83] = 1  # SK_GR_DELETE up
    print "Done."

def ctrl_c(obj = None):
    if not obj:
        obj = conf.kbd0
    print "Sending Ctrl-C to %s" % obj.name
    obj.key_event[69] = 0  # SK_CTRL_L down
    obj.key_event[30] = 0  # SK_C down
    obj.key_event[30] = 1  # SK_C up
    obj.key_event[69] = 1  # SK_CTRL_L up
    print "Done."

def enter(obj = None):
    if not obj:
        obj = conf.kbd0
    print "Pressing Enter on %s" % obj.name
    obj.key_event[67] = 0  # SK_ENTER down
    obj.key_event[67] = 1  # SK_ENTER up
    print "Done."

def cycles_per_keystroke():
	cpu_obj = SIM_current_processor()
	# time = cycles / freq
	freq = cpu_obj.freq_mhz
	# 10 ms
	return freq * 10000

def steps_per_keystroke():
	return cycles_per_keystroke()
