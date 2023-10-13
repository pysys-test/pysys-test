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
Contains the built-in reporter classes. 
"""

import collections, threading, time, math, sys, os
import io
import logging
import json
import glob

from pysys.perf.api import *
from pysys.constants import *
from pysys.utils.logutils import BaseLogFormatter
from pysys.utils.fileutils import mkdir, toLongPathSafe
from pysys.utils.pycompat import *

log = logging.getLogger('pysys.perfreporter')


class CSVPerformanceReporter(BasePerformanceReporter):
	"""Performance reporter which writes to a CSV file.
	
	This reporter writes to a UTF-8 file of 
	comma-separated values that is both machine and human readable and 
	easy to view and use in any spreadsheet program, and after the columns containing 
	the information for each result, contains comma-separated metadata containing 
	key=value information about the entire run (e.g. hostname, date/time, etc), 
	and (optionally) associated with each individual test result (e.g. test mode etc). 
	The per-run and per-result metadata is not arranged in columns since the structure 
	differs from row to row.

	After tests have run, the summary file is published with category ``CSVPerformanceReport`` 
	using the `pysys.writer.api.ArtifactPublisher` interface. 

	The following properties can be set in the project configuration for this reporter:		
	
	"""
	
	summaryFile = ''
	"""
	The filename pattern used for the summary file(s); see `DEFAULT_SUMMARY_FILE`. 
	
	For compatibility purposes, if not specified explicitly, the summary file for the CSVPerformanceReporter can be 
	configured with the project property ``csvPerformanceReporterSummaryFile``, however this is deprecated. 
	This property can also be accessed and configured under the alternative capitalization ``summaryfile``, however this 
	is discouraged as of PySys 2.1+, where ``summaryFile`` is the preferred name. 

	"""

	aggregateCycles = False
	"""
	Enable this if you want PySys to rewrite the summary file at the end of a multi-cycle test with an aggregated 
	file containing the mean and standard deviation for all the cycles, rather than a separate line for each cycle. 
	This may be easier to consume when triaging performance results and looking for regressions. 
	
	.. versionadded:: 2.1
	"""

	publishArtifactCategory = 'CSVPerformanceReport' 
	"""
	If specified, the output file will be published as an artifact using the specified category name. 

	.. versionadded:: 2.1
	"""

	DEFAULT_SUMMARY_FILE = '__pysys_performance/${outDirName}_${hostname}/perf_${startDate}_${startTime}.${outDirName}.csv'
	"""The default summary file if not overridden by the ``csvPerformanceReporterSummaryFile`` project property, or 
	the ``summaryFile=`` attribute. See `getRunSummaryFile()`. This is relative to the runner output+'/..' directory 
	(typically testRootDir, unless ``--outdir`` is overridden).
	"""

	def setup(self, **kwargs):
		super().setup()

		# for backwards compat
		self.summaryfile = self.summaryfile or self.summaryFile or getattr(self.project, 'csvPerformanceReporterSummaryFile', '') or self.DEFAULT_SUMMARY_FILE

		self.__summaryFilesWritten = set()

	def getRunHeader(self, testobj=None, **kwargs):
		"""Return the header string to the CSV file.
		
		There should usually be no reason to override this method. 
		
		:meta private:
		"""
		
		try:
			runDetails = self.getRunDetails(testobj)
		except Exception: # for pre-2.0 signature
			runDetails = self.getRunDetails()
		
		return CSVPerformanceFile.makeCSVHeaderLine(runDetails)

	def cleanup(self):
		with self._lock:
			if self.runner is not None and self.__summaryFilesWritten:
				for p in sorted(list(self.__summaryFilesWritten)):
					
					if self.runner.cycle > 1 and self.aggregateCycles:
						try:
							perfFile = CSVPerformanceFile.load(p)
							perfFile = CSVPerformanceFile.aggregate([perfFile])
						except Exception as ex: # pragma: no cover
							log.exception('Failed to read and aggregate performance information for %s: '%p)
							# Don't make it fatal, more useful to go ahead and publish it as best we can
						else:
							log.info('Rewriting CSV to aggregate results across all %d cycles'%self.runner.cycles)
							perfFile.dump(p)
				
					log.info('Performance results were written to: %s', os.path.normpath(p)) # absolute path is easiest to deal with
					log.info('  (add the above path to env %s to show a comparison against that baseline on future test runs)', PrintSummaryPerformanceReporter.BASELINES_ENV_VAR)
					
					if self.publishArtifactCategory:
						self.runner.publishArtifact(p, self.publishArtifactCategory)

	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		formatted = self.formatResult(testobj, value, resultKey, unit, toleranceStdDevs, resultDetails)
		self.recordResult(formatted, testobj)

	def formatResult(self, testobj, value, resultKey, unit, toleranceStdDevs, resultDetails):
		"""Retrieve an object representing the specified arguments that will be passed to recordResult to be written to the performance file(s).

		:meta private:

		:param testobj: the test case instance registering the value
		:param value: the value to be reported
		:param resultKey: a unique string that fully identifies what was measured
		:param unit: identifies the unit the value is measured in
		:param toleranceStdDevs: indicates how many standard deviations away from the mean for a regression
		:param resultDetails:  A dictionary of detailed information that should be recorded together with the result

		"""
		data = {'resultKey':resultKey,
				'testId':testobj.descriptor.id,
				'value':str(value),
				'unit':str(unit),
				'biggerIsBetter':str(unit.biggerIsBetter).upper(),
				'toleranceStdDevs':str(toleranceStdDevs) if toleranceStdDevs else '',
				'samples':'1',
				'stdDev':'0' ,
				'resultDetails':resultDetails
				}
		return CSVPerformanceFile.toCSVLine(data)+'\n'

	def recordResult(self, formatted, testobj):
		"""Record results to the performance summary file.

		:meta private:

		:param formatted: the formatted string to write
		:param testobj: object reference to the calling test

		"""
		# generate a file in the test output directory for convenience/triaging, plus add to the global summary
		path = testobj.output+'/performance_results.csv'
		encoding = 'utf-8'
		
		def callGetRunHeader():
			try:
				return self.getRunHeader(testobj)
			except Exception: # pragma: no cover - for pre-2.0 signature 
				return self.getRunHeader()
		
		if not os.path.exists(path):
			with io.open(toLongPathSafe(path), 'w', encoding=encoding) as f:
				f.write(callGetRunHeader())
		with io.open(toLongPathSafe(path), 'a', encoding=encoding) as f:
			f.write(formatted)
		
		# now the global one
		path = self.getRunSummaryFile(testobj)
		mkdir(os.path.dirname(path))
		with self._lock:
			alreadyexists = os.path.exists(toLongPathSafe(path))
			with io.open(toLongPathSafe(path), 'a', encoding=encoding) as f:
				if not alreadyexists: 
					testobj.log.info('Creating performance summary log file at: %s', os.path.normpath(path))
					f.write(callGetRunHeader())
				f.write(formatted)
			self.__summaryFilesWritten.add(path)
	
	@staticmethod
	def tryDeserializePerformanceFile(path):
		if not path.endswith('.csv'): return None
		return CSVPerformanceFile.load(path)

class JSONPerformanceReporter(BasePerformanceReporter):
	"""Performance reporter which writes to a JSON file.
	
	After tests have run, the summary file is published with category ``JSONPerformanceReport`` 
	using the `pysys.writer.api.ArtifactPublisher` interface. 

	.. versionadded:: 2.1

	The following properties can be set in the project configuration for this reporter:		
	
	"""
	
	summaryFile = ''
	"""
	The ``.json`` filename pattern used for the summary file(s); see `DEFAULT_SUMMARY_FILE`. 
	"""

	publishArtifactCategory = 'JSONPerformanceReport' 
	"""
	If specified, the output file will be published as an artifact using the specified category name. 
	"""

	DEFAULT_SUMMARY_FILE = '__pysys_performance/${outDirName}_${hostname}/perf_${startDate}_${startTime}.${outDirName}.json'
	"""The default summary file if not overridden by the ``summaryFile=`` attribute. See `getRunSummaryFile()`. 
	This is relative to the runner output+'/..' directory (typically testRootDir, unless ``--outdir`` is overridden).
	"""

	def setup(self, **kwargs):
		super().setup()
		self.__summaryFilesWritten = set()
		
	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		path = self.getRunSummaryFile(testobj)
		mkdir(os.path.dirname(path))
		with self._lock:
			alreadyexists = os.path.exists(toLongPathSafe(path))
			with io.open(toLongPathSafe(path), 'a', encoding='utf-8') as f:
				if not alreadyexists: 
					testobj.log.info('Creating performance summary log file at: %s', os.path.normpath(path))
					f.write('{"runDetails": ')
					json.dump(self.getRunDetails(testobj), f)
					f.write(', "results":[\n')
				else:
					f.write(',\n')
					
				json.dump({
					'resultKey':resultKey,
					'value':value,
					'unit':str(unit),
					'biggerIsBetter':unit.biggerIsBetter,
					'samples':1,
					'stdDev':0,
					'toleranceStdDevs':toleranceStdDevs,
					'testId':testobj.descriptor.id,
					'resultDetails':resultDetails or {}
				}, f)
			self.__summaryFilesWritten.add(path)

	def cleanup(self):
		with self._lock:
			if self.__summaryFilesWritten:
				for p in sorted(list(self.__summaryFilesWritten)):
					with io.open(toLongPathSafe(p), 'a', encoding='utf-8') as f:
						f.write('\n]}\n')
					
					log.info('Performance results were written to: %s', os.path.normpath(p).replace(os.path.normpath(self.project.testRootDir), '').lstrip('/\\'))

					if self.publishArtifactCategory:
						self.runner.publishArtifact(p, self.publishArtifactCategory)

	@staticmethod
	def tryDeserializePerformanceFile(path):
		if not path.endswith('.json'): return None
		with io.open(toLongPathSafe(path), encoding='utf-8') as f:
			data = json.load(f)
			return PerformanceRunData(path, data['runDetails'], data['results'])

class PrintSummaryPerformanceReporter(BasePerformanceReporter):
	"""Performance reporter which logs a human-friendly summary of all performance results to the console at the end of 
	the test run. 

	By setting the `BASELINES_ENV_VAR` environment variable, this reporter will also print out an 
	automatic comparison from the named baseline file(s) to the results from the current test run. 
	This feature is very useful when comparingdifferent strategies for optimizing your application. 
	
	.. versionadded:: 2.1

	"""

	BASELINES_ENV_VAR = 'PYSYS_PERFORMANCE_BASELINES'
	"""
	Set this environment variable to a comma-separated list of performance (e.g. ``.csv``) files to print out an 
	automatic comparison from the baseline file(s) to the results from the current test run. 
	
	This feature is very useful when comparing different strategies for optimizing your application. 
	
	For best results, use multiple cycles for all test runs so that standard deviation can be calculated. 
	
	The filenames can be absolute paths, glob paths using ``*`` and ``**``, or relative to the testRootDir. For example::
	
		export PYSYS_PERFORMANCE_BASELINES=__pysys_performance/mybaseline*/**/*.csv,__pysys_performance/optimization1*/**/*.csv
		
	"""

	def setup(self, **kwargs):
		super().setup()
		self.results = []
		
		import pysys.perf.perfreportstool
		self.comparisonGenerator = pysys.perf.perfreportstool.PerformanceComparisonGenerator(reporters=self.runner.performanceReporters)
		self.baselines = self.comparisonGenerator.loadFiles(
			baselineBaseDir=self.project.testRootDir,
			paths=os.getenv(self.BASELINES_ENV_VAR,'').split(','), 
			)
		if self.baselines:
			log.info('Successfully loaded performance comparison data from %d files: %s', len(self.baselines), ', '.join(b.name for b in self.baselines))

	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		with self._lock:
			self.results.append({
						'resultKey':resultKey,
						'value':value,
						'unit':str(unit),
						'biggerIsBetter':unit.biggerIsBetter,
						'samples':1,
						'stdDev':0,
						'toleranceStdDevs':toleranceStdDevs,
						'testId':testobj.descriptor.id,
						'resultDetails':resultDetails or {}
					})

	def isEnabled(self, **kwargs):
		return True
	
	def cleanup(self):
		if not self.isEnabled(): return
		if not self.results: return
		
		with self._lock:
			logmethod = logging.getLogger('pysys.perfreporter.summary').info

			# perform aggregation in case there are multiple cycles
			p = PerformanceRunData.aggregate(PerformanceRunData('this', self.getRunDetails(), self.results))

			if not self.baselines:
				logmethod('Performance results summary:')
				# simple formatting when there's no comparisons to be done
				for r in p.results:
					logmethod("  %s = %s %s (%s)%s %s", r['resultKey'], self.valueToDisplayString(r['value']), r['unit'],
						 'bigger is better' if r['biggerIsBetter'] else 'smaller is better',
							'' if r['samples']==1 or ['value'] == 0 else f", stdDev={self.valueToDisplayString(r['stdDev'])} ({100.0*r['stdDev']/r['value']:0.1f}% of mean)",
							r['testId'],
								extra = BaseLogFormatter.tag(LOG_TEST_PERFORMANCE, [0,1], suppress_prefix=True))
				
			else:
				logmethod('\n')
				self.comparisonGenerator.logComparisons(self.baselines+[p])
