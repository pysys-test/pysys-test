import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.pysys.pysys('pysys-make-list-root', ['make', '-h'], workingDir=self.input)
		self.pysys.pysys('pysys-make-list-dir1', ['make', '-h'], workingDir=self.input+'/dir1')
		self.pysys.pysys('pysys-make-list-dir2', ['make', '-h'], workingDir=self.input+'/dir1/dir2')

		# run from subdir to check that template is picked up relative to the dirconfig not to the cwd
		self.pysys.pysys('pysys-make', ['make', self.output+'/MyNewTest'], workingDir=self.input+'/dir1/dir2/subdir')
		self.pysys.pysys('pysys-make-custom-mkdir', ['make', '--template=mytmpl-project2', self.output+'/MyNewTestWithCustomMkdir'], workingDir=self.input+'/dir1/dir2')

		for x in ['badcopydir', 'badcopyglob', 'badname', 'badregex']:
			self.pysys.pysys('pysys-make-error-'+x, ['make', '-h'], workingDir=self.input+'/dir1/dir2/'+x, expectedExitStatus='!=0')

	def validate(self):
		self.logFileContents('pysys-make-list-dir2.out', maxLines=0)
	
		for x in ['pysys-make-list-root', 'pysys-make-list-dir1', 'pysys-make-list-dir2']:
			self.logFileContents(self.copy(x+'.out', x+'.txt', mappers=[pysys.mappers.IncludeLinesBetween(startAfter='Available templates', stopBefore=' +[(]')]))
			self.assertDiff(x+'.txt')
		self.log.info('')

		for x in ['badcopydir', 'badcopyglob', 'badname', 'badregex']:
			self.assertThatGrep('pysys-make-error-'+x+'.err', '.+', 're.match(expected, value)', 
				expected='ERROR: .* ".....+pysysdirconfig.xml"')

		self.assertThatGrep('pysys-make-error-badcopydir.err', '.+', 're.match(expected, value)', 
			expected=r'ERROR: Cannot find any file or directory ".......................+[\\/]non-existent-copy-dir[\\/][*]" in maker template "bad-tmpl" of ".+"')
		self.assertThatGrep('pysys-make-error-badcopyglob.err', '.+', 're.match(expected, value)', 
			expected=r'ERROR: Cannot find any file or directory ".......................+[\\/]non-existent[*]" in maker template "bad-tmpl" of ".+"')
			
		self.assertThatGrep('pysys-make-error-badname.err', '.+', 'value.startswith(expected)', 
			expected='ERROR: Invalid template name "bADname" - must be lowercase and use hyphens not underscores/spaces for separating words, in ')

		self.assertThatGrep('pysys-make-error-badregex.err', '.+', 'value.startswith(expected)', 
			expected='ERROR: Invalid replacement regular expression "***bad regex" in maker template "bad-tmpl" of ')

		self.log.info('')

		###########
		# check that actually executing make did the right thing

		self.assertDiff(self.write_text('MyNewTest-files.txt', '\n'.join(pysys.utils.fileutils.listDirContents(self.output+'/MyNewTest'))))
		self.assertDiff(self.write_text('MyNewTestWithCustomMkdir-files.txt', '\n'.join(pysys.utils.fileutils.listDirContents(self.output+'/MyNewTestWithCustomMkdir'))))

		# Check replacements haven't broken encoding of existing files
		POUND_SIGN = chr(163)
		self.assertThatGrep('MyNewTest/pysystest.xml', '<title>(.*)</title>', expected='Special character '+POUND_SIGN, encoding='utf-8')
		self.assertThatGrep('MyNewTest/MySubDir/myfile.txt', 'title="(.*)"', expected='Special character '+POUND_SIGN, encoding='latin-1')

		self.assertThatGrep('MyNewTest/pysystest.xml', 'Creation date is "(.*)"', 're.match(expected, value)', expected=r'\d\d\d\d-\d\d-\d\d$', encoding='utf-8')
		self.assertThatGrep('MyNewTest/pysystest.xml', 'User is "(.*)"', expected='pysystestuser', encoding='utf-8')
		self.assertThatGrep('MyNewTest/pysystest.xml', 'Test ID is "(.*)"', expected='MyNewTest', encoding='utf-8')
		self.assertThatGrep('MyNewTest/MySubDir/myfile.txt', 'Substituted dirname=(.*),', expected='MyNewTest', encoding='latin-1')
		self.assertThatGrep('MyNewTest/SubDir1/SubDir2/subfile.txt', 'user=(.*)', expected='pysystestuser', encoding='utf-8')
		self.assertGrep('MyNewTest/SubDir1/SubDir2/subfile.txt', '@', contains=False, assertMessage='Check all @@s were substituted')
		self.assertGrep('MyNewTest/SubDir1/SubDir2/subfile.txt', '__pysys_title__', assertMessage='Check DEFAULT_DESCRIPTOR_MINIMAL did something reasonable')

		self.assertThatGrep('MyNewTestWithCustomMkdir/pysystest.xml', 'User is "(.*)"', expected='\\pysystestuser\\', encoding='utf-8')
		self.assertThatGrep('MyNewTestWithCustomMkdir/pysystest.xml', 'Test ID is "(.*)"', expected='@@DIR_NAME@@', encoding='utf-8')

