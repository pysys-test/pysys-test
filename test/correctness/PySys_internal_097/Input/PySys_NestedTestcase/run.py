from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
from pysys.utils.pycompat import openfile
import tempfile

# This module loads various dynamic libraries so checking it loads is a good way to test we haven't broken the ability 
# to do things as a result of our env sanitization
import urllib

class PySysTest(BaseTest):
	def execute(self):
	
		self.log.info(u'Temp dir = %s', tempfile.gettempdir())
		assert os.path.exists(tempfile.gettempdir())
		
		env = self.getDefaultEnvirons()
		with openfile(self.output+'/env.txt', 'w', encoding='utf-8') as f:
			for k in sorted(env.keys()):
				f.write(u'%s=%s\n'%(k, env[k]))

		env = self.getDefaultEnvirons(command=sys.executable)
		with openfile(self.output+'/env-python.txt', 'w', encoding='utf-8') as f:
			for k in sorted(env.keys()):
				f.write(u'%s=%s\n'%(k, env[k]))
		
		self.startProcess(command=sys.executable, arguments=[self.input+'/test.py'], 
			stdout='python.out', stderr='python.err')#, ignoreExitStatus=True)
		
		if os.path.exists(self.output+'/mytemp'): # prevent it getting purged
			with openfile(self.output+'/mytemp'+'/tmpfile.txt', 'w', encoding='ascii') as f:
				f.write(u'xxx')


	def validate(self):
		pass 
