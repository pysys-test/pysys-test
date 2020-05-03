from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.write_text('myprocess.log', u'"Hello" world\nHi\n\'Hello\' beautiful world!')
		# deliberately use positional form for expr rather than expr= keyword to check it works
		waitForGrepReturnValue = self.waitForGrep('myprocess.log', '["\']Hello["\'] ', timeout=123.5, detailMessage='  (to ensure myprocess logs appropriate greetings)')
		self.assertEval('{waitForGrepReturnValue_len} == 2', waitForGrepReturnValue_len=len(waitForGrepReturnValue))
		self.assertEval('{waitForGrepReturnValue0_match} == {expected}', expected='"Hello" ', waitForGrepReturnValue0_match=waitForGrepReturnValue[0].group())
		
	def validate(self):
		pass 
