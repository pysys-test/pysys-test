import pysys

class CustomTestMaker(pysys.launcher.console_make.DefaultTestMaker):
	def validateTestId(self, prefix, numericSuffix, **kwargs):
		if '-' in prefix: raise Exception('Test ids containing - are not permitted')
		if numericSuffix and int(numericSuffix) < 10:
			raise pysys.launcher.console_make.ProposeNewTestIdNumericSuffixException('This test id conflicts with an existing test', '00010')
		