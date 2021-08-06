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


"""
Contains the test class used to run PyUnit tests. 

A suite of PyUnit tests becomes a single PySys test. 
"""

from __future__ import print_function
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.pycompat import openfile
import glob, os, unittest

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
		pyfiles = self._findPythonFiles()
		for pyfile in pyfiles:
			self._runTestFile(pyfile)

	def _findPythonFiles(self):
		return  glob.glob(os.path.join(self.input , '*.py'))

	def _runTestFile(self, testFile):
		globals = {}
		locals = {}
		displayName = 'PyUnit'
		instance = self.getInstanceCount(displayName)
		dstdout = os.path.join(self.output, 'pyunit.out')
		dstderr = os.path.join(self.output, 'pyunit.err')
		if instance: dstdout  = "%s.%d" % (dstdout, instance)
		if instance: dstderr  = "%s.%d" % (dstderr, instance)
		arguments = [__file__, testFile]		
		environ = os.environ.copy()
		environ['PYTHONPATH'] = os.pathsep.join(self.getPythonPath() + sys.path)
		process = self.startPython(arguments, environs=environ, workingDir=self.output, 
			state=FOREGROUND, timeout=DEFAULT_TIMEOUT, 
			stdout=dstdout, stderr=dstderr, 
			displayName=displayName, ignoreExitStatus=True, quiet=True)
		if process.exitStatus:
			self.addOutcome(FAILED, 'Non-zero exit code from %s'%os.path.basename(testFile), printReason=False)
		else:
			self.addOutcome(PASSED)
		with openfile(dstdout, encoding=self.getDefaultFileEncoding(dstdout)) as f:
			for l in f:
				self.log.info(l.rstrip())

	def getPythonPath(self):
		"""Override this method to return a sequence of paths to put
		at the beginning of the PYTHONPATH when running the PyUnit
		tests. See PyUnit_test_002 for an example of this.
		"""
		return []

class __PysysTestResult(unittest.TestResult): # pragma: no cover (undocumented, little used executable entry point)
	
	def __init__(self):
		unittest.TestResult.__init__(self)
		self.successes = []

	def addSuccess(self, test):
		self.successes.append(test)

if __name__ == '__main__': # pragma: no cover (undocumented, little used executable entry point)

	def getTestClasses(testFile):
		globals = {}
		# Use globals dictionary for locals as well because we
		# want to treat this like it is being run in a global
		# (file scope) context)
		exec(compile(openfile(testFile).read(), testFile, 'exec'), globals, globals)
		testClasses = []
		for k, v in list(globals.items()):
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
	results = __PysysTestResult()
	
	globals['_suite_'] = suite
	globals['_results_'] = results
	
	eval('_suite_.run(_results_)', globals)

	for r in results.successes:
		print(getTestName(r)+' ... passed')
	for r in results.errors:
		print(getTestName(r[0])+ ' ... failed')
		print(r[1].rstrip())
	for r in results.failures:
		print(getTestName(r[0])+' ... failed')
		print(r[1].rstrip())
	
	if results.wasSuccessful():
		sys.exit(0)
	else:
		sys.exit(1)

