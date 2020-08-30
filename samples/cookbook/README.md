# PySys Sample - Configuration, Extensions and Testing Techniques Cookbook

This project is a "cookbook" of snippets you can copy into your own project to configure PySys or create classes 
that extend PySys using its Python API, as well as some testcases that show common best practices and techniques. 

The focus is on making useful code snippets accessible (and not pretending this is anything like a "real" project). 
This sample demonstrates most of the available PySys configuration options and plugin/extension points in a form that 
will be useful for intermediate-level PySys users already familiar with the basics (see the 
https://github.com/pysys-test/sample-getting-started sample first if you're just starting to learn PySys).

# License

PySys sample projects are not shipped with the same license as PySys itself; instead the samples are released into the 
public domain (as described in the LICENSE file) to simplify copying and freely reusing in your own projects, whatever 
license they may use. 

# Running the tests

To use this project all you need is Python 3.6+, and the latest version of PySys. 

To run all tests - except the manual (non-auto ones) - with recording of the results (to show the functionality of all 
the configured writers) and code coverage:

	cd test
	pysys.py run -j0 --record -XcodeCoverage --type=auto

Note that this project contains some tests that deliberately fail, so that you can see how failing test results are 
recorded. 

This sample is automatically executed by GitHub(R) Actions - see the results (including the deliberate test failures) 
here: [![PySys tests](https://github.com/pysys-test/sample-cookbook/workflows/PySys/badge.svg)](https://github.com/pysys-test/sample-cookbook/actions)

# Main features

* pysysproject.xml - a comprehensive project configuration file showing how to configure project properties, a variety 
  of custom plugin extensions, and all the standard PySys writer classes.
* pysys-extensions/myorg/ - a Python package containing some custom extensions using the PySys API. 
* demo-tests/ - a directory of tests to demonstrate the functionality of the extensions and project configuration, and:
    * PySys manual (human-driven) tests
    * PyUnitTest - PyUnit test execution from PySys
    * PySysTestDescriptorSample and pysysdirconfig_sample - commented examples showing everything you can 
      in a PySys test or directory XML descriptor
    * test_outcome_samples - Examples of some failing tests, so you can see how careful use of assertions leads to really 
      informative messages when there's a failure. 

For more information on any PySys features demonstrated here, see the [PySys documentation](https://pysys-test.github.io/pysys-test).
