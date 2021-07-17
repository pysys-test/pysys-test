import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertThat('archive == expected', archive__eval="sorted(os.listdir(self.unpackArchive('archive.tar.gz')+os.sep+'ParentDir'))", expected=['MyFile1.txt', 'MyFile2.txt'])
		self.assertThat('archive == expected', archive__eval="sorted(os.listdir(self.unpackArchive('archive.zip', 'zipoutput', autoCleanup=False)+os.sep+'ParentDir'))", expected=['MyFile1.txt', 'MyFile2.txt'])
		self.assertPathExists('archive') # the tar.zip one
		
		self.assertPathExists(self.unpackArchive('MyFile1.txt.gz'))
		self.assertPathExists(self.unpackArchive('MyFile1.txt.xz', 'xzoutput', autoCleanup=False))

	def validate(self):
		pass
	