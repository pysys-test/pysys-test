import logging
import pysys

log = logging.getLogger('pysys.MyTestMaker')

class CustomTestMaker(pysys.launcher.console_make.DefaultTestMaker):
	def validateTestId(self, prefix, numericSuffix, parentDir, **kwargs):
		log.info('Called validateTestId for numericSuffix=%r and parentDir=%s', numericSuffix, parentDir)
		if '-' in prefix: raise Exception('Test ids containing - are not permitted')
		if numericSuffix and int(numericSuffix) < 10:
			raise pysys.launcher.console_make.ProposeNewTestIdNumericSuffixException('This test id conflicts with an existing test', '00010')
		