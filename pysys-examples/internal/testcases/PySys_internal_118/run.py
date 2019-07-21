from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	utf8teststring = b'utf8_European\\xe1\\xc1x\\xdf_Katakana\\uff89\\uff81\\uff90\\uff81\\uff7f\\uff78\\uff81\\uff7d\\uff81\\uff7f\\uff76\\uff72\\uff7d\\uff84_Hiragana\\u65e5\\u672c\\u8a9e_Symbols\\u2620\\u2622\\u2603_abc123@#\\xa3!~=\\xa3x'.decode('unicode_escape')

	def execute(self):
		self.write_text('output-raw.txt', 'Hello world\nTimestamp: 1234\nHello foo!')
		
		# this is the example from the docstring
		self.copy('output-raw.txt', 'output-processed.txt', encoding='utf-8', 
			mappers=[
				lambda line: None if ('Timestamp: ' in line) else line, 
				lambda line: line.replace('foo', 'bar'), 
			])

		self.write_text('output-i18n.txt', self.utf8teststring, encoding='utf-8')
		self.copy('output-i18n.txt', 'output-i18n-binary.txt')
		self.copy('output-i18n.txt', 'output-i18n-processed.txt', encoding='utf-8', 
			mappers=[lambda line: line.replace(self.utf8teststring, 'Foo bar')]
			)

	def validate(self):
		self.assertDiff('output-processed.txt', 'ref-output-processed.txt')
		self.assertDiff('output-i18n-processed.txt', 'ref-output-i18n-processed.txt')
		self.assertEval('{sizeI18NBinarySrc} == {sizeI18NBinaryDest}', 
			sizeI18NBinarySrc = os.path.getsize(self.output+'/output-i18n.txt'),
			sizeI18NBinaryDest = os.path.getsize(self.output+'/output-i18n-binary.txt'))
