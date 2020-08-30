# PySys Sample - Getting Started
[![PySys tests](../../workflows/PySys/badge.svg)](../../actions)
[![codecov](https://codecov.io/gh/pysys-test/sample-getting-started/branch/main/graph/badge.svg)](https://codecov.io/gh/pysys-test/sample-getting-started)

This project shows how to use the PySys system test framework to test a sample application (a small REST/HTTP server). 

Explore the tests in this project to get an idea for what is possible with PySys, or fork this repo to get started 
with your own project.

# License

PySys sample projects are not shipped with the same license as PySys itself; instead the samples are released into the 
public domain (as described in the LICENSE file) to simplify copying and freely reusing in your own projects, whatever 
license they may use. 

# Running the tests

To use this project all you need is Python 3.6+, and the latest version of PySys. You can run all the tests like this:

	cd test
	pysys.py run

To run just test MyServer_001:

	pysys.py run 001

PySys includes support for GitHub actions, and you can see the results of executing this test project in the 
[Actions](../../actions) tab for this repo. 

# Exploring the sample tests

Now it's time to start exploring the run.py files in each of the tests. 

The best way to find out what each test does is to print out the test titles like this:

	pysys.py print

Start with 001 test in the correctness/ directory which is a simple example to show the basics, then move on to the 
higher numbered tests to explore in more detail how to execute processes, validate results and more. 

This project also a performance test under the performance/ directory, which records throughput and latency summary 
statistics for our sample server. Have a look at how the run.py is written to see some recommended patterns for 
recording performance summary results, and then open the .csv file in the test/__pysys_performance directory to see 
what the performance summary looks like. In the performance directory there is an example of a pysysdirconfig.xml 
file that provides defaults for all tests under that directory.

For more information about the commands you see in the tests, see the [PySys documentation](https://pysys-test.github.io/pysys-test).

# Exploring some useful pysys.py options

If you want to re-run just the validation part of a test (which is a big time-saver during test development):

	pysys.py run 001 --validateOnly

PySys makes it easy to reproduce race conditions in your application by cycling a failing testcase many times, and to  
run multiple test jobs concurrently for faster execution:

	pysys.py run 001 --cycle=20 -j5

The 003 test demonstrates the PySys concept of running a test in multiple "modes". By default just the primary mode is 
executed, but to run all the available modes, just use --mode=ALL:

	pysys.py run 003 --mode=ALL

There is also a performance test, and just to show that numbers aren't essential in test ids, this is given a name 
("SensorValuesEndpoint") rather than a number. It has a class variable called "iterations" which controls how long the 
test runs for. If you wanted to run the test for a larger number of iterations to try to get a more stable performance 
result this is easy to do using the -X argument:

	pysys.py run SensorValuesEndpoint -Xiterations=5000

For more information about the available options see the help page:

	pysys.py run -h
