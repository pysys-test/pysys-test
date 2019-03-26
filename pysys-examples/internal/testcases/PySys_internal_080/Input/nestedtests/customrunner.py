from pysys.baserunner import BaseRunner
from pysys.constants import *
from pysys.process.monitor import *

class MyCustomRunner(BaseRunner):
	
	def setup(self, **kwargs):
		super(MyCustomRunner, self).setup(**kwargs)
		# matches what we put into changelog to document how to go back to old behaviour
		TabSeparatedFileHandler.setDefaults(
        [
           ProcessMonitorKey.DATE_TIME_LEGACY, 
           ProcessMonitorKey.CPU_CORE_UTILIZATION, 
           ProcessMonitorKey.MEMORY_RESIDENT_KB,
           ProcessMonitorKey.MEMORY_VIRTUAL_KB,
           ProcessMonitorKey.MEMORY_PRIVATE_KB,
           ProcessMonitorKey.THREADS,
           ProcessMonitorKey.KERNEL_HANDLES
        ] if IS_WINDOWS else [
           ProcessMonitorKey.DATE_TIME_LEGACY, 
           ProcessMonitorKey.CPU_CORE_UTILIZATION, 
           ProcessMonitorKey.MEMORY_RESIDENT_KB,
           ProcessMonitorKey.MEMORY_VIRTUAL_KB,
        ], writeHeaderLine=False)
