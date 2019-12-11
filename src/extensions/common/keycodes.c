/*
  keycodes.c - Generic keyboard functions.

  Copyright 1999-2007 Virtutech AB
  
  The contents herein are Source Code which are a subset of Licensed
  Software pursuant to the terms of the Virtutech Simics Software
  License Agreement (the "Agreement"), and are being distributed under
  the Agreement.  You should have received a copy of the Agreement with
  this Licensed Software; if not, please contact Virtutech for a copy
  of the Agreement prior to using this Licensed Software.
  
  By using this Source Code, you agree to be bound by all of the terms
  of the Agreement, and use of this Source Code is subject to the terms
  the Agreement.
  
  This Source Code and any derivatives thereof are provided on an "as
  is" basis.  Virtutech makes no warranties with respect to the Source
  Code or any derivatives thereof and disclaims all implied warranties,
  including, without limitation, warranties of merchantability and
  fitness for a particular purpose and non-infringement.

*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <simics/api.h>
#include <simics/utils.h>

#include "keycodes.h"

#ifdef _MSC_VER
/* suppress multiple "truncation from 'const int' to char" */
#pragma warning( once: 4305 )
#endif

/*
 * Scan Code Set 1
 * print-screen and pause (and extended keys) handled in sim_key_to_scan()
 */
