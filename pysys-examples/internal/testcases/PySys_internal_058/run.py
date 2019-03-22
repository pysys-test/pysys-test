from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		x = self.allocateUniqueStdOutErr('key')
		self.assertThat('%r.endswith("key.out")', os.path.basename(x[0]))
		self.assertThat('%r.endswith("key.err")', os.path.basename(x[1]))
		self.assertThat('len(%r)>10 and len(%r)>10', x[0], x[1]) # absolute paths

		x = self.allocateUniqueStdOutErr('key')
		self.assertThat('%r.endswith("key.1.out")', os.path.basename(x[0]))
		self.assertThat('%r.endswith("key.1.err")', os.path.basename(x[1]))

		x = self.allocateUniqueStdOutErr('key')
		self.assertThat('%r.endswith("key.2.out")', os.path.basename(x[0]))
		self.assertThat('%r.endswith("key.2.err")', os.path.basename(x[1]))

		x = self.allocateUniqueStdOutErr('keyb')
		self.assertThat('%r.endswith("keyb.out")', os.path.basename(x[0]))
		self.assertThat('%r.endswith("keyb.err")', os.path.basename(x[1]))

				
	def validate(self):
		pass
