#include <stdio.h>

int main(int argc, char* argv[]) {
  int max_index;
  long i;
  long *fib;

  // don't specify an argument less than 0!!
  if (argc == 2) {

	 max_index = atoi(argv[1]);
	 fib = (long *)malloc(max_index*sizeof(long));
	 
	 // create the fibonacci array
	 fib[0] = 0;
	 fib[1] = 1;
	 for(i=2; i<max_index; i++){
		fprintf(stderr, "Calculating index %d\n", i);
		fib[i] = fib[i-1] + fib[i-2];
	 }
	 
	 // print out the array to stdout 
	 for(i=0; i<max_index; i++){
		fprintf(stdout, "%lu\n", fib[i]);
	 }
	 
  }
  else {
	 fprintf(stderr, "Usage: %s <index>\n", argv[0]);
  }  

  return 0;
}
