Project Configuration
=====================

Each PySys project has a configuration file called ``pysysproject.xml`` at the top level. This file contains 
``property`` elements for any user-defined properties that will be used by your tests such as credentials, server 
names, which are available to your tests using `self.project <pysys.config.project.Project>`. 
The project file also contains allows customization of how PySys executes tests and reports on the results. 

When starting a new PySys test project you should create a minimal project file from scratch using 
``pysys makeproject``, then add any additional elements you require. 

To illustrate the range of available elements, here is a large project file that demonstrates all the main 
functionality.

Header
~~~~~~


.. code-block:: xml

  <?xml version="1.0" encoding="utf-8"?>
  <pysysproject>
  
  	<!-- This is a sample project file (from the "cookbook" sample) with snippets to use in your own project. 
  	
  	Do not copy the whole file; instead, run "pysys makeproject" and then copy in just the bits you need. 
  	-->
  	<!-- Specify a minimum required PySys version to run these tests. Update this each time you upgrade your project 
  	so that everyone gets a clear message if accidentally running tests using an old version. -->
  	<requires-pysys>2.0</requires-pysys>
  
  	<!-- Specify a minimum required python version to run these tests. -->
  	<requires-python>3.6</requires-python>
  
  
Project properties
~~~~~~~~~~~~~~~~~~

The following standard project properties are always defined and can be accessed through ${prop} syntax:

        * ``${testRootDir}`` - Path of the root directory containing the pysysproject.xml file
        * ``${outDirName}``  - The basename (with parent dirs removed) from the outdir for this test run. 
          This may be the name of the current OS or a unique user-specified name for the test run.
        * ``${os}``          - The operating system name e.g. ``windows``, ``linux``, ``darwin``.
        * ``${osfamily}``    - The operating system family, either ``windows`` or ``unix``.
        * ``${startDate}``   - The date that this test run was started, in a form that can be used in filenames. 
        * ``${startTime}``   - The (local) time that this test run was started, in a form that can be used in filenames. 
        * ``${hostname}``    - The (non-qualified) name of the host this is running on, suitable for including in filenames. 
        * ``${username}``    - The (lowercase) username of the account executing PySys. 
        * ``${/}``           - The backslash or forward-slash character used on this OS. 

Python expressions can be evaluated using ``${eval: ...}`` (and can use project properties 
as Python variables, and/or from a dictionary named ``properties``). 

In addition, within this file ``${env:VARNAME}`` (or ``${env.VARNAME}``) syntax can be used to access 
environment variables. 

Project properties can be used as substitution variables within the project file, and 
are set as attributes on the `pysys.config.project.Project` class for use by tests - so in the example below, 
the ``appHome`` property would be available to tests as ``self.project.appHome``

If a property value contains any properties or environment variables that do not exist, 
the ``default`` is used instead (or "" if a default is not explicitly specified). If the default 
also contains undefined properties the project will fail to load. 

The ``pathMustExist=true`` attribute can be used to stop the project loading if the property specifies a  
path that does not exist.

.. code-block:: xml

  	<!-- Property identifying the home directory of the application build being tested. 
  	
  	Binaries and configuration files can be specified relative to this directory 
  	to avoid having to hardcode locations inside each individual testcase. 
  	
  	Tests can be run against a different directory by setting the environment variable PYSYS_APP_HOME. 
  	-->
  	<property name="appHome" value="${env.PYSYS_APP_HOME}" default="${testRootDir}/.." pathMustExist="true"/>
  
  	<!-- This is an example of putting connection credentials into a project property, which can be overridden 
  	using an environment variable if desired. -->
  	<property name="myCredentials" value="${env.MYORG_CREDENTIALS}" default="testuser:testpassword"/>
  
  	<!-- This is an example of using a ${eval: ... } substitution to convert a path into a URL. -->
  	<property name="logConfigURL" value='${eval: "file:///"+os.path.abspath(appHome).replace("\\", "/")+"/logConfig.xml"}'/>
   		
  	<!-- 
  	Import project properties from any file, using the specified prefix for namespacing. 
  	
  	If pathMustExist=true, the project will fail to load if the specified file does not 
  	exist. If pathMustExist=false the project will silently ignore a missing properties file, 
  	which can be useful when using this feature to provide optional user-specific overrides. 
  	
  	The properties file should be of the format name=value (one pair specified per line). 
  	Each imported property line is handled just the same as a standard "property" element, 
  	so for example other project properties can be referenced within the values 
  	using ${...} syntax. 
  	
  	The set of property keys that are imported can be filtered with a regular expression using 
  	the optional includes="regex" and excludes="regex" . 
  	-->
  	<property file="pysys-extensions/myproject-${osfamily}.properties" pathMustExist="true" prefix="os_"
  		includes=".*(Dir|Version)$" excludes=""/>
  		
  
