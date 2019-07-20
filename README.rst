What is PySys?
==============
PySys is an easy-to-use cross-platform framework for writing and orchestrating 
all your system/integration tests, combined seamlessly with your unit and 
manual tests. 

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
  time, with a flexible mechanism for controlling execution order.
- Support for executing the same test in several modes during your test 
  run (for example against different web browsers, databases, etc). 
- A process memory monitoring framework to check for memory leaks when soak 
  testing your application.
- A performance monitoring framework for recording and aggregating latency, 
  throughput and other performance metrics.
- A pluggable "writers" framework for recording test outcomes in any format, 
  including a standard JUnit-compatible XML results writer in the box, and 
  support for running tests under Travis CI.
- Integrated support for running PyUnit tests and doctests, in case your 
  application is also written in Python.
- Integrated support for executing manual/interactively driven test cases.
- Test categorization and selective include/exclude execution, using per-test 
  classification groups.
- Support for Windows, Linux, macOS and Solaris. 


Project Links
=============
.. image:: https://travis-ci.com/pysys-test/pysys-test.svg?branch=master
	:target: https://travis-ci.com/pysys-test/pysys-test

.. image:: https://codecov.io/gh/pysys-test/pysys-test/branch/master/graph/badge.svg
	:target: https://codecov.io/gh/pysys-test/pysys-test

- API documentation: https://pysys-test.github.io/pysys-test
- Download releases, including sample testcases: https://github.com/pysys-test/pysys-test/releases
- Stackoverflow tag for questions: https://stackoverflow.com/tags/pysys
- Change log: https://github.com/pysys-test/pysys-test/blob/master/CHANGELOG.rst
- Bug/enhancement issue tracker: https://github.com/pysys-test/pysys-test/issues
- Source repository: https://github.com/pysys-test/pysys-test

License and Credits
===================
PySys is licensed under the GNU LESSER GENERAL PUBLIC LICENSE Version 2.1. See 
LICENSE.txt for details. 

PySys was created and developed by Moray Grieve. The current maintainer is 
Ben Spiller. 

This is a community effort so we welcome your contributions, whether 
enhancement issues or GitHub pull requests! 

Installation
============

PySys can be installed into Python 3.7/3.6/3.5 (recommended) or Python 2.7 
(though note that Python 2.7 will soon be out of support from the Python team). 

The best way to install PySys is using the standard `pip` installer which 
downloads and install the binary package (`.whl`) for the current PySys 
release, by executing::

	> python -m pip install PySys

Alternatively, you can download the binary .whl distribution from 
https://github.com/pysys-test/pysys-test/releases and use 
`python -m pip install PySys-<VERSION>.whl` instead. 

Make sure you have an up-to-date pip using `python -m pip install --upgrade pip`.
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
The executable launcher script `pysys.py` is installed into Python's binary 
directory, e.g. `/usr/local/bin`, and hence should be on the current user's 
`PATH` automatically; if not, just add it. Alternatively you can run PySys 
using `python -m pysys`.

Those wishing to use the manual tester should ensure they have 
installed the tcl/tk libraries on the host machine and are using a Python 
version that was compiled with tcl/tk support.


Getting Started
===============
After installation, to see the available options to the pysys.py script use::

	> pysys.py --help
 
The script has four main commands: 
  - `makeproject` to create your top-level testing project configuration file, 
  - `make` to create individual testcases, 
  - `run` to execute them, and 
  - `clean` to delete testcase output after execution.

For detailed information, see the `--help` command line. 

To get started, create a new directory to hold your tests. Then run the 
`makeproject` command from that directory to add a `pysysproject.xml` 
file which will hold default settings your all your tests::

	> mkdir tests
	> cd tests
	> pysys.py makeproject

Then to create your first test, run::

	> pysys.py make MyApplication_001

This will create a `MyApplication_001` subdirectory with a `pysystest.xml` 
file holding metadata about the test such as its title, and a `run.py` 
where you can add the logic to `execute` your test, and to `validate` that 
the results are as expected. 

To run your testcases, simply execute::

	> pysys.py run


Next Steps
==========
The methods you need for typical tasks like starting processes (`startProcess`), 
waiting for messages in log files (`waitForSignal`) and of course validating 
the results (various assert methods such as `assertGrep`) are 
all defined on the `BaseTest` class, so look that up in the API documentation 
for full details of what is possible - see https://pysys-test.github.io/pysys-test. 

You might also want to take a look at our sample testcases for some practical 
examples. These can be downloaded as a `.tar.gz` containing files with Unix 
line endings, or a `.zip` using Windows line endings from 
https://github.com/pysys-test/pysys-test/releases.

To unpack the tests on Unix systems, use::

	> tar zxvpf PySys-VERSION-sample-testcases-unix.tar.gz
	> cd pysys-examples

To run the testcases, after changing directory to the testcases location 
simply execute::

	> pysys.py run  

The `fibonacci` sample tests are a good place to start. 
