User Guide
==========

.. py:currentmodule:: pysys.basetest

Platform detection
------------------

It's very common to have one set of logic for Windows and another for 
all non-Windows (Unix-based) platforms, and PySys has a dedicated constant `pysys.constants.IS_WINDOWS` for 
that::

	self.startProcess('cmd.exe' if IS_WINDOWS else 'bash', ...)

For finer grained platform detection we recommend using the facilities built into Python, for example 
``sys.platform``, ``platform.platform()`` or ``platform.uname()``.

Skipping tests
--------------
If your tests' ``.py`` logic detects that a test should not be executed for this 
platform or mode, simply use `self.skipTest(...) <BaseTest.skipTest>` near the top of the test's 
`execute() <BaseTest.execute>` method, specifying the reason for the skip::

	self.skipTest('MyFeature is not supported on Windows') 
	
As well as setting the test outcome and reason, this will raise an exception 
ensuring that the rest of `execute() <BaseTest.execute>` and 
`validate() <BaseTest.validate>` do not get executed. 

Alternatively if the test should be skipped regardless of platform/mode etc, 
it is best to specify that statically in your `pysystest.*` file::

	__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed" 

Or::

	<skipped reason="Skipped until Bug-1234 is fixed"/>

Customizing pysys make
----------------------
You can define templates that ``pysys make`` will use to create new tests specific to your project, or even multiple 
templates for individual directories within your project. This helps to encourage teams to follow the latest best 
practice by ensuring new tests are copying known good patterns, and also saves looking up how to do common things when 
creating new tests. 

