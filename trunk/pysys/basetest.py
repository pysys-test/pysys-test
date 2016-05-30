#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

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

# Contact: moraygrieve@users.sourceforge.net
"""
Contains the base test class for test execution and validation. 

For more information see the L{pysys.basetest.BaseTest} API documentation. 

"""
import sys, os, os.path, re, string, time, thread, logging, copy, math, stat, inspect

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filecopy import filecopy
from pysys.utils.filegrep import filegrep
from pysys.utils.filegrep import lastgrep
from pysys.utils.filediff import filediff
from pysys.utils.filegrep import orderedgrep
from pysys.utils.linecount import linecount
from pysys.process.user import ProcessUser
from pysys.process.helper import ProcessWrapper
from pysys.process.monitor import ProcessMonitor
from pysys.manual.ui import ManualTester
from pysys.process.user import ProcessUser


TEST_TEMPLATE = '''%s
%s

class %s(%s):
	def execute(self):
		pass

	def validate(self):
		pass
'''


class BaseTest(ProcessUser):
	"""The base class for all PySys testcases.

	BaseTest is the parent class of all PySys system testcases. The class provides utility functions for 
	cross-platform process management and manipulation, test timing, and test validation. Any PySys testcase 
	should inherit from the base test and provide an implementation of the abstract L{execute} method 
	defined in this class. Child classes can also overide the L{setup}, L{cleanup} and L{validate} 
	methods of the class to provide custom setup and cleanup actions for a particual test, and to perform 
	all validation steps in a single method should this prove logically more simple.
	
	Execution of a PySys testcase is performed through an instance of the L{pysys.baserunner.BaseRunner}
	class, or a subclass thereof. The base runner instantiates an instance of the testcase, and then calls 
	the C{setup}, C{execute}, C{validate} and C{cleanup} methods of the instance. All processes started during 
	the test execution are reference counted within the base test, and terminated within the C{cleanup} method.
	
	Validation of the testcase is through the C{assert*} methods. Execution of many methods appends an outcome 
	to the outcome data structure maintained by the ProcessUser base class, thus building up a record of the 
	individual validation outcomes. Several potential outcomes are supported by the PySys framework 
	(C{SKIPPED}, C{BLOCKED}, C{DUMPEDCORE}, C{TIMEDOUT}, C{FAILED}, C{NOTVERIFIED}, and C{PASSED}) and the 
	overall outcome of the testcase is determined using aprecedence order of the individual outcomes. 
	
	All C{assert*} methods except for C{assertThat} support variable argument lists for common non-default parameters.
	Currently this includes the C{assertMessage} parameter, to override the default statement logged by the framework
	to stdout and the run log, and the C{abortOnError} parameter, to override the defaultAbortOnError project
	setting.

	@ivar mode: The user defined mode the test is running within. Subclasses can use this in conditional checks
	           to modify the test execution based upon the mode.
	@type mode: string
	@ivar input: Full path to the input directory of the testcase. This is used both by the class and its 
	            subclasses to locate the default directory containing all input data to the testcase, as defined
	            in the testcase descriptor.  
	@type input: string
	@ivar output: Full path to the output sub-directory of the testcase. This is used both by the class and its 
				subclasses to locate the default directory for output produced by the testcase. Note that this 
				is the actual directory where all output is written, as modified from that defined in the testcase 
				descriptor to accomodate for the sub-directory used within this location to sandbox concurrent 
				execution of the test, and/or to denote the run number. 
	@type output: string
	@ivar reference: Full path to the reference directory of the testcase. This is used both by the class and its 
	            subclasses to locate the default directory containing all reference data to the testcase, as defined
	            in the testcase descriptor.  
	@type reference: string
	@ivar log: Reference to the logger instance of this class
	@type log: logging.Logger
	@ivar project: Reference to the project details as set on the module load of the launching executable  
	@type project: L{Project}
		
	"""
	
	def __init__ (self, descriptor, outsubdir, runner):
		"""Create an instance of the BaseTest class.
		
		@param descriptor: The descriptor for the test giving all test details
		@param outsubdir: The output subdirectory the test output will be written to
		@param runner: Reference to the runner responsable for executing the testcase
		
		"""
		ProcessUser.__init__(self)
		self.descriptor = descriptor
		self.input = descriptor.input
		self.output = os.path.join(descriptor.output, outsubdir)
		self.reference = descriptor.reference
		self.runner = runner
		self.mode = runner.mode
		self.setKeywordArgs(runner.xargs)
		self.monitorList = []
		self.manualTester = None
		self.resources = []


	def setKeywordArgs(self, xargs):
		"""Set the xargs as data attributes of the test class.
				
		Values in the xargs dictionary are set as data attributes using the builtin C{setattr} method. 
		Thus an xargs dictionary of the form C{{'foo': 'bar'}} will result in a data attribute of the 
		form C{self.foo} with C{value bar}. This is used so that subclasses can define default values of 
		data attributes, which can be overriden on instantiation e.g. using the -X options to the 
		runTest.py launch executable.
		
		@param xargs: A dictionary of the user defined extra arguments
		
		"""
		for key in xargs.keys():
			setattr(self, key, xargs[key])

			
	# test methods for execution, validation and cleanup. The execute method is
	# abstract and must be implemented by a subclass. 
	def setup(self):
		"""Setup method which may optionally be overridden to perform custom setup operations prior to test execution.
		
		"""
		pass		


	def execute(self):
		"""Execute method which must be overridden to perform the test execution steps.
		
		@raises NotImplementedError:  Raised exeception should the method not be overridden
		"""
		raise NotImplementedError, "The execute method of the BaseTest class must be implemented in a subclass"


	def validate(self):
		"""Validate method which may optionally be overridden to group all validation steps.
		
		"""
		pass


	def cleanup(self):
		"""Cleanup method which performs cleanup actions after execution and validation of the test.
		
		The cleanup method performs actions to stop all processes started in the background and not 
		explicitly killed during the test execution. It also stops all process monitors running in 
		seperate threads, and any instances of the manual tester user interface. 
		
		Should a custom cleanup for a subclass be required, use 
		L{addCleanupFunction} instead of overriding this method. 
				
		"""
		try:
			if self.manualTester and self.manualTester.running():
				self.stopManualTester()
		
			for monitor in self.monitorList:
				if monitor.running(): monitor.stop()
	
			while len(self.resources) > 0:
				self.resources.pop()
		finally:
			ProcessUser.cleanup(self)


	def addResource(self, resource):
		"""Add a resource which is owned by the test and is therefore
		cleaned up (deleted) when the test is cleaned up. 
		
		Deprecated - please use addCleanupFunction instead of this function. 
		"""
		self.resources.append(resource)


	def startProcessMonitor(self, process, interval, file, **kwargs):
		"""Start a separate thread to log process statistics to logfile, and return a handle to the process monitor.
		
		This method uses the L{pysys.process.monitor} module to perform logging of the process statistics, 
		starting the monitor as a seperate background thread. Should the request to log the statistics fail 
		a C{BLOCKED} outcome will be added to the test outcome list. All process monitors not explicitly 
		stopped using the returned handle are automatically stopped on completion of the test via the L{cleanup} 
		method of the BaseTest. 
		
		@param process: The process handle returned from the L{startProcess} method
		@param interval: The interval in seconds between collecting and logging the process statistics
		@param file: The full path to the filename used for logging the process statistics
		@param kwargs: Keyword arguments to allow platform specific configurations
				
		@return: A handle to the process monitor (L{pysys.process.monitor.ProcessMonitor})
		@rtype: handle
		
		"""
		monitor = ProcessMonitor(process.pid, interval, file, **kwargs)
		try:
			self.log.info("Starting process monitor on process with id = %d", process.pid)
			monitor.start()
		except ProcessError, e:
			self.addOutcome(BLOCKED, 'Unable to start process monitor for %s: %s'%(process, e))
		else:
			self.monitorList.append(monitor)
			return monitor

	
	def stopProcessMonitor(self, monitor):
		"""Stop a process monitor.
		
		@param monitor: The process monitor handle returned from the L{startProcessMonitor} method
		
		"""
		if monitor.running: monitor.stop()


	# methods to control the manual tester user interface
	def startManualTester(self, file, filedir=None, state=FOREGROUND, timeout=TIMEOUTS['ManualTester']):
		"""Start the manual tester.
		
		The manual tester user interface (UI) is used to describe a series of manual steps to be performed 
		to execute and validate a test. Only a single instance of the UI can be running at any given time, and 
		can be run either in the C{FOREGROUND} (method will not return until the UI is closed or the timeout
		occurs) or in the C{BACKGROUND} (method will return straight away so automated actions may be performed 
		concurrently). Should the UI be terminated due to expiry of the timeout, a C{TIMEDOUT} outcome will be 
		added to the outcome list. The UI can be stopped via the L{stopManualTester} method. An instance of the 
		UI not explicitly stopped within a test will automatically be stopped via the L{cleanup} method of the 
		BaseTest.
		
		@param file: The name of the manual test xml input file (see L{pysys.xml.manual} for details on the DTD)
		@param filedir: The directory containing the manual test xml input file (defaults to the output subdirectory)
		@param state: Start the manual tester either in the C{FOREGROUND} or C{BACKGROUND} (defaults to C{FOREGROUND})
		@param timeout: The timeout period after which to termintate a manual tester running in the C{FOREGROUND}
		
		"""
		if filedir is None: filedir = self.input
	
		if not self.manualTester or self.manualTester.running() == 0:
			self.manualTester = ManualTester(self, os.path.join(filedir, file))
			thread.start_new_thread(self.manualTester.start, ())
		
			if state == FOREGROUND:
				startTime = time.time()
				while self.manualTester.running() == 1:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						self.addOutcome(TIMEDOUT, 'Manual tester timed out')
						self.manualTester.stop()
						return
					time.sleep(1)
			else:
				time.sleep(1)
		else:
			self.addOutcome(BLOCKED, 'Manual tester failed')


	def stopManualTester(self):
		"""Stop the manual tester if running.
		
		"""
		if self.manualTester and self.manualTester.running():
			self.manualTester.stop()
			time.sleep(1)
		else:
			self.addOutcome(BLOCKED, 'Manual tester could not be stopped')


	def waitManualTester(self, timeout=TIMEOUTS['ManualTester']):
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
				time.sleep(1)


	# test timing methods. These allow control flow of the test to be set
	# on various conditions i.e. a socket becoming available for connections,
	# a file to exist etc
	def wait(self, interval):
		"""Wait for a specified period of time.
		
		@param interval: The time interval in seconds to wait
		
		"""
		log.info('Waiting for %0.1f seconds'%interval)
		time.sleep(interval)


	# test validation methods.
	def assertThat(self, conditionstring, *args):
		"""Perform a validation based on a python eval string.

		The eval string should be specified as a format string, with zero or more %s-style
		arguments. This provides an easy way to check conditions that also produces clear
		outcome messages.
		
		e.g. self.assertThat('%d >= 5 or "%s"=="foobar"', myvalue, myothervalue)

		@param conditionstring: A string will have any following args 
			substituted into it and then be evaluated as a boolean python 
			expression. If your args are strings that could contain double-quotes, 
			put single quotes around the %s in the conditionstring, and vice-versa. 
		@param args: Zero or more arguments to be substituted into the format 
			string
		
		"""
		try:
			expr = conditionstring
			if args:
				expr = expr % args
			
			result = bool(eval(expr))
		except Exception, e:
			self.addOutcome(BLOCKED, 'Failed to evaluate "%s" with args %r: %s'%(conditionstring, args, e))
			return
		
		if result:
			self.addOutcome(PASSED, 'Assertion on %s'%expr)
		else:
			self.addOutcome(FAILED, 'Assertion on %s'%expr)


	def assertTrue(self, expr, **xargs):
		"""Perform a validation assert on the supplied expression evaluating to true.
		
		If the supplied expression evaluates to true a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to false, a C{FAILED} outcome is added.
		
		@param expr: The expression, as a boolean, to check for the True | False value
		@param xargs: Variable argument list (see class description for supported parameters)
		
		"""
		msg = self.__assertMsg(xargs, 'Assertion on boolean expression equal to true')
		if expr == True:
			self.addOutcome(PASSED, msg, abortOnError=self.__abortOnError(xargs))
		else:
			self.addOutcome(FAILED, msg, abortOnError=self.__abortOnError(xargs))
	

	def assertFalse(self, expr, **xargs):
		"""Perform a validation assert on the supplied expression evaluating to false.
		
		If the supplied expression evaluates to false a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to true, a C{FAILED} outcome is added.
		
		@param expr: The expression to check for the true | false value
		@param xargs: Variable argument list (see class description for supported parameters)
						
		"""
		msg = self.__assertMsg(xargs, 'Assertion on boolean expression equal to false')
		if expr == False:
			self.addOutcome(PASSED, msg, abortOnError=self.__abortOnError(xargs))
		else:
			self.addOutcome(FAILED, msg, abortOnError=self.__abortOnError(xargs))


	def assertDiff(self, file1, file2, filedir1=None, filedir2=None, ignores=[], sort=False, replace=[], includes=[], **xargs):
		"""Perform a validation assert on the comparison of two input text files.
		
		This method performs a file comparison on two input files. The files are pre-processed prior to the 
		comparison to either ignore particular lines, sort their constituent lines, replace matches to regular 
		expressions in a line with an alternate value, or to only include particular lines. Should the files 
		after pre-processing be equivalent a C{PASSED} outcome is added to the test outcome list, otherwise
		a C{FAILED} outcome is added.
		
		@param file1: The basename of the first file used in the file comparison
		@param file2: The basename of the second file used in the file comparison (often a reference file)
		@param filedir1: The dirname of the first file (defaults to the testcase output subdirectory)
		@param filedir2: The dirname of the second file (defaults to the testcase reference directory)
		@param ignores: A list of regular expressions used to denote lines in the files which should be ignored
		@param sort: Boolean flag to indicate if the lines in the files should be sorted prior to the comparison
		@param replace: List of tuples of the form ('regexpr', 'replacement'). For each regular expression in the 
			list, any occurences in the files is replaced with the replacement value prior to the comparison being 
			carried out. This is often useful to replace timestamps in logfiles etc.
		@param includes: A list of regular expressions used to denote lines in the files which should be used in the 
			comparison. Only lines which match an expression in the list are used for the comparison
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""
		if filedir1 is None: filedir1 = self.output
		if filedir2 is None: filedir2 = self.reference
		f1 = os.path.join(filedir1, file1)
		f2 = os.path.join(filedir2, file2)

		log.debug("Performing file comparison:")
		log.debug("  file1:       %s" % file1)
		log.debug("  filedir1:    %s" % filedir1)
		log.debug("  file2:       %s" % file2)
		log.debug("  filedir2:    %s" % filedir2)
		
		msg = self.__assertMsg(xargs, 'File comparison between %s and %s'%(file1, file2))
		unifiedDiffOutput=os.path.join(self.output, os.path.basename(f1)+'.diff')
		try:
			result = filediff(f1, f2, ignores, sort, replace, includes, unifiedDiffOutput=unifiedDiffOutput)
		except:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=self.__abortOnError(xargs))
		else:
			self.addOutcome(PASSED if result else FAILED, msg, abortOnError=self.__abortOnError(xargs))
			if not result:
				self.logFileContents(unifiedDiffOutput)


	def assertGrep(self, file, filedir=None, expr='', contains=True, ignores=None, literal=False, **xargs):
		"""Perform a validation assert on a regular expression occurring in a text file.
		
		When the C{contains} input argument is set to true, this method will add a C{PASSED} outcome 
		to the test outcome list if the supplied regular expression is seen in the file; otherwise a 
		C{FAILED} outcome is added. Should C{contains} be set to false, a C{PASSED} outcome will only 
		be added should the regular expression not be seen in the file.
		
		@param file: The basename of the file used in the grep
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression to check for in the file (or a string literal if literal=True). 
			If the match fails, the matching regex will be reported as the test outcome
		@param contains: Boolean flag to denote if the expression should or should not be seen in the file
		@param ignores: Optional list of regular expressions that will be 
			ignored when reading the file. 
		@param literal: By default expr is treated as a regex, but set this to True to pass in 
			a string literal instead
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""
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

		log.debug("Performing grep on file:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		log.debug("  expr:       %s" % expr)
		log.debug("  contains:   %s" % LOOKUP[contains])
		try:
			result = filegrep(f, expr, ignores=ignores, returnMatch=True)
		except:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			msg = self.__assertMsg(xargs, 'Grep on %s %s "%s"'%(file, 'contains' if contains else 'does not contain', expr))
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=self.__abortOnError(xargs))
		else:
			# short message if it succeeded, more verbose one if it failed to help you understand why, 
			# including the expression it found that should not have been there
			outcome = PASSED if (result!=None) == contains else FAILED
			if outcome == PASSED: 
				msg = self.__assertMsg(xargs, 'Grep on input file %s' % file)
			else:
				msg = self.__assertMsg(xargs, 'Grep on %s %s "%s"'%(file, 'contains' if contains else 'does not contain', 
					result.group(0) if result else expr))
			self.addOutcome(outcome, msg, abortOnError=self.__abortOnError(xargs))
		

	def assertLastGrep(self, file, filedir=None, expr='', contains=True, ignores=[], includes=[], **xargs):
		"""Perform a validation assert on a regular expression occurring in the last line of a text file.
		
		When the C{contains} input argument is set to true, this method will add a C{PASSED} outcome 
		to the test outcome list if the supplied regular expression is seen in the file; otherwise a 
		C{FAILED} outcome is added. Should C{contains} be set to false, a C{PASSED} outcome will only 
		be added should the regular expression not be seen in the file.
		
		@param file: The basename of the file used in the grep
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression to check for in the last line of the file
		@param contains: Boolean flag to denote if the expression should or should not be seen in the file
		@param ignores: A list of regular expressions used to denote lines in the file which should be ignored
		@param includes: A list of regular expressions used to denote lines in the file which should be used in the assertion.
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		log.debug("Performing grep on file:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		log.debug("  expr:       %s" % expr)
		log.debug("  contains:   %s" % LOOKUP[contains])

		msg = self.__assertMsg(xargs, 'Grep on last line of %s %s "%s"'%(file, 'contains' if contains else 'not contains', expr))
		try:
			result = lastgrep(f, expr, ignores, includes) == contains
		except:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=self.__abortOnError(xargs))
		else:
			if result: msg = self.__assertMsg(xargs, 'Grep on input file %s' % file)
			self.addOutcome(PASSED if result else FAILED, msg, abortOnError=self.__abortOnError(xargs))


	def assertOrderedGrep(self, file, filedir=None, exprList=[], contains=True, **xargs):   
		"""Perform a validation assert on a list of regular expressions occurring in specified order in a text file.
		
		When the C{contains} input argument is set to true, this method will append a C{PASSED} outcome 
		to the test outcome list if the supplied regular expressions in the C{exprList} are seen in the file
		in the order they appear in the list; otherwise a C{FAILED} outcome is added. Should C{contains} be set 
		to false, a C{PASSED} outcome will only be added should the regular expressions not be seen in the file in 
		the order they appear in the list.
		
		@param file: The basename of the file used in the ordered grep
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param exprList: A list of regular expressions which should occur in the file in the order they appear in the list
		@param contains: Boolean flag to denote if the expressions should or should not be seen in the file in the order specified
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)
	
		log.debug("Performing ordered grep on file:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		for expr in exprList: log.debug("  exprList:   %s" % expr)
		log.debug("  contains:   %s" % LOOKUP[contains])
		
		msg = self.__assertMsg(xargs, 'Ordered grep on input file %s' % file)
		try:
			expr = orderedgrep(f, exprList)
		except:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=self.__abortOnError(xargs))
		else:
			if expr is None and contains:
				result = PASSED
			elif expr is None and not contains:
				result = FAILED
			elif expr is not None and not contains:
				result = PASSED
			else:
				result = FAILED

			self.addOutcome(result, msg, abortOnError=self.__abortOnError(xargs))
			if result == FAILED: log.warn("Ordered grep failed on expression \"%s\"", expr)


	def assertLineCount(self, file, filedir=None, expr='', condition=">=1", ignores=None, **xargs):
		"""Perform a validation assert on the number of lines in a text file matching a specific regular expression.
		
		This method will add a C{PASSED} outcome to the outcome list if the number of lines in the 
		input file matching the specified regular expression evaluate to true when evaluated against 
		the supplied condition.
		
		@param file: The basename of the file used in the line count
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression used to match a line of the input file
		@param condition: The condition to be met for the number of lines matching the regular expression
		@param ignores: A list of regular expressions that will cause lines to be excluded from the count
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""	
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			numberLines = linecount(f, expr, ignores=ignores)
			log.debug("Number of matching lines is %d"%numberLines)
		except:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=self.__abortOnError(xargs))
		else:
			if (eval("%d %s" % (numberLines, condition))):
				msg = self.__assertMsg(xargs, 'Line count on input file %s' % file)
				self.addOutcome(PASSED, msg, abortOnError=self.__abortOnError(xargs))
			else:
				msg = self.__assertMsg(xargs, 'Line count on %s for "%s"%s (actual =%d) '%(file, expr, condition, numberLines))
				self.addOutcome(FAILED, msg, abortOnError=self.__abortOnError(xargs))


	def __assertMsg(self, xargs, default):
		"""Return an assert statement requested to override the default value.
		
		@param xargs: Variable argument list to an assert method
		@param default: Default assert statement to return if a parameter is not supplied
		
		"""
		if xargs.has_key('assertMessage'): return xargs['assertMessage']
		return default


	def __abortOnError(self, xargs):
		"""Return an assert statement requested to override the default value.

		@param xargs: Variable argument list to an assert method

		"""
		if xargs.has_key('abortOnError'): return xargs['abortOnError']
		return PROJECT.defaultAbortOnError.lower()=='true' if hasattr(PROJECT, 'defaultAbortOnError') else DEFAULT_ABORT_ON_ERROR

