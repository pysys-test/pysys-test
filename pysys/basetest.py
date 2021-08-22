#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import os.path, time, threading, logging
import inspect
import difflib

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filegrep import filegrep, getmatches
from pysys.utils.filegrep import lastgrep
from pysys.utils.filediff import filediff
from pysys.utils.filegrep import orderedgrep
from pysys.utils.linecount import linecount
from pysys.utils.threadutils import BackgroundThread
from pysys.utils.logutils import BaseLogFormatter
from pysys.process.monitor import ProcessMonitorTextFileHandler
from pysys.process.monitorimpl import DEFAULT_PROCESS_MONITOR
from pysys.manual.ui import ManualTester
from pysys.process.user import ProcessUser
from pysys.utils.pycompat import *
from pysys.utils.fileutils import pathexists
import pysys.utils.safeeval

# be sure to import all utility modules that we want to be available to tests that do an "import pysys" (e.g. pysys.mappers.XXX)
import pysys.mappers

class BaseTest(ProcessUser):
	"""BaseTest is the base class of every individual PySys test class, and contains the methods needed to execute your 
	test logic and then to validate the results against the expected behaviour. 
	
	Apart from the `addOutcome` method this class is not thread-safe, so if 
	you need to access it from multiple threads be sure to add your own locking 
	around use of its fields and methods, including any cleanup functions. 
	"""
	
	def __init__ (self, descriptor, outsubdir, runner):
		ProcessUser.__init__(self)
		self.descriptor = descriptor
		self.input = os.path.join(descriptor.testDir, 
			(
				'Input' if os.path.exists(os.path.join(descriptor.testDir, 'Input')) else '.'
			) if descriptor.input=='!Input_dir_if_present_else_testDir!' else descriptor.input
			).rstrip('/\\.') # strip /. suffix if input is ''

		self.output = os.path.join(descriptor.testDir, descriptor.output, outsubdir).rstrip('/\\.')
		self.reference = os.path.join(descriptor.testDir, descriptor.reference).rstrip('/\\.')
		self.runner = runner
		self.mode = descriptor.mode
		# NB: we don't set self.mode.params as keyword arguments since it'd be easy to overwrite a class/instance 
		# variable unintentionally with unpredictable results; accessing explicitly with self.mode is fine 
		self.setKeywordArgs(self.descriptor.userData)
		self.setKeywordArgs(runner.xargs)
		self.monitorList = []
		self.__backgroundThreads = []
		self.manualTester = None
		self.resources = []
		self.testCycle = getattr(BaseTest, '_currentTestCycle', None) # set when constructed by runner
		
		if 'disableCoverage' in descriptor.groups: 
			self.disableCoverage = True
			self.log.debug('Disabling coverage for this test due to disableCoverage group')
		
		self.__assertDetailLogger = logging.getLogger('pysys.assertions.diffs')
		
	def __str__(self): 
		""" Returns a human-readable and unique string representation of this test object containing the descriptor id 
		and a suffix indicating the cycle number if this is a multi-cycle test run. 
		
		This is suitable for diagnostic purposes and display to the test author. The format of this string may 
		change without notice. 
		"""
		return ('%s.cycle%03d'%(self.descriptor.id, self.testCycle)) if self. testCycle else self.descriptor.id
			
	# test methods for execution, validation and cleanup. The execute method is
	# abstract and must be implemented by a subclass. 
	def setup(self):
		"""
		Contains setup actions to be executed before the test is executed. 
		
		The ``setup`` method may be overridden by individual test classes, or (more commonly) in a custom `BaseTest` 
		subclass that provides common functionality for multiple individual tests. However before implementing a custom 
		``BaseTest`` subclass with its own ``setup()`` method, consider whether the PySys concept of test plugins would meet 
		your needs. 
		
		If you do override this method, be sure to call ``super(BASETEST_CLASS_HERE, self).setup()`` to allow the 
		setup commands from the base test to run. 
		
		If ``setup`` throws an exception, the `cleanup` method will still be called, to clean up any resources 
		that were already allocated.
		
		"""
		pass		


	def execute(self):
		"""The method tests implement to perform the test execution steps. 
		
		:raises NotImplementedError: If this method was not implemented yet. 
		"""
		raise NotImplementedError("The execute method of the BaseTest class must be implemented in a subclass")


	def validate(self):
		"""The method tests implement to perform assertions that check for the expected behaviour. 
		
		In some cases all of the required assertions (e.g. checking that a process ran without error etc) will have 
		been performed in the `execute` method and so `validate` will be empty. However, where possible it is 
		recommended to put assertions into the ``validate`` method for clarity, and so that the 
		``pysys run --validateOnly`` option can be used during test development. 
		
		"""
		pass


	def cleanup(self):
		"""
		Contains cleanup actions to be executed after the test's `execute` and `validate` methods have completed. 
		
		The cleanup method automatically stops all processes that are still still running (assuming they were started 
		with `startProcess`). It also stops all process monitors running in 
		separate threads, and any instances of the manual tester user interface.
		
		If any custom cleanup is required, use `addCleanupFunction` instead of overriding
		this method.
				
		"""
		try:
			if self.manualTester and self.manualTester.running():
				self.stopManualTester()

			# first request them all to stop
			# although we don't yet state this method is thread-safe, make it 
			# as thread-safe as possible by using swap operations
			with self.lock:
				threads, self.__backgroundThreads = list(self.__backgroundThreads), []
			for th in threads: th.stop()
			for th in threads: th.join(abortOnError=False)

			# this should be a no-op since the background threads will have been stopped and joined above
			for monitor in self.monitorList:
				if monitor.running(): monitor.stop()
		
			while len(self.resources) > 0:
				self.resources.pop()
		finally:
			ProcessUser.cleanup(self)


	def addResource(self, resource):
		"""Add a resource which is owned by the test and therefore gets its ``__del__`` method called 
		when the test is cleaned up. 
		
		:deprecated: Please use `addCleanupFunction` instead of this function. 
		"""
		self.resources.append(resource)


	def startProcessMonitor(self, process, interval=5, file=None, handlers=[], **pmargs):
		"""Start a background thread to monitor process statistics such as memory and CPU usage.
		
		All process monitors are automatically stopped on completion of 
		the test by L{BaseTest.cleanup}, but you may also wish to explicitly stop 
		your process monitors by calling `pysys.process.monitor.BaseProcessMonitor.stop` before you begin 
		shutting down processes at the end of a test to avoid unwanted spikes 
		and noise in the last few samples of the data. 
		
		You can specify a `file` and/or a list of `handlers`. If you use 
		`file`, a default `pysys.process.monitor.ProcessMonitorTextFileHandler`
		instance is created to produce tab-delimited lines with default columns 
		specified by 
		`pysys.process.monitor.ProcessMonitorTextFileHandler.DEFAULT_COLUMNS`. 
		If you wish to customize this for an individual test create your own 
		``ProcessMonitorTextFileHandler`` instance and pass it to handlers instead. 
		Additional default columns may be added in future releases. 
		
		:param process: The process handle returned from the L{startProcess} method.
		
		:param interval: The polling interval in seconds between collection of 
			monitoring statistics. 
		
		:param file: The name of a tab separated values (.tsv) file to write to, 
			for example 'monitor-myprocess.tsv'. 
			
			A default L{pysys.process.monitor.ProcessMonitorTextFileHandler} instance is 
			created if this parameter is specified, with default columns from 
			L{pysys.process.monitor.ProcessMonitorTextFileHandler.DEFAULT_COLUMNS}. 
		
		:param handlers: A list of L{pysys.process.monitor.BaseProcessMonitorHandler} 
			instances (such as L{pysys.process.monitor.ProcessMonitorTextFileHandler}), 
			which will process monitoring data every polling interval. This can be 
			used for recording results (for example in a file) or for dynamically 
			analysing them and reporting problems. 
		
		:param pmargs: Keyword arguments to allow advanced parameterization 
			of the process monitor class, which will be passed to its 
			constructor. It is an error to specify any parameters 
			not supported by the process monitor class on each platform. 
				
		:return: An object representing the process monitor 
			(L{pysys.process.monitor.BaseProcessMonitor}).
		:rtype: pysys.process.monitor.BaseProcessMonitor
		
		"""
		if isstring(file): file = os.path.join(self.output, file)
		handlers = [] if handlers is None else list(handlers)
		if file:
			handlers.append(ProcessMonitorTextFileHandler(file))
		
		self.log.debug("Starting process monitor for %r", process)
		monitor = DEFAULT_PROCESS_MONITOR(owner=self, process=process, interval=interval, handlers=handlers, **pmargs).start()
		assert hasattr(monitor, '_getData'), 'Start did not return a process monitor instance'
		self.monitorList.append(monitor)
		return monitor

	
	def stopProcessMonitor(self, monitor):
		"""Request a process monitor to stop.

		This method is deprecated - just call `pysys.process.monitor.BaseProcessMonitor.stop` directly instead. 
		
		Waits for the monitor to fully stop if possible, but does not throw an exception if it fails. 

		All process monitors are automatically stopped and joined during cleanup, 
		however you may wish to explicitly stop your process monitors 
		before you begin shutting down processes at the end of a test to avoid 
		unwanted spikes and noise in the last few samples of the data. 
		
		:param monitor: The process monitor handle returned from the L{startProcessMonitor} method
		
		"""
		monitor.stop()

	def startBackgroundThread(self, name, target, kwargsForTarget={}):
		"""
		Start a new background thread that will invoke the specified `target` 
		function. 
		
		The target function will be invoked with the specified keyword 
		arguments, preceded by the special keyword arguments `stopping` and `log`. 
		The `stopping` argument is a Python C{threading.Event} instance that 
		can be used to detect when the thread has been requested to terminate. 
		It is recommended to use this event instead of C{time.sleep} to avoid 
		waiting when the thread is meant to be finishing. 
		
		Example usage::
		
			class PySysTest(BaseTest):
				def dosomething(self, stopping, log, param1, pollingInterval):
					log.debug('Message from my thread')
					while not stopping.is_set():
		
						# ... do stuff here
		
						# sleep for pollingInterval, waking up if requested to stop; 
						# (hint: ensure this wait time is small to retain 
						# responsiveness to Ctrl+C interrupts)
						if stopping.wait(pollingInterval): return
		
				def execute(self):
					t = self.startBackgroundThread('DoSomething1', self.dosomething, {'param1':True, 'pollingInterval':1.0})
					...
					t.stop() # requests thread to stop but doesn't wait for it to stop
					t.join()
		
		Note that C{BaseTest} is not thread-safe (apart from C{addOutcome}, 
		C{startProcess} and the reading of fields like ``self.output`` that don't 
		change) so if you need to use its fields or methods from 
		background threads, be sure to add your own locking to the foreground 
		and background threads in your test, including any custom cleanup 
		functions. 
		
		The BaseTest will stop and join all running background threads at the 
		beginning of cleanup. If a thread doesn't stop within the expected 
		timeout period a L{constants.TIMEDOUT} outcome will be appended. 
		If a thread's ``target`` function raises an Exception then a 
		L{constants.BLOCKED} outcome will be appended during cleanup or 
		when it is joined. 
		
		:param name: A name for this thread that concisely describes its purpose. 
			Should be unique within this test/owner instance. 
			A prefix indicating the test/owner will be added to the provided name. 
		
		:param target: The function or instance method that will be executed 
			on the background thread. The function must accept a keyword argument 
			named `stopping` in addition to whichever keyword arguments are 
			specified in `kwargsForTarget`. 
		
		:param kwargsForTarget: A dictionary of keyword arguments that will be 
			passed to the target function. 
		
		:return: A L{pysys.utils.threadutils.BackgroundThread} instance 
			wrapping the newly started thread. 
		:rtype: L{pysys.utils.threadutils.BackgroundThread}
		
		"""
		t = BackgroundThread(self, name=name, target=target, kwargsForTarget=kwargsForTarget)
		t.thread.start()
		with self.lock:
			self.__backgroundThreads.append(t)
		return t

	# methods to control the manual tester user interface
	def startManualTester(self, file, filedir=None, state=FOREGROUND, timeout=TIMEOUTS['ManualTester']): # pragma: no cover
		"""Start the manual tester, which provides a UI to guide a human through the tests needed to implement this testcase.
		
		The manual tester user interface (UI) is used to describe a series of manual steps to be performed 
		to execute and validate a test. Only a single instance of the UI can be running at any given time, and 
		can be run either in the C{FOREGROUND} (method will not return until the UI is closed or the timeout
		occurs) or in the C{BACKGROUND} (method will return straight away so automated actions may be performed 
		concurrently). Should the UI be terminated due to expiry of the timeout, a C{TIMEDOUT} outcome will be 
		added to the outcome list. The UI can be stopped via the L{stopManualTester} method. An instance of the 
		UI not explicitly stopped within a test will automatically be stopped via the L{cleanup} method of the 
		BaseTest.
		
		:param file: The name of the manual test xml input file
		:param filedir: The directory containing the manual test xml input file (defaults to the output subdirectory)
		:param state: Start the manual tester either in the C{FOREGROUND} or C{BACKGROUND} (defaults to C{FOREGROUND})
		:param timeout: The timeout period after which to termintate a manual tester running in the C{FOREGROUND}
		
		"""
		if filedir is None: filedir = self.input
	
		if not self.manualTester or self.manualTester.running() == 0:
			self.manualTester = ManualTester(self, os.path.join(filedir, file))
			t = threading.Thread(target=self.manualTester.start, name=self.__class__.__name__+'.manualtester')
			t.start()
		
			if state == FOREGROUND:
				startTime = time.time()
				while self.manualTester.running() == 1:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						self.addOutcome(TIMEDOUT, 'Manual tester timed out')
						self.manualTester.stop()
						return
					self.pollWait(1)
			else:
				self.pollWait(1)
		else:
			self.addOutcome(BLOCKED, 'Manual tester failed')


	def stopManualTester(self):  # pragma: no cover
		"""Stop the manual tester if running.
		
		"""
		if self.manualTester and self.manualTester.running():
			self.manualTester.stop()
			self.pollWait(1)
		else:
			self.addOutcome(BLOCKED, 'Manual tester could not be stopped')


	def waitManualTester(self, timeout=TIMEOUTS['ManualTester']):  # pragma: no cover
		"""Wait for the manual tester to be stopped via user interaction.
		
		"""
		if self.manualTester and self.manualTester.running():
			startTime = time.time()
			while self.manualTester.running() == 1:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					self.addOutcome(TIMEDOUT, 'Timed out waiting for manual tester')
					self.manualTester.stop()
					return
				self.pollWait(1)


	# test timing methods. These allow control flow of the test to be set
	# on various conditions i.e. a socket becoming available for connections,
	# a file to exist etc
	def wait(self, interval):
		"""Wait for a specified period of time, and log a message to indicate this is happening.
		
		Tests that rely on waiting for arbitrary times usually take longer to execute than necessary, and are fragile 
		if the timings or machine load changes, so wherever possible use a method like `waitForGrep` to 
		wait for something specific instead. 
		
		See also `pollWait` which should be used when performing repeated polling to wait for a condition without logging. 
		
		:param interval: The time interval in seconds to wait. 
		
		"""
		log.info('Waiting for %0.1f seconds'%interval)
		self.pollWait(interval)


	# test validation methods.
	
	def assertPathExists(self, path, exists=True, abortOnError=False):
		"""Perform a validation that the specified file or directory path exists 
		(or does not exist). 
		
		:param path: The path to be checked. This can be an absolute path or 
			relative to the testcase output directory.

		:param exists: True if the path is asserted to exist, False if it 
			should not. 
		
		:param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 
		
		:return: True if the assertion succeeds, False if a failure outcome was appended. 
		"""
		result = PASSED if pathexists(os.path.join(self.output, path))==exists else FAILED
		self.addOutcome(result, 
			'Assertion that path exists=%s for "%s"'%(exists, os.path.normpath(path)), 
			abortOnError=abortOnError)
		return result

	def assertEval(self, evalstring, abortOnError=False, **formatparams):
		"""Perform a validation by substituting named ``{}`` placeholder values into a Python expression such as 
		``{expected}=={actual}`` or ``4 <= {actual} <= 10``. 
		
		:deprecated::
			Deprecated since 1.5.1 in favour of `assertThat` which is now significantly more powerful and should be 
			used for new tests. 
		
		Example use::
		
			self.assertEval('os.path.getsize({filename}) > {origFileSize}', 	
				filename=self.output+'/file.txt', origFileSize=1000)
		
		:param evalstring: a string that will be formatted using ``.format(...)``
			with the specified parameters, and result in failure outcome if not true. 
			
			Parameters should be specified using {name} syntax, and quoting is not 
			required as string values are automatically escaped using repr. 
			e.g. '`os.path.size({filename}) > {origFileSize}'`. 
			
			Do not use an f-string instead of explicitly passing formatparams, as 
			with an f-string this method will not know the names of the substituted 
			parameters which makes the intention of the assertion harder to 
			understand from looking at the test output. 
		
			The global environment used for evaluation includes the ``os.path``, ``math``, ``sys``, ``re``, ``json``, and ``locale`` 
			standard Python modules, as well as the ``pysys`` module and the contents of the `pysys.constants` module, 
			e.g. ``IS_WINDOWS``, and also the BaseTest's ``self`` variable. 
	
		:param formatparams: Named parameters for the format string, which 
			can be of any type. Use descriptive names for the parameters to produce 
			an assertion message that makes it really clear what is being checked. 
			
			String parameters will be automatically passed through `repr()` before 
			being formatted, so there is no need to perform additional 
			quoting or escaping of strings. 
		
		:param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. Unless abortOnError=True this method only throws 
			an exception if the format string is invalid; failure to execute the 
			eval(...) results in a BLOCKED outcome but no exception. 

		:return: True if the assertion succeeds, False if a failure outcome was appended. 

		"""
		formatparams = {k: (repr(v) if isstring(v) else v) for (k,v) in formatparams.items()}
		toeval = evalstring.format(**formatparams)
		
		display = 'with: %s'%', '.join(['%s=%s'%(k, 
			# avoid excessively long messages by removing self.output (slightly complicated by the fact we called repr recently above)
			str(formatparams[k]).replace(self.output.replace('\\','\\\\'), '<outputdir>') 
			) for k in sorted(formatparams.keys())])
		try:
			result = bool(pysys.utils.safeeval.safeEval(toeval, extraNamespace={'self':self}))
		except Exception as e: # the exception already contains everything it needs
			self.addOutcome(BLOCKED, str(e), abortOnError=abortOnError)
			return False
		
		if result:
			self.addOutcome(PASSED, 'Assertion %s passed %s'%(evalstring, display))
			return True
		else:
			self.addOutcome(FAILED, 'Assertion %s failed %s'%(evalstring, display), abortOnError=abortOnError)
			return False
			
	def assertThat(self, conditionstring, *positional_arguments, **kwargs):
		r"""Performs equality/range tests or any general-purpose validation by evaluating a Python ``eval()`` expression 
		in the context of some named values. 
		
		This method is designed to produce very clear and informative logging and failure reasons if the assertion is 
		unsuccessful (using the `logValueDiff` method). 
		
		Example usage::
		
			# Equality comparison of an 'actual' vs 'expected' message from when our server started; 
			# note the use of a descriptive name for the 'actualXXX=' keyword to produce a nice clear message if it fails
			self.assertThat("actualStartupMessage == expected", expected='Started successfully', actualStartupMessage=msg)
			
			# This produces the self-describing log messages like: 
			#   Assert that (actualStartupMessage == expected) with expected='Started successfully', actualStartupMessage='Started unsuccessfully' ... passed

			# Always design tests to give clear messages if there's a failure. Here's an example of adding an extra 
			# parameter (fromLogFile) that's not used in the condition string, to indicate which server we're testing here
			self.assertThat('actualUser == expected', expected='myuser', actualUser=user, fromLogFile='server1.log')

			# Any valid Python expression is permitted (not only equality testing):
			self.assertThat("actualStartupMessage.endswith('successfully')", actualStartupMessage=msg)
			self.assertThat("re.match(expected, actualStartupMessage)", expected=".* successfully", actualStartupMessage=msg)
			self.assertThat("(0 <= actualValue < max) and type(actualValue)!=float", actualValue=v, max=100)

			# Use ``is`` for comparisons to True/False/None as in Python ``==``/``!=`` don't always do what you'd 
			# expect for these types. 
			self.assertThat("actualValue is not None", actualValue=v)
			
		This method is powerful enough for almost any validation that the other assert methods don't 
		handle, and by enforcing the discipline of naming values it generates self-describing log messages and 
		outcome reasons to make it really obvious what is going on.
		For best results, make sure that your keyword= parameters have clear and unique names so it's obvious 
		how each assertThat() differs from the other ones, and ensure that all values you're going to want to see 
		are included as one of the named parameter values (rather than buried deep inside the main conditionstring). 
		
		The condition string is just a Python expression, which will be passed to ``eval()`` and can use any 
		of the ``keyword=`` argument values passed to this method (but not the caller's local variables).
		The evaluation is performed in a namespace that also includes the current `BaseTest` instance (``self``), 
		some standard Python modules (``os.path``, ``math``, ``sys``, ``re``, ``json``, and ``locale``), the `pysys` module, and 
		the contents of the `pysys.constants` module, e.g. ``IS_WINDOWS``. If necessary, symbols for additional modules 
		can be imported dynamically using ``import_module()``. For example::

			self.assertThat("IS_WINDOWS or re.match(expected, actual)", actual="foo", expected="f.*")
			self.assertThat("import_module('tarfile').is_tarfile(self.output+file) is False", file='/foo.zip')
		
		Sometimes the differences between assertThat expressions are hard to describe in the parameter names themselves, 
		and for these cases you can get self-describing behaviour with a parameter ending in the suffix 
		``__eval`` whose value is itself a Python expression to be evaluated, using any local variable in the 
		namespace of the calling code, for example::
		
			myDataStructure = ...
			self.assertThat("actual == expected", actual__eval="myDataStructure['item1'][-1].getId()", expected="foo")
			self.assertThat("actual == expected", actual__eval="myDataStructure['item2'][-1].getId()", expected="bar")
			self.assertThat("actual == expected", actual__eval="myDataStructure['item3'][-1].getId()", expected="baz")

			# Produces self-describing log messages like this:
			#  Assert that (actual == expected) with actual (myDataStructure['item1'][-1].getId()) ='foo', expected='foo' ... passed
			#  Assert that (actual == expected) with actual (myDataStructure['item2'][-1].getId()) ='bar', expected='bar' ... passed
			#  Assert that (actual == expected) with actual (myDataStructure['item3'][-1].getId()) ='baZaar', expected='baz' ... failed
			#       actual: 'baZaar'
			#     expected: 'baz'
			#                 ^
		
		As shown above, when (at least) two named parameters are provided and the condition string is a simple 
		comparison using exactly two of the parameters, additional lines are logged if the 
		assertion fails, showing at what point the two arguments differ (based on finding the longest common substring). 
		So it's a good idea to include both the actual and expected value as named parameters rather than as literals 
		inside the condition string. 
		
		.. versionchanged:: 1.5.1
			The ability to pass named keyword= parameters was added in 1.5.1 
			(prior to that this method was deprecated).
		
		:param str conditionstring: A string containing Python code that will be evaluated using ``eval()`` 
			as a boolean expression, for example ``actualXXX == expected``, where XXX is a brief description of 
			what value is being tested. 
			
			It's best to put expected values into a separate named parameter (rather than using literals inside the 
			conditionstring), since this will produce more informative messages if there is a failure. 
			
			Do not be tempted to use a Python f-string here, as that would deprive PySys of the 
			opportunity to provide a self-describing message and outcome reason. 
		
		:param \**kwargs: All additional keyword arguments are treated as values which will be made available 
			when evaluating the condition string. Any keyword ending in the special suffix ``__eval`` will be treated 
			as a Python expression string (rather than a string literal) and will be be evaluated in a namespace 
			containing the local variables of the calling code and (on Python 3.6+) any preceding named parameters.  

		:param \*positional_arguments: (deprecated) Unnamed positional arguments will be 
			substituted into the condition string using the old ``%`` format string mechanism, before it is evaluated. 
			This feature is deprecated as it provides poor diagnostic information, requires string parameters to be 
			explicitly escaped using ``repr()``, and only permits stringifiable 
			data structures to be used by the conditionstring. Instead use named ``keyword=`` in all new tests. 
		
		:param abortOnError=False: Set to True to make the test immediately abort if the
			assertion fails. By default this method produces a BLOCKED output 
			but does not throw if the eval(...) cannot be executed. 

		:param assertMessage='': Overrides the string used to describe this 
			assertion in log messages and the outcome reason. We do not recommend using this as the automatically 
			generated assertion message is usually clearer. If you want to add some additional information to 
			that message (e.g. which file/server it pertains to etc), just add the info as a string with an extra 
			keyword argument. 
		
		:return: True if the assertion succeeds, False if a failure outcome was appended (and abortOnError=False). 
		"""
		abortOnError = kwargs.pop('abortOnError',False)
		assertMessage = kwargs.pop('assertMessage',None)
		namedvalues = {}
		displayvalues = []
		
		EVAL_SUFFIX = '__eval'
		for k,v in kwargs.items():
			if k.endswith(EVAL_SUFFIX):
				k = k[:-len(EVAL_SUFFIX)] # strip the suffix
				displayvalues.append(u'%s (%s) '%(k, v))
				try:
					# evaluate in the namespace of the parent (which includes basetest)
					namespace = dict(inspect.currentframe().f_back.f_locals)
					if sys.version_info[0:2] >= (3, 6): # only do this if we have ordered kwargs, else it'd be non-deterministic
						namespace.update(namedvalues) # also add in any named values we already have
					v = pysys.utils.safeeval.safeEval(v, extraNamespace=namespace, errorMessage='Failed to evaluate named parameter %s=(%s): {error}'%(k+EVAL_SUFFIX, v))
				except Exception as ex:
					self.addOutcome(BLOCKED, '%s'%ex, abortOnError=abortOnError)
					return False
			else:
				displayvalues.append(k)
				
			if '__' in k: raise Exception('Please do not use __ in any for keywords, this is reserved for future use')

			# use quotestring which uses repr() for escaping only if we need it; other data structures are best using normal str()
			
			displayvalues[-1]+= (u'=%s'%quotestring(v) if isstring(v) else (u'=%s'%(v,)))
			namedvalues[k] = v

		if positional_arguments: # yucky old-style mechanism
			try:
				conditionstring = conditionstring % positional_arguments
			except Exception as e:
				self.addOutcome(BLOCKED, 'Failed to substitute unnamed/positional arguments into %r using %% operator; this feature is deprecated, please use named arguments instead, e.g. assertThat("...", expected=..., actual=...)'%conditionstring, abortOnError=abortOnError)
				return False
		
		displayvalues = ' with '+', '.join(displayvalues) if displayvalues else ''
		try:
			namespace = dict(namedvalues)
			namespace['self'] = self
			result = bool(pysys.utils.safeeval.safeEval(conditionstring, extraNamespace=namespace, errorMessage='Failed to evaluate (%s)%s - {error}'%(conditionstring, displayvalues)))

		except Exception as e:
			self.addOutcome(BLOCKED, str(e), abortOnError=abortOnError)
			return False
		
		assertMessage = assertMessage or ('Assert that (%s)%s'%(conditionstring, displayvalues))
		
		if result:
			self.addOutcome(PASSED, assertMessage)
			return True
		else:
			self.addOutcome(FAILED, assertMessage, abortOnError=abortOnError)
			
			# namesInUse impl is a bit rough-and-ready, but does a good enough job at identifying when it makes 
			# sense to compare two of the parameters passed in
			namesInUse = [x for x in namedvalues.keys() if x in conditionstring]
			if (re.match(r'^ *\w+ *(==|is|>=|<=|in) *\w+ *$', conditionstring) or 
				re.match(r'^ *\w+[.](startswith|endswith)[(] *\w+ *[)] *$', conditionstring)) and len(namesInUse)==2: 
				# if we're checking a==b we can help the user see why they didn't match; 
				# this kind of highlighting might be misleading for other conditionstrings, and certainly less useful

				self.logValueDiff(**{
					namesInUse[0]:namedvalues[namesInUse[0]],
					namesInUse[1]:namedvalues[namesInUse[1]],
				})

			return False

	def logValueDiff(self, actual=None, expected=None, logFunction=None, **namedvalues):
		"""Logs the differences between two values in a human-friendly way, on multiple lines (as displayed by `assertThat`). 
		
		Special handling is provided for common types such as strings, lists and dicts (note that this isn't intended 
		for use with data structures whose string representation is too big to display on the console). 
	
		:param obj actual: The actual value. 
			Alternatively, this parameter can be ignored and a value with a different key provided as a keyword argument instead. 
		:param obj expected: The baseline/expected value from which a diff will be computed to the actual value. 
			Alternatively, this parameter can be ignored and a value with a different key provided as a keyword argument instead. 
			
		:param function logFunction: By default each line is logged at INFO level using ``log.info()``, but an alternative 
			log function with the same signature can be provided if desired. 
		"""
		if logFunction is None: logFunction = self.__assertDetailLogger.info
		
		if len(namedvalues) < 2:
			# adding actual before expected to the dict gives the right ordering for the diff later on
			if actual is not None: namedvalues['actual'] = actual
			if expected is not None: namedvalues['expected'] = expected
		assert len(namedvalues)==2, 'Expecting 2 keyword args but got: %s'%namedvalues.keys()
		
		namesInUse = list(namedvalues.keys())
		pad = max(len(key) for key in namesInUse)+1
		
		v1, v2 = namedvalues[namesInUse[0]], namedvalues[namesInUse[1]]

		def tostringlist(x):
			if isinstance(x, dict): 
				# if they're dictionaries, convert to lists since otherwise the random ordering of the keys could mess up the comparisons
				return [u'%s=%s'%(k, quotestring(v)) for (k,v) in sorted(x.items())]
			return [quotestring(v) for v in x]

		if len(str(v1)+str(v2)) > 100 and isinstance(v1, (list,dict)) and isinstance(v2, (list,dict)) and min(len(v1), len(v2))>1 and tostringlist(v1)!=tostringlist(v2):
			# For list/dict data structures (unless of trivial size) it's clearer to display using a line-by-line diff approach

			v1, v2 = tostringlist(v1), tostringlist(v2)
				
			def logDiffLine(line):
				if line.startswith('-'): extra = BaseLogFormatter.tag(LOG_DIFF_REMOVED)
				elif line.startswith('+'): extra = BaseLogFormatter.tag(LOG_DIFF_ADDED)
				elif line.startswith('?'): extra, line = BaseLogFormatter.tag(LOG_FAILURES), ' '+line[1:] # e.g. ++++/---- pointers
				else: extra = BaseLogFormatter.tag(LOG_FILE_CONTENTS)
				logFunction(u'  %s', line.rstrip('\r\n'), extra=extra)
			
			# nb: since usually expected comes after actual, show actual (v1) as the delta from v2 (expected)
			for line in difflib.ndiff(v2, v1, charjunk=None):
				logDiffLine(line)
					
		else: 
			# compare stringified values
			
			# use %s for most objects, but repr for strings (so we see the escaping) and objects where str() would make them look the same
			v1 = u'%s'%(v1,)
			v2 = u'%s'%(v2,)

			if isstring(namedvalues[namesInUse[0]]) and ( # for strings do minimal escaping, but only if we can do it consistently for both strings
					('\\' in repr(namedvalues[namesInUse[0]]).replace('\\\\','')) == 
					('\\' in repr(namedvalues[namesInUse[1]]).replace('\\\\','')) ):
				v1 = quotestring(namedvalues[namesInUse[0]])
				v2 = quotestring(namedvalues[namesInUse[1]])
			elif v1==v2 or isstring(namedvalues[namesInUse[0]]):
				v1 = u'%r'%(namedvalues[namesInUse[0]],)
				v2 = u'%r'%(namedvalues[namesInUse[1]],)
			
			seq = difflib.SequenceMatcher(None, v1, v2, autojunk=False)
			
			matches = seq.get_matching_blocks()
			lastmatch = matches[-1] if len(matches)==2 else matches[-2] # may be of zero size
			
			# Find values of ijk such that vN[iN:jN] is a matching prefix and vN[kN:] is a matching suffix
			# Colouring will be red, white(first match, if any), red, white(last match, if any)
			ijk = []
			for v in [0,1]:
				ijk.append([
					matches[0][v], # i - start of first matching block
					matches[0][v]+matches[0].size, # j - end of first matching block
					lastmatch[v] + (0 if lastmatch.size+lastmatch[v] == len([v1,v2][v]) else lastmatch.size) # k - start of final matching block
				])
			i1, j1, k1 = ijk[0]
			i2, j2, k2 = ijk[1]
			
			# for some cases such as "XXXyyyXXX", "ZZZyyyZZZ" the above gives only the quotes as matching which is useless, so 
			# heuristically we'll do better with a longest substring match; compare number of matching chars to decide
			longestblock = seq.find_longest_match(0, len(v1), 0, len(v2))
			if (j1-i1) + (len(v1)-k1) < longestblock.size:
				log.debug('Using longest match %s rather than block matching %s', longestblock, matches)
				ijk = [
					# v1 ijk
					[longestblock.a, longestblock.a+longestblock.size, len(v1)],
					#v2
					[longestblock.b, longestblock.b+longestblock.size, len(v2)],
				]
				

			for (index, key) in enumerate(namesInUse):
				value = [v1,v2][index]
				i, j, k = ijk[index]
				#self.logFunction(u'  %{pad}s: %s__%s__%s__%s'.format(pad=pad), key, 
				logFunction(u'  %{pad}s: %s%s%s%s'.format(pad=pad), key, 
					value[:i], value[i:j], value[j:k], value[k:], # red - i:white (common prefix) - j:red - k:white (common suffix)
					extra=BaseLogFormatter.tag(LOG_FAILURES, arg_index=[1,3]))
			if j1==j2: # if there's a common prefix, show where it ends
				logFunction(u'  %{pad}s %s ^'.format(pad=pad), '', ' '*j1, extra=BaseLogFormatter.tag(LOG_FAILURES))

	def assertTrue(self, expr, abortOnError=False, assertMessage=None):
		"""Perform a validation assert on the supplied expression evaluating to true.
		
		:deprecated: Use `assertThat` instead of this method, which produces 
			clearer messages if the assertion fails. 
		
		If the supplied expression evaluates to true a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to false, a C{FAILED} outcome is added.
		
		:param expr: The expression, as a boolean, to check for the True | False value
		
		:param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 
		
		:param assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. 

		:return: True if the assertion succeeds, False if a failure outcome was appended. 
		"""
		msg = assertMessage or 'Assertion on boolean expression equal to true'
		if expr == True:
			self.addOutcome(PASSED, msg)
		else:
			self.addOutcome(FAILED, msg, abortOnError=abortOnError)
		return expr==True
	

	def assertFalse(self, expr, abortOnError=False, assertMessage=None):
		"""Perform a validation assert on the supplied expression evaluating to false.
		
		:deprecated: Use `assertThat` instead of this method, which produces 
			clearer messages if the assertion fails. 
		
		If the supplied expression evaluates to false a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to true, a C{FAILED} outcome is added.
		
		:param expr: The expression to check for the true | false value
		
		:param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 	
		
		:param assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. 

		:return: True if the assertion succeeds, False if a failure outcome was appended. 
		"""
		msg = assertMessage or 'Assertion on boolean expression equal to false'
		if expr == False:
			self.addOutcome(PASSED, msg)
		else:
			self.addOutcome(FAILED, msg, abortOnError=abortOnError)
		return expr==False

	def assertDiff(self, file1, file2=None, filedir1=None, filedir2=None, ignores=[], sort=False, replace=[], includes=[], encoding=None, 
			abortOnError=False, assertMessage=None, stripWhitespace=None):
		"""Perform a validation by comparing the contents of two text files, typically a file from the 
		output directory against a file in the ``<testdir>/Reference/`` directory containing the expected output.

		Differences in line ending are always ignored, and depending on the value of ``stripWhitespace`` leading 
		and trailing whitespace may also be ignored. 
		
		The files can be pre-processed prior to the comparison to either ignore particular lines, 
		sort their constituent lines, replace matches to regular 
		expressions in a line with an alternate value, or to only include particular lines. 
		However, it is often easier to instead use 
		`copy` to perform the transformations (e.g. stripping out timestamps, finding lines of interest etc)
		and then separately call assertDiff on the file generated by copy. This makes it easier to generate a suitable 
		reference file and to diagnose test failures. For example::
		
			self.assertDiff(self.copy('myfile.txt', 'myfile-processed.txt', mappers=[RegexReplace(RegexReplace.DATETIME_REGEX, '<timestamp>')])))
		
		The above example shows a very compact form of assertDiff, which uses the fact that copy() returns 
		the path of the destination file, and that there is no need to specify assertDiff's file2 (reference) 
		parameter if it's the same basename as the first argument (just located in a different directory). In practice 
		it's very convenient to use the same basename for both the reference file and the output file it's compared to. 
		
		Should the files after pre-processing be equivalent a C{PASSED} outcome is added to the test outcome list, 
		otherwise a C{FAILED} outcome is added.
		
		If you have any serialized dictionary/map data structures in the comparison files, or any lists that come from 
		a directory listing, be really careful to ensure there is deterministic sorting of the keys/filenames, as 
		by default the ordering is often subject to unpredictable changes when upgrading tools or switching between 
		OSes, and you don't want to have to update lots of testcases every time the sorting changes. If you are able 
		to get the data into a Python data structure (e.g. by serializing from JSON), 
		Python's ``json.dump(..., sort_keys=True)`` can be a convenient way to produce a predictable order for 
		dictionary keys.
		
		If you have a large set of test reference files which need to be updated after a behaviour or output formatting 
		change, you can use a special command line option which makes ``assertDiff`` overwrite the reference files with 
		a copy of the actual comparison file in cases where the diff would otherwise fail. 
		Use this feature with caution, since it overwrites reference files with no backup. In 
		particular, make sure you have committed all reference files to version control before running the command, and 
		the afterwards be sure to carefully check the resulting diff to make sure the changes were as expected before 
		committing. To use 
		this feature, run::
		
			pysys.py run -XautoUpdateAssertDiffReferences
		
		:param str file1: The actual (or first) file to be compared; can be an absolute path or relative to the test output directory. 
		:param str file2: The expected/reference (or second) file to be compared; can be an absolute path or relative to the Reference directory.
			The default is for file2 to be the same basename as file1 (but located in the Reference/ directory). 
		:param str filedir1: The dirname of the first file (defaults to the testcase output subdirectory)
		:param str filedir2: The dirname of the second file (defaults to the testcase reference directory)
		:param list[str] ignores: A list of regular expressions used to denote lines in the files which should be ignored
		:param bool sort: Boolean flag to indicate if the lines in the files should be sorted prior to the comparison
		:param list[(regexp:str,repl:str),...]replace: List of tuples of the form ('regexpr', 'replacement'). For each regular expression in the 
			list, any occurences in the files are replaced with the replacement value prior to the comparison being 
			carried out. This is often useful to replace timestamps in logfiles etc.
		:param bool stripWhitespace: If True, every line has leading and trailing whitespace stripped before comparison, 
			which means indentation differences and whether the file ends with a blank line do not affect the outcome. 
			If the value is ``None``, delegates to the value of the project property ``defaultAssertDiffStripWhitespace`` 
			(which is True for old projects, but recommended to be False for new projects). 
		:param list[str] includes: A list of regular expressions used to denote lines in the files which should be used in the 
			comparison. Only lines which match an expression in the list are used for the comparison.
		:param str encoding: The encoding to use to open the file. 
			The default value is None which indicates that the decision will be delegated 
			to the L{getDefaultFileEncoding()} method. 
		
		:param bool abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 
		
		:param str assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. 
			
		:return: True if the assertion succeeds, False if a failure outcome was appended. 
		"""
		if filedir1 is None: filedir1 = self.output
		if filedir2 is None: filedir2 = self.reference
		
		if not file2:
			if os.path.isabs(file1): 
				file2 = os.path.basename(file1)
			else:
				file2 = file1
		
		f1 = os.path.join(filedir1, file1)
		f2 = os.path.join(filedir2, file2)

		log.debug("Performing file comparison diff with file1=%s and file2=%s", f1, f2)
		
		if stripWhitespace is None: stripWhitespace = self.getBoolProperty('defaultAssertDiffStripWhitespace', default=False)
		
		msg = assertMessage or ('File comparison between %s and %s'%(
			self.__stripTestDirPrefix(f1), self.__stripTestDirPrefix(f2)))
		unifiedDiffOutput=os.path.join(self.output, os.path.basename(f1)+'.diff')
		result = False
		
		def logDiffLine(line):
			if line.startswith('-'): extra = BaseLogFormatter.tag(LOG_DIFF_REMOVED)
			elif line.startswith('+'): extra = BaseLogFormatter.tag(LOG_DIFF_ADDED)
			else: extra = BaseLogFormatter.tag(LOG_FILE_CONTENTS)
			self.__assertDetailLogger.info(u'  %s', line, extra=extra)

		try:
			for i in [0, 1]:
				result = filediff(f1, f2, 
					ignores, sort, replace, includes, unifiedDiffOutput=unifiedDiffOutput, encoding=encoding or self.getDefaultFileEncoding(f1), 
					stripWhitespace=stripWhitespace)
				
				if (not result) and self.getBoolProperty('autoUpdateAssertDiffReferences'):
					self.logFileContents(unifiedDiffOutput, encoding=encoding or self.getDefaultFileEncoding(f1), logFunction=logDiffLine)
					log.warning('... -XautoUpdateAssertDiffReferences option is enabled, so overwriting reference file %s and retrying ... '%f2)
					self.copy(f1, f2)
					continue

				break
		except Exception:
			log.warning("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
			return False
		else:
			result = PASSED if result else FAILED
			try:
				self.addOutcome(result, msg, abortOnError=abortOnError)
			finally:
				if result != PASSED:
					self.logFileContents(unifiedDiffOutput, encoding=encoding or self.getDefaultFileEncoding(f1), logFunction=logDiffLine)
			return result

	def __stripTestDirPrefix(self, path):
		"""Normalize the specified path then strip off any self.output (or failing that prefix. 
		This is preferable to using os.path.basename to shorten paths we display in outcome reasons, since it 
		retains path information that might be useful when triaging results. Also if a full path is specified, 
		it will be passed through unchanged. 
		"""
		if not path: return path
		path = os.path.normpath(path)
		return path.split(self.output+os.sep, 1)[-1].split(self.descriptor.testDir+os.sep, 1)[-1]

	def assertThatGrep(self, file, grepRegex, conditionstring='value == expected', encoding=None, reFlags=0, mappers=[], **kwargsForAssertThat):
		r"""Perform a validation by using a regular expression to extract a "value" from a text file and then check 
		the extracted value using an `assertThat` conditionstring.

		For example::
		
			# This is the typical case - "value" is assigned to the first (...) regex group, and keyword parameters 
			# (e.g. "expected=") are used to validate that the "value" is correct
			self.assertThatGrep('myserver.log', r'Successfully authenticated user "([^"]*)"', 
				"value == expected", expected='myuser')
			
			# In cases where you need multiple regex groups for matching purpose, name the one containing the value using (?P<value>...)
			self.assertThatGrep('myserver.log', r'Successfully authenticated user "([^"]*)" in (?P<value>[^ ]+) seconds', 
				"0.0 <= float(value) <= 60.0")

		This method is implemented using `grep` and `assertThat`, so see those methods for more detailed 
		information on the parameters. 

		.. versionadded:: 1.6.0

		:param file: The name or relative/absolute path of the file to be searched.
		
		:param str grepRegex: The regular expression to use for extracting the value of interest from the file. 
			Typically this will use a ``(...)`` regular expression group to identify the part of the expression 
			containing the value; alternatively a single ``(?P<value>...)`` named group may be used. 
		
		:param str conditionstring: A string containing Python code that will be evaluated using ``eval()`` 
			to validate that "value" is correct. For example ``value == expected``.
			
			It's best to put expected values into a separate named parameter (rather than using literals inside the 
			conditionstring), since this will produce more informative messages if there is a failure. 
			
			Do not be tempted to use a Python f-string here, as that would deprive PySys of the 
			opportunity to provide a self-describing message and outcome reason. 

		:param List[callable[str]->str] mappers: A list of filter functions that will be used to pre-process each 
			line from the file (returning None if the line is to be filtered out). This provides a very powerful 
			capability for filtering the file, for example `pysys.mappers.IncludeLinesBetween` 
			provides the ability to filter in/out sections of a file. 
			
			Do not share mapper instances across multiple tests or threads as this can cause race conditions. 
			
		:param str encoding: The encoding to use to open the file. 
			The default value is None which indicates that the decision will be delegated 
			to the L{getDefaultFileEncoding()} method. 
		
		:param int reFlags: Zero or more flags controlling how the behaviour of regular expression matching, 
			combined together using the ``|`` operator, for example ``reFlags=re.VERBOSE | re.IGNORECASE``. 
			
			For details see the ``re`` module in the Python standard library. Note that ``re.MULTILINE`` cannot 
			be used because expressions are matched against one line at a time.

		:param bool abortOnError: Set to True to make the test immediately abort if the
			assertion fails. By default this method produces a BLOCKED output 
			but does not throw if the eval(...) cannot be executed. 

		:param str assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. We do not recommend using this as the automatically 
			generated assertion message is usually clearer. If you want to add some additional information to 
			that message (e.g. which file/server it pertains to etc), just add the info as a string with an extra 
			keyword argument. 
			
		:param \**kwargs: All additional keyword arguments are treated as values which will be made available 
			when evaluating the condition string. Any keyword ending in the special suffix ``__eval`` will be treated 
			as a Python expression string (rather than a string literal) and will be be evaluated in a namespace 
			containing the local variables of the calling code and (on Python 3.6+) any preceding named parameters.  
		
		:return: True if the assertion succeeds, False if a failure outcome was appended (and abortOnError=False). 

		"""
		def grep(file, expr):
			e = self.grep(file, expr, encoding=encoding, reFlags=reFlags, mappers=mappers)
			# in case it has named parameters
			if isinstance(e, dict) and len(e)==1: return next(iter(e.values()))
			return e
		return self.assertThat(conditionstring, value__eval='grep(%r, %r)'%(file, grepRegex), 
			**kwargsForAssertThat)

	def assertGrep(self, file, _expr=None, _unused=None, contains=True, ignores=None, literal=False, encoding=None, 
			abortOnError=False, assertMessage=None, reFlags=0, mappers=[], expr='', filedir=None):
		r"""Perform a validation by checking for the presence or absence of a regular expression in the specified text file.

		Note that if your goal is to check that a value in the file matches some criteria, it is better to 
		use `assertThatGrep` instead of this function, as assertThatGrep can produce better messages on failure, and 
		also allows for more powerful matching using a full Python expression 
		(e.g. numeric range checks, pre-processing strings to normalize case, etc). If you need to extract a string for 
		further processing without updating the test outcome, consider using `grep` instead. 

		The assertGrep method is good for checking in a log to confirm that something happened, or to check that 
		there are no error messages. 
		When contains=True it adds a `PASSED <pysys.constants.PASSED>` outcome if found or a 
		`FAILED <pysys.constants.FAILED>` outcome if not found (except when where are named groups in the expression 
		in which case `BLOCKED <pysys.constants.BLOCKED>` is used to indicate that the return value is not valid).
		When contains=False this is inverted so a `PASSED <pysys.constants.PASSED>` outcome is added if not found 
		and `FAILED <pysys.constants.FAILED>` if found. 

		For example::
		
			self.assertGrep('myserver.log', expr=r' ERROR .*', contains=False)

			# If error messages may be accompanied by stack traces you can use a mapper to join them into the same line 
			# so if your test fails, the outcome reason includes all the information. This also allows ignoring errors 
			# based on the stack trace:
			self.assertGrep('myserver.log', expr=r' (ERROR|FATAL) .*', contains=False, 
				mappers=[pysys.mappers.JoinLines.JavaStackTrace()], 	
				ignores=['Caused by: java.lang.RuntimeError: My expected exception'])
			
			# In Python 3+, f-Strings can be used to substitute in parameters, including in-line escaping of regex literals:
			self.assertGrep('myserver.log', expr=f'Successfully authenticated user "{re.escape(username)}" in .* seconds[.]')
			
			# If you need to use \ characters use a raw r'...' string to avoid the need for Python \ escaping in 
			# addition to regex escaping. Square brackets are often the clearest way to escape regular expression 
			# characters such as \ . and ()
			self.assertGrep('myserver.log', expr=r'c:[\]Foo[\]bar[.]txt')
			
			# The IncludeLinesBetween mapper is very useful if you want to grep within a subset of the lines:
			self.assertGrep('myserver.log', expr=r'MyClass', mappers=[
				pysys.mappers.IncludeLinesBetween('Error message.* - stack trace is:', stopBefore='^$'),
			])
		
		The behaviour of the regular expression can be controlled using ``reFlags=``. For example, to perform 
		case-insensitive matching and to use Python's verbose regular expression syntax which permits whitespace 
		and comments::
			
			self.assertGrep('myserver.log', reFlags=re.VERBOSE | re.IGNORECASE, expr=r\"""
				in\   
				\d +  # the integral part
				\.    # the decimal point
				\d *  # some fractional digits
				\ seconds\. # in verbose regex mode we escape spaces with a slash
				\""")

		Remember to escape regular expression special characters such as ``.``, ``(``, ``[``, ``{`` and ``\`` if you want them to 
		be treated as literal values. If you have a regular expression string with backslashes, it's best to use a 'raw' 
		Python string so that you don't need to double-escape them, e.g. ``self.assertGrep(..., expr=r'c:\\Foo\\filename\.txt')``.
		
		If you want to search for a string that needs lots of regex escaping, a nice trick is to use a 
		substitution string (containing only A-Z chars) for the regex special characters and pass everything else 
		through re.escape::
		
			self.assertGrep('myserver.log', expr=re.escape(r'A"string[with \lots*] of crazy characters e.g. VALUE.').replace('VALUE', '(.*)'))

		.. versionchanged:: 1.5.1
			The return value and reFlags were added in 1.5.1.

		:param file: The name or relative/absolute path of the file to be searched.
		
		:param str expr: The regular expression to check for in the file (or a string literal if literal=True), 
			for example ``" ERROR .*"``. 
			
			Remember to escape regular expression special characters such as ``.``, ``(``, ``[``, ``{`` and ``\`` if you want them to 
			be treated as literal values. 
			
			If you wish to do something with the text inside the match you can use the ``re`` named 
			group syntax ``(?P<groupName>...)`` to specify a name for parts of the regular expression.
			
			For contains=False matches, you should end the expr with `.*` if you wish to include just the 
			matching text in the outcome failure reason. If contains=False and expr does not end with a `*` 
			then the entire matching line will be included in the outcome failure reason. 
		
		:param bool contains: Boolean flag to specify if the expression should or should not be seen in the file.
		
		:param list[str] ignores: Optional list of regular expressions that will be 
			ignored when reading the file. Ignore expressions are applied *after* any mappers. 
		
		:param List[callable[str]->str] mappers: A list of filter functions that will be used to pre-process each 
			line from the file (returning None if the line is to be filtered out). This provides a very powerful 
			capability for filtering the file, for example `pysys.mappers.IncludeLinesBetween` 
			provides the ability to filter in/out sections of a file and `pysys.mappers.JoinLines` can combine related 
			error lines such as stack trace to provide all the information in the test outcome reason. 
			
			Mappers must always preserve the final ``\n`` of each line (if present). 
			
			Do not share mapper instances across multiple tests or threads as this can cause race conditions. 
			
			Added in PySys 1.6.0.
		
		:param bool literal: By default expr is treated as a regex, but set this to True to pass in 
			a string literal instead.
		
		:param str encoding: The encoding to use to open the file. 
			The default value is None which indicates that the decision will be delegated 
			to the L{getDefaultFileEncoding()} method. 
		
		:param bool abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 
		
		:param str assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. 

		:param str filedir: The directory of the file (defaults to the testcase output subdirectory); this is 
			deprecated, as it's simpler to just include the directory in the file parameter. 

		:param int reFlags: Zero or more flags controlling how the behaviour of regular expression matching, 
			combined together using the ``|`` operator, for example ``reFlags=re.VERBOSE | re.IGNORECASE``. 
			
			For details see the ``re`` module in the Python standard library. Note that ``re.MULTILINE`` cannot 
			be used because expressions are matched against one line at a time. Added in PySys 1.5.1. 
			
		:return: The ``re.Match`` object, or None if there was no match (note the return value is not affected by 
			the contains=True/False parameter). 
			
			However if the expr contains any ``(?P<groupName>...)`` named groups, then a dict is returned 
			containing ``dict(groupName: str, matchValue: str or None)`` (or an empty ``{}`` dict if there is no match) 
			which allows the assertGrep result to be passed to `assertThat` for further checking (typically 
			unpacked using the ``**`` operator; see example above). 
		
		"""
		# support the natural pattern of passing expr as 2nd positional parameter whilst retaining pre-1.6.0 compatibility support for
		# assertGrep(file, filedir, expr, True), assertGrep(file, filedir, expr='foo')
		if not _unused and not expr: # modern usage: expr as positional and filedir not positional
			expr = _expr
		elif _expr or _unused: # older usage - either or both may be set via positional
			filedir, expr = filedir or _expr, expr or _unused
		
		assert expr, 'expr= argument must be specified'
		
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		if literal:
			def escapeRegex(expr):
				# use our own escaping as re.escape makes the string unreadable
				regex = expr
				expr = ''
				for c in regex:
					if c in '\\{}[]+?^$':
						expr += '\\'+c
					elif c in '().*/':
						expr += '['+c+']' # more readable
					else:
						expr += c
				return expr
			expr = escapeRegex(expr)

		namedGroupsMode = False
		log.debug("Performing %s contains=%s grep on file: %s", 'regex' if not literal else 'literal/non-regex', contains, f)
		try:
			compiled = re.compile(expr, flags=reFlags)
			namedGroupsMode = compiled.groupindex
			
			result = getmatches(f, expr, ignores=ignores, returnFirstOnly=(contains==True), encoding=encoding or self.getDefaultFileEncoding(f), flags=reFlags, mappers=mappers)
			if not contains:
				matchcount = len(result)
				result = None if matchcount==0 else result[0]
		except Exception:
			log.warning("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			msg = assertMessage or ('Grep on %s %s %s'%(file, 'contains' if contains else 'does not contain', quotestring(expr) ))
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
			result = None
		else:
			# short message if it succeeded, more verbose one if it failed to help you understand why, 
			# including the expression it found that should not have been there
			outcome = PASSED if (result!=None) == contains else (BLOCKED if namedGroupsMode else FAILED)
			if outcome == PASSED: 
				if contains: log.debug('Grep on input file %s successfully matched expression %s with line: %s', 
					file, quotestring(expr), quotestring(result.string))
				msg = assertMessage or ('Grep on input file %s' % file)
			else:
			
				if assertMessage:
					msg = assertMessage
				elif contains:
					msg = 'Grep on %s contains %s'%(file, quotestring(expr))
					if mappers: msg += ', using mappers %s'%mappers
				else:
					msg = 'Grep on %s does not contain %s failed with%s: %s'%(file, 
						quotestring(expr),
						' %d matches, first is'%matchcount if matchcount>1 else '',
						# heuristic to give best possible message; expressions ending with .* are usually 
						# complete and help to remove timestamps etc from the start so best to return match only; if user didn't do 
						# that they probably haven't thought much about it and returning the entire match string 
						# is more useful (though strip off trailing newlines):
						quotestring(
							(result.group(0) if expr.endswith('*') else result.string).rstrip('\n\r')
							))
			self.addOutcome(outcome, msg, abortOnError=abortOnError)
		
		# special-case if they're using named regex named groups to make it super-easy to use with assertThat - 
		# so always return a dict instead of None for that case
		if namedGroupsMode:
			return {} if result is None else result.groupdict()
		
		return result

	def assertLastGrep(self, file, _expr='', _unused=None, contains=True, ignores=[], includes=[], encoding=None, 
			abortOnError=False, assertMessage=None, reFlags=0, expr='', filedir=None):
		"""Perform a validation assert on a regular expression occurring in the last line of a text file.
		
		Rather than using this method, use `grepAll` with `assertThat` for better error messages and more 
		maintainable tests, e.g. you can extract the last line of a file easily 
		with ``self.grepAll(file, '.')[0]``.
		
		When the C{contains} input argument is set to true, this method will add a C{PASSED} outcome 
		to the test outcome list if the supplied regular expression is seen in the file; otherwise a 
		C{FAILED} outcome is added. Should C{contains} be set to false, a C{PASSED} outcome will only 
		be added should the regular expression not be seen in the file.
		
		:param file: The basename of the file used in the grep
		:param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		:param expr: The regular expression to check for in the last line of the file
		:param contains: Boolean flag to denote if the expression should or should not be seen in the file
		:param ignores: A list of regular expressions used to denote lines in the file which should be ignored
		:param includes: A list of regular expressions used to denote lines in the file which should be used in the assertion.#
		:param encoding: The encoding to use to open the file. 
			The default value is None which indicates that the decision will be delegated 
			to the L{getDefaultFileEncoding()} method. 

		:param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 

		:param assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. 				

		:param int reFlags: Zero or more flags controlling how the behaviour of regular expression matching, 
			combined together using the ``|`` operator, for example ``reFlags=re.VERBOSE | re.IGNORECASE``. 
			
			For details see the ``re`` module in the Python standard library. Note that ``re.MULTILINE`` cannot 
			be used because expressions are matched against one line at a time. Added in PySys 1.5.1. 

		:return: The ``re.Match`` object, or None if there was no match (note the return value is not affected by 
			the contains=True/False parameter). 
			
			However if the expr contains any ``(?P<groupName>...)`` named groups, then a dict is returned 
			containing ``dict(groupName: str, matchValue: str or None)`` (or an empty ``{}`` dict if there is no match) 
			which allows the result to be passed to `assertThat` for further checking (typically 
			unpacked using the ``**`` operator; see `assertGrep` for a similar example). 
		"""
		if not _unused and not expr: # modern usage: expr as positional and filedir not positional
			expr = _expr
		elif _expr or _unused: # older usage - either or both may be set via positional
			filedir, expr = filedir or _expr, expr or _unused

		assert expr, 'expr= argument must be specified'

		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		log.debug("Performing contains=%s grep on last line of file: %s", contains, f)

		msg = assertMessage or ('Grep on last line of %s %s %s'%(file, 'contains' if contains else 'not contains', quotestring(expr)))
		namedGroupsMode = False
		try:
			compiled = re.compile(expr, flags=reFlags)
			namedGroupsMode = compiled.groupindex
			match = lastgrep(f, expr, ignores, includes, encoding=encoding or self.getDefaultFileEncoding(f), returnMatch=True, flags=reFlags)
		except Exception:
			log.warning("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
			match = None
		else:
			result = (match is not None) == contains
			if result: msg = assertMessage or ('Grep on input file %s' % file)
			self.addOutcome(PASSED if result else (BLOCKED if namedGroupsMode else FAILED), msg, abortOnError=abortOnError)

		# special-case if they're using named regex named groups to make it super-easy to use with assertThat - 
		# so always return a dict instead of None for that case
		if namedGroupsMode:
			return {} if match is None else match.groupdict()
			
		return match


	def assertOrderedGrep(self, file, _exprList=[], _unused=None, contains=True, encoding=None, 
			abortOnError=False, assertMessage=None, reFlags=0, exprList=[], filedir=None):   
		"""Perform a validation assert on a list of regular expressions occurring in specified order in a text file.
		
		When the C{contains} input argument is set to true, this method will append a C{PASSED} outcome 
		to the test outcome list if the supplied regular expressions in the C{exprList} are seen in the file
		in the order they appear in the list; otherwise a C{FAILED} outcome is added. Should C{contains} be set 
		to false, a C{PASSED} outcome will only be added should the regular expressions not be seen in the file in 
		the order they appear in the list.
		
		Warning: while this assertion method can be very convenient for checking the order of a small number of expressions, 
		it becomes unwieldy when the number of expressions grows beyond a handful, and this is definitely not the 
		best tool for the job if what you're doing is really about checking that a subset of data from an output file 
		matches expectations. For that use case, it's better to do a filtered `copy()` of the file to remove 
		prefixes (e.g. timestamps) and lines that are not important, and then use `assertDiff` to check the extracted 
		text matches expectations. This approach makes it easier to write tests, and crucially makes it much easier 
		to figure out what went wrong if they fail. 
		
		Similarly, if you need to check that an expression appears between two other lines (e.g. for a start/end of 
		section) this method will not give you a reliable way to do that if there's a chance the section markers 
		could appear more than once in the file, so instead use the filtered `copy()` approach described above, or use 
		`assertGrep` with a `pysys.mappers.IncludeLinesBetween` mapper. 
		
		:param file: The basename of the file used in the ordered grep
		:param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		:param exprList: A list of regular expressions which should occur in the file in the order they appear in the list
		:param contains: Boolean flag to denote if the expressions should or should not be seen in the file in the order specified
		:param encoding: The encoding to use to open the file. 
			The default value is None which indicates that the decision will be delegated 
			to the L{getDefaultFileEncoding()} method. 

		:param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 

		:param assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. 

		:param int reFlags: Zero or more flags controlling how the behaviour of regular expression matching, 
			combined together using the ``|`` operator, for example ``reFlags=re.VERBOSE | re.IGNORECASE``. 
			
			For details see the ``re`` module in the Python standard library. Note that ``re.MULTILINE`` cannot 
			be used because expressions are matched against one line at a time. Added in PySys 1.5.1. 

		:return: True if the assertion succeeds, False if a failure outcome was appended. 

		"""
		if not _unused and not exprList: # modern usage: expr as positional and filedir not positional
			exprList = _exprList
		elif _exprList or _unused: # older usage - either or both may be set via positional
			filedir, exprList = filedir or _exprList, exprList or _unused

		assert exprList, 'exprList= argument must be specified'
		
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)
	
		log.debug("Performing contains=%s ordered grep on %s for %s", contains, f, exprList)
		
		msg = assertMessage or ('Ordered grep on input file %s' % file)
		expr = None
		try:
			expr = orderedgrep(f, exprList, encoding=encoding or self.getDefaultFileEncoding(f), flags=reFlags)
		except Exception:
			log.warning("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
		else:
			if expr is None and contains:
				result = PASSED
			elif expr is None and not contains:
				result = FAILED
			elif expr is not None and not contains:
				result = PASSED
			else:
				result = FAILED

			if result == FAILED and expr: 
				msg += ' failed on expression \"%s\"'% expr
			self.addOutcome(result, msg, abortOnError=abortOnError)
			return result==PASSED
		return False

	
	def assertLineCount(self, file, _expr='', _unused=None, condition=">=1", ignores=None, encoding=None, 
			abortOnError=False, assertMessage=None, reFlags=0, expr='', filedir=None, mappers=[]):
		r"""Perform a validation assert on the count of lines in a text file matching a specific regular expression.
		
		This method will add a C{PASSED} outcome to the outcome list if the number of lines in the 
		input file matching the specified regular expression evaluate to true when evaluated against 
		the supplied ``condition``.
		
		:param file: The basename of the file used in the line count
		:param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		:param expr: The regular expression string used to match a line of the input file
		:param condition: The condition to be met for the number of lines matching the regular expression
		:param ignores: A list of regular expressions that will cause lines to be excluded from the count.
			Ignore expressions are applied *after* any mappers. 
		:param encoding: The encoding to use to open the file. 
			The default value is None which indicates that the decision will be delegated 
			to the L{getDefaultFileEncoding()} method. 
		:param List[callable[str]->str] mappers: A list of filter functions that will be used to pre-process each 
			line from the file (returning None if the line is to be filtered out). This provides a very powerful 
			capability for filtering the file, for example `pysys.mappers.IncludeLinesBetween` 
			provides the ability to filter in/out sections of a file and `pysys.mappers.JoinLines` can combine related 
			error lines such as stack trace to provide all the information in the test outcome reason. 
			
			Mappers must always preserve the final ``\n`` of each line (if present). 
			
			Do not share mapper instances across multiple tests or threads as this can cause race conditions. 
			
			Added in PySys 2.0.

		:param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 
		
		:param assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. 

		:param int reFlags: Zero or more flags controlling how the behaviour of regular expression matching, 
			combined together using the ``|`` operator, for example ``reFlags=re.VERBOSE | re.IGNORECASE``. 
			
			For details see the ``re`` module in the Python standard library. Note that ``re.MULTILINE`` cannot 
			be used because expressions are matched against one line at a time. Added in PySys 1.5.1. 

		:return: True if the assertion succeeds, False if a failure outcome was appended. 
		"""	
		if not _unused and not expr: # modern usage: expr as positional and filedir not positional
			expr = _expr
		elif _expr or _unused: # older usage - either or both may be set via positional
			filedir, expr = filedir or _expr, expr or _unused

		assert expr, 'expr= argument must be specified'
		
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			if condition.replace(' ','') in ['==0', '<=0']:
				m = getmatches(f, expr, ignores=ignores, encoding=encoding or self.getDefaultFileEncoding(f), flags=reFlags, mappers=mappers)
				numberLines = len(m)
				firstMatch = (m[0] if len(m)>0 else None)
			else:
				numberLines = linecount(f, expr, ignores=ignores, encoding=encoding or self.getDefaultFileEncoding(f), flags=reFlags, mappers=mappers)
				firstMatch = None
			log.debug("Number of matching lines in %s is %d", f, numberLines)
		except Exception:
			log.warning("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			msg = assertMessage or ('Line count on %s for %s%s '%(file, quotestring(expr), condition))
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
		else:
			if (pysys.utils.safeeval.safeEval("%d %s" % (numberLines, condition), extraNamespace={'self':self})):
				msg = assertMessage or ('Line count on input file %s' % file)
				self.addOutcome(PASSED, msg)
				return True
			else:
				msg = assertMessage or ('Line count on %s for %s expected %s but got %d%s'%(file, quotestring(expr), condition.strip(), numberLines, 
					('; first is: '+quotestring( # special handling for condition==0, to match assertGrep(..., contains=False)
							(firstMatch.group(0) if expr.endswith('*') else firstMatch.string).rstrip('\n\r') # see assertGrep
					)) if firstMatch else ''))
				self.addOutcome(FAILED, msg, abortOnError=abortOnError)
		return False

	def reportPerformanceResult(self, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		""" Reports a new performance number to the performance ``csv`` file, with an associated unique string key 
		that identifies it for comparison purposes.
		
		
		Where possible it is better to report the rate at which an operation can be performed (e.g. throughput)
		rather than the total time taken, since this allows the number of iterations to be increased without affecting 
		historical comparisons. For example::
		
			self.reportPerformanceResult(int(iterations)/float(calctime), 
				'Fibonacci sequence calculation rate', '/s'))

		If your test runs in multiple modes, make sure you include some information about the mode in the resultKey::
		
			self.reportPerformanceResult(int(iterations)/float(calctime), 
				'Fibonacci sequence calculation rate using %s' % self.mode, '/s', 
				resultDetails=[('mode',self.mode)])

		While use of standard units such as '/s', 's' or 'ns' (nano-seconds) is recommended, custom units can be 
		provided when needed using `pysys.utils.perfreporter.PerformanceUnit`::
		
			self.reportPerformanceResult(int(iterations)/float(calctime)/1000, 
				'Fibonacci sequence calculation rate using %s with different units' % self.mode, 
				unit=PerformanceUnit('kilo_fibonacci/s', biggerIsBetter=True))

		:param value: The numeric value to be reported. If a str is provided, it will be converted to a float.

		:param resultKey: A unique string that fully identifies what was measured, which will be
			used to compare results from different test runs. For example "HTTP transport message sending throughput
			using with 3 connections in SSL mode". The resultKey must be unique across all test cases and modes. It should be fully
			self-describing (without the need to look up extra information such as the associated testId). Do not include
			the test id or units in the resultKey string. It must be stable across different runs, so cannot contain
			process identifiers, date/times or other numbers that will vary. If possible resultKeys should be written
			so that related results will be together when all performance results are sorted by resultKey, which usually
			means putting general information near the start of the string and specifics (throughput/latency, sending/receiving)
			towards the end of the string. It should be as concise as possible (given the above).

		:param unit: Identifies the unit the value is measured in, including whether bigger numbers are better or
			worse (used to determine improvement or regression). Must be an instance of L{pysys.utils.perfreporter.PerformanceUnit}.
			In most cases, use L{pysys.utils.perfreporter.PerformanceUnit.SECONDS} (e.g. for latency) or
			L{pysys.utils.perfreporter.PerformanceUnit.PER_SECOND} (e.g. for throughput); the string literals 's' and '/s' can be
			used as a shorthand for those PerformanceUnit instances.
		
		:param toleranceStdDevs: (optional) A float that indicates how many standard deviations away from the mean a
			result needs to be to be considered a regression.
		
		:param resultDetails: (optional) A dictionary of detailed information about this specific result 
			and/or test that should be recorded together with the result, for example detailed information about what mode 
			or versions the test is measuring. Note this is separate from the global run details shared across 
			all tests in this PySys execution, which can be customized by overriding 
			L{pysys.utils.perfreporter.CSVPerformanceReporter.getRunDetails}.

		"""
		for p in self.runner.performanceReporters:
			p.reportResult(self, value, resultKey, unit, toleranceStdDevs=toleranceStdDevs, resultDetails=resultDetails)
			
	def getDefaultFileEncoding(self, file, **xargs):
		"""
		Specifies what encoding should be used to read or write the specified 
		text file. The default implementation for BaseTest delegates to the 
		runner, which in turn gets its defaults from the ``pysyproject.xml`` 
		configuration. 
		
		See L{pysys.process.user.ProcessUser.getDefaultFileEncoding} for more details.
		"""
		return self.runner.getDefaultFileEncoding(file, **xargs)
	
	def pythonDocTest(self, pythonFile, pythonPath=None, output=None, environs=None, **kwargs):
		"""
		Execute the Python doctests that exist in the specified python file; 
		adds a FAILED outcome if any do not pass. 
		
		:param pythonFile: the absolute path to a python file name. 
		:param pythonPath: a list of directories to be added to the PYTHONPATH.
		:param output: the output file; if not specified, '%s-doctest.txt' is used with 
			the basename of the python file. 
		
		:param kwargs: extra arguments are passed to startProcess/startPython. 
		"""
		assert os.path.exists(os.path.abspath(pythonFile)), os.path.abspath(pythonFile)
		
		if not output: output = '%s-doctest.txt'%os.path.basename(pythonFile).replace('.py','')
		p = self.startPython(
			arguments=['-m', 'doctest', '-v', os.path.normpath(pythonFile)],
			environs=self.createEnvirons(overrides=[environs, {
				'PYTHONPATH':None if not pythonPath else os.pathsep.join(pythonPath or [])}]),
			stdout=output, 
			stderr=output+'.err', 
			displayName='Python doctest %s'%os.path.basename(pythonFile),
			ignoreExitStatus=True,
			abortOnError=False, 
			**kwargs
			)
		msg = 'Python doctest for %s'%(os.path.basename(pythonFile))
		try:
			msg += ': '+self.getExprFromFile(output, r'\d+ passed.*\d+ failed') # appears whether it succeeds or fails
		except Exception: 
			msg += ': failed to execute correctly'
		try:
			msg += '; first failure is: '+self.getExprFromFile(output, '^File .*, line .*, in .*')
		except Exception:
			pass # probably it succeeded
		
		if p.exitStatus == 0:
			self.addOutcome(PASSED, msg)
		else:
			self.addOutcome(FAILED, msg)
			self.logFileContents(output+'.err') # in case there are any clues there
			
			# full doctest output is quite hard to read, so try to summarize just the failures 
			
			failures = []
			lines = [] # accumulate each test
			with openfile(os.path.join(self.output, output), encoding=PREFERRED_ENCODING) as f:
				for line in f:
					line = line.rstrip()
					if line=='Trying:': # start of a new one, end of previous one
						if lines and lines[-1]!='ok':
							failures.append(lines)
						lines = [line]
					elif line == 'ok': # ignore if passed; needed if last test was a pass
						lines = []
					else:
						lines.append(line)
				if lines and lines[-1]!='ok':
					failures.append(lines)
				
			for failure in failures:
				log.info('-'*20)
				for line in failure:
					log.warning('  %s'%line.rstrip())
				log.info('')
