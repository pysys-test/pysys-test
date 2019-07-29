=========================
PySys 1.5.0 Release Notes
=========================

PySys can be used with Python 3.7/3.6/3.5. PySys also retains compatibility 
with Python 2.7 though users are encouraged to move to Python 3 when possible 
as 2.7 will soon be at the end of its support lifetime. 

See installation notes in README.rst for more details.

--------------------------
What's new in this release
--------------------------

PySys 1.5.0 brings some significant new features for large PySys projects 
including support for running a test in multiple modes, and 
`pysysdirconfig.xml` files that allow you to specify defaults that apply to 
all testcases under a particular directory - such as groups, modes, a prefix 
to add to the start of each test id, and a numeric hint to help define the 
execution order of your tests. 

There is also new support for collecting files from each test output 
directory (e.g. code coverage files), new features in the `pysys run` and 
`pysys print` command lines, and a host of small additions to the API to make 
test creation easier e.g. `assertEval`, `copy` (with filtering of each copied 
line) and `write_text` (for easy programmatic creation of files in the output 
directory). 

This is a major release and therefore there are a few significant changes 
that could required changes in existing projects; please review the 
compatibility section of this document and perform an initial test run using 
the new PySys version to check for issues before switching over. 

Miscellaneous new features
--------------------------

- Added support for running tests in multiple modes from within a single PySys 
  execution. To make use of this, add the following property to your 
  `pysysproject.xml`::
  
	<property name="supportMultipleModesPerRun" value="true"/>

  The old concept of modes within PySys is now deprecated in favour of the 
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
  
     <property name="pythonCoverageDir" value="coverage-python-@OUTDIR@"/>
	 <collect-test-output pattern=".coverage*" outputDir="${pythonCoverageDir}" outputPattern="@FILENAME@_@TESTID@_@UNIQUE@"/>

  The output directory is wiped clean at the start of each test run to prevent 
  unwanted interference between test runs, and is created on demand when the 
  first matching output file is found, so the directory will not be created if 
  there is no matching output. 

- Added support for generating code coverage reports for programs written in 
  Python, using the coverage.py library. To enable this, ensure the coverage 
  library is installed (`pip install coverage`), add collecting of test output 
  files named `.coverage*` to a directory stored in the `pythonCoverageDir` 
  project property (see above example), and run the tests with 
  `-X pythonCoverage=true`. You can optionally set a project property 
  `pythonCoverageArgs` to pass arguments to the coverage tool, such as which 
  modules/files to include or omit. After all tests have been executed, the 
  runner calls a new method `processCoverageData` which combines all the 
  collected coverage files into a single file and produces an HTML report 
  from it, within the pythonCoverageDir directory. If you wish to produce 
  coverage reports using other tools or languages (such as Java), this 
  should be easy to achieve by following the same pattern - using 
  `<collect-test-output>` to gather the coverage files and providing a 
  custom implementation of `BaseRunner.processCoverageData`.  

- Added `BaseTest.assertEval` method which supersedes `assertThat` and provides 
  a convenient way to assert an arbitrary Python expression, with generation of 
  a clear outcome reason that is easy to understand and debug. 

- Added `ProcessUser.copy` method for copying a binary or text file, with 
  optional transformation of the contents by a series of mapping functions. 
  This can be used to extract information of interest from a log file before 
  diff-ing with a reference copy, for example by stripping out timestamps 
  and irrelevant information. 

- Added `ProcessUser.write_text` method for writing characters to a text file 
  in the output directory using a single line of Python. 

- Added `expectedExitStatus` parameter to `ProcessUser.startProcess()` method 
  which can be used to assert that a command returns a non-zero exit code, 
  for example `self.startProcess(..., expectedExitStatus='==5')`. 
  This is simpler and more intuitive than setting `ignoreExitStatus=True` and 
  then checking the exit status separately. 

- Added `quiet` parameter to `ProcessUser.startProcess()` method 
  which disable INFO/WARN level logging (unless a failure outcome is appended), 
  which is useful when calling a process repeatedly to poll for completion of 
  some operation. 

- Added `ProcessUser.startPython` method with similar options to `startProcess` 
  that should be used for starting Python processes. Supports functionality 
  such as Python code coverage. 

