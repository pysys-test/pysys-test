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

import os, os.path, sys, stat, re, traceback, time, math, logging, string

from pysys import rootLogger
from pysys.constants import *
from pysys.exceptions import *
from pysys.basetest import BaseTest

log = logging.getLogger('pysys.baserunner')
log.setLevel(logging.NOTSET)


class BaseRunner:

	def __init__(self, record, purge, cycle, mode, outsubdir, descriptors, xargs):
		self.record = record
		self.purge = purge
		self.cycle = cycle
		self.mode = mode
		self.outsubdir = outsubdir
		self.descriptors = descriptors
		self.xargs = xargs
		self.setKeywordArgs(xargs)


	def setKeywordArgs(self, xargs):
		for key in xargs.keys():
			try:
				exec("self.%s = xargs['%s']" % (key, key))
			except:
				pass


	def purgeDirectory(self, dir, delTop=FALSE):
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
			  	self.purgeDirectory(path, delTop=TRUE)				 

		if delTop: os.rmdir(dir)


	def detectCore(self, dir):
		for file in os.listdir(dir):
			path = os.path.join(dir, file)
			mode = os.stat(path)[stat.ST_MODE]

			if stat.S_ISREG(mode):
				if re.search('^core', file): return TRUE


	def setup(self):
		pass


	def testComplete(self, testObj, dir):
		if self.purge:
			removeNonZero = TRUE
			for outcome in testObj.outcome:
				if outcome != PASSED:
					removeNonZero = FALSE
					break
		else:
			removeNonZero = FALSE

		try:
			for file in os.listdir(dir):
				path = "%s/%s" % (dir, file)
				if PLATFORM in ['sunos', 'linux']:
					size = os.lstat(path)[stat.ST_SIZE]
				else:
					size = os.stat(path)[stat.ST_SIZE]

				if (size == 0) or (removeNonZero and not re.search('run.log', file)):
					try:
						os.remove(path)
					except:
						pass
		except OSError:
			pass


	def cycleComplete(self):
		pass


	def cleanup(self):
		pass


	def start(self, printSummary=TRUE, writers=[]):
		results = {}
		totalDuration = 0
		
		# call the hook to setup prior to running tests
		self.setup()

		# loop through each cycle
		for cycle in range(self.cycle):
			results[cycle] = {}
			for outcome in PRECEDENT: results[cycle][outcome] = []

			# loop through tests for the cycle
			for descriptor in self.descriptors:
				startTime = time.time()
				blocked = FALSE
				keyboardInterupt = FALSE

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
					blocked = TRUE

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
					exec( "testObj = %s(descriptor, r'%s', r'%s', self.xargs)" % (descriptor.classname, outsubdir, self.mode) )
				except:
					log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
					testObj = BaseTest(descriptor, outsubdir, self.mode, self.xargs) 
					blocked = TRUE
				sys.path.pop()

				if descriptor.state != 'runnable':
					testObj.outcome.append(SKIPPED)
					
				elif self.mode and self.mode not in descriptor.modes:
					log.info("Unable to run test in %s mode", CONSTANTS[self.mode])
					testObj.outcome.append(SKIPPED)

				elif blocked:
					log.info("Errors setting up test for execution")
					testObj.outcome.append(BLOCKED)

				else:
					try:
						testObj.setup()
						testObj.execute()
					except KeyboardInterrupt:
						keyboardInterupt = TRUE
						log.info("test interrupt from keyboard")
						testObj.outcome.append(BLOCKED)
					except:
						log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
						testObj.outcome.append(BLOCKED)
					else:
						try:
						  	testObj.validate()
						except KeyboardInterrupt:
							keyboardInterupt = TRUE
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
						keyboardInterupt = TRUE
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
				del sys.modules["%s" % os.path.basename(descriptor.module)]
				del testObj

				# remove the run logger handler
				rootLogger.removeHandler(runLogger)

				# prompt for continuation on control-C
				if keyboardInterupt == TRUE:
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

			# send the results for this cycle to the result writers
			if self.record:
				for writer in writers:
					try:
						writer.setup()
						writer.writeResults(results=results[cycle])
						writer.cleanup()
					except:
						log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			
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
						for test in results[0][outcome]: log.info("  %s: %s ", LOOKUP[outcome], test)
				else:
					for key in results.keys():
						for outcome in FAILS:
							for test in results[key][outcome]: log.info(" [CYCLE %d] %s: %s ", key+1, LOOKUP[outcome], test)


		# return the results dictionary
		return results



	


