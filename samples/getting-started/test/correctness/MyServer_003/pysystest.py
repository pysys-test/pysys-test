__pysys_title__   = r""" MyServer responses - /sensorValues endpoint (+ demo of PySys assertions, and multiple modes) """
#                        ===============================================================================

__pysys_purpose__ = r""" To verify that responses from MyServer are correct on the /sensorValues REST endpoint. 
	
	This also shows some of the different approaches to validation in PySys, using various styles of assertion.
	"""

__pysys_created__ = "1999-12-31"
__pysys_groups__  = "myServerSensorValues"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

# This test will be executed for each of the following modes, in this case controlling the compression
# of results from the server and whether authentication is used. The test can use self.mode to find out which
# mode it is executing and/or self.mode.params to access any parameters; parameters are also assigned
# as fields on the test object. Keep mode strings short but self-describing.
# 
# The first mode in the list is the "primary" one.
__pysys_modes__            = lambda helper: [
	mode for mode in 
		helper.createModeCombinations( # Takes any number of mode lists as arguments and returns a single combined mode list
			helper.inheritedModes,
			{
					# NB: by default only the first - "primary" - mode in each list will execute unless using the --modes flag
					'CompressionNone': {'compressionType':None},
					'CompressionGZip': {'compressionType':'gzip'},
			}, 
			[
					{'auth':None}, # Mode name is autogenerated if not explicitly specified
					{'auth':'OS'}, # In practice auth=OS modes will always be excluded since MyFunkyOS isn't a real OS
			]) 
	# This is a Python list comprehension syntax for filtering the items in the list
	if mode['auth'] != 'OS' or helper.import_module('sys').platform == 'MyFunkyOS'
	]


import pysys.basetest, pysys.mappers
from pysys.constants import *
from myorg.myserverhelper import MyServerHelper

class PySysTest(MyServerHelper, pysys.basetest.BaseTest):

	def execute(self):
		server = self.myserver.startServer(name="my_server")
		
		self.startPython([self.input+'/httpget.py', 
			f'http://127.0.0.1:{server.info["port"]}/sensorValues', self.mode.params['compressionType'], self.mode.params['auth']], stdouterr='sensorValues')

	def validate(self):	
		self.logFileContents('sensorValues.out', maxLines=0) 

		# For demonstration purposes this test checks the same data in several different ways; in a real application 
		# you'd pick just one of these! 

		# assertGrep is good for checking errors aren't present, or positively for checking that an expression is 
		# present but you don't care where.
		self.assertGrep('my_server.out', r' (ERROR|FATAL|WARN) .*', contains=False)
		self.assertGrep('sensorValues.out', r'"timestamp": ".+"') # contains some timestamp, don't care what or where

		# Advanced: regular expression escaping can be tricky. Backslashes can be handled with r'...' strings, but 
		# here's a nice trick using re.escape() for cases where you want to include a literal that includes regex characters.
		self.assertGrep('sensorValues.out', re.escape(r'"dataPaths": "c:\\devicedata*\\sensor.EXTENSION"').replace('EXTENSION', '(xml|json|JSON)'))

		# assertThatGrep is useful for regular expression extract-and-assert use cases (and gives much better messages 
		# if there's a failure than the above assertGrep lines would!). 
		self.log.info('')
		self.assertThatGrep('sensorValues.out', grepRegex=r'"sensorId": "([^"]*)"', 
			conditionstring='value == expected', expected='ABC1234')
		
		# Advanced: for complex cases with multiple regex groups, a (?P<value>xxx) named group can be used to extract the desired one. 
		self.assertThatGrep('sensorValues.out', r'"(sensorId|deviceId)": "(?P<value>[^"]*)"', 
			'value.lower() in expected', expected=['abc1234', 'ghi987'])

		# assertLineCount is useful when you want to check how many times a line is present (rather than whether it's 
		# present or not).
		self.log.info('')
		self.assertLineCount('sensorValues.out', r'sensorId', condition='< 3')

		# assertThat provides a powerful way to validate data of any type; just load it into Python first. If you have a 
		# choice, JSON is often a great choice for a data format as it's trivial to convert to a Python data structure. 
		self.log.info('')
		sensorValuesData = pysys.utils.fileutils.loadJSON(self.output+'/sensorValues.out')
		self.assertThat('measurements == expected', measurements=sensorValuesData.get('measurements'), expected=[
			123.4,
			670,
			10/3.0,
			None,
			123.4,
		])
		# Sorting and filtering can be used to remove anomalies that you don't care about and ensure tests are reliable.
		self.assertThat('measurements == expected', measurements=sorted(m for m in sensorValuesData.get('measurements') if m is not None), 
			expected=[
				10/3.0,
				123.4,
				123.4,
				670,
		])

		# It's also great for checking value(s) are in range, or string operations like starts/endswith. 
		# It's sometimes useful to add extra parameters which aren't needed for the condition but provide useful info 
		# for someone debugging test failures.
		self.assertThat('0 < min(measurements) < 1000*1000', measurements=[m for m in sensorValuesData.get('measurements') if m is not None], 
			httpEndpoint='sensorValues')
		self.assertThat('sensorId.startswith(expected)', sensorId=sensorValuesData.get('sensorId'), expected='ABC')

		# When you want to check expressions deep inside a data structure, __eval provide a convenient way to do 
		# it that's also self-describing so if there's a failure you'll know what data the test was trying to pull out.
		self.assertThat('measurement == expected', measurement__eval="sensorValuesData['measurements'][0]", expected=123.4)
		self.assertThat('measurement == expected', measurement__eval="sensorValuesData['measurements'][1]", expected=670)
		self.assertThat('expected-0.5 < measurement < expected+0.5', measurement__eval="sensorValuesData['measurements'][2]", expected=3.3)
		
		# assertDiff is good for when you want to compare a big document or lots of values. A common pattern is to 
		# dynamically generate a file containing the data you want to diff. By default the diff is against a file 
		# in the test's Reference/ directory. If the reference filename is the same (recommended) the 2nd arg is optional. 
		self.log.info('')
		self.write_text('measurements-extracted.txt', '\n'.join('measurement=%0.4f'%m for m in sensorValuesData['measurements'] if m is not None))
		self.assertDiff('measurements-extracted.txt', 'measurements-extracted.txt')
		self.assertDiff('measurements-extracted.txt') # equivalent to the above

		# Another common pattern is to create a copy of an output file for diffing, by filtering the lines with mapper 
		# functions to remove inconsequential data that changes (e.g. timestamps), and irrelevant lines. 
		# PySys provides some built-in mappers, or you can create your own with lambda expressions.
		self.log.info('')
		self.assertDiff(self.copy('sensorValues.out', 'sensorValues-diffable.out', mappers=[
			pysys.mappers.RegexReplace(pysys.mappers.RegexReplace.DATETIME_REGEX, '<timestamp>'),
			pysys.mappers.RegexReplace('("collectionHost":) "[^"]*"', r'\1 "<host removed by test>"'),
			lambda line: None if line.startswith('WARNING: ') else line, # remove any warning log lines that contaminate the output
			lambda line: None if len(line.strip())==0 else line, # strip blank lines
		]))
		