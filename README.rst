Welcome to PySys!
=================

PySys is a powerful cross-platform framework for writing great system/integration tests. 

It provides a comprehensive package of methods to make all the common system/integration testing operations a breeze, 
with all the flexibility and power of the Python language at your fingertips. PySys is a framework that gives you a 
single unified way to control the selection, ordering and reporting of every type of test including system 
correctness, performance, soak/robustness testing, unit testing and manual testing.

Whatever language the application you're testing is written in, and whatever platforms it needs to run on, 
PySys can help!

Key features include:

- A comprehensive library of assertion methods appropriate for system-level 
  testing, such as checking for error/success messages in log files and 
  comparing the contents of output files.
- A comprehensive library of methods to automate platform-independent process 
  starting, orchestration, and cleanup, for both Windows and Unix-based 
  systems. Includes common operations such as:

  * dynamically picking a free TCP/IP port, 
  * waiting until a server is running on a specified port,
  * waiting until a file contains a specified message, 
  * powerful primitives for pre-processing text files (e.g. configuration input files, or output logs)
  * aborting early with a clear failure messages if an error is detected in a log file

- Support for executing tests in parallel to significantly speed up execution 
  time, with a flexible mechanism for controlling execution order.
- Ability to cycle a test many times (and in parallel) to reproduce rare race 
  conditions. 
- Support for executing the same test in several modes during your test 
  run (for example against different web browsers, databases, etc). Python 
  lambda expressions give the power to easily create complex and dynamic lists of 
  modes that combine multi-dimensional parameter matrices. 
- A process memory monitoring framework to check for memory leaks when soak 
  testing your application.
- A performance monitoring framework for recording and aggregating latency, 
  throughput and other performance metrics.
- A pluggable "writers" framework for recording test outcomes in any format, 
  including a standard JUnit-compatible XML results writer and output archiver 
  in the box, and support for running tests under CI providers such as 
  GitHub(R) Actions and Travis CI(R).
- Integrated support for running PyUnit tests and doctests, in case your 
  application is also written in Python.
- Integrated support for executing manual/interactively driven test cases.
- Test categorization and selective include/exclude execution, using per-test 
  classification groups.
- Support for Windows, Linux, macOS and Solaris. 

PySys was created by Moray Grieve. The maintainer is now Ben Spiller. 
This is a community project so we welcome your contributions, whether 
enhancement issues or GitHub pull requests! 

Project Links
=============
.. image:: https://img.shields.io/pypi/v/PySys
	:target: https://pypi.org/project/PySys/

.. image:: https://img.shields.io/badge/license-LGPL-blue
	:target: https://pysys-test.github.io/pysys-test/license.html

.. image:: https://github.com/pysys-test/pysys-test/actions/workflows/pysys-test.yml/badge.svg
	:target: https://github.com/pysys-test/pysys-test/actions/workflows/pysys-test.yml

.. image:: https://codecov.io/gh/pysys-test/pysys-test/branch/master/graph/badge.svg
	:target: https://codecov.io/gh/pysys-test/pysys-test

- Documentation: https://pysys-test.github.io/pysys-test
- Stack Overflow tag for questions: https://stackoverflow.com/questions/ask?tags=pysys
- Bug/enhancement issue tracker: https://github.com/pysys-test/pysys-test/issues
- Source repository and sample projects: https://github.com/pysys-test

.. inclusion-marker-section-start-installation

Installation
============

PySys can be installed into any Python version from 3.6 to 3.9. 

The best way to install PySys is using the standard ``pip`` installer which 
downloads and install the binary package for the current PySys 
release, by executing::

	> python -m pip install PySys

Alternatively, you can download the binary ``.whl`` package from 
https://github.com/pysys-test/pysys-test/releases and use 
``python -m pip install PySys-<VERSION>.whl`` instead. 

Make sure you have an up-to-date pip using ``python -m pip install --upgrade pip``.
See https://packaging.python.org/tutorials/installing-packages for 
more information about using ``pip``.

Windows
-------
On Windows, pip will automatically install the 
`pywin32 <https://pypi.org/project/pywin32/>`_ and 
`colorama <https://pypi.org/project/colorama/>`_ 
libraries that PySys depends upon.

The executable launcher script ``pysys.py`` is installed into the ``Scripts\`` 
directory of the Python installation, e.g. ``c:\Python\Scripts\pysys.py``. 
To allow easy invocation of PySys from any test directory you may wish to add 
the Scripts directory to your ``PATH`` or copy the script to a location that is 
already on ``PATH``. Alternatively you can run PySys using ``python -m pysys``.


Unix
----
The executable launcher script ``pysys.py`` is installed into Python's binary 
directory, e.g. ``/usr/local/bin``, and hence should be on the current user's 
``PATH`` automatically; if not, just add it. Alternatively you can run PySys 
using ``python -m pysys``.

Those wishing to use the manual tester should ensure they have 
installed the tcl/tk libraries on the host machine and are using a Python 
version that was compiled with tcl/tk support.

.. inclusion-marker-section-start-getting-started

