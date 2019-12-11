/*
  keycodes.h

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

#ifndef _KEYCODES_H
#define _KEYCODES_H

#include <simics/devs/sim-keys.h>

#define MAX_X11_KEYS            0x100

#define MAX_SCAN_CODE_LENGTH 8

#if !defined(GULP)

int sim_key_to_scan(uint8 key, int key_up, char *buf,
                    int xt_style_conversion,
                    int shift_down, int ctrl_down,
                    int alt_down, int num_lock_on);
int sim_key_to_sun(uint8 key);
const char *sim_key_name(int keycode);
int x11_pc_key_to_sim(int keycode);
int x11_sun_key_to_sim(int keycode);
int x11_mac_key_to_sim(int keycode);
int x11_cooked_key_to_sim(int keycode);
int ascii_to_sim(int ascii);

#endif /* ! GULP */

#endif /* _KEYCODES_H */
