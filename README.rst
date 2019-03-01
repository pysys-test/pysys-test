What is PySys?
==============
PySys is an easy-to-use cross-platform framework for writing and orchestrating all your system/integration tests, fully integrated with your unit and manual tests. 

It provides a comprehensive package of utility methods to make all the common system/integration testing operations a breeze, as well as the flexibility to add whatever test execution and validation logic you need using the full power of the Python language. If you've ever tried to repurpose a unit-test oriented framework such as JUnit/NUnit for writing system tests you'll find PySys makes your life a lot easier - there's no need to wait for testcase code to compile, put up with limited access to platform-specific APIs, or write a huge library of custom helper classes to deal with the process orchestration and log file checking aspects of integration testing. It's also a lot more powerful and easy to maintain than writing platform-specific shell scripts. Whatever language the application you're testing is written in, and whatever platforms it needs to run on, PySys can help!

Key features include:

- A comprehensive library of assertion methods appropriate for system-level testing, such as checking for error/success messages in log files and comparing the contents of output files
- A comprehensive library of methods to automate platform-independent process starting, orchestration, and cleanup, for both Windows and Unix-based systems. Includes common operations such as:

  * dynamic port allocation, 
  * waiting until a server is running on a specified port
  * waiting until a file contains a specified message, 
  * aborting early if an error message is detected

- Support for executing tests in parallel to significantly speed up execution time
- A process memory monitoring framework to check for memory leaks when soak testing your application
- A performance monitoring framework for recording and aggregating latency, throughput and other performance metrics
- A pluggable "writers" framework for recording test outcomes in any format, including a standard JUnit-compatible XML results writer in the box
- Integrated support for running PyUnit tests, in case your application is also written in Python
- Integrated support for executing manual interactively driven test cases
- Test categorization and selective include/exclude execution, using per-test classification groups


Project Links
=============
- API documentation: https://pysys-test.github.io/pysys-test
- Dowload releases, including example testcases: https://github.com/pysys-test/pysys-test/releases
- Stackoverflow tag for questions: https://stackoverflow.com/tags/pysys
- Change log: https://github.com/pysys-test/pysys-test/blob/master/CHANGELOG.rst
- Bug/enhancement issue tracker: https://github.com/pysys-test/pysys-test/issues
- Source respository: https://github.com/pysys-test/pysys-test

License and credits
===================
PySys is licensed under the GNU LESSER GENERAL PUBLIC LICENSE Version 2.1. See LICENSE.txt for details. 

PySys was created and developed by Moray Grieve. The current maintainer is Ben Spiller. 

This is a community effort so we welcome your contributions, whether enhancement issues or github pull requests! 

Installation
============

.. warning:: 
   This document describes how the upcoming PySys version 1.4.0 can be 
   installed, but as it has not yet been released on PyPi these instructions 
   do not yet work. 
   
   To install PySys 1.3.0 or earlier, see the README provided with the 
   release you're installing instead. 


PySys can be installed into Python 3.5/3.6/3.7+ (recommended) or Python 2.7. 

The best way to install PySys is using the standard 
`pip <https://packaging.python.org/tutorials/installing-packages>`_ installer 
to download and install the binary package (.whl) for the current PySys release 
from, by executing::

	> pip install pysys

Alternatively, you can download the binary .whl distribution from 
https://github.com/pysys-test/pysys-test/releases and use `pip install XXX.whl` 
instead. Make you have an up-to-date pip using `pip install --upgrade pip`. 

Windows
-------
On Windows, pip will automatically install the 
`pywin32 <https://pypi.org/project/pywin32/>`_ extensions written 
by Mark Hammond which PySys depends upon. Windows users may optionally 
install the `colorama <https://pypi.org/project/colorama/>`_ library 
(using `pip install colorama`) to enable colored output on the console. 

The executable launcher script `pysys.py` is installed into the `Scripts\` 
directory of the Python installation, e.g. `c:\Python\Scripts\pysys.py`. 
To allow easy invocation of PySys from any test directory you may wish to add 
the Scripts directory to your `PATH` or copy the script to a location that is 
already on `PATH`. 


Unix
----
On Unix, those wishing to use the manual tester should ensure they have 
installed the tcl/tk libraries on the host machine and are using a Python 
version that was compiled with tcl/tk support.

The executable launcher script `pysys.py` is installed into Python's binary 
directory, e.g. `/usr/local/bin`, and hence should be on the current user's 
`PATH` automatically; if not, just add it. 


Getting Started
===============
After installation, to see the available options to the pysys.py script use::

  > pysys.py --help
  
The script takes four main top level command line options to it: 
`run`, `print`, `make` and `clean`, which are used to run a set of testcases, 
print the meta data for a set of testcases, make a new testcase directory 
structure, or clean all testcase output. For more information on the further 
options available to each add --help after the top level option, e.g. ::

  > pysys.py run --help


PySys has a set of simple example testcases to demonstrate its use for 
running automated and manual testcases. 

The samples can be downloaded as a `.tar.gz` containing files with Unix line 
endings, or a `.zip` using Windows line endings from 
https://github.com/pysys-test/pysys-test/releases.

To unpack the tests on Unix systems, use::

	> tar zxvpf PySys-examples.X.Y.Z.tar.gz
	> cd pysys-examples

To run the testcases, after changing directory to the testcases location, 
simply execute::

	> pysys.py run  

When creating your own test suite you should copy the `pysysproject.xml` 
file from the examples directory into the root of your tests to get 
a good set of default settings which you can then customize as needed. 

For reference information about the PySys API, see
https://pysys-test.github.io/pysys-test.
