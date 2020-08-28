import logging, sys, io, os
import json

import pysys

log = logging.getLogger('pysys.myorg.mywriter')

class MyResultsWriter(pysys.writer.api.BaseRecordResultsWriter):
	"""Example of a writer plugin class that produces a JSON file to record the test results."""
	
	outputFile = None
	"""The filename. Must be pecified
	"""

	def setup(self, **kwargs):
		super().setup(**kwargs)
		assert self.outputFile, 'This property must be set in the pysysproject.xml configuration file'
		self.results = []

	def processResult(self, testObj, **kwargs):
		self.results.append({
			'testId': testObj.descriptor.id,
			'cycle': kwargs['cycle']+1, # (cycle parameter starts from 0)
			'outcome': str(testObj.getOutcome()),
			'outcomeReason': testObj.getOutcomeReason(),
			'outcomeIsFailure': testObj.getOutcome().isFailure(),
		})
	
	def cleanup(self, **kwargs):
		super().cleanup(**kwargs)

		with open(os.path.join(self.runner.output+'/..', self.outputFile), 'w', encoding='utf-8') as f:
			json.dump({
				'runDetails': dict(self.runner.runDetails), 
				'results': self.results
			}, f)
		log.debug('Wrote results to file: %s', self.outputFile)