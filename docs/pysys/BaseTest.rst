The BaseTest Class
~~~~~~~~~~~~~~~~~~

.. automodule:: pysys.basetest

.. currentmodule:: pysys.basetest.BaseTest

In PySys each test is a class which contains the methods needed to execute your 
test logic and then to validate the results against the expected behaviour to produce a final "outcome" for the test. 

All test classes inherit (directly or indirectly) from the ``BaseTest`` class, which provides everything you need to 
create your own tests. 

Implementing your test class
============================

Each PySys test class must implement an `execute` method containing the main body of the test, and 
(usually) a `validate` method containing the assertions that check for the expected result. 
Sometimes you may also need to provide `setup` and/or `cleanup` functionality:

.. autosummary::
	setup
	execute
	validate
	addCleanupFunction

Taken together, the PySys ``setup() -> execute() -> validate()`` methods correspond to the common 
'Arrange, Act, Assert' testing paradigm. 

At the end of each test, PySys automatically terminates all processes it 
started, in the `cleanup` method. If any additional custom cleanup steps are required, these can be added by calling 
`addCleanupFunction`.

NB: Do not ever override the ``__init__`` constructor of a test class; instead use `setup` for any initialization, 
which ensures orderly cleanup if an exception occurs during the setup process. 

Test configuration
==================

The input/output directories and other essential information about this test object and its parent project are 
can be accessed via instance attributes on ``self``:

- ``self.input`` *(str)*: Full path to the input directory of the testcase, which is where test-specific resources such as 
  configuration files are stored. The directory is the main ``<testDir>`` for projects created from PySys 2.0 onwards, 
  or ``<testdir>/Input`` for projects created earlier. The path can be customized in the pysysdirconfig at a 
  project, directory (or even testcase) level.  
  
  Here is an example of copying a configuration file template from the input directory::
  
    self.copy(self.input+'/serverconfig.xml', self.output, mappers=[lambda line: line.replace('@PORT@', str(myport))])
  
  When storing large text files in the input directory it is recommended to use compression; see 
  `pysys.basetest.BaseTest.unpackArchive` for details of how to decompress input files. 
  
  Do *not* use the ``self.input`` field as a way to locate other resources that are in directories above Input/ (since 
  this will fail when the input directory is empty and using a version control system (e.g. git) that doesn't commit 
  empty directories). For other test resource locations the recommended approach is to use ``self.project.testRootDir``, 
  define a specific project property for the directory (if widely used), or if that's not practical then use 
  ``self.descriptor.testDir`` to get the test directory. 

- ``self.output`` *(str)*: Full path to the output directory of the testcase, which is the only location to which the 
  test should write output files, temporary files and logs. The output directory is automatically created and 
  cleaned of existing content before the test runs to ensure separate runs do not influence each other. 
  There are separate output directories when a test is run for multiple cycles or in multiple modes. 
  The directory is usually ``<testdir>/Output/<outdir>`` but the path can be customized in the testcase descriptor and 
  the ``--outdir`` command line argument. 
  
- ``self.reference`` *(str)*: Full path to the reference directory of the testcase, which is where reference comparison files 
  are stored (typically for use with `assertDiff`).
  The directory is usually ``<testdir>/Reference`` but the path can be customized in the testcase descriptor. 

- ``self.log`` *(logging.Logger)*: The Python ``Logger`` instance that should be used to record progress and status 
  information. For example:: 
  
    self.log.info("Starting myserver on port %d", serverport)

- ``self.mode`` (`pysys.config.descriptor.TestMode`): The user-defined mode this test object is running. Tests can use 
  this to modify how the test executed based upon the mode, for example to allow the test to run against either a mock 
  or a real database. TestMode subclasses str so you can include this in situation where you need the name of the mode 
  such as when recording performance result, and you can also use the ``.params`` attribute to access any parameters 
  defined on the mode. 

- ``self.testCycle`` *(int)*: The cycle in which this test is running. Numbering starts from 1 in a multi-cycle test run. 
  The special value of 0 is used to indicate that this is not part of a multi-cycle run. 

- ``self.descriptor`` (`pysys.config.descriptor.TestDescriptor`): The descriptor contains 
  information about this testcase such as the test id, groups and test type, and typically comes from the 
  test's ``pysystest.*`` file. 

- ``self.runner`` (`pysys.baserunner.BaseRunner`): A reference to the singleton runner instance that's 
  responsible for orchestrating all the tests in this project. The runner is where any cross-test state can be held, 
  for example if you want to have multiple tests share use of a single server, VM, or other resource. 

- ``self.project`` (`pysys.config.project.Project`): A reference to the singleton project instance containing the 
  configuration of this PySys test project as defined by ``pysysproject.xml``. 
  The project can be used to access information such as the project properties which are shared across all tests 
  (e.g. for hosts and credentials). 

