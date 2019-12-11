/*
 * simics/devs/sim-keys.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_SIM_KEYS_H
#define _SIMICS_DEVS_SIM_KEYS_H

#define MOUSE_LEFT_DOWN   0x01
#define MOUSE_RIGHT_DOWN  0x02
#define MOUSE_MIDDLE_DOWN 0x04
#define MOUSE_4_DOWN      0x08
#define MOUSE_5_DOWN      0x10


/* keyboard_info codes */
#define KBD_CAPSLOCK_ON    0x00
#define KBD_CAPSLOCK_OFF   0x01
#define KBD_NUMLOCK_ON     0x02
#define KBD_NUMLOCK_OFF    0x03
#define KBD_SCROLLLOCK_ON  0x04
#define KBD_SCROLLLOCK_OFF 0x05

/* keycodes internal to simics */
#define SK_ILLEGAL        0

/* MF II keyboard keys ( = standard 101 keyboard )  */
#define SK_ESC            1
#define SK_F1             2
#define SK_F2             3
#define SK_F3             4
#define SK_F4             5
#define SK_F5             6
#define SK_F6             7
#define SK_F7             8
#define SK_F8             9
#define SK_F9            10
#define SK_F10           11
#define SK_F11           12
#define SK_F12           13

#define SK_PRNT_SCRN     14
#define SK_SCROLL_LOCK   15
#define SK_NUM_LOCK      16
#define SK_CAPS_LOCK     17

#define SK_0             18
#define SK_1             19
#define SK_2             20
#define SK_3             21
#define SK_4             22
#define SK_5             23
#define SK_6             24
#define SK_7             25
#define SK_8             26
#define SK_9             27
#define SK_A             28
#define SK_B             29
#define SK_C             30
#define SK_D             31
#define SK_E             32
#define SK_F             33
#define SK_G             34
#define SK_H             35
#define SK_I             36
#define SK_J             37
#define SK_K             38
#define SK_L             39
#define SK_M             40
#define SK_N             41
#define SK_O             42
#define SK_P             43
#define SK_Q             44
#define SK_R             45
#define SK_S             46
#define SK_T             47
#define SK_U             48
#define SK_V             49
#define SK_W             50
#define SK_X             51
#define SK_Y             52
#define SK_Z             53

#define SK_APOSTROPHE    54
#define SK_COMMA         55
#define SK_PERIOD        56
#define SK_SEMICOLON     57
#define SK_EQUAL         58
#define SK_SLASH         59
#define SK_BACKSLASH     60
#define SK_SPACE         61
#define SK_LEFT_BRACKET  62
#define SK_RIGHT_BRACKET 63
#define SK_MINUS         64
#define SK_GRAVE         65

#define SK_TAB           66
#define SK_ENTER         67
#define SK_BACKSPACE     68

#define SK_CTRL_L        69
#define SK_CTRL_R        70  /* Not on Sun */
#define SK_SHIFT_L       71
#define SK_SHIFT_R       72
#define SK_ALT_L         73
#define SK_ALT_R         74

#define SK_GR_DIVIDE     75
#define SK_GR_MULTIPLY   76
#define SK_GR_MINUS      77
#define SK_GR_PLUS       78
#define SK_GR_ENTER      79
#define SK_GR_INSERT     80
#define SK_GR_HOME       81
#define SK_GR_PG_UP      82
#define SK_GR_DELETE     83
#define SK_GR_END        84
#define SK_GR_PG_DOWN    85
#define SK_GR_UP         86
#define SK_GR_DOWN       87
#define SK_GR_LEFT       88
#define SK_GR_RIGHT      89

#define SK_KP_HOME       90
#define SK_KP_UP         91
#define SK_KP_PG_UP      92
#define SK_KP_LEFT       93
#define SK_KP_CENTER     94
#define SK_KP_RIGHT      95
#define SK_KP_END        96
#define SK_KP_DOWN       97
#define SK_KP_PG_DOWN    98
#define SK_KP_INSERT     99
#define SK_KP_DELETE    100

