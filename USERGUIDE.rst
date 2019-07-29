PySys User Guide and FAQ
========================

Platform detection
------------------
In addition to the features provided by Python itself, PySys includes some 
constants to help quickly detect what platform is in use, such as OSFAMILY and 
PLATFORM. It's very common to have one set of logic for Windows and another for 
all non-Windows (Unix-based) platforms, and PySys has a dedicated constant for 
that::

	if IS_WINDOWS:
		...
	else:
		...

Skipping tests
--------------
If your run.py logic detects that a test should not be executed for this 
platform or mode, simply use this near the top of the `execute()` method, 
specifying the reason for the skip::

	self.skipTest('MyFeature is not supported on Windows') 
	
As well as setting the test outcome and reason, this will raise an exception 
ensuring that the rest of `execute()` and `validate()` do not get executed. 

Alternatively if the test should be skipped regardless of platform/mode etc, 
it is best to specify that statically in your `pysystest.xml` file::

	<skipped reason="Skipped until bug #12345 is fixed"/>

Checking for error messages in log files
-----------------------------------------
The `assertGrep()` method is an easy way to check that there are no error 
messages in log files from processes started by PySys. Rather than checking for 
an expression such as `' ERROR: '`, it is recommended to define your expression 
so that the error message itself is included, e.g.::

	self.assertGrep('myprocess.log', expr=' ERROR: .*', contains=False)

This approach ensures that the error message itself is included in the test's 
console output, run.log and the summary of failed test outcomes, which avoids 
the need to open up the individual logs to find out what happened, and makes it 
much easier to triage test failures, especially if several tests fail for the 
same reason. 

Sharing logic for validation across tests
-----------------------------------------
Often you may have some standard logic that needs to be used in the validation 
of many/all testcases, such as checking log files for errors. One recommended 
pattern for this is to define a helper function in a custom `BaseTest` 
subclassed by all your tests that is named after what is being checked - for 
example `checkLogsForErrors()` - and explicitly call that method from 
the `.validate()` method of each test. That approach allows you to later 
customize the logic by changing just one single place, and also to omit it for 
specific tests where it is not wanted. 

Configuring and overriding test options
---------------------------------------
PySys provides two mechanisms for specifying options such as credentials, 
hostnames, or test duration/iteration that you might want to change or 
override when running tests:

- *Testcase attributes*, which are just variables on the Python testcase 
  instance (or a BaseTest subclass shared by many tests). 
  Attributes can be overridden on the command line when executing `pysys run`. 
  
  Attributes are useful for settings specific to an individual testcase such as 
  the number of iterations or time duration to use for a performance test. 
  A user running the test locally you might want to temporarily set to a lower 
  iteration count while getting the test right, or perhaps try 
  a higher value to get a more stable performance result. 
  
- *Project properties*. The default value is specified in the `pysysproject.xml` 
  file or in a `.properties` file. 
  
  Properties can be overridden using an environment variable. 
  Project properties are useful for things like credentials and hostnames that 
  are shared across many testcases, and where you might want to set up 
  customizations in your shell so that you don't need to keep specifying them 
  every time you invoke `pysys run`. 

To use a testcase attribute, set the default value as a Python string on your 
test or basetest before `BaseTest.__init__()` is called. The easiest way to do 
this in an individual testcase is usually to use a static attribute on the test 
class, e.g.::

	class PySysTest(BaseTest):

		myIterationCount = 100*1000 # can be overridden with -XmyIterationCount=
		
		def execute(self):
			self.log.info('Using iterations=%d', self.myIterationCount)
			...

If instead of setting a default for just one test you wish to set the default 
for many tests from your custom BaseTest subclass, then you need to set the 
defaults in your `__init__` before calling the super implementation of `__init__`. 

Once the default value is defined with an attribute, you can override the value 
when you run your test using the `-X` option::

	pysys run -XmyIterationCount=10

