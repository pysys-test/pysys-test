# PySys Sample - Configuration and extensions cookbook

This project is a "cookbook" of snippets you can copy into your own project to configure PySys or create classes 
that extend PySys using its Python API. 

It is structured like a "real" project, but aims to demonstrate most of the available PySys configuration options and 
plugin/extension points in a form that will be useful for intermediate-level PySys users already familiar with the 
basics (see the Getting Started sample).

# License

PySys sample projects are not shipped with the same license as PySys itself; instead the samples are released into the 
public domain (as described in the LICENSE file) to simplify copying and freely reusing in your own projects, whatever 
license they may use. 

# Running the tests

To use this project all you need is Python 3, and the latest version of PySys. 

To run all tests - except the manual (non-auto ones) - with recording of the results (to show the functionality of all 
the configured writers) and code coverage:

	cd test
	pysys.py run -j0 --record -XcodeCoverage --type=auto

Note that this project contains some tests that deliberately fail, so that you can see how failing test results are 
recorded. 

# Main features

* pysysproject.xml - a comprehensive project configuration file showing how to configure project properties, a variety 
  of custom plugin extensions, and all the standard PySys writer classes.
* pysys-extensions/myorg/ - a Python package containing some custom extensions using the PySys API. 
* demo-tests/ - a directory of tests to demonstrate the functionality of the extensions and project configuration, 
  also some testcase types such as PySys manual (human-driven) tests, and PyUnit test execution from PySys. 

For more information on anything you see here, see the [PySys documentation](https://pysys-test.github.io/pysys-test).
