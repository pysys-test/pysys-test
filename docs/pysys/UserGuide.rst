Guides
======

.. py:currentmodule:: pysys.basetest

======
How to
======

Detect the platform
-------------------

It's very common to have one set of logic for Windows and another for 
all non-Windows (Unix-based) platforms, and PySys has a dedicated constant `pysys.constants.IS_WINDOWS` for 
that::

	self.startProcess('myprogram.exe' if IS_WINDOWS else 'myprogram', ...)

For finer grained platform detection we recommend using the facilities built into Python, for example 
``sys.platform``, ``platform.platform()`` or ``platform.uname()``.

Skip tests
----------
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

Check for error messages in log files
-------------------------------------
The `BaseTest.assertGrep` method is an easy way to check that there are no error 
messages in log files from processes started by PySys. Rather than checking for 
an expression such as `' ERROR: '`, it is recommended to define your expression 
so that the error message itself is included, e.g.::

	self.assertGrep('myprocess.log', expr=' ERROR: .*', contains=False)

This approach ensures that the error message itself is included in the test's 
console output, run.log and the summary of failed test outcomes, which avoids 
the need to open up the individual logs to find out what happened, and makes it 
much easier to triage test failures, especially if several tests fail for the 
same reason. 

Create new test templates for pysys make
----------------------------------------
You can define templates that ``pysys make`` will use to create new tests specific to your project, or even multiple 
templates for individual directories within your project. This helps to encourage teams to follow the latest best 
practice by ensuring new tests are copying known good patterns, and also saves looking up how to do common things when 
creating new tests. 