If the attribute was defined with a default value of int, float or bool then 
the `-X` value will be automatically converted to that type; otherwise, it will 
be a string. 

The other mechanism that PySys supports for configurable test options is 
project properties. 

To use a project property that can be overridden with an environment variable, 
add a `property` element to your `pysysproject.xml` file::

	<property name="myCredentials" value="${env.MYCOMPANY_CREDENTIALS}" default="testuser:testpassword"/>

This property can will take the value of the specified environment variable, 
or else the default if not set. 

Another way to specify default project property values is to put them into a 
Java-style `.properties` file. You can use properties to specify which file is 
loaded, so it would be possible to customize using environment variables::

	<property name="myProjectPropertiesFile" value="${env.MYCOMPANY_CUSTOM_PROJECT_PROPERTIES}" default="${testRootDir}/default-config.properties"/>
	<property file="${myProjectPropertiesFile}"/>

To use projects properties in your testcase, just access the attributes on 
`self.project` from either a test instance or a runner::

	def execute(self):
		self.log.info('Using username=%s and password %s' % self.project.myCredentials.split(':'))

Property properties will always be of string type. 

Producing code coverage reports
-------------------------------
PySys includes built-in support for producing coverage reports for programs 
written in Python, using the `coverage.py` library. 

If you wish to produce coverage reports using any other tool or language (such 
as Java), this is easy to achieve by following the same pattern:

- When your tests start the program(s) whose coverage is to be measured, 
  add the required arguments or environment variables to enable coverage 
  using the coverage tool of your choice. PySys does this by adding 
  `-m coverage run` to the command line of Python programs 
  started using the `startPython` method (and setting COVERAGE_FILE to a 
  unique filename in the test output directory), when the `pythonCoverage` 
  property is set to true (typically by pysys.py run -X pythonCoverage=true). The 
  `pythonCoverageArgs` project property can be set to provide customized 
  arguments to the coverage tool, such as which files to include/exclude, or 
  a `--rcfile=` specifying a coverage configuration file. 

- Configure your `pysysproject.xml` to collect the coverage files generated in 
  your testcase output directories and put them into a single directory. Add a 
  project property to specify the directory location so it can be located 
  by the code that will generate the report. For Python programs, you'd 
  configure PySys to do it like this::
  
  	<property name="pythonCoverageDir" value="coverage-python-@OUTDIR@"/>
	<collect-test-output pattern=".coverage*" outputDir="${pythonCoverageDir}" outputPattern="@FILENAME@_@TESTID@_@UNIQUE@"/>

  Note that `collect-test-output` will delete the specified outputDir each 
  time PySys runs some tests. If you wish to preserve output from previous 
  runs, you could add a property such as `${startDate}_${startTime}` to the 
  directory name to make it unique each time. 
  
  In addition to any standard ${...} property variables from the project 
  configuration, the output pattern can contain these three `@...@` 
  substitutions which are specific to the collect-test-output `outputPattern`:
  
    - `@FILENAME@` is the original base filename, to which you 
      can add prefixes or suffixes as desired. 

    - `@TESTID@` is replaced by the identifier of the test that generated the 
      output file, which may be useful for tracking where each one came from. 

    - `@UNIQUE@` is replaced by a number that ensures the file does not clash 
      with any other collected output file from another test. The `@UNIQUE@` 
      substitution variable is mandatory. 
    
- Add a custom runner class, and provide a `BaseRunner.processCoverageData()` 
  implementation that combines the coverage files from the directory 
  where they were collected and generates any required reports. The default 
  implementation already does this for Python programs. Note that when reading 
  the property value specifying the output directory any `${...}` 
  property values will be substituted automatically, but any `@...@` values 
  such as `@OUTDIR@` must be replaced manually (since the value of 
  `runner.outsubdir` is not available when the project properties are 
  resolved). 
  
- Add a custom BaseTest class from the `__init__` constructor set 
  `self.disableCoverage=True` for test groups that should not use coverage, 
  such as performance tests. For example::
  
  	 if 'performance' in self.descriptor.groups: self.disableCoverage = True
  
