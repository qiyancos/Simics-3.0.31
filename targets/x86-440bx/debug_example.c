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

#define MAX_VALUE 1000000

/*
  A full definition of the magic instructions is available
  in simics-magic-instruction.h
*/
#define MAGIC_INSTRUCTION do {                  \
        __asm__ __volatile__ ("xchg %bx,%bx");  \
} while (0)

void mark(char *array, int start, int step) 
{
        int i;

	for (i=start; i<MAX_VALUE; i+=step)
                array[i] = 1;
}

int sum(char *array, int size) 
{
	int sum = 0;
	int i;

        for (i=0; i<size; i++)
		sum += array[i];

	return sum;
}

int main(int argc, char **argv) 
{
        int i;
	char *nonprime;

        printf("Allocating space\n");

        nonprime = (char *) calloc(1, MAX_VALUE); 

        printf("Counting\n");

        nonprime[0] = 1; 
        nonprime[1] = 1;

        MAGIC_INSTRUCTION;

	for (i=2; i<MAX_VALUE; i++)
		if (!nonprime[i])
			mark(nonprime, 2*i, i);

	printf("Primes less than %d: %d\n", 
               MAX_VALUE, MAX_VALUE - sum(nonprime, MAX_VALUE));

        printf("Done\n");

        free(nonprime);
        return 0;
}
