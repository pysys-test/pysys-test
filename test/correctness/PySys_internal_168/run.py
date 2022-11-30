import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.write_text('test.txt', """
			line 0 without expression.
			line 1 with expression.
			line 2 with expression.
			line 3 without expression.
			""")

		self.assertThat('actual == expected', 
			actual__eval="self.grep('test.txt', '[0-9] with e.pression')",
			expected="1 with expression")

		self.assertThat('actual == expected', 
			actual__eval="self.grep('test.txt', '[0-9] with (e.pression)')", # one unnamed group is allowed
			expected="expression")

		self.assertThat('actual == expected', 
			actual__eval="self.grep('test.txt', '(?P<num>[0-9]) with (e.pression)')", # unnamed group is ignored
			expected={'num': '1'})

		self.assertThat('actual == expected', 
			actual__eval="self.grepOrNone('test.txt', '[0-9] with e.pression')",
			expected="1 with expression")

		self.assertThat('actual == expected', 
			actual__eval="self.grepOrNone('test.txt', '[0-9] xxxxxx with e.pression')",
			expected=None)

		self.assertThat('actual == expected', 
			actual__eval="self.grepAll('test.txt', '[0-9] with e.pression')",
			expected=["1 with expression", "2 with expression"])

		self.assertThat('actual == expected', 
			actual__eval="self.grepAll('missing.txt', '[0-9] with e.pression', mustExist=False)",
			expected=[])
		self.assertThat('actual is None', 
			actual__eval="self.grepOrNone('missing.txt', '[0-9] with e.pression', mustExist=False)")

	
	def validate(self):
		pass
	