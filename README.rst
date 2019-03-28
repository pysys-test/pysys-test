What is PySys?
==============
PySys is an easy-to-use cross-platform framework for writing and orchestrating 
all your system/integration tests, together with your unit and manual 
tests. 

It provides a comprehensive package of utility methods to make all the common 
system/integration testing operations a breeze, as well as the flexibility to 
add whatever test execution and validation logic you need using the full power 
of the Python language. 

Whatever language the application you're testing is written in, and whatever 
platforms it needs to run on, PySys can help!

Key features include:

- A comprehensive library of assertion methods appropriate for system-level 
  testing, such as checking for error/success messages in log files and 
  comparing the contents of output files.
- A comprehensive library of methods to automate platform-independent process 
  starting, orchestration, and cleanup, for both Windows and Unix-based 
  systems. Includes common operations such as:

   * dynamic port allocation, 
   * waiting until a server is running on a specified port
   * waiting until a file contains a specified message, 
   * aborting early if an error message is detected

- Support for executing tests in parallel to significantly speed up execution 
  time.
- A process memory monitoring framework to check for memory leaks when soak 
  testing your application.
- A performance monitoring framework for recording and aggregating latency, 
  throughput and other performance metrics.
- A pluggable "writers" framework for recording test outcomes in any format, 
  including a standard JUnit-compatible XML results writer in the box.
- Integrated support for running PyUnit tests, in case your application is also 
  written in Python.
- Integrated support for executing manual/interactively driven test cases.
- Test categorization and selective include/exclude execution, using per-test 
  classification groups.
- Supports Windows, Linux, macOS and Solaris. 


Project Links
=============
.. image:: https://travis-ci.com/pysys-test/pysys-test.svg?branch=latest
	:target: https://travis-ci.com/pysys-test/pysys-test

.. image:: https://codecov.io/gh/pysys-test/pysys-test/branch/latest/graph/badge.svg
	:target: https://codecov.io/gh/pysys-test/pysys-test

- API documentation: https://pysys-test.github.io/pysys-test
- Download releases, including sample testcases: https://github.com/pysys-test/pysys-test/releases
- Stackoverflow tag for questions: https://stackoverflow.com/tags/pysys
- Change log: https://github.com/pysys-test/pysys-test/blob/master/CHANGELOG.rst
- Bug/enhancement issue tracker: https://github.com/pysys-test/pysys-test/issues
- Source repository: https://github.com/pysys-test/pysys-test

License and credits
===================
PySys is licensed under the GNU LESSER GENERAL PUBLIC LICENSE Version 2.1. See 
LICENSE.txt for details. 

PySys was created and developed by Moray Grieve. The current maintainer is 
Ben Spiller. 

This is a community effort so we welcome your contributions, whether 
enhancement issues or GitHub pull requests! 

Installation
============

.. warning:: 
	This document describes how the upcoming PySys version 1.4.0 can be 
	installed, but as it has not yet been released on PyPi these instructions 
	do not yet work. 

	To install PySys 1.3.0 or earlier, see the README provided with the 
	release you're installing instead. 


PySys can be installed into Python 3.5/3.6/3.7+ (recommended) or Python 2.7. 

The best way to install PySys is using the standard `pip` installer 
to download and install the binary package (`.whl`) for the current PySys 
release, by executing::

	> python -m pip install pysys

Alternatively, you can download the binary .whl distribution from 
https://github.com/pysys-test/pysys-test/releases and use 
`python -m pip install PySys-<VERSION>.whl` instead. 

Make you have an up-to-date pip using `python -m pip install --upgrade pip`.
See https://packaging.python.org/tutorials/installing-packages for 
more information about using `pip`.

Windows
-------
On Windows, pip will automatically install the 
`pywin32 <https://pypi.org/project/pywin32/>`_ and 
`colorama <https://pypi.org/project/colorama/>`_ 
libraries that PySys depends upon.

The executable launcher script `pysys.py` is installed into the `Scripts\\` 
directory of the Python installation, e.g. `c:\\Python\\Scripts\\pysys.py`. 
To allow easy invocation of PySys from any test directory you may wish to add 
the Scripts directory to your `PATH` or copy the script to a location that is 
already on `PATH`. Alternatively you can run PySys using `python -m pysys`.


Unix
----
On Unix, those wishing to use the manual tester should ensure they have 
installed the tcl/tk libraries on the host machine and are using a Python 
version that was compiled with tcl/tk support.

The executable launcher script `pysys.py` is installed into Python's binary 
directory, e.g. `/usr/local/bin`, and hence should be on the current user's 
`PATH` automatically; if not, just add it. Alternatively you can run PySys 
using `python -m pysys`.


Getting Started
===============
After installation, to see the available options to the pysys.py script use::

	> pysys.py --help
  
The script takes four main top level command line options to it: 
`run`, `print`, `make` and `clean`, which are used to run a set of testcases, 
print the metadata for a set of testcases, make a new testcase directory 
structure, or clean all testcase output. For more information on the further 
options available to each add --help after the top level option, e.g. ::

	> pysys.py run --help


PySys has a set of simple sample testcases to demonstrate its use for 
running automated and manual testcases. 

The samples can be downloaded as a `.tar.gz` containing files with Unix line 
endings, or a `.zip` using Windows line endings from 
https://github.com/pysys-test/pysys-test/releases.

To unpack the tests on Unix systems, use::

	> tar zxvpf PySys-VERSION-sample-testcases-unix.tar.gz
	> cd pysys-examples

To run the testcases, after changing directory to the testcases location, 
simply execute::

	> pysys.py run  

When creating your own test suite you should copy the `pysysproject.xml` 
file from the examples directory into the root of your tests directory to get 
a good set of default settings which you can then customize as needed. 

For reference information about the PySys API, see
https://pysys-test.github.io/pysys-test.

