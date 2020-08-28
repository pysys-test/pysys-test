import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, zipfile, glob

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/testroot')
	
		# each test generates about 4 kB of files, 2kB of which we exclude
		# limit is 2*5 = 10 i.e. half of them
		
		# this should stop us deleting this output dir
		self.write_text(self.mkdir('testroot/__pysys_output_archives_lowArchiveLimit')+'/myfile.foo', 'xxx')
		# this should NOT stop us deleting this output dir
		self.write_text(self.mkdir('testroot/__pysys_output_archives_lowTotalLimit/test_output')+'/myfile.txt', 'xxx')
		
		runPySys(self, 'pysys', ['run', '-o', 'test_output',
			'--record', '--threads', '6', '-c', '10'
		], workingDir='testroot', expectedExitStatus='!=0')
						
	def validate(self):
		if self.assertGrep('pysys.out', expr=r'(Traceback .*| WARN .*[Ww]riter)', contains=False):
			self.logFileContents('pysys.out', tail=True, maxLines=0)
			return

		self.log.info('')

		##########
		archivedir = self.output+'/testroot/__pysys_output_archives_lowArchiveLimit'
		self.log.info('--- Checking %s', os.path.basename(archivedir))

		self.assertThat("len([f for f in files if f.endswith('.zip')])==6", files=sorted(os.listdir(archivedir)))

		self.assertThat('archiveName == expected', 
			archiveName=os.path.basename(sorted(glob.glob(archivedir+'/PySys_NestedTestcaseFails.cycle*.zip'))[0]), 
			expected='PySys_NestedTestcaseFails.cycle001.test_output.zip') # includes the cycle and the outputdirname
		
		self.assertThat("all('PySys_NestedTestcaseFails' in z and z.endswith('.zip') for z in zips if not z.endswith(('.txt', '.foo')))",
			zips=sorted(os.listdir(archivedir)))
		self.assertPathExists(archivedir+'/myfile.foo') # ensure we didn't delete this unexpected file in the archive dir

		self.assertLineCount(archivedir+'/skipped_artifacts.txt', expr='.+', condition='==4')

		with zipfile.ZipFile(glob.glob(archivedir+'/PySys_NestedTestcaseFails.cycle*.zip')[0]) as zf:
			self.assertThat('badZipFiles is None', badZipFiles=zf.testzip())
			members = sorted(zf.namelist())
			zf.extractall(self.output+'/extracted-zip')
		self.assertThat('members == expected', members=sorted(members), expected=sorted([
			'f1.txt', 'run.log', '__pysys_skipped_archive_files.txt']), archive=os.path.basename(archivedir))
		self.assertDiff(
			self.copy('extracted-zip/__pysys_skipped_archive_files.txt', self.output, mappers=[
				lambda l: re.sub('cycle[0-9]+', 'cycleN', l[l.rfind('test_output'):].strip().replace('\\','/'))+'\n'], 
				encoding='utf-8'), encoding='utf-8'
		)
		self.assertThat('0.002*1024*1024-1000 < zipBytes < 0.002*1024*1024+200', zipBytes=os.path.getsize(glob.glob(archivedir+'/*.zip')[0]))
		self.log.info('')

		##########
		archivedir = self.output+'/testroot/__pysys_output_archives.test_output' # contains the output dir name
		self.log.info('--- Checking %s (defaults)', os.path.basename(archivedir))
		self.assertThat("len([f for f in files if f.endswith('.zip')])==10", files=sorted(os.listdir(archivedir)))
		self.assertThat("all('PySys_NestedTestcaseFails' in z and z.endswith('.zip') for z in zips)",
			zips=sorted(os.listdir(archivedir)))

		self.assertPathExists(archivedir+'/skipped_artifacts.txt', exists=False)
		
		with zipfile.ZipFile(glob.glob(archivedir+'/PySys_NestedTestcaseFails.cycle*.zip')[0]) as zf:
			self.assertThat('badZipFiles is None', badZipFiles=zf.testzip())
			members = sorted(zf.namelist())
		self.assertThat('members == expected', members=sorted(members), expected=sorted([
			'f1.txt', 'f2.txt', 'f3.txt', 'a/b/nested.txt', 'run.log', u'unicode_filename_\xa3.txt']), archive=os.path.basename(archivedir))
		self.log.info('')

		##########
		archivedir = self.output+'/testroot/__pysys_output_archives_lowTotalLimit/test_output'
		self.log.info('--- Checking %s', '__pysys_output_archives_lowTotalLimit')

		self.assertLineCount(archivedir+'/skipped_artifacts.txt', expr='.+', condition='>0')
		
		with zipfile.ZipFile(glob.glob(archivedir+'/PySys_NestedTestcaseFails.cycle*.zip')[0]) as zf:
			self.assertThat('badZipFiles is None', badZipFiles=zf.testzip())
			members = sorted(zf.namelist())
		# check that the includes works
		self.assertThat('(members == ["f1.txt"]) or (members == ["f1.txt", "f2.txt"])', members=sorted(members), archive=os.path.basename(archivedir))
		self.assertThat('0.010*1024*1024-1000 < totalBytes < 0.010*1024*1024+200', totalBytes=sum(
			os.path.getsize(f) for f in glob.glob(archivedir+'/*.zip')))


		##########
		archivedir = self.output+'/testroot/__pysys_output_archives_none'
		self.log.info('--- Checking %s', os.path.basename(archivedir))

		# check that the includes works
		self.assertThat('zips == []', zips=os.listdir(archivedir))
		