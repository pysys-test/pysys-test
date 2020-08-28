from pysys.constants import *
from pysys.basetest import BaseTest
import re
import glob
import codecs
import pysys

class PySysTest(BaseTest):
	
	def execute(self):
		# these items are deliberately omitted from the autosummary tables e.g. because they're really internal or unfortunate details we don't want to encourage people to use directly, or are documented in the associated method rather than centrally
		IGNORE_LIST = """
defaultAbortOnError
defaultIgnoreExitStatus
manualTester
monitorList
processCount
processList
resources
outcome
lock
deletedir
cleanup
pythonCoverage
codeCoverage
waitForSignal
logFileContentsDefaultExcludes
pysys
		""".strip().split('\n')

		def filter_member(m):
			return not (m.startswith('_') or m in IGNORE_LIST 
				or ':meta private:' in (getattr(self, m).__doc__ or '')
				or ':deprecated:' in (getattr(self, m).__doc__ or '')
				)
	
		attr = [m for m in self.__dict__.keys() if filter_member(m)]

		# dir is technically not something we shoudl rely on too much, but this is only a test so probably ok; unlike __dict__ it gives us base members
		members = [m for m in dir(BaseTest) if filter_member(m)]
		self.write_text('basetest.members.txt', '\n'.join(sorted(attr))+'\n\n'+'\n'.join(sorted(members)))
		
		attr = set()
		members = set()
		
		# make this work against both source and binary distributions
		pysysroot = os.path.dirname(os.path.dirname(pysys.__file__))
		docdir = glob.glob(pysysroot+'/PySys*dist-info*') # created when installing from whl
		if len(docdir)==1: 
			docdir = docdir[0]
		else:
			docdir = pysysroot+'/docs'
		self.log.info('Checking completeness of %s/BaseTest.rst', docdir)
		with codecs.open(docdir+'/BaseTest.rst', 'r', encoding='ascii') as f: # this also serves to check we don't have non-ascii chars creeping in
			for l in f:
				l = l.rstrip()
				m = re.match('\t+([a-z][a-zA-Z0-1_]+)$', l) # autosummary item
				if m: members.add(m.group(1))
				m = re.search(':ivar ([a-zA-Z0-9_]+)? *([a-zA-Z0-9_]+)+:', l) 
				if m: attr.add(m.group(2))
				m = re.search('- ``self.([a-zA-Z0-9_]+)`` ', l) # this is how we doc ivar's currently
				if m: attr.add(m.group(1))
		self.write_text('basetest.doc.txt', '\n'.join(sorted(attr))+'\n\n'+'\n'.join(sorted(members)))
		
	def validate(self):
		self.assertGrep('basetest.doc.txt', expr='.') # check it's not empty
		self.assertDiff(self.output+'/basetest.doc.txt', self.output+'/basetest.members.txt')