Special project properties
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: xml

  	<!-- If provided, the specified command line will be executed (in testRootDir) to populate the vcsCommit field 
  	in runner.runDetails with the current commit number from your version control system. 
  	-->
  	<property name="versionControlGetCommitCommand" value="git show -s --format=%h"/>
  
  	<!-- 
  	Set default LANG for child processes on Unix (ignored on Windows). 
  	Useful for making all machines behave the same. Ensure that the specified 
  	locale is installed on all machines. 
  	-->
  	<property name="defaultEnvironsDefaultLang" value="en_US.UTF-8"/>
  
  	<!-- 
  	Set environment variables to encourage temporary files from test processes to go to the test output directory 
  	rather than the OS or user's default temporary folder. This ensures tests are truly independent from each other 
  	and from previous runs, and also avoids the danger of disk space being used up by temporary files from test runs. 
  	-->
  	<property name="defaultEnvironsTempDir" value="self.output"/>
  
  	<!-- 
  	The defaultEnvirons. prefix can be used to provide a default environment variable for use by 
  	all processes that PySys starts. For example, to set Java(R)'s JAVA_TOOL_OPTIONS environment variable:
  	-->
  	<property name="defaultEnvirons.JAVA_TOOL_OPTIONS" value="-Xmx512M"/>
  
  	<!-- 
  	If you prefer spaces to tabs in Python source files, set this property to the spaces you want to use for each 
  	string. This affects Python files generated by pysys make. 
  	-->
  	<property name="pythonIndentationSpacesPerTab" value="    "/>
  
  	<!-- 
  	If you prefer a different length or style for the line length marker added under the __pysys_title__ in the 
  	default make test template, specify the string to use here. The following is an example for users who prefer 
  	to encourage a limit of 120 characters for the test title (rather than the default of 80), 
  	-->
  	<property name="pysystestTemplateLineLengthGuide" value="${eval: 120 * '-' }"/>
  
  
Configuring plugins
~~~~~~~~~~~~~~~~~~~

See also :ref:`pysys/UserGuide:Sharing logic across tests using plugins`.
If you want to provide some custom plugins/extensions you need to add them to the PYTHONPATH used by PySys 
as shown below. Usually the specified directory should contain a Python module named after your organization and 
containing an empty __init__.py file to mark it as a Python package (such as ``pysys-extensions/myorg/__init__.py``). 

.. code-block:: xml

  	<pythonpath value="${testRootDir}/pysys-extensions" />
  
  
Test plugins are additional classes instantiated when each test's BaseTest is instantiated, and accessible 
to testcases (using the specified alias) as a field of the BaseTest. They provide a way to expose extra 
functionality for use by your testcases, for example support for additional languages and technologies. 

Each plugin class must provide a ``setup(self, testObj)`` method that accepts the owner testObj (BaseTest instance) 
as a parameter. Any configuration properties are assigned as attributes before setup is called.

Each plugin class must provide a constructor that accepts the parent testObj (BaseTest instance) as a parameter.
The plugin instance is assigned as a field of the test object using the specified "alias" so that its 
methods and fields are available for use. The alias can be any valid Python identifier but must not conflict 
with other plugins or fields that PySys sets on the BaseTest; usually a brief lowercase name 
identifying your organization or the purpose of the plugin is best. 

.. code-block:: xml

  	<test-plugin classname="myorg.mytestplugin.MyTestPlugin" alias="mytestplugin">
  		<!-- <property name="myProp" value="..."/> -->
  	</test-plugin>
  	
  
Runner plugins are classes that are instantiated when the BaseRunner performs its setup() at 
the beginning of a test run. They can provide extra functionality both at the beginning of a test 
run, and also (by calling `addCleanupFunction() <pysys.baserunner.BaseRunner.addCleanupFunction>` from ``setup()``) 
at the end after testing has finished. For example, a runner plugin could be used to add support for starting a 
database server or virtual machine to be shared by all tests.

