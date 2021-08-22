
Change Log
==========

.. py:currentmodule:: pysys.basetest

.. note::

  Use the `issue tracker <https://github.com/pysys-test/pysys-test/issues>`_ if you want to report a bug or feature 
  request in the PySys test framework. For how-tos and advice, 
  `ask a question <https://stackoverflow.com/questions/ask?tags=pysys>`_. 


-------------------
What's new in 2.0
-------------------

PySys 2.0 was released in August 2021. Highlights from this release are:

- Addition of Python 3.9 support, and removal of Python 2 and 3.5 support. 
- A new standard test structure that avoids the use of XML by allowing descriptor values such as the test title to be 
  specified alongside your Python test class in a single ``pysystest.py`` file, instead of separate ``run.py`` and 
  ``pysystest.xml`` files. You can mix and match the old and new styles within the same project. For new PySys projects 
  a simpler directory layout is now recommended in which the ``self.input`` directory is configured to be the main 
  ``testDir/`` (which also contains the ``pysystest.py`` file) instead of having a separate ``testDir/Input/`` 
  subdirectory for input files. This can make test contents easier to navigate. 
- Some big extensions to the concept of "modes" that allow for more powerful configuration and use, including 
  mode parameters for easier handling of multi-dimensional modes, and dynamic mode lists configured with a Python 
  lambda expression. 
- A new template-based implementation of ``pysys make``, allowing easy configuration of how new tests are created - 
  on a per-directory basis - and also automatic generation of test identifiers for new tests (when using numeric 
  identifiers). 
- Several improvements to the `pysys.mappers` API for more easily transforming text files during copy and grep 
  operations, including support for multi-line exception stack traces. 
- A large set of smaller additions, many based on end-user requests. PySys "power users" are encouraged to read through 
  the full Change Log below to ensure they're aware of all the new functionality they might be able to benefit from. 
- There are a few breaking changes (see Migration Notes below) but in practice these are likely to affect few 
  users. 

Version and documentation changes
---------------------------------
- Added support for Python 3.9.
- Removed support for Python 2 and 3.5, which are now end-of-life. 
- PySys releases now use a simpler 2-digit semantic version, so this release is v2.0 compared to the previous 
  v1.6.1. The first digit changes when there are potentially breaking changes that are likely to require users to 
  update their existing tests.
- Added a new "cookbook" sample which is a great repository of copyable snippets for configurating and extending 
  PySys.
- Documentation for :doc:`/pysys/ProjectConfiguration` and :doc:`/pysys/TestDescriptors` is much improved. 

New test structure and descriptors
----------------------------------
Previously, every PySys test was defined by a ``pysystest.xml`` file. In practice having the test descriptor values 
separated from the ``run.py`` in a different file made tests harder to navigate. You can continue to use 
``pysystest.xml`` files if you wish, but the recommended structure for new tests is a single file called 
``pysystest.py``. There is a new Python-style syntax for specifying descriptor values within this file, for example::

	__pysys_title__   = r""" My foobar tool - Argument parsing success and error cases """
	#                        ========================================================================================================================

	__pysys_purpose__ = r""" The purpose of this test is to check that 
		argument parsing addresses these criteria:
			- Correctness
			- Clear error messages
		"""

	__pysys_groups__           = "performance, disableCoverage; inherit=true"
	#__pysys_skipped_reason__  = "Skipped until Bug-1234 is fixed"

For a full example of all the possible options (including more details on the subset of Python syntax PySys will 
parse correctly) see :doc:`/pysys/TestDescriptors`.  

Note that the ``=====`` characters act not only as an underline but also provide a guide to help test authors know 
when their title string has exceeded 80 characters which should be avoided if possible to make ``pysys print`` output 
easy to read. The character and length of this guide can be customized with project property 
``pysystestTemplateLineLengthGuide`` if desired. 

New descriptor values were added to record the ``authors`` who have worked on the test, and the original test 
``created`` date, both of which are useful to have available when looking into test failures. These are automatically 
populated when using ``pysys make``, but would need to be manually updated if you create tests through other means 
such as copying from an existing test. 

Actually PySys will recognize *any* file named ``pysystest.*`` (case insensitive) as a test not just ``pysystest.py``, 
so the same mechanism can be used for non-Python languages, for example a file named ``PySysTest.cs`` would also be 
identified as a PySys test. It just needs to contain at least a ``__pysys_title__ = ...``, and there would need to be 
an associated Python class for executing it (could be configured in the same file or in a parent 
``pysysdirconfig.xml``). 

It is also possible to embed an entire XML descriptor inside a ``pysystest.py`` using ``__pysys_xml_descriptor__ =`` 
which may be useful for some users. However note that parsing XML is really quite slow, so avoiding use of XML is an 
advantage, particularly if your project may grow large. 

See migration notes for more information about optionally switching to the new ``pysystest.py`` structure, including a 
sample utility to assist in migrating existing tests. 

Newly created PySys projects now store ``self.input`` files in the top-level ``<testDir>/`` of each test instead of the 
``<testDir>/Input/`` subdirectory, to make tests easier to navigate. Existing projects could be updated to follow the 
same structure if desired, or could make use of a new ``<input-dir>`` value to use ``Input/`` for existing tests in the 
project but not tests created from now on; see the migration notes below for more information. 

Other project and test configuration improvements
-------------------------------------------------
For those still using XML is now a leaner recommended structure for test descriptors which makes several 
elements optional, to allow descriptors to be shorter:

- Instead of specifying groups in separate ``<group>`` elements you can now specify them in a single string using 
  ``<groups groups="my-group1, my-group2"/>``.  
- The ``<description>`` element is no longer required - ``<title>`` and ``<purpose>`` can be placed directly under 
  the root element. 
- The ``<classification>`` element is no longer required - ``<modes>`` and ``<groups>`` can be placed directly under 
  the root element. 
- The ``<data>`` element is no longer required except as a parent for ``<user-data>``. Default directories can be 
  specified with ``<input/output/reference path=...>`` or using the slightly clearer names 
  ``<input-dir/output-dir/reference-dir>...<.../>``.
- ``<requirement id="..."/>`` elements can now be placed directly under the root element, without the need for 
  enclosing ``<traceability><requirements>...`` elements. 
- The ``<purpose>`` element is now optional; it's often clearer to put detailed multi-line information 
  about the test's purpose in the ``.py`` file alongside the test implementation.

Some additional improvements that will benefit advanced users are:

- PySys plugins sometimes provide a test class that can directly used by multiple tests (without each having their 
  own ``run.py``). You can now implement this pattern a lot more easily by specifying a fully qualified 
  ``classname`` and setting the ``module`` to the special string ``"PYTHONPATH"`` in the ``pysystest.*`` descriptor, 
  which will lookup the specified classname in the PYTHONPATH using Python's module importing mechanism. 
- Changed the creation of new tests (and the loading of test descriptors) to include the ``.py`` suffix in the 
  ``module=`` filename, to make it more explicit what is going on. As before, specifying this suffix is optional 
  so there is no need to update existing tests. 
- Added support for specifying project properties and descriptor user-data values using multi-line XML text 
  (or CDATA) as an alternative to setting the ``value=`` attribute. When converting string values to a list, 
  newline is now considered as a delimiter along with comma. This allows long value (especially path-like) 
  values to be specified in a more readable form, for example::
  
    <property name="myTestDescriptorPath">
      ${testRootDir}/foo/foo
      ${testRootDir}/foo/bar, ${testRootDir}/foo/baz
      
      <!-- Comments and whitespace are ignored when converting a string to a list -->
      
      ${testRootDir}/foo/bosh
    </property>
  
  Although less valuable there, the same approach can be used in non-XML ``pysystest.py`` files. 
- Top-level ``pysysdirconfig.xml`` directory configuration can now also be specified in the ``pysysproject.xml`` file 
  by adding a ``<pysysdirconfig>`` element under the ``<pysysproject>``. This allows all the ``pysysdirconfig`` options 
  such as your preferred Input/Reference/Output directory names to be specified in ``pysysproject.xml`` files and 
  ``makeproject`` templates. 

New template-based test maker
-----------------------------
There's now an easy way to create new tests specific to your project, or even multiple templates for individual 
directories within your project. This helps to encourage teams to follow the latest best practice by ensuring new 
tests are copying known good patterns, and also saves looking up how to do common things when creating new tests. 

The ``pysys make`` command line comes with a ``pysys-default-test`` template for creating a simple PySys test, you can 
add your own by adding ``<maker-template>`` elements to ``pysysdirconfig.xml`` in any directory under your project, 
or to a ``<pysysdirconfig>`` element in your ``pysysproject.xml`` file. Here are some examples (taken from 
the cookbook sample)::

	<pysysdirconfig>
		
		<maker-template name="my-test" description="a test with the Python code pre-customized to get things started" 
			copy="./_pysys_templates/MyTemplateTest/*" />

		<maker-template name="perf-test" description="a performance test including configuration for my fictional performance tool" 
			copy="${pysysTemplatesDir}/default-test/*, ./_pysys_templates/perf/my-perf-config.xml"/>

		<maker-template name="foobar-test" description="an advanced test based on the existing XXX test" 
			copy="./PySysDirConfigSample/*" 
			mkdir="ExtraDir1, ExtraDir2"
		>
			<replace regex='__pysys_title__ *= r"""[^"]*"""' with='__pysys_title__   = r""" Foobar - My new @{DIR_NAME} test title TODO """'/>
			<replace regex='__pysys_authors__ *= "[^"]*"'    with='__pysys_authors__ = "@{USERNAME}"'/>
			<replace regex='__pysys_created__ *= "[^"]*"'    with='__pysys_created__ = "@{DATE}"'/>
			<replace regex='@@DIR_NAME@@'                    with='@{DIR_NAME}'/>
		</maker-template>

	</pysysdirconfig>

For customizing the PySysTest class the best approach is usually to create a ``pysystest.py`` template test 
containing ``@@DEFAULT_DESCRIPTOR@@`` to include the default PySys descriptor values (this means your template will 
automatically benefit from any future changes to the defaults), and put it in a ``_pysys_templates/<templatename>`` 
directory alongside the ``pysystestdir.xml`` file. The ``_pysys_templates`` directory should contain a file 
named ``.pysysignore`` (which avoids the template being loaded as a real test). 

