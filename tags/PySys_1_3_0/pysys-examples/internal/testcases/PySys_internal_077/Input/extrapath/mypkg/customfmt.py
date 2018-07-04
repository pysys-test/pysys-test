from pysys.utils.logutils import ColorLogFormatter
import logging

this is a syntax error!

class CustomFormatter(ColorLogFormatter):
	def __init__(self, optionsDict):
		self.customprefix = optionsDict.pop('customopt')
		super(CustomFormatter, self).__init__(optionsDict)
		
	def format(self, record):
		result = super(CustomFormatter, self).format(record)
		result = self.customprefix+' %s'%(result)
		return result