Each plugin class must provide a ``setup(self, runner)`` method that accepts the owner runner (BaseRunner instance) 
as a parameter. Any configuration properties are assigned as attributes before setup is called.

The plugin instance can optionally be assigned as a field of the runner using the specified "alias" so that its 
methods and fields are available for use by tests. The alias can be any valid Python identifier but must not 
conflict with other plugins or fields that PySys sets on the BaseRunner; usually a brief lowercase name 
identifying your organization or the purpose of the plugin is best. 

.. code-block:: xml

  	<runner-plugin classname="myorg.myrunnerplugin.MyRunnerPlugin" alias="myrunnerplugin">
  		<property name="myPluginProperty" value="true"/>
  	</runner-plugin>
  	
  
For advanced cases it is possible to provide a custom `pysys.baserunner.BaseRunner` subclass. However, in most 
cases this isn't necessary so always consider whether the composition "runner-plugin" approach would do the job 
before using runner inheritance. 

.. code-block:: xml

  	<runner classname="myorg.myrunner.MyRunner"/>
  
  
Use a custom maker class for constructing new testcases. Custom maker classes can extend from the 
`pysys.launcher.console_make.DefaultTestMaker` class in order to customize details such as the automatic 
validation of new test ids. 

.. code-block:: xml

  	<maker classname="myorg.mymaker.MyTestMaker"/>
  
  
Writers
~~~~~~~

Configures the writers that implement reporting of test outcomes, typically to disk, to the console, or 
to a CI system. 

For full details of the configuration properties of each writer, and the API for creating custom writers, 
see `pysys.writer` in the API reference. 

Each writer element specifies the classname (which should be available on the pythonpath).