- ``self.testPlugins`` *(list[object])*: A list of any configured test plugin instances. This allows plugins 
  to access the functionality of other plugins if needed (for example looking them up by type in this list). 

- ``self.disableCoverage`` *(bool)*: Set this to True to request that no code coverage is generated for this test 
  (even when code coverage has been enabled for the PySys run), for example because this is a time-sensitive 
  or performance-measuring test. Typically this would be set in an individual testcase, or in the `setup` method of 
  a `BaseTest` subclass based on groups in the ``self.descriptor`` that indicate what kind of test this is.

Additional variables that affect only the behaviour of a single method are documented in the associated method. 

There is also a field for each test plugin listed in the project configuration. Plugins provide additional 
functionality such as methods for starting and working with a particular language or tool. A test plugin is 
just a class with a method ``setup(self, testobj)`` (and no constructor arguments), that provides methods and 
fields for use by tests. Each test plugin listed in the project configuration 
with ``<test-plugin classname="..." alias="..."/>`` is instantiated for each 
`BaseTest` instance, and can be accessed using ``self.<alias>`` on the test object. If you are using a third party 
PySys test plugin, consult the documentation for the third party test plugin class to find out what methods and fields 
are available using ``self.<alias>.*``. 

If you wish to support test parameters that can be overridden on the command line using ``-Xkey=value``, just add a 
static variable just after the ```class MyClass(BaseTest):`` line containing the default value, and access it using 
``self.key``. If a new value for that key is specified with ``-Xkey=value``, that value will be set as an attribute by 
the BaseTest constructor, with automatic conversion from string to the correct type if the default value is a 
bool/int/float.

.. _assertions-and-outcomes:

Assertions and outcomes
=======================

.. autosummary::
	assertThatGrep
	assertGrep
	assertLineCount
	assertDiff
	assertThat
	assertLastGrep
	assertOrderedGrep
	assertPathExists
	abort
	skipTest
	addOutcome
	getOutcome
	getOutcomeReason
	getOutcomeLocation
	reportPerformanceResult

PySys has a library of assertion methods that are great for typical system testing validation tasks such as 
checking log messages, diff'ing output files against a reference, and for more complex cases, evaluating arbitrary 
Python expressions. All these methods are designed to give a really clear outcome reason if the assertion fails. 
Note that by default assertion failures do not abort the test, so all the validation statements will be executed 
even if some early ones fail. 

For example::

	def validate(self):
		self.assertGrep('myserver.log', expr=' (ERROR|FATAL|WARN) .*', contains=False)
		
		self.assertThatGrep('myserver.log', r'Successfully authenticated user "([^"]*)"', 
			"value == expected", expected='myuser')

		self.assertThat('actualNumberOfLogFiles == expected', actualNumberOfLogFiles__eval="len(glob.glob(self.output+'/myserver*.log'))", expected=3)

The available test outcomes are listed in `pysys.constants.OUTCOMES`. 

There are some deprecated methods which we do not recommend using: `assertEval`, `assertTrue`, `assertFalse` 
(`assertThat` should be used instead of these). 

Processes
=========

.. autosummary::
	startProcess
	startPython
	getNextAvailableTCPPort
	allocateUniqueStdOutErr
	createEnvirons
	getDefaultEnvirons
	signalProcess
	stopProcess
	writeProcess
	waitForBackgroundProcesses
	startProcessMonitor
	stopProcessMonitor

The most important part of a test's `execute` method is starting the process(es) that you are testing. Always use 
the `startProcess` method for this (or a wrapper such as `startPython`) rather than ``os.system`` or ``subprocess``, 
to ensure that PySys can cleanup all test processes at the end of the test. 

This class also provides methods to dynamically allocate a free TCP server port, 
and to monitor the memory/CPU usage of the processes it starts. 

Waiting
=======

PySys provides a number of methods that can be used in your `execute` method to wait for operations to complete, 
of which the most commonly used is `waitForGrep`. 

.. autosummary::
	waitForGrep
	waitForFile
	waitForBackgroundProcesses
	waitProcess
	waitForSocket
	wait
	pollWait

Do not use `wait` unless there is no alternative, since it makes tests both slower and more fragile than they ought to be. 

Files
=====

The helper methods for common file I/O operations are:

.. autosummary::
	copy
	unpackArchive
	mkdir
	deleteDir
	deleteFile
	grep
	grepOrNone
	grepAll
	logFileContents
	write_text
	getDefaultFileEncoding

To get the configured input/output directories for this test see `Test configuration`_.

For additional file/directory helper functions such as support for loading JSON and properties files, 
see the `pysys.utils.fileutils` module. 

Miscellaneous
=============
.. autosummary::
	compareVersions
	logValueDiff
	disableLogging
	startBackgroundThread
	pythonDocTest
	startManualTester
	stopManualTester
	waitManualTester
	getBoolProperty


.. currentmodule:: pysys.basetest

All BaseTest members
====================

.. autoclass:: BaseTest
   :inherited-members:
