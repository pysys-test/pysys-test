import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		port = self.getNextAvailableTCPPort()
		server1 = self.startProcess(
			command=self.project.appHome+'/my_server.%s'%('bat' if IS_WINDOWS else 'sh'), 
			arguments=['--port', port, ], 
			
			# By default startProcess() uses a clean environment with a minimal set of env vars. If you need to 
			# override or add additional env vars, use the environs= keyword and the createEnvirons helper method
			environs=self.createEnvirons(addToExePath=os.path.dirname(PYTHON_EXE), command=PYTHON_EXE),
			
			# Usually you will want to capture process stdout and stderr. The stdouterr specifies a prefix onto which 
			# PySys will append .out or .err for this process's output. Be sure not to reuse the filename in this test
			stdouterr='my_server1', 
			
			# It's good practice to set a displayName for use in log and error messages
			displayName='my_server1<port %s>'%port, 
			
			# The info dictionary allows us to stash useful info such as port numbers in the Process object
			info={'port':port},
			
			background=True)
		
		# To make the test easier to debug, register a function that will log any lines from the server's stderr during 
		# this test's cleanup phase (i.e. after validate), in case there were any errors from the server
		self.addCleanupFunction(lambda: self.logFileContents(server1.stderr))
		
		# Although all processes are automatically killed by PySys during cleanup, it's sometimes beneficial to perform 
		# a clean shutdown first, for example many code coverage tools only generate output during a graceful shutdown
		self.addCleanupFunction(lambda: [
			self.startPython([self.input+'/httpget.py', f'http://127.0.0.1:{server1.info["port"]}/shutdown'], 
				stdouterr=self.allocateUniqueStdOutErr('my_server1_shudown'), displayName='my_server1 clean shutdown', ignoreExitStatus=True), 
			server1.wait(TIMEOUTS['WaitForProcessStop'])] if server1.running() else None)
		
		# One way to wait for a server to come up is to wait until it starts listening on the expected TCP port; 
		# always pass in the process that is responsible for the port to allow early aborting if it fails
		self.waitForSocket(port=server1.info['port'], process=server1)

		# Another way to wait for a server to start is by by polling for a grep regular expression. The 
		# errorExpr/process arguments ensure we abort with a really informative message if the server fails to start
		self.waitForGrep('my_server1.out', 'Started MyServer .*on port .*', errorExpr=[' (ERROR|FATAL) '], process=server1) 
		
		self.log.info('')
		
		# If you need to start the same process from multiple tests it may be worth factoring it out into a test plugin
		# In this case, we created a MyServerTestPlugin class and gave it the alias "myserver" so we can use a single 
		# line to allocate a port which saves re-tying the above logic every time
		server2 = self.myserver.startServer(name="my_server2")
		
		# Now we want to run some processes to check the server is behaving correctly. We could run these in the 
		# foreground, but since there are several, and since we don't care about ordering, it's quicker to run them 
		# in the background at the same time rather than one by one. We use allocateUniqueStdOutErr() rather than 
		# explicitly specifying the stdout/err files because we don't plan to examine the output during validation, but 
		# want it all to be in the output dir in case of failures. 
		self.startPython([self.input+'/httpget.py', f'http://127.0.0.1:{server1.info["port"]}/data/myfile.json'], 
			stdouterr=self.allocateUniqueStdOutErr('httpget'), background=True)
		self.startPython([self.input+'/httpget.py', f'http://127.0.0.1:{server2.info["port"]}/data/myfile.json'], 
			stdouterr=self.allocateUniqueStdOutErr('httpget'), background=True)

		self.log.info('')
		# Test some error cases of server startup
		self.myserver.startServer("my_server_invalid_loglevel", waitForServerUp=False, expectedExitStatus="!=0", 
			arguments=['--loglevel', 'foobar'])
		self.myserver.startServer("my_server_invalid_port", waitForServerUp=False, expectedExitStatus="== 123", 
			arguments=['--configfile', self.myserver.createConfigFile(port=-1), '--loglevel', 'DEBUG'])

		# Now wait for all the processes to finish (except for the main servers themselves which will keep running 
		# until they're stopped). This should be quick so use the short (60s) WaitForSignal rather than the longer 
		# default of WaitForProcess (10mins). It's recommended to never set a timeout value under 60s since it can 
		# make tests unreliable when run concurrently on heaily loaded test machines
		self.waitForBackgroundProcesses(excludes=[server1, server2], timeout=TIMEOUTS['WaitForSignal'])

		# Check that the server hasn't terminated unexpectedly while processing the above requests
		# (occasionally assertions can go into execute() if they need variables that aren't available to validate(). 
		self.assertThat('server.running()', server=server1)
		self.assertThat('server.running()', server=server2)
		
	def validate(self):	
		self.assertGrep('my_server1.out', r' (ERROR|FATAL|WARN) .*', contains=False)
		self.assertGrep('my_server2.out', r' (ERROR|FATAL|WARN) .*', contains=False)

		# It's often a good idea to factor out the above checking into a method on your test plugin, so there's only 
		# one place to change if you need to change the expressions you're checking for and/or ignoring, e.g.:
		self.myserver.checkLog('my_server1.out')
		self.myserver.checkLog('my_server2.out')

		self.assertThatGrep('my_server_invalid_port.out', r' ERROR +(.*)', "value == expected", 
			expected="Server failed: Invalid port number specified: -1")
		self.assertThatGrep('my_server_invalid_loglevel.out', r' ERROR +(.*)', "'FOOBAR' in value")
	
