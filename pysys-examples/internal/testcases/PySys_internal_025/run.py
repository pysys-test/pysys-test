import string, shutil
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = "%s/workingdir.py" % self.input
		self.copy(self.input+'/dir', self.output+'/parent/my-working-dir')
		
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script],
						  environs = os.environ,
						  workingDir = os.path.join(self.output, 'parent/my-working-dir'),
						  stdout = "%s/workingdir.out" % self.output,
						  stderr = "%s/workingdir.err" % self.output,
						  state=FOREGROUND)

		# wait for the strings to be writen to sdtout
		self.waitForGrep("workingdir.err", expr="Current working directory is", timeout=5)
		self.waitForGrep("workingdir.out", expr="Written contents of working directory", timeout=5)
			
		
	def validate(self):
		# validate the working directory of the process
		self.assertGrep("workingdir.err", expr="Current working directory is %s$"%os.path.join(self.output, 'parent/my-working-dir').replace("\\", "/"))
		
		# validate against the reference file
		self.assertDiff("workingdir.out", "ref_workingdir.out", ignores=['.svn'], sort=True)