- Added `ProcessUser.disableCoverage` attribute which can be used to globally 
  disable all code coverage (in all languages) for a specific test. For example 
  if you apply a group called 'performance' to all performance tests, you could 
  disable coverage for those tests by adding this line to your BaseTest::
  
  	 if 'performance' in self.descriptor.groups: self.disableCoverage = True

- Added `hostname`, `startTime` and `startDate` project properties which can be 
  used in any `pysysproject.xml` configuration file. The start time/date 
  gives the UTC time when the test run began, using the yyyy-mm-dd HH.MM.SS 
  format which is suitable for inclusion in file/directory names. 

- Added `ProcessUser.getBoolProperty()` helper method which provides a simple way to 
  get a True/False value indicating whether a setting is enabled, either 
  directly using a `-X prop=value` argument, or with a property set in the 
  `pysysproject.xml` configuration file.

- Added environment variable `PYSYS_PORTS_FILE` which if present will be read 
  as a UTF-8/ASCII file with one port number on each line, and used to populate 
  the pool of ports for `getNextAvailableTCPPort()`. This can be used to 
  avoid port conflicts when invoking PySys from an environment where some ports 
  are taken up by other processes. 

- Added `TIMEOUTS['WaitForAvailableTCPPort']` which controls how long 
  `getNextAvailableTCPPort()` will wait before throwing an exception. 
  Previously `getNextAvailableTCPPort()` would have thrown an exception if 
  other tests were using up all ports from the available pool; the new 
  behaviour is to block and retry until this timeout is reached.
  
Improvements to the XML descriptors that provide information about tests
------------------------------------------------------------------------

- Added support for disabling search for testcases in part of a directory tree 
  by adding a `.pysysignore` or `pysysignore` file. This is just an empty file 
  that prevents searching inside the directory tree that contains it for tests. 
  This could be useful for reducing time taken to locate testcase and also for 
  avoiding errors if a subdirectory of your PySys project directory contains 
  any non-PySys files with filenames that PySys would normally interpret 
  as a testcase such as `descriptor.xml`. 

- Added a new XML file called `pysysdirconfig.xml` which is similar to 
  `pysystest.xml` and allows setting configuration options that affect all 
  tests under the directory containing the `pysysdirconfig.xml` file.
   
  This allows setting things like groups, test id prefix, execution order, 
  and skipping of tests for a set of related testcases without needing to 
  add the options to each and every individual `pysystest.xml` file. For 
  example, if you have a couple of directories containing performance tests 
  you could add `pysysdirconfig.xml` files to each with a 
  `<group>performance</group>` element so it's easy to include/exclude all 
  your performance when you invoke `pysys.py run`. You could also include 
  a `<execution-order hint="+100"/>` to specify that performance 
  tests should be run after your other tests(the default order hint is 0.0).
  
  The `pysysdirconfig.xml` file can contain any option that's valid in 
  a `pysystest.xml` file except the `description/title/purpose`. a sample 
  `pysysdirconfig.xml` file is provided in 
  `pysys-examples/fibonacci/testcases` and also in 
  `pysys/xml/templates/dirconfig`. 
  
  See the PySys user guide for more information. 

- Added support for specifying a prefix that will be added to start of the 
  testcase directory name to form the testcase identifier. This can be 
  specified in `pysystest.xml` testcase descriptor files and/or in 
  directory-level `pysysdirconfig.xml` files like this:

    <id-prefix>MyComponent.Performance.</id-prefix>

  Large test projects may benefit from setting prefixes in `pysysdirconfig.xml` 
  files to provide automatic namespacing of testcases, ensuring there are no name 
  clashes across different test directories, and providing a way to group 
  together related test ids without the need to use very long names for 
  each individual testcase directory. Prefixes can be specified cumulatively, 
  so with the final testcase id generated from adding the prefix from each 
  parent directory, finishing with the name of the testcase directory itself. 
  
  We recommend using an underscore or dot character for separating test 
  prefixes. 