- If using a continuous integration system or centralized code coverage 
  database, you could optionally upload the coverage data there from the 
  directory PySys collected it into, so there is a permanent record of 
  any changes in coverage over time. 

Running tests in multiple modes
-------------------------------
One of the most powerful features of PySys is the ability to run the same test 
in multiple modes from a single execution. This could be useful for cases such 
as a web test that needs to pass against multiple supported web browsers, 
or a set of tests that should be run against various different database but 
can also be run against a mocked database for quick local development. 

Using modes is fairly straightforward. First make sure your project 
configuration includes::

   <property name="supportMultipleModesPerRun" value="true"/>
   
If you created your project using PySys 1.4.1 or later this will already be 
present. Next you should edit the `pysystest.xml` files for tests that 
need to run in multiple modes, and add a list of the supported modes::

   <classification>
	<groups>...</groups>
	<modes inherit="true">
		<mode>MockDatabase</mode>
		<mode>MyDatabase_2.0</mode>
	</modes>
   </classification>

When naming modes, TitleCase is recommended, and dot and underscore characters 
may be used. PySys will give an error if you use different capitalization for 
the same mode in different places, as this would likely result in test bugs. 

The first mode listed is designated the "primary" mode which means it's the 
one that is used by default when running your tests without a `--mode` 
argument. It's best to choose either the fastest mode or else the one that 
is most likely to show up interesting issues as the primary mode. 

In large projects you may wish to configure modes in a `pysysdirconfig.xml` 
file in a parent directory rather than in `pysystest.xml`, which will by 
default be inherited by all nested testcases (unless inherit="false" is 
specified in the `<modes>` element), and so there's a single place to 
edit the modes list if you need to change them later. It's also possible to 
create a custom DescriptorLoader subclass that dynamically adds modes 
from Python code, perhaps based on the groups specified in each descriptor 
or runtime information such as the current operating system.  

In your test case `run.py` (and/or in your test's base class if you have 
customized it) you can use `self.mode` to detect which mode the test is running 
in and alter your behaviour accordingly::

  if self.mode == 'MockDatabase': 
	return MockDB()
  elif self.mode == 'MyDatabase_2.0': 
    return startMyDatabase()
  else: raise Exception('Unknown mode: "%s"'%self.mode)

Finally, PySys provides a rich variety of `pysys run` arguments to control 
which modes your tests will run with. By default it will run every test in its 
primary mode (for tests with no mode, the primary mode is `self.mode==None`) - 
which is great for quick checks during development of your application and 
testcases. 

Your main test run (perhaps in a CI job) probably wants to run tests in all 
modes::

  pysys run --mode ALL --threads auto

You can also specify specifies modes to run in, or to run everything except 
specified modes::

  pysys run --mode MyMode1,MyMode2
  pysys run --mode !MyMode3,!MyMode4

After successfully getting all your tests passing in their primary mode, it could 
be useful to run them in every mode other than the primary one::

  pysys run --mode !PRIMARY

For reporting purposes, all testcases must have a unique id. With a multiple 
mode test this is achieved by having the id automatically include a ~Mode 
suffix. If you are reporting performance results from a multi-mode test, make 
sure you include the mode in the `resultKey`, since the `resultKey` must be 
globally unique. 

In addition to the `--mode` argument which affects all selected tests, it is 
possible to run a specific test in a specific mode. This can be useful when you 
have a few miscellaneous test failures and just want to re-run the failing 
tests::

  pysys run MyTest_001~MockDatabase MyTest_020~MyDatabase_2.0

See sample test Fibonacci_test_005 for an example of using modes for a 
performance test. 

Test ids and structuring large projects
---------------------------------------
Each test has a unique `id` which is used in various places such as when 
reporting passed/failed outcomes. By default the id is just the name of the 
directory containing the `pysystest.xml` file. 

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
large projects it is usually best to add a `pysysdirconfig.xml` file to 
provide default configuration for each directory of testcases. 

