from pysys.utils.perfreporter import CSVPerformanceReporter
import logging

class CustomPerfReporter(CSVPerformanceReporter):
	def __init__(self, project, summaryfile, testoutdir):
		# this checks backwards compatibility with any custom perf reporter classes created against 1.3.0 before **kwargs was added
		super(CustomPerfReporter, self).__init__(project, summaryfile, testoutdir)
		assert self.runner is not None
	
	def getRunHeader(self):
		return '<custom reporter>\n'+super(CustomPerfReporter, self).getRunHeader()

	def getRunDetails(self):
		d = super(CustomPerfReporter, self).getRunDetails()
		# a typical use of run details overriding would be to add detailed information 
		# about what we're testing, e.g. a build or version number
		d['myBuildNumber'] = '1.23.45X'
		return d

	def cleanup(self):
		# just to verify that this gets called
		logging.getLogger('perfreporter').info('Called cleanup on CustomPerfReporter')