- Added support for specifying the order in which testcases are run. To do 
  this, specify a floating point value in any `pysystest.xml` testcase 
  descriptor, or `pysysdirconfig.xml` descriptor (which provides a default for 
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

  Although tests can still be skipped by setting the `state="skipped"` 
  attribute, the use of the `skipped` element is recommended as it provides a 
  way to specify the reason the test has been skipped, and also allows a 
  whole directory of tests to be skipped by adding the element to a 
  `pysysdirconfig.xml` file. The default `pysystest.xml` template generated 
  for new testcases now contains a commented-out `skipped` element instead of 
  a `state=` attribute. 

- Added a new API for overriding the way test descriptors are loaded from a 
  directory on the file system. This allows for programmatic customization 
  of descriptor settings such as the supported modes for each testcase, and 
  also provides a way to make PySys capable of finding and running non-PySys 
  tests (by programmatically creating PySys TestDescriptor objects for them).
  See the `pysys.xml.descriptor.DescriptorLoader` class for more details. 

Improvements to the `pysys.py` command line tool
------------------------------------------------

- Added support for running tests by specifying just a (non-numeric) suffix 
  without needing to include the entire id. Although support for specifying a 
  pure numeric suffix (e.g. `pysys.py run 10`) has been around for a long time, 
  you can now do the same with strings such as `pysys.py run foo_10`. 

- Added `--sort` option to `pysys.py print`. This allows sorting by `title` 
  which is very helpful for displaying related testcases together (especially 
  if the titles are written carefully with common information at the beginning 
  of each one) and therefore for more easily locating testcases of interest. 
  It can also sort by `id` or `executionOrderHint` which indicates the order 
  in which the testcases will be executed. The default sort order if none of 
  these options is specified continues to be based on the full path of the 
  `pysystest.xml` files. 

- Added `--grep`/`-G` filtering option to `pysys.py print` and `pysys.py run` 
  which selects testcases that have the specific regular expression (matched 
  case insensitively) in their `id` or `title`. This can be a convenient way 
  to quickly run a set of tests related to a particular feature area.  

- Added a concise summary of the test ids for any non-passes in a format that's 
  easy to copy and paste into a new command, such as for re-running the failed 
  tests. This can be disabled using the `ConsoleSummaryResultsWriter` property 
  `showTestIdList` if desired. 

- Added an environment variable PYSYS_DEFAULT_THREADS which can be used to set 
  the number of threads to use with `--threads auto` is specified on a 
  per-machine or per-user basis. 

- Added the ability to set logging verbosity for specific `pysys.*` categories 
  individually using `-vCAT=LEVEL`. For example to enable just DEBUG logging 
  related to process starting, use `-vprocess=DEBUG`. Detailed DEBUG logging 
  related to assertions including the processed version of the input files uses 
  the category "assertions" and is no longer included by default when the 
  root log level is specified using `-vDEBUG` since it tends to be excessively 
  verbose and slow to generate; if required, it can be enabled using 
  `-vassertions=DEBUG`.

- Argument parsing now permits mixing of `-OPTION` and non-option (e.g. test 
  id) arguments, rather than requiring that the test ids be specified 
  only at the end of the command line. For example::
  
    pysys run --threads auto MyTest_001 -vDEBUG

- Added automatic conversion of strings specified on the command line with 
  `-Xkey=value` to int, float or bool if there's a static variable of the 
  same name and one of those types defined on the test class. This makes it 
  easier to write tests that have their parameters overridden from the command 
  line. For example, if a test class has a static variable `iterations=1000` 
  to control how many iterations it performs, it can be run with 
  `pysys run -Xiterations=10` during test development to override the number 
  of iterations to a much lower number without any changes to `run.py`. 

- Added `--json` output mode to `pysys.py print` which dumps full information 
  about the available tests in JSON format suitable for reading in from other 
  programs. 

- Changed `makeproject` so that when a template is to be specified, it is now 
  necessary to use an explicit `--template` argument, e.g `--template=NAME`. 

Bug fixes
---------

- PySys now uses `Test outcome reason:` rather than `Test failure reason:` 
  to display the outcome, since there is sometimes a reason for non-failure 
  outcomes such as SKIPPED. 

- Fixed `--purge` to delete files in nested subdirectories of the output 
  directory not just direct children of the output directory. 

- Previous versions of PySys did not complain if you created multiple tests 
  with the same id (in different parent directories under the same project). 
  This was dangerous as the results would overwrite each other, so in this 
  version PySys checks for this condition and will terminate with an error 
  if it is detected. If you intentionally have multiple tests with the same 
  name in different directories, add an `<id-prefix>` element to the 
  `pysystest.xml` or (better) to a `pysysdirconfig.xml` file to provide 
  separate namespaces for the tests in each directory and avoid colliding ids. 

- The Ant JUnit writer now includes the test duration. 

- Improved `assertGrep` outcome reason to include the entire matching string 
  when a `contains=False` test fails since `ERROR - The bad thing happened` is 
  a much more useful outcome reason than just `ERROR`. 

- Fixed CSV performance reporter runDetails which was including each item 
  twice. 

Upgrade guide and compatibility
-------------------------------
Occasionally it is necessary for a new PySys release to include changes that 
might change or break the behaviour of existing test suites. As 1.5.0 is a 
major release it is possible that some users might need to make changes:

- Errors and typos in `pysystest.xml` XML descriptors will now prevent any tests 
  from running, whereas previously they would just be logged. Since an invalid 
  descriptor prevents the associated testcase from reporting a result, the 
  new behaviour ensures such mistakes will be spotted and fixed promptly. 
  If you have any non-PySys files under your PySys project root directory 
  with names such as `descriptor.xml` which PySys would normally recognise 
  as testcases, you can avoid errors by adding a `.pysysignore` file to prevent 
  PySys looking in that part of the directory tree. 
  
- `ProcessUser.mkdir` now returns the absolute path (including the output 
  directory) instead of just the relative path passed in. This make it easier 
  to use in-line while performing operations such as creating a file in the 
  new directory. Code that relied on the old behaviour of returning the 
  path passed in may need to be updated to avoid having the output directory 
  specified twice. If you're using `os.path.join` then no change will be 
  required. 

- The `self.output` variable in `BaseRunner` is no longer set to the current 
  directory, but instead to a `pysys-runner-OUTDIR` subdirectory of the 
  test root (or to `OUTDIR/pysys-runner` if `OUTDIR` is an absolute path). 
  This ensures that any files created by the runner go into a known location 
  that is isolated from other runs using a different `OUTDIR`. The runner's 
  `self.output` directory is often not actually used for anything since 
  most logic that writes output files lives in `BaseTest` subclasses, so 
  most users won't be affected. For the same reason, the runner output 
  directory is not created (or cleaned) automatically. 
  If you have a custom `BaseRunner` that writes files to its output directory 
  then you should add a call to `self.deleteDir` and then `self.mkdir` to 
  clean previous output and then create the new output directory.

- The behaviour of `ProcessUser.getDefaultEnvirons` has changed compared to 
  PySys 1.4.0, but only when the command being launched is `sys.executable`, 
  i.e. another instance of the current Python process (`getDefaultEnvirons` is 
  used by `startProcess` when `environs=` is not explicitly provided). 
  
  In 1.4.0 the returned environment always set the `PYTHONHOME` environment 
  variable, and on Windows would add a copy of the `PATH` environment from the 
  parent process. In PySys 1.5.0 this is no longer the case, as the 1.4.0 
  behaviour was found to cause subtle problems when running from a virtualenv 
  installation or when the child Python itself launches another Python process 
  of a different version. The new behaviour is that `getDefaultEnvirons` adds 
  the directory containing the Python executable to `PATH` (on all OSes), and 
  copies the `LD_LIBRARY_PATH` from the parent process only on Unix (where it 
  is necessary to reliably load the required libraries). `getDefaultEnvirons` 
  no longer sets the `PYTHONHOME` environment variable. 

- On Windows, paths within the testcase are now normalized so that the drive 
  letter is always capitalized (e.g. `C:` not `c:`). Previously the 
  capitalization of the drive letter would vary depending on how exactly PySys 
  was launched, which could occasionally lead to inconsistent behaviour if 
  testing an application that relies on the ASCII sort order of paths. 

- The format of `pysys print` has changed to use a `|` character instead of a 
  colon to separate the test id and titles. This makes it easier to copy and 
  paste test ids from `pysys print` into the command line. 

- Several fields in the `TestDescriptor` (aka `XMLDescriptorContainer`) class 
  that used to contain absolute paths now contain paths relative to 
  the newly introduced `testDir` member. These are: `module`, `output`, 
  `input`, `reference`. The values of `BaseTest.output/input/reference` 
  have not changed (these are still absolute paths), so this change is unlikely 
  to affect many users. 

- The `PROJECT` variable in the `constants` module is deprecated. Use 
  `self.project` instead (which is defined on classes such as `BaseTest`, 
  `BaseRunner` etc). 

---------------
Release History
---------------

1.3.0 to 1.4.0
--------------

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

- Added support for running PySys tests under Travis CI to the sample 
  `pysysproject.xml` file. Travis support includes by default only printing 
  `run.log` output for failed tests, and containing that detailed output within 
  a folded section that can be expanded if needed. To enable this just ensure 
  that the Travis CI writer is enabled in your project configuration file, 
  which you can copy from the sample project configuration file if you already 
  have an existing project file. 

- Added support for configuring the default encodings to use for common file 
  patterns in the `pysysproject.xml` configuration, e.g. ::
  
	<default-file-encoding pattern="*.yaml" encoding="utf-8"/>. 

  The `pysys-examples/pysysproject.xml` sample project configuration file now 
  sets utf-8 as the default encoding for XML, json and yaml files, and also 
  for testcase run.log files (though run.log continues to be written in local 
  encoding unless the project file is updated). For more information on this 
  feature, see comments in `pysysproject.xml` and in 
  `ProcessUser.getDefaultFileEncoding()`.

- Use of `print()` rather than self.log is a common mistake that results in 
  essential diagnostic information showing up on the console but not 
  stored in `run.log`. A new project option `redirectPrintToLogger` 
  can optionally be enabled to instruct PySys to catch output written using 
  `print()` statements or to `sys.stdout` and redirect it to the logging 
  framework, so it will show up in `run.log`. Writers that genuinely need 
  the ability to write directly to stdout should be changed to use 
  `pysys.utils.logutils.stdoutPrint`. 

- There are new settings for customizing the default environment used by 
  `startProcess`::

	<property name="defaultEnvironsDefaultLang" value="en_US.UTF-8"/>
	<property name="defaultEnvironsTempDir" value="self.output'"/>  

  See `ProcessUser.getDefaultEnvirons()` for more information on these. 

Main API improvements:

- Added `ProcessUser.skipTest()` method, which can be used to avoid running the 
  rest of the `execute()` or `validate()` method, if it is not appropriate for 
  the test to execute on this platform/mode. 

- Added boolean `IS_WINDOWS` constant, since conditionalizing logic for Windows 
  versus all other Operating Systems is very common; this avoids the need for 
  error-prone matching against string literals. 

- Added `ProcessUser.startProcess()` argument `stdouterr` which allows 
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

- Added `ProcessUser.getDefaultEnvirons()` method which is now used by 
  `startProcess()` to provide a minimal but clean set of environment variables 
  for launching a given process, and can also be used as a basis for creating 
  customized environments using the new `createEnvirons()` helper method. 
  There are some new project properties to control how this works, which 
  you may wish to consider using for new projects, but are not enabled by 
  default in existing projects to maintain compatibility::
  
	<property name="defaultEnvironsDefaultLang" value="en_US.UTF-8"/>
	<property name="defaultEnvironsTempDir" value="self.output'"/>  

  See `ProcessUser.getDefaultEnvirons()` for more information on these. 
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

- Added `ProcessUser.compareVersions()` static helper method for 
  comparing two alphanumeric dotted version strings. 

- Added `ProcessUser.deletedir` which is more convenient that the associated 
  `fileutils.deletedir` for paths under the `self.output` directory. 

- Added `ProcessUser.addOutcome(override=...)` argument which can be used to 
  specify a new test outcome that replaces any existing outcomes even if 
  they have a higher precedence. 

- Added `ignores=` argument to `ProcessUser.waitForSignal()` method which 
  excludes lines matching the specified expression from matching both the 
  main `expr` match expression and any `errorExpr` expressions. 

- Added `fileutils.toLongPathSafe/fromLongPathSafe` which on Windows performs 
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

- The environment `startProcess` uses by default if no `environs=` 
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
  See the pysysproject.xml file in pysys-examples for more details.
- It is now possible to specify a regex for matching in the test selection.
  See the run usage for more details (pysys.py run -h).


0.9.3 to 1.1.0
--------------
- This release introduces optional fail fast semantics at a macro and micro
  level. At a macro level this is either through the "defaultAbortOnError"
  project property, or through the "-b|--abort" option to the pysys launcher
  run task. See the pysysproject.xml file in pysys-examples, and the run task
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
