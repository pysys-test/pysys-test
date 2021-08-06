from pysys.launcher.console_make import ConsoleMakeTestHelper

class MyLegacyMaker(ConsoleMakeTestHelper):
	def makeTest(self, **kwargs):
		kwargs['group'] = 'myGroup'
		return ConsoleMakeTestHelper.makeTest(self, **kwargs)