Getting Started
===============
After installation, to see the available options to the pysys.py script use::

	> pysys.py --help
 
The script has four main commands: 

- ``makeproject`` to create your top-level testing project configuration file, 
- ``make`` to create individual testcases, 
- ``run`` to execute them, and 
- ``clean`` to delete testcase output after execution.

For detailed information, see the ``--help`` command line. 

To get started, create a new directory to hold your tests. Then run the 
``makeproject`` command from that directory to add a ``pysysproject.xml`` 
file which will hold default settings your all your tests::

	> mkdir test
	> cd test
	> pysys.py makeproject

Then to create your first test, run::

	> pysys.py make MyApplication_001

This will create a ``MyApplication_001`` subdirectory with a ``pysystest.py`` file that contains both "descriptor" 
metadata about the test such as its title, and a Python class where you can add the logic to ``execute`` your test, 
and to ``validate`` that the results are as expected. 

To run your testcases, simply execute::

	> pysys.py run

To give a flavour for what's possible, here's a system test for checking the behaviour of a server application 
called MyServer, which shows of the most common PySys methods:

.. code-block:: python

  __pysys_title__   = r""" MyServer startup - basic sanity test (+ demo of PySys basics) """
  
  __pysys_purpose__ = r""" To demonstrate that MyServer can startup and response to basic requests. 
    """

  class PySysTest(pysys.basetest.BaseTest):
    def execute(self):
      # Ask PySys to allocate a free TCP port to start the server on (this allows running many tests in 
      # parallel without clashes)
      serverPort = self.getNextAvailableTCPPort()
      
      # A common system testing task is pre-processing a file, for example to substitute in required 
      # testing parameters
      self.copy(self.input+'/myserverconfig.json', self.output+'/', mappers=[
        lambda line: line.replace('@SERVER_PORT@', str(serverPort)),
      ])
      
      # Start the server application we're testing (as a background process)
      # self.project provides access to properties in pysysproject.xml, such as appHome which is the 
      # location of the application we're testing
      server = self.startProcess(
        command   = self.project.appHome+'/my_server.%s'%('bat' if IS_WINDOWS else 'sh'), 
        arguments = ['--configfile', self.output+'/myserverconfig.json', ], 
        environs  = self.createEnvirons(addToExePath=os.path.dirname(PYTHON_EXE)),
        stdouterr = 'my_server', displayName = 'my_server<port %s>'%serverPort, background = True,
        )
      
      # Wait for the server to start by polling for a grep regular expression. The errorExpr/process 
      # arguments ensure we abort with a really informative message if the server fails to start
      self.waitForGrep('my_server.out', 'Started MyServer .*on port .*', errorExpr=[' (ERROR|FATAL) '], process=server) 
      
      # Run a test tool (in this case, written in Python) from this test's Input/ directory.
      self.startPython([self.input+'/httpget.py', f'http://localhost:{serverPort}/data/myfile.json'], 
        stdouterr='httpget_myfile')
    
    def validate(self):
      # This method is called after execute() to perform validation of the results by checking the 
      # contents of files in the test's output directory. Note that during test development you can 
      # re-run validate() without waiting for a full execute() run using "pysys run --validateOnly". 
      
      # It's good practice to check for unexpected errors and warnings so they don't go unnoticed
      self.assertGrep('my_server.out', ' (ERROR|FATAL|WARN) .*', contains=False)
      
      # Checking for exception stack traces is also a good idea; and joining them into a single line with a mapper will 
      # give a more descriptive error if the test fails
      self.assertGrep('my_server.out', r'Traceback [(]most recent call last[)]', contains=False, 
        mappers=[pysys.mappers.JoinLines.PythonTraceback()])
      
      self.assertThat('message == expected', 
        message=pysys.utils.fileutils.loadJSON(self.output+'/httpget_myfile.out')['message'], 
        expected="Hello world!", 
        )
      
      self.logFileContents('my_server.out')

If you're curious about any of the functionality demonstrated above, there's lots of helpful information on these 
methods and further examples in the documentation:

- `pysys.basetest.BaseTest.getNextAvailableTCPPort()`
- `pysys.basetest.BaseTest.copy()`
- `pysys.basetest.BaseTest.startProcess()` (+ `pysys.basetest.BaseTest.createEnvirons()` and `pysys.basetest.BaseTest.startPython()`)
- `pysys.basetest.BaseTest.waitForGrep()`
- `pysys.basetest.BaseTest.assertGrep()`
- `pysys.basetest.BaseTest.assertThat()`
- `pysys.basetest.BaseTest.logFileContents()`
- `pysys.mappers`

Now take a look at `pysys.basetest` to begin exploring more of the powerful functionality 
PySys provides to help you implement your own ``pysystest.py`` system tests. 

The sample projects under https://github.com/pysys-test are a great starting point for learning more about PySys, and 
for creating your first project. 

.. inclusion-marker-section-start-license

License
=======

PySys System Test Framework

Copyright (C) 2006-2021 M.B. Grieve

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.
