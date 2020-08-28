import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
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
		self.copy('output-i18n.txt', 'output-i18n.txt') # src=dest should work for files
		self.copy('output-i18n.txt', 'output-i18n-binary.txt')
		self.copy('output-i18n.txt', 'output-i18n-binary.txt') # check overwrite works by default for files
		self.copy('output-i18n.txt', 'output-i18n-processed.txt', encoding='utf-8', 
			mappers=[lambda line: line.replace(self.utf8teststring, 'Foo bar')]
			)
		
		# setup
		self.mkdir('srcdirname/subdir1/subdir2')
		self.write_text('srcdirname/src.txt', 'src.txt')
		self.write_text('srcdirname/subdir1/subdir2/src2.txt', 'src2.txt')
		try:
			os.symlink(self.output+'/srcdirname/src.txt', self.output+'/srcdirname/symlink.txt')
			symlinks = True
		except Exception as ex:
			self.log.info('This platform does not support symlinks, so skipping that bit of the test: %s', ex)
			symlinks = False
		self.mkdir('srcdirname/subdir3')
		
		# directory copies
		self.assertPathExists(self.copy('srcdirname', 'dest-dir')) # dir doesn't already exist, so 
		self.assertPathExists(self.output+'/dest-dir/src.txt')
		self.assertPathExists(self.output+'/dest-dir/subdir1/subdir2/src2.txt')
		self.assertPathExists(self.output+'/dest-dir/subdir3')
		self.assertPathExists(self.output+'/dest-dir/symlink.txt', exists=symlinks)
		
		if symlinks:
			self.copy('srcdirname', 'dest-dir-symlinks', symlinks=True)
			self.assertThat('    os.path.islink(self.output+"/dest-dir-symlinks/symlink.txt")')
			self.assertThat('not os.path.islink(self.output+"/dest-dir/symlink.txt")')
			self.assertGrep(self.output+"/dest-dir-symlinks/symlink.txt", expr='.') # check not a broken link

		self.copy('srcdirname', self.mkdir(self.output+'/dest-copyinto')+'/')
		self.assertPathExists(self.output+'/dest-copyinto/srcdirname/src.txt')

		self.copy('srcdirname', 'dest-dir-slash/')
		self.assertPathExists(self.output+'/dest-dir-slash/srcdirname/src.txt')

		self.copy('srcdirname', 'dest-dir-slash2\\')
		self.assertPathExists(self.output+'/dest-dir-slash2/srcdirname/src.txt')

		try:
			self.copy('srcdirname', 'dest-dir-slash2\\')
		except Exception as ex:
			self.assertThat('"unless overwrite=True" in errorMessage', errorMessage=str(ex))
		else:
			self.addOutcome(FAILED, 'Expected error from copying to a path that already exists')
		self.copy('srcdirname', 'dest-dir-slash2\\', overwrite=True)

		self.copy('srcdirname', 'dest-with-ignores', ignoreIf=lambda src: src.endswith(('src2.txt', 'subdir3')))
		self.assertPathExists(self.output+'/dest-with-ignores/src.txt')
		self.assertPathExists(self.output+'/dest-with-ignores/subdir3/', exists=False)
		self.assertPathExists(self.output+'/dest-with-ignores/subdir1/subdir2/')
		self.assertPathExists(self.output+'/dest-with-ignores/subdir1/subdir2/src2.txt', exists=False)

		self.copy('srcdirname', 'dest-with-skip-mappers', skipMappersIf=lambda src: src.endswith(('src.txt')), 
			mappers=[lambda line: 'mapper-result'])
		self.assertGrep('dest-with-skip-mappers/src.txt', expr='src.txt')
		self.assertGrep('dest-with-skip-mappers/subdir1/subdir2/src2.txt', expr='src', contains=False)
		self.assertGrep('dest-with-skip-mappers/subdir1/subdir2/src2.txt', expr='mapper-result')

		# this example is in the doc
		class CustomLineMapper(object):
			def fileStarted(self, srcPath, destPath, srcFile, destFile):
				self.src = os.path.basename(srcPath)
			
			def __call__(self, line):
				return '"'+self.src+'": '+line
			
			def fileFinished(self, srcPath, destPath, srcFile, destFile):
				destFile.write('\n' + 'footer added by CustomLineMapper')
				
		# and this one (mix of samples from assertDiff() and copy()
		self.write_text('myfile.txt', 'Hello\nError message BAD THING 2020-01-02 01:23:45.1234:\n   stack trace\n   here\n\nMore text after the blank line')
		self.assertDiff(self.copy('myfile.txt', 'myfile-processed.txt', mappers=[
			pysys.mappers.IncludeLinesBetween('Error message .*:', stopBefore='^$'),
			pysys.mappers.RegexReplace(pysys.mappers.RegexReplace.DATETIME_REGEX, '<timestamp>'),
		]))

		
		# just to show we can also add them to lambdas if we want to
		counter = lambda line: line
		count = [0]
		def incrementCounter(srcPath, destPath, srcFile, destFile): 
			count[0]+=1
		counter.fileStarted = incrementCounter
		self.copy('srcdirname/src.txt', 'dest.txt', mappers=[CustomLineMapper(), counter, None])
		self.assertThat('mappedFileCount == 1', mappedFileCount=count[0])

	def validate(self):
		self.assertDiff('output-processed.txt', 'ref-output-processed.txt')
		self.assertDiff('output-i18n-processed.txt', 'ref-output-i18n-processed.txt')
		self.assertEval('{sizeI18NBinarySrc} == {sizeI18NBinaryDest}', 
			sizeI18NBinarySrc = os.path.getsize(self.output+'/output-i18n.txt'),
			sizeI18NBinaryDest = os.path.getsize(self.output+'/output-i18n-binary.txt'))
