from pysys.unit.junit import JUnitTest
import os

class PySysTest(JUnitTest):
	def execute(self):
		self.compileJavaFiles(os.path.join(self.project.root, 'junit', 'utilities'), ['totest/Factorial.java'])
		JUnitTest.execute(self)
