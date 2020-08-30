from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import io

class PySysTest(BaseTest):
	def execute(self):
		# XML spec says Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
		# ignore reserved unicode surrogate character range D800-DFFF which Python doesn't handle; > x10FFFF is not valid unicode
		# explore just before and just after each set of chars )but remove \n and \r, tested elsewhere)
		controlchars = u'!\x00 !\x01 tab\x09tab !\x10 !\x11 !\x0B !\x0C !\x0E !\x19 space\x20space BMP: \uD7FF \uE000 \uFFFD !\uFFFE !\uFFFF SMP: \U00010000 \U00010001 \U0010FFFF'

		self.log.info(u'Log with control characters: %s end', controlchars)
		
		with io.open(self.output+'/control.txt', 'w', encoding='utf-8') as f:
			f.write(u'%s end'%controlchars)
		
		self.addOutcome(FAILED, u'Outcome with control characters: %s end'%controlchars)
		
	def validate(self):
		pass 
