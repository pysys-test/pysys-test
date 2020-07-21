import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import pysys.utils.perfreporter
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, glob

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		
		self.copy(self.input, self.output+'/test')
		runPySys(self, 'pysys', ['run', '-o', 'myoutdir'], workingDir='test')
		self.logFileContents('pysys.out', maxLines=0)
		self.logFileContents('pysys.err')
		self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)

		self.copy(self.input+'/pysysproject.xml', self.output+'/test/', 
			mappers=[pysys.mappers.ExcludeLinesMatching('.*csvPerformanceReporterSummaryFile')])

		runPySys(self, 'default-perf-config', ['run', '-o', 'default-perf-config'], workingDir='test')
		
		# test standalone entrypoint
		perfreporterexe = os.path.dirname(pysys.utils.perfreporter.__file__)+'/perfreporter.py'
		self.startPython([perfreporterexe, '--help'], stdouterr='perfreporter-help', ignoreExitStatus=True)
		self.logFileContents('perfreporter-help.err')
		self.logFileContents('perfreporter-help.out')
		self.startPython([perfreporterexe, 'aggregate', self.input+'/sample.csv'], stdouterr='perfreporter-aggregate', abortOnError=False)
		
	def validate(self):
		defaultPerfFilename=glob.glob(self.output+'/test/__pysys_performance/*/*.csv')[0]
		defaultPerfFilename = '/'.join(defaultPerfFilename.replace('\\','/').split('/')[-3:])
		self.assertThat('"$" not in defaultPerfFilename', defaultPerfFilename=defaultPerfFilename)
		self.assertThat('re.match(expected, defaultPerfFilename)', defaultPerfFilename=defaultPerfFilename, 
			expected=r'__pysys_performance/default-perf-config_.+/perf_\d\d\d\d-\d\d-\d\d_\d\d.\d\d.\d\d.default-perf-config.csv')

		self.assertGrep('perfreporter-aggregate.out', expr='# resultKey,.*')
		self.assertLineCount('perfreporter-aggregate.out', expr='Sample small integer performance result', condition='==1')
		self.assertGrep('perfreporter-aggregate.out', expr=',150.0,') # average value
	
		perfdir = self.output+'/test/perfsummary'
		summ = os.listdir(perfdir)[0]
		self.logFileContents(perfdir+'/'+summ)
		
		assert summ.startswith('myoutdir_PySys_NestedTestcase_perf_'), summ
		assert summ.endswith('.csv'), summ
		for x in summ.split('_'): # all components should be non-empty, incl date, time, hostname
			assert x != '', summ

		with open(perfdir+'/'+summ) as f:
			lines = f.readlines()
		assert lines[0].strip() == '<custom reporter>'
		s = CSVPerformanceFile('\n'.join(lines[1:]))
		self.log.info('Parsed performance file: %s', str(s))
		self.log.info('Parsed performance file: %s', repr(s))

		with open(self.output+'/parsed_perf_genuine_data.txt', 'w') as f:
			f.write(repr(s))

		assert len(s.results)==4, s
		
		# do extra testing of parsing weirdly shaped data
		f2 = CSVPerformanceFile(
"""
			
				
# testId,value,   resultKey, foobar, unit,biggerIsBetter,toleranceStdDevs,samples,stdDev,
	
# some comment
	
testid1,0,   my result key1  , foobarval, unitval,fAlse,,-1,-1,,
testid1,0,   my result key1  , foobarval, unitval,fAlse,,-1,-1,XXXX,XXXX,XXXX,XXXX,XXXX
testid2,0,   my result key2  , foobarval2, unitval,fAlse,,-1,-1,,#resultDetails:#

""")
		with open(self.output+'/parsed_perf_contrived_data.txt', 'w') as f:
			f.write(repr(f2))
		self.log.info('Parsed performance file: %s', repr(f2))
		
		self.assertDiff('parsed_perf_genuine_data.txt', 'parsed_perf_genuine_data.txt', replace=[
			('hostname=".*startTime="\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d', 'hostname...startTime')])
		self.assertDiff('parsed_perf_contrived_data.txt', 'parsed_perf_contrived_data.txt')
		
		# now test the aggregation logic
		
		agg1 = CSVPerformanceFile('')
		agg1.runDetails['key1'] = 'val 1'
		agg1.runDetails['key2'] = 'val 2'
		# use large numbers to check for arithmetic overflow problems calcualting stddev
		agg1.results.append({'resultKey':'result 2','testId':'TEST','value':1000000000.1,'unit':'someunit','biggerIsBetter':True,'toleranceStdDevs':1.0,'samples':1,'stdDev':0})
		agg1.results.append({'resultKey':'result 1','testId':'TEST','value':1000000000.1,'unit':'someunit','biggerIsBetter':True,'toleranceStdDevs':1.0,'samples':1,'stdDev':0})
		agg1.results.append({'resultKey':'result 1','testId':'TEST','value':1000000002.1,'unit':'someunit','biggerIsBetter':True,'toleranceStdDevs':1.0,'samples':1,'stdDev':0, 'resultDetails':{'resultdet1':'val1'} })
		agg1.results.append({'resultKey':'result 1','testId':'TEST','value':1000000003.1,'unit':'someunit','biggerIsBetter':True,'toleranceStdDevs':1.0,'samples':1,'stdDev':0})

		agg2 = CSVPerformanceFile('')
		agg2.runDetails['key1'] = 'val 1'
		agg2.runDetails['key2'] = 'val 2B'
		agg2.runDetails['key3'] = 'val 3'
		agg2.results.append({'resultKey':'result 1','testId':'TEST','value':1000000015.1,'unit':'someunit','biggerIsBetter':True,'toleranceStdDevs':1.0,'samples':1,'stdDev':0, 'resultDetails':{'resultdet2':'val2'} })
		agg2.results.append({'resultKey':'result 1','testId':'TEST','value':1000000016.1,'unit':'someunit','biggerIsBetter':True,'toleranceStdDevs':1.0,'samples':1,'stdDev':0, 'resultDetails':{'resultdet3':'val3'}})

		self.log.info('agg1: %s'%repr(CSVPerformanceFile.aggregate([agg1])))
		combinedA = CSVPerformanceFile.aggregate([agg1, agg2])
		combinedB = CSVPerformanceFile.aggregate([CSVPerformanceFile.aggregate([CSVPerformanceFile.aggregate(agg1), agg2])]) # should be the same, but good to check
		
		self.log.info('aggregate(aggregate(agg1),agg2): %s'%repr(combinedA))
		self.log.info('aggregate(agg1,agg2): %s'%repr(combinedB))
		
		results = [x['value'] for x in agg1.results+agg2.results if x['resultKey'] == 'result 1']
		mean = sum(results)/len(results)
		assert mean > 1000000, mean
		stddev = math.sqrt(sum([(x-mean)**2 for x in results])/(len(results)-1))
		
		for a in combinedA, combinedB:
			assert a.results[0]['value'] == mean, a['value']
			assert a.results[0]['samples'] == 5
			assert str(a.results[0]['stdDev']).startswith(str(stddev)[:6]), a['stdDev']
			assert a.results[0]['resultDetails']['resultdet3'] == 'val3'
		
			assert a.runDetails['key1'] == 'val 1', a.runDetails
			assert a.runDetails['key2'] == 'val 2; val 2B', a.runDetails
			assert a.runDetails['key3'] == 'val 3', a.runDetails
