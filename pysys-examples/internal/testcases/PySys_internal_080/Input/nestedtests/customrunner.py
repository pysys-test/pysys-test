from pysys.baserunner import BaseRunner
from pysys.constants import *
from pysys.process.monitor import *

class MyCustomRunner(BaseRunner):
	
	def setup(self, **kwargs):
		super(MyCustomRunner, self).setup(**kwargs)
		# matches what we put into changelog to document how to go back to old behaviour
		ProcessMonitorTextFileHandler.setDefaults(
        [
           ProcessMonitorKey.DATE_TIME_LEGACY, 
           ProcessMonitorKey.CPU_CORE_UTILIZATION, 
           ProcessMonitorKey.MEMORY_RESIDENT_KB,
           ProcessMonitorKey.MEMORY_VIRTUAL_KB,
        ], writeHeaderLine=False)