The ``pysys make`` command line comes with a ``pysys-default-test`` template for creating a simple PySys test, you can 
add your own by adding ``<maker-template>`` elements to ``pysysdirconfig.xml`` in any directory under your project, 
or to a ``<pysysdirconfig>`` element in your ``pysysproject.xml`` file. Here are a few examples (taken from 
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
containing ``@@DEFAULT_DESCRIPTOR@@`` (or `@@DEFAULT_DESCRIPTOR_MINIMAL@@`) to include the default PySys descriptor 
values (this means your template will automatically benefit from any future changes to the defaults), and put it in a 
``_pysys_templates/<templatename>`` directory alongside the ``pysystestdir.xml`` file. 
The ``_pysys_templates`` directory should contain a file named ``.pysysignore`` file (which avoids the template being 
loaded as a real test). 

Other options are possible (as above) e.g. copying files from an absolute location such as under your project's 
``${testRootDir}``, copying from PySys default templates directly (if you just want to *add* files) by 
using ``${pysysTemplatesDir}/default-test/*``, or copying from a path relative to the XML file where the template is 
defined containing a real (but simple) test to copy from (with suitable regex replacements to make it more generic). 

See :ref:`pysys/TestDescriptors:Sample pysysdirconfig.xml` for more information about how to configure templates in 
a ``pysysdirconfig.xml`` file. 

When creating tests using ``pysys make``, by default the first template (from the most specific ``pysysdirconfig.xml``) 
is selected, but you can also specify any other template by name using the ``-t`` option, and get a list of available 
templates for the current directory using ``--help``. You can also customize which is the default template for a 
given directory by naming a template defined at a higher level (for example in the project) like this::

	<pysysdirconfig>
		<set-default-maker-template name="my-inherited-test-template"/>
	</pysysdirconfig>

It is possible to subclass the `pysys.launcher.console_make.DefaultTestMaker` responsible for this logic if needed. 
The main reason to do that is to provide a `pysys.launcher.console_make.DefaultTestMaker.validateTestId` method 
to check that new test ids do not conflict with others used by others in a remote version control system (to avoid 
merge conflicts). 

By default PySys creates ``.py`` files with tabs for indentation (as in previous PySys releases). If you prefer spaces, 
just set the ``pythonIndentationSpacesPerTab`` project property to a string containing the required spaces per tab.

=======================
Concepts and techniques
=======================

Sharing logic across tests using helpers
----------------------------------------
Often you will have some standard logic that needs to be used in the execute or validation 
of many/all testcases, such as starting the application you're testing, or checking log files for errors. 

The recommended way to do that in PySys is to create modular, independent helper classes that are included 
in the tests that need them using inheritance (via the "mix-in" pattern). A key constraint 
is that the helper classes themselves contain only a single field holding an instance that encapsulates all the 
real functionality - this avoid name clashes between different helpers, and with the PySys BaseTest class itself. 

The best way to add one is to copy from the **getting-started** sample where there is a ``MyServerHelper`` mix-in class 
that provides a field called ``self.myserver`` through which all of the real functionality is encapsulated and exposed 
to individual tests for reuse. To use it in a test all you need to do is inherit the helper in any tests that need it::

    from myorg.myserverhelper import MyServerHelper
    class PySysTest(MyServerHelper, pysys.basetest.BaseTest):

  	def execute(self):
	  	server = self.myserver.startServer(name="my_server")
      ...

Since this approach uses standard Python, any IDE will be able to give assistance for the myserver methods (provided your extension 
classes are on its configured PYTHONPATH). 
  
Any number of helpers can be added to each test that needs them. Just ensure that the BaseTest class is listed last in the list of 
classes your test inherits from. 

This approach has significant advantages over these alternatives that were used in the past:

- Custom BaseTest subclasses. In this paradigm, PySys methods/fields exist in the same namespace as the custom ones, creating a 
  risk of clashes and unexpected bugs and upgrade pain. Moreover as your project grows you will often end up with multiple 
  BaseTest subclasses for different parts of your testing, and there is a high chance that functionality that seemed to belong 
  in one place will one day be needed in a different sibling BaseTest, leading to a need to refactor or complex multiple 
  inheritance headaches. Using the composition approach of the "helper" classes avoids this complexity and keeps your test 
  extensions nice and clean. 
- Test plugins. These were introduced in older PySys versions to solve the encapsulation problem, but it is now recommended to 
  avoid them because Python IDEs are not able to resolve them, leading to errors or at least a lack of code assistance when 
  interacting with the plugin in your tests. 

Running tests in multiple modes
-------------------------------
One of the powerful features of PySys is the ability to run the same test in multiple modes from a single execution. 
This can be useful for both parameterized tests, where the same Python logic is invoked with multiple different 
parameters to test a range of scenarios, and for running tests against different databases, web browsers etc. 

In PySys, a mode consists of a mode name, and a dictionary of parameters with detailed information about how to 
execute in that mode. The Python test can use ``self.mode.params`` to access the parameter dictionary, and ``self.mode`` 
to get the mode name. 

During test execution, output files are kept separate by having mode executed from a different output directory, 
suffixed by ``~ModeName``. 

When naming modes, TitleCase is recommended, and dot, underscore and equals characters 
may be used. Typically dot is useful for version numbers and underscore ``_`` is 
useful for separating out different dimensions (e.g. compression vs authentication type 
in the example described later in this section). Separating dimensions cleanly in this way will make it 
much easier to include/exclude the test modes you want. PySys will give an error if you use different 
capitalization for the same mode in different places, as this can result in test bugs. 

Using modes for parameterized tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameterized tests provide a convenient way to re-use the same Python logic to check multiple different testing 
scenarios. This avoids the maintenance headache of copy+pasted testcases, and provides faster and more granular test 
outcomes than combining all the different parameters into a single test with a big ``for`` loop. 

To specify modes for a parameterized test, just edit the ``pysystest.*`` file for your test, and 
provide a dictionary of ``ModeName: {ParameterDict}`` like this::

	__pysys_parameterized_test_modes__ = {
			'Usage':        {'cmd': ['--help'], 'expectedExitStatus':'==0'}, 
			'BadPort':      {'cmd': ['--port', '-1'],  'expectedExitStatus':'!=0'}, 
			'MissingPort':  {'cmd': [],  'expectedExitStatus':'!=0'}, 
		}

This produces a test with 3 modes - named ``Usage``, ``BadPort`` and ``MissingPort`` - for the various scenarios 
being checked. As you can see, it is possible to provide both input data, and data for use during validation. 
The test can easily access the parameters using expressions such as ``self.mode.params["cmd"]``. 

It is also possible to provide the exact same configuration using the more advanced ``__pysys_modes__`` field described 
below, however ``__pysys_parameterized_test_modes__`` is easier for this use case, and automatically takes care of 
marking the parameterized modes as "primary" (so they will all run by default even specifying a ``--modes`` argument), 
and combining them with any inherited modes (e.g. for different databases, browsers, etc). 

Using modes for other purposes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Modes can also be used for making your test run with different databases, web browsers, and other execution 
environments. 

Often for these use cases you will want more control than parameterized tests give, for example 
it is likely you'll want to execute with one database/browser in local test runs (probably the fastest one!) so 
you would not want all of them marked as primary modes. Additionally for these use cases the modes are often defined 
at a directory level for a collection of testcases rather in each individual test. You may also need precise control 
over which of the modes from a parent directory are inherited, since some modes may not be applicable to all tests. 

All of these cases and more can be handled by the ``__pysys_modes__`` configuration, which allows you to return a 
Python expression that returns the list (or dict) of modes for each test and/or ``pysysdirconfig``. Since you will 
often need access to the inherited modes and (other useful methods and data) when defining your mode list, 
a ``helper`` object (`pysys.config.descriptor.TestModesConfigHelper`) is made available to your modes expression by the 
use of a Python lambda expression. 

If you want to add some new modes in addition to the inherited ones, you would add this to your ``pysystest.py`` file:

.. code-block:: python
	
	__pysys_modes__ = lambda helper: helper.inheritedModes+[
			{'mode':'CompressionGZip', 'compressionType':'gzip'},
		]

In large projects you may wish to configure modes in a ``pysysdirconfig.xml`` 
file in a parent directory rather than in ``pysystest.*``, which will by 
default be inherited by all nested testcases (unless an explicit modes 
configuration is provided), and so that there's a single place to edit the modes 
list if you need to change them later. 

By default the first mode in each list is "primary", so the test will only run in that one primary mode by 
default during local test runs (i.e. unless you supply a ``--modes`` or ``--ci`` argument). This is optimal when 
using modes to validate the same behaviour/conditions in different execution environments e.g. 
browsers/databases etc (but not for parameterized tests where you usually want to run all of them). It's best to choose 
either the fastest mode or else the one that is most likely to show up interesting issues as the primary mode. 

Sometimes your modes will have multiple dimensions, such as database, web browser, compression type, authentication 
type etc, and you may want your tests to run in all combinations of each item in each dimension list. 
Rather than writing out every combination manually, you can use the helper function 
`pysys.config.descriptor.TestModesConfigHelper.createModeCombinations` to automatically generate the combinations, 
passing it each dimension (e.g. each compression type) as a separate list. 

Here is an example of multi-dimensional modes (taken from the getting-started sample):

.. code-block:: python
	
	__pysys_modes__ = lambda helper: [
			mode for mode in 
				helper.createModeCombinations( # Takes any number of mode lists as arguments and returns a single combined mode list
				
					helper.inheritedModes,
					
					{
							'CompressionNone': {'compressionType':None, 'isPrimary':True}, 
							'CompressionGZip': {'compressionType':'gzip'},
					}, 
					
					[
						{'auth':None}, # Mode name is optional
						{'auth':'OS'}, # In practice auth=OS modes will always be excluded since MyFunkyOS is a fictional OS
					], 
				
			# This is Python list comprehension syntax for filtering the items in the list
			if (mode['auth'] != 'OS' or helper.import_module('sys').platform == 'MyFunkyOS')
		]

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

You can also use Python list comprehensions to generate sets of modes from a ``range`` like this::

	__pysys_modes__   = lambda helper: helper.createModeCombinations(
			helper.inheritedModes, 
			[ {'mode':'CompressionGZip', 'compressionType':'gzip'}, ],
			[ {'serverThreads': t} for t in range(1, 3) ],
		)

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

Executing modes with pysys run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PySys provides a rich variety of ``pysys run`` arguments to control 
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

Performance testing
-------------------
Recording results
~~~~~~~~~~~~~~~~~
PySys is a great tool for running performance tests, whether unit-level microbenchmarks or complex multi-process 
full system benchmarking. 

Often performance tests will produced detailed output files (XML/JSON/PDF/logs etc) that are worth capturing for 
analysis by a human, or for storing as a long term audit of how this build performed. To do this, you can add a 
`pysys.writer.testoutput.CollectTestOutputWriter` to your project configuration. This writer collects files matching a 
specified pattern from the output directory after each test, and puts them in a single directory or archive at the 
end of the test run. 

Whether or not you have some detailed files to stash, it is worth also using `BaseTest.reportPerformanceResult`, the 
powerful built-in capability for storing some summary numbers for each test. In complex tests you probably 
won't want to record every possible statistic - since that can quickly overwhelm once the total number of number of 
tests grows; a better strategy is to select a few representative data points from each test/mode combination. 
By default the numeric results are written to a CSV file (along with the runner's ``runDetails`` dictionary including 
things like OS, CPU count, hostname and git commit of your source changes). There is also a reporter available for 
writing in a simple JSON format, and another that produces a textual summary of the results at the end of the run. 
You can also create your own reporters (e.g. to publish to an in-house database) using the `pysys.perf` API.

The `BaseTest.reportPerformanceResult` documentation gives the details, but one point that's worth stressing is that 
every result should be identified by a short, unique, human-friendly ``resultKey`` which should give an at-a-glance 
definition of what is being recorded such as 
``Message send rate with 3 topics and small 100kB messages using MyMessagingVendor``. 
For maximum benefit, design your keys so that when sorted (imagine a big list of 100+ numbers from all your testcases!) 
you'll see closely related results next to each other. These keys must be unique - so if a test runs in multiple modes 
(e.g. messaging/database vendors) then you must add some kind of string to the result key to indicate which it is 
running in, otherwise PySys will raise an exception and not persist the result. See the samples for some examples of 
using this API. 

Designing performance tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Often a performance test will run for a bit longer than a simple correctness test, for example it might have a set 
number of iterations or time duration. See the above section "Configuring and overriding test options" for an example 
of how to make it easy to customize the iteration count/duration at runtime e.g. ``pysys run -XmyIterationCount=10``. 
You may find you want to run your test super-quick in the early stages until it executes the steps correctly. When 
tracking down performance problems you might want to try running it for longer than usual to get more reliable results. 

It is common to have a single performance test that should run with different parameters, for example against different 
databases, or perhaps with a variety of incoming message sizes. Avoid copy+pasting tests for this use case (which would 
be a maintenance nightmare). It is also a bad idea to add a giant "for" loop into your test and make it do everything in 
one invocation, since then it's very difficult to surgically re-run problematic parts of your parameter matrix when 
tracking down test bugs or optimizing your application. Instead use the built-in "modes" concept of PySys which is 
perfect for the job. It can even generate a combinatoric product of various different parameter dimensions for you 
with `pysys.config.descriptor.TestModesConfigHelper.createModeCombinations` as described above. 

Running performance tests
~~~~~~~~~~~~~~~~~~~~~~~~~
When running performance tests from an automated job, it is important to ensure that you do not have multiple 
tests executing at once since this will usually invalidate the results. It is therefore best to run your performance 
tests in a separate ``pysys run`` invocation to your correctness testing, which does benefit from multi-threaded 
execution. You should ensure code coverage is disabled in a performance run to avoid artificially slowing your components 
down by ensuring the ``disableCoverage`` group is set on all performance tests (but the command line flag can be used 
too just to be safe). So a typical automated performance run would need to modify the usual ``--ci`` default into something like::

	cd performance/
	pysys run --ci --threads=1 -XcodeCoverage=false

When running performance tests locally to investigate a performance bug, it can be incredibly valuable to run 
multiple cycles of each test to generate a more stable baseline, and also to give you a measurable indication of how 
variable your results are. There is no point trying to track down a 10% performance regression from a test whose 
normal variation is +/-50%! It is also worth customizing the ``--outdir`` to assign a human-friendly label each time 
you do a run against a different build of your application. The ``outdir`` is recorded with the performance numbers 
and also allows you to avoid overwriting previous detailed logging output when doing a new run. So a typical local 
execution of a performance test would be::

	pysys run -c5 --outdir=with-foobar-optimization MyTest~MyMode

You may wish to focus on just one mode, or all modes (``--modes=ALL``) or a specific subset of the modes (perhaps 
using a regular expression on the command line to indicate which modes are needed). At the end of the test run PySys 
will print a summary of the results, including a calculation of the sample standard deviation (if ``cycles`` > 1) 
which you can use to check your test is reliable and to decide whether measured increases/decreases are statistically 
significant or just random noise. 

Comparing performance results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When using PySys tests to measure your application while you experiment with possible optimizations, consider 
listing the ``.csv`` (or ``.json``) summary files containing your baselines (e.g. baseline before any changes, with 
optimization A, B, C etc...) in the ``PYSYS_PERFORMANCE_BASELINES`` environment variable. The 
`pysys.perf.reporters.PrintSummaryPerformanceReporter` will print a textual comparison from each of the listed 
baselines to the current result. You can also run comparisons from the command line at any time by running 
the ``pysys/perf/perfreportstool.py`` script. 

When reviewing comparisons, note that some numbers are "better" when large (e.g. rate of sending messages/transactions) 
while others are "worse" when large (e.g. latency or response time). The comparison tries to avoid confusion when 
looking at such results side by side, by showing "+" results for all improvements and "-" when things got worse. 
For each comparison, it prints the %improvement (with a + for bigger-is-better increases and - for reductions, and 
vice-versa), and the speedup ratio (newValue/oldValue for bigger-is-better, or oldValue/newValue for smaller is better). 
Typically the % is useful for small changes (< 100%) whereas the speedup ratio is more friendly for large changes 
(e.g. 3.5x faster). Provided multiple samples are available (from a multi-cycle run), it calculates the standard 
deviation (using whichever is the larger of the old and new stdDevs) and expresses the improvement delta as a ratio of 
the standard deviation (aka "sigma") to give a "sigmas" value which indicates statistically how significant the result 
is - above ``+/- 1 sigma`` means there is a 68% chance the change is a real (significant) one, and above 
``+/- 2 sigmas`` shows a 95% probability of significance. 
Results with less than 2 sigmas are not colour-coded since they typically don't indicate a real change; anything with a 
red or green colour is a regression or improvement that is statistically significant and worth paying attention to. 

Test ids and structuring large projects
---------------------------------------
Firstly, try to have everything in a single PySys project if possible. Use subdirectories to structure your tests, 
but don't separate into different PySys projects unless it's for testing a totally different component with different 
testing needs. Keeping everything in the same project gives you the ability to run all your tests 
(unit/correctness/perf) from a single command line which could be useful in the future even if you don't need it right 
now. 

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

Runner and writer plugins
-------------------------
Plugins can be used to extend PySys with additional capabilities: 

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

For an example of a runner plugin, see the cookbook sample. The configuration looks like this:

With configuration like this::

    <pysysproject>
	    <test-plugin classname="myorg.testplugin.MyTestPlugin" alias="myalias">
			<property name="myPluginProperty" value="my value"/>
	    </test-plugin>
    </pysysproject>

When creating a runner plugin you may need somewhere to put output files, logs etc. Plugins that generate output 
files/directories should by default put that output in a dedicated directory either the 
`runner.output <pysys.baserunner.BaseRunner>` directory, or (for increased prominence if it's something users will 
look at a lot) a directory one level up e.g. ``runner.output+'/../myplugin'`` (which is typically under ``testRootDir`` 
unless an absolute ``--outdir`` path was provided) . 
A prefix of double underscore ``__pysys`` is recommended under testRootDir to distinguish dynamically created 
directories (ignored by version control) from the testcase directories (checked into version control). 

For examples of the project configuration, including how to set plugin-specific properties that will be passed to 
its constructor, see :doc:`/pysys/ProjectConfiguration`. 

(Occasionally some user may wish to add their own custom writer that is not defined in the main ``pysysproject.xml`` file, 
and this can be achieved by putting the additional configuration into a user-specific XML file and setting its path in 
the environment variable ``PYSYS_PROJECT_APPEND``). 


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
As your test suite grows, the ability to run tests in parallel will be increasingly important, so make sure your 
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

- If you want to compare code coverage between branches/commits you will need to ensure the same set of tests is 
  running for both comparison points. So if you have a full test run and a smaller set of unit or smoke tests that 
  execute in pull requests it may be useful to generate two reports - one which includes all tests (for manual 
  reviewing) and another that includes just the tests executed in the unit tests or in pull requests, for automated 
  comparisons and quality gates. 
  This can be achieved by adding an additional coverage writer that will ignore the generated coverage files 
  from the non-unit/smoke tests::
  
  		<property name="includeTestIf">lambda testObj: 
			'unitTest' in testObj.descriptor.groups
			or testObj.project.getProperty('isLocalDeveloperTestRun',False)
		</property>
