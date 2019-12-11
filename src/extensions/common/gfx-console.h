/*
  gfx-console.h

  Copyright 2000-2007 Virtutech AB
  
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

#ifndef _GFX_CONSOLE_H
#define _GFX_CONSOLE_H

#ifdef CONSOLE_OPENGL
#include <GL/gl.h>
#include <GL/glx.h>
#include "../graphics-console/glfuncs.h"

#define FUN_PTR_DEF(r, f, p) r (*f) p;

typedef struct {
	int version;
	int nr_functions;
	WITH_GL_FUNCS(FUN_PTR_DEF)
} gl_interface_t;

#endif

/* target formats supported by the gfx console */

#define GFX_8BIT_INDEXED 8
#define GFX_RGB_565      16
#define GFX_RGB_888      24
#define GFX_xRGB_8888    32

/* Graphical breakpoint support */

#define GBP_MAGIC       0xe0e0e0e0

#define GBP_FMT_VGA_4   1

#define GBP_FMT_V3_8    8
#define GBP_FMT_V3_16   16
#define GBP_FMT_V3_24   24
#define GBP_FMT_V3_32   32

typedef struct gfx_breakpoint {
        int     id, enabled, format;
        uint32  minx, miny, maxx, maxy;
        uint8   *data;
        struct gfx_breakpoint *next, *prev;
} gfx_breakpoint_t;

#define GBP_COMMENT_OFFS 0
#define GBP_MAGIC_OFFS   32
#define GBP_FORMAT_OFFS  36
#define GBP_BYTES_OFFS   40
#define GBP_MINX_OFFS    44
#define GBP_MINY_OFFS    48
#define GBP_MAXX_OFFS    52
#define GBP_MAXY_OFFS    56

#define GBP_HEADER_SIZE  (GBP_MAXY_OFFS + 4)

/*
typedef struct {
        char            comment[32];
        uint32          magic;
        uint32          format, bytes;
        int             minx, miny, maxx, maxy;
} gbp_header_t;
*/

#define GFX_CONSOLE_INTERFACE "gfx-console"

typedef struct gfx_console_interface {
        int (*set_color)(conf_object_t *, int, int, int, int);
        void (*set_size)(conf_object_t *, int, int, int, int, int);
        void (*set_cursor_bitmap)(conf_object_t *, int, int, char bitmap[64][64], uint32, uint32);
        void (*set_cursor_location)(conf_object_t *, int, int);
        void (*cursor_toggle)(conf_object_t *, int);

        void (*put_pixel)(conf_object_t *, int, int, int);
        void (*put_pixel_rgb)(conf_object_t *, int, int, uint32);
        void (*put_block)(conf_object_t *, uint8 *, int, int, int, int, int,
			  int, int);
        int (*select_rectangle)(conf_object_t *_con, uint32 *x1, uint32 *y1, uint32 *x2, uint32 *y2);

#ifdef CONSOLE_OPENGL
        gl_interface_t* (*gl_init)(void);
        int (*set_gl_buffer)(void *buffer, unsigned int stride, unsigned int w, unsigned int h);
        void (*update_gl_buffer)(void);
#endif
        void (*redraw)(conf_object_t *);
        void (*keyboard_info)(conf_object_t *, int);
} gfx_console_interface_t;

#endif /* _GFX_CONSOLE_H */
