from pysys.utils.logutils import ColorLogFormatter
import logging, os

class CustomFormatter(ColorLogFormatter):
	def __init__(self, optionsDict):
		super(CustomFormatter, self).__init__(optionsDict)
		
	def colorCategoryToEscapeSequence(self, category):
		if os.getenv('PYSYS_TEST_FRIENDLY_ESCAPES','')!='true': # use env var to allow running nested test to see results visually when running nested test on its own
			return super(CustomFormatter,self).colorCategoryToEscapeSequence(category)
			
		# override this to avoid translating to actual escape sequences, to allow testing, even on windows where escape sequences are changed
		result = self.COLOR_CATEGORIES.get(category, None)
		if result not in self.COLOR_ESCAPE_CODES:
			return '<unknown escape code category "%s" color %s>'%(category, result)
		return '<%s>'%result
	