#define SK_PAUSE        101

/* Windows 95 keys found on 104 and 105 key keyboards */
#define SK_LEFT_WIN     102 /* Not on Sun */
#define SK_RIGHT_WIN    103 /* Not on Sun */
#define SK_LIST_BIT     104 /* Not on Sun */

/* the extra key on 102 and 105 key keyboards, compared to 101 104 */
#define SK_KEYB         105 /* Not on Sun */

/* not separate keys on 101+ key keyboards, but handles as such */
#define SK_BREAK        106 /* Not on Sun */
#define SK_SYSREQ       107 /* Not on Sun */

/* the extra keys on sun keyboards */
#define SK_SUN_STOP     108
#define SK_SUN_AGAIN    109
#define SK_SUN_PROPS    110
#define SK_SUN_UNDO     111
#define SK_SUN_FRONT    112
#define SK_SUN_COPY     113
#define SK_SUN_OPEN     114
#define SK_SUN_PASTE    115
#define SK_SUN_FIND     116
#define SK_SUN_CUT      117

#define SK_SUN_HELP     118

#define SK_SUN_COMPOSE  119
#define SK_SUN_META_L   120
#define SK_SUN_META_R   121

#define SK_SUN_POWER    122
#define SK_SUN_AUDIO_D  123
#define SK_SUN_AUDIO_U  124
#define SK_SUN_AUDIO_M  125
#define SK_SUN_EMPTY    126

/* number of keys.  highest + 1 (for 0 key) */
#define SK_MAX_KEY      127

#define SIM_KEY_NAMES                                                                                   \
	"ILLEGAL", "ESC",                                                                               \
	"F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",                      \
	"PRNT_SCRN", "SCROLL_LOCK", "NUM_LOCK", "CAPS_LOCK",                                            \
	"0", "1", "2", "3", "4", "5", "6", "7", "8", "9",                                               \
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",                           \
        "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",                                     \
	"APOSTROPHE", "COMMA", "PERIOD", "SEMICOLON", "EQUAL", "SLASH", "BACKSLASH", "SPACE",           \
        "LEFT_BRACKET", "RIGHT_BRACKET", "MINUS", "GRAVE", "TAB", "ENTER", "BACKSPACE",                 \
	"CTRL_L", "CTRL_R", "SHIFT_L", "SHIFT_R", "ALT_L", "ALT_R",                                     \
	"GR_DIVIDE", "GR_MULTIPLY", "GR_MINUS", "GR_PLUS", "GR_ENTER", "GR_INSERT", "GR_HOME",          \
        "GR_PG_UP", "GR_DELETE", "GR_END", "GR_PG_DOWN", "GR_UP", "GR_DOWN", "GR_LEFT", "GR_RIGHT",     \
	"KP_HOME", "KP_UP", "KP_PG_UP", "KP_LEFT", "KP_CENTER", "KP_RIGHT", "KP_END", "KP_DOWN",        \
        "KP_PG_DOWN", "KP_INSERT", "KP_DELETE",                                                         \
        "PAUSE",                                                                                        \
        "LEFT_WIN", "RIGHT_WIN", "LIST_BIT",                                                            \
        "KEY102", "BREAK", "SYSREQ",                                                                    \
        "SUN_STOP", "SUN_AGAIN", "SUN_PROPS", "SUN_UNDO", "SUN_FRONT", "SUN_COPY", "SUN_OPEN",          \
        "SUN_PASTE", "SUN_FIND", "SUN_CUT", "SUN_HELP", "SUN_COMPOSE", "SUN_META_L",                    \
        "SUN_META_R", "SUN_POWER", "SUN_AUDIO_D", "SUN_AUDIO_U", "SUN_AUDIO_M", "SUN_EMPTY",

#endif /* _SIMICS_DEVS_SIM_KEYS_H */