For example, in SubSystem1/performance you could create a `pysysdirconfig.xml` 
file containing::

	<?xml version="1.0" encoding="utf-8"?>
	<pysysdirconfig>
	  <id-prefix>SubSystem1_perf.</id-prefix>

	  <classification>
		<groups inherit="true">
		  <group>subsystem1</group>
		  <group>performance</group>
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

- It specifies that the performance tests will be run with a lower priority, 
  so they execute after more urgent (and quicker) tests such as unit tests. 

- It provides the ability to temporarily skip a set of tests if they are 
  broken temporarily pending a bug fix. 

By default both modes and groups are inherited from `pysysdirconfig.xml` files 
in parent directories, but inheriting can be disabled in an individual 
descriptor by setting inherit="false", in case you have a few tests that only 
make sense in one mode. Alternatively, you could allow the tests to exist 
in all modes but call `self.skipTest` at the start of the test `execute` method 
if the test cannot execute in the current mode. 

See the `pysysdirconfig.xml` sample in `pysys-examples/fibonacci/testcases` and 
also in `pysys/xml/templates/dirconfig` for a full example of a directory 
configuration file. 

Controlling execution order
---------------------------
In large projects where the test run takes several hours or days, you may wish 
to control the order that PySys executes different groups of tests - or tests 
with different modes, to maximize the chance of finding out quickly if 
something has gone wrong, and perhaps to prioritize running fast unit and 
correctness tests before commencing on longer running performance or soak tests. 

By default, PySys runs tests based on the sorting them by the full path of 
the `pysystest.xml` files. If you have tests with multiple modes, PySys will 
run all tests in their primary mode first, then any/all tests which list a 
second mode, followed by 3rd, 4th, etc. 

All of this can be customized using the concept of an execution order hint. 
Every test descriptor is assigned an execution order hint, which is a positive
or negative floating point number which defaults to 0.0, and is used to sort 
the descriptors before execution. Higher execution order hints mean later 
execution. If two tests have the same hint, PySys falls back on using the 
path of the `pysystest.xml` file to determine a canonical order. 

The hint for each test is generated by adding together hint components from the 
following:

  - A test-specific hint from the `pysystest.xml` file's 
    `<execution-order hint="..."/>`. If the hint is 
    blank (the default), the test inherits any hint specified in a 
    `pysysdirconfig.xml` file in an ancestor folder, or 0.0 if there aren't 
    any. Note that hints from `pysysdirconfig.xml` files are not added 
    together; instead, the most specific wins. 

  - All <execution-order> elements in the project configuration file which 
    match the mode and/or group of the test. The project configuration 
    is the place to put mode-specific execution order hints, such as putting 
    a particular database or web browser mode earlier/later. See the 
    sample `pysysproject.xml` file for details. 
  
  - For multi-mode tests, the `secondaryModesHintDelta` specified in the project 
    configuration (unless it's set to zero), multiplied by a number indicating 
    which mode this is. If a test had 3 modes Mode1, Mode2 and Mode3 then 
    the primary mode (Mode1) would get no additional hint, Mode2 would get 
    `secondaryModesHintDelta` added to its hint and Mode3 would get
    `2 x secondaryModesHintDelta` added to its hint. This is the mechanism 
    PySys uses to ensure all tests run first in their primary mode before 
    any tests run in their secondary modes. Usually the default value of 
    `secondaryModesHintDelta = +100.0` is useful and avoids the need for too 
    much mode-specific hint configuration (see above). However if you prefer to 
    turn it off to have more manual control - or you prefer each test to run 
    in all modes before moving on to the next test - then simply set 
    `secondaryModesHintDelta` to `0`.

For really advanced cases, you can programmatically set the 
`executionOrderHint` on each descriptor by providing a custom 
`DescriptorLoader` or in the constructor of a custom runner class. 
