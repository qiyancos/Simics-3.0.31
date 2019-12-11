/*
 * Separate readhist binary for adding Bash-like interface to Simics
 *
 * Copyright (1998-2004) Virtutech AB, All Rights Reserved
 *
 * This file is distributed under the GNU Public Licence, see the COPYING file.
 *
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>
#include <fcntl.h>
#include <limits.h>
#include <errno.h>
#include <unistd.h>
#include <sys/select.h>
#include <sys/time.h>
#include <sys/types.h>

#define READLINE_LIBRARY
#include "readline.h"
#include "history.h"
#include <simics/util/vect.h>

#define MAX_MSG_LEN 1024
#define HISTORY_FILENAME ".simics-history"

/* Set when Simics has written to stdout, indicating that we must redisplay
   the command line that has been trashed */
static volatile int got_output = 0;

static char *simics_history;
static int history_lines;
static int simics_fd;
static int batch_mode;
static int cmdline_disabled;

typedef enum {
        RH_BEGIN       = 'B',   /* from simics: batch_mode/h-lines/h-file */
        RH_CMD         = 'C',   /* to simics: send input line */
        RH_QUIT        = 'Q',   /* to simics: eof from input */
        RH_PROMPT      = 'P',   /* from simics: start new input line */
        RH_GET_COMPL   = 'G',   /* to simics: request completions */
        RH_ADD_COMPL   = 'A',   /* from simics: add one completion */
        RH_FILE_COMPL  = 'F',   /* from simics: use filename-style compl */
        RH_COMPL_1     = '1',   /* from simics: end of completions */
        RH_COMPL_0     = '0',   /* from simics: completion not available */
        RH_HIST_LEN    = 'H',   /* from simics: set number of history lines */
        RH_HIST_FILE   = 'I',   /* from simics: set name of history file */
        RH_OTHER_OUTP  = 'O',   /* from simics: forced display update */
        RH_SCREEN_SIZE = 'Z',   /* to simics: set new screen size */
        RH_DISABLE     = 'D',   /* from simics: disable input */
        RH_ENABLE      = 'E',   /* from simics: enable input again */
        RH_NUM_CMD
} cmd_t;

static int input_in_progress = 0;

static void
send_cmd(cmd_t cmd, const char *str)
{
        char buf[9];

        sprintf(buf, "#%c%05d;", cmd, (int)strlen(str));
        write(simics_fd, buf, 8);
        if (strlen(str))
                write(simics_fd, str, strlen(str));
}

/* Read exactly len bytes from fd. Return 0 if ok, -1 on EOF. */
static int
read_bytes(int fd, char *buf, int len)
{
        int r, nread = 0;
        do {
                r = read(fd, buf + nread, len - nread);
                if (r <= 0) {
                        if (r < 0) {
                                if (errno == EINTR)
                                        continue;
                                perror("read");
                        }
                        return -1;
                }
                nread += r;
        } while (nread < len);
        return 0;
}

static int
read_available_char(int fd)
{
        char buf;
        int flags = fcntl(fd, F_GETFL, 0);

        fcntl(fd, F_SETFL, flags | O_NONBLOCK);
        int r = read(fd, &buf, 1);
        fcntl(fd, F_SETFL, flags);
        if (r <= 0)
                return -1;
        return buf;
}

/* Attempt to read one protocol message from Simics.
   Return size of the extended part of message or -1 on EOF.
   The command code is returned in &cmd. */
static int
read_message(char *msg, char *cmd)
{
        char buf[9];
        int len;

        if (read_bytes(simics_fd, buf, 8) < 0)
                return -1;
        buf[8] = 0;
        if (sscanf(buf, "#%c%5d;", cmd, &len) != 2) {
                fprintf(stderr, "readhist: protocol error\n");
                return -1;
        }
        if (len > 0) {
                if (read_bytes(simics_fd, msg, len) < 0)
                        return -1;
                msg[len] = 0;
        }
        return len;
}

/* readline will catch SIGWINCH and set LINES/COLUMNS accordingly.
   If they have been changed, tell Simics about it. */
static void
check_for_resize(void)
{
        char *p;
        int width = -1, height = -1;
        static long oldw = -1, oldh = -1;
        char msg[32];

        p = getenv("COLUMNS");
        if (!p)
                return;
        width = atoi(p);
        if (!width)
                return;

        p = getenv("LINES");
        if (!p)
                return;
        height = atoi(p);
        if (!height)
                return;

        if (width <= 0 || height <= 0 || (width == oldw && height == oldh))
                return;

        oldw = width;
        oldh = height;

        sprintf(msg, "%d;%d;", width, height);
        send_cmd(RH_SCREEN_SIZE, msg);
}