.. code-block:: xml

  	<writers>
  		<!-- This writer is useful for creating zip archives of failed test output directories when 
  		running in record mode on a machine where it is not otherwise easy to access the output 
  		directories. The destDir could then be uploaded to a CI system (some CI writers 
  		implement this automatically) or manually copied to a file share. 
  		-->
  		<writer classname="pysys.writer.testoutput.TestOutputArchiveWriter">
  			<property name="destDir" value="__pysys_output_archives.${outDirName}/"/>
  			<property name="maxTotalSizeMB" value="1024.0"/>
  			<property name="maxArchiveSizeMB" value="200.0"/>
  			<property name="maxArchives" value="50"/>
  			<property name="archiveAtEndOfRun" value="true"/>
  			<property name="includeNonFailureOutcomes" value="REQUIRES INSPECTION, NOT VERIFIED"/>
  		</writer>
  
  		<!-- This writer is useful for collecting output files (e.g. logs, graphs, etc) from all tests into a 
  		single directory or archive for manual examination at the end of the test run. 
  		-->
  		<writer classname="pysys.writer.testoutput.CollectTestOutputWriter">
  			<property name="destDir" value="__pysys_collect_perf_graphs.${outDirName}/"/>
  			<property name="destArchive" value="perfgraphs.${outDirName}.zip"/>
  
  			<property name="fileIncludesRegex" value=".*[.](svg|pdf)"/>
  			
  			<!-- This causes the archive to be published to any interested writers with the specified category 
  				name (e.g. some CI systems have a mechanism for publishing arifacts) -->
  			<property name="publishArtifactArchiveCategory" value="performanceGraphsArchive"/>
  		</writer>
  		
  		<!-- CI writers automatically enable themselves only if running under 
  		the associated CI environment. 
  		-->
  		<writer classname="pysys.writer.ci.GitHubActionsCIWriter"></writer>
  		<writer classname="pysys.writer.ci.TravisCIWriter"></writer>
  
  		<!--
  		Writes each test outcomes to a separate XML file in the widely-used Apache Ant JUnit XML format.
  		Only enabled when the record flag is specified.
  		-->
  		<writer classname="pysys.writer.outcomes.JUnitXMLResultsWriter">
  			<!-- Use the outputDir property to define the output directory for the JUnit test summary files (the writer will 
  			produce one file per test into this output directory). By default the output directory is located under the 
  			test root dir (or the outdir if specified on the pysys run command).
  			-->
  			<property name="outputDir" value="__pysys_junit_xml"/>
  		</writer>
  
  		<!-- Writes all outcomes to a single XML file; only enabled when the record flag is specified. -->
  		<writer classname="pysys.writer.outcomes.XMLResultsWriter">
  			<!--
  			Set properties on the XML test output writer class. 
  			
  			The filename pattern above is processed through time.strftime so that time information can 
  			be set into the filename, e.g. a filename template of 'testsummary.%Y-%m-%d_%H.%M.%S' will result 
  			in a file created with a name of testsummary_2008-10-25_21.33.08.xml etc.
  			
  			By default the parent directory is the test root dir (or the outdir if specified on the pysys run command).
  			-->
  
  			<property name="file" value="__pysys_testsummary_${outDirName}_%Y-%m-%d_%H.%M.%S.xml"/>
  			
  			<!--  Use file URLs in all references to resources on the local disk. -->
  			<property name="useFileURL" value="true"/>
  		</writer>
  		
  		<!-- Writes all outcomes to a text file; only enabled when the record flag is specified. -->
  		<writer classname="pysys.writer.outcomes.TextResultsWriter">
  			<property name="file" value="__pysys_testsummary_%Y-%m-%d_%H.%M.%S.log"/>
  		</writer>
  
  		<!-- Writes all outcomes to a CSV file; only enabled when the record flag is specified. 
  		The CSV contains id, title, cycle, startTime, duration, outcome. -->
  		<writer classname="pysys.writer.outcomes.CSVResultsWriter">
  			<property name="file" value="__pysys_testsummary_%Y-%m-%d_%H.%M.%S.csv"/>
  		</writer>
  		
  		<!-- Write a code coverage report for .py files; enabled by -XcodeCoverage. -->
  		<writer classname="pysys.writer.coverage.PythonCoverageWriter">
  			<property name="destDir" value="__coverage_python.${outDirName}"/>
  			<property name="destArchive" value="coverage_python.${outDirName}.zip"/>
  			<property name="pythonCoverageArgs" value=""/>
  		</writer>
  
  		<!-- The ConsoleSummaryResultsWriter displays a summary of non-passed outcomes at the end of the test run, 
  		optionally including outcome reason. The ConsoleSummaryResultsWriter is automatically added to the writers 
  		list if no other "summary" writer is explicitly configured.
  		-->		
  		<writer classname="pysys.writer.console.ConsoleSummaryResultsWriter">
  			<property name="showTestTitle" value="true"/>
  		</writer>
  
  		<writer classname="pysys.writer.console.ConsoleProgressResultsWriter">
  		</writer>
  		
  		<!-- Example of a custom writer. -->		
  		<writer classname="myorg.mywriter.MyResultsWriter">
  			<property name="outputFile" value="__pysys_myresults.${outDirName}.json"/>
  		</writer>
  	</writers>
  
  
Configuration for how tests execute
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: xml
  
  	<default-file-encodings>
  		<!-- 
  		Specify the file encoding to be used for reading/writing text files. 
  		
  		The first pattern that matches is used to determine the encoding. The pattern is a glob-style expression to be 
  		matched case-insensitively against either the full path or the basename using Python's fnmatch.fnmatch method. 
  		
  		The defaults specified here can be overridden or added to by the runner or basetest getDefaultFileEncoding() 
  		method. See pysys.process.user.ProcessUser.getDefaultFileEncoding for more details. 
  		
  		-->
  		<default-file-encoding pattern="run.log" encoding="utf-8"/>
  		
  		<default-file-encoding pattern="*.xml" encoding="utf-8"/>
  		<default-file-encoding pattern="*.json" encoding="utf-8"/>
  		<default-file-encoding pattern="*.yaml" encoding="utf-8"/>
  		
  	</default-file-encodings>	
  	
  	<execution-order secondaryModesHintDelta="+100.0">
  		<!-- 
  		The execution-order elements provide a way to globally change the ordering hints specified on individual 
  		tests by adding or subtracting a value from the hints specified on test descriptors in a specified group 
  		and/or mode. For example, set a value less than 0 for performance tests so that they execute towards the 
  		end of the test run rather than beginning.
  		 
  		Groups and modes can be identified with a full name or a regular expression.  
  
  		The secondaryModesHintDelta value is used to order tests so that all tests execute in their primary 
  		mode before any secondary modes are executed. The 2nd mode (the one following the primary mode) has its 
  		execution order hint incremented by secondaryModesHintDelta, the third by 2*secondaryModesHintDelta etc, 
  		which ensures the modes are spaced out. To disable this behaviour and execute all modes of each test 
  		before moving on to the next test set it to 0.0. If not specified, the default value is +100.0.
  		-->
  		
  		<execution-order hint="-20.0" forMode="MyMode_.*"/>
  		<execution-order hint="+10.5" forGroup="performance" forMode="MyMode"/>
  	</execution-order>
  
  
