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
  
- If using a continuous integration system or centralized code coverage 
  database, you could optionally upload the coverage data there from the 
  directory PySys collected it into, so there is a permanent record of 
  any changes in coverage over time. 

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
		<groups>
		  <group>subsystem1</group>
		  <group>performance</group>
		</groups>

	  </classification>

	  <run-order-priority>-100.0</run-order-priority>

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

See the `pysysdirconfig.xml` sample in `pysys-examples/fibonacci/testcases` and 
also in `pysys/xml/templates/dirconfig` for a full example of a directory 
configuration file. 
