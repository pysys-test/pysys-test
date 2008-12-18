#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software
"""
Contains the base class used to perform the execution and audit trail reporting of a set of tests. 

Test selection is by default performed through the pysys.py launch script, which locates and 
creates a set of class instances representing the tests to be executed. These are passed to the 
base runner as a list of object references, so that the base runner can then iterate through the 
list to perform the test execution. For more information see the L{pysys.baserunner.BaseRunner} 
API documentation. 

"""
import os, os.path, sys, stat, re, traceback, time, math, logging, string

from pysys import rootLogger
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filecopy import filecopy
from pysys.utils.filegrep import filegrep
from pysys.utils.filediff import filediff
from pysys.utils.filegrep import orderedgrep
from pysys.utils.linecount import linecount
from pysys.process.helper import ProcessWrapper
from pysys.basetest import BaseTest
from pysys.process.user import ProcessUser

log = logging.getLogger('pysys.baserunner')
log.setLevel(logging.NOTSET)


class BaseRunner(ProcessUser):
	"""The base class for executing a set of PySys testcases.

	BaseRunner is the parent class for running a set of PySys system testcases. The runner is instantiated 
	with a list of L{pysys.xml.descriptor.XMLDescriptorContainer} objects detailing the set of testcases to be run. 
	The runner iterates through the descriptor list and for each entry imports the L{pysys.basetest.BaseTest}
	subclass for the testcase, creates an instance of the test class and then calls the setup, execute, validate 
	and cleanup methods of the test class instance. The runner is responsible for ensuring the output 
	subdirectory of each testcase is purged prior to test execution to remove stale output from a previous run, 
	detects any core files produced during execution of a testcase from processes started via the L{pysys.process} 
	module, and performs audit trail logging of the test results on completion of running a set of testcases.
	
	The base runner contains the hook functions L{setup}, L{testComplete}, L{cycleComplete} and L{cleanup} to 
	allow a subclass to perform custom operations prior to the execution of a set of testcases, between the 
	execution of each testcase in a set, between each cycle of execution of a set of testcases, and on completion 
	of all testcases respectively. Subclasses are typically used should some global conditions need to be setup 
	prior to the set of testcasess being run (i.e. load data into a shared database, start an external process 
	etc), and subsequently cleaned up after test execution. 
	      
	@ivar mode: The user defined modes to run the tests within
	@type mode: string
	@ivar outsubdir: The directory name for the output subdirectory 
	@type outsubdir: string
	@ivar log: Reference to the logger instance of this class
	@type log: logging.Logger
	@ivar project: Reference to the project details as set on the module load of the launching executable  
	@type project: L{Project}
	
	"""
	
	def __init__(self, record, purge, cycle, mode, outsubdir, descriptors, xargs):
		"""Create an instance of the BaseRunner class.
		
		@param record: Indicates if the test results should be recorded 
		@param purge: Indicates if the output subdirectory should be purged on C{PASSED} result
		@param cycle: The number of times to execute the set of requested testcases
		@param mode: The user defined mode to run the testcases in
		@param outsubdir: The name of the output subdirectory
		@param descriptors: List of XML descriptor containers detailing the set of testcases to be run
		@param xargs: The dictionary of additional arguments to be set as data attributes to the class
		
		"""
		ProcessUser.__init__(self)
		self.record = record
		self.purge = purge
		self.cycle = cycle
		self.mode = mode
		self.outsubdir = outsubdir
		self.descriptors = descriptors
		self.xargs = xargs
		self.setKeywordArgs(xargs)
		self.log = log
		self.project = PROJECT
	
		self.writers = []
		for classname, module, filename, properties in PROJECT.writers:
			exec( "from %s import %s" % (module, classname) )	
			exec( "writer = %s(\"%s\")" % (classname, filename) )
			for key in properties.keys(): setattr(writer, key, properties[key])
			self.writers.append(writer)


	def setKeywordArgs(self, xargs):
		"""Set the xargs as data attributes of the class.
				
		Values in the xargs dictionary are set as data attributes using the builtin C{setattr()} method. 
		Thus an xargs dictionary of the form C{{'foo': 'bar'}} will result in a data attribute of the 
		form C{self.foo} with C{value bar}. 
		
		@param xargs: A dictionary of the user defined extra arguments
		
		"""
		for key in xargs.keys():
			setattr(self, key, xargs[key])


	# utility methods
	def purgeDirectory(self, dir, delTop=False):
		"""Recursively purge a directory removing all files and sub-directories.
		
		@param dir: The top level directory to be purged
		@param delTop: Indicates if the top level directory should also be deleted
		
		"""
		for file in os.listdir(dir):
		  	path = os.path.join(dir, file)
		  	if PLATFORM in ['sunos', 'linux']:
		  		mode = os.lstat(path)[stat.ST_MODE]
		  	else:
		  		mode = os.stat(path)[stat.ST_MODE]
		
			if stat.S_ISLNK(mode):
				os.unlink(path)
			if stat.S_ISREG(mode):
				os.remove(path)
			elif stat.S_ISDIR(mode):
			  	self.purgeDirectory(path, delTop=True)				 

		if delTop: os.rmdir(dir)


	def detectCore(self, dir):
		"""Detect any core files in a directory (unix systems only), returning C{True} if a core is present.
		
		@param dir: The directory to search for core files
		@return: C{True} if a core detected, None if no core detected
		@rtype: integer 
		"""
		for file in os.listdir(dir):
			path = os.path.join(dir, file)
			mode = os.stat(path)[stat.ST_MODE]

			if stat.S_ISREG(mode):
				if re.search('^core', file): return True

	
	# methods to allow customer actions to be performed before a test run, after a test, after 
	# a cycle of all tests, and after all cycles
	def setup(self):
		"""Setup method which may optionally be overridden to perform custom setup operations prior to execution of a set of testcases.
		
		"""
		pass


	def testComplete(self, testObj, dir):
		"""Test complete method which performs completion actions after execution of a testcase.
		
		The testComplete method performs purging of the output subdirectory of a testcase on completion 
		of the test execution. Purging involves removing all files with a zero file length in order to 
		only include files with content of interest. Should C{self.purge} be set, the purging will remove
		all files (excluding the run.log) on a C{PASSED} outcome of the testcase in order to reduce the 
		on-disk memory footprint when running a large number of tests. Should a custom testComplete for 
		a subclass be required, the BaseRunner testComplete method should first be called.
		
		@param testObj: Reference to the L{pysys.basetest.BaseTest} instance of the test just completed
		@param dir: The directory to perform the purge on
				
		"""
		if self.purge:
			removeNonZero = True
			for outcome in testObj.outcome:
				if outcome != PASSED:
					removeNonZero = False
					break
		else:
			removeNonZero = False

		try:
			for file in os.listdir(dir):
				path = "%s/%s" % (dir, file)
				if PLATFORM in ['sunos', 'linux']:
					size = os.lstat(path)[stat.ST_SIZE]
				else:
					size = os.stat(path)[stat.ST_SIZE]

				if (size == 0) or (removeNonZero and not re.search('run.log', file)):
					count = 0
					while count < 3:
						try:
							os.remove(path)
							break
						except:
							time.sleep(0.1)
							count = count + 1
		except OSError:
			pass


	def cycleComplete(self):
		"""Cycle complete method which may optionally be overridden to perform custom operations between the repeated execution of a set of testcases.
		
		"""
		pass


	def cleanup(self):
		"""Cleanup method which may optionally be overridden to perform custom cleanup operations after execution of all testcases.
		
		"""
		ProcessUser.__del__(self)


	# perform a test run
	def start(self, printSummary=True):
		"""Start the execution of a set of testcases, returning a dictionary of the testcase outcomes.
		
		The start method is the main method for executing the set of requested testcases. The set of testcases 
		are executed a number of times determined by the C{self.cycle} attribute. When executing a testcase 
		all output from the execution is saved in the testcase output subdirectory; should C{self.cycle} be 
		set to more than 1, the output subdirectory is further split into cycle[n] directories to sandbox the 
		output from each iteration.
		
		@param printSummary: Indicates if the test results should be reported on test completion
	
		"""
		results = {}
		totalDuration = 0
		totalExecuted = 0

		# call the hook to setup prior to running tests
		self.setup()

		# call the hook to setup the test output writers
		if self.record:
			for writer in self.writers:
				try: writer.setup(numTests=self.cycle * len(self.descriptors))
				except: log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

		# loop through each cycle
		for cycle in range(self.cycle):
			results[cycle] = {}
			for outcome in PRECEDENT: results[cycle][outcome] = []

			# loop through tests for the cycle
			for descriptor in self.descriptors:
				startTime = time.time()
				blocked = False
				keyboardInterupt = False

				# set the output subdirectory and purge contents
				try:
					outsubdir = self.outsubdir
					if not os.path.exists(os.path.join(descriptor.output, outsubdir)):
						os.makedirs(os.path.join(descriptor.output, outsubdir))
					
					if cycle == 0: self.purgeDirectory(os.path.join(descriptor.output, outsubdir))
				
					if self.cycle > 1: 
						outsubdir = os.path.join(outsubdir, 'cycle%d' % (cycle+1))
						os.makedirs(os.path.join(descriptor.output, outsubdir))

					outputDirectory = os.path.join(descriptor.output, outsubdir)
				except:
					log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
					outputDirectory = ""
					blocked = True

				# create the logger handler for the run log
				runLogger = logging.FileHandler(os.path.join(outputDirectory, 'run.log'))
				runLogger.setFormatter(logging.Formatter('%(asctime)s %(levelname)-5s %(message)s'))
				runLogger.setLevel(logging.DEBUG)
				rootLogger.addHandler(runLogger)			

				# run the test execute, validate and cleanup methods
				log.info("==========================================")
				log.info("		" + descriptor.id)
				log.info("==========================================")
				try:
					sys.path.append(os.path.dirname(descriptor.module))
					exec( "from %s import %s" % (os.path.basename(descriptor.module), descriptor.classname) )
					exec( "testObj = %s(descriptor, r'%s', self)" % (descriptor.classname, outsubdir) )
				except:
					log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
					testObj = BaseTest(descriptor, outsubdir, self) 
					blocked = True
				sys.path.pop()
				
				if descriptor.state != 'runnable':
					testObj.outcome.append(SKIPPED)
					
				elif self.mode and self.mode not in descriptor.modes:
					log.info("Unable to run test in %s mode", self.mode)
					testObj.outcome.append(SKIPPED)

				elif blocked:
					log.info("Errors setting up test for execution")
					testObj.outcome.append(BLOCKED)

				else:
					try:
						testObj.setup()
						testObj.execute()
					except KeyboardInterrupt:
						keyboardInterupt = True
						log.info("test interrupt from keyboard")
						testObj.outcome.append(BLOCKED)
					except:
						log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
						testObj.outcome.append(BLOCKED)
					else:
						try:
						  	testObj.validate()
						except KeyboardInterrupt:
							keyboardInterupt = True
							log.info("test interrupt from keyboard")
							testObj.outcome.append(BLOCKED)
						except:
						  	log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
						  	testObj.outcome.append(BLOCKED)
					
						try:
							if self.detectCore(outputDirectory):
								log.info("core detected in output subdirectory")
								testObj.outcome.append(DUMPEDCORE)
						except:
							log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

					try:
						testObj.cleanup()
					except KeyboardInterrupt:
						keyboardInterupt = True
						log.info("test interrupt from keyboard")
						testObj.outcome.append(BLOCKED)
					except:
						log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

				# get and log the final outcome for the test
				testTime = math.floor(100*(time.time() - startTime))/100.0
				totalDuration = totalDuration + testTime
				outcome = testObj.getOutcome()
				results[cycle][outcome].append(descriptor.id)
				log.info("")
				log.info("Test duration %.2f secs", testTime)
				log.info("Test final outcome %s", LOOKUP[outcome])
				log.info("")
				if rootLogger.getEffectiveLevel() == logging._levelNames['CRITICAL']: log.critical("%s: %s", LOOKUP[outcome], descriptor.id)
				
				# call the hook for end of test execution
				self.testComplete(testObj, outputDirectory)
				totalExecuted = totalExecuted + 1
				
				# pass the test object to the test writers is recording
				if self.record:
					for writer in self.writers:
						try: writer.processResult(testObj, cycle=cycle)
						except: log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
				
				# perform cleanup actions
				try: del sys.modules["%s" % os.path.basename(descriptor.module)]
				except: pass
				del testObj

				# remove the run logger handler
				runLogger.close()
				rootLogger.removeHandler(runLogger)

				# prompt for continuation on control-C
				if keyboardInterupt == True:
					while 1:
						print ""
						print "Keyboard interupt detected, continue running tests? [yes|no] ... ",
						line = string.strip(sys.stdin.readline())
						if line == "y" or line == "yes":
							break
						elif line == "n" or line == "no":
							self.cycleComplete()
							self.cleanup()
							sys.exit(1)

			# call the hook for end of cycle
			try:
				self.cycleComplete()
			except:
				log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

		# perform cleanup on the test writers
		if self.record:
			for writer in self.writers:
				try: writer.cleanup()
				except: log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			
		# log the summary output to the console
		if printSummary:
			log.info("")
			log.info("Total duration: %.2f (secs)", totalDuration)		
			log.info("Summary of non passes: ")
			fails = 0
			for cycle in results.keys():
				for outcome in results[cycle].keys():
					if outcome in FAILS : fails = fails + len(results[cycle][outcome])
			if fails == 0:
				log.info("	THERE WERE NO NON PASSES")
			else:
				if len(results) == 1:
					for outcome in FAILS:
						for id in results[0][outcome]: log.info("  %s: %s ", LOOKUP[outcome], id)
				else:
					for key in results.keys():
						for outcome in FAILS:
							for id in results[key][outcome]: log.info(" [CYCLE %d] %s: %s ", key+1, LOOKUP[outcome], id)

		# call the hook to cleanup after running tests
		self.cleanup()

		# return the results dictionary
		return results



	


