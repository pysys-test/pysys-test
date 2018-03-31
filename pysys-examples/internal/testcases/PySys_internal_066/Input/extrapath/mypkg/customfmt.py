from pysys.utils.logutils import DefaultPySysLoggingFormatter
import logging

class CustomFormatter(DefaultPySysLoggingFormatter):
	def __init__(self, optionsDict, isStdOut):
		self.customprefix = optionsDict.pop('customopt')
		super(CustomFormatter, self).__init__(optionsDict, isStdOut)
		
	def format(self, record):
		result = super(CustomFormatter, self).format(record)
		result = self.customprefix+' isStdOut=%s %s'%(self.isStdOut, result)
		return result
