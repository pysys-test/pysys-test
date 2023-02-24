import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon shines bright')
		
		self.log.info('expected failure:')
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon shines r.ght')
		self.checkForFailedOutcome()

		self.log.info('expected failure:')
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon [^ ]*', contains=False)
		self.checkForFailedOutcome()

		self.log.info('expected failure:')
		self.assertGrep(file='file.txt', filedir=self.input, expr='e', contains=False) # multiple matches
		self.checkForFailedOutcome()

		self.log.info('expected failure:')
		self.assertGrep(file='file.txt', filedir=self.input, expr='moo. [^ ]', contains=False)
		self.checkForFailedOutcome()

		self.log.info('expected failure:')
		self.assertGrep(file='file.txt', filedir=self.input, expr='ERROR', contains=False)
		self.checkForFailedOutcome()

		self.log.info('expected failure:')
		self.assertGrep(file='file.txt', filedir=self.input, expr=' WARN .*', contains=False)
		self.checkForFailedOutcome()

		# check for correct failure message:
		self.log.info('')
		self.assertGrep(file='run.log', expr='Grep on file.txt contains "moon shines r[.]ght" ... failed')
		# for an expression ending in *, print just the match
		self.assertGrep(file='run.log', expr='Grep on file.txt does not contain "moon [^ ]*" failed with: "moon shines" ... failed', literal=True)
		
		self.assertGrep(file='run.log', expr='does not contain "e" failed with 7 matches, first is: "Now', literal=True)
				
		# for an expression not ending in *, print the whole line
		self.assertGrep(file='run.log', expr='Grep on file.txt does not contain "moo. [^ ]" failed with: "And the moon shines bright as I rove at night, " ... failed', literal=True)
		# here's a real-world example of why that's useful
		self.assertGrep(file='run.log', expr='Grep on file.txt does not contain "ERROR" failed with: "2019-07-24 [Thread1] ERROR This is an error message!"', literal=True)
		self.assertGrep(file='run.log', expr='Grep on file.txt does not contain " WARN .*" failed with: " WARN This is a warning message!"', literal=True)
		
		
		self.log.info('')
		self.assertThat('grepResult==None', grepResult=
			self.assertGrep(file='file.txt', filedir=self.input, expr='moon shines right', contains=False)
		)
		self.assertGrep(file='file.txt', filedir=self.input, expr='(?P<tag>moon) shines bright')
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon.*bright')
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon.*bright', ignores=['oon'], contains=False)
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon.*bright', ignores=['pysys is great', 'oh yes it is'])
		self.assertThat('grepResult==expected', expected=('westlin winds',),
			grepResult=self.assertGrep(file='file.txt', filedir=self.input, expr='(Now eastlin|westlin winds)').groups(),
		)

		# check new and old positional arguments
		self.assertGrep('file.txt', 'moon.*bright', filedir=self.input) # new, expr as 2nd arg
		self.assertGrep('file.txt', self.input, 'moon.*bright', True) # old
		self.assertGrep(self.input+'/file.txt', None, 'moon.*bright', True) #old
		self.assertGrep('file.txt', self.input, expr='moon.*bright') # old


		self.write_text('myserver.log', u'Successfully authenticated user "myuser" in 0.6 seconds.')

		self.assertThatGrep('myserver.log', r'Successfully authenticated user "([^"]*)" in ([^ ]+) seconds', "value == expected", expected='myuser')

		self.assertThatGrep('myserver.log', r'Successfully authenticated user "([^"]*)" in ([^ ]+) seconds', "value == expected", expected='myuser')
		self.assertThatGrep('myserver.log', r'Successfully authenticated user "(?P<value>[^"]*)"', "value == expected", expected='myuser')
		self.assertThatGrep('myserver.log', r'Successfully authenticated user "([^"]*)" in (?P<authSecs>[^ ]+) seconds', "0.0 <= float(value) <= 60.0")
		self.assertThatGrep('myserver.log', r'Successfully authenticated user "(?P<username>[^"]*)" in (?P<authSecs>[^ ]+) seconds', "value['username'] == expected", expected='myuser')

		self.assertThatGrep('myserver.log', r'Successfully authenticated user ".*" in ([^ ]+) seconds', 
			"re.match(detailRegex, value)", detailRegex=r"[0-9]+\.[0-9]$")

		MAX_AUTH_TIME = 60
		
		self.assertThat('username == expected', expected='myuser',
			**self.assertGrep('myserver.log', expr=r'Successfully authenticated user "(?P<username>[^"]*)"'))
			
		# this is a convenient place to test that waitForGrep behaves the same way
		self.assertThat('username == expected', expected='myuser',
			**self.waitForGrep('myserver.log', expr=r'Successfully authenticated user "(?P<username>[^"]*)"'))
		self.assertThat('result == {}', 
			result=self.waitForGrep('myserver.log', expr=r'NO MATCH authenticated user "(?P<username>[^"]*)"', timeout=0.01, abortOnError=False))

		self.assertThat('0 <= float(authSecs) < max', max=MAX_AUTH_TIME,
			**self.assertGrep('myserver.log', expr=r'Successfully authenticated user "[^"]*" in (?P<authSecs>[^ ]+) seconds\.'))

		self.assertGrep('myserver.log', reFlags=re.VERBOSE | re.IGNORECASE, expr=r"""
			in\   
			\d +  # the integral part
			\.    # the decimal point
			\d *  # some fractional digits
			\ seconds\. # in verbose regex mode we escape spaces with a slash
			""")


		self.assertThat('result == {}', 
			result=self.assertGrep('myserver.log', expr='NO MATCH "(?P<username>[^"]*)"', contains=False))

		self.assertThat('result is None', 
			result=self.assertGrep('myserver.log', expr='NO MATCH "([^"]*)"', contains=False))

		# example from doc:
		self.write_text('example.log', 'Foo\nBar\nError message FAILURE - stack trace is:\n   MyClass.class\n\nNow have Bar')
		
		self.assertGrep('example.log', expr=r'MyClass', mappers=[
				pysys.mappers.IncludeLinesBetween('Error message.* - stack trace is:', stopBefore='^$'),
			])
		self.assertGrep('example.log', expr=r'Bar', contains=False, mappers=[
				pysys.mappers.IncludeLinesBetween('Error message.* - stack trace is:', stopBefore='^$'),
			])

		# Check final newlines aren't captured by assertThatGrep, but trailing spaces are
		self.assertThatGrep(self.input+'/file.txt', r'Waiving grain wide over the plain delights the weary ([^x]*)', 
		      expected='farmer, ')
		
	def checkForFailedOutcome(self):
		outcome = self.outcome.pop()
		if outcome == FAILED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
