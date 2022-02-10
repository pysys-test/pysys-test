import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re

class PySysTest(BaseTest):

	def execute(self):
		self.pysys.pysys('makeproject', ['makeproject'])
		self.pysys.pysys('makeproject-custom', ['makeproject', '--dir', self.output+'/mytestRootDir', '--template=default'])
		
		# should not overwrite even though filename is different
		open(self.mkdir(self.output+'/fakeprojroot')+'/pysysproject.xml','w').close()
		exitcode = self.pysys.pysys('makeproject-alreadyexists', ['makeproject', '--dir', 'fakeprojroot'], expectedExitStatus='!=0')

		self.pysys.pysys('make', ['make', 'MyNewTest'])
		self.pysys.pysys('make', ['make', 'MyNewTestUncommented'])
		self.pysys.pysys('run-before-setting-title', ['run','MyNewTest', '-o', self.output+'/run-before-setting-title'], expectedExitStatus='!=0')

		self.copy('MyNewTest/pysystest.py', 'MyNewTest/pysystest.py', mappers=[
			pysys.mappers.RegexReplace(' TODO', ' <todo>'),
			pysys.mappers.RegexReplace(r'\t\tpass', r'\t\tself.log.info("Input dir = %s", self.input)'),
		])
		self.pysys.pysys('run-MyNewTest', ['run','MyNewTest', '-o', 'output-MyNewTest'])

		self.copy('MyNewTestUncommented/pysystest.py', 'MyNewTestUncommented/pysystest.py', mappers=[
			pysys.mappers.RegexReplace('^#', ''), # uncomment the commented bits to make sure they work
			pysys.mappers.RegexReplace(r'\s*======*', '# (underline waz here)'),   # need to nuke the separator too
		])

		self.pysys.pysys('print', ['print', '--full'])

	def validate(self):

		self.assertGrep('make.err', expr='.*', contains=False) # no errors
		self.assertGrep('makeproject.err', expr='.*', contains=False) # no errors
		self.assertGrep('makeproject-custom.err', expr='.*', contains=False) # no errors

		self.assertThat('not os.path.isdir(%s)', repr(self.output+'/MyNewTest/Input'))
		self.assertThat('not os.path.isfile(%s)', repr(self.output+'/MyNewTest/pysystest.xml'))
		self.assertThat('os.path.isfile(%s)', repr(self.output+'/MyNewTest/pysystest.py'))

		self.assertThatGrep('MyNewTest/pysystest.py', '     +(=+)$', 'len(value) == expected', expected=80)

		self.assertGrep('MyNewTest/pysystest.py', expr='@', contains=False) # no unsubstituted values
	
		# check for correct default outcome for new tests
		self.assertThatGrep('run-MyNewTest.out', 'Test final outcome *: *(.*)', expected='NOT VERIFIED') 
		self.assertThatGrep('run-MyNewTest.out', r'Input dir = .*([/\\][^/\\\n]+)$', r'not value.endswith((".", "/", "\\"))') 

		self.assertThatGrep('run-before-setting-title.out', 'Test final outcome *: *(.*)', expected='BLOCKED') 
		self.assertThatGrep('run-before-setting-title.out', 'Test outcome reason*: *(.*)', expected='Test title is still TODO') 
		
		self.assertDiff(
			self.copy('print.out', 'print.out', mappers=[
				pysys.mappers.RegexReplace(r' \d\d\d\d-\d\d-\d\d', ' <date waz here>')
			]))
		
		# makeproject checks
		self.assertGrep('makeproject-alreadyexists.out', expr='Cannot create as project file already exists: .+')
		self.assertDiff(self.output+'/pysysproject.xml', self.output+'/mytestRootDir/pysysproject.xml')
		self.assertGrep('makeproject.out', expr='Successfully created project configuration')
		self.logFileContents('makeproject.out')

		self.assertGrep('pysysproject.xml', expr=r'<requires-pysys>\d+[.]\d+</requires-pysys>')
		self.assertGrep('pysysproject.xml', expr=r'<requires-python>\d+[.]\d+[.]\d+</requires-python>')
		self.assertGrep('pysysproject.xml', expr=r'@.*', contains=False) # unsubstituted tokens
		