Other options are possible (as above) such as copying files from an absolute location such as under your project's 
``${testRootDir}``, copying from PySys default templates directly (if you just want to *add* files) by 
using ``${pysysTemplatesDir}/default-test/*``, or copying from a path relative to the XML file where the template is 
defined containing a real (but simple) test to copy from (with suitable regex replacements to make it more generic). 

See :doc:`/pysys/TestDescriptors` for more information about how to configure templates in a ``pysysdirconfig.xml`` file. 

When creating tests using ``pysys make``, by default the first template (from the more specific ``pysysdirconfig.xml``) 
is selected, but you can also specify any other template by name using the ``-t`` option, and get a list of available 
templates for the current directory using ``--help``. 

If you are using numeric suffixes (and assuming you don't have different prefixes in the same directory - not 
recommended!) you can now omit the test identifier/directory name argument and PySys will automatically pick one by 
incrementing the largest existing numeric identifier. 

It is possible to subclass the `pysys.launcher.console_make.DefaultTestMaker` responsible for this logic if needed. 
The main reason to do that is to provide a `pysys.launcher.console_make.DefaultTestMaker.validateTestId` method 
to check that new test ids do not conflict with others used by others in a remote version control system (to avoid 
merge conflicts). 

By default PySys creates ``.py`` files with tabs for indentation (as in previous PySys releases). If you prefer spaces, 
just set the new ``pythonIndentationSpacesPerTab`` project property to a string containing the required spaces per tab.

More powerful test modes
------------------------
This PySys release adds some big usability improvements for defining and using modes.

A more powerful and flexible configuration format is now provided for defining modes, which uses a Python 
lambda to provide the list of modes. Each mode can now define any number of *parameters* to avoid the need to 
parse/unpack from the mode string itself; these can then be accessed from a ``self.mode.params`` dictionary. 
The mode name can be automatically generated from the parameters, or provided explicitly. 

.. code-block:: python
	
	__pysys_modes__ = r""" 
			lambda helper: helper.inheritedModes+[
				{'mode':'CompressionGZip', 'compressionType':'gzip'},
			]
	"""

For those still using ``pysystest.xml`` files, the same Python lambda can also be added in your ``<modes>...</modes>`` 
element. 

There is also a helper function provided (in `pysys.config.descriptor.TestModesConfigHelper.combineModeDimensions`) 
to combine multiple mode "dimensions" together, for example every combination of your supported databases and your 
supported web browsers. This allows for some quite sophisticated logic to generate the mode list such as:

.. code-block:: python
	
	__pysys_modes__ = r""" 
		lambda helper: [
			mode for mode in 
				helper.combineModeDimensions( # Takes any number of mode lists as arguments and returns a single combined mode list
					helper.inheritedModes,
					{
							'CompressionNone': {'compressionType':None, 'isPrimary':True}, 
							'CompressionGZip': {'compressionType':'gzip'},
					}, 
					[
						{'auth':None}, # Mode name is optional
						{'auth':'OS'}, # In practice auth=OS modes will always be excluded since MyFunkyOS is a fictional OS
					],
					helper.makeAllPrimary(
						{
							'Usage':         {'cmd': ['--help'], 
								'expectedExitStatus':'==0', 'expectedMessage':None}, 
							'BadPort':       {'cmd': ['--port', '-1'],  
								'expectedExitStatus':'!=0', 'expectedMessage':'Server failed: Invalid port number specified: -1'}, 
							'SetPortTwice':  {'cmd': ['--port', '123', '--config', helper.testDir+'/myserverconfig.json'], 
								'expectedExitStatus':'!=0', 'expectedMessage':'Server failed: Cannot specify port twice'}, 
						}), 
					) 
			# This is Python list comprehension syntax for filtering the items in the list
			if (mode['auth'] != 'OS' or helper.import_module('sys').platform == 'MyFunkyOS')
		]
	"""

You can specify each dimension of modes either as a dict or a list (the latter is required to benefit from automatic 
generation of the mode name from the parameters). 

Previously there was just one mode designated as *primary*, which would run when no explicit ``--modes`` or ``--ci`` 
argument was specified. Now it is possible to configure multiple modes as primary (see above), and there is a helper 
method to add ``'isPrimary':True`` to a whole list/dict of modes which is handy when using modes for testing 
different test scenarios where you really want all of them executed by default even during quick local test runs. 

For more details see :doc:`/pysys/TestDescriptors`, :doc:`/pysys/UserGuide` and the Getting Started sample. 

Note that when using the new lambda-based mode configuration, the convention that modes begin with a capital letter 
is enforced by automatic upper-casing of the initial letter. If needed this can be turned off for existing projects 
which use lowercase mode names and have a mixture of old and new modes styles by setting the project property 
``enforceModeCapitalization`` to ``false``. 

There are also improvements to the ``pysys.py`` command line support for modes:

- ``pysys run --mode MODES`` now accepts regular expressions for modes, permitting more powerful selection of 
  a desired subset of modes.    
- ``pysys print --mode MODES`` now accepts the same mode specifiers (including regular expressions as above) 
  as ``pysys run``::

    pysys print -m MyDatabase2.0_FireFox,MyDatabase2.0_Chrome
    pysys print -m MyDatabase2.0_.*
    pysys print -m !MyOtherDatabase

Also, ``pysys print`` includes the ``~MODE`` suffix after the test identifier if a ``--mode`` filter was specified. 

Project configuration features
------------------------------
- Added automatic expansion of ``${...}`` project properties in a test/directory's 
  ``input/output/reference`` configuration.
- Added automatic normalization of slashes and ``..`` sequences in project property values for which 
  ``pathMustExist=true``. 
- Added a pre-defined project property ``${/}`` which is resolved to the forward or backslash character for this OS. 
- Added a pre-defined project property ``${username}`` which is resolved to the user running PySys. 
- Added a pre-defined project property ``${pysysTemplatesDir}`` which is the path to the directory where PySys stores 
  its default ``test/`` template for creating new tests; you may wish to reference this when defining the files to 
  copy into your own test templates. 
- Added support for executing Python ``eval()`` strings when resolving project properties. Other project properties 
  are available as Python variables when the ``eval()`` string is executed (and also in a ``properties`` dict, in case 
  of any name that is not a valid Python identifier). For more details on how ``eval()`` strings are evaluated within 
  PySys see `BaseTest.assertThat` which uses the same mechanism. For example::
  
    <property name="logConfigURL" value='${eval: "file:///"+os.path.abspath(appHome).replace("\\", "/")+"/logConfig.xml"}'/>

Process management improvements
-------------------------------
- Added automatic killing of nested child processes of processes PySys has started (using Unix "process groups", and 
  Windows "jobs"). This is especially useful when starting a process using a shell script; previously 
  only the wrapper script would have been killed, whereas now the process it starts is also terminated. 
- Fixed the default library path on macOS(R). Instead of setting ``DYLD_LIBRARY_PATH=/usr/lib:/usr/local/lib`` 
  (which overrides executables' default libraries), we now use the ``DYLD_FALLBACK_LIBRARY_PATH`` environment 
  variable. The `pysys.constants.LIBRARY_PATH_ENV_VAR` constant is now set to 'DYLD_FALLBACK_LIBRARY_PATH`. 
  Additionally, some extra items were added to the value of `pysys.constants.DYLD_LIBRARY_PATH` to match the 
  defaults as described in the latest macOS documentation. 
- Added improved debug logging to `BaseTest.startProcess()` including a full command line for manually re-running 
  troublesome commands, and expansion of PATH environment variables to show the individual components. 
- Added a ``processFactory`` argument to `BaseTest.startProcess()` which can be used either to have ``startProcess()`` 
  return a custom process subclass with extra features, or to make modifications to the arguments or environment 
  that were specified by the code that invoked ``startProcess()`` (if you're using some wrapper method that 
  starts a process rather than calling ``startProcess()`` directly). 

Line mapper/text manipulation improvements
------------------------------------------
- Added `pysys.mappers.JoinLines` which combines consecutive related logs such as exception stack traces. There are 
  also pre-configured mappers for some common tools: `pysys.mappers.JoinLines.PythonTraceback`, 
  `pysys.mappers.JoinLines.JavaStackTrace`, `pysys.mappers.JoinLines.AntBuildFailure`. For example::

    self.assertGrep('myserver.log', expr=r' (ERROR|FATAL) .*', contains=False, 
      mappers=[pysys.mappers.JoinLines.JavaStackTrace()], 	
      ignores=['Caused by: java.lang.RuntimeError: My expected exception'])
  
  This will produce a failure outcome that includes the Java stack trace following any error lines, and also 
  has the ability to ignore errors based on the contents of their stack trace. 

- Added `pysys.mappers.SortLines` which could be used with the `BaseTest.copy` method for ensuring deterministic 
  results in a `BaseTest.assertDiff`. 
- Added `pysys.mappers.applyMappers` which makes it easy to add mapper functionality to your own methods. 
- Added a ``mappers=`` argument to `BaseTest.logFileContents` and `BaseTest.assertLineCount`.
- Added a ``startAfter=`` argument to `pysys.mappers.IncludeLinesBetween`, as an alternative to the 
  existing ``startAt=``. 

BaseTest API improvements
-------------------------
The most significant are:

- The unwieldy `BaseTest.getExprFromFile` is superceded (though not actually deprecated) by the simpler functions 
  `BaseTest.grep`, `BaseTest.grepOrNone` and `BaseTest.grepAll` which provide the same capability but with more 
  memorable/understandable names. 
- Added `BaseTest.unpackArchive` to make it easy to store large ``Input/`` assets such as log files compressed 
  (``.xz/.tar.xz`` recommended for efficiency, but several other archive types also supported). The unpacked files 
  are automatically deleted during test cleanup to avoid consuming unnecessary disk space (especially if the test 
  fails). 
- Added `pysys.constants.PREFERRED_ENCODING` which should be used in testcases instead of 
  ``locale.getpreferredencoding()`` to avoid thread-safety issues. 
- Improved usability of the color highlighting and difference marker when `BaseTest.assertThat` or 
  `BaseTest.assertThatGrep` fail, for both primitive values and list/dict values.
- Added `pysys.utils.fileutils.listDirContents` for creating a normalized list of the files/directories contained 
  recursively within a specified directory. This is useful as input for assertions. 
- Changed `pysys.writer.outcomes.JUnitXMLResultsWriter` output to be more standards-compliant: added the ``timestamp`` 
  attribute, and changed the failure node to be::
  
    <failure message="OUTCOME: Outcome reason" type="OUTCOME"/>
    
  (where OUTCOME could be FAILED, BLOCKED, etc.) instead of::

    <failure message="OUTCOME">Outcome reason</failure>

  This may produce better error indicators in CI systems and IDEs that parse these files. 

Additional improvements which will be of use to some users:

- Added `pysys.constants.EXE_SUFFIX` which is ``.exe`` on Windows and empty string on Unix. This is convenient 
  when running executables. 
- Improved the failure messages for `BaseTest.assertGrep` (with ``contains=False``) and `BaseTest.assertLineCount` 
  (with ``condition="==0"``) to include both the first matching expression and the total number of matches. This 
  is useful when checking log files for unexpected errors and warnings. 
- Added `pysys.utils.allocport.excludedTCPPorts` which can be set before the `pysys.baserunner.BaseRunner` is 
  constructed to prevent the specified ports being allocated by `~pysys.basetest.BaseTest.getNextAvailableTCPPort`. 
  By default PySys comes with exclusions for a handful of ports that are commonly blocked by web browsers for security 
  reasons. 
- Added `pysys.utils.allocport.logPortAllocationStats` which can be useful for configuring an appropriately sized 
  pool of TCP ports. 
- Added ``key`` field to `pysys.process.user.STDOUTERR_TUPLE` to make it easier to create log file paths that match 
  a process's stdout/stderr files. 
- Added `pysys.utils.safeeval.safeEval` for cases where you want to evaluate a Python ``eval()`` string from a test 
  plugin, for example ``"expected >= value"``. The string is evaluated in a minimal namespace unpolluted by the 
  current module/test, but including access to standard Python modules such as ``os/sys/math`` and PySys constants. 
- Added ``includeCoverageFromPySysProcess`` option to `pysys.writer.coverage.PythonCoverageWriter` which is useful 
  for measuring code coverage when testing custom PySys plugins. 
- Added ``testobj`` argument to `pysys.utils.perfreporter.CSVPerformanceReporter.getRunDetails` in case you wish 
  to provide different ``runDetails`` based on some feature of the test object or mode. 
- Added `BaseTest.pollWait` which should be used instead of ``time.sleep`` when polling for something to happen 
  without any log messages (or the existing `BaseTest.wait` for longer polls where you do want logging). 
  In a future release this method will be able to abort early if a test run is cancelled. 
- `pysys.process.monitor.BaseProcessMonitor.stop` now waits for the process monitor to terminate before returning, 
  so that during test cleanup the process monitors will always be stopped before any processes are killed, avoiding 
  occasional failures of the process monitoring. 
- Moved the recently introduced ``pysys.writer.testoutput.PythonCoverageWriter`` to 
  its own module `pysys.writer.coverage.PythonCoverageWriter` (without breaking existing configuration files that 
  refer to the old name). 
- Added `BaseTest.deleteFile()` which provides a simple and safe way to delete a file similar to the 
  `BaseTest.deleteDir()` method. 
- Added a ``quiet=True/False`` option to `BaseTest.waitForGrep` to disable the INFO-level logging. 

Fixes
-----
- Fixed methods such as `BaseTest.assertGrep` to treat ``ignores='a string'`` as a list containing that string, 
  rather than as separate expressions containing each letter in the string which could lead to ignoring lines 
  that shoudl not be ignored. 
- Fixed the project property ``defaultEnvirons.ENVVAR`` added in 1.6.0 which did not in fact set the environment 
  variable as described (due to an additional unwanted ``.`` character); now it does. 
- Avoid creating unnecessary runner output directory as a result of ``mkdir(runner.output+'/../xxx')`` by 
  normalizing paths before calling ``mkdir``. 
- Fixed `BaseTest.assertLineCount` bug in which ``reFlags`` parameter was not honored. 
- Fixed numerous Python warnings. 
- Fixed bug in which `pysys.utils.fileutils.toLongPathSafe` and `pysys.utils.fileutils.mkdir` would incorrectly 
  capitalize the first letter when passed a relative path. 
- Improved the formatting of ``pysys print --full`` so it is easier to read. Most items with empty or default values 
  are no longer shown, so you can focus on the information that's actually interesting. 
- Fixed bug in which ``--modes`` argument would not be honored if running tests with ``--ci``. 

Migration notes
---------------

Breaking changes
~~~~~~~~~~~~~~~~

The main changes that might require changes to existing projects/tests are:

- Removal of Python 2 and 3.5 support; the minimum supported Python version is now 3.6. 
- When user-defined ``mappers=`` are used (for example during ``self.copy``; see also `pysys.mappers`), it is now an 
  error for a mapper to strip off the trailing ``\\n`` character at the end of each line, as failure to do so can have 
  unintended consequences on later mappers. This requirement is also more clearly documented. 
- Some mistakes in the ``pysystest.xml`` structure that were previously tolerated will now produce stderr warning 
  messages (such as incorrectly nesting ``<modes>`` inside ``<groups>``) and others will produce a fatal error 
  (for example multiple occurrences of the same element). To find out if any tests need fixing up, just execute 
  ``pysys print``  in your PySys project directory and act on any warning or error messages. 
- The deprecated ``supportMultipleModesPerRun=false`` project property (only used in very old PySys projects) can no 
  longer be used - please change your tests to use the modern modes approach instead. 
- On Windows the ``testDir`` (and the input/output/reference directories) no longer start with the ``\\?\`` 
  long path prefix; instead this can be added for operations where it is needed using 
  `pysys.utils.fileutils.toLongPathSafe` (as the standard PySys methods already do, for example ``self.copy``). 
  Where possible it is recommended to avoid nesting tests and output directories so deeply that long path support is 
  needed. 

The remaining breaking changes are unlikely edge cases or in rarely used APIs that are unlikely to affect many users:

- The ``pysys.xml`` package has been renamed to `pysys.config` to provide a more logical home for test descriptors 
  and project configuration. Aliases exist so nothing should break, however if you have added extra files to the 
  ``pysys/xml/templates`` directory such as customized ``pysys makeproject`` templates these should now be moved to 
  the ``pysys/config/templates`` directory. It is also recommended to find/rename your framework extensions to use the 
  new name as the ``pysys.xml`` module name is deprecated and will be removed in a future 
  release. 
- The deprecated ``pysys.process._stringToUnicode`` method is now removed, since in Python 3 it is a no-op. 
- If you created a custom `pysys.config.descriptor.DescriptorLoader` subclass to manipulate modes, you need to change 
  it to work with `pysys.config.descriptor.TestMode` objects instead of strings, and to set at least one of them 
  to be a primary mode. 
- It is now an error to have multiple ``pysystest.*`` filenames in a single directory, for example ``pysystest.py`` 
  and ``pysystest.xml``. 
- If a test's title ends with ``"goes here TODO"`` then the test will report a ``BLOCKED`` outcome, to encourage 
  test authors to remember to fill it in. This could cause some existing tests to start blocking, though only if 
  you have added a title ending with ``"goes here TODO"``. 
- Removed undocumented internal module ``pysys.utils.loader``; no-one should be using this; if you are, use Python's 
  ``importlib.import_module()`` instead. 
- The ``pysys run --ci`` flag now excludes tests tagged with group ``manual`` (in addition to excluding the 
  ``manual`` test type, since ``pysystest.py`` descriptors use groups for this rather than test type). 
- The ``--json`` output of ``pysys.py print`` now has a dict representing the modes and their parameters 
  for the ``modes`` value instead of a simple list, and the ``xmlDescriptor`` field was renamed to ``descriptorFile``. 
  Also the non-JSON ``pysys print`` output has changed slightly, especially around modes; use ``--json`` instead of 
  parsing the non-JSON output directly . 
- Removed the ``primaryMode`` attribute from `pysys.config.descriptor.TestDescriptor`, as this information is now 
  stored in the `pysys.config.descriptor.TestMode` object. 

Deprecations
~~~~~~~~~~~~

- It is strongly recommended to use the new `pysys.constants.PREFERRED_ENCODING` constant instead of 
  Python's built-in ``locale.getpreferredencoding()`` function, to avoid thread-safety issues in your tests - use of 
  that function within tests should be considered as deprecated. 
- If you have a custom `pysys.utils.perfreporter.CSVPerformanceReporter` subclass, the signatures for
  `pysys.utils.perfreporter.CSVPerformanceReporter.getRunDetails` and
  `pysys.utils.perfreporter.CSVPerformanceReporter.getRunHeader` have changed to include a ``testobj`` parameter.
  Although this should not immediately break existing applications, to avoid future breaking changes you should
  update the signatures of those methods if you override them to accept a ``testobj`` parameter and also any arbitrary
  ``**kwargs`` that may be added in future.
- The ``pysys.xml`` module is deprecated; rename any imports to use `pysys.config` instead. 
- The `pysys.utils.fileunzip` module is deprecated; use `BaseTest.unpackArchive` instead. For example, replace 
  ``unzip(gzfilename, binary=True)`` with ``self.unpackArchive(gzfilename, gzfilename[:-3])``. 
- The (undocumented) ``DEFAULT_DESCRIPTOR`` constant is now deprecated and should not be used. 
- The old ``<mode>`` elements are deprecated in favor of the new Python lambda syntax 
  (support for these won't be removed any time soon, but are discouraged for new tests). 
- The `pysys.utils.pycompat` module is now deprecated; see the documentation inside that module for details on 
  how to upgrade code that is using it.
- The ``ConsoleMakeTestHelper`` class is now deprecated in favor of `pysys.launcher.console_make.DefaultTestMaker`. 

A quick way to check for the removed and deprecated items using a regular expression is shown in the following grep 
command::

	grep -r "\(supportMultipleModesPerRun.*alse\|DescriptorLoader\|pysys.utils.loader\|_stringToUnicode\|pysys[.]xml\|pysys.utils.fileunzip\|[^_@]DEFAULT_DESCRIPTOR\|pysys.utils.pycompat\|PY2\|string_types\|binary_type\|isstring[(]\|quotestring[(]\|openfile[(]\|ConsoleMakeTestHelper\|def getRunDetails\|def getRunHeader\|locale.getpreferredencoding\|addResource\|CommonProcessWrapper\|TEST_TEMPLATE\|DESCRIPTOR_TEMPLATE\|ThreadFilter\)" .

(This expression also contains some removed/deprecated items from the previous 1.6.0 release, though does not attempt to cover 
any earlier releases). 

Optional steps
~~~~~~~~~~~~~~
As the default may change in a future release, existing PySys projects are recommended to explicitly specify what 
directory they wish to use to store test input by specifying one of the following 3 ``<input-dir>`` configurations::

  <pysysproject>
  
    <pysysdirconfig>
      
      <!-- The default for PySys projects created before 2.0 -->
      <input-dir>Input</input-dir> 
      
      <!-- Recommended for new projects - input files are stored in the testDir alongside pysystest.py -->
      <input-dir>.</input-dir> 
      
      <!-- Special option added in PySys 2.0 that auto-detects based on presence of an Input/ dir; useful for getting 
        the new behaviour for new tests without the need to update or potentially create bugs in existing tests
      -->
      <input-dir>!Input_dir_if_present_else_testDir!</input-dir>

    </pysysdirconfig>
  
  </pysysproject>

Many users will prefer to use the new ``pysystest.py`` style for newly created tests alongside older tests using
the ``pysystest.xml`` style. However for anyone who wants to switch entirely to the new style, a utility script for 
automatically converting ``pysystest.xml`` + ``run.py`` tests to ``pysystest.py`` (without losing 
version control history) is provided as part of the cookbook sample 
at https://github.com/pysys-test/sample-cookbook/tree/main/util_scripts/pysystestxml_upgrader.py

By default ``pysys make`` will generate tests with a new-style ``pysystest.py`` file, but if you prefer to keep your 
project using the previous ``pysystest.xml`` and ``run.py`` structure, just add this to your ``pysysdirconfig.xml`` to 
configure ``pysys make`` to use a template that based around ``pysystest.xml`` instead::

  <pysysdirconfig>

    <maker-template name="pysys-xml-test" description="a pre-v2.0 PySys test with pysystest.xml and run.py files" 
      copy="${pysysTemplatesDir}/pysystest-xml-test/*"/>

  </pysysdirconfig>

Some users may wish to run their tests with the ``PYTHONWARNINGS=error`` environment variable or ``-Werror`` command 
line argument, which is prevents use of language features that Python itself has deprecated or which are likely to 
result in test bugs.

-------------------
What's new in 1.6.1
-------------------

PySys 1.6.1 was released in August 2020 and contains fixes for some edge cases regarding allocation of TCP ports 
when running on GitHub(R) Actions:

- Improved detection of the server (non-ephemeral/dynamic) port range on Windows(R) as used by 
  `BaseTest.getNextAvailableTCPPort()`. This was previously incorrect on recent Windows versions leading to 
  potential clashes with ephemeral/dynamic/local ports or an insufficient pool of server ports. In addition, 
  a warning is now logged if a machine is configured with no ports available for starting server processes, 
  and falls back to using the IANA server port range in this case. If you get this warning on Windows you can 
  it by reconfiguring your system (e.g. ``netsh int ipv4 set dynamicportrange tcp ...``) or if that's not possible, 
  by setting the ``PYSYS_PORTS`` environment variable. 
- Fixed a `BaseTest.waitForSocket()` bug on macOS(R) in which the wait never succeeds although the socket is 
  listening. 
- Reduced the ``TIMEOUTS['WaitForAvailableTCPPort']`` constant from 20 minutes to 5 minutes since a properly 
  configured system should not spend significant amounts of time waiting for ports and it is better to 
  know sooner if the port pool is exhausted. 

-------------------
What's new in 1.6.0
-------------------

PySys 1.6.0 was released in August 2020. 

The significant new features of PySys 1.6.0 are grouped around a few themes:

- a new "plugins" concept to encourage a more modular style when sharing functionality between tests; 
- easier validation with the new `BaseTest.assertThatGrep()` method, which extracts a value using a grep 
  expression and then checks its value is as expected. For extract-and-assert use cases this approach gives much 
  clearer messages when the assert fails than using assertGrep; 
- new writers for recording test results, including GitHub(R) Actions support and a writer that produces .zip 
  archives of test output directories, plus new APIs to allow writers to publish artifacts, and to visit each of 
  the test's output files; 
- a library of line mappers for more powerful copy and grep line pre-processing; 
- process starting enhancements such as `BaseTest.waitForBackgroundProcesses()`, automatic logging of stderr when 
  a process fails, and `BaseTest.waitForGrep()` can now abort based on error messages in a different file; 
- several pysys.py and project configuration enhancements that make running and configuring PySys easier. 
- a new "getting started" `sample <https://github.com/pysys-test/sample-getting-started>`_ project which can be 
  easily forked from GitHub(R) to create new PySys-based projects. The sample also demonstrates common techniques 
  and best practices for writing tests in PySys.  

As this is a major release of PySys there are also some changes in this release that may require changes to your 
project configuration file and/or runner/basetest/writer framework extension classes you've written (though in most 
cases it won't be necessary to change individual tests). These breaking changes are either to reduce the chance of 
errors going undetected, or to support bug fixes and implementation simplification. So be sure to look at the upgrade 
guide below if you want to switch an existing project to use the new version. 

New Plugin API
--------------
This release introduces a new concept: test and runner "plugins" which provide shared functionality available for 
use in testcases. 

Existing users will be familiar with the pattern of creating one or more BaseTest framework subclasses to provide a 
convenient place for functionality needed by many tests, such as launching the applications you're testing, or 
starting compilation or deployment tools. This traditional approach of using *inheritance* to share functionality does 
have some merits, but in many projects it can lead to unhelpful complexity because:

a) it's not always clear what functionality is provided by your custom subclasses rather than by PySys itself 
   (which makes it hard to know which documentation to look at)
b) there is no automatic namespacing to prevent custom functionality clashing with methods PySys may add in future
c) sometimes a test needs functionality from more than one base class, and it's easy to get multiple inheritance 
   wrong
d) none of this really lends itself well to third parties implementing and distributing additional PySys 
   capabilities to support additional tools/languages etc

So, in this release we introduce the concept of "plugins" which use *composition* rather than *inheritance* to 
provide a simpler way to share functionality across tests. There are currently 3 kinds of plugin: 

- **test plugins**; instances of test plugins are created for each `BaseTest` that is instantiated, which allows them 
  to operate independently of other tests, starting and stopping processes just like code in the `BaseTest` class 
  would. Test plugins are configured with ``<test-plugin classname="..." alias="..."/>`` and can be any Python 
  class provided it has a method ``setup(self, testobj)`` (and no constructor arguments). 
  As the plugins are instantiated just after the `BaseTest` subclass, you can use them any time after (but not within) 
  your test's `__init__()` constructor (for example, in `BaseTest.setup()`). 

- **runner plugins**; these are instantiated just once per invocation of PySys, by the BaseRunner, 
  before `pysys.baserunner.BaseRunner.setup()` is called. Unlike test plugins, any processes or state they maintain are 
  shared across all tests. These can be used to start servers/VMs that are shared across tests.
  Runner plugins are configured with ``<runner-plugin classname="..." alias="..."/>`` and can be any Python 
  class provided it has a method ``setup(self, runner)`` (and no constructor arguments). 

- **writer plugins**: this kind of plugin has existed in PySys for many releases and are effectively a special kind of 
  runner plugin with extra callbacks to allow them to write test results and/or output files to a variety of 
  destinations. Writers must implement a similar but different interface to other runner plugins; see `pysys.writer` 
  for details. They can be used for everything from writing test outcome to an XML file, to archiving output files, to 
  collecting files from each test output and using them to generate a code coverage report during cleanup at the end 
  of the run. 
  
A test plugin could look like this::

	class MyTestPlugin(object):
		myPluginProperty = 'default value'
		"""
		Example of a plugin configuration property. The value for this plugin instance can be overridden using ``<property .../>``.
		Types such as boolean/list[str]/int/float will be automatically converted from string. 
		"""

		def setup(self, testObj):
			self.owner = self.testObj = testObj
			self.log = logging.getLogger('pysys.myorg.MyRunnerPlugin')
			self.log.info('Created MyTestPlugin instance with myPluginProperty=%s', self.myPluginProperty)

			testObj.addCleanupFunction(self.__myPluginCleanup)

		def __myPluginCleanup(self):
			self.log.info('Cleaning up MyTestPlugin instance')

		# An example of providing a method that can be accessed from each test
		def getPythonVersion(self):
			self.owner.startProcess(sys.executable, arguments=['--version'], stdouterr='MyTestPlugin.pythonVersion')
			return self.owner.waitForGrep('MyTestPlugin.pythonVersion.out', '(?P<output>.+)')['output'].strip()

With configuration like this::

	<pysysproject>
		<test-plugin classname="myorg.testplugin.MyTestPlugin" alias="myalias"/>
	</pysysproject>

... you can now access methods defined by the plugin from your tests using ``self.myalias.getPythonVersion()``. 

You can add any number of test and/or runner plugins to your project, perhaps a mixture of custom plugins specific 
to your application, and third party PySys plugins supporting standard tools and languages. 

In addition to the alias-based lookup, plugins can get a list of the other plugin instances added through the XML 
using ``self.testPlugins`` (from `BaseTest`) or ``self.runnerPlugins`` (from `pysys.baserunner.BaseRunner`), which 
provides a way for plugins to reference each other without depending on the aliases that may be in use in a 
particular project configuration.  

For examples of the project configuration, including how to set plugin-specific properties that will be passed to 
its constructor, see the sample ``pysysproject.xml`` file. 

New and improved result writers
-------------------------------
- Added `pysys.writer.testoutput.TestOutputArchiveWriter` that creates zip archives of each failed test's output directory, 
  producing artifacts that could be uploaded to a CI system or file share to allow the failures to be analysed. 
  Properties are provided to allow detailed control of the maximum number and size of archives generated, and the 
  files to include/exclude. 

- Added `pysys.writer.ci.GitHubActionsCIWriter` which if added to your pysysproject.xml will automatically enable 
  various features when run from GitHub(R) Actions including annotations summarizing failures, grouping/folding of 
  detailed test output, and setting output variables for published artifacts (e.g. performance .csv files, archived 
  test output etc) which can be used to upload the artifacts when present. 
  
  See `https://github.com/pysys-test/sample-getting-started` for an example workflow file you can copy into your 
  own project. 
  
  This uses the new `pysys.writer.api.TestOutcomeSummaryGenerator` mix-in class that can be used when implementing CI 
  writers to get a summary of test outcomes. 

- Added `pysys.writer.api.ArtifactPublisher` interface which can be implemented by writers that support some concept of 
  artifact publishing, for example CI providers that 'upload' artifacts. Artifacts are published by 
  various `pysys.utils.perfreporter.CSVPerformanceReporter` and various writers 
  including `pysys.writer.testoutput.TestOutputArchiveWriter`. 

- Added `pysys.writer.testoutput.CollectTestOutputWriter` which supercedes the ``collect-test-output`` feature, 
  providing a more powerful way to collect files of interest (e.g. performance graphs, code coverage files, etc) from 
  all tests and collate them into a single directory and optionally a .zip archive. 
  This uses the new `pysys.writer.api.TestOutputVisitor` writer interface which can be implemented by writers that wish 
  to visit each (non-zero) file in the test output directory after each test. 
  
  The CollectTestOutputWriter can be used standalone, or as a base class for writers that collect a particular kind 
  of file (e.g. code coverage) and then do something with it during the runner cleanup phase when all tests have 
  completed.  

- Moved Python code coverage generation out to ``pysys.writer.testoutput.PythonCoverageWriter`` (as of 2.0, 
  it's now in `pysys.writer.coverage.PythonCoverageWriter`) as an example of how to use a plugin to add 
  code coverage support without subclassing the runner. Existing projects use this behind the scenes, but new projects 
  should add the writer to their configuration explicitly if they need it (see sample project). 
  
- Added `pysys.writer.console.ConsoleFailureAnnotationsWriter` that prints a single annotation line to stdout for each test 
  failure, for the benefit of IDEs and CI providers that can highlight failures found by regular expression stdout 
  parsing. An instance of this writer is automatically added to every project, and enables itself if 
  the ``PYSYS_CONSOLE_FAILURE_ANNOTATIONS`` environment variable is set, producing make-style console output::
  
    C:\project\test\MyTest_001\pysystest.py:12: error: TIMED OUT - Reason for timed out outcome is general tardiness (MyTest_001 [CYCLE 02])
  
  The format can be customized using the ``PYSYS_CONSOLE_FAILURE_ANNOTATIONS`` environment variable, or alternatively 
  additional instances can be added to the project writers configuration and configured using the properties 
  described in the writer class.

- Added a ``runDetails`` dictionary to `pysys.baserunner.BaseRunner`. This is a dictionary of string metadata about 
  this test run, and is included in performance summary CSV reports and by some writers. The console summary writer 
  logs the runDetails when executing 2 or more tests. 
  
  The default runDetails contains a few standard values (currently these include ``outDirName``, ``hostname``, ``os`` 
  and ``startTime``). Additional items can be added by runner subclasses in the `pysys.baserunner.BaseRunner.setup()` 
  method - for example you could add the build number of your application (perhaps read 
  using `pysys.utils.fileutils.loadProperties()`). 
  
  If you had previously created a custom `pysys.utils.perfreporter.CSVPerformanceReporter.getRunDetails()` method it 
  is recommended to remove it and instead provide the same information in the runner ``runDetails``. 

- Added property ``versionControlGetCommitCommand`` which if set results in the specified command line 
  being executed (in the testRootDir) when the test run starts and used to populate the ``vcsCommit`` key in the 
  runner's ``runDetails`` with a commit/revision number from your version control system. This is a convenient way to 
  ensure writers and performance reports include the version of the application you're testing with. 

There are also some more minor enhancements to the writers:

- The `pysys.writer` module has been split up into separate submodules. However the writers module imports all symbols 
  from the new submodules, so no change is required in your code or projects that reference pysys.writer.XXX classes. 

- Added `pysys.writer.console.ConsoleSummaryResultsWriter` property for ``showTestTitle`` (default=False) as sometimes seeing 
  the titles of tests can be helpful when triaging results. There is also a new ``showTestDir`` which allows the 
  testDir to be displayed in addition to the output dir in cases where the output dir is not located underneath 
  the test dir (due to --outdir). Also changed the defaults for some other properties to 
  showOutcomeReason=True and showOutputDir=True, which are recommended for better visibility into why tests failed. 
  They can be disabled if desired in the project configuration. 

- Added a summary of INSPECT and NOTVERIFIED outcomes at the end of test execution (similar to the existing failures 
  summary), since often these outcomes do require human attention. This can be disabled using the properties on 
  `pysys.writer.console.ConsoleSummaryResultsWriter` if desired. 

- Added `pysys.utils.logutils.stripANSIEscapeCodes()` which can be used to remove ANSI escape codes such as console 
  color instructions from the ``runLogOutput=`` parameter of a custom writer (`pysys.writer.api.BaseResultsWriter`), 
  since usually you wouldn't want these if writing the output to a file. 

More powerful copy and line mapping
-----------------------------------
Manipulating the contents of text files is a very common task in system tests, and this version of PySys has 
several improvements that make this easier: 

- PySys now comes with some predefined mappers for common pre-processing tasks such as selecting multiple lines of 
  interest between two regular expressions, and stripping out timestamps and other regular expressions. 
  
  These can be found in the new `pysys.mappers` module and are particularly useful when using `BaseTest.copy()` to 
  pre-process a file before calling `BaseTest.assertDiff` to compare it to a reference file. For example::
    
     self.assertDiff(self.copy('myfile.txt', 'myfile-processed.txt', mappers=[
              pysys.mappers.IncludeLinesBetween('Error message .*:', stopBefore='^$'),
              pysys.mappers.RegexReplace(pysys.mappers.RegexReplace.DATETIME_REGEX, '<timestamp>'),
         ]), 
         'reference-myfile-processed.txt')
     
  (Note that for convenience we use the fact that copy() returns the destination path to allow passing it directly 
  as the first file for assertDiff to work on). 

- `BaseTest.assertGrep` has a new mappers= argument that can be used to pre-process the lines of a file before 
  grepping using any mapper function. The main use of this is to allow grepping within a range of lines, as defined by 
  the `pysys.mappers.IncludeLinesBetween` mapper::
    
       self.assertGrep('example.log', expr=r'MyClass', mappers=[
            pysys.mappers.IncludeLinesBetween('Error message.* - stack trace is:', stopBefore='^$') ])

  This is more reliable than trying to achieve the same effect with `BaseTest.assertOrderedGrep` (which can give 
  incorrect results if the section markers appear more than once in the file). Therefore, in most cases it's best to 
  avoid assertOrderedGrep() and instead try to use `BaseTest.assertDiff` or `BaseTest.assertGrep`.

- `BaseTest.waitForGrep` and `BaseTest.getExprFromFile` also now support a mappers= argument. 

- When used from `BaseTest.copy` there is also support for line mappers to be notified when starting/finishing a new 
  file, which allows for complex and stateful transformation of file contents based on file types/path if needed. 

- `BaseTest.copy` can now be used to copy directories in addition to individual files. 

  It is recommended to use this method instead of ``shutil.copytree`` as it provides a number of benefits including 
  better error safety, long path support, and the ability to copy over an existing directory.

- `BaseTest.copy` now permits the source and destination to be the same (except for directory copies) which allows it 
  to be used for in-place transformations. 

- `BaseTest.copy` now copies all file attributes including date/time, not just the Unix permissions/mode. 

Assertion improvements
----------------------

- Added `BaseTest.assertThatGrep()` which makes it easier to do the common operation of extracting a value using grep 
  and then performing a validation on it using `BaseTest.assertThat`. 
  
  This is essentially a simplified wrapper around the functionality added in 1.5.1, but avoids the need for slightly 
  complex syntax and hopefully will encourage people to use the extract-then-assert paradigm rather than trying to do 
  them both at the same time with a single `BaseTest.assertGrep` which is less powerful and produces much less 
  informative messages when there's a failure. 
  
  The new method is very easy to use::

        self.assertThatGrep('myserver.log', r'Successfully authenticated user "([^"]*)"', 
            "value == expected", expected='myuser')
        
        # In cases where you need multiple regex groups for matching purpose, name the one containing the value using (?P<value>...)
        self.assertThatGrep('myserver.log', r'Successfully authenticated user "([^"]*)" in (?P<value>[^ ]+) seconds', 
            "0.0 <= float(value) <= 60.0")


- All assertion methods that have the (deprecated and unnecessary) ``filedir`` as their second positional (non-keyword) 
  argument now support the more natural pattern of giving the expr/exprList as the second positional argument, 
  so instead of doing ``self.assertGrep('file', expr='Foo.*')`` you can also now use the more 
  natural ``self.assertGrep('file', 'Foo.*')``. For compatibility with existing testcases, the old signature of 
  ``self.assertGrep('file', 'filedir', [expr=]'expr')`` continues to behave as before, but the recommended usage 
  in new tests is now to avoid all use of filedir as a positional argument for consistency and readability. (If you 
  need to set the filedir, you can use the keyword argument or just add it as a prefix to the ``file`` argument).

Simpler process handling
------------------------

- `BaseTest.startProcess()` now logs the last few lines of stderr before aborting the test when a process fails. This 
  behaviour can be customized with a new ``onError=`` parameter::
  
    # Log stdout instead of stderr
    self.startProcess(..., onError=lambda process: self.logFileContents(process.stdout, tail=True))
    
    # Unless stderr is empty, log it and then use it to extract an error message (which will appear in the outcome reason)
    self.startProcess(..., onError=lambda process: self.logFileContents(process.stderr, tail=True) and self.getExprFromFile(process.stderr, 'Error: (.*)')
    
    # Do nothing on error
    self.startProcess(..., onError=lambda process: None)

- `BaseTest.waitForGrep` has a new optional ``errorIf=`` parameter that accepts a function which can trigger an abort 
  if it detects an error condition (not only in the file being waited on, as ``errorExpr=`` does). For example::
  
    self.waitForGrep('myoutput.txt', expr='My message', encoding='utf-8',
      process=myprocess, errorIf=lambda: self.getExprFromFile('myprocess.log', ' ERROR .*', returnNoneIfMissing=True))

- `BaseTest.waitProcess()` now has a ``checkExitStatus=`` argument that can be used to check the return code of the 
  process for success. 

- Added `BaseTest.waitForBackgroundProcesses()` which waits for completion of all background processes and optionally 
  checks for the expected exit status. This is especially useful when you have a test that needs to execute 
  lots of processes but doesn't care about the order they execute in, since having them all execute concurrently in the 
  background and then calling waitForBackgroundProcesses() will be a lot quicker than executing them serially in the 
  foreground. 

- Added a way to set global defaults for environment variables that will be used by `BaseTest.startProcess()`, using 
  project properties. For example, to set the ``JAVA_TOOL_OPTIONS`` environment variable that Java(R) uses for JVM 
  arguments::
  
    <property name="defaultEnvirons.JAVA_TOOL_OPTIONS" value="-Xmx512M"/>
  
  When you want to set environment variables globally to affect all processes in all tests, this is simpler than 
  providing a custom override of `BaseTest.getDefaultEnvirons()`. 

- `BaseTest.startProcess()` now accepts an ``info={}`` argument which can hold a dictionary of user-defined metadata 
  about the process such as port numbers, log file paths etc. 

pysys.py and project configuration improvements
-----------------------------------------------

- Added environment variable ``PYSYS_DEFAULT_ARGS`` which can be used to specify default arguments that the current 
  user/machine should use with pysys run, to avoid the need to explicitly provide them on the command line 
  each time, for example::
  
    PYSYS_DEFAULT_ARGS=--progress --outdir __pysys_outdir
    pysys.py run

- The sample project file and project defaults introduce a new naming convention of ``__pysys_*`` for output 
  directories and files created by PySys (for example, by writers). This helps avoid outputs getting mixed up with 
  testcase directories and also allows for easier ignore rules for version control systems. 

- Added command line option ``-j`` as an alias for ``--threads`` (to control the number of jobs/threads). The old 
  command line option ``-n`` continues to work, but ``-j`` is the main short name that's documented for it. 
  As an alternative to specifying an absolute number of threads, a multiplier of the number of cores in the machine 
  can be provided e.g. ``-j x1.5``. This could be useful in CI and other automated testing environments.
  Finally, if only one test is selected it will single-threaded regardless of the ``--threads`` argument.

- Added support for including Python log messages for categories other than pysys.* in the PySys test output, 
  using a "python:" prefix on the category name, e.g.::
  
    pysys run -v python:myorg.mycategory=debug

- Added ``pysys run --ci`` option which automatically sets the best defaults for non-interactive execution of PySys 
  to make it easier to run in CI jobs. See ``pysys run --help`` for more information. 

- Added convention of having a ``-XcodeCoverage`` command line option that enables coverage for all supported 
  languages. You may wish to add support for this is you have a plugin providing support for a different language. 

- Added a standard property ``${os}`` to the project file for finer-grained control of platform-specific properties. 
  The new  ``${os}`` property gets its value from Python's ``platform.system().lower()``, and has values such 
  as ``windows``, ``linux``, ``darwin``, etc. For comparison the existing ``${osfamily}`` is always either 
  ``windows`` or ``unix``. 

- Added a standard property ``${outDirName}`` to the project file which is the basename from the ``-outdir``, giving 
  a user-customizable "name" for the current test run that can be used in project property paths to keep test 
  runs separate, for example, this could be used to label performance CSV files from separate test runs with 
  ``--outdir perf_baseline`` and ``--outdir after_perf_improvements``. 

- The standard project property ``testRootDir`` is now defined automatically without the need to 
  add the boilerplate ``<property root="testRootDir"/>`` to your project configuration. The old property name ``root`` 
  continues to be defined for compatibility with older projects. 

- When importing a properties file using ``<property file=... />" there are some new attributes available for 
  controlling how the properties are imported: ``includes=`` and ``excludes=`` allow a regular expression to be 
  specified to control which properties keys in the file will be imported, and ``prefix=`` allows a string prefix to 
  be added onto every imported property, which provides namespacing so you know where each property came from and a 
  way to ensure there is no clash with other properties. 

- Added a handler for notifications from Python's ''warnings'' module so that any warnings are logged to run.log with 
  a stack trace (rather than just in stderr which is hard to track down). There is also a summary WARN log message at 
  the end of the test run if any Python warnings were encountered. There is however no error so users can choose when 
  and whether to deal with the warnings. 
 
- Colored output is disabled if the ``NO_COLOR`` environment variable is set; this is a cross-product standard 
  (https://no-color.org/). The ``PYSYS_COLOR`` variable take precedence if set. 

- Code coverage can now be disabled automatically for tests where it is not wanted (e.g. performance tests) by adding 
  the ``disableCoverage`` group to the ``pysystest.*`` descriptor, or the ``pysysdirconfig.xml`` for a whole 
  directory. This is equivalent to setting the ``self.disableCoverage`` attribute on the base test. 

- `Python code coverage <pysys.writer.coverage.PythonCoverageWriter>` now produces an XML ``coverage.xml`` report 
  in addition to the ``.coverage`` file and HTML report. This is useful for some code coverage UI/aggregation services. 

- The prefix "__" is now used for many files and directories PySys creates, to make it easier to spot which are 
  generated artifacts rather than checked in files. You may want to add ``__pysys_*`` and possibly ``__coverage_*`` 
  to your version control system's ignore patterns so that paths created by the PySys runner and performance/writer 
  log files don't show up in your local changes. 

Miscellaneous test API improvements
-----------------------------------

- Added `pysys.utils.fileutils.loadProperties()` for reading .properties files, and `pysys.utils.fileutils.loadJSON()` 
  for loading .json files. 

- `BaseTest.logFileContents` now has a global variable ``self.logFileContentsDefaultExcludes`` (default ``[]``) which 
  it uses to specify the line exclusion regular expressions if no ``excludes=[...]`` is passed as a parameter. This 
  provides a convenient way to filter out lines that you usually don't care about at a global level (e.g. from a 
  `BaseTest.setup` method shared by all tests), such as unimportant lines logged to stderr during startup of 
  commonly used processes which would otherwise be logged by `BaseTest.startProcess` when a process fails to start. 

- Added `BaseTest.disableLogging()` for cases where you need to pause logging (e.g. while repeatedly polling) to avoid 
  cluttering the run log.  

- Added `pysys.config.project.Project.getProperty()` which is a convenient and safe way to get a project property 
  of bool/int/float/list[str] type. Also added `pysys.baserunner.BaseRunner.getXArg()` which does the same thing for 
  ``-Xkey=value`` arguments.

- `BaseTest.getExprFromFile` now supports ``(?P<groupName>...)`` named regular expression groups, and will return 
  a dictionary containing the matched groups if any are present in the regular expression. For example::

    authInfo = self.getExprFromFile('myserver.log', expr=r'Successfully authenticated user "(?P<username>[^"]*)" in (?P<authSecs>[^ ]+) seconds\.'))

- Added `BaseTest.getOutcomeLocation()` which can be used from custom writers to record the file and line number 
  corresponding to the outcome, if known. 

Bug fixes
---------

- In some cases foreground processes could be left running after timing out; this is now fixed. 

- Ensure ANSI escape codes (e.g. for console coloring) do not appear in JUnit XML writer output files, or in test 
  outcome reasons. 

- Setting the project property ``redirectPrintToLogger`` to any value (including ``false``) was treated as if 
  it had been set to ``true``; this is now fixed. 

Upgrade guide and compatibility
-------------------------------

As this is a major version release of PySys we have taken the opportunity to clean up some aspects which could 
cause new errors or require changes. In many cases it will be necessary to make changes to your project configuration, 
and code changes if you have created custom BaseRunner/BaseTest/writer subclasses - though individual tests will 
generally not require changes, so the total migration effort should be small. 

The changes that everyone should pay attention to are:

- The default values of several project properties have been changed to reflect best practice. 
  
  If you are migrating an existing project we recommend sticking with the current behaviour to start with, by adding 
  the following properties to your project configuration (except for any that you already define ``<property .../>`` 
  overrides for). Then once the PySys upgrade is complete and all tests passing you can switch to some of the new 
  defaults (by removing these properties) if and when convenient. 
  
  The properties you should set to keep the same behaviour as pre-1.6.0 versions of PySys are::
  
    <!-- Whether tests will by default report a failure outcome when a process completes with a non-zero return code. 
        The default value as specified below will be used when the ignoreExitStatus= parameter to the function is not 
        specified. The default was changed to false in PySys 1.6.0. -->
    <property name="defaultIgnoreExitStatus" value="true"/>
    
    <!-- Whether tests will abort as soon as a process or wait operation completes with errors, rather than attempting 
        to limp on. The default value as specified below will be used when the abortOnError parameter to the function 
        is not specified. Default was changed to true in PySys 1.6.0. -->
    <property name="defaultAbortOnError" value="false"/>
    
    <!-- Recommended behaviour is to NOT strip whitespace unless explicitly requested with the stripWhitespace= 
         option; this option exists to keep compatibility for old projects. The default was changed to false 
         in PySys 1.6.0.  -->
    <property name="defaultAssertDiffStripWhitespace" value="true"/>

    <!-- Overrides the default name use to for the runner's ``self.output`` directory (which may be used for things 
        like code coverage reports, temporary files etc). 
        The default was changed to "__pysys_runner.${outDirName}" in PySys 1.6.0. 
        If a relative path is specified, it is relative to the testRootDir, or if an absolute --outdir was specified, 
        relative to that directory. 
    -->
    <property name="pysysRunnerDirName" value="pysys-runner-${outDirName}"/>

    <!-- Overrides the default name use to for the performance summary .csv file. The default was changed to 
        "__pysys_performance/${outDirName}_${hostname}/perf_${startDate}_${startTime}.${outDirName}.csv" in PySys 1.6.0. 
    -->
    <property name="csvPerformanceReporterSummaryFile" value="performance_output/${outDirName}_${hostname}/perf_${startDate}_${startTime}.csv"/>

    <!-- Set this to true unless you used the "mode" feature before it was redesigned in PySys 1.4.1. -->
    <property name="supportMultipleModesPerRun" value="false"/>
    
    <!-- Set temporary directory end var for child processes to the testcase output directory to avoid cluttering up 
        common file locations. Empty string means don't do this. "self.output" is recommended. 
    -->
    <property name="defaultEnvironsTempDir" value=""/>
    
    <!-- Controls whether print() and sys.stdout.write() statements will be automatically converted into logger.info() 
        calls. If redirection is disabled, output from print() statements will not be captured in run.log files and will 
        often not appear in the correct place on the console when running multi-threaded. 
        
        Note that this affects custom writers as well as testcases. If you have a custom writer, use 
        pysys.utils.logutils.stdoutPrint() to write to stdout without any redirection. -->
    <property name="redirectPrintToLogger" value="false"/>
    
    <!-- Produces more informative messages from waitForGrep/Signal. Can be set to false for the terser behaviour if 
         preferred. -->
    <property name="verboseWaitForGrep" value="false"/>

  The list is ordered with the properties most likely to break existing tests at the top of the list, so you may wish 
  to start with the easier ones at the bottom of the list. 
  
- If you have testcases using the non-standard descriptor filenames ``.pysystest`` or ``descriptor.xml`` (rather 
  than the usual ``pysystest.xml``) they will not be found by this version of PySys by default, so action is required 
  to have them execute as normal. If you wish to avoid renaming the files, just set the new project 
  property ``pysysTestDescriptorFileNames`` to a comma-separated list of the names you want to use, 
  e.g. "pysystest.xml, .pysystest, descriptor.xml".

  If you use the non-standard filename ``.pysysproject`` rather than ``pysysproject.xml`` for your project 
  configuration file you will need to rename it. 

- If your BaseTest or BaseRunner makes use of ``-Xkey[=value]`` command line overrides with int/float/bool/list types, you 
  should review your code and/or test thoroughly as there are now automatic conversions from string to int/float/bool/list[str] 
  in some cases where previously the string type would have been retained. 
  a) -Xkey and -Xkey=true/false now consistently produce a boolean True/False 
  (previously -Xkey=true would produce a string ``"true"`` whereas -Xkey would produce a boolean ``True``) and 
  b) -X attributes set on BaseRunner now undergo conversion from string to match the bool/int/float/list type of the 
  default value if a static field of that name already exists on the runner class (which brings BaseRunner into line 
  with the behaviour that BaseTest has had since 1.5.0, and also adds support for the ``list`` type). This applies to 
  the attributes set on the object, but not to the contents of the xargs dictionary. 
  
  The same type conversion applies to any custom `pysys.writer` classes, so if you have a static variable providing a 
  default value, then in this version the variable will be set to the type of that bool/int/float/list rather than to 
  string. 
  
  So, as well as checking your tests still pass you should test that the configuration of your writers 
  and ``pysys.py run -X`` handling is also working as expected. 

- Since `BaseTest.startProcess` now logs stderr/out automatically before aborting, if you previously wrote extensions 
  that manually log stderr/out after process failures (in a try...except/finally block), you may wish to remove them 
  to avoid duplication, or change them to use the new ``onError=`` mechanism. 

- The default directory for performance output is now under ``__pysys_performance/`` rather than 
  ``performance_output/``, so if you have any tooling that picks up these files you will need to redirect it, or set the 
  ``csvPerformanceReporterSummaryFile`` project property described above. The default filename also includes 
  the ``${outDirName}``. See `pysys.utils.perfreporter`. 

Be sure to remove use of the following deprecated items at your earliest convenience:

- Deprecated the ``ThreadFilter`` class. Usually it is not recommended 
  to suppress log output and better alternatives are available, e.g. the quiet=True option for `BaseTest.startProcess`, 
  and the `BaseTest.disableLogging()` method. 
  Please remove uses of ThreadFilter from your code as it will be removed in a future release. 

- The method `pysys.basetest.BaseTest.addResource` is deprecated and will be removed in a future release, so please 
  change tests to stop using it; use `pysys.basetest.BaseTest.addCleanupFunction` instead. 

- The ``pysys.process.commonwrapper.CommonProcessWrapper`` class is now renamed to `pysys.process.Process`. A 
  redirection module exists, so any code that depends on the old location will still work, but please change references 
  to the new name the old one will be removed in a future release. 

- If you need code coverage of a Python application, instead of the built-in python coverage support e.g.::

        <property name="pythonCoverageDir" value="__coverage_python.${outDirName}"/>
        <property name="pythonCoverageArgs" value="--rcfile=${testRootDir}/python_coveragerc"/>
        <collect-test-output pattern=".coverage*" outputDir="${pythonCoverageDir}" outputPattern="@FILENAME@_@TESTID@_@UNIQUE@"/>

  change to using the new writer, e.g.::
  
        <writer classname="pysys.writer.testoutput.PythonCoverageWriter">
            <property name="destDir" value="__coverage_python.${outDirName}"/>
            <property name="pythonCoverageArgs" value="--rcfile=${testRootDir}/python_coveragerc"/>
        </writer>
   
  (if using 2.0+, use `pysys.writer.coverage.PythonCoverageWriter` instead of 
  ``pysys.writer.testoutput.PythonCoverageWriter``. 

Finally there are also some fixes, cleanup, and better error checking that *could* require changes (typically to 
extension/framework classes rather than individual tests) but in most cases will not be noticed. Most users can ignore 
the following list and consult it only if you get new test failures after upgrading PySys:

- Timestamps in process monitor output, writers, performance reporter and similar places are now in local time instead 
  of UTC. 
  This means these timestamps will match up with the times in run.log output which have always been local time. 
- Performance CSV files contain some details about the test run. A couple of these have been renamed: ``time`` is 
  now ``startTime`` and ``outdir`` is now ``outDirName``. The keys and values can be changed as needed using 
  the ``runDetails`` field of `pysys.baserunner.BaseRunner`. It is encouraged to use this rather than the previous 
  mechanism of `pysys.utils.perfreporter.CSVPerformanceReporter.getRunDetails()`.
- Exceptions from cleanup functions will now lead to test failures whereas before they were only logged, so may have 
  easily gone unnoticed. You can disable this using the new "ignoreErrors=True" argument to 
  `BaseTest.addCleanupFunction` if desired. 
- Properties files referenced in the project configuration are now read using UTF-8 encoding if possible, falling back 
  to ISO8859-1 if they contain invalid UTF-8. This follows Java(R) 9+ behaviour and provides for more stable results 
  than the previous PySys behaviour of using whatever the default locale encoding is, which does not conform to any 
  standard for .properties file and makes it impossible to share a .properties file across tests running in different 
  locales. The PySys implementation still does not claim to fully implement the .properties file format, for example 
  ``\`` are treated as literals not escape sequences. See `pysys.utils.fileutils.loadProperties()` for details. 
- Duplicate ``<property name="..." .../>`` project properties now produce an error to avoid unintentional mistakes. 
  However it is still permitted to overwrite project properties from a .properties file. 
  You can also use the new ``includes``/``excludes`` attributes when importing a .properties file to avoid clashes. 
- PySys used to silently ignore project and writer properties that use a missing (or typo'd) property or environment 
  variable, setting it to "" (or the default value if specified). To ensure errors are noticed up-front, it is now a 
  fatal error if a property's value value cannot be resolved - unless a ``default=`` value is provided in which case 
  the default is used (but it would be an error if the default also references a non-existent variable). This is 
  unlikely to cause problems for working projects, however if you have some unused properties with invalid values you 
  may have to remove them. The new behaviour only applies to ``<property name="..." value="..." [default="..."]/>`` 
  elements, it does not apply to properties read from .properties files, which still default to "" if unresolved. 
  Run your tests with ``-vDEBUG`` logging if you need help debugging properties problems. 
- The ``PYSYS_PERMIT_NO_PROJECTFILE`` option is no longer supported - you must now have a pysysproject.xml file for 
  all projects. 
- Writer, performance and code coverage logs now go under ``--outdir`` if an absolute ``--outdir`` path is specified 
  on the command line rather than the usual location under ``testDirRoot/``. 
- On Windows the default output directory is now ``win`` rather than the (somewhat misleading) ``win32``. 
  There is no change to the value of PySys constants such as PLATFORM, just the default output directory. If you 
  prefer a different output directory on your machine you could customize it by setting environment variable 
  ``PYSYS_DEFAULT_ARGS=--outdir __myoutputdir``. 
- If you created a custom subclass of `pysys.utils.perfreporter.CSVPerformanceReporter` using the 1.3.0 release and 
  it does not yet have (and pass through to the superclass) a ``runner`` and/or ``**kwargs`` argument you will need 
  to add these, as an exception will be generated otherwise. 
- Made it an error to change project properties after the project has been loaded. This was never intended, as projects 
  are immutable. In the unlikely event you do this, change to storing user-defined cross-test/global state in your 
  runner class instead. 
- Project properties whose name clashes with one of the pre-defined fields of `pysys.config.project.Project` 
  (e.g. "properties" or "root") will no longer override those fields - which would most likely not work correctly 
  anyway. If you need to get a property whose name clashes with a built-in member, use 
  `pysys.config.project.Project.properties`.
- PySys now checks that its working directory (``os.chdir()``) and environment (``os.environ``) have not been modified 
  during execution of tests (after `pysys.baserunner.BaseRunner.setup()'). Sometimes test authors do this by mistake 
  and it's extremely dangerous as it causes behaviour changes (and potentially file system race conditions) in 
  subsequent tests that can be very hard to debug. 
  The environment and working directory should only be modified for child processes not for PySys itself - 
  calling or overriding `BaseTest.getDefaultEnvirons()` is a good way to do this.   
- Attempting to write to ``runDetails`` or ``pysys.constants.TIMEOUTS`` after `pysys.baserunner.BaseRunner.setup()` 
  has completed (e.g. from individual tests) is no longer permitted in the interests of safety. 
- Changed the implementation of the outcome constants such as `pysys.constants.FAILED` to be an instance of class 
  `pysys.constants.Outcome` rather than an integer. It is unlikely this change will affect existing code (unless you 
  have created any custom outcome types, which is not documented). The use of objects to represent outcomes allows for 
  simpler and more efficient conversion to display name using a ``%s`` format string or ``str()`` without the need for 
  the LOOKUP dictionary (which still works, but is now deprecated). It also allows easier checking if an outcome 
  represents a failure using `pysys.constants.Outcome.isFailure()`. The `pysys.constants.PRECEDENT` constant is 
  deprecated in favor of `pysys.constants.OUTCOMES` which has an identical value.
- There is no longer a default writer so if you choose delete the <writers> element from your project you won't 
  have any writers. 
- Removed undocumented ``TEST_TEMPLATE`` constant from ``pysys.basetest`` and ``DESCRIPTOR_TEMPLATE`` 
  from `pysys.config.descriptor` (they're now constants on `pysys.launcher.console_make.ConsoleMakeTestHelper` if you 
  really need them, but this is unlikely and they are not part of the public PySys API). 
- Removed deprecated and unused constant ``DTD`` from `pysys.config.project` and `pysys.config.descriptor`. 
- Removed deprecated method ``purgeDirectory()`` from `pysys.baserunner.BaseRunner` 
  and `pysys.writer.outcomes.JUnitXMLResultsWriter`. Use `pysys.utils.fileutils.deletedir` instead. 
- Removed deprecated classes ``ThreadedStreamHandler`` and ``ThreadedFileHandler`` from the 
  ``pysys.`` module as there is no reason for PySys to provide these. These are trivial to implement using the 
  Python logging API if anyone does need similar functionality. 
- `pysys.process.user.ProcessUser` no longer sets ``self.output``, and it sets ``self.input`` to the project's 
  testRootDir instead of the current directory. Since these are overridden by `pysys.basetest.BaseTest` and 
  `pysys.baserunner.BaseRunner` it is unlikely this will affect anyone.
- Changed the log messages at the end of a test run to say "THERE WERE NO FAILURES" instead of 
  "THERE WERE NO NON PASSES", and similarly for the "Summary of non passes:". 
- `pysys.process.Process.wait` now raises an error if the specified timeout isn't a positive 
  number (giving the same behaviour as `BaseTest.waitProcess`) rather than the dangerous behaviour of waiting without 
  a timeout. 

---------------
Release History
---------------

PySys 1.5.1 was released in May 2020. 

Documentation improvements:

PySys now uses Sphinx to build its documentation (instead of epydoc), and new content has also been written resulting 
in a significantly larger set of HTML documentation that is also easier to navigate, and brings together 
the detailed API reference with information on usage and how to get started with PySys. The main ``.rst`` 
documentation source files are shipped inside the binary distribution of PySys so that users can view and 
potentially even re-package the documentation combined with their own extensions. 

Assertion and waitForGrep improvements: 

- `BaseTest.assertThat` has been radically overhauled with a powerful mechanism that uses named parameters (e.g. 
  ``actualXXX=`` and ``expected=``) to produce self-describing log messages and outcome reasons, and even the ability to 
  evaluate arbitrary Python expressions in the parameters, for example::
  
     self.assertThat("actualStartupMessage == expected", expected='Started successfully', actualStartupMessage=msg)
     self.assertThat('actualUser == expected', expected='myuser', actualUser=user)

     self.assertThat("actual == expected", actual__eval="myDataStructure['item1'][-1].getId()", expected="foo")
     self.assertThat("actual == expected", actual__eval="myDataStructure['item2'][-1].getId()", expected="bar")
     self.assertThat("actual == expected", actual__eval="myDataStructure['item3'][-1].getId()", expected="baz")

  This automatically produces informative log messages such as::

     Assert that (actual == expected) with actual (myDataStructure['item1'][-1].getId()) ='foo', expected='foo' ... passed
     Assert that (actual == expected) with actual (myDataStructure['item2'][-1].getId()) ='bar', expected='bar' ... passed
     Assert that (actual == expected) with actual (myDataStructure['item3'][-1].getId()) ='baZaar', expected='baz' ... failed
          actual: 'baZaar'
        expected: 'baz'
                    ^

  Note that when two named parameters are provided and the condition string is a simple equality 
  comparison (``==`` or ``is``), additional lines are logged when the assertion fails to show at what point the 
  two arguments differ. For best results make sure you have colours turned on. 

  As a result of these changes to assertThat, the less powerful `BaseTest.assertEval` method is now deprecated and 
  new tests should use assertThat instead. 

  Both methods also now allow the condition/eval string to make use of some additional standard Python modules such as 
  ``math`` and ``re``, and to use ``import_module('...').XXX`` to dynamically import additional modules. 

- `BaseTest.assertGrep` (and `BaseTest.assertLastGrep`) now return the regular expression match object, or if any 
  ``(?P<groupName>...)`` named groups are present in the regular expression, a dictionary containing the matched values. 
  This allows matching values from within the regular expression in a way that produces nicely descriptive error 
  messages, and also enables more sophisticated checking (e.g. by casting numeric types to float). For example::

    self.assertThat('username == expected', expected='myuser',
      **self.assertGrep('myserver.log', expr=r'Successfully authenticated user "(?P<username>[^"]*)"'))
    
    self.assertThat('0 <= float(authSecs) < max', max=MAX_AUTH_TIME,
      **self.assertGrep('myserver.log', expr=r'Successfully authenticated user "[^"]*" in (?P<authSecs>[^ ]+) seconds\.'))
 
  `BaseTest.waitForGrep` now provides the same dictionary return value when given a regular expression with named 
  groups, so the above trick can also be used during execution of the test when convenient. 

- `BaseTest.waitForGrep()` has been added as a new and clearer name for `BaseTest.waitForSignal()`, and we recommend 
  using waitForGrep in new tests from now on (see upgrade section for more information about this change).

- `BaseTest.waitForGrep` (and `BaseTest.waitForSignal`) now logs more useful information if the 
  ``verboseWaitForGrep`` (or its alias, ``verboseWaitForSignal``) is set to true in the ``pysysproject.xml`` 
  properties. This includes logging at the start of waiting rather than at the end of waiting (to make it easier to 
  debug hangs during test development or when triaging an automated test run). In addition, if a non-default timeout 
  was specified this is included in the log message, and for the (small proportion of) waits that take longer than 
  30 seconds an additional message is logged to indicate how long was actually spent, which makes it easier to debug 
  tests that sometimes timeout and sometimes complete just before they would have timed out. All of this new 
  functionality only applies if you have ``verboseWaitForGrep=true`` so will not affect existing projects, but this 
  is now enabled for newly created projects.  

- `BaseTest.waitForGrep` (and `BaseTest.waitForSignal`) now has a ``detailMessage`` parameter that can 
  be used to provide some extra information to explain more about the wait condition. 

- All ``assertXXX`` methods in `BaseTest` now return a value to indicate the result of the assertion. In most 
  cases this is a boolean ``True``/``False``. This creates an opportunity to gather or log additional diagnostic 
  information (e.g. using `BaseTest.logFileContents`) after an assertion fails. 

- Regular expression behaviour can now be customized by a ``reFlags=`` parameter on methods such as 
  `BaseTest.assertGrep`, `BaseTest.waitForGrep`, etc. This allows for ignoring case, and use of verbose regular 
  expression syntax, for example::
  
    self.assertGrep('myserver.log', reFlags=re.VERBOSE | re.IGNORECASE, expr=r\"""
      in\   
      \d +  # the integral part
      \.    # the decimal point
      \d *  # some fractional digits
      \ seconds\. # in verbose regex mode we escape spaces with a slash
      \""")

- `BaseTest.assertDiff` now has colour-coding of the added/removed lines when logging a diff to the console on failure. 

- `BaseTest.assertDiff` usability was improved by including the relative path to each file 
  in the assertion messages, so you can now use the same basename for the file to be compared and the reference 
  file without losing track of which is which. This also makes it easier to manually diff the output directory against 
  the ``Reference`` directory using GUI diff tools when debugging test failures. 

- `BaseTest.assertDiff` has a new advanced feature, *autoUpdateAssertDiffReferences*, to help when you 
  have a large set of test reference files which need to be updated after a behaviour or output formatting change. 
  If you run the tests with ``-XautoUpdateAssertDiffReferences`` any diff failures will result in PySys overwriting 
  the reference file with the contents of the comparison file, providing an easy way to quickly update a large set 
  of references. Use this feature with caution, since it overwrites reference files with no backup. In 
  particular, make sure you have committed all reference files to version control before running the command, and 
  then afterwards be sure to carefully check the resulting diff to make sure the changes were as expected before 
  committing. 

Improvements to the ``pysys.py`` tool: 
- PySys now supports v3.8 of Python. 

- Added ``Test directory`` to ``pysys print --full``. The directory is given as a path relative to the directory 
  PySys was run from. 

New project options:

- The ``pysysproject.xml`` project configuration has a new ``<project-help>...</project-help>`` element which can be 
  used to provide project-specific text to be appended to the ``pysys run --help`` usage message. This could be useful 
  for documenting ``-Xkey=value`` options that are relevant for this project, and general usage information. A 
  ``Project Help`` heading is automatically added if no other heading is present, and PySys will intelligently add or 
  remove indentation from the specified content so that it aligns with the built-in options.

- ``pysysproject.xml`` has a new property ``defaultAssertDiffStripWhitespace`` which controls whether 
  `BaseTest.assertDiff` ignores whitespace (and blank lines at the end of a file). The recommended 
  value is False, but to maintain compatibility with existing projects the default if not specified in the project file 
  is True. 

- The ``<property name=.../>`` and ``<property file=.../>`` elements have a new optional attribute 
  called ``pathMustExist="true/false"`` that can be set to true to indicate that the project should not load (and no 
  tests be run) if the .properties file does not exist, or in the case of ``<property name=.../>``, if the property 
  value does not exist (either as an absolute path or as a path relative to the project root directory). We recommend 
  setting using ``pathMustExist`` on all ``<property file=.../>`` elements to be explicit about whether the file is 
  optional or mandatory. 

- ``<pythonpath>`` can now be used (and is recommended) instead of ``<path>`` to add items to the PYTHONPATH. There is 
  no plan to remove support for ``<path>`` but this should increase clarity for new users. 

Port allocation improvements:

- `BaseTest.getNextAvailableTCPPort` and `BaseTest.waitForSocket` now support IPv6, via the new 
  ``socketAddressFamily`` argument (IPv4 remains the default). It is also possible now to control which host 
  address/interface is used to check that an allocated port isn't in use using the new ``hosts`` argument. 

- A new environment variable ``PYSYS_PORTS=minport-maxport,port,...`` can be used to override the set of possible 
  server ports allocated from `BaseTest.getNextAvailableTCPPort()`. This avoids the usual logic which uses 
  `pysys.utils.portalloc.getEphemeralTCPPortRange()` to detect the local/client-side ports which should be avoided 
  for server-side use. In addition, the default behaviour of getEphemeralTCPPortRange has changed on Linux, so that 
  if ``/proc/sys/net/ipv4/ip_local_port_range`` is missing, PySys will fall back to using the default IANA ephemeral 
  port range (with a warning). This makes it possible to use PySys in environments such as 
  Windows Subsystem for Linux (WSL) v1 which may not have the usual Linux network stack. 

Advanced pysystest.xml additions:

- It is now possible to use ``${...}`` project properties when specifying the Python module to load for a given test, 
  for example::

     <data>
        <class name="PySysTest" module="${testRootDir}/test-utils/custom_run_module.py"/>
     </data>

- User-defined key/value data can be added to ``pysystest.xml`` (and will be inherited from any parent 
  ``pysysdirconfig.xml`` files)::

     <data>
        <user-data name="myThing" value="foobar"/>
     </data>
     
  Any user-defined data is available as a string in the ``userData`` field of `self.descriptor <pysys.config.descriptor.TestDescriptor>`, 
  and each named value will be set as a variable on the `BaseTest` class. If a static (non-instance) variable of the same name 
  exists on the test class at construction then the ``<user-data>`` will override it, but its type will be coerced 
  automatically to an int/float/bool to match the type of the variable. A ``pysys.py run -Xname=value`` argument can be 
  specified to provide a temporary override for any items in the test's user data. Note that there is no 
  automatic substituting of ``${...}`` properties in user data values. 
  
Bug fixes:

- Handling of errors deleting previous test output has been improved. In 1.5.0, there was a usability regression in 
  which a test would fail to run if any part of its output directory could not be deleted due 
  to a shell or tool (e.g. tail) keeping it locked. Now, although error deleting files will still cause the test to 
  fail (since this has a high chance of affecting correctness), directory deletion errors are logged at WARN in the 
  test output but do not cause an error. 

- Fixed bug in which ``BaseTest.assertDiff`` was not logging the diff to the console after a failure. 

- Fixed bug in which a ``pysysdirconfig.xml`` in the same directory as a ``pysysproject.xml`` would be read twice, 
  potentially resulting in duplicated a ``id-prefix``.

- Fixed some bugs in the selection of test ids on the command line. Now we always prefer an exact match over any 
  possible suffix matches, and give an error if there are multiple matching suffixes rather than just picking one.

- Fixed 1.5.0 bug in which a ``-Xkey=value`` command line value of ``1`` or ``0`` would be converted to a boolean 
  True or False value instead of an int, when the `BaseTest` object has a field named ``key`` of type int.

- Fixed reading .properties file values that contain an equals ``=`` symbol. 

- Replace new line characters in test outcome reasons to avoid confusing tools. 

- Changed `BaseTest.getNextAvailableTCPPort` to check the allocated port isn't in use on ``localhost`` (previously 
  we only checked ``INADDR_ANY`` which doesn't include the ``localhost`` interface). 

Upgrade guide and compatibility: 
This is a minor release so is not expected to break existing tests, however we recommend reading the notes 
below and making any 'recommended' changes at a convenient time after upgrading (to avoid problems in future major 
upgrades), and also running your tests with the new version before upgrading to confirm everything still works as 
expected.

- Default project property ``defaultAssertDiffStripWhitespace`` was added. It is recommended to add this to 
  your ``pysysproject.xml`` file set to false, but it is likely some test reference files may need fixing, so the 
  default value is True which maintains pre-1.5.1 behaviour.

- `BaseTest.waitForSignal()` is now just an alias for the newly added `BaseTest.waitForGrep()`, which is the 
  preferred method to use for waiting until a regular expression is found in a file. This is a bit of API cleanup that 
  provides consistency with widely-used `BaseTest.assertGrep()`, and increases clarity for new users who could 
  otherwise be unsure of the meaning of the term "signal". 
  
  The two methods are identical except for a small usability improvement in the method signature to avoid a common 
  mistake in which the (rarely used, and never needed) ``filedir`` was given a prominent position as the second 
  positional argument and therefore sometimes incorrectly given the value intended for the ``expr`` expression to be 
  searched, as can be seen from the two signatures::
  
    def waitForSignal( self, file, filedir, expr='', ... )
    def waitForGrep(   self, file, expr='', ..., filedir=None )
	
  In the new waitForGrep method, ``filedir`` can only be specified as a ``filedir=`` keyword argument, permitting the 
  more natural positional usage::
  
    self.waitForGrep('file', 'expr', ...)
  
  There is no plan to actually remove waitForSignal, however in the interests of consistency we'd recommend doing a 
  find-replace ``self.waitForSignal -> self.waitForGrep`` on your tests at a convenient time, bearing in mind that it 
  could result in test failures in the unlikely event you are setting ``filedir`` and doing so positionally rather 
  than with ``filedir=``.
  
  If you use the ``verboseWaitForSignal`` project property, we recommend you transition to the new 
  ``verboseWaitForGrep`` property, though both work on both methods for now. 

- In `BaseTest.startProcess()`, ``background=True/False`` has been added as an alternative and simpler equivalent of 
  ``state=BACKGROUND``. It is preferred to use ``background=True`` in new tests (although there is no plan to 
  remove ``state`` so it is not mandatory to change existing tests). 

- The global namespace available for use in eval() methods such as `BaseTest.assertThat`, `BaseTest.assertEval`, 
  `BaseTest.assertLineCount` and `BaseTest.waitForGrep` has been cut down to remove some functions and modules 
  (e.g. ``filegrep``) that no-one is likely to be using. If you find you need anything that is no longer available, 
  just use ``import_module('modulename').member`` in your eval string to add it, but it is highly unlikely this will 
  affect anyone as none of the removed symbols were documented. Also `BaseTest.assertEval` is deprecated in 
  favor of `BaseTest.assertThat` which provides more powerful capabilities (note that `BaseTest.assertThat` was itself 
  previously deprecated, but after recent changes is now the preferred way to perform general-purpose assertions). 

- There are some deprecations in this release, to remove some items that no-one is likely to be using from the API. 
  We encourage users to check for and remove any references to the following to be ready for future removal:

   - ``pysys.utils.filecopy`` and its functions ``copyfileobj`` and ``filecopy`` are now deprecated (and hidden from the 
     documentation) as there are functions in Python's standard library module ``shutil`` that do the same thing. 
   - ``pysys.utils.threadpool`` is also deprecated and hidden from the public API as it was never really 
     intended for general purpose use and Python 3 contains similar functionality. 
   - The ``DTD`` constants in `pysys.config.project` and `pysys.config.descriptor`.
   - ``pysys.config.descriptor.XMLDescriptorParser`` (replaced by `pysys.config.descriptor.DescriptorLoader`)
   - ``pysys.config.descriptor.XMLDescriptorContainer`` (replaced by `pysys.config.descriptor.TestDescriptor`)
   - ``pysys.config.descriptor.XMLDescriptorCreator`` and ``DESCRIPTOR_TEMPLATE`` (create descriptors manually if needed) 

1.4.0 to 1.5.0
--------------
PySys 1.5.0 was released in July 2019. 

PySys 1.5.0 brings some significant new features for large PySys projects 
including support for running a test in multiple modes, and 
``pysysdirconfig.xml`` files that allow you to specify defaults that apply to 
all testcases under a particular directory - such as groups, modes, a prefix 
to add to the start of each test id, and a numeric hint to help define the 
execution order of your tests. 

There is also new support for collecting files from each test output 
directory (e.g. code coverage files), new features in the `pysys run` and 
`pysys print` command lines, and a host of small additions to the API to make 
test creation easier e.g. `BaseTest.assertEval`, `BaseTest.copy` (with filtering of each copied 
line) and `BaseTest.write_text` (for easy programmatic creation of files in the output 
directory). 

This is a major release and therefore there are a few significant changes 
that could required changes in existing projects; please review the 
compatibility section of this document and perform an initial test run using 
the new PySys version to check for issues before switching over. 

Miscellaneous new features:

- Added support for running tests in multiple modes from within a single PySys 
  execution. To make use of this, add the following property to your 
  `pysysproject.xml`::
  
	<property name="supportMultipleModesPerRun" value="true"/>

  The old concept of modes within PySys is now deprecated in favor of the 
  more powerful features of `supportMultipleModesPerRun=True` so we recommend 
  all users to add this project setting when possible. Please note though that 
  it will result in slightly different behaviour (e.g. different output 
  directory names) if you have any tests with `<mode>...</mode>` in their 
  descriptor. See the user guide for detailed information about running tests 
  in multiple modes.

- Added a project configuration option that collects a copy of all test output 
  files matching a specified pattern into a single directory. This is useful 
  for collecting together code coverage files from all tests into one place, 
  and could also be used for collating other outputs such as performance or 
  memory usage graphs. Files are copied from the output directory at the 
  end of each test's execution, and before any files are purged. The sample 
  project file shows how to use this feature to collect Python code 
  coverage files::
  
     <property name="pythonCoverageDir" value="__pysys_coverage_python_@OUTDIR@"/>
	 <collect-test-output pattern=".coverage*" outputDir="${pythonCoverageDir}" outputPattern="@FILENAME@_@TESTID@_@UNIQUE@"/>

  The output directory is wiped clean at the start of each test run to prevent 
  unwanted interference between test runs, and is created on demand when the 
  first matching output file is found, so the directory will not be created if 
  there is no matching output. 

- Added support for generating code coverage reports for programs written in 
  Python, using the coverage.py library. To enable this, ensure the coverage 
  library is installed (``pip install coverage``), add collecting of test output 
  files named ``.coverage*`` to a directory stored in the ``pythonCoverageDir`` 
  project property (see above example), and run the tests with 
  ``-X pythonCoverage=true``. You can optionally set a project property 
  ``pythonCoverageArgs`` to pass arguments to the coverage tool, such as which 
  modules/files to include or omit. After all tests have been executed, the 
  runner calls a new method `processCoverageData` which combines all the 
  collected coverage files into a single file and produces an HTML report 
  from it, within the pythonCoverageDir directory. If you wish to produce 
  coverage reports using other tools or languages (such as Java), this 
  should be easy to achieve by following the same pattern - using 
  `<collect-test-output>` to gather the coverage files and providing a 
  custom implementation of `pysys.baserunner.BaseRunner.processCoverageData`.  

- Added `BaseTest.assertEval` method which supersedes `BaseTest.assertThat` and provides 
  a convenient way to assert an arbitrary Python expression, with generation of 
  a clear outcome reason that is easy to understand and debug. 

- Added `BaseTest.copy` method for copying a binary or text file, with 
  optional transformation of the contents by a series of mapping functions. 
  This can be used to extract information of interest from a log file before 
  diff-ing with a reference copy, for example by stripping out timestamps 
  and irrelevant information. 

- Added `BaseTest.write_text` method for writing characters to a text file 
  in the output directory using a single line of Python. 

- Added `expectedExitStatus` parameter to `BaseTest.startProcess()` method 
  which can be used to assert that a command returns a non-zero exit code, 
  for example ``self.startProcess(..., expectedExitStatus='==5')``. 
  This is simpler and more intuitive than setting `ignoreExitStatus=True` and 
  then checking the exit status separately. 

- Added ``quiet`` parameter to `BaseTest.startProcess()` method 
  which disable INFO/WARN level logging (unless a failure outcome is appended), 
  which is useful when calling a process repeatedly to poll for completion of 
  some operation. 

- Added `BaseTest.startPython` method with similar options to `BaseTest.startProcess` 
  that should be used for starting Python processes. Supports functionality 
  such as Python code coverage. 

- Added `BaseTest.disableCoverage` attribute which can be used to globally 
  disable all code coverage (in all languages) for a specific test. For example 
  if you apply a group called 'performance' to all performance tests, you could 
  disable coverage for those tests by adding this line to your BaseTest::
  
  	 if 'performance' in self.descriptor.groups: self.disableCoverage = True

- Added ``hostname``, ``startTime`` and ``startDate`` project properties which can be 
  used in any ``pysysproject.xml`` configuration file. The start time/date 
  gives the UTC time when the test run began, using the yyyy-mm-dd HH.MM.SS 
  format which is suitable for inclusion in file/directory names. 

- Added `BaseTest.getBoolProperty()` helper method which provides a simple way to 
  get a True/False value indicating whether a setting is enabled, either 
  directly using a ``-X prop=value`` argument, or with a property set in the 
  ``pysysproject.xml`` configuration file.

- Added environment variable ``PYSYS_PORTS_FILE`` which if present will be read 
  as a UTF-8/ASCII file with one port number on each line, and used to populate 
  the pool of ports for `BaseTest.getNextAvailableTCPPort()`. This can be used to 
  avoid port conflicts when invoking PySys from an environment where some ports 
  are taken up by other processes. 

- Added ``TIMEOUTS['WaitForAvailableTCPPort']`` which controls how long 
  `BaseTest.getNextAvailableTCPPort()` will wait before throwing an exception. 
  Previously ``getNextAvailableTCPPort()`` would have thrown an exception if 
  other tests were using up all ports from the available pool; the new 
  behaviour is to block and retry until this timeout is reached.
  
Improvements to the XML descriptors that provide information about tests:

- Added support for disabling search for testcases in part of a directory tree 
  by adding a ``.pysysignore`` or ``pysysignore`` file. This is just an empty file 
  that prevents searching inside the directory tree that contains it for tests. 
  This could be useful for reducing time taken to locate testcase and also for 
  avoiding errors if a subdirectory of your PySys project directory contains 
  any non-PySys files with filenames that PySys would normally interpret 
  as a testcase such as ``descriptor.xml``. 

- Added a new XML file called ``pysysdirconfig.xml`` which is similar to 
  ``pysystest.xml`` and allows setting configuration options that affect all 
  tests under the directory containing the ``pysysdirconfig.xml`` file.
   
  This allows setting things like groups, test id prefix, execution order, 
  and skipping of tests for a set of related testcases without needing to 
  add the options to each and every individual ``pysystest.xml`` file. For 
  example, if you have a couple of directories containing performance tests 
  you could add ``pysysdirconfig.xml`` files to each with a 
  ``<group>performance</group>`` element so it's easy to include/exclude all 
  your performance when you invoke ``pysys.py run``. You could also include 
  a ``<execution-order hint="+100"/>`` to specify that performance 
  tests should be run after your other tests(the default order hint is 0.0).
  
  The ``pysysdirconfig.xml`` file can contain any option that's valid in 
  a ``pysystest.xml`` file except the ``description/title/purpose``. a sample 
  ``pysysdirconfig.xml`` file is provided in ``pysys/config/templates/dirconfig``. 
  
  See the PySys User Guide for more information. 

- Added support for specifying a prefix that will be added to start of the 
  testcase directory name to form the testcase identifier. This can be 
  specified in ``pysystest.xml`` testcase descriptor files and/or in 
  directory-level ``pysysdirconfig.xml`` files like this:

    <id-prefix>MyComponent.Performance.</id-prefix>

  Large test projects may benefit from setting prefixes in ``pysysdirconfig.xml`` 
  files to provide automatic namespacing of testcases, ensuring there are no name 
  clashes across different test directories, and providing a way to group 
  together related test ids without the need to use very long names for 
  each individual testcase directory. Prefixes can be specified cumulatively, 
  so with the final testcase id generated from adding the prefix from each 
  parent directory, finishing with the name of the testcase directory itself. 
  
  We recommend using an underscore or dot character for separating test 
  prefixes. 

- Added support for specifying the order in which testcases are run. To do 
  this, specify a floating point value in any ``pysystest.xml`` testcase 
  descriptor, or ``pysysdirconfig.xml`` descriptor (which provides a default for 
  all testcases under that directory)::
  
    <execution-order hint="+100.0"/>

  Tests with a higher ordering hint are executed after tests with lower 
  values. The default order value is 0.0, and values can be positive or 
  negative. Tests with the same order hint are executed based on the 
  sort order of the testcase directories. It is also possible to configure 
  hints at a project level for specific modes or groups. See the user guide 
  for more information. 
  
  You might want to specify a large order hint for long-running performance or 
  robustness tests to ensure they execute after more important unit/correctness 
  tests. You might want to specify a negative hint for individual tests that 
  are known to take a long time (if you're running with multiple threads), to 
  ensure they get an early start and don't hold up the completion of the test 
  run. 

- Added a new way to skip tests, by adding this element to the `pysystest.xml` 
  descriptor::

    <skipped reason="Skipped due to open bug ABC-123"/>

  Although tests can still be skipped by setting the ``state="skipped"`` 
  attribute, the use of the ``skipped`` element is recommended as it provides a 
  way to specify the reason the test has been skipped, and also allows a 
  whole directory of tests to be skipped by adding the element to a 
  ``pysysdirconfig.xml`` file. The default ``pysystest.xml`` template generated 
  for new testcases now contains a commented-out ``skipped`` element instead of 
  a `state=` attribute. 

- Added a new API for overriding the way test descriptors are loaded from a 
  directory on the file system. This allows for programmatic customization 
  of descriptor settings such as the supported modes for each testcase, and 
  also provides a way to make PySys capable of finding and running non-PySys 
  tests (by programmatically creating PySys TestDescriptor objects for them).
  See the `pysys.config.descriptor.DescriptorLoader` class for more details. 

Improvements to the ``pysys.py`` command line tool:

- Added support for running tests by specifying just a (non-numeric) suffix 
  without needing to include the entire id. Although support for specifying a 
  pure numeric suffix (e.g. ``pysys.py run 10``) has been around for a long time, 
  you can now do the same with strings such as ``pysys.py run foo_10``. 

- Added ``--sort`` option to ``pysys.py print``. This allows sorting by ``title`` 
  which is very helpful for displaying related testcases together (especially 
  if the titles are written carefully with common information at the beginning 
  of each one) and therefore for more easily locating testcases of interest. 
  It can also sort by ``id`` or ``executionOrderHint`` which indicates the order 
  in which the testcases will be executed. The default sort order if none of 
  these options is specified continues to be based on the full path of the 
  ``pysystest.xml`` files. 

- Added ``--grep``/``-G`` filtering option to ``pysys.py print`` and ``pysys.py run`` 
  which selects testcases that have the specific regular expression (matched 
  case insensitively) in their ``id`` or ``title``. This can be a convenient way 
  to quickly run a set of tests related to a particular feature area.  

- Added a concise summary of the test ids for any non-passes in a format that's 
  easy to copy and paste into a new command, such as for re-running the failed 
  tests. This can be disabled using the `pysys.writer.console.ConsoleSummaryResultsWriter` property 
  ``showTestIdList`` if desired. 

- Added an environment variable ``PYSYS_DEFAULT_THREADS`` which can be used to set 
  the number of threads to use with ``--threads auto`` is specified on a 
  per-machine or per-user basis. 

- Added the ability to set logging verbosity for specific ``pysys.*`` categories 
  individually using ``-vCAT=LEVEL``. For example to enable just DEBUG logging 
  related to process starting, use ``-vprocess=DEBUG``. Detailed DEBUG logging 
  related to assertions including the processed version of the input files uses 
  the category "assertions" and is no longer included by default when the 
  root log level is specified using ``-vDEBUG`` since it tends to be excessively 
  verbose and slow to generate; if required, it can be enabled using 
  ``-vassertions=DEBUG``.

- Argument parsing now permits mixing of ``-OPTION`` and non-option (e.g. test 
  id) arguments, rather than requiring that the test ids be specified 
  only at the end of the command line. For example::
  
    pysys run --threads auto MyTest_001 -vDEBUG

- Added automatic conversion of strings specified on the command line with 
  ``-Xkey=value`` to int, float or bool if there's a static variable of the 
  same name and one of those types defined on the test `BaseTest` class. This makes it 
  easier to write tests that have their parameters overridden from the command 
  line. For example, if a test class has a static variable ``iterations=1000`` 
  to control how many iterations it performs, it can be run with 
  ``pysys run -Xiterations=10`` during test development to override the number 
  of iterations to a much lower number without any changes to ``run.py``. 
  Note that this doesn't apply to BaseRunner, only BaseTest.
  
- Added ``--json`` output mode to ``pysys.py print`` which dumps full information 
  about the available tests in JSON format suitable for reading in from other 
  programs. 

- Changed ``makeproject`` so that when a template is to be specified, it is now 
  necessary to use an explicit ``--template`` argument, e.g ``--template=NAME``. 

Bug fixes:

- PySys now uses ``Test outcome reason:`` rather than ``Test failure reason:`` 
  to display the outcome, since there is sometimes a reason for non-failure 
  outcomes such as SKIPPED. 

- Fixed ``--purge`` to delete files in nested subdirectories of the output 
  directory not just direct children of the output directory. 

- Previous versions of PySys did not complain if you created multiple tests 
  with the same id (in different parent directories under the same project). 
  This was dangerous as the results would overwrite each other, so in this 
  version PySys checks for this condition and will terminate with an error 
  if it is detected. If you intentionally have multiple tests with the same 
  name in different directories, add an ``<id-prefix>`` element to the 
  ``pysystest.xml`` or (better) to a ``pysysdirconfig.xml`` file to provide 
  separate namespaces for the tests in each directory and avoid colliding ids. 

- The Ant JUnit writer now includes the test duration. 

- Improved `BaseTest.assertGrep` outcome reason to include the entire matching string 
  when a ``contains=False`` test fails since ``ERROR - The bad thing happened`` is 
  a much more useful outcome reason than just ``ERROR``. 

- Fixed CSV performance reporter runDetails which was including each item 
  twice. 

- On Windows, paths within the testcase are now normalized so that the drive 
  letter is always capitalized (e.g. ``C:`` not ``c:``). Previously the 
  capitalization of the drive letter would vary depending on how exactly PySys 
  was launched, which could occasionally lead to inconsistent behaviour if 
  testing an application that relies on the ASCII sort order of paths. 

Upgrade guide and compatibility:

Occasionally it is necessary for a new PySys release to include changes that 
might change or break the behaviour of existing test suites. As 1.5.0 is a 
major release it is possible that some users might need to make changes:

- Errors and typos in ``pysystest.xml`` XML descriptors will now prevent any tests 
  from running, whereas previously they would just be logged. Since an invalid 
  descriptor prevents the associated testcase from reporting a result, the 
  new behaviour ensures such mistakes will be spotted and fixed promptly. 
  If you have any non-PySys files under your PySys project root directory 
  with names such as ``descriptor.xml`` which PySys would normally recognise 
  as testcases, you can avoid errors by adding a ``.pysysignore`` file to prevent 
  PySys looking in that part of the directory tree. 
  
- `BaseTest.mkdir` now returns the absolute path (including the output 
  directory) instead of just the relative path passed in. This make it easier 
  to use in-line while performing operations such as creating a file in the 
  new directory. Code that relied on the old behaviour of returning the 
  path passed in may need to be updated to avoid having the output directory 
  specified twice. If you're using ``os.path.join`` then no change will be 
  required. 

- The ``self.output`` variable in `pysys.baserunner.BaseRunner` is no longer set to the current 
  directory, but instead to a ``pysys-runner-OUTDIR`` subdirectory of the 
  test root (or to ``OUTDIR/pysys-runner`` if ``OUTDIR`` is an absolute path). 
  This ensures that any files created by the runner go into a known location 
  that is isolated from other runs using a different `OUTDIR`. The runner's 
  ``self.output`` directory is often not actually used for anything since 
  most logic that writes output files lives in `BaseTest` subclasses, so 
  most users won't be affected. For the same reason, the runner output 
  directory is not created (or cleaned) automatically. 
  If you have a custom ``BaseRunner`` that writes files to its output directory 
  then you should add a call to ``self.deleteDir <BaseTest.deleteDir>`` and then 
  `self.mkdir <BaseTest.mkdir>` to 
  clean previous output and then create the new output directory.

- The behaviour of `BaseTest.getDefaultEnvirons` has changed compared to 
  PySys 1.4.0, but only when the command being launched is ``sys.executable``, 
  i.e. another instance of the current Python process (``getDefaultEnvirons`` is 
  used by `BaseTest.startProcess` when ``environs=`` is not explicitly provided). 
  
  In 1.4.0 the returned environment always set the ``PYTHONHOME`` environment 
  variable, and on Windows would add a copy of the` `PATH`` environment from the 
  parent process. In PySys 1.5.0 this is no longer the case, as the 1.4.0 
  behaviour was found to cause subtle problems when running from a virtualenv 
  installation or when the child Python itself launches another Python process 
  of a different version. The new behaviour is that `BaseTest.getDefaultEnvirons` adds 
  the directory containing the Python executable to ``PATH`` (on all OSes), and 
  copies the ``LD_LIBRARY_PATH`` from the parent process only on Unix (where it 
  is necessary to reliably load the required libraries). `getDefaultEnvirons` 
  no longer sets the ``PYTHONHOME`` environment variable. 

- The format of ``pysys print`` has changed to use a ``|`` character instead of a 
  colon to separate the test id and titles. This makes it easier to copy and 
  paste test ids from ``pysys print`` into the command line. 

- Several fields in the `pysys.config.descriptor.TestDescriptor` (aka ``XMLDescriptorContainer``) class 
  that used to contain absolute paths now contain paths relative to 
  the newly introduced `testDir` member. These are: `module`, `output`, 
  `input`, `reference`. The values of `BaseTest.output/input/reference` 
  have not changed (these are still absolute paths), so this change is unlikely 
  to affect many users. 

- The ``PROJECT`` variable in the `constants` module is deprecated. Use 
  `self.project` instead (which is defined on classes such as `BaseTest`, 
  `pysys.baserunner.BaseRunner` etc). 


1.3.0 to 1.4.0
--------------
PySys 1.4.0 was released in April 2019. 

Installation:

- The available options for installing PySys have been reworked and modernised. 
  The recommended way to install PySys is by running `pip install PySys`. 

- A binary `.whl` wheel is now available for the first time, which is more 
  efficient, reliable and lightweight than other installation methods, and 
  is used by the pip installer. The `tar.gz` source distribution is still 
  available but is no longer a recommended installation mechanism. The Windows 
  GUI installer is no longer published as this is superseded by the simpler 
  installation experience provided by `pip`. 

- HTML documentation of the PySys API is no longer installed locally by default, 
  but is available on https://pysys-test.github.io/pysys-test website or as a 
  separate zip file available from 
  https://github.com/pysys-test/pysys-test/releases. 

Improvements to the `pysys.py` tool:

- `pysys.py` has a new `makeproject` command that generates a default 
  `pysysproject.xml` with some recommended defaults to make it easy to start a 
  new project without needing to download the samples. 

- As an alternative to the usual `pysys.py` executable script, it is now also 
  possible to launch PySys using::
  
    python -m pysys

- Added new command line option `--printLogs all|failures|none` (default value 
  is `all`) which allows user to avoid the printing of run.log to the stdout 
  console either for all tests, or for tests that pass. This is useful to 
  avoid generating huge amounts of output during large test runs (which can 
  be problematic when stdout is captured by a Continuous Integration system), 
  or to show detailed information only for failing tests which makes it easier 
  for a user to locate the diagnostic information they care about more quickly. 
  The specified value is stored in `runner.printLogs` and can be changed by 
  custom writer implementations if desired, for example to avoid duplicating 
  information already being printed to stdout by the writer in a different 
  format. 

- PySys will now automatically enable colored output if there is no color 
  setting in the `pysysproject.xml` or `PYSYS_COLOR` environment - provided 
  PySys is running in an interactive terminal. On Windows the `colorama` 
  library is now a dependency to ensure colored output is always possible. 

- Added `--threads auto` which is equivalent to `--threads 0` and provides 
  a clearer way to indicate that PySys will automatically determine how many 
  threads to run tests with based on the number of available CPUs. 

- The outcome reason string now has a suffix specifying how many additional 
  failure outcomes were logged (so if you have a complex test you can see at a 
  glance if there's just one problem to resolve, or 5, or 20!).


New project options:

- Added support for running PySys tests under Travis CI(R) to the sample 
  `pysysproject.xml` file. Travis support includes by default only printing 
  `run.log` output for failed tests, and containing that detailed output within 
  a folded section that can be expanded if needed. To enable this just ensure 
  that the Travis CI writer is enabled in your project configuration file, 
  which you can copy from the sample project configuration file if you already 
  have an existing project file. 

- Added support for configuring the default encodings to use for common file 
  patterns in the `pysysproject.xml` configuration, e.g. ::
  
	<default-file-encoding pattern="*.yaml" encoding="utf-8"/>. 

  The sample project configuration file now 
  sets utf-8 as the default encoding for XML, json and yaml files, and also 
  for testcase run.log files (though run.log continues to be written in local 
  encoding unless the project file is updated). For more information on this 
  feature, see comments in `pysysproject.xml` and in 
  `ProcessUser.getDefaultFileEncoding()`.

- Use of ``print()`` rather than ``self.log`` is a common mistake that results in 
  essential diagnostic information showing up on the console but not 
  stored in ``run.log``. A new project option `redirectPrintToLogger` 
  can optionally be enabled to instruct PySys to catch output written using 
  ``print()`` statements or to ``sys.stdout`` and redirect it to the logging 
  framework, so it will show up in ``run.log``. Writers that genuinely need 
  the ability to write directly to stdout should be changed to use 
  `pysys.utils.logutils.stdoutPrint`. 

- There are new settings for customizing the default environment used by 
  `BaseTest.startProcess`::

	<property name="defaultEnvironsDefaultLang" value="en_US.UTF-8"/>
	<property name="defaultEnvironsTempDir" value="self.output'"/>  

  See `BaseTest.getDefaultEnvirons()` for more information on these. 

Main API improvements:

- Added `BaseTest.skipTest()` method, which can be used to avoid running the 
  rest of the `BaseTest.execute()` or `BaseTest.validate()` method, if it is not appropriate for 
  the test to execute on this platform/mode. 

- Added boolean `pysys.constants.IS_WINDOWS` constant, since conditionalizing logic for Windows 
  versus all other Operating Systems is very common; this avoids the need for 
  error-prone matching against string literals. 

- Added `BaseTest.startProcess()` argument `stdouterr` which allows 
  specifying the base prefix to use for writing process standard output and 
  error using a single parameter, either as a string or from a tuple such 
  as that returned from `allocateUniqueStdOutErr()`. As as result there is no 
  longer a need to save the generated stdout and stderr to local variables 
  before passing to startProcess; you can simply specify::
  
    self.startProcess(..., stdouterr=self.allocateUniqueStdOutErr('myprocess'))
  
  Alternatively if you don't care about allocating unique names (perhaps 
  because you have only one instance of the process) a simple string prefix 
  can be specified instead. The final `stdout` and `stderr` paths are available 
  on the returned `ProcessWrapper` object. 
  
  If no displayName is provided, `startProcess` will generate one based on 
  the `stdouterr` prefix so it's easy to identify which process is being 
  started. 

- Added `BaseTest.getDefaultEnvirons()` method which is now used by 
  `BaseTest.startProcess()` to provide a minimal but clean set of environment variables 
  for launching a given process, and can also be used as a basis for creating 
  customized environments using the new `BaseTest.createEnvirons()` helper method. 
  There are some new project properties to control how this works, which 
  you may wish to consider using for new projects, but are not enabled by 
  default in existing projects to maintain compatibility::
  
	<property name="defaultEnvironsDefaultLang" value="en_US.UTF-8"/>
	<property name="defaultEnvironsTempDir" value="self.output'"/>  

  See `BaseTest.getDefaultEnvirons()` for more information on these. 
  If needed you can further customize the environment by overriding 
  `getDefaultEnvirons`. 

- Extended the writers API:
   - Added `runLogOutput=` parameter to the `processResult()` method of 
     the `BaseResultsWriter` class so that writers such as the 
     `JUnitXMLResultsWriter` can include the test output with no loss of unicode 
     character information. 
   - Added `testoutdir=` parameter to the `setup()` method so writers have 
     a way to identify different test runs on the same machine. 
   - Added `runner=` parameter to the `setup()` method so writers have 
     access to the runner instance for reading/modifying configuration 
     settings. 
   - Added `isEnabled()` method that can optionally be used by a writer to 
     disable itself based on the environment in which it is running, or 
     to enable itself even when `--record` isn't specified, which is useful 
     for writers that produce output for a CI system. 

- Rewrote the process monitoring API to make it easier to add extra monitoring 
  statistics (by subclassing the OS-specific `DEFAULT_PROCESS_MONITOR` or the 
  superclass `BaseProcessMonitor`, or to add a custom handler for the 
  generated statistics, by subclassing `BaseProcessMonitorHandler`. 

- Added `BaseTest.startBackgroundThread` method which takes care of ensuring 
  threads are stopped and joined during cleanup, that exceptions from threads 
  result in BLOCKED outcomes and that logging output from background threads 
  goes to the same handlers as foreground logging. The thread target can 
  be either a simple function or an instance method (e.g. on the testcase). 
  A Python `threading.Event` object called `stopped` is passed to the 
  background thread to make it easy to determine when it should finish 
  executing. The `ProcessUser.addOutcome()` method is now thread-safe 
  (though most of the `ProcessUser` and `BaseTest` should still not be accessed 
  from multiple threads without locking). 

- Added `BaseTest.pythonDocTest()` method for executing the doctests in a 
  Python file. 

Minor API additions:

- Added `PerformanceUnit.NANO_SECONDS` (with alias `ns`) which is now 
  recommended when measuring the peformance of operations that take less than a 
  second. 

- Added `__str__` implementations for BaseTest and BaseRunner, which uniquely 
  identify the test (and cycle, in multi-cycle runs). This may be useful for 
  diagnostic and logging purposes. 

- Performance reporter classes can now make use of `self.runner` to access 
  information such as the mode in which the test is running for reporting 
  purposes. 

- Added `BaseTest.assertPathExists` for checking that a file exists (or not). 

- The default implementation of `BaseTest.getDefaultFileEncoding()` now 
  delegates to the runner's implementation, allowing customizations to be 
  performed in just one place if neede for both `BaseTest` and runner class.

- Added `BaseTest.compareVersions()` static helper method for 
  comparing two alphanumeric dotted version strings. 

- Added `BaseTest.deletedir` which is more convenient that the associated 
  `fileutils.deletedir` for paths under the `self.output` directory. 

- Added `BaseTest.addOutcome(override=...)` argument which can be used to 
  specify a new test outcome that replaces any existing outcomes even if 
  they have a higher precedence. 

- Added `ignores=` argument to `BaseTest.waitForSignal()` method which 
  excludes lines matching the specified expression from matching both the 
  main `expr` match expression and any `errorExpr` expressions. 

- Added `pysys.utils.fileutils.toLongPathSafe/fromLongPathSafe` which on Windows performs 
  the necessary magic to allow Python to access paths longer than 256 
  characters (and on other platforms are a no-op), and `pathexists` which 
  is a long path-safe version of `os.path.exists`. PySys will now handle long 
  paths in the most critical places, such as `deletedir`, `logFileContents`, 
  `openfile`, `assertPathExists`, when enumerating available tests, and during 
  test cleanup. Test authors can make use of `toLongPathSafe` as needed in 
  their own test cases. 

- Added `pysys.utils.logutils.stdoutPrint` for writers that genuinely need 
  the ability to write directly to stdout without using a logger. 
  

Upgrade guide and compatibility:

It is pretty rare for a new PySys release to include changes that might change 
or break the behaviour of existing test suites, but occasionally it is 
necessary in order to fix bugs or allow us to provide new functionality. In 
this release there are a few such changes:

- In the previous release unknown or invalid keyword arguments passed to 
  assert* methods would be silently ignored (potentially masking mistakes); 
  now it is an error to specify an invalid argument.  

- The environment `BaseTest.startProcess` uses by default if no `environs=` 
  parameter was specified has changed. Although the documentation states that 
  a clean environment is used if no `environs` dictionary is specified, in 
  PySys v1.1, 1.2 and 1.3 the Windows behaviour changed to include a copy of 
  all environment variables in the parent PySys process (typically a very 
  large set of variables), which could cause tests to unintentionally 
  be affected by the environment it was run from. This is now fixed, so that 
  a small minimal set of environment variables are always returned, as returned 
  by the new `ProcessUser.getDefaultEnvirons()` method. As a result on Windows 
  a much smaller set of environment variables and PATH/LD_LIBRARY_PATH 
  components will be used, and on Unix instead of a completely empty 
  environment, a few variables will now be set. If this causes problems you can 
  temporarily go back to the legacy behaviour by setting this 
  `pysysproject.xml` option::
  
     <property name="defaultEnvironsLegacyMode" value="true"/>

  See https://github.com/pysys-test/pysys-test/issues/9 for more information. 

- The default process monitor file format has changed in this release to 
  provide consistency across all operating systems, and because the 
  Windows-specific statistics private/thread/handle count were not correct and 
  cannot easily be obtained in a robust way. If you need these, or wish to 
  use a wider set of monitoring statistics than PySys provides in the box, it 
  is easy to create a custom `BaseProcessMonitor` subclass, perhaps using a 
  cross-platform Python library such as `psutil` to gather the data. 
  
  Previously there was no header line, and on Windows the columns were::
  
     dd/mm/yy HH:MM:SS, CPU, Resident, Virtual, Private, Threads, Handles
  
  and on Linux::

     mm/dd/yy HH:MM:SS, CPU, Resident, Virtual
  
  In this release there is a header line comment at the start of the file 
  beginning with `#` indicating the column headings. Also a standard date 
  format is used, and only the columns supported on all operating systems are 
  included::
  
     yyyy-mm-dd HH:MM:SS, CPU, Resident, Virtual
  
  This behaviour can be customized for all your testcases from your runner's 
  `setup` method. For example to go back to the previous file format (although 
  without the Windows-specific columns, which are no longer supported), add::
  
    ProcessMonitorTextFileHandler.setDefaults(
        [
           ProcessMonitorKey.DATE_TIME_LEGACY, 
           ProcessMonitorKey.CPU_CORE_UTILIZATION, 
           ProcessMonitorKey.MEMORY_RESIDENT_KB,
           ProcessMonitorKey.MEMORY_VIRTUAL_KB,
        ], writeHeaderLine=False)

  Also note that the numProcessors keyword argument to `startProcessMonitor` is 
  deprecated. For now it can still be used to scale down the 
  `CPU_CORE_UTILIZATION` value but it is not recommended for use and may be 
  removed in a future release. Use `CPU_TOTAL_UTILIZATION` if you wish to see 
  total CPU usage across all cores. 
  
  In the previous release, the Linux process monitor also gathered data 
  from child processes (that were running at the moment the monitor was 
  started). As this functionality was Linux-specific, not documented, and 
  generated incorrect results this has been removed. Optional support for 
  monitoring child processes may be re-added in a future PySys release. 
  Although child process are not included in the statistics for each process, 
  the contributions from its child threads are included. 

- If you have created a custom subclass of `ProcessMonitor` you will need to 
  rework it, as this class no longer exists and the API has been rewritten in 
  order to make it easier to maintain and extend. 
  For example it is now easier to add extra monitoring statistics (by 
  subclassing `BaseProcessMonitor`), or provide custom handlers for the data 
  for different file formats or automated checking of results (by subclassing 
  `BaseProcessMonitorHandler`; no longer requires subclassing the process 
  monitor itself). If you have written a custom subclass of ProcessMonitor 
  to customize what data is gathered you will need to rework it when moving to 
  this version of PySys. If you need to provide custom code to handle the 
  generated statistics, you can now do that by passing a 
  `BaseProcessMonitorHandler` subclass to `BaseTest.startProcessMonitor`. 

- Fixed bug in which symbols (classes, constants, imports) defined in one 
  `run.py` could be seen by other run.py files, potentially causing test 
  behaviour to vary based on what other tests had previously run, and/or 
  race conditions seen only during parallel execution. Now every `run.py` file 
  has its own independent namespace. It is possible some previously passing 
  tests might fail as a result of this change, if they were relying on 
  the buggy behaviour to implicitly import symbols. 

- Although most real PySys projects had a `pysysproject.xml` file in the root 
  directory specifying the configuration, PySys v1.3.0 and earlier treated 
  this file as optional, resulting in confusing error messages, and 
  long and sometimes disruptive searching of non-test directories if a user 
  tried to run PySys from a non-test directory (e.g. from `c:`). To avoid 
  user confusion, by default PySys will now terminate with an error if you 
  try to run it from a directory which doesn't have a project file. Any users 
  who found the ability to use it without a project file useful can enable 
  it by setting the `PYSYS_PERMIT_NO_PROJECTFILE=true` environment variable. 

- Removed `pysys.utils.smtpserver` which was never used by any part of PySys,  
  does not really belong in this project, and adds little over Python's 
  built-in `smtpd` module.

- Removed `DEFAULT_STYLESHEET` `pysys-log.xsl` as referenced in 
  `XMLResultsWriter`, as it does not work in most modern browsers 
  (e.g. Chrome, Firefox) for security reasons and is not widely used. If you 
  need this functionality, the ability to specify a custom .xsl stylesheet for 
  the `XMLResultsWriter` is still available as a configuration option in 
  `pysysproject.xml`. 

- Any custom performance reporter classes created using PySys 1.3.0 
  and which provided a custom constructor should be updated to include the 
  `**kwargs` parameter added in this version of PySys, as the old constructor 
  signature is now deprecated. As this API was added in 1.3.0 no other versions 
  are affected. 


Bug fixes:

- Fixed bug in which random log lines might not be written to `run.log` and/or 
  stdout when running tests multi-threaded (as a result of an underlying 
  python bug https://bugs.python.org/issue35185).

- Fixed bug in which symbols (classes, constants, imports) defined in one 
  `run.py` could be seen by other run.py files, potentially causing test 
  behaviour to vary based on what other tests had previously run, and/or 
  race conditions seen only during parallel execution. Now every `run.py` file 
  has its own independent namespace. It is possible some previously passing 
  tests might fail as a result of this change, if they were relying on 
  the buggy behaviour to implicitly import symbols. 

- Fixed `startProcess()` to use a clean and minimal set of environment 
  variables on Windows if no `environs=` parameter was specified, rather than 
  copying all environment variables from the parent PySys process to the child 
  process. See https://github.com/pysys-test/pysys-test/issues/9 for more 
  information. 
  
- Fixed `startProcess()` to add a `BLOCKED` test outcome when a process fails 
  to start due to a `ProcessError`, unless `ignoreExitStatus=True`. Previously 
  this flag only affected non-zero exit codes, resulting in `ProcessError` 
  failures getting ignored. 

- Fixed `startProcess()` to correctly handle passing empty arguments, 
  and arguments containing spaces, quotes and glob characters on Windows. 
  Previously, empty arguments were skipped, and arguments containing spaces 
  were only handled correctly if first character was not a space. 

- Fixed a number of errors in the statistics reported by process monitors, 
  especially on Windows where negative values were sometimes returned 
  (due to integer overflow), incorrect (and very time-consuming) aggregation 
  based on the child threads that existed at the time the process monitor was 
  first started, lack of support for non-English Windows installations 
  (which have localized counter names) and that the statistics might be 
  returned for the wrong process due to the way the performance counter API 
  changes which process is being monitored when processes of the same name 
  terminate. 
  On Linux the statistics were sometimes wrong due to undocumented and 
  in some cases incorrect aggregation across child processes, which has now 
  been removed. The values are now correct on all operating systems. 

- Fix bug in which non-ASCII characters in test outcome reasons could 
  prevent the test log being written to disk if executed in multi-threaded 
  mode. Only affects Python 2. 
  
- Significant improvements to robustness when testing support for international 
  (I18N) characters. This includes implementing fully safe logging of unicode 
  strings (with `?` replacements for any unsupported characters) that works 
  regardless of what encoding is in use for stdout and `run.log`. Also fixed 
  exception when logging unicode characters in Python 2 if a formatter was not 
  configured in `pysysproject.xml`, by ensuring it is always stored as a 
  unicode character string not a byte string (which used to happen in Python 2 
  if it was not mentioned in the project config). Fixed `logFileContents` to 
  more robustly handle files containing I18N/non-ASCII characters. 

- `JUnitXMLResultsWriter` and `XMLResultsWriter` now write using UTF-8 
  encoding rather than local/default encoding, and also include the 
  `encoding="utf-8"` header in the XML header. Since previously there was no
  `encoding` header many tools would have interpreted them as UTF-8 already, 
  and now the behaviour is consistent with that expectation. 

- Added `pysys.writers.replaceIllegalXMLCharacters()` utility function, and use 
  it to avoid `XMLResultsWriter` and `JUnitXMLResultsWriter` from generating 
  invalid XML if `run.log` or outcome reason contain characters not permitted 
  by XML. Also ASCII control characters (e.g. coloring instructions 
  from other tools) are now stripped out of all outcome reason strings 
  (including in run.log and non-XML based writers) since such characters 
  are not useful and make summary test results harder to read. 

- Fixed rare condition in which performance result reporting would be prevented 
  due to spurious error about `resultKey` already being used. 

  
1.2.0 to 1.3.0
--------------
Changes affecting compatibility:

- Fixed `BaseTest.assertDiff` (and filediff) handling of "include" expressions 
  list to filter out lines if no include expressions match (as documented) 
  rather than if any include expressions match. This fix may cause tests to fail 
  that had previously - and incorrectly - passed as a result of all lines 
  being filtered out before the comparison. There is also now a message 
  logged at warn level when every line in a file comparison is filtered 
  out, since in most cases this is not desirable behaviour. 
- Changed `pysys.py run` to return a non-zero exit code if any tests 
  failed, whereas previously it would return 0.
 
Other fixes and new features:

- PySys now provides 'single-source' support for both Python 2.7 and 
  Python 3.x, without the need for the 2to3.py script to be run at 
  installation time for use with Python 3.
- Added support for specifying what file encoding is to be used for reading 
  and writing text files (for example in `waitForSignal` and various 
  assertions). This is especially important for Python 3 where text files 
  are processed using unicode character strings rather than Python 2 
  byte "str" objects. The encoding can be specified explicitly on 
  individual methods the open files, or globally based on file names 
  or extensions by overriding the new `ProcessUser.getDefaultFileEncoding()` 
  method. For example, `getDefaultFileEncoding` could be overridden to 
  specify that .xml files should be treated as UTF-8 by default. If 
  the encoding is not specified explicitly or through 
  `getDefaultFileEncoding()`, Python selects the preferred encoding based 
  on the locale that it is running in. 
- Changed the way multiple cycles are executed in multi-threaded mode to 
  allow tests from different cycles to execute in parallel instead of waiting 
  for each cycle to fully complete before starting the next cycle. This 
  improved parallelism makes it much easier to reproduce race 
  conditions demonstrated by a single testcase, which was not possible 
  with the previous threading behaviour. To maintain existing 
  behaviour for users who have provided a `runner.cycleComplete()` method, 
  concurrent cycle execution will be disabled if `cycleComplete()` is overridden. 
  Anybody affected by this is encouraged to transition away from use of 
  `cycleComplete()` and perform any required cleanup tasks in 
  `BaseTest.cleanup()` or `BaseRunner.testComplete()` instead. 
- Added `<requires-python>` and `<requires-pysys>` elements to the project XML 
  file which allow checking for the specified minimum python or pysys 
  version, resulting in a clear error if attempting to use the wrong 
  version. 
- Added support for coloring console output to highlight passes, fails, 
  warnings and more. This is configured in the project configuration file. 
  Coloring can also be enabled or disabled for a particular user and/or 
  machine using the `PYSYS_COLOR=true/false` environment variable override. 
  Coloring works on any terminal that supports ANSI escape sequences (e.g. 
  most Unix terminals). On Windows, which does not, it is possible to get 
  colored output by installing a package such as "colorama", which PySys will 
  load if it is present on the python path. It is possible to customize the 
  colors used or to use alternative libraries for coloring on windows by 
  providing a custom ColorLogFormatter class. The colors used for each 
  category of log messages can be customized in the project configuration 
  file, e.g. ::

  <formatter><property name="color:timed out" value="MAGENTA"/></formatter>

- Added `ProcessUser.getExprFromFile` helper method to automate the common task 
  of retrieving some text from a file, for example to capture information 
  such as a process identifier from a log file, or to extract some 
  performance results that were logged. 
- Added `BaseTest.reportPerformanceResult()` and a flexible framework for 
  recording performance results (e.g. throughput, latency etc) measured 
  by PySys tests, including storage of results in a human-readable and 
  machine-parsable CSV file together with run-specific information 
  such as the host where the test was executed. The CSV files can be 
  aggregated across multiple test runs and/or cycles and imported into 
  any spreadsheet for comparisons and more detailed analysis. The standard 
  CSVPerformanceReporter can be subclassed and replaced with an alternative 
  recording mechanism if desired (e.g. writing directly to a database or 
  other file format). Fibonacci_test_005 demonstrates how performance 
  results can be reported using this framework. 
- Added support for providing a custom class to implement formatting of 
  log messages, for both run.log and stdout. Errors in the `<formatters>` XML 
  node will now be treated as errors rather than being silently ignored. 
- Changed pysys.py to ignore trailing slash characters on test ids, which 
  makes it easier to use shell tab completion to select a specific test. 
- Fixed pysys.py command line parser to give a clear error if requested to 
  execute a non-existent test id, or if the test descriptor XML could 
  not be parsed. Previously invalid test ids would be either silently 
  ignored without an error, or would result in other test ids being 
  executed more than once. 
- Fixed `ProcessUser.startProcess` to use the test output directory (rather 
  than the current working directory) as the root when a relative path is 
  specified for the workingDir argument. 
- Fixed bug in which log level and exception tracebacks were being 
  inadvertently suppressed from the stdout console output when executing 
  from multiple threads. 
- Fixed manual tester thread to report a BLOCKED outcome instead of hanging 
  if a fatal error occurs (e.g. Tck does not load due to DISPLAY not being 
  configured correctly). 
- Added `BaseResultsWriter` class and associated docstring documentation to 
  make it easier to create new results writers. 
- Changed standard record writers to report the number of cycles starting 
  from 1 rather than from 0 (which is consistent with how cycles are 
  displayed by the rest of PySys).
- Extended the concept of "writers" to include not just "record" writers 
  (which are enabled only when `--record` is specified) but also "summary" 
  writers which are always enabled and log a summary at the end of test 
  execution (if none is explicitly configured a default 
  `ConsoleSummaryResultsWriter` is instantiated), and "progress" writers 
  which are enabled only when `--progress` is specified and log progress 
  information throughout a run. 
- The monolithic logic for writing a summary to the console at the end of 
  test execution has been refactored out of baserunner and into 
  the configurable and separately extendable `ConsoleSummaryResultsWriter` class. 
  Any baserunner subclasses that are currently overriding the summary printing 
  functionality and/or making use of the results dictionary returned by 
  `start()` should now switch to using "summary" writers instead. This 
  functionality will be removed in a future release and is now deprecated.
- The default summary results writer now has a configuration parameter 
  `showOutcomeReason` which causes the outcome reason string to be included 
  underneath each failure outcome, to provide a quick summary of what went 
  wrong. 
- The default summary results writer now has a configuration parameter 
  `showOutputDir` which causes the path to the test's output directory 
  to be printed underneath each failure outcome, to make it easy to quickly 
  find and open the relevant files to debug the failure. 
- Added a `--progress` command line option (can also be switched on using 
  the `PYSYS_PROGRESS=true` environment variable), which logs a summary of 
  how many test have executed, outcomes, a list of most recent failure 
  reasons and a list of what other tests are currently executing. This 
  provides very helpful feedback to the user while executing a long 
  test run. The progress reporting is implemented in a fully extensible 
  way using a new kind of 'progress' result writer. A custom progress 
  result writer class can be configured for a project; if none is 
  specified the default `ConsoleProgressResultsWriter` is added automatically. 
- Fixed unexpected DEBUG logging on standard output after any of the 
  Python `logging.info/warn/error()` methods is called. This behaviour was 
  triggered if certain libraries (e.g SSL libraries) were not available 
  when python starts. 
- Added `defaultIgnoreExitStatus` project property which controls whether 
  non-zero return codes from `startProcess()` result in test failures, when the 
  `ignoreExitStatus` flag is not explicitly specified. To retain the same 
  behaviour for existing projects, `defaultIgnoreExitStatus` is set to True if 
  the property is not configured in the project configuration. However to 
  promote best practice for new PySys projects, the example pysys project 
  configuration file sets `defaultIgnoreExitStatus` to False, which ensures 
  that processes that return failure codes are not ignored unless explicitly 
  intended by the author of the testcase. 
- Fixed `waitForSocket`, which in previous versions immediately returned 
  success instead of waiting a valid socket connection as documented. 
- If the test run is interrupted from the keyboard, the prompt that asks 
  whether to continue to run tests is no longer displayed if there are no more 
  tests left to run. The prompt can also be completely disabled using an 
  environment variable `PYSYS_DISABLE_KBRD_INTERRUPT_PROMPT=true`, for users who 
  prefer Ctrl+C to immediately terminate the test run in all cases. 
- Added `pysys.utils.pycompat` module containing a small set of helpers for 
  writing code that works with Python 2 and Python 3. 
- Fixed writing to process stdin so that if a character string is passed in it 
  will be converted to a byte object automatically, using the default 
  encoding. Previously, it was not possible to write character strings in 
  Python 3, and in Python 2 it would only work if they contained only ascii 
  characters. 

1.1.1 to 1.2.0
--------------
- Added the errorExpr argument to the waitForSignal method. Occurrence of any
  matches to expressions in this argument will terminate the waitForSignal
  loop, allowing early exit prior to the timeout.
- Refactored reconfiguration of global logging out of the pysys __init__.py
  class into the pysys.py launcher. This allows other applications making
  use of the PySys framework to make their own logging decisions.
- Improved usability of the assertDiff method by writing out the unified
  diff to a file in the output subdirectory so failures are easier to triage.
- Added the literal argument to the assertGrep method to avoid having to
  escape regular expressions.
- Added the utils.fileutils module for miscellaneous file related utilities.


1.1.0 to 1.1.1
--------------
- The validateOnly option has been added to the pysys.py run launcher
  task. When set the purge output subdirectory, setup and execute methods
  on the test will not be invoked. This makes it easier to fix validation
  errors in the test without the need to re-run the entire test.
- The logFileContents() method has been added to the pysys.basetest.BaseTest
  class to allow logging of file contents to the run.log. This can be used
  to provide additional diagnostic information to the run.log to assist
  the triage of test failures.
- The CSVResultsWriter has been added to the set of test summary writers.
  See the sample pysysproject.xml file for more details.
- It is now possible to specify a regex for matching in the test selection.
  See the run usage for more details (pysys.py run -h).


0.9.3 to 1.1.0
--------------
- This release introduces optional fail fast semantics at a macro and micro
  level. At a macro level this is either through the "defaultAbortOnError"
  project property, or through the "-b|--abort" option to the pysys launcher
  run task. See the sample pysysproject.xml, and the run task
  help usage respectively for more details. At a micro level, all assert and
  process related methods now take an optional "abortOnError" parameter to
  override any macro setting. When enabled any error will cause the test to
  immediately fail, reporting the failure reason.
- Outcomes which are considered a fail now log information as to the cause
  of the failure. Additionally a call record is reported, giving a comma
  separated list of "module:lineno" entries detailing the call stack up to
  the test class instance. This is to aid diagnosing test failure causes.
- The test title is now output to console when running the test.
- The BaseRunner class now contains an isPurgableFile() method. This method
  can be overridden by any extensions to denote if a zero length file should
  be purged from the output subdirectory after running of the test.
- It is now possible to register cleanup functions in the BaseTest to negate
  the need to override the cleanup() action where a call to
  BaseTest.cleanup(self) must specifically be made. See the epydoc for the
  addCleanupFunction() in the ProcessUser module.

0.9.2 to 0.9.3
--------------
- Added Darwin as a supported platform.
- Added the maker tag to the pysysproject file to allow specifying a
  custom test maker class, e.g. to create specific run templates etc.
  See the pysysproject.xml file in pysys-examples for more information.
- The make option to pysys.py now accepts the testcase directory to be
  specified to a value other than the current working directory.

0.9.1 to 0.9.2
--------------
- The method getNextAvailableTCPPort has been added to the 
  pysys.basetest.BaseTest class to allow users to allocate server TCP ports 
  in a robust manner.
- The unix and windows process helpers have been updated to fix handle leaks 
  (defect #11 "ProcessMonitor leaks file handles"), and to delete the stdin 
  queue when processes go away. 

0.9.0 to 0.9.1
--------------
- Fixed issue with the determination of the overall test outcome due to the 
  incorrect use of the inbuilt sorted() function. The issue meant the test
  outcome list was not correctly sorted based on precedent, leading to the 
  incorrect determination of the overall test outcome. 
- Fixed issue in the pysys.basetest on handling FileNotFoundExceptions in 
  the assert* methods. The exception was not being caught, leading to 
  subsequent asserts in the test class not being performed. 

0.8.1 to 0.9.0
--------------
- The PySys framework has been updated to be compliant with conversion to 
  Python 3.x with the 2to3.py conversion script. Installation on Python 3.x 
  is now supported via the source distribution bundle, where the 2to3.py 
  script is run automatically at install time. See details below for 
  installing the source distribution. A binary distribution installer for 
  windows will be included in a later release. 
- There are now separate 32 and 64 bit binary distribution installers for 
  windows. 
- On failure of the assertLineCount method, the log output now contains the 
  returned number and requested condition (tracker #3045931)  
- Each assert method now takes an "assertMessage" parameter to be written
  to the log output on execution (tracker #3045924). See test
  PySys_internal_053 in the example testcases for example usage.
- Added the JUnitXMLResultsWriter to log test results in Apache Ant JUnit 
  XML format (one output file per test per cycle). This is useful for 
  integration into Continuous Integration build systems, e.g. TeamCity. The 
  TextResultsWriter and XMLResultsWriter now support the outputDir property 
  to specify the location to write the output files. See the pysys-examples 
  pysysproject.xml file for more details.
- Added the ability to run suites of pyunit tests wrapped up as a single 
  PySys test. This capability is exposed through the PyUnitTest class 
  contained in the pysys.unit.pyunit module. See the pysys-examples pyunit
  tests for example usage.
- Fix to the unix process helper to correctly set the working directory of 
  child processes in the fork and exec. 
- When running tests in parallel, a value of zero given for the 
  -n|--threads option to the run task of the pysys.py launcher, will set 
  the number of threads to the number of available CPUs.

0.7.6 to 0.8.1
--------------
- Updated the pysys.process.plat-win32.helper.ProcessWrapper module to 
  eliminate the use of threads to collect the stdout and stderr from the 
  process via pipes. The module now directly uses win32file.CreateFile to 
  create file objects to pass to the call to win32process.CreateProcess. 
- Added the <formatters/> element to the pysysproject file. This allows 
  setting the format of the test output to stdout and the runlog in 
  accordance to the format specifiers in the python logging and time 
  modules. For examples of the use of this element, see the pysysproject 
  file included in the PySys examples. 
- Logging of exceptions and failed asserts has been changed from info to 
  warn level (tracker #2784251).
- Added extra debug logging in pysys.utils.filegrep, and pysys.basetest 
  for when performing asserts against a line count in an input file 
  (tracker #2824758).
- The testcase output summary is now printed on termination of the test 
  run via a keyboard interrupt (tracker #2816212).
- The PySys project file now allows assignment of the project root 
  location to a variable which can then be used for later expansion within 
  the file. This allows the definition of project variables to include the 
  full path where this is required, e.g. XSL stylesheets which must use 
  the full path to the file rather than a relative path etc. Note that 
  modules within PySys can reference the project root location directly 
  using PROJECT.root (tracker #2795316). 
- The pysys.baserunner class now passes the -X arguments into the test 
  summary writer setup action to allow logging of the user supplied extra 
  arguments(tracker #2814499). The pysys-log.xsl stylesheet used by the 
  XMLResultsWriter 
  has been updated to display this information in the test summary display. 
- Fixed an issue where when the pysysproject file was missing, defaults 
  for the runner module and the test output summary writer were not being 
  set.

0.7.5 to 0.7.6
--------------
- Fixed a defect in the unix process helper module to correct a file 
  handle leak in the write end of the stdin pipe.

0.6.1 to 0.7.5
--------------
- Added the ability to run tests concurrently through the -n | --threads 
  option to the pysys launcher run target. Tests to be run are placed on a 
  request queue and processed by the designated number of worker threads. 
  The results of each test are then placed on a result queue, collated and 
  displayed in the order in which they would run serially. Depending on 
  the nature of the application under test, the recommended number of 
  threads to designate when using this option is no more than two times 
  the number of CPUs. Note also that care needs to be made when running 
  tests in parallel, so as to ensure no shared resources are accessed 
  in a non-atomic way, e.g using direct references to os.environ() in one 
  test when another test modifies the environment directly etc.
- The constructor to the pysys.baserunner.BaseRunner class was changed to 
  include the threads parameter, i.e. ::
  
  	def __init__(self, record, purge, cycle, mode, threads, outsubdir, descriptors, xargs)
  	
  This parameter is required for the runner to create the required 
  threadpool before running a set of tests in parallel. Any custom runner 
  classes extending the base runner will need to be updated to incorporate 
  this change. 
- Removed module specific loggers from pysys in order to support running 
  tests in parallel. There is now a single logger used within the 
  framework, and which can be referenced directly from the pysys.constants 
  module. Attached to this logger are two handler types; one for logging 
  to stdout, and one for logging to the run 
  log file saved in the output subdirectory of each test. The stdout 
  handler is set to only log to stdout from the main thread, whilst the 
  run log file handlers are set to log to the output subdirectory of a 
  test only on the creating thread.
- Added exception handling to the pysys.process.user module when trying to 
  stop all processes on destruction. When a background process takes 
  longer to stop than the default timeout period, the thrown 
  pysys.exceptions.ProcessTimeout exception was uncaught causing abnormal 
  exit from the test run.  

0.6.0 to 0.6.1
--------------
- The clean target has been updated to accept the -a | --all command line 
  option to allow deleting all derived files produced when running a set 
  of testcases, i.e. both the testcase output subdirectory and any 
  compiled test class modules.
- The waitForSignal method of the ProcessUser class, subclassed by both 
  the BaseTestand BaseRunner classes, has been updated to return a list of 
  match objects on invocation. By using tagged regular expressions in the 
  expr parameter of the method call, this allows retrieval of portions of 
  the matched data e.g. to extract expressions in the file to use later in 
  the validation routines. 
- All references to pysys.constants.TRUE and pysys.constants.FALSE have 
  been replaced by the native Python True and False literals. The values 
  of the constants have been set to True and False respectively so as to 
  maintain backwards compatibility.

0.5.2 to 0.6.0
--------------
- The PySys test and PySys project files have been renamed by default from  
  .pysystest to pysystest.xm, and .pysysproject to pysysproject.xml 
  respectively. Backwards compatibility is maintained for the previous 
  file naming convention, though this will be deprecated in a later 
  release; it is strongly advised that the new naming convention is 
  adopted. New tests made using the PySys launcher will by default use the 
  new naming convention. This change was made due to issues on Windows 
  systems displaying and recognising hidden files, and files without 
  specified extensions e.g. within the Eclipse framework, for display in 
  internet browsers etc.
- The clean mode of operation has been added to the pysys.py launcher. This 
  allows removal of testcase output subdirectories, e.g. before importing 
  into a source code control system. The -o option allows specifying the 
  output subdirectory name to be deleted, which defaults to the platform 
  identifier if not specified. 
- The test output summary writer interface has been changed so that the 
  test output is written and updated during the test execution; previously 
  a call to the writer was only made on completion of the test run. This 
  allows monitoring the test output summary during the test execution to 
  monitor the run time status of the tests. 
- Added the XMLFileResultsWriter class to the pysys.writer module. This 
  performs logging of the test output summary in an XML format, suitable
  for display via XLST in a web browser. A simple XSL stylesheet is 
  included with the PySys distribution to provide better display in 
  internet browsers. 
- Added the ability to specify custom test output summary writers in the 
  PySys project file via the <writer> tag. For an example see the 
  .pysysproject file in the pysys-examples distribution. Should no 
  <writer> be specified in the project file, the default 
  XMLFileResultsWriter will be used. Multiple writers may be specified in 
  the PySys project file.  
- Added exception logging on parsing errors in the PySys project file, e.g. 
  when the file in badly formed due to invalid XML tokens etc.
- Added variable argument passing to the process.monitor.ProcessMonitor 
  class constructor so that operating specific arguments can be passed 
  into the class on instantiation. The wrapper method 
  pysys.basetest.BaseTest.startProcessMonitor has also been updated to 
  allow pass through of the variable arguments. 
- The win32 process.monitor module has been changed so that on windows 
  systems the percentage CPU usage is not normalised by default by the 
  number of available processors, e.g. on a 4 core processor if 2 cores 
  were fully utilized the CPU usage was previously output as 50% - the 
  change means that the reported usage will now be 200% (a value of 100% 
  indicates that one core is fully utilitised). This makes the output 
  consistent with that reported on unix systems. Should the 
  previous behavior be required the numProcessors argument can be passed 
  to the pysys.basetest.BaseTest.startProcessMonitor method in order to 
  normalise the CPU usage statistics by the number of processors. On 
  windows systems the number of processors can be obtained from the 
  NUM_PROCESSORS environment variable.
- Added comments to the PySys Project file distributed with the example 
  testcases, to detail the possible configuration options.

0.5.1 to 0.5.2
--------------
- The lastgrep method has been added to pysys.utils.filegrep, and the 
  assertLastGrep method has been added to the BaseTest class. This allows 
  test validation to be performed based on regular expression matching on 
  the last line of an input file to the assertLastGrep method.
- The win32 process monitor has been modified to calculate the percentage 
  CPU usage statistics as a sum over all available processors. A CPU usage 
  of 100% represents the process fully utilising all available processors. 
- The win32 process monitor now also logs the handle count of a process.

0.5.0 to 0.5.1
--------------
- Fixed a bug in pysys.process.user.ProcessUser destructor to explicitly 
  set the process list to null to allow process handles to be cleaned up 
  on destruction. This bug only seemed to be exhibited when the process 
  handle of a process returned in the startProcess() method was set as a 
  data attribute to an instance of the class. This handle was then both a 
  data attribute of the class, and was contained in a list data attribute 
  of the class. Under these conditions the handles were not being released 
  correctly.
- The print mode of the pysys.py launcher now supports printing out the 
  test user defined modes, and the printing out of tests that can be run 
  in a given mode.
  
0.4.0 to 0.5.0
--------------
- The OSFAMILY constant has been added to pysys.constants, and takes the 
  value 'windows' on all win32 operating systems, and 'unix' on sunos and 
  linux operating systems. The value of the OSFAMILY can be used within 
  the .pysysproject file using the osfamily attribute to the <property> 
  element. This allows capturing the value to be used in expansion of 
  other properties defined within the project file; see below for an 
  example usage. Should no value be set in a properties file, a default 
  value of "osfamily" is assumed. 
- The .pysysproject file now allows explicitly setting the environment 
  value to be used in expansions via the environment attribute to the 
  <property> element; see 
  below for an example usage. Should no value be set in a properties file, 
  a default value of "env" is assumed (this allows for backwards compatibility).
- The .pysysproject file now takes the file attribute to the <property> 
  element. This allows properties to be read from file, where the 
  properties are specified in the name=value syntax, e.g. ::
  
    <pysysproject>
      <property environment="env"/>
      <property osfamily="osfamily"/>
      <property file="${osfamily}.properties" />
      <property name="lib" value="${library}_${osfamily}_${version}_${env.USER}.so"/>
    </pysysproject>
  
  where the property file contains the following::
  
     version=1.0
     library=jstore${version}.jar
  
  For more details, see testcase PySys_internal_002 in the 
  pysys-examples/internal area which demonstrates this. 
  
- Fixed the issue of removing zero size files from the output subdirectory 
  on win32 platforms; was due to the stderr and stdout file handles not 
  being properly closed down. Updated the BaseRunner to attempt to remove 
  the zero sized files 3 times to try to avoid race conditions of stopped 
  background processes holding on to the file handles too long before dying.
- The win32 process helper now ensures the environment in which the  
  process runs is converted to unicode to avoid issues encountered with 
  running under certain locales. 

0.3.5 to 0.4.0
--------------
- The pysys.process.ProcessUser class has been added to define an 
  interface to subclasses which use the underlying process helper classes. 
  Both the BaseTest and BaseRunner classes now extend this so as to 
  provide a common interface for process manipulation. A common paradigm 
  for creating extension modules to PySys is to create a helper class 
  which provides the methods for starting an interacting with the 
  application under test (AUT). These helper classes have a call back to 
  an instance of the ProcessUser so that it can make use of the high level 
  process methods. As both the BaseTest and BaseRunner classes are 
  instances of the ProcessUser, the extension module helper classes can be 
  used in extensions to both of these to allow the AUT to be started both 
  within a testcase, and within the runner.
- The method signature to the pysys.utils.filereplace replace method has 
  been changed to set the default value for the marker to the empty string
- Bugs fixes for cleaning up leakage of threads from the process helpers, 
  and file handle leakage from the base runner classes.

0.3.4 to 0.3.5
--------------
- Fixed a bug a testcase was not being marked as BLOCKED when unable to 
  start a process using the process helper module.
- Failure on the assertOrderedGrep now prints out the line the failure 
  occurred on.

0.3.3 to 0.3.4
--------------
- Fixed a bug where timedout processes started in the foreground were not 
  being stopped automatically at the end of the testcase.
  
0.3.2 to 0.3.3
--------------
- The default name of the PySys test descriptor file has been changed from 
  "descriptor.xml", to ".pysystest". This change is to maintain a consistent
  naming convention across configuration files within the framework, e.g. 
  the project file ".pysysproject" denotes the project root and project 
  specific information, whilst a test file ".pysystest" denotes a testcase 
  within the project, and contains meta data for the test. Support for the 
  previous name is maintained, though it should be noted that testcases 
  created with the 'pysys.py make' command will have the new naming 
  convention used.
- The windows installer has been updated to add shortcuts to the 
  uninstaller, and to create a separate directory for the inclusion of 
  project extensions. 
- The getInstanceCount method has been added to the 
  pysys.basetest.BaseTest class to reference count the number of named 
  processes started during a test run. The startProcess method of the 
  class adds a reference count to an internal dictionary 
  structure keyed on the displayName passed into the method to achieve 
  this. 
- The writeProcess method has been added to the pysys.basetest.BaseTest 
  class to provide a wrapper around the write method of the underlying 
  process helper class. This wrapper perform a check on the running status 
  of the process prior to the write, and performs additional logging to 
  the run.log to audit the write. 
- Fixed a bug in the replace method of the filereplace module, where the 
  method signature was missing the marker parameter
- Added support to the pysys project file to allow adding path locations 
  to the Python path. See the .pysysproject file in pysys-examples for 
  more detail.

0.3.1 to 0.3.2
--------------
- Release was superseded immediately by the 0.3.3 release. See release 
  notes for new features for 0.3.3 for more information.

0.3.0 to 0.3.1
--------------
- The process helper modules have been updated to allow the writing to the 
  stdin of a process via the write() method on the process handle. 
- Several bug fixes have been applied to the unix process helper module.
- The pysys-examples/internal directory has been added to the examples 
  module. This will contain internal testcases for self testing the pysys 
  framework. These have been included in the distribution as examples of 
  the use of the framework.
- The pysys project file has been added into the framework to allow the 
  setting of project specific constants within the application. The 
  project file should be written to the base location of the project, with 
  the filename .pysysproject. The location of this file denotes the root 
  location of the project. For an example of the file see 
  pysys-examples/.pysysproject. Any name value properties
  within the file will be set as data attributes of the pysys.Project 
  class, which is referenced in the pysys.constants module using the 
  variable PROJECT. 

0.2.2 to 0.3.0
--------------
- Updates to the epydoc output for documenting the classes and modules of 
  pysys
- Addition of the pysys.py module for printing, running and making new 
  testcase directory structures. This allows a single distributed script 
  to be used to perform all functionality available from the console. 
- Remove of the run method from the console launch helper.

0.2.1 to 0.2.2
--------------
- The suites element in the test descriptor has been renamed to groups. 
  This is to allow testcases in a single directory to be classified as a 
  single testsuite, and subsets thereof to be regarded as a group
- Minor bug fixes to the manual tester and process module

0.2.0 to 0.2.1
--------------
- The Manual Tester has been updated to support the <expectedresult> 
  element in the input xml file. This allows display of the expected 
  result for a manual step to be presented in the user interface. The 
  ability to optionally record a defect in the log output is also now 
  included.
- The createDescriptors method has been removed from the 
  pysys.launcher.console package and moved into pysys.launcher. This 
  allows the utility method to be used for other custom launchers.

0.1.7 to 0.2.0
--------------
- This release includes updates to the Python doc strings for automated 
  generation of epydoc using the Epydoc package 
  (http://epydoc.sourceforge.net). The installer now distributes the 
  generated epydoc in the site-packages/pysys-doc directory. For 
  windows installs a link to the epydoc and release notes is now added as 
  a link in the start menu items
- Added the setup() method to the BaseTest class to allow custom setup 
  actions to be performed prior to execution of a particular test case
- Fixed a bug where if the --type option was not supplied to 
  ConsoleMakeTestHelper as a command line option, the resulting descriptor 
  had type="None"

0.1.6 to 0.1.7
--------------
- The Manual Tester UI has been updated so that it can be resized, and is 
  easier to navigate through the tests. 
- The BaseRunner start method now takes an optional list of result writer 
  class instances to perform test audit logging at the end of a test 
  cycle. This allows custom result writers to be passed to the runner to, 
  for example, write the results to a database, proprietary system etc
  
0.1.5 to 0.1.6
--------------
- Added the ability to differentiate between automated and manual 
  testcases using the test attribute to the pysystest element in the 
  testcase descriptor. If the attribute is not present the test will be 
  assumed to be an automated test. The runTest and printTest launch 
  helpers allow you to differentiate between automated and manual 
  tests using the --type command line argument. For more information see 
  the examples in pysys-examples

0.1.4 to 0.1.5
--------------
- Added support for the requirements traceability. This includes printing 
  requirements covered by a set of testcases, and running testcases which 
  cover a particular requirement id

0.1.3 to 0.1.4
--------------
- Added the ConsoleMakeTestHelper class to pysys.launcher.console. This 
  facilitates the creation of new testcase structures from the command 
  line. Updated pysys-examples/fibonacci to demonstrate the use of the 
  utility class 