Test descriptor defaults
~~~~~~~~~~~~~~~~~~~~~~~~

A project file can contain a ``pysysdirconfig`` element to configure directory-level defaults that will apply to 
all test descriptors. See the :ref:`pysys/TestDescriptors:Sample pysysdirconfig.xml` documentation for more information about the available options, 
including how to customize how new tests are created using maker templates. 

.. code-block:: xml

  	<pysysdirconfig>
  	
  			<!-- Recommended to specify this for new projects - input files are stored in the testDir alongside pysystest.py -->
  			<input-dir>.</input-dir> 
  
  			<!-- The default for PySys projects created before 2.0 -->
  			<!-- <input-dir>Input</input-dir> -->
  			<!-- Special option that auto-detects based on presence of an Input/ dir; useful for getting the new behaviour 
  				without the need to update or potentially create bugs in existing tests
  			-->
  			<!-- <input-dir>!Input_dir_if_present_else_testDir!</input-dir> -->
  		<!-- Could optionally override the default directory names for reference and output too. The following are the 
  			default values and do not need to be specified explicitly. 
  		-->
  		<output-dir>Output</output-dir>
  		<reference-dir>Reference</reference-dir>
  	</pysysdirconfig>
  
  
PySys run.log and console formatters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In most projects there is no reason to customize this, but it can be used if you real want a different 
log line format (incl date/time format) or console coloring. 

Specify custom formatters for logging to the console or run.log, and/or configure the formatter
appropriately through custom properties. Custom formatters should be defined using the classname
and module attributes and should extend the `pysys.utils.logutils.BaseLogFormatter` class. If no
classname and module is given the default `pysys.utils.logutils.ColorLogFormatter` is assumed.

The ColorLogFormatter allows specification of the message and date strings using the messagefmt and
datafmt attributes. Enabling color to the console (stdout) formatter can be done using the color
property, and the colors for supported message types can be specified via the color:<category> property.
See below for more details for the default color types and categories. Supported colors are BLUE,
GREEN, YELLOW, RED, MAGENTA, CYAN, WHITE and BLACK.

.. code-block:: xml

  	<formatters>
  		<formatter name="stdout" classname="pysys.utils.logutils.ColorLogFormatter" 
  			messagefmt="%(asctime)s %(levelname)-5s %(message)s" datefmt="%H:%M:%S"
  		>
  			<!-- 
  			<property name="color" value="true"/>
  			-->
  			<property name="color:warn" value="MAGENTA"/>
  			<property name="color:error" value="RED"/>
  			<property name="color:traceback" value="RED"/>
  			<property name="color:debug" value="BLUE"/>
  			<property name="color:filecontents" value="BLUE"/>
  			<property name="color:details" value="CYAN"/>
  			<property name="color:outcomereason" value="CYAN"/>
  			<property name="color:progress" value="CYAN"/>
  			<property name="color:performance" value="CYAN"/>
  			<property name="color:timed out" value="MAGENTA"/>
  			<property name="color:failed" value="RED"/>
  			<property name="color:passed" value="GREEN"/>
  			<property name="color:skipped" value="YELLOW"/>
  		</formatter>
  
  		<formatter name="runlog" classname="pysys.utils.logutils.BaseLogFormatter" 
  			messagefmt="%(asctime)s %(levelname)-5s %(message)s" datefmt=""/>
  	</formatters>
  	
  
Project-specific help information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: xml

  	<project-help>
  		<!-- Add project-specific text to be appended to the "pysys run -h". 
  		
  		You can use ${...} project properties, or ${$} to escape the $ character. 
  		
  		-->
  		
  		My project
  		----------
  		   -Xiterations=N   Override the number of request/response iterations performed 
  		                    during execution of each performance test. 
  		   
  		The application being tested is at "${appHome}"; to override use ${$}{PYSYS_APP_HOME}. 
  		
  		Don't forget to execute the MyProject build before running the tests! 
  	</project-help>
  </pysysproject>
  