static VECT(char *) completions = VNULL;

static void
add_completion(const char *str)
{
        VADD(completions, strdup(str));
}

/* return length of the longest common prefix of two strings */
static int
common_prefix_len(const char *s1, const char *s2)
{
        int i;
        for (i = 0; s1[i] == s2[i] && s1[i]; i++)
                ;
        return i;
}

static int
need_quote(char c)
{
        const char *chars = " *+&";
        for (int i = 0; i < strlen(chars); i++)
                if (c == chars[i])
                        return 1;
        return 0;
}

/* Wrap up current completion list to something that readline will accept,
   which is an argv style malloced array of malloced strings whose first
   element is the prefix to use for completion. */
static char **
make_completion_list(void)
{
        int clen;
        int n = VLEN(completions);
        char **c;

        if (!n)
                return NULL;

        /* move gathered completions to return list */
        c = malloc((n + 2) * sizeof(char *));
        memcpy(c + 1, VVEC(completions), n * sizeof(char *));
        c[n + 1] = NULL;
        VCLEAR(completions);

        /* compute the longest common prefix of all possibilities */
        clen = strlen(c[1]);
        for (int i = 1; i < n; i++) {
                int common = common_prefix_len(c[1], c[1 + i]);
                if (clen > common)
                        clen = common;
        }

        /* put the common prefix first in the returned list */
        int quote = 0;
        if (clen && c[1][clen - 1] != '=') {
                for (int i = 0; i < clen; i++) {
                        if (need_quote(c[1][i]))
                                quote = 1;
                }
        }

        if (quote) {
                // skip last quote if several completions
                int dst_len = clen + (n == 1 ? 3 : 2);
                c[0] = malloc(dst_len);
                snprintf(c[0], dst_len, "\"%s\"", c[1]);
        } else {
                c[0] = malloc(clen + 1);
                memcpy(c[0], c[1], clen);
                c[0][clen] = 0;
        }
        return c;
}

/* return NULL-terminated array of generated completions */
static char **
generate_completions(char *txt, int start, int end)
{
        char msg[MAX_MSG_LEN];

        rl_attempted_completion_over = 1;

        /* ask Simics for completions */
        snprintf(msg, sizeof msg, "%d;%d;%d;%d;%s %s",
                 start, end, (int)strlen(rl_line_buffer), (int)strlen(txt),
                 rl_line_buffer, txt);
        send_cmd(RH_GET_COMPL, msg);

        /* receive completions + completion action */
        for (;;) {
                char cmd;
                int len = read_message(msg, &cmd);
                if (len < 0)
                        return NULL;
                switch (cmd) {
                case RH_ADD_COMPL:
                        add_completion(msg);
                        break;

                case RH_COMPL_0: /* completion not available */
                        return NULL;

                case RH_COMPL_1: /* end of completions */
                        return make_completion_list();

                case RH_FILE_COMPL:
                        rl_filename_completion_desired = 1;
                        break;

                case RH_OTHER_OUTP:
                        if (input_in_progress)
                                got_output = 1;
                        break;

                default:
                        fprintf(stderr,
                                "bad command (%d) in completion mode\n", cmd);
                        break;
                }
        }
}

static void
init_readhist(void)
{
        rl_attempted_completion_function = (CPPFunction *)generate_completions;
        rl_basic_word_break_characters = (char *)" (%$=;";
        rl_special_prefixes = (char *)"";
        rl_completer_quote_characters = (char *)"\"";

        /* initialize history */
        using_history();

        stifle_history(history_lines);

        /* no command history in batch mode */
        if (batch_mode)
                return;

        if (read_history(simics_history)) {
                /* no history file, create one */
                if (write_history(simics_history)) {
                        free(simics_history);
                        simics_history = NULL;
                }
        }
}

static void
sigtstp_handler(int sig)
{
        /* There are mild races associated with got_output, but since it's
           only for cosmetic purposes it's no actual problem */
        got_output = 1;
        kill(getpid(), SIGSTOP);
}

static void
make_blocking(int fd)
{
        fcntl(fd, F_SETFL, fcntl(fd, F_GETFL, 0) & ~O_NONBLOCK);
}

static void
handle_history(char *line)
{
        add_history(line);
        if (simics_history)
                append_history(1, simics_history);
}

static void
send_input_line(char *line)
{
        rl_callback_handler_remove();
        input_in_progress = 0;
        got_output = 0;
        if (!line) {
                /* This indicates EOF from keyboard input */
                send_cmd(RH_QUIT, "");
                return;
        }

        if (line[0])
                handle_history(line);
        send_cmd(RH_CMD, line);
}

