from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Bar')
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Foo', contains=FALSE)
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Foo', contains=FALSE)
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Line is a foo', ignores=['Bar'])
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Line is a not foo', ignores=['Bar'], contains=FALSE)
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Bar foo humbug', includes=['humbug'])
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Bar humbug', includes=['humbug'], ignores=['foo'])
		