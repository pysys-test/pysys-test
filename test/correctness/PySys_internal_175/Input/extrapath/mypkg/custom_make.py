from pysys.launcher.console_make import LegacyConsoleMakeTestHelper

class MyLegacyMaker(LegacyConsoleMakeTestHelper):
	def makeTest(self, **kwargs):
		kwargs['group'] = 'myGroup'
		return LegacyConsoleMakeTestHelper.makeTest(self, **kwargs)
