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
Contains the test class used to run pyunit tests
"""

from pysys.constants import *
from pysys.basetest import BaseTest
import glob
import os
import unittest

class PyUnitTest(BaseTest):
"""
Class for running PyUnit tests (standard Python unittest module). The execute
method will execute all the .py files, find all the unittest.TestCase
classes within those files and run the test methods within them. A separate
Python process will be spawned for each input test file. By default child
Python processes will have the same PYTHONPATH as the python process which
is running pysys. However, this can be changed by overriding the
getPythonPath() method.
"""
	def execute(self):
		pyfiles = glob.glob(os.path.join(self.input , '*.py'))
		for pyfile in pyfiles:
			self.runTestFile(pyfile)

	def runTestFile(self, testFile):
		globals = {}
		locals = {}
		command = sys.executable
		displayName = 'PyUnit'
		instance = self.getInstanceCount(displayName)
		dstdout = os.path.join(self.output, 'pyunit.out')
		dstderr = os.path.join(self.output, 'pyunit.err')
                if instance: dstdout  = "%s.%d" % (dstdout, instance)
                if instance: dstderr  = "%s.%d" % (dstderr, instance)
		arguments = [__file__, testFile]
		logLevel = self.log.level
		self.log.setLevel(logging.CRITICAL)
		environ = os.environ.copy()
		environ['PYTHONPATH'] = os.pathsep.join(sys.path + self.getPythonPath())
		process = self.startProcess(command, arguments, environ, self.output, FOREGROUND, DEFAULT_TIMEOUT, dstdout, dstderr, displayName)
		self.log.setLevel(logLevel)
		if process.exitStatus:
			self.outcome.append(FAILED)
#			self.log.info('%s.%s... failed' % (testClass.__name__, testMethod))
#			f = open(dstdout)
#			for line in f:
#				self.log.info(line.rstrip('\r\n'))
		else:
			self.outcome.append(PASSED)
#			self.log.info('%s.%s... passed' % (testClass.__name__, testMethod))
		
		
		return
		execfile(testFile, globals, locals)
		testClasses = []
		for k, v in locals.items():
			if isinstance(v, type(unittest.TestCase)):
				testClasses.append(v)
		for testClass in testClasses:
			self.runTestClass(testFile, testClass)

	def runTestClass(self, testFile, testClass):
		suite = unittest.TestSuite()
		loader = unittest.TestLoader()
		methods = loader.getTestCaseNames(testClass)
		for method in methods:
			self.runTestMethod(testFile, testClass, method)

	def getPythonPath(self):
		return []			

if __name__ == '__main__':

	class PysysTestResult(unittest.TestResult):
		
		def __init__(self):
			unittest.TestResult.__init__(self)
			self.successes = []
	
		def addSuccess(self, test):
			self.successes.append(test)

	def getTestClasses(testFile):
		globals = {}
		# Use globals dictionary for locals as well because we
		# want to treat this like it is being run in a global
		# (file scope) context)
		execfile(testFile, globals, globals)
		testClasses = []
		for k, v in globals.items():
			if isinstance(v, type(unittest.TestCase)):
				testClasses.append(v)
		return (testClasses, globals)

	def createTestSuite(testFile):
		suite = unittest.TestSuite()
		loader = unittest.TestLoader()
		testClasses, globals = getTestClasses(testFile)
		for testClass in testClasses:
			methods = loader.getTestCaseNames(testClass)
			for method in methods:
				suite.addTest(testClass(method))
		return (suite, globals)

	testFile = sys.argv[1]

	suite, globals = createTestSuite(testFile)
	results = PysysTestResult()
	
	globals['_suite_'] = suite
	globals['_results_'] = results
	
	eval('_suite_.run(_results_)', globals)
	
	print results.successes
	if results.wasSuccessful():
		sys.exit(0)
	else:
		for e in results.errors:
			for line in e[1].split('\n'):
				print line
		for e in results.failures:
			for line in e[1].split('\n'):
				print line
		sys.exit(1)

