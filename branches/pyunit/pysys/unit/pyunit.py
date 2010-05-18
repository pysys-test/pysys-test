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
	Class for running PyUnit tests (standard Python unittest module). The
	execute method will execute all the .py files, find all the
	unittest.TestCase classes within those files and run the test methods
	within them. A separate Python process will be spawned for each input
	test file. By default child Python processes will have the same
	PYTHONPATH as the python process which is running pysys. However,
	this can be changed by overriding the getPythonPath() method.
	"""

	def execute(self):
		"""
		Implementation of the execute() abstract method which simply
		calls executePyUnitTests()
		"""
		self.executePyUnitTests()

	def executePyUnitTests(self):
		"""
		Run all the PyUnit tests in the Input directory.
		"""
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
		environ['PYTHONPATH'] = os.pathsep.join(self.getPythonPath() + sys.path)
		process = self.startProcess(command, arguments, environ, self.output, FOREGROUND, DEFAULT_TIMEOUT, dstdout, dstderr, displayName)
		self.log.setLevel(logLevel)
		if process.exitStatus:
			self.outcome.append(FAILED)
		else:
			self.outcome.append(PASSED)
		for l in open(dstdout):
			self.log.info(l.rstrip())

	def getPythonPath(self):
		"""Override this method to return a sequence of paths to put
		at the beginning of the PYTHONPATH when running the PyUnit
		tests. See PyUnit_test_002 for an example of this.
		"""
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

	def getTestName(testcase):
		name = testcase.id()
		return name.replace('__builtin__.','')

	testFile = sys.argv[1]

	suite, globals = createTestSuite(testFile)
	results = PysysTestResult()
	
	globals['_suite_'] = suite
	globals['_results_'] = results
	
	eval('_suite_.run(_results_)', globals)

	for r in results.successes:
		print getTestName(r), '... passed'
	for r in results.errors:
		print getTestName(r[0]), '... failed'
		print r[1].rstrip()
	for r in results.failures:
		print getTestName(r[0]), '... failed'
		print r[1].rstrip()
	
	if results.wasSuccessful():
		sys.exit(0)
	else:
		sys.exit(1)

