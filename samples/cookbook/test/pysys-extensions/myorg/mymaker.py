import logging
import pysys

log = logging.getLogger('pysys.MyTestMaker')

class MyTestMaker(pysys.launcher.console_make.DefaultTestMaker):
	"""
	A custom test maker that validates proposed test ids based on what is already present in your version control system 
	to avoid collisions. 
	"""
	
	def validateTestId(self, prefix, numericSuffix, parentDir, **kwargs):
		# Raises an exception if test id is already in use
	
		def alreadyExistsInMyVersionControlSystem(testid):
			return False # put real implementation here
		
		if not alreadyExistsInMyVersionControlSystem(prefix+numericSuffix): return
		
		if not numericSuffix: raise Exception(f'Test id {prefix} already exists in remote version control system; cannot auto-generate a free test id unless there is a numeric _NN suffix')
		
		numericPad = len(numericSuffix)
		
		while True:
			log.info('Test id %s already exists, will try to find a later numeric suffix that is free', prefix+numericSuffix)
			
			assert int(numericSuffix) < 1000, f'Failed to find a free numeric id for a new test in {parentDir} after too many attempts' # avoid infinite loops
			numericSuffix = f'{int(numericSuffix)+1 :0{numericPad}}'
			
			if not alreadyExistsInMyVersionControlSystem(prefix+numericSuffix): 
				raise pysys.launcher.console_make.ProposeNewTestIdNumericSuffixException('This test id conflicts with an existing test', numericSuffix)
		