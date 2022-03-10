#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2022 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""
Non-public module providing a command line for working with performance reports. 

:meta private: Not public API may change at any time. 

"""

import collections, threading, time, math, sys, os
import io
import logging
import json
import glob

if __name__ == "__main__":
	sys.path.append(os.path.dirname( __file__)+'/../..') # pragma: no cover

from pysys.constants import *
from pysys.utils.logutils import BaseLogFormatter
from pysys.utils.fileutils import mkdir, toLongPathSafe
from pysys.utils.pycompat import *
from pysys.utils.logutils import ColorLogFormatter, stdoutPrint

from pysys.perf.api import *
from pysys.perf.reporters import *

log = logging.getLogger('pysys.perfreporter')

class PerformanceComparisonGenerator:
	"""Internal helper class for comparing multiple .csv or json performance files and printing the differences. 

	:meta private: Not public API may change at any time. 
	.. versionadded:: 2.1

	"""

	BASELINES_ENV_VAR = PrintSummaryPerformanceReporter.BASELINES_ENV_VAR

	def __init__(self, reporters): 
		self.reporters = reporters # list of perf reporter instances (or for standalone invocation, classes); must be at least one
		
			# - with the static tryDeserializePerformanceFile method on them
			
		# We'd like to delegate to the first runner. Assuming it's a static method is probably reasonable. Could break if user subclass redefines as non-static
		self.valueToDisplayString = reporters[0].valueToDisplayString

	def loadFiles(self, baselineBaseDir, paths):
		# return a list PerformanceRunData for each path in the specified list
		
		configuredBaselines = os.getenv(self.BASELINES_ENV_VAR)
		if not paths:
			return None  # pragma: no cover

		baselines = []
		for b in paths:
			b = b.strip()
			if not b: continue
			
			# if not abs, take paths as relative to testRootDir. Easier to work with the cwd which is constantly changing
			b = os.path.join(baselineBaseDir, b)
			
			if os.path.isfile(b): 
				baselines.append(b)
			else:
				globresults = sorted(glob.glob(b, recursive=True))
				if not globresults: raise Exception('Cannot find any paths matching '+self.BASELINES_ENV_VAR+' expression: %s'%b)
				baselines.extend(globresults)
		baselineData = {}
		for b in baselines:
			if os.path.isdir(b): raise Exception(self.BASELINES_ENV_VAR+' may contain "*" or "**" glob expressions but not directories: %s'%b)
			x = None
			for r in self.reporters:
				x = r.tryDeserializePerformanceFile(b)
				if x: break
			if x:
				baselineData[b] = x
			else:  # pragma: no cover
				raise Exception('Failed to find a reporter that can deserialize performance files of this type: %s'%b)

		baselineData = [PerformanceRunData.aggregate(b) for b in baselineData.values()]
		return baselineData
		
	def logComparisons(self, comparisonFiles, sortby=None, printmethod=stdoutPrint):
		# comparisonFiles are a list of PerformanceRunData instances
		
		# NB: this method implementation mutates the passed in comparisonFiles
		
		sortby = sortby or os.getenv('PYSYS_PERFORMANCE_SORT_BY', 'resultKey')
		
		files = comparisonFiles

		out  = printmethod

		# we may not have the project available here if running this standalone, but can still reuse the same 
		# logic for deciding if coloring is enabled
		colorFormatter = ColorLogFormatter({})
		def addColor(category, s):
			if not category: return s
			return colorFormatter.formatArg(category, s) 
				
		# usually resultKey is itself the unique key, but for comparisons we also 
		# want to include units/biggerIsBetter since if these change the 
		# comparison would be invalidated
		ComparisonKey = collections.namedtuple('ComparisonKey', ['resultKey', 'unit', 'biggerIsBetter'])

		# iterate over each comparison item, stashing various aggregated information we need later, and printing summary info
		for p in files:
			p.keyedResults = {
				ComparisonKey(resultKey=r['resultKey'], unit=r['unit'], biggerIsBetter=r['biggerIsBetter'])
				: r for r in p.results
			}

		commonRunDetails = {}
		for k in list(files[-1].runDetails.keys()):
			if all([k in p.runDetails and  p.runDetails[k] == files[-1].runDetails[k] for p in files]):
				commonRunDetails[k] = files[-1].runDetails[k]

		def formatRunDetails(k, val):
			valsplit = val.split(';')
			if k == 'startTime' and len(valsplit)>=3:
				val = ' .. '.join([valsplit[0].strip(), valsplit[-1].strip()])
			else:
				val = val.replace('; ',';')
			return '%s=%s'%(k, addColor(LOG_TEST_DETAILS, val))

		#out('Comparing performance files with these common run details: %s'% ', '.join([formatRunDetails(k, commonRunDetails[k]) for k in commonRunDetails]))

		# Assign a comparison label to each; use outDirName if unique, else make something based on the filename
		if len(set(p.runDetails.get('outDirName') for p in files)) == len(files):
			for p in files: p.comparisonLabel = p.runDetails.get('outDirName', p.name)
		else:
			for p in files: p.comparisonLabel = os.path.splitext(os.path.basename(p.name))[0].replace('perf_','')
			
		out('Performance comparison summary between the following runs (the differing "run details" are shown):')
			
		for p in files:
			out('- %s (%d result keys, %d samples/result)%s:'%(
				addColor(LOG_TEST_DETAILS, p.comparisonLabel), 
				len(p.results), 
				float( sum([r['samples'] for r in p.results])) / len(p.results),
				'' if p.comparisonLabel != p.runDetails.get('outDirName')
					else f' from {p.name if not os.path.abspath(p.name) else os.path.relpath(p.name)}'
				))
			out('     %s'%', '.join([formatRunDetails(k, p.runDetails[k]) for k in p.runDetails if k not in commonRunDetails]))

		out('')
		out('Comparison results:')
		out('  where fromRun->toRun format is: (%improvement) = (speedup ratio) = (sigmas/stdDevs where change above +/- 2.0 gives 95% probability it\'s significant; only significant results are colored)')
		out('')
		ComparisonData = collections.namedtuple('ComparisonData', [
			'comparisonPercent', #%improvement
			'comparisonSigmas',  #improvements as a multiple of stddev
			'ratio', # speedup ratio of from->to, how much faster we are now
			'rfrom', # the "from" result value
			'rto',   # the "to"   result value
			'relativeStdDevTo', # relative stdDev as a % of the "to" value, or None if only one sample (or value is 0)
			'toleranceStdDevs', # The configured tolerance specified in this test, if any
			])
		
		# now compute comparison info, comparing each path to the final one
		comparisons = {} # ComparisonKey:[ComparisonInfo or string if not available, ...]
		comparetoresults = files[-1].keyedResults
		comparisonheaders = []
		for p in files[:-1]:
			if len(files)>2:
				comparisonheaders.append('%s->%s'%(p.comparisonLabel, files[-1].comparisonLabel))
			
			keyedResults = p.keyedResults
			for k in comparetoresults:
				c = comparisons.setdefault(k, [])
				if k not in keyedResults:
					c.append('Compare from value is missing')
				else:
					rfrom = keyedResults[k]
					rto = comparetoresults[k]
					# avoid div by zero errors; results are nonsensical anyway if either is zero
					if rfrom['value'] == 0: 
						c.append('Compare from value is zero')
						continue
					if rto['value'] == 0: 
						c.append('Compare to value is zero')
						continue

					
					# frequently at least one of these will have only one sample so 
					# not much point doing a statistically accurate stddev estimate; so just 
					# take whichever is bigger (which neatly ignores any that are zero due
					# to only one sample)
					relStdDev = max(abs(rfrom['stdDev']/rfrom['value']), abs(rto['stdDev']/rto['value']))

					# how many times faster are we now
					ratio = rto['value']/rfrom['value'] # initially, we ignore biggerIsBetter in the ratio calculation...
					
					# use a + or - sign to indicate improvement vs regression in the % (rather than a reciprocal which is harder to understand)
					sign = 1.0 if k.biggerIsBetter else -1.0
					comparisonPercent = 100.0*(ratio - 1)*sign
					
					# assuming a normal distribution, 1.0 or more gives 68% confidence of 
					# a real difference, and 2.0 or more gives 95%. 
					comparisonSigmas = sign*((ratio-1)/relStdDev) if relStdDev else None
					# = (new-old)/stddev

					# but +/- isn't relevant when displaying the ratio; we want ratios >1 to always be a good thing, so use reciprocal here
					if not k.biggerIsBetter: ratio = 1.0/ratio
					
					c.append(ComparisonData(
						comparisonPercent=comparisonPercent, 
						comparisonSigmas=comparisonSigmas,
						ratio=ratio,
						rfrom=rfrom['value'], 
						rto=rto['value'],
						relativeStdDevTo=100.0*rto['stdDev']/rto['value'] if rto['samples'] > 0 and rto['value']!=0 else None,
						toleranceStdDevs=files[-1].keyedResults[k].get('toleranceStdDevs', 0.0),
					))

		if comparisonheaders:
			headerpad = max([len(h) for h in comparisonheaders])
			comparisonheaders = [('%'+str(headerpad+1)+'s')%(h+':') for h in ([files[-1].comparisonLabel]+comparisonheaders)]

		def getComparisonKey(k):
			if sortby == 'resultKey': return k
			if sortby == 'testId': return (allresultinfo[k]['testId'], k)
			# sort with regressions at the bottom, so they're more prominent
			if sortby == 'comparison%': return [
					(-1*c.comparisonPercent) if hasattr(c, 'comparisonPercent') else -10000000.0
					for c in comparisons[k]]+[k]
			raise Exception(f'Invalid sortby key "{sortby}"; valid values are: resultKey, testId, comparison%')

		sortedkeys = sorted(comparisons.keys(), key=getComparisonKey)
		
		for k in sortedkeys:
			out('%s from %s'%(colorFormatter.formatArg(LOG_TEST_PERFORMANCE, k.resultKey), files[-1].keyedResults[k]['testId']))
			
			r = files[-1].keyedResults[k]
			out(' '+f"Mean from this run = {colorFormatter.formatArg(LOG_TEST_PERFORMANCE, self.valueToDisplayString(r['value']))} {r['unit']}"+
							('' if r['samples']==1 or ['value'] == 0 else f" with stdDev={self.valueToDisplayString(r['stdDev'])} ({100.0*r['stdDev']/r['value']:0.1f}% of mean)")+
							('' if not r.get('toleranceStdDevs') else f"; configured toleranceStdDevs={self.valueToDisplayString(r['toleranceStdDevs'])}"),
					)

			i = 0
			for c in comparisons[k]:
				i+=1
				prefix = ('%s '%comparisonheaders[i]) if comparisonheaders else ''
				if not hasattr(c, 'comparisonPercent'):
					# strings for error messages
					out('  '+prefix+c)
					continue
				
				out('  '+prefix+self.formatResultComparison(c, addColor=addColor))
			out('')

	@staticmethod
	def addPlus(s):
		if not s.startswith('-'): return '+'+s
		return s

	def formatResultComparison(self, comparisonData, addColor, **kwargs):
		# addColor function is passed like this just for simplicity, would be more elegant if this was public API
		c = comparisonData
		
		# don't color for tiny deviations
		if c.comparisonSigmas != None:
			significantresult = abs(c.comparisonSigmas) >= (c.toleranceStdDevs or 2.0)
		else:
			significantresult = abs(c.comparisonPercent) >= 10
		category = None
		if significantresult:
			category = LOG_PERF_BETTER if c.comparisonPercent > 0 else LOG_PERF_WORSE
		
		if c.comparisonSigmas is None:
			sigmas = ''
		else:
			sigmas = ' = %s sigmas'%addColor(category, self.addPlus('%0.1f'%c.comparisonSigmas))
		
		result = addColor(category, '%6s'%(self.addPlus('%0.1f'%c.comparisonPercent)+'%'))

		result += ' = '+addColor(category, self.valueToDisplayString(c.ratio)+'x')+' speedup'

		result += sigmas
		
		return result



def perfReportsToolMain(args):
	USAGE = """