static void
handle_simics_message(void)
{
        char msg[MAX_MSG_LEN];
        char cmd;

        int len = read_message(msg, &cmd);
        if (len < 0) {
                /* reset terminal by removing callback */
                rl_callback_handler_remove();
                /* simics died - just exit silently */
                exit(0);
        }
        switch (cmd) {
        case RH_ENABLE:
                cmdline_disabled = 0;
                if (simics_history) {
                        /* restore the history when enabled again */
                        stifle_history(0);
                        stifle_history(history_lines);
                        read_history(simics_history);
                }
                /* fall through */
        case RH_PROMPT:
                /* start input of a new line */
                got_output = 0;
                input_in_progress = 1;
                rl_callback_handler_install(msg, send_input_line);
                break;
        case RH_OTHER_OUTP:
                if (input_in_progress)
                        got_output = 1;
                break;
        case RH_HIST_LEN:
                sscanf(msg, "%d", &history_lines);
                stifle_history(history_lines);
                break;
        case RH_HIST_FILE:
                free(simics_history);
                if (!batch_mode)
                        simics_history = strdup(msg);
                break;
        case RH_DISABLE:
                if (input_in_progress) {
                        rl_point = rl_end = 0; /* delete input */
                        /* empty prompt not supported, fake it */
                        rl_set_prompt(" \010");
                        rl_redisplay();
                }
                rl_callback_handler_remove();
                input_in_progress = 0;
                cmdline_disabled = 1;
                break;
        default:
                fprintf(stderr, "ignoring cmd: '%c'\n", cmd);
                break;
        }
}

/* Timeout for redisplaying the input line after asynchronous output, in ms */
#define ASYNC_REDISPLAY_TIME 100000

static void
main_loop(void)
{
        for (;;) {
                int r;
                fd_set readfds;
                struct timeval *tout = NULL;
                struct timeval t;

                check_for_resize();

                FD_ZERO(&readfds);
                if (input_in_progress || cmdline_disabled)
                        FD_SET(0, &readfds);
                FD_SET(simics_fd, &readfds);

                if (got_output && input_in_progress) {
                        t.tv_sec = 0;
                        t.tv_usec = ASYNC_REDISPLAY_TIME;
                        tout = &t;
                }

                r = select(simics_fd + 1, &readfds, NULL, NULL, tout);
                if (r < 0) {
                        if (errno == EINTR)
                                continue;
                        /* reset terminal by removing callback */
                        rl_callback_handler_remove();
                        exit(1);
                }
                if (r == 0) {
                        /* timeout */
                        rl_forced_update_display();
                        got_output = 0;
                        continue;
                }

                if (FD_ISSET(0, &readfds)) {
                        if (input_in_progress)
                                rl_callback_read_char();
                        else
                                while (read_available_char(0) >= 0) ;
                }
                if (FD_ISSET(simics_fd, &readfds))
                        handle_simics_message();
        }
}

static void
usage(void)
{
        fprintf(stderr, "usage: readhist simics-fd\n");
        exit(1);
}

static void
save_history(void)
{
        if (simics_history && !cmdline_disabled) {
                /* write history to file, to truncate it */
                write_history(simics_history);
        }
}

int
main(int argc, char **argv)
{
	sigset_t blk_set;
        struct sigaction sigact;
        char msg[MAX_MSG_LEN];
        char cmd;
        int len;

        if (argc < 2)
                usage();

        simics_fd = atoi(argv[1]);

        /* Simics will handle most signals, and we will die when it dies,
           so only accept some signals */
	sigfillset(&blk_set);
        sigdelset(&blk_set, SIGTSTP);
        sigdelset(&blk_set, SIGWINCH);
        sigdelset(&blk_set, SIGTERM);

        sigprocmask(SIG_SETMASK, &blk_set, NULL);

        sigact.sa_handler = sigtstp_handler;
        sigact.sa_flags = SA_RESTART;
        sigemptyset(&sigact.sa_mask);
        if (sigaction(SIGTSTP, &sigact, NULL) < 0) {
                perror("sigaction");
                exit(1);
        }

        make_blocking(simics_fd);

        len = read_message(msg, &cmd);
        if (len < 0) {
                fprintf(stderr, "readhist: no begin command\n");
                exit(1);
        } else {
                if (cmd != RH_BEGIN) {
                        fprintf(stderr,
                                "readhist: unexpected message at init\n");
                        exit(1);
                }
                simics_history = malloc(PATH_MAX);
                sscanf(msg, "%d;%d;%s", &batch_mode,
                       &history_lines, simics_history);
        }

        atexit(save_history);

        init_readhist();
        main_loop();

        return 0;
}
