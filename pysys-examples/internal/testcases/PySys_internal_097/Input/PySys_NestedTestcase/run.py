from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import tempfile

class PySysTest(BaseTest):
	def execute(self):
	
		self.log.info('Temp dir = %s', tempfile.gettempdir())
		assert os.path.exists(tempfile.gettempdir())
		
		env = self.getDefaultEnvirons()
		with open(self.output+'/env.txt', 'w', encoding='utf-8') as f:
			for k in sorted(env.keys()):
				f.write('%s=%s\n'%(k, env[k]))

		env = self.getDefaultEnvirons(command=sys.executable)
		with open(self.output+'/env-python.txt', 'w', encoding='utf-8') as f:
			for k in sorted(env.keys()):
				f.write('%s=%s\n'%(k, env[k]))
		
		self.startProcess(command=sys.executable, arguments=[self.input+'/test.py'], 
			stdout='python.out', stderr='python.err')#, ignoreExitStatus=True)

	def validate(self):
		pass 
