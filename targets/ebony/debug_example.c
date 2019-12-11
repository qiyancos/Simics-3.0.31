/*
  Copyright 2005-2007 Virtutech AB
  
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
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>

/*
 * A full definition of the magic instructions is available
 * in simics/magic-instruction.h, which can be found in the
 * [simics]/src/include/ tree. Use -I flag to gcc.
 */
#include <simics/magic-instruction.h>

/* This is our Segmentation Fault handler */
void sigsegv_handler(int sig)
{
        printf("Got segmentation fault!\n");
        exit(1);
}

/* Struct describing a person and his/her occupation */
struct person {
        char name[8];
        char *type;
};

/* Reads a line from a file, and fill in the struct */
int read_developer(struct person *p, FILE *f)
{
        char line[100], *colon;

        if (fgets(line, 100, f) == NULL)
                return 0;       /* end of file */

        /* Type is always developer */
        p->type = "developer";

        /* Everything until the first colon is the name */
        colon = strchr(line, ':');
        *colon = '\0';
        strcpy(p->name, line);
        return 1;
}

int main(int argc, char **argv)
{
        const char *filename = "/etc/passwd";
        FILE *f;
        struct person user;

        /* Install signal handler */
        signal(SIGSEGV, sigsegv_handler);

        MAGIC_BREAKPOINT;

        /* Open file */
        printf("Reading %s...\n", filename);
        f = fopen(filename, "r");

        /* Read and print all users found in the file */
        while (read_developer(&user, f)) {
                printf("User: %s, ", user.name);
                printf("Type: %s\n", user.type);
        }

        printf("Done.\n");
        return 0;
}
