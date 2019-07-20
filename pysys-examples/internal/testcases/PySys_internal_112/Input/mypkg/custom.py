from pysys.baserunner import BaseRunner
from pysys.xml.descriptor import DescriptorLoader

class CustomDescriptorLoader(DescriptorLoader):
	def loadDescriptors(self, dir, **kwargs):
		descriptors = super(CustomDescriptorLoader, self).loadDescriptors(dir, **kwargs)
		
		# dynamically determine available databases; perhaps based on project 
		# config, current platform, etc
		availableDatabases = ['MockDatabase']
		for ver in self.project.supportedMyDatabaseVersions.split(','):
			availableDatabases.append('MyDatabase_%s'%ver.strip())
		
		# programatically modify descriptors as needed - add modes, change run order, add skips, etc
		for d in descriptors:
			if 'database-test' in d.groups:
				for db in availableDatabases: 
					if db not in d.modes: # be sure not to add duplicate modes
						d.modes.append(db)

		return descriptors

class CustomRunner(BaseRunner):
	def setup(self):
		# by this point we have a descriptor for each mode and the descriptors 
		# have been sorted by run order; we could manually change the order 
		# of the descriptors if we wish. 
		
		"""
		for d in self.descriptors:
			# run all the mock database tests early
			if 'database-test' in d.groups and 'MockDatabase' in d.mode:
				d.executionOrderHint = +10

		self.descriptors.sort(key=lambda d: (d.executionOrderHint, d.file.lower(), d.id))
		"""