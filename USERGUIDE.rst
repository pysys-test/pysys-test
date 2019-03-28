User Guide/FAQ
==============

Platform detection
------------------
In addition to the features provided by Python itself, PySys includes some 
constants to help quickly detect what platform is in use, such as OSFAMILY and 
PLATFORM. It's very common to have one set of logic for Windows and another for 
all non-Windows (Unix-based) platforms, and PySys has a dedicated constant for 
that::

	if IS_WINDOWS:
		...
	else:
		...

Skipping tests
--------------
If your run.py logic detects that a test should not be executed for this 
platform or mode, simply use this near the top of the `execute()` method, 
specifying the reason for the skip::

	self.skipTest('MyFeature is not supported on Windows') 
	
As well as setting the test outcome and reason, this will raise an exception 
ensuring that the rest of `execute()` and `validate()` do not get executed. 

Checking for error messages in log files
-----------------------------------------
The `assertGrep()` method is an easy way to check that there are no error 
messages in log files from processes started by PySys. Rather than checking for 
an expression such as `' ERROR: '`, it is recommended to define your expression 
so that the error message itself is included, e.g.::

	self.assertGrep('myprocess.log', expr=' ERROR: .*', contains=False)

This approach ensures that the error message itself is included in the test's 
console output, run.log and the summary of failed test outcomes, which avoids 
the need to open up the individual logs to find out what happened, and makes it 
much easier to triage test failures, especially if several tests fail for the 
same reason. 

Sharing logic for validation across tests
-----------------------------------------
Often you may have some standard logic that needs to be used in the validation 
of many/all testcases, such as checking log files for errors. One recommended 
pattern for this is to define a helper function in a custom `BaseTest` 
subclassed by all your tests that is named after what is being checked - for 
example `checkLogsForErrors()` - and explicitly call that method from 
the `.validate()` method of each test. That approach allows you to later 
customize the logic by changing just one single place, and also to omit it for 
specific tests where it is not wanted. 