static uint8 sk_to_scan[SK_MAX_KEY] =
{
        /* (null), esc, f1 - f12 */
        0x00, 0x01, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f, 0x40, 0x41, 0x42, 0x43, 0x44, 0x57, 0x58,
        /* prnt-scrn, scroll-lock, num-lock, caps-lock */
        0x00, 0x46, 0x45, 0x3a,
        /* 0 - 9 */
        0x0b, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a,
        /* A - M */
        0x1e, 0x30, 0x2e, 0x20, 0x12, 0x21, 0x22, 0x23, 0x17, 0x24, 0x25, 0x26, 0x32,
        /* N - Z */
        0x31, 0x18, 0x19, 0x10, 0x13, 0x1f, 0x14, 0x16, 0x2f, 0x11, 0x2d, 0x15, 0x2c,
        /* ' , . ; = / \ space [ ] - ` */
        0x28, 0x33, 0x34, 0x27, 0x0d, 0x35, 0x2b, 0x39, 0x1a, 0x1b, 0x0c, 0x29,
        /* tab enter backspace */
        0x0f, 0x1c, 0x0e, 
        /* ctrl-l ctrl-r shift-l shift-r alt-l alt-r */
        0x1d, 0x1d, 0x2a, 0x36, 0x38, 0x38,
        /* grey: / * - + enter ins home pg-up del end pg-down up down left right */
        0x35, 0x37, 0x4a, 0x4e, 0x1c, 0x52, 0x47, 0x49, 0x53, 0x4f, 0x51, 0x48, 0x50, 0x4b, 0x4d,
        /* keypad: home up pg-up left center right end down pg-down ins del (or nums) */
        0x47, 0x48, 0x49, 0x4b, 0x4c, 0x4d, 0x4f, 0x50, 0x51, 0x52, 0x53,
        /* pause left-win right-win list-bit keyb break sysreq */
        0x00, 0x5b, 0x5c, 0x5d, 0x56, 0x00, 0x00,
        /* sun keys: stop, again, props, undo, front, copy, open, paste, find, cut */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        /* sun keys: help, compose, meta-l, meta-r, power, audio-down, audio-up, audio-mute, empty */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

/*
 * Scan Code Set 2 - used by keyboard but converted to Set 1 by the 8042
 * pause, print-screen (and extended keys) handled in sim_key_to_scan()
 */
static uint8 sk_to_kscan[SK_MAX_KEY] =
{
        /* (null), esc, f1 - f12 */
        0x00, 0x76, 0x05, 0x06, 0x04, 0x0c, 0x03, 0x0b, 0x83, 0x0a, 0x01, 0x09, 0x78, 0x07,
        /* prnt-scrn, scroll-lock, num-lock, caps-lock */
        0x00, 0x7e, 0x77, 0x58,
        /* 0 - 9 */
        0x45, 0x16, 0x1e, 0x26, 0x25, 0x2e, 0x36, 0x3d, 0x3e, 0x46,
        /* A - M */
        0x1c, 0x32, 0x21, 0x23, 0x24, 0x2b, 0x34, 0x33, 0x43, 0x3b, 0x42, 0x4b, 0x3a,
        /* N - Z */
        0x31, 0x44, 0x4d, 0x15, 0x2d, 0x1b, 0x2c, 0x3c, 0x2a, 0x1d, 0x22, 0x35, 0x1a,
        /* ' , . ; = / \ space [ ] - ` */
        0x52, 0x41, 0x49, 0x4c, 0x55, 0x4a, 0x5d, 0x29, 0x54, 0x5b, 0x4e, 0x0e,
        /* tab enter backspace */
        0x0d, 0x5a, 0x66, 
        /* ctrl-l ctrl-r shift-l shift-r alt-l alt-r */
        0x14, 0x14, 0x12, 0x59, 0x11, 0x11,
        /* grey: / * - + enter ins home pg-up del end pg-down up down left right */
        0x4a, 0x7c, 0x7b, 0x79, 0x5a, 0x70, 0x6c, 0x7d, 0x71, 0x69, 0x7a, 0x75, 0x72, 0x6b, 0x74,
        /* keypad: home up pg-up left center right end down pg-down ins del */
        0x6c, 0x75, 0x7d, 0x6b, 0x73, 0x74, 0x69, 0x72, 0x7a, 0x70, 0x71,
        /* pause left-win right-win list-bit keyb break sysreq */
        0x00, 0x1f, 0x27, 0x2f, 0x61, 0x00, 0x00,
        /* sun keys: stop, again, props, undo, front, copy, open, paste, find, cut */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        /* sun keys: help, compose, meta-l, meta-r, power, audio-down, audio-up, audio-mute, empty */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

/*
 * 119 keys
 * sim-key ctrl-r mapped to ctrl
 * "unused" raw codes: 0x4b, 0x6f, 0x73, 0x74, 0x75, 0x7c
 */
static uint8 sk_to_sun[SK_MAX_KEY] =
{
        /* (null), esc, f1 - f12 */
        0x00, 0x1d, 0x05, 0x06, 0x08, 0x0a, 0x0c, 0x0e, 0x10, 0x11, 0x12, 0x07, 0x09, 0x0b,
        /* prnt-scrn, scroll-lock, num-lock, caps-lock */
        0x16, 0x17, 0x62, 0x77,
        /* 0 - 9 */
        0x27, 0x1e, 0x1f, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26,
        /* A - M */
        0x4d, 0x68, 0x66, 0x4f, 0x38, 0x50, 0x51, 0x52, 0x3d, 0x53, 0x54, 0x55, 0x6a,
        /* N - Z */
        0x69, 0x3e, 0x3f, 0x36, 0x39, 0x4e, 0x3a, 0x3c, 0x67, 0x37, 0x65, 0x3b, 0x64,
        /* ' , . ; = / \ space [ ] - ` */
        0x57, 0x6b, 0x6c, 0x56, 0x29, 0x6d, 0x58, 0x79, 0x40, 0x41, 0x28, 0x2a,
        /* tab enter backspace */
        0x35, 0x59, 0x2b,
        /* ctrl-l ctrl-r shift-l shift-r alt-l alt-r (alt-r = alt-gr on sun) */
        0x4c, 0x4c, 0x63, 0x6e, 0x13, 0x0d,
        /* grey: / * - + enter ins home pg-up del end pg-down up down left right */
        0x2e, 0x2f, 0x47, 0x7d, 0x5a, 0x2c, 0x34, 0x60, 0x42, 0x4a, 0x7b, 0x14, 0x1b, 0x18, 0x1c,
        /* keypad: home up pg-up left center right end down pg-down ins del (or nums) */
        0x44, 0x45, 0x46, 0x5b, 0x5c, 0x5d, 0x70, 0x71, 0x72, 0x5e, 0x32,
        /* pause left-win right-win list-bit keyb break sysreq */
        0x15, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        /* sun keys: stop, again, props, undo, front, copy, open, paste, find, cut */
        0x01, 0x03, 0x19, 0x1a, 0x31, 0x33, 0x48, 0x49, 0x5f, 0x61,
        /* sun keys: help, compose, meta-l, meta-r, power, audio-down, audio-up, audio-mute, empty */
        0x76, 0x43, 0x78, 0x7a, 0x30, 0x02, 0x04, 0x2d, 0x0f
};

#define NUM_X11_PC_KEYS          0x80
#define NUM_X11_SUN_KEYS         0x90
#define NUM_X11_MAC_KEYS         0x90
#define NUM_X11_COOKED_00_KEYS   0x80
#define NUM_X11_COOKED_FF_KEYS  0x100
#define NUM_ASCII_KEYS           0x80

/* 105 keys */
static uint8 x11_pc_to_sk[NUM_X11_PC_KEYS] = {
/* 0x */   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,  19,  20,  21,  22,  23,  24,
/* 1x */  25,  26,  27,  18,  64,  58,  68,  66,  44,  50,  32,  45,  47,  52,  48,  36,
/* 2x */  42,  43,  62,  63,  67,  69,  28,  46,  31,  33,  34,  35,  37,  38,  39,  57,
/* 3x */  54,  65,  71,  60,  53,  51,  30,  49,  29,  41,  40,  55,  56,  59,  72,  76,
/* 4x */  73,  61,  17,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  16,  15,  90,
/* 5x */  91,  92,  77,  93,  94,  95,  78,  96,  97,  98,  99, 100,   0,   0, 105,  12,
/* 6x */  13,  81,  86,  82,  88,   0,  89,  84,  87,  85,  80,  83,  79,  70, 101,  14,
/* 7x */  75,  74,   0, 102, 103, 104,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
};

/* 119 keys */
static uint8 x11_sun_to_sk[NUM_X11_SUN_KEYS] = {
/* 0x */   0,   0,   0,   0,   0,   0,   0,   0, 108, 123, 109, 124,   2,   3,  11,   4,
/* 1x */  12,   5,  13,   6,  74,   7, 126,   8,   9,  10,  73,  86, 101,  14,  15,  88,
/* 2x */ 110, 111,  87,  89,   1,  19,  20,  21,  22,  23,  24,  25,  26,  27,  18,  64,
/* 3x */  58,  65,  68,  80, 125,  75,  76, 122, 112, 100, 113,  81,  66,  44,  50,  32,
/* 4x */  45,  47,  52,  48,  36,  42,  43,  62,  63,  83, 119,  90,  91,  92,  77, 114,
/* 5x */ 115,  84,   0,  69,  28,  46,  31,  33,  34,  35,  37,  38,  39,  57,  54,  60,
/* 6x */  67,  79,  93,  94,  95,  99, 116,  82, 117,  16,  71,  53,  51,  30,  49,  29,
/* 7x */  41,  40,  55,  56,  59,  72,   0,  96,  97,  98,   0,   0,   0, 118,  17, 120,
/* 8x */  61, 121,  85,   0,  78,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
};

static uint8 x11_mac_to_sk[NUM_X11_MAC_KEYS] = {
/* 0x */  0,  0,  0,  0,  0,  0,  0,  0, 28, 46, 31, 33, 35, 34, 53, 51,
/* 1x */ 30, 49,105, 29, 44, 50, 32, 45, 52, 47, 19, 20, 21, 22, 24, 23,
/* 2x */ 58, 27, 25, 64, 26, 18, 63, 42, 48, 62, 36, 43, 67, 39, 37, 54,
/* 3x */ 38, 57, 60, 55, 59, 41, 40, 56, 66, 61, 65, 68,  0,  1, 69, 73,
/* 4x */ 71, 70, 74, 88, 89, 87, 86,  0,  0,100,  0, 76,  0, 78,  0, 16,
/* 5x */  0,  0,  0, 75, 79,  0, 77,  0,  0, 75, 99, 96, 97, 98, 93, 94,
/* 6x */ 95, 90,  0, 91, 92,  0,  0,  0,  6,  7,  8,  4,  9, 10,  0, 12,
/* 7x */  0, 14,  0, 15,  0, 11,  0, 13,  0,101, 80, 81, 82, 83,  5, 84,
/* 8x */  3, 85,  2, 72, 74, 70, 74,  0,  0,  0,  0,  0,  0,  0,  0,  0
};

static uint8 x11_cooked_00_to_sk[NUM_X11_COOKED_00_KEYS] = {
/* 0x */  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
/* 1x */  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
/* 2x */ 61, 19, 54, 21, 22, 23, 25, 54, 27, 18, 26, 58, 55, 64, 56, 59,
/* 3x */ 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 57, 57, 55, 58, 56, 59,
/* 4x */ 20, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
/* 5x */ 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 62, 60, 63, 24, 64,
/* 6x */ 65, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
/* 7x */ 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 62, 60, 63, 65,  0
};

static uint8 x11_cooked_ff_to_sk[NUM_X11_COOKED_FF_KEYS] = {
/* 0x */  0,   0,   0,   0,   0,   0,   0,   0,  68,  66,   0,   0,   0,  67,   0,   0,
/* 1x */  0,   0,   0, 101,  15, 107,   0,   0,   0,   0,   0,   1,   0,   0,   0,   0,
/* 2x */  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
/* 3x */  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
/* 4x */  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
/* 5x */ 90,  93,  91,  95,  97,  92,  98,  96,   0,   0,   0,   0,   0,   0,   0,   0,
/* 6x */  0,  61,   0,  99,   0, 111, 109,   0, 116,   0, 118, 106,   0,   0,   0,   0,
/* 7x */  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  16,
/* 8x */ 61,   0,   0,   0,   0,   0,   0,   0,   0,  66,   0,   0,   0,  79,   0,   0,
/* 9x */  0,   0,   0,   0,   0,  81,  88,  86,  89,  87,  82,  85,  84,   0,  80,  93,
/* Ax */  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  76,  78,   0,  77,   0,  75,
/* Bx */  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   2,   3,
/* Cx */  4,   5,   6,   7,   8,   9,  10,  11,  12,  13,   0,   0,   0,   0,   0,   0,
/* Dx */  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
/* Ex */  0,  71,  72,  69,  70,  17,   0, 120, 121,  73,  74,   0,   0,   0,   0,   0,
/* Fx */  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 100
};

static uint8 ascii_to_sk[NUM_ASCII_KEYS][2] = {
/*   0 */ { 0,  0}, {69, 28}, {69, 29}, {69, 30}, {69, 31}, {69, 32}, {69, 33}, {69, 34},
/*   8 */ { 0, 68}, { 0, 66}, {69, 37}, {69, 38}, {69, 39}, { 0, 67}, {69, 41}, {69, 42},
/*  16 */ {69, 43}, {69, 44}, {69, 45}, {69, 46}, {69, 47}, {69, 48}, {69, 49}, {69, 50},
/*  24 */ {69, 51}, {69, 52}, {69, 53}, { 0,  1}, { 0,  0}, {69, 63}, { 0,  0}, { 0,  0},
/*  32 */ { 0, 61}, {71, 19}, {71, 54}, {71, 21}, {71, 22}, {71, 23}, {71, 25}, { 0, 54},
/*  40 */ {71, 27}, {71, 18}, {71, 26}, {71, 58}, { 0, 55}, { 0, 64}, { 0, 56}, { 0, 59},
/*  48 */ { 0, 18}, { 0, 19}, { 0, 20}, { 0, 21}, { 0, 22}, { 0, 23}, { 0, 24}, { 0, 25},
/*  56 */ { 0, 26}, { 0, 27}, {71, 57}, { 0, 57}, {71, 55}, { 0, 58}, {71, 56}, {71, 59},
/*  64 */ {71, 20}, {71, 28}, {71, 29}, {71, 30}, {71, 31}, {71, 32}, {71, 33}, {71, 34},
/*  72 */ {71, 35}, {71, 36}, {71, 37}, {71, 38}, {71, 39}, {71, 40}, {71, 41}, {71, 42},
/*  80 */ {71, 43}, {71, 44}, {71, 45}, {71, 46}, {71, 47}, {71, 48}, {71, 49}, {71, 50},
/*  88 */ {71, 51}, {71, 52}, {71, 53}, { 0, 62}, { 0, 60}, { 0, 63}, {71, 24}, {71, 64},
/*  96 */ { 0, 65}, { 0, 28}, { 0, 29}, { 0, 30}, { 0, 31}, { 0, 32}, { 0, 33}, { 0, 34},
/* 104 */ { 0, 35}, { 0, 36}, { 0, 37}, { 0, 38}, { 0, 39}, { 0, 40}, { 0, 41}, { 0, 42},
/* 112 */ { 0, 43}, { 0, 44}, { 0, 45}, { 0, 46}, { 0, 47}, { 0, 48}, { 0, 49}, { 0, 50},
/* 120 */ { 0, 51}, { 0, 52}, { 0, 53}, {71, 62}, {71, 60}, {71, 63}, {71, 65}, { 0, 83}
};

        
static const char *sk_names[SK_MAX_KEY] = {
        SIM_KEY_NAMES
};


/*
 * Translates a Simics internal keycode to a scan code from a 104/105 key
 * keyboard. Returns the number of bytes in the scan code.
 * A return of -1 means that there is no mapping.
 * The buffer must be large enough to hold all bytes (MAX_SCAN_CODE_LENGTH)
 */
int
sim_key_to_scan(uint8 key, int key_up, char *buf,
                int xt_style_conversion,
                int shift_down, int ctrl_down, int alt_down, int num_lock_on)
{
        int ret;

        if ((key == 0) || (key >= SK_MAX_KEY)) {
                pr_err("[keycodes] Error: Illegal key code in sim_key_to_scan()\n");
                return 0;
        }
        if (xt_style_conversion) {
                /* handle the ugly ones first, Scan Code Set 1 */
                switch (key) {
                case SK_PRNT_SCRN:
                        if (!shift_down && !ctrl_down && !alt_down) {
                                if (!key_up) {
                                        buf[0] = 0xe0; buf[1] = 0x2a;
                                        buf[2] = 0xe0; buf[3] = 0x37;
                                } else {
                                        buf[0] = 0xe0; buf[1] = 0xb7;
                                        buf[2] = 0xe0; buf[3] = 0xaa;
                                }
                                return 4;
                        } else if (alt_down) { /* emulation of sys-req */
                                if (!key_up)
                                        buf[0] = 0x54;
                                else
                                        buf[0] = 0xd4;
                                return 1;
                        } else { /* ctrl or shift down */
                                if (!key_up) {
                                        buf[0] = 0xe0; buf[1] = 0x37;
                                } else {
                                        buf[0] = 0xe0; buf[1] = 0xb7;
                                }
                                return 2;
                        }
                        break;

                case SK_PAUSE:
                        /* the Pause key immediately sends all bytes */
                        if (key_up)
                                return 0;

                        if (ctrl_down) {
                                buf[0] = 0xe0; buf[1] = 0x46;
                                buf[2] = 0xe0; buf[3] = 0xc6;
                                return 4;
                        } else {
                                buf[0] = 0xe1; buf[1] = 0x1d; buf[2] = 0x45; 
                                buf[3] = 0xe1; buf[4] = 0x9d; buf[5] = 0xc5;
                                return 6;
                        }
                        break;

                /* the following are 2 bytes, read second from table */
                case SK_GR_DIVIDE:
                case SK_GR_ENTER:
                case SK_GR_INSERT:
                case SK_GR_HOME:
                case SK_GR_PG_UP:
                case SK_GR_DELETE:
                case SK_GR_END:
                case SK_GR_PG_DOWN:
                case SK_GR_UP:
                case SK_GR_DOWN:
                case SK_GR_LEFT:
                case SK_GR_RIGHT:
                case SK_CTRL_R:
                case SK_ALT_R:
                case SK_LEFT_WIN:
                case SK_RIGHT_WIN:
                case SK_LIST_BIT:
                        buf[0] = 0xe0; buf[1] = sk_to_scan[key];
                        if (key_up)
                                buf[1] |= 0x80;
                        return 2;
                default:
                        buf[0] = sk_to_scan[key];
                                /* check for undefined */
                        if (buf[0] == 0)
                                return -1;
                        if (key_up)
                                buf[0] |= 0x80;
                        return 1;
                }
        } else {
                /* handle the ugly ones first */
                switch (key) {
                case SK_GR_ENTER:
                case SK_LEFT_WIN:
                case SK_RIGHT_WIN:
                case SK_LIST_BIT:
                case SK_ALT_R:
                case SK_CTRL_R:
                        buf[0] = 0xE0;
                        if (key_up) {
                                buf[1] = 0xF0;
                                buf[2] = sk_to_kscan[key];
                                return 3;
                        } else {
                                buf[1] = sk_to_kscan[key];
                                return 2;
                        }
                        break;

                case SK_GR_END:
                case SK_GR_DOWN:
                case SK_GR_PG_DOWN:
                case SK_GR_LEFT:
                case SK_GR_RIGHT:
                case SK_GR_HOME:
                case SK_GR_UP:
                case SK_GR_PG_UP:
                case SK_GR_INSERT:
                case SK_GR_DELETE:
                        if (key_up) {
                                if (!shift_down && !num_lock_on) {
                                        buf[0] = 0xE0;
                                        buf[1] = 0xF0;
                                        buf[2] = sk_to_kscan[key];
                                        ret = 3;
                                } else if (!shift_down && num_lock_on) {
                                        buf[0] = 0xE0;
                                        buf[1] = 0xF0;
                                        buf[2] = sk_to_kscan[key];
                                        buf[3] = 0xE0;
                                        buf[4] = 0xF0;
                                        buf[5] = 0x12;
                                        ret = 6;
                                } else if (shift_down && !num_lock_on) {
                                        buf[0] = 0xE0;
                                        buf[1] = 0xF0;
                                        buf[2] = sk_to_kscan[key];
                                        buf[3] = 0xE0;
                                        buf[4] = 0x12;
                                        ret = 5;
                                } else {
                                        buf[0] = 0xE0;
                                        buf[1] = 0xF0;
                                        buf[2] = sk_to_kscan[key];
                                        ret = 3;
                                }
                        } else {
                                if (!shift_down && !num_lock_on) {
                                        buf[0] = 0xE0;
                                        buf[1] = sk_to_kscan[key];
                                        ret = 2;
                                } else if (!shift_down && num_lock_on) {
                                        buf[0] = 0xE0;
                                        buf[1] = 0x12;
                                        buf[2] = 0xE0;
                                        buf[3] = sk_to_kscan[key];
                                        ret = 4;
                                } else if (shift_down && !num_lock_on) {
                                        buf[0] = 0xE0;
                                        buf[1] = 0xF0;
                                        buf[2] = 0x12;
                                        buf[3] = 0xE0;
                                        buf[4] = sk_to_kscan[key];
                                        ret = 5;
                                } else {
                                        buf[1] = 0xE0;
                                        buf[2] = sk_to_kscan[key];
                                        ret = 2;
                                }
                        }
                        return ret;

                case SK_GR_DIVIDE:
                        if (key_up) {
                                if (!shift_down) {
                                        buf[0] = 0xE0;
                                        buf[1] = 0xF0;
                                        buf[2] = 0x4A;
                                        ret = 3;
                                } else {
                                        buf[0] = 0xe0;
                                        buf[1] = 0xf0;
                                        buf[2] = 0x4a;
                                        buf[3] = 0xe0;
                                        buf[4] = 0x12;
                                        ret = 5;
                                }
                        } else {
                                if (!shift_down) {
                                        buf[0] = 0xE0;
                                        buf[1] = 0x4A;
                                        ret = 2;
                                } else {
                                        buf[0] = 0xE0;
                                        buf[1] = 0xF0;
                                        buf[2] = 0x12;
                                        buf[3] = 0xE0;
                                        buf[4] = 0x4A;
                                        ret = 5;
                                }
                        }
                        return ret;

                case SK_PRNT_SCRN:
                        if (!shift_down && !ctrl_down && !alt_down) {
                                if (!key_up) {
                                        buf[0] = 0xe0; buf[1] = 0x12; buf[2] = 0xe0; buf[3] = 0x7c;
                                        return 4;
                                } else {
                                        buf[0] = 0xe0; buf[1] = 0xf0; buf[2] = 0x7c;
                                        buf[3] = 0xe0; buf[4] = 0xf0; buf[5] = 0x12;
                                        return 6;
                                }
                        } else if (alt_down) { /* emulation of sys-req */
                                if (!key_up) {
                                        buf[0] = 0x84;
                                        return 1;
                                } else {
                                        buf[0] = 0xf0; buf[1] = 0x84;
                                        return 2;
                                }
                        } else { /* ctrl or shift down */
                                if (!key_up) {
                                        buf[0] = 0xe0; buf[1] = 0x7c;
                                        return 2;
                                } else {
                                        buf[0] = 0xf0; buf[1] = 0xe0; buf[2] = 0x7c;
                                        return 3;
                                }
                        }
                        break;

                case SK_PAUSE:
                        /* The Pause key immediately sends all bytes */
                        if (key_up)
                                return 0;

                        if (ctrl_down) {
                                buf[0] = 0xe0; buf[1] = 0x7e;
                                buf[2] = 0xe0; buf[3] = 0xf0; buf[4] = 0x7e;
                                return 5;
                        } else {
                                buf[0] = 0xe1; buf[1] = 0x14; buf[2] = 0x77;
                                buf[3] = 0xe1; buf[4] = 0xf0; buf[5] = 0x14;
                                buf[6] = 0xf0; buf[7] = 0x77;
                                CASSERT_STMT(MAX_SCAN_CODE_LENGTH >= 8);
                                return 8;
                        }
                        break;

                default:
                        if (key_up) {
                                buf[0] = 0xF0;
                                buf[1] = sk_to_kscan[key];
                                if (buf[1] == 0)
                                        return -1;
                                else
                                        return 2;
                        } else {
                                buf[0] = sk_to_kscan[key];
                                if (buf[0] == 0)
                                        return -1;
                                else
                                        return 1;
                        }
                }
        }
}


const char *
sim_key_name(int keycode)
{
        if (keycode < SK_MAX_KEY)
                return sk_names[keycode];
        return "<Undefined>";
}


int
sim_key_to_sun(uint8 key)
{
        if ((key == 0) || (key >= SK_MAX_KEY)) {
                pr_err("[keycodes] Error: Illegal key code in sim_key_to_sun()\n");
                return 0;
        }
        return sk_to_sun[key];
}


/* Translates a X11 (PC) keycode to Simics internal keycode
 * format. A return of 0 means that there is no translation.
 */
int
x11_pc_key_to_sim(int keycode)
{
        int simcode = 0;

        if (keycode < NUM_X11_PC_KEYS)
                simcode = x11_pc_to_sk[keycode];
        return simcode;
}


int
x11_sun_key_to_sim(int keycode)
{
        int simcode = 0;

        if (keycode < NUM_X11_SUN_KEYS)
                simcode = x11_sun_to_sk[keycode];
        return simcode;
}

int
x11_mac_key_to_sim(int keycode)
{
        int simcode = 0;

        if (keycode < NUM_X11_MAC_KEYS)
                simcode = x11_mac_to_sk[keycode];
        return simcode;
}

int
x11_cooked_key_to_sim(int keycode)
{
        int simcode = 0;

        if (keycode < NUM_X11_COOKED_00_KEYS)
                simcode = x11_cooked_00_to_sk[keycode];
        else if ((keycode >= 0xff00) && (keycode < (0xff00 + NUM_X11_COOKED_FF_KEYS)))
                simcode = x11_cooked_ff_to_sk[keycode - 0xff00];
        return simcode;
}


/* returns modifier key in bits 8..15, sim key code in bits 0..7 */
int
ascii_to_sim(int ascii)
{
        if (ascii > NUM_ASCII_KEYS)
                return 0;
        return (ascii_to_sk[ascii][0] << 8) | ascii_to_sk[ascii][1];
}
