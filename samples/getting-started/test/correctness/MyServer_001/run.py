import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	""" This is a system test for a server process called MyServer. It checks that the server can be started and 
	respond to basic HTTP requests. """
	
	def execute(self):
		# Ask PySys to pick a free TCP port to start the server on (this allows running tests in 
		# parallel without clashes).
		serverPort = self.getNextAvailableTCPPort()
		
		# A common system testing task is pre-processing a file, for example to substitute in required 
		# testing parameters.
		self.copy(self.input+'/myserverconfig.json', self.output+'/', mappers=[
			lambda line: line.replace('@SERVER_PORT@', str(serverPort)),
		])
		
		# Start the server application we're testing (as a background process)
		# self.project provides access to properties in pysysproject.xml, such as appHome which is the 
		# location of the application we're testing.
		server = self.startProcess(
			command   = self.project.appHome+'/my_server.%s'%('bat' if IS_WINDOWS else 'sh'), 
			arguments = ['--configfile', self.output+'/myserverconfig.json', ], 
			environs  = self.createEnvirons(addToExePath=os.path.dirname(PYTHON_EXE)),
			stdouterr = 'my_server', displayName = 'my_server<port %s>'%serverPort, background = True,
			)
		
		# Wait for the server to start by polling for a grep regular expression. The errorExpr/process 
		# arguments ensure we abort with a really informative message if the server fails to start.
		try:
			self.waitForGrep('my_server.out', 'Started MyServer .*on port .*', errorExpr=[' (ERROR|FATAL) '], process=server) 
		finally:
			self.logFileContents('my_server.out')
			self.logFileContents('my_server.err')
		
		# Logging a blank line every now and again can make the test output easier to read
		self.log.info('')
		
		# Run a test tool (in this case, written in Python) from this test's Input/ directory.
		self.startPython([self.input+'/httpget.py', f'http://127.0.0.1:{serverPort}/data/myfile.json'], 
			stdouterr='httpget_myfile')
		
		# By default PySys checks that processes return a 0 (success) exit code, so the test will abort with 
		# an error if not, unless we set expectedExitStatus to indicate we're expecting some kind of failure.
		self.startPython([self.input+'/httpget.py', f'http://127.0.0.1:{serverPort}/non-existent-path'], 
			stdouterr='httpget_nonexistent', expectedExitStatus='!= 0')
	
	def validate(self):
		# This method is called after execute() to perform validation of the results by checking the 
		# contents of files in the test's output directory. Note that during test development you can 
		# re-run validate() without waiting for a full execute() run using "pysys run --validateOnly". 
		
		self.logFileContents('my_server.out')
		
		# It's good practice to check for unexpected errors and warnings so they don't go unnoticed
		self.assertGrep('my_server.out', r' (ERROR|FATAL|WARN) .*', contains=False)
		
		self.assertThat('message == expected', 
			message=pysys.utils.fileutils.loadJSON(self.output+'/httpget_myfile.out')['message'], 
			expected="Hello world!", 
			# Extra arguments can be used to give a more informative message if there's a failure:
			url='/data/myfile.json', 
			)
