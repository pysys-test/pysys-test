from pysys.constants import *
from pysys.basetest import BaseTest
import glob
import os
import unittest

class PyUnitTest(BaseTest):
	def execute(self):
		pyfiles = glob.glob(os.path.join(self.input , '*.py'))
		for pyfile in pyfiles:
			self.runTestFile(pyfile)

	def runTestFile(self, testFile):
		globals = {}
		locals = {}
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

	def runTestMethod(self, testFile, testClass, testMethod):
		command = sys.executable
		displayName = 'PyUnit'
		instance = self.getInstanceCount(displayName)
		dstdout = os.path.join(self.output, 'pyunit.out')
		dstderr = os.path.join(self.output, 'pyunit.err')
                if instance: dstdout  = "%s.%d" % (dstdout, instance)
                if instance: dstderr  = "%s.%d" % (dstderr, instance)
		arguments = [__file__, testFile, testClass.__name__, testMethod]
		logLevel = self.log.level
		self.log.setLevel(logging.CRITICAL)
		environ = os.environ.copy()
		environ['PYTHONPATH'] = os.pathsep.join(sys.path)
		process = self.startProcess(command, arguments, environ, self.output, FOREGROUND, DEFAULT_TIMEOUT, dstdout, dstderr, displayName)
		self.log.setLevel(logLevel)
		if process.exitStatus:
			self.outcome.append(FAILED)
			self.log.info('%s.%s... failed' % (testClass.__name__, testMethod))
			f = open(dstdout)
			for line in f:
				self.log.info(line.rstrip('\r\n'))
		else:
			self.outcome.append(PASSED)
			self.log.info('%s.%s... passed' % (testClass.__name__, testMethod))

if __name__ == '__main__':
	testFile = sys.argv[1]
	testClassName = sys.argv[2]
	testMethod = sys.argv[3]

	globals = {}
	locals = {}
	execfile(testFile, globals, locals)
	for k, v in locals.items():
		if isinstance(v, type(unittest.TestCase)) and k == testClassName:
			testClass = v
			break
	globals.update(locals)

	test = testClass(testMethod)
	results = unittest.TestResult()
	globals['_test_'] = test
	globals['_results_'] = results
	eval('_test_.run(_results_)', globals)
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

