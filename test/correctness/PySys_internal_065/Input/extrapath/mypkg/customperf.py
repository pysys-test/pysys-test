from pysys.utils.perfreporter import CSVPerformanceReporter
import logging

class CustomPerfReporter(CSVPerformanceReporter):
	myDefaultedProperty = 5

	def __init__(self, project, summaryfile, testoutdir, runner, **kwargs):
		super(CustomPerfReporter, self).__init__(project, summaryfile, testoutdir, runner, **kwargs)
		assert self.runner is not None
	
	def getRunHeader(self, testobj, **kwargs): # new signature with testobj
		assert testobj
		assert self.myproperty == 'my_project_value'
		assert self.myDefaultedProperty == 10
		return '<custom reporter>\n'+super(CustomPerfReporter, self).getRunHeader()

	def getRunDetails(self): # deprecated legacy signature without testobj
		d = super(CustomPerfReporter, self).getRunDetails()
		# a typical use of run details overriding would be to add detailed information 
		# about what we're testing, e.g. a build or version number
		d['myBuildNumber'] = '1.23.45X'
		return d

	def cleanup(self):
		# just to verify that this gets called
		logging.getLogger('perfreporter').info('Called cleanup on CustomPerfReporter')