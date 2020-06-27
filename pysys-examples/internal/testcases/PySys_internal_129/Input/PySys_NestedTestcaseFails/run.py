from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import random

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(FAILED, 'Simulated failure')
		
		def makeFile(f):
			# use random numbers so it's not compressible
			r = random.Random(12345)
			# generate a 1 kB file
			with open(os.path.join(self.output, f), 'wb') as fp:
				fp.write( 
				bytearray(random.getrandbits(8) for _ in range(1024))
				)

				#b''.join(chr(r.randint(0, 255))
				#for x in range(1024)
		
		makeFile('f1.txt')
		makeFile('f2.txt')
		makeFile('f3.txt')
		makeFile(self.mkdir('a/b')+'/nested.txt')

		# i18n
		#with open(self.output+'/a\xa3.txt', 'w') as f: f.write('abc')
		
		# should be deleted
		with open(self.output+'/empty.txt', 'w') as f: pass

	def validate(self):
		pass 
