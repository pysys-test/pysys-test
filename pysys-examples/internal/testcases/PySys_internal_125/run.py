from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		# start with the failures
		self.log.info('--- Expected failures:')
		self.assertThat('actual == expected', actual__eval="'prefix'+' foo bar '+'suffix'", expected='foobar')
		reasonFailedEvalAssert = self.getOutcomeReason()
		self.addOutcome(PASSED, override=True)

		self.assertThat('actual == expected', actual="prefix foo bar suffix", expected='foobar')
		reasonFailedAssert = self.getOutcomeReason()
		self.addOutcome(PASSED, override=True)

		self.assertThat('actual', actual__eval="undefined_variable+1")
		reasonBlockedParamEval = self.getOutcomeReason()
		self.addOutcome(PASSED, override=True)

		self.assertThat('undefined_parameter+1', actual='foo')
		reasonBlockedConditionEval = self.getOutcomeReason()
		self.addOutcome(PASSED, override=True)
		
		self.log.info('--- Checking the failures gave the right messages:')

		# now check the first message was correct; the rest will be caught with the diff

		self.assertThat('reasonFailedEvalAssert.startswith(expected)', reasonFailedEvalAssert=reasonFailedEvalAssert, 
			expected="Assert that (actual == expected) with ")

		self.log.info('------')

		###############
		
		# documented success cases
	
		msg = 'Started successfully'
		v = 20

		class MyClass:
			def __init__(self, id): self.x = self.id = id
			def getId(self): return self.x
			def __repr__(self): return 'MyClass(%s)'%self.x
		myDataStructure = {'item1':[MyClass('foobar')],
			'item2':[MyClass('baz')],
			}
		self.write_text('myprocess-1.log', u'Server started in 51.9 seconds')
		self.write_text('myprocess-2.log', u'Server started in 20.3 seconds')
		self.write_text('foo.zip', '')

		# examples are from our API doc:
		self.assertThat("actualStartupMessage == expected", actualStartupMessage=msg, expected='Started successfully')
		self.assertThat("actualStartupMessage.endswith('successfully')", actualStartupMessage=msg)
		self.assertThat("(0 <= actualValue < max) and type(actualValue)!=float", actualValue=v, max=100)

		self.assertThat("IS_WINDOWS or re.match(expected, actual)", actual="foo", expected="f.*")
		self.assertThat("import_module('tarfile').is_tarfile(self.output+file) is False", file='/foo.zip')

		self.assertThat('float(startupTime) < 60.0', 
			startupTime__eval="self.getExprFromFile('myprocess-1.log', 'Server started in ([0-9.]+) seconds')")
		self.assertThat('float(startupTime) < 60.0', 
			startupTime__eval="self.getExprFromFile('myprocess-2.log', 'Server started in ([0-9.]+) seconds')")

		self.assertThat('actual == expected', actual__eval="myDataStructure['item1'][-1].getId()", expected='foobar')
		self.assertThat('actual == expected', actual__eval="myDataStructure['item2'][-1].getId()", expected='baz')
		self.assertThat('actual == expected', actual__eval="myDataStructure['item2'][-1].id", expected='baz')
		self.assertThat('len(actual) == 1', actual__eval="myDataStructure['item2']")

		item = 5 # should be ignored
		# this is advanced usage - using a previous named parameter in a named parameter eval, useful for unpacking complex data structures in a clear way
		if sys.version_info[0:2] >= (3, 6):
			self.assertThat('actual == expected', item__eval="myDataStructure['item1']", actual__eval="item[-1].getId()", expected='foobar', needsPython36=True)

		########

		# extra cases
		
		# string escaping
		msg = 'Foo"\'\nbar'
		self.assertThat(r'actualErrorMessage == "Foo\"\'\nbar"', actualErrorMessage=msg)

		self.write_text('file1.dat', u'xxx')
		self.write_text('file2.dat', u'xxx')
		self.assertThat('actualFileSize > 0', actualFileSize__eval="os.path.getsize(self.output+'/file1.dat')")
		self.assertThat('actualFileSize > 0', actualFileSize__eval="os.path.getsize(self.output+'/file2.dat')")

		# check we print something sane if there are no named parameters
		self.assertThat("5 == %s", '5.0')

		self.copy('run.log', 'assertions.txt', mappers=[
			lambda line: line[line.find('Assert '):] if 'Assert that' in line else None,
			])

	def validate(self):
		replace = []
		ignores = []
		# unfortunately prior to Python 3.6 iteration over kwargs was not in a guaranteed order so we can't 
		# match the order of multiple named parameters
		if sys.version_info[0:2] < (3, 6):
			self.log.info('Ignoring order of named parameters in log messages as that is only fixed in Python 3.6+')
			replace = [('with .*,.* [.][.][.]', 'with <named parameters> [.][.][.]')]
			ignores = ['needsPython36']
		self.assertDiff('assertions.txt', replace=replace, ignores=ignores)
		