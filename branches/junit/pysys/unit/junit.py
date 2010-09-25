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
Contains the test class used to run JUnit tests
"""

from pysys.constants import *
from pysys.basetest import BaseTest
import glob
import os
import unittest

class JUnitTest(BaseTest):
	"""
	Class for running JUnit tests. The execute method will compile all
	.java files found under the Input directory. It will then assume they
	are all JUnit test classes and run them as such.
	"""

	def execute(self):
		"""
		Implementation of the execute() abstract method which simply
		calls executeJUnitTests()
		"""
		self.executeJUnitTests()

	def executeJUnitTests(self):
		"""
		Run all the JUnit tests in the Input directory.
		"""
		jfiles = self.findJavaFiles()
		self.compileJavaFiles(self.input, jfiles)
		classes = map(self.javaPathToClass, jfiles)
		self.runTests(classes)

	def findJavaFiles(self):
		ignoreSet = set(OSWALK_IGNORES)
		jfiles = []
		for root, dirs, files in os.walk(self.input):
			for ignore in (ignoreSet & set(dirs)): dirs.remove(ignore)
			for f in files:
				if os.path.splitext(f)[1] == '.java':
					jfiles.append(os.path.relpath(os.path.join(root, f), self.input))
		return jfiles

	def compileJavaFiles(self, workingDir, jfiles):
		command = '/usr/bin/javac'
		displayName = 'JavaC'
		instance = self.getInstanceCount(displayName)
		dstdout = os.path.join(self.output, 'javac.out')
		dstderr = os.path.join(self.output, 'javac.err')
                if instance: dstdout  = "%s.%d" % (dstdout, instance)
                if instance: dstderr  = "%s.%d" % (dstderr, instance)
		arguments = ['-d', self.output, '-cp', '/home/mark/dev/junit-4.8.2.jar:%s' % (self.output)]
		arguments.extend(jfiles)
		process = self.startProcess('/usr/bin/javac', arguments, workingDir=workingDir, stdout=dstdout, stderr=dstderr, timeout=DEFAULT_TIMEOUT, displayName=displayName)
		if process.exitStatus:
                        self.outcome.append(BLOCKED)

	def javaPathToClass(self, jfile):
		classfile = os.path.splitext(jfile)[0]
		return classfile.replace(os.sep, '.')

	def runTests(self, classes):
		command = '/usr/bin/java'
		displayName = 'Java'
		instance = self.getInstanceCount(displayName)
		dstdout = os.path.join(self.output, 'junit.out')
		dstderr = os.path.join(self.output, 'junit.err')
                if instance: dstdout  = "%s.%d" % (dstdout, instance)
                if instance: dstderr  = "%s.%d" % (dstderr, instance)
		arguments = ['-cp', '/home/mark/dev/junit-4.8.2.jar:.', 'org.junit.runner.JUnitCore']
		arguments.extend(classes)
		logLevel = self.log.level
		self.log.setLevel(logging.CRITICAL)
		environ = os.environ.copy()
		process = self.startProcess(command, arguments, environ, self.output, FOREGROUND, DEFAULT_TIMEOUT, dstdout, dstderr, displayName)
		self.log.setLevel(logLevel)
		if process.exitStatus:
			self.outcome.append(FAILED)
		else:
			self.outcome.append(PASSED)
		for l in open(dstdout):
			self.log.info(l.rstrip())

