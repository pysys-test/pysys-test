from pysys.utils.perfreporter import CSVPerformanceReporter
import logging

class CustomPerfReporter(CSVPerformanceReporter):
	def getRunHeader(self):
		return '<custom reporter>\n'+super(CustomPerfReporter, self).getRunHeader()

	def cleanup(self):
		logging.getLogger('perfreporter').info('Called cleanup on CustomPerfReporter')