perfreportstool.py aggregate PATH1 PATH2... > aggregated.csv
perfreportstool.py compare PATH_GLOB1 PATH_GLOB2...

where PATH is a .csv file or directory of .csv files 
      GLOB_PATH is a path to a file or files, optionally containing by * and ** globs

The aggregate command combines the specifies CSVfile(s) to form a single file 
with one row for each resultKey, with the 'value' equal to the mean of all 
values for that resultKey and the 'stdDev' updated with the standard deviation. 
This can also be used with one or more .csv file to aggregate results from multiple 
cycles. 

The compare command prints a comparison from each listed performance file to the final one in the list.
Note that the format of the output may change at any time, and it is not intended for machine parsing. 

"""
	# could later add support for automatically comparing files
	if '-h' in sys.argv or '--help' in args or len(args) <2 or args[0] not in ['aggregate', 'compare']:
		sys.stderr.write(USAGE)
		sys.exit(1)
	
	cmd = args[0]
	
	# send log output to stderr to avoid interfering with output we might be redirecting to a file	
	logging.basicConfig(format='%(levelname)s: %(message)s', stream=sys.stderr, level=getattr(logging, os.getenv('PYSYS_LOG_LEVEL', 'INFO').upper()))
	
	if cmd == 'aggregate':
		paths = []
		for p in args[1:]:
			if os.path.isfile(p):
				paths.append(p)
			elif os.path.isdir(p):
				for (dirpath, dirnames, filenames) in os.walk(p):
					for f in sorted(filenames):
						if f.endswith('.csv'):
							paths.append(dirpath+'/'+f)
			else:
				raise Exception('Cannot find file: %s'%p)
		
		if not paths:
			raise Exception('No .csv files found')
		files = []
		for p in paths:
			with io.open(toLongPathSafe(os.path.abspath(p)), encoding='utf-8') as f:
				files.append(CSVPerformanceFile(f.read()))

		f = CSVPerformanceFile.aggregate(files)
		f.dump(sys.stdout)
	elif cmd == 'compare':
		paths = args[1:]
		from pysys.config.project import Project

		project = Project.findAndLoadProject()
		# Can't easily get these classes from project without replicating the logic to instantiate them, which would 
		# be error prone
		performanceReporterClasses = [CSVPerformanceReporter, JSONPerformanceReporter]
		
		gen = PerformanceComparisonGenerator(performanceReporterClasses)
		files = gen.loadFiles(baselineBaseDir=project.testRootDir, paths=paths)
		gen.logComparisons(files)

if __name__ == "__main__":
	perfReportsToolMain(sys.argv[1:])