The ``pysys make`` command line comes with a ``pysys-default-test`` template for creating a simple PySys test, you can 
add your own by adding ``<maker-template>`` elements to ``pysysdirconfig.xml`` in any directory under your project, 
or to a ``<pysysdirconfig>`` element in your ``pysysproject.xml`` file. Here are a couple of examples (taken from 
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
named ``.pysysignore`` file (which avoids the template being loaded as a real test). 

other options are possible (as above) e.g. copying files from an absolute location such as under your project's 
``${testRootDir}``, copying from PySys default templates directly (if you just want to *add* files) by 
using ``${pysysTemplatesDir}/default-test/*``, or copying from a path relative to the XML file where the template is 
defined containing a real (but simple) test to copy from (with suitable regex replacements to make it more generic). 

See :ref:`pysys/TestDescriptors:Sample pysysdirconfig.xml` for more information about how to configure templates in 
a ``pysysdirconfig.xml`` file. 

When creating tests using ``pysys make``, by default the first template (from the most specific ``pysysdirconfig.xml``) 
is selected, but you can also specify any other template by name using the ``-t`` option, and get a list of available 
templates for the current directory using ``--help``. 

It is possible to subclass the `pysys.launcher.console_make.DefaultTestMaker` responsible for this logic if needed. 
The main reason to do that is to provide a `pysys.launcher.console_make.DefaultTestMaker.validateTestId` method 
to check that new test ids do not conflict with others used by others in a remote version control system (to avoid 
merge conflicts). 

By default PySys creates ``.py`` files with tabs for indentation (as in previous PySys releases). If you prefer spaces, 
just set the ``pythonIndentationSpacesPerTab`` project property to a string containing the required spaces per tab.

Checking for error messages in log files
-----------------------------------------
The `BaseTest.assertGrep()` method is an easy way to check that there are no error 
messages in log files from processes started by PySys. Rather than checking for 
an expression such as `' ERROR: '`, it is recommended to define your expression 
so that the error message itself is included, e.g.::

	self.assertGrep('myprocess.log', expr=' ERROR: .*', contains=False)

This approach ensures that the error message itself is included in the test's 
console output, run.log and the summary of failed test outcomes, which avoids 
the need to open up the individual logs to find out what happened, and makes it 
much easier to triage test failures, especially if several tests fail for the 
same reason. 

Sharing logic across tests using plugins
----------------------------------------
Often you will have some standard logic that needs to be used in the execute or validation 
of many/all testcases, such as starting the application you're testing, or checking log files for errors. 

The recommended way to do that in PySys is to create one or more "plugins". There are currently several kinds of plugin: 

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

  Runner plugins that generate output files/directories should by default put that output under either the 
  `runner.output <pysys.baserunner.BaseRunner>` directory, or (for increased prominence) the ``runner.output+'/..'`` 
  directory (which is typically ``testRootDir`` unless an absolute ``--outdir`` path was provided). 

- **writer plugins**: this kind of plugin has existed in PySys for many releases and are effectively a special kind of 
  runner plugin with extra callbacks to allow them to write test results and/or output files to a variety of 
  destinations. Writers must implement a similar but different interface to other runner plugins; see `pysys.writer` 
  for details. They can be used for everything from writing test outcome to an XML file, to archiving output files, to 
  collecting files from each test output and using them to generate a code coverage report during cleanup at the end 
  of the run. 

To make your plugin configurable, add a static field for each plugin property, which defines the default value 
and (implicitly) the type. After construction of each plugin, an attribute is assigned with the actual value 
of each plugin property so each property can be accessed using ``self.propname`` (by the time the plugin's setup method 
is called). In addition to plugin properties, ``pysys run -Xkey=value`` command line options for the plugin 
(if needed) can be accessed using the runner's `pysys.baserunner.BaseRunner.getXArg()` method. 

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

			# there is no standard cleanup() method, so do this if you need to execute something on cleanup:
			testObj.addCleanupFunction(self.__myPluginCleanup)  

		def __myPluginCleanup(self):
			self.log.info('Cleaning up MyTestPlugin instance')

		# An example of providing a method that can be accessed from each test
		def getPythonVersion(self):
			self.owner.startProcess(sys.executable, arguments=['--version'], stdouterr='MyTestPlugin.pythonVersion')
			return self.owner.waitForGrep('MyTestPlugin.pythonVersion.out', '(?P<output>.+)')['output'].strip()

		# A common pattern is to create a helper method that you always call from your `BaseTest.validate()`
		# That approach allows you to later customize the logic by changing just one single place, and also to omit 
		# it for specific tests where it is not wanted. 
		def checkLogsForErrors(self, logfile="my_server.log"):
			self.assertGrep(logfile, ' (ERROR|FATAL) .*', contains=False)

With configuration like this::

    <pysysproject>
	    <test-plugin classname="myorg.testplugin.MyTestPlugin" alias="myalias">
			<property name="myPluginProperty" value="my value"/>
	    </test-plugin>
    </pysysproject>

... you can now access methods defined by the plugin from your tests using ``self.myalias.getPythonVersion()``. 

Alternatively, you can create a trivial `BaseTest` subclass that instantiates plugins in code (rather than XML) 
which would allow code completion (if your editor of choice supports this) but still provide the benefits of 
the modular composition approach. 

You can add any number of test and/or runner plugins to your project, perhaps a mixture of custom plugins specific 
to your application, and third party PySys plugins supporting standard tools and languages. 

In addition to the alias-based lookup, plugins can get a list of the other plugin instances 
using ``self.testPlugins`` (from `BaseTest`) or ``self.runnerPlugins`` (from `pysys.baserunner.BaseRunner`), which 
provides a way for plugins to reference each other without depending on the aliases that may be in use in a 
particular project configuration.  

When creating a runner plugin you may need somewhere to put output files, logs etc. Plugins that generate output 
files/directories should by default put that output in a dedicated directory either the 
`runner.output <pysys.baserunner.BaseRunner>` directory, or (for increased prominence if it's something users will 
look at a lot) a directory one level up e.g. ``runner.output+'/../myplugin'`` (which is typically under ``testRootDir`` 
unless an absolute ``--outdir`` path was provided) . 
A prefix of double underscore ``__pysys`` is recommended under testRootDir to distinguish dynamically created 
directories (ignored by version control) from the testcase directories (checked into version control). 

For examples of the project configuration, including how to set plugin-specific properties that will be passed to 
its constructor, see :doc:`/pysys/ProjectConfiguration`. 

Configuring and overriding test options
---------------------------------------
PySys provides two mechanisms for specifying options such as credentials, 
hostnames, or test duration/iteration that you might want to change or 
override when running tests:

- *Testcase attributes*, which are just variables on the Python testcase 
  instance (or a `BaseTest` subclass shared by many tests). 
  Attributes can be overridden on the command line using ``pysys run -Xattr=value``. 
  
  Attributes are useful for settings specific to an individual testcase such as 
  the number of iterations or time duration to use for a performance test. 
  A user running the test locally you might want to temporarily set to a lower 
  iteration count while getting the test right, or perhaps try 
  a higher value to get a more stable performance result. 
  
- *Project properties*. The default value is specified in the ``pysysproject.xml`` 
  file or in a ``.properties`` file referenced from it. 
  
  Properties can be overridden using an environment variable. 
  Project properties are useful for things like credentials and hostnames that 
  are shared across many testcases, and where you might want to set up 
  customizations in your shell so that you don't need to keep specifying them 
  every time you invoke ``pysys run``. 

To use a testcase attribute, set the default value on your test or basetest as a static attribute on the test 
class, for example::

	class PySysTest(BaseTest):

		myIterationCount = 100*1000 # can be overridden with -XmyIterationCount=
		
		def execute(self):
			self.log.info('Using iterations=%d', self.myIterationCount)
			...

Once the default value is defined with a static attribute, you can override the value 
when you run your test using the ``-X`` option::

	pysys run -XmyIterationCount=10

If the attribute was defined with a default value of int, float, bool or list then 
the ``-X`` value will be automatically converted to that type; otherwise, it will 
be a string. 

If instead of setting a default for just one test you wish to set the default 
for many tests from your custom `BaseTest` subclass, then you would do the same thing in the 
definition of that `BaseTest` subclass. If you don't have a custom BaseTest class, you can use 
`self.runner.getXArg() <pysys.baserunner.BaseRunner.getXArg>` from any plugin to get the value or default, with the same 
type conversion described above. 

The other mechanism that PySys supports for configurable test options is 
project properties. 

To use a project property that can be overridden with an environment variable, 
add a ``property`` element to your ``pysysproject.xml`` file::

	<property name="myCredentials" value="${env.MYORG_CREDENTIALS}" default="testuser:testpassword"/>

This property can will take the value of the specified environment variable, 
or else the default if any undefined properties/env vars are included in value. Note that if the value contains 
unresolved variables and there is no valid default, the project will fail to load. 

You may want to set the attribute ``pathMustExist="true"`` when defining properties that refer to a path such as a 
build output directory that should always be present. 

Another way to specify default project property values is to put them into a ``.properties`` file. You can use 
properties to specify which file is loaded, so it would be possible to customize using environment variables::

	<property name="myProjectPropertiesFile" value="${env.MYORG_CUSTOM_PROJECT_PROPERTIES}" default="${testRootDir}/default-config.properties"/>
	<property file="${myProjectPropertiesFile}" pathMustExist="true"/>

To use projects properties in your testcase, just access the attributes on 
`self.project <pysys.config.project.Project>` from either a test instance or a runner::

	def execute(self):
		username, password = self.project.myCredentials.split(':')
		self.log.info('Using username=%s and password=%s', username, password)

Project properties are always be of string type, but `pysys.config.project.Project.getProperty()` can be used to 
convert the value to other types when needed. 

Thread-safety
-------------
As your testsuite grows, the ability to run tests in parallel will be increasingly important, so make sure your 
tests and any shared plugin code do not manipulate shared data structures or files in a way that could cause 
race conditions.

Most Python library functions are safe to use, but you should avoid calling ``locale.getpreferredencoding()`` 
(use `pysys.constants.PREFERRED_ENCODING` instead) and ``shutil.make_archive`` which are not. 

It is also important not to change to the working directory of the PySys process or its environment (``os.environ``) 
while tests are executing. Any setup that might involve changing the environment - including initialization of 
some libraries (e.g. Matplotlib) must be performed before tests start in the ``setup`` of a runner plugin (or runner), 
so that everything is stable ready for tests to be executed. 

To avoid dangerous and hard-to-debug race conditions, PySys has built-in checking for changes to the working directory 
and os.environ and the test run will fail if either is detected. 

Producing code coverage reports
-------------------------------
PySys can be extended to produce code coverage reports for any language, by creating a writer plugin. 

There is an existing writer that produces coverage reports for programs written in Python called 
`pysys.writer.coverage.PythonCoverageWriter`, which uses the ``coverage.py`` library. To use this you need to add the 
``<writer>`` to your project (see the sample :doc:`/pysys/ProjectConfiguration` for an example) and make sure you're starting 
your Python processes with coverage support enabled, by using `BaseTest.startPython`. 

The usual way to enable code coverage (for all supported languages) is to set ``-XcodeCoverage`` when running your 
tests (or to run with ``--ci`` which does this automatically). Individual writers may additionally provide their own 
properties to allow fine-grained control e.g. ``-XpythonCoverage=true/false``. 

Be sure to add the ``disableCoverage`` group to any tests (or test directories) that should not use coverage, 
such as performance tests. 

If you wish to produce coverage reports using any other language, this is easy to achieve by following the same pattern:

- When your tests start the program(s) whose coverage is to be measured, add the required arguments or environment 
  variables to enable coverage using the coverage tool of your choice. The most convenient place to put helper methods 
  for starting your application is in a custom test plugin class. 
  
  When starting your process, you can detect whether to enable code coverage like this::
  
    if self.runner.getBoolProperty('mylanguageCoverage', default=self.runner.getBoolProperty('codeCoverage')) and not self.disableCoverage:
	  ...

  Often you will need to set an environment variable to indicate the filename that coverage should be generated under. 
  Make sure to use a unique filename so that multiple processes started by the same test do not clash. Often you 
  will need to ensure that your application is shutdown cleanly (rather than being automatically killed at the end of 
  the test) so that it has a chance to write the code coverage information. 

- Create a custom writer class which collects coverage files (matching a specific regex pattern) from the output 
  directory. The usual way to do this would be to subclass `pysys.writer.testoutput.CollectTestOutputWriter`. Configure 
  default values for main configuration properties (by defining them as static variables in your class). Then implement 
  `pysys.writer.api.BaseResultsWriter.isEnabled()` to define when coverage reporting will happen, and run the 
  required processes to combine coverage files and generate a report in the destDir in 
  `pysys.writer.api.BaseResultsWriter.cleanup()`, which will execute after all tests have completed. 
  
  Finally, add the new writer class to your ``pysysproject.xml`` file. 
  
- Add the ``disableCoverage`` group to any tests (or test directories) that should not use coverage, 
  such as performance tests. 
   
- If using a continuous integration system or centralized code coverage database, you could optionally upload the 
  coverage data there from the directory PySys collected it into, so there is a permanent record of 
  any changes in coverage over time. The artifact publishing capability of 
  `pysys.writer.testoutput.CollectTestOutputWriter` will help with that. 

Running tests in multiple modes
-------------------------------
One of the powerful features of PySys is the ability to run the same test 
in multiple modes from a single execution. This could be useful for cases such 
as a set of tests that should be run against various different databases but 
can also be run against a mocked database for quick local development. 
Another common use case is executing the same PySysTest class in different 
modes to test different scenarios. 

To define some modes, first edit the ``pysystest.*`` file for your test, and provide a string 
containing a Python lambda that will be evaluated when the test descriptors are loaded to 
return a list of named modes that the test can run in:

.. code-block:: python
	
	__pysys_modes__ = r""" 
		lambda helper: helper.inheritedModes+[
			{'mode':'CompressionGZip', 'compressionType':'gzip'},
		]
	"""

The ``helper`` is an instance of `pysys.config.descriptor.TestModesConfigHelper` which provides 
access to the list of inherited modes (and more). 

When naming modes, TitleCase is recommended, and dot, underscore and equals characters 
may be used. Typically dot is useful for version numbers and underscore ``_`` is 
useful for separating out different dimensions (e.g. compression vs authentication type 
in the example described later in this section); separating dimensions cleanly will make it 
much easier to include/exclude the test modes you want. PySys will give an error if you use different 
capitalization for the same mode in different places, as this can result in test bugs. 

In large projects you may wish to configure modes in a ``pysysdirconfig.xml`` 
file in a parent directory rather than in ``pysystest.*``, which will by 
default be inherited by all nested testcases (unless an explicit modes 
configuration is provided), and so that there's a single place to edit the modes 
list if you need to change them later. 

By default the first mode in each list is "primary", so the test will only run in that one primary mode by 
default during local test runs (i.e. unless you supply a ``--modes`` or ``--ci`` argument). This is optimal when 
using modes to validate the same behaviour/conditions in different execution environments e.g. 
browsers/databases etc. It's best to choose either the fastest mode or else the one that 
is most likely to show up interesting issues as the primary mode. 

However when using modes to validate different *behaviours/conditions* (e.g. testing 
out different command line options) using a single PySysTest class, then you should designate all your modes as 
"primary" as you want *all of them* to execute by default in a quick local test run. 
The `pysys.config.descriptor.TestModesConfigHelper.makeAllPrimary` helper function can do this. 

Sometimes your modes will have multiple dimensions, such as database, web browser, compression type, authentication 
type etc, and you may want your tests to run in all combinations of each item in each dimension list. 
Rather than writing out every combination manually, you can use the function 
`pysys.config.descriptor.TestModesConfigHelper.combineModeDimensions` to automatically generate the combinations, 
passing it each dimension (e.g. each compression type) as a separate list. 

Here is an example of multi-dimensional modes (taken from the getting-started sample):

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
					
					# By default only the first mode in each list is "primary", so the test will only run in that one mode by 
					# default during local development (unless you supply a ``--modes`` or ``--ci`` argument). This is optimal when 
					# using modes to validate the same behaviour/conditions in different execution environments e.g. 
					# browsers/databases etc. However when using modes to validate different *behaviours/conditions* (e.g. testing 
					# out different command line options) using a single PySysTest class, then you should have all your modes as 
					# "primary" as you want all of them to execute by default in a quick local test run. 
					helper.makeAllPrimary(
						{
							'Usage':        {'cmd': ['--help'], 'expectedExitStatus':'==0'}, 
							'BadPort':      {'cmd': ['--port', '-1'],  'expectedExitStatus':'!=0'}, 
							'MissingPort':  {'cmd': [],  'expectedExitStatus':'!=0'}, 
						}), 
					)
				
			# This is Python list comprehension syntax for filtering the items in the list
			if (mode['auth'] != 'OS' or helper.import_module('sys').platform == 'MyFunkyOS')
		]
	"""

This will create the following modes::

	CompressionNone_Auth=None_Usage       [PRIMARY]
	CompressionNone_Auth=None_BadPort     [PRIMARY]
	CompressionNone_Auth=None_MissingPort [PRIMARY]
	CompressionGZip_Auth=None_Usage
	CompressionGZip_Auth=None_BadPort
	CompressionGZip_Auth=None_MissingPort
	CompressionNone_OS_Usage
	CompressionNone_OS_BadPort
	CompressionNone_OS_MissingPort
	CompressionGZip_OS_Usage
	CompressionGZip_OS_BadPort
	CompressionGZip_OS_MissingPort

When creating multi-dimensional modes you can explicitly specify the name of each mode using ``'mode':..``, but 
if you want to avoid repeating the value of your parameters you can let PySys generate a default mode, which 
it does by taking each parameter concatenated with ``_``; parameters with non-string values (e.g. ``None`` in 
the above example) are additionally qualified with ``paramName=`` to make the meaning clear. 

The above example also shows how a Python list comprehension can be used to filter prevent the Auth=OS modes 
from being added on some operation systems (in this example, on all non-fictional operating systems!). 

You can find the mode that this test is running in using `self.mode <BaseTest>`, which returns an instance of 
`pysys.config.descriptor.TestMode` that subclasses a ``str`` of the mode name, as well as the parameters 
via a ``params`` field. 

Here's an example showing how a test plugin might use modes configuration to configure the test object 
during test setup::

	class MyTestPlugin(object):
		def setup(self, testObj):
			# This is a convenient pattern for specifying the method or class 
			# constructor to call for each mode, and to get an exception if an 
			# invalid mode is specified
			dbHelperFactory = {
				'MockDatabase': MockDB,
				'MyDatabase2.0': lambda: self.startMyDatabase('2.0')
			}[testObj.mode.params['database']]
			...
			# Call the supplied method to start/configure the database
			testObj.db = dbHelperFactory() 

Finally, PySys provides a rich variety of ``pysys run`` arguments to control 
which modes your tests will run with. By default it will run every test in its 
primary modes (for tests with no mode, the primary mode is ``self.mode==None``) - 
which is great for quick checks during development of your application and 
testcases. 

Your main test run (perhaps in a CI job) probably wants to run tests in all 
modes::

  pysys run --mode ALL

(In practice you would use ``--ci`` which does the above and also sets some other useful defaults). 

You can also specify specifies modes to run in, or to run everything except 
specified modes, or even use regular expressions for even more flexibility::

  pysys run --mode MyMode1,MyMode2
  pysys run --mode !MyMode3,!MyMode4
  pysys run --mode MyMode.*


After successfully getting all your tests passing in their primary modes, it could 
be useful to run them in every mode other than the primary::

  pysys run --mode !PRIMARY

For reporting purposes, all testcases must have a unique id. With a multiple 
mode test this is achieved by having the id automatically include a ``~Mode`` 
suffix. If you are reporting performance results from a multi-mode test, make 
sure you include the mode in the ``resultKey`` when you all `BaseTest.reportPerformanceResult`, 
since the ``resultKey`` must be globally unique. 

In addition to the ``--mode`` argument which affects all selected tests, it is 
possible to run a specific test in a specific mode. This can be useful when you 
have a few miscellaneous test failures and just want to re-run the failing 
tests::

  pysys run MyTest_001~MockDatabase MyTest_020~MyDatabase_2.0

Test ids and structuring large projects
---------------------------------------
Each test has a unique ``id`` which is used in various places such as when 
reporting passed/failed outcomes. By default the id is just the name of the 
directory containing the ``pysystest.*`` file. 

You can choose a suitable naming convention for your tests. For example, 
you might wish to differentiate with just a numeric suffix such as::

  MyApp_001
  MyApp_002
  MyApp_003

This has the benefit that it's easy to refer to tests when communicating with 
other developers, and that you can run tests on the command line by specifying 
just a number, but you have to look at the test title to discover what it does. 

Alternatively you could choose to use a semantically meaningful name for each 
test::

  MyApp_TimeoutValueWorks
  MyApp_TimeoutInvalidValuesAreRejected
  MyApp_ValidCredentialsAreAccepted
  
These test ids are easier to understand but can't be referred to as concisely. 

Whatever scheme you use for naming test ids, if you have a large set of tests 
you will want to separate them out into different directories, so that 
related tests can be executed and maintained together. You might have 
different directories for different subsystems/parts of your application, 
and/or for different kinds of testing::

  /  (root dir containing pysysproject.xml)
  
  /SubSystem1/unit/
  /SubSystem1/correctness/
  /SubSystem1/long-running/
  /SubSystem1/performance/
  
  /SubSystem2/unit/
  /SubSystem2/correctness/
  /SubSystem2/long-running/
  /SubSystem2/performance/
  etc.

It is important to ensure every test has a unique id. Although it would be 
possible to do this by convention in the individual test directory names, 
this is fragile and could lead to clashes if someone forgets. Therefore for 
large projects it is usually best to add a ``pysysdirconfig.xml`` file to 
provide default configuration for each directory of testcases. 

For example, in SubSystem1/performance you could create a ``pysysdirconfig.xml`` 
file containing::

	<?xml version="1.0" encoding="utf-8"?>
	<pysysdirconfig>
	  <id-prefix>SubSystem1_perf.</id-prefix>

	  <classification>
		<groups inherit="true">
		  <group>subsystem1</group>
		  <group>performance</group>
		  <group>disableCoverage</group>
		</groups>

		<modes inherit="true">
		</modes>

	  </classification>

	  <execution-order hint="-100.0"/>

	  <!-- Uncomment this to mark all tests under this directory as skipped 
		(overrides the state= attribute on individual tests). -->
	  <!-- <skipped reason=""/> -->

	</pysysdirconfig>

This serves several useful purposes:

- It adds a prefix "SubSystem1_perf." to the beginning of the test directory 
  names to ensure there's a unique id for each one with no chance of conflicts 
  across different directories. 

- It adds groups that make it possible to run all your performance tests, or 
  all your tests for a particular part of the application, in a single command. 

- It disables code coverage instrumentation which could adversely affect your 
  performance results. 

- It specifies that the performance tests will be run with a lower priority, 
  so they execute after more urgent (and quicker) tests such as unit tests. 

- It provides the ability to temporarily skip a set of tests if they are 
  broken temporarily pending a bug fix. 

By default both modes and groups are inherited from ``pysysdirconfig.xml`` files 
in parent directories, but inheriting can be disabled in an individual 
descriptor by providing an explicit list of modes, in case you have a few tests that only 
make sense in one mode. Alternatively, you could allow the tests to exist 
in all modes but call ``self.skipTest <BaseTest.skipTest>`` at the start of the test `BaseTest.execute` method 
if the test cannot execute in the current mode. 

See the :ref:`pysys/TestDescriptors:Sample pysysdirconfig.xml` for a full example of a directory configuration file. 

Controlling execution order
---------------------------
In large projects where the test run takes several hours or days, you may wish 
to control the order that PySys executes different groups of tests - or tests 
with different modes, to maximize the chance of finding out quickly if 
something has gone wrong, and perhaps to prioritize running fast unit and 
correctness tests before commencing on longer running performance or soak tests. 

By default, PySys runs tests based on the sorting them by the full path of 
the `pysystest.*` files. If you have tests with multiple modes, PySys will 
run all tests in their primary modes first, then any/all tests which list a 
second mode, followed by 3rd, 4th, etc. 

All of this can be customized using the concept of an execution order hint. 
Every test descriptor is assigned an execution order hint, which is a positive
or negative floating point number which defaults to 0.0, and is used to sort 
the descriptors before execution. Higher execution order hints mean later 
execution. If two tests have the same hint, PySys falls back on using the 
path of the ``pysystest.*`` file to determine a canonical order. 

The hint for each test is generated by adding together hint components from the 
following:

  - A test-specific hint from the ``pysystest.*`` file's ``__pysys_execution_order_hint__ = `` or 
    ``<execution-order hint="..."/>``. If the hint is 
    not specified (the default), the test inherits any hint specified in a 
    ``pysysdirconfig.xml`` file in an ancestor folder, or 0.0 if there aren't 
    any. Note that hints from ``pysysdirconfig.xml`` files are not added 
    together; instead, the most specific wins. 

  - All ``<execution-order>`` elements in the project configuration file which 
    match the mode and/or group of the test. The project configuration 
    is the place to put mode-specific execution order hints, such as putting 
    a particular database or web browser mode earlier/later. See the 
    sample :doc:`/pysys/ProjectConfiguration` file for details. 
  
  - For multi-mode tests, the ``secondaryModesHintDelta`` specified in the project 
    configuration (unless it's set to zero), multiplied by a number indicating 
    which mode this is. If a test had 3 modes Mode1, Mode2 and Mode3 then 
    the primary mode(s) (Mode1) would get no additional hint, Mode2 would get 
    ``secondaryModesHintDelta`` added to its hint and Mode3 would get
    ``2 x secondaryModesHintDelta`` added to its hint. This is the mechanism 
    PySys uses to ensure all tests run first in their primary modes before 
    any tests run in their secondary modes. Usually the default value of 
    ``secondaryModesHintDelta = +100.0`` is useful and avoids the need for too 
    much mode-specific hint configuration (see above). However if you prefer to 
    turn it off to have more manual control - or you prefer each test to run 
    in all modes before moving on to the next test - then simply set 
    ``secondaryModesHintDelta`` to ``0``.

For really advanced cases, you can programmatically set the 
``executionOrderHint`` on each descriptor by providing a custom 
`pysys.config.descriptor.DescriptorLoader` or in the constructor of a 
custom `pysys.baserunner.BaseRunner` class or plugin. 
